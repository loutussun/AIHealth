# Phase C.0 Tracking Append Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone deterministic helper that appends one validated row to one canonical `04_tracking/*.csv` file.

**Architecture:** Implement a small Python module, `family_doctor/tracking_append.py`, that owns the table registry, validation, and CSV append behavior. Add a thin standalone CLI wrapper, `scripts/family_doctor/append_tracking_row.py`, that parses arguments, loads row JSON, prints JSON results, and exits non-zero on errors. Do not add a `run_skill.py` route, do not add an `event_type`, and do not wire this into `family_doctor/skill_router.py`.

**Tech Stack:** Python standard library (`argparse`, `csv`, `json`, `pathlib`, dataclasses), pytest, subprocess CLI tests, Markdown skill docs

---

## Source Spec

Implement from:

- `docs/superpowers/obsidian-first-llm-wiki/phase-c0-tracking-append-helper-design.md`

Do not broaden scope beyond that design.

## File Map

- Create: `family_doctor/tracking_append.py`
  - Owns canonical table registry, row validation, header validation, append behavior, and structured result/error objects.
- Create: `scripts/family_doctor/append_tracking_row.py`
  - Thin CLI wrapper around `family_doctor.tracking_append`.
  - Emits JSON to stdout for both success and handled errors.
- Create: `tests/family_doctor/test_tracking_append.py`
  - Module-level TDD coverage for append behavior and validation.
- Create: `tests/family_doctor/test_append_tracking_row_cli.py`
  - CLI-level TDD coverage for stdout JSON, exit codes, and row JSON loading.
- Modify: `.codex/skills/family-doctor/SKILL.md`
  - Teach host LLMs to prefer the helper for `daily_tracking_update` append requests.
- Modify: `.claude/skills/family-doctor.md`
  - Mirror the helper rule without claiming a new route.
- Modify: `tests/family_doctor/test_skill_workflow_contract_docs.py`
  - Lock that both skill docs mention the helper while still forbidding new route/event claims.
- Modify: `docs/superpowers/obsidian-first-llm-wiki/README.md`
  - Add this plan to the document index.
  - Mark Phase C.0 complete only after implementation and verification pass.

## Canonical Table Registry

Use exactly this registry in `family_doctor/tracking_append.py`:

```python
TRACKING_TABLES = {
    "checkup": {
        "relative_path": "04_tracking/体检指标.csv",
        "header": [
            "member_id",
            "date",
            "item",
            "result",
            "unit",
            "reference_range",
            "status",
            "source_ref",
            "notes",
        ],
    },
    "medication": {
        "relative_path": "04_tracking/用药打卡.csv",
        "header": [
            "member_id",
            "date",
            "time",
            "medication_id",
            "dose",
            "status",
            "source_ref",
            "notes",
        ],
    },
    "diet": {
        "relative_path": "04_tracking/饮食记录.csv",
        "header": [
            "member_id",
            "date",
            "meal",
            "summary",
            "tags",
            "source_ref",
            "notes",
        ],
    },
    "exercise": {
        "relative_path": "04_tracking/运动记录.csv",
        "header": [
            "member_id",
            "date",
            "activity",
            "duration_minutes",
            "intensity",
            "source_ref",
            "notes",
        ],
    },
    "sleep": {
        "relative_path": "04_tracking/睡眠记录.csv",
        "header": [
            "member_id",
            "date",
            "sleep_start",
            "sleep_end",
            "duration_hours",
            "quality",
            "source_ref",
            "notes",
        ],
    },
}
```

Required non-empty fields for every table:

```python
REQUIRED_NON_EMPTY_FIELDS = ("member_id", "date", "source_ref")
```

## Task 1: Add Module Contract Tests

**Files:**

- Create: `tests/family_doctor/test_tracking_append.py`

- [x] **Step 1: Write table registry test**

Create `tests/family_doctor/test_tracking_append.py` with imports that currently fail:

