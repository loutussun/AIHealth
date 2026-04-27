---
type: index
scope: family-health
---

# 家庭健康中心

这是给 LLM 和维护者看的导航索引。给家庭成员直接阅读的入口是 [[家庭健康管理中心]]。

## 人类入口

- [[家庭健康管理中心]]
- 最近可发送给家人的摘要：`03_outputs/family-messages/`
- 就医准备材料：`03_outputs/visit-briefs/`

## 成员

- 成员档案：`02_wiki/members/`
- 成员注册规则：`00_schema/members.md`
- 低置信度成员识别必须进入人工复核。

## 原始资料

- 体检报告：`01_raw/reports/`
- 化验资料：`01_raw/labs/`
- 用药资料：`01_raw/medications/`
- 饮食记录：`01_raw/diets/`
- 运动记录：`01_raw/exercise/`
- 睡眠记录：`01_raw/sleep/`
- 就医记录：`01_raw/visits/`
- 附件：`01_raw/attachments/`

## Wiki 页面

- 来源摘要：`02_wiki/sources/`
- 健康问题：`02_wiki/conditions/`
- 用药知识：`02_wiki/medications/`
- 时间线：`02_wiki/timelines/`
- 趋势页：`02_wiki/trends/`
- 计划页：`02_wiki/plans/`

## 输出

- 体检更新：`03_outputs/checkup-updates/`
- 化验更新：`03_outputs/lab-updates/`
- 就医准备：`03_outputs/visit-briefs/`
- 家庭沟通：`03_outputs/family-messages/`
- 周报：`03_outputs/weekly-reports/`
- 月报：`03_outputs/monthly-reports/`
- 提醒文案：`03_outputs/reminder-messages/`
- QA 摘要：`03_outputs/qa-summaries/`

## Tracking CSV

- 体检指标：`04_tracking/体检指标.csv`
- 用药打卡：`04_tracking/用药打卡.csv`
- 饮食记录：`04_tracking/饮食记录.csv`
- 运动记录：`04_tracking/运动记录.csv`
- 睡眠记录：`04_tracking/睡眠记录.csv`

## Runtime

- `99_runtime/`: 运行过程状态
- `99_runtime/jobs/`: 作业记录
- `99_runtime/state/`: 幂等、复核和去重状态
- `99_runtime/traces/`: 调试追踪
