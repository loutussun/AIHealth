# Family Doctor Phase 3 Trends / Writeback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first stable `trends / writeback` layer so `family-doctor` can turn scattered source data into member-topic trend pages, then conservatively promote only safe long-term conclusions into `members/` and `plans/`.

**Architecture:** Phase 3 keeps the system file-first and deterministic. We add a dedicated `trend_pipeline` that reads existing wiki and report artifacts, writes canonical `02_wiki/trends/*.md` pages, and records only light runtime state. A separate `writeback_gate` decides whether trend conclusions are safe to promote into `members/` or `plans/`; `query` and `report` are updated only after the trend layer is stable.

**Tech Stack:** Python 3 standard library, Markdown, JSON, pytest

---

## Planned File Map

**Create package modules**
- `family_doctor/trend_context.py`
  - Collect member-topic evidence from `members/`, `plans/`, `sources/`, and `03_outputs/`.
- `family_doctor/trend_pages.py`
  - Render deterministic `02_wiki/trends/*.md` pages with the fixed Phase 3 section contract.
- `family_doctor/trend_pipeline.py`
  - Load trend events, build trend pages, run the inline controlled writeback subphase, and emit `output_result`.
- `family_doctor/writeback_gate.py`
  - Evaluate candidate conclusions against the conservative five-rule gate and classify `member_summary`, `plan_action`, or `rejected`.

**Modify existing package modules**
- `family_doctor/query_context.py`
  - Add `trends` retrieval items into the query read model with member/topic filtering.
- `family_doctor/query_pipeline.py`
  - Prefer `trends` content over re-synthesizing from `sources` when trend pages exist.
- `family_doctor/report_pipeline.py`
  - Prefer `trends` content when generating report text and evidence refs.
- `family_doctor/runtime_records.py`
  - Add `trend_build_job` persistence helpers only if needed by pipeline tests.
- `family_doctor/wiki_updates.py`
  - Reuse the existing wiki mutation boundary for writing gated summaries to `members/` and actions to `plans/`; do not create a new writeback-specific mutation layer.
- `family_doctor/markdown_utils.py`
  - Add any minimal helper needed for stable trend-page updates; avoid broad refactors.

**Create scripts**
- `scripts/family_doctor/run_trend_build.py`
  - Thin CLI wrapper for the trend pipeline.

**Create fixtures**
- `tests/family_doctor/fixtures/events/trend-build-blood-pressure.json`
- `tests/family_doctor/fixtures/events/trend-build-weight.json`
- `tests/family_doctor/fixtures/events/trend-build-lipids.json`
- `tests/family_doctor/fixtures/events/trend-build-sleep.json`
- `tests/family_doctor/fixtures/events/trend-build-glucose.json`
  - Minimal deterministic events that point at a member and a topic.

**Create tests**
- `tests/family_doctor/test_trend_pages.py`
  - Trend page contract and section ordering.
- `tests/family_doctor/test_trend_pipeline.py`
  - Trend event loading, context building, page generation, and runtime output contract.
- `tests/family_doctor/test_writeback_gate.py`
  - Conservative gate behavior for accepted and rejected conclusions.
- `tests/family_doctor/test_trend_query_integration.py`
  - Query prefers `trends` when available and falls back safely when not.
- `tests/family_doctor/test_trend_report_integration.py`
  - Report prefers `trends` and keeps evidence traceability.
- `tests/family_doctor/test_run_trend_build_cli.py`
  - CLI behavior for success and contract failures.

**Modify shared test helpers**
- `tests/family_doctor/conftest.py`
  - Extend query event materialization so tests can inject `retrieval["trends"]` entries and explicit `member_id`; this keeps Phase 3 aligned with the current event-driven query contract.

**Modify existing docs**
- `README.md`
  - Update current project state after Phase 3 ships.
- `docs/superpowers/handoffs/...`
  - Add Phase 3 completion handoff and latest project snapshot.

---

## Shared Contracts To Freeze First

### 1. Trend Build Event Contract

`trend build` v1 minimum input should be frozen as:

- `event_type = "trend_build"`
- `target.member_id`
- `payload.topic`
- optional `payload.window_primary`
- optional `payload.window_secondary`
- optional `runtime.related_runtime_id`

Recommended fixture set:

