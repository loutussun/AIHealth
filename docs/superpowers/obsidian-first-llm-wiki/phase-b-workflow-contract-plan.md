# Phase B Workflow Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]` / `- [x]`) syntax for tracking.

**Goal:** Update the `family-doctor` skill documentation so host agents choose Obsidian-first user-intent workflows before mapping to the existing low-level `event_type` core.

**Architecture:** This phase is skill/prompt-contract-only. It adds tests that lock the workflow contract in the two skill documents, then updates `.codex/skills/family-doctor/SKILL.md` and `.claude/skills/family-doctor.md` to describe workflows, vault read/write boundaries, safety rules, and current non-goals. It does not add Python routes, pipelines, OCR, medical reasoning, or Phase 3 trends.

**Tech Stack:** Markdown skill docs, pytest file-content contract tests, existing Python test runner

---

## Source Spec

Implement from:

- `docs/superpowers/obsidian-first-llm-wiki/phase-b-workflow-contract-design.md`

Do not broaden scope beyond that design.

## File Map

- Create: `tests/family_doctor/test_skill_workflow_contract_docs.py`
  - Locks the Phase B workflow contract in both skill docs.
  - Prevents future docs from claiming unsupported CLI routes.
  - Checks evidence and write-boundary rules for `health_question` and direct LLM writes.
  - Requires each workflow to have an independent Markdown heading so per-workflow rules stay locally scoped.
- Modify: `.codex/skills/family-doctor/SKILL.md`
  - Primary Codex skill instructions.
  - Should lead with Obsidian-first workflow selection.
- Modify: `.claude/skills/family-doctor.md`
  - Claude-facing mirror of the same contract.
  - Can be shorter, but must preserve the same workflow, safety, and non-goal rules.
- Modify: `docs/superpowers/obsidian-first-llm-wiki/README.md`
  - Add the Phase B implementation plan to the document index.
  - Update Phase B state after implementation completes.

## Contract Vocabulary

Required workflows:

- `ingest_report`
- `medical_visit_prep`
- `family_message`
- `daily_tracking_update`
- `health_question`

Current low-level core remains:

- `ingest`
- `query`
- `report`
- `reminder`

Disallowed Phase B claims:

- No `visit_brief` CLI route
- No `family_message` CLI route
- No new Python pipeline
- No Phase 3 trends
- No OCR/PDF/image parsing promise

Required per-workflow markers:

- `ingest_report writes via existing ingest pipeline`
- `ingest_report tracking direct write only when explicitly requested and must include source_ref`
- `ingest_report tracking direct write must preserve CSV headers`
- `ingest_report appends log.md after direct tracking write`
- `ingest_report review triggers: member uncertainty, abnormal values, medication dose, diagnosis, missing source`
- `medical_visit_prep reads 02_wiki/members/, 02_wiki/sources/, 02_wiki/plans/, 04_tracking/`
- `medical_visit_prep writes 03_outputs/visit-briefs/ only when explicitly requested`
- `medical_visit_prep uses visit-brief-template.md`
- `medical_visit_prep must not diagnose or replace clinician judgment`
- `medical_visit_prep key claims need source or verification marker`
- `medical_visit_prep appends log.md after artifact write`
- `family_message writes 03_outputs/family-messages/ only when explicitly requested`
- `family_message uses family-message-template.md`
- `family_message must not add new medical claims`
- `family_message must not soften urgent risk`
- `family_message writes uncertainty to 不确定项`
- `family_message appends log.md after artifact write`
- `daily_tracking_update preserves CSV headers`
- `daily_tracking_update requires member_id, date, source_ref`
- `daily_tracking_update must not silently overwrite existing rows`
- `daily_tracking_update corrections require traceable explanation in notes`
- `daily_tracking_update writes ambiguous values to notes or review`
- `daily_tracking_update appends log.md after CSV write`
- `health_question separates facts, inferences, and verification items`
- `health_question review triggers: source conflict, member uncertainty, missing units or reference ranges, urgent symptoms, medication change request, diagnosis request`

