#!/usr/bin/env python3
"""Render an Excalidraw-like SVG flow diagram from a JSON spec."""

from __future__ import annotations

import argparse
import html
import json
import math
import unicodedata
from pathlib import Path

DEFAULT_THEME = {
    "bg_paper": "#FCFBF7",
    "ink": "#2D2926",
    "muted": "#7A6F66",
    "grid": "#E8E1D7",
    "sand": "#FFF0CF",
    "mint": "#DFF7E8",
    "sky": "#DCEBFF",
    "coral": "#FFE0D7",
    "amber": "#FFE8B5",
    "graphite": "#EAE6E1",
    "flow_mint": "#24B36B",
    "flow_sky": "#2F7CF6",
    "flow_coral": "#F36B3C",
    "flow_amber": "#D79210",
}

TONE_TO_FILL = {
    "sand": "sand",
    "mint": "mint",
    "sky": "sky",
    "coral": "coral",
    "amber": "amber",
    "graphite": "graphite",
}

TONE_TO_FLOW = {
    "sand": "flow-amber",
    "mint": "flow-mint",
    "sky": "flow-sky",
    "coral": "flow-coral",
    "amber": "flow-amber",
    "graphite": "ink",
}

LABEL_OUTER_PADDING = 24.0
LABEL_NODE_MARGIN = 22.0
LABEL_LABEL_MARGIN = 14.0
LABEL_EDGE_MARGIN = 8.0
EDGE_SAMPLE_COUNT = 41
HEADER_CONTENT_GAP = 24.0
CANVAS_BOTTOM_PADDING = 24.0
CANVAS_SIDE_PADDING = 24.0
NODE_MIN_VERTICAL_GAP = 34.0
NODE_MIN_HORIZONTAL_GAP = 68.0
EDGE_NODE_MARGIN = 5.0
EDGE_NODE_ADJUST_ITERS = 14
LABEL_NODE_PUSH_ITERS = 16
EDGE_LABEL_FONT_SIZE = 13.5
EDGE_LABEL_MAX_WIDTH = 280.0
EDGE_LABEL_MIN_WIDTH = 92.0
EDGE_LABEL_LINE_HEIGHT = 16.0
EDGE_LABEL_MAX_LINES = 3
EDGE_LABEL_PAD_X = 20.0
EDGE_LABEL_PAD_Y = 10.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a standalone SVG flow diagram from a JSON spec."
    )
    parser.add_argument("spec", help="Path to the JSON diagram spec.")
    parser.add_argument("output", help="Path to the output SVG file.")
    return parser.parse_args()


def fmt(value: float) -> str:
    if int(value) == value:
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def text_lines(value: str | None) -> list[str]:
    if not value:
        return []
    return [line for line in str(value).splitlines() if line]


def char_width_px(char: str, font_size: float) -> float:
    if char.isspace():
        return font_size * 0.34
    if unicodedata.east_asian_width(char) in {"W", "F"}:
        return font_size * 0.95
    if char.isascii():
        if char.isupper():
            return font_size * 0.64
        if char.isdigit():
            return font_size * 0.58
        return font_size * 0.56
    return font_size * 0.72


def text_width_px(text: str, font_size: float) -> float:
    return sum(char_width_px(ch, font_size) for ch in text)


def truncate_line_to_width(text: str, max_width: float, font_size: float) -> str:
    if text_width_px(text, font_size) <= max_width:
        return text
    suffix = "…"
    suffix_width = text_width_px(suffix, font_size)
    if suffix_width >= max_width:
        return ""
    kept: list[str] = []
    width = 0.0
    for ch in text:
        ch_width = char_width_px(ch, font_size)
        if width + ch_width + suffix_width > max_width:
            break
        kept.append(ch)
        width += ch_width
    return "".join(kept).rstrip() + suffix


def wrap_line_by_width(text: str, max_width: float, font_size: float) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    lines: list[str] = []
    current: list[str] = []
    current_width = 0.0
    for char in stripped:
        char_width = char_width_px(char, font_size)
        if current and current_width + char_width > max_width:
            lines.append("".join(current).rstrip())
            current = []
            current_width = 0.0
        if not current and char.isspace():
            continue
        current.append(char)
        current_width += char_width
    if current:
        lines.append("".join(current).rstrip())
    return [line for line in lines if line]


def wrap_text_to_width(
    lines: list[str], max_width: float, font_size: float
) -> list[str]:
    wrapped: list[str] = []
    for line in lines:
        pieces = wrap_line_by_width(line, max_width, font_size)
        if pieces:
            wrapped.extend(pieces)
    return wrapped


