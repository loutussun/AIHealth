from pathlib import Path
import subprocess
import sys

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
        return subprocess.run(
            [
                sys.executable,
                str(INGEST),
                "--event",
                str(event_path),
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
