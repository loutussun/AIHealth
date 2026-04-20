import json
from pathlib import Path

from family_doctor.ingest_pipeline import load_event, run_ingest_pipeline


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def _materialize_event(
    tmp_path: Path,
    source_name: str,
    *,
    event_id: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
    idempotency_key: str | None = None,
) -> Path:
    raw_event = json.loads(_event_path(source_name).read_text(encoding="utf-8"))
    raw_event["event_id"] = event_id
    raw_event["request_id"] = request_id or f"req_{event_id}"
    raw_event["correlation_id"] = correlation_id or f"corr_{event_id}"
    if idempotency_key is not None:
        raw_event["idempotency_key"] = idempotency_key

    event_path = tmp_path / f"{event_id}.json"
    event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")
    return event_path


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


def test_run_ingest_duplicate_of_pending_review_preserves_needs_review(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    first_event = _event_path("symptom-note-low-confidence.json")
    duplicate_event = _materialize_event(
        tmp_path,
        "symptom-note-low-confidence.json",
        event_id="evt_symptom_note_low_confidence_002",
        idempotency_key="idem_symptom_note_low_confidence_001",
    )
    assert run_bootstrap(target).returncode == 0

    first = run_ingest_pipeline(first_event, target)
    second = run_ingest_pipeline(duplicate_event, target)

    assert first["status"] == "needs_review"
    assert second["status"] == "needs_review"
    assert "deduplicated" in second["summary"].lower()

    duplicate_job_path = target / "99_runtime" / "jobs" / "ingest_job_evt_symptom_note_low_confidence_002.json"
    duplicate_job = json.loads(duplicate_job_path.read_text(encoding="utf-8"))
    assert duplicate_job["status"] == "pending_review"
    assert duplicate_job["phase"] == "accepted"
    assert duplicate_job["completed_writes"] == ["ingest_job", "dedupe_record"]

    dedupe_path = target / "99_runtime" / "state" / "dedupe_record_evt_symptom_note_low_confidence_002.json"
    dedupe_record = json.loads(dedupe_path.read_text(encoding="utf-8"))
    assert dedupe_record["matched_job_id"] == "evt_symptom_note_low_confidence_001"


def test_run_ingest_creates_current_job_for_new_event_with_same_idempotency_key(
    run_bootstrap, tmp_path
):
    target = tmp_path / "family-health"
    first_event = _event_path("checkup-report.json")
    duplicate_event = _materialize_event(
        tmp_path,
        "checkup-report.json",
        event_id="evt_checkup_report_002",
        idempotency_key="idem_checkup_report_001",
    )
    assert run_bootstrap(target).returncode == 0

    first = run_ingest_pipeline(first_event, target)
    second = run_ingest_pipeline(duplicate_event, target)

    assert first["status"] == "ok"
    assert second["status"] == "ok"
    assert "deduplicated" in second["summary"].lower()

    job_files = sorted((target / "99_runtime" / "jobs").glob("ingest_job_*.json"))
    assert len(job_files) == 2

    duplicate_job = json.loads(
        (target / "99_runtime" / "jobs" / "ingest_job_evt_checkup_report_002.json").read_text(
            encoding="utf-8"
        )
    )
    assert duplicate_job["status"] == "committed"
    assert duplicate_job["phase"] == "committed"
    assert duplicate_job["completed_writes"] == ["ingest_job", "dedupe_record"]

    dedupe_record = json.loads(
        (target / "99_runtime" / "state" / "dedupe_record_evt_checkup_report_002.json").read_text(
            encoding="utf-8"
        )
    )
    assert dedupe_record["matched_job_id"] == "evt_checkup_report_001"
