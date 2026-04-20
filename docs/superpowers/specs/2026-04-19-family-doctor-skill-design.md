# 家庭医生 Skill 设计文档

> 状态：已确认第 1-6 部分，可作为后续实现与继续讨论的基线文档。

## 0. 背景与目标

本项目采用 Andrej Karpathy 提出的 `LLM Wiki` 思路，将家庭健康管理系统设计为一个由 LLM 持续维护的知识库系统，而不是一次性问答工具。

核心理念：

- `raw sources` 是原始材料，只读保存
- `wiki` 是 LLM 持续编译和维护的长期知识层
- `schema` 是约束 LLM 如何摄取、回答、生成报告、维护知识库的一组规则

本项目的目标不是开发即时通讯渠道接入层，而是开发一个可被宿主系统调用的 `family-doctor` 单入口 skill。宿主系统负责接入即时通讯、定时触发与消息投递；`family-doctor` skill 负责知识维护、内容生成、状态推进和风险控制。

---

## 1. 系统边界与能力分层

### 1.1 V1 目标

`family-doctor` v1 的职责：

- 接收宿主转交的消息、文件、定时触发事件
- 维护一个持续演化的家庭健康 wiki
- 基于 wiki 生成回答、提醒文案、周报、月报和新报告摘要
- 维护知识一致性、待核实项、冲突项和长期趋势

`family-doctor` v1 的非目标：

- 不实现即时通讯渠道接入
- 不实现独立 scheduler / bot 服务
- 不做自动设备同步
- 不做向量数据库或独立 RAG 基础设施
- 不替代医生进行诊断、处方调整或停药判断
- 不做多家庭 SaaS 化

### 1.2 单入口与内部子能力

对外只暴露一个 skill：

- `family-doctor`

内部按四类能力拆分：

- `health-ingest`
- `health-query`
- `health-report`
- `health-reminder`

设计原则：

- 对宿主保持单入口，降低对接复杂度
- 对内部保持清晰分工，便于后续扩展

### 1.3 职责分工

宿主系统负责：

- 将外部消息、附件、定时事件转为标准输入事件
- 在定时点触发 `report` 或 `reminder`
- 将 skill 返回的文本、文件、提醒内容投递给用户

`family-doctor` skill 负责：

- 路由输入到 ingest / query / report / reminder
- 读写家庭健康知识库
- 生成结构化结果与面向人的成品输出
- 维护冲突标注、待核实项、长期知识与过程状态

知识库负责：

- 保存长期有效的家庭健康认知与结构化关系

原始资料层负责：

- 保存证据原件，不被自动改写

输出层负责：

- 保存高价值、可复用、可发送的阶段性产物

---

## 2. 目录结构与分层设计

建议根目录结构：

```text
family-health/
├── AGENTS.md
├── index.md
├── log.md
├── 00_schema/
├── 01_raw/
├── 02_wiki/
├── 03_outputs/
└── 99_runtime/
```

### 2.1 根级文件

- `AGENTS.md`
  - 总 schema 文件
  - 定义角色、四类内部能力、医疗边界、更新规则、回写规则、lint 规则
- `index.md`
  - 全局导航页
  - 面向 LLM 和人类，列出成员页、问题页、趋势页、计划页、近期输出
- `log.md`
  - append-only 操作日志
  - 记录 ingest、query 产物回写、report 生成、reminder 确认、lint 检查

### 2.2 `00_schema/`

存放规则和注册表，而不是业务数据。

建议内容：

- `members.md`
- `reporting-rules.md`
- `reminder-rules.md`
- `page-templates/`

### 2.3 `01_raw/`

只放原始资料，永不允许 LLM 覆盖。

建议子目录：

- `reports/`
- `labs/`
- `medications/`
- `diets/`
- `exercise/`
- `sleep/`
- `visits/`
- `attachments/`

关键原则：

- 原件永远保留
- wiki 只是编译结果，不替代证据

### 2.4 `02_wiki/`

这是系统核心知识层，v1 先做 7 类页面：

- `members/`
- `sources/`
- `conditions/`
- `medications/`
- `timelines/`
- `trends/`
- `plans/`

设计意图：

- `members` 管人
- `sources` 管证据摘要
- `conditions` 和 `medications` 管主题知识
- `timelines`、`trends`、`plans` 管长期演化与未来动作

### 2.5 `03_outputs/`

只放面向消费的成品，不直接充当核心知识层。

建议子目录：

- `checkup-updates/`
- `weekly-reports/`
- `monthly-reports/`
- `visit-briefs/`
- `reminder-messages/`
- `qa-summaries/`

产物分两类：

