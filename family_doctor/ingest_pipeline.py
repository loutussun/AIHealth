from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from family_doctor.ingest_models import IngestEvent, NormalizedAttachment
from family_doctor.runtime_records import (
    write_dedupe_record,
    write_ingest_job,
    write_review_item,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ATTACHMENT_KINDS = {"image", "pdf", "text", "csv", "zip"}
REVIEW_THRESHOLD = 0.5


class IngestError(ValueError):
    """Raised when an ingest event cannot be normalised or processed."""


def _require_dict(raw: Any, label: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise IngestError(f"{label} must be an object")
    return raw


def _require_str(raw: Any, label: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise IngestError(f"{label} must be a non-empty string")
    return raw


def _require_optional_str(raw: Any, label: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw:
        raise IngestError(f"{label} must be a non-empty string when provided")
    return raw


def _require_float(raw: Any, label: str) -> float:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise IngestError(f"{label} must be a number")
    value = float(raw)
    if value < 0 or value > 1:
        raise IngestError(f"{label} must be between 0 and 1")
    return value


def _require_list(raw: Any, label: str) -> list[Any]:
    if not isinstance(raw, list):
        raise IngestError(f"{label} must be an array")
    return raw


def _resolve_attachment_path(raw_path: str, event_path: Path) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        if candidate.exists():
            return candidate
        raise IngestError(f"attachment.path does not exist: {candidate}")

    for resolved in (
        (event_path.parent / candidate).resolve(),
        (Path.cwd() / candidate).resolve(),
        (REPO_ROOT / candidate).resolve(),
    ):
        if resolved.exists():
            return resolved

    raise IngestError(f"attachment.path does not exist: {raw_path}")


def load_event(path: Path) -> IngestEvent:
    raw_event = json.loads(path.read_text(encoding="utf-8"))
    event = _require_dict(raw_event, "event")

    actor = _require_dict(event.get("actor"), "actor")
    target = _require_dict(event.get("target"), "target")
    payload = _require_dict(event.get("payload"), "payload")
    context = _require_dict(event.get("context"), "context")
    runtime = _require_dict(event.get("runtime"), "runtime")

    attachments: list[NormalizedAttachment] = []
    for raw_attachment in _require_list(payload.get("attachments"), "payload.attachments"):
        attachment = _require_dict(raw_attachment, "attachment")
        attachment_kind = _require_str(attachment.get("kind"), "attachment.kind")
        if attachment_kind not in ALLOWED_ATTACHMENT_KINDS:
            raise IngestError(f"attachment.kind must be one of {sorted(ALLOWED_ATTACHMENT_KINDS)}")

        attachments.append(
            NormalizedAttachment(
                attachment_id=_require_str(attachment.get("attachment_id"), "attachment.attachment_id"),
                kind=attachment_kind,
                path=_resolve_attachment_path(_require_str(attachment.get("path"), "attachment.path"), path),
                mime_type=_require_optional_str(attachment.get("mime_type"), "attachment.mime_type"),
                caption=_require_optional_str(attachment.get("caption"), "attachment.caption"),
                source_name=_require_optional_str(attachment.get("source_name"), "attachment.source_name"),
                content_sha256=_require_optional_str(
                    attachment.get("content_sha256"), "attachment.content_sha256"
                ),
                attachment_group_id=_require_optional_str(
                    attachment.get("attachment_group_id"), "attachment.attachment_group_id"
                ),
            )
        )

    source_refs = tuple(
        _require_str(ref, "payload.source_refs[]")
        for ref in _require_list(payload.get("source_refs"), "payload.source_refs")
    )

    return IngestEvent(
        request_id=_require_str(event.get("request_id"), "request_id"),
        event_id=_require_str(event.get("event_id"), "event_id"),
        idempotency_key=_require_str(event.get("idempotency_key"), "idempotency_key"),
        correlation_id=_require_str(event.get("correlation_id"), "correlation_id"),
        causation_id=_require_optional_str(event.get("causation_id"), "causation_id"),
        occurred_at=_require_str(event.get("occurred_at"), "occurred_at"),
        event_type=_require_str(event.get("event_type"), "event_type"),
        trigger_mode=_require_str(event.get("trigger_mode"), "trigger_mode"),
        actor_id=_require_str(actor.get("actor_id"), "actor.actor_id"),
        actor_role=_require_str(actor.get("role"), "actor.role"),
        member_id=_require_optional_str(target.get("member_id"), "target.member_id"),
        member_hint=_require_str(target.get("member_hint"), "target.member_hint"),
        match_confidence=_require_float(target.get("match_confidence"), "target.match_confidence"),
        payload_text=_require_optional_str(payload.get("text"), "payload.text"),
        source_refs=source_refs,
        attachments=tuple(attachments),
        context_source=_require_str(context.get("source"), "context.source"),
        context_locale=_require_str(context.get("locale"), "context.locale"),
        context_timezone=_require_str(context.get("timezone"), "context.timezone"),
        runtime_related_id=_require_optional_str(runtime.get("related_runtime_id"), "runtime.related_runtime_id"),
        runtime_review_item_id=_require_optional_str(runtime.get("review_item_id"), "runtime.review_item_id"),
        runtime_dedupe_scope=_require_str(runtime.get("dedupe_scope"), "runtime.dedupe_scope"),
    )


def _fingerprint_material(event: IngestEvent) -> str:
    attachment_shas = sorted(
        attachment.content_sha256 for attachment in event.attachments if attachment.content_sha256
    )
    parts = [event.idempotency_key, event.event_type, event.member_id or "", *attachment_shas]
    return "\u0000".join(parts)


def derive_dedupe_fingerprint(event: IngestEvent) -> str:
    return hashlib.sha256(_fingerprint_material(event).encode("utf-8")).hexdigest()


def _existing_job_records(target: Path) -> list[tuple[Path, dict[str, Any]]]:
    jobs_dir = target / "99_runtime" / "jobs"
    if not jobs_dir.exists():
        return []

    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(jobs_dir.glob("ingest_job_*.json")):
        records.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return records


def _existing_dedupe_records(target: Path) -> list[tuple[Path, dict[str, Any]]]:
    state_dir = target / "99_runtime" / "state"
    if not state_dir.exists():
        return []

    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(state_dir.glob("dedupe_record_*.json")):
        records.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return records


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_job_record_by_event_id(target: Path, event_id: str) -> tuple[Path, dict[str, Any]] | None:
    for path, record in _existing_job_records(target):
        if record.get("event_id") == event_id:
            return path, record
    return None


def _resolve_duplicate_match(
    target: Path,
    duplicate_kind: str | None,
    duplicate_path: str | None,
    matched_job_id: str | None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if duplicate_kind == "ingest_job" and duplicate_path:
        path = Path(duplicate_path)
        return path, _load_json(path)

    if matched_job_id:
        matched = _find_job_record_by_event_id(target, matched_job_id)
        if matched is not None:
            return matched

    return None, None


def _write_job_fingerprint(job_path: Path, fingerprint: str) -> None:
    payload = _load_json(job_path)
    payload["fingerprint"] = fingerprint
    job_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _find_duplicate(
    target: Path, event: IngestEvent, fingerprint: str
) -> tuple[str | None, str | None, str | None]:
    for path, record in _existing_dedupe_records(target):
        if record.get("fingerprint") == fingerprint:
            matched_job_id = (
                record.get("matched_job_id") if isinstance(record.get("matched_job_id"), str) else None
            )
            return "dedupe_record", str(path), matched_job_id

    for path, record in _existing_job_records(target):
        if record.get("fingerprint") == fingerprint:
            matched_job_id = record.get("event_id") if isinstance(record.get("event_id"), str) else event.event_id
            return "ingest_job", str(path), matched_job_id

    return None, None, None


def _duplicate_result_details(
    matched_job_status: str | None, matched_job_phase: str | None
) -> tuple[str, str, str, str, str, list[str], str | None]:
    if matched_job_status == "pending_review":
        return (
            "pending_review",
            matched_job_phase or "accepted",
            "needs_review",
            "matched job still pending review",
            "已识别为重复输入，关联任务仍需人工复核。",
            ["等待已命中的复核任务完成后再继续处理。"],
            "matched duplicate remains pending human review",
        )

    if matched_job_status in {"created", "processing"}:
        in_flight_status = matched_job_status
        return (
            in_flight_status,
            matched_job_phase or "accepted",
            "ok",
            f"matched job still {in_flight_status}",
            "已识别为重复输入，关联任务仍在处理中。",
            ["等待已命中的任务完成后再继续处理。"],
            "matched duplicate is still in flight",
        )

    if matched_job_status == "committed" and matched_job_phase == "committed":
        return (
            "committed",
            "committed",
            "ok",
            "",
            "已识别为重复输入，未重复处理。",
            [],
            None,
        )

    failure_status = matched_job_status if matched_job_status in {"failed", "aborted"} else "failed"
    failure_phase = matched_job_phase or "accepted"
    failure_label = matched_job_status or "unknown"
    return (
        failure_status,
        failure_phase,
        "error",
        f"matched job is not in a reusable success state ({failure_label})",
        "已识别为重复输入，但关联任务未处于可复用的成功状态。",
        ["检查已命中的运行时任务状态后再决定是否重试。"],
        "matched duplicate is not in a reusable success state",
    )


def _classification(event: IngestEvent) -> str:
    text = (event.payload_text or "").lower()
    names = " ".join(
        [
            event.member_hint.lower(),
            *(attachment.source_name.lower() for attachment in event.attachments if attachment.source_name),
        ]
    )
    blob = f"{text} {names}"

    if any(keyword in blob for keyword in ["lab", "化验", "检验", "化验单"]):
        return "lab_result"
    if any(keyword in blob for keyword in ["medication", "药", "处方", "药品"]):
        return "medication_record"
    if any(keyword in blob for keyword in ["symptom", "症状", "不舒服", "疼"]):
        return "symptom_note"
    return "checkup_report"


def _evidence_refs(event: IngestEvent) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = [
        {
            "kind": "event",
            "event_id": event.event_id,
            "idempotency_key": event.idempotency_key,
        }
    ]
    for attachment in event.attachments:
        refs.append(
            {
                "kind": "attachment",
                "attachment_id": attachment.attachment_id,
                "path": str(attachment.path),
                "source_name": attachment.source_name,
            }
        )
    return refs


def _runtime_update(path: Path, entity_type: str, status: str, phase: str | None = None) -> dict[str, Any]:
    update: dict[str, Any] = {"entity_type": entity_type, "path": str(path), "status": status}
    if phase is not None:
        update["phase"] = phase
    return update


def _output_result(
    *,
    status: str,
    summary: str,
    message: str,
    artifacts: list[Any],
    wiki_updates: list[Any],
    runtime_updates: list[Any],
    evidence_refs: list[Any],
    followup_suggestions: list[str],
) -> dict[str, Any]:
    return {
        "status": status,
        "route": "ingest",
        "summary": summary,
        "user_facing_message": message,
        "artifacts": artifacts,
        "wiki_updates": wiki_updates,
        "runtime_updates": runtime_updates,
        "evidence_refs": evidence_refs,
        "followup_suggestions": followup_suggestions,
    }


def run_ingest_pipeline(event_path: Path, target: Path) -> dict[str, Any]:
    event = load_event(event_path)
    fingerprint = derive_dedupe_fingerprint(event)
    duplicate_kind, duplicate_path, matched_job_id = _find_duplicate(target, event, fingerprint)

    if duplicate_path:
        matched_job_path, matched_job_record = _resolve_duplicate_match(
            target, duplicate_kind, duplicate_path, matched_job_id
        )
        matched_job_status = (
            matched_job_record.get("status") if isinstance(matched_job_record.get("status"), str) else None
        )
        matched_job_phase = (
            matched_job_record.get("phase") if isinstance(matched_job_record.get("phase"), str) else None
        )
        (
            current_status,
            current_phase,
            result_status,
            summary_suffix,
            message,
            followup_suggestions,
            recovery_hint,
        ) = _duplicate_result_details(matched_job_status, matched_job_phase)
        current_job = write_ingest_job(
            target=target,
            event=event,
            phase="accepted",
            status="processing",
            planned_writes=["ingest_job", "dedupe_record"],
            completed_writes=["ingest_job"],
            source_id=event.event_id,
            recovery_hint="duplicate detected; reconcile with matched job",
        )
        _write_job_fingerprint(current_job, fingerprint)
        dedupe_path = write_dedupe_record(
            target=target,
            event=event,
            fingerprint=fingerprint,
            matched_job_id=matched_job_id or event.event_id,
        )
        current_job = write_ingest_job(
            target=target,
            event=event,
            phase=current_phase,
            status=current_status,
            planned_writes=["ingest_job", "dedupe_record"],
            completed_writes=["ingest_job", "dedupe_record"],
            source_id=matched_job_id or event.event_id,
            recovery_hint=recovery_hint,
        )
        _write_job_fingerprint(current_job, fingerprint)

        runtime_updates = []
        if matched_job_path is not None and matched_job_path != current_job:
            runtime_updates.append(
                _runtime_update(
                    matched_job_path,
                    "ingest_job",
                    matched_job_status or "committed",
                    matched_job_phase,
                )
            )
        elif duplicate_path is not None and duplicate_kind == "dedupe_record":
            runtime_updates.append(_runtime_update(Path(duplicate_path), "dedupe_record", "committed"))

        runtime_updates.extend(
            [
                _runtime_update(current_job, "ingest_job", current_status, current_phase),
                _runtime_update(dedupe_path, "dedupe_record", "committed"),
            ]
        )

        return _output_result(
            status=result_status,
            summary=(
                f"deduplicated ingest event {event.event_id}; {summary_suffix}"
                if summary_suffix
                else f"deduplicated ingest event {event.event_id}"
            ),
            message=message,
            artifacts=[],
            wiki_updates=[],
            runtime_updates=runtime_updates,
            evidence_refs=_evidence_refs(event),
            followup_suggestions=followup_suggestions,
        )

    initial_job = write_ingest_job(
        target=target,
        event=event,
        phase="accepted",
        status="processing",
        planned_writes=["ingest_job", "review_item"],
        completed_writes=[],
        source_id=event.event_id,
        recovery_hint="resume from accepted phase",
    )
    _write_job_fingerprint(initial_job, fingerprint)

    if event.match_confidence < REVIEW_THRESHOLD or event.member_id is None:
        review_path = write_review_item(
            target=target,
            event=event,
            reason="low-confidence member match",
            severity="medium",
        )
        write_ingest_job(
            target=target,
            event=event,
            phase="accepted",
            status="pending_review",
            planned_writes=["ingest_job", "review_item"],
            completed_writes=["ingest_job", "review_item"],
            source_id=event.event_id,
            recovery_hint="waiting on human review for member resolution",
        )
        return _output_result(
            status="needs_review",
            summary=f"low-confidence member match for {event.event_id}",
            message="需要人工复核成员匹配后再继续处理。",
            artifacts=[],
            wiki_updates=[],
            runtime_updates=[
                _runtime_update(initial_job, "ingest_job", "pending_review", "accepted"),
                _runtime_update(review_path, "review_item", "committed"),
            ],
            evidence_refs=_evidence_refs(event),
            followup_suggestions=["确认成员匹配后重新提交输入。"],
        )

    final_job = write_ingest_job(
        target=target,
        event=event,
        phase="committed",
        status="committed",
        planned_writes=["ingest_job"],
        completed_writes=["ingest_job"],
        source_id=event.event_id,
        recovery_hint=None,
    )
    _write_job_fingerprint(final_job, fingerprint)

    return _output_result(
        status="ok",
        summary=f"ingest committed for {event.event_id} ({_classification(event)})",
        message="已完成摄取处理。",
        artifacts=[],
        wiki_updates=[],
        runtime_updates=[_runtime_update(final_job, "ingest_job", "committed", "committed")],
        evidence_refs=_evidence_refs(event),
        followup_suggestions=[],
    )
