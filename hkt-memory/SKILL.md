---
name: "hkt-memory"
description: "对齐 OpenClaw 的记忆系统：Tree 记忆库 + SQLite 向量/全文索引 + 混合检索（MMR/时间衰减/增强分块）。所有检索与写入通过脚本完成，并同时给出 .trae/.claude 路径。"
---

# hkt-memory v2（OpenClaw 对齐）

## 这是什么

- hkt-memory v2 用“Tree 记忆库 + 向量/全文索引”实现 OpenClaw 风格的记忆检索与维护：先用可控的摘要结构定位，再用混合检索在叶子级别取回最相关片段，最后按需回到树结构做验证与扩展。

## 核心原则（必须）

- 只通过脚本读写：默认不直接遍历/手改 `memory/`（需要查看某条 Leaf 原文时，用 IDE 打开文件属于“人类阅读”，但不要让 Agent 以“扫描文件夹”代替检索）。
- 结构化优先：写入以“短标题 + 列表要点”为主，便于分块与检索；长文本会退化成固定窗口分块，效果更不可控。
- 可维护：重复内容用 `--dedupe/--merge-duplicate`，过期内容用 `expire/prune`，索引由脚本维护。
- 与 OpenClaw 对齐：默认支持加权混合检索、MMR 多样性重排、时间衰减、增强分块（list item 语义分块 + fixed window 兜底）。

## 数据模型

- Tree：`memory/<root>/<branch>/<leaf>.md`，通过 `index.md` 维护 Root/Branch/Leaf 列表与摘要。
- Index：`memory/memory.db`（SQLite），包含
  - chunks：每个 leaf 被切成多个 chunk（语义分块或固定窗口分块）
  - chunks_fts：FTS5 全文索引
  - files：文件 hash，用于 `sync` 增量更新

Leaf 最小字段（脚本会写入/更新）：

```text
id: <leaf-id>                 # 默认自动生成；可用 --id 指定
title: <短标题>               # 必填
status: <现行|过期|未知>       # 默认: 现行
confidence: <高|中|低>         # 默认: 中
scope: <适用范围>              # 默认: 默认
created_at: <ISO8601>          # 自动生成
updated_at: <ISO8601>          # 发生合并/变更时更新
source: <来源锚点>             # 必填：conversation-YYYY-MM-DD 或 文件路径
content:
  - <要点1>
  - <要点2>
```

## 检索策略（OpenClaw 风格）

优先级从高到低：

1. 混合检索（推荐）：当目标是“找结论/找片段/跨 Root 语义相关”时，先 `sync`，再 `query --hybrid`。
2. 树检索（可控披露）：当需要“理解有哪些 Root/Branch/最新叶子”或混合检索不可用时，用 `query/tree` 逐层展开（depth 1→2→3）。
3. 精确过滤：用 `--root/--branch/--status/--strict-keyword` 收敛范围，避免兜底返回过多无关叶子。

混合检索能力：

- 加权混合：`score = vector_score*vector_weight + text_score*text_weight`
- MMR：降低重复 chunk，提升多样性（适合探索性问题）
- 时间衰减：优先近期更新（适合“系统现状/最近决策”）
- 增强分块：优先用 `content:` 下每条 `- item` 作为语义 chunk；无 items 则对正文做 fixed window（2048/overlap 200）

## 写入与归类规则（必须）

- Branch 只做语义分类；来源写在 `source`，不要把“对话/日期”当 Branch。
- 禁止泛化 Branch：`对话记录/临时/其他/misc/temp/conversation`（脚本会拦截或回退建议分支）。
- 一条 Leaf 只承载一个主题；跨主题拆分为多条 Leaf（建议每轮最多 3 条）。
- 优先复用已有 Root/Branch；只有稳定且长期会复用的主题才新增 Root/Branch。

建议的“写入前分类输出”（给 LLM 自己用的结构）：

```json
{
  "root": "HKT记忆系统",
  "branch": "工具与脚本",
  "title": "hkt-memory v2 的检索与写入约束",
  "status": "现行",
  "confidence": "高",
  "scope": "本仓库 AI IDE 工作流",
  "source": "conversation-YYYY-MM-DD",
  "content": [
    "检索/写入通过 entry.sh 或 hkt_memory.py",
    "混合检索需先 sync 生成 memory/memory.db"
  ]
}
```

