#!/usr/bin/env python3
"""Flatten CSS variables in an SVG so raster converters render stable colors."""

from __future__ import annotations

import argparse
from pathlib import Path

THEME = {
    "bg-paper": "#FCFBF7",
    "ink": "#2D2926",
    "muted": "#7A6F66",
    "grid": "#E8E1D7",
    "sand": "#FFF0CF",
    "mint": "#DFF7E8",
    "sky": "#DCEBFF",
    "coral": "#FFE0D7",
    "amber": "#FFE8B5",
    "graphite": "#EAE6E1",
    "flow-mint": "#24B36B",
    "flow-sky": "#2F7CF6",
    "flow-coral": "#F36B3C",
    "flow-amber": "#D79210",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Flatten CSS variables and context-stroke markers in an SVG."
    )
    parser.add_argument("src", help="Path to the source SVG.")
    parser.add_argument("dst", help="Path to the flattened SVG.")
    return parser.parse_args()


def flatten_svg(src: Path, dst: Path) -> None:
    text = src.read_text()
    for key, value in THEME.items():
        text = text.replace(f"var(--{key})", value)
    text = text.replace('stroke="context-stroke"', f'stroke="{THEME["ink"]}"')
    dst.write_text(text)


if __name__ == "__main__":
    args = parse_args()
    flatten_svg(Path(args.src), Path(args.dst))
    print(f"Wrote {args.dst}")
