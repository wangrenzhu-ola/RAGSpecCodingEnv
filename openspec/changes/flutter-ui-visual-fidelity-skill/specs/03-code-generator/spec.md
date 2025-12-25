# Spec 03: 代码生成器 (Code Generator)

## ADDED Requirements

### Requirement: 确定性代码生成
该组件必须 (`SHALL`) 严格根据 `layout_spec.json` 生成 Flutter 代码，不包含随机性。

#### Scenario: 节点到 Widget 的映射
- **GIVEN** LayoutSpec 中定义了一个类型为 `Container` 的节点，带有背景色 `#FF0000` 和圆角 `8px`
- **WHEN** 运行代码生成器
- **THEN** 生成 Dart 代码 `Container(decoration: BoxDecoration(color: Color(0xFFFF0000), borderRadius: BorderRadius.circular(8)))`。
- **AND** 不得随意添加 Spec 中未定义的属性（如阴影或边框）。

### Requirement: 调试埋点注入
生成器必须 (`SHALL`) 在代码中自动注入用于运行时定位和导出的标识符。

#### Scenario: 自动 Key 生成
- **WHEN** 生成任何对应的 Widget 代码
- **THEN** 必须添加 `key: Key('vf:<node_id>')` 属性。

#### Scenario: 调试按钮注入
- **WHEN** 生成根页面 Scaffold
- **THEN** 必须在 `floatingActionButton` 或 `overlay` 中注入 `VisualFidelityDumper` 触发按钮。
- **AND** 该按钮代码必须被 `if (kDebugMode)` 包裹，确保不影响 Release 包。
