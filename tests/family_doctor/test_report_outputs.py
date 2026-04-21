import json
from pathlib import Path

import pytest

from family_doctor.output_pages import build_report_output_markdown
from family_doctor.report_pipeline import load_report_event
from family_doctor.report_templates import ReportTemplateContext, output_subdir_for


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def _context_from_event(name: str) -> ReportTemplateContext:
    event = load_report_event(_event_path(name))
    return ReportTemplateContext(
        output_id=f"out_{event.event_id}",
        report_kind=event.report_kind,
        member_id=event.member_id,
        member_scope=event.member_scope,
        period_start=event.period_start,
        period_end=event.period_end,
        related_runtime_id=event.runtime_related_id,
        source_refs=event.source_refs,
        evidence_refs=("source:evt_stub_evidence_001",),
    )


def _frontmatter(content: str) -> list[str]:
    lines = content.splitlines()
    assert lines[0] == "---"

    closing_index = lines.index("---", 1)
    return lines[1:closing_index]


def test_report_output_template_frontmatter_tracks_scope_period_and_traceability():
    content = build_report_output_markdown(_context_from_event("report-weekly-health.json"))
    frontmatter = _frontmatter(content)

    assert "type: output" in frontmatter
    assert "output_kind: weekly_health_report" in frontmatter
    assert "member_id: null" in frontmatter
    assert "member_scope: family" in frontmatter
    assert "period_start: 2026-04-14" in frontmatter
    assert "period_end: 2026-04-20" in frontmatter
    assert "related_runtime_id: null" in frontmatter
    assert "wiki_writeback_policy: long_term_only" in frontmatter
    assert "source_refs:" in frontmatter
    assert "  - trend:blood_pressure_week_2026_w16" in frontmatter
    assert "  - source:evt_bp_followup_001" in frontmatter
    assert "evidence_refs:" in frontmatter
    assert "  - source:evt_stub_evidence_001" in frontmatter


def test_report_output_template_frontmatter_tracks_member_id_without_polluting_source_refs():
    content = build_report_output_markdown(_context_from_event("report-checkup-update.json"))
    frontmatter = _frontmatter(content)

    assert "output_kind: checkup_update" in frontmatter
    assert "member_id: dad" in frontmatter
    assert "member_scope: null" in frontmatter
    assert "related_runtime_id: runtime_query_checkup_001" in frontmatter
    assert "source_refs:" in frontmatter
    assert "  - source:evt_checkup_report_001" in frontmatter
    assert "member:dad" not in content


def test_report_output_template_keeps_empty_refs_empty_without_fake_pending_entries():
    context = ReportTemplateContext(
        output_id="out_empty_refs",
        report_kind="weekly_health_report",
        member_id=None,
        member_scope="family",
        period_start="2026-04-14",
        period_end="2026-04-20",
        related_runtime_id=None,
        source_refs=(),
        evidence_refs=(),
    )

    content = build_report_output_markdown(context)
    frontmatter = _frontmatter(content)

    assert "source_refs:" in frontmatter
    assert "evidence_refs:" in frontmatter
    assert "  - pending" not in frontmatter


@pytest.mark.parametrize(
    "report_kind",
    [
        "checkup_update",
        "lab_update",
        "weekly_health_report",
        "monthly_health_report",
    ],
)
def test_output_subdir_mapping_stays_within_03_outputs_contract(report_kind: str):
    output_path = Path("03_outputs") / output_subdir_for(report_kind)

    assert output_path.parts[0] == "03_outputs"
    assert output_path.parts[1]
    assert output_path.parts[1] not in {".", ".."}


def test_report_event_fixtures_remain_json_serializable():
    for name in (
        "report-checkup-update.json",
        "report-weekly-health.json",
        "report-monthly-health.json",
    ):
        raw = json.loads(_event_path(name).read_text(encoding="utf-8"))
        assert raw["event_type"] == "report"
