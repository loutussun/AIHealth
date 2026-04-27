import json
import shutil
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TRACKING_HEADERS = {
    "04_tracking/体检指标.csv": "member_id,date,item,result,unit,reference_range,status,source_ref,notes",
    "04_tracking/用药打卡.csv": "member_id,date,time,medication_id,dose,status,source_ref,notes",
    "04_tracking/饮食记录.csv": "member_id,date,meal,summary,tags,source_ref,notes",
    "04_tracking/运动记录.csv": "member_id,date,activity,duration_minutes,intensity,source_ref,notes",
    "04_tracking/睡眠记录.csv": "member_id,date,sleep_start,sleep_end,duration_hours,quality,source_ref,notes",
}

EXPECTED_OUTPUT_DIRECTORIES = [
    "03_outputs/checkup-updates",
    "03_outputs/lab-updates",
    "03_outputs/visit-briefs",
    "03_outputs/family-messages",
    "03_outputs/weekly-reports",
    "03_outputs/monthly-reports",
    "03_outputs/reminder-messages",
    "03_outputs/qa-summaries",
]

EXPECTED_PAGE_TEMPLATES = [
    "00_schema/page-templates/family-message-template.md",
    "00_schema/page-templates/visit-brief-template.md",
]


def test_validate_accepts_bootstrapped_phase0_vault(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    result = run_validate(target)

    assert result.returncode == 0
    assert "phase 0 validation passed" in result.stdout.lower()


def test_phase0_acceptance_baseline(run_bootstrap, run_validate, tmp_path):
    canonical = ROOT / "family-health"
    canonical_result = run_validate(canonical)

    assert canonical_result.returncode == 0
    assert "phase 0 validation passed" in canonical_result.stdout.lower()

    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    result = run_validate(target)

    assert result.returncode == 0
    assert (target / "02_wiki" / "members").exists()
    assert (target / "99_runtime" / "jobs").exists()
    assert "phase 0 validation passed" in result.stdout.lower()


def test_validate_rejects_missing_runtime_directory(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    (target / "99_runtime" / "jobs" / ".gitkeep").unlink()
    (target / "99_runtime" / "jobs").rmdir()

    result = run_validate(target)

    assert result.returncode == 1
    assert "99_runtime/jobs" in result.stderr


def test_validate_rejects_missing_core_markdown_assets(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    (target / "AGENTS.md").unlink()

    result = run_validate(target)

    assert result.returncode == 1
    assert "AGENTS.md" in result.stderr


def test_validate_rejects_missing_family_health_home_page(
    run_bootstrap, run_validate, tmp_path
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    home = target / "家庭健康管理中心.md"
    home.write_text(
        "# 家庭健康管理中心\n\n- [[index]]\n- [[log]]\n",
        encoding="utf-8",
    )
    assert home.exists()
    home.unlink()

    result = run_validate(target)

    assert result.returncode == 1
    assert "家庭健康管理中心.md" in result.stderr


@pytest.mark.parametrize("relative_path", EXPECTED_TRACKING_HEADERS)
def test_validate_rejects_missing_tracking_csv(
    run_bootstrap, run_validate, tmp_path, relative_path
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    csv_path = target / relative_path
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text(f"{EXPECTED_TRACKING_HEADERS[relative_path]}\n", encoding="utf-8")
    assert csv_path.exists()
    csv_path.unlink()

    result = run_validate(target)

    assert result.returncode == 1
    assert relative_path in result.stderr


@pytest.mark.parametrize(
    ("relative_path", "expected_header"), EXPECTED_TRACKING_HEADERS.items()
)
def test_validate_rejects_tracking_csv_header_drift(
    run_bootstrap, run_validate, tmp_path, relative_path, expected_header
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    csv_path = target / relative_path
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("member_id,date,item,result\n", encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert relative_path in result.stderr
    assert expected_header in result.stderr


@pytest.mark.parametrize("relative_path", EXPECTED_OUTPUT_DIRECTORIES)
def test_validate_rejects_missing_obsidian_first_output_directories(
    run_bootstrap, run_validate, tmp_path, relative_path
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    missing_dir = target / relative_path
    missing_dir.mkdir(parents=True, exist_ok=True)
    (missing_dir / ".gitkeep").write_text("", encoding="utf-8")
    assert missing_dir.is_dir()
    shutil.rmtree(missing_dir)

    result = run_validate(target)

    assert result.returncode == 1
    assert relative_path in result.stderr


@pytest.mark.parametrize("relative_path", EXPECTED_PAGE_TEMPLATES)
def test_validate_rejects_missing_obsidian_first_page_templates(
    run_bootstrap, run_validate, tmp_path, relative_path
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    template_path = target / relative_path
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text("---\ntype: template\n---\n", encoding="utf-8")
    assert template_path.exists()
    template_path.unlink()

    result = run_validate(target)

    assert result.returncode == 1
    assert relative_path in result.stderr


def test_validate_rejects_incomplete_event_contract(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["required_top_level_keys"] = ["event_id", "payload"]
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "required_top_level_keys" in result.stderr


def test_validate_rejects_actor_schema_drift(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["field_shapes"]["actor"] = {
        "type": "object",
        "nullable": False,
        "required_keys": ["id"],
        "properties": {
            "id": {"type": "string", "nullable": False, "min_length": 1},
        },
    }
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    sample_path = target / "examples" / "sample-input-event.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    sample["actor"] = {"id": "user_dad"}
    sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "field_shapes.actor" in result.stderr


def test_validate_rejects_target_property_schema_drift(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["field_shapes"]["target"]["properties"]["member_hint"]["type"] = "number"
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    sample_path = target / "examples" / "sample-input-event.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    sample["target"]["member_hint"] = 123
    sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "field_shapes.target.properties.member_hint.type" in result.stderr


def test_validate_rejects_invalid_runtime_registry(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    registry_path = target / "00_schema" / "runtime-entities.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    del registry["entities"]["review_item"]["statuses"]
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "review_item missing statuses" in result.stderr


def test_validate_rejects_runtime_property_schema_drift(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["field_shapes"]["runtime"]["properties"]["dedupe_scope"]["min_length"] = 0
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    sample_path = target / "examples" / "sample-input-event.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    sample["runtime"]["dedupe_scope"] = ""
    sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "field_shapes.runtime.properties.dedupe_scope.min_length" in result.stderr


def test_validate_rejects_invalid_sample_event(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    sample_path = target / "examples" / "sample-input-event.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    del sample["runtime"]["dedupe_scope"]
    sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "runtime missing dedupe_scope" in result.stderr


def test_validate_rejects_invalid_trigger_mode_contract(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    sample_path = target / "examples" / "sample-input-event.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    sample["trigger_mode"] = "manual_import"
    sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "invalid trigger_mode" in result.stderr


def test_validate_rejects_invalid_context_locale_and_timezone(
    run_bootstrap, run_validate, tmp_path
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    sample_path = target / "examples" / "sample-input-event.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    sample["context"]["locale"] = "not-a-locale"
    sample["context"]["timezone"] = "Mars/Base"
    sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "context.locale" in result.stderr
    assert "context.timezone" in result.stderr


def test_validate_rejects_unsupported_context_keys(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    sample_path = target / "examples" / "sample-input-event.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    sample["context"]["calendar"] = "gregorian"
    sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "context has unsupported key calendar" in result.stderr


def test_validate_rejects_missing_occurred_at_field_shape(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    del schema["field_shapes"]["occurred_at"]
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "field_shapes.occurred_at" in result.stderr


def test_validate_rejects_invalid_attachment_values(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    sample_path = target / "examples" / "sample-input-event.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    attachment = sample["payload"]["attachments"][0]
    attachment["attachment_id"] = None
    attachment["path"] = ""
    attachment["caption"] = 123
    sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "attachment.attachment_id" in result.stderr
    assert "attachment.path" in result.stderr
    assert "attachment.caption" in result.stderr


def test_validate_rejects_context_property_schema_drift(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    del schema["field_shapes"]["context"]["properties"]["locale"]["format"]
    del schema["field_shapes"]["context"]["properties"]["timezone"]["format"]
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "field_shapes.context.properties.locale.format" in result.stderr
    assert "field_shapes.context.properties.timezone.format" in result.stderr


def test_validate_rejects_attachment_property_schema_drift(run_bootstrap, run_validate, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    del schema["attachment_shape"]["properties"]["attachment_id"]["min_length"]
    del schema["attachment_shape"]["properties"]["path"]["min_length"]
    schema["attachment_shape"]["properties"]["caption"]["type"] = "number"
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "attachment_shape.properties.attachment_id.min_length" in result.stderr
    assert "attachment_shape.properties.path.min_length" in result.stderr
    assert "attachment_shape.properties.caption.type" in result.stderr


def test_validate_rejects_additive_context_property_schema_drift(
    run_bootstrap, run_validate, tmp_path
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["field_shapes"]["context"]["properties"]["calendar"] = {
        "type": "string",
        "nullable": True,
        "min_length": 1,
    }
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "field_shapes.context.properties" in result.stderr
    assert "calendar" in result.stderr


def test_validate_rejects_additive_attachment_property_schema_drift(
    run_bootstrap, run_validate, tmp_path
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["attachment_shape"]["optional_keys"].append("checksum_hint")
    schema["attachment_shape"]["properties"]["checksum_hint"] = {
        "type": "string",
        "nullable": True,
        "min_length": 1,
    }
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "attachment_shape optional_keys" in result.stderr
    assert "attachment_shape.properties" in result.stderr
    assert "checksum_hint" in result.stderr
