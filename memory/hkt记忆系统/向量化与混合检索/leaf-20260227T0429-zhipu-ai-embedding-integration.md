id: leaf-20260227T0429-zhipu-ai-embedding-integration
title: Zhipu AI Embedding Integration
status: 现行
confidence: 中
scope: 默认
created_at: 2026-02-27T04:29:57.620285
updated_at: 2026-02-27T04:29:57.620285
source: conversation
content:
- Configured Zhipu AI (GLM-4) via init-ai-env.sh (embedding-3)
- Implemented EmbeddingClient in .trae/skills/hkt-memory/scripts/embedding_client.py
- Implemented VectorStore in .trae/skills/hkt-memory/scripts/vector_store.py with SQLite + FTS5
- Verified vector search functionality with Zhipu embeddings (dim=2048)
