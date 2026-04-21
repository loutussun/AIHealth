from __future__ import annotations

from dataclasses import dataclass


REPORT_OUTPUT_DIRS = {
    "checkup_update": "checkup-updates",
    "lab_update": "checkup-updates",
    "weekly_health_report": "weekly-reports",
    "monthly_health_report": "monthly-reports",
}


@dataclass(frozen=True)
class ReportTemplateContext:
    output_id: str
    report_kind: str
    member_id: str | None
    member_scope: str | None
    period_start: str
    period_end: str
    related_runtime_id: str | None
    source_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]


def output_subdir_for(report_kind: str) -> str:
    try:
        return REPORT_OUTPUT_DIRS[report_kind]
    except KeyError as exc:
        raise ValueError(f"unsupported report_kind: {report_kind}") from exc
