# 操作日志

> Append-only。后续所有 ingest、report、reminder、lint 和回写动作都应追加新条目，不要改写历史。

## 日志格式

- 统一格式：`## [YYYY-MM-DD HH:MM] <phase> | <member_id> | <artifact_kind> | <artifact_id>`
- 当条目对应 `99_runtime/` 实体时，`artifact_kind` 应直接使用 runtime entity 名称，例如 `reminder_instance`、`review_item`
- 当条目对应 `99_runtime/` 实体时，`artifact_id` 应使用该实体 `log_identity_field` 指向的字段值
- 说明行放在标题下面，使用简短句子记录本次动作
- 旧条目不重写，只能追加新条目

## [2026-04-19 09:00] bootstrap | system | scaffold | canonical_phase0

初始化 canonical `family-health/` scaffold，并建立 `00_schema/`、`01_raw/`、`02_wiki/`、`03_outputs/`、`99_runtime/` 的 Phase 0 目录约定。

## [2026-04-19 09:20] ingest | dad | source | report_2026_04_19_dad

原始体检报告已入库，等待后续事实提炼与长期知识回写。
