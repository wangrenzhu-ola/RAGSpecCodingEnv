id: leaf-20260227T0642-embedding-501-排查与智谱-bigmodel-配置
title: embedding 501 排查与智谱 bigmodel 配置
status: 现行
confidence: 中
scope: 默认
created_at: 2026-02-27T06:42:36.645569
updated_at: 2026-02-27T06:42:36.645569
source: conversation-2026-02-27
content:
- 当前环境 OPENAI_BASE_URL=http://127.0.0.1:8000/v1 会把 embeddings POST 打到本地服务，返回 501(Unsupported method POST)
- 智谱 GLM Embedding 正确 endpoint: https://open.bigmodel.cn/api/paas/v4/embeddings；建议设置 OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
- 设置 HKT_MEMORY_MODEL=embedding-3；OPENAI_API_KEY 使用 bigmodel token；http_proxy/https_proxy 仅作为代理，不应写进 OPENAI_BASE_URL
- 已增强混合检索健壮性：embedding 不可用时自动退化为 FTS5 关键词检索；并对 FTS 查询做安全清洗避免 hkt-memory 触发 SQL 错误
