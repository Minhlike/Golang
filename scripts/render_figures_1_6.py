"""
Render Figures 1 to 6 for Golang Living Textbook.
Authoritative Source of Truth & Real Matplotlib Geometric Auditor:
- Authoritative specification: This script defines the canonical semantic models for
  Figures 1 to 6, renders the print-ready PNGs, and auto-synchronizes the companion
  .puml files so they never drift semantically.
- Geometry: Printable width 168 mm (476.22 pt), max height <= 128 mm (362.83 pt).
- Effective DPI: >= 320 DPI at 1:1 print scale.
- Pure Grayscale: R = G = B for every pixel (diff1 = diff2 = 0).
- Typography: Source Sans 3 and JetBrains Mono, all font sizes >= 6.0 pt (enforced >= 6.2 pt).
- Real Glyph Width Wrapping: wrap_text_strictly() measures actual rendered glyph width
  via Matplotlib's FreeType renderer (not merely character counts) and raises ValueError
  on any width or line-count overflow.
- Real Geometric Collision & Safe Padding Audit: FigureGeometryAuditor verifies after
  fig.canvas.draw() that:
  1. Every text artist is registered to an explicit logical container.
  2. Every text artist's rendered glyph bounding box stays inside its container with
     safe padding >= 4.0 pt on all sides.
  3. No text glyph bounding box intersects any box border, divider line, polygon edge,
     or connector line (distinguishing any explicitly declared intentional touches).
  4. No two text artists overlap.
  5. All artists lie strictly inside the canvas without clipping.
"""

import os
import sys
import math
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ASSETS_DIR = os.path.join(ROOT_DIR, 'assets', 'diagrams')
FONTS_DIR = os.path.join(ROOT_DIR, 'assets', 'fonts')

FONT_REG = FontProperties(fname=os.path.join(FONTS_DIR, 'SourceSans3-Regular.ttf'))
FONT_BOLD = FontProperties(fname=os.path.join(FONTS_DIR, 'SourceSans3-Semibold.ttf'))
FONT_MONO = FontProperties(fname=os.path.join(FONTS_DIR, 'JetBrainsMono-Regular.ttf'))

PT_PER_MM = 72.0 / 25.4          # ~2.83464567 pt per mm
MM_PER_PT = 25.4 / 72.0          # ~0.35277778 mm per pt
PRINTABLE_WIDTH_MM = 168.0
PRINTABLE_WIDTH_PT = PRINTABLE_WIDTH_MM * PT_PER_MM  # 476.22 pt
MAX_FIG_HEIGHT_MM = 128.0
MAX_FIG_HEIGHT_PT = MAX_FIG_HEIGHT_MM * PT_PER_MM    # 362.83 pt
MIN_SAFE_PADDING_PT = 4.0
MIN_FONT_SIZE_PT = 6.0

# Cached offscreen measurement canvas so wrap_text_strictly can measure real glyph extents
_MEASURE_FIG = None
_MEASURE_AX = None
_MEASURE_RENDERER = None


def _get_measure_context():
    global _MEASURE_FIG, _MEASURE_AX, _MEASURE_RENDERER
    if _MEASURE_FIG is None:
        _MEASURE_FIG, _MEASURE_AX = plt.subplots(figsize=(PRINTABLE_WIDTH_MM / 25.4, 100.0 / 25.4), dpi=320)
        _MEASURE_FIG.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
        _MEASURE_AX.set_xlim(0.0, PRINTABLE_WIDTH_MM)
        _MEASURE_AX.set_ylim(0.0, 100.0)
        _MEASURE_AX.set_aspect('equal')
        _MEASURE_AX.axis('off')
        _MEASURE_FIG.canvas.draw()
        _MEASURE_RENDERER = _MEASURE_FIG.canvas.get_renderer()
    return _MEASURE_FIG, _MEASURE_AX, _MEASURE_RENDERER


def measure_text_bbox_mm(text, fontproperties=FONT_REG, fontsize=6.2):
    """
    Measure the exact rendered glyph width and height (in mm and pt) of a single line
    of text using Matplotlib's FreeType renderer.
    """
    if not text:
        return 0.0, 0.0, 0.0, 0.0
    _, ax, renderer = _get_measure_context()
    t = ax.text(10.0, 10.0, text, fontproperties=fontproperties, fontsize=fontsize,
                ha='left', va='baseline')
    bbox_disp = t.get_window_extent(renderer=renderer)
    bbox_data = bbox_disp.transformed(ax.transData.inverted())
    t.remove()
    w_mm = float(bbox_data.width)
    h_mm = float(bbox_data.height)
    return w_mm, h_mm, w_mm * PT_PER_MM, h_mm * PT_PER_MM


def wrap_text_strictly(
    text,
    max_chars_per_line=None,
    max_lines=3,
    context="",
    max_width_mm=None,
    fontproperties=FONT_REG,
    fontsize=6.2,
):
    """
    Wrap text into lines without dropping any characters, verifying BOTH character budget
    (if given) AND actual rendered glyph width in mm (using Matplotlib's renderer).
    Raises ValueError immediately if a single token exceeds the width budget or if the
    wrapped text requires more than max_lines.
    """
    if max_width_mm is None and max_chars_per_line is not None:
        # Derive a conservative physical width budget if only max_chars_per_line was supplied,
        # while still enforcing real glyph measurement on every line.
        max_width_mm = max_chars_per_line * (fontsize * 0.55 * MM_PER_PT)

    words = text.split()
    lines = []
    cur = ""
    for w in words:
        w_width_mm, _, _, _ = measure_text_bbox_mm(w, fontproperties=fontproperties, fontsize=fontsize)
        if max_width_mm is not None and w_width_mm > max_width_mm:
            raise ValueError(
                f"GLYPH WIDTH OVERFLOW in {context}: single word '{w}' width "
                f"{w_width_mm:.2f} mm ({w_width_mm * PT_PER_MM:.2f} pt) > max_width_mm {max_width_mm:.2f} mm"
            )
        candidate = f"{cur} {w}".strip() if cur else w
        cand_width_mm, _, _, _ = measure_text_bbox_mm(candidate, fontproperties=fontproperties, fontsize=fontsize)
        char_exceeded = (max_chars_per_line is not None and len(candidate) > max_chars_per_line)
        width_exceeded = (max_width_mm is not None and cand_width_mm > max_width_mm)

        if char_exceeded or width_exceeded:
            if cur:
                lines.append(cur)
                cur = w
            else:
                raise ValueError(
                    f"TEXT OVERFLOW in {context}: token '{w}' cannot fit within constraints "
                    f"(width={cand_width_mm:.2f} mm, max_width_mm={max_width_mm})"
                )
        else:
            cur = candidate

    if cur:
        lines.append(cur)

    if len(lines) > max_lines:
        raise ValueError(
            f"TEXT OVERFLOW in {context}: generated {len(lines)} lines > max {max_lines}.\n"
            f"Text: '{text}'\n"
            f"Lines: {lines}"
        )
    return lines


