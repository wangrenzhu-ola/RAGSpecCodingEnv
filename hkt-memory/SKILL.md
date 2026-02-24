---
name: "hkt-memory"
description: "基于 HKT 树状记忆系统的渐进式披露与主动检索指南。用户要求储存/检索记忆或需要上下文管理时调用。"
---

# HKT 记忆引擎（渐进式披露）

## 使用场景

- 当用户要求“保存记忆/写入记忆/持久化上下文/记住偏好”时调用。
- 当任务需要长期上下文管理、跨会话追踪或避免上下文过载时调用。
- 当需要像“先看说明书再深入细节”的方式做检索与决策时调用。
- 当每次对话结束需要自动沉淀关键信息，并在后续对话中可检索时调用。

## 目标

- 先大后小：先定位 Root（大原则），再定位 Branch（具体主题），最后精确到 Leaf（案例或事实）。
- 主动发现：像读取 AGENTS.md 的技能说明一样，先检查是否存在相关记忆，再按需展开。
- 控制负载：每次只加载必要层级，避免一次性拉取过多上下文。

## 分类规则（必须）

- Branch 只用于语义分类，不用于“来源记录”。对话轮次/日期等来源信息必须写入 `source` 字段。
- 禁止使用泛化 Branch（例如：对话记录/临时/其他/misc/temp/conversation）。出现此类输入时必须重新分类或自动纠正。
- 当一条记忆包含多个主题时，必须拆分为多条 Leaf，并分别写入对应 Branch（每轮最多 3 条 Leaf）。
- 优先复用已有 Branch；只有当主题长期稳定且确实缺少分支时，才新增 Branch。

## LLM 自分类输出（推荐）

- 分类决策由 LLM 完成，脚本负责“落盘 + 校验 + 纠偏（拒绝泛化分支）”。
- LLM 在写入前 SHOULD 先输出一个分类结果，再用脚本逐条写入 Leaf。

分类输出建议 Schema（示意）：

```json
{
  "root": "HKT记忆系统",
  "root_summary": "HKT 树状记忆系统（渐进式披露 + 主动发现）",
  "leaves": [
    {
      "branch": "验收与测试",
      "branch_summary": "验收标准、测试流程与示例结果",
      "title": "本轮对话关键记忆（hkt-memory 代码化存取）",
      "confidence": "高",
      "scope": "AI IDE 记忆管理",
      "source": "conversation-YYYY-MM-DD",
      "content": ["要点1", "要点2"]
    }
  ]
}
```

## 树状结构定义

- Root：高层原则/长期稳定信息，例如“产品定位”“长期偏好”“工程规范”。
- Branch：Root 下的主题分支，例如“部署流程”“验证方式”“记忆写入策略”。
- Leaf：具体事实/案例/一次性记录，例如“某次部署失败的原因”“某次调整后的命令”。

## 存储介质与目录结构

- 默认以文档化方式管理记忆，存放在仓库内的固定目录。
- 建议目录结构（不自动创建，仅作为规范）：
  - `memory/index.md`：Root 索引与摘要，仅包含 Root 列表与一句话说明。
  - `memory/<root>/index.md`：Root 概要与 Branch 列表。
  - `memory/<root>/<branch>/index.md`：Branch 概要与 Leaf 索引。
  - `memory/<root>/<branch>/<leaf-id>.md`：具体 Leaf 记忆文档。
- Leaf 文档必须包含最小字段：`id`、`title`、`content`、`source`、`created_at`、`status`。

## 代码化存取方式

- 使用脚本统一写入与检索：`.trae/skills/hkt-memory/scripts/hkt_memory.py`
- 初始化索引：
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py init`
- 分类建议（用于渐进式披露写入前的 Root/Branch 选择）：
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py suggest --root <root> --title <title> --content <item>`
- 写入 Leaf：
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py add --root <root> --branch <branch> --title <title> --content <item>`
  - 可选参数：`--root-summary` `--branch-summary` `--auto-classify` `--status` `--confidence` `--scope` `--source` `--id`
- 重新归类（用于修复错误分类，避免污染知识库）：
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py reclassify --id <leaf-id> --branch <new-branch> [--root <new-root>]`
- 渐进式检索：
  - `python .trae/skills/hkt-memory/scripts/hkt_memory.py query --root <root> --branch <branch> --keyword <kw> --depth <1|2|3> --limit <n>`

## 默认分类建议（HKT记忆系统 Root）

