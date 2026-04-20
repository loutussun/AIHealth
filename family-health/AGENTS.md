# family-health Canonical Vault

> 这是 `family-doctor` Phase 0 的 canonical vault scaffold。  
> 这里保存的是结构、契约和长期知识入口，不包含业务逻辑代码。

## 角色

- `family-doctor`: 唯一对外 skill 入口
- `health-ingest`: 处理原始资料入库与知识提炼
- `health-query`: 处理问答与信息检索
- `health-report`: 生成周报、月报、体检摘要与就医准备材料
- `health-reminder`: 生成提醒文案与确认流程

## 四类内部能力边界

- `ingest`: 只负责把新资料归档、提取事实、更新知识，不做面向人的最终成品编排
- `query`: 只负责读取和解释现有知识，默认不写长期状态，必要时才生成短期输出
- `report`: 只负责把知识编排成报告类成品，并在需要时沉淀可复用结论回 `02_wiki/`
- `reminder`: 只负责构造提醒、追踪确认与升级状态，长期摘要再按需回写 `02_wiki/`

## 分层约束

- `01_raw/` 只存原始资料，不回写、不改写
- `02_wiki/` 存长期知识与编译结果
- `03_outputs/` 存可发送、可复用的成品
- `99_runtime/` 存运行过程状态，不作为兜底杂物层
- `00_schema/` 存规则、注册表和模板

## 更新规则

- 优先新增页面和增量更新，不直接覆盖证据原件
- 所有可回写内容都应能追溯到 `01_raw/` 或明确的上下文来源
- 涉及冲突、缺失、模糊识别或高风险判断时，必须生成 `review_item`
- `log.md` 记录关键操作，保持 append-only

## 回写规则

- `ingest` 可写 `01_raw/`、`02_wiki/`、`log.md`
- `query` 默认只读；在生成临时答复或短期导出时，可选择写 `03_outputs/`
- `report` 可写 `03_outputs/`，并可将稳定结论提炼回 `02_wiki/`
- `reminder` 主要写 `99_runtime/`，长期摘要或稳定知识按需写回 `02_wiki/`

## Lint 规则

- `structure`: 检查目录拓扑、必要 `.gitkeep`、模板文件和导航页是否齐全
- `knowledge`: 检查成员页、来源页、计划页和趋势页之间的引用是否闭环，低置信度判断是否转为 `review_item`
- `runtime`: 检查运行时实体、状态迁移、去重范围与日志关联字段是否一致
  运行时条目的 `artifact_kind` 应使用 runtime entity 名称，`artifact_id` 应与对应实体的 `log_identity_field` 对齐

## 医疗边界

- 不做诊断、处方调整、停药建议或替代医生判断
- 对于异常指标、症状恶化或高风险情况，只做风险提示与就医建议
- 不自动删除历史记录；必要时只做归档和状态推进

## 目录导航

- `index.md`: 全局导航
- `log.md`: 运行日志
- `00_schema/members.md`: 成员注册规则
- `00_schema/reporting-rules.md`: 报告生成规则
- `00_schema/reminder-rules.md`: 提醒生成规则
- `00_schema/event-schema.json`: 输入事件契约
- `00_schema/runtime-entities.json`: 运行时实体契约
- `00_schema/page-templates/`: 页面模板
