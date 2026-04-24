# SVG Recipes

Use this file when you need the JSON input format or reusable SVG / draw.io implementation details.

## Output Defaults

- Default artifact: `.svg`
- Preview artifact when needed: `.png` plus `.flat.svg`
- Editable artifact when requested: `.drawio`

Typical mapping:

- no explicit format request -> `.svg`
- "send me a preview" / "发我图片" -> `.svg` + `.png`
- "editable draw.io" / "diagrams.net" -> `.svg` + `.drawio`
- both preview and editability -> `.svg` + `.png` + `.drawio`

## CLI

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/svg-flow-diagram"
test -f "$SKILL_DIR/scripts/render_flow_svg.py"
test -f "$SKILL_DIR/assets/example-spec.json"
python3 "$SKILL_DIR/scripts/render_flow_svg.py" \
  "$SKILL_DIR/assets/example-spec.json" \
  /absolute/path/to/output.svg
```

For chat-friendly delivery, keep the SVG and also export a flattened SVG plus PNG in one pass:

```bash
python3 "$SKILL_DIR/scripts/render_flow_svg.py" \
  /absolute/path/to/spec.json \
  /absolute/path/to/output.svg \
  --flat-svg-out /absolute/path/to/output.flat.svg \
  --png-out /absolute/path/to/output.png
```

For editable diagrams.net / draw.io delivery, add a `.drawio` output:

```bash
python3 "$SKILL_DIR/scripts/render_flow_svg.py" \
  /absolute/path/to/spec.json \
  /absolute/path/to/output.svg \
  --drawio-out /absolute/path/to/output.drawio
```

You can combine all outputs in one invocation when the user wants both preview and editability.

If the skill was provided with an explicit filesystem path, use that path as `SKILL_DIR` instead of assuming the default install location.

Write the output SVG to the task workspace or another explicit destination. Do not write generated output back into the skill's `assets/` directory.

## Minimal Spec

```json
{
  "width": 1440,
  "height": 900,
  "title": "Insight Delivery Flow",
  "subtitle": "Signal intake -> scoring -> routing",
  "nodes": [
    {
      "id": "collect",
      "label": "Collect\nSignals",
      "caption": "intake",
      "x": 120,
      "y": 220,
      "w": 220,
      "h": 96,
      "tone": "sand"
    },
    {
      "id": "score",
      "label": "Score\nOpportunity",
      "caption": "model",
      "x": 620,
      "y": 220,
      "w": 220,
      "h": 96,
      "tone": "mint"
    }
  ],
  "edges": [
    {
      "from": "collect",
      "to": "score",
      "label": "clean stream",
      "tone": "mint",
      "duration": 2.2
    }
  ]
}
```

## Supported Shapes

- `rect`: default rounded rectangle
- `pill`: rounded terminal shape
- `diamond`: decision node

## Supported Tones

- `sand`
- `mint`
- `sky`
- `coral`
- `amber`
- `graphite`

Use one tone per node. Use edge `tone` to select the animated dashed flow color.

## Optional Groups

Use groups to frame stages or swimlanes:

```json
{
  "id": "lane-a",
  "title": "Discovery"
}
```

Assign membership on the node, not by hoping the node lands inside the frame:

```json
{
  "id": "score",
  "label": "Score\nOpportunity",
  "x": 620,
  "y": 220,
  "w": 220,
  "h": 96,
  "tone": "mint",
  "group": "lane-a"
}
```

The renderer treats group bounds as content-driven containers:

- `node.group` is the primary way to associate nodes with groups
- `groups[].x/y/w/h` are optional seed hints for early layout only
- `groups[].align` can force `row`, `column`, or `auto`
- `groups[].gap` can raise the minimum spacing between members in a forced row/column layout
- `groups[].phase` can align multiple peer groups to a shared baseline
- `groups[].uniformSize=false` can opt out of group-level size normalization
- the final group frame is auto-sized from member-node bounds plus inner padding
- the emitted SVG nests each grouped node `<g>` inside its owning group `<g>`

When multiple nodes belong to the same group, provide approximate row/column intent in the input positions. If the group already reads as one horizontal row, the renderer snaps all member nodes onto one shared y-center and redistributes them left-to-right with standard flowchart spacing. If it reads as one vertical column, it snaps them onto one shared x-center and redistributes them top-to-bottom. Mixed layouts stay mixed unless you explicitly set `groups[].align`.

If several groups should visually read as the same phase, give them the same `phase` value. Column groups in the same phase will share the same top baseline; row groups in the same phase will share the same left baseline. This keeps multi-column process diagrams from looking staggered.

## Relationship Pattern

Compose each relationship with one animated dashed stroke:

1. Dashed connector path
2. Optional small arrowhead on the same stroke
3. Offset label pill placed away from the connector

Keep the connector clean. Do not add a background pipe, ghost track, or underlay.
When placing labels by hand, keep a visible gap between the label pill and the connector, and avoid any connector crossing through the label area.

## Direct SVG Editing Rules

- Keep reusable markers, patterns, and classes inside `<defs>` and `<style>`.
- Keep the canvas self-contained.
- Keep labels in separate groups so text changes do not disturb pipe geometry.
- Keep `stroke-linecap="round"` and `stroke-linejoin="round"` on all connectors.
- Keep edge labels offset from the connector instead of centering them directly on the path.

## Theme Overrides

Override any base token by adding a `theme` object:

```json
{
  "theme": {
    "bg_paper": "#fffdf8",
    "ink": "#24201c",
    "flow_sky": "#2563eb"
  }
}
```

Use snake_case keys that match the script token names.
