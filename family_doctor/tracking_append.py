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


TRACKING_TABLES = {
    "checkup": TrackingTable(
        relative_path=Path("04_tracking/体检指标.csv"),
        header=(
            "member_id",
            "date",
            "item",
            "result",
            "unit",
            "reference_range",
            "status",
            "source_ref",
            "notes",
        ),
    ),
    "medication": TrackingTable(
        relative_path=Path("04_tracking/用药打卡.csv"),
        header=(
            "member_id",
            "date",
            "time",
            "medication_id",
            "dose",
            "status",
            "source_ref",
            "notes",
        ),
    ),
    "diet": TrackingTable(
        relative_path=Path("04_tracking/饮食记录.csv"),
        header=(
            "member_id",
            "date",
            "meal",
            "summary",
            "tags",
            "source_ref",
            "notes",
        ),
    ),
    "exercise": TrackingTable(
        relative_path=Path("04_tracking/运动记录.csv"),
        header=(
            "member_id",
            "date",
            "activity",
            "duration_minutes",
            "intensity",
            "source_ref",
            "notes",
        ),
    ),
    "sleep": TrackingTable(
        relative_path=Path("04_tracking/睡眠记录.csv"),
        header=(
            "member_id",
            "date",
            "sleep_start",
            "sleep_end",
            "duration_hours",
            "quality",
            "source_ref",
            "notes",
        ),
    ),
}


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


def _validate_header(csv_path: Path, table: TrackingTable) -> None:
    if not csv_path.exists():
        raise TrackingAppendError("missing_tracking_csv", f"tracking CSV does not exist: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)

    if header != list(table.header):
        raise TrackingAppendError(
            "tracking_header_drift",
            f"tracking CSV header does not match expected schema: {csv_path}",
        )


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


__all__ = [
    "REQUIRED_NON_EMPTY_FIELDS",
    "TrackingTable",
    "TRACKING_TABLES",
    "TrackingAppendError",
    "append_tracking_row",
]
