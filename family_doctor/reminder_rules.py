from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from family_doctor.raw_archive import _safe_name


REMINDER_RULES_ROOT = Path("02_wiki") / "plans"


class ReminderRuleError(ValueError):
    """Raised when a reminder rule page cannot be loaded."""


@dataclass(frozen=True)
class ReminderRule:
    item_id: str
    confirm_keywords: tuple[str, ...]
    escalation_policy: str


def reminder_rule_path_for_member(member_id: str) -> Path:
    safe_member_id = _safe_name(member_id).replace("..", "-").lstrip(".-") or "member"
    safe_member_id = re.sub(r"-{2,}", "-", safe_member_id)
    return REMINDER_RULES_ROOT / f"{safe_member_id}-reminders.md"


def _parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        raise ReminderRuleError("reminder rule page must start with frontmatter")

    end_marker = "\n---"
    end_index = text.find(end_marker, 4)
    if end_index == -1:
        raise ReminderRuleError("reminder rule page must close frontmatter")

    frontmatter = text[4:end_index].splitlines()
    data: dict[str, Any] = {}
    current_key: str | None = None

    for raw_line in frontmatter:
        if not raw_line.strip():
            continue
        if raw_line.startswith("  - ") or raw_line.startswith("- "):
            if current_key is None:
                raise ReminderRuleError("list item found before key in frontmatter")
            current_value = data.setdefault(current_key, [])
            if not isinstance(current_value, list):
                raise ReminderRuleError(f"{current_key} must be a list")
            current_value.append(raw_line.split("- ", 1)[1].strip())
            continue
        if ":" not in raw_line:
            raise ReminderRuleError(f"invalid frontmatter line: {raw_line}")
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            data[key] = value
            current_key = None
        else:
            data[key] = []
            current_key = key

    return data


def _require_str(raw: Any, label: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ReminderRuleError(f"{label} must be a non-empty string")
    return raw


def _require_keyword_list(raw: Any, label: str) -> tuple[str, ...]:
    if not isinstance(raw, list) or not raw:
        raise ReminderRuleError(f"{label} must be a non-empty list")
    keywords = tuple(_require_str(item, f"{label}[]") for item in raw)
    return keywords


def load_reminder_rule(path: Path) -> ReminderRule:
    if not path.exists():
        raise ReminderRuleError(f"missing reminder rule page: {path}")
    raw_text = path.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(raw_text)

    return ReminderRule(
        item_id=_require_str(frontmatter.get("item_id"), "item_id"),
        confirm_keywords=_require_keyword_list(
            frontmatter.get("confirm_keywords"),
            "confirm_keywords",
        ),
        escalation_policy=_require_str(
            frontmatter.get("escalation_policy"),
            "escalation_policy",
        ),
    )
