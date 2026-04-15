# SVG Recipes

Use this file when you need the JSON input format or reusable SVG implementation details.

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
  "title": "Discovery",
  "x": 80,
  "y": 150,
  "w": 430,
  "h": 520
}
```

When multiple nodes belong to the same group, keep their centers roughly aligned by row or column. The renderer now snaps near-aligned nodes inside a group and prefers edge routes with fewer crossings, so provide group boxes and approximate grid placement instead of tiny per-node offsets.

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
