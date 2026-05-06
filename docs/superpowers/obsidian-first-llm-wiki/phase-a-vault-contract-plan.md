# Obsidian-first Vault Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the canonical `family-health/` scaffold so the Obsidian vault is the primary product surface, while keeping existing bootstrap and validation tooling deterministic.

**Architecture:** This phase is vault-contract-only. It updates human-readable Obsidian pages, page templates, directory topology, and validation tests; it does not implement report extraction, LLM ingestion, medical reasoning, or Phase 3 trends. Python changes are limited to `bootstrap_vault.py` / `validate_phase0.py` support for the revised vault contract.

**Tech Stack:** Markdown, Obsidian wiki links, CSV fixtures, Python standard library, pytest

---

## Scope

This plan implements only Phase A from [design.md](./design.md):

- Make `family-health/` look and behave like an Obsidian-first family health vault.
- Merge the useful human-readable structure from `ai-health-vault`.
- Add `04_tracking/` CSV assets.
- Align `03_outputs/` directories with the new design.
- Update validators and tests so the scaffold remains reproducible.

This plan does not implement:

- OCR or LLM report parsing
- family-message generation
- visit preparation generation
- medication recognition
- reminder runtime behavior
- trend build execution
- code cleanup for existing Phase 3 candidate modules

## Planned File Map

### Vault Assets

- Modify: `family-health/AGENTS.md`
  - Reframe rules around Obsidian-first vault maintenance.
  - Keep medical safety and source traceability rules.
- Modify: `family-health/index.md`
  - Make it the LLM navigation index for members, sources, plans, outputs, tracking.
- Modify: `family-health/log.md`
  - Preserve append-only contract and document stable log prefixes.
- Create: `family-health/家庭健康管理中心.md`
  - Human-facing Obsidian home page adapted from `ai-health-vault/vault/健康管理中心.md`.
- Create: `family-health/04_tracking/体检指标.csv`
- Create: `family-health/04_tracking/用药打卡.csv`
- Create: `family-health/04_tracking/饮食记录.csv`
- Create: `family-health/04_tracking/运动记录.csv`
- Create: `family-health/04_tracking/睡眠记录.csv`
- Modify: `family-health/00_schema/page-templates/member-template.md`
- Modify: `family-health/00_schema/page-templates/source-template.md`
- Modify: `family-health/00_schema/page-templates/medication-template.md`
- Modify: `family-health/00_schema/page-templates/plan-template.md`
- Create: `family-health/00_schema/page-templates/family-message-template.md`
- Create: `family-health/00_schema/page-templates/visit-brief-template.md`

### Tooling

- Modify: `scripts/family_doctor/validate_phase0.py`
  - Add required directories for `04_tracking/` and revised `03_outputs/`.
  - Validate required human-facing root page.
  - Validate tracking CSV headers.
  - Validate new page templates.
- Modify: `scripts/family_doctor/bootstrap_vault.py`
  - No behavior change expected if it copies all canonical assets recursively; add tests to prove new assets are copied.

### Tests

- Modify: `tests/family_doctor/test_validate_phase0.py`
  - Add red tests for new directories, root page, output dirs, CSV headers, and templates.
- Modify: `tests/family_doctor/test_bootstrap_vault.py`
  - Assert bootstrapped vault includes `家庭健康管理中心.md` and all `04_tracking/*.csv` files.
- Create: `tests/family_doctor/test_obsidian_first_vault_contract.py`
  - Focused contract tests for human-facing page links and Obsidian-first invariants.

### Docs

- Modify: `docs/superpowers/obsidian-first-llm-wiki/README.md`
  - Mark Phase A as planned / in progress / complete as implementation proceeds.
- Optional Modify: `README.md`
  - Only after Phase A passes, update the project state pointer to this directory.

---

## Task 1: Add Obsidian-first Contract Tests

**Files:**

- Create: `tests/family_doctor/test_obsidian_first_vault_contract.py`
- Modify: `tests/family_doctor/test_validate_phase0.py`
- Modify: `tests/family_doctor/test_bootstrap_vault.py`

