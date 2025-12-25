---
id: flutter-ui-visual-fidelity-skill
status: proposed
created: 2025-12-25
title: Flutter UI Visual Fidelity Skill
authors:
  - Trae
---

# Proposal: Flutter UI Visual Fidelity Skill

## Why
Flutter 的非 UI 逻辑（业务/数据流）相对容易做到“稳定且精准”的代码输出；但 UI 视觉还原具有强不确定性：同样的提示词可能产出不同布局结构，且难以持续对齐设计师意图。

我们希望把“UI 还原”从开放式生成收敛成工程化的确定性流程：工程师通过可视化标注工具把设计输入（效果图 + 切图 + 开发描述）补齐为结构化元数据（LayoutSpec），再由该元数据驱动 Flutter UI 代码生成与运行态元数据对比，形成可重复、可迭代的闭环。

该方案完全不依赖视觉模型；主闭环只使用机器可读的结构化元数据，避免 AI IDE 解析截图带来的不稳定性。

## What Changes
- 新增一个面向 Flutter 研发的 OpenSkills Skill：Flutter UI Visual Fidelity（暂定名），用于把视觉还原约束成确定性的输入/输出合同。
- 定义结构化中间表示 LayoutSpec（JSON/YAML），用于描述切图与控件映射、控件类型/类名、布局参数与样式 token。
- 定义运行态元数据导出机制：生成页面中注入仅 debug 生效的临时 dump 按钮，导出 `runtime.json`（node 级渲染位置/尺寸/文本测量/图片 fit 等）。
- 定义结构化差异报告：对比 LayoutSpec 与 runtime.json，输出 `layout-diff.json`，驱动 AI 做“定向 patch”而非推倒重来。
- 将该 skill 以 fork 官方 skills 仓库并跟随上游更新的方式分发与版本化。

## ADDED Requirements

本提案包含 5 个独立的子 Specs，涵盖了从资源解析到最终验证的完整闭环：

1.  **[01-design-parser](specs/01-design-parser/spec.md)**: 负责解析原始设计资源。
2.  **[02-visual-editor](specs/02-visual-editor/spec.md)**: 提供可视化交互界面与服务。
3.  **[03-code-generator](specs/03-code-generator/spec.md)**: 负责确定性的 Flutter 代码生成与埋点。
4.  **[04-runtime-bridge](specs/04-runtime-bridge/spec.md)**: 负责 Flutter 运行时的元数据采集。
5.  **[05-diff-engine](specs/05-diff-engine/spec.md)**: 负责差异对比与反馈闭环。

详见各子 Spec 文件。

## Impact
- **Deterministic UI**: Eliminates prompt-based randomness in UI structure.
- **Verifiable Output**: `runtime.json` provides ground truth for pixel-perfect verification.
- **No Extra AI Cost**: Removes dependency on expensive/unstable visual models.
- **Workflow**: Requires a "Design -> Annotate -> Generate -> Verify" workflow, slightly more upfront effort for high-fidelity results.
