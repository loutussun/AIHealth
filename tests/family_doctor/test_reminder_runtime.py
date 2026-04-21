from __future__ import annotations

import json
from pathlib import Path

from family_doctor.reminder_pipeline import load_reminder_event
from family_doctor.reminder_runtime import (
    ReminderInstance,
    build_reminder_instance_snapshot,
    select_confirmation_instance,
)


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def test_reminder_instance_contract_contains_the_minimal_runtime_fields():
    assert tuple(ReminderInstance.__dataclass_fields__) == (
        "instance_id",
        "plan_id",
        "item_id",
        "member_id",
        "scheduled_for",
        "status",
        "related_runtime_id",
    )


def test_reminder_runtime_record_tracks_planned_and_completed_writes():
    event = load_reminder_event(_event_path("reminder-generate.json"))
    record = build_reminder_instance_snapshot(event)

    assert record["entity_type"] == "reminder_instance"
    assert record["runtime_id"] == "runtime_reminder_generate_001"
    assert record["instance_id"] == "runtime_reminder_generate_001"
    assert record["plan_id"] == "plan_mom_bp_202604"
    assert record["item_id"] == "bp_morning"
    assert record["member_id"] == "mom"
    assert record["scheduled_for"] == "2026-04-21T08:00:00+08:00"
    assert record["status"] == "scheduled"
    assert record["planned_writes"] == ["reminder_instance"]
    assert record["completed_writes"] == ["reminder_instance"]


def test_confirmation_selection_requires_an_exact_related_runtime_match():
    instances = [
        {
            "instance_id": "runtime_reminder_generate_002",
            "plan_id": "plan_mom_bp_202604",
                "item_id": "bp_morning",
                "member_id": "mom",
                "scheduled_for": "2026-04-21T08:00:00+08:00",
                "status": "sent",
                "related_runtime_id": "runtime_reminder_generate_002",
            },
            {
            "instance_id": "runtime_reminder_generate_001",
            "plan_id": "plan_mom_bp_202604",
                "item_id": "bp_morning",
                "member_id": "mom",
                "scheduled_for": "2026-04-21T08:00:00+08:00",
                "status": "sent",
                "related_runtime_id": "runtime_reminder_generate_001",
            },
        ]

    selected = select_confirmation_instance(instances, "runtime_reminder_generate_001")

    assert selected is not None
    assert selected["instance_id"] == "runtime_reminder_generate_001"
    assert selected["related_runtime_id"] == "runtime_reminder_generate_001"


def test_confirmation_selection_rejects_when_related_runtime_id_does_not_match():
    instances = [
        {
            "instance_id": "runtime_reminder_generate_002",
            "plan_id": "plan_mom_bp_202604",
                "item_id": "bp_morning",
                "member_id": "mom",
                "scheduled_for": "2026-04-21T08:00:00+08:00",
                "status": "sent",
                "related_runtime_id": "runtime_reminder_generate_002",
            }
        ]

    selected = select_confirmation_instance(instances, "runtime_reminder_generate_001")

    assert selected is None


def test_confirmation_selection_does_not_accept_backlink_only_matches():
    instances = [
        {
            "instance_id": "runtime_reminder_generate_shadow",
            "runtime_id": "runtime_reminder_generate_shadow",
            "plan_id": "plan_mom_bp_202604",
            "item_id": "bp_morning",
            "member_id": "mom",
            "scheduled_for": "2026-04-21T08:00:00+08:00",
            "status": "sent",
            "related_runtime_id": "runtime_reminder_generate_001",
        }
    ]

    selected = select_confirmation_instance(instances, "runtime_reminder_generate_001")

    assert selected is None
