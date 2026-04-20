import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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
