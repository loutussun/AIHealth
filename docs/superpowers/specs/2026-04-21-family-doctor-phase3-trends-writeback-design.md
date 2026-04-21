# Family Doctor Phase 3 Trends / Writeback Design

## 1. 目标

Phase 3 的核心目标不是新增更多输入渠道，而是让 `family-doctor` 第一次具备“长期健康认知生长能力”。

在本阶段结束后，系统应当不仅能：

- ingest
- query
- report
- reminder

还应当能够：

- 形成稳定的趋势页
- 沉淀长期有效结论
- 将高价值输出受控回写到 wiki

换句话说，Phase 3 的重点是让系统从“会处理事件”升级到“会积累长期认知”。

## 2. 范围

本阶段首批趋势主题固定为 5 类：

- 血压
- 血脂
- 血糖
- 睡眠
- 体重

默认采用以下策略：

- 页面维度：`成员 + 主题`
- 主时间窗口：最近 `12 个月`
- 辅助观察窗口：最近 `4 周 / 3 个月`
- 回写策略：保守回写

保守回写的定义是：

- 只有长期有效、证据明确、无冲突的结论才允许写回 `02_wiki/`
- 其余内容继续停留在 `02_wiki/trends/`、`03_outputs/` 或 `待核实项`

## 3. 页面模型

Phase 3 新的中间知识层位于：

- `02_wiki/trends/`

建议页面命名为：

- `dad-blood-pressure.md`
- `dad-lipids.md`
- `dad-glucose.md`
- `dad-sleep.md`
- `dad-weight.md`

其他成员同理。

页面职责划分如下：

- `02_wiki/trends/`
  - 负责长期观察、趋势分析、候选结论
- `02_wiki/members/`
  - 只接收长期摘要
- `02_wiki/plans/`
  - 只接收后续动作与跟进项
- `03_outputs/`
  - 继续承载某次报告或某次问答的成品

### 趋势页 schema

示例：`dad-weight.md`

```md
---
type: trend
trend_id: dad_weight
member_id: dad
topic: weight
window_primary: 12_months
window_secondary: [4_weeks, 3_months]
tags: [trend]
---

# 爸爸：体重趋势

> 摘要：过去 12 个月体重整体小幅上升，最近 4 周相对稳定。

## 覆盖时间范围
## 关键观测点
## 趋势判断
## 短期波动
## 可能相关因素
## 关联资料
## 可提炼结论
## 待核实项
```

各 section 职责：

- `覆盖时间范围`
  - 明确使用了哪些日期范围
- `关键观测点`
  - 列出最关键的原始数据点或阶段点
- `趋势判断`
  - 只写长期判断
- `短期波动`
  - 记录最近 4 周 / 3 个月内的变化
- `可能相关因素`
  - 仅写“可能有关”，不写确定因果
- `关联资料`
  - 指向 `sources / outputs / plans`
- `可提炼结论`
  - 作为 writeback gate 的候选输入
- `待核实项`
  - 记录冲突、缺值、低置信判断

## 4. Writeback Gate

Phase 3 的关键护栏是 `writeback gate`。

一个结论只有同时满足以下 5 条时，才允许从 `trends / outputs` 回写到 `02_wiki/members/` 或 `02_wiki/plans/`：

1. 长期有效
   - 不是一次性波动
   - 不是只对单次报告成立的措辞
2. 证据明确
   - 能追溯到 `source_id / date / metric`
3. 无冲突
   - 当前 wiki 中不存在未解决的相反证据
4. 语义稳定
   - 适合作为长期档案摘要或计划项
5. 不越过医疗边界
   - 不升级成诊断
   - 不变成停药、换药、处方决策

允许回写的目标主要有两类：

- 回写到 `members/`
  - 长期摘要
- 回写到 `plans/`
  - 后续动作与观察项

不允许直接回写的内容：

- 单次异常值的扩大解释
- 临时鼓励话术
- 不确定因果关系
- 用药调整建议
- 诊断式措辞
- 无来源判断

## 5. 工作流设计

Phase 3 新增 3 条核心工作流：

- `trend build`
- `report consume`
- `controlled writeback`

它们构成一条链路：

`source / existing wiki -> trend page -> output -> gated writeback`

### trend build

触发时机：

- 新资料 ingest 后
- 周报 / 月报生成前

处理步骤：

1. 识别成员与主题
2. 收集相关 `sources / outputs / members / plans`
3. 按窗口整理数据
4. 更新对应 `02_wiki/trends/<member>-<topic>.md`
5. 生成：
   - `关键观测点`
   - `趋势判断`
   - `短期波动`
   - `可提炼结论`
   - `待核实项`

### report consume

Phase 3 后，report 不再优先从零拼装，而是优先消费趋势页。

建议 report 读取顺序调整为：

1. `members`
2. `plans`
3. `trends`
4. `sources`
5. `outputs`

### controlled writeback

触发点：

- 趋势页更新后产生新的候选结论
- 某次 report 产物中出现稳定、可沉淀的长期结论

处理步骤：

1. 收集候选结论
2. 逐条经过 `writeback gate`
3. 决定写回位置：
   - 长期摘要 -> `members`
   - 后续动作 -> `plans`
4. 写入时附带来源和更新时间
5. 未通过 gate 的内容留在 `trends / outputs / 待核实项`

## 6. 目录与代码变更范围

