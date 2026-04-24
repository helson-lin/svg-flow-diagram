# svg-flow-diagram

用于生成 Excalidraw 风格的 SVG 流程图、架构图和节点关系图。默认保留原始 `svg`，同时可导出兼容转换器的 `flat.svg` 和可直接发送的 `png`。

## 目录

- `SKILL.md`：给代理读的技能定义
- `scripts/render_flow_svg.py`：主渲染器
- `scripts/flatten_svg_colors.py`：颜色扁平化辅助脚本
- `references/style-guide.md`：视觉规则
- `references/svg-recipes.md`：spec 格式和命令示例

## 示例展示

### base-template.svg

![base-template](assets/base-template.svg)

### Hermes Agent 架构图示例

![hermes-agent-architecture](assets/hermess-agent-architecture-v3.svg)

## 安装

### Codex

Codex 用户级 skills 默认安装在：

```bash
~/.codex/skills/
```

如果你已经有这个 skill，只需要确认目录存在：

```bash
ls ~/.codex/skills/svg-flow-diagram
```

如果是手动安装或同步：

```bash
mkdir -p ~/.codex/skills
cp -R /path/to/svg-flow-diagram ~/.codex/skills/svg-flow-diagram
```

如果你想从工作目录软链接进去：

```bash
mkdir -p ~/.codex/skills
ln -s /path/to/svg-flow-diagram ~/.codex/skills/svg-flow-diagram
```

安装或更新后，重启 Codex 会话更稳妥。

### Claude Code

Claude Code 常见的技能目录是：

```bash
~/.claude/skills/
```

手动安装：

```bash
mkdir -p ~/.claude/skills
cp -R /path/to/svg-flow-diagram ~/.claude/skills/svg-flow-diagram
```

或者用软链接：

```bash
mkdir -p ~/.claude/skills
ln -s /path/to/svg-flow-diagram ~/.claude/skills/svg-flow-diagram
```

安装后开启新的 Claude Code 会话，让它重新发现技能。

## 使用方式

### Codex

推荐直接在提示词里点名技能：

```text
$svg-flow-diagram 帮我画一个 Hermes Agent 架构图，并把 png 发给我，同时保留 svg
```

如果需要显式指定路径：

```text
Use $svg-flow-diagram at /Users/you/.codex/skills/svg-flow-diagram to draw a Hermes Agent architecture diagram. Export svg and png, and tell me both file paths.
```

交付约定：

- `png`：用于聊天里发送和预览
- `svg`：用于继续编辑或二次加工
- 回复时应同时标注两者路径

### Claude Code

在 Claude Code 里，建议用“技能名 + 路径 + 任务”的方式，避免技能发现差异：

```text
Use $svg-flow-diagram at ~/.claude/skills/svg-flow-diagram to draw a Hermes Agent architecture diagram. Keep the original svg, also export a png preview, and tell me where both files were written.
```

中文也可以直接说：

```text
使用 $svg-flow-diagram（路径 ~/.claude/skills/svg-flow-diagram）帮我画一个 Hermes Agent 架构图，保留 svg，同时导出 png 发给我，并告诉我两个文件的位置。
```

## 命令行直跑

如果你不通过代理，而是直接跑脚本：

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/svg-flow-diagram"
python3 "$SKILL_DIR/scripts/render_flow_svg.py" \
  /absolute/path/to/spec.json \
  /absolute/path/to/output.svg \
  --flat-svg-out /absolute/path/to/output.flat.svg \
  --png-out /absolute/path/to/output.png
```

这条命令会产出三份文件：

- `output.svg`：原始矢量
- `output.flat.svg`：兼容大多数 SVG 转 PNG 工具的扁平版
- `output.png`：可直接发送的图片

## 推荐交付规范

生成完成后，默认按下面的方式回复用户：

1. 发送 `png` 预览
2. 告知 `png` 文件位置
3. 告知 `svg` 文件位置
4. 如有需要，再补充 `flat.svg` 位置

推荐表述：

```text
已生成图片：
- PNG: /absolute/path/to/output.png
- SVG: /absolute/path/to/output.svg
```

## 布局约定

为了让主流程更稳定、节点不轻易跑偏，渲染器现在会优先遵守下面这些布局信号：

- `groups[].id` 最好和节点里的 `lane`、`phase`、`group` 或 `groupId` 对应
- 常见写法是分组 id 用 `lane-input`、`lane-agent`、`lane-output`，节点里写 `lane: "input"`、`lane: "agent"`、`lane: "output"`
- 在左到右流程图里，如果一批节点在 spec 里原本就在同一条横向主线上，渲染器会尽量保持它们仍然落在同一条主线上
- 在上到下流程图里，同理会优先保持原始的纵向主线
- `column` 仍然建议保留，它主要表达左右顺序；真正的主线对齐更多依赖你在 spec 里给出的初始 `x/y` 布局

一个更稳的习惯是：

- 主线节点先按一条直线摆好
- 支线节点再放到主线的上方或下方
- 组框先表达阶段或泳道，不要把主线和支线混在同一块很窄的区域里

## 注意事项

- 如果导出的 PNG 变黑，优先检查 SVG 转换器是否完整支持 CSS 变量。
- 本 skill 现在已经把颜色扁平化步骤并入交付链，优先用 `--flat-svg-out` + `--png-out`。
- 对复杂图，先拆主流程和支线，不要把“系统构成”和“执行时序”强塞进一张图。
- 如果你发现节点跑到别的组框里，优先检查节点的 `lane/phase/group` 是否和目标 `group.id` 能对应上。
- 如果你希望一条主流程严格保持在同一条线上，直接在 spec 里把这批节点先摆到同一行或同一列，再让渲染器做细调。
