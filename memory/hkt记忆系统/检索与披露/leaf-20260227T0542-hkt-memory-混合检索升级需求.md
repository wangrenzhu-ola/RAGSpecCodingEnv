id: leaf-20260227T0542-hkt-memory-混合检索升级需求
title: HKT-Memory 混合检索升级需求
status: 现行
confidence: 中
scope: 默认
created_at: 2026-02-27T05:42:16.752602
updated_at: 2026-02-27T05:42:16.752602
source: conversation
content:
- 目标：引入 Weighted Hybrid Search, MMR, Temporal Decay
- 算法变更：RRF -> Weighted Sum
- 新增特性：MMR (lambda=0.7), Temporal Decay (half_life=30d)
- 分块增强：增加固定窗口分块兜底
- 实现计划：修改 vector_store.py 和 hkt_memory.py