- `tests/family_doctor/fixtures/events/trend-build-blood-pressure.json`
- `tests/family_doctor/fixtures/events/trend-build-weight.json`
- `tests/family_doctor/fixtures/events/trend-build-lipids.json`
- `tests/family_doctor/fixtures/events/trend-build-sleep.json`
- `tests/family_doctor/fixtures/events/trend-build-glucose.json`

### 2. Trend Page Contract

Every generated trend page must preserve:

- frontmatter:
  - `type: trend`
  - `trend_id`
  - `member_id`
  - `topic`
  - `window_primary`
  - `window_secondary`
  - `tags`
- headings in this exact order:
  - `## 覆盖时间范围`
  - `## 关键观测点`
  - `## 趋势判断`
  - `## 短期波动`
  - `## 可能相关因素`
  - `## 关联资料`
  - `## 可提炼结论`
  - `## 待核实项`

### 3. Writeback Gate Contract

Each candidate conclusion must be classified as one of:

- `member_summary`
- `plan_action`
- `rejected`

Acceptance requires all of:

- `long_term = true`
- `has_evidence = true`
- `conflict_free = true`
- `semantically_stable = true`
- `medical_boundary_safe = true`

Rejected results must preserve a human-readable `reason`.

### 4. Topic Identity Contract

Phase 3 must freeze one canonical topic mapping and reuse it everywhere:

| canonical topic id | file slug | display label |
| --- | --- | --- |
| `blood_pressure` | `blood-pressure` | `血压` |
| `lipids` | `lipids` | `血脂` |
| `glucose` | `glucose` | `血糖` |
| `sleep` | `sleep` | `睡眠` |
| `weight` | `weight` | `体重` |

Rules:

- events use `payload.topic = canonical topic id`
- trend frontmatter uses `topic = canonical topic id`
- `trend_id = f"{member_id}_{canonical_topic_id}"`
- filenames use `<safe_slug(member_id)>-<file slug>.md`
- query `retrieval["trends"]` uses `topic = canonical topic id`
- trend page `#` heading uses `<display_name>：<display label>趋势`
- query/report matching joins on `(member_id, canonical topic id)` only; do not join on filename or freeform heading text
- report matching must resolve trend pages through the same mapping, not ad-hoc string conversion

Add one helper module-level constant or function to own this mapping; do not duplicate conversions across `trend_pages.py`, `trend_pipeline.py`, `query_context.py`, and `report_pipeline.py`.

### 5. Controlled Writeback Execution Boundary

Phase 3 freezes one implementation mode:

- `controlled writeback` is **not** a separate public event or CLI in this phase
- `run_trend_pipeline(...)` owns three sequential internal phases:
  1. build/update the trend page
  2. evaluate candidate conclusions through `writeback_gate`
  3. apply accepted writes to `members/` / `plans/`

Runtime/result contract:

- `result["route"] == "trend_build"`
- `result["wiki_updates"]` always includes the trend page update
- accepted writeback targets appear as additional `wiki_updates`
- rejected candidates never mutate `members/` or `plans/`

### 6. Writeback Candidate Contract

`writeback_gate` must consume a normalized candidate model, not loose booleans spread across the pipeline.

Suggested minimal model:

```python
@dataclass(frozen=True)
class WritebackCandidate:
    candidate_id: str
    candidate_kind: str  # member_summary | plan_action
    text: str
    member_id: str
    topic: str
    source_trend_id: str
    evidence_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    target_page_type: str  # member | plan
    target_heading: str
    updated_at: str
    generated_from_section: str  # trend_judgments | promotable_conclusions
    long_term: bool
    semantically_stable: bool
    medical_boundary_safe: bool
```

Derivation rules:

- `trend_pipeline` owns candidate creation
- candidates are produced only from:
  - `## 趋势判断`
  - `## 可提炼结论`
- candidates are never produced from:
  - `## 短期波动`
  - `## 可能相关因素`
  - `## 待核实项`
- `has_evidence` is derived as `bool(evidence_refs)`
- `conflict_free` is derived as `not conflict_refs`
- `target_page_type` / `target_heading` are assigned by pipeline before the gate runs
- `long_term` is true only when:
  - `generated_from_section` is `trend_judgments` or `promotable_conclusions`
  - and the event uses `window_primary == "12_months"`
- `semantically_stable` is false when the text contains obviously time-local phrasing such as:
  - `本次`
  - `今天`
  - `最近一次`
  - `单次`
