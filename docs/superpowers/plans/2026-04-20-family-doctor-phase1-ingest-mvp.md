# Family Doctor Phase 1 Ingest MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working `health-ingest` pipeline so new inputs can be archived, turned into `sources/` pages, and minimally update the family-health wiki with traceable evidence and review items.

**Architecture:** Phase 1 stays deterministic and file-first. We do not introduce OCR or LLM providers yet. Instead, we accept the full Phase 0 `input_event` contract, create an `ingest_job` before any cross-layer writes, record planned and completed write sets as the job advances through staged phases, then archive raw inputs, classify the ingest event conservatively, write `sources/` pages, emit structured `output_result`, and perform tightly-scoped wiki updates or `review_item` creation when confidence is low or sources conflict. The CLI remains thin; reusable logic lives in a small Python package.

**Tech Stack:** Python 3 standard library, Markdown, JSON, pytest

---

## Planned File Map

**Create package modules**
- `family_doctor/__init__.py`
  - Package marker for reusable ingest logic.
- `family_doctor/ingest_models.py`
  - Dataclasses and typed helpers for ingest events, normalized attachments, and write results.
- `family_doctor/ingest_pipeline.py`
  - Main orchestration for ingest: validate input, dedupe, archive, classify, write source page, update wiki, write runtime records.
- `family_doctor/raw_archive.py`
  - Copies raw files into the right `01_raw/` destination and computes destination-relative references.
- `family_doctor/source_pages.py`
  - Renders `02_wiki/sources/*.md` pages from normalized ingest results.
- `family_doctor/wiki_updates.py`
  - Applies minimal updates to `members/`, `medications/`, `plans/`, and `trends/`.
- `family_doctor/runtime_records.py`
  - Writes `ingest_job`、`review_item` and `dedupe_record` JSON artifacts under `99_runtime/`.
- `family_doctor/conflict_detection.py`
  - Compares new ingest facts against existing wiki summaries and source history, producing `needs_review` decisions.
- `family_doctor/markdown_utils.py`
  - Small helpers for append/update patterns in Markdown files.

**Create scripts**
- `scripts/family_doctor/run_ingest.py`
  - CLI entrypoint: accepts an input event JSON file and a target vault, then runs ingest.

**Create test fixtures**
- `tests/family_doctor/fixtures/events/checkup-report.json`
- `tests/family_doctor/fixtures/events/lab-report.json`
- `tests/family_doctor/fixtures/events/medication-photo.json`
- `tests/family_doctor/fixtures/events/symptom-note.json`
- `tests/family_doctor/fixtures/files/`
  - Minimal local files referenced by fixture events.

**Create tests**
- `tests/family_doctor/test_run_ingest_cli.py`
  - CLI-level acceptance coverage.
- `tests/family_doctor/test_ingest_pipeline.py`
  - Pipeline behavior, dedupe, low-confidence blocking, review item creation.
- `tests/family_doctor/test_output_contract.py`
  - Pipeline-level `output_result` contract coverage for `ok` and `needs_review`.
- `tests/family_doctor/test_source_pages.py`
  - Source page rendering and evidence traceability.
- `tests/family_doctor/test_wiki_updates.py`
  - Minimal updates to member/medication/plan/trend pages.
- `tests/family_doctor/test_ingest_acceptance.py`
  - Fixed acceptance scenarios required by the spec for Phase 1.

**Modify existing files**
- `pyproject.toml`
  - Add package discovery guidance only if needed by test execution.
- `tests/family_doctor/conftest.py`
  - Add helpers for running the ingest CLI and bootstrapping temp vaults with fixture event files.
- `docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md`
  - Update current project status after Phase 1 is implemented.

---

### Task 1: Establish the Ingest Package Boundary and Red Tests

**Files:**
- Create: `family_doctor/__init__.py`
- Create: `family_doctor/ingest_models.py`
- Create: `tests/family_doctor/test_run_ingest_cli.py`
- Create: `tests/family_doctor/test_ingest_pipeline.py`
- Modify: `tests/family_doctor/conftest.py`

- [ ] **Step 1: Add reusable test helpers for ingest runs**

Update `tests/family_doctor/conftest.py` with a helper shaped like:

```python
INGEST = ROOT / "scripts" / "family_doctor" / "run_ingest.py"


@pytest.fixture
def run_ingest():
    def _run_ingest(event_path: Path, target: Path):
        return subprocess.run(
            [sys.executable, str(INGEST), "--event", str(event_path), "--target", str(target)],
            capture_output=True,
            text=True,
        )

    return _run_ingest
```

