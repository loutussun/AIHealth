import json
from pathlib import Path

from family_doctor.query_pipeline import run_query_pipeline


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def _assert_query_contract(result: dict[str, object]) -> None:
    assert result["route"] == "query"
    assert isinstance(result["status"], str)
    assert isinstance(result["summary"], str)
    assert isinstance(result["answer"], str)
    assert isinstance(result["used_sources"], list)
    assert isinstance(result["followup_suggestions"], list)


def test_query_pipeline_answers_current_medications_from_member_then_medication_pages(
    materialize_query_event,
    tmp_path,
):
    event_path = materialize_query_event(
        tmp_path,
        question="妈妈现在在吃什么药？",
        intent_hint="current_medications",
    )

    result = run_query_pipeline(event_path)

    _assert_query_contract(result)
    assert result["status"] == "ok"
    assert "氨氯地平" in result["answer"]
    assert "5mg" in result["answer"]
    assert "待核实" in result["answer"]


def test_query_pipeline_surfaces_latest_records_from_sources_after_member_context(
    materialize_query_event,
    tmp_path,
):
    event_path = materialize_query_event(
        tmp_path,
        question="妈妈最近有什么资料？",
        intent_hint="recent_records",
    )

    result = run_query_pipeline(event_path)

    _assert_query_contract(result)
    assert result["status"] == "ok"
    assert "2026-04-18" in result["answer"]
    assert "148/92" in result["answer"]
    assert result["used_sources"]


def test_query_pipeline_summarizes_visit_preparation_from_plans_before_low_evidence_qa(
    materialize_query_event,
    tmp_path,
):
    event_path = materialize_query_event(
        tmp_path,
        question="妈妈复诊前要准备什么？",
        intent_hint="visit_preparation",
    )

    result = run_query_pipeline(event_path)

    _assert_query_contract(result)
    assert result["status"] == "ok"
    assert "血压记录" in result["answer"]
    assert "药盒" in result["answer"]
    assert "qa_mom_prepare_001" not in result["used_sources"]


def test_query_pipeline_returns_conservative_low_evidence_answer_when_context_is_weak(
    materialize_query_event,
    tmp_path,
):
    event_path = materialize_query_event(
        tmp_path,
        question="妈妈现在可以继续原样吃药吗？",
        intent_hint="low_evidence_safe_answer",
        allow_qa_summary_reuse=True,
    )

    raw_event = json.loads(event_path.read_text(encoding="utf-8"))
    raw_event["retrieval"]["members"][0]["sections"]["current_medications"] = []
    raw_event["retrieval"]["plans"][0]["sections"]["visit_prep"] = []
    raw_event["retrieval"]["medications"] = []
    event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_query_pipeline(event_path)

    _assert_query_contract(result)
    assert result["status"] == "ok"
    assert "无法确认" in result["answer"]
    assert "请以医生" in result["answer"]
    assert "不要自行调整" in result["answer"]


def test_query_pipeline_filters_out_other_member_retrieval_items(
    materialize_query_event,
    tmp_path,
):
    event_path = materialize_query_event(
        tmp_path,
        question="妈妈现在在吃什么药？",
        intent_hint="current_medications",
    )

    raw_event = json.loads(event_path.read_text(encoding="utf-8"))
    raw_event["retrieval"]["members"].append(
        {
            "member_id": "dad",
            "display_name": "爸爸",
            "page_path": "02_wiki/members/dad.md",
            "sections": {
                "current_medications": ["二甲双胍（爸爸）"],
            },
        }
    )
    raw_event["retrieval"]["medications"].append(
        {
            "medication_id": "metformin",
            "display_name": "二甲双胍",
            "member_id": "dad",
            "page_path": "02_wiki/medications/metformin.md",
            "sections": {
                "dosage": ["0.5g，每日两次（爸爸）。"],
            },
        }
    )
    event_path.write_text(json.dumps(raw_event, ensure_ascii=False, indent=2), encoding="utf-8")

    result = run_query_pipeline(event_path)

    _assert_query_contract(result)
    assert "氨氯地平" in result["answer"]
    assert "5mg" in result["answer"]
    assert "二甲双胍" not in result["answer"]
    assert "爸爸" not in result["answer"]
    assert all("metformin" not in source for source in result["used_sources"])
    assert all("dad" not in source for source in result["used_sources"])
