# Family Doctor Phase 0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 0 foundation for the `family-doctor` project: a canonical `family-health/` vault scaffold, machine-readable contracts for events and runtime entities, a bootstrap CLI that can reproduce that vault in any target directory, and a validator CLI that proves the scaffold is structurally sound before Phase 1 begins.

**Architecture:** Phase 0 is “canonical-assets-first”. The repo itself stores the canonical `family-health/` scaffold and contract files. `bootstrap_vault.py` copies those canonical assets to any target directory idempotently, and `validate_phase0.py` validates both the canonical scaffold and bootstrapped copies against explicit structural rules. The event contract is a repo-owned JSON contract document consumed by `validate_phase0.py`; it does not depend on a third-party JSON Schema validator in Phase 0. This keeps the vault definition stable while making downstream execution deterministic.

**Tech Stack:** Markdown, YAML frontmatter, JSON, Python 3 standard library, pytest

---

## Planned File Map

**Create at repo root**
- `pyproject.toml`
  - Minimal Python metadata and pytest config.

**Create canonical vault assets**
- `family-health/AGENTS.md`
- `family-health/index.md`
- `family-health/log.md`
- `family-health/00_schema/members.md`
- `family-health/00_schema/reporting-rules.md`
- `family-health/00_schema/reminder-rules.md`
- `family-health/00_schema/event-schema.json`
- `family-health/00_schema/runtime-entities.json`
- `family-health/00_schema/page-templates/member-template.md`
- `family-health/00_schema/page-templates/source-template.md`
- `family-health/00_schema/page-templates/medication-template.md`
- `family-health/00_schema/page-templates/condition-template.md`
- `family-health/00_schema/page-templates/trend-template.md`
- `family-health/00_schema/page-templates/plan-template.md`
- `family-health/00_schema/page-templates/output-template.md`
- `family-health/00_schema/page-templates/reminder-template.md`
- `family-health/01_raw/reports/.gitkeep`
- `family-health/01_raw/labs/.gitkeep`
- `family-health/01_raw/medications/.gitkeep`
- `family-health/01_raw/diets/.gitkeep`
- `family-health/01_raw/exercise/.gitkeep`
- `family-health/01_raw/sleep/.gitkeep`
- `family-health/01_raw/visits/.gitkeep`
- `family-health/01_raw/attachments/.gitkeep`
- `family-health/02_wiki/members/.gitkeep`
- `family-health/02_wiki/sources/.gitkeep`
- `family-health/02_wiki/conditions/.gitkeep`
- `family-health/02_wiki/medications/.gitkeep`
- `family-health/02_wiki/timelines/.gitkeep`
- `family-health/02_wiki/trends/.gitkeep`
- `family-health/02_wiki/plans/.gitkeep`
- `family-health/03_outputs/checkup-updates/.gitkeep`
- `family-health/03_outputs/weekly-reports/.gitkeep`
- `family-health/03_outputs/monthly-reports/.gitkeep`
- `family-health/03_outputs/visit-briefs/.gitkeep`
- `family-health/03_outputs/reminder-messages/.gitkeep`
- `family-health/03_outputs/qa-summaries/.gitkeep`
- `family-health/99_runtime/inbox/.gitkeep`
- `family-health/99_runtime/staging/.gitkeep`
- `family-health/99_runtime/jobs/.gitkeep`
- `family-health/99_runtime/state/.gitkeep`
- `family-health/99_runtime/traces/.gitkeep`
- `family-health/examples/sample-input-event.json`

**Create tooling**
- `scripts/family_doctor/bootstrap_vault.py`
  - Copies canonical vault assets into any target directory.
- `scripts/family_doctor/validate_phase0.py`
  - Validates vault topology, contracts, templates, and sample event compatibility.

**Create tests**
- `tests/family_doctor/conftest.py`
  - Shared helpers for bootstrapping temporary vaults.
- `tests/family_doctor/test_bootstrap_vault.py`
  - Verifies copy behavior, idempotency, and topology.
- `tests/family_doctor/test_validate_phase0.py`
  - Verifies validation on canonical and mutated scaffolds.

**Do not create in Phase 0**
- Ingest/query/report/reminder business logic
- OCR integrations
- LLM provider integrations
- Reminder scheduler integrations

---

### Task 1: Establish Tooling and Write the Red Tests