- Root：HKT记忆系统
  - Branch：验收与测试（验收标准、测试流程、示例结果）
  - Branch：工具与脚本（CLI/脚本实现、命令使用）
  - Branch：存储结构（目录结构、索引文件）
  - Branch：检索与披露（depth/limit、渐进式披露策略）
  - Branch：格式与约束（字段模板、冲突处理、规范化输出）
  - Branch：知识管理（分类、裁剪、归档与维护）

## 对话结束自动写入流程

1. 汇总本轮对话的关键信息，只保留可复用与可验证的事实或规则。
2. 将信息映射到 Root/Branch/Leaf：
   - Root：高层稳定主题
   - Branch：单一话题分支
   - Leaf：本轮新增事实/规则/结论
3. 对 Leaf 执行“稳定性评估”：
   - 若为短期、一次性、不可复用信息，则不写入。
   - 若为可复用规则或高价值事实，则写入。
4. 冲突合并：
   - 与现有 Leaf 冲突时保留双版本，并标注“现行/过期”。
5. 生成最小记忆记录集：
   - 每轮写入不超过 3 条 Leaf。

## 存储与命名规范

- 记忆以树状结构组织，Root/Branch/Leaf 必须具有稳定的唯一标识。
- Root 使用语义稳定、可长期复用的名称。
- Branch 聚焦单一主题，避免把多个主题混在同一分支。
- Leaf 描述必须可验证、可追溯，尽量包含来源或上下文锚点。
- Leaf 文件名使用 `leaf-YYYYMMDD-HHMM-<slug>.md`，确保可追踪与去重。

## 渐进式披露检索流程

1. 识别用户意图并归类到 Root（若不确定，创建候选 Root 列表并选择最匹配项）。
2. 仅加载 Root 摘要，判断是否需要展开 Branch。
3. 仅加载相关 Branch 摘要，判断是否需要展开 Leaf。
4. 仅在明确需要细节时加载 Leaf，使用最小必要集合返回答案。

## 记忆检索与调用流程

1. 先检索 Root 索引：
   - 若匹配到高置信 Root，仅加载该 Root 摘要。
   - 若无匹配，创建候选 Root 并记录为候选，不直接写入。
2. 再检索 Branch：
   - 仅展开与当前任务高度相关的 Branch 摘要。
3. 最后检索 Leaf：
   - 仅加载与当前问题直接相关的 Leaf。
4. 输出顺序：
   - 先输出 Root 结论，再输出 Branch 与 Leaf 细节。

## 记忆文档模板

```text
id: <leaf-id>
title: <简短标题>
status: <现行|过期>
confidence: <高|中|低>
scope: <适用范围>
created_at: <ISO8601>
source: <对话轮次或文件路径>
content:
  - <要点1>
  - <要点2>
```

## 主动发现规则

- 优先查 Root 与 Branch 的索引摘要，而不是直接读取 Leaf。
- 当用户提到稳定偏好/长期规则/跨会话信息时，必须先查 Root。
- 当 Root 匹配度不足时，再扩展到相邻 Root 或创建新 Root。

## 记忆写入规则

- 只有在信息稳定、可复用、对后续任务有价值时写入 Leaf。
- 写入 Leaf 时必须关联 Root 与 Branch，避免“孤立记忆”。
- 冲突处理：若新信息与旧 Leaf 冲突，保留两条并标注“现行/过期”，或合并为新的 Leaf，旧 Leaf 标为过期。

## 记忆评估标准

- 价值：能显著提升后续任务效率或决策质量。
- 稳定：预计在多轮对话中保持有效。
- 可验证：来源清晰，能追溯上下文或依据。
- 可重用：在不同任务中仍然适用。

## 记忆选择与裁剪

- 优先返回最近更新且与当前任务高度相关的 Leaf。
- 对过期或低价值 Leaf 做归档或合并，保持树的可用性。
- 不允许一次性展开多个 Root 的全部 Branch 或 Leaf。

## 输出行为

- 回答前先简述 Root 层结论，再补充 Branch 与 Leaf 的必要细节。
- 用户未要求细节时，保持 Root 层输出即可。
- 用户要求证据或可执行步骤时，再展开 Leaf。

## 输出格式模板

- Root: <名称> | 摘要: <一句话原则>
  - Branch: <名称> | 摘要: <一句话主题>
    - Leaf: <事实/规则> | 可信度: <高/中/低> | 适用范围: <范围>

## 示例（简要）

- Root：部署与交付
  - Branch：阿里云部署流程
    - Leaf：docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
