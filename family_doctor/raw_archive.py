from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from family_doctor.ingest_models import IngestEvent, NormalizedAttachment


@dataclass(frozen=True)
class ArchivedArtifact:
    attachment_id: str
    path: Path
    relative_path: str


def archive_subdir_for_kind(source_kind: str) -> str | None:
    mapping = {
        "checkup_report": "reports",
        "lab_result": "labs",
        "medication_record": "medications",
        "symptom_note": None,
    }
    return mapping.get(source_kind)


def should_archive_raw(source_kind: str) -> bool:
    return archive_subdir_for_kind(source_kind) is not None


def _safe_name(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return normalized or "attachment"


def _assert_within_root(path: Path, root: Path) -> Path:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    resolved_path.relative_to(resolved_root)
    return resolved_path


def _target_name(event: IngestEvent, attachment: NormalizedAttachment) -> str:
    original_name = attachment.source_name or attachment.path.name or attachment.attachment_id
    safe_event_id = _safe_name(event.event_id)
    safe_attachment_id = _safe_name(attachment.attachment_id)
    safe_original = _safe_name(original_name)
    return f"{safe_event_id}__{safe_attachment_id}__{safe_original}"


def archive_event_raw_files(target: Path, event: IngestEvent, source_kind: str) -> list[ArchivedArtifact]:
    subdir = archive_subdir_for_kind(source_kind)
    if subdir is None:
        return []

    archive_root = target / "01_raw" / subdir
    archive_root.mkdir(parents=True, exist_ok=True)

    archived: list[ArchivedArtifact] = []
    for attachment in event.attachments:
        archived_path = _assert_within_root(archive_root / _target_name(event, attachment), archive_root)
        shutil.copy2(attachment.path, archived_path)
        archived.append(
            ArchivedArtifact(
                attachment_id=attachment.attachment_id,
                path=archived_path,
                relative_path=archived_path.relative_to(target.resolve()).as_posix(),
            )
        )

    return archived