- `snapshot`
  - 一次性的周报、提醒文案、某次问答摘要
- `promotable`
  - 其中值得沉淀的内容，可提炼后更新回 `02_wiki/`

### 2.6 `99_runtime/`

保存运行时状态，不属于长期知识。

建议子目录：

- `inbox/`
- `staging/`
- `jobs/`
- `state/`
- `traces/`

职责：

- 管理当前输入的解析过程
- 管理提醒实例和确认状态
- 管理报告生成状态
- 管理去重、重试、人工确认等运行过程

设计原则：

- `wiki` 管知识
- `runtime` 管过程状态

v1 不允许把 `99_runtime/` 作为兜底杂物层。建议最少拆成 5 类实体：

- `ingest_job`
  - 描述一次 ingest 的计划写集、执行阶段、提交状态和恢复点
- `report_job`
  - 描述一次 report 的输入范围、生成状态、派生回写状态
- `reminder_instance`
  - 描述一次提醒的计划时间、发送状态、确认状态、升级状态
- `review_item`
  - 描述一次需要人工确认的冲突、不清晰识别或高风险阻断事件
- `dedupe_record`
  - 描述一次输入的去重范围、内容指纹和命中结果

每类实体都应定义：

- 唯一键
- 生命周期状态
- 允许的状态迁移
- 保留期限或归档策略
- 与 `log.md` 的关联方式

当前阶段的设计约束：

- `state/` 不允许直接承载未分类的任意 JSON
- 所有长期存在的运行状态必须能映射到上述实体之一
- 所有 `needs_review` 都必须对应一个 `review_item`

---

## 3. 四类内部能力工作流

### 3.1 统一事件模型

所有输入都先归一化为一个内部事件：

```text
event = {
  event_id,
  event_type: ingest | query | report | reminder,
  correlation_id,
  causation_id,
  actor_id,
  member_id,
  text,
  attachments,
  trigger_reason,
  occurred_at,
  idempotency_key,
  related_runtime_id,
  source_refs
}
```

这样无论输入来自聊天、文件上传还是定时任务，内部处理方式都统一。

### 3.1A 工作单元与提交模型

为了避免跨目录写入在失败时分叉，所有会产生副作用的事件都必须先创建一个 runtime job，再逐步执行。

最小原则：

1. 先创建 job，再开始任何跨层写入
2. job 中记录：
   - 输入事件摘要
   - 计划写集
   - 当前阶段
   - 已完成写集
   - 回滚或恢复提示
3. 只有当 job 到达 `committed`，这次事件才算成功
4. 如果中途失败，必须留下可恢复状态，而不是只留下半更新的 wiki

建议状态：

- `created`
- `processing`
- `pending_review`
- `committed`
- `failed`
- `aborted`

适用范围：

- `ingest`
- `report`
- `reminder`

`query` 默认是只读流程，只有当它生成 `03_outputs` 或创建 `review_item` 时才需要 job。

### 3.2 `health-ingest`

适用于：

- 新体检报告
- 化验单
- 药盒 / 处方
- 饮食记录
- 运动记录
- 睡眠记录
- 症状补充

处理步骤：

1. 识别成员和资料类型
2. 将原始输入落到 `01_raw/`
3. 提取结构化事实
4. 生成或更新对应 `02_wiki/sources/` 页面
5. 增量更新相关知识页
6. 写入 `log.md`
7. 如命中新报告等场景，发出后续 `report` 任务建议

常见更新目标：

- `members/`
- `conditions/`
- `medications/`
- `timelines/`
- `trends/`
- `plans/`

输出：

- 入库确认摘要
- 待核实项
- 建议的下一步动作

### 3.3 `health-query`

适用于：

- 健康问答
- 历史查询
- 用药说明查询
- 就医准备提问

处理步骤：

1. 识别问题类型和目标成员
2. 优先读取 `index.md` 和对应成员页
3. 再读取相关 `trends / plans / medications / conditions / sources`
4. 生成回答
5. 明确区分事实、判断、待核实项和需医生确认的部分
6. 判断是否生成高价值产物到 `03_outputs/qa-summaries/`

写入原则：

- 默认只读 `02_wiki/`
- 只有当用户提供新事实，或问答产物明显有长期价值时，才允许写入

### 3.4 `health-report`

适用于：

- 新体检报告上传后的趋势摘要
- 新化验单解读
- 每周健康报告
- 每月综合健康报告
- 就医前摘要

处理步骤：

1. 根据 `trigger_reason` 确定报告模板
2. 读取对应时间窗口或主题范围的数据
3. 从 `02_wiki/` 汇总长期上下文
4. 生成面向人的成品并写入 `03_outputs/`
5. 将其中长期有效的结论提炼回写 `02_wiki/`
6. 写入 `log.md`

