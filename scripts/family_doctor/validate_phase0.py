from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REQUIRED_DIRS = [
    "00_schema/page-templates",
    "01_raw/reports",
    "01_raw/labs",
    "01_raw/medications",
    "01_raw/diets",
    "01_raw/exercise",
    "01_raw/sleep",
    "01_raw/visits",
    "01_raw/attachments",
    "02_wiki/members",
    "02_wiki/sources",
    "02_wiki/conditions",
    "02_wiki/medications",
    "02_wiki/timelines",
    "02_wiki/trends",
    "02_wiki/plans",
    "04_tracking",
    "03_outputs/checkup-updates",
    "03_outputs/lab-updates",
    "03_outputs/weekly-reports",
    "03_outputs/monthly-reports",
    "03_outputs/visit-briefs",
    "03_outputs/family-messages",
    "03_outputs/reminder-messages",
    "03_outputs/qa-summaries",
    "99_runtime/inbox",
    "99_runtime/staging",
    "99_runtime/jobs",
    "99_runtime/state",
    "99_runtime/traces",
]

REQUIRED_MARKDOWN_MARKERS = {
    "AGENTS.md": ["# family-health Canonical Vault", "## 四类内部能力边界"],
    "index.md": ["type: index", "## 成员索引", "## 近期输出"],
    "log.md": ["# 操作日志", "## 日志格式"],
    "00_schema/members.md": ["# 成员注册规则", "## 成员识别护栏"],
    "00_schema/reporting-rules.md": ["# 报告生成规则", "## 输出要求"],
    "00_schema/reminder-rules.md": ["# 提醒生成规则", "## 交付要求"],
    "家庭健康管理中心.md": [
        "# 家庭健康管理中心",
        "[[index]]",
        "[[log]]",
        "02_wiki/members",
        "04_tracking/体检指标.csv",
    ],
}

TEMPLATE_MARKERS = {
    "member-template.md": ["type: member", "## 基本信息", "## 当前用药"],
    "source-template.md": ["type: source", "## 来源信息", "## 提取出的结构化事实"],
    "medication-template.md": ["type: medication", "display_name:", "## 适应证", "## 漏服规则"],
    "condition-template.md": ["type: condition", "display_name:", "## 涉及成员", "## 关键证据"],
    "trend-template.md": ["type: trend", "## 关键指标表", "## 趋势判断"],
    "plan-template.md": ["type: plan", "## 当前目标", "## 待复查事项"],
    "output-template.md": [
        "type: output",
        "output_kind:",
        "source_refs:",
        "## 结论摘要",
        "## 证据来源",
        "## 待核实项",
    ],
    "reminder-template.md": [
        "type: reminder",
        "runtime_id:",
        "status:",
        "scheduled_for:",
        "## 提醒内容",
        "## 运行时映射",
    ],
    "family-message-template.md": [
        "type: output",
        "output_kind: family_message",
        "## 可发送版本",
        "## 证据来源",
        "## 待核实项",
    ],
    "visit-brief-template.md": [
        "type: output",
        "output_kind: visit_brief",
        "## 就诊目标",
        "## 证据来源",
        "## 待核实项",
    ],
}

EXPECTED_TRACKING_HEADERS = {
    "04_tracking/体检指标.csv": "member_id,date,item,result,unit,reference_range,status,source_ref,notes",
    "04_tracking/用药打卡.csv": "member_id,date,time,medication_id,dose,status,source_ref,notes",
    "04_tracking/饮食记录.csv": "member_id,date,meal,summary,tags,source_ref,notes",
    "04_tracking/运动记录.csv": "member_id,date,activity,duration_minutes,intensity,source_ref,notes",
    "04_tracking/睡眠记录.csv": "member_id,date,sleep_start,sleep_end,duration_hours,quality,source_ref,notes",
}

