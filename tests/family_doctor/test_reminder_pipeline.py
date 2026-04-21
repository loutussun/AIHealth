from __future__ import annotations

import json
from pathlib import Path

import pytest

from family_doctor.reminder_pipeline import (
    ReminderError,
    load_reminder_event,
    run_reminder_pipeline,
)
from family_doctor.reminder_rules import (
    ReminderRule,
    ReminderRuleError,
    load_reminder_rule,
    reminder_rule_path_for_member,
)


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def _rule_path(member_id: str) -> Path:
    return Path("02_wiki") / "plans" / f"{member_id}-reminders.md"


def _write_rule_page(target: Path, member_id: str = "mom") -> Path:
    rule_path = target / _rule_path(member_id)
    rule_path.parent.mkdir(parents=True, exist_ok=True)
    rule_path.write_text(
        "\n".join(
            [
                "---",
                "type: reminder_rule",
                f"member_id: {member_id}",
                "plan_id: plan_mom_bp_202604",
                "item_id: bp_morning",
                "confirm_keywords:",
                "  - 已吃",
                "  - 已测",
                "escalation_policy: escalate_after_2_misses",
                "---",
                "",
                "# Reminder Rule",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return rule_path


def _write_mismatched_rule_page(target: Path, member_id: str = "mom") -> Path:
    rule_path = target / _rule_path(member_id)
    rule_path.parent.mkdir(parents=True, exist_ok=True)
    rule_path.write_text(
        "\n".join(
            [
                "---",
                "type: reminder_rule",
                f"member_id: {member_id}",
                "plan_id: plan_mom_bp_202604",
                "item_id: bp_evening",
                "confirm_keywords:",
                "  - 已吃",
                "escalation_policy: escalate_after_2_misses",
                "---",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return rule_path


def _seed_runtime_instance(target: Path, runtime_id: str, *, status: str) -> Path:
    state_root = target / "99_runtime" / "state"
    state_root.mkdir(parents=True, exist_ok=True)
    path = state_root / f"reminder_instance_{runtime_id}.json"
    payload = {
        "entity_type": "reminder_instance",
        "runtime_id": runtime_id,
        "instance_id": runtime_id,
        "plan_id": "plan_mom_bp_202604",
        "item_id": "bp_morning",
        "member_id": "mom",
        "scheduled_for": "2026-04-21T08:00:00+08:00",
        "status": status,
        "related_runtime_id": runtime_id,
        "planned_writes": ["reminder_instance"],
        "completed_writes": ["reminder_instance"],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_reminder_event_fixture_freezes_minimal_shape():
    event = load_reminder_event(_event_path("reminder-generate.json"))

    assert event.event_type == "reminder"
    assert event.member_id == "mom"
    assert event.reminder_action == "generate"
    assert event.plan_id == "plan_mom_bp_202604"
    assert event.item_id == "bp_morning"
    assert event.scheduled_for == "2026-04-21T08:00:00+08:00"
    assert event.runtime_related_id is None


def test_reminder_rule_source_is_pinned_to_member_plan_page():
    assert reminder_rule_path_for_member("mom") == _rule_path("mom")
    assert reminder_rule_path_for_member("dad") == _rule_path("dad")
    assert reminder_rule_path_for_member("../../../escape") == _rule_path("escape")


def test_reminder_rule_schema_exposes_the_minimal_required_fields():
    assert tuple(ReminderRule.__dataclass_fields__) == (
        "item_id",
        "confirm_keywords",
        "escalation_policy",
    )


def test_load_reminder_rule_rejects_missing_rule_page_without_fallback(tmp_path: Path):
    rule_path = tmp_path / "02_wiki" / "plans" / "mom-reminders.md"

    with pytest.raises(ReminderRuleError, match="missing reminder rule page"):
        load_reminder_rule(rule_path)


def test_reminder_generate_pipeline_does_not_emit_supplement_plan_by_default(tmp_path: Path):
    target = tmp_path / "family-health"
    event_path = _event_path("reminder-generate.json")
    _write_rule_page(target)

    result = run_reminder_pipeline(event_path, target)

    assert result["route"] == "reminder"
    assert result["status"] == "ok"
    assert "supplement_plan" not in result
    assert result["runtime"]["related_runtime_id"] is None
    assert result["plan_id"] == "plan_mom_bp_202604"
    assert result["item_id"] == "bp_morning"
    assert result["scheduled_for"] == "2026-04-21T08:00:00+08:00"
    assert result["artifacts"]
    assert result["runtime_updates"]


def test_reminder_confirm_pipeline_matches_only_the_related_runtime_instance(tmp_path: Path):
    target = tmp_path / "family-health"
    _write_rule_page(target)
    _seed_runtime_instance(target, "runtime_reminder_generate_002", status="sent")
    _seed_runtime_instance(target, "runtime_reminder_generate_001", status="sent")
    result = run_reminder_pipeline(_event_path("reminder-confirm.json"), target)

    assert result["status"] == "ok"
    assert result["runtime"]["related_runtime_id"] == "runtime_reminder_generate_001"
    assert result["selected_runtime_id"] == "runtime_reminder_generate_001"
    assert result["matched_instance_id"] == "runtime_reminder_generate_001"
    assert result["matched_instance_id"] != "runtime_reminder_generate_002"


def test_reminder_escalate_pipeline_keeps_traceability_but_not_supplement_plan(tmp_path: Path):
    target = tmp_path / "family-health"
    _write_rule_page(target)
    _seed_runtime_instance(target, "runtime_reminder_generate_001", status="sent")
    result = run_reminder_pipeline(_event_path("reminder-escalate.json"), target)

    assert result["status"] == "ok"
    assert result["runtime"]["related_runtime_id"] == "runtime_reminder_generate_001"
    assert "supplement_plan" not in result
    assert result["escalation_policy"] == "escalate_after_2_misses"
    assert result["artifacts"]


def test_reminder_pipeline_rejects_rule_pages_for_a_different_item_id(tmp_path: Path):
    target = tmp_path / "family-health"
    _write_mismatched_rule_page(target)

    with pytest.raises(ReminderError, match="item_id did not match"):
        run_reminder_pipeline(_event_path("reminder-generate.json"), target)


def test_reminder_pipeline_sanitizes_message_artifact_paths(tmp_path: Path):
    target = tmp_path / "family-health"
    _write_rule_page(target)

    event_path = tmp_path / "reminder-generate-unsafe.json"
    raw_event = json.loads(_event_path("reminder-generate.json").read_text(encoding="utf-8"))
    raw_event["event_id"] = "evt_../../escaped"
    event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_reminder_pipeline(event_path, target)

    artifact_path = Path(result["artifacts"][0]["path"])
    assert artifact_path.parent == (target / "03_outputs" / "reminders").resolve()
    assert artifact_path.relative_to((target / "03_outputs").resolve())
    assert artifact_path.name == "runtime_-escaped.md"
