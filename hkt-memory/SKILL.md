---
name: "hkt-memory-v4.5"
description: "生产级长期记忆系统，支持混合检索(Vector+BM25)、自适应检索、Multi-Scope隔离"
triggers:
  - memory
  - recall
  - store
  - retrieve
---

# HKT-Memory v4.5

> 生产级长期记忆系统，融合LanceDB Pro、Mem0众家之长  
> **核心**: 存储 → 检索 → 使用，6阶段智能管道自动处理

## ⚡ 30秒上手

```bash
# 1. 安装
cd .trae/skills/hkt-memory && bash install.sh

# 2. 存储 (指定Scope和Layer)
python3 scripts/hkt_memory_v4.py store \
  --content "用户偏好使用Python" \
  --scope agent:myagent \
  --layer L2

# 3. 检索 (自适应混合检索)
python3 scripts/hkt_memory_v4.py retrieve \
  --query "Python偏好" \
  --scope global,agent:myagent
```

## 🏗️ 核心概念

### 存储层 (Layer)
| 层级 | 用途 | 适用场景 |
|------|------|----------|
| **L2** | 完整内容 | 重要决策、用户偏好 |
| **L1** | 概述摘要 | 会话/项目概览 |
| **L0** | 极简索引 | 快速检索入口 |

### 作用域 (Scope)
| 类型 | 格式 | 说明 |
|------|------|------|
| global | `global` | 全局共享 |
| agent | `agent:<id>` | Agent私有 |
| project | `project:<id>` | 项目级 |

## 🔍 检索模式

```bash
# 混合检索 (默认) - 推荐
python3 scripts/hkt_memory_v4.py retrieve --query "..." --mode hybrid

# 纯BM25 - 代码/专有名词精确匹配
python3 scripts/hkt_memory_v4.py retrieve --query "def calculate" --mode bm25

# 纯向量 - 语义相似
python3 scripts/hkt_memory_v4.py retrieve --query "..." --mode vector
```

> **自适应检索**: 系统自动判断是否需要检索（问候语/短句自动跳过）

## 📝 AGENTS.md 集成

在 `AGENTS.md` 中添加：

```markdown
## 记忆集成 (HKT-Memory v4.5)

**对话前检索:**
```bash
python3 scripts/hkt_memory_v4.py retrieve \
  --query "<当前话题>" \
  --scope global,agent:<agent_id> \
  --limit 3
```

**对话后存储 (重要决策):**
```bash
python3 scripts/hkt_memory_v4.py store \
  --content "<关键决策>" \
  --layer L2 \
  --scope agent:<agent_id>
```

**触发词**: "记得/之前/上次" → 强制检索 | 问候语/短句 → 跳过
```

## 📚 完整文档

| 文档 | 内容 | 路径 |
|------|------|------|
| **DESIGN.md** | 架构设计、6阶段管道、性能对比 | [DESIGN.md](./DESIGN.md) |
| **API.md** | 完整CLI参考、所有参数说明 | [API.md](./API.md) |

## 🔧 常用命令

```bash
# 基础操作
python3 scripts/hkt_memory_v4.py store --content "..." --scope agent:id
python3 scripts/hkt_memory_v4.py retrieve --query "..." --mode hybrid
python3 scripts/hkt_memory_v4.py stats

# 高级功能
python3 scripts/hkt_memory_v4.py test-retrieval --query "..."
python3 scripts/hkt_memory_v4.py bm25 optimize
```

---
**当前版本**: v4.5 | **依赖**: Python 3.8+, SQLite, 智谱AI API
