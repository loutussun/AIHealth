# Family Doctor Phase 2 Query / Report / Reminder Completion Handoff

更新时间：`2026-04-21`  
阶段：`Phase 2 / health-query + health-report + health-reminder + thin CLI`  
文档类型：`completion handoff`

## 1. 本阶段完成了什么

`Phase 2` 的目标，是在 `Phase 1 ingest` 的基础上，把 `family-doctor` 从“可入库”推进到“可查询、可产出、可提醒、可命令行调用”的可用阶段。

截至当前，这个目标已经完成到可交接状态。现在项目具备：

- `query MVP`
  - 基于 wiki 的最小读取优先级
  - 首批 query 场景：当前用药、最近资料、就医前准备、低证据保守回答
- `report MVP`
  - 四类标准产物：
    - `checkup_update`
    - `lab_update`
    - `weekly_health_report`
    - `monthly_health_report`
  - `03_outputs/` 产物页生成
  - `report_job` runtime contract
- `reminder MVP`
  - `generate / confirm / escalate`
  - `reminder_instance` runtime persistence
  - 规则页读取、精确 runtime 匹配、路径安全约束
- thin CLI
  - [run_query.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_query.py)
  - [run_report.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_report.py)
  - [run_reminder.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_reminder.py)

一句话总结：

**现在已经有了一个可以 ingest、query、report、reminder 并可由 CLI 驱动的 family-doctor 最小系统。**

## 2. 关键交付物

核心实现文件：

- [family_doctor/query_context.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/query_context.py)
- [family_doctor/query_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/query_pipeline.py)
- [family_doctor/report_templates.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/report_templates.py)
- [family_doctor/output_pages.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/output_pages.py)
- [family_doctor/report_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/report_pipeline.py)
- [family_doctor/reminder_rules.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/reminder_rules.py)
- [family_doctor/reminder_runtime.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/reminder_runtime.py)
- [family_doctor/reminder_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/reminder_pipeline.py)
- [family_doctor/runtime_records.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/runtime_records.py)
- [scripts/family_doctor/run_query.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_query.py)
- [scripts/family_doctor/run_report.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_report.py)
- [scripts/family_doctor/run_reminder.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_reminder.py)

关键测试文件：

- [tests/family_doctor/test_query_contract.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_query_contract.py)
- [tests/family_doctor/test_query_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_query_pipeline.py)
- [tests/family_doctor/test_report_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_report_pipeline.py)
- [tests/family_doctor/test_report_outputs.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_report_outputs.py)
- [tests/family_doctor/test_reminder_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_reminder_pipeline.py)
- [tests/family_doctor/test_reminder_runtime.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_reminder_runtime.py)
- [tests/family_doctor/test_query_cli.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_query_cli.py)
- [tests/family_doctor/test_report_cli.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_report_cli.py)
- [tests/family_doctor/test_reminder_cli.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_reminder_cli.py)
- [tests/family_doctor/test_phase1_regression_smoke.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_phase1_regression_smoke.py)

相关规范与计划：

- [2026-04-19-family-doctor-skill-design.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
- [2026-04-21-family-doctor-phase2-query-report-reminder.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/plans/2026-04-21-family-doctor-phase2-query-report-reminder.md)

## 3. 本阶段补齐的关键边界

### Query

- 读取优先级固定为：
  - `members`
  - `plans`
  - `medications`
  - `sources`
  - `qa_summaries`（仅显式允许时）
- 默认只读
- 低证据问题统一走保守回答
- mixed-member 泄漏已有回归测试

### Report

- `report_job` contract 对齐 Phase 0 runtime registry
- output/runtime 文件名加入稳定 token，避免 sanitize collision
- path-like `event_id` 不会越界写出目标根目录
- output frontmatter 继续保留 traceability 字段和 `wiki_writeback_policy: long_term_only`

### Reminder

- 规则页路径固定为 `02_wiki/plans/<member_id>-reminders.md`
- `rule.item_id` 必须与 `event.item_id` 显式匹配
- confirm/escalate 只能按 `instance_id/runtime_id` 精确命中
- backlink-only 匹配被明确禁止
- reminder message artifact 路径与规则页路径都做了安全归一化
- `completed_writes` 不再虚报未落盘的 `reminder_audit`

## 4. 当前验证基线

已在本地确认通过：

```bash
PYTHONPATH=. uv run pytest \
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
  tests/family_doctor/test_output_contract.py \
  tests/family_doctor/test_phase1_regression_smoke.py -q
```

结果：

- `81 passed`

局部回归也已通过：

```bash
PYTHONPATH=. uv run pytest \
  tests/family_doctor/test_query_cli.py \
  tests/family_doctor/test_report_cli.py \
  tests/family_doctor/test_reminder_cli.py \
  tests/family_doctor/test_phase1_regression_smoke.py -q
```

结果：

- `7 passed`

## 5. 当前 review 状态

- `Task 5 / reminder RED`：spec reviewer `APPROVED`，quality reviewer `APPROVED`
- `Task 6 / reminder MVP`：spec reviewer `APPROVED`，quality reviewer `APPROVED`
- `Task 7 / thin CLI`：
  - spec reviewer `APPROVED`
  - quality reviewer 首轮提出 smoke coverage 问题，已修复
  - 修复后因子代理额度限制，未拿到新的正式 reviewer 文本确认

因此，关于 `Task 7` 需要明确说明：

**代码与测试已在主线程完成修复并本地验证通过，但最终 reviewer 文本确认因额度限制中断。**

从当前实现和验证结果看，没有发现新的阻塞性问题；如果后续继续推进，建议在额度恢复后补一次 reviewer 留痕。

## 6. 当前限制

- 还没有 `needs_review` 的真实 query/report/reminder CLI 端到端样例
- `query` 仍是 deterministic/wiki-first MVP，不做复杂搜索
- `report` 仍未执行真实 wiki writeback
- `reminder` 规则页仍是最小 frontmatter 解析版本
- `uv.lock` 仍未纳入 repo 基线

## 7. 对下一阶段的建议

当前最合理的继续方向有两个：

1. 先收口
   - 提交 Phase 2 代码与文档
   - 补一份最新项目快照
   - 在额度恢复后补一条 `Task 7` 的最终 reviewer 留痕
2. 继续开发
   - 增加真实 `needs_review` CLI 回归用例
   - 开始下一阶段的趋势页 / writeback / richer reminder rule 规划

## 8. 推荐接手方式

建议接手顺序：

1. 先读本 handoff  
   [2026-04-21-family-doctor-phase2-query-report-reminder-completion.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-phase2-query-report-reminder-completion.md)
2. 再读当前最新项目快照  
   [2026-04-21-family-doctor-project-snapshot-phase2.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-project-snapshot-phase2.md)
3. 再读总设计与 Phase 2 plan  
   [2026-04-19-family-doctor-skill-design.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)  
   [2026-04-21-family-doctor-phase2-query-report-reminder.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/plans/2026-04-21-family-doctor-phase2-query-report-reminder.md)

最短验证命令：

```bash
PYTHONPATH=. uv run pytest \
  tests/family_doctor/test_query_pipeline.py \
  tests/family_doctor/test_report_pipeline.py \
  tests/family_doctor/test_reminder_pipeline.py \
  tests/family_doctor/test_query_cli.py \
  tests/family_doctor/test_report_cli.py \
  tests/family_doctor/test_reminder_cli.py -q
```

## 9. 当前结论

`Phase 2 query / report / reminder` 可以视为：

- `implemented`
- `locally verified`
- `handoff-ready`

只是在 `Task 7` 的最终 reviewer 留痕上，还留有一个很小的待补动作。
