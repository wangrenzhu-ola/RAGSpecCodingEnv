# 需求规格说明书：HKT-Memory 增强版 (Hybrid Search Upgrade)

## 1. 目标
对齐 OpenClaw 的混合检索算法，提升 `hkt-memory` 技能的检索质量和多样性。在保留 HKT 树状结构和 Markdown Source of Truth 的基础上，引入 MMR（最大边际相关性）、时间衰减（Temporal Decay）和加权融合（Weighted Fusion）机制。

## 2. 功能特性 (Features)

### 2.1 混合检索算法升级 (Hybrid Search v2)
- **从 RRF 迁移到加权求和**
  - **公式**: `Score = (VectorScore * vector_weight) + (BM25Score * text_weight)`
  - **默认权重**:
    - Vector Weight: `0.7`
    - Text Weight: `0.3`
  - **BM25 分数归一化**: `Score = 1 / (1 + rank)` (OpenClaw 实现) 或直接使用 FTS5 `rank` (越小越好，需取倒数)。
  - **Vector 分数**: `Cosine Similarity` (范围 `[-1, 1]`，需归一化到 `[0, 1]`)。

### 2.2 最大边际相关性 (MMR)
- **目的**: 减少相似结果的冗余，提升检索内容的多样性。
- **参数**:
  - `lambda`: `0.7` (默认)
    - `1.0`: 仅考虑相关性 (Max Relevance)。
    - `0.0`: 仅考虑多样性 (Max Diversity)。
- **逻辑**:
  - 在候选集中迭代选择结果，每次选择时最大化 `lambda * Relevance - (1 - lambda) * MaxSim(Result, Selected)`。

### 2.3 时间衰减 (Temporal Decay)
- **目的**: 提升近期记忆的权重，降低陈旧信息的干扰。
- **参数**:
  - `half_life_days`: `30` (半衰期天数，默认 30 天)。
- **逻辑**:
  - `DecayFactor = 0.5 ^ (AgeInDays / HalfLifeDays)`
  - `FinalScore = BaseScore * DecayFactor`
  - `AgeInDays`: `(Now - LeafUpdatedAt) / (24 * 3600)`

### 2.4 分块策略增强 (Chunking)
- **目的**: 解决 Leaf 中长文本无法被有效检索的问题。
- **逻辑**:
  - 保留现有的 `Title + List Item` 语义分块。
  - 新增 **固定窗口分块** 作为补充：
    - 对 Leaf 中的非列表段落进行切分。
    - 窗口大小: `512` 字符 (约 128 tokens)。
    - 重叠: `64` 字符。

## 3. 技术实现 (Technical Implementation)

### 3.1 Python 脚本修改
- **`vector_store.py`**:
  - `search_similar`: 返回原始余弦相似度。
  - `search_keyword`: 返回基于 rank 的归一化分数。
  - `hybrid_search`: 
    - 废弃 RRF 逻辑。
    - 实现加权求和。
    - 集成 MMR 重排序。
    - 集成 Temporal Decay。
  - 新增 `mmr_reorder(results, query_embedding, lambda_param)` 函数。
  - 新增 `apply_temporal_decay(results, half_life)` 函数。

- **`hkt_memory.py`**:
  - `query` 命令参数扩展：
    - `--vector-weight`: 默认 0.7
    - `--text-weight`: 默认 0.3
    - `--mmr`: 启用 MMR (默认 False)
    - `--mmr-lambda`: 默认 0.7
    - `--decay`: 启用时间衰减 (默认 False)
    - `--decay-days`: 默认 30

### 3.2 数据库 Schema 变更
- 无需变更 Schema，利用现有的 `metadata` JSON 字段存储分块类型（语义/固定窗口）。

## 4. 验收标准 (Acceptance Criteria)
1. **单元测试**:
   - 验证加权求和计算正确。
   - 验证 MMR 能有效过滤极其相似的向量结果。
   - 验证时间衰减能让近期 Leaf 排名更靠前。
2. **集成测试**:
   - 运行 `hkt-memory query --hybrid --keyword "测试" --mmr --decay`，确输出结果符合预期。
   - 对比新旧算法在同一查询下的 Top 5 结果差异。

## 5. 里程碑
1. **Phase 1**: 实现加权求和与 MMR。
2. **Phase 2**: 实现时间衰减。
3. **Phase 3**: 增强分块策略。
