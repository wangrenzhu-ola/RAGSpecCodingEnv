---
name: "hkt-memory"
description: "Manages long-term memory (Tree + Vector/Hybrid Search). Invoke to store key decisions/context or retrieve project history. Supports semantic search."
---

# HKT Memory (v2)

A progressive disclosure memory system that organizes knowledge in a Tree (Root > Branch > Leaf) and supports Hybrid Search (Vector + FTS).

## Capabilities

- **Store**: Save key decisions, specs, and context to persistent memory.
- **Retrieve**: Find relevant information using semantic search (Hybrid) or structured navigation (Tree).
- **Sync**: Automatically maintain vector indices for fast retrieval.

## When to Use

- **Write (`add`)**: When a task is completed, a key decision is made, or new requirements are defined.
- **Search (`query`)**: When starting a new task, needing context on previous decisions, or understanding project background.
- **Explore (`suggest`)**: When you need help categorizing new information.

## Commands

### 1. Retrieve Information (Recommended)

Use hybrid search to find semantically related information.

```bash
# Search with keywords (automatically uses hybrid vector + text search)
HKT_MEMORY_FORCE_LOCAL=true python3 hkt-memory/scripts/hkt_memory.py query --hybrid --keyword "<your query>" --limit 10
```

### 2. Structured Navigation

Use when you need to explore the memory structure or list all items under a category.

```bash
# List roots and branches (Depth 1-2)
python3 hkt-memory/scripts/hkt_memory.py query --depth 2

# List leaves under a specific branch
python3 hkt-memory/scripts/hkt_memory.py query --root "<root>" --branch "<branch>" --depth 3
```

### 3. Store Memory

Save important context. Keep titles short and content as bullet points.

```bash
# Add a new memory leaf
python3 hkt-memory/scripts/hkt_memory.py add \
  --root "<root>" \
  --branch "<branch>" \
  --title "<short title>" \
  --source "conversation" \
  --content "<point 1>" \
  --content "<point 2>"
```

**Tip**: If you are unsure about Root/Branch, use `suggest` first:

```bash
python3 hkt-memory/scripts/hkt_memory.py suggest --title "<title>" --content "<content>"
```

### 4. Sync Index

Run this after adding new memories to update the vector index.

```bash
HKT_MEMORY_FORCE_LOCAL=true python3 hkt-memory/scripts/hkt_memory.py sync
```

## Rules

1. **Check First**: Always search memory before asking the user for repeated information.
2. **Atomic Leaves**: Each leaf should cover ONE specific topic.
3. **Source of Truth**: The Markdown files in `memory/` are the source of truth; the SQLite DB is just an index.
