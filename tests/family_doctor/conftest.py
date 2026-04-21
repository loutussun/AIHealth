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


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


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


@pytest.fixture
def materialize_query_event():
    def _materialize_query_event(
        tmp_path: Path,
        *,
        question: str,
        intent_hint: str,
        allow_qa_summary_reuse: bool = False,
    ) -> Path:
        raw_event = json.loads(_event_path("query-mvp.json").read_text(encoding="utf-8"))
        raw_event["event_id"] = f"evt_{intent_hint}"
        raw_event["request_id"] = f"req_{intent_hint}"
        raw_event["correlation_id"] = f"corr_{intent_hint}"
        raw_event["idempotency_key"] = f"idem_{intent_hint}"
        raw_event["payload"]["text"] = question
        raw_event["payload"]["intent_hint"] = intent_hint
        raw_event["payload"]["allow_qa_summary_reuse"] = allow_qa_summary_reuse

        event_path = tmp_path / f"{intent_hint}.json"
        event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")
        return event_path

    return _materialize_query_event
