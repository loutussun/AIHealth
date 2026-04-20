# Family Doctor 项目当前快照

更新时间：`2026-04-20`  
快照类型：`current-state snapshot`  
适用对象：后续接手的 AI agent、开发者、其他平台执行环境

## 1. 这份文档的作用

这份文档用于记录 **当前最新项目快照**。  
它补充而不是替代旧的交接文档：

- [2026-04-20-family-doctor-project-handoff.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md)

旧 handoff 主要覆盖 `Phase 0 foundation` 完成时的状态；  
本文档覆盖当前已经发生的新增变化，包括：

- 仓库已经纳入 git / GitHub 管理
- GitHub Actions 基础设施已配置
- `Phase 1 ingest MVP` 计划已落地
- `Task 1` 已完成并推送
- `Task 2` 已有本地实现提交，但尚未完成 review gate / push

## 2. 当前总状态

截至当前快照，项目处于：

- `Phase 0 foundation`：已完成
- `Phase 1 ingest MVP`：执行中
- 当前精确位置：`Task 2` 已有实现提交，待主代理 review gate

一句话结论：

**项目不是停在“准备开始 Phase 1”，而是已经进入 `Phase 1 / ingest MVP` 的实现阶段。**

## 3. 当前工作区与仓库状态

当前活动工作区：

- `/Users/loutussun/.codex/worktrees/8402/AIHealth`

主仓目录：

- `/Users/loutussun/Documents/codex/AIHealth`

Git 远端：

- `origin = https://github.com/loutussun/AIHealth.git`

当前分支状态：

- 工作树分支：`codex/aihealthvault`
- 主分支：`main`
- 当前本地 `main` 相对 `origin/main`：`ahead 1`

这意味着：

- GitHub 上已经有基线代码
- 当前本地还有 1 个未推送提交
- 这个未推送提交就是 `Phase 1 / Task 2` 的实现提交

## 4. 必读文档

建议接手时按以下顺序阅读：

