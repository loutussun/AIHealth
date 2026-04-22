from __future__ import annotations

import json
from pathlib import Path

import pytest

from family_doctor import skill_router


def _write_event(tmp_path: Path, payload: dict[str, object], name: str = "event.json") -> Path:
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


def test_run_skill_router_dispatches_query_without_target(tmp_path, monkeypatch):
    event_path = _write_event(tmp_path, _base_event("query", with_target=False))
    called: dict[str, object] = {}

    def fake_query_pipeline(received_event_path: Path) -> dict[str, object]:
        called["event_path"] = received_event_path
        return {"status": "ok", "route": "query"}

    monkeypatch.setattr(skill_router, "run_query_pipeline", fake_query_pipeline)

    result = skill_router.run_skill_router(event_path)

    assert result == {"status": "ok", "route": "query"}
    assert called["event_path"] == event_path


def test_run_skill_router_dispatches_ingest_with_target(tmp_path, monkeypatch):
    event_path = _write_event(tmp_path, _base_event("ingest"))
    called: dict[str, object] = {}

    def fake_ingest_pipeline(received_event_path: Path, received_target: Path) -> dict[str, object]:
        called["event_path"] = received_event_path
        called["target"] = received_target
        return {"status": "ok", "route": "ingest"}

    monkeypatch.setattr(skill_router, "run_ingest_pipeline", fake_ingest_pipeline)

    target = tmp_path / "vault-root"
    result = skill_router.run_skill_router(event_path, target)

    assert result == {"status": "ok", "route": "ingest"}
    assert called["event_path"] == event_path
    assert called["target"] == target


def test_run_skill_router_dispatches_report_with_target(tmp_path, monkeypatch):
    event_path = _write_event(tmp_path, _base_event("report"))
    called: dict[str, object] = {}

    def fake_report_pipeline(received_event_path: Path, received_target: Path) -> dict[str, object]:
        called["event_path"] = received_event_path
        called["target"] = received_target
        return {"status": "ok", "route": "report"}

    monkeypatch.setattr(skill_router, "run_report_pipeline", fake_report_pipeline)

    target = tmp_path / "vault-root"
    result = skill_router.run_skill_router(event_path, target)

    assert result == {"status": "ok", "route": "report"}
    assert called["event_path"] == event_path
    assert called["target"] == target


def test_run_skill_router_dispatches_reminder_with_target(tmp_path, monkeypatch):
    event_path = _write_event(tmp_path, _base_event("reminder"))
    called: dict[str, object] = {}

    def fake_reminder_pipeline(received_event_path: Path, received_target: Path) -> dict[str, object]:
        called["event_path"] = received_event_path
        called["target"] = received_target
        return {"status": "ok", "route": "reminder"}

    monkeypatch.setattr(skill_router, "run_reminder_pipeline", fake_reminder_pipeline)

    target = tmp_path / "vault-root"
    result = skill_router.run_skill_router(event_path, target)

    assert result == {"status": "ok", "route": "reminder"}
    assert called["event_path"] == event_path
    assert called["target"] == target


@pytest.mark.parametrize(
    ("event_payload", "expected_route", "expected_message"),
    [
        (
            {"event_type": "unsupported", "target": {"member_id": "mom"}},
            "unsupported",
            "unsupported event_type: unsupported",
        ),
        (
            {"target": {"member_id": "mom"}},
            "unknown",
            "missing event_type",
        ),
    ],
)
def test_run_skill_router_returns_structured_error_for_invalid_event_type(
    tmp_path,
    event_payload,
    expected_route,
    expected_message,
):
    event_path = _write_event(tmp_path, event_payload)

    result = skill_router.run_skill_router(event_path)

    assert result["status"] == "error"
    assert result["route"] == expected_route
    assert result["summary"] == "family-doctor skill dispatch failed"
    assert result["user_facing_message"] == expected_message
    assert result["artifacts"] == []
    assert result["wiki_updates"] == []
    assert result["runtime_updates"] == []
    assert result["evidence_refs"] == []
    assert result["followup_suggestions"] == []


@pytest.mark.parametrize("event_type", ["ingest", "report", "reminder"])
def test_run_skill_router_returns_structured_error_when_target_is_missing(tmp_path, event_type):
    event_path = _write_event(tmp_path, _base_event(event_type, with_target=False))

    result = skill_router.run_skill_router(event_path)

    assert result["status"] == "error"
    assert result["route"] == event_type
    assert result["summary"] == "family-doctor skill dispatch failed"
    assert result["user_facing_message"] == "missing target for route: " + event_type
    assert result["artifacts"] == []
    assert result["wiki_updates"] == []
    assert result["runtime_updates"] == []
    assert result["evidence_refs"] == []
    assert result["followup_suggestions"] == []


def test_run_skill_router_returns_structured_error_for_invalid_json(tmp_path):
    event_path = tmp_path / "broken.json"
    event_path.write_text("{", encoding="utf-8")

    result = skill_router.run_skill_router(event_path)

    assert result["status"] == "error"
    assert result["route"] == "unknown"
    assert result["summary"] == "family-doctor skill dispatch failed"
    assert result["user_facing_message"] == "invalid JSON in event file"
    assert result["artifacts"] == []
    assert result["wiki_updates"] == []
    assert result["runtime_updates"] == []
    assert result["evidence_refs"] == []
    assert result["followup_suggestions"] == []