- [ ] **Step 1: Write failing tests for the human-facing root page**

Add tests that assert:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_family_health_home_page_exists_and_links_core_pages():
    home = ROOT / "family-health" / "家庭健康管理中心.md"
    assert home.exists()

    content = home.read_text(encoding="utf-8")
    assert "[[index]]" in content
    assert "[[log]]" in content
    assert "02_wiki/members" in content
    assert "04_tracking/体检指标.csv" in content
```

- [ ] **Step 2: Write failing tests for `04_tracking/` CSV assets**

Expected files:

```python
EXPECTED_TRACKING_FILES = {
    "体检指标.csv": "member_id,date,item,result,unit,reference_range,status,source_ref,notes",
    "用药打卡.csv": "member_id,date,time,medication_id,dose,status,source_ref,notes",
    "饮食记录.csv": "member_id,date,meal,summary,tags,source_ref,notes",
    "运动记录.csv": "member_id,date,activity,duration_minutes,intensity,source_ref,notes",
    "睡眠记录.csv": "member_id,date,sleep_start,sleep_end,duration_hours,quality,source_ref,notes",
}
```

Assert each file exists and its first line matches the expected header.

- [ ] **Step 3: Write failing tests for revised output directories**

Assert `family-health/03_outputs/` includes:

- `checkup-updates`
- `lab-updates`
- `visit-briefs`
- `family-messages`
- `weekly-reports`
- `monthly-reports`
- `reminder-messages`
- `qa-summaries`

- [ ] **Step 4: Write failing bootstrap copy tests**

Extend `test_bootstrap_vault.py` so a fresh bootstrapped vault contains:

- `家庭健康管理中心.md`
- all `04_tracking/*.csv`
- new output directories
- new page templates

- [ ] **Step 5: Run focused tests and verify they fail**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest \
  tests/family_doctor/test_obsidian_first_vault_contract.py \
  tests/family_doctor/test_validate_phase0.py \
  tests/family_doctor/test_bootstrap_vault.py \
  -q
```

Expected: FAIL because new vault assets and validator rules are not implemented yet.

- [ ] **Step 6: Commit red tests**

```bash
git add tests/family_doctor/test_obsidian_first_vault_contract.py \
  tests/family_doctor/test_validate_phase0.py \
  tests/family_doctor/test_bootstrap_vault.py
git commit -m "test: define obsidian-first vault contract"
```

---

## Task 2: Add Human-facing Vault Assets

**Files:**

- Create: `family-health/家庭健康管理中心.md`
- Modify: `family-health/index.md`
- Modify: `family-health/log.md`
- Modify: `family-health/AGENTS.md`

- [ ] **Step 1: Create `家庭健康管理中心.md`**

Use this minimum structure:

```markdown
---
type: health-hub
purpose: 家庭健康管理入口
---

# 家庭健康管理中心

> 这里是给人看的入口；`index.md` 是给 LLM 和维护者看的导航索引。

## 家庭成员

- [[02_wiki/members/README|成员档案]]

## 最近资料

- [[index|查看 LLM 导航索引]]

## 待复查与计划

- `02_wiki/plans/`

## 给家人的摘要

- `03_outputs/family-messages/`

## 追踪表格

- `04_tracking/体检指标.csv`
- `04_tracking/用药打卡.csv`
- `04_tracking/饮食记录.csv`
- `04_tracking/运动记录.csv`
- `04_tracking/睡眠记录.csv`

## 维护日志

- [[log]]
```

- [ ] **Step 2: Update `index.md`**

Ensure it has sections:

- `## 人类入口`
- `## 成员`
- `## 原始资料`
- `## Wiki 页面`
- `## 输出`
- `## Tracking CSV`
- `## Runtime`

Include a link to `[[家庭健康管理中心]]`.

- [ ] **Step 3: Update `log.md`**

Document stable prefixes:

```markdown
## 日志格式

- `[ingest]`
- `[query]`
- `[report]`
- `[reminder]`
- `[lint]`
- `[manual-review]`
```

- [ ] **Step 4: Update `AGENTS.md`**

Make these rules explicit:

- Vault is the product surface.
- Every meaningful medical assertion needs a source.
- `01_raw/` is append-only / never rewritten by LLM.
- `99_runtime/` is process state, not user-facing knowledge.
- `04_tracking/` is structured tracking data and must preserve headers.

- [ ] **Step 5: Run focused tests**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_obsidian_first_vault_contract.py -q
```

Expected: root-page and index/log/AGENTS tests pass; tracking/output/template tests may still fail.

- [ ] **Step 6: Commit vault root assets**

```bash
git add family-health/家庭健康管理中心.md family-health/index.md family-health/log.md family-health/AGENTS.md
git commit -m "docs: add obsidian-first vault home"
```

---

## Task 3: Add Tracking CSV Contract

**Files:**

- Create: `family-health/04_tracking/体检指标.csv`
- Create: `family-health/04_tracking/用药打卡.csv`
- Create: `family-health/04_tracking/饮食记录.csv`
- Create: `family-health/04_tracking/运动记录.csv`
- Create: `family-health/04_tracking/睡眠记录.csv`
- Modify: `scripts/family_doctor/validate_phase0.py`

- [ ] **Step 1: Add canonical tracking CSV files**

Each file starts with exactly one header row:

```csv
member_id,date,item,result,unit,reference_range,status,source_ref,notes
```

for `体检指标.csv`.

Use the headers listed in Task 1 Step 2 for the other files.

- [ ] **Step 2: Extend validator required directories**

In `scripts/family_doctor/validate_phase0.py`, add:

```python
"04_tracking",
```

to required directory checks.

- [ ] **Step 3: Add tracking header validation**

Add a helper similar to:

```python
EXPECTED_TRACKING_HEADERS = {
    "04_tracking/体检指标.csv": "member_id,date,item,result,unit,reference_range,status,source_ref,notes",
    "04_tracking/用药打卡.csv": "member_id,date,time,medication_id,dose,status,source_ref,notes",
    "04_tracking/饮食记录.csv": "member_id,date,meal,summary,tags,source_ref,notes",
    "04_tracking/运动记录.csv": "member_id,date,activity,duration_minutes,intensity,source_ref,notes",
    "04_tracking/睡眠记录.csv": "member_id,date,sleep_start,sleep_end,duration_hours,quality,source_ref,notes",
}

def validate_tracking_csv_assets(target: Path) -> list[str]:
    errors: list[str] = []
    for relative_path, expected_header in EXPECTED_TRACKING_HEADERS.items():
        path = target / relative_path
        if not path.exists():
            errors.append(f"Missing tracking CSV: {relative_path}")
            continue
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        if first_line != expected_header:
            errors.append(f"{relative_path} header mismatch")
    return errors
```

Call it from `validate_phase0(...)`.

- [ ] **Step 4: Run validator tests**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor/test_validate_phase0.py -q
python3 scripts/family_doctor/validate_phase0.py --target ./family-health
```

Expected: PASS.

- [ ] **Step 5: Commit tracking contract**

```bash
git add family-health/04_tracking scripts/family_doctor/validate_phase0.py tests/family_doctor/test_validate_phase0.py
git commit -m "feat: add health tracking csv contract"
```

---

## Task 4: Align Output Directories and Page Templates

**Files:**

- Modify: `family-health/03_outputs/`
- Modify: `family-health/00_schema/page-templates/member-template.md`
- Modify: `family-health/00_schema/page-templates/source-template.md`
- Modify: `family-health/00_schema/page-templates/medication-template.md`
- Modify: `family-health/00_schema/page-templates/plan-template.md`
- Create: `family-health/00_schema/page-templates/family-message-template.md`
- Create: `family-health/00_schema/page-templates/visit-brief-template.md`
- Modify: `scripts/family_doctor/validate_phase0.py`
- Modify: `tests/family_doctor/test_validate_phase0.py`

- [ ] **Step 1: Add missing output directories**

Create `.gitkeep` files for:

- `family-health/03_outputs/lab-updates/.gitkeep`
- `family-health/03_outputs/family-messages/.gitkeep`

Ensure `reminder-messages` remains the canonical reminder output directory.

- [ ] **Step 2: Update output directory validator**

Make `validate_phase0.py` require the full output directory list from Task 1 Step 3.

- [ ] **Step 3: Update member template**

Ensure required headings:

```markdown
## 基本信息
## 成员识别与代理关系
## 重要病史
## 过敏史与禁忌
## 当前用药
## 最近关键指标
## 近期就医/检查
## 当前计划
## 待核实项
## 来源索引
```

- [ ] **Step 4: Update source template**

Ensure required headings:

```markdown
## 来源信息
## 提取事实
## 异常项
## 影响到的 Wiki 页面
## 待核实项
```

- [ ] **Step 5: Add family message template**

Minimum headings:

```markdown
## 面向对象
## 可发送消息
## 依据来源
## 不确定项
```

- [ ] **Step 6: Add visit brief template**

Minimum headings:

```markdown
## 就医目标
## 一页纸摘要
## 当前用药
## 近期关键检查
## 建议追问医生的问题
## 就医后记录模板
## 依据来源
```

- [ ] **Step 7: Run focused tests**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest \
  tests/family_doctor/test_validate_phase0.py \
  tests/family_doctor/test_obsidian_first_vault_contract.py \
  -q
```

Expected: PASS.

- [ ] **Step 8: Commit output/template alignment**

```bash
git add family-health/03_outputs family-health/00_schema/page-templates \
  scripts/family_doctor/validate_phase0.py tests/family_doctor/test_validate_phase0.py \
  tests/family_doctor/test_obsidian_first_vault_contract.py
git commit -m "feat: align vault templates with obsidian-first contract"
```

---

## Task 5: Prove Bootstrap and Full Regression

**Files:**

- Modify: `tests/family_doctor/test_bootstrap_vault.py`
- Optional Modify: `README.md`
- Modify: `docs/superpowers/obsidian-first-llm-wiki/README.md`

- [ ] **Step 1: Run bootstrap smoke**

Run:

```bash
rm -rf /tmp/family-health-obsidian-first-smoke
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-obsidian-first-smoke
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-obsidian-first-smoke
```

Expected: validation passes.

- [ ] **Step 2: Run full family_doctor tests**

Run:

```bash
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q
```

Expected: PASS. If existing Phase 3 candidate tests fail because they assume old directories or templates, fix only the test/contract conflict needed for Phase A; do not continue Phase 3 implementation.

- [ ] **Step 3: Update this directory index**

In `docs/superpowers/obsidian-first-llm-wiki/README.md`, mark:

```markdown
- Phase A: planned
```

as:

```markdown
- Phase A: complete
```

after tests pass.

- [ ] **Step 4: Optionally update root README**

Only after all tests pass, add a short pointer:

```markdown
Current Obsidian-first realignment docs live in docs/superpowers/obsidian-first-llm-wiki/.
```

Do not rewrite the whole README in this phase.

- [ ] **Step 5: Review git diff**

Run:

```bash
git diff --stat
git diff -- family-health scripts/family_doctor/validate_phase0.py tests/family_doctor docs/superpowers/obsidian-first-llm-wiki README.md
```

Expected: diff includes only Phase A vault-contract changes and docs.

- [ ] **Step 6: Commit final docs**

```bash
git add docs/superpowers/obsidian-first-llm-wiki README.md
git commit -m "docs: record obsidian-first phase a completion"
```

---

## Verification Summary

Phase A is complete only when all of these pass:

```bash
python3 scripts/family_doctor/validate_phase0.py --target ./family-health
rm -rf /tmp/family-health-obsidian-first-smoke
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-obsidian-first-smoke
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-obsidian-first-smoke
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q
```

## Residual Risks After Phase A

- The vault will be structurally correct, but report ingestion will still be mostly scaffolded.
- `family_doctor/*_pipeline.py` will still contain pipeline-first assumptions until later phases.
- Existing uncommitted Phase 3 trend files must remain candidate-only unless a later plan explicitly brings them back.
- Medical interpretation still depends on future LLM workflow prompts and source-grounded write rules.