本阶段尽量少扩目录，重点强化已有结构。

### 主要目录

- `02_wiki/trends/`
  - Phase 3 核心目录
- `02_wiki/members/`
  - 接收受控回写的长期摘要
- `02_wiki/plans/`
  - 接收受控回写的动作项
- `03_outputs/`
  - report 继续输出成品，但读取优先消费 trends
- `99_runtime/`
  - 如有必要，记录 `trend_build_job` 或对应运行时状态

### 建议新增代码文件

- `family_doctor/trend_pipeline.py`
- `family_doctor/trend_context.py`
- `family_doctor/trend_pages.py`
- `family_doctor/writeback_gate.py`
- `tests/family_doctor/test_trend_pipeline.py`
- `tests/family_doctor/test_trend_pages.py`
- `tests/family_doctor/test_writeback_gate.py`

### 建议修改代码文件

- `family_doctor/query_pipeline.py`
  - 让 query 优先读取 trends
- `family_doctor/report_pipeline.py`
  - 让 report 优先消费 trends
- `family_doctor/runtime_records.py`
  - 如需要，增加 trend/writeback runtime record
- `family_doctor/markdown_utils.py`
  - 如需要，补趋势页稳定更新辅助函数

### 尽量不动的部分

- `family_doctor/ingest_pipeline.py`
  - 除非为了 ingest 后触发 trend build
- `family_doctor/reminder_pipeline.py`
  - 本阶段不主动扩 reminder 能力
- 仓库目录结构本身
  - 避免为了趋势层引入过多新目录

## 7. 测试策略

Phase 3 应重点覆盖 4 类测试：

### 1. trend pipeline tests

验证：

- 能按成员 + 主题构建趋势页
- 能正确聚合 12 个月主窗口
- 能补 4 周 / 3 个月短期摘要
- 没有数据时不会伪造趋势
- 主题不相关资料不会混入

### 2. trend page contract tests

验证：

- frontmatter 完整
- 固定 section 全部存在
- section 顺序稳定
- 页面路径总在 `02_wiki/trends/` 内

### 3. writeback gate tests

重点验证“**不该写的时候真的不会写**”：

- 长期有效 + 证据明确 + 无冲突 -> 允许回写
- 单次波动 -> 不允许回写
- 缺来源 -> 不允许回写
- 有冲突 -> 进入 `待核实项`
- 超出医疗边界 -> 不允许回写

### 4. integration / regression tests

验证：

- query 开始优先读取 trends
- report 开始优先消费 trends
- members/plans 只接收到 gated 内容
- 既有 ingest / query / report / reminder 回归不坏

## 8. 验收标准

Phase 3 的 exit criteria 建议为：

1. 能为 5 个主题生成 `成员 + 主题` 趋势页
2. 趋势页默认主窗口为最近 `12 个月`
3. 趋势页包含最近 `4 周 / 3 个月` 的短期摘要
4. query 能优先读取 trends
5. report 能优先读取 trends
6. `writeback gate` 能阻止不安全或不稳定结论写回
7. `members / plans` 只接收受控摘要或行动项
8. family_doctor 全量回归保持通过

建议固定 5 个验收场景：

1. 新血压资料进入后，更新 `dad-blood-pressure.md`
2. 新体重资料进入后，只形成短期波动，不写回成员页
3. 血脂趋势达到稳定结论后，允许写回 `members`
4. 睡眠数据证据不足时，只更新 trends，不写回 `plans`
5. query/report 在有 trends 时优先读取 trends，而不是重新从零拼装

## 9. 推荐实施顺序

建议顺序如下：

1. `trend page contract`
2. `trend pipeline`
3. `writeback gate`
4. `query` 接入 trends
5. `report` 接入 trends
6. regression 与文档收尾

原因：

- 没有稳定趋势页 contract，后续 query/report 容易反复调整
- 没有 writeback gate，members/plans 很容易被趋势分析污染
- 先稳中间层，再接消费方，返工最少

## 10. 任务拆分建议

### Task 1：冻结 trend page contract

输出：

- `test_trend_pages.py`
- `trend_pages.py` 最小模板骨架

### Task 2：实现 trend pipeline MVP

输出：

- `trend_context.py`
- `trend_pipeline.py`
- `test_trend_pipeline.py`

### Task 3：实现 writeback gate

输出：

- `writeback_gate.py`
- `test_writeback_gate.py`

### Task 4：接入 members / plans 受控回写

输出：

- trend -> member / plan 集成测试
- 小范围修改现有 wiki update 逻辑

### Task 5：让 query 优先消费 trends

输出：

- `query_pipeline.py` 调整
- query regression tests

### Task 6：让 report 优先消费 trends

输出：

- `report_pipeline.py` 调整
- report regression tests

### Task 7：全量回归与文档收尾

输出：

- 新 handoff
- 新 snapshot
- 如需要，新的 phase completion 文档

## 11. 推荐执行模式

建议继续沿用当前已经确认的协作方式：

- 主线程
  - 控任务顺序
  - 控边界
  - 控验收
  - 控 PR / merge / handoff
- subagent
  - 单 task 实现
  - 单 task review
  - CI / regression / comment triage

## 12. 一句话总结

Phase 3 的核心不是“再加几个功能”，而是：

**让 trend page 成为 query / report / writeback 的稳定中间知识层。**
