from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from family_doctor.output_pages import build_report_output_markdown
from family_doctor.raw_archive import _assert_within_root, _safe_name
from family_doctor.report_templates import ReportTemplateContext, output_subdir_for


SUPPORTED_REPORT_KINDS = {
    "checkup_update",
    "lab_update",
    "weekly_health_report",
    "monthly_health_report",
}


class ReportError(ValueError):
    """Raised when a report event cannot be normalised."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_dict(raw: Any, label: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ReportError(f"{label} must be an object")
    return raw


def _require_str(raw: Any, label: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ReportError(f"{label} must be a non-empty string")
    return raw


def _require_optional_str(raw: Any, label: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw:
        raise ReportError(f"{label} must be a non-empty string when provided")
    return raw


def _require_list(raw: Any, label: str) -> list[Any]:
    if not isinstance(raw, list):
        raise ReportError(f"{label} must be an array")
    return raw


@dataclass(frozen=True)
class ReportEvent:
    event_id: str
    event_type: str
    report_kind: str
    member_id: str | None
    member_scope: str | None
    period_start: str
    period_end: str
    source_refs: tuple[str, ...]
    runtime_related_id: str | None


def load_report_event(path: Path) -> ReportEvent:
    raw_event = json.loads(path.read_text(encoding="utf-8"))
    event = _require_dict(raw_event, "event")
    target = _require_dict(event.get("target"), "target")
    payload = _require_dict(event.get("payload"), "payload")
    runtime = _require_dict(event.get("runtime"), "runtime")

    event_type = _require_str(event.get("event_type"), "event_type")
    if event_type != "report":
        raise ReportError("event_type must be report")

    report_kind = _require_str(payload.get("report_kind"), "payload.report_kind")
    if report_kind not in SUPPORTED_REPORT_KINDS:
        raise ReportError(f"payload.report_kind unsupported: {report_kind}")

    member_id = _require_optional_str(target.get("member_id"), "target.member_id")
    member_scope = _require_optional_str(payload.get("member_scope"), "payload.member_scope")
    if member_id is None and member_scope is None:
        raise ReportError("report target requires target.member_id or payload.member_scope")

    source_refs = tuple(
        _require_str(ref, "payload.source_refs[]")
        for ref in _require_list(payload.get("source_refs", []), "payload.source_refs")
    )

    return ReportEvent(
        event_id=_require_str(event.get("event_id"), "event_id"),
        event_type=event_type,
        report_kind=report_kind,
        member_id=member_id,
        member_scope=member_scope,
        period_start=_require_str(payload.get("period_start"), "payload.period_start"),
        period_end=_require_str(payload.get("period_end"), "payload.period_end"),
        source_refs=source_refs,
        runtime_related_id=_require_optional_str(
            runtime.get("related_runtime_id"),
            "runtime.related_runtime_id",
        ),
    )


def _runtime_root(target: Path) -> Path:
    runtime_root = target / "99_runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "jobs").mkdir(parents=True, exist_ok=True)
    return runtime_root


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _safe_event_name(event_id: str) -> str:
    normalized = _safe_name(event_id).lstrip(".-")
    return normalized or "report"


def _stable_event_token(event_id: str) -> str:
    safe_name = _safe_event_name(event_id)
    digest = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:10]
    return f"{safe_name}-{digest}"


def _report_job_path(target: Path, event: ReportEvent) -> Path:
    jobs_root = _runtime_root(target) / "jobs"
    filename = f"report_job_{_stable_event_token(event.event_id)}.json"
    return _assert_within_root(jobs_root / filename, jobs_root)


def _report_job_id(event: ReportEvent) -> str:
    return f"report_job_{_stable_event_token(event.event_id)}"


def _output_path(target: Path, event: ReportEvent, output_id: str) -> Path:
    output_root = target / "03_outputs" / output_subdir_for(event.report_kind)
    output_root.mkdir(parents=True, exist_ok=True)
    return _assert_within_root(output_root / f"{output_id}.md", output_root)


def _write_report_job(target: Path, event: ReportEvent, output_path: Path) -> Path:
    path = _report_job_path(target, event)
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    created_at = existing.get("created_at") or _utc_now()
    target_root = target.resolve()

    payload = {
        "entity_type": "report_job",
        "job_id": _report_job_id(event),
        "event_id": event.event_id,
        "status": "committed",
        "phase": "committed",
        "planned_writes": ["report_job", "output_page"],
        "completed_writes": ["report_job", "output_page"],
        "report_kind": event.report_kind,
        "member_id": event.member_id,
        "member_scope": event.member_scope,
        "source_refs": list(event.source_refs),
        "period_start": event.period_start,
        "period_end": event.period_end,
        "related_runtime_id": event.runtime_related_id,
        "output_path": output_path.relative_to(target_root).as_posix(),
        "created_at": created_at,
        "updated_at": _utc_now(),
    }
    return _write_json(path, payload)


def run_report_pipeline(event_path: Path, target: Path) -> dict[str, Any]:
    event = load_report_event(event_path)
    output_id = f"out_{_stable_event_token(event.event_id)}"
    output_path = _output_path(target, event, output_id)

    context = ReportTemplateContext(
        output_id=output_id,
        report_kind=event.report_kind,
        member_id=event.member_id,
        member_scope=event.member_scope,
        period_start=event.period_start,
        period_end=event.period_end,
        related_runtime_id=event.runtime_related_id,
        source_refs=event.source_refs,
        evidence_refs=event.source_refs,
    )
    output_path.write_text(build_report_output_markdown(context), encoding="utf-8")
    report_job_path = _write_report_job(target, event, output_path)

    resolved_target = target.resolve()
    resolved_output = output_path.resolve()
    resolved_report_job = report_job_path.resolve()
    artifact = {
        "artifact_type": "output_page",
        "path": str(resolved_output),
        "relative_path": resolved_output.relative_to(resolved_target).as_posix(),
        "output_id": output_id,
        "output_kind": event.report_kind,
    }

    return {
        "status": "ok",
        "route": "report",
        "summary": f"generated report output for {event.report_kind}",
        "user_facing_message": "报告草稿已生成，当前仅保留长期写回策略 contract，未执行 wiki 写回。",
        "artifacts": [artifact],
        "wiki_updates": [],
        "runtime_updates": [
            {
                "entity_type": "report_job",
                "path": str(resolved_report_job),
                "status": "committed",
            },
            {
                "entity_type": "output_page",
                "path": str(resolved_output),
                "status": "committed",
            }
        ],
        "evidence_refs": [{"kind": "source_ref", "ref": ref} for ref in event.source_refs],
        "followup_suggestions": [],
    }
