# Family Doctor 项目交接与恢复文档

更新时间：`2026-04-20`  
适用对象：后续接手的 AI agent、开发者、其他平台执行环境

## 1. 项目是什么

这个项目的目标，是把 `ai-health-vault` 从“模板 + Prompt starter kit”升级成一个由 `LLM Wiki` 驱动的家庭健康管理系统。

当前已经明确的产品方向：

- 外部只有一个 skill 入口：`family-doctor`
- skill 内部按 4 类能力拆分：
  - `health-ingest`
  - `health-query`
  - `health-report`
  - `health-reminder`
- 核心不是单次问答，而是维护一套长期演化的家庭健康 wiki

当前实现阶段：

- 设计文档已完成并多轮评审
- `Phase 0 foundation` 已完成
- `Phase 1 ingest MVP` 还未开始

## 2. 当前工作区结构

当前工作区根目录：

- `/Users/loutussun/Documents/codex/AIHealth`

主要内容分成两块：

- 历史参考项目：
  - `/Users/loutussun/Documents/codex/AIHealth/ai-health-vault`
- 当前 family-doctor 新项目资产：
  - `/Users/loutussun/Documents/codex/AIHealth/family-health`
  - `/Users/loutussun/Documents/codex/AIHealth/scripts/family_doctor`
  - `/Users/loutussun/Documents/codex/AIHealth/tests/family_doctor`
  - `/Users/loutussun/Documents/codex/AIHealth/docs/superpowers`

重要说明：

- 工作区根目录 **不是 git repo**
- `ai-health-vault/` 自己是一个独立 git repo，仅作为参考来源
- 当前 `family-doctor` Phase 0 工作没有 commit 历史可依赖，恢复时请以本文档和 `docs/superpowers/` 下的文档为准

## 3. 必读文档

接手时建议按下面顺序阅读：

1. 设计总文档  
   `/Users/loutussun/Documents/codex/AIHealth/docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md`
2. Phase 0 实施计划  
   `/Users/loutussun/Documents/codex/AIHealth/docs/superpowers/plans/2026-04-19-family-doctor-phase0-foundation.md`
3. 当前交接文档  
   `/Users/loutussun/Documents/codex/AIHealth/docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md`

如果需要追溯 spec / plan 的历史版本，可查看：

- `/Users/loutussun/Documents/codex/AIHealth/docs/superpowers/specs/*.backup.md`
- `/Users/loutussun/Documents/codex/AIHealth/docs/superpowers/plans/*.backup.md`
- `/Users/loutussun/Documents/codex/AIHealth/docs/superpowers/backups/`

## 4. 已完成内容

### 4.1 设计层

已完成并固化：

- skill 单入口模型
- `01_raw / 02_wiki / 03_outputs / 99_runtime` 四层结构
- 事件驱动输入输出契约
- 页面 schema
- 医疗安全边界
- 回写规则
- lint 思路
- v1 分阶段落地方案

### 4.2 Phase 0 基础设施

已完成文件：

- `pyproject.toml`
- `family-health/` canonical scaffold
- `scripts/family_doctor/bootstrap_vault.py`
- `scripts/family_doctor/validate_phase0.py`
- `tests/family_doctor/conftest.py`
- `tests/family_doctor/test_bootstrap_vault.py`
- `tests/family_doctor/test_validate_phase0.py`

### 4.3 canonical scaffold

已建立 canonical vault：

- `/Users/loutussun/Documents/codex/AIHealth/family-health`

其职责：

- 作为 `Phase 0` 的唯一 canonical 资产源
- 后续通过 `bootstrap_vault.py` 复制到任意目标目录
- 由 `validate_phase0.py` 做结构与契约校验

当前已覆盖的 canonical 内容包括：

- 核心 Markdown 资产：
  - `AGENTS.md`
  - `index.md`
  - `log.md`
  - `00_schema/members.md`
  - `00_schema/reporting-rules.md`
  - `00_schema/reminder-rules.md`
- 结构化契约：
  - `00_schema/event-schema.json`
  - `00_schema/runtime-entities.json`
- 页面模板：
  - `member/source/medication/condition/trend/plan/output/reminder`
- 目录骨架：
  - `01_raw`
  - `02_wiki`
  - `03_outputs`
  - `99_runtime`
- 示例输入：
  - `examples/sample-input-event.json`

## 5. 当前验证状态

截至 `2026-04-20`，Phase 0 已通过以下验证：

### 5.1 canonical scaffold 校验

命令：

```bash
python3 scripts/family_doctor/validate_phase0.py --target /Users/loutussun/Documents/codex/AIHealth/family-health
```

结果：

```text
Phase 0 validation passed: /Users/loutussun/Documents/codex/AIHealth/family-health
```

### 5.2 fresh bootstrap copy 校验

验证方式：

1. 使用 `bootstrap_vault.py` 复制到临时目录
2. 对 fresh copy 再执行 `validate_phase0.py`

