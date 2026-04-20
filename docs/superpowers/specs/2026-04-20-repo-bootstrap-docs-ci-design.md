# 仓库基础工程化设计

更新时间：`2026-04-20`

## 目标

为 `AIHealth` 仓库补齐最小但高收益的 GitHub 基础设施，提升后续开发、协作和恢复效率。

本轮范围只包含：

- 根目录 `README.md`
- `push / pull_request` 触发的 Phase 0 CI
- 基础协作模板

## 设计决策

### 1. README

根目录 `README.md` 负责回答 4 个问题：

- 这个仓库是什么
- 当前做到了哪一步
- 关键目录和文档在哪里
- 如何验证和继续开发

README 不重复复制完整 spec，只做导航与快速上手。

### 2. CI

新增 `.github/workflows/phase0-ci.yml`，只做当前仓库已经稳定具备的检查：

- `python3 scripts/family_doctor/validate_phase0.py --target family-health`
- `PYTHONPATH=/tmp/codex_pytest python3 -m pytest tests/family_doctor -q`

CI 使用 GitHub Actions 官方 Python setup，不引入额外复杂依赖。

### 3. 协作模板

本轮只补最基础的两个入口：

- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/pull_request_template.md`

目标是降低未来协作时的信息缺失，不做复杂流程化配置。

## 非目标

本轮不做：

- Dependabot
- CODEOWNERS
- Release 流程
- 多环境矩阵测试
- 自动发布文档

## 验证标准

完成后应满足：

- README 能引导新接手者快速定位 spec / plan / handoff
- 本地现有验证命令仍通过
- CI 工作流与本地验证命令保持一致
