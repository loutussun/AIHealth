# Family Doctor Query / Report / Reminder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the next usable `family-doctor` capability layer on top of Phase 1 ingest by adding safe wiki-backed query, report generation, and reminder state handling.

**Architecture:** This phase should stay file-first and deterministic where possible. We reuse the ingest-produced `02_wiki/`, `03_outputs/`, and `99_runtime/` assets as the system of record, then add a read-oriented query layer, a controlled output/report layer, and finally a runtime-driven reminder layer. Delivery order matters: `query` first, then `report`, then `reminder`.

**Tech Stack:** Python 3 standard library, Markdown, JSON, pytest

---

## Shared Contracts To Define First

在真正进入 `query / report / reminder` 的 RED 之前，先把下面三类共享边界固定下来：

### 1. Report Event Contract

`report` v1 最小输入至少固定为：

- `event_type = "report"`
- `target.member_id` 或 `payload.member_scope`
- `payload.report_kind`
- `payload.period_start`
- `payload.period_end`
- `runtime.related_runtime_id` 可选

建议 fixture 路径：

- `tests/family_doctor/fixtures/events/report-checkup-update.json`
- `tests/family_doctor/fixtures/events/report-weekly-health.json`
- `tests/family_doctor/fixtures/events/report-monthly-health.json`

### 2. Reminder Event Contract

`reminder` v1 最小输入至少固定为：

- `event_type = "reminder"`
- `target.member_id`
- `payload.reminder_action`
- `payload.plan_id`
- `payload.item_id`
- `payload.scheduled_for`
- `runtime.related_runtime_id` 用于 confirm / escalate

建议 fixture 路径：

- `tests/family_doctor/fixtures/events/reminder-generate.json`
- `tests/family_doctor/fixtures/events/reminder-confirm.json`
- `tests/family_doctor/fixtures/events/reminder-escalate.json`

### 3. Reminder Rule Source

`reminder` 不直接从自由文本生成，v1 统一从规则页读取。建议先定义：

- 路径：`02_wiki/plans/<member_id>-reminders.md`
- frontmatter：
  - `type: reminder_rule`
  - `member_id`
  - `plan_id`
- 最小字段：
  - `item_id`
  - `title`
  - `channel_hint`
  - `schedule_hint`
  - `confirm_keywords`
  - `escalation_policy`
  - `source_refs`

写入责任：

- v1 不要求 ingest 自动生成 reminder rule
- 规则页由后续人工维护或 report/query 派生逻辑受控生成
- reminder pipeline 只消费已存在规则；缺失规则时必须返回 `needs_review` 或 `error`

## Scope Strategy

这一轮不是一次把三个子系统同时做完，而是按依赖关系推进：

1. `health-query MVP`
2. `health-report MVP`
3. `health-reminder MVP`

这样拆的原因：

- `query` 先定义“如何安全读取 wiki 并回答”
- `report` 再基于 `query` 的读取与证据模型生成成品
- `reminder` 最后依赖 `plans / medications / runtime state` 的稳定语义

## Planned File Map

**Create package modules**

- `family_doctor/query_pipeline.py`
  - 路由 query 输入、加载 wiki 上下文、生成结构化回答结果。
- `family_doctor/query_context.py`
  - 定义页面读取优先级、相关页面选择、source/evidence 聚合。
- `family_doctor/query_outputs.py`
  - 控制 `qa-summaries/` 的生成、promotion gate、可回写判定。
- `family_doctor/report_pipeline.py`
  - 根据 `report_kind` 生成 `03_outputs/` 成品并执行受控回写。
- `family_doctor/report_templates.py`
  - 封装 v1 报告模板：新报告摘要、周报、月报、就医摘要。
- `family_doctor/reminder_pipeline.py`
  - 处理 `generate / confirm / escalate` 三类 reminder 事件。
- `family_doctor/reminder_runtime.py`
  - 维护 `reminder_instance`、确认状态、超时升级状态。
- `family_doctor/output_pages.py`
  - 生成 `03_outputs/` 下的 Markdown 成品页。
- `family_doctor/reminder_rules.py`
  - 解析 `02_wiki/plans/*-reminders.md` 规则页并提供稳定读取接口。

**Modify existing modules**

- `family_doctor/ingest_models.py`
  - 如有必要，扩展 query/report/reminder 事件字段读取。
- `family_doctor/runtime_records.py`
  - 增加 `report_job`、`reminder_instance` 等运行时实体。