```python
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from family_doctor.tracking_append import (
    REQUIRED_NON_EMPTY_FIELDS,
    TRACKING_TABLES,
    TrackingAppendError,
    append_tracking_row,
)


EXPECTED_TABLES = {
    "checkup": ("04_tracking/体检指标.csv", "member_id,date,item,result,unit,reference_range,status,source_ref,notes"),
    "medication": ("04_tracking/用药打卡.csv", "member_id,date,time,medication_id,dose,status,source_ref,notes"),
    "diet": ("04_tracking/饮食记录.csv", "member_id,date,meal,summary,tags,source_ref,notes"),
    "exercise": ("04_tracking/运动记录.csv", "member_id,date,activity,duration_minutes,intensity,source_ref,notes"),
    "sleep": ("04_tracking/睡眠记录.csv", "member_id,date,sleep_start,sleep_end,duration_hours,quality,source_ref,notes"),
}


def test_tracking_table_registry_matches_vault_contract():
    assert set(TRACKING_TABLES) == set(EXPECTED_TABLES)
    assert REQUIRED_NON_EMPTY_FIELDS == ("member_id", "date", "source_ref")
    for table, (relative_path, header) in EXPECTED_TABLES.items():
        definition = TRACKING_TABLES[table]
        assert definition.relative_path == Path(relative_path)
        assert ",".join(definition.header) == header
```

- [x] **Step 2: Add test helpers**

Add helpers:

```python
def _tracking_path(target: Path, table: str) -> Path:
    return target / TRACKING_TABLES[table].relative_path


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _base_row(table: str) -> dict[str, str]:
    return {field: "" for field in TRACKING_TABLES[table].header} | {
        "member_id": "dad",
        "date": "2026-05-06",
        "source_ref": "source:test_001",
    }
```

- [x] **Step 3: Add append success tests**

Add:

```python
@pytest.mark.parametrize("table", sorted(EXPECTED_TABLES))
def test_append_tracking_row_appends_one_row_and_preserves_header(run_bootstrap, tmp_path, table):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    path = _tracking_path(target, table)
    original_header = path.read_text(encoding="utf-8").splitlines()[0]
    row = _base_row(table)
    row["notes"] = "contains comma, and newline\nsecond line"

    result = append_tracking_row(target, table, row)

    assert result == {
        "status": "ok",
        "table": table,
        "path": str(TRACKING_TABLES[table].relative_path),
        "appended": 1,
    }
    assert path.read_text(encoding="utf-8").splitlines()[0] == original_header
    rows = _read_rows(path)
    assert len(rows) == 1
    assert rows[0]["member_id"] == "dad"
    assert rows[0]["source_ref"] == "source:test_001"
    assert rows[0]["notes"] == "contains comma, and newline\nsecond line"
```

- [x] **Step 4: Add failure tests**

Add:

```python
def test_append_tracking_row_rejects_invalid_table(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    with pytest.raises(TrackingAppendError) as exc_info:
        append_tracking_row(target, "unknown", {"member_id": "dad"})

    assert exc_info.value.code == "invalid_table"


@pytest.mark.parametrize("missing_field", ["member_id", "date", "source_ref", "notes"])
def test_append_tracking_row_rejects_missing_fields(run_bootstrap, tmp_path, missing_field):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    row = _base_row("medication")
    row.pop(missing_field)

    with pytest.raises(TrackingAppendError) as exc_info:
        append_tracking_row(target, "medication", row)

    assert exc_info.value.code == "missing_field"
    assert missing_field in exc_info.value.message
    assert _read_rows(_tracking_path(target, "medication")) == []


def test_append_tracking_row_rejects_unknown_fields(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    row = _base_row("medication") | {"extra": "nope"}

    with pytest.raises(TrackingAppendError) as exc_info:
        append_tracking_row(target, "medication", row)

    assert exc_info.value.code == "unknown_field"
    assert "extra" in exc_info.value.message
    assert _read_rows(_tracking_path(target, "medication")) == []


@pytest.mark.parametrize("required_field", ["member_id", "date", "source_ref"])
def test_append_tracking_row_rejects_empty_required_fields(run_bootstrap, tmp_path, required_field):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    row = _base_row("medication")
    row[required_field] = "  "

    with pytest.raises(TrackingAppendError) as exc_info:
        append_tracking_row(target, "medication", row)

    assert exc_info.value.code == "missing_required_field"
    assert required_field in exc_info.value.message
    assert _read_rows(_tracking_path(target, "medication")) == []


def test_append_tracking_row_rejects_header_drift_before_writing(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    path = _tracking_path(target, "medication")
    path.write_text("member_id,date\n", encoding="utf-8")

    with pytest.raises(TrackingAppendError) as exc_info:
        append_tracking_row(target, "medication", _base_row("medication"))

    assert exc_info.value.code == "tracking_header_drift"
    assert path.read_text(encoding="utf-8") == "member_id,date\n"
```

