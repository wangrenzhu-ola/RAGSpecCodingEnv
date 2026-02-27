id: leaf-20260227T0542-openclaw-vs-hkt-memory-分析报告
title: OpenClaw vs HKT-Memory 分析报告
status: 现行
confidence: 中
scope: 默认
created_at: 2026-02-27T05:42:08.995725
updated_at: 2026-02-27T05:42:08.995725
source: conversation
content:
- 混合检索算法差异：OpenClaw 使用 Weighted Sum + MMR + Temporal Decay，HKT 使用 RRF
- 向量存储差异：OpenClaw 优先使用 sqlite-vec，HKT 使用 Python 内存计算
- 分块策略差异：OpenClaw 使用固定窗口 (tokens * 4)，HKT 使用语义分块 (Title + List Item)
- 架构差异：OpenClaw 深度集成 Node.js，HKT 为独立 Python 脚本
- 结论：HKT 需要升级算法以对齐 OpenClaw 的智能水平
