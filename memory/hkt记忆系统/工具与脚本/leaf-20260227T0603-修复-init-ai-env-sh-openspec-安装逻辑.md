id: leaf-20260227T0603-修复-init-ai-env-sh-openspec-安装逻辑
title: 修复 init-ai-env.sh OpenSpec 安装逻辑
status: 现行
confidence: 中
scope: 默认
created_at: 2026-02-27T06:03:43.369052
updated_at: 2026-02-27T06:03:43.369052
source: conversation
content:
- 1. 增加 proxy export 确保网络连通。\n2. 将 OpenSpec 克隆目录从 openspec-repo 改为 openspec 以匹配技能名称。\n3. 更新清理逻辑，移除旧的 openspec-repo 技能。\n4. 验证 v1.2.0 tag 存在且有效。
