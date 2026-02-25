---
name: "hkt-memory"
description: "基于 HKT 树状记忆系统的渐进式披露与主动检索指南。所有记忆检索与写入必须通过脚本执行，并明确给出 .trae/.claude 两种路径。"
---

# HKT 记忆引擎（渐进式披露）

## 使用场景

- 保存或检索长期记忆与跨会话上下文
- 需要先结论后细节，避免一次性加载过多信息

## 强制规则（必须）

- 记忆检索与写入必须通过脚本执行，禁止直接读取 memory 目录。
- 输出命令时必须同时提供 `.trae/` 与 `.claude/` 两种路径。
- 需要历史结论或上下文时必须先查询 hkt-memory，只有记忆不足或需要精准定位代码时才进行工作区搜索。
- Branch 仅用于语义分类，来源信息写入 `source` 字段，禁止泛化分支。

## 渐进式检索原则

- Root → Branch → Leaf 逐层展开，只在需要细节时读取 Leaf。
- 输出顺序先 Root/Branch 摘要，再补充必要 Leaf。

## 存储结构（简述）

- `memory/index.md`：Root 索引与摘要
- `memory/<root>/index.md`：Root 概要与 Branch 列表
- `memory/<root>/<branch>/index.md`：Branch 概要与 Leaf 索引
- `memory/<root>/<branch>/<leaf-id>.md`：Leaf 文档
- Leaf 最小字段：`id`、`title`、`content`、`source`、`created_at`、`status`

## 常用命令

- 初始化：
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py init`
  - `python .claude/skills/hkt-memory/scripts/hkt_memory.py init`
- 写入：
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py add --root <root> --branch <branch> --title <title> --content <item>`
  - `python .claude/skills/hkt-memory/scripts/hkt_memory.py add --root <root> --branch <branch> --title <title> --content <item>`
- 查询：
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py query --root <root> --branch <branch> --keyword <kw> --depth <1|2|3> --limit <n> --fallback-leaf-limit <n>`
  - `python .claude/skills/hkt-memory/scripts/hkt_memory.py query --root <root> --branch <branch> --keyword <kw> --depth <1|2|3> --limit <n> --fallback-leaf-limit <n>`
- 严格关键词：
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py query ... --strict-keyword`
  - `python .claude/skills/hkt-memory/scripts/hkt_memory.py query ... --strict-keyword`
- 归类/过期/清理：
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py reclassify --id <leaf-id> --branch <new-branch> [--root <new-root>]`
  - `python .claude/skills/hkt-memory/scripts/hkt_memory.py reclassify --id <leaf-id> --branch <new-branch> [--root <new-root>]`
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py expire --id <leaf-id> --status <过期|现行>`
  - `python .claude/skills/hkt-memory/scripts/hkt_memory.py expire --id <leaf-id> --status <过期|现行>`
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py prune --before-days <n> --status <过期|现行|未知> --dry-run`
  - `python .claude/skills/hkt-memory/scripts/hkt_memory.py prune --before-days <n> --status <过期|现行|未知> --dry-run`