Each workflow must also appear in its own Markdown heading in both skill docs:

- `### ingest_report`
- `### medical_visit_prep`
- `### family_message`
- `### daily_tracking_update`
- `## health_question evidence rules` or another heading containing `health_question`

Direct host-LLM writes are allowed only when the user explicitly requests an artifact or tracking update, and only to:

- `03_outputs/visit-briefs/`
- `03_outputs/family-messages/`
- `03_outputs/qa-summaries/`
- `04_tracking/*.csv`
- `log.md`

## Task 1: Add Skill Workflow Contract Tests

**Files:**

- Create: `tests/family_doctor/test_skill_workflow_contract_docs.py`

- [x] **Step 1: Create test helpers that read both skill docs**

Use exact paths:

```python
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
SKILL_DOCS = [
    ROOT / ".codex" / "skills" / "family-doctor" / "SKILL.md",
    ROOT / ".claude" / "skills" / "family-doctor.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
```

- [x] **Step 2: Add test for required workflows**

Add:

```python
def test_skill_docs_define_obsidian_first_workflows():
    required = [
        "ingest_report",
        "medical_visit_prep",
        "family_message",
        "daily_tracking_update",
        "health_question",
    ]

    for doc in SKILL_DOCS:
        content = _read(doc)
        assert "Obsidian-first workflows" in content
        for workflow in required:
            assert workflow in content, f"{doc}: {workflow}"
```

- [x] **Step 3: Add test for mapping to current low-level core**

Add:

```python
def test_skill_docs_map_workflows_to_existing_event_types():
    required = [
        "event_type: ingest",
        "event_type: query",
        "event_type: report",
        "payload.report_kind: checkup_update",
        "payload.report_kind: lab_update",
    ]

    for doc in SKILL_DOCS:
        content = _read(doc)
        for marker in required:
            assert marker in content, f"{doc}: {marker}"
```

- [x] **Step 4: Add test for write boundary**

Add:

```python
def test_skill_docs_lock_direct_write_boundaries():
    allowed = [
        "03_outputs/visit-briefs/",
        "03_outputs/family-messages/",
        "03_outputs/qa-summaries/",
        "04_tracking/*.csv",
        "log.md",
    ]
    forbidden = [
        "Do not directly write 01_raw/",
        "Do not directly write 02_wiki/sources/",
        "Do not directly write 02_wiki/members/",
        "Do not directly write 02_wiki/plans/",
        "Do not directly write 03_outputs/checkup-updates/",
        "Do not directly write 03_outputs/lab-updates/",
    ]

    for doc in SKILL_DOCS:
        content = _read(doc)
        for marker in allowed + forbidden:
            assert marker in content, f"{doc}: {marker}"
```

Final implementation also parses the `Allowed direct writes:` block and asserts it is exactly:

```python
[
    "03_outputs/visit-briefs/",
    "03_outputs/family-messages/",
    "03_outputs/qa-summaries/",
    "04_tracking/*.csv",
    "log.md",
]
```

This prevents future docs from adding extra direct-write targets while keeping the forbidden markers.

- [x] **Step 5: Add test for `health_question` evidence rules**

Add:

```python
def test_skill_docs_lock_health_question_evidence_rules():
    required = [
        "03_outputs/* is auxiliary context only",
        "must not be used as standalone evidence",
        "Key claims must cite",
        "source_ref",
        "02_wiki/sources/",
        "04_tracking",
        "source insufficient",
        "default read-only",
        "only save qa-summaries when the user explicitly asks",
        "separates facts, inferences, and verification items",
        "source conflict",
        "member uncertainty",
        "missing units or reference ranges",
        "urgent symptoms",
        "high-risk",
        "care-seeking guidance",
        "must not diagnose",
        "medication change request",
        "diagnosis request",
    ]

    for doc in SKILL_DOCS:
        content = _read(doc)
        section = _workflow_section(content, "health_question")
        for marker in required:
            assert marker in section, f"{doc}: {marker}"
```