def fit_node_text(
    node: dict,
) -> tuple[list[str], float, float | None, str | None, float]:
    x = float(node["x"])
    _ = x
    w = float(node["w"])
    h = float(node["h"])
    raw_lines = text_lines(node.get("label")) or [" "]
    caption_raw = str(node.get("caption", "")).strip() or None
    max_label_width = max(42.0, w - 30.0)
    max_label_font = min(20.0, max(14.0, h * 0.21))

    for font_size in [float(size) for size in range(int(max_label_font), 11, -1)]:
        line_height = font_size * 1.18
        caption_font = min(12.5, max(10.0, font_size * 0.68)) if caption_raw else None
        caption_text = (
            truncate_line_to_width(caption_raw, w - 26.0, caption_font)
            if (caption_raw and caption_font)
            else None
        )
        caption_height = caption_font * 1.35 if (caption_text and caption_font) else 0.0
        caption_gap = 8.0 if caption_text else 0.0
        max_lines_allowed = max(
            1, int((h - 24.0 - caption_gap - caption_height) / line_height)
        )
        wrapped = wrap_text_to_width(raw_lines, max_label_width, font_size) or [" "]
        if len(wrapped) > max_lines_allowed:
            kept = wrapped[:max_lines_allowed]
            kept[-1] = truncate_line_to_width(
                "".join(wrapped[max_lines_allowed - 1 :]),
                max_label_width,
                font_size,
            )
            wrapped = kept
        block_height = len(wrapped) * line_height + caption_gap + caption_height
        if block_height <= h - 24.0:
            return wrapped, font_size, caption_font, caption_text, line_height

    fallback_font = 12.0
    fallback_line_height = fallback_font * 1.18
    fallback_caption_font = 10.0 if caption_raw else None
    fallback_caption = (
        truncate_line_to_width(caption_raw, w - 26.0, fallback_caption_font)
        if (caption_raw and fallback_caption_font)
        else None
    )
    wrapped = wrap_text_to_width(raw_lines, max_label_width, fallback_font) or [" "]
    max_lines_allowed = max(
        1,
        int(
            (
                h
                - 24.0
                - (8.0 if fallback_caption else 0.0)
                - ((fallback_caption_font or 0.0) * 1.35 if fallback_caption else 0.0)
            )
            / fallback_line_height
        ),
    )
    if len(wrapped) > max_lines_allowed:
        kept = wrapped[:max_lines_allowed]
        kept[-1] = truncate_line_to_width(
            "".join(wrapped[max_lines_allowed - 1 :]),
            max_label_width,
            fallback_font,
        )
        wrapped = kept
    return wrapped, fallback_font, fallback_caption_font, fallback_caption, fallback_line_height


def jitter(key: str, amount: float) -> float:
    total = sum((index + 1) * ord(char) for index, char in enumerate(key))
    ratio = ((total % 2000) / 1999.0) - 0.5
    return ratio * amount * 2


def rounded_rect_path(x: float, y: float, w: float, h: float, r: float) -> str:
    r = min(r, w / 2, h / 2)
    return (
        f"M {fmt(x + r)} {fmt(y)} "
        f"H {fmt(x + w - r)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x + w)} {fmt(y + r)} "
        f"V {fmt(y + h - r)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x + w - r)} {fmt(y + h)} "
        f"H {fmt(x + r)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x)} {fmt(y + h - r)} "
        f"V {fmt(y + r)} "
        f"A {fmt(r)} {fmt(r)} 0 0 1 {fmt(x + r)} {fmt(y)} Z"
    )


def diamond_path(x: float, y: float, w: float, h: float) -> str:
    cx = x + w / 2
    cy = y + h / 2
    return (
        f"M {fmt(cx)} {fmt(y)} "
        f"L {fmt(x + w)} {fmt(cy)} "
        f"L {fmt(cx)} {fmt(y + h)} "
        f"L {fmt(x)} {fmt(cy)} Z"
    )


def node_path(node: dict, variant: int) -> str:
    x = float(node["x"]) + jitter(f"{node['id']}-x-{variant}", 1.6)
    y = float(node["y"]) + jitter(f"{node['id']}-y-{variant}", 1.4)
    w = float(node["w"])
    h = float(node["h"])
    shape = node.get("shape", "rect")
    if shape == "diamond":
        return diamond_path(x, y, w, h)
    radius = h / 2 if shape == "pill" else 20
    return rounded_rect_path(x, y, w, h, radius)


def infer_side(source: dict, target: dict) -> str:
    sx = float(source["x"]) + float(source["w"]) / 2
    sy = float(source["y"]) + float(source["h"]) / 2
    tx = float(target["x"]) + float(target["w"]) / 2
    ty = float(target["y"]) + float(target["h"]) / 2
    dx = tx - sx
    dy = ty - sy
    if abs(dx) >= abs(dy):
        return "right" if dx >= 0 else "left"
    return "bottom" if dy >= 0 else "top"


def anchor_point(node: dict, side: str) -> tuple[float, float]:
    x = float(node["x"])
    y = float(node["y"])
    w = float(node["w"])
    h = float(node["h"])
    if side == "left":
        return (x, y + h / 2)
    if side == "right":
        return (x + w, y + h / 2)
    if side == "top":
        return (x + w / 2, y)
    return (x + w / 2, y + h)


def shift(point: tuple[float, float], side: str, amount: float) -> tuple[float, float]:
    x, y = point
    if side == "left":
        return (x - amount, y)
    if side == "right":
        return (x + amount, y)
    if side == "top":
        return (x, y - amount)
    return (x, y + amount)


