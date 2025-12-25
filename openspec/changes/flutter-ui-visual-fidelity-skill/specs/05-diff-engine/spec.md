# Spec 05: 差异对比引擎 (Diff Engine)

## ADDED Requirements

### Requirement: 结构化差异计算
该组件必须 (`SHALL`) 对比 `LayoutSpec` (设计意图) 和 `runtime.json` (运行结果)，输出量化的差异报告。

#### Scenario: 几何差异检测
- **GIVEN** 设计节点 A 宽度为 100，运行时节点 A 宽度为 90
- **WHEN** 运行 Diff 引擎
- **THEN** 输出差异项 `{ nodeId: "A", property: "width", expected: 100, actual: 90, delta: -10 }`。

#### Scenario: 阈值过滤
- **GIVEN** 设定允许误差为 0.5px
- **WHEN** 实际误差为 0.3px
- **THEN** 该差异项被忽略或标记为 "PASS"。

### Requirement: 反馈闭环支持
该组件必须 (`SHALL`) 支持将差异报告转换回 Visual Editor 可识别的格式，以便在编辑器中高亮显示问题区域。

#### Scenario: 差异可视化数据生成
- **WHEN** 差异计算完成
- **THEN** 生成 `diff_overlay.json`。
- **AND** Visual Editor 读取该文件后，能在画布上用红色边框标记出偏差过大的节点。
