# AIHealth

一个基于 `LLM Wiki` 方法构建的家庭健康管理项目。

当前主线只围绕一个对外 skill：

- `family-doctor`

宿主形态：

- `codex/openclaw -> family-doctor -> input_event/output_result`

## 当前主交付

当前稳定主线固定为已提交且已验证的 `d2038f4`，主交付是 `family-doctor` skill core：

- `ingest`
- `query`
- `report`
- `reminder`
- `scripts/family_doctor/run_skill.py` 统一宿主入口

补充说明：

- `run_ingest.py`、`run_query.py`、`run_report.py`、`run_reminder.py` 只作为开发/调试入口
- 当前不把 CLI 描述为产品最终形态

## 当前不属于主线

以下内容不应写成当前主交付：

- 即时通讯接入
- 独立 `scheduler / bot`
- 自动设备同步
- `visit_brief`
- `trend_build`
- 未提交 `Phase 3 trends`

## 必读文档

以下文档是当前项目状态的真相源，按顺序阅读：

1. [2026-04-19-family-doctor-skill-design.md](docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
2. [2026-04-21-project-execution-collaboration-agreement.md](docs/superpowers/specs/2026-04-21-project-execution-collaboration-agreement.md)
3. [2026-04-22-family-doctor-skill-realignment.md](docs/superpowers/plans/2026-04-22-family-doctor-skill-realignment.md)
4. [2026-04-22-family-doctor-skill-realignment-handoff.md](docs/superpowers/handoffs/2026-04-22-family-doctor-skill-realignment-handoff.md)
5. [2026-04-22-family-doctor-project-snapshot-skill-realignment.md](docs/superpowers/handoffs/2026-04-22-family-doctor-project-snapshot-skill-realignment.md)

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

## 稳定基线验证

稳定基线验证口径：

```bash
git worktree add /tmp/aihealth-check d2038f4
cd /tmp/aihealth-check
python3 scripts/family_doctor/validate_phase0.py --target ./family-health
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q
```

结果：

- `validate_phase0` 通过
- `115 passed`

## 本轮 skill 包装验证

当前隔离 worktree 的 skill 包装实现已验证：

- `python3 scripts/family_doctor/validate_phase0.py --target ./family-health` 通过
- `PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q` 结果 `133 passed`
- 从非 repo cwd 使用绝对路径调用 `run_skill.py` 的 `query` / `ingest` 已实测可用