**Files:**
- Create: `pyproject.toml`
- Create: `tests/family_doctor/conftest.py`
- Create: `tests/family_doctor/test_bootstrap_vault.py`
- Create: `tests/family_doctor/test_validate_phase0.py`

- [ ] **Step 1: Add minimal Python project config**

```toml
[project]
name = "family-doctor-foundation"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- [ ] **Step 2: Add shared test helpers**

```python
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "scripts" / "family_doctor" / "bootstrap_vault.py"
VALIDATE = ROOT / "scripts" / "family_doctor" / "validate_phase0.py"
CANONICAL = ROOT / "family-health"


def run_bootstrap(target: Path):
    return subprocess.run(
        [sys.executable, str(BOOTSTRAP), "--target", str(target)],
        capture_output=True,
        text=True,
    )


def run_validate(target: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATE), "--target", str(target)],
        capture_output=True,
        text=True,
    )
```

- [ ] **Step 3: Write the failing bootstrap tests**

```python
from pathlib import Path

from .conftest import run_bootstrap


def test_bootstrap_copies_full_phase0_topology(tmp_path):
    target = tmp_path / "family-health"
    result = run_bootstrap(target)

    assert result.returncode == 0
    assert (target / "00_schema" / "event-schema.json").exists()
    assert (target / "02_wiki" / "members").exists()
    assert (target / "99_runtime" / "jobs").exists()
    assert (target / "family-health").exists() is False


def test_bootstrap_is_idempotent(tmp_path):
    target = tmp_path / "family-health"
    first = run_bootstrap(target)
    second = run_bootstrap(target)

    assert first.returncode == 0
    assert second.returncode == 0
    assert "copied" in first.stdout.lower()
    assert "skipped" in second.stdout.lower() or "already exists" in second.stdout.lower()
```

- [ ] **Step 4: Write the failing validator tests**

```python
import json

from .conftest import run_bootstrap, run_validate


