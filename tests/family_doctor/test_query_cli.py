import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUERY = ROOT / "scripts" / "family_doctor" / "run_query.py"


def test_run_query_prints_success_json_to_stdout(materialize_query_event, tmp_path):
    event_path = materialize_query_event(
        tmp_path,
        question="妈妈现在在吃什么药？",
        intent_hint="current_medications",
    )

    result = subprocess.run(
        [sys.executable, str(QUERY), "--event", str(event_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["route"] == "query"
    assert result.stderr == ""


def test_run_query_returns_non_zero_and_stderr_for_missing_event(tmp_path):
    missing_event = tmp_path / "missing-query-event.json"

    result = subprocess.run(
        [sys.executable, str(QUERY), "--event", str(missing_event)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert "No such file" in result.stderr or "does not exist" in result.stderr