- [x] **Step 6: Add test that Phase B docs do not claim unsupported routes**

Add:

```python
def test_skill_docs_do_not_claim_new_cli_routes():
    forbidden = [
        "event_type: visit_brief",
        "event_type: family_message",
        "event_type: daily_tracking_update",
        "visit_brief route",
        "family_message route",
        "daily_tracking_update route",
        "new CLI route",
        "new Python pipeline",
        "OCR/PDF/image parsing is supported",
        "trend_build",
    ]

    for doc in SKILL_DOCS:
        content = _read(doc)
        for marker in forbidden:
            assert marker not in content, f"{doc}: {marker}"
```

- [x] **Step 7: Add test for per-workflow operational contract**

Add:

```python
def test_skill_docs_lock_per_workflow_operational_contracts():
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

    for doc in SKILL_DOCS:
        content = _read(doc)
        for workflow, markers in workflow_markers.items():
            section = _workflow_section(content, workflow)
            for marker in markers:
                assert marker in section, f"{doc}: {workflow}: {marker}"
```

- [x] **Step 8: Add test that docs do not contain contradictory route claims**

Add:

```python
def test_skill_docs_do_not_contradict_route_boundaries():
    forbidden_phrases = [
        "medical_visit_prep route",
        "family_message route",
        "daily_tracking_update route",
        "health_question writes by default",
        "03_outputs/* can be used as evidence",
        "03_outputs/* may be standalone evidence",
    ]

    for doc in SKILL_DOCS:
        content = _read(doc)
        for phrase in forbidden_phrases:
            assert phrase not in content, f"{doc}: {phrase}"
```

- [x] **Step 9: Run the new tests and verify RED**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_skill_workflow_contract_docs.py -q
```

Expected: FAIL because current skill docs only list low-level event types.

- [x] **Step 10: Commit red tests**

Run:

```bash
git add tests/family_doctor/test_skill_workflow_contract_docs.py
git commit -m "test: define family doctor workflow skill contract"
```

## Task 2: Update Codex Skill Doc

**Files:**

- Modify: `.codex/skills/family-doctor/SKILL.md`

- [x] **Step 1: Rewrite the role summary**

Make the top of the doc say:

```markdown
# family-doctor

Use `family-doctor` as an Obsidian-first family health wiki maintainer. The vault is the product surface; Python routes are mechanical helpers.
```

- [x] **Step 2: Add `Obsidian-first workflows` section**

Include all five workflows in a summary table:

```markdown
## Obsidian-first workflows

Choose the user-intent workflow first, then map it to the current low-level core.

| Workflow | Use when | Current mapping |
| --- | --- | --- |
| `ingest_report` | New reports, labs, visit records, doctor notes | `event_type: ingest`; optional `event_type: report` with `payload.report_kind: checkup_update` or `payload.report_kind: lab_update` |
| `medical_visit_prep` | User wants a doctor-visit one-pager | `event_type: query`; if user explicitly asks for an artifact, host LLM may write `03_outputs/visit-briefs/` |
| `family_message` | User wants family-friendly wording | `event_type: query`; if user explicitly asks for an artifact, host LLM may write `03_outputs/family-messages/` |
| `daily_tracking_update` | User wants to update medication, diet, exercise, sleep, or checkup CSVs | No dedicated route; append-only rows should use `scripts/family_doctor/append_tracking_row.py`; corrections must not use the helper |
| `health_question` | User asks a question about the vault | `event_type: query`; default read-only |
```

The summary table is not enough for Task 1 tests. The doc must also contain independent Markdown headings for each workflow so tests can scope operational markers to the right workflow section. Do not add empty placeholder workflow headings here; Step 5 provides the real `### ingest_report`, `### medical_visit_prep`, `### family_message`, and `### daily_tracking_update` sections with their markers inside.

