import json
from pathlib import Path

from family_doctor.ingest_pipeline import load_event, run_ingest_pipeline


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def test_load_event_normalizes_full_input_contract():
    event = load_event(_event_path("checkup-report.json"))

    assert event.event_id == "evt_checkup_report_001"
    assert event.request_id == "req_checkup_report_001"
    assert event.member_id == "dad"
    assert event.runtime_dedupe_scope == "family-health"
    assert event.attachments[0].path.is_absolute()
    assert event.attachments[0].source_name == "checkup-report.txt"


def test_run_ingest_blocks_low_confidence_member_resolution(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    event = _event_path("symptom-note-low-confidence.json")
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(event, target)

    assert result["status"] == "needs_review"
    assert "low-confidence member match" in result["summary"].lower()
    assert list((target / "99_runtime" / "state").glob("review_item_*.json"))
    job_files = list((target / "99_runtime" / "jobs").glob("ingest_job_*.json"))
    assert len(job_files) == 1
    job = json.loads(job_files[0].read_text(encoding="utf-8"))
    assert job["status"] == "pending_review"
    assert job["phase"] == "accepted"


def test_run_ingest_is_idempotent_for_same_idempotency_key(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    event = _event_path("medication-photo.json")
    assert run_bootstrap(target).returncode == 0

    first = run_ingest_pipeline(event, target)
    second = run_ingest_pipeline(event, target)

    assert first["status"] == "ok"
    assert second["status"] == "ok"
    assert "deduplicated" in second["summary"].lower()
    assert len(list((target / "99_runtime" / "jobs").glob("ingest_job_*.json"))) == 1
    assert len(list((target / "99_runtime" / "state").glob("dedupe_record_*.json"))) == 1