- `family_doctor/markdown_utils.py`
  - 支持输出页与更稳定的 section append/update。

**Create scripts**

- `scripts/family_doctor/run_query.py`
  - 薄 CLI，执行 query pipeline。
- `scripts/family_doctor/run_report.py`
  - 薄 CLI，执行 report pipeline。
- `scripts/family_doctor/run_reminder.py`
  - 薄 CLI，执行 reminder pipeline。

**Create tests**

- `tests/family_doctor/test_query_pipeline.py`
- `tests/family_doctor/test_query_contract.py`
- `tests/family_doctor/test_report_pipeline.py`
- `tests/family_doctor/test_report_outputs.py`
- `tests/family_doctor/test_reminder_pipeline.py`
- `tests/family_doctor/test_reminder_runtime.py`
- `tests/family_doctor/test_query_cli.py`
- `tests/family_doctor/test_report_cli.py`
- `tests/family_doctor/test_reminder_cli.py`
- `tests/family_doctor/test_phase1_regression_smoke.py`
  - 确保 Phase 2-4 实现过程中不破坏既有 ingest 基线。

**Modify docs**

- `README.md`
  - 在相应阶段完成后更新项目状态。
- `docs/superpowers/handoffs/...`
  - 每个子阶段结束后补 snapshot/handoff。

---

### Task 1: Build Query Red Tests and Read Model

**Files:**
- Create: `family_doctor/query_context.py`
- Create: `family_doctor/query_pipeline.py`
- Create: `tests/family_doctor/test_query_pipeline.py`
- Create: `tests/family_doctor/test_query_contract.py`

- [ ] **Step 1: Add failing tests for the first supported query scenarios**

首批问题只覆盖：

- 某成员当前用药
- 某成员最近资料
- 某成员就医前准备摘要
- 低证据问题必须保守回答

- [ ] **Step 2: Add a minimal query event fixture set**

如果现有 fixture 不够，新增最小 query event JSON，保持与当前 event contract 一致。

- [ ] **Step 2.5: Freeze the query event contract in one helper**

在测试辅助层集中定义 query 最小 event shape，避免后续 CLI/pipeline 各自发明字段。

- [ ] **Step 3: Define the read priority model in tests first**

要求测试先锁住读取顺序：

1. `members/`
2. `plans/`
3. `medications/`
4. `sources/`
5. 相关 `03_outputs/qa-summaries/`（仅当明确允许复用）

- [ ] **Step 4: Run only the new query tests to verify RED**

```bash
uv run --with pytest python -m pytest \
  tests/family_doctor/test_query_pipeline.py \
  tests/family_doctor/test_query_contract.py -q
```

- [ ] **Step 5: Commit**

```bash
git add family_doctor tests/family_doctor
git commit -m "test: add phase2 query red tests"
```

---

### Task 2: Implement Query Pipeline and Promotion Gate

**Files:**
- Create: `family_doctor/query_context.py`
- Create: `family_doctor/query_pipeline.py`
- Create: `family_doctor/query_outputs.py`
- Test: `tests/family_doctor/test_query_pipeline.py`
- Test: `tests/family_doctor/test_query_contract.py`

- [ ] **Step 1: Implement minimal query event loading**

支持从标准 event 中识别：

- `event_type = query`
- `member_id`
- `payload.text`

- [ ] **Step 2: Implement wiki-backed context loading**

先从固定路径读取最相关页面，不做复杂搜索。

- [ ] **Step 3: Implement conservative answer assembly**

回答至少包含：

- `known_facts`
- `source_refs`
- `needs_review`
- `requires_doctor_confirmation`

- [ ] **Step 4: Add optional `qa-summaries/` output for promotable answers**

默认 query 只读；只有满足 promotion gate 时才写 `03_outputs/qa-summaries/`。

- [ ] **Step 5: Verify GREEN**

```bash
uv run --with pytest python -m pytest \
  tests/family_doctor/test_query_pipeline.py \
  tests/family_doctor/test_query_contract.py -q
```

- [ ] **Step 6: Commit**

```bash
git add family_doctor tests/family_doctor
git commit -m "feat: add phase2 query pipeline"
```

---

### Task 3: Build Report Red Tests and Output Templates

