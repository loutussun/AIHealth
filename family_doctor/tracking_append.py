from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


REQUIRED_NON_EMPTY_FIELDS = ("member_id", "date", "source_ref")
REQUIRED_VAULT_MARKERS = (
    (Path("AGENTS.md"), ("# family-health Canonical Vault", "policy: vault-product-surface")),
    (Path("index.md"), ("type: index", "[[家庭健康管理中心]]", "## Tracking CSV")),
    (Path("00_schema/event-schema.json"), ('"event_type"', '"payload"')),
    (Path("00_schema/members.md"), ("# 成员注册规则", "## 成员识别护栏")),
)


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
        raw_value = row[field]
        if not isinstance(raw_value, str) or not raw_value.strip():
            raise TrackingAppendError("missing_required_field", f"{field} is required")
    return coerced


def _validate_header(csv_path: Path, table: TrackingTable) -> None:
    if not csv_path.exists():
        raise TrackingAppendError("missing_tracking_csv", f"tracking CSV does not exist: {csv_path}")
    if not csv_path.is_file():
        raise TrackingAppendError("missing_tracking_csv", f"tracking CSV is not a file: {csv_path}")

    try:
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
    except OSError as exc:
        raise TrackingAppendError("missing_tracking_csv", str(exc)) from exc

    if header != list(table.header):
        raise TrackingAppendError(
            "tracking_header_drift",
            f"tracking CSV header does not match expected schema: {csv_path}",
        )


def _validate_canonical_vault_target(target: Path) -> None:
    problems = []
    for marker, required_text in REQUIRED_VAULT_MARKERS:
        marker_path = target / marker
        if not marker_path.is_file():
            problems.append(str(marker))
            continue
        try:
            marker_content = marker_path.read_text(encoding="utf-8")
        except OSError:
            problems.append(str(marker))
            continue
        missing_text = [text for text in required_text if text not in marker_content]
        if missing_text:
            problems.append(str(marker))

    tracking_dir = target / "04_tracking"
    if not tracking_dir.is_dir():
        problems.append("04_tracking")

    if problems:
        raise TrackingAppendError(
            "invalid_target",
            "target is not a canonical family-health vault; "
            f"invalid markers: {', '.join(problems)}",
        )


def _validate_tracking_path(target: Path, csv_path: Path) -> None:
    path_to_check = csv_path
    while path_to_check != target:
        if path_to_check.is_symlink():
            raise TrackingAppendError(
                "invalid_tracking_path",
                f"tracking CSV path must not contain symlinks: {csv_path}",
            )
        if path_to_check.parent == path_to_check:
            raise TrackingAppendError(
                "invalid_tracking_path",
                f"tracking CSV path is not under target vault: {csv_path}",
            )
        path_to_check = path_to_check.parent

    try:
        csv_real = csv_path.resolve(strict=True)
    except OSError as exc:
        raise TrackingAppendError("missing_tracking_csv", str(exc)) from exc

    if not csv_real.is_relative_to(target):
        raise TrackingAppendError(
            "invalid_tracking_path",
            f"tracking CSV resolves outside target vault: {csv_path}",
        )


def _ensure_final_newline(csv_path: Path) -> None:
    try:
        if csv_path.stat().st_size == 0:
            return
        with csv_path.open("rb+") as handle:
            handle.seek(-1, 2)
            if handle.read(1) != b"\n":
                handle.write(b"\n")
    except OSError as exc:
        raise TrackingAppendError("write_failed", str(exc)) from exc


def append_tracking_row(target: Path, table: str, row: Mapping[str, object]) -> dict[str, object]:
    if not target.exists():
        raise TrackingAppendError("invalid_target", f"target does not exist: {target}")
    if not target.is_dir():
        raise TrackingAppendError("invalid_target", f"target is not a directory: {target}")
    try:
        target = target.resolve(strict=True)
    except OSError as exc:
        raise TrackingAppendError("invalid_target", str(exc)) from exc
    if table not in TRACKING_TABLES:
        raise TrackingAppendError("invalid_table", f"unsupported tracking table: {table}")

    _validate_canonical_vault_target(target)
    definition = TRACKING_TABLES[table]
    csv_path = target / definition.relative_path
    validated_row = _validate_row_fields(definition, row)
    _validate_tracking_path(target, csv_path)
    _validate_header(csv_path, definition)
    _ensure_final_newline(csv_path)

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
