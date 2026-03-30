# OP-AI-WORKSPACE（OpenSkills + OpenSpec 标准化 AI 开发环境）

这是一套“可一键初始化”的 AI Coding 工作区标准，把两类能力组合在一起，让团队在成熟项目里也能稳定使用 AI 编程。

- **OpenSkills**：把可复用的“技能/操作规程”标准化成 `SKILL.md`，并同步到 `AGENTS.md`，让 AI 按需加载、可发现、可复用。
- **OpenSpec**：把需求/意图从聊天记录里“抽出来”，落在 `openspec/` 里做成可评审、可归档的规格与变更提案，减少跑偏与返工。

## 🔥 HKT-memory v4.5 更新速览（置顶）

- **核心变化**：对标 LanceDB Pro，实现完整的 6 阶段检索管道 (Adaptive → Hybrid → Rerank → Lifecycle → MMR → Scope Filter)。
- **新增能力**：
  - **BM25 全文检索**：SQLite FTS5 + 中文分词 (jieba)，代码/专有名词召回率 40%→80%+
  - **混合融合**：Vector(0.7) + BM25(0.3) Fusion，可配置权重
  - **自适应检索**：智能跳过问候/短句查询，强制关键词触发
  - **MMR 多样性**：相似度>0.85 降权，增加结果多样性
  - **Multi-Scope 隔离**：global/agent/project/user 多租户隔离
- **CLI 增强**：新增 `--mode hybrid/bm25/vector`、`--scope`、`--min-score`、`--mmr-threshold` 等参数
- **完整文档**：见 [hkt-memory/SKILL.md](./hkt-memory/SKILL.md)

---

### 历史版本
- [HKT-memory v3](./HKT-memory-v3-release.md)：Query Routing + Graph 扩展
- [HKT-memory v2](./HKT-memory-v2-release.md)：混合检索基础版

## 解决什么问题

- 需求在聊天里反复变更，AI 实现容易“漂移” → 用 OpenSpec 把 intent 锁定成规格/提案，先对齐再编码。
- 团队/多人/多工具切换时提示词难复用、难管理 → 用 OpenSkills 把能力模块化成 skill，集中管理并同步进 AI 上下文入口。
- 项目越成熟越难改、上下文越大越容易漏边界条件 → 用 specs 作为“系统行为真相”，让改动可审计、可追溯。

## 一键初始化（推荐：在目标工程目录执行）

在任意目标工程根目录，执行下面一段即可把该项目初始化为 AI 工作区：

```bash
curl -fsSL https://raw.githubusercontent.com/olaola-chat/OP-AI-SPEC-CODING-ENV/main/init-ai-env.sh -o init-ai-env.sh \
  && chmod +x init-ai-env.sh \
  && ./init-ai-env.sh
```

说明：

- 初始化会在项目里创建/更新少量文件与目录：`AGENTS.md`、`openspec/`、`.ai-env/`、`.claude/skills/`（细节见下文）。

如果你更偏好“clone & 执行”：

```bash
git clone https://github.com/olaola-chat/OP-AI-SPEC-CODING-ENV.git /tmp/op-ai-workspace \
  && cp /tmp/op-ai-workspace/init-ai-env.sh ./init-ai-env.sh \
  && chmod +x ./init-ai-env.sh \
  && ./init-ai-env.sh
```

## 成熟项目如何集成？

可以直接集成。推荐做法是：

1. 进入成熟项目根目录执行“一键初始化”命令
2. 将 `AGENTS.md` 作为 Trae（以及其他 AI 工具）的上下文入口文件
3. 之后所有“非小改动”的需求，默认走 OpenSpec：先 proposal，再 apply，再 archive

是否需要把脚本 clone 到目标工程？

- **可以，但不是必须**。更推荐用上面的 `curl` 一键拉取脚本并执行，避免每个项目都维护一份脚本副本。

## 初始化后有哪些东西？

- `AGENTS.md`：AI 工作规范入口（Trae 里建议固定让 AI 先读它）
- `openspec/`：规格与变更提案目录
  - `openspec/specs/`：规格真相（source of truth）
  - `openspec/changes/`：变更提案与任务
