from __future__ import annotations

from family_doctor.report_templates import ReportTemplateContext


def build_report_output_markdown(context: ReportTemplateContext) -> str:
    member_value = context.member_id if context.member_id is not None else "null"
    scope_value = context.member_scope if context.member_scope is not None else "null"
    runtime_value = (
        context.related_runtime_id if context.related_runtime_id is not None else "null"
    )
    source_lines = "\n".join(f"  - {ref}" for ref in context.source_refs) or "  - pending"
    evidence_lines = "\n".join(f"  - {ref}" for ref in context.evidence_refs) or "  - pending"

    return "\n".join(
        [
            "---",
            "type: output",
            f"output_id: {context.output_id}",
            f"output_kind: {context.report_kind}",
            f"member_id: {member_value}",
            f"member_scope: {scope_value}",
            f"period_start: {context.period_start}",
            f"period_end: {context.period_end}",
            f"related_runtime_id: {runtime_value}",
            "wiki_writeback_policy: long_term_only",
            "source_refs:",
            source_lines,
            "evidence_refs:",
            evidence_lines,
            "---",
            "",
            "# 报告草稿",
            "",
            "## 结论摘要",
            "待生成。",
            "",
            "## 证据来源",
            "待生成。",
            "",
            "## 关联追踪",
            f"- source_refs_count: {len(context.source_refs)}",
            f"- evidence_refs_count: {len(context.evidence_refs)}",
            f"- member_id: `{member_value}`",
            f"- member_scope: `{scope_value}`",
            f"- related_runtime_id: `{runtime_value}`",
            f"- period: `{context.period_start}` ~ `{context.period_end}`",
            "",
            "## 长期结论候选",
            "- 仅长期有效结论允许后续回写 wiki；本阶段仅锁定 contract，不执行写回。",
            "",
            "## 待核实项",
            "- 待 report pipeline 生成真实内容。",
            "",
        ]
    )