- [ ] **Step 2: Write the first failing CLI acceptance test**

Add to `tests/family_doctor/test_run_ingest_cli.py`:

```python
def test_run_ingest_archives_report_and_writes_source_page(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "checkup-report.json"
    assert run_bootstrap(target).returncode == 0

    result = run_ingest(event, target)

    assert result.returncode == 0
    assert (target / "02_wiki" / "sources").glob("*.md")
    assert "ingest completed" in result.stdout.lower()
```

- [ ] **Step 3: Write the failing low-confidence guardrail test**

Add to `tests/family_doctor/test_ingest_pipeline.py`:

```python
def test_run_ingest_blocks_low_confidence_member_resolution(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "symptom-note-low-confidence.json"
    assert run_bootstrap(target).returncode == 0

    result = run_ingest(event, target)

    assert result.returncode == 1
    assert "needs_review" in result.stderr.lower()
    assert "low-confidence member match" in result.stderr.lower()
    assert list((target / "99_runtime" / "state").glob("review_item_*.json"))
    job_files = list((target / "99_runtime" / "jobs").glob("ingest_job_*.json"))
    job = json.loads(job_files[0].read_text(encoding="utf-8"))
    assert job["status"] == "pending_review"
```

- [ ] **Step 4: Write the failing dedupe test**

```python
def test_run_ingest_is_idempotent_for_same_idempotency_key(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "medication-photo.json"
    assert run_bootstrap(target).returncode == 0

    first = run_ingest(event, target)
    second = run_ingest(event, target)

    assert first.returncode == 0
    assert second.returncode == 0
    assert "deduplicated" in second.stdout.lower()
```

- [ ] **Step 5: Write the failing same-day multi-report acceptance test**

Add to `tests/family_doctor/test_ingest_acceptance.py`:

```python
def test_same_day_distinct_reports_generate_distinct_source_ids(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    first_event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "lab-report.json"
    second_event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "lab-report-second.json"
    assert run_bootstrap(target).returncode == 0

    assert run_ingest(first_event, target).returncode == 0
    assert run_ingest(second_event, target).returncode == 0

    source_pages = sorted((target / "02_wiki" / "sources").glob("*.md"))
    assert len(source_pages) == 2
    assert source_pages[0].name != source_pages[1].name
```

- [ ] **Step 6: Run only the new ingest tests to verify they fail**

Run:

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest \
  tests/family_doctor/test_run_ingest_cli.py \
  tests/family_doctor/test_ingest_pipeline.py -v
```

Expected:

- FAIL because `run_ingest.py` and ingest package modules do not exist yet.

- [ ] **Step 7: Commit**

```bash
git add family_doctor tests/family_doctor
git commit -m "test: add phase1 ingest red tests"
```

---

### Task 2: Implement Event Loading, Dedupe, and Runtime Records

**Files:**
- Create: `family_doctor/ingest_models.py`
- Create: `family_doctor/runtime_records.py`
- Create: `family_doctor/ingest_pipeline.py`
- Test: `tests/family_doctor/test_ingest_pipeline.py`
- Test: `tests/family_doctor/test_output_contract.py`

- [ ] **Step 1: Add dataclasses for normalized ingest state**

In `family_doctor/ingest_models.py`, create small dataclasses such as:

```python
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
```

- [ ] **Step 2: Implement JSON loading and normalization**

In `family_doctor/ingest_pipeline.py`, add functions like:

```python
def load_event(path: Path) -> IngestEvent:
    raw = json.loads(path.read_text(encoding="utf-8"))
    # map to dataclass and validate expected Phase 0 contract fields
```

- [ ] **Step 3: Implement `ingest_job` persistence**

In `family_doctor/runtime_records.py`, add:

```python
def write_ingest_job(
    target: Path,
    event: IngestEvent,
    phase: str,
    status: str,
    planned_writes: list[str],
    completed_writes: list[str],
    source_id: str | None,
    recovery_hint: str | None,
) -> Path:
    ...
