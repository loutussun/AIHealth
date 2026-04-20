import json
from pathlib import Path

from family_doctor.ingest_pipeline import (
    derive_dedupe_fingerprint,
    load_event,
    run_ingest_pipeline,
)
from family_doctor.runtime_records import write_ingest_job


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
    assert job["phase"] == "wrote_source"


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
    assert duplicate_job["phase"] == "wrote_source"
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


def test_run_ingest_same_idempotency_key_but_different_fingerprint_does_not_dedupe(
    run_bootstrap, tmp_path
):
    target = tmp_path / "family-health"
    shared_idempotency_key = "idem_shared_ingest_001"
    first_event = _materialize_event(
        tmp_path,
        "checkup-report.json",
        event_id="evt_checkup_report_shared_001",
        idempotency_key=shared_idempotency_key,
    )
    second_event = _materialize_event(
        tmp_path,
        "medication-photo.json",
        event_id="evt_medication_photo_shared_001",
        idempotency_key=shared_idempotency_key,
    )
    assert run_bootstrap(target).returncode == 0

    first = run_ingest_pipeline(first_event, target)
    second = run_ingest_pipeline(second_event, target)

    assert first["status"] == "ok"
    assert second["status"] == "ok"
    assert "deduplicated" not in second["summary"].lower()
    assert len(list((target / "99_runtime" / "jobs").glob("ingest_job_*.json"))) == 2
    assert len(list((target / "99_runtime" / "state").glob("dedupe_record_*.json"))) == 0

    second_job = json.loads(
        (target / "99_runtime" / "jobs" / "ingest_job_evt_medication_photo_shared_001.json").read_text(
            encoding="utf-8"
        )
    )
    assert second_job["status"] == "committed"
    assert second_job["phase"] == "committed"


def test_run_ingest_duplicate_of_processing_job_stays_in_flight(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    first_event_path = _materialize_event(
        tmp_path,
        "checkup-report.json",
        event_id="evt_checkup_report_processing_001",
    )
    duplicate_event_path = _materialize_event(
        tmp_path,
        "checkup-report.json",
        event_id="evt_checkup_report_processing_002",
    )
    assert run_bootstrap(target).returncode == 0

    first_event = load_event(first_event_path)
    first_job = write_ingest_job(
        target=target,
        event=first_event,
        phase="accepted",
        status="processing",
        planned_writes=["ingest_job", "review_item"],
        completed_writes=["ingest_job"],
        source_id=first_event.event_id,
        recovery_hint="resume from accepted phase",
    )
    first_job_payload = json.loads(first_job.read_text(encoding="utf-8"))
    first_job_payload["fingerprint"] = derive_dedupe_fingerprint(first_event)
    first_job.write_text(json.dumps(first_job_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_ingest_pipeline(duplicate_event_path, target)

    assert result["status"] == "ok"
    assert "deduplicated" in result["summary"].lower()
    assert "still processing" in result["summary"].lower()

    duplicate_job = json.loads(
        (target / "99_runtime" / "jobs" / "ingest_job_evt_checkup_report_processing_002.json").read_text(
            encoding="utf-8"
        )
    )
    assert duplicate_job["status"] == "processing"
    assert duplicate_job["phase"] == "accepted"
    assert duplicate_job["completed_writes"] == ["ingest_job", "dedupe_record"]

    persisted_first_job = json.loads(first_job.read_text(encoding="utf-8"))
    assert persisted_first_job["status"] == "processing"
    assert persisted_first_job["phase"] == "accepted"


def test_run_ingest_duplicate_of_created_job_stays_in_flight(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    first_event_path = _materialize_event(
        tmp_path,
        "checkup-report.json",
        event_id="evt_checkup_report_created_001",
    )
    duplicate_event_path = _materialize_event(
        tmp_path,
        "checkup-report.json",
        event_id="evt_checkup_report_created_002",
    )
    assert run_bootstrap(target).returncode == 0

    first_event = load_event(first_event_path)
    first_job = write_ingest_job(
        target=target,
        event=first_event,
        phase="accepted",
        status="created",
        planned_writes=["ingest_job", "review_item"],
        completed_writes=["ingest_job"],
        source_id=first_event.event_id,
        recovery_hint="resume from accepted phase",
    )
    first_job_payload = json.loads(first_job.read_text(encoding="utf-8"))
    first_job_payload["fingerprint"] = derive_dedupe_fingerprint(first_event)
    first_job.write_text(json.dumps(first_job_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_ingest_pipeline(duplicate_event_path, target)

    assert result["status"] == "ok"
    assert "deduplicated" in result["summary"].lower()
    assert "still created" in result["summary"].lower()

    duplicate_job = json.loads(
        (target / "99_runtime" / "jobs" / "ingest_job_evt_checkup_report_created_002.json").read_text(
            encoding="utf-8"
        )
    )
    assert duplicate_job["status"] == "created"
    assert duplicate_job["phase"] == "accepted"
    assert duplicate_job["completed_writes"] == ["ingest_job", "dedupe_record"]


def test_run_ingest_duplicate_of_failed_job_returns_error(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    first_event_path = _materialize_event(
        tmp_path,
        "checkup-report.json",
        event_id="evt_checkup_report_failed_001",
    )
    duplicate_event_path = _materialize_event(
        tmp_path,
        "checkup-report.json",
        event_id="evt_checkup_report_failed_002",
    )
    assert run_bootstrap(target).returncode == 0

    first_event = load_event(first_event_path)
    first_job = write_ingest_job(
        target=target,
        event=first_event,
        phase="accepted",
        status="failed",
        planned_writes=["ingest_job", "review_item"],
        completed_writes=["ingest_job"],
        source_id=first_event.event_id,
        recovery_hint="inspect failure before retry",
    )
    first_job_payload = json.loads(first_job.read_text(encoding="utf-8"))
    first_job_payload["fingerprint"] = derive_dedupe_fingerprint(first_event)
    first_job.write_text(json.dumps(first_job_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_ingest_pipeline(duplicate_event_path, target)

    assert result["status"] == "error"
    assert "deduplicated" in result["summary"].lower()
    assert "not in a reusable success state" in result["summary"].lower()

    duplicate_job = json.loads(
        (target / "99_runtime" / "jobs" / "ingest_job_evt_checkup_report_failed_002.json").read_text(
            encoding="utf-8"
        )
    )
    assert duplicate_job["status"] == "failed"
    assert duplicate_job["phase"] == "accepted"
    assert duplicate_job["completed_writes"] == ["ingest_job", "dedupe_record"]
