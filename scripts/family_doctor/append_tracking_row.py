from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from family_doctor.tracking_append import TrackingAppendError, append_tracking_row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append one row to a family-health tracking CSV.")
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
    args = parse_args()
    try:
        row = _load_row(args.row_json)
        result = append_tracking_row(args.target, args.table, row)
    except TrackingAppendError as exc:
        _print_json(exc.to_payload())
        return 1
    except Exception as exc:
        _print_json(_error_payload("write_failed", str(exc)))
        return 1

    _print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
