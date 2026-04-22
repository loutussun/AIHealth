# AIHealth 项目执行协作约定

> 本文档用于固定 AIHealth 的默认执行方式，减少主线程判断漂移。

## 目的

适用范围：

- `family-doctor` 相关设计、实现、测试、review、CI、handoff
- 后续阶段规划与执行

## 核心原则

默认采用：

- 主线程负责总控、边界、验收、集成、文档状态
- subagent 负责局部实现、专项排查、局部 review、测试补齐

## 主线程职责

主线程默认负责：

1. 维护当前阶段目标
2. 维护架构边界和安全边界
3. 决定任务拆分与优先级
4. 指派 subagent 的任务范围与写入边界
5. 审核 subagent 返回结果
6. 做最终实现取舍与集成
7. 跑最终验证并给出阶段结论
8. 维护关键文档、handoff 状态

## Subagent 适用场景

以下任务默认优先交给 subagent：

1. 独立代码实现
2. 定点测试补齐
3. 局部 review thread 核对与修复
4. 某个 CI/job 的失败原因调查
5. 局部文档整理
6. 局部重构
7. 只读型代码审查

## Subagent 返回格式

subagent 返回内容至少包含：

1. 做了什么
2. 改了哪些文件
3. 跑了什么验证
4. 结果如何
5. 还剩什么风险或未解决项

## 默认执行顺序

1. 主线程确认目标与边界
2. 主线程拆 task
3. subagent 执行局部任务
4. 主线程收敛结果
5. 主线程做 review / integration
6. 主线程跑最终验证
7. 主线程更新文档、handoff

## 当前项目默认策略

对 AIHealth 项目，后续默认采用：

- 规划：主线程主导
- 实现：尽量 subagent 化
- review triage：尽量 subagent 化
- CI 排查：尽量 subagent 化
- 最终验收：主线程负责
- handoff：主线程负责
