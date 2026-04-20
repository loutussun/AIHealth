# Family Doctor Phase 0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Phase 0 foundation for the `family-doctor` project: a reproducible `family-health/` vault scaffold, machine-readable schema files, runtime entity definitions, and validation tooling that proves the structure is stable before Phase 1 begins.

**Architecture:** This phase is Markdown-first and file-system-first. The vault itself lives under `family-health/`, while small Python CLIs create and validate that vault. `00_schema/` stores rules and machine-readable contracts, `99_runtime/` stores process-state entities, and pytest fixtures enforce that the foundation remains deterministic and safe to extend.

**Tech Stack:** Markdown, YAML frontmatter, JSON, Python 3 standard library, pytest

---

## Planned File Map

**Create at repo root**
- `pyproject.toml`
  - Minimal Python project metadata and pytest config.

**Create vault scaffold**
- `family-health/AGENTS.md`
  - System rules for the skill, scoped to the vault.
- `family-health/index.md`
  - Global navigation page.
- `family-health/log.md`
  - Append-only operation log placeholder.
- `family-health/00_schema/members.md`
  - Member registry starter template.
- `family-health/00_schema/reporting-rules.md`
  - Report generation rule scaffold.
- `family-health/00_schema/reminder-rules.md`
  - Reminder rule scaffold.
- `family-health/00_schema/event-schema.json`
  - Machine-readable event contract for `family-doctor`.
- `family-health/00_schema/runtime-entities.json`
  - Machine-readable definitions for `ingest_job`, `report_job`, `reminder_instance`, `review_item`, `dedupe_record`.
- `family-health/00_schema/page-templates/member-template.md`
- `family-health/00_schema/page-templates/source-template.md`
- `family-health/00_schema/page-templates/medication-template.md`
- `family-health/00_schema/page-templates/condition-template.md`
- `family-health/00_schema/page-templates/trend-template.md`
- `family-health/00_schema/page-templates/plan-template.md`
- `family-health/00_schema/page-templates/output-template.md`
- `family-health/01_raw/.gitkeep`
- `family-health/02_wiki/.gitkeep`
- `family-health/03_outputs/.gitkeep`
- `family-health/99_runtime/.gitkeep`

**Create tooling**
- `scripts/family_doctor/bootstrap_vault.py`
  - CLI that creates the Phase 0 scaffold idempotently.
- `scripts/family_doctor/validate_phase0.py`
  - CLI that validates directory structure, schema files, and starter templates.

**Create examples and tests**
- `family-health/examples/sample-input-event.json`
  - Canonical example for the event schema.
- `tests/family_doctor/test_bootstrap_vault.py`
  - Verifies scaffold creation and idempotency.
- `tests/family_doctor/test_validate_phase0.py`
  - Verifies validation behavior on good and bad fixtures.
- `tests/family_doctor/fixtures/invalid-missing-runtime-entity/`
  - Broken fixture for validator failure case.
- `tests/family_doctor/fixtures/invalid-missing-template/`
  - Broken fixture for validator failure case.

**Do not create in Phase 0**
- Any ingest/query/report/reminder business logic
- Any OCR integration
- Any real reminder scheduler
- Any LLM provider integration

---

### Task 1: Establish Python Tooling and Failing Tests

**Files:**
- Create: `pyproject.toml`
- Create: `tests/family_doctor/test_bootstrap_vault.py`
- Create: `tests/family_doctor/test_validate_phase0.py`

- [ ] **Step 1: Write the failing bootstrap tests**

```python
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "scripts" / "family_doctor" / "bootstrap_vault.py"


def test_bootstrap_creates_expected_structure(tmp_path):
    target = tmp_path / "family-health"
    result = subprocess.run(
        [sys.executable, str(BOOTSTRAP), "--target", str(target)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (target / "AGENTS.md").exists()
    assert (target / "00_schema" / "event-schema.json").exists()
    assert (target / "00_schema" / "page-templates" / "member-template.md").exists()
    assert (target / "99_runtime").exists()


def test_bootstrap_is_idempotent(tmp_path):
    target = tmp_path / "family-health"
    first = subprocess.run(
        [sys.executable, str(BOOTSTRAP), "--target", str(target)],
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        [sys.executable, str(BOOTSTRAP), "--target", str(target)],
        capture_output=True,
        text=True,
    )

    assert first.returncode == 0
    assert second.returncode == 0
    assert "created" in first.stdout.lower()
    assert "already exists" in second.stdout.lower() or "skipped" in second.stdout.lower()
```

