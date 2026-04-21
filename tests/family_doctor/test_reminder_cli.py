import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REMINDER = ROOT / "scripts" / "family_doctor" / "run_reminder.py"


def _write_rule_page(target: Path, member_id: str = "mom") -> Path:
    rule_path = target / "02_wiki" / "plans" / f"{member_id}-reminders.md"
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


def test_run_reminder_prints_success_json_to_stdout(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "reminder-generate.json"
    assert run_bootstrap(target).returncode == 0
    _write_rule_page(target)

    result = subprocess.run(
        [
            sys.executable,
            str(REMINDER),
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
    assert payload["route"] == "reminder"
    assert payload["artifacts"]
    assert result.stderr == ""


def test_run_reminder_returns_non_zero_and_stderr_when_rule_is_missing(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "reminder-generate.json"
    assert run_bootstrap(target).returncode == 0

    result = subprocess.run(
        [
            sys.executable,
            str(REMINDER),
            "--event",
            str(event),
            "--target",
            str(target),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert "missing reminder rule page" in result.stderr