- `medical_boundary_safe` is false when the text contains medication or diagnosis directive wording such as:
  - `停药`
  - `换药`
  - `加药`
  - `确诊`
  - `诊断为`
- `reason` must be a stable machine-friendly token, for example:
  - `missing_evidence`
  - `conflict_detected`
  - `not_long_term`
  - `not_semantically_stable`
  - `medical_boundary`

### 7. Destination Page Writeback Contract

Phase 3 must write only into existing headings already created by the scaffold and Phase 1 helpers:

- member page:
  - `## 最近关键指标` for `candidate_kind = member_summary`
- plan page:
  - `## 行动步骤` for `candidate_kind = plan_action`

Fallback rules:

- if the heading exists, append idempotently under that heading
- if the heading is missing, create it using the same `append_lines_under_heading(...)` helper
- repeated accepted writebacks de-duplicate by exact normalized line text; reruns must be no-op
- rejected candidates stay only in the trend page under `## 待核实项`
- every written line must preserve both evidence and update time in the line itself, for example:

```text
- 过去 12 个月血脂总体较前期改善。（来源：source:evt_lab_001, source:evt_lab_002；更新：2026-04-22）
```

### 8. Query Trend Retrieval Contract

Phase 3 must preserve the current query shape: `run_query_pipeline(event_path)` remains event-driven. Trend-aware query retrieval must support two sources, in this order:

1. discover real trend pages from `context.vault_root` when provided
2. fall back to `retrieval["trends"]` when tests or callers inject the bucket directly

Query events therefore gain one optional but preferred field:

- `context.vault_root`

Each trend retrieval item should preserve:

- `trend_id`
- `member_id`
- `topic`
- `page_path`
- `sections`
  - at least `trend_judgments`
  - optional `short_term_fluctuations`
  - optional `promotable_conclusions`

`query_context.py` owns discovery from disk and normalization into the same retrieval shape. Test helpers may inject `retrieval["trends"]`, but at least one integration test must prove that a real file under `02_wiki/trends/` is discoverable through `context.vault_root`.

---

### Task 1: Freeze the Trend Page Contract with RED Tests

**Files:**
- Create: `family_doctor/trend_pages.py`
- Create: `tests/family_doctor/test_trend_pages.py`

- [ ] **Step 1: Write the failing trend page contract test**

Add a test like:

```python
def test_build_trend_page_markdown_preserves_phase3_section_order():
    markdown = build_trend_page_markdown(
        member_id="dad",
        display_name="爸爸",
        topic="weight",
        summary="过去 12 个月体重整体小幅上升，最近 4 周相对稳定。",
        coverage_window=["2025-04-01 ~ 2026-04-01"],
        key_points=["2025-04-01: 68kg", "2026-04-01: 71kg"],
        trend_judgments=["过去 12 个月整体上升。"],
        short_term_fluctuations=["最近 4 周无明显波动。"],
        possible_factors=["节假日饮食变化可能相关。"],
        related_refs=["source:evt_weight_001"],
        promotable_conclusions=["过去 3 个月体重总体平稳。"],
        open_questions=["部分记录缺少测量时间。"],
    )

    assert "type: trend" in markdown
    assert "trend_id: dad_weight" in markdown
    assert markdown.index("## 覆盖时间范围") < markdown.index("## 关键观测点")
    assert markdown.index("## 关键观测点") < markdown.index("## 趋势判断")
    assert markdown.index("## 趋势判断") < markdown.index("## 短期波动")
    assert markdown.index("## 短期波动") < markdown.index("## 可能相关因素")
    assert markdown.index("## 可能相关因素") < markdown.index("## 关联资料")
    assert markdown.index("## 关联资料") < markdown.index("## 可提炼结论")
    assert markdown.index("## 可提炼结论") < markdown.index("## 待核实项")
```

- [ ] **Step 2: Add the failing path-safety test for trend page filenames**

```python
def test_build_trend_page_path_sanitizes_member_and_topic(tmp_path):
    path = trend_page_path(tmp_path, member_id="../dad", topic="../blood pressure")

    assert path.parent == tmp_path
    assert path.name == "dad-blood-pressure.md"
```

- [ ] **Step 3: Run only the trend page tests to verify RED**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_trend_pages.py -q
```

Expected:

- FAIL because `trend_pages.py` functions do not exist yet.

- [ ] **Step 4: Implement the minimal trend page renderer**

Create `family_doctor/trend_pages.py` with functions shaped like:

```python
def build_trend_page_markdown(... ) -> str:
    ...


