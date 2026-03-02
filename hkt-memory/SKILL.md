---
name: "hkt-memory"
description: "Manages long-term memory (Temporal + Evergreen). Invoke to store key decisions/context or retrieve project history. Supports Hybrid Search (Vector + FTS)."
---

# HKT Memory (v2 - OpenClaw Aligned)

A memory system aligned with OpenClaw that organizes knowledge in a Temporal structure (Daily Logs) and Evergreen notes, supporting Hybrid Search (Vector + FTS) with MMR and Time Decay.

## Capabilities

- **Store**: Save key decisions, specs, and context to persistent memory (Daily or Evergreen).
- **Retrieve**: Find relevant information using Hybrid Search (Vector + Keyword) with re-ranking.
- **Sync**: Automatically maintain vector indices for fast retrieval.

## When to Use

- **Write (`add`)**: When a task is completed, a key decision is made, or new requirements are defined.
- **Search (`query`)**: When starting a new task, needing context on previous decisions, or understanding project background.

## Commands

### 1. Retrieve Information (Recommended)

Use hybrid search to find semantically related information.

```bash
# Search with keywords (automatically uses hybrid vector + text search with MMR & Decay)
HKT_MEMORY_FORCE_LOCAL=true python3 hkt-memory/scripts/hkt_memory.py query --keyword "<your query>" --limit 10
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
HKT_MEMORY_FORCE_LOCAL=true python3 hkt-memory/scripts/hkt_memory.py sync
```

## Rules

1. **Check First**: Always search memory before asking the user for repeated information.
2. **Atomic Items**: Each memory item should cover ONE specific topic.
3. **Source of Truth**: The Markdown files in `memory/` are the source of truth; the SQLite DB is just an index.
