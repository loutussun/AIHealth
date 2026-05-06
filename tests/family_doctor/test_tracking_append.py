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
    "checkup": (
        "04_tracking/体检指标.csv",
        "member_id,date,item,result,unit,reference_range,status,source_ref,notes",
    ),
    "medication": (
        "04_tracking/用药打卡.csv",
        "member_id,date,time,medication_id,dose,status,source_ref,notes",
    ),
    "diet": (
        "04_tracking/饮食记录.csv",
        "member_id,date,meal,summary,tags,source_ref,notes",
    ),
    "exercise": (
        "04_tracking/运动记录.csv",
        "member_id,date,activity,duration_minutes,intensity,source_ref,notes",
    ),
    "sleep": (
        "04_tracking/睡眠记录.csv",
        "member_id,date,sleep_start,sleep_end,duration_hours,quality,source_ref,notes",
    ),
}


def test_tracking_table_registry_matches_vault_contract():
    assert set(TRACKING_TABLES) == set(EXPECTED_TABLES)
    assert REQUIRED_NON_EMPTY_FIELDS == ("member_id", "date", "source_ref")
    for table, (relative_path, header) in EXPECTED_TABLES.items():
        definition = TRACKING_TABLES[table]
        assert definition.relative_path == Path(relative_path)
        assert ",".join(definition.header) == header


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


@pytest.mark.parametrize("table", sorted(EXPECTED_TABLES))
def test_append_tracking_row_appends_one_row_and_preserves_header(
    run_bootstrap, tmp_path, table
):
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
def test_append_tracking_row_rejects_empty_required_fields(
    run_bootstrap, tmp_path, required_field
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    row = _base_row("medication")
    row[required_field] = "  "

    with pytest.raises(TrackingAppendError) as exc_info:
        append_tracking_row(target, "medication", row)

    assert exc_info.value.code == "missing_required_field"
    assert required_field in exc_info.value.message
    assert _read_rows(_tracking_path(target, "medication")) == []


@pytest.mark.parametrize(
    ("required_field", "value"),
    [
        ("member_id", 0),
        ("date", False),
        ("source_ref", []),
    ],
)
def test_append_tracking_row_rejects_non_string_required_fields(
    run_bootstrap, tmp_path, required_field, value
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    row = _base_row("medication")
    row[required_field] = value

    with pytest.raises(TrackingAppendError) as exc_info:
        append_tracking_row(target, "medication", row)

    assert exc_info.value.code == "missing_required_field"
    assert required_field in exc_info.value.message
    assert _read_rows(_tracking_path(target, "medication")) == []


def test_append_tracking_row_rejects_header_drift_before_writing(
    run_bootstrap, tmp_path
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    path = _tracking_path(target, "medication")
    path.write_text("member_id,date\n", encoding="utf-8")

    with pytest.raises(TrackingAppendError) as exc_info:
        append_tracking_row(target, "medication", _base_row("medication"))

    assert exc_info.value.code == "tracking_header_drift"
    assert path.read_text(encoding="utf-8") == "member_id,date\n"


def test_append_tracking_row_does_not_corrupt_header_without_final_newline(
    run_bootstrap, tmp_path
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    path = _tracking_path(target, "medication")
    header = ",".join(TRACKING_TABLES["medication"].header)
    path.write_text(header, encoding="utf-8")

    append_tracking_row(target, "medication", _base_row("medication"))

    assert path.read_text(encoding="utf-8").splitlines()[0] == header
    assert _read_rows(path) == [_base_row("medication")]


def test_append_tracking_row_rejects_tracking_csv_path_that_is_not_a_file(
    run_bootstrap, tmp_path
):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    path = _tracking_path(target, "medication")
    path.unlink()
    path.mkdir()

    with pytest.raises(TrackingAppendError) as exc_info:
        append_tracking_row(target, "medication", _base_row("medication"))

    assert exc_info.value.code == "missing_tracking_csv"
    assert "not a file" in exc_info.value.message