```

Write files under:

- `99_runtime/jobs/ingest_job_<event_id>.json`

Minimum fields:

- `entity_type`
- `event_id`
- `request_id`
- `idempotency_key`
- `correlation_id`
- `status`
- `phase`
- `planned_writes`
- `completed_writes`
- `recovery_hint`
- `member_id`
- `source_id`
- `created_at`

Runtime `status` values must follow the spec runtime model, not the output contract:

- `created`
- `processing`
- `pending_review`
- `committed`
- `failed`
- `aborted`

Required staged phases for Phase 1:

- `accepted`
- `archived_raw`
- `wrote_source`
- `updated_wiki`
- `committed`

Rule:

- no cross-layer write may happen before the first job record exists
- only `status=committed` + `phase=committed` counts as ingest success
- interrupted ingest must leave a recoverable job state on disk
- low-confidence member matching and conflict paths should set runtime `status=pending_review`

- [ ] **Step 4: Implement `review_item` persistence**

Add:

```python
def write_review_item(target: Path, event: IngestEvent, reason: str, severity: str) -> Path:
    ...
```

Write files under:

- `99_runtime/state/review_item_<event_id>.json`

- [ ] **Step 5: Implement `dedupe_record` persistence**

Add:

```python
def write_dedupe_record(
    target: Path,
    event: IngestEvent,
    fingerprint: str,
    matched_job_id: str,
) -> Path:
    ...
```

Write files under:

- `99_runtime/state/dedupe_record_<event_id>.json`

Minimum fields:

- `entity_type`
- `event_id`
- `idempotency_key`
- `fingerprint`
- `matched_job_id`
- `created_at`

- [ ] **Step 6: Implement idempotency check**

Add a function that:

- derives a conservative dedupe fingerprint from `idempotency_key`, `event_type`, `member_id`, and attachment `content_sha256` when present
- checks both existing `ingest_job` and `dedupe_record`
- returns a deduplicated result instead of writing duplicate artifacts
- persists a `dedupe_record` whenever a duplicate is recognized

- [ ] **Step 7: Implement structured `output_result`**

The ingest pipeline should return a dict shaped to the spec, including at least:

```python
{
    "status": "ok" | "needs_review" | "error",
    "route": "ingest",
    "summary": "...",
    "user_facing_message": "...",
    "artifacts": [...],
    "wiki_updates": [...],
    "runtime_updates": [...],
    "evidence_refs": [...],
    "followup_suggestions": [...],
}
```

Clarification:

- `output_result.status` uses spec result values: `ok | needs_review | error`
- `ingest_job.status` uses runtime values: `created | processing | pending_review | committed | failed | aborted`

The CLI can print a compact summary to stdout/stderr, but the pipeline itself must keep the structured result contract.

- [ ] **Step 8: Add pipeline-level contract tests**

In `tests/family_doctor/test_output_contract.py`, add:

```python
def test_ingest_pipeline_returns_ok_output_contract(...):
    result = run_ingest_pipeline(...)
    assert result["status"] == "ok"
    assert result["route"] == "ingest"
    assert isinstance(result["artifacts"], list)
    assert isinstance(result["wiki_updates"], list)
    assert isinstance(result["runtime_updates"], list)
    assert isinstance(result["evidence_refs"], list)


def test_ingest_pipeline_returns_needs_review_output_contract(...):
    result = run_ingest_pipeline(...)
    assert result["status"] == "needs_review"
    assert result["route"] == "ingest"
    assert "user_facing_message" in result
    assert isinstance(result["runtime_updates"], list)
```

- [ ] **Step 9: Run targeted tests**

Run:

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest \
  tests/family_doctor/test_ingest_pipeline.py \
  tests/family_doctor/test_output_contract.py -v
```

Expected:

- Dedupe and low-confidence tests PASS.

- [ ] **Step 10: Commit**

```bash
git add family_doctor tests/family_doctor
git commit -m "feat: add ingest runtime records and dedupe"
```

---

### Task 3: Archive Raw Inputs and Generate `sources/` Pages

**Files:**
- Create: `family_doctor/raw_archive.py`
- Create: `family_doctor/source_pages.py`
- Modify: `family_doctor/ingest_pipeline.py`
- Create: `tests/family_doctor/test_source_pages.py`
- Test: `tests/family_doctor/test_run_ingest_cli.py`

- [ ] **Step 1: Write the failing source-page traceability test**

In `tests/family_doctor/test_source_pages.py`:

```python
def test_source_page_includes_raw_reference_and_fact_sections(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "lab-report.json"
    assert run_bootstrap(target).returncode == 0

    assert run_ingest(event, target).returncode == 0

    source_pages = list((target / "02_wiki" / "sources").glob("*.md"))
    content = source_pages[0].read_text(encoding="utf-8")
    assert "## 来源信息" in content
    assert "## 提取出的结构化事实" in content
    assert "01_raw/" in content
```