- [x] **Step 5: Run module tests and verify RED**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_tracking_append.py -q
```

Expected: FAIL because `family_doctor.tracking_append` does not exist.

- [x] **Step 6: Commit red module tests**

Run:

```bash
git add tests/family_doctor/test_tracking_append.py
git commit -m "test: define tracking append helper contract"
```

## Task 2: Implement Tracking Append Module

**Files:**

- Create: `family_doctor/tracking_append.py`

- [x] **Step 1: Add module skeleton**

Create:

```python
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


REQUIRED_NON_EMPTY_FIELDS = ("member_id", "date", "source_ref")


@dataclass(frozen=True)
class TrackingTable:
    relative_path: Path
    header: tuple[str, ...]


class TrackingAppendError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_payload(self) -> dict[str, object]:
        return {"status": "error", "error": {"code": self.code, "message": self.message}}
```

- [x] **Step 2: Add table registry**

Add `TRACKING_TABLES` using the exact registry from the top of this plan, converting each header list to a tuple and each path to `Path`.

- [x] **Step 3: Add validation helpers**

Implement:

```python
def _coerce_row(row: Mapping[str, object]) -> dict[str, str]:
    return {key: "" if value is None else str(value) for key, value in row.items()}


def _validate_row_fields(table: TrackingTable, row: Mapping[str, object]) -> dict[str, str]:
    coerced = _coerce_row(row)
    expected = set(table.header)
    actual = set(coerced)
    missing = sorted(expected - actual)
    if missing:
        raise TrackingAppendError("missing_field", f"missing fields: {', '.join(missing)}")
    unknown = sorted(actual - expected)
    if unknown:
        raise TrackingAppendError("unknown_field", f"unknown fields: {', '.join(unknown)}")
    for field in REQUIRED_NON_EMPTY_FIELDS:
        if not coerced[field].strip():
            raise TrackingAppendError("missing_required_field", f"{field} is required")
    return coerced
```

Implement `_validate_header(csv_path: Path, table: TrackingTable) -> None` using `csv.reader`. It must:

- raise `missing_tracking_csv` if the file does not exist
- raise `tracking_header_drift` if the first row is not exactly `list(table.header)`

- [x] **Step 4: Add append function**

Implement:

```python
def append_tracking_row(target: Path, table: str, row: Mapping[str, object]) -> dict[str, object]:
    if not target.exists() or not target.is_dir():
        raise TrackingAppendError("invalid_target", f"target does not exist: {target}")
    if table not in TRACKING_TABLES:
        raise TrackingAppendError("invalid_table", f"unsupported tracking table: {table}")

    definition = TRACKING_TABLES[table]
    csv_path = target / definition.relative_path
    validated_row = _validate_row_fields(definition, row)
    _validate_header(csv_path, definition)

    try:
        with csv_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(definition.header))
            writer.writerow({field: validated_row[field] for field in definition.header})
    except OSError as exc:
        raise TrackingAppendError("write_failed", str(exc)) from exc

    return {
        "status": "ok",
        "table": table,
        "path": str(definition.relative_path),
        "appended": 1,
    }
```

- [x] **Step 5: Run module tests and verify GREEN**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_tracking_append.py -q
```

Expected: PASS.

- [x] **Step 6: Commit module implementation**

Run:

```bash
git add family_doctor/tracking_append.py tests/family_doctor/test_tracking_append.py
git commit -m "feat: add tracking append helper"
```

## Task 3: Add CLI Contract Tests

**Files:**

- Create: `tests/family_doctor/test_append_tracking_row_cli.py`

- [x] **Step 1: Write CLI tests**

Create:

```python
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APPEND_TRACKING_ROW = ROOT / "scripts" / "family_doctor" / "append_tracking_row.py"


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _medication_row() -> dict[str, str]:
    return {
        "member_id": "dad",
        "date": "2026-05-06",
        "time": "08:00",
        "medication_id": "med_001",
        "dose": "1 tablet",
        "status": "taken",
        "source_ref": "source:test_001",
        "notes": "breakfast",
    }
```

- [x] **Step 2: Add CLI success test**

Add:

```python
def test_append_tracking_row_cli_appends_and_prints_success_json(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    row_path = _write_json(tmp_path / "row.json", _medication_row())

    result = subprocess.run(
        [
            sys.executable,
            str(APPEND_TRACKING_ROW),
            "--target",
            str(target),
            "--table",
            "medication",
            "--row-json",
            str(row_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload == {
        "status": "ok",
        "table": "medication",
        "path": "04_tracking/用药打卡.csv",
        "appended": 1,
    }
    with (target / "04_tracking" / "用药打卡.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [_medication_row()]
```

- [x] **Step 3: Add CLI error tests**

Add:

```python
def test_append_tracking_row_cli_prints_error_json_for_invalid_table(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    row_path = _write_json(tmp_path / "row.json", _medication_row())

    result = subprocess.run(
        [
            sys.executable,
            str(APPEND_TRACKING_ROW),
            "--target",
            str(target),
            "--table",
            "unknown",
            "--row-json",
            str(row_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_table"


def test_append_tracking_row_cli_rejects_invalid_json(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    row_path = tmp_path / "row.json"
    row_path.write_text("{", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(APPEND_TRACKING_ROW),
            "--target",
            str(target),
            "--table",
            "medication",
            "--row-json",
            str(row_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_row_json"


def test_append_tracking_row_cli_rejects_non_object_json(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    row_path = _write_json(tmp_path / "row.json", ["not", "object"])

    result = subprocess.run(
        [
            sys.executable,
            str(APPEND_TRACKING_ROW),
            "--target",
            str(target),
            "--table",
            "medication",
            "--row-json",
            str(row_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "row_must_be_object"
```

Final implementation also locks two CLI quality paths:

- missing required CLI arguments return stdout JSON with `error.code == "invalid_arguments"` and empty stderr
- unexpected internal exceptions return stdout JSON with `error.code == "internal_error"` and empty stderr

- [x] **Step 4: Run CLI tests and verify RED**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_append_tracking_row_cli.py -q
```

Expected: FAIL because `scripts/family_doctor/append_tracking_row.py` does not exist.

- [x] **Step 5: Commit red CLI tests**

Run:

```bash
git add tests/family_doctor/test_append_tracking_row_cli.py
git commit -m "test: define tracking append cli contract"
```

## Task 4: Implement CLI Wrapper

**Files:**

- Create: `scripts/family_doctor/append_tracking_row.py`

- [x] **Step 1: Add CLI script**

Create:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from family_doctor.tracking_append import TrackingAppendError, append_tracking_row


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise TrackingAppendError("invalid_arguments", message)


def parse_args() -> argparse.Namespace:
    parser = JsonArgumentParser(
        add_help=False,
        description="Append one row to a family-health tracking CSV.",
    )
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--table", required=True)
    parser.add_argument("--row-json", required=True, type=Path)
    return parser.parse_args()


def _error_payload(code: str, message: str) -> dict[str, object]:
    return {"status": "error", "error": {"code": code, "message": message}}


def _print_json(payload: dict[str, object]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def _load_row(row_json: Path) -> dict[str, object]:
    try:
        raw = row_json.read_text(encoding="utf-8")
    except OSError as exc:
        raise TrackingAppendError("invalid_row_json", str(exc)) from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TrackingAppendError("invalid_row_json", str(exc)) from exc
    if not isinstance(payload, dict):
        raise TrackingAppendError("row_must_be_object", "row JSON must be an object")
    return payload


def main() -> int:
    try:
        args = parse_args()
        row = _load_row(args.row_json)
        result = append_tracking_row(args.target, args.table, row)
    except TrackingAppendError as exc:
        _print_json(exc.to_payload())
        return 1
    except Exception as exc:
        _print_json(_error_payload("internal_error", str(exc)))
        return 1

    _print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 2: Run CLI tests and verify GREEN**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_append_tracking_row_cli.py -q
```

Expected: PASS.

