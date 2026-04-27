# Family Doctor Obsidian-first LLM Wiki 设计

更新时间：`2026-04-27`
文档类型：`product realignment design`
状态：`approved for implementation planning`

## 1. 背景

用户的原始目标不是开发一个传统后端系统，而是将 Andrej Karpathy 的 `LLM Wiki / LLM Knowledge Base` 方法实例化到家庭健康管理场景中。

原始输入包含三个关键约束：

1. 以 Karpathy 的 `LLM Wiki` 思想为方法基础。
2. 结合参考项目 `ai-health-vault`。
3. 先给大致规划方案，再与用户逐步敲定，最后开发项目。

因此，本项目的产品中心应是一个可被 Obsidian 打开、可被 LLM 持续维护、可被家庭成员长期使用的健康知识库。`family-doctor` skill 是维护这个知识库的操作员，而不是产品本身。

## 2. 回正结论

当前项目需要从以下方向回正：

- 从 `pipeline-first` 回到 `Obsidian-first`
- 从 `backend workflow` 回到 `LLM-maintained wiki`
- 从 `CLI as product surface` 回到 `vault as product surface`
- 从 `event routing demo` 回到 `family health knowledge maintenance`

新的主线定义为：

> `family-doctor` 是一个 Obsidian-first 的家庭健康 LLM Wiki skill。它读取 raw sources，维护 family health wiki，更新 index/log，生成面向家庭成员的健康摘要、就医准备、提醒清单和长期趋势页面。

## 3. 非目标

本阶段不做：

- 即时通讯接入层
- 独立 bot 服务
- 多家庭 SaaS
- 医疗诊断、处方调整、停药建议
- 自动设备实时同步
- 向量数据库优先的 RAG 系统
- 把 Python pipeline 作为用户主要体验

本阶段也不默认接入当前未提交的 `Phase 3 trends` 实现。趋势能力应重新按 Obsidian-first 产品闭环纳入，而不是以 pipeline 形态抢主线。

## 4. 产品原则

### 4.1 Vault 是产品

用户每天打开的是 Obsidian vault，不是 CLI、JSON、runtime job 或测试报告。

vault 必须满足：

- 人可以直接读懂
- LLM 可以稳定维护
- Obsidian 双链可导航
- 每个重要医学判断能追溯来源
- `index.md` 和 `log.md` 能解释知识库当前状态与演化历史

### 4.2 LLM 是 wiki 维护员

LLM 的职责不是每次临时回答问题，而是持续维护一个会积累的健康知识库：

- 新资料进入时，读取 raw source
- 提取事实和待核实项
- 更新成员、报告、药物、问题、趋势、计划页面
- 记录冲突和不确定性
- 更新 `index.md`
- 追加 `log.md`
- 把高价值问答沉淀为可复用页面

### 4.3 Python 是机械层

Python 只负责确定性机械任务：

- vault bootstrap
- schema/contract 校验
- Markdown frontmatter 校验
- 文件路径安全
- index/log 基础更新
- CSV 读写
- 附件归档
- 简单全文搜索

Python 不应假装自己能完成医学理解。报告解读、趋势总结、就医摘要、家庭友好改写，应由 LLM 在 schema 护栏下完成。

### 4.4 医疗安全优先

所有医学输出必须遵守：

- 不诊断
- 不开药
- 不建议自行停药、换药、加药
- 高风险症状提示就医
- 不确定信息进入 `待核实项`
- 重要结论必须带来源
- 面向家人的语言要温和，但不能弱化紧急风险

## 5. 参考项目吸收方式

`ai-health-vault` 的价值在于它已经接近用户真实场景：

- 中文家庭健康入口
- 家庭成员健康档案
- 就医记录
- 体检档案模板
- 用药、饮食、运动、体检指标 CSV
- 8 个贴近用户的 skill/prompt：
  - `health-report-extract`
  - `medication-recognize`
  - `health-trend-analysis`
  - `medical-visit-prep`
  - `apple-watch-analysis`
  - `family-friendly-health`
  - `checkup-calendar`
  - `daily-health-plan`

新项目不应抛弃这些工作流，而应把它们合并成一个 `family-doctor` skill 的内部操作模式。

## 6. 推荐 Vault 结构

保留 `LLM Wiki` 的分层，但让它更像一个可用的 Obsidian vault：

```text
family-health/
├── AGENTS.md
├── index.md
├── log.md
├── 家庭健康管理中心.md
├── 00_schema/
├── 01_raw/
├── 02_wiki/
├── 03_outputs/
├── 04_tracking/
└── 99_runtime/
```

