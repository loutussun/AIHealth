# family-doctor

`family-doctor` is an Obsidian-first family health wiki maintainer. The vault is the product interface; Python routes are helper tools for the current core workflow.

对外统一使用一个 `family-doctor` skill，宿主通过 `input_event` JSON 调用 AIHealth 当前已提交的 core。先选择用户意图 workflow，再映射到现有低层 `event_type`。

## Obsidian-first workflows

Choose the user-intent workflow first, then map it to the current low-level core.
先判断用户意图对应哪个 vault 工作流，再映射到底层 `event_type`；不要把底层路由当成用户可见产品形态。

| Workflow | Use when | Current mapping |
| --- | --- | --- |
| `ingest_report` | New reports, labs, visit records, doctor notes | `event_type: ingest`; optional `event_type: report` with `payload.report_kind: checkup_update` or `payload.report_kind: lab_update` |
| `medical_visit_prep` | User wants a doctor-visit one-pager | `event_type: query`; if user explicitly asks for an artifact, host LLM may write `03_outputs/visit-briefs/` |
| `family_message` | User wants family-friendly wording | `event_type: query`; if user explicitly asks for an artifact, host LLM may write `03_outputs/family-messages/` |
| `daily_tracking_update` | User wants to update medication, diet, exercise, sleep, or checkup CSVs | No dedicated low-level event; append-only rows should use `scripts/family_doctor/append_tracking_row.py`; corrections must not use the helper |
| `health_question` | User asks a question about the vault | `event_type: query`; default read-only |

## Direct write boundaries

Only write directly when the user explicitly asks for an artifact or tracking update.
直接写入只用于用户明确要求产物或追踪更新的场景；其他 vault 更新仍交给既有 pipeline。

Allowed direct writes:

- `03_outputs/visit-briefs/`
- `03_outputs/family-messages/`
- `03_outputs/qa-summaries/`
- `04_tracking/*.csv`
- `log.md`

Forbidden direct writes:

- Do not directly write 01_raw/
- Do not directly write 02_wiki/sources/
- Do not directly write 02_wiki/members/
- Do not directly write 02_wiki/plans/
- Do not directly write 03_outputs/checkup-updates/
- Do not directly write 03_outputs/lab-updates/

## `health_question` evidence rules

回答健康问题默认只读，必须区分事实、推断和待核验项；证据不足时直接说明不足。

- default read-only.
- `03_outputs/* is auxiliary context only`.
- `03_outputs/* must not be used as standalone evidence`.
- Key claims must cite `source_ref`, `02_wiki/sources/`, or `04_tracking` rows.
- If evidence is weak, say `source insufficient`.
- Only save qa-summaries when the user explicitly asks.
- Separates facts, inferences, and verification items.
- For high-risk or urgent symptoms, provide care-seeking guidance only; must not diagnose.
- Review triggers: source conflict, member uncertainty, missing units or reference ranges, urgent symptoms, medication change request, diagnosis request.

## Workflow operational contracts

以下规则限定每个 workflow 的读写边界、复核触发条件和可生成产物；不要把这些 workflow 解释成新增 Python route。

### ingest_report

- ingest_report writes via existing ingest pipeline.
- ingest_report tracking direct write only when explicitly requested and must include source_ref.
- ingest_report tracking direct write must preserve CSV headers.
- ingest_report appends log.md after direct tracking write.
- ingest_report review triggers: member uncertainty, abnormal values, medication dose, diagnosis, missing source.

### medical_visit_prep

- medical_visit_prep reads 02_wiki/members/, 02_wiki/sources/, 02_wiki/plans/, 04_tracking/.
- medical_visit_prep writes 03_outputs/visit-briefs/ only when explicitly requested.
- medical_visit_prep uses visit-brief-template.md.
- medical_visit_prep must not diagnose or replace clinician judgment.
- medical_visit_prep key claims need source or verification marker.
- medical_visit_prep appends log.md after artifact write.

### family_message

- family_message writes 03_outputs/family-messages/ only when explicitly requested.
- family_message uses family-message-template.md.
- family_message must not add new medical claims.
- family_message must not soften urgent risk.
- family_message writes uncertainty to 不确定项.
- family_message appends log.md after artifact write.

### daily_tracking_update

- daily_tracking_update should use standalone CLI helper `scripts/family_doctor/append_tracking_row.py` for append-only tracking rows.
- daily_tracking_update helper is append-only and must not use helper for corrections.
- daily_tracking_update helper is not a new route or event_type.
- daily_tracking_update must preserve CSV headers exactly.
- daily_tracking_update requires member_id, date, source_ref.
- daily_tracking_update must not silently overwrite existing rows.
- daily_tracking_update corrections require traceable explanation in notes.
- daily_tracking_update writes ambiguous values to notes or review.
- daily_tracking_update appends log.md after CSV write.

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

`query` 不要求 `--target`。

```bash
python3 /absolute/path/to/AIHealth/scripts/family_doctor/run_skill.py \
  --event /absolute/path/to/event.json \
  --target /absolute/path/to/family-health-vault
```

## 当前不支持

- No new route.
- No OCR/PDF/image parsing promise.
- No Phase 3 trends.
- No diagnosis/prescription/medication change advice.
- `trend_build`
- `visit_brief`

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
