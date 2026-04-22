from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from family_doctor.ingest_pipeline import run_ingest_pipeline
from family_doctor.query_pipeline import run_query_pipeline
from family_doctor.reminder_pipeline import run_reminder_pipeline
from family_doctor.report_pipeline import run_report_pipeline


SUPPORTED_EVENT_TYPES = {"ingest", "query", "report", "reminder"}
REQUIRED_TARGET_ROUTES = {"ingest", "report", "reminder"}


def _empty_error_lists() -> dict[str, list[Any]]:
    return {
        "artifacts": [],
        "wiki_updates": [],
        "runtime_updates": [],
        "evidence_refs": [],
        "followup_suggestions": [],
    }


def _structured_error(route: str, user_facing_message: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "error",
        "route": route,
        "summary": "family-doctor skill dispatch failed",
        "user_facing_message": user_facing_message,
    }
    payload.update(_empty_error_lists())
    return payload


def _load_event_payload(event_path: Path) -> dict[str, Any]:
    raw_text = event_path.read_text(encoding="utf-8")
    raw_event = json.loads(raw_text)
    if not isinstance(raw_event, dict):
        raise ValueError("event must be a JSON object")
    return raw_event


def load_skill_event_type(event_path: Path) -> str:
    event = _load_event_payload(event_path)
    event_type = event.get("event_type")
    if not isinstance(event_type, str) or not event_type:
        raise ValueError("missing event_type")
    return event_type


def run_skill_router(event_path: Path, target: Path | None = None) -> dict[str, Any]:
    route = "unknown"
    try:
        event = _load_event_payload(event_path)
        event_type = event.get("event_type")
        if not isinstance(event_type, str) or not event_type:
            return _structured_error(route, "missing event_type")

        route = event_type
        if event_type not in SUPPORTED_EVENT_TYPES:
            return _structured_error(route, f"unsupported event_type: {event_type}")

        if event_type in REQUIRED_TARGET_ROUTES and target is None:
            return _structured_error(route, f"missing target for route: {event_type}")

        dispatch_table = {
            "ingest": lambda: run_ingest_pipeline(event_path, target),
            "query": lambda: run_query_pipeline(event_path),
            "report": lambda: run_report_pipeline(event_path, target),
            "reminder": lambda: run_reminder_pipeline(event_path, target),
        }
        try:
            return dispatch_table[event_type]()
        except Exception as exc:
            return _structured_error(route, str(exc))
    except FileNotFoundError:
        return _structured_error(route, f"event file not found: {event_path}")
    except json.JSONDecodeError:
        return _structured_error(route, "invalid JSON in event file")
    except Exception as exc:
        return _structured_error(route, str(exc))