def _point_to_segment_dist_mm(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    len_sq = dx * dx + dy * dy
    if len_sq == 0.0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / len_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def _segments_intersect(ax, ay, bx, by, cx, cy, dx, dy):
    def ccw(p1x, p1y, p2x, p2y, p3x, p3y):
        return (p3y - p1y) * (p2x - p1x) - (p2y - p1y) * (p3x - p1x)

    d1 = ccw(cx, cy, dx, dy, ax, ay)
    d2 = ccw(cx, cy, dx, dy, bx, by)
    d3 = ccw(ax, ay, bx, by, cx, cy)
    d4 = ccw(ax, ay, bx, by, dx, dy)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True

    eps = 1e-9
    if abs(d1) <= eps and min(cx, dx) - eps <= ax <= max(cx, dx) + eps and min(cy, dy) - eps <= ay <= max(cy, dy) + eps:
        return True
    if abs(d2) <= eps and min(cx, dx) - eps <= bx <= max(cx, dx) + eps and min(cy, dy) - eps <= by <= max(cy, dy) + eps:
        return True
    if abs(d3) <= eps and min(ax, bx) - eps <= cx <= max(ax, bx) + eps and min(ay, by) - eps <= cy <= max(ay, by) + eps:
        return True
    if abs(d4) <= eps and min(ax, bx) - eps <= dx <= max(ax, bx) + eps and min(ay, by) - eps <= dy <= max(ay, by) + eps:
        return True
    return False


def rect_to_segment_dist_mm(rx0, ry0, rx1, ry1, sx0, sy0, sx1, sy1):
    """
    Exact minimum Euclidean distance in mm between axis-aligned rectangle [rx0, ry0, rx1, ry1]
    and line segment (sx0, sy0)-(sx1, sy1). Returns 0.0 if the segment intersects or lies
    inside the rectangle.
    """
    if (rx0 <= sx0 <= rx1 and ry0 <= sy0 <= ry1) or (rx0 <= sx1 <= rx1 and ry0 <= sy1 <= ry1):
        return 0.0
    rect_edges = [
        (rx0, ry0, rx1, ry0),
        (rx1, ry0, rx1, ry1),
        (rx1, ry1, rx0, ry1),
        (rx0, ry1, rx0, ry0),
    ]
    for ex0, ey0, ex1, ey1 in rect_edges:
        if _segments_intersect(sx0, sy0, sx1, sy1, ex0, ey0, ex1, ey1):
            return 0.0

    dists = [
        _point_to_segment_dist_mm(rx0, ry0, sx0, sy0, sx1, sy1),
        _point_to_segment_dist_mm(rx1, ry0, sx0, sy0, sx1, sy1),
        _point_to_segment_dist_mm(rx1, ry1, sx0, sy0, sx1, sy1),
        _point_to_segment_dist_mm(rx0, ry1, sx0, sy0, sx1, sy1),
    ]
    for ex0, ey0, ex1, ey1 in rect_edges:
        dists.append(_point_to_segment_dist_mm(sx0, sy0, ex0, ey0, ex1, ey1))
        dists.append(_point_to_segment_dist_mm(sx1, sy1, ex0, ey0, ex1, ey1))
    return min(dists)


class FigureGeometryAuditor:
    """
    Real Matplotlib Geometric Auditor for Figures 1 to 6.
    Enforces:
    - All text artists registered to explicit logical containers.
    - All text artists have fontsize >= 6.0 pt.
    - Rendered glyph bbox inside container with safe padding >= 4.0 pt on all sides.
    - Zero unintended intersections between text glyph bboxes and box borders, polygon edges,
      divider lines, or connector lines.
    - Zero overlaps between distinct text artists.
    - Zero canvas clipping (all elements inside canvas with >= 4.0 pt margin).
    """

    def __init__(self, fig, ax, width_mm, height_mm, fig_name):
        self.fig = fig
        self.ax = ax
        self.width_mm = float(width_mm)
        self.height_mm = float(height_mm)
        self.fig_name = fig_name
        self.text_records = []
        self.border_segments = []   # (x0, y0, x1, y1, name, min_clearance_pt)
        self.connector_segments = []  # (x0, y0, x1, y1, name, min_clearance_pt)
        self.intentional_touches = set()  # set of (text_name, seg_name)
        self.last_report = None

    def register_box_borders(self, x0, y0, x1, y1, name, min_clearance_pt=1.5):
        edges = [
            (x0, y0, x1, y0, f"{name}:bottom"),
            (x1, y0, x1, y1, f"{name}:right"),
            (x1, y1, x0, y1, f"{name}:top"),
            (x0, y1, x0, y0, f"{name}:left"),
        ]
        for ex0, ey0, ex1, ey1, ename in edges:
            self.border_segments.append((float(ex0), float(ey0), float(ex1), float(ey1), ename, float(min_clearance_pt)))

    def register_divider_line(self, x0, y0, x1, y1, name, min_clearance_pt=1.5):
        self.border_segments.append((float(x0), float(y0), float(x1), float(y1), name, float(min_clearance_pt)))

    def register_polygon_borders(self, vertices, name, min_clearance_pt=1.5):
        n = len(vertices)
        for i in range(n):
            x0, y0 = vertices[i]
            x1, y1 = vertices[(i + 1) % n]
            self.border_segments.append((float(x0), float(y0), float(x1), float(y1), f"{name}:edge{i}", float(min_clearance_pt)))

    def register_connector_path(self, xs, ys, name, min_clearance_pt=1.2):
        for i in range(len(xs) - 1):
            self.connector_segments.append((
                float(xs[i]), float(ys[i]), float(xs[i + 1]), float(ys[i + 1]),
                f"{name}:seg{i}", float(min_clearance_pt)
            ))

    def allow_intentional_touch(self, text_name, seg_name_prefix):
        self.intentional_touches.add((text_name, seg_name_prefix))

    def add_text(
        self,
        x,
        y,
        text,
        container,
        name="",
        min_padding_pt=MIN_SAFE_PADDING_PT,
        v_center_in_container=False,
        **kwargs,
    ):
        t = self.ax.text(x, y, text, **kwargs)
        self.text_records.append({
            'artist': t,
            'container': container,
            'name': name or text[:24],
            'min_padding_pt': float(min_padding_pt),
            'v_center_in_container': bool(v_center_in_container),
        })
        return t

    def verify(self):
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()

        # Optional optical vertical centering for single-line headers/badges/titles
        recentered = False
        for rec in self.text_records:
            if rec['v_center_in_container'] and isinstance(rec['container'], tuple) and len(rec['container']) == 4:
                t = rec['artist']
                cx0, cy0, cx1, cy1 = rec['container']
                bbox_mm = t.get_window_extent(renderer=renderer).transformed(self.ax.transData.inverted())
                target_cy = 0.5 * (cy0 + cy1)
                current_cy = 0.5 * (bbox_mm.y0 + bbox_mm.y1)
                shift_y = target_cy - current_cy
                if abs(shift_y) > 0.02:
                    px, py = t.get_position()
                    t.set_position((px, py + shift_y))
                    recentered = True
        if recentered:
            self.fig.canvas.draw()
            renderer = self.fig.canvas.get_renderer()

        # 1. Verify no unregistered non-empty text artists exist on ax
        registered_artists = {rec['artist'] for rec in self.text_records}
        for t in self.ax.texts:
            if t.get_text().strip() and t not in registered_artists:
                raise ValueError(
                    f"UNREGISTERED TEXT ARTIST in {self.fig_name}: '{t.get_text()}' "
                    f"was added without a logical container binding."
                )

        # Also harvest any unregistered Line2D segments from ax.lines so nothing slips through
        recorded_line_coords = {
            (round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2))
            for (x0, y0, x1, y1, _, _) in (self.border_segments + self.connector_segments)
        }
        for idx, line in enumerate(self.ax.lines):
            xdata = line.get_xdata()
            ydata = line.get_ydata()
            for i in range(len(xdata) - 1):
                key = (round(float(xdata[i]), 2), round(float(ydata[i]), 2),
                       round(float(xdata[i + 1]), 2), round(float(ydata[i + 1]), 2))
                rev_key = (key[2], key[3], key[0], key[1])
                if key not in recorded_line_coords and rev_key not in recorded_line_coords:
                    self.connector_segments.append((
                        float(xdata[i]), float(ydata[i]), float(xdata[i + 1]), float(ydata[i + 1]),
                        f"auto_line_{idx}_seg{i}", 1.2
                    ))

        canvas_margin_mm = MIN_SAFE_PADDING_PT * MM_PER_PT
        min_observed_padding_pt = float('inf')
        min_observed_border_dist_pt = float('inf')
        min_observed_line_dist_pt = float('inf')
        rendered_bboxes = []

        for rec in self.text_records:
            t = rec['artist']
            txt = t.get_text()
            if not txt.strip():
                continue
            name = rec['name']
            fs = float(t.get_fontsize())
            if fs < MIN_FONT_SIZE_PT - 1e-6:
                raise ValueError(
                    f"FONT SIZE VIOLATION in {self.fig_name} [{name}]: "
                    f"fontsize={fs:.2f} pt < minimum {MIN_FONT_SIZE_PT:.2f} pt"
                )

            bbox_disp = t.get_window_extent(renderer=renderer)
            bbox_mm = bbox_disp.transformed(self.ax.transData.inverted())
            bx0, by0, bx1, by1 = float(bbox_mm.x0), float(bbox_mm.y0), float(bbox_mm.x1), float(bbox_mm.y1)

            # 2. Canvas bounds check
            if (bx0 < canvas_margin_mm - 1e-4 or by0 < canvas_margin_mm - 1e-4 or
                    bx1 > self.width_mm - canvas_margin_mm + 1e-4 or by1 > self.height_mm - canvas_margin_mm + 1e-4):
                raise ValueError(
                    f"CANVAS CLIPPING / MARGIN VIOLATION in {self.fig_name} [{name}]: "
                    f"text '{txt}' bbox=({bx0:.2f}, {by0:.2f}, {bx1:.2f}, {by1:.2f}) mm "
                    f"violates canvas (0, 0, {self.width_mm:.1f}, {self.height_mm:.1f}) mm"
                )

            # 3. Container safe padding check (>= 4.0 pt)
            cont = rec['container']
            req_pad_pt = rec['min_padding_pt']
            if isinstance(cont, tuple) and len(cont) == 4:
                cx0, cy0, cx1, cy1 = [float(v) for v in cont]
                pad_l_pt = (bx0 - cx0) * PT_PER_MM
                pad_r_pt = (cx1 - bx1) * PT_PER_MM
                pad_b_pt = (by0 - cy0) * PT_PER_MM
                pad_t_pt = (cy1 - by1) * PT_PER_MM
                min_pad = min(pad_l_pt, pad_r_pt, pad_b_pt, pad_t_pt)
                min_observed_padding_pt = min(min_observed_padding_pt, min_pad)
                if min_pad < req_pad_pt - 1e-4:
                    raise ValueError(
                        f"CONTAINER PADDING / OVERFLOW ERROR in {self.fig_name} [{name}]: "
                        f"text '{txt}' bbox=({bx0:.2f}, {by0:.2f}, {bx1:.2f}, {by1:.2f}) mm "
                        f"in container ({cx0:.2f}, {cy0:.2f}, {cx1:.2f}, {cy1:.2f}) mm "
                        f"has padding (L={pad_l_pt:.2f}, R={pad_r_pt:.2f}, B={pad_b_pt:.2f}, T={pad_t_pt:.2f}) pt "
                        f"< required {req_pad_pt:.2f} pt"
                    )
            elif isinstance(cont, tuple) and len(cont) == 5 and cont[0] == 'diamond':
                _, dcx, dcy, dhw, dhh = cont
                dcx, dcy, dhw, dhh = float(dcx), float(dcy), float(dhw), float(dhh)
                denom = math.hypot(1.0 / dhw, 1.0 / dhh)
                corner_pads_pt = []
                for px, py in [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]:
                    val = 1.0 - abs(px - dcx) / dhw - abs(py - dcy) / dhh
                    dist_mm = val / denom
                    corner_pads_pt.append(dist_mm * PT_PER_MM)
                min_pad = min(corner_pads_pt)
                min_observed_padding_pt = min(min_observed_padding_pt, min_pad)
                if min_pad < req_pad_pt - 1e-4:
                    raise ValueError(
                        f"DIAMOND CONTAINER PADDING / OVERFLOW ERROR in {self.fig_name} [{name}]: "
                        f"text '{txt}' has min perpendicular padding {min_pad:.2f} pt < {req_pad_pt:.2f} pt"
                    )
            else:
                raise ValueError(f"Invalid container specification for {name}: {cont}")

            # 4. Check against all registered box/polygon/divider border segments
            for sx0, sy0, sx1, sy1, sname, min_clr_pt in self.border_segments:
                if any(name == t_allow and sname.startswith(s_allow) for t_allow, s_allow in self.intentional_touches):
                    continue
                dist_pt = rect_to_segment_dist_mm(bx0, by0, bx1, by1, sx0, sy0, sx1, sy1) * PT_PER_MM
                min_observed_border_dist_pt = min(min_observed_border_dist_pt, dist_pt)
                if dist_pt < min_clr_pt - 1e-4:
                    raise ValueError(
                        f"BORDER COLLISION in {self.fig_name}: text '{txt}' [{name}] "
                        f"intersects or touches border [{sname}] (distance={dist_pt:.2f} pt < {min_clr_pt:.2f} pt)"
                    )

            # 5. Check against all connector / arrow line segments
            for sx0, sy0, sx1, sy1, sname, min_clr_pt in self.connector_segments:
                if any(name == t_allow and sname.startswith(s_allow) for t_allow, s_allow in self.intentional_touches):
                    continue
                dist_pt = rect_to_segment_dist_mm(bx0, by0, bx1, by1, sx0, sy0, sx1, sy1) * PT_PER_MM
                min_observed_line_dist_pt = min(min_observed_line_dist_pt, dist_pt)
                if dist_pt < min_clr_pt - 1e-4:
                    raise ValueError(
                        f"CONNECTOR LINE COLLISION in {self.fig_name}: text '{txt}' [{name}] "
                        f"intersects or touches line [{sname}] (distance={dist_pt:.2f} pt < {min_clr_pt:.2f} pt)"
                    )

            rendered_bboxes.append((bx0, by0, bx1, by1, name, txt))

        # 6. Pairwise text-to-text overlap check
        for i in range(len(rendered_bboxes)):
            ax0, ay0, ax1, ay1, aname, atxt = rendered_bboxes[i]
            for j in range(i + 1, len(rendered_bboxes)):
                bx0, by0, bx1, by1, bname, btxt = rendered_bboxes[j]
                overlap_x = min(ax1, bx1) - max(ax0, bx0)
                overlap_y = min(ay1, by1) - max(ay0, by0)
                if overlap_x > -0.15 and overlap_y > -0.15:
                    raise ValueError(
                        f"TEXT-TO-TEXT COLLISION in {self.fig_name}: "
                        f"'{atxt}' [{aname}] overlaps '{btxt}' [{bname}]"
                    )

        self.last_report = {
            'fig_name': self.fig_name,
            'text_count': len(rendered_bboxes),
            'border_segment_count': len(self.border_segments),
            'connector_segment_count': len(self.connector_segments),
            'min_container_padding_pt': round(min_observed_padding_pt, 2),
            'min_border_clearance_pt': round(min_observed_border_dist_pt, 2),
            'min_connector_clearance_pt': round(
                min_observed_line_dist_pt if min_observed_line_dist_pt != float('inf') else 99.9, 2
            ),
        }
        return self.last_report


def verify_image(filepath, target_dpi=320, geom_report=None):
    """
    Verify rendered PNG artifact:
    1. Pure grayscale: R = G = B for every pixel.
    2. Output dimensions & aspect ratio within A4 printable area (168 mm x 128 mm).
    3. Effective DPI >= 300 (specifically ~320 DPI) when placed in PDF.
    4. Outer canvas border pixels are clean white (no edge clipping).
    """
    im = Image.open(filepath).convert('RGB')
    w_px, h_px = im.size
    arr = np.array(im, dtype=np.int16)
    diff1 = int(np.max(np.abs(arr[:, :, 0] - arr[:, :, 1])))
    diff2 = int(np.max(np.abs(arr[:, :, 1] - arr[:, :, 2])))
    if diff1 != 0 or diff2 != 0:
        raise AssertionError(f"FAIL: {filepath} is not pure grayscale (diff={diff1},{diff2})")

    if w_px < 2116:
        raise AssertionError(f"FAIL: {filepath} pixel width {w_px} < required 2116 px for 320 DPI")

    # Compute effective DPI when scaled into PDF printable frame (476.22 pt x 362.83 pt)
    scale = min(PRINTABLE_WIDTH_PT / w_px, MAX_FIG_HEIGHT_PT / h_px)
    disp_w_pt = w_px * scale
    disp_h_pt = h_px * scale
    eff_dpi_x = w_px / (disp_w_pt / 72.0)
    eff_dpi_y = h_px / (disp_h_pt / 72.0)
    if eff_dpi_x < 300.0 or eff_dpi_y < 300.0:
        raise AssertionError(
            f"FAIL: {filepath} effective PDF DPI ({eff_dpi_x:.1f}, {eff_dpi_y:.1f}) < 300 DPI"
        )

    # Check outer 8-pixel perimeter is pure white (#FFFFFF) to prove no canvas clipping
    gray = arr[:, :, 0]
    border_min = min(
        int(np.min(gray[:8, :])),
        int(np.min(gray[-8:, :])),
        int(np.min(gray[:, :8])),
        int(np.min(gray[:, -8:])),
    )
    if border_min < 250:
        raise AssertionError(f"FAIL: {filepath} has non-white ink on outer canvas edge (min={border_min})")

    geom_info = ""
    if geom_report:
        geom_info = (
            f" | Texts: {geom_report['text_count']} "
            f"| MinPad: {geom_report['min_container_padding_pt']:.2f}pt "
            f"| MinBorderDist: {geom_report['min_border_clearance_pt']:.2f}pt "
            f"| MinLineDist: {geom_report['min_connector_clearance_pt']:.2f}pt"
        )
    print(
        f"VERIFIED: {os.path.basename(filepath)} | Size: {im.size} | "
        f"EffDPI: {eff_dpi_x:.1f} | Grayscale: OK (diff=0){geom_info}"
    )


def _draw_titled_card(
    ax, auditor, x, y, w, h, head_h,
    face_body='#F9F9F9', face_head='#E8E8E8', edge_col='#444444',
    lw=0.9, ls='-', rounding=2.0, card_name="card"
):
    """
    Draw a rounded card with a header bar and divider line, and register its
    outer borders and divider line with the FigureGeometryAuditor.
    Returns (head_container_tuple, body_container_tuple).
    """
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={rounding}",
        facecolor=face_body, edgecolor=edge_col, linewidth=lw, linestyle=ls
    )
    ax.add_patch(rect)

    y_div = y + h - head_h
    head = patches.FancyBboxPatch(
        (x, y_div), w, head_h,
        boxstyle=f"round,pad=0,rounding_size={rounding}",
        facecolor=face_head, edgecolor=edge_col, linewidth=lw, linestyle=ls
    )
    ax.add_patch(head)
    ax.add_patch(patches.Rectangle((x + 0.4, y_div), w - 0.8, min(2.2, head_h * 0.45),
                                   facecolor=face_head, edgecolor='none'))
    ax.plot([x, x + w], [y_div, y_div], color=edge_col, linewidth=max(0.7, lw - 0.15), linestyle=ls)

    auditor.register_box_borders(x, y, x + w, y + h, name=card_name, min_clearance_pt=MIN_SAFE_PADDING_PT)
    auditor.register_divider_line(x, y_div, x + w, y_div, name=f"{card_name}:divider", min_clearance_pt=MIN_SAFE_PADDING_PT)

    head_cont = (x, y_div, x + w, y + h)
    body_cont = (x, y, x + w, y_div)
    return head_cont, body_cont


