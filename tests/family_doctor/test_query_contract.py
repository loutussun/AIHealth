from pathlib import Path

from family_doctor.query_context import (
    QUERY_RETRIEVAL_PRIORITY,
    build_query_context,
    load_query_event,
)


ROOT = Path(__file__).resolve().parents[2]


def _event_path(name: str) -> Path:
    return ROOT / "tests" / "family_doctor" / "fixtures" / "events" / name


def test_query_event_fixture_freezes_minimal_shape():
    event = load_query_event(_event_path("query-mvp.json"))

    assert event["event_type"] == "query"
    assert event["target"]["member_id"] == "mom"
    assert event["payload"]["text"] == "妈妈现在在吃什么药？"
    assert event["payload"]["intent_hint"] == "current_medications"
    assert event["payload"]["allow_qa_summary_reuse"] is False
    assert "query" not in event
    assert event["retrieval"]["members"][0]["sections"]["current_medications"] == [
        "氨氯地平（名称/剂量待核实）"
    ]
    assert event["retrieval"]["plans"][0]["sections"]["visit_prep"] == [
        "带上最近一周血压记录。",
        "带上当前在用药盒或药品照片。"
    ]
    assert event["retrieval"]["medications"][0]["sections"]["dosage"] == ["5mg，每晚一次。"]
    assert event["retrieval"]["sources"][0]["summary"] == "最近资料显示 2026-04-18 血压复测 148/92 mmHg。"
    assert event["retrieval"]["qa_summaries"][0]["evidence_level"] == "low"


def test_build_query_context_locks_read_priority_and_bucket_shapes():
    context = build_query_context(load_query_event(_event_path("query-mvp.json")))

    assert context.member_id == "mom"
    assert context.question == "妈妈现在在吃什么药？"
    assert context.intent_hint == "current_medications"
    assert tuple(bucket for bucket, _ in context.ordered_retrieval_items()) == (
        "members",
        "plans",
        "medications",
        "sources",
    )
    assert "qa_summaries" in context.retrieval
    assert "archive_notes" not in context.retrieval


def test_build_query_context_keeps_unknown_buckets_and_only_uses_priority_for_ordering(
    materialize_query_event,
    tmp_path,
):
    event_path = materialize_query_event(
        tmp_path,
        question="妈妈最近有什么资料？",
        intent_hint="recent_records",
    )
    event = load_query_event(event_path)
    event["retrieval"]["archive_notes"] = [{"note_id": "arch_001", "member_id": "mom"}]

    context = build_query_context(event)

    assert context.retrieval["archive_notes"] == ({"note_id": "arch_001", "member_id": "mom"},)
    assert tuple(bucket for bucket, _ in context.ordered_retrieval_items()) == (
        "members",
        "plans",
        "medications",
        "sources",
        "archive_notes",
    )


def test_query_event_materializer_reuses_the_same_contract_for_all_mvp_scenarios(
    materialize_query_event,
    tmp_path,
):
    event_path = materialize_query_event(
        tmp_path,
        question="复诊前要准备什么？",
        intent_hint="visit_preparation",
    )

    event = load_query_event(event_path)

    assert event["target"]["member_id"] == "mom"
    assert event["retrieval"]["members"][0]["member_id"] == "mom"
    assert event["retrieval"]["plans"][0]["member_id"] == "mom"
    assert event["retrieval"]["medications"][0]["member_id"] == "mom"
    assert event["retrieval"]["sources"][0]["member_id"] == "mom"
    assert event["retrieval"]["qa_summaries"][0]["member_id"] == "mom"
    assert event["payload"]["allow_qa_summary_reuse"] is False


def test_build_query_context_only_includes_qa_summaries_in_order_when_explicitly_enabled(
    materialize_query_event,
    tmp_path,
):
    event_path = materialize_query_event(
        tmp_path,
        question="复诊前要准备什么？",
        intent_hint="visit_preparation",
        allow_qa_summary_reuse=True,
    )

    context = build_query_context(load_query_event(event_path))

    assert QUERY_RETRIEVAL_PRIORITY[-1] == "qa_summaries"
    assert tuple(bucket for bucket, _ in context.ordered_retrieval_items()) == (
        "members",
        "plans",
        "medications",
        "sources",
        "qa_summaries",
    )


def test_build_query_context_does_not_fallback_to_legacy_query_fields(
    materialize_query_event,
    tmp_path,
):
    event_path = materialize_query_event(
        tmp_path,
        question="妈妈现在在吃什么药？",
        intent_hint="current_medications",
    )
    event = load_query_event(event_path)
    event["payload"].pop("text")
    event["payload"].pop("intent_hint")
    event["query"] = {
        "question": "旧 query 字段里的问题",
        "intent_hint": "recent_records",
    }

    context = build_query_context(event)

    assert context.question == ""
    assert context.intent_hint is None