def trend_page_path(trends_root: Path, member_id: str, topic: str) -> Path:
    ...
```

- [ ] **Step 5: Re-run the trend page tests to verify GREEN**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_trend_pages.py -q
```

Expected:

- PASS

- [ ] **Step 6: Commit**

```bash
git add family_doctor/trend_pages.py tests/family_doctor/test_trend_pages.py
git commit -m "feat: add phase3 trend page contract"
```

---

### Task 2: Build the Trend Event Contract and Pipeline MVP

**Files:**
- Create: `family_doctor/trend_context.py`
- Create: `family_doctor/trend_pipeline.py`
- Create: `tests/family_doctor/test_trend_pipeline.py`
- Create: `tests/family_doctor/fixtures/events/trend-build-blood-pressure.json`
- Create: `tests/family_doctor/fixtures/events/trend-build-weight.json`
- Create: `tests/family_doctor/fixtures/events/trend-build-lipids.json`
- Create: `tests/family_doctor/fixtures/events/trend-build-sleep.json`
- Create: `tests/family_doctor/fixtures/events/trend-build-glucose.json`

- [ ] **Step 1: Write the failing event contract test**

```python
def test_load_trend_build_event_accepts_member_topic_contract(event_path):
    event = load_trend_build_event(event_path)

    assert event.event_type == "trend_build"
    assert event.member_id == "dad"
    assert event.topic == "blood_pressure"
    assert event.window_primary == "12_months"
    assert event.window_secondary == ("4_weeks", "3_months")
```

- [ ] **Step 2: Write the failing pipeline generation test**

```python
def test_trend_pipeline_writes_member_topic_trend_page(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    event_path = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "trend-build-blood-pressure.json"

    result = run_trend_pipeline(event_path, target)

    trend_page = target / "02_wiki" / "trends" / "dad-blood-pressure.md"
    assert result["status"] == "ok"
    assert trend_page.exists()
    assert "## 趋势判断" in trend_page.read_text(encoding="utf-8")
```

- [ ] **Step 3: Write the failing “no evidence, no fake trend” test**

```python
def test_trend_pipeline_keeps_empty_topic_conservative(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    event_path = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "trend-build-glucose.json"

    result = run_trend_pipeline(event_path, target)

    trend_page = target / "02_wiki" / "trends" / "dad-glucose.md"
    content = trend_page.read_text(encoding="utf-8")
    assert "暂无足够资料形成长期趋势判断" in content
    assert result["wiki_updates"]
```

- [ ] **Step 4: Run the new trend pipeline tests to verify RED**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_trend_pipeline.py -q
```

Expected:

- FAIL because the event loader and pipeline do not exist yet.

- [ ] **Step 5: Implement minimal event loading and context assembly**

In `family_doctor/trend_pipeline.py`, add:

```python
@dataclass(frozen=True)
class TrendBuildEvent:
    event_id: str
    event_type: str
    member_id: str
    topic: str
    window_primary: str
    window_secondary: tuple[str, ...]
    runtime_related_id: str | None
```

In `family_doctor/trend_context.py`, add a small collector shaped like:

```python
def build_trend_context(target: Path, *, member_id: str, topic: str) -> dict[str, object]:
    return {
        "member_page": ...,
        "plan_pages": ...,
        "source_pages": ...,
        "output_pages": ...,
    }
```

- [ ] **Step 6: Re-run the trend pipeline tests to verify GREEN**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_trend_pipeline.py tests/family_doctor/test_trend_pages.py -q
```

Expected:

- PASS

- [ ] **Step 7: Commit**

```bash
git add family_doctor/trend_context.py family_doctor/trend_pipeline.py family_doctor/trend_pages.py tests/family_doctor
git commit -m "feat: add phase3 trend pipeline"
```

---

### Task 3: Implement the Conservative Writeback Gate

**Files:**
- Create: `family_doctor/writeback_gate.py`
- Create: `tests/family_doctor/test_writeback_gate.py`

- [ ] **Step 1: Write the failing acceptance test for a promotable member summary**

```python
def test_writeback_gate_accepts_stable_lipid_summary():
    decision = evaluate_writeback_candidate(
        candidate_text="过去 12 个月血脂总体较前期改善。",
        evidence_refs=["source:evt_lab_001", "source:evt_lab_002"],
        long_term=True,
        conflict_free=True,
        semantically_stable=True,
        medical_boundary_safe=True,
        candidate_kind="member_summary",
    )

    assert decision.classification == "member_summary"
    assert decision.accepted is True
```

