# Family Doctor Phase 1 Ingest MVP Completion Handoff

更新时间：`2026-04-21`  
阶段：`Phase 1 / health-ingest MVP`  
文档类型：`completion handoff`

## 1. 本阶段完成了什么

`Phase 1` 的目标，是先把 `family-doctor` 的 `health-ingest` 跑成一个可恢复、可追溯、可验证的最小闭环。

截至当前，这个目标已经完成到可交接状态。当前 ingest MVP 具备：

- 接收标准 `input_event` JSON
- 规范化事件与附件
- 基于 `idempotency_key + fingerprint` 的去重
- 运行时 `ingest_job / dedupe_record / review_item` 记录
- 原始资料归档到 `01_raw/`
- `02_wiki/sources/` 页面生成
- 最小 wiki 增量更新：
  - `members/`
  - `plans/`
  - `medications/`
- 低置信成员匹配阻断
- crash/retry 场景下的恢复能力
- 薄 CLI：
  - [run_ingest.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_ingest.py)

一句话总结：

**现在已经不是“只有设计和脚手架”，而是有了一个真正可运行的 ingest 基线。**

## 2. 关键交付物

核心实现文件：

- [family_doctor/ingest_models.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/ingest_models.py)
- [family_doctor/ingest_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/ingest_pipeline.py)
- [family_doctor/raw_archive.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/raw_archive.py)
- [family_doctor/source_pages.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/source_pages.py)
- [family_doctor/wiki_updates.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/wiki_updates.py)
- [family_doctor/runtime_records.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/runtime_records.py)
- [family_doctor/markdown_utils.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/family_doctor/markdown_utils.py)
- [scripts/family_doctor/run_ingest.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/scripts/family_doctor/run_ingest.py)

关键测试文件：

- [tests/family_doctor/test_ingest_pipeline.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_ingest_pipeline.py)
- [tests/family_doctor/test_output_contract.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_output_contract.py)
- [tests/family_doctor/test_source_pages.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_source_pages.py)
- [tests/family_doctor/test_wiki_updates.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_wiki_updates.py)
- [tests/family_doctor/test_run_ingest_cli.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_run_ingest_cli.py)
- [tests/family_doctor/test_ingest_acceptance.py](/Users/loutussun/.codex/worktrees/8402/AIHealth/tests/family_doctor/test_ingest_acceptance.py)

相关规范与计划：

- [2026-04-19-family-doctor-skill-design.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
- [2026-04-20-family-doctor-phase1-ingest-mvp.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/plans/2026-04-20-family-doctor-phase1-ingest-mvp.md)

## 3. 当前 ingest 能力边界

### 已支持

- `checkup_report`
- `lab_result`
- `medication_record`
- `symptom_note`

### 当前行为特点

- 分类保守，不引入 OCR/LLM
- `sources/` 页面优先，wiki 只做最小增量更新
- 低置信成员匹配进入 `needs_review`
- 重复输入默认走 dedupe
- 对同一 `event_id` 的 `wrote_source/processing` 中断，支持恢复

### 还没做

- 冲突检测模块化
- 结构化指标抽取
- 趋势页自动生成
- 复杂 medication reconciliation
- 更丰富的 acceptance matrix

## 4. 本阶段解决掉的关键风险

这一阶段不只是“功能做出来”，还专门收掉了几个很关键的工程风险：

1. `dedupe` 不是只看 `idempotency_key`，而是看 `fingerprint`
2. 低置信成员匹配不会提前污染 wiki
3. `planned_writes / completed_writes` 与真实写入对齐
4. wiki 页面已写、final job 未写回时，重跑可以恢复
5. CLI 成功/失败输出契约有测试锁住

这几个点很重要，因为后续的 `query / report / reminder` 都会默认依赖 ingest 产出的状态质量。

## 5. 当前验证基线

本地已确认通过：

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

review gate 状态：

- Task 4 reviewer：`APPROVED`
- Task 5 reviewer：`APPROVED`

## 6. 当前已知限制

- ingest 仍然是“deterministic/file-first”版本，不做 OCR 和模型理解
- `sources/` 页已经可用，但提取事实仍偏占位
- `members / plans / medications` 只做最小更新，不代表最终 schema 已定稿
- 当前还没有 `query / report / reminder` 的实现层
- `uv.lock` 仍未纳入 repo 基线

## 7. 对下一阶段的建议

从当前基线往后走，最合理的顺序仍然是：

1. `query MVP`
2. `report MVP`
3. `reminder MVP`

原因：

- `query` 先把“如何读 wiki 和如何输出安全回答”做稳
- `report` 复用 `query` 的读取与证据逻辑
- `reminder` 最依赖 plans、medications、runtime state 的稳定语义

## 8. 推荐接手方式

如果下一个执行者要继续开发，建议这样接：

1. 先读本 handoff  
   [2026-04-21-family-doctor-phase1-ingest-completion.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-phase1-ingest-completion.md)
2. 再读当前最新快照  
   [2026-04-21-family-doctor-project-snapshot.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/handoffs/2026-04-21-family-doctor-project-snapshot.md)
3. 再读下一阶段 planning  
   [2026-04-21-family-doctor-phase2-query-report-reminder.md](/Users/loutussun/.codex/worktrees/8402/AIHealth/docs/superpowers/plans/2026-04-21-family-doctor-phase2-query-report-reminder.md)

最短上手命令：

```bash
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-phase1-smoke
python3 scripts/family_doctor/run_ingest.py \
  --event tests/family_doctor/fixtures/events/checkup-report.json \
  --target /tmp/family-health-phase1-smoke
uv run --with pytest python -m pytest \
  tests/family_doctor/test_run_ingest_cli.py \
  tests/family_doctor/test_ingest_acceptance.py \
  tests/family_doctor/test_wiki_updates.py \
  tests/family_doctor/test_source_pages.py \
  tests/family_doctor/test_ingest_pipeline.py \
  tests/family_doctor/test_output_contract.py -q
```

## 9. 当前结论

`Phase 1 ingest MVP` 可以视为：

- `implemented`
- `reviewed`
- `handoff-ready`

它已经足够作为 `Phase 2 / query` 的真实依赖层继续往前开发。
