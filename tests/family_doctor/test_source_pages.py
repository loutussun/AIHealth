import json
from pathlib import Path

import pytest

from family_doctor.ingest_pipeline import load_event, run_ingest_pipeline
from family_doctor.ingest_models import IngestEvent
from family_doctor.raw_archive import ArchivedArtifact
from family_doctor.source_pages import build_source_page_content


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def _safe_event_filename(label: str) -> str:
    sanitized = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in label)
    return sanitized or "input_event"


def _write_event_payload(tmp_path: Path, payload: dict, *, label: str) -> Path:
    event_path = tmp_path / f"{_safe_event_filename(label)}.json"
    suffix = 1
    while event_path.exists():
        event_path = tmp_path / f"{_safe_event_filename(label)}_{suffix}.json"
        suffix += 1
    event_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return event_path


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

    return _write_event_payload(tmp_path, raw_event, label=f"{source_name}_{event_id}")


def _materialize_plain_symptom_event(tmp_path: Path, *, event_id: str) -> Path:
    attachment_path = tmp_path / "note.txt"
    attachment_path.write_text("昨晚开始咳嗽发热两天", encoding="utf-8")

    raw_event = json.loads(_event_path("symptom-note-low-confidence.json").read_text(encoding="utf-8"))
    raw_event["event_id"] = event_id
    raw_event["request_id"] = f"req_{event_id}"
    raw_event["correlation_id"] = f"corr_{event_id}"
    raw_event["target"] = {
        "member_id": "dad",
        "member_hint": "dad",
        "match_confidence": 1.0,
    }
    raw_event["payload"]["text"] = "昨晚开始咳嗽发热两天"
    raw_event["payload"]["attachments"][0]["path"] = str(attachment_path)
    raw_event["payload"]["attachments"][0]["source_name"] = "note.txt"
    raw_event["payload"]["attachments"][0]["caption"] = "昨晚开始咳嗽发热两天"

    return _write_event_payload(tmp_path, raw_event, label=f"plain_symptom_{event_id}")


