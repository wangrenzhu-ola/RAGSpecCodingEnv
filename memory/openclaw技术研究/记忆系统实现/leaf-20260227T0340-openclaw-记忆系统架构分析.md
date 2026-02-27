id: leaf-20260227T0340-openclaw-记忆系统架构分析
title: OpenClaw 记忆系统架构分析
status: 现行
confidence: 中
scope: 默认
created_at: 2026-02-27T03:40:23.919468
updated_at: 2026-02-27T03:40:23.919468
source: conversation
content:
- 核心架构：Markdown (Source of Truth) + SQLite (Index/Cache)。索引技术：sqlite-vec (Vector) + FTS5 (Keyword) = Hybrid Search。排序算法：MMR (多样性) + Temporal Decay (时间衰减)。分块策略：基于字符估算 Token (tokens * 4)，支持重叠。交互模式：通过 Tool (memory_search) 暴露给 Agent，System Prompt 强制调用。