- [ ] **Step 2: Write the failing rejection tests**

```python
def test_writeback_gate_rejects_single_point_fluctuation():
    decision = evaluate_writeback_candidate(
        candidate_text="这次体重偏高，可判断为持续增重。",
        evidence_refs=["source:evt_weight_001"],
        long_term=False,
        conflict_free=True,
        semantically_stable=False,
        medical_boundary_safe=True,
        candidate_kind="member_summary",
    )

    assert decision.classification == "rejected"
    assert "long_term" in decision.reason
```

```python
def test_writeback_gate_rejects_medication_adjustment_language():
    decision = evaluate_writeback_candidate(
        candidate_text="建议停掉当前降压药。",
        evidence_refs=["source:evt_bp_001"],
        long_term=True,
        conflict_free=True,
        semantically_stable=True,
        medical_boundary_safe=False,
        candidate_kind="plan_action",
    )

    assert decision.classification == "rejected"
    assert "medical_boundary" in decision.reason
```

- [ ] **Step 2.5: Write the failing candidate-production contract test**

```python
def test_extract_writeback_candidates_preserves_gate_inputs_from_trend_page():
    trend_markdown = build_trend_page_markdown(
        member_id="dad",
        display_name="爸爸",
        topic="lipids",
        summary="过去 12 个月血脂总体较前期改善。",
        coverage_window=["2025-04-01 ~ 2026-04-01"],
        key_points=["LDL: 3.6 -> 2.4"],
        trend_judgments=["过去 12 个月血脂总体较前期改善。"],
        short_term_fluctuations=["最近 4 周波动不大。"],
        possible_factors=[],
        related_refs=["source:evt_lab_001", "source:evt_lab_002"],
        promotable_conclusions=["建议下次复查前整理近三次血脂结果。"],
        open_questions=[],
    )

    candidates = extract_writeback_candidates(
        trend_markdown=trend_markdown,
        member_id="dad",
        topic="lipids",
        trend_id="dad_lipids",
        window_primary="12_months",
        updated_at="2026-04-22",
        conflict_refs=(),
    )

    assert [candidate.generated_from_section for candidate in candidates] == [
        "trend_judgments",
        "promotable_conclusions",
    ]
    assert all(candidate.long_term is True for candidate in candidates)
    assert all(candidate.target_heading in {"## 最近关键指标", "## 行动步骤"} for candidate in candidates)
```

- [ ] **Step 3: Run the gate tests to verify RED**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_writeback_gate.py -q
```

Expected:

- FAIL because `writeback_gate.py` does not exist yet.

- [ ] **Step 4: Implement the minimal gate**

Create a small dataclass, extractor, and evaluator:

```python
@dataclass(frozen=True)
class WritebackDecision:
    accepted: bool
    classification: str
    reason: str | None


def evaluate_writeback_candidate(... ) -> WritebackDecision:
    ...


def extract_writeback_candidates(... ) -> list[WritebackCandidate]:
    ...
```

- [ ] **Step 5: Re-run the gate tests to verify GREEN**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_writeback_gate.py -q
```

Expected:

- PASS

- [ ] **Step 6: Commit**

```bash
git add family_doctor/writeback_gate.py tests/family_doctor/test_writeback_gate.py
git commit -m "feat: add phase3 writeback gate"
```

---

### Task 4: Connect Controlled Writeback into Members and Plans

**Files:**
- Modify: `family_doctor/trend_pipeline.py`
- Modify: `family_doctor/wiki_updates.py`
- Modify: `family_doctor/markdown_utils.py`
- Test: `tests/family_doctor/test_trend_pipeline.py`

- [ ] **Step 1: Write the failing member-summary writeback integration test**

```python
def test_trend_pipeline_writes_promoted_summary_to_member_page(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    event_path = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "trend-build-lipids.json"

    result = run_trend_pipeline(event_path, target)

    member_page = target / "02_wiki" / "members" / "dad.md"
    content = member_page.read_text(encoding="utf-8")
    assert "过去 12 个月血脂总体较前期改善" in content
    assert any(update["page_type"] == "member_page" for update in result["wiki_updates"])
```

- [ ] **Step 2: Write the failing plan-action writeback integration test**

