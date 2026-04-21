# Family Doctor 项目当前快照

更新时间：`2026-04-21`  
快照类型：`current-state snapshot`  
适用对象：后续接手的 AI agent、开发者、其他平台执行环境

## 1. 当前总状态

截至这份快照，项目处于：

- `Phase 0 foundation`：已完成
- `Phase 1 ingest MVP`：执行中
- 当前精确位置：`Task 5` 已完成 CLI 与 acceptance coverage，下一步可继续补 Phase 1 handoff / integration 收尾

一句话结论：

**项目已经完成 ingest 核心链路、source/raw/runtime/wiki 最小更新闭环，并补齐了最小 CLI 与 acceptance coverage。**

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

- 当前 worktree 里有未提交修改，主要是 `Task 4` 修复与新测试
- 仓库根目录存在未跟踪 `uv.lock`，当前未纳入正式基线，也没有在文档中作为必须资产引用

## 3. 必读文档

建议接手时按以下顺序阅读：

1. 设计总文档  
   [2026-04-19-family-doctor-skill-design.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
2. `Phase 1` 实施计划  
   [2026-04-20-family-doctor-phase1-ingest-mvp.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/plans/2026-04-20-family-doctor-phase1-ingest-mvp.md)
3. 旧交接文档  
   [2026-04-20-family-doctor-project-handoff.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md)
4. 上一版快照  
   [2026-04-20-family-doctor-project-snapshot.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-20-family-doctor-project-snapshot.md)
5. 当前这份快照  
   [2026-04-21-family-doctor-project-snapshot.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-project-snapshot.md)

## 4. Phase 1 当前进展

### 4.1 已完成任务

- `Task 1`: ingest 包边界、红测与 fixture 基线
- `Task 2`: 事件加载、dedupe、runtime records
- `Task 3`: raw archive、source pages、路径安全与 source kind 收敛
- `Task 4`: 最小 wiki updates（member / plan / medication）与恢复性修复

### 4.2 Task 4 最终状态

`Task 4` 已完成，并且两个 review gate 都已过：

- 低置信成员匹配不再提前写入 `member_page / plan_page / medication_page`
- `planned_writes / completed_writes` 已与真实页面类型对齐
- 新增了 crash/retry 回归测试
  - 同一 `event_id` 在 `wrote_source/processing` 且 wiki 已部分写入后崩溃
  - 重跑会恢复并推进到 `committed`
  - 不再被错误地 short-circuit 成 duplicate processing

本轮关键改动文件：

- [family_doctor/ingest_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/ingest_pipeline.py)
- [family_doctor/wiki_updates.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/wiki_updates.py)
- [tests/family_doctor/test_wiki_updates.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_wiki_updates.py)
- [tests/family_doctor/test_ingest_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_ingest_pipeline.py)

### 4.3 Task 5 当前状态

`Task 5` 已完成本轮最小闭环：

- 新增 [scripts/family_doctor/run_ingest.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_ingest.py)
- CLI 支持 `--event` / `--target`
- 调用 `family_doctor.ingest_pipeline.run_ingest_pipeline()`
- 成功时输出结构化 JSON 到 `stdout`
- 异常时输出到 `stderr` 并返回非 `0`
- CLI contract 测试已补齐：
  - 成功路径：`stdout` 可解析 JSON、`stderr == ""`
  - 失败路径：`stderr` 有错误、`stdout == ""`

当前更适合视为：

- `Task 5 implementation done`
- `Task 5 review gate passed`
- 下一步可进入 `Phase 1` 收尾文档或继续下一阶段规划

## 5. 最近验证状态

当前已确认通过的本地验证：

```bash
uv run --with pytest python -m pytest \
  tests/family_doctor/test_run_ingest_cli.py \
  tests/family_doctor/test_ingest_acceptance.py \
  tests/family_doctor/test_wiki_updates.py \
  tests/family_doctor/test_source_pages.py \
  tests/family_doctor/test_ingest_pipeline.py \
  tests/family_doctor/test_output_contract.py -q
```

结果：

- `31 passed`

上一轮 Task 4 核心局部验证：

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest \
  tests/family_doctor/test_wiki_updates.py \
  tests/family_doctor/test_source_pages.py \
  tests/family_doctor/test_ingest_pipeline.py \
  tests/family_doctor/test_output_contract.py -q
```

Task 4 review gate 补充验证：

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest \
  tests/family_doctor/test_ingest_pipeline.py \
  tests/family_doctor/test_wiki_updates.py -q
PYTHONPATH=/tmp/codex_pytest python3 -m pytest \
  tests/family_doctor/test_output_contract.py -q
```

结果：

- reviewer 标记 `APPROVED`
- Task 5 CLI reviewer 也已 `APPROVED`

## 6. 当前风险与注意事项

- `uv.lock` 仍是未跟踪文件
  - 当前不要默认把它视为 repo 基线
  - 如后续要正式引入 `uv` 工作流，应先更新文档和 CI

## 7. 如果会话中断，建议如何恢复

1. 先打开本快照  
   [2026-04-21-family-doctor-project-snapshot.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-project-snapshot.md)
2. 再打开 `Phase 1` plan  
   [2026-04-20-family-doctor-phase1-ingest-mvp.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/plans/2026-04-20-family-doctor-phase1-ingest-mvp.md)
3. 先确认 worktree 改动：
   - `family_doctor/ingest_pipeline.py`
   - `family_doctor/wiki_updates.py`
   - `tests/family_doctor/test_ingest_pipeline.py`
   - `tests/family_doctor/test_wiki_updates.py`
4. 下一步优先处理：
   - `Phase 1` 收尾 handoff / implementation notes
   - 或直接开始下一阶段计划拆分
5. 如需重新验证 ingest 基线，优先执行：
   - `uv run --with pytest python -m pytest tests/family_doctor/test_run_ingest_cli.py tests/family_doctor/test_ingest_acceptance.py tests/family_doctor/test_wiki_updates.py tests/family_doctor/test_source_pages.py tests/family_doctor/test_ingest_pipeline.py tests/family_doctor/test_output_contract.py -q`

## 8. 下一步最合适的动作

当前最推荐的直接下一步：

1. 写一份 `Phase 1` 最新 handoff / completion note
2. 决定是继续补更完整 acceptance 场景，还是进入下一阶段
3. 如要继续开发，优先进入 `query / report / reminder` 的 planning
