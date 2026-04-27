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
    member_id: str,
    member_hint: str,
    match_confidence: float = 1.0,
) -> Path:
    raw_event = json.loads(_event_path(source_name).read_text(encoding="utf-8"))
    raw_event["event_id"] = event_id
    raw_event["request_id"] = f"req_{event_id}"
    raw_event["correlation_id"] = f"corr_{event_id}"
    raw_event["target"] = {
        "member_id": member_id,
        "member_hint": member_hint,
        "match_confidence": match_confidence,
    }

    event_path = tmp_path / f"{event_id}.json"
    event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")
    return event_path


def test_symptom_ingest_creates_member_and_plan_pages(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    event_path = _materialize_event(
        tmp_path,
        "symptom-note-low-confidence.json",
        event_id="evt_symptom_note_member_001",
        member_id="dad",
        member_hint="dad",
    )
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(event_path, target)

    assert result["status"] == "ok"
    member_page = target / "02_wiki" / "members" / "dad.md"
    plan_page = target / "02_wiki" / "plans" / "dad.md"
    source_page = target / "02_wiki" / "sources" / "evt_symptom_note_member_001.md"

    assert member_page.exists()
    assert plan_page.exists()
    assert source_page.exists()

    member_content = member_page.read_text(encoding="utf-8")
    assert "## 来源索引" in member_content
    assert "evt_symptom_note_member_001.md" in member_content
    assert "## 待核实项" in member_content
    assert "待核实" in member_content
    assert "## 当前计划" in member_content
    assert "dad.md" in member_content

    plan_content = plan_page.read_text(encoding="utf-8")
    assert "## 待复查事项" in plan_content
    assert "症状" in plan_content
    assert "evt_symptom_note_member_001.md" in plan_content

    assert any(update["page_type"] == "member_page" for update in result["wiki_updates"])
    assert any(update["page_type"] == "plan_page" for update in result["wiki_updates"])


def test_medication_ingest_creates_medication_page_and_links_member(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(_event_path("medication-photo.json"), target)

    assert result["status"] == "ok"
    member_page = target / "02_wiki" / "members" / "mom.md"
    medication_page = target / "02_wiki" / "medications" / "medication-photo.md"

    assert member_page.exists()
    assert medication_page.exists()

    member_content = member_page.read_text(encoding="utf-8")
    assert "## 当前用药" in member_content
    assert "medication-photo.md" in member_content
    assert "## 来源索引" in member_content
    assert "evt_medication_photo_001.md" in member_content

    medication_content = medication_page.read_text(encoding="utf-8")
    assert "# medication-photo" in medication_content
    assert "## 关联成员" in medication_content
    assert "mom" in medication_content
    assert "evt_medication_photo_001.md" in medication_content

    assert any(update["page_type"] == "member_page" for update in result["wiki_updates"])
    assert any(update["page_type"] == "medication_page" for update in result["wiki_updates"])


def test_low_confidence_match_does_not_write_member_or_plan_pages(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    event_path = _materialize_event(
        tmp_path,
        "checkup-report.json",
        event_id="evt_checkup_low_confidence_block_001",
        member_id="dad",
        member_hint="dad",
        match_confidence=0.2,
    )
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(event_path, target)

    assert result["status"] == "needs_review"
    assert (target / "02_wiki" / "sources" / "evt_checkup_low_confidence_block_001.md").exists()
    assert not (target / "02_wiki" / "members" / "dad.md").exists()
    assert not (target / "02_wiki" / "plans" / "dad.md").exists()
    assert all(
        artifact["artifact_type"] not in {"member_page", "plan_page"} for artifact in result["artifacts"]
    )
    assert all(
        update["page_type"] not in {"member_page", "plan_page"} for update in result["wiki_updates"]
    )
    assert all(
        update["entity_type"] not in {"member_page", "plan_page"} for update in result["runtime_updates"]
    )

    ingest_job = json.loads(
        (target / "99_runtime" / "jobs" / "ingest_job_evt_checkup_low_confidence_block_001.json").read_text(
            encoding="utf-8"
        )
    )
    assert ingest_job["status"] == "pending_review"
    assert set(ingest_job["planned_writes"]) == {
        "ingest_job",
        "raw_archive",
        "source_page",
        "review_item",
    }
    assert set(ingest_job["completed_writes"]) == {
        "ingest_job",
        "raw_archive",
        "source_page",
        "review_item",
    }


def test_ingest_job_planned_and_completed_writes_include_member_and_plan_pages(
    run_bootstrap, tmp_path
):
    target = tmp_path / "family-health"
    event_path = _materialize_event(
        tmp_path,
        "symptom-note-low-confidence.json",
        event_id="evt_symptom_write_sets_001",
        member_id="dad",
        member_hint="dad",
    )
    assert run_bootstrap(target).returncode == 0

    result = run_ingest_pipeline(event_path, target)

    assert result["status"] == "ok"
    ingest_job = json.loads(
        (target / "99_runtime" / "jobs" / "ingest_job_evt_symptom_write_sets_001.json").read_text(
            encoding="utf-8"
        )
    )

    assert set(ingest_job["planned_writes"]) == {
        "ingest_job",
        "source_page",
        "member_page",
        "plan_page",
    }
    assert set(ingest_job["completed_writes"]) == {
        "ingest_job",
        "source_page",
        "member_page",
        "plan_page",
    }
    assert any(artifact["artifact_type"] == "member_page" for artifact in result["artifacts"])
    assert any(artifact["artifact_type"] == "plan_page" for artifact in result["artifacts"])
