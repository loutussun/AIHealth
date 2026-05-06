from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SKILL_DOCS = [
    ROOT / ".codex" / "skills" / "family-doctor" / "SKILL.md",
    ROOT / ".claude" / "skills" / "family-doctor.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_markers_present(text: str, markers: list[str], path: Path) -> None:
    missing = [marker for marker in markers if marker not in text]
    assert not missing, f"{path} missing markers: {missing}"


def _assert_markers_absent(text: str, markers: list[str], path: Path) -> None:
    present = [marker for marker in markers if marker in text]
    assert not present, f"{path} contains forbidden markers: {present}"


def _workflow_section(text: str, workflow: str) -> str:
    heading_pattern = re.compile(rf"(?m)^#+\s+.*{re.escape(workflow)}.*$")
    heading_match = heading_pattern.search(text)
    assert heading_match is not None, f"missing workflow heading: {workflow}"

    start = heading_match.start()
    heading_level = len(heading_match.group(0)) - len(heading_match.group(0).lstrip("#"))
    next_heading_pattern = re.compile(rf"(?m)^#{{1,{heading_level}}}\s+")
    next_heading_match = next_heading_pattern.search(text, heading_match.end())
    end = next_heading_match.start() if next_heading_match else len(text)
    return text[start:end]


def test_skill_docs_define_obsidian_first_workflows() -> None:
    markers = [
        "Obsidian-first",
        "workflow",
        "ingest_report",
        "medical_visit_prep",
        "family_message",
        "daily_tracking_update",
        "health_question",
    ]

    for path in SKILL_DOCS:
        _assert_markers_present(_read(path), markers, path)


def test_skill_docs_map_workflows_to_existing_event_types() -> None:
    markers = [
        "event_type: ingest",
        "event_type: query",
        "event_type: report",
        "payload.report_kind: checkup_update",
        "payload.report_kind: lab_update",
    ]

    for path in SKILL_DOCS:
        _assert_markers_present(_read(path), markers, path)


def test_skill_docs_lock_direct_write_boundaries() -> None:
    markers = [
        "03_outputs/visit-briefs/",
        "03_outputs/family-messages/",
        "03_outputs/qa-summaries/",
        "04_tracking/*.csv",
        "log.md",
        "Do not directly write 01_raw/",
        "Do not directly write 02_wiki/sources/",
        "Do not directly write 02_wiki/members/",
        "Do not directly write 02_wiki/plans/",
        "Do not directly write 03_outputs/checkup-updates/",
        "Do not directly write 03_outputs/lab-updates/",
    ]

    for path in SKILL_DOCS:
        _assert_markers_present(_read(path), markers, path)


def test_skill_docs_lock_health_question_evidence_rules() -> None:
    markers = [
        "03_outputs/* is auxiliary context only",
        "must not be used as standalone evidence",
        "Key claims must cite",
        "source_ref",
        "02_wiki/sources/",
        "04_tracking",
        "source insufficient",
        "default read-only",
        "qa-summaries",
        "explicitly asks",
        "facts",
        "inferences",
        "verification items",
        "source conflict",
        "member uncertainty",
        "missing units or reference ranges",
        "urgent symptoms",
        "medication change request",
        "diagnosis request",
    ]

    for path in SKILL_DOCS:
        content = _read(path)
        section = _workflow_section(content, "health_question")
        _assert_markers_present(section, markers, path)


def test_skill_docs_do_not_claim_new_cli_routes() -> None:
    forbidden_markers = [
        "event_type: visit_brief",
        "event_type: family_message",
        "event_type: daily_tracking_update",
        "visit_brief route",
        "family_message route",
        "daily_tracking_update route",
        "new CLI route",
        "new Python pipeline",
        "OCR/PDF/image parsing is supported",
        "event_type: trend_build",
        "trend_build route",
    ]

    for path in SKILL_DOCS:
        _assert_markers_absent(_read(path), forbidden_markers, path)


def test_skill_docs_lock_per_workflow_operational_contracts() -> None:
    workflow_markers = {
        "ingest_report": [
            "existing ingest pipeline",
            "explicitly requested",
            "source_ref",
            "preserve CSV headers",
            "log.md",
            "member uncertainty",
            "abnormal values",
            "medication dose",
            "diagnosis",
            "missing source",
        ],
        "medical_visit_prep": [
            "02_wiki/members/",
            "02_wiki/sources/",
            "02_wiki/plans/",
            "04_tracking/",
            "03_outputs/visit-briefs/",
            "explicitly requested",
            "visit-brief-template.md",
            "must not diagnose",
            "clinician judgment",
            "source",
            "verification marker",
            "log.md",
        ],
        "family_message": [
            "03_outputs/family-messages/",
            "explicitly requested",
            "family-message-template.md",
            "must not add new medical claims",
            "must not soften urgent risk",
            "不确定项",
            "log.md",
        ],
        "daily_tracking_update": [
            "preserve CSV headers",
            "member_id",
            "date",
            "source_ref",
            "must not silently overwrite",
            "traceable explanation",
            "notes",
            "review",
            "log.md",
        ],
    }

    for path in SKILL_DOCS:
        content = _read(path)
        for workflow, markers in workflow_markers.items():
            section = _workflow_section(content, workflow)
            _assert_markers_present(section, markers, path)


def test_skill_docs_do_not_contradict_route_boundaries() -> None:
    forbidden_markers = [
        "medical_visit_prep route",
        "family_message route",
        "daily_tracking_update route",
        "health_question writes by default",
        "03_outputs/* can be used as evidence",
        "03_outputs/* may be standalone evidence",
    ]

    for path in SKILL_DOCS:
        _assert_markers_absent(_read(path), forbidden_markers, path)
