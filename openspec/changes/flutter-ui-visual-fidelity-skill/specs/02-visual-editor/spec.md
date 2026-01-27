# Spec 02: Visual Editor (可视化编辑器)

## 目标
提供一个基于 Web 的可视化编辑环境，用于导入 Sketch 设计稿，查看解析后的图层结构，进行人工微调（如标记组件、调整布局参数），并最终导出符合规范的 Layout JSON。

## 核心功能
1.  **Import**: 上传并解析 Sketch 文件 (调用 Spec 01 Parser)。
2.  **Visualize**: 渲染图层树，展示属性 (X, Y, Width, Height, Style)。
3.  **Edit**:
    - **Layout Tweaking**: 修改位置、尺寸、Padding、Alignment。
    - **Logic Hooks**: 标记动态属性 (IsDynamic)，关联业务逻辑参数。
    - **Component Marking**: 标记复用组件。
4.  **Correction Management**:
    - 记录用户对布局的修改（如 "将此 Group 强制设为 VStack"，"手动设置 Margin-Top 为 20px"）。
    - 生成 `layout.json` 修正文件，以便下次解析同一 Sketch 文件时复用这些修正。
5.  **Export**: 
    - 生成清洗后的 Layout JSON，作为 Spec 03 DSL Generator 的输入。
    - 导出 `layout.json` 供 Parser 使用。

## 输入
- Sketch File (.sketch)

## 输出
- Layout JSON (Raw UI Tree)
- Layout Correction File (`layout.json`)
