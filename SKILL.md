---
name: svg-flow-diagram
description: Create or revise standalone SVG flowcharts, process maps, architecture diagrams, and pipeline diagrams with dashed animated flow lines and an Excalidraw-like hand-drawn visual language. Use when Codex needs raw `.svg` output rather than Mermaid, HTML, or Figma, especially for requests mentioning SVG flowcharts, node-link diagrams, flowing connectors, animated pipelines, or Extradraw/Excalidraw-style visuals.
---

# SVG Flow Diagram

Create standalone SVG diagrams with dashed animated flow connectors and a sketchy visual system inspired by Excalidraw.

## Quick Start

1. Translate the request into a diagram spec: canvas size, groups, nodes, edges, and notes.
2. Use the bundled renderer at the skill path when building a fresh diagram or iterating on layout several times.
3. If the user needs an image in chat, keep the SVG and also generate a PNG preview from a flattened-color SVG.
4. Patch the SVG directly only for small label, spacing, or color edits.
5. Open references only when needed:
- `references/style-guide.md` for palette, typography, node, and motion rules
- `references/svg-recipes.md` for the JSON spec format and reusable SVG patterns

Treat all paths in this skill as relative to the skill directory, not the caller's current working directory. If the skill was invoked with an explicit path, use that path as `SKILL_DIR`. Otherwise, resolve it from `${CODEX_HOME:-$HOME/.codex}/skills/svg-flow-diagram`.

Before using bundled files, verify they exist. In shared environments such as opencode, the `SKILL.md` text may be available while `scripts/`, `references/`, or `assets/` are missing. If a bundled file is absent, do not claim it exists and do not keep retrying the same missing path.

Write generated SVG files to the user's workspace or to an explicit output path, not back into the skill's `assets/` directory.

## Workflow

### 1. Define the flow grammar

List these before drawing:

- Primary flow direction: left-to-right, top-to-bottom, or loop
- One dominant story: execution flow, system inventory, or responsibility map
- Node types: step, decision, data, external system, annotation
- Relationship types: main pipeline, optional branch, feedback loop, async signal
- Emphasis: which edge or node needs accent color or faster motion

Default to 4-8 nodes, one primary path, and at most two secondary branches when the request is vague. If the request mixes system inventory and execution flow, split it into two diagrams instead of forcing both into one canvas.

Before drawing, reduce the request into this planning stub:

```text
primary_path: node-a -> node-b -> node-c -> node-d
secondary_branches:
- node-b -> helper-x
feedback_loops:
- tool-y -> node-b
layout_model: columns-by-phase | rows-by-swimlane
lanes_or_phases: input, agent, execution, external, output
```

Do not skip this reduction step for diagrams with more than 4 nodes.

### 2. Choose the implementation path

Use the bundled script when:

- creating a new diagram from scratch
- iterating on layout multiple times
- building diagrams with 4 or more nodes
- needing consistent animated pipes across several files

Edit raw SVG when:

- changing only labels or copy
- adjusting one or two connectors
- integrating into an existing handcrafted SVG

### 3. Apply the house style

- Use a warm paper background, dark ink outlines, and restrained pastel fills.
- Use double-stroke nodes to mimic hand-drawn boxes.
- Prefer rounded rectangles, pills, and soft diamonds over sharp enterprise boxes.
- Use a single dashed animated connector for each relationship. Do not add pipe tracks or connector backplates.
- Keep connector thickness proportional to node size; avoid thick pipes that overpower smaller nodes.
- Prefer gentle curves or rounded orthogonal movement. Avoid brittle right-angle spaghetti.
- Keep edge-note capsules offset from the connector with visible breathing room.
- Place edge notes on the cleaner side of the curve so the note pill and any connector never cross.
- Keep icons minimal or omit them entirely.

Enforce flow clarity before decoration:

- Highlight one primary path with the straightest route, strongest contrast, and fewest turns.
- Demote support and lookup paths with lighter color, thinner visual emphasis, or both.
- Route feedback loops on the outer perimeter, not through the middle of the main spine.
- Keep external systems at the far edge of the canvas so they read as destinations or dependencies, not core steps.
- Write edge labels as verb phrases such as `load context`, `run command`, or `return result`. Avoid topic labels such as `context`, `command`, or `result`.
- Use only one structural model per diagram: columns by phase or rows by swimlane. Do not mix both as primary organization cues.

When the user says `extradraw`, treat it as `Excalidraw-like` unless they provide a more specific visual reference.

### 4. Encode direction with motion

For every primary edge:

- Draw one dashed connector around 4-6 px thick.
- Animate `stroke-dashoffset` on that dashed stroke.
- Keep any arrowhead small and secondary to the dashed motion.
- Do not draw a dark background track, ghost track, or filled pipe underneath.
- Keep motion subtle enough that the chart remains readable when animation is paused.

Use static arrowheads only as a fallback cue, not as the only directional signal.

### 5. Finish cleanly

Before handing off:

- Keep 24-40 px of breathing room between nodes.
- Keep edge labels 18-28 px away from the connector centerline.
- Keep edge labels clear of nodes, connector turns, and other labels.
- Keep edge-label text wrapped or truncated so it always stays inside the label background capsule.
- Keep visible inner padding between edge-label text and edge-label background; center text horizontally and vertically in the capsule.
- Keep enough gap between flow blocks so edge labels have placement room and do not overlap node shapes.
- Keep both horizontal and vertical node spacing sufficient to form connector corridors between nodes.
- Keep the gap between connected node blocks larger than 2x the corresponding edge-label width.
- Keep edges routed through blank corridors between nodes; avoid letting connector paths pass through non-endpoint node blocks.
- Keep node label/caption text inside node bounds using wrapping, truncation, or font-size reduction when needed.
- Keep the title/subtitle header area separate from the first row of nodes; never let descriptive text overlap the flow graph.
- If a note would sit on a connector, move it to a cleaner side or farther along the path.
- Keep text at 14 px or above.
- Keep the SVG standalone with no external JavaScript.
- Prefer CSS variables and grouped classes over repeated inline styles.
- When the user asks to send or preview the diagram, keep the original SVG and also export a PNG.
- In the final response, include both file locations and use the PNG for the inline preview.

Run this clarity checklist before handing off:

- Can a reader trace the main path in under 5 seconds without reading every note? If not, simplify.
- Does every non-primary edge justify itself? If not, delete it.
- Does any feedback loop cut through the center of the chart? If yes, reroute it to the perimeter.
- Does the diagram try to explain both architecture and chronological flow? If yes, split the output.
- Do color and stroke weight encode a stable meaning across all edges? If not, normalize them before export.

## Script

Render from a JSON spec with:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/svg-flow-diagram"
test -f "$SKILL_DIR/scripts/render_flow_svg.py"
test -f "$SKILL_DIR/assets/example-spec.json"
python3 "$SKILL_DIR/scripts/render_flow_svg.py" \
  "$SKILL_DIR/assets/example-spec.json" \
  /absolute/path/to/output.svg
```

When you need a deliverable image for chat, render all three artifacts in one command:

```bash
python3 "$SKILL_DIR/scripts/render_flow_svg.py" \
  /absolute/path/to/spec.json \
  /absolute/path/to/output.svg \
  --flat-svg-out /absolute/path/to/output.flat.svg \
  --png-out /absolute/path/to/output.png
```

Keep the original SVG, use the PNG for preview/sending, and tell the user where both files were written.

When the user supplies an explicit skill path, prefer that exact location:

```bash
SKILL_DIR="/absolute/path/to/svg-flow-diagram"
python3 "$SKILL_DIR/scripts/render_flow_svg.py" \
  "$SKILL_DIR/assets/example-spec.json" \
  /absolute/path/to/output.svg
```

Use the example spec at `"$SKILL_DIR/assets/example-spec.json"` as the starter format.

If the renderer script is missing, skip the script flow and generate the SVG directly in the task workspace by following this skill's house style and the JSON shape documented in `references/svg-recipes.md`. If `base-template.svg` exists, copy and adapt it. If it does not exist, write a standalone SVG from scratch.

Supported top-level fields:

- `width`, `height`, `title`, `subtitle`
- `direction`: prefer `lr` unless the request strongly needs top-to-bottom
- `layoutModel`: `columns` or `swimlanes`
- `theme`
- `groups`
- `nodes`
- `edges`

Use `direction`, `layoutModel`, and node/edge role metadata as planning fields even when the current renderer ignores them. They document intent and make manual revisions safer.

Supported node fields:

- `id`, `label`, `caption`
- `x`, `y`, `w`, `h`
- `lane` or `phase`: optional structural placement hints
- `column`: optional ordering hint for left-to-right diagrams
- `role`: `entry`, `core`, `support`, `decision`, `external`, `exit`
- `tone`: `sand`, `mint`, `sky`, `coral`, `amber`, `graphite`
- `shape`: `rect`, `pill`, `diamond`

Always decide node `role` before choosing tone or shape. Let the role drive emphasis, not the other way around.

Supported edge fields:

- `from`, `to`
- `label`
- `kind`: `primary`, `secondary`, `feedback`, `async`
- `tone`
- `fromSide`, `toSide`
- `duration`

Treat `kind` as mandatory during planning even if the current renderer only consumes `tone`. Keep one dominant `primary` chain, no more than two `secondary` branches, and at most one `feedback` loop unless the user explicitly asks for a denser systems map.

## References

Open only what matters for the current task:

- `references/style-guide.md`
- `references/svg-recipes.md`

## Assets

Reuse bundled assets as starting points:

- `"$SKILL_DIR/assets/example-spec.json"` for script input
- `"$SKILL_DIR/assets/base-template.svg"` for quick copy-edit workflows

## Guardrails

- Do not switch to Mermaid, HTML, Canvas, or Figma unless the user explicitly asks.
- Do not import remote fonts, libraries, or JavaScript.
- Do not use glossy gradients, glassmorphism, or heavy shadows.
- Do not cram too many nodes into a small canvas. Expand the canvas or split the diagram instead.
- Do not use motion as the only way to convey meaning. Keep labels and static structure readable.
- Do not draw connector tracks or backplates behind dashed flow lines.
- Do not place edge labels on top of connectors or where another connector crosses the label pill.
- Do not place nodes so tightly that edge labels lose a clear placement zone between connected blocks.
- Do not allow an edge to overlap any node other than its source/target endpoints.