- `.ai-env/`：在项目内单独安装 openskills/openspec（不污染全局环境，也不干扰项目生产依赖）
- `.claude/skills/`：由 OpenSkills 安装的 skills 目录（OpenSpec skill 会被安装在这里）

## 📦 当前内置技能

初始化脚本默认安装以下核心技能：

### 1. OpenSpec (核心)

这是本环境的“大脑”，负责需求管理与规格定义。

- **能力**：管理 Spec-Driven Development (SDD) 的完整生命周期。
- **解决痛点**：防止 AI 在长对话中丢失上下文或偏离原始需求。

**技能详情 (SKILL.md 内容预览)**：

```markdown
## Capabilities

- **Spec-Driven Development**: You should always look for specs in `openspec/specs/` before coding.
- **Change Management**: All major changes should go through a Proposal -> Implementation -> Archive lifecycle.

## Commands

- **Create Proposal**: `npx openspec proposal "Description of change"`
  - _Trigger_: When user requests a new feature or significant refactor.
- **Apply Change**: `npx openspec apply <change-id>`
  - _Trigger_: When you are ready to implement the code for a proposal.
- **Archive Change**: `npx openspec archive <change-id>`
  - _Trigger_: When implementation is done and verified.
- **List Changes**: `npx openspec changes`
  - _Trigger_: To see what is currently in progress.

## Workflow Rules

1. **Always Check Specs**: Before writing code, read relevant specs in `openspec/specs/`.
2. **Propose First**: For non-trivial changes, create a proposal first using `npx openspec proposal`.
3. **Update Specs**: Keep specs as the source of truth.
```

### 2. HKT 记忆引擎（v4.5 生产级检索）

基于 LanceDB Pro 架构的完整长期记忆系统，支持 6 阶段检索管道：

- **BM25 全文检索**：SQLite FTS5 + 中文分词，精确匹配代码/专有名词
- **混合融合检索**：Vector(0.7) + BM25(0.3) 权重可调
- **自适应检索**：智能判断是否需要检索（跳过问候/短句）
- **Cross-Encoder 重排序**：Jina/SiliconFlow API 支持
- **Weibull Decay 生命周期**：Core/Working/Peripheral 三层衰减
- **MMR 多样性优化**：自动降低重复结果权重
- **Multi-Scope 隔离**：global/agent/project/user 作用域隔离
- **L0/L1/L2 分层存储**：渐进式披露，快速检索

**快速使用**：
```bash
# 存储记忆（带scope）
python3 hkt-memory/scripts/hkt_memory_v4.py store \
  --content "用户偏好Python开发" \
  --scope agent:myagent

# 混合检索
python3 hkt-memory/scripts/hkt_memory_v4.py retrieve \
  --query "Python框架" \
  --mode hybrid \
  --scope global,agent:myagent

# 测试检索管道
python3 hkt-memory/scripts/hkt_memory_v4.py test-retrieval \
  --query "记得上次说的配置吗"
```

- **详情**：见 [SKILL.md](./hkt-memory/SKILL.md)

### 3. Anthropic 官方技能 (推荐)

通过 `npx openskills install anthropics/skills` 安装，包含以下强大能力：

#### 📄 文档处理技能 (Document Skills)

| 技能名   | 描述                                                                            |
| -------- | ------------------------------------------------------------------------------- |
| **docx** | 创建、编辑和分析 Word 文档。支持修订跟踪、评论、格式保留和文本提取。            |
| **pdf**  | 综合 PDF 处理工具包。支持提取文本/表格、创建新 PDF、合并/拆分文档以及表单处理。 |
| **pptx** | 创建、编辑和分析 PowerPoint 演示文稿。支持布局、模板、图表和自动化幻灯片生成。  |
| **xlsx** | 创建、编辑和分析 Excel 电子表格。支持公式、格式化、数据分析和可视化。           |

#### 🎨 设计与创意 (Design & Creative)

