from __future__ import annotations

from pathlib import Path
from typing import Any

from family_doctor.ingest_models import IngestEvent
from family_doctor.markdown_utils import append_lines_under_heading, ensure_page, relative_link, safe_slug


def _wiki_update(path: Path, target: Path, page_type: str, source_id: str) -> dict[str, Any]:
    resolved_path = path.resolve()
    resolved_target = target.resolve()
    return {
        "page_type": page_type,
        "path": str(resolved_path),
        "relative_path": resolved_path.relative_to(resolved_target).as_posix(),
        "source_id": source_id,
        "status": "committed",
    }


def _member_page_content(member_id: str, display_name: str) -> str:
    return "\n".join(
        [
            "---",
            "type: member",
            f"member_id: {member_id}",
            f"display_name: {display_name}",
            "---",
            "",
            f"# {display_name}",
            "",
            "## 基本信息",
            "",
            "## 成员识别与代理关系",
            "",
            "## 重要病史",
            "",
            "## 过敏史与禁忌",
            "",
            "## 当前用药",
            "",
            "## 最近关键指标",
            "",
            "## 近期就医/检查",
            "",
            "## 当前计划",
            "",
            "## 待核实项",
            "",
            "## 来源索引",
            "",
        ]
    )


def _plan_page_content(member_id: str) -> str:
    return "\n".join(
        [
            "---",
            "type: plan",
            f"plan_id: {member_id}",
            f"member_id: {member_id}",
            "---",
            "",
            f"# {member_id} 计划",
            "",
            "## 当前目标",
            "",
            "## 待复查事项",
            "",
            "## 行动步骤",
            "",
            "## 风险提示",
            "",
            "## 关联页面",
            "",
        ]
    )


def _medication_page_content(medication_id: str, display_name: str) -> str:
    return "\n".join(
        [
            "---",
            "type: medication",
            f"medication_id: {medication_id}",
            f"display_name: {display_name}",
            "---",
            "",
            f"# {display_name}",
            "",
            "## 适应证",
            "",
            "## 剂量与频率",
            "",
            "## 漏服规则",
            "",
            "## 常见风险",
            "",
            "## 关联成员",
            "",
            "## 关联来源",
            "",
        ]
    )


def _source_page_line(from_path: Path, source_page_path: Path, label: str | None = None) -> str:
    title = label or source_page_path.stem
    return f"- [{title}]({relative_link(from_path, source_page_path)})"


def _page_line(from_path: Path, target_path: Path, label: str) -> str:
    return f"- [{label}]({relative_link(from_path, target_path)})"


def _append_update_once(
    updates: list[dict[str, Any]], path: Path, target: Path, page_type: str, source_id: str
) -> None:
    resolved_path = str(path.resolve())
    if any(update["path"] == resolved_path for update in updates):
        return
    updates.append(_wiki_update(path, target, page_type, source_id))


def _derive_medication_stub(event: IngestEvent) -> tuple[str, str] | None:
    for attachment in event.attachments:
        if attachment.source_name:
            stem = Path(attachment.source_name).stem
            slug = safe_slug(stem)
            if slug:
                return slug, stem

    if event.payload_text:
        slug = safe_slug(event.payload_text)
        if slug:
            return slug, slug
    return None


def planned_wiki_page_types(event: IngestEvent, source_kind: str) -> list[str]:
    if event.member_id is None:
        return []

    page_types = ["member_page"]
    if source_kind in {"symptom_note", "checkup_report", "lab_result"}:
        page_types.append("plan_page")
    if source_kind == "medication_record" and _derive_medication_stub(event) is not None:
        page_types.append("medication_page")
    return page_types


def apply_wiki_updates(
    target: Path,
    event: IngestEvent,
    source_kind: str,
    source_page_path: Path,
) -> list[dict[str, Any]]:
    if event.member_id is None:
        return []

    updates: list[dict[str, Any]] = []
    member_page = target / "02_wiki" / "members" / f"{safe_slug(event.member_id)}.md"
    ensure_page(member_page, _member_page_content(event.member_id, event.member_hint or event.member_id))

    member_lines = [
        _source_page_line(member_page, source_page_path),
    ]
    if append_lines_under_heading(member_page, "## 来源索引", member_lines):
        _append_update_once(updates, member_page, target, "member_page", event.event_id)

    verification_line = (
        f"- 来源 `{event.event_id}` 仅完成最小归档；具体症状、指标、药物细节仍待人工核实。"
    )
    if append_lines_under_heading(member_page, "## 待核实项", [verification_line]):
        _append_update_once(updates, member_page, target, "member_page", event.event_id)

    if source_kind in {"symptom_note", "checkup_report", "lab_result"}:
        plan_page = target / "02_wiki" / "plans" / f"{safe_slug(event.member_id)}.md"
        ensure_page(plan_page, _plan_page_content(event.member_id))
        summary_map = {
            "symptom_note": "症状来源待继续人工核对，必要时补充持续时间、严重度与对应成员。",
            "checkup_report": "体检/报告来源待继续人工核对，必要时补充明确结论与建议。",
            "lab_result": "化验来源待继续人工核对，必要时补充指标、单位与参考区间。",
        }
        plan_line = (
            f"- [ ] {summary_map[source_kind]} 参考 [{source_page_path.stem}]"
            f"({relative_link(plan_page, source_page_path)})。"
        )
        changed = False
        changed = append_lines_under_heading(plan_page, "## 待复查事项", [plan_line]) or changed
        changed = append_lines_under_heading(
            plan_page,
            "## 关联页面",
            [_source_page_line(plan_page, source_page_path)],
        ) or changed
        if changed:
            _append_update_once(updates, plan_page, target, "plan_page", event.event_id)

        if append_lines_under_heading(
            member_page,
            "## 当前计划",
            [_page_line(member_page, plan_page, f"{event.member_id} 计划")],
        ):
            _append_update_once(updates, member_page, target, "member_page", event.event_id)

    if source_kind == "medication_record":
        medication_stub = _derive_medication_stub(event)
        if medication_stub is not None:
            medication_id, display_name = medication_stub
            medication_page = target / "02_wiki" / "medications" / f"{medication_id}.md"
            ensure_page(medication_page, _medication_page_content(medication_id, display_name))
            changed = False
            changed = append_lines_under_heading(
                medication_page,
                "## 适应证",
                ["- 当前仅保留来源占位，暂不推断适应证。"],
            ) or changed
            changed = append_lines_under_heading(
                medication_page,
                "## 剂量与频率",
                ["- 当前仅识别到药品记录/照片，剂量与频率待人工核实。"],
            ) or changed
            changed = append_lines_under_heading(
                medication_page,
                "## 常见风险",
                ["- 当前不写入药理或风险细节，避免误导。"],
            ) or changed
            changed = append_lines_under_heading(
                medication_page,
                "## 关联成员",
                [_page_line(medication_page, member_page, event.member_id)],
            ) or changed
            changed = append_lines_under_heading(
                medication_page,
                "## 关联来源",
                [_source_page_line(medication_page, source_page_path)],
            ) or changed
            if changed:
                _append_update_once(
                    updates, medication_page, target, "medication_page", event.event_id
                )

            if append_lines_under_heading(
                member_page,
                "## 当前用药",
                [
                    (
                        f"- [{display_name}]({relative_link(member_page, medication_page)})"
                        f"（来自 [{source_page_path.stem}]({relative_link(member_page, source_page_path)})；"
                        "名称/剂量待核实）"
                    )
                ],
            ):
                _append_update_once(updates, member_page, target, "member_page", event.event_id)

    return updates
