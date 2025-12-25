## 目标与原则
目标不是让 AI “更会猜”，而是把 UI 还原从不稳定的自由生成，变成可约束、可验证、可迭代的工程流程：

- 确定性输入：效果图 + 切图 + 约束（设备/字号/字体/主题/布局策略）+ 开发描述
- 结构化中间层：LayoutSpec（机器可读）
- 可执行输出：Flutter 页面代码（widget tree + assets + tokens）
- 可验证闭环：运行态元数据导出 + 差异报告，驱动定向修正

## 可行性拆解
### A. “从输入到结构化”的可行性
1) **可视化标注工具（推荐路线：不引入额外 AI 能力）**
- 提供一个可视化界面导入效果图与切图，在画布上框选区域并补齐元数据（控件类型/类名/布局参数/样式 token/资源绑定）
- 产出确定性的 LayoutSpec（而不是依赖模型去“猜”层级与约束），显著提升稳定性与可复用性
- 支持从 Sketch/Figma 导出产物导入，但第一阶段不强绑定某个设计工具：优先支持“效果图 + 切图目录 + 可选 manifest.json”的通用输入

2) **人工标注（兜底）**
- 允许工程师用最少输入直接产出 LayoutSpec（例如用矩形坐标 + 组件类型 + token）
- 保证在没有任何视觉模型能力时仍能运行闭环

### B. “Flutter 运行后读取元数据”的可行性
**运行态元数据导出：可行（强，且更适合 AI IDE）**
- 相比“让 AI IDE 读截图并判断像素差异”，结构化元数据更易被稳定解析与用于定向修正
- **实现机制**：
  1. 在生成 Flutter 代码时，为 LayoutSpec 中的每个 node 生成唯一的 `Key('vf:<nodeId>')`。
  2. 在页面顶层（如 `Scaffold.floatingActionButton` 或 `Overlay`）注入一个仅 debug 模式显示的 `ElevatedButton`。
  3. 按钮点击事件触发遍历：通过 `find.byKey` 或递归遍历 Element Tree，找到所有 `vf:` 开头的节点。
  4. 提取 RenderObject 信息：
     - `globalPaintBounds` (x, y, width, height)
     - `Text` 组件的 `TextPainter` 属性 (fontSize, fontFamily, actual text metrics)
     - `Image` 组件的 `naturalSize` vs `renderSize`
  5. 序列化为 `runtime.json` 并写入 App Documents 目录或通过 `debugPrint` 输出。

```dart
// 示例：注入的 Debug Dump 按钮逻辑
if (kDebugMode)
  FloatingActionButton(
    key: Key('vf-debug-dump'),
    onPressed: () {
      final runtimeData = VisualFidelityDumper.dump(context);
      // 1. 打印到控制台供 IDE 抓取
      debugPrint('VF_RUNTIME_DUMP_START\n${jsonEncode(runtimeData)}\nVF_RUNTIME_DUMP_END');
      // 2. (可选) 写入文件供 adb pull
      File('${docDir.path}/runtime.json').writeAsStringSync(jsonEncode(runtimeData));
    },
    child: Icon(Icons.bug_report),
  )
```

**页面结构读取：可选（受限）**
- debug 模式下可使用 `debugDumpApp()` / `debugDumpRenderTree()` 输出 widget/render tree
- 该输出对机器解析的稳定性不如 `runtime.json`，建议仅作为诊断辅助，而不是主闭环输入

### C. “1:1 还原”的边界条件
严格 1:1 依赖环境一致性。必须先把可变因素锁死，否则 diff 没有意义：
- 目标设备尺寸与 DPR
- 字体文件与字重（含 fallback 字体）
- TextScaleFactor 固定（无系统缩放干扰）
- 主题与颜色空间（暗色/亮色、sRGB）
- 图标与切图导出规则（倍率、裁切、透明边）

建议把“1:1”定义为：在上述约束成立时，运行态元数据与 LayoutSpec 的差异低于阈值（例如每个节点的 x/y/width/height 偏差均 <= 1px，或按控件类型设定不同阈值），并能输出可解释的差异报告（哪些节点偏差、偏差量、可能原因）。

## LayoutSpec（结构化中间表示）
建议输出一个 JSON（或 YAML）作为唯一真相，字段示例（非最终）：

- meta：screenName、targetDevice、dpr、theme、fontAssets、exportRules
- assets：切图清单（路径、尺寸、倍率、用途）
- nodes：控件节点列表（可被稳定映射到 Flutter widget）
  - id、type（Container/Stack/Row/Column/Text/Image/Button/Custom）
  - bounds：x,y,width,height（以设计稿坐标系）
  - constraints：padding、margin、alignment、flex、fit、clip、radius
  - style：colors、typography token、shadows、borders
  - content：text、assetRef、children、zIndex
- runtime（可选）：用于运行态回传与二次修正
  - key：与 Flutter Key 的绑定策略（例如 `vf:<nodeId>`）
- mappings：切图区域与 nodes 的对应关系（用于追溯）

该 spec 的价值是：一旦确定，Flutter 代码生成就是确定性的；UI 调整也变成“改 spec 的字段”，而不是重新 prompt 一遍。

## 视觉对比与迭代闭环
### 输出物
- `layout-diff.json`：基于 LayoutSpec 与 runtime.json 的结构化差异报告（节点偏差、偏差量、建议归因）
- `runtime.json`（可选）：基于 Key 的节点级渲染元数据导出（用于定向修正）
- `render.png`（可选）：Flutter 运行截图（用于人工验收或 CI 归档，不作为主闭环输入）
- `design.png`（可选）：设计效果图（用于人工对照或归档）
- `tree.txt`（可选）：widget/render tree dump（用于定位布局来源）

### 迭代策略
- AI 每次只允许做“定向 patch”：对 diff 归因到具体 node，再调整对应约束/样式
- 禁止“推倒重来”，否则不确定性回升

## 分发与跟随官方更新（fork 方案）
采用 fork 官方 `anthropics/skills`：
- 上游同步：定期 merge/rebase 上游更新
- 自定义 skills：放在 fork 的 `skills/flutter-ui-visual-fidelity/`（暂定名）
- 初始化脚本：clone 你们 fork 的 repo 地址进行安装（可通过环境变量或配置切换官方/内部 fork）

## 非目标（第一阶段不做）
- 动画/交互状态的 1:1 还原（先做静态页面/单状态）
- 复杂自绘（CustomPainter 大量像素级绘制）自动还原
- 动态数据导致的布局变化（先用固定 mock 数据）
