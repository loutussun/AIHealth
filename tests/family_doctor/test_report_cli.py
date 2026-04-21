import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "scripts" / "family_doctor" / "run_report.py"


def test_run_report_prints_success_json_to_stdout(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "report-checkup-update.json"
    assert run_bootstrap(target).returncode == 0

    result = subprocess.run(
        [
            sys.executable,
            str(REPORT),
            "--event",
            str(event),
            "--target",
            str(target),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["route"] == "report"
    assert payload["artifacts"]
    assert result.stderr == ""


def test_run_report_returns_non_zero_and_stderr_for_missing_event(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    missing_event = tmp_path / "missing-report-event.json"
    assert run_bootstrap(target).returncode == 0

    result = subprocess.run(
        [
            sys.executable,
            str(REPORT),
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
