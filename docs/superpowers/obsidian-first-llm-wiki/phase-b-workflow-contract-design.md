# Phase B: Obsidian-first Workflow Contract Design

更新时间：`2026-05-04`
文档类型：`workflow contract design`
状态：`reviewed, pending user review`

## 1. 目标

Phase B 的目标不是扩展 Python pipeline，而是把 `family-doctor` skill 的对外语义从底层 `event_type` 回正为 Obsidian-first 的用户意图工作流。

Phase A 已经让 `family-health/` 成为可打开、可校验、可复制的 canonical vault。Phase B 要回答下一层问题：

> 当用户说“帮我整理体检报告”“帮我准备明天就诊”“帮我给家人解释一下”，`family-doctor` 应该如何作为 LLM wiki 维护员读写这个 vault？

本阶段交付的是 skill/prompt 契约，不是新的医学能力实现。

## 2. 非目标

本阶段不做：

- 新增 `skill_router.py` 路由
- 新增 Python pipeline
- OCR、图像识别或 PDF 解析
- 新的医学推理、诊断、处方建议
- 接入未合并的 Phase 3 trends
- 即时通讯、scheduler、bot 或自动设备同步

底层已提交能力仍是：

- `ingest`
- `query`
- `report`
- `reminder`

Phase B 只在 skill/prompt 层定义“用户意图 workflow 如何映射到这些底层能力和 vault 写入规则”。

## 3. 写入边界

Phase B 必须区分两类写入：

1. 既有 pipeline 写入：由当前已提交的 `ingest`、`report`、`reminder` 执行，按现有代码和测试写入 `01_raw/`、`02_wiki/`、`03_outputs/checkup-updates/`、`03_outputs/lab-updates/`、`99_runtime/` 等路径。
2. 宿主 LLM 直接写入：在用户明确要求产生成品或维护 tracking 时，按 vault contract 直接创建 Markdown 页面或更新 CSV。这属于 skill/prompt 层的 vault 维护行为，不等于新增 Python route。

宿主 LLM 允许的直接写入仅限：

- `03_outputs/visit-briefs/`
- `03_outputs/family-messages/`
- `03_outputs/qa-summaries/`
- `04_tracking/*.csv`
- `log.md`

禁止的直接写入：

- 不直接改写 `01_raw/`
- 不直接写入或静默覆盖 `02_wiki/sources/`、`02_wiki/members/`、`02_wiki/plans/`
- 不直接写入 `03_outputs/checkup-updates/` 或 `03_outputs/lab-updates/`；这些仍由现有 `report` pipeline 负责
- 不创建新的 Python pipeline、CLI route 或 runtime entity
- 不把未证实的医学推断写入长期 wiki

当 workflow 需要稳定、可重复、可测试的机械写入能力时，必须进入后续 Phase C 计划。

## 4. 设计选择

### 4.1 方案 A：直接给 `skill_router` 加 workflow route

优点：看起来更像产品入口。  
缺点：很容易再次变成 pipeline-first，并迫使 Python 承担还没有 LLM/prompt 契约支撑的医学理解。

### 4.2 方案 B：只写文档，不改 skill 文件

优点：最安全。  
缺点：宿主 agent 仍不知道该如何调用 `family-doctor`，Phase B 难以验证。

### 4.3 方案 C：skill/prompt 契约优先

这是推荐方案。更新 `.codex/skills/family-doctor/SKILL.md` 和 `.claude/skills/family-doctor.md`，让宿主 agent 先按用户意图选择 workflow，再把它降级映射到当前底层 `event_type`。不新增 route，不新增 pipeline。

Phase B 采用方案 C。

## 5. 工作流目录

### 5.1 `ingest_report`

适用场景：

- 体检报告
- 化验单
- 就医记录
- 医生建议或出院小结

LLM 行为：

1. 识别这是“新资料入库”意图。
2. 要求或构造底层 `event_type: ingest`。
3. 由既有 `ingest` pipeline 将原始资料归档到 `01_raw/`，并写入 `02_wiki/sources/`、成员页、计划页或待核实项。
4. 宿主 LLM 不直接改写 `01_raw/` 或 `02_wiki/`；它只检查 pipeline 结果是否需要人工复核。
5. 如用户明确要求 tracking 更新，宿主 LLM 可更新 `04_tracking/体检指标.csv`，但必须保留表头并记录 `source_ref`。
6. 如用户明确要求体检/化验更新成品，必须使用现有 `report` pipeline 的 `checkup_update` 或 `lab_update`；不由宿主 LLM 直接写入 `checkup-updates/` 或 `lab-updates/`。
7. 追加 `log.md`。

输出位置：

- 既有 `ingest` pipeline：`01_raw/`、`02_wiki/sources/`、`02_wiki/members/`、`02_wiki/plans/`、`99_runtime/`
- 可选宿主 LLM 直接写入：`04_tracking/体检指标.csv`、`log.md`
- 可选既有 `report` pipeline：`03_outputs/checkup-updates/` 或 `03_outputs/lab-updates/`

当前底层映射：

- `event_type: ingest`
- 可选后续 `event_type: report`，`payload.report_kind: checkup_update` 或 `lab_update`

### 5.2 `medical_visit_prep`

适用场景：

- 明天要去医院，想整理要带什么、问什么
- 复诊前准备一页纸摘要
- 想把近期指标和症状整理给医生看

LLM 行为：

1. 从 `02_wiki/members/`、`02_wiki/sources/`、`02_wiki/plans/`、`04_tracking/` 读取信息。
2. 汇总近期变化、当前用药、关键检查和待核实项。
3. 不补诊断，不替医生决策。
4. 输出结构必须贴合 `visit-brief-template.md`。
5. 每条关键结论都带来源或标记待核实。
6. 追加 `log.md`。

