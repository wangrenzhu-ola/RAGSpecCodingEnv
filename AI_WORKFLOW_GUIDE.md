# OlaParty AI 规格驱动开发环境指南

这是一套标准化的 AI 开发环境，集成了 **OpenSkills**（技能管理）与 **OpenSpec**（规格/提案管理），目的是把“需求对齐 → 落地实现 → 结果可审计”固化成统一流程，避免需求只存在于聊天记录里导致实现漂移。

## 快速开始

在任意项目（新项目或成熟项目）根目录执行：

```bash
chmod +x init-ai-env.sh
./init-ai-env.sh
```

初始化会完成：

1. 安装本项目私有依赖（OpenSkills、OpenSpec），不污染全局环境
2. 安装并同步 OpenSpec Skill 到 `AGENTS.md`
3. 初始化 `openspec/` 目录（规格与变更提案）

## 在 Trae / 其他 AI 工具中怎么用

把 `AGENTS.md` 作为 AI 的主要上下文入口。AI 应该先读它，再开始执行任务。

### “先规格，后代码”的标准流程

不要直接写代码，按以下流程推进：

1. **需求/提案**  
   你说：我要加用户登录。  
   AI：创建提案（proposal），把需求写清楚、可评审、可落地。  
   命令：`npx openspec proposal "Add user login"`

2. **评审/补齐细节**  
   你和 AI 一起修改提案内容（尤其边界条件、验收标准、非功能需求），直到一致。

3. **实施（严格按提案）**  
   你说：开始实现这个提案。  
   AI：`npx openspec apply <change-id>` 并按提案实现代码。

4. **归档（让 specs 成为真相）**  
   验证通过后归档：`npx openspec archive <change-id>`  
   归档会把已完成变更沉淀进 `openspec/specs/`，后续再改就有“权威规格”可查。

## 命令速查

通常你不需要自己手动敲命令，AI 会在需要时运行并把结果呈现给你审阅。下面这张表用于理解 AI 在做什么（或排障时使用）。

| 命令 | 说明 |
| :-- | :-- |
| `npx openspec proposal "标题"` | 创建变更提案（先对齐需求） |
| `npx openspec changes` | 查看当前有哪些提案 |
| `npx openspec apply <id>` | 按提案执行实现 |
| `npx openspec archive <id>` | 验证后归档进 specs |
| `.ai-env/node_modules/.bin/openskills sync` | 重新同步技能到 `AGENTS.md` |

## 目录结构说明

- `AGENTS.md`：AI 的“工作规范入口”
- `.ai-env/`：本项目私有的 AI 工具依赖（不影响项目生产依赖）
- `.claude/skills/`：OpenSkills 安装后的技能目录（由 OpenSkills 维护）
- `openspec/`：
  - `specs/`：系统行为的规格真相（source of truth）
  - `changes/`：变更提案与任务

## 初始化后验证（建议必做）

把下面这段话复制到 Trae 的 AI 对话里：

> 请先阅读并遵守当前仓库的 `AGENTS.md`。然后列出你能使用的 skills，并加载 OpenSpec skill。接着为“新增 /healthz 健康检查接口（仅规划，不写代码）”创建一个 OpenSpec proposal，并告诉我在 `openspec/changes/` 下生成了哪些文件、proposal 的 change-id 是什么，以及我下一步应该如何审阅它。