v1 支持的报告类型：

- 新报告趋势摘要
- 周生活方式报告
- 月综合健康报告
- 就医前摘要

### 3.5 `health-reminder`

适用于：

- 定时服药提醒
- 漏服升级提醒
- 复查前提醒
- 用户确认消息，如“已服药”

两类流程：

提醒生成：

1. 读取 `plans` 和提醒规则
2. 读取 `99_runtime/state/` 中的当前提醒状态
3. 生成提醒文案
4. 将提醒实例写入运行时状态
5. 返回给宿主发送

确认处理：

1. 识别用户确认对应哪次提醒实例
2. 更新 `99_runtime/state/`
3. 按需更新 `02_wiki/members/` 中的依从性摘要
4. 如超时未确认，则生成升级提醒内容

关键原则：

- 提醒配置属于知识层
- 提醒实例和确认状态属于运行时层
- 默认只做提醒、确认、升级、记录，不做个体化补服指导
- 默认不建议双倍剂量
- 只有当该药物存在已记录、可追溯且仍有效的 `missed-dose` 规则时，才允许输出药物特异性的漏服处理提示
- `PRN` 用药与固定频次用药必须分开建模，不能共用同一种提醒语义

### 3.6 四类能力的写入边界

- `ingest`
  - 可写 `01_raw / 02_wiki / log`
- `query`
  - 默认只读，可选写 `03_outputs`
- `report`
  - 主要写 `03_outputs`，并选择性回写 `02_wiki`
- `reminder`
  - 主要写 `99_runtime`，并按需更新成员依从性摘要

---

## 4. 核心页面 Schema 设计

设计原则：

- 适合人读
- 适合 LLM 稳定增量维护
- 标题结构固定
- section 顺序尽量稳定
- frontmatter 只放关键元数据
- 正文中显式区分事实、判断、待核实和来源

### 4.1 `members/`

每个成员一页，作为个人健康主档。

示例：

```md
---
type: member
member_id: dad
display_name: 爸爸
tags: [member]
---

# 爸爸

> 摘要：65岁男性，已知高血压和高脂血症，当前处于长期随访阶段。

## 基本信息
## 成员识别与代理关系
## 慢性病与重要问题
## 过敏史与禁忌
## 当前用药
## 最近关键指标
## 待处理事项
## 最近资料
## 关联页面
## 待核实项
```

职责：

- 汇总个人健康上下文
- 作为 query 的第一入口
- 为 report 和 reminder 提供最近状态

最小安全字段建议：

- 法定姓名或主显示名
- 别名或家庭称呼
- 出生日期或年龄
- 生理性别
- 是否处于妊娠 / 产后一年内
- 主要照护者 / 代理人
- 是否支持代理确认提醒
- 认知或执行能力风险标记
- 严重过敏史
- 肝肾功能高风险标记
- 常用就医机构

写入护栏：

- 当 `member_id` 推断置信度不足时，不允许自动回写成员页
- 需要创建 `review_item` 并返回 `needs_review`

### 4.2 `sources/`

每份原始资料对应一页，保存编译后的摘要和结构化提取结果。

示例：

```md
---
type: source
source_id: report_2026_04_19_dad
member_id: dad
source_kind: checkup_report
source_path: 01_raw/reports/...
event_date: 2026-04-19
tags: [source, report]
---

# 2026-04-19 爸爸体检报告

> 摘要：本次报告新增血脂、肝功能、肾功能数据，LDL 较上次改善，ALT 轻度升高。

## 来源信息
## 提取出的结构化事实
## 异常项
## 与历史差异
## 更新影响
## 关联页面
## 待核实项
```

职责：

- 承接 OCR 和提取结果
- 保留“这份原件说了什么”
- 作为 `raw` 与 `wiki` 之间的桥梁

### 4.3 `medications/`

每种药一页，重点记录本家庭语境中的用药信息。

示例：

```md
---
type: medication
medication_id: atorvastatin
display_name: 阿托伐他汀
tags: [medication]
---

# 阿托伐他汀

> 摘要：本家庭中当前用于爸爸的血脂管理，睡前服用。

## 基本信息
## 适应证
## 剂型与规格
## 当前适用成员
## 已记录用法用量
## 给药途径
## 固定用药 / PRN 标记
## 开始与停止日期
## 最近一次 medication reconciliation
## 漏服规则
## 注意事项
## 已知不良反应
## 已知来源
## 关联问题
## 待核实项
```

原则：

