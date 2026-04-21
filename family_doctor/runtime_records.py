from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from family_doctor.ingest_models import IngestEvent
from family_doctor.raw_archive import _assert_within_root, _safe_name


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _runtime_root(target: Path) -> Path:
    runtime_root = target / "99_runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "jobs").mkdir(parents=True, exist_ok=True)
    (runtime_root / "state").mkdir(parents=True, exist_ok=True)
    return runtime_root


def _job_path(target: Path, event: IngestEvent) -> Path:
    jobs_root = _runtime_root(target) / "jobs"
    filename = f"ingest_job_{_safe_name(event.event_id)}.json"
    return _assert_within_root(jobs_root / filename, jobs_root)


def _state_path(target: Path, prefix: str, event: IngestEvent) -> Path:
    state_root = _runtime_root(target) / "state"
    filename = f"{prefix}_{_safe_name(event.event_id)}.json"
    return _assert_within_root(state_root / filename, state_root)


def _load_existing_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_ingest_job(
    target: Path,
    event: IngestEvent,
    phase: str,
    status: str,
    planned_writes: list[str],
    completed_writes: list[str],
    source_id: str | None,
    recovery_hint: str | None,
) -> Path:
    path = _job_path(target, event)
    existing = _load_existing_json(path) or {}
    created_at = existing.get("created_at") or _utc_now()

    payload: dict[str, Any] = {
        "entity_type": "ingest_job",
        "event_id": event.event_id,
        "request_id": event.request_id,
        "idempotency_key": event.idempotency_key,
        "correlation_id": event.correlation_id,
        "status": status,
        "phase": phase,
        "planned_writes": list(planned_writes),
        "completed_writes": list(completed_writes),
        "recovery_hint": recovery_hint,
        "member_id": event.member_id,
        "source_id": source_id,
        "created_at": created_at,
        "updated_at": _utc_now(),
        "fingerprint": existing.get("fingerprint"),
        "event_type": event.event_type,
        "trigger_mode": event.trigger_mode,
        "dedupe_scope": event.runtime_dedupe_scope,
    }

    return _write_json(path, payload)


def write_review_item(target: Path, event: IngestEvent, reason: str, severity: str) -> Path:
    path = _state_path(target, "review_item", event)
    existing = _load_existing_json(path) or {}
    payload: dict[str, Any] = {
        "entity_type": "review_item",
        "event_id": event.event_id,
        "request_id": event.request_id,
        "idempotency_key": event.idempotency_key,
        "reason": reason,
        "severity": severity,
        "member_id": event.member_id,
        "member_hint": event.member_hint,
        "created_at": existing.get("created_at") or _utc_now(),
        "updated_at": _utc_now(),
    }

    return _write_json(path, payload)


def write_dedupe_record(
    target: Path,
    event: IngestEvent,
    fingerprint: str,
    matched_job_id: str,
) -> Path:
    path = _state_path(target, "dedupe_record", event)
    existing = _load_existing_json(path) or {}
    payload: dict[str, Any] = {
        "entity_type": "dedupe_record",
        "event_id": event.event_id,
        "request_id": event.request_id,
        "idempotency_key": event.idempotency_key,
        "fingerprint": fingerprint,
        "matched_job_id": matched_job_id,
        "member_id": event.member_id,
        "created_at": existing.get("created_at") or _utc_now(),
        "updated_at": _utc_now(),
    }

    return _write_json(path, payload)


def reminder_instance_path(target: Path, runtime_id: str) -> Path:
    state_root = _runtime_root(target) / "state"
    filename = f"reminder_instance_{_safe_name(runtime_id)}.json"
    return _assert_within_root(state_root / filename, state_root)


def write_reminder_instance(target: Path, payload: dict[str, Any]) -> Path:
    runtime_id = payload.get("runtime_id") or payload.get("instance_id")
    if not isinstance(runtime_id, str) or not runtime_id:
        raise ValueError("reminder_instance payload requires runtime_id or instance_id")
    if "runtime_id" not in payload:
        payload = {**payload, "runtime_id": runtime_id}
    return _write_json(reminder_instance_path(target, runtime_id), payload)


def serialise_event(event: IngestEvent) -> dict[str, Any]:
    payload = asdict(event)
    payload["attachments"] = [asdict(attachment) for attachment in event.attachments]
    payload["source_refs"] = list(event.source_refs)
    for attachment in payload["attachments"]:
        attachment["path"] = str(attachment["path"])
    return payload