```python
def test_trend_pipeline_writes_promoted_action_to_plan_page(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    event_path = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "trend-build-sleep.json"

    result = run_trend_pipeline(event_path, target)

    plan_page = target / "02_wiki" / "plans" / "dad.md"
    content = plan_page.read_text(encoding="utf-8")
    assert "建议继续记录近 4 周睡眠时长" in content
    assert any(update["page_type"] == "plan_page" for update in result["wiki_updates"])
```

- [ ] **Step 3: Write the failing rejection-path test**

```python
def test_trend_pipeline_keeps_rejected_candidate_out_of_member_and_plan_pages(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    event_path = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "trend-build-weight.json"

    run_trend_pipeline(event_path, target)

    member_page = target / "02_wiki" / "members" / "dad.md"
    plan_page = target / "02_wiki" / "plans" / "dad.md"
    assert "持续增重已明确" not in member_page.read_text(encoding="utf-8")
    assert "立即调整饮食方案" not in plan_page.read_text(encoding="utf-8")
```

- [ ] **Step 3.5: Write the failing idempotency test for repeated trend builds**

```python
def test_trend_pipeline_rerun_is_idempotent_for_accepted_writebacks(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    event_path = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "trend-build-lipids.json"

    first = run_trend_pipeline(event_path, target)
    second = run_trend_pipeline(event_path, target)

    member_page = target / "02_wiki" / "members" / "dad.md"
    content = member_page.read_text(encoding="utf-8")

    assert first["status"] == "ok"
    assert second["status"] == "ok"
    assert content.count("过去 12 个月血脂总体较前期改善") == 1
```

- [ ] **Step 4: Run the integration tests to verify RED**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_trend_pipeline.py -q
```

Expected:

- FAIL because writeback is not connected yet.

- [ ] **Step 5: Implement minimal gated member/plan updates**

Add narrow helpers to `family_doctor/wiki_updates.py` shaped like:

```python
def apply_member_trend_summary(... ) -> dict[str, Any] | None:
    ...


def apply_plan_trend_action(... ) -> dict[str, Any] | None:
    ...
```

Only write under existing headings:

- `## 最近关键指标`
- `## 行动步骤`

Every accepted write must include inline evidence refs and an update date string, not a hidden sidecar field.

- [ ] **Step 6: Re-run the trend pipeline tests to verify GREEN**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_trend_pipeline.py tests/family_doctor/test_writeback_gate.py -q
```

Expected:

- PASS

- [ ] **Step 7: Commit**

```bash
git add family_doctor/trend_pipeline.py family_doctor/wiki_updates.py family_doctor/markdown_utils.py tests/family_doctor/test_trend_pipeline.py
git commit -m "feat: connect phase3 controlled writeback"
```

---

### Task 5: Make Query Prefer Trend Pages

**Files:**
- Modify: `family_doctor/query_context.py`
- Modify: `family_doctor/query_pipeline.py`
- Modify: `tests/family_doctor/conftest.py`
- Create: `tests/family_doctor/test_trend_query_integration.py`

- [ ] **Step 1: Write the failing real-file discovery test**

```python
def test_query_discovers_real_trend_page_before_falling_back(materialize_query_event, tmp_path):
    vault_root = tmp_path / "family-health"
    trend_page = vault_root / "02_wiki" / "trends" / "dad-blood-pressure.md"
    trend_page.parent.mkdir(parents=True, exist_ok=True)
    trend_page.write_text(
        \"\"\"---
type: trend
trend_id: dad_blood_pressure
member_id: dad
topic: blood_pressure
window_primary: 12_months
window_secondary: [4_weeks, 3_months]
tags: [trend]
---

# 爸爸：血压趋势

## 趋势判断
- 过去 12 个月血压总体高于理想范围，仍需持续监测。
\"\"\",
        encoding="utf-8",
    )

    event_path = materialize_query_event(
        tmp_path,
        question="爸爸最近血压趋势怎么样？",
        intent_hint="recent_records",
        member_id="dad",
        context_overrides={"vault_root": str(vault_root)},
    )

    result = run_query_pipeline(event_path)

    assert "总体高于理想范围" in result["answer"]
    assert any("trends:dad_blood_pressure" in source for source in result["used_sources"])
