from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


QUERY_RETRIEVAL_PRIORITY = ("members", "plans", "medications", "sources", "qa_summaries")


@dataclass(frozen=True)
class QueryContext:
    event_id: str
    request_id: str
    member_id: str | None
    question: str
    intent_hint: str | None
    allow_qa_summary_reuse: bool
    retrieval: dict[str, tuple[dict[str, Any], ...]]

    def ordered_retrieval_items(self) -> tuple[tuple[str, dict[str, Any]], ...]:
        ordered: list[tuple[str, dict[str, Any]]] = []
        seen_buckets: set[str] = set()
        for bucket in QUERY_RETRIEVAL_PRIORITY:
            seen_buckets.add(bucket)
            if bucket == "qa_summaries" and not self.allow_qa_summary_reuse:
                continue
            for item in self.retrieval.get(bucket, ()):
                ordered.append((bucket, item))
        for bucket, items in self.retrieval.items():
            if bucket in seen_buckets:
                continue
            for item in items:
                ordered.append((bucket, item))
        return tuple(ordered)


def load_query_event(event_path: Path) -> dict[str, Any]:
    return json.loads(event_path.read_text(encoding="utf-8"))


def _item_matches_member(item: Any, member_id: str | None) -> bool:
    if not isinstance(item, dict):
        return False
    if member_id is None:
        return True
    item_member_id = item.get("member_id")
    if item_member_id is None:
        return False
    return item_member_id == member_id


def build_query_context(event: dict[str, Any]) -> QueryContext:
    payload = event.get("payload", {})
    target = event.get("target", {})
    member_id = target.get("member_id")
    retrieval = event.get("retrieval", {})
    normalized_retrieval = {
        bucket: tuple(item for item in items if _item_matches_member(item, member_id))
        for bucket, items in retrieval.items()
    }
    return QueryContext(
        event_id=event["event_id"],
        request_id=event["request_id"],
        member_id=member_id,
        question=payload.get("text", ""),
        intent_hint=payload.get("intent_hint"),
        allow_qa_summary_reuse=bool(payload.get("allow_qa_summary_reuse", False)),
        retrieval=normalized_retrieval,
    )