输出位置：

- `03_outputs/visit-briefs/`

当前底层映射：

- 先使用 `event_type: query` 取上下文。
- 当前不新增 `visit_brief` route。
- 若用户明确要求产生成品，宿主 LLM 可按 `visit-brief-template.md` 直接写入 `03_outputs/visit-briefs/` 并追加 `log.md`。
- 若后续希望由确定性 Python 生成该文件，必须另立 Phase C 实现计划。

### 5.3 `family_message`

适用场景：

- 把报告结论解释给家人
- 给父母/配偶写一段温和但准确的提醒
- 把专业术语改写成易懂版本

LLM 行为：

1. 读取相关 source/member/plan/output 页面。
2. 把专业信息改写为家庭沟通语言。
3. 不弱化紧急风险。
4. 不新增医学判断；只改写已有来源支持的信息。
5. 不确定内容放入 `不确定项`。
6. 输出结构必须贴合 `family-message-template.md`。
7. 追加 `log.md`。

输出位置：

- `03_outputs/family-messages/`

当前底层映射：

- `event_type: query` 用于读取和组织事实。
- 当前不新增 `family_message` route。
- 若用户明确要求产生成品，宿主 LLM 可按 `family-message-template.md` 直接写入 `03_outputs/family-messages/` 并追加 `log.md`。
- 若后续希望由确定性 Python 生成该文件，必须另立 Phase C 实现计划。

### 5.4 `daily_tracking_update`

适用场景：

- 记录今天吃药、运动、睡眠、饮食
- 把一条指标追加到 tracking CSV
- 根据用户补充更正 tracking 行

LLM 行为：

1. 识别要更新哪个 `04_tracking/*.csv`。
2. 保留原始表头。
3. 追加记录时必须包含 `member_id`、日期和 `source_ref`。
4. 修改既有记录时必须保留可追踪说明，必要时追加 `notes`，避免静默覆盖。
5. 对含糊值写入 `notes` 或待核实项。
6. 追加 `log.md`。

输出位置：

- `04_tracking/体检指标.csv`
- `04_tracking/用药打卡.csv`
- `04_tracking/饮食记录.csv`
- `04_tracking/运动记录.csv`
- `04_tracking/睡眠记录.csv`

当前底层映射：

- 当前没有专用 Python route。
- Skill/prompt 应指导 LLM 直接维护 vault 文件，并在后续 Phase C 再决定是否增加确定性 CSV helper。

### 5.5 `health_question`

适用场景：

- “最近血压变化怎么样？”
- “上次化验有什么要注意？”
- “爸爸现在有哪些待复查事项？”

LLM 行为：

1. 默认只读 vault。
2. 主要使用 `02_wiki/`、`04_tracking/` 和带 `source_ref` 的页面回答。
3. `03_outputs/*` 只能作为辅助上下文或帮助定位原始证据，永远不能单独作为关键结论证据。
4. 每条关键结论必须回指 `source_ref`、`02_wiki/sources/` 页面、`04_tracking` 行或明确说明“来源不足”。
5. 回答必须区分事实、推断和待核实项。
6. 以下情况必须进入人工复核：来源冲突、成员不确定、指标单位/参考范围缺失、疑似急症、用户要求用药调整、用户要求诊断。
7. 默认不写盘；只有用户明确要求保存问答摘要时，才可沉淀到 `03_outputs/qa-summaries/`。
8. 高风险问题只做就医提示，不诊断。

输出位置：

- 默认不写。
- 用户明确要求保存时，才可写入 `03_outputs/qa-summaries/`。

当前底层映射：

- `event_type: query`

## 6. Skill 文件契约

Phase B 应更新：

- `.codex/skills/family-doctor/SKILL.md`
- `.claude/skills/family-doctor.md`

这两个文件应新增：

- `Obsidian-first workflows`
- workflow 到底层 `event_type` 的映射表
- 每个 workflow 的读写位置
- 医疗安全边界
- 何时必须进入人工复核
- 当前明确不支持的能力

这两个文件不应声称已经支持新的 CLI route。

## 7. 事件映射契约

宿主 agent 应先判断用户意图，再选择底层事件：

| 用户意图 workflow | 当前底层事件 | 是否需要 `--target` | 说明 |
| --- | --- | --- | --- |
| `ingest_report` | `ingest` | 是 | 新资料入库 |
| `medical_visit_prep` | `query` | 否 | 先读取上下文；用户要求时由宿主 LLM 按模板写 Markdown 成品 |
| `family_message` | `query` | 否 | 先读取事实；用户要求时由宿主 LLM 按模板写 Markdown 成品 |
| `daily_tracking_update` | 无专用 route | 视宿主能力而定 | 本阶段只定义 vault 写入规则；确定性 helper 留到 Phase C |
| `health_question` | `query` | 否 | 默认只读 |

## 8. 验收标准

Phase B 完成时应满足：

1. skill 文档从“只列 event_type”升级为“先选用户意图 workflow，再映射 event_type”。
2. 文档明确 `family-health/` 是产品界面，`family-doctor` 是 vault 维护员。
3. 文档不承诺尚未实现的新 route。
4. 文档明确 workflow 的读写目录和复核条件。
5. 当前 Python 测试仍全部通过。
6. 不引入 Phase 3 trends 代码。

## 9. 后续阶段

Phase C 可在 Phase B 契约稳定后再选择一个最小实现点，例如：

- `family_message` 输出 helper
- `visit_brief` 输出 helper
- `04_tracking` CSV helper
- source-grounded prompt examples

每个点都必须单独设计和测试，避免一次性把 skill 再次推回 pipeline-first。