EXPECTED_REQUIRED_TOP_LEVEL_KEYS = {
    "event_id",
    "request_id",
    "idempotency_key",
    "correlation_id",
    "causation_id",
    "event_type",
    "trigger_mode",
    "occurred_at",
    "actor",
    "target",
    "payload",
    "context",
    "runtime",
}
EXPECTED_EVENT_TYPES = {"ingest", "query", "report", "reminder"}
EXPECTED_TRIGGER_MODES = {"user_message", "scheduled", "file_drop", "followup"}
EXPECTED_REPORT_KINDS = {
    "checkup_update",
    "weekly_health_report",
    "monthly_health_report",
    "visit_brief",
}
EXPECTED_REMINDER_ACTIONS = {"generate", "confirm", "escalate"}
EXPECTED_ATTACHMENT_KINDS = {"image", "pdf", "text", "csv", "zip"}
EXPECTED_RUNTIME_ENTITIES = [
    "ingest_job",
    "report_job",
    "reminder_instance",
    "review_item",
    "dedupe_record",
]
EXPECTED_SCALAR_FIELD_SHAPES = {
    "event_id": {"type": "string", "nullable": False, "min_length": 1},
    "request_id": {"type": "string", "nullable": False, "min_length": 1},
    "idempotency_key": {"type": "string", "nullable": False, "min_length": 1},
    "correlation_id": {"type": "string", "nullable": False, "min_length": 1},
    "causation_id": {"type": "string", "nullable": True, "min_length": 1},
    "event_type": {"type": "string", "nullable": False, "enum": sorted(EXPECTED_EVENT_TYPES)},
    "trigger_mode": {"type": "string", "nullable": False, "enum": sorted(EXPECTED_TRIGGER_MODES)},
    "occurred_at": {"type": "string", "nullable": False, "format": "rfc3339"},
}
EXPECTED_CONTEXT_PROPERTY_SHAPES = {
    "source": {"type": "string", "nullable": False, "min_length": 1},
    "locale": {"type": "string", "nullable": False, "format": "bcp47"},
    "timezone": {"type": "string", "nullable": False, "format": "iana-timezone"},
}
EXPECTED_ACTOR_PROPERTY_SHAPES = {
    "actor_id": {"type": "string", "nullable": False, "min_length": 1},
    "role": {
        "type": "string",
        "nullable": False,
        "enum": ["assistant", "caregiver", "member", "system"],
    },
}
EXPECTED_TARGET_PROPERTY_SHAPES = {
    "member_id": {"type": "string", "nullable": True, "min_length": 1},
    "member_hint": {"type": "string", "nullable": False, "min_length": 1},
    "match_confidence": {"type": "number", "nullable": False, "minimum": 0, "maximum": 1},
}
EXPECTED_PAYLOAD_PROPERTY_SHAPES = {
    "text": {"type": "string", "nullable": True, "min_length": 0},
    "attachments": {"type": "array", "nullable": False, "items": "attachment_shape", "min_items": 0},
    "source_refs": {
        "type": "array",
        "nullable": False,
        "items": {"type": "string", "nullable": False, "min_length": 1},
        "min_items": 0,
    },
    "report_kind": {
        "type": "string",
        "nullable": True,
        "enum": sorted(EXPECTED_REPORT_KINDS),
    },
    "reminder_action": {
        "type": "string",
        "nullable": True,
        "enum": sorted(EXPECTED_REMINDER_ACTIONS),
    },
}
EXPECTED_RUNTIME_PROPERTY_SHAPES = {
    "related_runtime_id": {"type": "string", "nullable": True, "min_length": 1},
    "review_item_id": {"type": "string", "nullable": True, "min_length": 1},
    "dedupe_scope": {"type": "string", "nullable": False, "min_length": 1},
}
EXPECTED_ATTACHMENT_PROPERTY_SHAPES = {
    "attachment_id": {"type": "string", "nullable": False, "min_length": 1},
    "kind": {"type": "string", "nullable": False, "enum": sorted(EXPECTED_ATTACHMENT_KINDS)},
    "path": {"type": "string", "nullable": False, "min_length": 1},
    "mime_type": {"type": "string", "nullable": True, "min_length": 1},
    "caption": {"type": "string", "nullable": True, "min_length": 1},
    "source_name": {"type": "string", "nullable": True, "min_length": 1},
    "content_sha256": {"type": "string", "nullable": True, "min_length": 1},
    "attachment_group_id": {"type": "string", "nullable": True, "min_length": 1},
}

