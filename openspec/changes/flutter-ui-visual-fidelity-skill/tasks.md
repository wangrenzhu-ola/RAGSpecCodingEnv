# Master Task List: Flutter UI Visual Fidelity Skill

> 本文档为总任务索引。每个子模块的详细任务清单请参考各 `specs/XX-name/tasks.md` 文件。

## 1. Phase 1: 核心解析与可视化 (Design Parser & Visual Editor)
目标：能够解析 Sketch 文件，并在 Web 界面中精准还原，同时提供开发绑定功能。

- [ ] **Spec 01: Design Parser** ([详细任务](./specs/01-design-parser/tasks.md))
    - [ ] Sketch 解压与 JSON 解析
    - [ ] 约束推断 (Flex/Padding)
    - [ ] 资源导出
- [ ] **Spec 02: Visual Editor** ([详细任务](./specs/02-visual-editor/tasks.md))
    - [ ] Web 画布渲染
    - [ ] 属性面板 (Constraint 配置)
    - [ ] **Dev Binding 界面** (类名映射/代码注入)
    - [ ] 保存 LayoutSpec

## 2. Phase 2: 代码生成与桥接 (Code Gen & Runtime Bridge)
目标：基于绑定信息生成高质量 Flutter 代码，并建立运行时数据提取通道。

- [ ] **Spec 03: Code Generator** ([详细任务](./specs/03-code-generator/tasks.md))
    - [ ] Widget 模板映射
    - [ ] **基于 Binding 的组件抽离**
    - [ ] 调试 Key 注入
- [ ] **Spec 04: Runtime Bridge** ([详细任务](./specs/04-runtime-bridge/tasks.md))
    - [ ] `visual_fidelity_bridge` 库开发
    - [ ] RenderTree 遍历与数据导出

## 3. Phase 3: 闭环验证 (Diff Engine & Integration)
目标：实现设计与实现的自动对比，计算还原度。

- [ ] **Spec 05: Diff Engine** ([详细任务](./specs/05-diff-engine/tasks.md))
    - [ ] 节点匹配与属性对比
    - [ ] 可视化报告生成
- [ ] **Integration**
    - [ ] CLI 命令串联 (`parse` -> `editor` -> `codegen` -> `diff`)
    - [ ] E2E 测试流程验证