## 命令速查（同时给出 .trae/.claude）

统一入口（自动识别 .trae/.claude）：

```bash
bash .trae/skills/hkt-memory/entry.sh <command> [args...]
bash .claude/skills/hkt-memory/entry.sh <command> [args...]
```

初始化索引：

```bash
python .trae/skills/hkt-memory/scripts/hkt_memory.py init
python .claude/skills/hkt-memory/scripts/hkt_memory.py init
```

写入 Leaf（可多次传 `--content`）：

```bash
python .trae/skills/hkt-memory/scripts/hkt_memory.py add --root <root> --branch <branch> --title <title> --content <item> --source <source>
python .claude/skills/hkt-memory/scripts/hkt_memory.py add --root <root> --branch <branch> --title <title> --content <item> --source <source>
```

分类建议（从 taxonomy 猜测 branch）：

```bash
python .trae/skills/hkt-memory/scripts/hkt_memory.py suggest --root <root> --title <title> --content <item>
python .claude/skills/hkt-memory/scripts/hkt_memory.py suggest --root <root> --title <title> --content <item>
```

树检索（depth 1/2/3 控制披露）：

```bash
python .trae/skills/hkt-memory/scripts/hkt_memory.py query --depth 1 --limit 20
python .claude/skills/hkt-memory/scripts/hkt_memory.py query --root <root> --branch <branch> --keyword <kw> --depth 3 --limit 50
```

向量索引同步（生成/更新 `memory/memory.db`）：

```bash
python .trae/skills/hkt-memory/scripts/hkt_memory.py sync
python .claude/skills/hkt-memory/scripts/hkt_memory.py sync
```

混合检索（需要先 sync）：

```bash
python .trae/skills/hkt-memory/scripts/hkt_memory.py query --hybrid --keyword "<query>" --limit 10
python .claude/skills/hkt-memory/scripts/hkt_memory.py query --hybrid --keyword "<query>" --mmr --decay --limit 10
```

维护：

```bash
python .trae/skills/hkt-memory/scripts/hkt_memory.py reclassify --id <leaf-id> --branch <new-branch> --root <new-root>
python .claude/skills/hkt-memory/scripts/hkt_memory.py expire --id <leaf-id> --status 过期
python .trae/skills/hkt-memory/scripts/hkt_memory.py prune --before-days 90 --status 过期 --dry-run
```

## 配置与故障排查

- 记忆目录：`HKT_MEMORY_DIR=/path/to/memory`（默认 `./memory`）
- 智谱 GLM Embedding（与你截图一致）的环境变量示例：

```bash
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
export OPENAI_API_KEY="<你的 bigmodel token>"
export HKT_MEMORY_MODEL="embedding-3"
```

- 常见误配：`OPENAI_BASE_URL` 指向本地 `http://127.0.0.1:8000/v1` 这类非 embeddings 服务，会导致 POST 报 501/HTML 错误
- 混合检索失败且报 embedding 错误时：
  - 优先切到本地 embedding：`export HKT_MEMORY_FORCE_LOCAL=true`（需要安装 `sentence-transformers` 并可用 `HKT_MEMORY_MODEL` 指定模型名）
  - 或修正远端 embedding 配置：`OPENAI_API_KEY` / `OPENAI_BASE_URL` / `HKT_MEMORY_MODEL`
- 报 `Memory database not found. Please run 'sync' first.`：先执行 `sync` 生成 `memory/memory.db`
- 需要“严格命中关键词”时：在非 hybrid `query` 加 `--strict-keyword`（否则会触发“兜底: 最新”）

## 对话结束的最小写入流程

1. 用 1-2 句话总结本轮可复用结论（可验证、可长期复用）。
2. 为每条结论选 Root/Branch，并写成 `content:` 的 1-5 个要点。
3. `add` 写入；疑似重复用 `--dedupe` 或 `--merge-duplicate`。
4. 若依赖混合检索：写入后执行 `sync`（或在维护/清理后统一 sync）。
