# Family Doctor 项目当前快照（Phase 2）

更新时间：`2026-04-21`  
快照类型：`current-state snapshot`  
适用对象：后续接手的 AI agent、开发者、其他平台执行环境

## 1. 当前总状态

截至这份快照，项目处于：

- `Phase 0 foundation`：已完成
- `Phase 1 ingest MVP`：已完成
- `Phase 2 query/report/reminder + thin CLI`：已实现并本地验证

一句话结论：

**项目已经从“只有 ingest 基线”推进到“可 ingest、可 query、可 report、可 reminder、可 CLI 驱动”的 family-doctor MVP。**

## 2. 当前工作区与分支

当前活动工作区：

- `/Users/loutussun/.codex/worktrees/8402/AIHealth`

主仓目录：

- `/Users/loutussun/Documents/codex/AIHealth`

Git 远端：

- `origin = https://github.com/loutussun/AIHealth.git`

当前工作分支：

- `codex/aihealthvault`

重要说明：

- 当前 worktree 里仍有一批未提交改动，主要是 `Phase 2` 的 query/report/reminder/CLI 文件与文档更新
- 仓库根目录仍有未跟踪 `uv.lock`，当前未纳入正式基线

## 3. 必读文档

建议接手时按以下顺序阅读：

1. 设计总文档  
   [2026-04-19-family-doctor-skill-design.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
2. `Phase 1` 完成 handoff  
   [2026-04-21-family-doctor-phase1-ingest-completion.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-phase1-ingest-completion.md)
3. `Phase 2` 计划  
   [2026-04-21-family-doctor-phase2-query-report-reminder.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/plans/2026-04-21-family-doctor-phase2-query-report-reminder.md)
4. `Phase 2` 完成 handoff  
   [2026-04-21-family-doctor-phase2-query-report-reminder-completion.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-phase2-query-report-reminder-completion.md)
5. 本快照  
   [2026-04-21-family-doctor-project-snapshot-phase2.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-project-snapshot-phase2.md)

## 4. 当前已完成能力

### Query

- wiki-backed query context
- 首批 intent：
  - `current_medications`
  - `recent_records`
  - `visit_preparation`
  - `low_evidence_safe_answer`
- mixed-member 泄漏防护

### Report

- 四类 report output
- `03_outputs/` 成品页生成
- `report_job` runtime record
- path safety / sanitize collision 回归

### Reminder

- `generate / confirm / escalate`
- 最小规则页解析
- `reminder_instance` runtime persistence
- 精确 runtime 定位
- 路径安全与 item-level rule binding

### CLI

- [run_query.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_query.py)
- [run_report.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_report.py)
- [run_reminder.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_reminder.py)

## 5. 当前验证状态

已在本地完整确认通过：

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

CLI + smoke 子集：

- `7 passed`

Reminder 核心子集：

- `14 passed`

## 6. 当前 review 状态

- Query：通过 review gate
- Report：通过 review gate
- Reminder：通过 review gate
- CLI：
  - spec reviewer：通过
  - quality reviewer：首轮提出 smoke 不足问题，已修复
  - 修复后最终 reviewer 文本确认因额度问题中断

因此当前的最准确表述是：

**Phase 2 已实现、已本地验证、可继续交接，但仍建议在 reviewer 配额恢复后补一条 CLI 最终质量留痕。**

## 7. 当前风险与注意事项

- `uv.lock` 仍未纳入 repo 基线
- 当前没有真实 `needs_review` 的 CLI 端到端回归样例
- 当前 snapshot 基于 worktree 状态，尚未形成新的 git commit

## 8. 如果会话中断，建议如何恢复

1. 先打开本快照  
   [2026-04-21-family-doctor-project-snapshot-phase2.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-project-snapshot-phase2.md)
2. 再打开 `Phase 2` completion handoff  
   [2026-04-21-family-doctor-phase2-query-report-reminder-completion.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-phase2-query-report-reminder-completion.md)
3. 再确认 worktree 改动：
   - `family_doctor/query_*`
   - `family_doctor/report_*`
   - `family_doctor/reminder_*`
   - `scripts/family_doctor/run_*.py`
   - `tests/family_doctor/test_*cli.py`
4. 优先执行完整回归：
   - 直接运行上面的 `81 passed` 命令

## 9. 下一步最合适的动作

当前最推荐的直接下一步：

1. 把 `Phase 2` 代码与文档整理成一次 checkpoint commit
2. 在 reviewer 配额恢复后补一条 `Task 7` 的最终质量 reviewer 留痕
3. 再决定是进入下一阶段规划，还是先补 richer regression / `needs_review` CLI 用例
