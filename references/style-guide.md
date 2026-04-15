# SVG Flow Diagram Style Guide

Use this style guide when authoring or revising a diagram by hand.

## Visual Direction

Aim for a warm, sketchy, intentional feel:

- Prefer paper-like backgrounds over stark white.
- Prefer dark brown-black ink over pure black.
- Prefer pastel fills over saturated panels.
- Prefer double-strokes and slight offsets over mathematically perfect boxes.
- Prefer compact, expressive diagrams over dense systems maps.

## Core Tokens

Use these defaults unless the user provides a stronger brand system:

```css
:root {
  --bg-paper: #fcfbf7;
  --ink: #2d2926;
  --muted: #7a6f66;
  --grid: #e8e1d7;
  --sand: #fff0cf;
  --mint: #dff7e8;
  --sky: #dcebff;
  --coral: #ffe0d7;
  --amber: #ffe8b5;
  --graphite: #eae6e1;
  --flow-mint: #24b36b;
  --flow-sky: #2f7cf6;
  --flow-coral: #f36b3c;
  --flow-amber: #d79210;
}
```

## Typography

- Use a Virgil-like hand-drawn stack for primary labels:
  `Virgil, "Segoe Print", "Bradley Hand", "Comic Sans MS", cursive`
- Use a neutral sans stack for captions:
  `"Avenir Next", "Segoe UI", sans-serif`
- Keep node labels around 18 px.
- Keep captions around 12-13 px.
- Keep edge labels around 14-15 px.

## Node Rules

- Default to rounded rectangles with `rx` around 18-24.
- Use pills for terminal or delivery states.
- Use soft diamonds for decisions.
- Use pastel fills with dark outlines.
- Use two strokes with a 1-2 px offset to fake a hand-drawn box.
- Keep node sizes comfortable. A good default is `200-240 x 84-104`.

## Connector Rules

- Treat relationships as animated dashed strokes, not filled pipes.
- Use one connector stroke around 4-6 px.
- Keep the dash pattern readable at a glance.
- Use a small arrowhead only as a supporting cue when helpful.
- Do not add a dark base track, ghost track, or other connector background.
- Prefer curves or rounded routing over rigid right angles.

## Edge Label Rules

- Offset note pills from the connector by roughly 18-28 px.
- Keep note pills entirely off the connector path, including branches crossing nearby.
- When the default midpoint placement is crowded, move the note to the cleaner side of the curve.
- Keep note pills from touching nodes or other note pills.

## Motion Rules

- Keep animation duration between `1.6s` and `2.8s`.
- Use linear timing for dashed flow.
- Use dash movement or pulse movement, not both on the same edge.
- Keep motion restrained. The diagram should feel alive, not noisy.

## Spacing Rules

- Use outer canvas padding around `64-80`.
- Keep at least `24-40` px between nodes.
- Keep group frames roomy enough to avoid crowding labels near borders.
- Leave vertical space above the first row when adding a title.
- Inside one group, snap nodes to shared center lines instead of nudging each box by hand.
- Keep enough inner padding inside each group so rerouted edges can pass around nodes without clipping the frame.

## Avoid

- Pure white backgrounds with jet-black lines
- Sharp 90-degree boxy enterprise diagrams
- Overly thin connectors
- Tiny type
- Heavy shadows or glossy fills
- More than 2-3 accent hues in one diagram
