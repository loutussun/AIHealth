import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_run_ingest_blocks_low_confidence_member_resolution(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    event = (
        ROOT
        / "tests"
        / "family_doctor"
        / "fixtures"
        / "events"
        / "symptom-note-low-confidence.json"
    )
    assert run_bootstrap(target).returncode == 0

    result = run_ingest(event, target)

    assert result.returncode == 1
    assert "needs_review" in result.stderr.lower()
    assert "low-confidence member match" in result.stderr.lower()
    assert list((target / "99_runtime" / "state").glob("review_item_*.json"))
    job_files = list((target / "99_runtime" / "jobs").glob("ingest_job_*.json"))
    job = json.loads(job_files[0].read_text(encoding="utf-8"))
    assert job["status"] == "pending_review"


def test_run_ingest_is_idempotent_for_same_idempotency_key(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    event = (
        ROOT
        / "tests"
        / "family_doctor"
        / "fixtures"
        / "events"
        / "medication-photo.json"
    )
    assert run_bootstrap(target).returncode == 0

    first = run_ingest(event, target)
    second = run_ingest(event, target)

    assert first.returncode == 0
    assert second.returncode == 0
    assert "deduplicated" in second.stdout.lower()