# ==============================================================================
# AUTHORITATIVE SEMANTIC SPECIFICATIONS FOR FIGURES 1 TO 6
# ==============================================================================

FIG1_SPEC = {
    'title': 'DÒNG THỜI GIAN CÁC CỘT MỐC TIẾN HÓA CỦA GO (2007 – 2026)',
    'bus_label': 'Tiến trình tự lưu chuyển & mở rộng tính năng liên tục',
    'row1': [
        {
            'year': '2007',
            'title': 'Khởi thảo Ý tưởng',
            'tag': 'Giai đoạn vườn ươm',
            'desc': 'Griesemer, Pike, Thompson phác thảo mục tiêu giải quyết bế tắc scale phần mềm tại Google.'
        },
        {
            'year': '2008',
            'title': 'Compiler Thử nghiệm',
            'tag': 'Bộ công cụ đầu tiên',
            'desc': 'Trình biên dịch mẫu hoàn thành; cú pháp dần ổn định và bắt đầu thử nghiệm nội bộ.'
        },
        {
            'year': '2009',
            'title': 'Mở Mã Nguồn',
            'tag': '10 tháng 11, 2009',
            'desc': 'Công bố mã nguồn mở chính thức; hình thành cộng đồng đóng góp trên toàn cầu.'
        },
        {
            'year': '2012',
            'title': 'Go 1.0 Ra Mắt',
            'tag': 'Cam kết tương thích',
            'desc': 'Xác lập Cam kết Tương thích: hầu hết mã nguồn Go 1 tiếp tục biên dịch trong tương lai.'
        },
    ],
    'row2': [
        {
            'year': '2015',
            'title': 'Go 1.5 Tự thân',
            'tag': 'Tự biên dịch & GC',
            'desc': 'Viết lại compiler và runtime bằng Go & assembly; ra mắt Concurrent Garbage Collector.'
        },
        {
            'year': '2018',
            'title': 'Go 1.11 Modules',
            'tag': 'Quản lý phụ thuộc',
            'desc': 'Giới thiệu Go Modules (go.mod), chuẩn hóa quản lý gói không lệ thuộc $GOPATH.'
        },
        {
            'year': '2022',
            'title': 'Go 1.18 Generics',
            'tag': 'Tham số kiểu',
            'desc': 'Bổ sung Type Parameters (Generics), trừu tượng hóa thuật toán an toàn kiểu tĩnh.'
        },
        {
            'year': '2026',
            'title': 'Go 1.27 Đương đại',
            'tag': 'Mở rộng phương thức',
            'desc': 'Hoàn thiện Generic Methods trên kiểu dữ liệu; tối ưu hóa PGO và toolchain hiện đại.'
        },
    ],
}

FIG2_SPEC = {
    'title': 'DÒNG DÕI Ý TƯỞNG VÀ SỰ HỘI TỤ THỰC DỤNG VÀO GO',
    'pillars': [
        {
            'id': 'C_Lang',
            'name': 'DÒNG DÕI C (Kernighan, Ritchie)',
            'items': [
                '• Cú pháp biểu thức gọn: khối lệnh {}, toán tử cơ bản.',
                '• Con trỏ định vị ô nhớ trực tiếp (bỏ số học con trỏ).',
                '• Biên dịch thẳng ra mã máy tối ưu, hiệu năng cao.'
            ],
            'conn_lines': ['Cú pháp &', 'hiệu năng'],
        },
        {
            'id': 'Pascal_Lang',
            'name': 'DÒNG DÕI PASCAL (Wirth: Modula-2, Oberon-2)',
            'items': [
                '• Khai báo tên trước kiểu (name type) sáng sủa.',
                '• Cấu trúc package tường minh, phân tách ranh giới.',
                '• An toàn bộ nhớ tĩnh; loại bỏ hoàn toàn header files.'
            ],
            'conn_lines': ['Package &', 'an toàn kiểu'],
        },
        {
            'id': 'CSP_Lang',
            'name': 'TIẾN TRÌNH CSP (Hoare, Newsqueak, Alef, Limbo)',
            'items': [
                '• Giao tiếp tuần tự qua kênh (channels, goroutines).',
                '• Khuyến khích đồng bộ hóa qua gửi nhận thông điệp.',
                '• Điều phối ghép kênh phi tuần tự với toán tử select.'
            ],
            'conn_lines': ['Mô hình', 'đồng thời'],
        },
    ],
    'go_title': 'GOLANG: HỘI TỤ THỰC DỤNG',
    'go_sections': [
        ('KẾ THỪA & DUNG HÒA CHỌN LỌC', [
            '• Biên dịch nhanh, tạo mã máy & runtime tự hành.',
            '• Đồng thời: hỗ trợ cả channel (CSP) lẫn chia sẻ',
            '  bộ nhớ có đồng bộ (sync.Mutex, sync/atomic).',
            '• Giao diện ngầm định (static structural typing).'
        ]),
        ('TRIẾT LÝ TINH GIẢN (TỪ CHỐI CỐ Ý)', [
            '• KHÔNG kế thừa lớp phân cấp (no inheritance).',
            '• KHÔNG nạp chồng hàm/toán tử (no overloading).',
            '• KHÔNG số học con trỏ mặc định.',
            '• KHÔNG ép kiểu ngầm định (zero implicit cast).'
        ]),
    ],
    'conclusion_lines': [
        'Nguyên lý: Go kết hợp chọn lọc các ý tưởng kinh điển (hỗ trợ cả giao tiếp channel lẫn đồng bộ bộ nhớ chia sẻ),',
        'đồng thời kiên quyết loại bỏ các tính năng làm phức tạp hóa mô hình tư duy và làm chậm tốc độ biên dịch.'
    ],
}

FIG3_SPEC = {
    'title': 'VÒNG LẶP PHẢN HỒI THỰC NGHIỆM KHI HỌC VÀ LẬP TRÌNH GO',
    'steps': [
        {
            'num': 'BƯỚC 1',
            'title': 'Đặt Giả Thuyết Kỹ Thuật',
            'desc': 'Xác định kỳ vọng cụ thể trước khi chạy: đoạn mã sẽ trả về giá trị gì, thay đổi trạng thái nào hoặc báo lỗi gì?',
        },
        {
            'num': 'BƯỚC 2',
            'title': 'Chỉnh Sửa Nhỏ Nhất (Minimal Edit)',
            'desc': 'Thay đổi đúng một biến số độc lập để cô lập nguyên nhân; tránh sửa dồn nhiều chỗ cùng lúc.',
        },
        {
            'num': 'BƯỚC 3',
            'title': 'Đo Lường Bằng Bộ Công Cụ Chuẩn',
            'lines': [
                '• go fmt: Chuẩn hóa định dạng mã nguồn.',
                '• go vet: Phân tích tĩnh các cấu trúc đáng ngờ.',
                '• go test: Kiểm chứng hành vi theo kịch bản test.'
            ],
        },
    ],
    'diamond_lines': ['Kết quả thực tế', 'bác bỏ giả thuyết?'],
    'branch_yes': {
        'title': 'NHÁNH CÓ (BÁC BỎ): CHẨN ĐOÁN LỖI',
        'edge_label': 'CÓ (Bác bỏ)',
        'loop_label': 'Điều chỉnh giả thuyết & lặp lại',
        'lines': [
            '• Đọc chẩn đoán từ compiler, go vet hoặc test.',
            '• Khoanh vùng nguyên nhân gốc rễ (Root Cause).',
            '• Cập nhật giả thuyết và lặp lại từ Bước 1.'
        ],
    },
    'branch_no': {
        'title': 'NHÁNH KHÔNG (PHÙ HỢP): GHI NHẬN',
        'edge_label': 'KHÔNG (Phù hợp)',
        'lines': [
            '• Kết quả đo phù hợp với phạm vi kịch bản thử.',
            '• Củng cố mô hình tư duy bằng thực nghiệm.',
            '• Lưu commit sạch và chuyển sang bước kế tiếp.'
        ],
    },
    'conclusion_lines': [
        'Nguyên lý: Công cụ tự động cung cấp bằng chứng khách quan trong phạm vi kiểm tra của chúng;',
        'lập trình viên dựa trên tín hiệu thực nghiệm đó để hiệu chỉnh giả thuyết và hoàn thiện mô hình tư duy.'
    ],
}

FIG4_SPEC = {
    'window_title': 'main.go (Source Code Anatomy)',
    'code_items': [
        (0, 'package main'),
        (0, ''),
        (0, 'import "fmt"'),
        (0, ''),
        (0, 'const service = "checkout"'),
        (0, ''),
        (0, 'func classify(status int) string {'),
        (1, 'if status >= 500 {'),
        (2, 'return "failed"'),
        (1, '}'),
        (1, 'return "healthy"'),
        (0, '}'),
        (0, ''),
        (0, 'func main() {'),
        (1, 'status := 503'),
        (1, 'label := classify(status)'),
        (1, 'fmt.Println(service, label)'),
        (0, '}'),
    ],
    'cards': [
        {
            'title': '1. Khai báo Package (package main)',
            'lines': [
                '• Xác định không gian tên & ranh giới biên dịch.',
                '• Gói "main" chỉ thị compiler tạo tệp thực thi độc lập.'
            ],
            'anchor_line_idx': 0.0,
        },
        {
            'title': '2. Khai báo Import (import "fmt")',
            'lines': [
                '• Đưa package "fmt" vào phạm vi tệp để tham chiếu.',
                '• Giải quyết tại compile-time; không nạp động lúc chạy.'
            ],
            'anchor_line_idx': 2.0,
        },
        {
            'title': '3. Khai báo Cấp Package (const & func)',
            'lines': [
                '• Hằng số "service": chuỗi bất biến gán tại compile-time.',
                '• Hàm "classify": logic nhận int, trả string theo giá trị.'
            ],
            'anchor_line_idx': 7.5,
        },
        {
            'title': '4. Hàm Khởi điểm (func main)',
            'lines': [
                '• Điểm neo thực thi sau khi hoàn tất khởi tạo runtime.',
                '• Không nhận tham số và không trả mã lỗi trực tiếp.'
            ],
            'anchor_line_idx': 13.0,
        },
        {
            'title': '5. Biến Cục bộ & Lời Gọi Hàm',
            'lines': [
                '• "status := 503": Khai báo biến ngắn trong hàm main.',
                '• "fmt.Println": Lời gọi hàm xuất dữ liệu ra stdout.'
            ],
            'anchor_line_idx': 15.5,
        },
    ],
}

FIG5_SPEC = {
    'title': 'MÔ HÌNH CÁC LỚP XỬ LÝ CỦA GO COMPILER & LINKER',
    'subtitle': 'Kiến trúc cmd/compile & cmd/link: Parsing (syntax) → Type Checking (types2) → IR & Walk → SSA & Codegen → Linker',
    'layers': [
        {
            'id': 1,
            'tag': 'TẦNG 1: FRONTEND — PARSING (cmd/compile/internal/syntax)',
            'boxes': [
                ('Scanner / Lexer', ['Tách chuỗi nguồn thành luồng', 'token (từ khóa, tên, literal)']),
                ('Parser', ['Phân tích cấu trúc ngữ pháp', '→ Dựng cây cú pháp (Syntax Tree)']),
            ],
            'output': 'Cây cú pháp (Syntax Tree)',
            'has_rejection': True,
            'side_title': 'CỔNG CHẶN: SYNTAX ERROR',
            'side_lines': [
                '• Lỗi cú pháp, thiếu dấu, token lạ.',
                '• Compiler DỪNG NGAY tại Frontend.',
                '• Không kiểm tra kiểu hay sinh IR.'
            ],
        },
        {
            'id': 2,
            'tag': 'TẦNG 2: KIỂM TRA KIỂU & NGỮ NGHĨA (cmd/compile/internal/types2)',
            'boxes': [
                ('Name & Constant Check', ['Phân giải tên theo phạm vi (scope)', 'Đánh giá hằng & suy luận kiểu']),
                ('Strict Type Checker', ['Kiểm tra tương thích kiểu tĩnh', 'Chặn biến hoặc import thừa']),
            ],
            'output': 'Cú pháp đã kiểm tra kiểu (Typed Tree)',
            'has_rejection': True,
            'side_title': 'CỔNG CHẶN: TYPE ERROR',
            'side_lines': [
                '• Sai kiểu, undefined, biến/import thừa.',
                '• Báo lỗi biên dịch (compiler error).',
                '• Dừng ngay, không tạo IR hay mã máy.'
            ],
        },
        {
            'id': 3,
            'tag': 'TẦNG 3: IR, MIDDLE-END & SSA BACKEND (noder, ir, walk, ssa, obj)',
            'boxes': [
                ('1. Noding & IR', ['Chuyển sang IR', 'Inlining & escape']),
                ('2. Walk & SSA', ['Hạ cấu trúc lệnh', 'Dựng & tối ưu SSA']),
                ('3. Codegen (obj)', ['Hạ mã theo CPU', 'Tạo tệp .a / .o']),
            ],
            'output': 'Tệp đối tượng trung gian (.a / .o)',
            'has_rejection': False,
            'side_title': 'PHÂN ĐỊNH LỖI & CÔNG CỤ',
            'side_lines': [
                '• Compiler: chặn lỗi cú pháp & kiểu tĩnh.',
                '• go vet: cảnh báo cấu trúc đáng ngờ.',
                '• Runtime/Test: bắt panic, race & logic.'
            ],
        },
        {
            'id': 4,
            'tag': 'TẦNG 4: LINKER & ĐÓNG GÓI THỰC THI (cmd/link)',
            'boxes': [
                ('1. Symbol Link', ['Phân giải ký hiệu', 'giữa các package']),
                ('2. Runtime Link', ['Gắn Go runtime', '(GC, scheduler)']),
                ('3. Emit Binary', ['Xuất tệp thực thi', '(ELF / PE / Mach-O)']),
            ],
            'output': 'Tệp thực thi tự hành (Standalone Binary)',
            'has_rejection': False,
            'side_title': 'TỆP THỰC THI ĐỘC LẬP',
            'side_lines': [
                '• Đóng gói sẵn Go runtime & GC.',
                '• Không phụ thuộc máy ảo (Zero VM).',
                '• Chạy trực tiếp trên hệ điều hành đích.'
            ],
        },
    ],
}

