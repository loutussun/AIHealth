# family-doctor

对外统一使用一个 `family-doctor` skill，宿主通过 `input_event` JSON 调用 AIHealth 当前已提交的 core。

## 当前支持

- `ingest`
- `query`
- `report`
- `reminder`

统一入口命令：

```bash
python3 /absolute/path/to/AIHealth/scripts/family_doctor/run_skill.py --event /absolute/path/to/event.json
```

以下路由必须额外提供 vault root：

- `ingest`
- `report`
- `reminder`

```bash
python3 /absolute/path/to/AIHealth/scripts/family_doctor/run_skill.py \
  --event /absolute/path/to/event.json \
  --target /absolute/path/to/family-health-vault
```

## 当前不支持

- `trend_build`
- `visit_brief`
- 未提交 `Phase 3 trends`

## 支持的 payload 范围

`report_kind`：

- `checkup_update`
- `lab_update`
- `weekly_health_report`
- `monthly_health_report`

`reminder_action`：

- `generate`
- `confirm`
- `escalate`

## 错误行为

- 缺失事件文件：`stderr + non-zero`
- 缺 `event_type`、不支持的 `event_type`、缺少必需 CLI `--target`：`stdout JSON + exit code 0`

## 返回字段提醒

- `query` 没有 `user_facing_message`
- `reminder` 不保证带 `wiki_updates` / `evidence_refs`
- 宿主应按 `route` 读取结果，不要假设所有字段完全统一
