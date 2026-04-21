from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from family_doctor.raw_archive import _assert_within_root, _safe_name
from family_doctor.reminder_rules import ReminderRuleError, load_reminder_rule
from family_doctor.reminder_rules import reminder_rule_path_for_member
from family_doctor.reminder_runtime import (
    build_reminder_instance_snapshot,
    load_runtime_instances,
    select_confirmation_instance,
    update_instance_status,
)
from family_doctor.runtime_records import write_reminder_instance


class ReminderError(ValueError):
    """Raised when a reminder event cannot be normalised."""


@dataclass(frozen=True)
class ReminderEvent:
    event_id: str
    event_type: str
    member_id: str
    reminder_action: str
    plan_id: str
    item_id: str
    scheduled_for: str
    runtime_related_id: str | None


def _require_dict(raw: Any, label: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ReminderError(f"{label} must be an object")
    return raw


def _require_str(raw: Any, label: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ReminderError(f"{label} must be a non-empty string")
    return raw


def _require_optional_str(raw: Any, label: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw:
        raise ReminderError(f"{label} must be a non-empty string when provided")
    return raw


def load_reminder_event(path: Path) -> ReminderEvent:
    raw_event = json.loads(path.read_text(encoding="utf-8"))
    event = _require_dict(raw_event, "event")
    target = _require_dict(event.get("target"), "target")
    payload = _require_dict(event.get("payload"), "payload")
    runtime = _require_dict(event.get("runtime"), "runtime")

    event_type = _require_str(event.get("event_type"), "event_type")
    if event_type != "reminder":
        raise ReminderError("event_type must be reminder")

    return ReminderEvent(
        event_id=_require_str(event.get("event_id"), "event_id"),
        event_type=event_type,
        member_id=_require_str(target.get("member_id"), "target.member_id"),
        reminder_action=_require_str(payload.get("reminder_action"), "payload.reminder_action"),
        plan_id=_require_str(payload.get("plan_id"), "payload.plan_id"),
        item_id=_require_str(payload.get("item_id"), "payload.item_id"),
        scheduled_for=_require_str(payload.get("scheduled_for"), "payload.scheduled_for"),
        runtime_related_id=_require_optional_str(
            runtime.get("related_runtime_id"),
            "runtime.related_runtime_id",
        ),
    )


def _absolute_rule_path(target: Path, member_id: str) -> Path:
    return target / reminder_rule_path_for_member(member_id)


def _build_message(action: str, item_id: str, escalation_policy: str | None = None) -> str:
    if action == "generate":
        return f"提醒：请按计划完成 {item_id}。"
    if action == "confirm":
        return f"已确认 {item_id} 的提醒。"
    if action == "escalate":
        return f"升级提醒：{item_id} 未按时确认，按 {escalation_policy} 跟进。"
    raise ReminderError(f"unsupported reminder_action: {action}")


def _write_artifact(target: Path, instance_id: str, message: str) -> Path:
    output_root = target / "03_outputs" / "reminders"
    output_root.mkdir(parents=True, exist_ok=True)
    safe_instance_id = _safe_name(instance_id).replace("..", "-").lstrip(".-") or "reminder"
    safe_instance_id = re.sub(r"-{2,}", "-", safe_instance_id)
    artifact_path = _assert_within_root(output_root / f"{safe_instance_id}.md", output_root)
    artifact_path.write_text(message + "\n", encoding="utf-8")
    return artifact_path.resolve()


def run_reminder_pipeline(event_path: Path, target: Path | None = None) -> dict[str, Any]:
    if target is None:
        raise ReminderError("target is required for reminder pipeline")

    event = load_reminder_event(event_path)
    rule_path = _absolute_rule_path(target, event.member_id)
    try:
        rule = load_reminder_rule(rule_path)
    except ReminderRuleError as exc:
        raise ReminderError(str(exc)) from exc
    if rule.item_id != event.item_id:
        raise ReminderError("reminder rule item_id did not match payload.item_id")

    runtime_updates: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    matched_instance_id: str | None = None
    selected_runtime_id: str | None = None

    if event.reminder_action == "generate":
        snapshot = build_reminder_instance_snapshot(event, status="scheduled")
        reminder_path = write_reminder_instance(target, snapshot).resolve()
        message = _build_message("generate", event.item_id)
        artifact_path = _write_artifact(target, snapshot["instance_id"], message)
        runtime_updates.append(
            {
                "entity_type": "reminder_instance",
                "path": str(reminder_path),
                "status": snapshot["status"],
            }
        )
        artifacts.append(
            {
                "artifact_type": "reminder_message",
                "path": str(artifact_path),
                "instance_id": snapshot["instance_id"],
            }
        )
    elif event.reminder_action in {"confirm", "escalate"}:
        selected_runtime_id = event.runtime_related_id
        selected = select_confirmation_instance(
            load_runtime_instances(target),
            event.runtime_related_id,
        )
        if selected is None:
            raise ReminderError("runtime.related_runtime_id did not match any reminder_instance")
        matched_instance_id = str(selected.get("instance_id") or selected.get("runtime_id"))
        next_status = "confirmed" if event.reminder_action == "confirm" else "escalated"
        message = _build_message(event.reminder_action, event.item_id, rule.escalation_policy)
        updated = update_instance_status(selected, status=next_status, message=message)
        reminder_path = write_reminder_instance(target, updated).resolve()
        artifact_path = _write_artifact(target, matched_instance_id, message)
        runtime_updates.append(
            {
                "entity_type": "reminder_instance",
                "path": str(reminder_path),
                "status": updated["status"],
            }
        )
        artifacts.append(
            {
                "artifact_type": "reminder_message",
                "path": str(artifact_path),
                "instance_id": matched_instance_id,
            }
        )
    else:
        raise ReminderError(f"unsupported reminder_action: {event.reminder_action}")

    result = {
        "route": "reminder",
        "status": "ok",
        "summary": f"processed reminder {event.reminder_action}",
        "event_id": event.event_id,
        "member_id": event.member_id,
        "reminder_action": event.reminder_action,
        "plan_id": event.plan_id,
        "item_id": event.item_id,
        "scheduled_for": event.scheduled_for,
        "runtime": {"related_runtime_id": event.runtime_related_id},
        "rule_path": str(rule_path.resolve()),
        "artifacts": artifacts,
        "runtime_updates": runtime_updates,
        "followup_suggestions": [],
        "confirm_keywords": list(rule.confirm_keywords),
        "escalation_policy": rule.escalation_policy,
    }
    if selected_runtime_id is not None:
        result["selected_runtime_id"] = selected_runtime_id
    if matched_instance_id is not None:
        result["matched_instance_id"] = matched_instance_id
    return result