def test_validate_accepts_bootstrapped_phase0_vault(tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    result = run_validate(target)

    assert result.returncode == 0
    assert "phase 0 validation passed" in result.stdout.lower()


def test_validate_rejects_missing_runtime_directory(tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    (target / "99_runtime" / "jobs").rmdir()

    result = run_validate(target)

    assert result.returncode == 1
    assert "99_runtime/jobs" in result.stderr


def test_validate_rejects_incomplete_event_contract(tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["required_top_level_keys"] = ["event_id", "payload"]
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "required_top_level_keys" in result.stderr
```

- [ ] **Step 5: Run tests to verify they fail**

Run:

```bash
pytest tests/family_doctor/test_bootstrap_vault.py tests/family_doctor/test_validate_phase0.py -v
```

Expected:

- FAIL because canonical assets and CLIs do not exist yet.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml tests/family_doctor/conftest.py tests/family_doctor/test_bootstrap_vault.py tests/family_doctor/test_validate_phase0.py
git commit -m "test: add phase0 red tests and tooling config"
```

---

### Task 2: Create the Canonical Phase 0 Vault Assets

**Files:**
- Create: `family-health/AGENTS.md`
- Create: `family-health/index.md`
- Create: `family-health/log.md`
- Create: `family-health/00_schema/members.md`
- Create: `family-health/00_schema/reporting-rules.md`
- Create: `family-health/00_schema/reminder-rules.md`
- Create: `family-health/00_schema/event-schema.json`
- Create: `family-health/00_schema/runtime-entities.json`
- Create: `family-health/00_schema/page-templates/member-template.md`
- Create: `family-health/00_schema/page-templates/source-template.md`
- Create: `family-health/00_schema/page-templates/medication-template.md`
- Create: `family-health/00_schema/page-templates/condition-template.md`
- Create: `family-health/00_schema/page-templates/trend-template.md`
- Create: `family-health/00_schema/page-templates/plan-template.md`
- Create: `family-health/00_schema/page-templates/output-template.md`
- Create: `family-health/00_schema/page-templates/reminder-template.md`
- Create: `family-health/examples/sample-input-event.json`
- Create all `.gitkeep` files listed in the file map

- [ ] **Step 1: Create the canonical event contract**

```json
{
  "schema_version": "1.2",
  "required_top_level_keys": [
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
    "runtime"
  ],
  "allowed_event_types": ["ingest", "query", "report", "reminder"],
  "allowed_trigger_modes": ["user_message", "scheduled", "file_drop", "followup"],
  "field_shapes": {
    "actor": {
      "type": "object",
      "required_keys": ["actor_id", "role"]
    },
    "target": {
      "type": "object",
      "required_keys": ["member_hint", "match_confidence"],
      "optional_keys": ["member_id"]
    },
    "payload": {
      "type": "object",
      "required_keys": ["attachments", "source_refs"],
      "optional_keys": ["text", "report_kind", "reminder_action"]
    },
    "context": {
      "type": "object",
      "required_keys": ["source", "locale", "timezone"]
    },
    "runtime": {
      "type": "object",
      "required_keys": ["dedupe_scope"],
      "optional_keys": ["related_runtime_id", "review_item_id"]
    }
  },
  "event_type_rules": {
    "ingest": {
      "payload_at_least_one_of": ["text", "attachments"],
      "target_member_id": "recommended"
    },
    "query": {
      "payload_required_keys": ["text"]
    },
    "report": {
      "payload_required_keys": ["report_kind"]
    },
    "reminder": {
      "payload_required_keys": ["reminder_action"],
      "confirm_recommended_runtime_keys": ["related_runtime_id"]
    }
  },
  "attachment_shape": {
    "type": "object",
    "required_keys": ["attachment_id", "kind", "path"],
    "optional_keys": ["mime_type", "caption", "source_name", "content_sha256", "attachment_group_id"]
  }
}
```

- [ ] **Step 2: Create the canonical runtime entity registry**

```json
{
  "schema_version": "1.0",
  "entities": {
    "ingest_job": {
      "primary_key": "job_id",
      "statuses": ["created", "processing", "pending_review", "committed", "failed", "aborted"],
      "required_fields": ["job_id", "status", "planned_writes", "completed_writes"],
      "allowed_transitions": {
        "created": ["processing", "aborted"],
        "processing": ["pending_review", "committed", "failed"],
        "pending_review": ["processing", "aborted"],
        "failed": [],
        "committed": [],
        "aborted": []
      },
      "retention": "retain committed jobs for 30d; review and failed jobs until resolved",
      "log_identity_field": "job_id"
    },
    "report_job": {
      "primary_key": "job_id",
      "statuses": ["created", "processing", "pending_review", "committed", "failed", "aborted"],
      "required_fields": ["job_id", "status", "report_kind", "source_refs"],
      "allowed_transitions": {
        "created": ["processing", "aborted"],
        "processing": ["pending_review", "committed", "failed"],
        "pending_review": ["processing", "aborted"],
        "failed": [],
        "committed": [],
        "aborted": []
      },
      "retention": "retain committed jobs for 30d; review and failed jobs until resolved",
      "log_identity_field": "job_id"
    },
    "reminder_instance": {
      "primary_key": "runtime_id",
      "statuses": ["scheduled", "sent", "confirmed", "escalated", "expired"],
      "required_fields": ["runtime_id", "member_id", "item_id", "status", "scheduled_for"],
      "allowed_transitions": {
        "scheduled": ["sent", "expired"],
        "sent": ["confirmed", "escalated", "expired"],
        "confirmed": [],
        "escalated": ["confirmed", "expired"],
        "expired": []
      },
      "retention": "retain for 90d to support adherence summaries",
      "log_identity_field": "runtime_id"
    },
    "review_item": {
      "primary_key": "review_item_id",
      "statuses": ["open", "resolved", "dismissed"],
      "required_fields": ["review_item_id", "reason", "status", "source_refs"],
      "allowed_transitions": {
        "open": ["resolved", "dismissed"],
        "resolved": [],
        "dismissed": []
      },
      "retention": "retain until manually closed, then archive after 30d",
      "log_identity_field": "review_item_id"
    },
    "dedupe_record": {
      "primary_key": "dedupe_key",
      "statuses": ["active", "archived"],
      "required_fields": ["dedupe_key", "scope", "first_seen_at", "result"],
      "allowed_transitions": {
        "active": ["archived"],
        "archived": []
      },
      "retention": "retain active for 30d; archived for audit as needed",
      "log_identity_field": "dedupe_key"
    }
  }
}
```

- [ ] **Step 3: Create the canonical sample event**

```json
{
  "event_id": "evt_sample_001",
  "request_id": "req_sample_001",
  "idempotency_key": "sha256:sample",
  "correlation_id": "corr_sample_001",
  "causation_id": null,
  "event_type": "ingest",
  "trigger_mode": "user_message",
  "occurred_at": "2026-04-19T21:30:00+08:00",
  "actor": {
    "actor_id": "user_admin",
    "role": "caregiver"
  },
  "target": {
    "member_id": "dad",
    "member_hint": "爸爸",
    "match_confidence": 1.0
  },
  "payload": {
    "text": "这是爸爸的体检报告",
    "attachments": [
      {
        "attachment_id": "att_001",
        "kind": "image",
        "path": "/abs/path/to/report.jpg",
        "mime_type": "image/jpeg",
        "caption": "爸爸 2026 年 4 月体检报告第一页",
        "source_name": "report.jpg",
        "content_sha256": "sha256:sample-report",
        "attachment_group_id": "grp_2026_04_19_01"
      }
    ],
    "source_refs": []
  },
  "context": {
    "source": "canonical-sample",
    "locale": "zh-CN",
    "timezone": "Asia/Shanghai"
  },
  "runtime": {
    "dedupe_scope": "family-health"
  }
}
```

- [ ] **Step 4: Create minimal but meaningful template content**

Example `member-template.md`:

```md
---
type: member
member_id: example_member
display_name: 示例成员
---

# 示例成员

## 基本信息
## 成员识别与代理关系
## 慢性病与重要问题
## 过敏史与禁忌
## 当前用药
## 最近关键指标
## 待处理事项
## 最近资料
## 关联页面
## 待核实项
```

Example `source-template.md`:

```md
---
type: source
source_id: example_source
member_id: example_member
source_kind: checkup_report
source_path: 01_raw/reports/example-report.pdf
event_date: 2026-04-19
---

# 示例来源

## 来源信息
## 提取出的结构化事实
## 异常项
## 与历史差异
## 更新影响
## 关联页面
## 待核实项
```

Example `output-template.md`:

```md
---
type: output
output_id: example_output
output_kind: weekly_report
member_scope: family
member_id: example_member
source_refs:
  - example_source
---

# 示例输出

## 结论摘要
## 证据来源
## 关联页面
## 事实
## 推断
## 建议
## 待核实项
## 后续动作
```

- [ ] **Step 5: Run the red tests again**

Run:

```bash
pytest tests/family_doctor/test_bootstrap_vault.py tests/family_doctor/test_validate_phase0.py -v
```

Expected:

- Still FAIL because bootstrap and validator CLIs do not exist yet.
- Failure has moved from “missing canonical assets” toward “missing scripts”.

- [ ] **Step 6: Commit**

```bash
git add family-health
git commit -m "feat: add canonical phase0 vault assets"
```

---

### Task 3: Implement the Bootstrap CLI Against Canonical Assets

**Files:**
- Create: `scripts/family_doctor/bootstrap_vault.py`
- Test: `tests/family_doctor/test_bootstrap_vault.py`

- [ ] **Step 1: Implement bootstrap as a canonical-asset copier**

```python
from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = ROOT / "family-health"


def copy_missing(src: Path, dst: Path, logs: list[str]) -> None:
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            logs.append(f"skipped {target}")
            continue
        target.write_bytes(path.read_bytes())
        logs.append(f"copied {target}")


def bootstrap(target: Path) -> list[str]:
    logs: list[str] = []
    target.mkdir(parents=True, exist_ok=True)
    copy_missing(CANONICAL_ROOT, target, logs)
    return logs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, type=Path)
    args = parser.parse_args()

    for line in bootstrap(args.target):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run bootstrap tests**

Run:

```bash
pytest tests/family_doctor/test_bootstrap_vault.py -v
```

Expected:

- PASS for topology copy and idempotency.

- [ ] **Step 3: Smoke-test a fresh target**

Run:

```bash
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-phase0-smoke
```

Expected:

- `/tmp/family-health-phase0-smoke/00_schema/event-schema.json` exists.
- `/tmp/family-health-phase0-smoke/99_runtime/jobs` exists.

- [ ] **Step 4: Commit**

```bash
git add scripts/family_doctor/bootstrap_vault.py
git commit -m "feat: add canonical vault bootstrap cli"
```

---

### Task 4: Implement the Validator CLI with Real Contract Checks

**Files:**
- Create: `scripts/family_doctor/validate_phase0.py`
- Modify: `tests/family_doctor/test_validate_phase0.py`

- [ ] **Step 1: Implement directory topology validation**

```python
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
    "03_outputs/checkup-updates",
    "03_outputs/weekly-reports",
    "03_outputs/monthly-reports",
    "03_outputs/visit-briefs",
    "03_outputs/reminder-messages",
    "03_outputs/qa-summaries",
    "99_runtime/inbox",
    "99_runtime/staging",
    "99_runtime/jobs",
    "99_runtime/state",
    "99_runtime/traces",
]
```

- [ ] **Step 2: Implement template and contract validation**

```python
TEMPLATE_MARKERS = {
    "member-template.md": ["type: member", "## 基本信息", "## 当前用药"],
    "source-template.md": ["type: source", "## 来源信息", "## 提取出的结构化事实"],
    "medication-template.md": ["type: medication", "display_name:", "## 适应证", "## 漏服规则"],
    "condition-template.md": ["type: condition", "display_name:", "## 涉及成员", "## 关键证据"],
    "trend-template.md": ["type: trend", "## 关键指标表", "## 趋势判断"],
    "plan-template.md": ["type: plan", "## 当前目标", "## 待复查事项"],
    "output-template.md": ["type: output", "output_kind:", "source_refs:", "## 结论摘要", "## 证据来源", "## 待核实项"],
    "reminder-template.md": ["type: reminder", "runtime_id:", "status:", "scheduled_for:", "## 提醒内容", "## 运行时映射"],
}


def validate_event_schema(schema: dict) -> list[str]:
    errors: list[str] = []
    required = set(schema.get("required_top_level_keys", []))
    expected = {
        "event_id", "request_id", "idempotency_key", "correlation_id", "causation_id",
        "event_type", "trigger_mode", "occurred_at", "actor", "target",
        "payload", "context", "runtime",
    }
    if required != expected:
        errors.append("event-schema.json has incorrect required_top_level_keys")
    if set(schema.get("allowed_event_types", [])) != {"ingest", "query", "report", "reminder"}:
        errors.append("event-schema.json has incorrect allowed_event_types")
    if set(schema.get("allowed_trigger_modes", [])) != {"user_message", "scheduled", "file_drop", "followup"}:
        errors.append("event-schema.json has incorrect allowed_trigger_modes")
    field_shapes = schema.get("field_shapes", {})
    for key in ["actor", "target", "payload", "context", "runtime"]:
        if key not in field_shapes:
            errors.append(f"event-schema.json missing field_shapes.{key}")
    if set(field_shapes.get("target", {}).get("required_keys", [])) != {"member_hint", "match_confidence"}:
        errors.append("event-schema.json target required_keys are incorrect")
    if set(field_shapes.get("target", {}).get("optional_keys", [])) != {"member_id"}:
        errors.append("event-schema.json target optional_keys are incorrect")
    if set(field_shapes.get("payload", {}).get("required_keys", [])) != {"attachments", "source_refs"}:
        errors.append("event-schema.json payload required_keys are incorrect")
    if set(field_shapes.get("payload", {}).get("optional_keys", [])) != {"text", "report_kind", "reminder_action"}:
        errors.append("event-schema.json payload optional_keys are incorrect")
    if set(field_shapes.get("runtime", {}).get("required_keys", [])) != {"dedupe_scope"}:
        errors.append("event-schema.json runtime required_keys are incorrect")
    if set(field_shapes.get("runtime", {}).get("optional_keys", [])) != {"related_runtime_id", "review_item_id"}:
        errors.append("event-schema.json runtime optional_keys are incorrect")
    rules = schema.get("event_type_rules", {})
    for key in ["ingest", "query", "report", "reminder"]:
        if key not in rules:
            errors.append(f"event-schema.json missing event_type_rules.{key}")
    if rules.get("ingest", {}).get("target_member_id") != "recommended":
        errors.append("event-schema.json ingest target_member_id rule is incorrect")
    if rules.get("report", {}).get("payload_required_keys") != ["report_kind"]:
        errors.append("event-schema.json report payload_required_keys are incorrect")
    if rules.get("reminder", {}).get("payload_required_keys") != ["reminder_action"]:
        errors.append("event-schema.json reminder payload_required_keys are incorrect")
    if rules.get("reminder", {}).get("confirm_recommended_runtime_keys") != ["related_runtime_id"]:
        errors.append("event-schema.json reminder confirm_recommended_runtime_keys are incorrect")
    if "attachment_shape" not in schema:
        errors.append("event-schema.json missing attachment_shape")
    elif set(schema["attachment_shape"].get("required_keys", [])) != {"attachment_id", "kind", "path"}:
        errors.append("event-schema.json attachment_shape required_keys are incorrect")
    payload_properties = field_shapes.get("payload", {}).get("properties", {})
    if set(payload_properties.get("report_kind", {}).get("enum", [])) != {
        "checkup_update", "weekly_health_report", "monthly_health_report", "visit_brief"
    }:
        errors.append("event-schema.json report_kind enum is incorrect")
    if set(payload_properties.get("reminder_action", {}).get("enum", [])) != {
        "generate", "confirm", "escalate"
    }:
        errors.append("event-schema.json reminder_action enum is incorrect")
    if set(schema.get("attachment_shape", {}).get("properties", {}).get("kind", {}).get("enum", [])) != {
        "image", "pdf", "text", "csv", "zip"
    }:
        errors.append("event-schema.json attachment kind enum is incorrect")
    return errors


def validate_runtime_entities(registry: dict) -> list[str]:
    errors: list[str] = []
    entities = registry.get("entities", {})
    for name in ["ingest_job", "report_job", "reminder_instance", "review_item", "dedupe_record"]:
        entity = entities.get(name)
        if not entity:
            errors.append(f"Missing runtime entity: {name}")
            continue
        for key in ["primary_key", "statuses", "required_fields", "allowed_transitions", "retention", "log_identity_field"]:
            if key not in entity:
                errors.append(f"{name} missing {key}")
        if entity.get("primary_key") and entity["primary_key"] not in entity.get("required_fields", []):
            errors.append(f"{name} primary_key not listed in required_fields")
        if entity.get("log_identity_field") and entity["log_identity_field"] not in entity.get("required_fields", []):
            errors.append(f"{name} log_identity_field not listed in required_fields")
        statuses = set(entity.get("statuses", []))
        for from_status, to_statuses in entity.get("allowed_transitions", {}).items():
            if from_status not in statuses:
                errors.append(f"{name} transition source {from_status} not declared in statuses")
            for target_status in to_statuses:
                if target_status not in statuses:
                    errors.append(f"{name} transition target {target_status} not declared in statuses")
    return errors
```

- [ ] **Step 3: Validate that the sample event matches the event contract**

```python
def validate_sample_event(schema: dict, sample: dict) -> list[str]:
    errors: list[str] = []
    for key in schema["required_top_level_keys"]:
        if key not in sample:
            errors.append(f"sample-input-event.json missing {key}")
    if sample.get("event_type") not in schema["allowed_event_types"]:
        errors.append("sample-input-event.json has invalid event_type")
    if sample.get("trigger_mode") not in schema["allowed_trigger_modes"]:
        errors.append("sample-input-event.json has invalid trigger_mode")
    target_shape = schema["field_shapes"]["target"]
    runtime_shape = schema["field_shapes"]["runtime"]
    payload_shape = schema["field_shapes"]["payload"]
    for key in target_shape["required_keys"]:
        if key not in sample.get("target", {}):
            errors.append(f"sample-input-event.json target missing {key}")
    for key in runtime_shape["required_keys"]:
        if key not in sample.get("runtime", {}):
            errors.append(f"sample-input-event.json runtime missing {key}")
    for key in sample.get("runtime", {}):
        if key not in set(runtime_shape["required_keys"]) | set(runtime_shape.get("optional_keys", [])):
            errors.append(f"sample-input-event.json runtime has unsupported key {key}")
    for key in sample.get("payload", {}):
        if key not in set(payload_shape["required_keys"]) | set(payload_shape.get("optional_keys", [])):
            errors.append(f"sample-input-event.json payload has unsupported key {key}")
    for attachment in sample.get("payload", {}).get("attachments", []):
        for key in schema["attachment_shape"]["required_keys"]:
            if key not in attachment:
                errors.append(f"sample-input-event.json attachment missing {key}")
    event_rules = schema["event_type_rules"][sample["event_type"]]
    for key in event_rules.get("payload_required_keys", []):
        if key not in sample.get("payload", {}):
            errors.append(f"sample-input-event.json payload missing {key} for {sample['event_type']}")
    if "payload_at_least_one_of" in event_rules:
        if not any(sample.get("payload", {}).get(key) for key in event_rules["payload_at_least_one_of"]):
            errors.append("sample-input-event.json payload missing required ingest text/attachments")
    return errors
```

- [ ] **Step 4: Run validator tests**

Run:

```bash
pytest tests/family_doctor/test_validate_phase0.py -v
```

Expected:

- PASS for positive validation.
- PASS for missing directory, incomplete event contract, and invalid runtime registry cases.

- [ ] **Step 5: Commit**

```bash
git add scripts/family_doctor/validate_phase0.py tests/family_doctor/test_validate_phase0.py
git commit -m "feat: add phase0 validator with contract checks"
```

---

### Task 5: Lock the Acceptance Baseline and Simplify Negative Fixtures

**Files:**
- Modify: `tests/family_doctor/test_validate_phase0.py`
- Modify: `docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md`

- [ ] **Step 1: Use dynamic fixture mutation instead of placeholder fixture directories**

```python
import json


def test_validate_rejects_invalid_runtime_registry(tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    registry_path = target / "00_schema" / "runtime-entities.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    del registry["entities"]["review_item"]["statuses"]
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "review_item missing statuses" in result.stderr
```

- [ ] **Step 2: Add event-contract negative tests that prove sample compatibility is enforced**

```python
import json


def test_validate_rejects_invalid_sample_event(tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    sample_path = target / "examples" / "sample-input-event.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    del sample["runtime"]["dedupe_scope"]
    sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "runtime missing dedupe_scope" in result.stderr


def test_validate_rejects_invalid_trigger_mode_contract(tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    schema_path = target / "00_schema" / "event-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema["allowed_trigger_modes"] = ["user_message"]
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_validate(target)

    assert result.returncode == 1
    assert "allowed_trigger_modes" in result.stderr
```

- [ ] **Step 3: Add an explicit acceptance baseline test**

```python
def test_phase0_acceptance_baseline(tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    result = run_validate(target)

    assert result.returncode == 0
    assert (target / "02_wiki" / "members").exists()
    assert (target / "99_runtime" / "jobs").exists()
    assert "phase 0 validation passed" in result.stdout.lower()
```

- [ ] **Step 4: Update the spec Phase 0 exit criteria**

Add this bullet under `Phase 0 / 退出标准` in the spec:

```md
- `python3 scripts/family_doctor/validate_phase0.py --target <vault>` passes on the canonical scaffold and a fresh bootstrapped copy
```

- [ ] **Step 5: Run the full Phase 0 test suite**

Run:

```bash
pytest tests/family_doctor -v
```

Expected:

- All Phase 0 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/family_doctor docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md
git commit -m "test: lock phase0 acceptance baseline"
```

---

### Task 6: Final Verification and Handoff

**Files:**
- Verify: `family-health/`
- Verify: `scripts/family_doctor/`
- Verify: `tests/family_doctor/`

- [ ] **Step 1: Validate the canonical scaffold**

Run:

```bash
python3 scripts/family_doctor/validate_phase0.py --target /Users/loutussun/Documents/codex/AIHealth/family-health
```

Expected:

- `Phase 0 validation passed`

- [ ] **Step 2: Re-bootstrap into a fresh temporary location**

Run:

```bash
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-phase0-final
```

Expected:

- Fresh scaffold copied without errors.

- [ ] **Step 3: Validate the fresh copy**

Run:

```bash
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-phase0-final
```

Expected:

- `Phase 0 validation passed`

- [ ] **Step 4: Run all tests**

Run:

```bash
pytest tests/family_doctor -v
```

Expected:

- All tests PASS.

- [ ] **Step 5: Capture Phase 0 handoff notes**

```text
- Canonical family-health scaffold created and versioned in-repo
- Bootstrap CLI reproduces the scaffold in arbitrary targets
- Validator proves topology, contracts, templates, and sample-event compatibility
- Phase 0 is now stable enough to begin ingest MVP work
```

- [ ] **Step 6: Commit**

```bash
git add family-health scripts/family_doctor tests/family_doctor pyproject.toml docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md
git commit -m "feat: complete family-doctor phase0 foundation"
```