### 6.1 根级页面

`家庭健康管理中心.md`

- 面向用户的入口
- 显示家庭成员、最近资料、待复查事项、近期提醒
- 可以使用 Obsidian 双链和 Dataview 约定

`index.md`

- 面向 LLM 和高级用户的内容目录
- 按成员、来源、问题、药物、趋势、计划、输出分类
- 每次 ingest/report/lint 后更新

`log.md`

- append-only
- 记录 ingest、query、report、reminder、lint、manual review
- 使用稳定前缀，便于 `rg` / `grep` 检索

### 6.2 `01_raw/`

只保存原始资料或原始资料引用，LLM 不得改写。

建议子目录：

- `reports/`
- `labs/`
- `medications/`
- `visits/`
- `symptoms/`
- `wearables/`
- `attachments/`

### 6.3 `02_wiki/`

LLM 主要维护层。

建议页面类型：

- `members/`：每个家庭成员一页
- `sources/`：每份原始资料一页摘要
- `conditions/`：健康问题页
- `medications/`：家庭语境中的药物页
- `visits/`：就医事件页
- `trends/`：成员 + 指标主题趋势页
- `plans/`：行动计划、复查计划、提醒依据

### 6.4 `03_outputs/`

面向消费的成品，不直接替代 wiki。

建议子目录：

- `checkup-updates/`
- `lab-updates/`
- `visit-briefs/`
- `family-messages/`
- `weekly-reports/`
- `monthly-reports/`
- `reminder-messages/`
- `qa-summaries/`

### 6.5 `04_tracking/`

保留 `ai-health-vault` 的 CSV 实用性：

- `体检指标.csv`
- `用药打卡.csv`
- `饮食记录.csv`
- `运动记录.csv`
- `睡眠记录.csv`

这些文件用于表格化追踪。LLM 可以读写，但必须遵守 schema 和追加/更新规则。

### 6.6 `99_runtime/`

只保存过程状态，不保存长期知识。

可保留：

- `jobs/`
- `state/`
- `staging/`
- `traces/`

runtime 的存在是为了恢复、去重、人工复核，不是用户主要阅读入口。

## 7. `family-doctor` Skill 工作流

对外仍可保留单入口 `family-doctor`，但内部语义应从低层 `event_type` 扩展为面向用户意图的工作流。

### 7.1 `ingest_report`

适用于体检报告、化验单、影像摘要等。

流程：

1. 归档 raw source
2. 读取报告或 OCR 文本
3. 提取关键指标、日期、机构、异常项
4. 写入 `02_wiki/sources/`
5. 更新成员页、趋势页、相关 condition 页
6. 更新 `04_tracking/体检指标.csv`
7. 生成 `03_outputs/checkup-updates/` 或 `lab-updates/`
8. 更新 `index.md`
9. 追加 `log.md`

### 7.2 `ingest_medication`

适用于药盒、处方、医生调整用药说明。

流程：

1. 归档 raw source
2. 识别药名、规格、频次、来源置信度
3. 更新 `02_wiki/medications/`
4. 更新对应成员页当前用药
5. 对剂量、频次、相互作用进入待核实项
6. 只在来源明确时更新提醒依据
7. 追加 `log.md`

### 7.3 `visit_prep`

适用于就医前准备。

流程：

1. 读取成员页、相关 condition、medication、trend、visit 记录
2. 生成一页纸医生版摘要
3. 生成 5-8 个个性化追问问题
4. 生成就医后记录模板
5. 输出到 `03_outputs/visit-briefs/`

### 7.4 `visit_followup`

适用于就医后更新。

流程：

1. 读取医生建议、处方、复查时间
2. 更新 `02_wiki/visits/`
3. 更新成员页、药物页、计划页
4. 标记新增复查提醒
5. 追加 `log.md`

### 7.5 `family_message`

适用于把专业内容转成给父母或家人的版本。

流程：

1. 读取目标输出或 wiki 页面
2. 转换为简短、温和、可执行的中文消息
3. 不弱化需要及时就医的风险
4. 输出到 `03_outputs/family-messages/`

### 7.6 `review_periodic`

适用于周报、月报、季度复盘。

流程：

1. 读取最近 log、成员页、tracking CSV、未完成计划
2. 汇总新增资料、异常变化、已过期复查、待确认事项
3. 生成家庭健康管理摘要
4. 必要时提出下一批要补充的 sources

### 7.7 `lint_vault`