def test_lab_report_writes_source_page_with_raw_archive_reference(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(_event_path("lab-report.json"), target)

    assert result["status"] == "ok"
    source_page = target / "02_wiki" / "sources" / "evt_lab_report_001.md"
    assert source_page.exists()
    content = source_page.read_text(encoding="utf-8")
    assert 'source_path: "01_raw/labs/' in content
    assert "## 来源信息" in content
    assert "## 提取事实" in content
    assert "## 异常项" in content
    assert "## 影响到的 Wiki 页面" in content
    assert "02_wiki/members/dad.md" in content
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


def test_plain_symptom_text_without_keyword_still_uses_symptom_note(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    event_path = _materialize_event(
        tmp_path,
        "symptom-note-low-confidence.json",
        event_id="evt_plain_note_001",
        member_id="dad",
        member_hint="dad",
        match_confidence=1.0,
    )
    raw_event = json.loads(event_path.read_text(encoding="utf-8"))
    raw_event["payload"]["text"] = "昨晚开始咳嗽发热两天"
    raw_event["payload"]["attachments"][0]["source_name"] = "note.txt"
    event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(event_path, target)

    assert result["status"] == "ok"
    assert "(symptom_note)" in result["summary"]
    assert not any(
        artifact["artifact_type"] == "raw_archive" for artifact in result["artifacts"]
    )
    source_page = target / "02_wiki" / "sources" / "evt_plain_note_001.md"
    assert source_page.exists()
    content = source_page.read_text(encoding="utf-8")
    assert "source_kind: symptom_note" in content
    assert "source_path: null" in content


def test_path_like_event_and_attachment_ids_stay_within_vault(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    event_path = _materialize_event(
        tmp_path,
        "lab-report.json",
        event_id="../../../../escaped_lab",
        member_id="dad",
        member_hint="dad",
        match_confidence=1.0,
    )
    raw_event = json.loads(event_path.read_text(encoding="utf-8"))
    raw_event["payload"]["attachments"][0]["attachment_id"] = "../../../../escape_att"
    event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(event_path, target)

    assert result["status"] == "ok"
    source_page = Path(
        next(artifact["path"] for artifact in result["artifacts"] if artifact["artifact_type"] == "source_page")
    ).resolve()
    assert source_page.is_relative_to((target / "02_wiki" / "sources").resolve())
    raw_path = Path(
        next(artifact["path"] for artifact in result["artifacts"] if artifact["artifact_type"] == "raw_archive")
    ).resolve()
    assert raw_path.is_relative_to((target / "01_raw" / "labs").resolve())
    runtime_paths = [
        Path(update["path"]).resolve()
        for update in result["runtime_updates"]
        if update["entity_type"] in {"ingest_job", "dedupe_record", "review_item"}
    ]
    assert runtime_paths
    for runtime_path in runtime_paths:
        assert runtime_path.is_relative_to((target / "99_runtime").resolve())


def test_source_page_failure_leaves_archived_raw_checkpoint(monkeypatch, run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("family_doctor.ingest_pipeline.write_source_page", boom)

    with pytest.raises(RuntimeError, match="boom"):
        run_ingest_pipeline(_event_path("lab-report.json"), target)

    job = json.loads(
        (target / "99_runtime" / "jobs" / "ingest_job_evt_lab_report_001.json").read_text(
            encoding="utf-8"
        )
    )
    assert job["status"] == "processing"
    assert job["phase"] == "archived_raw"
    assert job["completed_writes"] == ["ingest_job", "raw_archive"]


def test_plain_symptom_text_without_symptom_keyword_stays_as_symptom_note(
    run_bootstrap, tmp_path
):
    target = tmp_path / "family-health"
    event_path = _materialize_plain_symptom_event(
        tmp_path,
        event_id="evt_symptom_note_plain_text_001",
    )
    event = load_event(event_path)
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(event_path, target)

    assert "symptom" not in (event.payload_text or "").lower()
    assert "symptom" not in (event.attachments[0].source_name or "").lower()
    assert result["status"] == "ok"
    source_page = target / "02_wiki" / "sources" / "evt_symptom_note_plain_text_001.md"
    assert source_page.exists()
    content = source_page.read_text(encoding="utf-8")
    assert "source_kind: symptom_note" in content
    assert "source_path: null" in content
    assert not any(
        artifact["artifact_type"] == "raw_archive" for artifact in result["artifacts"]
    )
    assert not list((target / "01_raw" / "reports").glob("*evt_symptom_note_plain_text_001*"))


def test_source_page_frontmatter_quotes_yaml_sensitive_scalars():
    event = IngestEvent(
        request_id="req_sensitive",
        event_id="evt_bad: injected\nfoo: bar",
        idempotency_key="idem_sensitive",
        correlation_id="corr_sensitive",
        causation_id=None,
        occurred_at="2026-04-21T12:00:00+08:00",
        event_type="ingest",
        trigger_mode="user_message",
        actor_id="user_mom",
        actor_role="member",
        member_id="mom:primary",
        member_hint="mom",
        match_confidence=1.0,
        payload_text="报告里写着: ALT #偏高",
        source_refs=(),
        attachments=(),
        context_source="host-runtime",
        context_locale="zh-CN",
        context_timezone="Asia/Shanghai",
        runtime_related_id=None,
        runtime_review_item_id=None,
        runtime_dedupe_scope="family-health",
    )
    archived_artifacts = [
        ArchivedArtifact(
            attachment_id="att:1",
            path=Path("/tmp/ignored"),
            relative_path="01_raw/reports/report:1.txt",
        )
    ]

    content = build_source_page_content(event, "checkup_report", archived_artifacts)

    assert 'source_id: "evt_bad: injected\\nfoo: bar"' in content
    assert 'member_id: "mom:primary"' in content
    assert 'source_path: "01_raw/reports/report:1.txt"' in content
    assert "02_wiki/members/mom-primary.md" in content
    assert "02_wiki/plans/mom-primary.md" in content
    assert "02_wiki/members/mom:primary.md" not in content
