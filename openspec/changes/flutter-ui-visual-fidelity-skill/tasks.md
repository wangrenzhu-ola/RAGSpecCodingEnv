## 1. Spec 01: 设计资源解析器
- [ ] 1.1 实现 Image Parser: 读取 design.png 并输出基础尺寸信息
- [ ] 1.2 实现 Asset Scanner: 扫描 assets/ 目录并生成清单
- [ ] 1.3 实现 Design File Parser: 直接解析 .sketch (unzip+json) 或 .skp (Skia)

## 2. Spec 02: 可视化编辑器与服务
- [ ] 2.1 搭建 Web 前端框架 (React/Vue)
- [ ] 2.2 实现画布组件: 支持图片加载、缩放、平移
- [ ] 2.3 实现拖拽交互: 允许将 Asset 拖入画布并记录坐标
- [ ] 2.4 实现属性面板: 编辑 Node 的 Padding/Margin/Flex
- [ ] 2.5 实现本地服务 (Node.js): 提供 API 读写 layout_spec.json

## 3. Spec 03: 代码生成器
- [ ] 3.1 定义 Widget 模板: Container, Text, Image, Row, Column, Stack
- [ ] 3.2 实现 LayoutSpec -> Dart AST 的转换逻辑
- [ ] 3.3 实现 Debug Key 自动注入逻辑

## 4. Spec 04: 运行时桥接
- [ ] 4.1 实现 Dart 库 `visual_fidelity_bridge`
- [ ] 4.2 实现 `dumpRuntimeData()` 方法: 遍历 RenderTree 并序列化
- [ ] 4.3 集成到生成的 Scaffold 代码中

## 5. Spec 05: 差异对比引擎
- [ ] 5.1 实现 JSON Diff 算法: 对比 LayoutSpec vs Runtime.json
- [ ] 5.2 实现误差阈值逻辑 (Tolerance Logic)
- [ ] 5.3 实现 Diff 报告生成器 (用于前端展示)
