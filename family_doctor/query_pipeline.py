from __future__ import annotations

from pathlib import Path
from typing import Any

from family_doctor.query_context import QueryContext, build_query_context, load_query_event


def _section_lines(item: dict[str, Any], section_name: str) -> list[str]:
    sections = item.get("sections", {})
    values = sections.get(section_name, [])
    if not isinstance(values, list):
        return []
    return [str(value) for value in values if isinstance(value, str) and value.strip()]


def _used_source(bucket: str, item: dict[str, Any], *, section_name: str | None = None) -> str:
    identifier = (
        item.get("qa_id")
        or item.get("source_id")
        or item.get("medication_id")
        or item.get("member_id")
        or item.get("page_path")
        or "unknown"
    )
    page_path = item.get("page_path")
    if isinstance(page_path, str) and section_name:
        return f"{bucket}:{identifier}@{page_path}#{section_name}"
    if isinstance(page_path, str):
        return f"{bucket}:{identifier}@{page_path}"
    if section_name:
        return f"{bucket}:{identifier}#{section_name}"
    return f"{bucket}:{identifier}"


def _base_result(context: QueryContext) -> dict[str, Any]:
    return {
        "route": "query",
        "status": "ok",
        "summary": "",
        "answer": "",
        "member_id": context.member_id,
        "question": context.question,
        "used_sources": [],
        "followup_suggestions": [],
    }


def _conservative_low_evidence_answer(
    context: QueryContext,
    *,
    used_sources: list[str] | None = None,
) -> dict[str, Any]:
    result = _base_result(context)
    result["summary"] = "returned conservative low-evidence answer"
    result["answer"] = (
        "目前基于现有资料我无法确认是否可以继续原样用药。"
        " 请以医生意见为准，不要自行调整或停用当前药物；如有不适或血压异常，请尽快联系医生。"
    )
    result["used_sources"] = used_sources or []
    return result


def _answer_current_medications(context: QueryContext) -> dict[str, Any]:
    member_lines: list[str] = []
    medication_lines: list[str] = []
    used_sources: list[str] = []

    for bucket, item in context.ordered_retrieval_items():
        if bucket == "members":
            lines = _section_lines(item, "current_medications")
            if lines:
                member_lines.extend(lines)
                used_sources.append(_used_source(bucket, item, section_name="current_medications"))
        elif bucket == "medications":
            lines = _section_lines(item, "dosage")
            if lines:
                medication_lines.extend(lines)
                used_sources.append(_used_source(bucket, item, section_name="dosage"))

    if not member_lines and not medication_lines:
        return _conservative_low_evidence_answer(context)

    answer_parts: list[str] = []
    if member_lines:
        answer_parts.append(f"当前资料里记录的用药有：{'；'.join(member_lines)}。")
    if medication_lines:
        answer_parts.append(f"可对应到的用法用量信息：{'；'.join(medication_lines)}")
    answer_parts.append("以上仅供核对，请以医生最终确认和药盒标签为准，不要自行调整。")

    result = _base_result(context)
    result["summary"] = "answered current medications from member and medication pages"
    result["answer"] = " ".join(answer_parts)
    result["used_sources"] = used_sources
    return result


def _answer_recent_records(context: QueryContext) -> dict[str, Any]:
    recent_lines: list[str] = []
    used_sources: list[str] = []

    for bucket, item in context.ordered_retrieval_items():
        if bucket == "members":
            lines = _section_lines(item, "recent_records")
            if lines:
                recent_lines.extend(lines)
                used_sources.append(_used_source(bucket, item, section_name="recent_records"))
        elif bucket == "sources":
            summary = item.get("summary")
            if isinstance(summary, str) and summary.strip():
                recent_lines.append(summary)
                used_sources.append(_used_source(bucket, item))

    if not recent_lines:
        return _conservative_low_evidence_answer(context)

    result = _base_result(context)
    result["summary"] = "answered recent records from member context and source pages"
    result["answer"] = (
        f"我目前能找到的最近资料包括：{'；'.join(recent_lines)}"
        " 这些只是现有记录摘录，具体解读和后续处理请以医生意见为准。"
    )
    result["used_sources"] = used_sources
    return result


def _answer_visit_preparation(context: QueryContext) -> dict[str, Any]:
    prep_lines: list[str] = []
    used_sources: list[str] = []

    for bucket, item in context.ordered_retrieval_items():
        if bucket != "plans":
            continue
        lines = _section_lines(item, "visit_prep")
        if not lines:
            continue
        prep_lines.extend(lines)
        used_sources.append(_used_source(bucket, item, section_name="visit_prep"))

    if not prep_lines:
        return _conservative_low_evidence_answer(context)

    result = _base_result(context)
    result["summary"] = "answered visit preparation from plan page"
    result["answer"] = (
        f"按现有计划，复诊前建议先准备：{'；'.join(prep_lines)}"
        " 这只是就医前整理清单，不替代医生的现场评估。"
    )
    result["used_sources"] = used_sources
    return result


def _answer_low_evidence(context: QueryContext) -> dict[str, Any]:
    used_sources: list[str] = []

    for bucket, item in context.ordered_retrieval_items():
        if bucket != "qa_summaries":
            continue
        used_sources.append(_used_source(bucket, item))

    return _conservative_low_evidence_answer(context, used_sources=used_sources)


def run_query_pipeline(event_path: Path) -> dict[str, Any]:
    context = build_query_context(load_query_event(event_path))
    handlers = {
        "current_medications": _answer_current_medications,
        "recent_records": _answer_recent_records,
        "visit_preparation": _answer_visit_preparation,
        "low_evidence_safe_answer": _answer_low_evidence,
    }

    handler = handlers.get(context.intent_hint or "")
    if handler is None:
        return _conservative_low_evidence_answer(context)
    return handler(context)