FIG6_SPEC = {
    'title': 'TRỰC QUAN HÓA RANH GIỚI PHẠM VI TỪ VỰNG (LEXICAL SCOPE)',
    'subtitle': 'Quy tắc phân giải tên tại thời điểm biên dịch và sự tách biệt với vòng đời lưu trữ (storage lifetime)',
    'window_title': 'scope_demo.go — Cấu trúc Khối lệnh Lồng nhau',
    'scope1_label': 'SCOPE 1: Khối hàm func main()',
    'scope2_label': 'SCOPE 2: Khối con if block',
    'error_note': '[Ví dụ lỗi minh họa]: undefined: label',
    'cards': [
        {
            'title': '1. Tham chiếu Hợp lệ: Từ Khối con ra Khối cha',
            'status': '[PASS] Biểu thức tại if status >= 500',
            'pass': True,
            'lines': [
                '• Tại biểu thức điều kiện: Compiler tìm biến "status".',
                '• Scope 2 không có → Dò ngược ra Scope 1 (khối cha).',
                '• Thấy "status" khai báo trong main → Phân giải THÀNH CÔNG.'
            ],
        },
        {
            'title': '2. Tham chiếu Hợp lệ: Nội bộ trong Khối con',
            'status': '[PASS] Lời gọi trong if: fmt.Println(label)',
            'pass': True,
            'lines': [
                '• Tại lời gọi hàm bên trong if: Compiler tìm biến "label".',
                '• Khai báo "label := failed" nằm ngay trong Scope 2.',
                '• Tên "label" đang trong tầm vực → Phân giải THÀNH CÔNG.'
            ],
        },
        {
            'title': '3. [Ví dụ Lỗi]: Vi phạm Ranh giới Từ vựng',
            'status': '[FAIL] undefined: label ngoài khối if',
            'pass': False,
            'lines': [
                '• Tại lệnh ngoài khối if: cố gắng truy xuất biến "label".',
                '• Dấu "}" đã ĐÓNG Scope 2; "label" kết thúc phạm vi từ vựng.',
                '• Compiler không bao giờ dò vào khối con → Báo lỗi biên dịch.'
            ],
        },
    ],
    'bottom_title': 'PHÂN BIỆT RẠCH RÒI: PHẠM VI TỪ VỰNG (LEXICAL SCOPE) VÀ VÒNG ĐỜI LƯU TRỮ (LIFETIME)',
    'bottom_lines': [
        '1. Lexical Scope (Phạm vi từ vựng): Là quy tắc cú pháp tĩnh tại compile-time, xác định tên biến có thể được tham chiếu ở đâu.',
        '2. Storage Lifetime (Vòng đời vật lý): Là khoảng thời gian ô nhớ tồn tại (stack/heap); do compiler & runtime phối hợp quyết định',
        '   (như escape analysis, closure, con trỏ tham chiếu), hoàn toàn không đồng nhất hay suy diễn trực tiếp từ cú pháp khai báo.'
    ],
}


# ==============================================================================
# FIGURE RENDERERS (1 TO 6) WITH REAL GEOMETRIC AUDIT
# ==============================================================================

def render_fig1(custom_milestones=None, save=True):
    """
    Hình 1: Dòng thời gian tiến hóa của Go (go-history-timeline.png)
    """
    fig_w_mm = 168.0
    fig_h_mm = 92.0
    fig, ax = plt.subplots(figsize=(fig_w_mm / 25.4, fig_h_mm / 25.4), dpi=320)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
    ax.set_xlim(0.0, fig_w_mm)
    ax.set_ylim(0.0, fig_h_mm)
    ax.set_aspect('equal')
    ax.axis('off')

    auditor = FigureGeometryAuditor(fig, ax, fig_w_mm, fig_h_mm, "Fig1:go-history-timeline")
    ax.add_patch(patches.Rectangle((0, 0), fig_w_mm, fig_h_mm, facecolor='#FFFFFF', edgecolor='none'))

    # Title header (y: 81.5 to 89.5, h=8.0)
    t_x, t_y, t_w, t_h = 4.0, 81.5, 160.0, 8.0
    title_box = patches.FancyBboxPatch(
        (t_x, t_y), t_w, t_h,
        boxstyle="round,pad=0,rounding_size=1.8",
        facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.9
    )
    ax.add_patch(title_box)
    auditor.register_box_borders(t_x, t_y, t_x + t_w, t_y + t_h, "title_box")
    auditor.add_text(
        84.0, t_y + t_h / 2.0, FIG1_SPEC['title'],
        container=(t_x, t_y, t_x + t_w, t_y + t_h),
        name="fig1_title", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=8.5, color='#111111', ha='center', va='center'
    )

    row1 = custom_milestones.get('row1', FIG1_SPEC['row1']) if custom_milestones else FIG1_SPEC['row1']
    row2 = custom_milestones.get('row2', FIG1_SPEC['row2']) if custom_milestones else FIG1_SPEC['row2']

    card_w = 36.8
    gap_x = (160.0 - 4 * card_w) / 3.0  # 4.2667 mm
    start_x = 4.0
    h_card = 31.0
    h_head = 7.0

    for row_idx, (y_r, row_data) in enumerate([(47.0, row1), (5.0, row2)], start=1):
        for i, item in enumerate(row_data):
            x = start_x + i * (card_w + gap_x)
            cname = f"r{row_idx}_c{i+1}_{item['year']}"
            head_cont, body_cont = _draw_titled_card(
                ax, auditor, x, y_r, card_w, h_card, h_head,
                face_body='#F8F8F8', face_head='#E8E8E8', edge_col='#444444',
                lw=0.9, rounding=2.0, card_name=cname
            )

            # Year (left of header) and Tag (right of header)
            y_head_mid = y_r + h_card - h_head / 2.0
            auditor.add_text(
                x + 2.2, y_head_mid, item['year'],
                container=(x, y_r + h_card - h_head, x + 13.5, y_r + h_card),
                name=f"{cname}_year", v_center_in_container=True,
                fontproperties=FONT_BOLD, fontsize=8.0, color='#000000', ha='left', va='center'
            )
            auditor.add_text(
                x + card_w - 2.2, y_head_mid, item['tag'],
                container=(x + 12.0, y_r + h_card - h_head, x + card_w, y_r + h_card),
                name=f"{cname}_tag", v_center_in_container=True,
                fontproperties=FONT_REG, fontsize=6.2, color='#333333', ha='right', va='center'
            )

            # Body title + 3 wrapped lines
            y_body_top = y_r + h_card - h_head
            auditor.add_text(
                x + 2.2, y_body_top - 3.8, item['title'],
                container=body_cont, name=f"{cname}_title",
                fontproperties=FONT_BOLD, fontsize=7.0, color='#111111', ha='left', va='center'
            )

            max_text_w_mm = card_w - 2 * 2.2 - 0.6  # 31.8 mm -> ensures >= 2.2 mm (6.2 pt) L/R padding
            lines = wrap_text_strictly(
                item['desc'], max_chars_per_line=30, max_lines=3,
                max_width_mm=max_text_w_mm, fontproperties=FONT_REG, fontsize=6.2,
                context=f"Fig 1 Milestone {item['year']}"
            )
            for li, l_text in enumerate(lines):
                auditor.add_text(
                    x + 2.2, y_body_top - 9.0 - li * 4.5, l_text,
                    container=body_cont, name=f"{cname}_line{li+1}",
                    fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='left', va='center'
                )

            if i < 3:
                y_arr = y_r + (h_card - h_head) / 2.0
                ax.plot([x + card_w, x + card_w + gap_x], [y_arr, y_arr], color='#333333', linewidth=1.1)
                auditor.register_connector_path([x + card_w, x + card_w + gap_x], [y_arr, y_arr], f"{cname}_arrow")
                ax.annotate(
                    '', xy=(x + card_w + gap_x, y_arr), xytext=(x + card_w + gap_x - 1.2, y_arr),
                    arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6)
                )

    # Orthogonal bus from 2012 bottom (y=47.0) to 2015 top (y=36.0)
    x_2012 = start_x + 3 * (card_w + gap_x) + card_w / 2.0
    x_2015 = start_x + card_w / 2.0
    y_bus = 39.2  # Leaves 7.8 mm above y_bus to y_r1=47.0 for the bus label!

    ax.plot([x_2012, x_2012, x_2015, x_2015], [47.0, y_bus, y_bus, 36.0], color='#333333', linewidth=1.2)
    auditor.register_connector_path([x_2012, x_2012, x_2015, x_2015], [47.0, y_bus, y_bus, 36.0], "bus_2012_2015")
    ax.annotate(
        '', xy=(x_2015, 36.0), xytext=(x_2015, 37.2),
        arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.2, mutation_scale=7)
    )

    auditor.add_text(
        84.0, 43.1, FIG1_SPEC['bus_label'],
        container=(26.0, y_bus, 142.0, 47.0),
        name="bus_label", v_center_in_container=True,
        fontproperties=FONT_REG, fontsize=6.3, color='#333333', ha='center', va='center'
    )

    report = auditor.verify()
    out_path = os.path.join(ASSETS_DIR, 'go-history-timeline.png')
    if save:
        fig.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
        verify_image(out_path, geom_report=report)
    plt.close(fig)
    return report