- [ ] **Step 2: Write the failing validator tests**

```python
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "scripts" / "family_doctor" / "bootstrap_vault.py"
VALIDATE = ROOT / "scripts" / "family_doctor" / "validate_phase0.py"


def test_validate_phase0_accepts_bootstrapped_vault(tmp_path):
    target = tmp_path / "family-health"
    subprocess.run([sys.executable, str(BOOTSTRAP), "--target", str(target)], check=True)

    result = subprocess.run(
        [sys.executable, str(VALIDATE), "--target", str(target)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "phase 0 validation passed" in result.stdout.lower()


def test_validate_phase0_rejects_missing_runtime_schema(tmp_path):
    target = tmp_path / "family-health"
    subprocess.run([sys.executable, str(BOOTSTRAP), "--target", str(target)], check=True)
    (target / "00_schema" / "runtime-entities.json").unlink()

    result = subprocess.run(
        [sys.executable, str(VALIDATE), "--target", str(target)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "runtime-entities.json" in result.stderr
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
pytest tests/family_doctor/test_bootstrap_vault.py tests/family_doctor/test_validate_phase0.py -v
```

Expected:

- FAIL because `scripts/family_doctor/bootstrap_vault.py` and `scripts/family_doctor/validate_phase0.py` do not exist yet.

- [ ] **Step 4: Add minimal Python project config**

```toml
[project]
name = "family-doctor-foundation"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/family_doctor/test_bootstrap_vault.py tests/family_doctor/test_validate_phase0.py
git commit -m "test: add phase0 foundation failing tests"
```

---

### Task 2: Implement the Vault Bootstrap CLI

**Files:**
- Create: `scripts/family_doctor/bootstrap_vault.py`
- Create: `family-health/AGENTS.md`
- Create: `family-health/index.md`
- Create: `family-health/log.md`
- Create: `family-health/00_schema/members.md`
- Create: `family-health/00_schema/reporting-rules.md`
- Create: `family-health/00_schema/reminder-rules.md`
- Create: `family-health/00_schema/page-templates/member-template.md`
- Create: `family-health/00_schema/page-templates/source-template.md`
- Create: `family-health/00_schema/page-templates/medication-template.md`
- Create: `family-health/00_schema/page-templates/condition-template.md`
- Create: `family-health/00_schema/page-templates/trend-template.md`
- Create: `family-health/00_schema/page-templates/plan-template.md`
- Create: `family-health/00_schema/page-templates/output-template.md`
- Create: `family-health/01_raw/.gitkeep`
- Create: `family-health/02_wiki/.gitkeep`
- Create: `family-health/03_outputs/.gitkeep`
- Create: `family-health/99_runtime/.gitkeep`

- [ ] **Step 1: Implement the bootstrap CLI with deterministic file creation**

