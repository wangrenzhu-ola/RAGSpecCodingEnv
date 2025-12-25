# Spec 04: 运行时桥接 (Runtime Bridge)

## ADDED Requirements

### Requirement: 运行时数据采集
该组件必须 (`SHALL`) 提供 Dart 运行时库，用于提取当前页面的渲染元数据。

#### Scenario: 遍历 RenderObject
- **WHEN** 触发数据导出
- **THEN** 必须通过 `find.byKey` 查找所有以 `vf:` 开头的 Element。
- **AND** 提取其对应的 `RenderObject` 的 `localToGlobal` 坐标、`size` 和 `runtimeType`。

#### Scenario: 文本与图片元数据
- **GIVEN** 一个 Text 节点
- **WHEN** 导出数据时
- **THEN** 必须包含 `fontSize`, `fontFamily`, `text` 内容以及实际渲染的文本边界。

### Requirement: 数据输出通道
该组件必须 (`SHALL`) 将采集到的数据可靠地传输到外部。

#### Scenario: 输出 runtime.json
- **WHEN** 数据采集完成
- **THEN** 将数据序列化为 JSON 字符串。
- **AND** 通过 `debugPrint` 输出到控制台（带有特定起始/结束标记以便 CLI 抓取）。
- **OR** 写入应用沙盒的 `Documents` 目录供 `adb pull` 获取。