def render_fig2(custom_spec=None, save=True):
    """
    Hình 2: Dòng dõi và sự hội tụ ý tưởng vào Go (go-idea-lineage.png)
    - Widen convergence corridor to 26 mm so 2-line arrow labels have > 14 pt clearance
      from both column borders and >= 4 pt vertical clearance from arrow shafts.
    - Wrap conclusion note into 2 balanced lines inside a 12 mm tall bottom container.
    """
    spec = custom_spec if custom_spec else FIG2_SPEC
    fig_w_mm = 168.0
    fig_h_mm = 116.0

    fig, ax = plt.subplots(figsize=(fig_w_mm / 25.4, fig_h_mm / 25.4), dpi=320)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
    ax.set_xlim(0.0, fig_w_mm)
    ax.set_ylim(0.0, fig_h_mm)
    ax.set_aspect('equal')
    ax.axis('off')

    auditor = FigureGeometryAuditor(fig, ax, fig_w_mm, fig_h_mm, "Fig2:go-idea-lineage")
    ax.add_patch(patches.Rectangle((0, 0), fig_w_mm, fig_h_mm, facecolor='#FFFFFF', edgecolor='none'))

    # Title box (y: 105.5 to 113.5, h=8.0)
    t_x, t_y, t_w, t_h = 4.0, 105.5, 160.0, 8.0
    ax.add_patch(patches.FancyBboxPatch(
        (t_x, t_y), t_w, t_h, boxstyle="round,pad=0,rounding_size=1.8",
        facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.9
    ))
    auditor.register_box_borders(t_x, t_y, t_x + t_w, t_y + t_h, "title_box")
    auditor.add_text(
        84.0, t_y + t_h / 2.0, spec['title'],
        container=(t_x, t_y, t_x + t_w, t_y + t_h),
        name="fig2_title", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=8.5, color='#111111', ha='center', va='center'
    )

    # Left Column: 3 Lineage Pillars (x: 4.0 to 74.0, width: 70.0)
    p_x = 4.0
    p_w = 70.0
    p_h = 26.0
    p_head_h = 6.5
    pillar_ys = [76.5, 47.5, 18.5]

    # Right Column: Convergent Go Box (x: 100.0 to 164.0, width: 64.0, y: 18.5 to 102.5)
    r_x = 100.0
    r_w = 64.0
    r_y = 18.5
    r_h = 84.0
    r_head_h = 8.0

    go_head_cont, go_body_cont = _draw_titled_card(
        ax, auditor, r_x, r_y, r_w, r_h, r_head_h,
        face_body='#F4F4F4', face_head='#333333', edge_col='#222222',
        lw=1.1, rounding=2.5, card_name="go_box"
    )
    auditor.add_text(
        r_x + r_w / 2.0, r_y + r_h - r_head_h / 2.0, spec['go_title'],
        container=go_head_cont, name="go_box_title", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=8.0, color='#FFFFFF', ha='center', va='center'
    )

    curr_y = r_y + r_h - r_head_h - 4.8
    for s_idx, (stitle, slines) in enumerate(spec['go_sections'], start=1):
        auditor.add_text(
            r_x + 2.8, curr_y, stitle,
            container=go_body_cont, name=f"go_sec{s_idx}_title",
            fontproperties=FONT_BOLD, fontsize=6.7, color='#111111', ha='left', va='center'
        )
        curr_y -= 5.2
        for l_idx, sline in enumerate(slines, start=1):
            auditor.add_text(
                r_x + 2.8, curr_y, sline,
                container=go_body_cont, name=f"go_sec{s_idx}_line{l_idx}",
                fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='left', va='center'
            )
            curr_y -= 4.8
        curr_y -= 4.2

    for idx, p in enumerate(spec['pillars']):
        py = pillar_ys[idx]
        pname = f"pillar_{idx+1}"
        head_cont, body_cont = _draw_titled_card(
            ax, auditor, p_x, py, p_w, p_h, p_head_h,
            face_body='#F9F9F9', face_head='#E8E8E8', edge_col='#444444',
            lw=0.9, rounding=2.0, card_name=pname
        )
        auditor.add_text(
            p_x + 2.5, py + p_h - p_head_h / 2.0, p['name'],
            container=head_cont, name=f"{pname}_title", v_center_in_container=True,
            fontproperties=FONT_BOLD, fontsize=6.8, color='#111111', ha='left', va='center'
        )
        y_body_top = py + p_h - p_head_h
        for li, itext in enumerate(p['items']):
            auditor.add_text(
                p_x + 2.5, y_body_top - 4.3 - li * 5.2, itext,
                container=body_cont, name=f"{pname}_item{li+1}",
                fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='left', va='center'
            )

        # Convergence arrow in corridor x: 74.0 -> 100.0 (width 26.0 mm)
        y_arr = py + 7.5
        ax.plot([p_x + p_w, r_x], [y_arr, y_arr], color='#333333', linewidth=1.1)
        auditor.register_connector_path([p_x + p_w, r_x], [y_arr, y_arr], f"{pname}_arrow")
        ax.annotate(
            '', xy=(r_x, y_arr), xytext=(r_x - 1.5, y_arr),
            arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6)
        )

        # Corridor container above arrow: (74.0, y_arr, 100.0, py + p_h) -> 26.0 mm wide x 18.5 mm tall
        corridor_cont = (p_x + p_w, y_arr, r_x, py + p_h)
        conn_lines = p['conn_lines']
        mid_corr_x = 0.5 * (p_x + p_w + r_x)
        if len(conn_lines) == 1:
            auditor.add_text(
                mid_corr_x, y_arr + 4.5, conn_lines[0],
                container=corridor_cont, name=f"{pname}_conn_line1",
                fontproperties=FONT_BOLD, fontsize=6.2, color='#333333', ha='center', va='center'
            )
        else:
            auditor.add_text(
                mid_corr_x, y_arr + 8.2, conn_lines[0],
                container=corridor_cont, name=f"{pname}_conn_line1",
                fontproperties=FONT_BOLD, fontsize=6.2, color='#333333', ha='center', va='center'
            )
            auditor.add_text(
                mid_corr_x, y_arr + 3.8, conn_lines[1],
                container=corridor_cont, name=f"{pname}_conn_line2",
                fontproperties=FONT_BOLD, fontsize=6.2, color='#333333', ha='center', va='center'
            )

    # Bottom Invariant Note (x: 4.0 to 164.0, y: 3.0 to 15.0, h=12.0)
    n_x, n_y, n_w, n_h = 4.0, 3.0, 160.0, 12.0
    ax.add_patch(patches.FancyBboxPatch(
        (n_x, n_y), n_w, n_h, boxstyle="round,pad=0,rounding_size=1.8",
        facecolor='#FAFAFA', edgecolor='#555555', linewidth=0.8
    ))
    auditor.register_box_borders(n_x, n_y, n_x + n_w, n_y + n_h, "note_box")
    note_cont = (n_x, n_y, n_x + n_w, n_y + n_h)
    c_lines = spec['conclusion_lines']
    if len(c_lines) == 1:
        auditor.add_text(
            84.0, n_y + n_h / 2.0, c_lines[0],
            container=note_cont, name="fig2_conclusion_1", v_center_in_container=True,
            fontproperties=FONT_BOLD, fontsize=6.2, color='#222222', ha='center', va='center'
        )
    else:
        auditor.add_text(
            84.0, n_y + 8.3, c_lines[0],
            container=note_cont, name="fig2_conclusion_1",
            fontproperties=FONT_BOLD, fontsize=6.2, color='#222222', ha='center', va='center'
        )
        auditor.add_text(
            84.0, n_y + 3.8, c_lines[1],
            container=note_cont, name="fig2_conclusion_2",
            fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='center', va='center'
        )

    report = auditor.verify()
    out_path = os.path.join(ASSETS_DIR, 'go-idea-lineage.png')
    if save:
        fig.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
        verify_image(out_path, geom_report=report)
    plt.close(fig)
    return report


def render_fig3(custom_spec=None, save=True):
    """
    Hình 3: Vòng lặp phản hồi thực nghiệm (feedback-loop.png)
    - Wrap Step 1 and Step 2 descriptions by real glyph width inside s_w = 78.0 mm.
    - Route CÓ and KHÔNG arrows cleanly without intersecting labels or missing target boxes.
    """
    spec = custom_spec if custom_spec else FIG3_SPEC
    fig_w_mm = 168.0
    fig_h_mm = 118.0

    fig, ax = plt.subplots(figsize=(fig_w_mm / 25.4, fig_h_mm / 25.4), dpi=320)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
    ax.set_xlim(0.0, fig_w_mm)
    ax.set_ylim(0.0, fig_h_mm)
    ax.set_aspect('equal')
    ax.axis('off')

    auditor = FigureGeometryAuditor(fig, ax, fig_w_mm, fig_h_mm, "Fig3:feedback-loop")
    ax.add_patch(patches.Rectangle((0, 0), fig_w_mm, fig_h_mm, facecolor='#FFFFFF', edgecolor='none'))

    # Title box (y: 107.5 to 115.5, h=8.0)
    t_x, t_y, t_w, t_h = 4.0, 107.5, 160.0, 8.0
    ax.add_patch(patches.FancyBboxPatch(
        (t_x, t_y), t_w, t_h, boxstyle="round,pad=0,rounding_size=1.8",
        facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.9
    ))
    auditor.register_box_borders(t_x, t_y, t_x + t_w, t_y + t_h, "title_box")
    auditor.add_text(
        84.0, t_y + t_h / 2.0, spec['title'],
        container=(t_x, t_y, t_x + t_w, t_y + t_h),
        name="fig3_title", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=8.5, color='#111111', ha='center', va='center'
    )

    # Left: 3 Steps (x: 6.0 to 84.0, width: 78.0)
    s_x = 6.0
    s_w = 78.0
    s_head_h = 6.2
    step_geoms = [
        (86.5, 18.0),  # Step 1: 86.5 to 104.5 (body 11.8 mm)
        (65.0, 18.0),  # Step 2: 65.0 to 83.0  (body 11.8 mm)
        (39.5, 22.0),  # Step 3: 39.5 to 61.5  (body 15.8 mm)
    ]

    for i, s in enumerate(spec['steps']):
        sy, sh = step_geoms[i]
        sname = f"step_{i+1}"
        head_cont, body_cont = _draw_titled_card(
            ax, auditor, s_x, sy, s_w, sh, s_head_h,
            face_body='#F9F9F9', face_head='#E8E8E8', edge_col='#444444',
            lw=0.9, rounding=2.0, card_name=sname
        )
        auditor.add_text(
            s_x + 2.5, sy + sh - s_head_h / 2.0, f"{s['num']}: {s['title']}",
            container=head_cont, name=f"{sname}_title", v_center_in_container=True,
            fontproperties=FONT_BOLD, fontsize=6.8, color='#111111', ha='left', va='center'
        )

        y_body_top = sy + sh - s_head_h
        max_line_w_mm = s_w - 2 * 2.5 - 0.6  # 72.4 mm
        if 'lines' in s:
            d_lines = s['lines']
            for li, dl in enumerate(d_lines):
                # Also verify each bullet fits max_line_w_mm
                wrap_text_strictly(
                    dl, max_lines=1, max_width_mm=max_line_w_mm,
                    fontproperties=FONT_REG, fontsize=6.2, context=f"Fig3 {sname} line {li+1}"
                )
                auditor.add_text(
                    s_x + 2.5, y_body_top - 3.8 - li * 4.3, dl,
                    container=body_cont, name=f"{sname}_line{li+1}",
                    fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='left', va='center'
                )
        else:
            d_lines = wrap_text_strictly(
                s['desc'], max_lines=2, max_width_mm=max_line_w_mm,
                fontproperties=FONT_REG, fontsize=6.2, context=f"Fig3 {sname}"
            )
            for li, dl in enumerate(d_lines):
                auditor.add_text(
                    s_x + 2.5, y_body_top - 3.8 - li * 4.4, dl,
                    container=body_cont, name=f"{sname}_line{li+1}",
                    fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='left', va='center'
                )

        if i < 2:
            next_top = step_geoms[i + 1][0] + step_geoms[i + 1][1]
            cx = s_x + s_w / 2.0
            ax.plot([cx, cx], [sy, next_top], color='#333333', linewidth=1.1)
            auditor.register_connector_path([cx, cx], [sy, next_top], f"step{i+1}_to_{i+2}")
            ax.annotate(
                '', xy=(cx, next_top), xytext=(cx, next_top + 1.2),
                arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6)
            )

    # Decision Diamond (center: 45.0, 27.5; hw=23.5, hh=9.0 -> x: 21.5..68.5, y: 18.5..36.5)
    d_cx, d_cy, d_hw, d_hh = 45.0, 27.5, 23.5, 9.0
    ax.plot([d_cx, d_cx], [39.5, d_cy + d_hh], color='#333333', linewidth=1.1)
    auditor.register_connector_path([d_cx, d_cx], [39.5, d_cy + d_hh], "step3_to_diamond")
    ax.annotate(
        '', xy=(d_cx, d_cy + d_hh), xytext=(d_cx, d_cy + d_hh + 1.2),
        arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6)
    )

    d_verts = [
        (d_cx, d_cy + d_hh),
        (d_cx + d_hw, d_cy),
        (d_cx, d_cy - d_hh),
        (d_cx - d_hw, d_cy),
    ]
    ax.add_patch(patches.Polygon(d_verts, closed=True, facecolor='#EEEEEE', edgecolor='#222222', linewidth=1.1))
    auditor.register_polygon_borders(d_verts, "decision_diamond")

    d_cont = ('diamond', d_cx, d_cy, d_hw, d_hh)
    auditor.add_text(
        d_cx, d_cy + 1.9, spec['diamond_lines'][0],
        container=d_cont, name="diamond_line1",
        fontproperties=FONT_BOLD, fontsize=6.3, color='#111111', ha='center', va='center'
    )
    auditor.add_text(
        d_cx, d_cy - 1.9, spec['diamond_lines'][1],
        container=d_cont, name="diamond_line2",
        fontproperties=FONT_BOLD, fontsize=6.3, color='#111111', ha='center', va='center'
    )

    # Right Branch Cards (x: 104.0 to 164.0, width: 60.0)
    b_x = 104.0
    b_w = 60.0
    b_head_h = 6.2

    # NHÁNH CÓ (y: 55.0 to 81.0, h=26.0)
    b1_y, b1_h = 55.0, 26.0
    b1_head, b1_body = _draw_titled_card(
        ax, auditor, b_x, b1_y, b_w, b1_h, b_head_h,
        face_body='#F6F6F6', face_head='#E2E2E2', edge_col='#444444',
        lw=0.9, ls='--', rounding=2.0, card_name="branch_yes"
    )
    auditor.add_text(
        b_x + 2.5, b1_y + b1_h - b_head_h / 2.0, spec['branch_yes']['title'],
        container=b1_head, name="branch_yes_title", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=6.6, color='#111111', ha='left', va='center'
    )
    for li, bl in enumerate(spec['branch_yes']['lines']):
        auditor.add_text(
            b_x + 2.5, b1_y + b1_h - b_head_h - 4.2 - li * 5.2, bl,
            container=b1_body, name=f"branch_yes_line{li+1}",
            fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='left', va='center'
        )

    # NHÁNH KHÔNG (y: 16.0 to 42.0, h=26.0)
    b2_y, b2_h = 16.0, 26.0
    b2_head, b2_body = _draw_titled_card(
        ax, auditor, b_x, b2_y, b_w, b2_h, b_head_h,
        face_body='#F9F9F9', face_head='#E8E8E8', edge_col='#333333',
        lw=1.0, ls='-', rounding=2.0, card_name="branch_no"
    )
    auditor.add_text(
        b_x + 2.5, b2_y + b2_h - b_head_h / 2.0, spec['branch_no']['title'],
        container=b2_head, name="branch_no_title", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=6.6, color='#111111', ha='left', va='center'
    )
    for li, bl in enumerate(spec['branch_no']['lines']):
        auditor.add_text(
            b_x + 2.5, b2_y + b2_h - b_head_h - 4.2 - li * 5.2, bl,
            container=b2_body, name=f"branch_no_line{li+1}",
            fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='left', va='center'
        )

    # Connector 1: Diamond Right Tip (68.5, 27.5) -> (94.0, 27.5) -> (94.0, 68.0) -> (104.0, 68.0)
    yes_xs = [d_cx + d_hw, 94.0, 94.0, b_x]
    yes_ys = [d_cy, d_cy, b1_y + b1_h / 2.0, b1_y + b1_h / 2.0]
    ax.plot(yes_xs, yes_ys, color='#333333', linewidth=1.1, linestyle='--')
    auditor.register_connector_path(yes_xs, yes_ys, "diamond_to_yes")
    ax.annotate(
        '', xy=(b_x, b1_y + b1_h / 2.0), xytext=(b_x - 1.5, b1_y + b1_h / 2.0),
        arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6)
    )
    # Place "CÓ (Bác bỏ)" cleanly inside corridor (68.5, 27.5, 94.0, 39.0)
    auditor.add_text(
        81.2, 31.8, spec['branch_yes']['edge_label'],
        container=(d_cx + d_hw, d_cy, 94.0, 39.0),
        name="yes_edge_label", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=6.2, color='#111111', ha='center', va='center'
    )

    # Connector 2: Feedback Loop from top of NHÁNH CÓ (134.0, 81.0) -> (134.0, 95.5) -> (84.0, 95.5)
    loop_xs = [b_x + b_w / 2.0, b_x + b_w / 2.0, s_x + s_w]
    loop_ys = [b1_y + b1_h, 95.5, 95.5]
    ax.plot(loop_xs, loop_ys, color='#444444', linewidth=1.0, linestyle=':')
    auditor.register_connector_path(loop_xs, loop_ys, "yes_to_step1_loop")
    ax.annotate(
        '', xy=(s_x + s_w, 95.5), xytext=(s_x + s_w + 1.5, 95.5),
        arrowprops=dict(arrowstyle="-|>", color='#444444', lw=1.0, mutation_scale=6)
    )
    auditor.add_text(
        0.5 * (s_x + s_w + b_x + b_w / 2.0), 99.8, spec['branch_yes']['loop_label'],
        container=(s_x + s_w, 95.5, b_x + b_w / 2.0, 104.5),
        name="loop_edge_label", v_center_in_container=True,
        fontproperties=FONT_REG, fontsize=6.2, color='#333333', ha='center', va='center'
    )

    # Connector 3: Diamond Bottom Tip (45.0, 18.5) -> (45.0, 17.2)?
    # Better: exit diamond bottom tip (45.0, 18.5) -> (45.0, 16.5) is too close to note_box (13.0).
    # Instead, route from diamond bottom tip (45.0, 18.5) straight right at y=18.5 into b2 left wall (b2_y=16.0..42.0)!
    no_xs = [d_cx, b_x]
    no_ys = [d_cy - d_hh, d_cy - d_hh]
    ax.plot(no_xs, no_ys, color='#333333', linewidth=1.1)
    auditor.register_connector_path(no_xs, no_ys, "diamond_to_no")
    ax.annotate(
        '', xy=(b_x, d_cy - d_hh), xytext=(b_x - 1.5, d_cy - d_hh),
        arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.1, mutation_scale=6)
    )
    auditor.add_text(
        81.2, 22.2, spec['branch_no']['edge_label'],
        container=(60.0, d_cy - d_hh, b_x, 26.5),
        name="no_edge_label", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=6.2, color='#111111', ha='center', va='center'
    )

    # Bottom Invariant Note (x: 4.0 to 164.0, y: 2.5 to 13.5, h=11.0)
    n_x, n_y, n_w, n_h = 4.0, 2.5, 160.0, 11.0
    ax.add_patch(patches.FancyBboxPatch(
        (n_x, n_y), n_w, n_h, boxstyle="round,pad=0,rounding_size=1.8",
        facecolor='#FAFAFA', edgecolor='#555555', linewidth=0.8
    ))
    auditor.register_box_borders(n_x, n_y, n_x + n_w, n_y + n_h, "note_box")
    note_cont = (n_x, n_y, n_x + n_w, n_y + n_h)
    auditor.add_text(
        84.0, n_y + 7.7, spec['conclusion_lines'][0],
        container=note_cont, name="fig3_note_1",
        fontproperties=FONT_BOLD, fontsize=6.2, color='#222222', ha='center', va='center'
    )
    auditor.add_text(
        84.0, n_y + 3.5, spec['conclusion_lines'][1],
        container=note_cont, name="fig3_note_2",
        fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='center', va='center'
    )

    report = auditor.verify()
    out_path = os.path.join(ASSETS_DIR, 'feedback-loop.png')
    if save:
        fig.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
        verify_image(out_path, geom_report=report)
    plt.close(fig)
    return report


