"""Standalone artwork generator for Agent 2 - Golang Book Design System 2026.

Generates three completely distinct, high-end cover art concepts:
1. Concept 1: Architectural Cross-Section & Spatial Cut (Manual of Section / Axonometric Cutaway)
2. Concept 2: Scientific Engraving & Topological Flow Field (Tufte / Haeckel / Vector Manifold)
3. Concept 3: Constructivist Kinetic Typography & Modular Monolith (Ruder / Müller-Brockmann / Isometric)

Produces for each concept:
- Vector SVG file
- Vector PDF file
- High-res flat A4 print PNG (300 DPI)
- Photorealistic 3D book perspective mockup PNG (with spine, page block, and lighting)
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ARTWORK_DIR = HERE.parent / "artwork"
ARTWORK_DIR.mkdir(parents=True, exist_ok=True)

# A4 Dimensions in points and inches
A4_WIDTH_PT = 595.28   # 210 mm
A4_HEIGHT_PT = 841.89  # 297 mm
DPI = 300
A4_WIDTH_PX = int(A4_WIDTH_PT / 72.0 * DPI)   # 2480 px
A4_HEIGHT_PX = int(A4_HEIGHT_PT / 72.0 * DPI) # 3508 px


# ==============================================================================
# CONCEPT 1: ARCHITECTURAL CROSS-SECTION & SPATIAL CUT
# ==============================================================================
def draw_concept1_cross_section(ax):
    """Draws an intricate architectural cutaway of the Go software systems architecture."""
    ax.set_xlim(0, A4_WIDTH_PT)
    ax.set_ylim(0, A4_HEIGHT_PT)
    ax.set_aspect("equal")
    ax.axis("off")

    # Pure white background
    ax.add_patch(patches.Rectangle((0, 0), A4_WIDTH_PT, A4_HEIGHT_PT, color="#FFFFFF"))

    # Outer border & technical frame (24mm inside, 18mm outside, 22mm top, 20mm bottom)
    left_m = 24 * 72 / 25.4   # ~68 pt
    right_m = 18 * 72 / 25.4  # ~51 pt
    top_m = 22 * 72 / 25.4    # ~62 pt
    bottom_m = 20 * 72 / 25.4 # ~57 pt
    fw = A4_WIDTH_PT - left_m - right_m
    fh = A4_HEIGHT_PT - top_m - bottom_m

    # Fine technical framing lines
    ax.plot([left_m, left_m + fw], [top_m + fh, top_m + fh], color="#111111", lw=1.2)
    ax.plot([left_m, left_m + fw], [bottom_m, bottom_m], color="#111111", lw=1.2)
    ax.plot([left_m, left_m], [bottom_m, top_m + fh], color="#111111", lw=1.2)
    ax.plot([left_m + fw, left_m + fw], [bottom_m, top_m + fh], color="#111111", lw=1.2)

    # Secondary hairline guide
    inset = 6.0
    ax.plot([left_m + inset, left_m + fw - inset], [top_m + fh - inset, top_m + fh - inset], color="#888888", lw=0.4, ls=":")
    ax.plot([left_m + inset, left_m + fw - inset], [bottom_m + inset, bottom_m + inset], color="#888888", lw=0.4, ls=":")
    ax.plot([left_m + inset, left_m + inset], [bottom_m + inset, top_m + fh - inset], color="#888888", lw=0.4, ls=":")
    ax.plot([left_m + fw - inset, left_m + fw - inset], [bottom_m + inset, top_m + fh - inset], color="#888888", lw=0.4, ls=":")

    # Header Technical Metadata
    ax.text(left_m + 12, top_m + fh - 20, "SYSTEMS ARCHITECTURE SPECIFICATION // MONOCHROME SECTION",
            fontsize=6.5, fontfamily="monospace", color="#555555", weight="bold")
    ax.text(left_m + fw - 12, top_m + fh - 20, "DOC REF: PAP-SEC-2026",
            fontsize=6.5, fontfamily="monospace", color="#555555", ha="right")

    # Typography: Title Block
    title_y = top_m + fh - 75
    ax.text(A4_WIDTH_PT / 2.0, title_y, "G  O  L  A  N  G",
            fontsize=38, fontfamily="sans-serif", weight="bold", color="#000000",
            ha="center", va="center")
    
    # Subtitle with strong architectural rhythm
    ax.text(A4_WIDTH_PT / 2.0, title_y - 28, "GIÁO TRÌNH CẬP NHẬT LIÊN TỤC VỀ KỸ NGHỆ PHẦN MỀM VÀ DEVOPS/SRE",
            fontsize=9.5, fontfamily="sans-serif", weight="bold", color="#222222",
            ha="center", va="center")
    
    # Author line
    ax.text(A4_WIDTH_PT / 2.0, title_y - 46, "ĐOÀN NGỌC HOÀNG MINH",
            fontsize=9.0, fontfamily="sans-serif", color="#555555",
            ha="center", va="center")

    # Horizontal dividing caliper line
    sep_y = title_y - 62
    ax.plot([left_m + 30, left_m + fw - 30], [sep_y, sep_y], color="#000000", lw=0.8)
    ax.plot([left_m + 30, left_m + 30], [sep_y - 4, sep_y + 4], color="#000000", lw=0.8)
    ax.plot([left_m + fw - 30, left_m + fw - 30], [sep_y - 4, sep_y + 4], color="#000000", lw=0.8)

    # --------------------------------------------------------------------------
    # ARTWORK: Axonometric Cross-Section Cutaway of the Go Systems Engine
    # Center: (cx, cy)
    cx = A4_WIDTH_PT / 2.0
    cy = 380.0

    # Axonometric isometric basis vectors
    cos30 = math.cos(math.radians(28))
    sin30 = math.sin(math.radians(28))

    def iso_proj(x, y, z):
        """Projects 3D (x, y, z) into 2D canvas coordinates."""
        px = cx + (x - y) * cos30 * 1.05
        py = cy + (x + y) * sin30 * 0.65 + z * 1.15
        return px, py

    # 4 Architectural Platform Tiers:
    # Tier 0 (z = -120): Hardware & Linux Kernel Boundary
    # Tier 1 (z = -30):  Go Runtime Engine (GMP, Heaps, Channels, GC)
    # Tier 2 (z = 60):   Networking, Protocols & Data Boundaries (HTTP/2, gRPC, SQL)
    # Tier 3 (z = 150):  Cloud Native & SRE Control Plane (K8s Reconcile, eBPF, Tracing)
    tiers = [
        {"z": -120, "label": "TIER 0 // HARDWARE & LINUX KERNEL SUBSYSTEM (SYSCALL / CPU / MMU)", "dx": 110, "dy": 80},
        {"z": -30,  "label": "TIER 1 // GO RUNTIME ENGINE (M:N SCHEDULER / CHANNELS / GC ARENAS)", "dx": 100, "dy": 72},
        {"z": 60,   "label": "TIER 2 // SERVICES & BOUNDARIES (HTTP/gRPC / SQL TRANSACTIONS / POOLS)", "dx": 90, "dy": 64},
        {"z": 150,  "label": "TIER 3 // DISTRIBUTED SRE & OBSERVALITY (CONTROLLER / eBPF / TRACING)", "dx": 80, "dy": 56},
    ]

    # Draw vertical structural corner columns linking all tiers
    for corner_x, corner_y in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        pts = [iso_proj(corner_x * 75, corner_y * 55, z) for z in [-140, 170]]
        ax.plot([pts[0][0], pts[1][0]], [pts[0][1], pts[1][1]], color="#777777", lw=0.7, ls="--")

    # Draw each structural tier
    for idx, tier in enumerate(tiers):
        z = tier["z"]
        dx = tier["dx"]
        dy = tier["dy"]

        # Platform Slab corners: (p0: front-left, p1: front-right, p2: back-right, p3: back-left)
        p0 = iso_proj(-dx, -dy, z)
        p1 = iso_proj(dx, -dy, z)
        p2 = iso_proj(dx, dy, z)
        p3 = iso_proj(-dx, dy, z)

        # Platform lower edge for thickness (h = 8 pt)
        p0_b = (p0[0], p0[1] - 8)
        p1_b = (p1[0], p1[1] - 8)
        p2_b = (p2[0], p2[1] - 8)

        # Front edge faces (thickness poché)
        face_left = patches.Polygon([p0, p1, p1_b, p0_b], closed=True,
                                    facecolor="#E5E5E5" if idx % 2 == 0 else "#D8D8D8",
                                    edgecolor="#000000", lw=1.2)
        ax.add_patch(face_left)

        face_right = patches.Polygon([p1, p2, p2_b, p1_b], closed=True,
                                     facecolor="#CCCCCC" if idx % 2 == 0 else "#BEBEBE",
                                     edgecolor="#000000", lw=1.2)
        ax.add_patch(face_right)

        # Top face of platform (white or near-white with technical grid)
        slab_top = patches.Polygon([p0, p1, p2, p3], closed=True,
                                   facecolor="#FAFAFA", edgecolor="#000000", lw=1.4)
        ax.add_patch(slab_top)

        # Grid lines on top face
        for gx in np.linspace(-dx + 15, dx - 15, 5):
            g_start = iso_proj(gx, -dy, z)
            g_end = iso_proj(gx, dy, z)
            ax.plot([g_start[0], g_end[0]], [g_start[1], g_end[1]], color="#C0C0C0", lw=0.4, ls=":")

        for gy in np.linspace(-dy + 15, dy - 15, 5):
            g_start = iso_proj(-dx, gy, z)
            g_end = iso_proj(dx, gy, z)
            ax.plot([g_start[0], g_end[0]], [g_start[1], g_end[1]], color="#C0C0C0", lw=0.4, ls=":")

        # Detailed internal architectural machinery cutaways on each tier:
        if idx == 0:
            # Kernel syscall traps and memory rings
            ring_cx, ring_cy = iso_proj(0, 0, z)
            ax.plot([ring_cx - 40, ring_cx + 40], [ring_cy, ring_cy], color="#222222", lw=1.0)
            # Memory pages hatch
            for bx in np.linspace(-50, 50, 4):
                b_p = iso_proj(bx, -20, z)
                box = patches.Polygon([
                    iso_proj(bx-8, -25, z), iso_proj(bx+8, -25, z),
                    iso_proj(bx+8, -5, z), iso_proj(bx-8, -5, z)
                ], closed=True, facecolor="#111111", edgecolor="#000000", lw=0.8)
                ax.add_patch(box)
        elif idx == 1:
            # GMP Scheduler: M-threads, G-goroutines, P-processors as geometric cut volumes
            for g_idx, (gx, gy_val) in enumerate([(-40, -10), (0, -20), (35, 5), (-25, 25), (20, 30)]):
                # Extruded 3D prism (Goroutine/Processor node)
                base = iso_proj(gx, gy_val, z)
                top = iso_proj(gx, gy_val, z + 22)
                ax.plot([base[0], top[0]], [base[1], top[1]], color="#000000", lw=1.2)
                # Prism top
                prism = patches.Circle(top, radius=3.2, facecolor="#000000" if g_idx == 0 else "#FFFFFF",
                                       edgecolor="#000000", lw=1.0)
                ax.add_patch(prism)
            # Channel pipeline arrows (hatched vector line)
            c1 = iso_proj(-35, -10, z + 12)
            c2 = iso_proj(30, 10, z + 12)
            ax.annotate("", xy=c2, xytext=c1,
                        arrowprops=dict(arrowstyle="->", color="#000000", lw=1.2, ls="-"))
        elif idx == 2:
            # Network multiplexing streams
            for sx in np.linspace(-45, 45, 5):
                s_start = iso_proj(sx, -25, z)
                s_mid = iso_proj(sx * 0.4, 0, z + 15)
                s_end = iso_proj(sx * 0.8, 25, z + 30)
                ax.plot([s_start[0], s_mid[0], s_end[0]], [s_start[1], s_mid[1], s_end[1]],
                        color="#333333", lw=0.9)
        elif idx == 3:
            # Reconcile control loop & eBPF sensor tower
            tower_base = iso_proj(0, 0, z)
            tower_top = iso_proj(0, 0, z + 35)
            ax.plot([tower_base[0], tower_top[0]], [tower_base[1], tower_top[1]], color="#000000", lw=2.0)
            # Reconcile circular loop
            t = np.linspace(0, 2*np.pi, 30)
            rx = 28 * np.cos(t)
            ry = 18 * np.sin(t)
            loop_pts = [iso_proj(x, y, z + 25) for x, y in zip(rx, ry)]
            lx = [p[0] for p in loop_pts]
            ly = [p[1] for p in loop_pts]
            ax.plot(lx, ly, color="#000000", lw=1.4, ls="-")

        # Architectural section annotations & callout leaders
        leader_x = left_m + 16 if idx % 2 == 0 else left_m + fw - 16
        leader_ha = "left" if idx % 2 == 0 else "right"
        target_pt = p0 if idx % 2 == 0 else p1
        ax.plot([leader_x, target_pt[0] - 10 if idx % 2 == 0 else target_pt[0] + 10, target_pt[0]],
                [target_pt[1], target_pt[1], target_pt[1]], color="#666666", lw=0.5)
        ax.text(leader_x, target_pt[1] + 3, tier["label"],
                fontsize=5.8, fontfamily="monospace", color="#222222", ha=leader_ha, weight="bold")

    # Bottom Technical Legend & Colophon
    bot_y = bottom_m + 30
    ax.plot([left_m + 30, left_m + fw - 30], [bot_y + 35, bot_y + 35], color="#000000", lw=0.8)

    col1_x = left_m + 25
    col2_x = left_m + fw / 2.0
    col3_x = left_m + fw - 25

    ax.text(col1_x, bot_y + 20, "SYSTEM RUNTIME SPECIFICATION", fontsize=6.5, fontfamily="sans-serif", weight="bold")
    ax.text(col1_x, bot_y + 8, "M:N Work-Stealing Scheduler\nGarbage-Collection Tri-Color Sweep\nConcurrent Channel Topology",
            fontsize=5.5, fontfamily="monospace", color="#444444", linespacing=1.3)

    ax.text(col2_x, bot_y + 20, "PRODUCTION & DEVOPS ENGINEERING", fontsize=6.5, fontfamily="sans-serif", weight="bold", ha="center")
    ax.text(col2_x, bot_y + 8, "Kubernetes Level-Triggered Reconcile\neBPF Kernel Observability Probes\nZero-Downtime Microservice Lifecycle",
            fontsize=5.5, fontfamily="monospace", color="#444444", ha="center", linespacing=1.3)

    ax.text(col3_x, bot_y + 20, "PUBLICATION STANDARDS", fontsize=6.5, fontfamily="sans-serif", weight="bold", ha="right")
    ax.text(col3_x, bot_y + 8, "Format: ISO A4 (210 x 297 mm)\nType: Source Serif 4 & JetBrains Mono\nPrint: High-Density Grayscale Monotone",
            fontsize=5.5, fontfamily="monospace", color="#444444", ha="right", linespacing=1.3)


# ==============================================================================
# CONCEPT 2: SCIENTIFIC ENGRAVING & TOPOLOGICAL FLOW FIELD
# ==============================================================================
def draw_concept2_engraving_flow(ax):
    """Draws an ultra-fine copperplate scientific engraving of a topological concurrency flow field."""
    ax.set_xlim(0, A4_WIDTH_PT)
    ax.set_ylim(0, A4_HEIGHT_PT)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(patches.Rectangle((0, 0), A4_WIDTH_PT, A4_HEIGHT_PT, color="#FFFFFF"))

    left_m = 24 * 72 / 25.4
    right_m = 18 * 72 / 25.4
    top_m = 22 * 72 / 25.4
    bottom_m = 20 * 72 / 25.4
    fw = A4_WIDTH_PT - left_m - right_m
    fh = A4_HEIGHT_PT - top_m - bottom_m

    # Classic Double Border (Scientific Engraving Frame)
    ax.plot([left_m, left_m + fw], [top_m + fh, top_m + fh], color="#000000", lw=2.0)
    ax.plot([left_m, left_m + fw], [bottom_m, bottom_m], color="#000000", lw=2.0)
    ax.plot([left_m, left_m], [bottom_m, top_m + fh], color="#000000", lw=2.0)
    ax.plot([left_m + fw, left_m + fw], [bottom_m, top_m + fh], color="#000000", lw=2.0)

    # Inner fine border
    gap = 4.0
    ax.plot([left_m + gap, left_m + fw - gap], [top_m + fh - gap, top_m + fh - gap], color="#000000", lw=0.6)
    ax.plot([left_m + gap, left_m + fw - gap], [bottom_m + gap, bottom_m + gap], color="#000000", lw=0.6)
    ax.plot([left_m + gap, left_m + gap], [bottom_m + gap, top_m + fh - gap], color="#000000", lw=0.6)
    ax.plot([left_m + fw - gap, left_m + fw - gap], [bottom_m + gap, top_m + fh - gap], color="#000000", lw=0.6)

    # Corner rosette squares (Scientific plate registration)
    for cx_c, cy_c in [(left_m, bottom_m), (left_m + fw, bottom_m), (left_m, top_m + fh), (left_m + fw, top_m + fh)]:
        ax.add_patch(patches.Rectangle((cx_c - 3, cy_c - 3), 6, 6, facecolor="#000000", edgecolor="none"))

    # Header plate banner
    plate_y = top_m + fh - 30
    ax.text(A4_WIDTH_PT / 2.0, plate_y, "TABULA MATHEMATICA ET TOPOLOGICA CONCURRENTIAE",
            fontsize=7.0, fontfamily="serif", style="italic", color="#333333", ha="center")
    ax.plot([left_m + 80, left_m + fw - 80], [plate_y - 6, plate_y - 6], color="#333333", lw=0.5)

    # Main Title: Classical Roman Typography
    title_y = top_m + fh - 80
    ax.text(A4_WIDTH_PT / 2.0, title_y, "G   O   L   A   N   G",
            fontsize=40, fontfamily="serif", weight="bold", color="#000000",
            ha="center", va="center")

    ax.text(A4_WIDTH_PT / 2.0, title_y - 30, "MÔ HÌNH TOÁN HỌC & ĐỒ THỊ DÒNG CHẢY HỆ THỐNG",
            fontsize=10.0, fontfamily="serif", style="italic", color="#222222", ha="center")

    ax.text(A4_WIDTH_PT / 2.0, title_y - 48, "Đoàn Ngọc Hoàng Minh",
            fontsize=9.5, fontfamily="serif", color="#444444", ha="center")

    # --------------------------------------------------------------------------
    # ARTWORK: 3D Topological Streamline Manifold (Riemann Potential Field)
    # Generated with analytical mathematical curves to emulate master copperplate engraving
    center_x = A4_WIDTH_PT / 2.0
    center_y = 390.0

    # Grid of stream lines (80 concentric and orthogonal manifold curves)
    u_vals = np.linspace(-3.2, 3.2, 90)
    for idx, u in enumerate(u_vals):
        # Parametric curve representing concurrency backpressure and saddle barrier
        v = np.linspace(-2.2, 2.2, 120)
        # Potential function: z = x^3 - 3xy^2 (Monkey saddle) blended with Gaussian well
        z = (u**3 - 3 * u * (v**2)) * 0.08 + 1.2 * np.exp(-(u**2 + v**2))

        # Oblique cabinet projection onto 2D
        scale = 32.0
        x_proj = center_x + (u * scale) - (v * scale * 0.45)
        y_proj = center_y + (v * scale * 0.65) + (z * scale * 0.85)

        # Variable stroke density: lines near saddle get thicker or denser
        is_key_line = (idx % 3 == 0)
        lw = 0.8 if is_key_line else 0.35
        color = "#111111" if is_key_line else "#555555"

        ax.plot(x_proj, y_proj, color=color, lw=lw)

    # Cross-contour orthogonal ribs (hatching)
    for v_cross in np.linspace(-2.0, 2.0, 35):
        u_pts = np.linspace(-3.0, 3.0, 100)
        z_pts = (u_pts**3 - 3 * u_pts * (v_cross**2)) * 0.08 + 1.2 * np.exp(-(u_pts**2 + v_cross**2))

        x_p = center_x + (u_pts * 32.0) - (v_cross * 32.0 * 0.45)
        y_p = center_y + (v_cross * 32.0 * 0.65) + (z_pts * 32.0 * 0.85)

        ax.plot(x_p, y_p, color="#333333", lw=0.4, ls="--")

    # Singularities / Critical Points (Labelled with classical mathematical callouts)
    # Center saddle
    ax.plot([center_x], [center_y + 35], "o", color="#000000", markersize=4.0)
    ax.text(center_x + 8, center_y + 38, "Ω [Rendezvous Barrier]", fontsize=6.5, fontfamily="serif", style="italic")

    # Left vortex (Goroutine Work-Stealing Pool)
    vx1 = center_x - 75
    vy1 = center_y - 20
    ax.plot([vx1], [vy1], "o", color="#000000", markersize=3.5)
    ax.text(vx1 - 10, vy1 - 10, "G_pool [Work-Stealing Equilibrium]", fontsize=6.0, fontfamily="serif", ha="right")

    # Right sink (Backpressure Buffer Drain)
    vx2 = center_x + 75
    vy2 = center_y + 20
    ax.plot([vx2], [vy2], "o", color="#000000", markersize=3.5)
    ax.text(vx2 + 10, vy2 - 10, "Δ_sink [Bounded Leaky Bucket]", fontsize=6.0, fontfamily="serif", ha="left")

    # Mathematical Equation Plate below artwork
    eq_y = 175.0
    ax.text(A4_WIDTH_PT / 2.0, eq_y,
            r"$\oint_{\partial \Omega} (\mathbf{J}_{goroutine} \cdot \mathbf{n}) \, dA = \sum_{k=1}^N \lambda_k - \mu_{drain}$",
            fontsize=9.5, fontfamily="serif", color="#111111", ha="center")
    ax.text(A4_WIDTH_PT / 2.0, eq_y - 18,
            "ĐỊNH LÝ BẢO TOÀN ÁP SUẤT DÒNG CÔNG VIỆC TRONG HỆ THỐNG ĐỒNG THỜI GO",
            fontsize=6.8, fontfamily="sans-serif", weight="bold", color="#444444", ha="center")

    # Bottom Caliper Scale Bar & Plate Identification
    scale_y = bottom_m + 35
    ax.plot([left_m + 50, left_m + fw - 50], [scale_y, scale_y], color="#000000", lw=1.0)
    for tick_x in np.linspace(left_m + 50, left_m + fw - 50, 11):
        ax.plot([tick_x, tick_x], [scale_y - 3, scale_y + 3], color="#000000", lw=0.8)

    ax.text(left_m + 50, scale_y - 14, "0.0 μs", fontsize=6.0, fontfamily="serif")
    ax.text(A4_WIDTH_PT / 2.0, scale_y - 14, "QUANTUM SCHEDULER SCALE // 10ms TIME-SLICE", fontsize=6.0, fontfamily="serif", ha="center")
    ax.text(left_m + fw - 50, scale_y - 14, "10.0 ms", fontsize=6.0, fontfamily="serif", ha="right")

    ax.text(A4_WIDTH_PT / 2.0, bottom_m + 12, "ẤN BẢN KHOA HỌC KỸ NGHỆ // NĂM XUẤT BẢN 2026",
            fontsize=7.0, fontfamily="serif", weight="bold", color="#111111", ha="center")


# ==============================================================================
# CONCEPT 3: CONSTRUCTIVIST KINETIC TYPOGRAPHY & MODULAR MONOLITH
# ==============================================================================
def draw_concept3_kinetic_typography(ax):
    """Draws a high-impact Constructivist Swiss typography composition with 3D monolithic blocks."""
    ax.set_xlim(0, A4_WIDTH_PT)
    ax.set_ylim(0, A4_HEIGHT_PT)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(patches.Rectangle((0, 0), A4_WIDTH_PT, A4_HEIGHT_PT, color="#FFFFFF"))

    left_m = 24 * 72 / 25.4
    right_m = 18 * 72 / 25.4
    top_m = 22 * 72 / 25.4
    bottom_m = 20 * 72 / 25.4
    fw = A4_WIDTH_PT - left_m - right_m
    fh = A4_HEIGHT_PT - top_m - bottom_m

    # Swiss 12-Column Grid Guide (Subtle Hairlines)
    col_w = fw / 12.0
    for i in range(13):
        gx = left_m + i * col_w
        ax.plot([gx, gx], [bottom_m, top_m + fh], color="#EAEAEA", lw=0.4)

    # 16 Horizontal Modular Rows
    row_h = fh / 16.0
    for j in range(17):
        gy = bottom_m + j * row_h
        ax.plot([left_m, left_m + fw], [gy, gy], color="#EAEAEA", lw=0.4)

    # Structural Outer Frame with Caliper Alignment Ticks
    ax.plot([left_m, left_m + fw], [top_m + fh, top_m + fh], color="#000000", lw=2.2)
    ax.plot([left_m, left_m + fw], [bottom_m, bottom_m], color="#000000", lw=2.2)
    ax.plot([left_m, left_m], [bottom_m, top_m + fh], color="#000000", lw=2.2)
    ax.plot([left_m + fw, left_m + fw], [bottom_m, top_m + fh], color="#000000", lw=2.2)

    # Dynamic Asymmetrical Black Header Block (Top 3 columns)
    header_block = patches.Rectangle((left_m, top_m + fh - 4 * row_h), 7 * col_w, 4 * row_h,
                                     facecolor="#000000", edgecolor="none")
    ax.add_patch(header_block)

    # Massive Contrast White Text inside black block
    ax.text(left_m + 16, top_m + fh - 1.2 * row_h, "GOLANG",
            fontsize=46, fontfamily="sans-serif", weight="bold", color="#FFFFFF")
    ax.text(left_m + 18, top_m + fh - 2.2 * row_h, "SYSTEMS // 2026",
            fontsize=12, fontfamily="monospace", weight="bold", color="#FFFFFF")
    ax.text(left_m + 18, top_m + fh - 3.2 * row_h, "KỸ NGHỆ PHẦN MỀM & SRE",
            fontsize=8.5, fontfamily="sans-serif", color="#CCCCCC")

    # Author and metadata block in right column
    meta_x = left_m + 7.5 * col_w
    ax.text(meta_x, top_m + fh - 1.0 * row_h, "TÁC GIẢ: ĐOÀN NGỌC HOÀNG MINH",
            fontsize=8.5, fontfamily="sans-serif", weight="bold", color="#000000")
    ax.text(meta_x, top_m + fh - 1.8 * row_h, "THIẾT KẾ: HỆ THỐNG MẪU ĐỐI TƯỢNG VÀ TRANG",
            fontsize=7.5, fontfamily="sans-serif", color="#444444")
    ax.text(meta_x, top_m + fh - 2.6 * row_h, "CHUẨN BẢN THẢO: ORIGIN/MAIN // A4 DỌC",
            fontsize=7.5, fontfamily="monospace", color="#555555")

    # Line weight scale visual index in right header
    scale_y = top_m + fh - 3.5 * row_h
    weights = [0.3, 0.6, 1.2, 2.0, 3.5]
    for w_idx, w in enumerate(weights):
        ax.plot([meta_x, meta_x + 30], [scale_y - w_idx * 6, scale_y - w_idx * 6], color="#000000", lw=w)
        ax.text(meta_x + 36, scale_y - w_idx * 6 - 2, f"{w}pt", fontsize=5.5, fontfamily="monospace", color="#666666")

    # --------------------------------------------------------------------------
    # ARTWORK: 3D Isometric Typographic Monolithic Blocks (Constructivist Modules)
    # The letters G, O, L, A, N, G built as extruded concrete architectural slabs
    letters = [
        {"char": "G", "x": 0, "y": 0, "z": 0},
        {"char": "O", "x": 1, "y": 0, "z": 1},
        {"char": "L", "x": 2, "y": 0, "z": 0},
        {"char": "A", "x": 0, "y": 1, "z": 2},
        {"char": "N", "x": 1, "y": 1, "z": 1},
        {"char": "G", "x": 2, "y": 1, "z": 3},
    ]

    base_cx = left_m + fw / 2.0
    base_cy = bottom_m + 5.5 * row_h

    # Isometric projection constants
    iso_w = 48.0
    iso_h = 28.0
    block_h = 32.0

    def block_proj(ix, iy, iz):
        px = base_cx + (ix - iy) * iso_w
        py = base_cy + (ix + iy) * (iso_h * 0.5) + iz * block_h
        return px, py

    # Draw interlocking blocks in depth order (painter's algorithm)
    sorted_letters = sorted(letters, key=lambda l: (l["x"] + l["y"], l["z"]))

    for blk in sorted_letters:
        bx, by = blk["x"], blk["y"]
        bz = blk["z"]

        p_front = block_proj(bx, by, bz)
        p_right = block_proj(bx + 0.8, by, bz)
        p_back = block_proj(bx + 0.8, by + 0.8, bz)
        p_left = block_proj(bx, by + 0.8, bz)

        p_front_t = (p_front[0], p_front[1] + block_h)
        p_right_t = (p_right[0], p_right[1] + block_h)
        p_back_t = (p_back[0], p_back[1] + block_h)
        p_left_t = (p_left[0], p_left[1] + block_h)

        # Front face (dark gray / hatched)
        front_poly = patches.Polygon([p_front, p_right, p_right_t, p_front_t], closed=True,
                                     facecolor="#1A1A1A", edgecolor="#000000", lw=1.2)
        ax.add_patch(front_poly)

        # Left face (medium gray)
        left_poly = patches.Polygon([p_front, p_left, p_left_t, p_front_t], closed=True,
                                    facecolor="#555555", edgecolor="#000000", lw=1.2)
        ax.add_patch(left_poly)

        # Top face (solid white with letter imprint)
        top_poly = patches.Polygon([p_front_t, p_right_t, p_back_t, p_left_t], closed=True,
                                   facecolor="#FFFFFF", edgecolor="#000000", lw=1.4)
        ax.add_patch(top_poly)

        # Bold letter glyph inside top face
        top_cx = (p_front_t[0] + p_back_t[0]) / 2.0
        top_cy = (p_front_t[1] + p_back_t[1]) / 2.0
        ax.text(top_cx, top_cy, blk["char"], fontsize=18, fontfamily="sans-serif",
                weight="bold", color="#000000", ha="center", va="center")

    # Keyword structural slabs flanking the isometric monument
    keywords = ["package", "import", "type", "struct", "interface", "func", "select", "chan", "go", "defer"]
    for k_idx, kw in enumerate(keywords):
        kw_y = bottom_m + 3.0 * row_h + (k_idx % 5) * 16.0
        kw_x = left_m + 15 if k_idx < 5 else left_m + fw - 75
        # Technical chip box
        chip = patches.Rectangle((kw_x, kw_y - 2), 60, 12, facecolor="#F0F0F0", edgecolor="#222222", lw=0.6)
        ax.add_patch(chip)
        ax.text(kw_x + 30, kw_y + 4, kw, fontsize=6.5, fontfamily="monospace", color="#000000", ha="center", va="center")

    # Bottom Manifesto Strip
    strip_y = bottom_m + 1.2 * row_h
    strip = patches.Rectangle((left_m, bottom_m), fw, 1.2 * row_h, facecolor="#000000", edgecolor="none")
    ax.add_patch(strip)

    ax.text(left_m + 14, bottom_m + 10, "MINIMALISM. PRECISION. ROBUSTNESS. CONCURRENCY. INVARIANTS.",
            fontsize=8.0, fontfamily="monospace", weight="bold", color="#FFFFFF")
    ax.text(left_m + fw - 14, bottom_m + 10, "EDITION 2026 // A4 MONOCHROME",
            fontsize=8.0, fontfamily="monospace", color="#AAAAAA", ha="right")


# ==============================================================================
# 3D BOOK PERSPECTIVE MOCKUP GENERATOR
# ==============================================================================
def create_3d_book_mockup(flat_img_path: Path, output_path: Path, concept_name: str):
    """Takes a flat 2D A4 cover image and renders a photorealistic 3D book mockup.
    
    Includes:
    - 3D perspective foreshortening of front cover
    - Visible spine on the left with book thickness (~3.5cm)
    - Realistic paper page block on right and bottom edges with fine page lines
    - Soft atmospheric drop shadow on neutral background
    - Lighting gradient / specular sheen
    """
    flat = Image.open(flat_img_path).convert("RGBA")
    w, h = flat.size

    # Mockup Canvas: 2400 x 2000 px, pure light-gray studio background
    cw, ch = 2400, 2000
    canvas = Image.new("RGBA", (cw, ch), (245, 245, 247, 255))

    # Calculate 3D perspective quad coordinates for front cover
    # Facing camera at a ~20 degree oblique three-quarter angle
    # Book origin in canvas
    origin_x = 780
    origin_y = 350
    cover_w = 1050
    cover_h = 1350

    # Perspective Quad: [Top-Left, Top-Right, Bottom-Right, Bottom-Left]
    # Foreshortening: right side is further away (smaller height)
    p_tl = (origin_x, origin_y)
    p_tr = (origin_x + cover_w, origin_y + 80)
    p_br = (origin_x + cover_w - 60, origin_y + cover_h - 40)
    p_bl = (origin_x, origin_y + cover_h)

    # Spine Coordinates (to the left of front cover)
    spine_thick = 140
    s_tl = (origin_x - spine_thick + 30, origin_y + 70)
    s_tr = p_tl
    s_bl = p_bl
    s_br = (origin_x - spine_thick + 30, origin_y + cover_h + 70)

    # Page Block Coordinates (thick paper stack visible on bottom and right)
    page_thick = 100
    pb_tr = (p_tr[0] + page_thick - 20, p_tr[1] + 20)
    pb_br = (p_br[0] + page_thick - 20, p_br[1] + 20)
    pb_bl = (p_bl[0] + page_thick - 30, p_bl[1] + 30)

    # 1. Cast Soft Drop Shadow underneath book
    shadow_mask = Image.new("L", (cw, ch), 0)
    s_draw = ImageDraw.Draw(shadow_mask)
    # Shadow polygon slightly shifted down and right
    shadow_poly = [
        (s_br[0] - 40, s_br[1] + 40),
        (s_bl[0], s_bl[1] + 60),
        (pb_bl[0] + 40, pb_bl[1] + 60),
        (pb_br[0] + 60, pb_br[1] + 40),
        (pb_tr[0] + 40, pb_tr[1] + 20),
        (s_tl[0] - 20, s_tl[1] + 40)
    ]
    s_draw.polygon(shadow_poly, fill=180)
    shadow_blurred = shadow_mask.filter(ImageFilter.GaussianBlur(radius=50))
    # Paste shadow
    shadow_layer = Image.new("RGBA", (cw, ch), (20, 20, 25, 0))
    shadow_layer.putalpha(shadow_blurred)
    canvas = Image.alpha_composite(canvas, shadow_layer)

    # 2. Render Page Block (Cream-white layered edges)
    draw = ImageDraw.Draw(canvas)
    # Right page block
    draw.polygon([p_tr, pb_tr, pb_br, p_br], fill=(238, 235, 228, 255), outline=(180, 175, 165, 255))
    # Bottom page block
    draw.polygon([p_bl, p_br, pb_br, pb_bl], fill=(230, 226, 218, 255), outline=(170, 165, 155, 255))

    # Draw fine horizontal page layer lines along page block
    for i in range(1, 20):
        t = i / 20.0
        # Right edge lines
        lx1 = p_tr[0] + (pb_tr[0] - p_tr[0]) * t
        ly1 = p_tr[1] + (pb_tr[1] - p_tr[1]) * t
        lx2 = p_br[0] + (pb_br[0] - p_br[0]) * t
        ly2 = p_br[1] + (pb_br[1] - p_br[1]) * t
        draw.line([(lx1, ly1), (lx2, ly2)], fill=(210, 205, 195, 255), width=1)

    # 3. Render Spine (Left)
    # Dark curved spine with lighting
    draw.polygon([s_tl, s_tr, s_bl, s_br], fill=(30, 30, 32, 255), outline=(15, 15, 15, 255))
    # Spine text (vertical)
    spine_img = Image.new("RGBA", (int(cover_h), int(spine_thick)), (30, 30, 32, 255))
    spine_draw = ImageDraw.Draw(spine_img)
    spine_draw.text((100, 35), "GOLANG // ĐOÀN NGỌC HOÀNG MINH // 2026", fill=(240, 240, 240, 255))
    spine_rotated = spine_img.rotate(90, expand=True)

    # 4. Warp Front Cover via 3D Perspective Transform
    # Find coefficients for PIL transform
    def find_coeffs(pa, pb):
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
        A = np.matrix(matrix, dtype=float)
        B = np.array(pb).reshape(8)
        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        return np.array(res).reshape(8)

    # Destination quad
    dest_quad = [p_tl, p_tr, p_br, p_bl]
    src_quad = [(0, 0), (w, 0), (w, h), (0, h)]
    coeffs = find_coeffs(dest_quad, src_quad)

    warped_cover = flat.transform((cw, ch), Image.PERSPECTIVE, coeffs, Image.BICUBIC)

    # Add lighting sheen gradient on cover (subtle reflection)
    sheen = Image.new("RGBA", (cw, ch), (255, 255, 255, 0))
    sheen_draw = ImageDraw.Draw(sheen)
    sheen_draw.polygon(dest_quad, fill=(255, 255, 255, 25))
    warped_cover = Image.alpha_composite(warped_cover, sheen)

    # Composite cover onto canvas
    canvas = Image.alpha_composite(canvas, warped_cover)

    # Book hinge groove (subtle vertical crease line at spine boundary)
    draw_canvas = ImageDraw.Draw(canvas)
    draw_canvas.line([p_tl, p_bl], fill=(50, 50, 50, 180), width=3)
    draw_canvas.line([(p_tl[0]+2, p_tl[1]), (p_bl[0]+2, p_bl[1])], fill=(220, 220, 220, 100), width=1)

    # Title Caption on Studio Background
    draw_canvas.text((100, 1850), f"3D PRESENTATION MOCKUP // {concept_name.upper()}",
                     fill=(80, 80, 85, 255))
    draw_canvas.text((100, 1885), "SPECIFICATION: A4 PORTRAIT (210 x 297 mm) // 493 PAGES ARCHIVAL BLOCK // MONOCHROME PRINT",
                     fill=(140, 140, 145, 255))

    canvas.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"Saved 3D Mockup: {output_path}")


# ==============================================================================
# MAIN BATCH GENERATOR
# ==============================================================================
def generate_all_artworks():
    """Generates vector SVG, vector PDF, flat PNG, and 3D mockups for all 3 concepts."""
    concepts = [
        {
            "name": "Concept 1: Architectural Cross-Section & Spatial Cut",
            "slug": "concept1_cross_section",
            "draw_func": draw_concept1_cross_section,
        },
        {
            "name": "Concept 2: Scientific Engraving & Topological Flow Field",
            "slug": "concept2_engraving_flow",
            "draw_func": draw_concept2_engraving_flow,
        },
        {
            "name": "Concept 3: Constructivist Kinetic Typography & Modular Monolith",
            "slug": "concept3_kinetic_typography",
            "draw_func": draw_concept3_kinetic_typography,
        },
    ]

    for idx, c in enumerate(concepts, 1):
        slug = c["slug"]
        print(f"\n[Art Direction] Rendering {c['name']}...")

        # 1. Matplotlib Figure for Exact Vector & High-Res A4 Rendering
        fig = plt.figure(figsize=(A4_WIDTH_PT / 72.0, A4_HEIGHT_PT / 72.0), dpi=DPI)
        ax = fig.add_axes([0, 0, 1, 1])

        c["draw_func"](ax)

        # Output paths
        flat_png = ARTWORK_DIR / f"{slug}_flat.png"
        vector_pdf = ARTWORK_DIR / f"{slug}_vector.pdf"
        vector_svg = ARTWORK_DIR / f"{slug}_vector.svg"
        mockup_png = ARTWORK_DIR / f"{slug}_3d_mockup.png"

        # Save Flat 300 DPI PNG
        fig.savefig(flat_png, dpi=DPI, format="png")
        print(f"Saved Flat 300 DPI PNG: {flat_png}")

        # Save Vector PDF
        fig.savefig(vector_pdf, format="pdf")
        print(f"Saved Vector PDF: {vector_pdf}")

        # Save Vector SVG
        fig.savefig(vector_svg, format="svg")
        print(f"Saved Vector SVG: {vector_svg}")

        plt.close(fig)

        # Render 3D Book Mockup
        create_3d_book_mockup(flat_png, mockup_png, c["name"])

    print("\n[Art Direction] All 3 Cover Concepts Generated Successfully!")


if __name__ == "__main__":
    generate_all_artworks()
