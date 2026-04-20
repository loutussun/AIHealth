import json
from pathlib import Path

from family_doctor.ingest_pipeline import run_ingest_pipeline


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def _materialize_event(
    tmp_path: Path,
    source_name: str,
    *,
    event_id: str,
    idempotency_key: str | None = None,
) -> Path:
    raw_event = json.loads(_event_path(source_name).read_text(encoding="utf-8"))
    raw_event["event_id"] = event_id
    raw_event["request_id"] = f"req_{event_id}"
    raw_event["correlation_id"] = f"corr_{event_id}"
    if idempotency_key is not None:
        raw_event["idempotency_key"] = idempotency_key

    event_path = tmp_path / f"{event_id}.json"
    event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")
    return event_path


def _assert_contract(result: dict[str, object]) -> None:
    assert result["route"] == "ingest"
    assert isinstance(result["artifacts"], list)
    assert isinstance(result["wiki_updates"], list)
    assert isinstance(result["runtime_updates"], list)
    assert isinstance(result["evidence_refs"], list)
    assert isinstance(result["followup_suggestions"], list)
    assert isinstance(result["user_facing_message"], str)
    assert isinstance(result["summary"], str)


def test_ingest_pipeline_returns_ok_output_contract(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(_event_path("checkup-report.json"), target)

    assert result["status"] == "ok"
    _assert_contract(result)


def test_ingest_pipeline_returns_needs_review_output_contract(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(_event_path("symptom-note-low-confidence.json"), target)

    assert result["status"] == "needs_review"
    _assert_contract(result)
    assert "low-confidence member match" in result["summary"].lower()


def test_ingest_pipeline_duplicate_pending_review_keeps_needs_review_contract(
    run_bootstrap, tmp_path
):
    target = tmp_path / "family-health"
    duplicate_event = _materialize_event(
        tmp_path,
        "symptom-note-low-confidence.json",
        event_id="evt_symptom_note_low_confidence_002",
        idempotency_key="idem_symptom_note_low_confidence_001",
    )
    assert run_bootstrap(target).returncode == 0

    run_ingest_pipeline(_event_path("symptom-note-low-confidence.json"), target)
    result = run_ingest_pipeline(duplicate_event, target)

    assert result["status"] == "needs_review"
    _assert_contract(result)
    assert "deduplicated" in result["summary"].lower()
    assert any(update["status"] == "pending_review" for update in result["runtime_updates"])
