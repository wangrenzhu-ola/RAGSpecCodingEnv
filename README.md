# OP-AI-WORKSPACE（OpenSkills + OpenSpec 标准化 AI 开发环境）

这是一套“可一键初始化”的 AI Coding 工作区标准，把两类能力组合在一起，让团队在成熟项目里也能稳定使用 AI 编程。

- **OpenSkills**：把可复用的“技能/操作规程”标准化成 `SKILL.md`，并同步到 `AGENTS.md`，让 AI 按需加载、可发现、可复用。
- **OpenSpec**：把需求/意图从聊天记录里“抽出来”，落在 `openspec/` 里做成可评审、可归档的规格与变更提案，减少跑偏与返工。

## 解决什么问题

- 需求在聊天里反复变更，AI 实现容易“漂移” → 用 OpenSpec 把 intent 锁定成规格/提案，先对齐再编码。
- 团队/多人/多工具切换时提示词难复用、难管理 → 用 OpenSkills 把能力模块化成 skill，集中管理并同步进 AI 上下文入口。
- 项目越成熟越难改、上下文越大越容易漏边界条件 → 用 specs 作为“系统行为真相”，让改动可审计、可追溯。

## 一键初始化（推荐：在目标工程目录执行）

在任意目标工程根目录，执行下面一段即可把该项目初始化为 AI 工作区：

```bash
curl -fsSL https://raw.githubusercontent.com/olaola-chat/OP-AI-SPEC-CODING-ENV/main/init-ai-env.sh -o init-ai-env.sh \
  && chmod +x init-ai-env.sh \
  && ./init-ai-env.sh
```

说明：

- 初始化会在项目里创建/更新少量文件与目录：`AGENTS.md`、`openspec/`、`.ai-env/`、`.claude/skills/`（细节见下文）。

如果你更偏好“clone & 执行”：

```bash
git clone https://github.com/olaola-chat/OP-AI-SPEC-CODING-ENV.git /tmp/op-ai-workspace \
  && cp /tmp/op-ai-workspace/init-ai-env.sh ./init-ai-env.sh \
  && chmod +x ./init-ai-env.sh \
  && ./init-ai-env.sh
```

## 成熟项目如何集成？

可以直接集成。推荐做法是：

1. 进入成熟项目根目录执行“一键初始化”命令
2. 将 `AGENTS.md` 作为 Trae（以及其他 AI 工具）的上下文入口文件
3. 之后所有“非小改动”的需求，默认走 OpenSpec：先 proposal，再 apply，再 archive

是否需要把脚本 clone 到目标工程？

- **可以，但不是必须**。更推荐用上面的 `curl` 一键拉取脚本并执行，避免每个项目都维护一份脚本副本。

## 初始化后有哪些东西？

- `AGENTS.md`：AI 工作规范入口（Trae 里建议固定让 AI 先读它）
- `openspec/`：规格与变更提案目录
  - `openspec/specs/`：规格真相（source of truth）
  - `openspec/changes/`：变更提案与任务
- `.ai-env/`：在项目内单独安装 openskills/openspec（不污染全局环境，也不干扰项目生产依赖）
- `.claude/skills/`：由 OpenSkills 安装的 skills 目录（OpenSpec skill 会被安装在这里）

## 📦 当前内置技能

初始化脚本默认安装以下核心技能：

### 1. OpenSpec (核心)
这是本环境的“大脑”，负责需求管理与规格定义。
- **能力**：管理 Spec-Driven Development (SDD) 的完整生命周期。
- **解决痛点**：防止 AI 在长对话中丢失上下文或偏离原始需求。

**技能详情 (SKILL.md 内容预览)**：
```markdown
## Capabilities
- **Spec-Driven Development**: You should always look for specs in `openspec/specs/` before coding.
- **Change Management**: All major changes should go through a Proposal -> Implementation -> Archive lifecycle.

## Commands
- **Create Proposal**: `npx openspec proposal "Description of change"`
  - *Trigger*: When user requests a new feature or significant refactor.
- **Apply Change**: `npx openspec apply <change-id>`
  - *Trigger*: When you are ready to implement the code for a proposal.
- **Archive Change**: `npx openspec archive <change-id>`
  - *Trigger*: When implementation is done and verified.
- **List Changes**: `npx openspec changes`
  - *Trigger*: To see what is currently in progress.

## Workflow Rules
1. **Always Check Specs**: Before writing code, read relevant specs in `openspec/specs/`.
2. **Propose First**: For non-trivial changes, create a proposal first using `npx openspec proposal`.
3. **Update Specs**: Keep specs as the source of truth.
```

### 扩展更多技能
本环境基于 [OpenSkills](https://github.com/numman-ali/openskills) 构建，你可以随时安装更多社区技能（如 PDF 处理、浏览器自动化等）来增强 AI 能力：

```bash
# 示例：安装 Anthropic 官方技能库
npx openskills install anthropics/skills
```

安装后运行 `npx openskills sync`，新技能就会自动出现在 `AGENTS.md` 中供 AI 使用。

## 最小使用流程（你只要记住这 4 句）

你不需要自己运行 `npx`。这些命令应该由 AI 在需要时自动运行（并把结果文件展示给你审阅）。你只需要用自然语言驱动流程：

1. 让 AI 先读 `AGENTS.md`
2. 让 AI 先做提案/规格对齐（不要直接写代码）
3. 你确认后，让 AI 按规格实现
4. 验证通过后，让 AI 归档（把变更沉淀进 specs）

更多细节见 [AI_WORKFLOW_GUIDE.md](./AI_WORKFLOW_GUIDE.md)。

## 初始化后如何验证能力可用？

把下面这段话复制到 Trae 的 AI 对话里（建议在目标工程根目录执行完初始化后立刻验证）：

> 请先阅读并遵守当前仓库的 `AGENTS.md`。然后列出你能使用的 skills，并加载 OpenSpec skill。接着为“新增 /healthz 健康检查接口（仅规划，不写代码）”创建一个 OpenSpec proposal，并告诉我在 `openspec/changes/` 下生成了哪些文件、proposal 的 change-id 是什么，以及我下一步应该如何审阅它。
