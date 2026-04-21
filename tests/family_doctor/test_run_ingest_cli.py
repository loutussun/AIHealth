import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INGEST = ROOT / "scripts" / "family_doctor" / "run_ingest.py"


def test_run_ingest_archives_report_and_writes_source_page(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "checkup-report.json"
    assert run_bootstrap(target).returncode == 0

    result = run_ingest(event, target)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["route"] == "ingest"
    assert result.stderr == ""
    assert list((target / "02_wiki" / "sources").glob("*.md"))


def test_run_ingest_reports_errors_to_stderr_for_missing_event(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    missing_event = tmp_path / "missing-event.json"
    assert run_bootstrap(target).returncode == 0

    result = subprocess.run(
        [
            sys.executable,
            str(INGEST),
            "--event",
            str(missing_event),
            "--target",
            str(target),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert "No such file" in result.stderr or "does not exist" in result.stderr
