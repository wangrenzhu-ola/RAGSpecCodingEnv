id: leaf-20260227T0629-hkt-memory-v2-skill-md-重写-openclaw-对齐
title: hkt-memory v2 SKILL.md 重写（OpenClaw 对齐）
status: 现行
confidence: 中
scope: 默认
created_at: 2026-02-27T06:29:31.760003
updated_at: 2026-02-27T06:29:31.760003
source: conversation-2026-02-27
content:
- SKILL.md 以 Tree 记忆库 + SQLite(memory.db) 向量/FTS 索引为核心
- 检索优先级：hybrid(需先 sync) > tree/query 渐进式披露(depth 1→2→3) > strict 过滤
- 混合检索支持加权融合、MMR、多样性重排、时间衰减、语义分块+fixed window 兜底
- 写入/维护：禁止泛化 branch；重复用 --dedupe/--merge-duplicate；过期用 expire/prune
- 故障排查：memory.db 缺失先 sync；embedding 失败可用 HKT_MEMORY_FORCE_LOCAL 或修正 OPENAI_* 配置
