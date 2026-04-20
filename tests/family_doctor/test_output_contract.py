from pathlib import Path

from family_doctor.ingest_pipeline import run_ingest_pipeline


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


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