- [x] **Step 3: Add write-boundary section**

Include exact marker strings from Task 1:

```markdown
## Direct write boundaries

Only write directly when the user explicitly asks for an artifact or tracking update.

Allowed direct writes:
- `03_outputs/visit-briefs/`
- `03_outputs/family-messages/`
- `03_outputs/qa-summaries/`
- `04_tracking/*.csv`
- `log.md`

Forbidden direct writes:
- Do not directly write 01_raw/
- Do not directly write 02_wiki/sources/
- Do not directly write 02_wiki/members/
- Do not directly write 02_wiki/plans/
- Do not directly write 03_outputs/checkup-updates/
- Do not directly write 03_outputs/lab-updates/
```

- [x] **Step 4: Add health question evidence section**

Include:

```markdown
## `health_question` evidence rules

- default read-only
- `03_outputs/* is auxiliary context only`
- `03_outputs/* must not be used as standalone evidence`
- Key claims must cite `source_ref`, `02_wiki/sources/`, or `04_tracking` rows.
- If evidence is weak, say `source insufficient`.
- Only save qa-summaries when the user explicitly asks.
- Separates facts, inferences, and verification items.
- For high-risk or urgent symptoms, provide care-seeking guidance only; must not diagnose.
- Review triggers: source conflict, member uncertainty, missing units or reference ranges, urgent symptoms, medication change request, diagnosis request.
```

- [x] **Step 5: Add per-workflow operational contract sections**

Add a shared parent section plus independent workflow headings. Each marker must appear inside the section headed by that workflow name:

```markdown
## Workflow operational contracts

### ingest_report

- ingest_report writes via existing ingest pipeline.
- ingest_report tracking direct write only when explicitly requested and must include source_ref.
- ingest_report tracking direct write must preserve CSV headers.
- ingest_report appends log.md after direct tracking write.
- ingest_report review triggers: member uncertainty, abnormal values, medication dose, diagnosis, missing source.

### medical_visit_prep

- medical_visit_prep reads 02_wiki/members/, 02_wiki/sources/, 02_wiki/plans/, 04_tracking/.
- medical_visit_prep writes 03_outputs/visit-briefs/ only when explicitly requested.
- medical_visit_prep uses visit-brief-template.md.
- medical_visit_prep must not diagnose or replace clinician judgment.
- medical_visit_prep key claims need source or verification marker.
- medical_visit_prep appends log.md after artifact write.

### family_message

- family_message writes 03_outputs/family-messages/ only when explicitly requested.
- family_message uses family-message-template.md.
- family_message must not add new medical claims.
- family_message must not soften urgent risk.
- family_message writes uncertainty to 不确定项.
- family_message appends log.md after artifact write.

### daily_tracking_update

- daily_tracking_update preserves CSV headers.
- daily_tracking_update requires member_id, date, source_ref.
- daily_tracking_update must not silently overwrite existing rows.
- daily_tracking_update corrections require traceable explanation in notes.
- daily_tracking_update writes ambiguous values to notes or review.
- daily_tracking_update appends log.md after CSV write.
```

- [x] **Step 6: Preserve current low-level invocation details**

Keep existing command examples for:

```bash
python3 /absolute/path/to/AIHealth/scripts/family_doctor/run_skill.py --event /absolute/path/to/event.json
```

Keep the note that `ingest`, `report`, and `reminder` require `--target`, while `query` does not.

- [x] **Step 7: Preserve non-goals**

Keep or add:

- no new route
- no OCR/PDF/image parsing promise
- no Phase 3 trends
- no diagnosis, prescription, medication change advice

- [x] **Step 8: Run focused test and verify partial GREEN**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_skill_workflow_contract_docs.py -q
```

Expected: still FAIL because `.claude/skills/family-doctor.md` is not updated yet.

## Task 3: Update Claude Skill Doc

**Files:**

- Modify: `.claude/skills/family-doctor.md`

- [x] **Step 1: Mirror the workflow contract**

Add the same five workflow names and mappings as the Codex doc. The wording may be shorter, but the exact marker strings required by tests must appear.

- [x] **Step 2: Mirror direct write boundaries**

Add the same allowed and forbidden direct-write markers.

- [x] **Step 3: Mirror health question evidence rules**

Add the same evidence markers:

- `03_outputs/* is auxiliary context only`
- `must not be used as standalone evidence`
- `source_ref`
- `02_wiki/sources/`
- `04_tracking`
- `source insufficient`
- `default read-only`
- `only save qa-summaries when the user explicitly asks`
- `separates facts, inferences, and verification items`
- `source conflict`
- `member uncertainty`
- `missing units or reference ranges`
- `urgent symptoms`
- `high-risk`
- `care-seeking guidance`
- `must not diagnose`
- `medication change request`
- `diagnosis request`

- [x] **Step 4: Mirror per-workflow operational contracts**

Add the same independent Markdown headings and exact marker strings from Task 2 Step 5. The Claude-facing doc may be shorter around those sections, but each workflow's markers must remain inside that workflow's heading section.

- [x] **Step 5: Preserve existing invocation behavior**

Keep the current command syntax and current supported low-level event types.

- [x] **Step 6: Run focused test and verify GREEN**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_skill_workflow_contract_docs.py -q
```

Expected: PASS.

- [x] **Step 7: Commit skill docs**

Run:

```bash
git add .codex/skills/family-doctor/SKILL.md .claude/skills/family-doctor.md tests/family_doctor/test_skill_workflow_contract_docs.py
git commit -m "docs: add family doctor workflow skill contract"
```

## Task 4: Update Phase B Index and Verify

**Files:**

- Modify: `docs/superpowers/obsidian-first-llm-wiki/README.md`

- [x] **Step 1: Add Phase B implementation plan to the document index**

Add to `## 当前文档`:

```markdown
- [phase-b-workflow-contract-plan.md](./phase-b-workflow-contract-plan.md)：阶段 B 实施计划，聚焦 skill/prompt workflow contract 落地
```

- [x] **Step 2: Add Phase B implementation state**

Change the phase state section to include:

```markdown
- Phase A: complete
- Phase B: complete
```

- [x] **Step 3: Run full validation**

Run:

```bash
rm -f uv.lock
python3 scripts/family_doctor/validate_phase0.py --target ./family-health
rm -rf /tmp/family-health-phase-b-skill-contract
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-phase-b-skill-contract
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-phase-b-skill-contract
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q
rm -f uv.lock
```

Expected:

- Both validators pass.
- Full `tests/family_doctor` passes.
- No `uv.lock` remains.

- [x] **Step 4: Review diff scope**

Run:

```bash
git diff --stat
git diff -- .codex/skills/family-doctor/SKILL.md .claude/skills/family-doctor.md tests/family_doctor/test_skill_workflow_contract_docs.py docs/superpowers/obsidian-first-llm-wiki/README.md
```

Expected: diff only touches Phase B skill contract docs, tests, and README state.

- [x] **Step 5: Commit final docs**

Run:

```bash
git add docs/superpowers/obsidian-first-llm-wiki/README.md
git commit -m "docs: record phase b skill contract completion"
```

## Verification Summary

Phase B implementation is complete only when all of these pass:

```bash
python3 scripts/family_doctor/validate_phase0.py --target ./family-health
rm -rf /tmp/family-health-phase-b-skill-contract
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-phase-b-skill-contract
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-phase-b-skill-contract
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q
```

## Residual Risks After Phase B

- Workflows are documented for host agents, but Python still only knows `ingest`, `query`, `report`, and `reminder`.
- `medical_visit_prep` and `family_message` artifacts are host-LLM-maintained Markdown outputs, not deterministic Python products.
- CSV maintenance is still prompt-governed, not protected by a dedicated helper.
- Phase 3 trends remains out of scope until a separate Obsidian-first plan reintroduces it.
