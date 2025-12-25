# Spec 01: 设计资源解析器 (Design Parser)

## ADDED Requirements

### Requirement: Direct Design File Parsing
The component SHALL support parsing design source files directly (e.g., .sketch, .skp) to extract structure and assets, eliminating the need for manual metadata export.

#### Scenario: Direct Sketch File Parsing
- **GIVEN** a valid `.sketch` file (which is a ZIP of JSONs)
- **WHEN** the parser processes the file
- **THEN** it SHALL unzip the archive in memory.
- **AND** parse `pages/*.json` to extract layer hierarchy, bounds, and style properties.
- **AND** generate a `manifest.json` and initial `layout_spec.json` directly from the source.

#### Scenario: Skia Picture Parsing (Experimental)
- **GIVEN** a `.skp` (Skia Picture) file provided as a source
- **WHEN** the parser processes the file
- **THEN** it SHALL use Skia tools (e.g., `skia_python` or `flutter` CLI) to deserialize the draw commands.
- **AND** extract accessible drawing primitives (Rects, Images, Text) to form a structural guess.

### Requirement: 资源完整性校验
该组件必须 (`SHALL`) 在处理前校验输入资源的完整性。

#### Scenario: 缺失关键文件
- **GIVEN** 一个缺少 `design.png` 的输入目录
- **WHEN** 运行解析器
- **THEN** 抛出明确错误 "Missing design.png reference image"。
