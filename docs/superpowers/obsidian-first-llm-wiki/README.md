# Family Doctor Obsidian-first LLM Wiki

这个目录集中保存 `family-doctor` 回到 Obsidian-first 产品形态后的设计、计划、验收和交接文档。

## 当前文档

- [design.md](./design.md)：回正后的产品与架构设计
- [phase-a-vault-contract-plan.md](./phase-a-vault-contract-plan.md)：阶段 A 实施计划，聚焦 Obsidian-first vault contract
- [phase-b-workflow-contract-design.md](./phase-b-workflow-contract-design.md)：阶段 B 设计，聚焦 skill/prompt workflow contract
- [phase-b-workflow-contract-plan.md](./phase-b-workflow-contract-plan.md)：阶段 B 实施计划，聚焦 skill/prompt workflow contract 落地

## 当前主线

`family-health/` 是产品中心，`family-doctor` 是维护这个 vault 的 LLM wiki 操作员，Python 代码只承担确定性机械工具职责。

## 阶段状态

- Phase A: complete
- Phase B: complete

## 分支与目录约定

- `origin/main` / `6975fae`：当前干净基线，包含 `family-doctor` skill wrapper。
- `codex/obsidian-first-vault-contract`：Obsidian-first Phase A/B 实施分支，已完成 vault contract 与 skill/prompt workflow contract。
- `codex/phase3-trends-writeback`：历史 Phase 3 trends 候选区，不作为当前主线。
- `/Users/loutussun/Documents/codex/AIHealth`：当前原工作区，保留候选和历史上下文，不继续叠加 Phase A 实现。
- `/Users/loutussun/.config/superpowers/worktrees/AIHealth/obsidian-first-vault-contract`：Phase A/B 干净工作区。

清理原则：

- 不在原工作区直接 reset 或删除候选文件。
- Obsidian-first 回正的所有实现和验证先在干净 worktree 完成。
- Phase 3 趋势能力后续如需接回，必须在 Obsidian-first 设计下另立计划。