```python
from __future__ import annotations

import argparse
from pathlib import Path


DIRECTORIES = [
    "00_schema/page-templates",
    "01_raw",
    "02_wiki",
    "03_outputs",
    "99_runtime",
]

FILES = {
    "AGENTS.md": "# Family Health Vault Rules\n",
    "index.md": "# Family Health Index\n",
    "log.md": "# Operation Log\n",
    "00_schema/members.md": "# Members Registry\n",
    "00_schema/reporting-rules.md": "# Reporting Rules\n",
    "00_schema/reminder-rules.md": "# Reminder Rules\n",
    "00_schema/page-templates/member-template.md": "---\ntype: member\n---\n",
    "00_schema/page-templates/source-template.md": "---\ntype: source\n---\n",
    "00_schema/page-templates/medication-template.md": "---\ntype: medication\n---\n",
    "00_schema/page-templates/condition-template.md": "---\ntype: condition\n---\n",
    "00_schema/page-templates/trend-template.md": "---\ntype: trend\n---\n",
    "00_schema/page-templates/plan-template.md": "---\ntype: plan\n---\n",
    "00_schema/page-templates/output-template.md": "---\ntype: output\n---\n",
    "01_raw/.gitkeep": "",
    "02_wiki/.gitkeep": "",
    "03_outputs/.gitkeep": "",
    "99_runtime/.gitkeep": "",
}


def ensure_file(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return f"skipped {path}"
    path.write_text(content, encoding="utf-8")
    return f"created {path}"


def bootstrap(target: Path) -> list[str]:
    logs: list[str] = []
    target.mkdir(parents=True, exist_ok=True)
    for rel_dir in DIRECTORIES:
        directory = target / rel_dir
        directory.mkdir(parents=True, exist_ok=True)
        logs.append(f"ensured {directory}")
    for rel_file, content in FILES.items():
        logs.append(ensure_file(target / rel_file, content))
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

- [ ] **Step 2: Run bootstrap tests to verify they pass**

Run:

```bash
pytest tests/family_doctor/test_bootstrap_vault.py -v
```

Expected:

- PASS for both scaffold creation and idempotency.

- [ ] **Step 3: Smoke-test the generated vault**

Run:

```bash
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-phase0-smoke
```

Expected:

- Output lists created or ensured paths.
- `/tmp/family-health-phase0-smoke/AGENTS.md` exists.

- [ ] **Step 4: Commit**

```bash
git add scripts/family_doctor/bootstrap_vault.py family-health pyproject.toml
git commit -m "feat: add phase0 vault bootstrap scaffold"
```

---

### Task 3: Add Machine-Readable Contracts for Events and Runtime Entities

**Files:**
- Create: `family-health/00_schema/event-schema.json`
- Create: `family-health/00_schema/runtime-entities.json`
- Create: `family-health/examples/sample-input-event.json`

- [ ] **Step 1: Write the failing validator expectation for schema files**

Add this assertion to `tests/family_doctor/test_validate_phase0.py`:

```python
def test_validate_phase0_checks_event_schema_shape(tmp_path):
    target = tmp_path / "family-health"
    subprocess.run([sys.executable, str(BOOTSTRAP), "--target", str(target)], check=True)

    event_schema = target / "00_schema" / "event-schema.json"
    event_schema.write_text('{"type":"object","properties":{}}', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(VALIDATE), "--target", str(target)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "required top-level keys" in result.stderr.lower()
```

- [ ] **Step 2: Define the event schema contract**

```json
{
  "schema_version": "1.0",
  "type": "object",
  "required_top_level_keys": [
    "event_id",
    "request_id",
    "idempotency_key",
    "correlation_id",
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
  "allowed_trigger_modes": ["user_message", "scheduled", "file_drop", "followup"]
}
```

- [ ] **Step 3: Define the runtime entity registry**

```json
{
  "schema_version": "1.0",
  "entities": {
    "ingest_job": ["job_id", "status", "planned_writes", "completed_writes"],
    "report_job": ["job_id", "status", "report_kind", "source_refs"],
    "reminder_instance": ["runtime_id", "member_id", "item_id", "status", "scheduled_for"],
    "review_item": ["review_item_id", "reason", "status", "source_refs"],
    "dedupe_record": ["dedupe_key", "scope", "first_seen_at", "result"]
  }
}
```

- [ ] **Step 4: Add the canonical sample input event**

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
  "actor": {"actor_id": "user_admin", "role": "caregiver"},
  "target": {"member_id": "dad", "member_hint": "爸爸", "match_confidence": 1.0},
  "payload": {"text": "这是爸爸的体检报告", "attachments": [], "source_refs": []},
  "context": {"source": "test-fixture", "locale": "zh-CN", "timezone": "Asia/Shanghai"},
  "runtime": {"related_runtime_id": null, "review_item_id": null, "dedupe_scope": "family-health"}
}
```

- [ ] **Step 5: Commit**

```bash
git add family-health/00_schema/event-schema.json family-health/00_schema/runtime-entities.json family-health/examples/sample-input-event.json tests/family_doctor/test_validate_phase0.py
git commit -m "feat: add phase0 machine-readable contracts"
```

---

### Task 4: Implement the Phase 0 Validator CLI

**Files:**
- Create: `scripts/family_doctor/validate_phase0.py`
- Modify: `tests/family_doctor/test_validate_phase0.py`

- [ ] **Step 1: Implement the validator CLI**

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_PATHS = [
    "AGENTS.md",
    "index.md",
    "log.md",
    "00_schema/members.md",
    "00_schema/reporting-rules.md",
    "00_schema/reminder-rules.md",
    "00_schema/event-schema.json",
    "00_schema/runtime-entities.json",
    "00_schema/page-templates/member-template.md",
    "00_schema/page-templates/source-template.md",
    "00_schema/page-templates/medication-template.md",
    "00_schema/page-templates/condition-template.md",
    "00_schema/page-templates/trend-template.md",
    "00_schema/page-templates/plan-template.md",
    "00_schema/page-templates/output-template.md",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_required_paths(target: Path) -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_PATHS:
        if not (target / rel).exists():
            errors.append(f"Missing required path: {rel}")
    return errors


def validate_event_schema(target: Path) -> list[str]:
    data = load_json(target / "00_schema" / "event-schema.json")
    required = set(data.get("required_top_level_keys", []))
    minimum = {"event_id", "event_type", "payload", "runtime"}
    if not minimum.issubset(required):
        return ["event-schema.json missing required top-level keys"]
    return []


def validate_runtime_entities(target: Path) -> list[str]:
    data = load_json(target / "00_schema" / "runtime-entities.json")
    entities = data.get("entities", {})
    required_entities = {"ingest_job", "report_job", "reminder_instance", "review_item", "dedupe_record"}
    if not required_entities.issubset(set(entities)):
        return ["runtime-entities.json missing required runtime entities"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, type=Path)
    args = parser.parse_args()

    errors = []
    errors.extend(validate_required_paths(args.target))
    if not errors:
        errors.extend(validate_event_schema(args.target))
        errors.extend(validate_runtime_entities(args.target))

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print("Phase 0 validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run validator tests**

Run:

```bash
pytest tests/family_doctor/test_validate_phase0.py -v
```

Expected:

- PASS for bootstrapped vault validation.
- PASS for broken fixture rejection.

- [ ] **Step 3: Run end-to-end validation against the in-repo scaffold**

Run:

```bash
python3 scripts/family_doctor/validate_phase0.py --target /Users/loutussun/Documents/codex/AIHealth/family-health
```

Expected:

- `Phase 0 validation passed`

- [ ] **Step 4: Commit**

```bash
git add scripts/family_doctor/validate_phase0.py tests/family_doctor/test_validate_phase0.py
git commit -m "feat: add phase0 structure validator"
```

---

### Task 5: Add Broken Fixtures and Lock the Acceptance Baseline

**Files:**
- Create: `tests/family_doctor/fixtures/invalid-missing-runtime-entity/README.md`
- Create: `tests/family_doctor/fixtures/invalid-missing-template/README.md`
- Modify: `tests/family_doctor/test_validate_phase0.py`
- Modify: `docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md`

- [ ] **Step 1: Replace placeholder fixture dirs with executable fixture setup inside tests**

```python
def make_invalid_missing_template_fixture(tmp_path, bootstrap):
    target = tmp_path / "family-health"
    bootstrap(target)
    (target / "00_schema" / "page-templates" / "member-template.md").unlink()
    return target


def make_invalid_missing_runtime_entity_fixture(tmp_path, bootstrap):
    target = tmp_path / "family-health"
    bootstrap(target)
    runtime_path = target / "00_schema" / "runtime-entities.json"
    runtime_path.write_text(
        '{"schema_version":"1.0","entities":{"ingest_job":[]}}',
        encoding="utf-8",
    )
    return target
```

- [ ] **Step 2: Add the fixed acceptance baseline cases**

```python
def test_phase0_acceptance_baseline(tmp_path):
    target = tmp_path / "family-health"
    subprocess.run([sys.executable, str(BOOTSTRAP), "--target", str(target)], check=True)

    result = subprocess.run(
        [sys.executable, str(VALIDATE), "--target", str(target)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Phase 0 validation passed" in result.stdout
```

- [ ] **Step 3: Update the spec to reference the Phase 0 acceptance gate**

Add one sentence under `7.2 / Phase 0` exit criteria:

```md
- `python3 scripts/family_doctor/validate_phase0.py --target <vault>` passes on the canonical scaffold
```

- [ ] **Step 4: Run the full Phase 0 test suite**

Run:

```bash
pytest tests/family_doctor -v
```

Expected:

- All Phase 0 tests PASS.

- [ ] **Step 5: Commit**

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

- [ ] **Step 1: Re-run bootstrap into a fresh temp directory**

Run:

```bash
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-phase0-final
```

Expected:

- Fresh scaffold created without errors.

- [ ] **Step 2: Validate the fresh scaffold**

Run:

```bash
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-phase0-final
```

Expected:

- `Phase 0 validation passed`

- [ ] **Step 3: Run all tests**

Run:

```bash
pytest tests/family_doctor -v
```

Expected:

- All tests PASS.

- [ ] **Step 4: Capture the Phase 0 implementation notes**

Write a short summary in the PR / handoff description:

```text
- Added deterministic family-health scaffold
- Added machine-readable event and runtime contracts
- Added validator CLI and acceptance tests
- Confirmed Phase 0 scaffold is reproducible and idempotent
```

- [ ] **Step 5: Commit**

```bash
git add family-health scripts/family_doctor tests/family_doctor pyproject.toml
git commit -m "feat: complete family-doctor phase0 foundation"
```