**Files:**
- Create: `family_doctor/report_pipeline.py`
- Create: `family_doctor/report_templates.py`
- Create: `family_doctor/output_pages.py`
- Create: `tests/family_doctor/test_report_pipeline.py`
- Create: `tests/family_doctor/test_report_outputs.py`
- Create: `tests/family_doctor/fixtures/events/report-checkup-update.json`
- Create: `tests/family_doctor/fixtures/events/report-weekly-health.json`
- Create: `tests/family_doctor/fixtures/events/report-monthly-health.json`

- [ ] **Step 1: Write failing tests for four report kinds**

v1 只覆盖：

- `checkup_update`
- `lab_update`
- `weekly_health_report`
- `monthly_health_report`

- [ ] **Step 2: Lock the output contract**

每个 report 测试都要先锁住：

- 成品写入 `03_outputs/`
- 结果可追溯到 source / member / period
- 只有长期有效结论才允许回写 wiki

- [ ] **Step 2.5: Freeze the report event contract and fixture mapping**

在测试中显式锁住：

- `payload.report_kind`
- `payload.period_start / period_end`
- `target.member_id` 或 `payload.member_scope`
- fixture 文件路径不允许在 CLI / pipeline 各自漂移

- [ ] **Step 3: Verify RED**

```bash
uv run --with pytest python -m pytest \
  tests/family_doctor/test_report_pipeline.py \
  tests/family_doctor/test_report_outputs.py -q
```

- [ ] **Step 4: Commit**

```bash
git add family_doctor tests/family_doctor
git commit -m "test: add phase3 report red tests"
```

---

### Task 4: Implement Report Pipeline and Controlled Writeback

**Files:**
- Create: `family_doctor/report_pipeline.py`
- Create: `family_doctor/report_templates.py`
- Create: `family_doctor/output_pages.py`
- Modify: `family_doctor/runtime_records.py`
- Test: `tests/family_doctor/test_report_pipeline.py`
- Test: `tests/family_doctor/test_report_outputs.py`

- [ ] **Step 1: Implement `report_job` runtime entity**

要求有：

- `planned_writes`
- `completed_writes`
- `report_kind`
- `member_id` 或 `member_scope`

- [ ] **Step 2: Implement report rendering**

保持 deterministic，先基于已有 wiki/sources 拼成 Markdown 成品。

- [ ] **Step 3: Implement controlled writeback**

只允许回写：

- 新确认的 follow-up
- 新确认的 trend summary
- 新确认的 risk / review item

- [ ] **Step 4: Verify GREEN**

```bash
uv run --with pytest python -m pytest \
  tests/family_doctor/test_report_pipeline.py \
  tests/family_doctor/test_report_outputs.py -q
```

- [ ] **Step 5: Commit**

```bash
git add family_doctor tests/family_doctor
git commit -m "feat: add phase3 report pipeline"
```

---

### Task 5: Build Reminder Red Tests and Runtime State Model

**Files:**
- Create: `family_doctor/reminder_pipeline.py`
- Create: `family_doctor/reminder_runtime.py`
- Create: `family_doctor/reminder_rules.py`
- Create: `tests/family_doctor/test_reminder_pipeline.py`
- Create: `tests/family_doctor/test_reminder_runtime.py`
- Create: `tests/family_doctor/fixtures/events/reminder-generate.json`
- Create: `tests/family_doctor/fixtures/events/reminder-confirm.json`
- Create: `tests/family_doctor/fixtures/events/reminder-escalate.json`

- [ ] **Step 1: Write failing tests for `generate / confirm / escalate`**

先锁住三类提醒场景：

- 定时生成
- 用户确认
- 超时升级

- [ ] **Step 2: Lock safety rules in tests first**

测试要明确：

- 默认不输出补服方案
- 未定义 reminder rule 时不能生成提醒
- 不允许把确认消息匹配到错误实例

- [ ] **Step 2.5: Freeze reminder rule source and schema in tests**

测试要明确：

- 规则页位置：`02_wiki/plans/<member_id>-reminders.md`
- 缺失规则页时不能默默 fallback
- `item_id / confirm_keywords / escalation_policy` 是最小必需字段

- [ ] **Step 2.6: Freeze the reminder event contract and fixture mapping**

测试显式锁住：

- `payload.reminder_action`
- `payload.plan_id`
- `payload.item_id`
- `payload.scheduled_for`
- `runtime.related_runtime_id`

- [ ] **Step 3: Verify RED**

