---
name: svg-flow-diagram
description: Create or revise standalone SVG flowcharts, process maps, architecture diagrams, and pipeline diagrams with dashed animated flow lines and an Excalidraw-like hand-drawn visual language. Use when the agent needs raw `.svg` output rather than Mermaid, HTML, or Figma, especially for requests mentioning SVG flowcharts, node-link diagrams, flowing connectors, animated pipelines, or Extradraw/Excalidraw-style visuals.
---

# SVG Flow Diagram

Create standalone SVG diagrams with dashed animated flow connectors and a sketchy visual system inspired by Excalidraw.

## SKILL_DIR — resolve this FIRST

**IMPORTANT:** All file paths in this skill are relative to the directory containing this `SKILL.md` file. Do NOT resolve them from your current working directory.

Set `SKILL_DIR` to the **absolute path of the directory containing this SKILL.md file** before reading any other file in this skill. For example, if this file was loaded from `/home/user/.codex/skills/svg-flow-diagram/SKILL.md`, then `SKILL_DIR=/home/user/.codex/skills/svg-flow-diagram`.

If you cannot determine the path this file was loaded from, search these locations and use the first that exists:

1. `$CODEX_HOME/skills/svg-flow-diagram` (if `CODEX_HOME` is set)
2. `~/.codex/skills/svg-flow-diagram`
3. `~/.claude/skills/svg-flow-diagram`
4. `~/.opencode/skills/svg-flow-diagram`

Use a simple test to find the directory. Run each line one at a time until one succeeds:

```bash
test -d ~/.codex/skills/svg-flow-diagram && SKILL_DIR=~/.codex/skills/svg-flow-diagram
```

```bash
test -d ~/.claude/skills/svg-flow-diagram && SKILL_DIR=~/.claude/skills/svg-flow-diagram
```

```bash
test -d ~/.opencode/skills/svg-flow-diagram && SKILL_DIR=~/.opencode/skills/svg-flow-diagram
```

## Quick Start

1. Translate the request into a diagram spec: canvas size, groups, nodes, edges, and notes.
2. Use the bundled renderer at `$SKILL_DIR/scripts/render_flow_svg.py` when building a fresh diagram or iterating on layout several times.
3. Patch the SVG directly only for small label, spacing, or color edits.
4. Open references only when needed:
- `$SKILL_DIR/references/style-guide.md` for palette, typography, node, and motion rules
- `$SKILL_DIR/references/svg-recipes.md` for the JSON spec format and reusable SVG patterns

## Workflow

### 1. Define the flow grammar

List these before drawing:

- Primary flow direction: left-to-right, top-to-bottom, or loop
- Node types: step, decision, data, external system, annotation
- Relationship types: main pipeline, optional branch, feedback loop, async signal
- Emphasis: which edge or node needs accent color or faster motion

Default to 4-8 nodes, one primary path, and at most two secondary branches when the request is vague.

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

## Script

Render from a JSON spec with:

```bash
# Resolve SKILL_DIR (see "Resolving SKILL_DIR" above), then:
python3 "$SKILL_DIR/scripts/render_flow_svg.py" \
  "$SKILL_DIR/assets/example-spec.json" \
  /absolute/path/to/output.svg
```

Use the example spec at `"$SKILL_DIR/assets/example-spec.json"` as the starter format.

Supported top-level fields:

- `width`, `height`, `title`, `subtitle`
- `theme`
- `groups`
- `nodes`
- `edges`

Supported node fields:

- `id`, `label`, `caption`
- `x`, `y`, `w`, `h`
- `tone`: `sand`, `mint`, `sky`, `coral`, `amber`, `graphite`
- `shape`: `rect`, `pill`, `diamond`
- `group`: id of the parent group (optional; if omitted, inferred by containment)

Supported edge fields:

- `from`, `to`
- `label`
- `tone`
- `fromSide`, `toSide`
- `duration`

## References

Open only what matters for the current task:

- `$SKILL_DIR/references/style-guide.md`
- `$SKILL_DIR/references/svg-recipes.md`

## Assets

Reuse bundled assets as starting points:

- `$SKILL_DIR/assets/example-spec.json` for script input
- `$SKILL_DIR/assets/base-template.svg` for quick copy-edit workflows

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
