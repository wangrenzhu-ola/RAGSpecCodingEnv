# hkt-memory 与 OpenClaw Memory 实现差异分析报告

## 1. 概述

本报告对比了当前环境中的 `hkt-memory` 技能实现与 `OpenClaw` 源码中的记忆系统实现。`hkt-memory` 目前是一个基于 Python 的轻量级实现，而 `OpenClaw` 的记忆系统是一个基于 TypeScript/Node.js 的深度集成模块。

## 2. 核心差异点

### 2.1 混合检索算法 (Hybrid Search)

- **OpenClaw**:
  - 使用 **加权求和 (Weighted Sum)**：`Score = (VectorScore * vectorWeight) + (BM25Score * textWeight)`。
  - 支持 **MMR (Maximal Marginal Relevance)** 用于结果多样性去重。
  - 支持 **时间衰减 (Temporal Decay)** 用于提升近期记忆的权重。
  - BM25 分数归一化：`1 / (1 + rank)`。
- **hkt-memory**:
  - 使用 **RRF (Reciprocal Rank Fusion)**：`Score = 1 / (k + rank)`。
  - **不支持** MMR。
  - **不支持** 时间衰减。
  - 无法调整向量与关键词的权重比例。

### 2.2 向量存储引擎 (Vector Store)

- **OpenClaw**:
  - 优先使用 `sqlite-vec` 扩展进行数据库内向量搜索 (`vec_distance_cosine`)，性能更好。
  - 只有在扩展不可用时才回退到内存计算。
  - 存储结构分离：`chunks_vec` (向量) 和 `chunks_fts` (全文索引)。
- **hkt-memory**:
  - 完全依赖 Python 内存计算 (`numpy.dot`)。
  - 每次搜索需加载所有 Embedding 到内存，随着记忆量增长会有性能瓶颈。
  - 向量以 JSON 字符串形式存储在 `chunks` 表中。

### 2.3 分块策略 (Chunking)

- **OpenClaw**:
  - **固定窗口分块**：基于字符数估算 Token (tokens \* 4)，支持重叠 (overlap)。
  - 适用于长文档的无差别分块。
- **hkt-memory**:
  - **语义分块**：基于 `Title + List Item` 的结构化分块。
  - 强依赖 Markdown 的列表格式，对于非结构化的长文本段落处理能力较弱。

### 2.4 数据结构与组织

- **OpenClaw**:
  - **时间流**：`memory/YYYY-MM-DD.md` (每日日志)。
  - **精选集**：`MEMORY.md` (长期记忆)。
  - 强调 "Source of Truth" 是 Markdown 文件。
- **hkt-memory**:
  - **HKT 树**：`Root -> Branch -> Leaf` 结构。
  - 强调渐进式披露 (Progressive Disclosure) 和分类管理。
  - 同样以 Markdown 为 Source of Truth。

## 3. 结论

`hkt-memory` 技能在**设计理念**上（Markdown 为主，SQLite 为辅）与 OpenClaw 保持一致，但在**检索算法的精细度**和**工程实现**上存在较大差距。

为了达到 OpenClaw 的智能水平，建议在保持 HKT 树状结构的前提下，引入 OpenClaw 的高级检索特性（MMR、时间衰减、加权混合）。

## 4. 建议

1. **升级检索算法**：在 Python 脚本中实现 MMR 和时间衰减逻辑。
2. **优化混合打分**：从 RRF 迁移到加权求和，以便微调语义与关键词的权重。
3. **增强分块能力**：对于 Leaf 中的长文本内容，增加固定窗口分块的兜底策略。
