import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "scripts" / "family_doctor" / "bootstrap_vault.py"
INGEST = ROOT / "scripts" / "family_doctor" / "run_ingest.py"
VALIDATE = ROOT / "scripts" / "family_doctor" / "validate_phase0.py"


@pytest.fixture
def run_bootstrap():
    def _run_bootstrap(target: Path):
        return subprocess.run(
            [sys.executable, str(BOOTSTRAP), "--target", str(target)],
            capture_output=True,
            text=True,
        )

    return _run_bootstrap


@pytest.fixture
def run_ingest():
    def _run_ingest(event_path: Path, target: Path):
        raw_event = json.loads(event_path.read_text(encoding="utf-8"))
        for attachment in raw_event.get("payload", {}).get("attachments", []):
            attachment_path = Path(attachment["path"])
            if not attachment_path.is_absolute():
                attachment["path"] = str((ROOT / attachment_path).resolve())

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as temp_event:
            json.dump(raw_event, temp_event, ensure_ascii=False, indent=2)
            temp_event_path = Path(temp_event.name)

        return subprocess.run(
            [
                sys.executable,
                str(INGEST),
                "--event",
                str(temp_event_path),
                "--target",
                str(target),
            ],
            capture_output=True,
            text=True,
        )

    return _run_ingest


@pytest.fixture
def run_validate():
    def _run_validate(target: Path):
        return subprocess.run(
            [sys.executable, str(VALIDATE), "--target", str(target)],
            capture_output=True,
            text=True,
        )

    return _run_validate