```

- [ ] **Step 2: Write the failing injected-bucket fallback test**

```python
def test_query_falls_back_to_injected_trend_bucket_when_disk_page_missing(materialize_query_event, tmp_path):
    event_path = materialize_query_event(
        tmp_path,
        question="爸爸最近血压趋势怎么样？",
        intent_hint="recent_records",
        member_id="dad",
        retrieval_overrides={
            "trends": [
                {
                    "trend_id": "dad_blood_pressure",
                    "member_id": "dad",
                    "topic": "blood_pressure",
                    "page_path": "02_wiki/trends/dad-blood-pressure.md",
                    "sections": {
                        "trend_judgments": ["过去 12 个月血压总体高于理想范围，仍需持续监测。"],
                    },
                }
            ]
        },
    )

    result = run_query_pipeline(event_path)

    assert "总体高于理想范围" in result["answer"]
```

- [ ] **Step 3: Run the new query integration tests to verify RED**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_trend_query_integration.py -q
```

Expected:

- FAIL because query neither discovers trend pages from `context.vault_root` nor falls back to the normalized `retrieval["trends"]` bucket yet.

- [ ] **Step 4: Implement trend-aware query retrieval**

Update `family_doctor/query_context.py` and `tests/family_doctor/conftest.py` so query does both:

- discover trend pages from `context.vault_root`
- normalize them into the same `retrieval["trends"]` shape used by tests

The normalized bucket shape remains:

```python
"trends": [
    {
        "trend_id": "dad_blood_pressure",
        "member_id": "dad",
        "topic": "blood_pressure",
        "page_path": "02_wiki/trends/dad-blood-pressure.md",
        "sections": {
            "trend_judgments": [...],
            "short_term_fluctuations": [...],
            "promotable_conclusions": [...],
        },
    }
]
```

