# Family Doctor 当前快照（Skill Realignment）

更新时间：`2026-04-22`

## 当前总状态

截至当前快照，项目应按以下方式理解：

- `Phase 0 foundation`：已完成
- `Phase 1 ingest MVP`：已完成
- `Phase 2 query/report/reminder`：已完成并已提交
- 当前主线：`family-doctor` skill
- 当前未提交 `Phase 3 trends`：候选能力区

一句话结论：

**当前稳定主线是 `d2038f4` 对应的 `family-doctor` skill core。**

## 当前主线能力

当前主线只承认：

- `ingest`
- `query`
- `report`
- `reminder`
- `scripts/family_doctor/run_skill.py`
- `input_event -> output_result`

## 当前非主线

当前不应写成主线的内容：

- 即时通讯接入
- 独立 `scheduler / bot`
- 自动设备同步
- `visit_brief`
- `trend_build`
- 未提交趋势层

## 真相源顺序

1. [2026-04-19-family-doctor-skill-design.md](/private/tmp/aihealth-skill-wrapper/docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
2. [2026-04-21-project-execution-collaboration-agreement.md](/private/tmp/aihealth-skill-wrapper/docs/superpowers/specs/2026-04-21-project-execution-collaboration-agreement.md)
3. [2026-04-22-family-doctor-skill-realignment.md](/private/tmp/aihealth-skill-wrapper/docs/superpowers/plans/2026-04-22-family-doctor-skill-realignment.md)
4. [2026-04-22-family-doctor-skill-realignment-handoff.md](/private/tmp/aihealth-skill-wrapper/docs/superpowers/handoffs/2026-04-22-family-doctor-skill-realignment-handoff.md)
5. 本快照

## 稳定基线验证

稳定基线验证结果：

- `validate_phase0` 通过
- `115 passed`

## 当前实现验证

本轮 `family-doctor` skill 包装验证结果：

- `validate_phase0` 通过
- `tests/family_doctor` 为 `133 passed`
- 非 repo cwd 的绝对路径宿主调用已通过 `query` / `ingest` 实测
