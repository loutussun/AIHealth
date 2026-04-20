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

当前尚未开始：

- `Phase 1 ingest MVP`
- query / report / reminder 业务逻辑
- OCR、即时通讯接入、调度器接入

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
- Phase 0 实施计划：
  [2026-04-19-family-doctor-phase0-foundation.md](docs/superpowers/plans/2026-04-19-family-doctor-phase0-foundation.md)
- 当前交接文档：
  [2026-04-20-family-doctor-project-handoff.md](docs/superpowers/handoffs/2026-04-20-family-doctor-project-handoff.md)

## 本地验证

### 1. 校验 canonical scaffold

```bash
python3 scripts/family_doctor/validate_phase0.py --target /Users/loutussun/Documents/codex/AIHealth/family-health
```

### 2. 运行 Phase 0 测试

当前环境默认没有可直接调用的 `pytest` 命令，统一使用：

```bash
PYTHONPATH=/tmp/codex_pytest python3 -m pytest tests/family_doctor -q
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

下一阶段建议直接进入：

- `Phase 1: ingest MVP`

建议从下面几个点开始：

1. 为 `ingest MVP` 写 implementation plan
2. 先支持体检报告、化验单、药盒 / 处方、手工症状文本
3. 优先落 `sources/` 页面生成和最小增量更新链路
4. 延续当前 Phase 0 的验证和 review 节奏
