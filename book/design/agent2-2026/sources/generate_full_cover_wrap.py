# -*- coding: utf-8 -*-
"""generate_full_cover_wrap.py
Generates the complete, print-ready full cover wrap (Bìa sau + Gáy sách + Bìa trước)
and the standalone Front Cover page for the book GOLANG based on Concept 1:
Architectural Cross-Section & Spatial Cut (Manual of Section / Princeton Arch Press).

Specifications:
- Format: ISO A4 Trim Size (210 x 297 mm per page)
- Spine Width: 28.0 mm (calculated for 602 pages / 301 leaves on 70 gsm bookpaper: 301 x 0.090 mm + 1.0 mm PUR binding ≈ 28.0 mm).
  * Prepress Calibration Note: If printed on 80 gsm woodfree paper (caliper 0.098 mm), spine expands to ~30.5 mm and must be re-calibrated by the print shop.
- Bleed: 3.0 mm on all 4 outer edges
- Total Wrap Width: 3 + 210 + 28 + 210 + 3 = 454.0 mm (1286.93 pt)
- Total Wrap Height: 3 + 297 + 3 = 303.0 mm (858.90 pt)
- Front Cover Page: 210 x 297 mm (595.28 x 841.89 pt)
- Outputs: Vector PDF, 300 DPI PNG, Vector SVG
"""
import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = Path("D:/Golang/book/design/agent2-2026/artwork")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Conversion
MM_TO_PT = 72.0 / 25.4  # ~2.83464567 pt per mm

# Physical Dimensions (in mm)
BLEED_MM = 3.0
PAGE_W_MM = 210.0
PAGE_H_MM = 297.0
SPINE_W_MM = 28.0

WRAP_W_MM = BLEED_MM + PAGE_W_MM + SPINE_W_MM + PAGE_W_MM + BLEED_MM  # 454.0 mm
WRAP_H_MM = BLEED_MM + PAGE_H_MM + BLEED_MM                          # 303.0 mm

# Dimensions in points
WRAP_W_PT = WRAP_W_MM * MM_TO_PT  # ~1286.93 pt
WRAP_H_PT = WRAP_H_MM * MM_TO_PT  # ~858.90 pt

# Coordinate boundaries (in pt from left)
BLEED_PT = BLEED_MM * MM_TO_PT
BACK_LEFT_PT = BLEED_PT
BACK_RIGHT_PT = BACK_LEFT_PT + PAGE_W_MM * MM_TO_PT
SPINE_LEFT_PT = BACK_RIGHT_PT
SPINE_RIGHT_PT = SPINE_LEFT_PT + SPINE_W_MM * MM_TO_PT
FRONT_LEFT_PT = SPINE_RIGHT_PT
FRONT_RIGHT_PT = FRONT_LEFT_PT + PAGE_W_MM * MM_TO_PT

BOTTOM_TRIM_PT = BLEED_PT
TOP_TRIM_PT = BOTTOM_TRIM_PT + PAGE_H_MM * MM_TO_PT