- [x] **Step 3: Run module and CLI tests together**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_tracking_append.py tests/family_doctor/test_append_tracking_row_cli.py -q
```

Expected: PASS.

- [x] **Step 4: Commit CLI implementation**

Run:

```bash
git add scripts/family_doctor/append_tracking_row.py tests/family_doctor/test_append_tracking_row_cli.py
git commit -m "feat: add tracking append cli"
```

## Task 5: Update Skill Contract Docs

**Files:**

- Modify: `.codex/skills/family-doctor/SKILL.md`
- Modify: `.claude/skills/family-doctor.md`
- Modify: `tests/family_doctor/test_skill_workflow_contract_docs.py`

- [x] **Step 1: Add failing skill-doc test markers**

In `tests/family_doctor/test_skill_workflow_contract_docs.py`, update the `daily_tracking_update` workflow markers to include:

```python
"scripts/family_doctor/append_tracking_row.py",
"append-only",
"standalone CLI helper",
"must not use helper for corrections",
```

Keep forbidden markers that prevent:

- `event_type: daily_tracking_update`
- `daily_tracking_update route`
- `new CLI route`
- `new Python pipeline`

- [x] **Step 2: Run focused skill-doc test and verify RED**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_skill_workflow_contract_docs.py -q
```

Expected: FAIL because skill docs do not mention the Phase C.0 helper yet.

- [x] **Step 3: Update Codex skill doc**

In `.codex/skills/family-doctor/SKILL.md`, under `### daily_tracking_update`, add concise rules:

```markdown
- daily_tracking_update should use standalone CLI helper `scripts/family_doctor/append_tracking_row.py` for append-only tracking rows.
- daily_tracking_update helper is append-only and must not use helper for corrections.
- daily_tracking_update helper is not a new route or event_type.
```

Preserve existing markers and forbidden route boundaries.

- [x] **Step 4: Update Claude skill doc**

Mirror the same three rules in `.claude/skills/family-doctor.md`.

- [x] **Step 5: Run focused skill-doc test and verify GREEN**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_skill_workflow_contract_docs.py -q
```

Expected: PASS.

- [x] **Step 6: Commit skill docs**

Run:

```bash
git add .codex/skills/family-doctor/SKILL.md .claude/skills/family-doctor.md tests/family_doctor/test_skill_workflow_contract_docs.py
git commit -m "docs: route tracking appends through helper"
```

## Task 6: Update Phase C.0 Index and Verify

**Files:**

- Modify: `docs/superpowers/obsidian-first-llm-wiki/README.md`

- [x] **Step 1: Add this plan to the document index**

Add:

```markdown
- [phase-c0-tracking-append-helper-plan.md](./phase-c0-tracking-append-helper-plan.md)：阶段 C.0 实施计划，聚焦只追加 tracking CSV helper
```

- [x] **Step 2: Update Phase C.0 state**

Change:

```markdown
- Phase C.0: design approved; implementation plan pending
```

to:

```markdown
- Phase C.0: complete
```

- [x] **Step 3: Run full validation**

Run:

```bash
rm -f uv.lock
python3 scripts/family_doctor/validate_phase0.py --target ./family-health
rm -rf /tmp/family-health-phase-c0-tracking-append
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-phase-c0-tracking-append
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-phase-c0-tracking-append
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q
rm -f uv.lock
```

Expected:

- Both validators pass.
- Full `tests/family_doctor` passes.
- No `uv.lock` remains.

- [x] **Step 4: Review diff scope**

Run:

```bash
git diff --stat
git diff -- family_doctor/tracking_append.py scripts/family_doctor/append_tracking_row.py tests/family_doctor/test_tracking_append.py tests/family_doctor/test_append_tracking_row_cli.py tests/family_doctor/test_skill_workflow_contract_docs.py .codex/skills/family-doctor/SKILL.md .claude/skills/family-doctor.md docs/superpowers/obsidian-first-llm-wiki/README.md
```

Expected: diff only touches the Phase C.0 helper, its tests, skill docs, and Phase C.0 docs.

- [x] **Step 5: Commit final docs**

Run:

```bash
git add docs/superpowers/obsidian-first-llm-wiki/README.md
git commit -m "docs: record phase c0 tracking append completion"
```

## Verification Summary

Phase C.0 implementation is complete only when all of these pass:

```bash
python3 scripts/family_doctor/validate_phase0.py --target ./family-health
rm -rf /tmp/family-health-phase-c0-tracking-append
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-phase-c0-tracking-append
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-phase-c0-tracking-append
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q
```

Implementation note: Task 6 verification completed with both Phase 0 validators passing, the full `tests/family_doctor` suite passing, and no `uv.lock` left behind.

## Residual Risks After Phase C.0

- Corrections remain prompt-governed and out of scope.
- `log.md` audit entries are still manual or host-LLM-maintained.
- The helper validates structure, not medical correctness.
- Duplicate row detection is out of scope until row identity is designed.