适用于知识库健康检查。

检查：

- 无来源医学结论
- 新资料覆盖旧结论但旧页未更新
- 成员页与药物页不一致
- orphan 页面
- 计划页过期项
- 重要 source 未进入 index
- `log.md` 缺记录

## 8. 页面合同

### 8.1 成员页

每个成员页必须包含：

- 基本信息
- 代理关系
- 重要病史
- 过敏史与禁忌
- 当前用药
- 最近关键指标
- 近期就医/检查
- 当前计划
- 待核实项
- 来源索引

成员页是 query/report 的第一入口。

### 8.2 source 页

每份原始资料一页，必须包含：

- 原件路径或来源说明
- source 类型
- 目标成员
- 资料日期
- 提取事实
- 异常项
- 影响到的 wiki 页面
- 待核实项

source 页不是报告复写，而是证据摘要。

### 8.3 药物页

只记录家庭语境中的药物信息，不做通用百科。

必须包含：

- 药品名
- 适用成员
- 来源
- 已记录用法用量
- 开始/停止日期
- fixed / PRN 标记
- 提醒依据
- 漏服规则
- 待核实项

### 8.4 趋势页

趋势页必须从多份 source 或 tracking 数据中生成。

必须区分：

- 事实数据点
- 趋势判断
- 短期波动
- 可能相关因素
- 待核实项
- 可回写结论

单次记录不得被写成长期趋势。

### 8.5 输出页

输出页必须说明：

- 面向谁
- 用途是什么
- 读取了哪些 sources/wiki 页面
- 是否允许回写 wiki
- 哪些内容仍需人工确认

## 9. 与当前代码的关系

### 9.1 保留

可以保留：

- `family-health/` scaffold 的基础分层
- `bootstrap_vault.py`
- `validate_phase0.py`
- 路径安全、frontmatter 校验、runtime contract 的部分工具
- 现有测试中对幂等、路径安全、低置信度 review 的思路

### 9.2 降级

需要降级为辅助工具：

- `family_doctor/*_pipeline.py`
- `scripts/family_doctor/run_*.py`
- `input_event -> output_result` 作为宿主调用协议，而不是产品定义

### 9.3 暂缓

暂缓默认接回：

- `trend_pipeline.py`
- `trend_context.py`
- `writeback_gate.py`
- ingest 自动触发趋势构建

这些能力有价值，但必须重新围绕 Obsidian 页面、来源证据和真实用户闭环设计。

## 10. 第一可用闭环

下一阶段只做一个真实闭环：

> 用户给一份体检报告或 OCR 文本，`family-doctor` 将其归档、提取、更新 Obsidian vault，并生成一份可发给家人的摘要和一份复查待办。

验收标准：

1. `01_raw/` 有原始资料或来源引用。
2. `02_wiki/sources/` 有 source 页。
3. 对应成员页被更新。
4. `04_tracking/体检指标.csv` 被更新或明确说明无法更新。
5. `03_outputs/family-messages/` 有家庭友好版摘要。
6. `02_wiki/plans/` 有复查/待办项。
7. `index.md` 更新。
8. `log.md` 追加记录。
9. 所有医学判断能追溯来源。
10. 不确定项进入 `待核实项`。

## 11. 后续阶段建议

### 阶段 A：Obsidian-first vault contract

- 重写 vault 结构设计
- 合并 `ai-health-vault` 的人类可读页面
- 明确 page templates
- 明确 index/log 更新规则

### 阶段 B：单报告入库闭环

- 支持 OCR 文本或 markdown 报告
- 写 source/member/tracking/output/log
- 生成家庭友好摘要

### 阶段 C：就医准备闭环

- 从 wiki 读取相关上下文
- 生成医生版一页纸摘要
- 生成就医追问清单
- 生成就医后记录模板

### 阶段 D：用药与提醒闭环

- 药物页 contract
- 当前用药核对
- 提醒依据与提醒文案
- 漏服安全边界

### 阶段 E：趋势与周期复盘

- 只基于多 source / tracking 数据形成趋势
- 接回趋势页
- 周报/月报
- vault lint

## 12. 决策记录

- `family-doctor` 的主产品形态是 Obsidian vault。
- skill 是 LLM wiki 维护员，不是独立医疗应用。
- Python 是工具层，不是医学判断层。
- 现有 pipeline 代码可复用，但必须服从 Obsidian-first 设计。
- `ai-health-vault` 的中文家庭健康工作流应作为重要产品参考，而不是只作为历史背景。