- [ ] **Step 2: Implement raw archive helpers**

In `family_doctor/raw_archive.py`, add:

```python
def archive_attachment(target: Path, event: IngestEvent, attachment: NormalizedAttachment) -> Path:
    ...
```

Routing rules for Phase 1:

- report-like events -> `01_raw/reports/`
- lab-like events -> `01_raw/labs/`
- medication / prescription -> `01_raw/medications/`
- symptom-only text -> no file copy, but still produce source page

- [ ] **Step 3: Implement conservative event classification**

In `family_doctor/ingest_pipeline.py`, add simple deterministic classification based on:

- `payload.text`
- attachment `kind`
- attachment filename / `source_name`

Phase 1 only needs categories:

- `checkup_report`
- `lab_result`
- `medication_record`
- `symptom_note`

- [ ] **Step 4: Render source pages**

In `family_doctor/source_pages.py`, add:

```python
def render_source_page(... ) -> str:
    return f\"\"\"---
type: source
...
## 来源信息
...
## 提取出的结构化事实
...
## 待核实项
\"\"\"
```

Rule:

- If Phase 1 cannot confidently extract structured facts from an attachment, write an explicit placeholder plus a `review_item`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest \
  tests/family_doctor/test_source_pages.py \
  tests/family_doctor/test_run_ingest_cli.py -v
```

Expected:

- Source page generation and raw archive tests PASS.

- [ ] **Step 6: Commit**

```bash
git add family_doctor tests/family_doctor
git commit -m "feat: archive ingest raw inputs and render source pages"
```

---

### Task 4: Add Minimal Wiki Updates for Members, Medications, Plans, and Trends

**Files:**
- Create: `family_doctor/markdown_utils.py`
- Create: `family_doctor/wiki_updates.py`
- Modify: `family_doctor/ingest_pipeline.py`
- Create: `tests/family_doctor/test_wiki_updates.py`

- [ ] **Step 1: Write the failing member update test**

```python
def test_symptom_ingest_updates_member_page_and_plan(
    run_bootstrap, run_ingest, tmp_path
):
    target = tmp_path / "family-health"
    event = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "symptom-note.json"
    assert run_bootstrap(target).returncode == 0

    assert run_ingest(event, target).returncode == 0

    member_page = target / "02_wiki" / "members" / "dad.md"
    plan_page = target / "02_wiki" / "plans" / "dad-followup-plan.md"
    assert member_page.exists()
    assert plan_page.exists()
```

- [ ] **Step 2: Write the failing medication update test**

```python
def test_medication_ingest_creates_medication_page_and_member_summary(
    run_bootstrap, run_ingest, tmp_path
):
    ...
    medication_page = target / "02_wiki" / "medications" / "atorvastatin.md"
    assert medication_page.exists()
```

- [ ] **Step 3: Implement page upsert helpers**

In `family_doctor/markdown_utils.py`, add helpers for:

- create-if-missing from template-like skeleton
- append one-line bullet without duplicating identical content
- inject source references into a stable section

- [ ] **Step 4: Implement conservative wiki updates**

In `family_doctor/wiki_updates.py`, handle:

- `members/`
  - create member page if missing
  - append source link to `最近资料`
  - append `待核实项` if extraction was incomplete
- `medications/`
  - create medication page only for medication-record events with sufficiently specific text
- `plans/`
  - append observation or follow-up bullets for symptom / report events
- `trends/`
  - for Phase 1, only create a stub trend page when lab or report text includes a clearly named metric in text

Do **not** attempt broad diagnosis or uncontrolled inference.

- [ ] **Step 5: Add conflict detection and `needs_review` behavior**

In `family_doctor/conflict_detection.py`, implement minimal Phase 1 conflict rules:

- if a new medication ingest disagrees with an existing current-medication summary for the same member, create `review_item`
- if a new symptom or report event clearly contradicts an existing “current status” bullet for the same member, create `review_item`
- conflicting source ingest should return `status="needs_review"` instead of `ok`

Add a failing acceptance test to `tests/family_doctor/test_ingest_acceptance.py`:

```python
def test_conflicting_source_creates_review_item_and_returns_needs_review(...):
    ...
    assert result.returncode == 1
    assert "needs_review" in result.stderr.lower()
    assert list((target / "99_runtime" / "state").glob("review_item_*.json"))
