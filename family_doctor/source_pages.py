from __future__ import annotations

from pathlib import Path

from family_doctor.ingest_models import IngestEvent
from family_doctor.raw_archive import ArchivedArtifact


def _yaml_scalar(value: str | None) -> str:
    if value is None:
        return "null"
    return value


def _event_date(event: IngestEvent) -> str:
    if "T" in event.occurred_at:
        return event.occurred_at.split("T", 1)[0]
    return event.occurred_at


def _source_path(archived_artifacts: list[ArchivedArtifact]) -> str | None:
    if not archived_artifacts:
        return None
    return archived_artifacts[0].relative_path


def _source_info_lines(
    event: IngestEvent, source_kind: str, archived_artifacts: list[ArchivedArtifact]
) -> list[str]:
    primary_source_path = _source_path(archived_artifacts)
    lines = [
        "## 来源信息",
        f"- source_id: `{event.event_id}`",
        f"- member_id: `{event.member_id}`" if event.member_id else "- member_id: `null`",
        f"- source_kind: `{source_kind}`",
        (
            f"- source_path: `{primary_source_path}`"
            if primary_source_path
            else "- source_path: `null`（本阶段仅创建 source page，不复制原始文本）"
        ),
        f"- event_date: `{_event_date(event)}`",
        f"- occurred_at: `{event.occurred_at}`",
        f"- trigger_mode: `{event.trigger_mode}`",
    ]
    if archived_artifacts:
        lines.append("- archived_attachments:")
        for artifact in archived_artifacts:
            lines.append(f"  - `{artifact.attachment_id}` -> `{artifact.relative_path}`")
    else:
        lines.append("- archived_attachments: 无")
    return lines


def _structured_fact_lines(source_kind: str) -> list[str]:
    return [
        "## 提取出的结构化事实",
        f"- deterministic_classification: `{source_kind}`",
        "- placeholder: 当前阶段未接入 OCR/LLM，暂不稳定抽取检验值、诊断、药品明细或症状细节。",
        "- placeholder: 为避免误判，此页仅保留确定性分类与来源元数据。",
    ]


def _verification_lines(source_kind: str, member_id: str | None) -> list[str]:
    lines = [
        "## 待核实项",
        "- 待后续 OCR/LLM 能力接入后，再补充可追溯的结构化事实。",
    ]
    if member_id is None:
        lines.append("- 当前成员归属仍需人工确认。")
    if source_kind == "lab_result":
        lines.append("- 请人工核对化验指标、单位、参考区间与异常标记。")
    elif source_kind == "medication_record":
        lines.append("- 请人工核对药品名称、剂量、频次与有效期。")
    elif source_kind == "checkup_report":
        lines.append("- 请人工核对体检结论、项目名称与报告日期。")
    else:
        lines.append("- 请人工核对症状描述、持续时间与对应成员。")
    return lines


def build_source_page_content(
    event: IngestEvent, source_kind: str, archived_artifacts: list[ArchivedArtifact]
) -> str:
    primary_source_path = _source_path(archived_artifacts)
    frontmatter = [
        "---",
        "type: source",
        f"source_id: {event.event_id}",
        f"member_id: {_yaml_scalar(event.member_id)}",
        f"source_kind: {source_kind}",
        f"source_path: {_yaml_scalar(primary_source_path)}",
        f"event_date: {_event_date(event)}",
        "---",
        "",
    ]

    sections = [
        *_source_info_lines(event, source_kind, archived_artifacts),
        "",
        *_structured_fact_lines(source_kind),
        "",
        *_verification_lines(source_kind, event.member_id),
        "",
    ]
    return "\n".join(frontmatter + sections)


def write_source_page(
    target: Path, event: IngestEvent, source_kind: str, archived_artifacts: list[ArchivedArtifact]
) -> Path:
    source_page_path = target / "02_wiki" / "sources" / f"{event.event_id}.md"
    source_page_path.parent.mkdir(parents=True, exist_ok=True)
    source_page_path.write_text(
        build_source_page_content(event, source_kind, archived_artifacts),
        encoding="utf-8",
    )
    return source_page_path
