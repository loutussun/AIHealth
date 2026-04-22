# Family Doctor Skill 回正计划

更新时间：`2026-04-22`  
阶段：`skill realignment`

## 目标

把项目重新收束到原约定形态：

- 宿主：`codex` / `openclaw`
- 对外唯一入口：`family-doctor`
- 对外唯一主合同：`input_event -> output_result`

当前稳定基线固定为已提交并已单独验证的 commit：

- `d2038f4`

## 文档真相源顺序

后续实现、review、handoff、snapshot 都按以下顺序引用：

1. [2026-04-19-family-doctor-skill-design.md](/private/tmp/aihealth-skill-wrapper/docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
2. [2026-04-21-project-execution-collaboration-agreement.md](/private/tmp/aihealth-skill-wrapper/docs/superpowers/specs/2026-04-21-project-execution-collaboration-agreement.md)
3. 本文档
4. 最新 handoff / snapshot

## 当前主交付

当前主交付固定为 `family-doctor` skill core：

- `ingest`
- `query`
- `report`
- `reminder`
- `scripts/family_doctor/run_skill.py` 作为统一宿主入口

补充说明：

- `run_ingest.py`、`run_query.py`、`run_report.py`、`run_reminder.py` 只作为开发/调试入口
- 不新增第二套宿主接口抽象
- 不把 CLI 当成产品最终形态

## 当前不纳入主线

当前不纳入默认主线：

- 即时通讯接入
- 独立 `scheduler / bot`
- 自动设备同步
- `trend_build`
- `visit_brief`
- 未提交 `Phase 3 trends`

## 候选能力登记

当前工作区里仍存在一批趋势层候选能力，只登记，不纳入当前主交付：

1. `trend_topics.py` / `trend_pages.py`
2. `trend_context.py`
3. `trend_pipeline.py`
4. `writeback_gate.py`
5. `query/report` 的 trend-aware 消费
6. `ingest` 自动触发趋势与 `run_trend_build.py`

处理原则：

- 有产品价值
- 当前不计入主线
- 如要接回，必须单独立计划

## 基线验证

稳定基线验证口径固定为：

```bash
git worktree add /tmp/aihealth-check d2038f4
cd /tmp/aihealth-check
python3 scripts/family_doctor/validate_phase0.py --target ./family-health
PYTHONPATH=. uv run --with pytest pytest tests/family_doctor -q
```

结果：

- `validate_phase0` 通过
- `115 passed`
