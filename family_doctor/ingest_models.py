from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NormalizedAttachment:
    attachment_id: str
    kind: str
    path: Path
    mime_type: str | None
    caption: str | None
    source_name: str | None
    content_sha256: str | None
    attachment_group_id: str | None


@dataclass(frozen=True)
class IngestEvent:
    request_id: str
    event_id: str
    idempotency_key: str
    correlation_id: str
    causation_id: str | None
    occurred_at: str
    event_type: str
    trigger_mode: str
    actor_id: str
    actor_role: str
    member_id: str | None
    member_hint: str
    match_confidence: float
    payload_text: str | None
    source_refs: tuple[str, ...]
    attachments: tuple[NormalizedAttachment, ...]
    context_source: str
    context_locale: str
    context_timezone: str
    runtime_related_id: str | None
    runtime_review_item_id: str | None
    runtime_dedupe_scope: str