# ==============================================================================
# Helper: Draw Concept 1 Architectural Cross-Section Engine
# ==============================================================================
def draw_axonometric_cross_section(ax, cx, cy, scale=1.04):
    """Draws an expanded, balanced 4-tier isometric axonometric cross-section of the Go engine."""
    cos30 = math.cos(math.radians(28))
    sin30 = math.sin(math.radians(28))

    def iso_proj(x, y, z):
        px = cx + (x - y) * cos30 * 1.05 * scale
        py = cy + (x + y) * sin30 * 0.65 * scale + z * 1.15 * scale
        return px, py

    tiers = [
        (-135, "TIER 0 // KERNEL & HARDWARE", "Syscall • Epoll • Cgroups v2", True),
        (-45,  "TIER 1 // GO RUNTIME CORE", "M:N Scheduler • Tri-Color GC", False),
        (50,   "TIER 2 // SERVICE BOUNDARIES", "gRPC Wire • HTTP/2 • ACID Locks", False),
        (145,  "TIER 3 // DISTRIBUTED SRE", "Kubernetes Controller • eBPF Mesh", False),
    ]

    slab_dx = 126
    slab_dy = 75
    thickness = 13

    # 1. Broad Background Architectural Projection Grid (Blueprint Lines)
    grid_c = "#EEEEEE"
    for gx in [-180, -120, -60, 0, 60, 120, 180]:
        p_a = iso_proj(gx, -110, -155)
        p_b = iso_proj(gx, 110, -155)
        ax.plot([p_a[0], p_b[0]], [p_a[1], p_b[1]], color=grid_c, lw=0.45, ls=(0, (3, 3)), zorder=1)
    for gy in [-110, -55, 0, 55, 110]:
        p_a = iso_proj(-180, gy, -155)
        p_b = iso_proj(180, gy, -155)
        ax.plot([p_a[0], p_b[0]], [p_a[1], p_b[1]], color=grid_c, lw=0.45, ls=(0, (3, 3)), zorder=1)

    # 2. Vertical Core Data Transmission Hairlines through all tiers
    pillars = [(-65, -30), (-65, 30), (0, -35), (0, 0), (0, 35), (65, -30), (65, 30)]
    for px_loc, py_loc in pillars:
        p_bot = iso_proj(px_loc, py_loc, -150)
        p_top = iso_proj(px_loc, py_loc, 160)
        ax.plot([p_bot[0], p_top[0]], [p_bot[1], p_top[1]],
                color="#666666", lw=0.42 * scale, ls=(0, (3, 4)), zorder=6)

    # 3. Draw Slabs
    for z_base, t_title, t_sub, is_foundation in tiers:
        p0 = iso_proj(-slab_dx, -slab_dy, z_base)
        p1 = iso_proj(slab_dx, -slab_dy, z_base)
        p2 = iso_proj(slab_dx, slab_dy, z_base)
        p3 = iso_proj(-slab_dx, slab_dy, z_base)

        face_color = "#E4E4E4" if is_foundation else "#FFFFFF"
        poly_top = patches.Polygon([p0, p1, p2, p3], closed=True,
                                   facecolor=face_color, edgecolor="#000000",
                                   lw=0.85 * scale, zorder=10 + int(z_base))
        ax.add_patch(poly_top)

        # Front cut poché (thickness)
        q0 = iso_proj(-slab_dx, -slab_dy, z_base - thickness)
        q1 = iso_proj(slab_dx, -slab_dy, z_base - thickness)
        poly_front = patches.Polygon([p0, p1, q1, q0], closed=True,
                                     facecolor="#1A1A1A", edgecolor="#000000",
                                     lw=0.65 * scale, zorder=11 + int(z_base))
        ax.add_patch(poly_front)

        # Right cut poché
        q2 = iso_proj(slab_dx, slab_dy, z_base - thickness)
        poly_side = patches.Polygon([p1, p2, q2, q1], closed=True,
                                    facecolor="#444444", edgecolor="#000000",
                                    lw=0.65 * scale, zorder=11 + int(z_base))
        ax.add_patch(poly_side)

        # Internal Features
        if is_foundation:
            # Tier 0: 4 Sockets
            for k in range(4):
                kx = -90 + k * 48
                ky = -22
                v0 = iso_proj(kx, ky, z_base)
                v1 = iso_proj(kx + 26, ky, z_base)
                v2 = iso_proj(kx + 26, ky + 40, z_base)
                v3 = iso_proj(kx, ky + 40, z_base)
                ax.add_patch(patches.Polygon([v0, v1, v2, v3], closed=True,
                                             facecolor="#111111", edgecolor="#000000",
                                             lw=0.5 * scale, zorder=12 + int(z_base)))
        elif z_base == -45:
            # Tier 1: 6 Go Scheduler P-M-G Queues
            for g in range(6):
                col = g % 3
                row = g // 3
                gx = -80 + col * 60
                gy = -28 + row * 38
                r0 = iso_proj(gx, gy, z_base)
                r1 = iso_proj(gx + 26, gy, z_base)
                r2 = iso_proj(gx + 26, gy + 22, z_base)
                r3 = iso_proj(gx, gy + 22, z_base)
                ax.add_patch(patches.Polygon([r0, r1, r2, r3], closed=True,
                                             facecolor="#F4F4F4", edgecolor="#111111",
                                             lw=0.55 * scale, zorder=12 + int(z_base)))
                ir0 = iso_proj(gx + 5, gy + 4, z_base)
                ir1 = iso_proj(gx + 21, gy + 4, z_base)
                ir2 = iso_proj(gx + 21, gy + 18, z_base)
                ir3 = iso_proj(gx + 5, gy + 18, z_base)
                ax.add_patch(patches.Polygon([ir0, ir1, ir2, ir3], closed=True,
                                             facecolor="#DDDDDD", edgecolor="#333333",
                                             lw=0.35 * scale, zorder=13 + int(z_base)))
        elif z_base == 50:
            # Tier 2: Service Wire Channels
            for c in range(3):
                cx_pipe = -60 + c * 52
                pt_a = iso_proj(cx_pipe, -50, z_base)
                pt_b = iso_proj(cx_pipe + 18, 50, z_base)
                ax.plot([pt_a[0], pt_b[0]], [pt_a[1], pt_b[1]],
                        color="#111111", lw=1.3 * scale, zorder=12 + int(z_base))
                mid_node = iso_proj(cx_pipe + 9, 0, z_base)
                ax.scatter([mid_node[0]], [mid_node[1]], s=8 * scale,
                           color="#000000", zorder=13 + int(z_base))
        elif z_base == 145:
            # Tier 3: Central SRE Tower
            c0 = iso_proj(-35, -35, z_base)
            c1 = iso_proj(35, -35, z_base)
            c2 = iso_proj(35, 35, z_base)
            c3 = iso_proj(-35, 35, z_base)
            ax.add_patch(patches.Polygon([c0, c1, c2, c3], closed=True,
                                         facecolor="#FFFFFF", edgecolor="#000000",
                                         lw=1.0 * scale, zorder=12 + int(z_base)))
            ic0 = iso_proj(-16, -16, z_base)
            ic1 = iso_proj(16, -16, z_base)
            ic2 = iso_proj(16, 16, z_base)
            ic3 = iso_proj(-16, 16, z_base)
            ax.add_patch(patches.Polygon([ic0, ic1, ic2, ic3], closed=True,
                                         facecolor="#1A1A1A", edgecolor="#000000",
                                         lw=0.6 * scale, zorder=13 + int(z_base)))

        # 4. Architectural Tier Leader Callouts (Left-Hand Side)
        p3_x, p3_y = p3
        lead_len = 16.0 * scale
        ax.plot([p3_x, p3_x - lead_len], [p3_y, p3_y],
                color="#000000", lw=0.6 * scale, zorder=20)
        ax.plot([p3_x - lead_len, p3_x - lead_len], [p3_y - 3.5 * scale, p3_y + 3.5 * scale],
                color="#000000", lw=0.8 * scale, zorder=20)
        ax.scatter([p3_x], [p3_y], s=7 * scale, color="#000000", zorder=21)

        ax.text(p3_x - lead_len - 4 * scale, p3_y + 4.0 * scale, t_title,
                fontsize=max(6.2, 6.4 * scale), fontfamily="sans-serif", weight="bold", color="#000000",
                ha="right", va="bottom", zorder=22)
        ax.text(p3_x - lead_len - 4 * scale, p3_y - 2.5 * scale, t_sub,
                fontsize=6.0, fontfamily="monospace", color="#333333",
                ha="right", va="top", zorder=22)

        # 5. Right-Hand Elevation Benchmarks
        p1_x, p1_y = p1
        r_lead_len = 10.0 * scale
        ax.plot([p1_x, p1_x + r_lead_len], [p1_y, p1_y],
                color="#888888", lw=0.5 * scale, ls=(0, (3, 3)), zorder=18)
        ax.plot([p1_x + r_lead_len, p1_x + r_lead_len], [p1_y - 3.0 * scale, p1_y + 3.0 * scale],
                color="#777777", lw=0.7 * scale, zorder=18)
        ax.scatter([p1_x], [p1_y], s=6 * scale, color="#555555", zorder=19)
        el_str = f"EL. {z_base:+04d} MM"
        ax.text(p1_x + r_lead_len + 3 * scale, p1_y, el_str,
                fontsize=6.0, fontfamily="monospace", color="#555555",
                ha="left", va="center", zorder=19)


