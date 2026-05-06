from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUN_SKILL = ROOT / "scripts" / "family_doctor" / "run_skill.py"


def _write_event(tmp_path: Path, payload: dict[str, object], name: str) -> Path:
    event_path = tmp_path / name
    event_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return event_path


def _base_event(event_type: str, *, with_target: bool = True) -> dict[str, object]:
    event: dict[str, object] = {
        "event_id": f"evt_{event_type}_001",
        "request_id": f"req_{event_type}_001",
        "idempotency_key": f"idem_{event_type}_001",
        "correlation_id": f"corr_{event_type}_001",
        "event_type": event_type,
        "payload": {},
        "runtime": {},
    }
    if with_target:
        event["target"] = {"member_id": "mom"}
    return event


def test_run_skill_prints_success_json_for_query_without_target(tmp_path):
    event_path = _write_event(tmp_path, _base_event("query", with_target=False), "query.json")

    result = subprocess.run(
        [sys.executable, str(RUN_SKILL), "--event", str(event_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["route"] == "query"
    assert result.stderr == ""


def test_run_skill_prints_success_json_for_ingest_with_target(run_bootstrap, tmp_path):
    event_path = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "checkup-report.json"
    target = tmp_path / "vault-root"
    assert run_bootstrap(target).returncode == 0

    result = subprocess.run(
        [sys.executable, str(RUN_SKILL), "--event", str(event_path), "--target", str(target)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["route"] == "ingest"
    assert result.stderr == ""


@pytest.mark.parametrize("event_type", ["ingest", "report", "reminder"])
def test_run_skill_prints_structured_error_json_for_missing_target(tmp_path, event_type):
    event_path = _write_event(tmp_path, _base_event(event_type), f"{event_type}.json")

    result = subprocess.run(
        [sys.executable, str(RUN_SKILL), "--event", str(event_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["route"] == event_type
    assert payload["user_facing_message"] == f"missing target for route: {event_type}"
    assert result.stderr == ""


def test_run_skill_returns_non_zero_and_stderr_for_missing_event(tmp_path):
    missing_event = tmp_path / "missing-event.json"

    result = subprocess.run(
        [sys.executable, str(RUN_SKILL), "--event", str(missing_event)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert f"error: event file not found: {missing_event}" in result.stderr


def test_run_skill_prints_structured_error_json_for_invalid_json(tmp_path):
    event_path = tmp_path / "broken.json"
    event_path.write_text("{", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(RUN_SKILL), "--event", str(event_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["route"] == "unknown"
    assert payload["user_facing_message"] == "invalid JSON in event file"
    assert result.stderr == ""


def test_run_skill_prints_structured_error_json_for_unsupported_event_type(tmp_path):
    event_path = _write_event(
        tmp_path,
        _base_event("unsupported", with_target=False),
        "unsupported.json",
    )

    result = subprocess.run(
        [sys.executable, str(RUN_SKILL), "--event", str(event_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["route"] == "unsupported"
    assert payload["user_facing_message"] == "unsupported event_type: unsupported"
    assert result.stderr == ""