最近一次通过的 fresh copy：

- `/private/tmp/family-health-phase0-final.RUUxL6`

结果：

```text
Phase 0 validation passed: /private/tmp/family-health-phase0-final.RUUxL6
```

### 5.3 测试状态

命令：

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest tests/family_doctor -q
```

结果：

```text
24 passed in 1.81s
```

### 5.4 当前 validator 已锁住的关键基线

`validate_phase0.py` 当前已经会拦截以下 drift：

- 缺失关键目录
- 缺失核心 Markdown 资产
- 核心 Markdown marker 漂移
- 页面模板缺失或 marker 漂移
- `event-schema.json` 顶层 contract 漂移
- `actor / target / payload / runtime / context / attachment` property shape 漂移
- `sample-input-event.json` 与 contract 不兼容
- `context` 出现未声明字段
- attachment shape 弱化或扩展 drift
- runtime registry 缺关键字段

## 6. 当前代码入口

### 6.1 Bootstrap CLI

文件：

- `/Users/loutussun/Documents/codex/AIHealth/scripts/family_doctor/bootstrap_vault.py`

作用：

- 把 canonical `family-health/` scaffold 复制到任意目标目录
- 支持幂等复制
- 拒绝把目标放在 canonical root 内部

### 6.2 Validator CLI

文件：

- `/Users/loutussun/Documents/codex/AIHealth/scripts/family_doctor/validate_phase0.py`

作用：

- 校验 Phase 0 scaffold 的目录、Markdown 资产、模板、event contract、runtime contract 和 sample event compatibility

### 6.3 测试入口

文件：

- `/Users/loutussun/Documents/codex/AIHealth/tests/family_doctor/test_bootstrap_vault.py`
- `/Users/loutussun/Documents/codex/AIHealth/tests/family_doctor/test_validate_phase0.py`

## 7. 环境与执行注意事项

### 7.1 Python / pytest

当前环境里默认没有直接可用的 `pytest` 命令，因此测试统一使用：

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest ...
```

不要直接假设 `pytest` 在 PATH 中可用。

### 7.2 Git

当前根目录不是 git repo，所以：

- 不能把“缺少 git diff / commit”当成阻塞问题
- 交接、恢复、回溯主要依靠 `docs/superpowers/` 下的文档与备份

### 7.3 不要误判 fresh copy 校验失败

曾经出现过一次“bootstrap 和 validate 并行跑，导致 validate 读到了未复制完成目录”的误报。  
恢复或自动化时，务必保证：

1. `bootstrap_vault.py` 完全结束
2. 再执行 `validate_phase0.py`

不要把这两步并行。

## 8. 如果异常中断，如何恢复

如果后续对话、平台或 agent 异常中断，建议按下面流程恢复：

1. 确认工作区位置：

```bash
cd /Users/loutussun/Documents/codex/AIHealth
```

2. 先读文档：

- `docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md`
- `docs/superpowers/plans/2026-04-19-family-doctor-phase0-foundation.md`
- `docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md`

3. 校验 canonical 基线：

```bash
python3 scripts/family_doctor/validate_phase0.py --target /Users/loutussun/Documents/codex/AIHealth/family-health
```

4. 跑测试：

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest tests/family_doctor -q
```

5. 如果以上都通过，则说明 `Phase 0` 仍然健康，可以继续进入下一阶段。

## 9. 下一步应该做什么

下一阶段应进入：

- `Phase 1: ingest MVP`

推荐顺序：

1. 基于 spec 和 plan，再写一份 `Phase 1 ingest MVP` implementation plan
2. 明确第一批支持输入：
   - 体检报告
   - 化验单
   - 药盒 / 处方
   - 手工症状文本
3. 优先实现：
   - `ingest_job`
   - `sources/` 页面生成
   - `members / plans / medications / trends` 的最小增量更新
   - `needs_review / review_item`
4. 继续沿用：
   - subagent-driven-development
   - 每个 task 后做 spec review + quality review

## 10. 当前未完成内容

以下仍未开始，属于后续阶段：

- ingest 业务逻辑
- query 业务逻辑
- report 业务逻辑
- reminder 业务逻辑
- OCR 接入
- IM 接入
- scheduler 接入
- LLM provider 集成

## 11. 当前非阻塞改进项

这些不是当前阻塞问题，但后续可以补：

- 增加 `payload property schema drift` 的对称测试
- 增加“核心 Markdown marker drift”的显式测试，不只测缺文件
- 让 `bootstrap_vault.py` 更明确跳过未来可能出现的隐藏杂项文件

## 12. 一句话状态结论

当前项目已经完成：

- 设计文档
- Phase 0 foundation
- canonical scaffold
- bootstrap / validate 工具链
- 24 条测试基线

可以安全进入 `Phase 1 ingest MVP`，并且已经具备较好的断线恢复与跨人交接基础。
