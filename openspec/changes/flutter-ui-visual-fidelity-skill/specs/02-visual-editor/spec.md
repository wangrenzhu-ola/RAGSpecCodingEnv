# Spec 02: 可视化编辑器与服务 (Visual Editor & Service)

## ADDED Requirements

### Requirement: 交互式标注界面
该组件必须 (`SHALL`) 提供一个 Web 界面，允许用户在设计图上可视化地绑定切图和设置布局参数。

#### Scenario: 拖拽绑定切图
- **GIVEN** 解析后的设计图展示在画布上，右侧列出未绑定的切图资源
- **WHEN** 用户将切图拖拽到画布的特定区域
- **THEN** 在该区域生成一个控件节点 (Node)。
- **AND** 自动记录该节点的 `bounds` (x, y, w, h) 和关联的 `assetId`。

#### Scenario: 布局约束配置
- **GIVEN** 画布上已选中的一个控件节点
- **WHEN** 用户在属性面板设置 Padding/Margin 或 Flex 比例
- **THEN** 实时更新该节点的 `LayoutSpec` 数据。

### Requirement: 自动化服务部署
该编辑器必须 (`SHALL`) 能够作为一个独立的本地服务自动启动，无需用户配置复杂的环境。

#### Scenario: 一键启动
- **WHEN** 用户运行 `openskills run flutter-ui-visual-fidelity`
- **THEN** 自动启动本地 HTTP 服务 (e.g., localhost:3000)。
- **AND** 自动打开浏览器并加载当前项目的设计资源。

### Requirement: 结构化数据二次生成
编辑器必须 (`SHALL`) 支持保存操作，将画布上的可视状态序列化为最终的 `layout_spec.json`。

#### Scenario: 保存 LayoutSpec
- **WHEN** 用户点击“保存”或“生成”按钮
- **THEN** 校验所有必填字段（如根节点类型）。
- **AND** 将内存中的状态写入磁盘上的 `layout_spec.json` 文件。
