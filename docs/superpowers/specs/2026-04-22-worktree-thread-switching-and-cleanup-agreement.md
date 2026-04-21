# Worktree 线程切换与清理约定

## 目的

这份约定用于避免以下问题重复出现：

- Codex 线程绑定的工作目录被删除后，出现“当前工作目录缺失”
- feature 已合并，但线程仍停留在旧 worktree
- 清理 worktree 时误以为项目内容会丢失
- 新线程恢复时不知道该从哪个目录和哪份文档接续

这是一份短约定，不替代项目设计文档或实施计划。

## 核心原则

### 1. worktree 是阶段性执行目录，不是长期线程锚点

默认理解：

- 主仓长期目录：`/Users/loutussun/Documents/codex/AIHealth`
- worktree 目录：只服务于某个阶段、某个 PR、某组隔离任务

因此：

- 阶段开发时可以使用 worktree
- 阶段合并后，应优先回到主仓目录继续
- 不要把已完成阶段的 worktree 当作长期会话唯一工作目录

### 2. 清理 worktree 前，先确认线程迁移状态

如果一个聊天线程当前仍绑定某个 worktree，就不要直接删除该 worktree。

必须先确认下面三件事：

1. 当前线程后续是否还要继续使用
2. 关键改动是否已经进入正式仓库目录并完成 `git commit`
3. 是否已经准备好新线程接续入口

### 3. 项目安全依赖于“文档化 + 提交”，不是依赖某个线程

项目连续性依赖：

- 关键设计文档已落盘
- plan 已落盘
- snapshot / handoff 已更新
- 关键状态已 commit

只要这些成立：

- 关闭旧线程不会导致项目内容丢失
- 新开线程也能从仓库文档恢复上下文

## 标准流程

### 场景 A：阶段开发中

适用：

- 正在做某个 feature
- 需要隔离分支和目录

做法：

1. 在 worktree 中开发
2. 用 handoff / snapshot 持续记录当前状态
3. 把关键节点提交到 git

### 场景 B：PR 合并后继续长期推进项目

适用：

- feature 已合并
- 后面还会继续做下一阶段

做法：

1. 先同步主仓 `main`
2. 确认正式目录可用：
   - `/Users/loutussun/Documents/codex/AIHealth`
3. 后续新线程默认从主仓目录启动
4. 再清理旧 worktree 和开发分支

约定：

- 不在“即将删除的 worktree 所绑定的旧线程”里继续长期推进
- 新阶段如需隔离，再新建新的 worktree

### 场景 C：旧线程仍绑定已删除 worktree

症状：

- Codex 提示“当前工作目录缺失”

处理方式：

1. 不尝试在旧线程里继续修复该路径
2. 新开线程
3. 工作目录切到主仓：
   - `/Users/loutussun/Documents/codex/AIHealth`
4. 用最新 spec / plan / handoff 继续

## worktree 清理前检查清单

在删除 worktree 前，必须至少检查：

- [ ] 关键改动已 commit
- [ ] 需要保留的内容已进入正式仓库目录
- [ ] README 或 handoff 能指向当前阶段最新文档
- [ ] 如果后续还要继续推进，已经明确下一线程使用的目录
- [ ] 当前线程不再依赖即将删除的 worktree

## 新线程恢复模板

如果因为 worktree 被删而必须新开线程，默认使用：

```text
继续 AIHealth 当前阶段开发，项目目录是 /Users/loutussun/Documents/codex/AIHealth。
请先读取当前阶段的 spec、plan 和最新 handoff，再继续执行。
默认采用 Subagent-Driven。
```

## AIHealth 当前默认做法

对这个项目，默认执行方式固定为：

1. 阶段实现时可使用 worktree
2. 阶段合并后回到主仓目录继续
3. 新阶段开始时，再决定是否重新开 worktree
4. 不把已清理的 worktree 作为长期线程恢复目标

## 一句话结论

**worktree 用来隔离开发，主仓目录用来承接长期连续性。**