def render_fig4(save=True):
    """
    Hình 4: Giải phẫu trực quan cấu trúc một tệp nguồn Go (go-source-anatomy.png)
    """
    spec = FIG4_SPEC
    fig_w_mm = 168.0
    fig_h_mm = 114.0

    fig, ax = plt.subplots(figsize=(fig_w_mm / 25.4, fig_h_mm / 25.4), dpi=320)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
    ax.set_xlim(0.0, fig_w_mm)
    ax.set_ylim(0.0, fig_h_mm)
    ax.set_aspect('equal')
    ax.axis('off')

    auditor = FigureGeometryAuditor(fig, ax, fig_w_mm, fig_h_mm, "Fig4:go-source-anatomy")
    ax.add_patch(patches.Rectangle((0, 0), fig_w_mm, fig_h_mm, facecolor='#FFFFFF', edgecolor='none'))

    # Left Column: Code Window (x: 4.0 to 68.0, y: 5.0 to 109.0, h=104.0)
    c_x, c_y, c_w, c_h, c_head_h = 4.0, 5.0, 64.0, 104.0, 8.0
    code_head, code_body = _draw_titled_card(
        ax, auditor, c_x, c_y, c_w, c_h, c_head_h,
        face_body='#F9F9F9', face_head='#EEEEEE', edge_col='#444444',
        lw=1.0, rounding=2.5, card_name="code_window"
    )
    for cx in [7.5, 10.3, 13.1]:
        ax.add_patch(patches.Circle((cx, c_y + c_h - c_head_h / 2.0), 1.0, facecolor='#888888', edgecolor='none'))

    auditor.add_text(
        c_x + 36.0, c_y + c_h - c_head_h / 2.0, spec['window_title'],
        container=(c_x + 15.0, c_y + c_h - c_head_h, c_x + c_w, c_y + c_h),
        name="code_window_title", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=8.0, color='#222222', ha='center', va='center'
    )

    y_top_code = 95.2
    line_h = 4.75
    bands = [
        (0, 0, '#E8E8E8'),
        (2, 2, '#EDEDED'),
        (4, 11, '#EAEAEA'),
        (13, 17, '#EDEDED'),
    ]
    for s_idx, e_idx, col in bands:
        y_b = y_top_code - (e_idx + 0.5) * line_h + 0.5
        h_b = (e_idx - s_idx + 1) * line_h - 0.4
        ax.add_patch(patches.Rectangle(
            (c_x + 1.8, y_b), c_w - 3.6, h_b,
            facecolor=col, edgecolor='#CCCCCC', linewidth=0.5, linestyle=':', alpha=0.55
        ))

    for line_idx, (indent_lvl, text) in enumerate(spec['code_items']):
        if not text:
            continue
        y_pos = y_top_code - line_idx * line_h
        x_pos = c_x + 3.5 + indent_lvl * 4.8
        auditor.add_text(
            x_pos, y_pos, text,
            container=code_body, name=f"code_line_{line_idx+1}",
            fontproperties=FONT_MONO, fontsize=7.4, color='#111111', ha='left', va='center'
        )

    # Right Column: 5 Semantic Zone Cards (x: 78.0 to 164.0, width: 86.0)
    card_x = 78.0
    card_w = 86.0
    card_head_h = 6.5
    card_geoms = [
        (89.8, 19.2),  # Card 1: 89.8 to 109.0
        (68.6, 19.2),  # Card 2: 68.6 to 87.8
        (47.4, 19.2),  # Card 3: 47.4 to 66.6
        (26.2, 19.2),  # Card 4: 26.2 to 45.4
        (5.0, 19.2),   # Card 5: 5.0 to 24.2
    ]

    for idx, c in enumerate(spec['cards']):
        y_b, h_b = card_geoms[idx]
        cname = f"anatomy_card_{idx+1}"
        head_cont, body_cont = _draw_titled_card(
            ax, auditor, card_x, y_b, card_w, h_b, card_head_h,
            face_body='#FBFBFB', face_head='#EBEBEB', edge_col='#555555',
            lw=0.9, rounding=2.2, card_name=cname
        )
        auditor.add_text(
            card_x + 2.8, y_b + h_b - card_head_h / 2.0, c['title'],
            container=head_cont, name=f"{cname}_title", v_center_in_container=True,
            fontproperties=FONT_BOLD, fontsize=7.0, color='#111111', ha='left', va='center'
        )
        y_body_top = y_b + h_b - card_head_h
        for li, line_text in enumerate(c['lines']):
            auditor.add_text(
                card_x + 2.8, y_body_top - 4.1 - li * 4.5, line_text,
                container=body_cont, name=f"{cname}_line{li+1}",
                fontproperties=FONT_REG, fontsize=6.4, color='#222222', ha='left', va='center'
            )

        code_anchor_x = c_x + c_w
        code_anchor_y = y_top_code - c['anchor_line_idx'] * line_h
        card_anchor_y = y_b + (h_b - card_head_h) / 2.0
        elbow_x = 73.0

        ax.plot([code_anchor_x, elbow_x, card_x], [code_anchor_y, card_anchor_y, card_anchor_y],
                color='#444444', linewidth=1.0)
        auditor.register_connector_path(
            [code_anchor_x, elbow_x, card_x], [code_anchor_y, card_anchor_y, card_anchor_y],
            f"{cname}_leader"
        )
        ax.add_patch(patches.Circle((code_anchor_x, code_anchor_y), 0.65, facecolor='#333333', edgecolor='none'))
        ax.annotate(
            '', xy=(card_x, card_anchor_y), xytext=(card_x - 1.5, card_anchor_y),
            arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.0, mutation_scale=6)
        )

    report = auditor.verify()
    out_path = os.path.join(ASSETS_DIR, 'go-source-anatomy.png')
    if save:
        fig.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
        verify_image(out_path, geom_report=report)
    plt.close(fig)
    return report