```

- [ ] **Step 6: Add recoverable failure-path testing**

Add a failing test to `tests/family_doctor/test_ingest_pipeline.py` that injects a write failure after raw archive but before wiki commit:

```python
def test_ingest_failure_leaves_recoverable_job_state(...):
    result = run_ingest_pipeline(..., fail_after_phase="archived_raw")
    assert result["status"] == "error"
    job_files = list((target / "99_runtime" / "jobs").glob("ingest_job_*.json"))
    job = json.loads(job_files[0].read_text(encoding="utf-8"))
    assert job["phase"] == "archived_raw"
    assert job["status"] == "failed"
    assert job["recovery_hint"]
```

Implementation note:

- use a narrow test-only injection point such as an optional `fail_after_phase` argument on the pipeline function
- do not expose this fault-injection knob in the CLI

- [ ] **Step 7: Write `log.md` entries**

Append entries like:

```text
## [2026-04-20 16:30] ingest | dad | source | source_evt_2026_04_20_0001
```

- [ ] **Step 8: Run targeted tests**

Run:

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest \
  tests/family_doctor/test_wiki_updates.py -v
```

Expected:

- Minimal wiki update tests PASS.

- [ ] **Step 9: Commit**

```bash
git add family_doctor tests/family_doctor family-health/log.md
git commit -m "feat: add minimal wiki updates for ingest"
```

---

### Task 5: Add the CLI, End-to-End Acceptance Coverage, and Phase 1 Handoff Notes

**Files:**
- Create: `scripts/family_doctor/run_ingest.py`
- Modify: `family_doctor/ingest_pipeline.py`
- Modify: `tests/family_doctor/test_run_ingest_cli.py`
- Modify: `docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md`

- [ ] **Step 1: Implement the CLI wrapper**

`scripts/family_doctor/run_ingest.py` should support:

```bash
python3 scripts/family_doctor/run_ingest.py --event <event.json> --target <vault>
```

On success:

- exit `0`
- print a short summary beginning with `Ingest completed:`
- optionally print the JSON path of the saved `output_result` if persisted

On `needs_review` / `error` cases:

- exit `1`
- print a short actionable message to `stderr`
- preserve the underlying structured `output_result` and runtime artifacts on disk

- [ ] **Step 2: Add end-to-end acceptance tests**

In `tests/family_doctor/test_run_ingest_cli.py`, cover:

- bootstrapped vault + report event
- medication record event
- symptom note event
- duplicate ingest event
- low-confidence blocked event
- same-day distinct reports
- conflicting source -> `needs_review`
- recoverable failure-path leaves resumable job state

- [ ] **Step 3: Run full test suite**

Run:

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest tests/family_doctor -q
```

Expected:

- All Phase 0 and Phase 1 tests PASS.

- [ ] **Step 4: Update handoff notes**

In `docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md`, update:

- current stage
- new CLI entrypoint
- new validation / acceptance commands
- next recommended phase

- [ ] **Step 5: Commit**

```bash
git add family_doctor scripts/family_doctor tests/family_doctor docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md
git commit -m "feat: complete phase1 ingest mvp"
```

---

## Verification Checklist

Before declaring Phase 1 done, run all of these:

```bash
python3 scripts/family_doctor/validate_phase0.py --target /Users/loutussun/Documents/codex/AIHealth/family-health
PYTHONPATH=/tmp/codex_pytest python3 -m pytest tests/family_doctor -q
python3 scripts/family_doctor/run_ingest.py --event tests/family_doctor/fixtures/events/checkup-report.json --target /tmp/family-health-phase1-demo
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-phase1-demo
```

Expected outcome:

- Phase 0 scaffold still validates
- Full test suite passes
- Ingest demo writes raw artifacts, a `sources/` page, staged runtime records, structured `output_result`, and minimal wiki updates

Required Phase 1 acceptance coverage:

- duplicate ingest
- same-day distinct reports
- low-confidence member block -> `needs_review` + `review_item`
- conflicting source -> `needs_review` + `review_item`
- recoverable failure preserves staged job state

---

## Scope Guardrails

Do **not** add any of the following in Phase 1:

- OCR
- LLM extraction
- IM integrations
- scheduler integrations
- query / report / reminder business logic
- complex trend analytics
- diagnosis-like inference

Phase 1 succeeds if ingest is:

- repeatable
- traceable
- conservative
- recoverable