| 技能名                | 描述                                                    |
| --------------------- | ------------------------------------------------------- |
| **algorithmic-art**   | 使用 p5.js 创建生成艺术，支持随机种子、流场和粒子系统。 |
| **canvas-design**     | 使用设计哲学创建精美的 .png 和 .pdf 格式视觉艺术。      |
| **slack-gif-creator** | 创建针对 Slack 尺寸约束优化的动画 GIF。                 |

#### 💻 开发工具 (Development)

| 技能名                | 描述                                                                            |
| --------------------- | ------------------------------------------------------------------------------- |
| **frontend-design**   | 指导 AI 避免“AI 垃圾代码”，做出大胆的设计决策。特别适用于 React & Tailwind。    |
| **artifacts-builder** | 使用 React、Tailwind CSS 和 shadcn/ui 组件构建复杂的 HTML 制品。                |
| **mcp-builder**       | 创建高质量 MCP (Model Context Protocol) 服务器的指南，用于集成外部 API 和服务。 |
| **webapp-testing**    | 使用 Playwright 进行本地 Web 应用的 UI 验证和调试。                             |

#### 📢 沟通与品牌 (Communication)

| 技能名               | 描述                                                          |
| -------------------- | ------------------------------------------------------------- |
| **brand-guidelines** | 将官方品牌颜色和排版应用到生成的制品中。                      |
| **internal-comms**   | 撰写内部沟通文档，如状态报告、时事通讯和常见问题解答 (FAQs)。 |

#### 🛠️ 技能创建 (Skill Creation)

| 技能名            | 描述                                                 |
| ----------------- | ---------------------------------------------------- |
| **skill-creator** | 交互式技能创建工具，通过问答引导你构建新的 AI 技能。 |

### 4. Community 增强技能 (高级专家角色)

通过初始化脚本自动安装，引入了大量 "Senior" 级别的专家角色与工具，覆盖研发、产品、管理与合规四大领域：

#### 👨‍💻 高级工程师角色 (Engineering & Architecture)

| 技能名                     | 描述                                                  |
| -------------------------- | ----------------------------------------------------- |
| **senior-architect**       | 系统架构师，提供技术选型、设计模式与系统设计建议。    |
| **aws-solution-architect** | AWS 解决方案架构师，专注于云原生架构设计。            |
| **senior-fullstack**       | 全栈开发专家，精通前后端集成与最佳实践。              |
| **senior-backend**         | 后端专家，专注于高性能、可扩展的后端系统设计。        |
| **senior-frontend**        | 前端专家，专注于现代前端架构与用户体验。              |
| **senior-devops**          | DevOps 专家，涵盖 CI/CD、基础设施即代码与云原生技术。 |
| **senior-secops**          | 安全运维专家，专注于系统安全与合规。                  |
| **senior-security**        | 高级安全专家，负责应用与数据安全策略。                |
| **senior-data-engineer**   | 高级数据工程师，专注于数据管道与数仓建设。            |
| **senior-data-scientist**  | 高级数据科学家，专注于数据分析与建模。                |
| **senior-ml-engineer**     | 机器学习工程师，专注于模型训练与部署。                |
| **senior-computer-vision** | 计算机视觉专家，专注于图像处理与视觉算法。            |
| **senior-prompt-engineer** | 提示词工程专家，优化 LLM 交互与输出质量。             |
| **senior-qa**              | 高级 QA 工程师，制定测试策略与质量保障体系。          |
| **ms365-tenant-manager**   | Microsoft 365 租户管理专家。                          |

#### 🛠 质量与评估 (Quality & Evaluation)

| 技能名                   | 描述                                                   |
| ------------------------ | ------------------------------------------------------ |
| **code-reviewer**        | 自动代码审查工具，识别潜在 bug、安全漏洞与代码坏味道。 |
| **tdd-guide**            | 测试驱动开发向导，指导编写高质量的测试用例与实现。     |
| **tech-stack-evaluator** | 技术栈评估工具，分析引入新库或框架的利弊与适用性。     |

#### 💼 管理与战略 (Management & Strategy)

| 技能名          | 描述                                       |
| --------------- | ------------------------------------------ |
| **ceo-advisor** | CEO 顾问，提供企业战略与商业决策支持。     |
| **cto-advisor** | 技术战略顾问，提供技术愿景与团队管理建议。 |

