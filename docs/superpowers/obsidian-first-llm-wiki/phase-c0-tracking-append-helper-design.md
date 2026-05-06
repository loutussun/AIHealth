# Phase C.0: Tracking Append Helper Design

## Goal

Phase C.0 adds one deterministic helper for appending new rows to the canonical `04_tracking/*.csv` files.

The purpose is to move the riskiest Phase B prompt-only operation, `daily_tracking_update`, into a small protected tool without broadening the `family-doctor` skill router or changing the Obsidian-first product model.

## Background

Phase A made `family-health/` the canonical Obsidian vault.

Phase B defined user-intent workflows and direct-write boundaries. It still leaves CSV maintenance prompt-governed:

- `daily_tracking_update must preserve CSV headers exactly`
- `daily_tracking_update requires member_id, date, source_ref`
- `daily_tracking_update must not silently overwrite existing rows`
- `daily_tracking_update corrections require traceable explanation in notes`
- `daily_tracking_update writes ambiguous values to notes or review`

Phase C.0 implements only the lowest-risk part of that contract: append a new tracking row.

## Scope

In scope:

- Add a standalone CLI helper for appending one row to one tracking CSV.
- Validate the target vault, table key, CSV header, row fields, and required non-empty fields.
- Use Python standard library CSV handling for quoting, commas, and newlines.
- Return machine-readable JSON for success and errors.
- Add focused tests for success and failure cases.
- Update skill docs so host LLMs prefer the helper for `daily_tracking_update`.

Out of scope:

- No new `run_skill.py` route.
- No new `event_type`.
- No row correction, update, overwrite, delete, merge, or deduplication.
- No trend generation.
- No source extraction, OCR, PDF/image parsing, or medical reasoning.
- No automatic `log.md` write in Phase C.0.

## User-Facing Contract

The helper is called directly:

```bash
python3 scripts/family_doctor/append_tracking_row.py \
  --target /absolute/path/to/family-health \
  --table medication \
  --row-json /absolute/path/to/row.json
```

The script accepts exactly these table keys:

| Table key | CSV path | Header |
| --- | --- | --- |
| `checkup` | `04_tracking/体检指标.csv` | `member_id,date,item,result,unit,reference_range,status,source_ref,notes` |
| `medication` | `04_tracking/用药打卡.csv` | `member_id,date,time,medication_id,dose,status,source_ref,notes` |
| `diet` | `04_tracking/饮食记录.csv` | `member_id,date,meal,summary,tags,source_ref,notes` |
| `exercise` | `04_tracking/运动记录.csv` | `member_id,date,activity,duration_minutes,intensity,source_ref,notes` |
| `sleep` | `04_tracking/睡眠记录.csv` | `member_id,date,sleep_start,sleep_end,duration_hours,quality,source_ref,notes` |

Every row must contain all fields for its table and no unknown fields.

For every table, these fields must be non-empty:

- `member_id`
- `date`
- `source_ref`

The helper may accept empty strings for table-specific optional fields when the user explicitly wants to keep uncertainty in `notes`, but it must reject unknown keys and missing canonical keys.

## Data Flow

1. Parse CLI arguments.
2. Resolve `--target` as the vault root.
3. Resolve `--table` through the table registry.
4. Load row JSON from `--row-json`.
5. Validate that the row JSON is an object.
6. Validate exact field set.
7. Validate `member_id`, `date`, and `source_ref` are non-empty strings after trimming.
8. Validate the target CSV exists and its first row exactly matches the canonical header.
9. Append one CSV row using `csv.DictWriter`.
10. Print JSON result to stdout.

## Success Output

Success returns exit code `0` and stdout JSON:

```json
{
  "status": "ok",
  "table": "medication",
  "path": "04_tracking/用药打卡.csv",
  "appended": 1
}
```

The `path` field is always vault-relative and always one of the canonical `04_tracking/*.csv` files.

## Error Output

Errors return a non-zero exit code and stdout JSON:

```json
{
  "status": "error",
  "error": {
    "code": "missing_required_field",
    "message": "source_ref is required"
  }
}
```

Planned error codes:

- `invalid_target`
- `invalid_arguments`
- `invalid_table`
- `invalid_row_json`
- `internal_error`
- `row_must_be_object`
- `missing_field`
- `unknown_field`
- `missing_required_field`
- `missing_tracking_csv`
- `tracking_header_drift`
- `write_failed`

## Safety Rules

- The helper only writes under `04_tracking/`.
- The helper only writes the five canonical CSV files listed above.
- The helper never creates a missing CSV file.
- The helper never changes the header row.
- The helper never overwrites existing rows.
- The helper never updates `log.md` in Phase C.0.
- The helper never interprets medical meaning; it only validates structure and appends data already supplied by the host.

## Host LLM Rules

For `daily_tracking_update`, the skill docs should instruct the host LLM to prefer this helper whenever a tracking append is requested.

Before calling the helper, the host LLM must identify:

- target member
- table key
- date
- source reference
- row fields

If any required value is ambiguous, the host LLM should ask the user for clarification or put the ambiguity into `notes` only when the structured field can safely remain empty.

The host LLM must not use the helper for corrections. Corrections remain out of scope until a later phase defines row identity and audit behavior.

## Tests

Phase C.0 should add tests for:

- successful append to each table key or at least one parameterized success case per table
- preserving the header row exactly
- rejecting an invalid table key
- rejecting unknown fields
- rejecting missing fields
- rejecting empty `member_id`, `date`, or `source_ref`
- rejecting header drift before writing
- preserving commas and newlines in `notes`
- CLI success output shape
- CLI error output and non-zero exit codes

Existing vault validation should continue passing.

## Implementation Notes

Prefer a small module plus a tiny CLI wrapper:

- `family_doctor/tracking_append.py` owns table registry, validation, CSV append, and result objects.
- `scripts/family_doctor/append_tracking_row.py` owns argparse, JSON loading, stdout JSON, and exit codes.
- `tests/family_doctor/test_tracking_append.py` covers module behavior.
- `tests/family_doctor/test_append_tracking_row_cli.py` covers CLI behavior.

Do not add this to `family_doctor/skill_router.py` in Phase C.0.

## Acceptance Criteria

Phase C.0 is complete when:

- The helper appends valid rows to canonical tracking CSVs.
- Invalid inputs fail without modifying files.
- Header drift fails before writing.
- Skill docs mention the helper for `daily_tracking_update` without claiming a new `event_type`.
- `python3 scripts/family_doctor/validate_phase0.py --target ./family-health` passes.
- `PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q` passes.
- No `uv.lock` remains.