- 不做通用药学百科
- 只保留与家庭场景直接相关的可靠信息
- 需要满足提醒、依从性和就医前摘要的基层随访需求
- 所有提醒依据必须来自当前仍有效的 medication reconciliation 结果

### 4.4 `conditions/`

每个健康问题一页，例如高血压、高血脂、脂肪肝、睡眠不足。

示例：

```md
---
type: condition
condition_id: hypertension
display_name: 高血压
tags: [condition]
---

# 高血压

> 摘要：家庭中主要影响爸爸，目前处于持续监测和药物管理阶段。

## 涉及成员
## 当前状态
## 关键证据
## 相关指标趋势
## 相关药物
## 监测与随访建议
## 待核实项
```

### 4.5 `trends/`

按“成员 + 指标主题”建页，如：

- `dad-blood-pressure.md`
- `mom-sleep.md`
- `dad-lipids.md`

示例：

```md
---
type: trend
trend_id: dad_lipids
member_id: dad
metric_group: lipids
tags: [trend]
---

# 爸爸：血脂趋势

> 摘要：过去 12 个月 LDL 整体下降，甘油三酯有波动，当前风险较前期改善。

## 覆盖时间范围
## 关键指标表
## 趋势判断
## 可能影响因素
## 相关资料
## 相关行动计划
## 待核实项
```

职责：

- 承接多次 source 的累计分析
- 为 query 和 report 提供稳定依据

### 4.6 `plans/`

承担未来动作和提醒依据。

建议拆分：

- 成员级计划页
- 专题计划页
- 提醒规则页的知识镜像

示例：

```md
---
type: plan
plan_id: dad_followup_plan
member_id: dad
tags: [plan]
---

# 爸爸随访与管理计划

> 摘要：当前重点是血压稳定、血脂复查、保持夜间服药依从性。

## 当前目标
## 待复查事项
## 提醒中的事项
## 观察信号
## 下次更新时间
## 关联页面
```

### 4.7 `03_outputs/` 下的成品页

这些页面面向人消费，不必过度结构化，但需保留基础 metadata。

周报示例：

```md
---
type: output
output_kind: weekly_report
member_scope: family
period_start: 2026-04-13
period_end: 2026-04-19
tags: [output, weekly-report]
---

# 家庭健康周报（2026-04-13 ~ 2026-04-19）

## 本周亮点
## 需要关注
## 睡眠摘要
## 运动摘要
## 饮食摘要
## 用药依从性
## 下周建议
## 关联知识页
```

新体检报告摘要示例：

```md
---
type: output
output_kind: checkup_update
member_id: dad
source_id: report_2026_04_19_dad
tags: [output, checkup-update]
---

# 爸爸新体检报告摘要

## 结论摘要
## 与上次相比
## 异常项
## 建议动作
## 需要医生确认
## 关联页面
```

### 4.8 `index.md` 与 `log.md`

`index.md` 建议包含：

- 成员索引
- 当前活跃问题
- 近期新增资料
- 近期新增输出
- 重点趋势页
- 重点计划页

`log.md` 建议统一前缀格式：

```md
## [2026-04-19 09:20] ingest | dad | checkup_report | report_2026_04_19_dad
## [2026-04-19 09:25] report | dad | checkup_update | output_2026_04_19_dad
## [2026-04-19 21:30] reminder | dad | atorvastatin | sent
## [2026-04-19 21:45] reminder-confirm | dad | atorvastatin | confirmed
```

### 4.9 事实主归属矩阵

为避免多页漂移，v1 需要明确“哪类事实首先归谁所有”：

- `sources/`
  - 持有提取事实、原始数值、单位、参考范围、OCR 结果和来源锚点
- `trends/`
  - 持有跨 source 的趋势结论，不重复存所有原始明细
- `plans/`
  - 持有未来动作、随访安排、提醒依据和观察信号
- `medications/`
  - 持有当前有效的 medication reconciliation 结果
- `conditions/`
  - 持有问题级综合认知，不重复复制全部 source 事实
- `members/`
  - 只做成员级摘要导航和当前状态快照，不作为明细事实的主存储

冲突时的优先原则：

- 原始证据以 `01_raw` 为准
- 编译后的结构化事实以 `sources/` 为准
- 成员页和问题页必须引用或摘要，不应成为唯一事实来源

---

## 5. 输入输出契约与事件 Schema 草案

### 5.1 单入口调用原则

统一入口：

```text
family-doctor(input_event) -> output_result
```

所有外部行为都先由宿主包装成 `input_event` 再交给 skill。

### 5.2 输入事件 Schema

