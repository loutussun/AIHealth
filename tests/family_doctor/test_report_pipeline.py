import json
from pathlib import Path

import pytest

from family_doctor.report_pipeline import ReportError, load_report_event, run_report_pipeline
from family_doctor.report_templates import output_subdir_for


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def _materialize_event(tmp_path: Path, source_name: str, **overrides: object) -> Path:
    raw_event = json.loads(_event_path(source_name).read_text(encoding="utf-8"))
    for key, value in overrides.items():
        if key in {"target", "payload"}:
            raw_event[key].update(value)
        else:
            raw_event[key] = value

    event_path = tmp_path / source_name
    event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")
    return event_path


def test_load_report_event_accepts_member_target_contract():
    event = load_report_event(_event_path("report-checkup-update.json"))

    assert event.event_type == "report"
    assert event.report_kind == "checkup_update"
    assert event.member_id == "dad"
    assert event.member_scope is None
    assert event.period_start == "2026-04-01"
    assert event.period_end == "2026-04-21"
    assert event.runtime_related_id == "runtime_query_checkup_001"


def test_load_report_event_accepts_family_scope_contract():
    event = load_report_event(_event_path("report-weekly-health.json"))

    assert event.event_type == "report"
    assert event.report_kind == "weekly_health_report"
    assert event.member_id is None
    assert event.member_scope == "family"
    assert event.runtime_related_id is None


def test_load_report_event_rejects_missing_member_target_and_scope(tmp_path):
    event_path = _materialize_event(
        tmp_path,
        "report-weekly-health.json",
        target={"member_id": None},
        payload={"member_scope": None},
    )

    with pytest.raises(
        ReportError, match="target.member_id or payload.member_scope"
    ):
        load_report_event(event_path)


@pytest.mark.parametrize(
    ("source_name", "report_kind"),
    [
        ("report-checkup-update.json", "checkup_update"),
        ("report-checkup-update.json", "lab_update"),
        ("report-weekly-health.json", "weekly_health_report"),
        ("report-monthly-health.json", "monthly_health_report"),
    ],
)
def test_report_pipeline_writes_minimal_output_page_for_supported_report_kinds(
    run_bootstrap,
    tmp_path,
    source_name,
    report_kind,
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    event_path = _materialize_event(tmp_path, source_name, payload={"report_kind": report_kind})

    event = load_report_event(event_path)

    assert event.report_kind == report_kind

    result = run_report_pipeline(event_path, target)
    output_id = result["artifacts"][0]["output_id"]

    output_path = (
        target
        / "03_outputs"
        / output_subdir_for(report_kind)
        / f"{output_id}.md"
    )

    assert result["status"] == "ok"
    assert result["route"] == "report"
    assert output_path.exists()
    assert result["artifacts"] == [
        {
            "artifact_type": "output_page",
            "path": str(output_path.resolve()),
            "relative_path": output_path.relative_to(target).as_posix(),
            "output_id": output_id,
            "output_kind": report_kind,
        }
    ]
    assert result["wiki_updates"] == []
    assert result["followup_suggestions"] == []


def test_report_pipeline_writes_report_job_runtime_contract(
    run_bootstrap,
    tmp_path,
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    event = load_report_event(_event_path("report-checkup-update.json"))

    result = run_report_pipeline(_event_path("report-checkup-update.json"), target)
    runtime_path = (
        target
        / "99_runtime"
        / "jobs"
        / "report_job_evt_report_checkup_update_001-60bf5767dc.json"
    )

    assert runtime_path.exists()
    runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))

    assert runtime_payload["entity_type"] == "report_job"
    assert runtime_payload["job_id"] == "report_job_evt_report_checkup_update_001-60bf5767dc"
    assert runtime_payload["event_id"] == event.event_id
    assert runtime_payload["status"] == "committed"
    assert runtime_payload["phase"] == "committed"
    assert runtime_payload["report_kind"] == "checkup_update"
    assert runtime_payload["member_id"] == "dad"
    assert runtime_payload["member_scope"] is None
    assert runtime_payload["source_refs"] == ["source:evt_checkup_report_001"]
    assert set(runtime_payload["planned_writes"]) == {"report_job", "output_page"}
    assert set(runtime_payload["completed_writes"]) == {"report_job", "output_page"}
    assert any(
        update["entity_type"] == "report_job" and update["status"] == "committed"
        for update in result["runtime_updates"]
    )


