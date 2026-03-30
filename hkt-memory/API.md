# HKT-Memory v4.5 API 参考

> 完整CLI命令和参数说明

---

## 全局

```bash
python3 scripts/hkt_memory_v4.py <command> [options]
```

---

## store - 存储记忆

```bash
python3 scripts/hkt_memory_v4.py store \
  --content "..."           # 记忆内容 (必需)
  --title "..."             # 标题
  --topic "general"         # 主题分类
  --layer L2                # 存储层: L0/L1/L2/all
  --scope global            # 作用域: global/agent:<id>/project:<id>
  --agent-id <id>           # Agent ID (用于scope)
  --project-id <id>         # Project ID (用于scope)
  --no-extract              # 禁用智能提取
```

### 示例

```bash
# 基础存储
python3 scripts/hkt_memory_v4.py store \
  --content "用户偏好使用Python开发" \
  --title "开发偏好" \
  --layer L2

# 带Scope存储
python3 scripts/hkt_memory_v4.py store \
  --content "陛下偏好使用Python" \
  --scope agent:liubowen \
  --layer L2
```

---

## retrieve - 检索记忆

```bash
python3 scripts/hkt_memory_v4.py retrieve \
  --query "..."             # 查询文本 (必需)
  --layer all               # 目标层: L0/L1/L2/all
  --limit 10                # 返回数量
  --mode hybrid             # 检索模式: vector/bm25/hybrid
  --vector-weight 0.7       # 向量搜索权重 (0-1)
  --bm25-weight 0.3         # BM25权重 (0-1)
  --scope <scopes>          # 作用域过滤 (逗号分隔)
  --min-score 0.35          # 最小分数阈值
  --mmr-threshold 0.85      # MMR相似度阈值
  --no-adaptive             # 禁用自适应检索
  --no-mmr                  # 禁用MMR多样性
  --no-rerank               # 禁用重排序
  --no-vector               # 禁用向量搜索
```

### 检索模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `hybrid` | Vector+BM25融合 (默认) | 通用场景 |
| `vector` | 纯向量语义检索 | 语义相似查询 |
| `bm25` | 纯BM25全文检索 | 代码/专有名词精确匹配 |

### 示例

```bash
# 基础检索
python3 scripts/hkt_memory_v4.py retrieve \
  --query "Python开发" \
  --limit 5

# 混合检索 (完整参数)
python3 scripts/hkt_memory_v4.py retrieve \
  --query "FastAPI配置" \
  --mode hybrid \
  --vector-weight 0.7 \
  --bm25-weight 0.3 \
  --scope global,agent:liubowen \
  --min-score 0.35 \
  --mmr-threshold 0.85

# 纯BM25检索 (代码片段)
python3 scripts/hkt_memory_v4.py retrieve \
  --query "def calculate_total" \
  --mode bm25
```

---

## stats - 查看统计

```bash
python3 scripts/hkt_memory_v4.py stats
```

### 输出示例

```json
{
  "layers": {
    "L0": {"entries": 10},
    "L1": {"entries": 20},
    "L2": {"entries": 100}
  },
  "vector_store": {
    "total_vectors": 130,
    "embedding_dimensions": 2048,
    "embedding_model": "embedding-3"
  },
  "bm25_index": {
    "total_documents": 130,
    "fts_version": "FTS5"
  },
  "scopes": {
    "active_scopes": ["global"],
    "total_registered": 5
  }
}
```

---

## test-retrieval - 测试检索管道

```bash
python3 scripts/hkt_memory_v4.py test-retrieval \
  --query "..."             # 测试查询 (必需)
  --mode hybrid             # 检索模式
```

### 示例

```bash
# 测试自适应判断
python3 scripts/hkt_memory_v4.py test-retrieval --query "你好"
# 输出: Should retrieve: False (问候语跳过)

python3 scripts/hkt_memory_v4.py test-retrieval --query "记得Python框架吗"
# 输出: Should retrieve: True (强制关键词)
```

---

## bm25 - BM25索引管理

### bm25 stats

```bash
python3 scripts/hkt_memory_v4.py bm25 stats
```

### bm25 optimize

```bash
python3 scripts/hkt_memory_v4.py bm25 optimize
```

---

## learn - 记录学习

```bash
python3 scripts/hkt_memory_v4.py learn \
  --content "..."           # 学习内容 (必需)
  --category insight        # 类别: pattern/methodology/insight
  --context "..."           # 上下文
```

---

## error - 记录错误

```bash
python3 scripts/hkt_memory_v4.py error \
  --description "..."       # 错误描述 (必需)
  --severity medium         # 严重级: critical/high/medium/low
  --message "..."           # 错误信息
```

---

## maintenance - 运行维护

```bash
python3 scripts/hkt_memory_v4.py maintenance
```

执行层级升降级评估，输出统计：
- Promoted: 升级到更高层级的记忆数
- Demoted: 降级到更低层级的记忆数
- Unchanged: 保持不变的记忆数

---

## mcp - MCP工具命令

### mcp recall

```bash
python3 scripts/hkt_memory_v4.py mcp recall \
  --query "..."             # 查询
  --limit 5                 # 数量
```

### mcp store

```bash
python3 scripts/hkt_memory_v4.py mcp store \
  --content "..."           # 内容
  --title "..."             # 标题
```

### mcp stats

```bash
python3 scripts/hkt_memory_v4.py mcp stats
```

---

## auto - 自动捕获/回忆

### auto capture

```bash
python3 scripts/hkt_memory_v4.py auto capture \
  --file conversation.json  # 对话文件 (可选，默认stdin)
```

### auto recall

```bash
python3 scripts/hkt_memory_v4.py auto recall \
  --query "..."             # 查询
```

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HKT_MEMORY_DIR` | 记忆存储目录 | `memory` |
| `HKT_MEMORY_API_KEY` | 智谱AI API Key | 内置Key |
| `HKT_MEMORY_BASE_URL` | 智谱AI Base URL | `https://open.bigmodel.cn/api/paas/v4/` |
| `HKT_MEMORY_MODEL` | Embedding模型 | `embedding-3` |
| `JINA_API_KEY` | Jina Reranker API Key | - |
| `SILICONFLOW_API_KEY` | SiliconFlow API Key | - |

---

## 返回值

所有命令返回JSON格式结果或文本输出。检索命令返回：

```json
[
  {
    "id": "doc-id",
    "content": "记忆内容",
    "score": 0.92,
    "layer": "L2",
    "scope": "global",
    "metadata": {...}
  }
]
```