```json
{
  "event_id": "evt_2026_04_19_0001",
  "request_id": "req_2026_04_19_0001",
  "idempotency_key": "sha256:...",
  "correlation_id": "corr_2026_04_19_family_01",
  "causation_id": null,
  "event_type": "ingest",
  "trigger_mode": "user_message",
  "occurred_at": "2026-04-19T21:30:00+08:00",
  "actor": {
    "actor_id": "user_dad",
    "role": "member"
  },
  "target": {
    "member_id": "dad",
    "member_hint": "爸爸",
    "match_confidence": 0.98
  },
  "payload": {
    "text": "这是我今天的体检报告",
    "attachments": [
      {
        "attachment_id": "att_001",
        "kind": "image",
        "path": "/abs/path/to/report.jpg",
        "mime_type": "image/jpeg",
        "content_sha256": "sha256:..."
      }
    ],
    "source_refs": []
  },
  "context": {
    "source": "host-runtime",
    "locale": "zh-CN",
    "timezone": "Asia/Shanghai"
  },
  "runtime": {
    "related_runtime_id": null,
    "review_item_id": null,
    "dedupe_scope": "family-health"
  }
}
```

字段说明：

- `request_id`
- `event_id`
- `idempotency_key`
- `correlation_id`
- `causation_id`
- `event_type`
- `trigger_mode`
- `actor`
- `target`
- `payload`
- `context`
- `runtime`

### 5.3 四类事件的最小输入要求

`ingest`

- 至少有 `text` 或 `attachments`
- 最好有 `target.member_id`
- 如果 `member_id` 需要推断且置信度不足，不允许自动回写长期知识层

`query`

- 必须有 `payload.text`

`report`

- 需明确 `payload.report_kind`
- v1 支持：
  - `checkup_update`
  - `weekly_health_report`
  - `monthly_health_report`
  - `visit_brief`

`reminder`

- 需明确 `payload.reminder_action`
- v1 支持：
  - `generate`
  - `confirm`
  - `escalate`
- `confirm` 事件应尽量携带 `related_runtime_id`

### 5.4 附件 Schema

```json
{
  "attachment_id": "att_001",
  "kind": "image",
  "path": "/abs/path/to/file.jpg",
  "mime_type": "image/jpeg",
  "caption": "爸爸 2026 年 4 月体检报告第一页",
  "source_name": "report.jpg",
  "content_sha256": "sha256:...",
  "attachment_group_id": "grp_2026_04_19_01"
}
```

v1 支持的附件类型：

- `image`
- `pdf`
- `text`
- `csv`
- `zip`

关键约束：

- 宿主负责提供稳定的本地文件路径
- skill 只处理本地可读文件

### 5.5 输出结果 Schema

```json
{
  "status": "ok",
  "route": "ingest",
  "summary": "已识别为爸爸的体检报告，已完成入库并更新趋势页。",
  "user_facing_message": "这份体检报告我已经整理好了：LDL 比上次下降，ALT 轻度偏高，建议关注肝功能复查。",
  "artifacts": [
    {
      "kind": "wiki_page",
      "path": "/abs/path/02_wiki/sources/report_2026_04_19_dad.md"
    },
    {
      "kind": "output_page",
      "path": "/abs/path/03_outputs/checkup-updates/2026-04-19_dad.md"
    }
  ],
  "wiki_updates": [
    "02_wiki/members/dad.md",
    "02_wiki/trends/dad-lipids.md",
    "02_wiki/plans/dad-followup-plan.md"
  ],
  "runtime_updates": [],
  "evidence_refs": [
    {
      "source_id": "report_2026_04_19_dad",
      "event_date": "2026-04-19",
      "fact": "LDL-C",
      "value": "2.8",
      "unit": "mmol/L",
      "confidence": 0.94
    }
  ],
  "followup_suggestions": [
    "建议 1-2 周内复查肝功能",
    "如需，我可以继续生成给医生看的摘要"
  ],
  "safety_flags": [
    "not_medical_advice"
  ]
}
```

状态值：

- `ok`
- `needs_review`
- `error`

### 5.6 幂等性要求

建议规则：

- 同一个 `idempotency_key` 的 `ingest` 不重复入库
- 同一个时间窗口内的同一提醒不重复生成提醒实例
- 同一个 `related_runtime_id` 的确认消息不重复记账
- 去重应优先依赖内容指纹，而不是文件路径
- `source_id` 不能只靠“成员 + 日期”命名，需支持同日多份资料和修订版本

### 5.7 宿主与 skill 的最小契约

- 宿主必须提供稳定的本地文件路径
- 宿主应尽量提供 `member_id`，但允许 skill 推断
- 宿主负责真正发送消息和触发定时任务
- skill 只负责内容、知识更新和状态推进

