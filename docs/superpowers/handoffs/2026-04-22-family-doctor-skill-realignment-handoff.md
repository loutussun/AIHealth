# Family Doctor Skill 回正 Handoff

更新时间：`2026-04-22`

## 当前结论

当前项目主线固定为：

- 稳定基线 commit：`d2038f4`
- 主交付：`family-doctor` skill core
- 宿主形态：`codex/openclaw -> family-doctor -> input_event/output_result`

当前不再把未提交的 `Phase 3 trends` 当成默认主线。

## 真相源

接手时按以下顺序判断项目边界：

1. [2026-04-19-family-doctor-skill-design.md](/private/tmp/aihealth-skill-wrapper/docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
2. [2026-04-21-project-execution-collaboration-agreement.md](/private/tmp/aihealth-skill-wrapper/docs/superpowers/specs/2026-04-21-project-execution-collaboration-agreement.md)
3. [2026-04-22-family-doctor-skill-realignment.md](/private/tmp/aihealth-skill-wrapper/docs/superpowers/plans/2026-04-22-family-doctor-skill-realignment.md)
4. 本 handoff 与最新 snapshot

## 当前主线

当前只承认以下能力属于主线：

- `ingest`
- `query`
- `report`
- `reminder`
- `run_skill.py` 统一宿主入口

`run_ingest.py`、`run_query.py`、`run_report.py`、`run_reminder.py` 仍保留，但只作为开发/调试入口。

## 当前非主线

以下内容不算当前默认主线：

- 即时通讯接入
- 独立 `scheduler / bot`
- 自动设备同步
- `visit_brief`
- `trend_build`
- 未提交 `Phase 3 trends`

## 候选能力区

当前只做候选登记的能力：

1. `trend_topics.py` / `trend_pages.py`
2. `trend_context.py`
3. `trend_pipeline.py`
4. `writeback_gate.py`
5. `query/report` 的 trend-aware 消费
6. `ingest` 自动触发趋势与 `run_trend_build.py`

## 稳定基线验证

当前被承认的稳定验证结果来自 `d2038f4`：

- `python3 scripts/family_doctor/validate_phase0.py --target ./family-health` 通过
- `PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q` 为 `115 passed`

## 本轮 skill 包装验证

当前隔离 worktree 的实现验证结果：

- `python3 scripts/family_doctor/validate_phase0.py --target ./family-health` 通过
- `PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q` 为 `133 passed`
- 从非 repo cwd 使用绝对路径调用 `run_skill.py` 的 `query` / `ingest` 已实测可用
