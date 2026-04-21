from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALID_REMINDER_STATUSES = {
    "scheduled",
    "sent",
    "confirmed",
    "escalated",
    "expired",
}


@dataclass(frozen=True)
class ReminderInstance:
    instance_id: str
    plan_id: str
    item_id: str
    member_id: str
    scheduled_for: str
    status: str
    related_runtime_id: str | None


def _instance_id_for_event(event: Any) -> str:
    event_id = getattr(event, "event_id", "")
    if isinstance(event_id, str) and event_id.startswith("evt_"):
        return f"runtime_{event_id.removeprefix('evt_')}"
    return f"runtime_{getattr(event, 'plan_id')}:{getattr(event, 'item_id')}"


def _require_valid_status(status: str) -> str:
    if status not in VALID_REMINDER_STATUSES:
        raise ValueError(f"unsupported reminder status: {status}")
    return status


def build_reminder_instance_snapshot(event: Any, *, status: str = "scheduled") -> dict[str, Any]:
    instance_id = _instance_id_for_event(event)
    resolved_status = _require_valid_status(status)
    return {
        "entity_type": "reminder_instance",
        "runtime_id": instance_id,
        "instance_id": instance_id,
        "plan_id": event.plan_id,
        "item_id": event.item_id,
        "member_id": event.member_id,
        "scheduled_for": event.scheduled_for,
        "status": resolved_status,
        "related_runtime_id": event.runtime_related_id or instance_id,
        "planned_writes": ["reminder_instance"],
        "completed_writes": ["reminder_instance"],
    }


def select_confirmation_instance(
    instances: list[dict[str, Any]],
    related_runtime_id: str | None,
) -> dict[str, Any] | None:
    if not instances or not related_runtime_id:
        return None
    for instance in instances:
        if instance.get("instance_id") == related_runtime_id:
            return instance
        if instance.get("runtime_id") == related_runtime_id:
            return instance
    return None


def update_instance_status(
    instance: dict[str, Any],
    *,
    status: str,
    message: str,
) -> dict[str, Any]:
    resolved_status = _require_valid_status(status)
    updated = dict(instance)
    updated["status"] = resolved_status
    updated["message"] = message
    return updated


def load_runtime_instances(target: Path) -> list[dict[str, Any]]:
    state_root = target / "99_runtime" / "state"
    if not state_root.exists():
        return []
    instances: list[dict[str, Any]] = []
    for path in sorted(state_root.glob("reminder_instance_*.json")):
        instances.append(__import__("json").loads(path.read_text(encoding="utf-8")))
    return instances