```bash
uv run --with pytest python -m pytest \
  tests/family_doctor/test_reminder_pipeline.py \
  tests/family_doctor/test_reminder_runtime.py -q
```

- [ ] **Step 4: Commit**

```bash
git add family_doctor tests/family_doctor
git commit -m "test: add phase4 reminder red tests"
```

---

### Task 6: Implement Reminder Pipeline and Runtime Entities

**Files:**
- Create: `family_doctor/reminder_pipeline.py`
- Create: `family_doctor/reminder_runtime.py`
- Create: `family_doctor/reminder_rules.py`
- Modify: `family_doctor/runtime_records.py`
- Test: `tests/family_doctor/test_reminder_pipeline.py`
- Test: `tests/family_doctor/test_reminder_runtime.py`

- [ ] **Step 1: Implement `reminder_instance` runtime model**

最小字段包括：

- `instance_id`
- `plan_id`
- `item_id`
- `member_id`
- `scheduled_for`
- `status`

- [ ] **Step 2: Implement reminder generate flow**

从 `02_wiki/plans/<member_id>-reminders.md` 读取生成依据；v1 不支持自由推断 reminder 规则。

- [ ] **Step 3: Implement confirm flow**

需要显式关联 `related_runtime_id` 或其他确定性定位方式。

- [ ] **Step 4: Implement escalate flow**

仅升级提醒文本与状态，不输出药物补服建议。

- [ ] **Step 5: Verify GREEN**

```bash
uv run --with pytest python -m pytest \
  tests/family_doctor/test_reminder_pipeline.py \
  tests/family_doctor/test_reminder_runtime.py -q
```

- [ ] **Step 6: Commit**

```bash
git add family_doctor tests/family_doctor
git commit -m "feat: add phase4 reminder pipeline"
```

---

### Task 7: Add Thin CLIs and End-to-End Validation

**Files:**
- Create: `scripts/family_doctor/run_query.py`
- Create: `scripts/family_doctor/run_report.py`
- Create: `scripts/family_doctor/run_reminder.py`
- Create: `tests/family_doctor/test_query_cli.py`
- Create: `tests/family_doctor/test_report_cli.py`
- Create: `tests/family_doctor/test_reminder_cli.py`
- Create: `tests/family_doctor/test_phase1_regression_smoke.py`

- [ ] **Step 1: Implement the three thin CLIs**

和 `run_ingest.py` 保持一致风格：

- 成功写 JSON 到 `stdout`
- 异常写到 `stderr`
- `needs_review` 仍视为可预期结果并返回 `0`

- [ ] **Step 2: Add CLI contract tests**

每个 CLI 至少锁住：

- success JSON
- empty stderr on success
- non-zero + stderr on failure

- [ ] **Step 3: Run the full next-phase suite**

```bash
uv run --with pytest python -m pytest \
  tests/family_doctor/test_query_pipeline.py \
  tests/family_doctor/test_query_contract.py \
  tests/family_doctor/test_report_pipeline.py \
  tests/family_doctor/test_report_outputs.py \
  tests/family_doctor/test_reminder_pipeline.py \
  tests/family_doctor/test_reminder_runtime.py \
  tests/family_doctor/test_query_cli.py \
  tests/family_doctor/test_report_cli.py \
  tests/family_doctor/test_reminder_cli.py \
  tests/family_doctor/test_run_ingest_cli.py \
  tests/family_doctor/test_ingest_acceptance.py \
  tests/family_doctor/test_wiki_updates.py \
  tests/family_doctor/test_source_pages.py \
  tests/family_doctor/test_ingest_pipeline.py \
  tests/family_doctor/test_output_contract.py -q
```

- [ ] **Step 4: Commit**

```bash
git add family_doctor scripts tests
git commit -m "feat: add query report reminder cli workflows"
```

---

## Exit Criteria

这一阶段完成时，应该满足：

- `query` 能回答首批 wiki-backed 问题
- `report` 能生成四类标准产物
- `reminder` 能处理 generate / confirm / escalate
- 所有输出都有 evidence refs 或明确的 safety flag
- CLI contract 对 `query / report / reminder` 都有测试兜底
- Phase 1 ingest 回归套件仍然保持通过

## Recommended Execution Order

建议实际执行顺序严格保持：

1. Query
2. Report
3. Reminder
4. CLI + full validation

不要先做 reminder，再回头补 query/report。那样会让运行时设计先于知识读取模型定型，后面更容易返工。