BCP47_PATTERN = re.compile(
    r"^(?:[A-Za-z]{2,3}|[A-Za-z]{4}|[A-Za-z]{5,8})"
    r"(?:-[A-Za-z]{4})?"
    r"(?:-(?:[A-Za-z]{2}|\d{3}))?"
    r"(?:-(?:[A-Za-z0-9]{5,8}|\d[A-Za-z0-9]{3}))*$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a family-health Phase 0 vault against the canonical contract."
    )
    parser.add_argument("--target", required=True, type=Path)
    return parser.parse_args()


def load_json_file(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"Missing required JSON file: {path}"]

    if not path.is_file():
        return None, [f"Expected a file but found non-file path: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON in {path}: {exc.msg}"]

    if not isinstance(data, dict):
        return None, [f"Expected top-level JSON object in {path}"]

    return data, []


def validate_directory_topology(target: Path) -> list[str]:
    errors: list[str] = []

    if not target.exists():
        return [f"Target vault does not exist: {target}"]

    if not target.is_dir():
        return [f"Target vault is not a directory: {target}"]

    for relative_dir in REQUIRED_DIRS:
        path = target / relative_dir
        if not path.exists():
            errors.append(f"Missing required directory: {relative_dir}")
            continue
        if not path.is_dir():
            errors.append(f"Required path is not a directory: {relative_dir}")

    return errors


def validate_required_markdown_assets(target: Path) -> list[str]:
    errors: list[str] = []

    for relative_path, markers in REQUIRED_MARKDOWN_MARKERS.items():
        path = target / relative_path
        if not path.exists():
            errors.append(f"Missing required Markdown file: {relative_path}")
            continue
        if not path.is_file():
            errors.append(f"Required Markdown path is not a file: {relative_path}")
            continue

        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                errors.append(f"Markdown file {relative_path} missing marker: {marker}")

    return errors


def validate_templates(target: Path) -> list[str]:
    errors: list[str] = []
    template_root = target / "00_schema" / "page-templates"

    for filename, markers in TEMPLATE_MARKERS.items():
        path = template_root / filename
        if not path.exists():
            errors.append(f"Missing template file: 00_schema/page-templates/{filename}")
            continue
        if not path.is_file():
            errors.append(f"Template path is not a file: 00_schema/page-templates/{filename}")
            continue

        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                errors.append(f"Template {filename} missing marker: {marker}")

    return errors


def validate_tracking_csvs(target: Path) -> list[str]:
    errors: list[str] = []

    for relative_path, expected_header in EXPECTED_TRACKING_HEADERS.items():
        path = target / relative_path
        if not path.exists():
            errors.append(f"Missing tracking CSV file: {relative_path}")
            continue
        if not path.is_file():
            errors.append(f"Tracking CSV path is not a file: {relative_path}")
            continue

        first_line = path.read_text(encoding="utf-8").splitlines()
        actual_header = first_line[0] if first_line else ""
        if actual_header != expected_header:
            errors.append(
                f"Tracking CSV {relative_path} must start with header: {expected_header}"
            )

    return errors


def validate_expected_property_shapes(
    properties: dict[str, Any],
    expected_shapes: dict[str, dict[str, Any]],
    error_prefix: str,
    errors: list[str],
) -> None:
    unexpected_properties = set(properties) - set(expected_shapes)
    if unexpected_properties:
        extras = ", ".join(sorted(unexpected_properties))
        errors.append(f"{error_prefix} has unexpected keys: {extras}")

    for property_name, expected_shape in expected_shapes.items():
        property_shape = properties.get(property_name)
        if not isinstance(property_shape, dict):
            errors.append(f"{error_prefix}.{property_name} is missing")
            continue
        for key, expected_value in expected_shape.items():
            actual_value = property_shape.get(key)
            if key == "enum":
                if set(actual_value or []) != set(expected_value):
                    errors.append(f"{error_prefix}.{property_name}.{key} is incorrect")
                continue
            if actual_value != expected_value:
                errors.append(f"{error_prefix}.{property_name}.{key} is incorrect")