def test_report_pipeline_sanitizes_path_like_event_id_for_output_and_runtime_paths(
    run_bootstrap,
    tmp_path,
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    event_path = _materialize_event(
        tmp_path,
        "report-checkup-update.json",
        event_id="../escape/evt:report?unsafe",
    )

    result = run_report_pipeline(event_path, target)

    output_artifact = result["artifacts"][0]
    output_path = Path(output_artifact["path"])
    runtime_update = next(
        update for update in result["runtime_updates"] if update["entity_type"] == "report_job"
    )
    runtime_path = Path(runtime_update["path"])

    assert output_artifact["output_id"] == "out_escape-evt-report-unsafe-d8aacaf9f2"
    assert output_path.exists()
    assert output_path.parent == (target / "03_outputs" / "checkup-updates").resolve()
    assert output_path.name == "out_escape-evt-report-unsafe-d8aacaf9f2.md"
    assert output_path.relative_to((target / "03_outputs").resolve())

    assert runtime_path.exists()
    assert runtime_path.parent == (target / "99_runtime" / "jobs").resolve()
    assert runtime_path.name == "report_job_escape-evt-report-unsafe-d8aacaf9f2.json"
    assert runtime_path.relative_to((target / "99_runtime").resolve())


def test_report_pipeline_avoids_filename_collisions_after_sanitizing_event_id(
    run_bootstrap,
    tmp_path,
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()

    first_event_path = _materialize_event(
        first_dir,
        "report-checkup-update.json",
        event_id="a",
    )
    second_event_path = _materialize_event(
        second_dir,
        "report-checkup-update.json",
        event_id="../a",
    )

    first_result = run_report_pipeline(first_event_path, target)
    second_result = run_report_pipeline(second_event_path, target)

    first_output = Path(first_result["artifacts"][0]["path"])
    second_output = Path(second_result["artifacts"][0]["path"])
    first_job = Path(first_result["runtime_updates"][0]["path"])
    second_job = Path(second_result["runtime_updates"][0]["path"])

    assert first_result["artifacts"][0]["output_id"] == "out_a-ca978112ca"
    assert second_result["artifacts"][0]["output_id"] == "out_a-61b4c98bfb"
    assert first_output != second_output
    assert second_job != first_job
    assert first_output.exists()
    assert second_output.exists()
    assert first_job.exists()
    assert second_job.exists()


def test_report_pipeline_preserves_traceable_contract_in_written_output(
    run_bootstrap,
    tmp_path,
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    event = load_report_event(_event_path("report-checkup-update.json"))

    assert event.source_refs == ("source:evt_checkup_report_001",)
    assert event.member_id == "dad"
    assert event.period_start == "2026-04-01"
    assert event.period_end == "2026-04-21"
    assert event.runtime_related_id == "runtime_query_checkup_001"

    result = run_report_pipeline(_event_path("report-checkup-update.json"), target)
    output_path = (
        target
        / "03_outputs"
        / "checkup-updates"
        / "out_evt_report_checkup_update_001-60bf5767dc.md"
    )
    content = output_path.read_text(encoding="utf-8")

    assert result["status"] == "ok"
    assert "output_id: out_evt_report_checkup_update_001-60bf5767dc" in content
    assert "output_kind: checkup_update" in content
    assert "member_id: dad" in content
    assert "period_start: 2026-04-01" in content
    assert "period_end: 2026-04-21" in content
    assert "related_runtime_id: runtime_query_checkup_001" in content
    assert "wiki_writeback_policy: long_term_only" in content
    assert "  - source:evt_checkup_report_001" in content