# ==============================================================================
# 1. GENERATE FRONT COVER (BÌA 1) STANDALONE
# ==============================================================================
def generate_front_cover_page():
    """Generates the standalone Front Cover A4 page for the electronic PDF (Full Bleed, No Frame Box)."""
    fig, ax = plt.subplots(figsize=(PAGE_W_MM / 25.4, PAGE_H_MM / 25.4), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    w_pt = PAGE_W_MM * MM_TO_PT
    h_pt = PAGE_H_MM * MM_TO_PT
    ax.set_xlim(0, w_pt)
    ax.set_ylim(0, h_pt)
    ax.axis("off")

    left_m = 32.0
    right_m = w_pt - 32.0

    # 1. Top Technical Caliper Header Bar
    head_y = h_pt - 36.0
    ax.plot([left_m, right_m], [head_y, head_y], color="#000000", lw=0.7)
    for tick_x in [left_m, (left_m + right_m) / 2.0, right_m]:
        ax.plot([tick_x, tick_x], [head_y - 3.5, head_y + 3.5], color="#000000", lw=0.7)

    ax.text(left_m + 6, head_y + 5,
            "SYSTEMS ARCHITECTURE SPECIFICATION // FULL MONOCHROME SECTION",
            fontsize=6.5, fontfamily="monospace", weight="bold", color="#111111", va="bottom")
    ax.text(right_m - 6, head_y + 5,
            "DOC REF: PAP-SEC-2026 // ISO A4 EDITION",
            fontsize=6.5, fontfamily="monospace", color="#444444", ha="right", va="bottom")

    # 2. Main Title Block
    title_y = head_y - 36.0
    ax.text(w_pt / 2.0, title_y, "G  O  L  A  N  G",
            fontsize=46, fontfamily="sans-serif", weight="bold", color="#000000",
            ha="center", va="top")

    sub_y = title_y - 74.0
    ax.text(w_pt / 2.0, sub_y,
            "GIÁO TRÌNH CẬP NHẬT LIÊN TỤC VỀ KỸ NGHỆ PHẦN MỀM VÀ DEVOPS/SRE",
            fontsize=9.6, fontfamily="sans-serif", weight="bold", color="#111111",
            ha="center", va="top")

    auth_y = sub_y - 24.0
    ax.text(w_pt / 2.0, auth_y,
            "ĐOÀN NGỌC HOÀNG MINH",
            fontsize=9.2, fontfamily="sans-serif", color="#444444",
            ha="center", va="top")

    # Caliper dividing rule under author
    cal_y = auth_y - 18.0
    ax.plot([left_m + 15, right_m - 15], [cal_y, cal_y], color="#000000", lw=0.75)
    for cx_tick in [left_m + 15, w_pt / 2.0, right_m - 15]:
        ax.plot([cx_tick, cx_tick], [cal_y - 3, cal_y + 3], color="#000000", lw=0.75)

    # 3. Expanded Architectural Section Artwork (Fills page, no clipping)
    art_cx = 345.0
    art_cy = 385.0
    draw_axonometric_cross_section(ax, art_cx, art_cy, scale=1.04)

    # 4. Bottom Caliper Divider & 3-Column Metadata Specifications
    bot_y = 96.0
    ax.plot([left_m, right_m], [bot_y, bot_y], color="#000000", lw=0.7)
    for bx_tick in [left_m, left_m + 175, left_m + 355, right_m]:
        ax.plot([bx_tick, bx_tick], [bot_y - 3.5, bot_y + 3.5], color="#000000", lw=0.7)

    col1_x = left_m + 4
    col2_x = left_m + 180
    col3_x = left_m + 360

    # Column 1
    ax.text(col1_x, bot_y - 8, "SYSTEM RUNTIME SPECIFICATION",
            fontsize=6.2, fontfamily="sans-serif", weight="bold", color="#000000", va="top")
    ax.text(col1_x, bot_y - 22,
            "M:N Work-Stealing Go Scheduler\nTri-Color Concurrent Mark-Sweep GC\nChannel Rendezvous & Mutex Arena",
            fontsize=6.0, fontfamily="monospace", color="#333333", linespacing=1.35, va="top")

    # Column 2
    ax.text(col2_x, bot_y - 8, "DISTRIBUTED SRE INFRASTRUCTURE",
            fontsize=6.2, fontfamily="sans-serif", weight="bold", color="#000000", va="top")
    ax.text(col2_x, bot_y - 22,
            "Kubernetes Level-Triggered Reconcile\neBPF Kernel Tracing & Observability\nZero-Downtime Service Mesh Routing",
            fontsize=6.0, fontfamily="monospace", color="#333333", linespacing=1.35, va="top")

    # Column 3
    ax.text(col3_x, bot_y - 8, "PUBLICATION STANDARDS",
            fontsize=6.2, fontfamily="sans-serif", weight="bold", color="#000000", va="top")
    ax.text(col3_x, bot_y - 22,
            "Format: ISO A4 (210 x 297 mm)\nType: Source Serif 4 & JetBrains Mono\nPrint: High-Density Grayscale Monotone",
            fontsize=6.0, fontfamily="monospace", color="#333333", linespacing=1.35, va="top")

    # Sub-footer line
    sub_foot_y = 28.0
    ax.plot([left_m, right_m], [sub_foot_y, sub_foot_y], color="#999999", lw=0.4)
    ax.text(left_m, sub_foot_y - 5,
            "TECHNICAL MONOGRAPH SERIES // COMPUTING & ARCHITECTURE",
            fontsize=6.0, fontfamily="monospace", color="#666666", va="top")
    ax.text(right_m, sub_foot_y - 5,
            "BUILD: 2026-RELEASE",
            fontsize=6.0, fontfamily="monospace", color="#666666", ha="right", va="top")

    # Save
    out_pdf = OUTPUT_DIR / "front_cover_page.pdf"
    out_png = OUTPUT_DIR / "front_cover_page_300dpi.png"
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    fig.savefig(out_pdf, format="pdf", dpi=300)
    fig.savefig(out_png, format="png", dpi=300)
    plt.close(fig)
    print(f"[Cover] Front Cover saved:\n  - {out_pdf}\n  - {out_png}")


# ==============================================================================
# 2. GENERATE FULL COVER WRAP (BÌA SAU + GÁY + BÌA TRƯỚC) PRINT-READY
# ==============================================================================
def generate_full_cover_wrap():
    """Generates the full print-ready cover wrap with Back Cover, Spine, and Front Cover."""
    fig_w_in = WRAP_W_MM / 25.4
    fig_h_in = WRAP_H_MM / 25.4

    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    ax.set_xlim(0, WRAP_W_PT)
    ax.set_ylim(0, WRAP_H_PT)
    ax.axis("off")

    # Draw Crop / Fold Marks
    tick_len = 12.0  # pt
    def draw_crop_mark(x, y, dx, dy):
        ax.plot([x, x + dx], [y, y + dy], color="#000000", lw=0.4)

    # Corner Bleed marks
    for x_pos in [BACK_LEFT_PT, FRONT_RIGHT_PT]:
        draw_crop_mark(x_pos, 0, 0, tick_len)
        draw_crop_mark(x_pos, WRAP_H_PT, 0, -tick_len)
    for y_pos in [BOTTOM_TRIM_PT, TOP_TRIM_PT]:
        draw_crop_mark(0, y_pos, tick_len, 0)
        draw_crop_mark(WRAP_W_PT, y_pos, -tick_len, 0)

    # Spine Fold tick marks (top and bottom)
    for s_x in [SPINE_LEFT_PT, SPINE_RIGHT_PT]:
        draw_crop_mark(s_x, 0, 0, tick_len)
        draw_crop_mark(s_x, WRAP_H_PT, 0, -tick_len)

    # --------------------------------------------------------------------------
    # FRONT COVER (BÌA TRƯỚC - BÌA 1) - FULL BLEED, NO FRAME BOX
    # Range: x in [FRONT_LEFT_PT, FRONT_RIGHT_PT], y in [BOTTOM_TRIM_PT, TOP_TRIM_PT]
    # --------------------------------------------------------------------------
    f_w_pt = PAGE_W_MM * MM_TO_PT
    f_left_m = FRONT_LEFT_PT + 32.0
    f_right_m = FRONT_LEFT_PT + f_w_pt - 32.0

    # 1. Top Technical Caliper Header Bar
    f_head_y = TOP_TRIM_PT - 36.0
    ax.plot([f_left_m, f_right_m], [f_head_y, f_head_y], color="#000000", lw=0.7)
    for tick_x in [f_left_m, (f_left_m + f_right_m) / 2.0, f_right_m]:
        ax.plot([tick_x, tick_x], [f_head_y - 3.5, f_head_y + 3.5], color="#000000", lw=0.7)

    ax.text(f_left_m + 6, f_head_y + 5,
            "SYSTEMS ARCHITECTURE SPECIFICATION // FULL MONOCHROME SECTION",
            fontsize=6.5, fontfamily="monospace", weight="bold", color="#111111", va="bottom")
    ax.text(f_right_m - 6, f_head_y + 5,
            "DOC REF: PAP-SEC-2026 // ISO A4 EDITION",
            fontsize=6.5, fontfamily="monospace", color="#444444", ha="right", va="bottom")

    # 2. Main Title Block
    f_title_y = f_head_y - 36.0
    f_cx_center = FRONT_LEFT_PT + f_w_pt / 2.0
    ax.text(f_cx_center, f_title_y, "G  O  L  A  N  G",
            fontsize=46, fontfamily="sans-serif", weight="bold", color="#000000",
            ha="center", va="top")

    f_sub_y = f_title_y - 74.0
    ax.text(f_cx_center, f_sub_y,
            "GIÁO TRÌNH CẬP NHẬT LIÊN TỤC VỀ KỸ NGHỆ PHẦN MỀM VÀ DEVOPS/SRE",
            fontsize=9.6, fontfamily="sans-serif", weight="bold", color="#111111",
            ha="center", va="top")

    f_auth_y = f_sub_y - 24.0
    ax.text(f_cx_center, f_auth_y,
            "ĐOÀN NGỌC HOÀNG MINH",
            fontsize=9.2, fontfamily="sans-serif", color="#444444",
            ha="center", va="top")

    # Caliper dividing rule under author
    f_cal_y = f_auth_y - 18.0
    ax.plot([f_left_m + 15, f_right_m - 15], [f_cal_y, f_cal_y], color="#000000", lw=0.75)
    for cx_tick in [f_left_m + 15, f_cx_center, f_right_m - 15]:
        ax.plot([cx_tick, cx_tick], [f_cal_y - 3, f_cal_y + 3], color="#000000", lw=0.75)

    # 3. Expanded Architectural Section Artwork (Fills page, no clipping, clears spine fold)
    f_art_cx = FRONT_LEFT_PT + 355.0
    f_art_cy = BOTTOM_TRIM_PT + 385.0
    draw_axonometric_cross_section(ax, f_art_cx, f_art_cy, scale=1.04)

    # 4. Bottom Caliper Divider & 3-Column Metadata Specifications
    f_bot_y = BOTTOM_TRIM_PT + 96.0
    ax.plot([f_left_m, f_right_m], [f_bot_y, f_bot_y], color="#000000", lw=0.7)
    for bx_tick in [f_left_m, f_left_m + 175, f_left_m + 355, f_right_m]:
        ax.plot([bx_tick, bx_tick], [f_bot_y - 3.5, f_bot_y + 3.5], color="#000000", lw=0.7)

    f_col1_x = f_left_m + 4
    f_col2_x = f_left_m + 180
    f_col3_x = f_left_m + 360

    # Column 1
    ax.text(f_col1_x, f_bot_y - 8, "SYSTEM RUNTIME SPECIFICATION",
            fontsize=6.2, fontfamily="sans-serif", weight="bold", color="#000000", va="top")
    ax.text(f_col1_x, f_bot_y - 22,
            "M:N Work-Stealing Go Scheduler\nTri-Color Concurrent Mark-Sweep GC\nChannel Rendezvous & Mutex Arena",
            fontsize=6.0, fontfamily="monospace", color="#333333", linespacing=1.35, va="top")

    # Column 2
    ax.text(f_col2_x, f_bot_y - 8, "DISTRIBUTED SRE INFRASTRUCTURE",
            fontsize=6.2, fontfamily="sans-serif", weight="bold", color="#000000", va="top")
    ax.text(f_col2_x, f_bot_y - 22,
            "Kubernetes Level-Triggered Reconcile\neBPF Kernel Tracing & Observability\nZero-Downtime Service Mesh Routing",
            fontsize=6.0, fontfamily="monospace", color="#333333", linespacing=1.35, va="top")

    # Column 3
    ax.text(f_col3_x, f_bot_y - 8, "PUBLICATION STANDARDS",
            fontsize=6.2, fontfamily="sans-serif", weight="bold", color="#000000", va="top")
    ax.text(f_col3_x, f_bot_y - 22,
            "Format: ISO A4 (210 x 297 mm)\nType: Source Serif 4 & JetBrains Mono\nPrint: High-Density Grayscale Monotone",
            fontsize=6.0, fontfamily="monospace", color="#333333", linespacing=1.35, va="top")

    # Sub-footer line
    f_sub_foot_y = BOTTOM_TRIM_PT + 28.0
    ax.plot([f_left_m, f_right_m], [f_sub_foot_y, f_sub_foot_y], color="#999999", lw=0.4)
    ax.text(f_left_m, f_sub_foot_y - 5,
            "TECHNICAL MONOGRAPH SERIES // COMPUTING & ARCHITECTURE",
            fontsize=6.0, fontfamily="monospace", color="#666666", va="top")
    ax.text(f_right_m, f_sub_foot_y - 5,
            "BUILD: 2026-RELEASE",
            fontsize=6.0, fontfamily="monospace", color="#666666", ha="right", va="top")

    # --------------------------------------------------------------------------
    # SPINE (GÁY SÁCH)
    # Range: x in [SPINE_LEFT_PT, SPINE_RIGHT_PT], y in [BOTTOM_TRIM_PT, TOP_TRIM_PT]
    # --------------------------------------------------------------------------
    spine_cx = (SPINE_LEFT_PT + SPINE_RIGHT_PT) / 2.0

    # Vertical fold guideline (faint)
    ax.plot([SPINE_LEFT_PT, SPINE_LEFT_PT], [BOTTOM_TRIM_PT, TOP_TRIM_PT], color="#E0E0E0", lw=0.4, ls="--")
    ax.plot([SPINE_RIGHT_PT, SPINE_RIGHT_PT], [BOTTOM_TRIM_PT, TOP_TRIM_PT], color="#E0E0E0", lw=0.4, ls="--")

    # Spine Text (Rotated 270 degrees: reads top-to-bottom)
    # Top logo
    ax.text(spine_cx, TOP_TRIM_PT - 45, "[ AGY ]",
            fontsize=7.5, fontfamily="monospace", weight="bold", color="#000000",
            ha="center", va="center")

    # Title along spine
    ax.text(spine_cx, TOP_TRIM_PT - 160, "G  O  L  A  N  G",
            fontsize=18, fontfamily="sans-serif", weight="bold", color="#000000",
            ha="center", va="center", rotation=270)

    # Subtitle along spine
    ax.text(spine_cx, TOP_TRIM_PT - 450, "KỸ NGHỆ PHẦN MỀM & DEVOPS / SRE",
            fontsize=7.8, fontfamily="sans-serif", weight="bold", color="#333333",
            ha="center", va="center", rotation=270)

    # Author along spine
    ax.text(spine_cx, BOTTOM_TRIM_PT + 160, "ĐOÀN NGỌC HOÀNG MINH",
            fontsize=7.8, fontfamily="sans-serif", color="#555555",
            ha="center", va="center", rotation=270)

    # Edition tag at bottom of spine
    ax.text(spine_cx, BOTTOM_TRIM_PT + 45, "2026",
            fontsize=8.0, fontfamily="monospace", weight="bold", color="#000000",
            ha="center", va="center")

    # --------------------------------------------------------------------------
    # BACK COVER (BÌA SAU - BÌA 4)
    # Range: x in [BACK_LEFT_PT, BACK_RIGHT_PT], y in [BOTTOM_TRIM_PT, TOP_TRIM_PT]
    # --------------------------------------------------------------------------
    b_margin = 16.0 * MM_TO_PT
    b_x0 = BACK_LEFT_PT + b_margin
    b_y0 = BOTTOM_TRIM_PT + b_margin
    b_w = (PAGE_W_MM * MM_TO_PT) - 2 * b_margin
    b_h = (PAGE_H_MM * MM_TO_PT) - 2 * b_margin

    # Border
    ax.add_patch(patches.Rectangle((b_x0, b_y0), b_w, b_h, facecolor="none", edgecolor="#000000", lw=1.1))

    # Back Header Bar
    b_head_y = b_y0 + b_h - 20
    ax.plot([b_x0 + 10, b_x0 + b_w - 10], [b_head_y, b_head_y], color="#000000", lw=0.5)
    ax.text(b_x0 + 14, b_head_y + 4, "GOLANG LIVING TEXTBOOK // ARCHITECTURAL MONOGRAPH",
            fontsize=6.2, fontfamily="monospace", weight="bold", color="#333333", va="bottom")

    # Book Title on Back
    b_title_y = b_head_y - 25
    ax.text(b_x0 + 20, b_title_y, "G O L A N G", fontsize=22, fontfamily="sans-serif", weight="bold", color="#000000", va="top")
    
    b_sub_y = b_title_y - 42
    ax.text(b_x0 + 20, b_sub_y, "Giáo trình Cập nhật Liên tục về Kỹ nghệ Phần mềm và DevOps/SRE",
            fontsize=8.8, fontfamily="sans-serif", weight="bold", color="#333333", va="top")

    # Divider line
    b_div1_y = b_sub_y - 18
    ax.plot([b_x0 + 20, b_x0 + b_w - 20], [b_div1_y, b_div1_y], color="#CCCCCC", lw=0.5)

    # Blurb / Synopsis
    b_blurb_y = b_div1_y - 10
    blurb_text = (
        "Cuốn giáo trình cung cấp góc nhìn sâu sắc và thực chiến nhất về Kỹ nghệ Phần mềm hiện đại\n"
        "và vận hành hạ tầng quy mô lớn bằng ngôn ngữ Go. Không dừng lại ở cú pháp bề mặt, ấn phẩm\n"
        "dẫn lối kỹ sư đi sâu vào bản chất cơ học của Go Runtime, cách thức dữ liệu dịch chuyển trên\n"
        "ngăn xếp và heap của Linux, và phương pháp kiểm chứng tính đúng đắn của các hệ thống phân tán."
    )
    ax.text(b_x0 + 20, b_blurb_y, blurb_text, fontsize=7.4, fontfamily="serif", color="#111111", linespacing=1.45, va="top")

    # Divider line
    b_div2_y = b_blurb_y - 62
    ax.plot([b_x0 + 20, b_x0 + b_w - 20], [b_div2_y, b_div2_y], color="#000000", lw=0.6)

    # 4 Architectural Pillars (Callout Blocks) - Clean vertical separation
    pillars_start_y = b_div2_y - 12
    box_height = 72.0
    box_gap = 15.0

    pillars = [
        ("I. NỀN TẢNG CƠ HỌC & BỘ NHỚ",
         "Ngữ nghĩa giá trị (pass-by-value), cấu trúc slice header 24-byte, phân tích thoát heap\n"
         "(escape analysis) và kỹ thuật điều hòa GC pacer tối ưu hóa độ trễ tail-latency."),
        ("II. TƯƠNG TRANH & ĐỘ ỔN ĐỊNH HỆ THỐNG",
         "Mô hình CSP, cơ chế hẹn gặp rendezvous không bộ đệm, phát hiện data race trong thực tế,\n"
         "quản lý vòng đời với context.Context và chống rò rỉ goroutine."),
        ("III. DỊCH VỤ PHÂN TÁN & CƠ SỞ DỮ LIỆU",
         "Thiết kế microservices với gRPC streaming, HTTP/2 multiplexing, ranh giới transaction\n"
         "cơ sở dữ liệu ACID, cơ chế retry lũy biến và circuit breaker."),
        ("IV. KUBERNETES CONTROLLER, OPERATOR & eBPF",
         "Xây dựng Kubernetes Operator hoàn chỉnh với controller-runtime, vòng lặp điều hòa mức\n"
         "(Level-Triggered Reconcile), OwnerReferences, Finalizers và quan sát hạt nhân với eBPF.")
    ]

    for idx, (p_title, p_desc) in enumerate(pillars):
        box_y = pillars_start_y - (idx * (box_height + box_gap)) - box_height
        # Outer box
        ax.add_patch(patches.Rectangle((b_x0 + 20, box_y), b_w - 40, box_height,
                                       facecolor="#F8F8F8", edgecolor="#CCCCCC", lw=0.5))
        # Left solid black accent bar
        ax.add_patch(patches.Rectangle((b_x0 + 20, box_y), 3.0, box_height,
                                       facecolor="#000000", edgecolor="none"))
        # Pillar Title
        ax.text(b_x0 + 32, box_y + box_height - 11, p_title,
                fontsize=7.4, fontfamily="sans-serif", weight="bold", color="#000000", va="top")
        # Pillar Description
        ax.text(b_x0 + 32, box_y + box_height - 27, p_desc,
                fontsize=6.2, fontfamily="sans-serif", color="#333333", linespacing=1.38, va="top")

    # Bottom Metadata & Barcode Box
    colophon_div_y = b_y0 + 105
    ax.plot([b_x0 + 10, b_x0 + b_w - 10], [colophon_div_y, colophon_div_y], color="#000000", lw=0.5)

    # Left: Colophon details
    ax.text(b_x0 + 20, colophon_div_y - 12, "THÔNG TIN XUẤT BẢN // EDITION SPECIFICATION",
            fontsize=6.5, fontfamily="sans-serif", weight="bold", va="top")
    ax.text(b_x0 + 20, colophon_div_y - 27,
            "Tác giả: Đoàn Ngọc Hoàng Minh\n"
            "Định dạng: ISO A4 // Khâu chỉ dán gáy keo PUR\n"
            "Chế bản: Đơn sắc Grayscale // Bản thảo 2026\n"
            "Kho mã nguồn: github.com/Minhlike/Golang",
            fontsize=6.2, fontfamily="DejaVu Sans", color="#444444", linespacing=1.4, va="top")

    # Right: Placeholder Box for Official Distribution Barcode (No synthetic stripes/ISBN)
    bc_w = 110
    bc_h = 44
    bc_x = b_x0 + b_w - bc_w - 20
    bc_y = colophon_div_y - 68
    ax.add_patch(patches.Rectangle((bc_x, bc_y), bc_w, bc_h, facecolor="#FAFAFA", edgecolor="#999999", lw=0.6, ls="--"))
    ax.text(bc_x + bc_w / 2.0, bc_y + bc_h / 2.0, "VỊ TRÍ DÁN MÃ VẠCH\nKHI PHÁT HÀNH CHÍNH THỨC",
            fontsize=6.0, fontfamily="sans-serif", color="#777777", ha="center", va="center", linespacing=1.3)

    # Save Full Cover Wrap Outputs
    out_wrap_pdf = OUTPUT_DIR / "full_cover_wrap_print.pdf"
    out_wrap_png = OUTPUT_DIR / "full_cover_wrap_300dpi.png"
    out_wrap_svg = OUTPUT_DIR / "full_cover_wrap.svg"

    fig.savefig(out_wrap_pdf, format="pdf", dpi=300)
    fig.savefig(out_wrap_png, format="png", dpi=300)
    fig.savefig(out_wrap_svg, format="svg")
    plt.close(fig)
    print(f"[Cover] Full Cover Wrap saved:\n  - {out_wrap_pdf}\n  - {out_wrap_png}\n  - {out_wrap_svg}")


if __name__ == "__main__":
    generate_front_cover_page()
    generate_full_cover_wrap()
    print("[Cover] All cover wrap deliverables generated successfully!")