#### 🚀 产品与营销 (Product & Marketing)

| 技能名                           | 描述                                                     |
| -------------------------------- | -------------------------------------------------------- |
| **product-manager-toolkit**      | 产品经理工具箱，辅助需求分析、用户故事编写与优先级管理。 |
| **agile-product-owner**          | 敏捷 PO 角色，负责 Backlog 管理与迭代规划。              |
| **product-strategist**           | 产品战略专家，制定产品路线图与市场定位。                 |
| **marketing-strategy-pmm**       | 产品营销策略专家，负责 GTM 策略与市场推广。              |
| **marketing-demand-acquisition** | 市场获客专家，专注于流量获取与转化率优化。               |
| **app-store-optimization**       | ASO 专家，优化应用商店排名与转化。                       |
| **content-creator**              | 内容创作者，辅助生成营销文案与内容策略。                 |
| **social-media-analyzer**        | 社交媒体分析师，分析社媒趋势与用户反馈。                 |
| **ux-researcher-designer**       | UX 研究与设计专家，关注用户体验与交互设计。              |
| **ui-design-system**             | UI 设计系统专家，构建一致的视觉规范与组件库。            |

#### ⚖️ 合规与法规 (Compliance & Regulatory)

| 技能名                                    | 描述                                         |
| ----------------------------------------- | -------------------------------------------- |
| **gdpr-dsgvo-expert**                     | GDPR/DSGVO 合规专家，确保数据隐私合规。      |
| **information-security-manager-iso27001** | ISO 27001 信息安全管理专家。                 |
| **quality-manager-qms-iso13485**          | ISO 13485 医疗器械质量管理专家。             |
| **quality-manager-qmr**                   | 质量管理代表 (QMR)，负责质量体系运行。       |
| **quality-documentation-manager**         | 质量文档管理专家，维护合规文档体系。         |
| **qms-audit-expert**                      | 质量管理体系审计专家。                       |
| **isms-audit-expert**                     | 信息安全管理体系审计专家。                   |
| **risk-management-specialist**            | 风险管理专家，识别与评估项目风险。           |
| **regulatory-affairs-head**               | 法规事务负责人，确保产品符合行业法规。       |
| **fda-consultant-specialist**             | FDA 法规顾问，辅助医疗器械 FDA 申报。        |
| **mdr-745-specialist**                    | 欧盟 MDR (2017/745) 法规专家。               |
| **capa-officer**                          | CAPA (纠正预防措施) 专员，处理质量问题闭环。 |

### 扩展更多技能

本环境基于 [OpenSkills](https://github.com/numman-ali/openskills) 构建，你可以随时安装更多社区技能（如 PDF 处理、浏览器自动化等）来增强 AI 能力：

```bash
# 示例：安装 Anthropic 官方技能库
npx openskills install anthropics/skills
```

安装后运行 `npx openskills sync`，新技能就会自动出现在 `AGENTS.md` 中供 AI 使用。

## 最小使用流程（你只要记住这 4 句）

你不需要自己运行 `npx`。这些命令应该由 AI 在需要时自动运行（并把结果文件展示给你审阅）。你只需要用自然语言驱动流程：

1. 让 AI 先读 `AGENTS.md`
2. 让 AI 先做提案/规格对齐（不要直接写代码）
3. 你确认后，让 AI 按规格实现
4. 验证通过后，让 AI 归档（把变更沉淀进 specs）

更多细节见 [AI_WORKFLOW_GUIDE.md](./AI_WORKFLOW_GUIDE.md)。

## 初始化后如何验证能力可用？

把下面这段话复制到 Trae 的 AI 对话里（建议在目标工程根目录执行完初始化后立刻验证）：

> 请先阅读并遵守当前仓库的 `AGENTS.md`。然后列出你能使用的 skills，并加载 OpenSpec skill。接着为“新增 /healthz 健康检查接口（仅规划，不写代码）”创建一个 OpenSpec proposal，并告诉我在 `openspec/changes/` 下生成了哪些文件、proposal 的 change-id 是什么，以及我下一步应该如何审阅它。
