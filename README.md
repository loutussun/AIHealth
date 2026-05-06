# AIHealth

一个基于 `LLM Wiki` 方法构建的家庭健康管理项目。

当前主线只围绕一个对外 skill：

- `family-doctor`

产品形态：

- `family-health/` 是 Obsidian-first 家庭健康 vault，也是主要产品界面。
- `family-doctor` 是维护这个 vault 的 LLM wiki 操作员。
- Python 代码只承担确定性机械工具职责。

宿主形态：

- `codex/openclaw -> family-doctor -> input_event/output_result`

## 当前主交付

当前本地 `main` 合并后的主交付是 Obsidian-first `family-doctor` skill core：

- `ingest`
- `query`
- `report`
- `reminder`
- `scripts/family_doctor/run_skill.py` 统一宿主入口
- `scripts/family_doctor/append_tracking_row.py` 作为 `04_tracking/*.csv` append-only helper

补充说明：

- `run_ingest.py`、`run_query.py`、`run_report.py`、`run_reminder.py` 只作为开发/调试入口
- 当前不把 CLI 描述为产品最终形态
- Phase 3 trends/writeback 仍是历史候选区，不属于当前主线实现

## 当前不属于主线

以下内容不应写成当前主交付：

- 即时通讯接入
- 独立 `scheduler / bot`
- 自动设备同步
- `visit_brief` route
- `trend_build` route
- 未接回 Obsidian-first 设计的 `Phase 3 trends`

## 必读文档

以下文档是当前项目状态的真相源，按顺序阅读：

1. [2026-04-19-family-doctor-skill-design.md](docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
2. [2026-04-21-project-execution-collaboration-agreement.md](docs/superpowers/specs/2026-04-21-project-execution-collaboration-agreement.md)
3. [obsidian-first-llm-wiki/README.md](docs/superpowers/obsidian-first-llm-wiki/README.md)
4. [2026-04-22-family-doctor-skill-realignment.md](docs/superpowers/plans/2026-04-22-family-doctor-skill-realignment.md)
5. [2026-04-22-family-doctor-skill-realignment-handoff.md](docs/superpowers/handoffs/2026-04-22-family-doctor-skill-realignment-handoff.md)
6. [2026-04-22-family-doctor-project-snapshot-skill-realignment.md](docs/superpowers/handoffs/2026-04-22-family-doctor-project-snapshot-skill-realignment.md)

历史候选参考：

- [2026-04-21-family-doctor-phase3-trends-writeback-design.md](docs/superpowers/specs/2026-04-21-family-doctor-phase3-trends-writeback-design.md)
- [2026-04-22-worktree-thread-switching-and-cleanup-agreement.md](docs/superpowers/specs/2026-04-22-worktree-thread-switching-and-cleanup-agreement.md)

## Skill 使用

统一入口：

```bash
python3 /absolute/path/to/AIHealth/scripts/family_doctor/run_skill.py --event /absolute/path/to/event.json
```

`ingest`、`report`、`reminder` 需要 vault root：

```bash
python3 /absolute/path/to/AIHealth/scripts/family_doctor/run_skill.py \
  --event /absolute/path/to/event.json \
  --target /absolute/path/to/family-health-vault
```

`query` 不要求 CLI `--target`。

## Tracking Append Helper

`daily_tracking_update` 的 append-only tracking rows 应使用 standalone helper：

```bash
python3 /absolute/path/to/AIHealth/scripts/family_doctor/append_tracking_row.py \
  --target /absolute/path/to/family-health-vault \
  --table medication \
  --row-json /absolute/path/to/row.json
```

该 helper 只用于追加新行，不用于 corrections 或覆盖旧行。

## 当前支持范围

`event_type`：

- `ingest`
- `query`
- `report`
- `reminder`

`report_kind`：

- `checkup_update`
- `lab_update`
- `weekly_health_report`
- `monthly_health_report`

`reminder_action`：

- `generate`
- `confirm`
- `escalate`

## 当前验证

本地 `main` merge 后的验证口径：

```bash
python3 scripts/family_doctor/validate_phase0.py --target ./family-health
rm -rf /tmp/family-health-phase-c0-tracking-append
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-phase-c0-tracking-append
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-phase-c0-tracking-append
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q
```

最近一次 merge 前验证结果：

- 本地 `family-health/` 的 `validate_phase0` 通过
- bootstrap 到 `/tmp/family-health-phase-c0-tracking-append` 后再次 `validate_phase0` 通过
- `tests/family_doctor` 结果：`201 passed`

## 下一步建议

当前最推荐的直接下一步：

1. 在本地 `main` 上重新跑完整验证。
2. 如需发布，再 push/PR。
3. Phase 3 趋势能力后续如需接回，必须在 Obsidian-first 设计下另立计划。
