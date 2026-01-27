# Spec 01: Design Parser (设计解析器)

## 目标
实现对 Sketch 设计文件的深度解析，提取图层结构、样式信息和资源数据，将其转换为标准化的中间 JSON 格式 (Intermediate Layout JSON)，为后续的可视化编辑和代码生成提供数据基础。

## 核心功能
1.  **Sketch File Parsing**:
    - 解压 `.sketch` 文件。
    - 读取 `document.json`, `meta.json`, `user.json` 和 `pages/*.json`。
2.  **Layer Extraction**:
    - 提取 Artboard (画板), Group (组), Text (文本), Shape (形状), Image (图片) 等图层信息。
    - 保留图层层级关系。
3.  **Style Extraction**:
    - 提取 Fill (填充), Border (边框), Shadow (阴影), TextStyle (字体样式), Opacity (透明度)。
4.  **Resource Handling**:
    - 提取内嵌图片资源，并支持 Base64 编码或文件路径导出。
5.  **Layout Processing**:
    - 计算绝对坐标 (Absolute Coordinates) 和尺寸 (Size)。
    - 处理 Sketch 的 Group 偏移量。
6.  **Layout Correction (人工干预)**:
    - 读取可选的 `layout.json` 修正文件。
    - 根据修正规则（如强制类型转换、手动指定边距/对齐、忽略图层等）覆盖自动解析结果。
    - 解决自动推断无法完美还原复杂布局（如 Icon 错位、Padding 丢失）的问题。

## 输入
- Sketch File (.sketch)
- [Optional] Layout Correction File (`layout.json`): 包含人工修正规则的 JSON 文件。

## 输出
- Intermediate Layout JSON (包含完整图层树和样式信息的 JSON 对象)
- Assets (图片文件)
