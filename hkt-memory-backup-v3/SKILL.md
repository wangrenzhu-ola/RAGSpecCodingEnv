---
name: "hkt-memory"
description: "Manages long-term memory (Temporal + Evergreen). Invoke to store key decisions/context or retrieve project history. Supports Hybrid Search (Vector + FTS)."
---

# HKT Memory (v3 - Hybrid + Graph Routing)

A memory system aligned with OpenClaw that organizes knowledge in a Temporal structure (Daily Logs) and Evergreen notes, supporting Hybrid Search (Vector + FTS) with MMR and Time Decay, plus optional query routing and graph expansion for complex questions.

## Capabilities

- **Store**: Save key decisions, specs, and context to persistent memory (Daily or Evergreen).
- **Retrieve**: Find relevant information using Hybrid Search (Vector + Keyword) with re-ranking.
- **Route**: Detect complex multi-hop/causal queries and switch between `hybrid_only` and `hybrid_plus_graph`.
- **Expand**: Build bounded graph-style related candidates from hybrid seeds and fuse results deterministically.
- **Consolidate**: Distill current context into memory with 4-layer controlled tags (`kind/scope/status/topic`), auto mapping, and threshold checks.
- **Sync**: Automatically maintain vector indices for fast retrieval.

## When to Use

- **Write (`add`)**: When a task is completed, a key decision is made, or new requirements are defined.
- **Search (`query`)**: When starting a new task, needing context on previous decisions, or understanding project background.

## Commands

### 1. Retrieve Information (Recommended)

Use hybrid search to find semantically related information.

```bash
# Search with keywords (默认开启 routing，graph 按阈值触发)
HKT_MEMORY_FORCE_LOCAL=false python3 hkt-memory/scripts/hkt_memory.py query --keyword "<your query>" --limit 10

# Show current mode (hybrid_only / hybrid_plus_graph)
HKT_MEMORY_FORCE_LOCAL=false python3 hkt-memory/scripts/hkt_memory.py query \
  --keyword "<your query>" \
  --limit 10 \
  --show-mode

# Force disable routing or graph (debug / baseline compare)
HKT_MEMORY_FORCE_LOCAL=false python3 hkt-memory/scripts/hkt_memory.py query \
  --keyword "<your query>" \
  --no-routing
```

### 2. Store Memory

Save important context. Keep titles short and content as bullet points.

```bash
# Add a new memory item (Defaults to today's daily log: memory/YYYY-MM-DD.md)
python3 hkt-memory/scripts/hkt_memory.py add \
  --title "<short title>" \
  --content "<point 1>" \
  --content "<point 2>"

# Add to Evergreen memory (memory/MEMORY.md) for permanent rules/facts
python3 hkt-memory/scripts/hkt_memory.py add \
  --evergreen \
  --title "<short title>" \
  --content "<point 1>"
```

### 3. Sync Index

Run this after adding new memories to update the vector index.

```bash
HKT_MEMORY_FORCE_LOCAL=false python3 hkt-memory/scripts/hkt_memory.py sync
```

### 4. Consolidate Current Context

Use this when user says “整合当前记忆” and you need to summarize key context into memory.

```bash
# Consolidate from explicit bullets
python3 hkt-memory/scripts/hkt_memory.py consolidate \
  --title "整合当前记忆" \
  --content "决策: 默认启用 routing" \
  --content "行动: 新增 --no-routing 便于回归" \
  --content "风险: graph 阈值需要继续调优"

# Consolidate from stdin
cat /tmp/context.txt | python3 hkt-memory/scripts/hkt_memory.py consolidate \
  --stdin \
  --title "整合当前记忆" \
  --source "当前会话"

# Force write when threshold validation fails
cat /tmp/context.txt | python3 hkt-memory/scripts/hkt_memory.py consolidate \
  --stdin \
  --title "整合当前记忆" \
  --scope session \
  --status active \
  --default-topic misc \
  --max-unknown-topic-ratio 0.6 \
  --max-fallback-kind-ratio 0.7 \
  --allow-threshold-breach
```

## Rules

1. **Check First**: Always search memory before asking the user for repeated information.
2. **Atomic Items**: Each memory item should cover ONE specific topic.
3. **Source of Truth**: The Markdown files in `memory/` are the source of truth; the SQLite DB is just an index.
4. **Consolidate Trigger**: If user says “整合当前记忆”, summarize current context and run `consolidate` to store it.
