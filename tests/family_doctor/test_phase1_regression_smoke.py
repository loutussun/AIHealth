import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_phase1_ingest_cli_and_validation_baseline_still_hold(
    run_bootstrap,
    run_ingest,
    run_validate,
    tmp_path,
):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "checkup-report.json"

    bootstrap = run_bootstrap(target)
    assert bootstrap.returncode == 0
    assert bootstrap.stderr == ""

    ingest = run_ingest(event, target)
    assert ingest.returncode == 0
    payload = json.loads(ingest.stdout)
    assert payload["status"] == "ok"
    assert payload["route"] == "ingest"
    assert ingest.stderr == ""
    assert list((target / "02_wiki" / "sources").glob("*.md"))
    assert list((target / "99_runtime" / "jobs").glob("ingest_job_*.json"))
    assert any(artifact["artifact_type"] == "raw_archive" for artifact in payload["artifacts"])

    validate = run_validate(target)
    assert validate.returncode == 0
    assert "Phase 0 validation passed" in validate.stdout
    assert validate.stderr == ""