---

## 6. 医疗安全边界、回写规则与 Lint 机制

### 6.1 输出类别

所有输出严格划分为四类：

- `事实`
- `整理后的判断`
- `一般性建议`
- `必须交给医生的事项`

skill 可以处理前三类，但最后一类只能提示、引导和说明不确定性，不能替代医生决策。

### 6.2 默认安全规则

- 不做诊断结论
- 不直接给停药、换药、加药指令
- 不把药物相互作用结论写成“确定无风险”，除非有明确来源
- 不把单次异常值直接写成疾病结论
- 不把生成内容伪装成医生意见
- 不在证据不足时做肯定表述

建议输出时使用这些标签之一：

- `事实`
- `趋势判断`
- `一般建议`
- `需医生确认`
- `待核实`

### 6.3 高风险场景强制升级

一旦 query 或 ingest 命中以下内容，优先输出及时就医建议，而不是继续展开复杂分析：

- 胸痛
- 呼吸困难
- 意识模糊
- 持续高热伴明显不适
- 严重低血糖 / 高血糖表现
- 血压极高并伴症状
- 明显过敏反应
- 黑便、呕血、突发肢体无力、言语异常

### 6.3A 急症分诊规则

高风险规则不能只是一组症状词，还必须落成可执行动作。

每条急症规则至少应定义：

- `escalation_level`
  - `call_emergency_now`
  - `same_day_emergency_evaluation`
  - `urgent_contact_clinician`
- `recommended_action`
- `stop_normal_flow`
- `record_symptom_onset_time`
- `caregiver_notify`
- `source_basis`

红旗命中后的默认行为：

1. 立即停止常规 query / report 深度分析
2. 优先输出急症动作建议
3. 记录症状起始时间（如用户已提供）
4. 明确提醒不要自行驾车前往急诊
5. 如成员支持代理通知，则通知照护者或家庭管理员
6. 创建 `review_item` 以便事后追踪

特殊规则包应单列：

- 儿童
- 妊娠 / 产后一年内
- 老年人
- 多药联用

### 6.4 特殊人群保守策略

以下成员应自动提高保守级别：

- 儿童
- 孕妇 / 备孕
- 老年人
- 多药联用成员
- 肝肾功能异常成员
- 有严重过敏史成员

这些人群不能只使用通用规则的“更保守版”，而应允许挂接专门规则包：

- 儿科规则包
- 妊娠 / 产后规则包
- 老年综合评估规则包
- polypharmacy 规则包

### 6.4A 提醒与漏服安全禁令

v1 的 reminder 系统默认遵守以下硬性禁令：

- 不输出双倍补服建议
- 不输出与原处方冲突的补服建议
- 不把 `PRN` 用药当成固定频次药处理
- 不在药名、剂量、成员、当前是否仍在服用任一信息不清时生成药物特异性建议

只有同时满足以下条件，才允许给出药物特异性的 missed-dose 提示：

- 已完成最近一次 medication reconciliation
- 药物页中存在明确的 `missed-dose` 规则
- 该规则有可靠来源
- 当前提醒实例仍落在允许判断的时间窗内

### 6.5 回写规则

永远不自动改写的层：

- `01_raw/`

允许稳定回写的层：

- `02_wiki/`
- `03_outputs/`
- `99_runtime/`

### 6.6 四类能力的回写边界

- `ingest`
  - 可写 `01_raw`
  - 可写 `02_wiki`
  - 可写 `log.md`
  - 必须记录来源页
- `query`
  - 默认不改 `02_wiki`
  - 高价值回答可写 `03_outputs/qa-summaries/`
  - 只有用户提供新事实时才允许更新 `02_wiki`
- `report`
  - 必写 `03_outputs/`
  - 可提炼回写 `02_wiki`
- `reminder`
  - 主要写 `99_runtime/`
  - 只把长期统计摘要写回 `members/` 或 `plans/`

### 6.7 可以提炼回 `02_wiki/` 的内容

- 新确认的健康问题
- 新确认的长期用药信息
- 新确认的异常趋势
- 新确认的复查 / 随访计划
- 新确认的成员偏好或限制
- 新确认的风险提示

不建议直接回写的内容：

- 一次性的鼓励话术
- 面向群聊的口语版周报
- 临时问答措辞
- 未确认的推测
- 重复的摘要性内容

### 6.7A Promotion Gate

任何内容从 `03_outputs` 或 `query` 进入 `02_wiki`，都必须通过显式门槛。

必须同时满足：