def cubic_point(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    u = 1 - t
    x = (
        (u**3) * p0[0]
        + 3 * (u**2) * t * p1[0]
        + 3 * u * (t**2) * p2[0]
        + (t**3) * p3[0]
    )
    y = (
        (u**3) * p0[1]
        + 3 * (u**2) * t * p1[1]
        + 3 * u * (t**2) * p2[1]
        + (t**3) * p3[1]
    )
    return (x, y)


def cubic_derivative(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    u = 1 - t
    x = (
        3 * (u**2) * (p1[0] - p0[0])
        + 6 * u * t * (p2[0] - p1[0])
        + 3 * (t**2) * (p3[0] - p2[0])
    )
    y = (
        3 * (u**2) * (p1[1] - p0[1])
        + 6 * u * t * (p2[1] - p1[1])
        + 3 * (t**2) * (p3[1] - p2[1])
    )
    return (x, y)


def unit_normal(tangent: tuple[float, float]) -> tuple[float, float]:
    dx, dy = tangent
    length = math.hypot(dx, dy) or 1.0
    return (-dy / length, dx / length)


def rect_from_center(
    center_x: float, center_y: float, width: float, height: float
) -> tuple[float, float, float, float]:
    return (center_x - width / 2, center_y - height / 2, width, height)


def rect_intersects(
    rect_a: tuple[float, float, float, float],
    rect_b: tuple[float, float, float, float],
    margin: float = 0.0,
) -> bool:
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b
    return not (
        ax + aw + margin <= bx - margin
        or bx + bw + margin <= ax - margin
        or ay + ah + margin <= by - margin
        or by + bh + margin <= ay - margin
    )


def point_in_rect(
    point: tuple[float, float],
    rect: tuple[float, float, float, float],
    margin: float = 0.0,
) -> bool:
    px, py = point
    rx, ry, rw, rh = rect
    return (
        rx - margin <= px <= rx + rw + margin
        and ry - margin <= py <= ry + rh + margin
    )


def off_canvas_penalty(
    rect: tuple[float, float, float, float],
    width: float,
    height: float,
    padding: float,
) -> float:
    x, y, w, h = rect
    penalty = 0.0
    penalty += max(0.0, padding - x)
    penalty += max(0.0, padding - y)
    penalty += max(0.0, x + w - (width - padding))
    penalty += max(0.0, y + h - (height - padding))
    return penalty


def rect_center(rect: tuple[float, float, float, float]) -> tuple[float, float]:
    x, y, w, h = rect
    return (x + w / 2, y + h / 2)


def clamp_rect_to_canvas(
    rect: tuple[float, float, float, float],
    width: float,
    height: float,
    padding: float = LABEL_OUTER_PADDING,
) -> tuple[float, float, float, float]:
    x, y, w, h = rect
    min_x = padding
    max_x = max(padding, width - padding - w)
    min_y = padding
    max_y = max(padding, height - padding - h)
    return (min(max(x, min_x), max_x), min(max(y, min_y), max_y), w, h)


def rect_overlap_area(
    rect_a: tuple[float, float, float, float],
    rect_b: tuple[float, float, float, float],
    margin: float = 0.0,
) -> float:
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b
    left = max(ax, bx - margin)
    right = min(ax + aw, bx + bw + margin)
    top = max(ay, by - margin)
    bottom = min(ay + ah, by + bh + margin)
    if right <= left or bottom <= top:
        return 0.0
    return (right - left) * (bottom - top)


def node_bounds(node: dict) -> tuple[float, float, float, float]:
    return (
        float(node["x"]),
        float(node["y"]),
        float(node["w"]),
        float(node["h"]),
    )


def overlap_1d(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def normalize_node_vertical_spacing(
    nodes_list: list[dict], min_gap: float = NODE_MIN_VERTICAL_GAP
) -> None:
    if len(nodes_list) < 2:
        return
    for _ in range(12):
        moved = False
        for i in range(len(nodes_list)):
            for j in range(i + 1, len(nodes_list)):
                a = nodes_list[i]
                b = nodes_list[j]
                ax0 = float(a["x"])
                ax1 = ax0 + float(a["w"])
                bx0 = float(b["x"])
                bx1 = bx0 + float(b["w"])
                if overlap_1d(ax0, ax1, bx0, bx1) <= 0:
                    continue
                ay0 = float(a["y"])
                ay1 = ay0 + float(a["h"])
                by0 = float(b["y"])
                by1 = by0 + float(b["h"])
                if ay0 <= by0:
                    gap = by0 - ay1
                    if gap < min_gap:
                        b["y"] = by0 + (min_gap - gap)
                        moved = True
                else:
                    gap = ay0 - by1
                    if gap < min_gap:
                        a["y"] = ay0 + (min_gap - gap)
                        moved = True
        if not moved:
            break


def normalize_node_spacing_2d(
    nodes_list: list[dict],
    min_h_gap: float = NODE_MIN_HORIZONTAL_GAP,
    min_v_gap: float = NODE_MIN_VERTICAL_GAP,
) -> None:
    if len(nodes_list) < 2:
        return
    for _ in range(20):
        moved = False
        for i in range(len(nodes_list)):
            for j in range(i + 1, len(nodes_list)):
                a = nodes_list[i]
                b = nodes_list[j]
                ax0 = float(a["x"])
                ay0 = float(a["y"])
                aw = float(a["w"])
                ah = float(a["h"])
                ax1 = ax0 + aw
                ay1 = ay0 + ah
                bx0 = float(b["x"])
                by0 = float(b["y"])
                bw = float(b["w"])
                bh = float(b["h"])
                bx1 = bx0 + bw
                by1 = by0 + bh

                y_overlap = overlap_1d(ay0, ay1, by0, by1)
                x_overlap = overlap_1d(ax0, ax1, bx0, bx1)

                if y_overlap > 0:
                    if ax0 <= bx0:
                        gap = bx0 - ax1
                        if gap < min_h_gap:
                            delta = (min_h_gap - gap) / 2.0
                            a["x"] = ax0 - delta
                            b["x"] = bx0 + delta
                            moved = True
                    else:
                        gap = ax0 - bx1
                        if gap < min_h_gap:
                            delta = (min_h_gap - gap) / 2.0
                            a["x"] = ax0 + delta
                            b["x"] = bx0 - delta
                            moved = True

                if x_overlap > 0:
                    if ay0 <= by0:
                        gap = by0 - ay1
                        if gap < min_v_gap:
                            delta = (min_v_gap - gap) / 2.0
                            a["y"] = ay0 - delta
                            b["y"] = by0 + delta
                            moved = True
                    else:
                        gap = ay0 - by1
                        if gap < min_v_gap:
                            delta = (min_v_gap - gap) / 2.0
                            a["y"] = ay0 + delta
                            b["y"] = by0 - delta
                            moved = True
        if not moved:
            break


def enforce_edge_label_corridors(
    nodes_list: list[dict],
    edges: list[dict],
    corridor_padding: float = 24.0,
) -> None:
    if not nodes_list or not edges:
        return
    for _ in range(10):
        moved = False
        nodes = {node["id"]: node for node in nodes_list}
        for edge in edges:
            source = nodes.get(edge.get("from"))
            target = nodes.get(edge.get("to"))
            if not source or not target:
                continue
            source_cx, source_cy = node_center(source)
            target_cx, target_cy = node_center(target)
            dx = target_cx - source_cx
            dy = target_cy - source_cy
            is_horizontal = abs(dx) >= abs(dy)
            label = edge.get("label")
            if label:
                label_width, label_height, _ = edge_label_size(str(label))
            else:
                label_width, label_height = (EDGE_LABEL_MIN_WIDTH, EDGE_LABEL_LINE_HEIGHT + (EDGE_LABEL_PAD_Y * 2))
            required_gap = (label_width * 2.0) + corridor_padding + 1.0

            if is_horizontal:
                if source_cx <= target_cx:
                    left = source
                    right = target
                else:
                    left = target
                    right = source
                left_x = float(left["x"])
                right_x = float(right["x"])
                gap = right_x - (left_x + float(left["w"]))
                if gap < required_gap:
                    delta = (required_gap - gap) / 2.0
                    left["x"] = left_x - delta
                    right["x"] = right_x + delta
                    moved = True
            else:
                if source_cy <= target_cy:
                    top = source
                    bottom = target
                else:
                    top = target
                    bottom = source
                top_y = float(top["y"])
                bottom_y = float(bottom["y"])
                gap = bottom_y - (top_y + float(top["h"]))
                if gap < required_gap:
                    delta = (required_gap - gap) / 2.0
                    top["y"] = top_y - delta
                    bottom["y"] = bottom_y + delta
                    moved = True
        if not moved:
            break


def clamp_nodes_to_canvas(
    nodes_list: list[dict],
    width: float,
    min_top: float = 0.0,
    side_padding: float = CANVAS_SIDE_PADDING,
    clamp_right: bool = True,
) -> None:
    for node in nodes_list:
        x = float(node["x"])
        y = float(node["y"])
        w = float(node["w"])
        if clamp_right:
            max_x = max(side_padding, width - side_padding - w)
            node["x"] = min(max(x, side_padding), max_x)
        else:
            node["x"] = max(x, side_padding)
        node["y"] = max(y, min_top)


def node_center(node: dict) -> tuple[float, float]:
    return (float(node["x"]) + float(node["w"]) / 2, float(node["y"]) + float(node["h"]) / 2)


def edge_node_push_vectors(
    edge: dict,
    geometry: dict[str, object],
    nodes: dict[str, dict],
    margin: float = EDGE_NODE_MARGIN,
) -> dict[str, tuple[float, float, int]]:
    source_id = edge["from"]
    target_id = edge["to"]
    samples = sample_cubic_points(
        geometry["start"],
        geometry["cp1"],
        geometry["cp2"],
        geometry["end"],
    )
    interior = samples[2:-2] if len(samples) > 5 else samples
    out: dict[str, tuple[float, float, int]] = {}
    for node_id, node in nodes.items():
        if node_id in {source_id, target_id}:
            continue
        rect = node_bounds(node)
        hit_points = [point for point in interior if point_in_rect(point, rect, margin)]
        if not hit_points:
            continue
        center = node_center(node)
        push_x = 0.0
        push_y = 0.0
        for hit_x, hit_y in hit_points:
            push_x += center[0] - hit_x
            push_y += center[1] - hit_y
        length = math.hypot(push_x, push_y)
        if length < 1e-4:
            flow_x = geometry["end"][0] - geometry["start"][0]
            flow_y = geometry["end"][1] - geometry["start"][1]
            # If the path goes through the center, use a perpendicular push.
            push_x = -flow_y
            push_y = flow_x
            length = math.hypot(push_x, push_y) or 1.0
        out[node_id] = (push_x / length, push_y / length, len(hit_points))
    return out


def avoid_edge_node_overlaps(
    nodes_list: list[dict],
    edges: list[dict],
    width: float,
    min_top: float = 0.0,
    margin: float = EDGE_NODE_MARGIN,
) -> None:
    if not nodes_list or not edges:
        return
    for _ in range(EDGE_NODE_ADJUST_ITERS):
        nodes = {node["id"]: node for node in nodes_list}
        geometries = [edge_geometry(edge, nodes) for edge in edges]
        displacement: dict[str, tuple[float, float, int]] = {}
        overlaps = 0
        for index, edge in enumerate(edges):
            pushes = edge_node_push_vectors(edge, geometries[index], nodes, margin)
            for node_id, (dx, dy, weight) in pushes.items():
                overlaps += 1
                acc_dx, acc_dy, acc_w = displacement.get(node_id, (0.0, 0.0, 0))
                displacement[node_id] = (
                    acc_dx + dx * weight,
                    acc_dy + dy * weight,
                    acc_w + weight,
                )
        if overlaps == 0:
            break
        for node in nodes_list:
            node_id = node["id"]
            if node_id not in displacement:
                continue
            dx, dy, weight = displacement[node_id]
            length = math.hypot(dx, dy)
            if length < 1e-4:
                continue
            step = min(34.0, 11.0 + (weight * 2.6))
            node["x"] = float(node["x"]) + (dx / length) * step
            node["y"] = float(node["y"]) + (dy / length) * step
        normalize_node_spacing_2d(nodes_list)
        clamp_nodes_to_canvas(nodes_list, width, min_top=min_top)


def sample_cubic_points(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    count: int = EDGE_SAMPLE_COUNT,
) -> list[tuple[float, float]]:
    if count <= 1:
        return [cubic_point(p0, p1, p2, p3, 0.5)]
    return [
        cubic_point(p0, p1, p2, p3, step / (count - 1))
        for step in range(count)
    ]


def edge_geometry(edge: dict, nodes: dict[str, dict]) -> dict[str, object]:
    source = nodes[edge["from"]]
    target = nodes[edge["to"]]
    from_side = edge.get("fromSide") or infer_side(source, target)
    to_side = edge.get("toSide") or infer_side(target, source)
    start = anchor_point(source, from_side)
    end = anchor_point(target, to_side)
    dx = abs(end[0] - start[0])
    dy = abs(end[1] - start[1])
    handle = max(54.0, min(180.0, dx * 0.36 + dy * 0.14))
    cp1 = shift(start, from_side, handle)
    cp2 = shift(end, to_side, handle)
    path = (
        f"M {fmt(start[0])} {fmt(start[1])} "
        f"C {fmt(cp1[0])} {fmt(cp1[1])}, {fmt(cp2[0])} {fmt(cp2[1])}, "
        f"{fmt(end[0])} {fmt(end[1])}"
    )
    min_dim = min(
        float(source["w"]),
        float(source["h"]),
        float(target["w"]),
        float(target["h"]),
    )
    stroke_width = max(2.2, min(4.0, min_dim * 0.028))
    dash_a = max(6.0, stroke_width * 2.0)
    dash_b = max(7.0, stroke_width * 2.4)
    return {
        "path": path,
        "start": start,
        "cp1": cp1,
        "cp2": cp2,
        "end": end,
        "stroke_width": stroke_width,
        "dash_a": dash_a,
        "dash_b": dash_b,
    }


def header_metrics(spec: dict) -> dict[str, float]:
    title = spec.get("title")
    subtitle = spec.get("subtitle")
    title_y = 82.0
    subtitle_y = 112.0
    bottom = 0.0
    if title:
        bottom = max(bottom, title_y + 10.0)
    if subtitle:
        bottom = max(bottom, subtitle_y + 10.0)
    return {"title_y": title_y, "subtitle_y": subtitle_y, "bottom": bottom}


def render_header(spec: dict, metrics: dict[str, float]) -> str:
    title = spec.get("title")
    subtitle = spec.get("subtitle")
    if not title and not subtitle:
        return ""
    parts = ['<g class="header">']
    if title:
        parts.append(
            f'<text class="title" x="72" y="{fmt(metrics["title_y"])}">{escape(title)}</text>'
        )
    if subtitle:
        parts.append(
            f'<text class="subtitle" x="72" y="{fmt(metrics["subtitle_y"])}">{escape(subtitle)}</text>'
        )
    parts.append("</g>")
    return "\n".join(parts)


def render_groups(groups: list[dict]) -> str:
    parts: list[str] = []
    for group in groups:
        x = float(group["x"])
        y = float(group["y"])
        w = float(group["w"])
        h = float(group["h"])
        title = escape(group.get("title", ""))
        parts.append(
            f'<g class="group" id="group-{escape(group.get("id", title or "group"))}">'
        )
        parts.append(
            f'<path class="group-frame" d="{rounded_rect_path(x, y, w, h, 28)}" />'
        )
        if title:
            parts.append(
                f'<text class="group-title" x="{fmt(x + 22)}" y="{fmt(y + 34)}">{title}</text>'
            )
        parts.append("</g>")
    return "\n".join(parts)


def render_node(node: dict) -> str:
    tone = node.get("tone", "sand")
    fill_var = TONE_TO_FILL.get(tone, "sand")
    x = float(node["x"])
    y = float(node["y"])
    w = float(node["w"])
    h = float(node["h"])
    cx = x + w / 2
    lines, label_font, caption_font, caption, line_height = fit_node_text(node)
    caption_gap = 8.0 if caption else 0.0
    caption_height = (caption_font or 0.0) * 1.35 if caption else 0.0
    text_block_height = len(lines) * line_height + caption_gap + caption_height
    label_y = y + ((h - text_block_height) / 2.0) + label_font * 0.78

    parts = [f'<g class="node" id="node-{escape(node["id"])}">']
    parts.append(
        f'<path class="node-fill" style="fill: var(--{fill_var});" d="{node_path(node, 0)}" />'
    )
    parts.append(f'<path class="node-stroke" d="{node_path(node, 0)}" />')
    parts.append(f'<path class="node-stroke ghost" d="{node_path(node, 1)}" />')
    parts.append(
        f'<text class="node-label" style="font-size: {fmt(label_font)}px;" x="{fmt(cx)}" y="{fmt(label_y)}">'
    )
    for index, line in enumerate(lines or [" "]):
        dy = "0" if index == 0 else fmt(line_height)
        parts.append(f'<tspan x="{fmt(cx)}" dy="{dy}">{escape(line)}</tspan>')
    parts.append("</text>")
    if caption and caption_font:
        caption_y = label_y + len(lines) * line_height + caption_gap + caption_font * 0.76
        parts.append(
            f'<text class="node-caption" style="font-size: {fmt(caption_font)}px;" x="{fmt(cx)}" y="{fmt(caption_y)}">{escape(caption)}</text>'
        )
    parts.append("</g>")
    return "\n".join(parts)


def edge_label_size(label_text: str) -> tuple[float, float, list[str]]:
    raw_lines = text_lines(label_text) or [label_text]
    wrapped = wrap_text_to_width(
        raw_lines,
        EDGE_LABEL_MAX_WIDTH - (EDGE_LABEL_PAD_X * 2),
        EDGE_LABEL_FONT_SIZE,
    )
    lines = wrapped or [""]
    if len(lines) > EDGE_LABEL_MAX_LINES:
        kept = lines[:EDGE_LABEL_MAX_LINES]
        kept[-1] = truncate_line_to_width(
            "".join(lines[EDGE_LABEL_MAX_LINES - 1 :]),
            EDGE_LABEL_MAX_WIDTH - (EDGE_LABEL_PAD_X * 2),
            EDGE_LABEL_FONT_SIZE,
        )
        lines = kept
    line_w = max(text_width_px(line, EDGE_LABEL_FONT_SIZE) for line in lines)
    width = min(
        max(EDGE_LABEL_MIN_WIDTH, line_w + (EDGE_LABEL_PAD_X * 2)),
        EDGE_LABEL_MAX_WIDTH,
    )
    height = EDGE_LABEL_LINE_HEIGHT * len(lines) + (EDGE_LABEL_PAD_Y * 2)
    return width, height, lines


def label_hits_edge(
    rect: tuple[float, float, float, float],
    edge_samples: list[list[tuple[float, float]]],
) -> bool:
    for samples in edge_samples:
        for point in samples:
            if point_in_rect(point, rect, LABEL_EDGE_MARGIN):
                return True
    return False


def fallback_label_score(
    rect: tuple[float, float, float, float],
    canvas_width: float,
    canvas_height: float,
    node_rects: list[tuple[float, float, float, float]],
    used_label_rects: list[tuple[float, float, float, float]],
    edge_samples: list[list[tuple[float, float]]],
    offset: float,
    t_value: float,
) -> float:
    score = 0.0
    score -= off_canvas_penalty(rect, canvas_width, canvas_height, LABEL_OUTER_PADDING) * 14
    score -= offset * 0.6
    score -= abs(t_value - 0.5) * 30
    for node_rect in node_rects:
        if rect_intersects(rect, node_rect, LABEL_NODE_MARGIN):
            score -= 1000
    for used_rect in used_label_rects:
        if rect_intersects(rect, used_rect, LABEL_LABEL_MARGIN):
            score -= 800
    edge_hits = 0
    for samples in edge_samples:
        for point in samples:
            if point_in_rect(point, rect, LABEL_EDGE_MARGIN):
                edge_hits += 1
    score -= edge_hits * 36
    return score


def choose_label_rect(
    geometry: dict[str, object],
    label_width: float,
    label_height: float,
    canvas_width: float,
    canvas_height: float,
    node_rects: list[tuple[float, float, float, float]],
    used_label_rects: list[tuple[float, float, float, float]],
    edge_samples: list[list[tuple[float, float]]],
) -> tuple[float, float, float, float]:
    start = geometry["start"]
    cp1 = geometry["cp1"]
    cp2 = geometry["cp2"]
    end = geometry["end"]
    # Keep labels centered on the middle section of the edge by default.
    t_value = 0.5
    point = cubic_point(start, cp1, cp2, end, t_value)
    normal = unit_normal(cubic_derivative(start, cp1, cp2, end, t_value))
    tangent = cubic_derivative(start, cp1, cp2, end, t_value)
    tan_len = math.hypot(tangent[0], tangent[1]) or 1.0
    tx = tangent[0] / tan_len
    ty = tangent[1] / tan_len
    normal_offsets = (0.0, 18.0, -18.0, 30.0, -30.0, 44.0, -44.0, 60.0, -60.0)
    tangent_offsets = (0.0, -20.0, 20.0, -34.0, 34.0, -50.0, 50.0)
    candidates: list[tuple[float, tuple[float, float, float, float]]] = []

    for tangent_offset in tangent_offsets:
        for normal_offset in normal_offsets:
            rect = rect_from_center(
                point[0] + (tx * tangent_offset) + (normal[0] * normal_offset),
                point[1] + (ty * tangent_offset) + (normal[1] * normal_offset),
                label_width,
                label_height,
            )
            score = 0.0
            score += off_canvas_penalty(
                rect,
                canvas_width,
                canvas_height,
                LABEL_OUTER_PADDING,
            ) * 140.0
            score += abs(normal_offset) * 0.9
            score += abs(tangent_offset) * 0.55
            for node_rect in node_rects:
                if rect_intersects(rect, node_rect, 0.0):
                    score += 8000.0
            for used_rect in used_label_rects:
                if rect_intersects(rect, used_rect, 0.0):
                    score += 12000.0
            candidates.append((score, rect))

    if candidates:
        return min(candidates, key=lambda item: item[0])[1]
    return rect_from_center(point[0], point[1], label_width, label_height)


def separate_label_from_nodes(
    rect: tuple[float, float, float, float],
    node_rects: list[tuple[float, float, float, float]],
    canvas_width: float,
    canvas_height: float,
    margin: float = LABEL_NODE_MARGIN,
) -> tuple[float, float, float, float]:
    origin = clamp_rect_to_canvas(rect, canvas_width, canvas_height)
    ox, oy, lw, lh = origin
    distances = (0.0, 28.0, 48.0, 72.0, 98.0, 126.0, 156.0, 188.0, 222.0, 258.0)
    directions = (
        (0.0, 0.0),
        (1.0, 0.0),
        (-1.0, 0.0),
        (0.0, 1.0),
        (0.0, -1.0),
        (0.707, 0.707),
        (0.707, -0.707),
        (-0.707, 0.707),
        (-0.707, -0.707),
    )
    best = origin
    best_score = float("inf")
    for distance in distances:
        for dx, dy in directions:
            candidate = clamp_rect_to_canvas(
                (ox + (dx * distance), oy + (dy * distance), lw, lh),
                canvas_width,
                canvas_height,
            )
            penalty_hits = 0
            penalty_area = 0.0
            for node_rect in node_rects:
                if rect_intersects(candidate, node_rect, margin):
                    penalty_hits += 1
                    penalty_area += rect_overlap_area(candidate, node_rect, margin)
            move_cost = math.hypot(candidate[0] - ox, candidate[1] - oy)
            score = (penalty_hits * 100000.0) + (penalty_area * 100.0) + move_cost
            if score < best_score:
                best = candidate
                best_score = score
            if penalty_hits == 0:
                return candidate
    return best


def separate_label_from_existing_labels(
    rect: tuple[float, float, float, float],
    used_label_rects: list[tuple[float, float, float, float]],
    canvas_width: float,
    canvas_height: float,
    margin: float = LABEL_LABEL_MARGIN,
) -> tuple[float, float, float, float]:
    out = clamp_rect_to_canvas(rect, canvas_width, canvas_height)
    for _ in range(10):
        moved = False
        lx, ly, lw, lh = out
        lcx, lcy = rect_center(out)
        for used_rect in used_label_rects:
            if not rect_intersects(out, used_rect, margin):
                continue
            ucx, ucy = rect_center(used_rect)
            dx = lcx - ucx
            dy = lcy - ucy
            length = math.hypot(dx, dy) or 1.0
            step = 8.0 + margin
            lx += (dx / length) * step
            ly += (dy / length) * step
            moved = True
            out = clamp_rect_to_canvas((lx, ly, lw, lh), canvas_width, canvas_height)
            lcx, lcy = rect_center(out)
        if not moved:
            break
    return out


def layout_edge_labels(
    edges: list[dict],
    geometries: list[dict[str, object]],
    nodes: dict[str, dict],
    width: float,
    height: float,
) -> list[dict[str, object] | None]:
    node_rects = [node_bounds(node) for node in nodes.values()]
    edge_samples = [
        sample_cubic_points(
            geometry["start"],
            geometry["cp1"],
            geometry["cp2"],
            geometry["end"],
        )
        for geometry in geometries
    ]
    used_label_rects: list[tuple[float, float, float, float]] = []
    placements: list[dict[str, object] | None] = []

    for index, edge in enumerate(edges):
        label = edge.get("label")
        if not label:
            placements.append(None)
            continue
        label_width, label_height, lines = edge_label_size(str(label))
        rect = choose_label_rect(
            geometries[index],
            label_width,
            label_height,
            width,
            height,
            node_rects,
            used_label_rects,
            edge_samples,
        )
        used_label_rects.append(rect)
        placements.append({"rect": rect, "lines": lines})
    return placements


def render_edge(
    edge: dict,
    index: int,
    geometry: dict[str, object],
    label_layout: dict[str, object] | None,
) -> str:
    tone = edge.get("tone", "sky")
    flow_var = TONE_TO_FLOW.get(tone, "flow_sky")
    duration = float(edge.get("duration", 2.2))
    path = geometry["path"]
    stroke_width = float(geometry["stroke_width"])
    dash_a = float(geometry["dash_a"])
    dash_b = float(geometry["dash_b"])
    label = edge.get("label")
    parts = [f'<g class="edge edge-{index}">']
    parts.append(
        f'<path class="pipe-flow" style="stroke: var(--{flow_var}); stroke-width: {fmt(stroke_width)}; stroke-dasharray: {fmt(dash_a)} {fmt(dash_b)}; animation-duration: {fmt(duration)}s;" d="{path}" />'
    )
    if label and label_layout:
        lx, ly, label_width, label_height = label_layout["rect"]
        lines = label_layout["lines"]
        label_center_x = lx + label_width / 2
        total_text_height = EDGE_LABEL_LINE_HEIGHT * len(lines)
        label_text_y = (
            ly
            + EDGE_LABEL_PAD_Y
            + ((label_height - (EDGE_LABEL_PAD_Y * 2) - total_text_height) / 2.0)
            + EDGE_LABEL_FONT_SIZE * 0.8
        )
        parts.append(
            f'<rect class="edge-label-bg" x="{fmt(lx)}" y="{fmt(ly)}" width="{fmt(label_width)}" height="{fmt(label_height)}" rx="16" />'
        )
        parts.append(
            f'<text class="edge-label" style="font-size: {fmt(EDGE_LABEL_FONT_SIZE)}px;" x="{fmt(label_center_x)}" y="{fmt(label_text_y)}">'
        )
        for line_index, line in enumerate(lines):
            dy = "0" if line_index == 0 else fmt(EDGE_LABEL_LINE_HEIGHT)
            parts.append(
                f'<tspan x="{fmt(label_center_x)}" dy="{dy}">{escape(line)}</tspan>'
            )
        parts.append("</text>")
    parts.append("</g>")
    return "\n".join(parts)


def render_svg(spec: dict) -> str:
    width = int(spec.get("width", 1440))
    height = int(spec.get("height", 900))
    title = escape(spec.get("title", "SVG flow diagram"))
    subtitle = escape(spec.get("subtitle", "Animated pipeline diagram"))
    theme = dict(DEFAULT_THEME)
    theme.update(spec.get("theme", {}))
    metrics = header_metrics(spec)
    nodes_list = [dict(node) for node in spec.get("nodes", [])]
    groups = [dict(group) for group in spec.get("groups", [])]
    edges = spec.get("edges", [])
    min_content_y = min(
        [float(node["y"]) for node in nodes_list]
        + [float(group["y"]) for group in groups]
        + [height],
    )
    header_bottom = metrics["bottom"]
    min_top = 0.0
    if header_bottom > 0:
        required_top = header_bottom + HEADER_CONTENT_GAP
        min_top = required_top
        if min_content_y < required_top:
            delta = required_top - min_content_y
            for node in nodes_list:
                node["y"] = float(node["y"]) + delta
            for group in groups:
                group["y"] = float(group["y"]) + delta
    normalize_node_spacing_2d(nodes_list)
    enforce_edge_label_corridors(nodes_list, edges)
    clamp_nodes_to_canvas(nodes_list, float(width), min_top=min_top, clamp_right=False)
    avoid_edge_node_overlaps(
        nodes_list,
        edges,
        float(width),
        min_top=min_top,
    )
    normalize_node_spacing_2d(nodes_list)
    normalize_node_vertical_spacing(nodes_list)
    enforce_edge_label_corridors(nodes_list, edges)
    clamp_nodes_to_canvas(nodes_list, float(width), min_top=min_top, clamp_right=False)
    enforce_edge_label_corridors(nodes_list, edges)
    clamp_nodes_to_canvas(nodes_list, float(width), min_top=min_top, clamp_right=False)
    content_right = max(
        [float(node["x"]) + float(node["w"]) for node in nodes_list]
        + [float(group["x"]) + float(group["w"]) for group in groups]
        + [0.0]
    )
    width = max(width, int(math.ceil(content_right + CANVAS_SIDE_PADDING)))
    content_bottom = max(
        [float(node["y"]) + float(node["h"]) for node in nodes_list]
        + [float(group["y"]) + float(group["h"]) for group in groups]
        + [0.0]
    )
    height = max(height, int(math.ceil(content_bottom + CANVAS_BOTTOM_PADDING)))
    nodes = {node["id"]: node for node in nodes_list}
    theme_css = "\n".join(
        f"      --{key.replace('_', '-')}: {value};" for key, value in theme.items()
    )

    node_markup = "\n".join(render_node(node) for node in nodes_list)
    edge_geometries = [edge_geometry(edge, nodes) for edge in edges]
    edge_label_layouts = layout_edge_labels(edges, edge_geometries, nodes, width, height)
    edge_markup = "\n".join(
        render_edge(edge, index, edge_geometries[index], edge_label_layouts[index])
        for index, edge in enumerate(edges)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="diagram-title diagram-subtitle">
  <title id="diagram-title">{title}</title>
  <desc id="diagram-subtitle">{subtitle}</desc>
  <defs>
    <pattern id="paper-dots" width="28" height="28" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1" fill="var(--grid)" opacity="0.45" />
      <circle cx="16" cy="12" r="0.8" fill="var(--grid)" opacity="0.28" />
      <circle cx="10" cy="22" r="0.9" fill="var(--grid)" opacity="0.22" />
    </pattern>
    <marker id="pipe-arrow" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="8" markerHeight="8" orient="auto">
      <path d="M 2 2 L 10 6 L 2 10" fill="none" stroke="context-stroke" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
    </marker>
  </defs>
  <style>
    :root {{
{theme_css}
      --font-hand: Virgil, "Segoe Print", "Bradley Hand", "Comic Sans MS", cursive;
      --font-sans: "Avenir Next", "Segoe UI", sans-serif;
    }}

    .canvas-bg {{
      fill: var(--bg-paper);
    }}

    .canvas-grain {{
      fill: url(#paper-dots);
    }}

    .title {{
      fill: var(--ink);
      font-family: var(--font-hand);
      font-size: 30px;
      font-weight: 600;
      letter-spacing: 0.2px;
    }}

    .subtitle {{
      fill: var(--muted);
      font-family: var(--font-sans);
      font-size: 14px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}

    .group-frame {{
      fill: none;
      stroke: var(--grid);
      stroke-width: 2;
      stroke-dasharray: 10 12;
    }}

    .group-title {{
      fill: var(--muted);
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}

    .node-fill {{
      stroke: none;
    }}

    .node-stroke {{
      fill: none;
      stroke: var(--ink);
      stroke-width: 2.2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}

    .node-stroke.ghost {{
      opacity: 0.38;
    }}

    .node-label {{
      fill: var(--ink);
      font-family: var(--font-hand);
      font-size: 18px;
      font-weight: 600;
      text-anchor: middle;
    }}

    .node-caption {{
      fill: var(--muted);
      font-family: var(--font-sans);
      font-size: 12.5px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-anchor: middle;
      text-transform: uppercase;
    }}

    .pipe-flow {{
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
      marker-end: url(#pipe-arrow);
      animation: flow linear infinite;
    }}

    .edge-label-bg {{
      fill: rgba(252, 251, 247, 0.96);
      stroke: rgba(45, 41, 38, 0.12);
      stroke-width: 1;
    }}

    .edge-label {{
      fill: var(--ink);
      font-family: var(--font-hand);
      font-size: 13.5px;
      font-weight: 600;
      text-anchor: middle;
    }}

    @keyframes flow {{
      from {{
        stroke-dashoffset: 0;
      }}
      to {{
        stroke-dashoffset: -44;
      }}
    }}
  </style>
  <rect class="canvas-bg" x="0" y="0" width="{width}" height="{height}" />
  <rect class="canvas-grain" x="0" y="0" width="{width}" height="{height}" />
  {render_header(spec, metrics)}
  {render_groups(groups)}
  <g class="edges">
    {edge_markup}
  </g>
  <g class="nodes">
    {node_markup}
  </g>
</svg>
"""


def main() -> None:
    args = parse_args()
    spec_path = Path(args.spec)
    output_path = Path(args.output)
    spec = json.loads(spec_path.read_text())
    output_path.write_text(render_svg(spec))
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