def render_fig5(custom_spec=None, save=True):
    """
    Hình 5: Mô hình các lớp xử lý của Go compiler (compiler-doc-go.png)
    - Aligned with go.dev/src/cmd/compile/README:
      Parsing (syntax) -> Type Checking (types2) -> IR & Walk (noder, ir, walk) -> SSA & Codegen (ssa, obj) -> Linker (cmd/link).
    - Eliminates "Zero warnings: mọi sai lệch là lỗi".
    - Clearly distinguishes compiler static errors, go vet diagnostics, and runtime/test failures.
    - Widens sub-boxes and enforces >= 4.0 pt padding inside all SSA and Linker sub-boxes.
    """
    spec = custom_spec if custom_spec else FIG5_SPEC
    fig_w_mm = 168.0
    fig_h_mm = 125.0

    fig, ax = plt.subplots(figsize=(fig_w_mm / 25.4, fig_h_mm / 25.4), dpi=320)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
    ax.set_xlim(0.0, fig_w_mm)
    ax.set_ylim(0.0, fig_h_mm)
    ax.set_aspect('equal')
    ax.axis('off')

    auditor = FigureGeometryAuditor(fig, ax, fig_w_mm, fig_h_mm, "Fig5:compiler-doc-go")
    ax.add_patch(patches.Rectangle((0, 0), fig_w_mm, fig_h_mm, facecolor='#FFFFFF', edgecolor='none'))

    # Title box (y: 111.0 to 122.5, h=11.5)
    t_x, t_y, t_w, t_h = 4.0, 111.0, 160.0, 11.5
    ax.add_patch(patches.FancyBboxPatch(
        (t_x, t_y), t_w, t_h, boxstyle="round,pad=0,rounding_size=2.0",
        facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.9
    ))
    auditor.register_box_borders(t_x, t_y, t_x + t_w, t_y + t_h, "title_box")
    t_cont = (t_x, t_y, t_x + t_w, t_y + t_h)
    auditor.add_text(
        84.0, t_y + 7.7, spec['title'],
        container=t_cont,
        name="fig5_title",
        fontproperties=FONT_BOLD, fontsize=8.5, color='#111111', ha='center', va='center'
    )
    auditor.add_text(
        84.0, t_y + 3.2, spec['subtitle'],
        container=t_cont,
        name="fig5_subtitle",
        fontproperties=FONT_REG, fontsize=6.3, color='#333333', ha='center', va='center'
    )

    main_x = 4.0
    main_w = 110.0   # 4.0 to 114.0
    side_x = 121.0
    side_w = 43.0    # 121.0 to 164.0
    lyr_h = 22.0
    tag_h = 6.2
    gap_y = 6.0
    layer_y_tops = [108.0, 108.0 - (lyr_h + gap_y), 108.0 - 2 * (lyr_h + gap_y), 108.0 - 3 * (lyr_h + gap_y)]

    for idx, lyr in enumerate(spec['layers']):
        y_top = layer_y_tops[idx]
        y_bot = y_top - lyr_h
        lname = f"layer_{lyr['id']}"

        head_cont, body_cont = _draw_titled_card(
            ax, auditor, main_x, y_bot, main_w, lyr_h, tag_h,
            face_body='#FBFBFB', face_head='#EBEBEB', edge_col='#444444',
            lw=0.9, rounding=2.0, card_name=lname
        )
        auditor.add_text(
            main_x + 2.8, y_top - tag_h / 2.0, lyr['tag'],
            container=head_cont, name=f"{lname}_tag", v_center_in_container=True,
            fontproperties=FONT_BOLD, fontsize=6.8, color='#111111', ha='left', va='center'
        )

        # Sub-boxes inside layer body (y_bot to y_top - tag_h, height = 15.8 mm)
        n_boxes = len(lyr['boxes'])
        inner_pad_x = 2.4
        sub_gap_x = 3.8
        sub_w = (main_w - 2 * inner_pad_x - (n_boxes - 1) * sub_gap_x) / float(n_boxes)
        sub_h = 13.4
        sub_y = y_bot + 1.2

        for bi, (btitle, bdescs) in enumerate(lyr['boxes']):
            bx = main_x + inner_pad_x + bi * (sub_w + sub_gap_x)
            sb_name = f"{lname}_sub{bi+1}"
            ax.add_patch(patches.FancyBboxPatch(
                (bx, sub_y), sub_w, sub_h,
                boxstyle="round,pad=0,rounding_size=1.4",
                facecolor='#EEEEEE', edgecolor='#666666', linewidth=0.75
            ))
            auditor.register_box_borders(bx, sub_y, bx + sub_w, sub_y + sub_h, sb_name, min_clearance_pt=MIN_SAFE_PADDING_PT)
            sb_cont = (bx, sub_y, bx + sub_w, sub_y + sub_h)

            auditor.add_text(
                bx + sub_w / 2.0, sub_y + sub_h - 3.05, btitle,
                container=sb_cont, name=f"{sb_name}_title",
                fontproperties=FONT_BOLD, fontsize=6.5, color='#111111', ha='center', va='center'
            )
            for di, desc_line in enumerate(bdescs):
                auditor.add_text(
                    bx + sub_w / 2.0, sub_y + sub_h - 6.75 - di * 3.55, desc_line,
                    container=sb_cont, name=f"{sb_name}_line{di+1}",
                    fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='center', va='center'
                )

            if bi < n_boxes - 1:
                arr_x0 = bx + sub_w + 0.4
                arr_x1 = bx + sub_w + sub_gap_x - 0.4
                arr_y = sub_y + sub_h / 2.0
                ax.plot([arr_x0, arr_x1], [arr_y, arr_y], color='#444444', linewidth=0.9)
                auditor.register_connector_path([arr_x0, arr_x1], [arr_y, arr_y], f"{sb_name}_arrow")
                ax.annotate(
                    '', xy=(arr_x1, arr_y), xytext=(arr_x1 - 1.0, arr_y),
                    arrowprops=dict(arrowstyle="-|>", color='#444444', lw=0.9, mutation_scale=5)
                )

        # Downward transition to next layer across the 6.0 mm inter-layer gap
        if idx < 3:
            next_top = layer_y_tops[idx + 1]
            cx = 42.0
            ax.plot([cx, cx], [y_bot, next_top], color='#222222', linewidth=1.1)
            auditor.register_connector_path([cx, cx], [y_bot, next_top], f"{lname}_down_arrow")
            ax.annotate(
                '', xy=(cx, next_top), xytext=(cx, next_top + 1.1),
                arrowprops=dict(arrowstyle="-|>", color='#222222', lw=1.1, mutation_scale=6)
            )
            gap_cont = (cx + 1.5, next_top, main_x + main_w, y_bot)
            auditor.add_text(
                cx + 3.2, 0.5 * (y_bot + next_top), f"→ {lyr['output']}",
                container=gap_cont, name=f"{lname}_output", v_center_in_container=True,
                fontproperties=FONT_MONO, fontsize=6.2, color='#222222', ha='left', va='center'
            )

        # Side Box (Error Gate or Compiler Scope Note)
        sname = f"side_{lyr['id']}"
        s_head_cont, s_body_cont = _draw_titled_card(
            ax, auditor, side_x, y_bot, side_w, lyr_h, tag_h,
            face_body='#F6F6F6' if lyr['has_rejection'] else '#FAFAFA',
            face_head='#E2E2E2' if lyr['has_rejection'] else '#ECECEC',
            edge_col='#444444' if lyr['has_rejection'] else '#666666',
            lw=0.9, ls='--' if lyr['has_rejection'] else '-',
            rounding=2.0, card_name=sname
        )
        auditor.add_text(
            side_x + side_w / 2.0, y_top - tag_h / 2.0, lyr['side_title'],
            container=s_head_cont, name=f"{sname}_title", v_center_in_container=True,
            fontproperties=FONT_BOLD, fontsize=6.4, color='#111111', ha='center', va='center'
        )
        y_sbody_top = y_top - tag_h
        for li, line_t in enumerate(lyr['side_lines']):
            auditor.add_text(
                side_x + 2.3, y_sbody_top - 3.6 - li * 4.2, line_t,
                container=s_body_cont, name=f"{sname}_line{li+1}",
                fontproperties=FONT_REG, fontsize=6.2,
                color='#111111' if lyr['has_rejection'] else '#333333', ha='left', va='center'
            )

        mid_y = y_bot + (lyr_h - tag_h) / 2.0
        ax.plot(
            [main_x + main_w, side_x], [mid_y, mid_y],
            color='#333333' if lyr['has_rejection'] else '#777777',
            linewidth=1.0 if lyr['has_rejection'] else 0.8,
            linestyle='--' if lyr['has_rejection'] else ':'
        )
        auditor.register_connector_path([main_x + main_w, side_x], [mid_y, mid_y], f"{lname}_to_side")
        ax.annotate(
            '', xy=(side_x, mid_y), xytext=(side_x - 1.4, mid_y),
            arrowprops=dict(
                arrowstyle="-|>",
                color='#333333' if lyr['has_rejection'] else '#777777',
                lw=1.0 if lyr['has_rejection'] else 0.8,
                mutation_scale=5
            )
        )

    report = auditor.verify()
    out_path = os.path.join(ASSETS_DIR, 'compiler-doc-go.png')
    if save:
        fig.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
        verify_image(out_path, geom_report=report)
    plt.close(fig)
    return report


def render_fig6(custom_s2_x=None, save=True):
    """
    Hình 6: Trực quan hóa ranh giới phạm vi từ vựng (go-scope-trace.png)
    - Eliminates leading whitespace in indented code lines; uses exact x coordinates
      so Scope 2's dashed border (x=11.0) wraps cleanly outside 'if status >= 500 {'
      and '}' (at x=13.5) with > 7 pt horizontal padding.
    """
    spec = FIG6_SPEC
    fig_w_mm = 168.0
    fig_h_mm = 121.0

    fig, ax = plt.subplots(figsize=(fig_w_mm / 25.4, fig_h_mm / 25.4), dpi=320)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
    ax.set_xlim(0.0, fig_w_mm)
    ax.set_ylim(0.0, fig_h_mm)
    ax.set_aspect('equal')
    ax.axis('off')

    auditor = FigureGeometryAuditor(fig, ax, fig_w_mm, fig_h_mm, "Fig6:go-scope-trace")
    ax.add_patch(patches.Rectangle((0, 0), fig_w_mm, fig_h_mm, facecolor='#FFFFFF', edgecolor='none'))

    # Title box (y: 107.0 to 118.5, h=11.5)
    t_x, t_y, t_w, t_h = 4.0, 107.0, 160.0, 11.5
    ax.add_patch(patches.FancyBboxPatch(
        (t_x, t_y), t_w, t_h, boxstyle="round,pad=0,rounding_size=2.0",
        facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.9
    ))
    auditor.register_box_borders(t_x, t_y, t_x + t_w, t_y + t_h, "title_box")
    t_cont = (t_x, t_y, t_x + t_w, t_y + t_h)
    auditor.add_text(
        84.0, t_y + 7.7, spec['title'],
        container=t_cont,
        name="fig6_title",
        fontproperties=FONT_BOLD, fontsize=8.5, color='#111111', ha='center', va='center'
    )
    auditor.add_text(
        84.0, t_y + 3.2, spec['subtitle'],
        container=t_cont,
        name="fig6_subtitle",
        fontproperties=FONT_REG, fontsize=6.4, color='#333333', ha='center', va='center'
    )

    # Left Column: Code Window (x: 4.0 to 86.0, y: 21.5 to 104.0, h=82.5)
    cw_x, cw_y, cw_w, cw_h, cw_head_h = 4.0, 21.5, 82.0, 82.5, 6.5
    cw_head, cw_body = _draw_titled_card(
        ax, auditor, cw_x, cw_y, cw_w, cw_h, cw_head_h,
        face_body='#FAFAFA', face_head='#EEEEEE', edge_col='#444444',
        lw=1.0, rounding=2.5, card_name="code_win"
    )
    for cx in [7.0, 9.8, 12.6]:
        ax.add_patch(patches.Circle((cx, cw_y + cw_h - cw_head_h / 2.0), 0.95, facecolor='#888888', edgecolor='none'))

    auditor.add_text(
        cw_x + 46.0, cw_y + cw_h - cw_head_h / 2.0, spec['window_title'],
        container=(cw_x + 14.5, cw_y + cw_h - cw_head_h, cw_x + cw_w, cw_y + cw_h),
        name="code_win_title", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=7.4, color='#222222', ha='center', va='center'
    )

    # Scope 1 (main) outer box: x=6.0 to 84.0, y=23.5 to 95.5 (w=78.0, h=72.0)
    s1_x, s1_y, s1_w, s1_h = 6.0, 23.5, 78.0, 72.0
    ax.add_patch(patches.FancyBboxPatch(
        (s1_x, s1_y), s1_w, s1_h, boxstyle="round,pad=0,rounding_size=2.0",
        facecolor='#F4F4F4', edgecolor='#666666', linewidth=0.85
    ))
    auditor.register_box_borders(s1_x, s1_y, s1_x + s1_w, s1_y + s1_h, "scope1_box")
    s1_cont = (s1_x, s1_y, s1_x + s1_w, s1_y + s1_h)

    # Scope 1 badge: x=8.0 to 46.0, y=87.8 to 93.8 (w=38.0, h=6.0)
    b1_x, b1_y, b1_w, b1_h = 8.0, 87.8, 38.0, 6.0
    ax.add_patch(patches.FancyBboxPatch(
        (b1_x, b1_y), b1_w, b1_h, boxstyle="round,pad=0,rounding_size=1.2",
        facecolor='#E0E0E0', edgecolor='#555555', linewidth=0.65
    ))
    auditor.register_box_borders(b1_x, b1_y, b1_x + b1_w, b1_y + b1_h, "scope1_badge")
    auditor.add_text(
        b1_x + b1_w / 2.0, b1_y + b1_h / 2.0, spec['scope1_label'],
        container=(b1_x, b1_y, b1_x + b1_w, b1_y + b1_h),
        name="scope1_badge_text", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=6.3, color='#111111', ha='center', va='center'
    )

    # Scope 2 (if block) inner dashed box: x=11.0 to 82.0, y=46.0 to 75.5 (w=71.0, h=29.5)
    s2_x = float(custom_s2_x) if custom_s2_x is not None else 11.0
    s2_y, s2_w, s2_h = 46.0, 82.0 - s2_x, 29.5
    ax.add_patch(patches.FancyBboxPatch(
        (s2_x, s2_y), s2_w, s2_h, boxstyle="round,pad=0,rounding_size=2.0",
        facecolor='#E8E8E8', edgecolor='#333333', linewidth=0.95, linestyle='--'
    ))
    auditor.register_box_borders(s2_x, s2_y, s2_x + s2_w, s2_y + s2_h, "scope2_box")
    s2_cont = (s2_x, s2_y, s2_x + s2_w, s2_y + s2_h)

    # Scope 2 badge: x=13.5 to 49.5, y=67.9 to 73.9 (w=36.0, h=6.0)
    b2_x, b2_y, b2_w, b2_h = 13.5, 67.9, 36.0, 6.0
    ax.add_patch(patches.FancyBboxPatch(
        (b2_x, b2_y), b2_w, b2_h, boxstyle="round,pad=0,rounding_size=1.2",
        facecolor='#D5D5D5', edgecolor='#444444', linewidth=0.65
    ))
    auditor.register_box_borders(b2_x, b2_y, b2_x + b2_w, b2_y + b2_h, "scope2_badge")
    auditor.add_text(
        b2_x + b2_w / 2.0, b2_y + b2_h / 2.0, spec['scope2_label'],
        container=(b2_x, b2_y, b2_x + b2_w, b2_y + b2_h),
        name="scope2_badge_text", v_center_in_container=True,
        fontproperties=FONT_BOLD, fontsize=6.2, color='#111111', ha='center', va='center'
    )

    # Error highlight box outside Scope 2: x=11.0 to 82.0, y=31.0 to 44.0 (w=71.0, h=13.0)
    err_x, err_y, err_w, err_h = 11.0, 31.0, 71.0, 13.0
    ax.add_patch(patches.FancyBboxPatch(
        (err_x, err_y), err_w, err_h, boxstyle="round,pad=0,rounding_size=1.5",
        facecolor='#EEEEEE', edgecolor='#444444', linewidth=0.8, linestyle=':'
    ))
    auditor.register_box_borders(err_x, err_y, err_x + err_w, err_y + err_h, "error_box")
    err_cont = (err_x, err_y, err_x + err_w, err_y + err_h)

    # Code lines placed with explicit x coordinates (NO leading whitespace!)
    code_lines_spec = [
        (8.5, 83.8, 'func main() {', '#111111', s1_cont, 'code_main_open'),
        (13.5, 79.0, 'status := 503', '#111111', s1_cont, 'code_status'),
        (13.5, 64.2, 'if status >= 500 {', '#111111', s2_cont, 'code_if_open'),
        (18.5, 59.3, 'label := "failed"', '#111111', s2_cont, 'code_label_decl'),
        (18.5, 54.4, 'fmt.Println("Bên trong if:", label)', '#222222', s2_cont, 'code_println_in'),
        (13.5, 49.5, '}', '#111111', s2_cont, 'code_if_close'),
        (13.5, 40.2, 'fmt.Println(label)', '#222222', err_cont, 'code_println_err'),
        (8.5, 26.8, '}', '#111111', s1_cont, 'code_main_close'),
    ]
    for cx_pos, cy_pos, ctext, ccol, ccont, cname in code_lines_spec:
        auditor.add_text(
            cx_pos, cy_pos, ctext,
            container=ccont, name=cname,
            fontproperties=FONT_MONO, fontsize=7.0, color=ccol, ha='left', va='center'
        )

    auditor.add_text(
        13.5, 34.4, spec['error_note'],
        container=err_cont, name="code_error_caption",
        fontproperties=FONT_BOLD, fontsize=6.3, color='#333333', ha='left', va='center'
    )

    # Right Column: 3 Lookup Trace Cards (x: 92.0 to 164.0, width: 72.0)
    card_x = 92.0
    card_w = 72.0
    card_head_h = 6.2
    card_geoms = [
        (78.3, 25.7, 64.2),  # Card 1: 78.3 to 104.0
        (49.9, 25.7, 54.4),  # Card 2: 49.9 to 75.6
        (21.5, 25.7, 37.5),  # Card 3: 21.5 to 47.2
    ]

    for idx, c in enumerate(spec['cards']):
        y_bot, h, code_pt_y = card_geoms[idx]
        y_top = y_bot + h
        cname = f"scope_card_{idx+1}"
        head_cont, body_cont = _draw_titled_card(
            ax, auditor, card_x, y_bot, card_w, h, card_head_h,
            face_body='#FAFAFA',
            face_head='#E4E4E4' if not c['pass'] else '#EAEAEA',
            edge_col='#444444' if not c['pass'] else '#666666',
            lw=0.9, ls='--' if not c['pass'] else '-',
            rounding=2.0, card_name=cname
        )
        auditor.add_text(
            card_x + 2.5, y_top - card_head_h / 2.0, c['title'],
            container=head_cont, name=f"{cname}_title", v_center_in_container=True,
            fontproperties=FONT_BOLD, fontsize=6.6, color='#111111', ha='left', va='center'
        )
        y_body_top = y_top - card_head_h
        auditor.add_text(
            card_x + 2.5, y_body_top - 3.3, c['status'],
            container=body_cont, name=f"{cname}_status",
            fontproperties=FONT_BOLD, fontsize=6.2, color='#222222', ha='left', va='center'
        )
        for li, line_t in enumerate(c['lines']):
            auditor.add_text(
                card_x + 2.5, y_body_top - 7.4 - li * 4.3, line_t,
                container=body_cont, name=f"{cname}_line{li+1}",
                fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='left', va='center'
            )

        c_mid_y = y_bot + (h - card_head_h) / 2.0
        ax.plot(
            [86.0, 89.0, card_x], [code_pt_y, c_mid_y, c_mid_y],
            color='#444444' if not c['pass'] else '#666666',
            linewidth=0.9, linestyle='--' if not c['pass'] else '-'
        )
        auditor.register_connector_path([86.0, 89.0, card_x], [code_pt_y, c_mid_y, c_mid_y], f"{cname}_pointer")
        ax.add_patch(patches.Circle((86.0, code_pt_y), 0.65, facecolor='#333333', edgecolor='none'))
        ax.annotate(
            '', xy=(card_x, c_mid_y), xytext=(card_x - 1.5, c_mid_y),
            arrowprops=dict(arrowstyle="-|>", color='#333333', lw=0.9, mutation_scale=6)
        )

    # Bottom Invariant Note: Lexical Scope vs Storage Lifetime (y: 2.1 to 18.9, h=16.8)
    nb_x, nb_y, nb_w, nb_h = 4.0, 2.1, 160.0, 16.8
    ax.add_patch(patches.FancyBboxPatch(
        (nb_x, nb_y), nb_w, nb_h, boxstyle="round,pad=0,rounding_size=2.0",
        facecolor='#F6F6F6', edgecolor='#555555', linewidth=0.85
    ))
    auditor.register_box_borders(nb_x, nb_y, nb_x + nb_w, nb_y + nb_h, "bottom_note_box")
    nb_cont = (nb_x, nb_y, nb_x + nb_w, nb_y + nb_h)

    auditor.add_text(
        nb_x + 3.0, nb_y + 13.5, spec['bottom_title'],
        container=nb_cont, name="bottom_note_title",
        fontproperties=FONT_BOLD, fontsize=7.0, color='#111111', ha='left', va='center'
    )
    for li, bline in enumerate(spec['bottom_lines']):
        auditor.add_text(
            nb_x + 3.0, nb_y + 9.6 - li * 3.3, bline,
            container=nb_cont, name=f"bottom_note_line{li+1}",
            fontproperties=FONT_REG, fontsize=6.2, color='#222222', ha='left', va='center'
        )

    report = auditor.verify()
    out_path = os.path.join(ASSETS_DIR, 'go-scope-trace.png')
    if save:
        fig.savefig(out_path, dpi=320, facecolor='#FFFFFF', edgecolor='none')
        verify_image(out_path, geom_report=report)
    plt.close(fig)
    return report