- 有明确 `source_id`
- 能定位到原始值、单位、日期或原始陈述
- 不属于一次性话术
- 能落到既定 schema section
- 不与现有事实冲突，或已创建 `review_item`
- 涉及高风险主题时，具备足够置信度或人工确认

任一条件不满足时：

- 允许保留在 `03_outputs`
- 不允许提升为长期知识

### 6.8 冲突处理规则

新资料与旧 wiki 冲突时，不能直接覆盖，必须：

1. 更新对应 `sources/` 页面
2. 在目标 wiki 页标记冲突项
3. 添加 `待核实` section
4. 记录冲突来源
5. 必要时返回 `needs_review`

以下情况应被视为安全阻断，而不仅仅是普通冲突：

- 药名或剂量识别不清
- 单位缺失或明显异常
- 成员不明确
- 来源互相冲突
- 涉及高风险药但信息不全

命中安全阻断时：

- 必须返回 `needs_review`
- 只能输出“需要人工核实 / 医生确认”
- 不允许继续生成看似确定的建议

### 6.9 所有关键更新都应带来源

建议记录：

- `updated_from`
- `updated_at`

### 6.10 Lint 机制

v1 建议先做 3 类 lint。

结构 lint：

- frontmatter 是否齐全
- broken links
- `index.md` 是否遗漏重要页面
- orphan pages
- `log.md` 格式是否合法

知识 lint：

- 成员页中的药物是否都有对应 `medications/` 页面
- `plans/` 中的待复查事项是否有来源
- `trends/` 中的关键结论是否能追溯到 `sources/`
- 是否存在互相矛盾的核心事实
- 是否存在长期未处理的 `待核实项`

运行 lint：

- 是否有 reminder 规则但无对应成员 / 计划
- 是否有已过期随访计划未更新
- 是否有应出的周报 / 月报未生成
- 是否有反复未确认的提醒实例
- 是否有多次 ingest 重复入库的嫌疑

### 6.11 Lint 输出位置

建议写入：

- `03_outputs/lint-reports/`
- 或 `99_runtime/traces/`

高价值问题再提炼回：

- `02_wiki/plans/`
- `02_wiki/members/` 中的待处理事项

### 6.13 固定验收场景

在进入实现阶段前，至少应定义以下端到端验收场景：

1. 重复 ingest
   - 同一资料重复上传，不应重复入库
2. 同日多份报告
   - 同一天两份不同报告，必须生成不同 source 身份
3. 提醒发送后确认
   - 正确命中 reminder 实例并更新状态
4. 提醒超时升级
   - 未确认时进入升级路径，不重复发相同实例
5. 冲突 source 触发 `needs_review`
   - 新旧来源冲突时创建 `review_item`
6. report 派生回写
   - output 生成后，仅在满足 promotion gate 时回写 wiki

每个场景都应定义：

- 输入 fixture
- 预期文件变化
- 预期状态变化
- 允许和禁止的回写
- 预期 `status`

### 6.12 总原则

原始资料不可篡改，长期知识谨慎沉淀，临时产物独立存放，高风险情况宁可保守。

---

## 7. 当前状态与后续

本文档已沉淀以下已确认内容：

- 系统边界与能力分层
- 目录结构与分层设计
- 四类内部能力工作流
- 核心页面 schema
- 输入输出契约
- 医疗安全边界、回写规则与 lint 机制

### 7.1 总体策略

v1 不追求一次做全，而是按“先把知识维护链路跑通，再加主动能力”的顺序推进。

优先级原则：

- 先做 `ingest -> wiki -> query`
- 再做 `report`
- 然后做 `reminder`
- 最后做 `lint / review / 验证闭环`

核心判断：

- 先把家庭健康知识库真的做成“可增长、可追溯、可恢复”的系统
- 再在这个基础上叠加主动提醒和周期性输出

### 7.2 分阶段落地

#### Phase 0：基础骨架

目标：

- 固定目录、schema、模板、事件契约和运行时实体

交付物：

- 根目录结构
- `AGENTS.md`
- `00_schema/` 初版
- 核心页面模板
- 事件 schema 文档
- runtime 实体定义
- 基础样例数据

退出标准：

- 能用一组样例文件初始化一个空的家庭健康 vault
- `python3 scripts/family_doctor/validate_phase0.py --target <vault>` passes on the canonical scaffold and a fresh bootstrapped copy
- schema 不再频繁改名、改目录

#### Phase 1：ingest MVP

目标：

- 把“新资料进入系统”做成可重复、可追溯、可恢复

首批支持输入：

- 体检报告
- 化验单
- 药盒 / 处方
- 手工症状文本

交付物：