def validate_event_schema(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = set(schema.get("required_top_level_keys", []))
    if required != EXPECTED_REQUIRED_TOP_LEVEL_KEYS:
        errors.append("event-schema.json has incorrect required_top_level_keys")

    if set(schema.get("allowed_event_types", [])) != EXPECTED_EVENT_TYPES:
        errors.append("event-schema.json has incorrect allowed_event_types")

    if set(schema.get("allowed_trigger_modes", [])) != EXPECTED_TRIGGER_MODES:
        errors.append("event-schema.json has incorrect allowed_trigger_modes")

    field_shapes = schema.get("field_shapes", {})
    for field_name, expected_shape in EXPECTED_SCALAR_FIELD_SHAPES.items():
        shape = field_shapes.get(field_name)
        if not isinstance(shape, dict):
            errors.append(f"event-schema.json missing field_shapes.{field_name}")
            continue
        for key, expected_value in expected_shape.items():
            actual_value = shape.get(key)
            if key == "enum":
                if set(actual_value or []) != set(expected_value):
                    errors.append(f"event-schema.json field_shapes.{field_name}.{key} is incorrect")
                continue
            if actual_value != expected_value:
                errors.append(f"event-schema.json field_shapes.{field_name}.{key} is incorrect")

    for key in ["actor", "target", "payload", "context", "runtime"]:
        if key not in field_shapes:
            errors.append(f"event-schema.json missing field_shapes.{key}")

    actor_shape = field_shapes.get("actor", {})
    if set(actor_shape.get("required_keys", [])) != {"actor_id", "role"}:
        errors.append("event-schema.json field_shapes.actor.required_keys are incorrect")
    if set(actor_shape.get("optional_keys", [])) != set():
        errors.append("event-schema.json field_shapes.actor.optional_keys are incorrect")
    actor_properties = actor_shape.get("properties", {})
    validate_expected_property_shapes(
        actor_properties,
        EXPECTED_ACTOR_PROPERTY_SHAPES,
        "event-schema.json field_shapes.actor.properties",
        errors,
    )

    target_shape = field_shapes.get("target", {})
    if set(target_shape.get("required_keys", [])) != {
        "member_hint",
        "match_confidence",
    }:
        errors.append("event-schema.json target required_keys are incorrect")

    if set(target_shape.get("optional_keys", [])) != {"member_id"}:
        errors.append("event-schema.json target optional_keys are incorrect")
    validate_expected_property_shapes(
        target_shape.get("properties", {}),
        EXPECTED_TARGET_PROPERTY_SHAPES,
        "event-schema.json field_shapes.target.properties",
        errors,
    )

    payload_shape = field_shapes.get("payload", {})
    if set(payload_shape.get("required_keys", [])) != {
        "attachments",
        "source_refs",
    }:
        errors.append("event-schema.json payload required_keys are incorrect")

    if set(payload_shape.get("optional_keys", [])) != {
        "text",
        "report_kind",
        "reminder_action",
    }:
        errors.append("event-schema.json payload optional_keys are incorrect")
    validate_expected_property_shapes(
        payload_shape.get("properties", {}),
        EXPECTED_PAYLOAD_PROPERTY_SHAPES,
        "event-schema.json field_shapes.payload.properties",
        errors,
    )

    runtime_shape = field_shapes.get("runtime", {})
    if set(runtime_shape.get("required_keys", [])) != {"dedupe_scope"}:
        errors.append("event-schema.json runtime required_keys are incorrect")

    if set(runtime_shape.get("optional_keys", [])) != {
        "related_runtime_id",
        "review_item_id",
    }:
        errors.append("event-schema.json runtime optional_keys are incorrect")
    validate_expected_property_shapes(
        runtime_shape.get("properties", {}),
        EXPECTED_RUNTIME_PROPERTY_SHAPES,
        "event-schema.json field_shapes.runtime.properties",
        errors,
    )

    context_shape = field_shapes.get("context", {})
    if context_shape.get("required_keys", []) != ["source", "locale", "timezone"]:
        errors.append("event-schema.json context required_keys are incorrect")
    if set(context_shape.get("optional_keys", [])) != set():
        errors.append("event-schema.json context optional_keys are incorrect")
    validate_expected_property_shapes(
        context_shape.get("properties", {}),
        EXPECTED_CONTEXT_PROPERTY_SHAPES,
        "event-schema.json field_shapes.context.properties",
        errors,
    )

    rules = schema.get("event_type_rules", {})
    for key in EXPECTED_EVENT_TYPES:
        if key not in rules:
            errors.append(f"event-schema.json missing event_type_rules.{key}")

    if rules.get("ingest", {}).get("target_member_id") != "recommended":
        errors.append("event-schema.json ingest target_member_id rule is incorrect")

    if rules.get("query", {}).get("payload_required_keys") != ["text"]:
        errors.append("event-schema.json query payload_required_keys are incorrect")

    if rules.get("report", {}).get("payload_required_keys") != ["report_kind"]:
        errors.append("event-schema.json report payload_required_keys are incorrect")

    if rules.get("reminder", {}).get("payload_required_keys") != ["reminder_action"]:
        errors.append("event-schema.json reminder payload_required_keys are incorrect")

    if rules.get("reminder", {}).get("confirm_recommended_runtime_keys") != ["related_runtime_id"]:
        errors.append("event-schema.json reminder confirm_recommended_runtime_keys are incorrect")

    attachment_shape = schema.get("attachment_shape")
    if not isinstance(attachment_shape, dict):
        errors.append("event-schema.json missing attachment_shape")
        return errors

    if set(attachment_shape.get("required_keys", [])) != {"attachment_id", "kind", "path"}:
        errors.append("event-schema.json attachment_shape required_keys are incorrect")
    if set(attachment_shape.get("optional_keys", [])) != {
        "mime_type",
        "caption",
        "source_name",
        "content_sha256",
        "attachment_group_id",
    }:
        errors.append("event-schema.json attachment_shape optional_keys are incorrect")
    validate_expected_property_shapes(
        attachment_shape.get("properties", {}),
        EXPECTED_ATTACHMENT_PROPERTY_SHAPES,
        "event-schema.json attachment_shape.properties",
        errors,
    )

    payload_properties = field_shapes.get("payload", {}).get("properties", {})
    if set(payload_properties.get("report_kind", {}).get("enum", [])) != EXPECTED_REPORT_KINDS:
        errors.append("event-schema.json report_kind enum is incorrect")

    if set(payload_properties.get("reminder_action", {}).get("enum", [])) != EXPECTED_REMINDER_ACTIONS:
        errors.append("event-schema.json reminder_action enum is incorrect")

    if set(attachment_shape.get("properties", {}).get("kind", {}).get("enum", [])) != EXPECTED_ATTACHMENT_KINDS:
        errors.append("event-schema.json attachment kind enum is incorrect")

    return errors


def validate_runtime_entities(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    entities = registry.get("entities", {})
    if not isinstance(entities, dict):
        return ["runtime-entities.json missing entities object"]

    for name in EXPECTED_RUNTIME_ENTITIES:
        entity = entities.get(name)
        if not isinstance(entity, dict):
            errors.append(f"Missing runtime entity: {name}")
            continue

        for key in [
            "primary_key",
            "statuses",
            "required_fields",
            "allowed_transitions",
            "retention",
            "log_identity_field",
        ]:
            if key not in entity:
                errors.append(f"{name} missing {key}")

        statuses = entity.get("statuses", [])
        required_fields = entity.get("required_fields", [])
        transitions = entity.get("allowed_transitions", {})

        if not isinstance(statuses, list):
            errors.append(f"{name} statuses must be a list")
            statuses = []
        if not isinstance(required_fields, list):
            errors.append(f"{name} required_fields must be a list")
            required_fields = []
        if not isinstance(transitions, dict):
            errors.append(f"{name} allowed_transitions must be an object")
            transitions = {}

        primary_key = entity.get("primary_key")
        if primary_key and primary_key not in required_fields:
            errors.append(f"{name} primary_key not listed in required_fields")

        log_identity_field = entity.get("log_identity_field")
        if log_identity_field and log_identity_field not in required_fields:
            errors.append(f"{name} log_identity_field not listed in required_fields")

        declared_statuses = set(statuses)
        for from_status, to_statuses in transitions.items():
            if from_status not in declared_statuses:
                errors.append(f"{name} transition source {from_status} not declared in statuses")
            if not isinstance(to_statuses, list):
                errors.append(f"{name} transition targets for {from_status} must be a list")
                continue
            for target_status in to_statuses:
                if target_status not in declared_statuses:
                    errors.append(f"{name} transition target {target_status} not declared in statuses")

    return errors


def validate_string_value(name: str, value: Any, shape: dict[str, Any], errors: list[str]) -> None:
    if value is None:
        if not shape.get("nullable", False):
            errors.append(f"{name} must not be null")
        return

    if not isinstance(value, str):
        errors.append(f"{name} must be a string")
        return

    min_length = shape.get("min_length")
    if isinstance(min_length, int) and len(value) < min_length:
        errors.append(f"{name} must have min_length {min_length}")

    allowed_values = shape.get("enum")
    if isinstance(allowed_values, list) and value not in allowed_values:
        errors.append(f"{name} has invalid value: {value}")

    if shape.get("format") == "rfc3339":
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{name} must be a valid rfc3339 string")
    elif shape.get("format") == "bcp47":
        if not BCP47_PATTERN.fullmatch(value):
            errors.append(f"{name} must be a valid bcp47 string")
    elif shape.get("format") == "iana-timezone":
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            errors.append(f"{name} must be a valid iana-timezone string")


def get_object_shape(
    field_shapes: dict[str, Any], field_name: str, errors: list[str]
) -> dict[str, Any] | None:
    shape = field_shapes.get(field_name)
    if not isinstance(shape, dict):
        errors.append(f"event-schema.json missing field_shapes.{field_name}")
        return None
    return shape


def validate_number_value(name: str, value: Any, shape: dict[str, Any], errors: list[str]) -> None:
    if value is None:
        if not shape.get("nullable", False):
            errors.append(f"{name} must not be null")
        return

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append(f"{name} must be a number")
        return

    minimum = shape.get("minimum")
    maximum = shape.get("maximum")
    if isinstance(minimum, (int, float)) and value < minimum:
        errors.append(f"{name} must be >= {minimum}")
    if isinstance(maximum, (int, float)) and value > maximum:
        errors.append(f"{name} must be <= {maximum}")


def validate_string_array(name: str, value: Any, shape: dict[str, Any], errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{name} must be an array")
        return

    min_items = shape.get("min_items")
    if isinstance(min_items, int) and len(value) < min_items:
        errors.append(f"{name} must contain at least {min_items} items")

    for index, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(f"{name}[{index}] must be a string")
            continue
        item_shape = shape.get("items", {})
        min_length = item_shape.get("min_length")
        if isinstance(min_length, int) and len(item) < min_length:
            errors.append(f"{name}[{index}] must have min_length {min_length}")


def validate_attachment_list(schema: dict[str, Any], attachments: Any, errors: list[str]) -> None:
    if not isinstance(attachments, list):
        errors.append("sample-input-event.json payload.attachments must be an array")
        return

    attachment_shape = schema.get("attachment_shape", {})
    allowed_attachment_keys = set(attachment_shape.get("required_keys", [])) | set(
        attachment_shape.get("optional_keys", [])
    )
    attachment_kind_enum = set(
        attachment_shape.get("properties", {}).get("kind", {}).get("enum", [])
    )
    attachment_properties = attachment_shape.get("properties", {})

    for attachment in attachments:
        if not isinstance(attachment, dict):
            errors.append("sample-input-event.json attachment must be an object")
            continue

        for key in attachment_shape.get("required_keys", []):
            if key not in attachment:
                errors.append(f"sample-input-event.json attachment missing {key}")

        for key in attachment:
            if key not in allowed_attachment_keys:
                errors.append(f"sample-input-event.json attachment has unsupported key {key}")

        kind = attachment.get("kind")
        if kind is not None and kind not in attachment_kind_enum:
            errors.append(f"sample-input-event.json attachment has invalid kind {kind}")

        for key, shape in attachment_properties.items():
            if key not in attachment:
                continue
            if shape.get("type") == "string":
                validate_string_value(
                    f"sample-input-event.json attachment.{key}",
                    attachment[key],
                    shape,
                    errors,
                )


def validate_sample_event(schema: dict[str, Any], sample: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_top_level_keys = schema.get("required_top_level_keys", [])
    for key in required_top_level_keys:
        if key not in sample:
            errors.append(f"sample-input-event.json missing {key}")

    event_type = sample.get("event_type")
    if event_type not in schema.get("allowed_event_types", []):
        errors.append("sample-input-event.json has invalid event_type")

    trigger_mode = sample.get("trigger_mode")
    if trigger_mode not in schema.get("allowed_trigger_modes", []):
        errors.append("sample-input-event.json has invalid trigger_mode")

    field_shapes = schema.get("field_shapes", {})
    scalar_fields = [
        "event_id",
        "request_id",
        "idempotency_key",
        "correlation_id",
        "causation_id",
        "event_type",
        "trigger_mode",
        "occurred_at",
    ]
    for field_name in scalar_fields:
        if field_name not in sample:
            continue

        shape = get_object_shape(field_shapes, field_name, errors)
        if shape is None:
            continue
        field_type = shape.get("type")
        if field_type == "string":
            validate_string_value(
                f"sample-input-event.json {field_name}",
                sample.get(field_name),
                shape,
                errors,
            )

    actor_shape = get_object_shape(field_shapes, "actor", errors)
    actor = sample.get("actor", {})
    if not isinstance(actor, dict):
        errors.append("sample-input-event.json actor must be an object")
    elif actor_shape is not None:
        allowed_actor_keys = set(actor_shape.get("required_keys", [])) | set(
            actor_shape.get("optional_keys", [])
        )
        for key in actor_shape.get("required_keys", []):
            if key not in actor:
                errors.append(f"sample-input-event.json actor missing {key}")
        for key in actor:
            if key not in allowed_actor_keys:
                errors.append(f"sample-input-event.json actor has unsupported key {key}")
        for key, shape in actor_shape.get("properties", {}).items():
            if key in actor and shape.get("type") == "string":
                validate_string_value(f"sample-input-event.json actor.{key}", actor[key], shape, errors)

    target_shape = get_object_shape(field_shapes, "target", errors)
    target = sample.get("target", {})
    if not isinstance(target, dict):
        errors.append("sample-input-event.json target must be an object")
    elif target_shape is not None:
        allowed_target_keys = set(target_shape.get("required_keys", [])) | set(
            target_shape.get("optional_keys", [])
        )
        for key in target_shape.get("required_keys", []):
            if key not in target:
                errors.append(f"sample-input-event.json target missing {key}")
        for key in target:
            if key not in allowed_target_keys:
                errors.append(f"sample-input-event.json target has unsupported key {key}")
        for key, shape in target_shape.get("properties", {}).items():
            if key not in target:
                continue
            if shape.get("type") == "string":
                validate_string_value(f"sample-input-event.json target.{key}", target[key], shape, errors)
            elif shape.get("type") == "number":
                validate_number_value(f"sample-input-event.json target.{key}", target[key], shape, errors)

    context_shape = get_object_shape(field_shapes, "context", errors)
    context = sample.get("context", {})
    if not isinstance(context, dict):
        errors.append("sample-input-event.json context must be an object")
    elif context_shape is not None:
        allowed_context_keys = set(context_shape.get("required_keys", [])) | set(
            context_shape.get("optional_keys", [])
        )
        for key in context_shape.get("required_keys", []):
            if key not in context:
                errors.append(f"sample-input-event.json context missing {key}")
        for key in context:
            if key not in allowed_context_keys:
                errors.append(f"sample-input-event.json context has unsupported key {key}")
        for key, shape in context_shape.get("properties", {}).items():
            if key in context and shape.get("type") == "string":
                validate_string_value(f"sample-input-event.json context.{key}", context[key], shape, errors)

    runtime_shape = get_object_shape(field_shapes, "runtime", errors)
    runtime = sample.get("runtime", {})
    if not isinstance(runtime, dict):
        errors.append("sample-input-event.json runtime must be an object")
    elif runtime_shape is not None:
        allowed_runtime_keys = set(runtime_shape.get("required_keys", [])) | set(
            runtime_shape.get("optional_keys", [])
        )
        for key in runtime_shape.get("required_keys", []):
            if key not in runtime:
                errors.append(f"sample-input-event.json runtime missing {key}")
        for key in runtime:
            if key not in allowed_runtime_keys:
                errors.append(f"sample-input-event.json runtime has unsupported key {key}")
        for key, shape in runtime_shape.get("properties", {}).items():
            if key in runtime and shape.get("type") == "string":
                validate_string_value(
                    f"sample-input-event.json runtime.{key}",
                    runtime[key],
                    shape,
                    errors,
                )

    payload_shape = get_object_shape(field_shapes, "payload", errors)
    payload = sample.get("payload", {})
    if not isinstance(payload, dict):
        errors.append("sample-input-event.json payload must be an object")
    elif payload_shape is not None:
        allowed_payload_keys = set(payload_shape.get("required_keys", [])) | set(
            payload_shape.get("optional_keys", [])
        )
        for key in payload_shape.get("required_keys", []):
            if key not in payload:
                errors.append(f"sample-input-event.json payload missing {key}")
        for key in payload:
            if key not in allowed_payload_keys:
                errors.append(f"sample-input-event.json payload has unsupported key {key}")

        payload_properties = payload_shape.get("properties", {})
        if "text" in payload:
            validate_string_value(
                "sample-input-event.json payload.text",
                payload["text"],
                payload_properties.get("text", {}),
                errors,
            )
        if "report_kind" in payload:
            validate_string_value(
                "sample-input-event.json payload.report_kind",
                payload["report_kind"],
                payload_properties.get("report_kind", {}),
                errors,
            )
        if "reminder_action" in payload:
            validate_string_value(
                "sample-input-event.json payload.reminder_action",
                payload["reminder_action"],
                payload_properties.get("reminder_action", {}),
                errors,
            )
        if "source_refs" in payload:
            validate_string_array(
                "sample-input-event.json payload.source_refs",
                payload["source_refs"],
                payload_properties.get("source_refs", {}),
                errors,
            )
        if "attachments" in payload:
            validate_attachment_list(schema, payload["attachments"], errors)

    event_rules = schema.get("event_type_rules", {}).get(event_type, {})
    if isinstance(event_rules, dict):
        for key in event_rules.get("payload_required_keys", []):
            if key not in sample.get("payload", {}):
                errors.append(
                    f"sample-input-event.json payload missing {key} for {sample['event_type']}"
                )
        if "payload_at_least_one_of" in event_rules:
            if not any(sample.get("payload", {}).get(key) for key in event_rules["payload_at_least_one_of"]):
                errors.append("sample-input-event.json payload missing required ingest text/attachments")

    return errors


def validate_phase0(target: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_directory_topology(target))
    errors.extend(validate_required_markdown_assets(target))
    errors.extend(validate_templates(target))
    errors.extend(validate_tracking_csvs(target))

    event_schema_path = target / "00_schema" / "event-schema.json"
    runtime_entities_path = target / "00_schema" / "runtime-entities.json"
    sample_event_path = target / "examples" / "sample-input-event.json"

    event_schema, event_schema_errors = load_json_file(event_schema_path)
    runtime_entities, runtime_entities_errors = load_json_file(runtime_entities_path)
    sample_event, sample_event_errors = load_json_file(sample_event_path)

    errors.extend(event_schema_errors)
    errors.extend(runtime_entities_errors)
    errors.extend(sample_event_errors)

    if event_schema is not None:
        errors.extend(validate_event_schema(event_schema))
    if runtime_entities is not None:
        errors.extend(validate_runtime_entities(runtime_entities))
    if event_schema is not None and sample_event is not None:
        errors.extend(validate_sample_event(event_schema, sample_event))

    return errors


def main() -> int:
    args = parse_args()
    errors = validate_phase0(args.target.resolve())

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"Phase 0 validation passed: {args.target.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
