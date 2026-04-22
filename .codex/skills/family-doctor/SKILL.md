# family-doctor

统一调用 AIHealth `family-doctor` 的 skill。宿主是 `codex` 或 `openclaw`，对外只走一个入口。

## 作用

把宿主准备好的 `input_event` JSON 路由到当前已提交的 core：

- `ingest`
- `query`
- `report`
- `reminder`

## 不包含

当前 skill 不包含：

- `trend_build`
- `visit_brief`
- 未提交 `Phase 3 trends`
- 即时通讯接入
- 独立 `scheduler / bot`
- 自动设备同步

## 调用方式

统一入口：

```bash
python3 /absolute/path/to/AIHealth/scripts/family_doctor/run_skill.py --event /absolute/path/to/event.json
```

需要 vault root 的路由：

- `ingest`
- `report`
- `reminder`

示例：

```bash
python3 /absolute/path/to/AIHealth/scripts/family_doctor/run_skill.py \
  --event /absolute/path/to/event.json \
  --target /absolute/path/to/family-health-vault
```

`query` 不要求 CLI `--target`。

## 支持范围

只支持以下 `event_type`：

- `ingest`
- `query`
- `report`
- `reminder`

`report` 当前只支持这些 `payload.report_kind`：

- `checkup_update`
- `lab_update`
- `weekly_health_report`
- `monthly_health_report`

`reminder` 当前只支持这些 `payload.reminder_action`：

- `generate`
- `confirm`
- `escalate`

## 错误行为

- 事件文件不存在：`stderr + non-zero`
- 其他 wrapper 级可恢复错误：`stdout JSON + exit code 0`

## 返回字段

不要假设四条路由返回完全同构。

- `ingest` 重点看：`status`、`summary`、`user_facing_message`、`artifacts`、`wiki_updates`、`runtime_updates`、`evidence_refs`
- `query` 重点看：`status`、`summary`、`answer`、`used_sources`
- `report` 重点看：`status`、`summary`、`user_facing_message`、`artifacts`、`runtime_updates`、`evidence_refs`
- `reminder` 重点看：`status`、`summary`、`artifacts`、`runtime_updates`、`confirm_keywords`、`escalation_policy`