- `ingest_job` 工作流
- `sources/` 页面生成
- `members / medications / plans / trends` 的最小增量更新
- 冲突检测
- `needs_review` 与 `review_item`

退出标准：

- 同一资料不会重复入库
- 成员识别低置信时会阻断
- source 与 wiki 的关系可追溯

#### Phase 2：query MVP

目标：

- 让 skill 能稳定回答“围绕 wiki 的问题”

首批支持问题：

- 某成员当前用药
- 最近指标趋势
- 新报告主要异常项
- 就医前准备摘要

交付物：

- query 路由
- 页面读取优先级
- `qa-summaries/` 生成规则
- promotion gate 初版

退出标准：

- 回答能引用具体 source
- 没有 source 的判断不能升级为长期知识
- 高风险问题会触发安全边界

#### Phase 3：report MVP

目标：

- 把“新报告摘要”和“周期性总结”做成标准产物

v1 只做 4 类：

- 新体检报告摘要
- 新化验单摘要
- 周生活方式报告
- 月综合健康报告

交付物：

- `report_job`
- `03_outputs/` 成品模板
- evidence refs
- report 到 wiki 的受控回写

退出标准：

- 报告是可发送成品
- 关键结论有证据锚点
- promotion gate 生效

#### Phase 4：reminder MVP

目标：

- 把提醒做成“安全的记录与通知系统”，而不是补服建议系统

v1 只支持：

- 定时提醒生成
- 用户确认
- 超时升级
- 依从性摘要

交付物：

- `reminder_instance`
- `confirm / escalate` 事件
- medication reconciliation 约束
- 漏服安全禁令

退出标准：

- 能正确匹配确认到某次提醒实例
- 不重复发同一提醒
- 默认不输出补服方案

#### Phase 5：lint 与验证闭环

目标：

- 让系统具备长期维护能力

交付物：

- 结构 lint
- 知识 lint
- 运行 lint
- 固定验收场景
- 最小可运行样例

退出标准：

- 至少覆盖已定义的 6 个固定验收场景
- 能发现 orphan page、冲突事实、过期计划、重复入库嫌疑

### 7.3 v1 范围控制

v1 必做：

- 体检 / 化验 / 药物 ingest
- 成员页与 source 页维护
- 基于 wiki 的 query
- 新报告摘要与周 / 月报告
- 提醒生成、确认、升级
- review item、promotion gate、lint

v1 不做：

- 即时通讯接入实现
- 自动设备同步
- 向量检索基础设施
- 复杂权限系统
- 真正医疗分诊产品化
- 多家庭 SaaS 化

### 7.4 未来扩展性与兼容性原则

为了确保当前 v1 不是一次性 demo，而是后续可以持续长大的系统，扩展性原则应正式写入方案。

#### Schema Versioning

- page schema、event schema、runtime schema 都应带版本号
- 未来扩展字段时优先追加，不轻易破坏旧结构

#### Backward Compatibility

- 新版本优先兼容旧页面
- 如必须变更结构，应通过迁移脚本或显式 upgrade 流程处理
- 不允许隐式破坏旧数据

#### Rule Pack Modularization

- 儿科
- 妊娠 / 产后
- 老年
- 多药联用

这些规则应逐步抽成独立规则包，而不是在通用 prompt 中继续堆叠条件分支

#### Capability Registry

未来如新增：

- `health-triage`
- `health-sync`
- `health-caregiver`
- `health-export`

都应显式注册到能力表中，而不是只靠文档约定

#### Stable Core, Replaceable Edge

- 宿主系统可替换
- OCR 方案可替换
- LLM 提供方可替换
- 提醒发送方式可替换

但核心 wiki 结构应尽量稳定

#### Evidence-First Evolution

- 未来新增任何自动化能力，都不能绕过 source 与 evidence refs
- 越是主动化的能力，越要保留证据链和 review 入口

### 7.5 推荐开发顺序

如果项目正式进入开发，我建议严格按下面顺序推进：

1. 先完成 `Phase 0`
2. 再做 `ingest MVP`
3. 接着做 `query MVP`
4. 然后做 `report MVP`
5. 再做 `reminder MVP`
6. 最后补 `lint + 验证闭环`

原因：

- 如果 `ingest` 和 `source -> wiki` 没做好，后面的报告和提醒都会建立在不稳的数据上
- 如果没有 promotion gate 和 review item，越早自动化，污染知识库的风险越大

### 7.6 继续展开的内容

本阶段完成后，后续仍需继续产出：

- 正式 implementation plan
- 具体 skill 文件结构与模板
- 最小可运行样例
- 端到端验证流程