- [ ] **Step 5: Re-run the query tests to verify GREEN**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_query_pipeline.py tests/family_doctor/test_trend_query_integration.py -q
```

Expected:

- PASS

- [ ] **Step 6: Commit**

```bash
git add family_doctor/query_context.py family_doctor/query_pipeline.py tests/family_doctor/conftest.py tests/family_doctor/test_trend_query_integration.py
git commit -m "feat: make phase3 query consume trends"
```

---

### Task 6: Make Report Prefer Trend Pages

**Files:**
- Modify: `family_doctor/report_pipeline.py`
- Create: `tests/family_doctor/test_trend_report_integration.py`

- [ ] **Step 1: Write the failing trend-first report test**

```python
def test_report_prefers_trend_page_summary_when_present(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    trend_page = target / "02_wiki" / "trends" / "dad-lipids.md"
    trend_page.parent.mkdir(parents=True, exist_ok=True)
    trend_page.write_text(
        \"\"\"---
type: trend
trend_id: dad_lipids
member_id: dad
topic: lipids
window_primary: 12_months
window_secondary: [4_weeks, 3_months]
tags: [trend]
---

# 爸爸：血脂趋势

## 趋势判断
- 过去 12 个月 LDL 整体下降，当前较前期改善。
\"\"\",
        encoding="utf-8",
    )

    result = run_report_pipeline(
        ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "report-checkup-update.json",
        target,
    )

    output_path = Path(result["artifacts"][0]["path"])
    assert "LDL 整体下降" in output_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: Write the failing combined trend-consumption + evidence-ref preservation test**

```python
def test_report_consumes_trend_summary_and_preserves_source_refs(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    trend_page = target / "02_wiki" / "trends" / "dad-lipids.md"
    trend_page.parent.mkdir(parents=True, exist_ok=True)
    trend_page.write_text(
        \"\"\"---
type: trend
trend_id: dad_lipids
member_id: dad
topic: lipids
window_primary: 12_months
window_secondary: [4_weeks, 3_months]
tags: [trend]
---

# 爸爸：血脂趋势

## 趋势判断
- 过去 12 个月 LDL 整体下降，当前较前期改善。

## 关联资料
- source:evt_checkup_report_001
\"\"\",
        encoding="utf-8",
    )

    result = run_report_pipeline(
        ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "report-checkup-update.json",
        target,
    )

    output_path = Path(result["artifacts"][0]["path"])
    assert "LDL 整体下降" in output_path.read_text(encoding="utf-8")
    assert result["evidence_refs"]
    assert any(ref["ref"] == "source:evt_checkup_report_001" for ref in result["evidence_refs"])
```

- [ ] **Step 3: Run the report integration tests to verify RED**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_trend_report_integration.py -q
```

Expected:

- FAIL because report does not consume `trends` yet.

- [ ] **Step 4: Implement trend-aware report composition**

Prefer trend-page `趋势判断` and `短期波动` content when a matching member/topic page exists, but do not remove existing `source_refs`.

- [ ] **Step 5: Re-run the report tests to verify GREEN**

Run:

```bash
PYTHONPATH=. uv run pytest tests/family_doctor/test_report_pipeline.py tests/family_doctor/test_trend_report_integration.py -q
```

Expected:

- PASS

- [ ] **Step 6: Commit**

```bash
git add family_doctor/report_pipeline.py tests/family_doctor/test_trend_report_integration.py
git commit -m "feat: make phase3 report consume trends"
```

---

### Task 7: Add the Trend CLI, Run Full Regression, and Close the Phase

**Files:**
- Create: `scripts/family_doctor/run_trend_build.py`
- Create: `tests/family_doctor/test_run_trend_build_cli.py`
- Modify: `README.md`
- Modify: `docs/superpowers/handoffs/...`

- [ ] **Step 1: Write the failing CLI smoke test**

```python
def test_run_trend_build_cli_writes_trend_page(run_bootstrap, tmp_path):
    target = tmp_path / "family-health"
    assert run_bootstrap(target).returncode == 0
    event_path = ROOT / "tests" / "family_doctor" / "fixtures" / "events" / "trend-build-blood-pressure.json"

    result = subprocess.run(
        [sys.executable, str(TREND_CLI), "--event", str(event_path), "--target", str(target)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "trend build completed" in result.stdout.lower()
    assert (target / "02_wiki" / "trends" / "dad-blood-pressure.md").exists()
```

- [ ] **Step 2: Implement the thin CLI**

Follow the same thin-wrapper pattern as:

- `scripts/family_doctor/run_ingest.py`
- `scripts/family_doctor/run_query.py`
- `scripts/family_doctor/run_report.py`

- [ ] **Step 3: Run the Phase 3 focused tests**

Run:

```bash
PYTHONPATH=. uv run pytest \
  tests/family_doctor/test_trend_pages.py \
  tests/family_doctor/test_trend_pipeline.py \
  tests/family_doctor/test_writeback_gate.py \
  tests/family_doctor/test_trend_query_integration.py \
  tests/family_doctor/test_trend_report_integration.py \
  tests/family_doctor/test_run_trend_build_cli.py -q
```

Expected:

- PASS

- [ ] **Step 4: Run the family_doctor regression suite**

Run:

```bash
python3 scripts/family_doctor/validate_phase0.py --target ./family-health
PYTHONPATH=. uv run pytest tests/family_doctor -q
```

Expected:

- `Phase 0 validation passed`
- full `family_doctor` suite PASS

- [ ] **Step 5: Update docs and snapshot**

At minimum:

- update `README.md`
- add a Phase 3 completion handoff under `docs/superpowers/handoffs/`
- add a current project snapshot

- [ ] **Step 6: Commit**

```bash
git add scripts/family_doctor/run_trend_build.py tests/family_doctor README.md docs/superpowers/handoffs
git commit -m "feat: complete phase3 trends writeback baseline"
```

---

## Exit Criteria

Phase 3 is complete only when all of the following are true:

- `02_wiki/trends/` supports the five initial topics:
  - blood pressure
  - lipids
  - glucose
  - sleep
  - weight
- trend pages preserve the frozen frontmatter and section order
- `trend build` uses `12_months` as the default primary window
- trend pages can include `4_weeks / 3_months` short-term observations
- `writeback_gate` rejects one-off, unsupported, or medically unsafe conclusions
- only gated summaries/actions reach `members/` and `plans/`
- `query` prefers trends when present and falls back safely otherwise
- `report` prefers trends when present and preserves `source_refs`
- the trend CLI works end-to-end
- `validate_phase0.py` still passes
- full `tests/family_doctor` regression passes

---

## Review Checklist for the Implementing Agent

Before claiming Phase 3 complete, verify:

- no new write path escapes `02_wiki/trends/`, `02_wiki/members/`, or `02_wiki/plans/`
- `safe_slug` and relative path handling are reused rather than duplicated
- rejected writeback candidates do not silently mutate member or plan pages
- query/report trend consumption does not weaken existing evidence refs
- Phase 1 / Phase 2 behavior remains green