1. 设计总文档  
   [2026-04-19-family-doctor-skill-design.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
2. `Phase 0` 实施计划  
   [2026-04-19-family-doctor-phase0-foundation.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/plans/2026-04-19-family-doctor-phase0-foundation.md)
3. `Phase 1` 实施计划  
   [2026-04-20-family-doctor-phase1-ingest-mvp.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/plans/2026-04-20-family-doctor-phase1-ingest-mvp.md)
4. 旧交接文档  
   [2026-04-20-family-doctor-project-handoff.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md)
5. 当前快照文档  
   [2026-04-20-family-doctor-project-snapshot.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-20-family-doctor-project-snapshot.md)

## 5. Git 与 GitHub 基线

相比旧 handoff，这里有几个重要更新：

- 根目录现在已经是 git repo
- GitHub 远端仓库已经建立并接通
- 仓库已经有根目录 `README.md`
- GitHub Actions 已配置 `Phase 0 CI`
- 基础 Issue / PR 模板已经存在

相关文件：

- [README.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/README.md)
- [.github/workflows/phase0-ci.yml](/Users/loutussun/.codex/worktrees/8402/AIHealth/.github/workflows/phase0-ci.yml)
- [.github/ISSUE_TEMPLATE/bug_report.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/.github/ISSUE_TEMPLATE/bug_report.md)
- [.github/pull_request_template.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/.github/pull_request_template.md)

已知 GitHub 状态：

- `Phase 0 CI` 首次运行已成功
- 非阻塞提示：`actions/checkout@v4` 和 `actions/setup-python@v5` 存在 Node.js 20 deprecation warning，可后续统一升级

## 6. 最近关键提交

最近 6 个关键提交：

- `a4d015b feat: add ingest runtime records and dedupe`
- `690c89e test: refine phase1 ingest red test fixtures`
- `7033656 test: align ingest fixtures with phase0 contract`
- `aabaf28 test: add phase1 ingest red tests`
- `ea729ed docs: add phase1 ingest mvp plan`
- `e23c78a docs: add repository README and github baseline`

其中：

- `e23c78a`：README、GitHub workflow、Issue/PR 模板
- `ea729ed`：`Phase 1 ingest MVP` 计划
- `aabaf28`、`7033656`、`690c89e`：`Task 1` 红测与 fixture 收敛
- `a4d015b`：`Task 2` 的本地实现提交

## 7. Phase 0 当前状态

`Phase 0 foundation` 已完成，仍然是当前系统稳定基线。

关键资产包括：

- `family-health/` canonical scaffold
- `scripts/family_doctor/bootstrap_vault.py`
- `scripts/family_doctor/validate_phase0.py`
- `tests/family_doctor/test_bootstrap_vault.py`
- `tests/family_doctor/test_validate_phase0.py`

最近一次已知通过验证：

```bash
python3 scripts/family_doctor/validate_phase0.py --target /Users/loutussun/Documents/codex/AIHealth/family-health
PYTHONPATH=/tmp/codex_pytest python3 -m pytest tests/family_doctor -q
```

已知结果：

- `Phase 0 validation passed`
- `24 passed`

说明：

- 这是 `Phase 0` 的完整健康基线
- 后续 `Phase 1` 实现必须在这个基线之上增量推进

## 8. Phase 1 当前进展

### 8.1 Phase 1 plan

`Phase 1 ingest MVP` 计划已经完成、review 通过并纳入仓库：

- [2026-04-20-family-doctor-phase1-ingest-mvp.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/plans/2026-04-20-family-doctor-phase1-ingest-mvp.md)

计划重点：

- staged commit / recoverable 的 `ingest_job`
- `dedupe_record`
- `needs_review + review_item`
- same-day distinct reports / conflicting source / low-confidence block / recoverable failure 等验收场景
- `output_result` 契约测试

### 8.2 Task 1 状态

`Task 1: 建立 ingest 包边界并写红测` 已完成。

已完成内容：

- `family_doctor` 包边界占位
- `ingest` 红测
- 最小 fixture
- fixture 运行时绝对路径重写
- 去除脆弱 stdout 文案断言
- same-day distinct report 用例改为检查 `source_id`

相关提交：

- `aabaf28`
- `7033656`
- `690c89e`

状态判断：

- `Task 1` 已完成并已纳入已推送历史

### 8.3 Task 2 状态

`Task 2: 实现事件加载、去重与 runtime records` 已有本地实现提交：

- `a4d015b feat: add ingest runtime records and dedupe`

本地提交涉及文件：

- [family_doctor/ingest_models.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/ingest_models.py)
- [family_doctor/ingest_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/ingest_pipeline.py)
- [family_doctor/runtime_records.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/runtime_records.py)
- [tests/family_doctor/test_ingest_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_ingest_pipeline.py)
- [tests/family_doctor/test_output_contract.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_output_contract.py)

当前判断：

- `Task 2` 代码已经落地到本地提交
- 但尚未完成主代理的 `spec review + code quality review` gate
- 尚未确认是否可以直接推送到 `origin/main`

为了避免误判，当前应把 `Task 2` 视为：

- `implemented locally`
- `pending review`
- `not yet pushed`

## 9. 当前验证状态

### 9.1 已确认通过的验证

已确认通过：

- `Phase 0` validator
- `Phase 0` 全量测试
- `Task 1` 红测处于预期失败态

### 9.2 Task 2 已知测试结果

根据 implementer 回报，`Task 2` 已运行：

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest tests/family_doctor/test_ingest_pipeline.py tests/family_doctor/test_output_contract.py -v
```

已知结果：

- `5 passed`

重要说明：

- 这代表 `Task 2` 的局部测试已有正向信号
- 但当前快照仍应以“待主代理 review gate”处理，而不是直接视为完全完成

## 10. 当前恢复与接手建议

如果当前会话中断，建议按以下顺序恢复：

1. 进入当前工作区：

```bash
cd /Users/loutussun/.codex/worktrees/8402/AIHealth
```

2. 先读文档：

- `docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md`
- `docs/superpowers/plans/2026-04-20-family-doctor-phase1-ingest-mvp.md`
- `docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md`
- `docs/superpowers/handoffs/2026-04-20-family-doctor-project-snapshot.md`

3. 确认 git 状态：

```bash
git status --short
git log --oneline -6
git branch -vv
```

4. 优先检查 `Task 2`：

- 阅读 `a4d015b`
- 做 `spec review`
- 做 `code quality review`
- 通过后再决定是否 push

5. 如果需要重新确认 Phase 0 基线，可运行：

```bash
python3 scripts/family_doctor/validate_phase0.py --target /Users/loutussun/Documents/codex/AIHealth/family-health
PYTHONPATH=/tmp/codex_pytest python3 -m pytest tests/family_doctor -q
```

## 11. 当前最合理的下一步

当前不建议直接跳到 `Task 3`。  
最合理的下一步是：

1. review `a4d015b`
2. 如果 review 通过，则推送当前本地提交
3. 更新 handoff / snapshot
4. 再进入 `Phase 1 / Task 3`

## 12. 一句话状态结论

**当前项目已经不是“只有 spec 和 Phase 0”，而是已经完成 Git/GitHub 基线、进入 `Phase 1 ingest MVP`，其中 `Task 1` 已完成并推送，`Task 2` 已本地实现但仍待 review gate。**
