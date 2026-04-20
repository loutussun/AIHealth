import json
from pathlib import Path

from family_doctor.ingest_pipeline import run_ingest_pipeline


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def _materialize_event(
    tmp_path: Path,
    source_name: str,
    *,
    event_id: str,
    member_id: str | None = None,
    member_hint: str | None = None,
    match_confidence: float | None = None,
) -> Path:
    raw_event = json.loads(_event_path(source_name).read_text(encoding="utf-8"))
    raw_event["event_id"] = event_id
    raw_event["request_id"] = f"req_{event_id}"
    raw_event["correlation_id"] = f"corr_{event_id}"
    if member_id is not None or member_hint is not None or match_confidence is not None:
        raw_event["target"] = {
            "member_id": member_id,
            "member_hint": member_hint or raw_event["target"]["member_hint"],
            "match_confidence": (
                match_confidence
                if match_confidence is not None
                else raw_event["target"]["match_confidence"]
            ),
        }

    event_path = tmp_path / f"{event_id}.json"
    event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")
    return event_path


def test_lab_report_writes_source_page_with_raw_archive_reference(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(_event_path("lab-report.json"), target)

    assert result["status"] == "ok"
    source_page = target / "02_wiki" / "sources" / "evt_lab_report_001.md"
    assert source_page.exists()
    content = source_page.read_text(encoding="utf-8")
    assert "source_path: 01_raw/labs/" in content
    assert "## 来源信息" in content
    assert "## 提取出的结构化事实" in content
    assert "## 待核实项" in content
    assert any(
        artifact["artifact_type"] == "source_page" and artifact["path"] == str(source_page)
        for artifact in result["artifacts"]
    )
    assert any(
        update["entity_type"] == "source_page" and update["status"] == "committed"
        for update in result["runtime_updates"]
    )
    assert any(
        update["entity_type"] == "ingest_job"
        and update["status"] == "committed"
        and update["phase"] == "committed"
        for update in result["runtime_updates"]
    )


def test_medication_photo_archives_into_medications_folder(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(_event_path("medication-photo.json"), target)

    assert result["status"] == "ok"
    raw_artifacts = [
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "raw_archive"
    ]
    assert raw_artifacts
    assert raw_artifacts[0]["path"].startswith(str(target / "01_raw" / "medications"))
    assert Path(raw_artifacts[0]["path"]).exists()


def test_symptom_text_creates_source_page_without_copying_raw_file(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    event_path = _materialize_event(
        tmp_path,
        "symptom-note-low-confidence.json",
        event_id="evt_symptom_note_high_confidence_001",
        member_id="dad",
        member_hint="dad",
        match_confidence=1.0,
    )
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(event_path, target)

    assert result["status"] == "ok"
    source_page = target / "02_wiki" / "sources" / "evt_symptom_note_high_confidence_001.md"
    assert source_page.exists()
    content = source_page.read_text(encoding="utf-8")
    assert "source_path: null" in content
    assert "## 来源信息" in content
    assert not any(
        artifact["artifact_type"] == "raw_archive" for artifact in result["artifacts"]
    )
    assert not list((target / "01_raw" / "reports").glob("*symptom*"))
    assert not list((target / "01_raw" / "labs").glob("*symptom*"))
    assert not list((target / "01_raw" / "medications").glob("*symptom*"))
