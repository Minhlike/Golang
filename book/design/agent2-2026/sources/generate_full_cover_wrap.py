# -*- coding: utf-8 -*-
"""generate_full_cover_wrap.py
Generates the complete, print-ready full cover wrap (Bìa sau + Gáy sách + Bìa trước)
and the standalone Front Cover page for the book GOLANG based on Concept 1:
Architectural Cross-Section & Spatial Cut (Manual of Section / Princeton Arch Press).

Specifications:
- Format: ISO A4 Trim Size (210 x 297 mm per page)
- Spine Width: 28.0 mm (calculated for ~500 pages on 80gsm Woodfree paper)
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
def draw_axonometric_cross_section(ax, cx, cy, scale=0.88):
    """Draws the 4-tier isometric axonometric cross-section of the Go engine."""
    cos30 = math.cos(math.radians(28))
    sin30 = math.sin(math.radians(28))

    def iso_proj(x, y, z):
        px = cx + (x - y) * cos30 * 1.05 * scale
        py = cy + (x + y) * sin30 * 0.65 * scale + z * 1.15 * scale
        return px, py

    tiers = [
        (-120, "TIER 0 // KERNEL & HARDWARE", "Syscall • Epoll • Cgroups", True),
        (-30,  "TIER 1 // GO RUNTIME ENGINE", "M:N Scheduler • GC • Channels", False),
        (60,   "TIER 2 // SERVICE BOUNDARIES", "gRPC • HTTP/2 • SQL Transactions", False),
        (150,  "TIER 3 // DISTRIBUTED SRE", "Controller • eBPF • Observability", False),
    ]

    slab_dx = 110
    slab_dy = 70
    thickness = 11

    # Vertical transmission hairlines (drawn behind/through tiers)
    for px_local in [-55, 0, 55]:
        for py_local in [-25, 20]:
            p_bot = iso_proj(px_local, py_local, -120)
            p_top = iso_proj(px_local, py_local, 150)
            ax.plot([p_bot[0], p_top[0]], [p_bot[1], p_top[1]],
                    color="#888888", lw=0.35 * scale, ls=(0, (3, 4)), zorder=5)

    for z_base, t_title, t_sub, is_foundation in tiers:
        p0 = iso_proj(-slab_dx, -slab_dy, z_base)
        p1 = iso_proj(slab_dx, -slab_dy, z_base)
        p2 = iso_proj(slab_dx, slab_dy, z_base)
        p3 = iso_proj(-slab_dx, slab_dy, z_base)

        face_color = "#E2E2E2" if is_foundation else "#FFFFFF"
        edge_color = "#000000"
        poly_top = patches.Polygon([p0, p1, p2, p3], closed=True,
                                   facecolor=face_color, edgecolor=edge_color,
                                   lw=0.8 * scale, zorder=10 + int(z_base))
        ax.add_patch(poly_top)

        # Front cut poché (thickness)
        q0 = iso_proj(-slab_dx, -slab_dy, z_base - thickness)
        q1 = iso_proj(slab_dx, -slab_dy, z_base - thickness)
        poly_front = patches.Polygon([p0, p1, q1, q0], closed=True,
                                     facecolor="#1A1A1A", edgecolor="#000000",
                                     lw=0.6 * scale, zorder=11 + int(z_base))
        ax.add_patch(poly_front)

        # Right cut poché
        q2 = iso_proj(slab_dx, slab_dy, z_base - thickness)
        poly_side = patches.Polygon([p1, p2, q2, q1], closed=True,
                                    facecolor="#444444", edgecolor="#000000",
                                    lw=0.6 * scale, zorder=11 + int(z_base))
        ax.add_patch(poly_side)

        # Internal poché voids & architectural features
        if is_foundation:
            for k in range(4):
                kx = -75 + k * 45
                ky = -20
                v0 = iso_proj(kx, ky, z_base)
                v1 = iso_proj(kx + 22, ky, z_base)
                v2 = iso_proj(kx + 22, ky + 35, z_base)
                v3 = iso_proj(kx, ky + 35, z_base)
                void_poly = patches.Polygon([v0, v1, v2, v3], closed=True,
                                            facecolor="#000000", edgecolor="#000000",
                                            lw=0.4 * scale, zorder=12 + int(z_base))
                ax.add_patch(void_poly)
        elif z_base == -30:
            for g in range(4):
                gx = -80 + g * 42
                gy = -25 + (g % 2) * 35
                r0 = iso_proj(gx, gy, z_base)
                r1 = iso_proj(gx + 18, gy, z_base)
                r2 = iso_proj(gx + 18, gy + 18, z_base)
                r3 = iso_proj(gx, gy + 18, z_base)
                poly_g = patches.Polygon([r0, r1, r2, r3], closed=True,
                                         facecolor="#F0F0F0", edgecolor="#222222",
                                         lw=0.5 * scale, zorder=12 + int(z_base))
                ax.add_patch(poly_g)
        elif z_base == 60:
            for c in range(3):
                cx_pipe = -55 + c * 55
                pt_a = iso_proj(cx_pipe, -45, z_base)
                pt_b = iso_proj(cx_pipe + 16, 45, z_base)
                ax.plot([pt_a[0], pt_b[0]], [pt_a[1], pt_b[1]],
                        color="#111111", lw=1.1 * scale, zorder=12 + int(z_base))
        elif z_base == 150:
            c0 = iso_proj(-30, -30, z_base)
            c1 = iso_proj(30, -30, z_base)
            c2 = iso_proj(30, 30, z_base)
            c3 = iso_proj(-30, 30, z_base)
            tower = patches.Polygon([c0, c1, c2, c3], closed=True,
                                    facecolor="#FFFFFF", edgecolor="#000000",
                                    lw=0.9 * scale, zorder=12 + int(z_base))
            ax.add_patch(tower)

        # Architectural tier tag leader from left corner (p3)
        p3_x, p3_y = p3
        ax.plot([p3_x, p3_x - 10 * scale], [p3_y, p3_y],
                color="#000000", lw=0.5 * scale, zorder=20)
        ax.plot([p3_x - 10 * scale, p3_x - 10 * scale], [p3_y - 2.5 * scale, p3_y + 2.5 * scale],
                color="#000000", lw=0.5 * scale, zorder=20)
        ax.text(p3_x - 13 * scale, p3_y + 4.5 * scale, t_title,
                fontsize=5.6 * scale, fontfamily="sans-serif", weight="bold", color="#111111",
                ha="right", va="bottom", zorder=20)
        ax.text(p3_x - 13 * scale, p3_y - 2.0 * scale, t_sub,
                fontsize=4.8 * scale, fontfamily="monospace", color="#444444",
                ha="right", va="top", zorder=20)


# ==============================================================================
# 1. GENERATE FRONT COVER (BÌA 1) STANDALONE
# ==============================================================================
def generate_front_cover_page():
    """Generates the standalone Front Cover A4 page for the electronic PDF."""
    fig, ax = plt.subplots(figsize=(8.267, 11.692), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    w_pt = PAGE_W_MM * MM_TO_PT
    h_pt = PAGE_H_MM * MM_TO_PT
    ax.set_xlim(0, w_pt)
    ax.set_ylim(0, h_pt)
    ax.axis("off")

    # Outer border
    margin = 18.0 * MM_TO_PT
    fw = w_pt - 2 * margin
    fh = h_pt - 2 * margin
    border_rect = patches.Rectangle((margin, margin), fw, fh,
                                    facecolor="none", edgecolor="#000000", lw=1.2)
    ax.add_patch(border_rect)

    # Top caliper header
    header_y = margin + fh - 20
    ax.plot([margin + 12, margin + fw - 12], [header_y, header_y], color="#000000", lw=0.6)
    ax.text(margin + 16, header_y + 4, "SYSTEMS ARCHITECTURE SPECIFICATION // MONOCHROME SECTION",
            fontsize=6.5, fontfamily="monospace", weight="bold", color="#333333", va="bottom")
    ax.text(margin + fw - 16, header_y + 4, "DOC REF: PAP-SEC-2026",
            fontsize=6.5, fontfamily="monospace", color="#555555", ha="right", va="bottom")

    # Main Title
    title_y = header_y - 30
    ax.text(w_pt / 2.0, title_y, "G  O  L  A  N  G",
            fontsize=40, fontfamily="sans-serif", weight="bold", color="#000000",
            ha="center", va="top")

    subtitle_y = title_y - 48
    ax.text(w_pt / 2.0, subtitle_y, "GIÁO TRÌNH CẬP NHẬT LIÊN TỤC VỀ KỸ NGHỆ PHẦN MỀM VÀ DEVOPS/SRE",
            fontsize=9.2, fontfamily="sans-serif", weight="bold", color="#222222",
            ha="center", va="top")

    author_y = subtitle_y - 20
    ax.text(w_pt / 2.0, author_y, "ĐOÀN NGỌC HOÀNG MINH",
            fontsize=9.0, fontfamily="sans-serif", color="#555555",
            ha="center", va="top")

    # Caliper dividing rule
    cal_y = author_y - 18
    ax.plot([margin + 35, margin + fw - 35], [cal_y, cal_y], color="#000000", lw=0.8)
    ax.plot([margin + 35, margin + 35], [cal_y - 3, cal_y + 3], color="#000000", lw=0.8)
    ax.plot([margin + fw - 35, margin + fw - 35], [cal_y - 3, cal_y + 3], color="#000000", lw=0.8)

    # Architectural Cross-Section Artwork
    cx = (w_pt / 2.0) + 48.0
    cy = 380.0
    draw_axonometric_cross_section(ax, cx, cy, scale=0.88)

    # Bottom Caliper Divider
    bot_div_y = margin + 75
    ax.plot([margin + 12, margin + fw - 12], [bot_div_y, bot_div_y], color="#000000", lw=0.6)

    # 3-Column Specifications with clean left-aligned gutters
    col1_x = margin + 14
    col2_x = margin + 14 + 165
    col3_x = margin + 14 + 340

    ax.text(col1_x, bot_div_y - 10, "SYSTEM RUNTIME SPECIFICATION",
            fontsize=5.4, fontfamily="sans-serif", weight="bold", va="top")
    ax.text(col1_x, bot_div_y - 23,
            "M:N Work-Stealing Scheduler\nTri-Color Concurrent GC\nChannel Rendezvous Engine",
            fontsize=4.6, fontfamily="monospace", color="#444444", linespacing=1.35, va="top")

    ax.text(col2_x, bot_div_y - 10, "PRODUCTION & DEVOPS ENGINEERING",
            fontsize=5.4, fontfamily="sans-serif", weight="bold", va="top")
    ax.text(col2_x, bot_div_y - 23,
            "Kubernetes Level-Triggered Reconcile\neBPF Kernel Observability Probes\nZero-Downtime Service Lifecycle",
            fontsize=4.6, fontfamily="monospace", color="#444444", linespacing=1.35, va="top")

    ax.text(col3_x, bot_div_y - 10, "PUBLICATION STANDARDS",
            fontsize=5.4, fontfamily="sans-serif", weight="bold", va="top")
    ax.text(col3_x, bot_div_y - 23,
            "Format: ISO A4 (210 x 297 mm)\nType: Source Serif 4 & JetBrains Mono\nPrint: High-Density Grayscale Monotone",
            fontsize=4.6, fontfamily="monospace", color="#444444", linespacing=1.35, va="top")

    # Save
    out_pdf = OUTPUT_DIR / "front_cover_page.pdf"
    out_png = OUTPUT_DIR / "front_cover_page_300dpi.png"
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
    # FRONT COVER (BÌA TRƯỚC - BÌA 1)
    # Range: x in [FRONT_LEFT_PT, FRONT_RIGHT_PT], y in [BOTTOM_TRIM_PT, TOP_TRIM_PT]
    # --------------------------------------------------------------------------
    f_margin = 16.0 * MM_TO_PT
    f_x0 = FRONT_LEFT_PT + f_margin
    f_y0 = BOTTOM_TRIM_PT + f_margin
    f_w = (PAGE_W_MM * MM_TO_PT) - 2 * f_margin
    f_h = (PAGE_H_MM * MM_TO_PT) - 2 * f_margin

    # Border
    ax.add_patch(patches.Rectangle((f_x0, f_y0), f_w, f_h, facecolor="none", edgecolor="#000000", lw=1.1))

    # Header
    f_head_y = f_y0 + f_h - 20
    ax.plot([f_x0 + 10, f_x0 + f_w - 10], [f_head_y, f_head_y], color="#000000", lw=0.5)
    ax.text(f_x0 + 14, f_head_y + 4, "SYSTEMS ARCHITECTURE SPECIFICATION // MONOCHROME SECTION",
            fontsize=6.2, fontfamily="monospace", weight="bold", color="#333333", va="bottom")
    ax.text(f_x0 + f_w - 14, f_head_y + 4, "DOC REF: PAP-SEC-2026",
            fontsize=6.2, fontfamily="monospace", color="#555555", ha="right", va="bottom")

    # Front Title
    f_title_y = f_head_y - 26
    f_cx = FRONT_LEFT_PT + (PAGE_W_MM * MM_TO_PT) / 2.0
    ax.text(f_cx, f_title_y, "G  O  L  A  N  G",
            fontsize=38, fontfamily="sans-serif", weight="bold", color="#000000", ha="center", va="top")

    f_sub_y = f_title_y - 45
    ax.text(f_cx, f_sub_y, "GIÁO TRÌNH CẬP NHẬT LIÊN TỤC VỀ KỸ NGHỆ PHẦN MỀM VÀ DEVOPS/SRE",
            fontsize=8.8, fontfamily="sans-serif", weight="bold", color="#222222", ha="center", va="top")

    f_auth_y = f_sub_y - 18
    ax.text(f_cx, f_auth_y, "ĐOÀN NGỌC HOÀNG MINH",
            fontsize=8.6, fontfamily="sans-serif", color="#555555", ha="center", va="top")

    # Front Caliper Divider
    f_cal_y = f_auth_y - 16
    ax.plot([f_x0 + 30, f_x0 + f_w - 30], [f_cal_y, f_cal_y], color="#000000", lw=0.7)
    ax.plot([f_x0 + 30, f_x0 + 30], [f_cal_y - 3, f_cal_y + 3], color="#000000", lw=0.7)
    ax.plot([f_x0 + f_w - 30, f_x0 + f_w - 30], [f_cal_y - 3, f_cal_y + 3], color="#000000", lw=0.7)

    # Front Artwork
    f_art_cy = BOTTOM_TRIM_PT + 380.0
    draw_axonometric_cross_section(ax, f_cx + 48.0, f_art_cy, scale=0.88)

    # Front Bottom Metadata
    f_bot_y = f_y0 + 72
    ax.plot([f_x0 + 10, f_x0 + f_w - 10], [f_bot_y, f_bot_y], color="#000000", lw=0.5)

    f_col1_x = f_x0 + 14
    f_col2_x = f_x0 + 14 + 168
    f_col3_x = f_x0 + 14 + 348

    ax.text(f_col1_x, f_bot_y - 10, "SYSTEM RUNTIME SPECIFICATION",
            fontsize=5.2, fontfamily="sans-serif", weight="bold", va="top")
    ax.text(f_col1_x, f_bot_y - 23,
            "M:N Work-Stealing Scheduler\nTri-Color Concurrent GC\nChannel Rendezvous Engine",
            fontsize=4.5, fontfamily="monospace", color="#444444", linespacing=1.35, va="top")

    ax.text(f_col2_x, f_bot_y - 10, "PRODUCTION & DEVOPS ENGINEERING",
            fontsize=5.2, fontfamily="sans-serif", weight="bold", va="top")
    ax.text(f_col2_x, f_bot_y - 23,
            "Kubernetes Level-Triggered Reconcile\neBPF Kernel Observability Probes\nZero-Downtime Service Lifecycle",
            fontsize=4.5, fontfamily="monospace", color="#444444", linespacing=1.35, va="top")

    ax.text(f_col3_x, f_bot_y - 10, "PUBLICATION STANDARDS",
            fontsize=5.2, fontfamily="sans-serif", weight="bold", va="top")
    ax.text(f_col3_x, f_bot_y - 23,
            "Format: ISO A4 (210 x 297 mm)\nType: Source Serif 4 & JetBrains Mono\nPrint: High-Density Grayscale Monotone",
            fontsize=4.5, fontfamily="monospace", color="#444444", linespacing=1.35, va="top")

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
    ax.text(b_x0 + b_w - 14, b_head_y + 4, "ISBN 978-604-0-2026-X",
            fontsize=6.2, fontfamily="monospace", color="#555555", ha="right", va="bottom")

    # Book Title on Back
    b_title_y = b_head_y - 25
    ax.text(b_x0 + 20, b_title_y, "G O L A N G", fontsize=22, fontfamily="sans-serif", weight="bold", color="#000000", va="top")
    
    b_sub_y = b_title_y - 30
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
            "Định dạng: ISO A4 (210 x 297 mm) // Khâu chỉ dán gáy keo PUR\n"
            "Chế bản: Đơn sắc High-Density Grayscale // Bản in thử nghiệm 2026\n"
            "Phần mềm mã nguồn mở: https://github.com/Minhlike/Golang",
            fontsize=5.4, fontfamily="monospace", color="#444444", linespacing=1.4, va="top")

    # Right: Barcode Box Placeholder
    bc_w = 95
    bc_h = 48
    bc_x = b_x0 + b_w - bc_w - 20
    bc_y = colophon_div_y - 70
    ax.add_patch(patches.Rectangle((bc_x, bc_y), bc_w, bc_h, facecolor="#FFFFFF", edgecolor="#000000", lw=0.6))
    
    # Barcode stripes
    for s in range(25):
        sx = bc_x + 6 + s * 3.4
        sw = 1.0 if (s % 3 != 0) else 1.8
        ax.plot([sx, sx], [bc_y + 13, bc_y + bc_h - 7], color="#000000", lw=sw)
    ax.text(bc_x + bc_w / 2.0, bc_y + 4.5, "9 786040 202601",
            fontsize=5.8, fontfamily="monospace", color="#000000", ha="center")

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