# ==============================================================================
# AUTHORITATIVE PLANTUML SYNCHRONIZATION
# ==============================================================================

PUML_HEADER = (
    "@startuml\n"
    "' AUTHORITATIVE SOURCE OF TRUTH: scripts/render_figures_1_6.py\n"
    "' Auto-synchronized from the canonical specification in scripts/render_figures_1_6.py.\n"
    "skinparam backgroundColor white\n"
    "skinparam shadowing false\n"
    "skinparam defaultFontName \"Source Sans 3\"\n"
    "skinparam defaultFontSize 13\n"
    "skinparam defaultFontColor #000000\n\n"
)


def build_expected_puml_contents():
    """
    Generate the exact PlantUML (.puml) companion sources directly from
    FIG1_SPEC .. FIG6_SPEC so there is never semantic drift between .puml and PNG.
    """
    pumls = {}

    # 1. go-history-timeline.puml
    lines1 = [PUML_HEADER.rstrip(), f"title {FIG1_SPEC['title']}\n"]
    for item in FIG1_SPEC['row1'] + FIG1_SPEC['row2']:
        lines1.append(
            f"rectangle \"{item['year']}: {item['title']} ({item['tag']})\\n---\\n{item['desc']}\" as y{item['year']}"
        )
    lines1.append("")
    for i in range(3):
        lines1.append(f"y{FIG1_SPEC['row1'][i]['year']} -right-> y{FIG1_SPEC['row1'][i+1]['year']}")
    lines1.append(f"y2012 --> y2015 : {FIG1_SPEC['bus_label']}")
    for i in range(3):
        lines1.append(f"y{FIG1_SPEC['row2'][i]['year']} -right-> y{FIG1_SPEC['row2'][i+1]['year']}")
    lines1.append("@enduml\n")
    pumls['go-history-timeline.puml'] = "\n".join(lines1)

    # 2. go-idea-lineage.puml
    lines2 = [PUML_HEADER.rstrip(), f"title {FIG2_SPEC['title']}\n"]
    for p in FIG2_SPEC['pillars']:
        joined_items = "\\n".join(p['items'])
        lines2.append(f"rectangle \"{p['name']}\\n---\\n{joined_items}\" as {p['id']}")
    sec_strs = []
    for stitle, slines in FIG2_SPEC['go_sections']:
        sec_strs.append(stitle + "\\n" + "\\n".join(slines))
    go_body_str = "\\n---\\n".join(sec_strs)
    lines2.append(f"rectangle \"{FIG2_SPEC['go_title']}\\n---\\n{go_body_str}\" as Go_Lang\n")
    for p in FIG2_SPEC['pillars']:
        lbl = " ".join(p['conn_lines'])
        lines2.append(f"{p['id']} -right-> Go_Lang : {lbl}")
    lines2.append("@enduml\n")
    pumls['go-idea-lineage.puml'] = "\n".join(lines2)

    # 3. feedback-loop.puml
    lines3 = [PUML_HEADER.rstrip(), f"title {FIG3_SPEC['title']}\n", "start", "repeat"]
    for s in FIG3_SPEC['steps']:
        if 'lines' in s:
            body = "\\n".join(s['lines'])
        else:
            body = s['desc']
        lines3.append(f"  :{s['num']}: {s['title']}\\n{body};")
    d_q = " ".join(FIG3_SPEC['diamond_lines'])
    by = FIG3_SPEC['branch_yes']
    bn = FIG3_SPEC['branch_no']
    lines3.append(f"  if ({d_q}) then ({by['edge_label']})")
    lines3.append(f"    :{by['title']}\\n" + "\\n".join(by['lines']) + ";")
    lines3.append(f"  else ({bn['edge_label']})")
    lines3.append(f"    :{bn['title']}\\n" + "\\n".join(bn['lines']) + ";")
    lines3.append("    stop")
    lines3.append("  endif")
    lines3.append(f"repeat while ({by['loop_label']})")
    lines3.append("@enduml\n")
    pumls['feedback-loop.puml'] = "\n".join(lines3)

    # 4. go-source-anatomy.puml
    lines4 = [PUML_HEADER.rstrip(), "title GIẢI PHẪU TRỰC QUAN CẤU TRÚC MỘT TỆP NGUỒN GO (main.go)\n", "left to right direction\n"]
    code_escaped = "\\n".join(
        ("    " * indent + txt).replace('"', '\\"') for indent, txt in FIG4_SPEC['code_items']
    )
    lines4.append(f"rectangle \"{FIG4_SPEC['window_title']}\\n---\\n{code_escaped}\" as code\n")
    for idx, c in enumerate(FIG4_SPEC['cards'], start=1):
        c_body = "\\n".join(l.replace('"', "'") for l in c['lines'])
        c_title = c['title'].replace('"', "'")
        lines4.append(f"rectangle \"{c_title}\\n---\\n{c_body}\" as zone{idx}")
    lines4.append("")
    for idx in range(1, len(FIG4_SPEC['cards']) + 1):
        lines4.append(f"code --> zone{idx} : Khối cú pháp {idx}")
    lines4.append("@enduml\n")
    pumls['go-source-anatomy.puml'] = "\n".join(lines4)

    # 5. compiler-doc-go.puml
    lines5 = [PUML_HEADER.rstrip(), f"title {FIG5_SPEC['title']}\n", "top to bottom direction\n"]
    for lyr in FIG5_SPEC['layers']:
        lid = lyr['id']
        b_strs = [f"• {bt}: " + ", ".join(bd) for bt, bd in lyr['boxes']]
        lines5.append(f"rectangle \"{lyr['tag']}\\n---\\n" + "\\n".join(b_strs) + f"\" as layer{lid}")
        s_strs = "\\n".join(lyr['side_lines'])
        lines5.append(f"rectangle \"{lyr['side_title']}\\n---\\n{s_strs}\" as side{lid}")
    lines5.append("")
    for lyr in FIG5_SPEC['layers']:
        lid = lyr['id']
        lines5.append(f"layer{lid} .right.> side{lid}")
        if lid < 4:
            lines5.append(f"layer{lid} --> layer{lid+1} : {lyr['output']}")
    lines5.append("@enduml\n")
    pumls['compiler-doc-go.puml'] = "\n".join(lines5)

    # 6. go-scope-trace.puml
    lines6 = [
        PUML_HEADER.rstrip(),
        f"title {FIG6_SPEC['title']}\n",
        f"package \"{FIG6_SPEC['scope1_label']}\" {{",
        "  rectangle \"status := 503\\n[Khả kiến trong toàn bộ main]\" as status_var",
        f"  package \"{FIG6_SPEC['scope2_label']}\" {{",
        "    rectangle \"label := \\\"failed\\\"\\n[Chỉ khả kiến bên trong if]\" as label_var",
        "    rectangle \"fmt.Println(label)\\n[PASS: Phân giải label thành công]\" as pass_label",
        "  }",
        f"  rectangle \"fmt.Println(label) (Ngoài khối if)\\n[{FIG6_SPEC['error_note']}]\" as fail_label",
        "}",
        "label_var ..> pass_label : Tham chiếu hợp lệ (nội bộ khối)",
        "status_var ..> label_var : Tham chiếu hợp lệ (từ con ra cha)",
        "fail_label ..> label_var : Vi phạm ranh giới từ vựng (chặn bởi '}')",
        "@enduml\n",
    ]
    pumls['go-scope-trace.puml'] = "\n".join(lines6)

    return pumls


def sync_puml_sources(check_only=False):
    """
    Synchronize or verify the 6 companion .puml files in assets/diagrams/ against
    the authoritative specifications in this module.
    """
    expected = build_expected_puml_contents()
    drifted = []
    for fname, content in expected.items():
        fpath = os.path.join(ASSETS_DIR, fname)
        current = ""
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                current = f.read()
        if current.replace('\r\n', '\n') != content.replace('\r\n', '\n'):
            drifted.append(fname)
            if not check_only:
                with open(fpath, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(content)
    if check_only and drifted:
        raise AssertionError(
            f"PUML DRIFT DETECTED from authoritative renderer scripts/render_figures_1_6.py: {drifted}"
        )
    return drifted


def main():
    print("=== Rendering Figures 1 to 6 (Final Visual Collision Repair & Geometric Audit) ===")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    sync_puml_sources(check_only=False)
    r1 = render_fig1()
    r2 = render_fig2()
    r3 = render_fig3()
    r4 = render_fig4()
    r5 = render_fig5()
    r6 = render_fig6()
    print("=== All 6 figures rendered, geometrically audited, and PUML-synchronized! ===")
    return [r1, r2, r3, r4, r5, r6]


if __name__ == '__main__':
    main()
