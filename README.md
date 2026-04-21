# AIHealth

一个基于 `LLM Wiki` 方法构建的家庭健康管理项目。

当前仓库的目标，不是做一个单次问答机器人，而是逐步构建一套可持续维护的家庭健康知识系统：

- `family-doctor` 作为唯一外部 skill 入口
- `family-health/` 作为 canonical 家庭健康 wiki 骨架
- `scripts/family_doctor/` 提供 bootstrap 和 validation 工具链
- `docs/superpowers/` 保存设计、计划、交接和恢复文档

## 当前状态

当前已完成：

- 核心设计文档
- `Phase 0 foundation`
- canonical `family-health/` scaffold
- `bootstrap_vault.py`
- `validate_phase0.py`
- Phase 0 自动化测试基线
- Git / GitHub 基线与 `Phase 0 CI`
- `Phase 1 ingest MVP`
- `Phase 2 query / report / reminder` 核心实现
- `Phase 2 thin CLI`
- `Phase 2` family_doctor 回归套件

当前进行中：

- `Phase 3` 设计与 planning 准备

当前尚未开始：

- OCR、即时通讯接入、调度器接入
- `Phase 3` 代码实现
- advanced reminder rules

## 核心目录

```text
AIHealth/
├── docs/superpowers/
│   ├── specs/
│   ├── plans/
│   ├── handoffs/
│   └── backups/
├── family-health/
├── scripts/family_doctor/
├── tests/family_doctor/
└── ai-health-vault/   # 外部参考仓，当前主仓已排除版本管理
```

## 必读文档

- 设计总文档：
  [2026-04-19-family-doctor-skill-design.md](docs/superpowers/specs/2026-04-19-family-doctor-skill-design.md)
- Agent 执行协作通用约定：
  [2026-04-21-agent-execution-collaboration-agreement.md](docs/superpowers/specs/2026-04-21-agent-execution-collaboration-agreement.md)
- 项目执行协作约定：
  [2026-04-21-project-execution-collaboration-agreement.md](docs/superpowers/specs/2026-04-21-project-execution-collaboration-agreement.md)
- Phase 3 设计稿：
  [2026-04-21-family-doctor-phase3-trends-writeback-design.md](docs/superpowers/specs/2026-04-21-family-doctor-phase3-trends-writeback-design.md)
- Phase 0 实施计划：
  [2026-04-19-family-doctor-phase0-foundation.md](docs/superpowers/plans/2026-04-19-family-doctor-phase0-foundation.md)
- 当前交接文档：
  [2026-04-20-family-doctor-project-handoff.md](docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md)
- Phase 1 完成说明：
  [2026-04-21-family-doctor-phase1-ingest-completion.md](docs/superpowers/handoffs/2026-04-21-family-doctor-phase1-ingest-completion.md)
- Phase 2 完成说明：
  [2026-04-21-family-doctor-phase2-query-report-reminder-completion.md](docs/superpowers/handoffs/2026-04-21-family-doctor-phase2-query-report-reminder-completion.md)
- 当前最新快照：
  [2026-04-21-family-doctor-project-snapshot-phase2.md](docs/superpowers/handoffs/2026-04-21-family-doctor-project-snapshot-phase2.md)
- 之前的 Phase 1 快照：
  [2026-04-21-family-doctor-project-snapshot.md](docs/superpowers/handoffs/2026-04-21-family-doctor-project-snapshot.md)
- 上一版快照：
  [2026-04-20-family-doctor-project-snapshot.md](docs/superpowers/handoffs/2026-04-20-family-doctor-project-snapshot.md)
- 下一阶段 planning：
  [2026-04-21-family-doctor-phase2-query-report-reminder.md](docs/superpowers/plans/2026-04-21-family-doctor-phase2-query-report-reminder.md)

## 本地验证

### 1. 校验 canonical scaffold

```bash
python3 scripts/family_doctor/validate_phase0.py --target /Users/loutussun/Documents/codex/AIHealth/family-health
```

### 2. 运行当前 family_doctor 回归套件

当前环境默认没有可直接调用的 `pytest` 命令，统一使用：

```bash
PYTHONPATH=. uv run pytest \
  tests/family_doctor/test_query_pipeline.py \
  tests/family_doctor/test_query_contract.py \
  tests/family_doctor/test_report_pipeline.py \
  tests/family_doctor/test_report_outputs.py \
  tests/family_doctor/test_reminder_pipeline.py \
  tests/family_doctor/test_reminder_runtime.py \
  tests/family_doctor/test_query_cli.py \
  tests/family_doctor/test_report_cli.py \
  tests/family_doctor/test_reminder_cli.py \
  tests/family_doctor/test_run_ingest_cli.py \
  tests/family_doctor/test_ingest_acceptance.py \
  tests/family_doctor/test_wiki_updates.py \
  tests/family_doctor/test_source_pages.py \
  tests/family_doctor/test_ingest_pipeline.py \
  tests/family_doctor/test_output_contract.py \
  tests/family_doctor/test_phase1_regression_smoke.py -q
```

## Bootstrap 新 vault

将 canonical `family-health/` scaffold 复制到任意目录：

```bash
python3 scripts/family_doctor/bootstrap_vault.py --target /tmp/family-health-demo
python3 scripts/family_doctor/validate_phase0.py --target /tmp/family-health-demo
```

## GitHub 基线

当前仓库已补齐最小基础设施：

- 根目录 `README.md`
- Phase 0 CI：
  - `.github/workflows/phase0-ci.yml`
- 协作模板：
  - `.github/ISSUE_TEMPLATE/bug_report.md`
  - `.github/pull_request_template.md`

## 下一步

当前最推荐的直接下一步：

1. 基于 `Phase 3` 设计稿生成 implementation plan
2. 按 `trend page contract -> trend pipeline -> writeback gate` 顺序推进实现
3. 在趋势层稳定后，再接 `query / report` 的 trends 消费逻辑
