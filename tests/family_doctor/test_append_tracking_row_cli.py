from __future__ import annotations

import csv
import importlib.util
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


def _load_cli_module():
    spec = importlib.util.spec_from_file_location("append_tracking_row_cli", APPEND_TRACKING_ROW)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_append_tracking_row_cli_prints_error_json_for_missing_arguments():
    result = subprocess.run(
        [sys.executable, str(APPEND_TRACKING_ROW)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_arguments"


def test_append_tracking_row_cli_maps_unexpected_errors_to_internal_error(
    monkeypatch, capsys, tmp_path
):
    cli_module = _load_cli_module()
    row_path = _write_json(tmp_path / "row.json", _medication_row())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(APPEND_TRACKING_ROW),
            "--target",
            str(tmp_path),
            "--table",
            "medication",
            "--row-json",
            str(row_path),
        ],
    )
    monkeypatch.setattr(
        cli_module,
        "append_tracking_row",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    exit_code = cli_module.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "internal_error"
