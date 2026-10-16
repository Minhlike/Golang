# -*- coding: utf-8 -*-
"""High-precision vector technical diagram for Chapter 5: Package Boundaries & One-Way DAG.

Refined based on actual implementation in labs/part5-package-design/:
- Pure monochrome black & white / grayscale palette (NO red details).
- Accurate file list: probe has check.go, doc.go (NO probe.go).
- Accurate runner description: stub runner returning nil.
- Accurate output separation: config error writes stderr & exits 2; probe error writes stdout & continues.
- Synchronized config input: os.LookupEnv passed to config.LoadTargets (no CLI flags).
- Exact Go type declaration: type Result struct { Service string }.
- Explicit distinction: Mandatory Go rules (internal/, import cycle) vs Project architectural policy.
- Exact publication dimensions (1:1 with Master PDF):
  * Figure 19 (Page 104, xref 246): 369.13 x 362.83 pt (Aspect Ratio = 1.01735)
"""

from __future__ import annotations

import math
from pathlib import Path
import tempfile

import pymupdf
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import (
    Circle,
    Drawing,
    Group,
    Line,
    Polygon,
    Rect,
    String,
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Root directory
ROOT = Path(__file__).resolve().parents[1]

# Pure monochrome & grayscale palette matching book_style
COLOR_BLACK = colors.HexColor("#000000")
COLOR_INK_DARK = colors.HexColor("#1A1A1A")
COLOR_INK_MID = colors.HexColor("#262626")
COLOR_INK_MUTED = colors.HexColor("#4A5568")
COLOR_INK_LIGHT = colors.HexColor("#718096")
COLOR_BORDER = colors.HexColor("#1A1A1A")
COLOR_BORDER_SUBTLE = colors.HexColor("#CBD5E1")
COLOR_BG_HEADER = colors.HexColor("#F0F2F5")
COLOR_BG_CARD = colors.HexColor("#FFFFFF")
COLOR_BG_SUBTLE = colors.HexColor("#F8F9FA")
COLOR_POLICY_BG = colors.HexColor("#F1F5F9")
COLOR_POLICY_BORDER = colors.HexColor("#CBD5E1")
COLOR_POLICY_TEXT = colors.HexColor("#2D3748")
COLOR_TAG_BG = colors.HexColor("#EDF2F7")


def register_fonts():
    """Register standard book typography fonts from assets/fonts/."""
    fonts_dir = ROOT / "assets/fonts"
    fonts = {
        "BookSerif": fonts_dir / "SourceSerif4-Regular.ttf",
        "BookSerifBold": fonts_dir / "SourceSerif4-Semibold.ttf",
        "BookSans": fonts_dir / "SourceSans3-Regular.ttf",
        "BookSansBold": fonts_dir / "SourceSans3-Semibold.ttf",
        "BookMono": fonts_dir / "JetBrainsMono-Regular.ttf",
    }
    for name, path in fonts.items():
        if name not in pdfmetrics.getRegisteredFontNames():
            if path.exists():
                pdfmetrics.registerFont(TTFont(name, str(path)))
            else:
                raise FileNotFoundError(f"Missing font file: {path}")


def draw_arrow(
    d: Drawing,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color=COLOR_BLACK,
    width: float = 1.1,
    head_size: float = 4.5,
):
    """Draw a clean vector line with an arrowhead."""
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width))
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 1e-4:
        return
    ux = dx / dist
    uy = dy / dist
    px = -uy
    py = ux

    p_tip = (x2, y2)
    p_left = (
        x2 - head_size * ux + (head_size * 0.45) * px,
        y2 - head_size * uy + (head_size * 0.45) * py,
    )
    p_right = (
        x2 - head_size * ux - (head_size * 0.45) * px,
        y2 - head_size * uy - (head_size * 0.45) * py,
    )

    poly = Polygon(
        [p_tip[0], p_tip[1], p_left[0], p_left[1], p_right[0], p_right[1]],
        fillColor=color,
        strokeColor=color,
        strokeWidth=0.2,
    )
    d.add(poly)


def draw_vector_x(d: Drawing, cx: float, cy: float, r: float = 2.8, color=COLOR_INK_DARK, width: float = 1.1):
    """Draw crisp vector X mark in pure monochrome."""
    d.add(Line(cx - r, cy - r, cx + r, cy + r, strokeColor=color, strokeWidth=width))
    d.add(Line(cx - r, cy + r, cx + r, cy - r, strokeColor=color, strokeWidth=width))


def build_package_boundary_graph_drawing(w: float = 369.13, h: float = 362.83) -> Drawing:
    """Figure 19: Package boundaries and one-way dependency graph.
    
    Dimensions: 369.13 x 362.83 pt (exact 1:1 match with Master PDF).
    """
    d = Drawing(w, h)

    # Background clean white canvas
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_CARD, strokeColor=None))

    # Outer layout margins
    x_left = 12.0
    box_w = w - 24.0  # 345.13 pt

    # ------------------------------------------------------------------
    # 1. TOP HEADER BANNER: Architecture context
    # ------------------------------------------------------------------
    d.add(String(x_left, h - 16.0, "RANH GIỚI GÓI // ĐỒ THỊ PHỤ THUỘC MỘT CHIỀU",
                 fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))
    d.add(String(w - x_left, h - 16.0, "GOLANG ARCHITECTURE // ONE-WAY DAG",
                 fontName="BookMono", fontSize=6.5, fillColor=COLOR_INK_MUTED, textAnchor="end"))
    d.add(Line(x_left, h - 21.0, w - x_left, h - 21.0, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.75))

    # ------------------------------------------------------------------
    # 2. TOP CONTAINER: cmd/opsprobe (Composition Root)
    # ------------------------------------------------------------------
    top_box_y = 247.0
    top_box_h = 91.0

    # Card background & border
    d.add(Rect(x_left, top_box_y, box_w, top_box_h,
               fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=1.0, rx=3, ry=3))

    # Header bar
    d.add(Rect(x_left, top_box_y + top_box_h - 22.0, box_w, 22.0,
               fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=1.0, rx=3, ry=3))
    d.add(Rect(x_left, top_box_y + top_box_h - 22.0, box_w, 4.0,
               fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(Line(x_left, top_box_y + top_box_h - 22.0, x_left + box_w, top_box_y + top_box_h - 22.0,
               strokeColor=COLOR_BORDER, strokeWidth=1.0))

    # Header Titles
    d.add(String(x_left + 8.0, top_box_y + top_box_h - 15.0, "cmd/opsprobe",
                 fontName="BookSansBold", fontSize=8.8, fillColor=COLOR_INK_DARK))
    d.add(String(x_left + 72.0, top_box_y + top_box_h - 15.0, "[GỐC LẮP GHÉP / COMPOSITION ROOT]",
                 fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_MUTED))
    d.add(String(x_left + box_w - 8.0, top_box_y + top_box_h - 15.0, "main.go (Package main)",
                 fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    # Body Content (Split into 2 Columns)
    col_split_x = x_left + (box_w / 2.0)

    # Column 1: Config Coordination & Data Mapping
    d.add(String(x_left + 8.0, top_box_y + 53.0, "• Nạp cấu hình: config.LoadTargets(os.LookupEnv)",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(x_left + 8.0, top_box_y + 40.0, "• Lỗi config: Ghi stderr, thoát os.Exit(2)",
                 fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(x_left + 8.0, top_box_y + 27.0, "• Ánh xạ ranh giới kiểu: config.Target → probe.Service",
                 fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(x_left + 14.0, top_box_y + 15.0, "(Gán Name, Host, Port; ngăn config rò rỉ vào domain)",
                 fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_MUTED))

    # Vertical divider between columns
    d.add(Line(col_split_x, top_box_y + 6.0, col_split_x, top_box_y + top_box_h - 26.0,
               strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, strokeDashArray=[2, 2]))

    # Column 2: Execution & Output Separation
    d.add(String(col_split_x + 8.0, top_box_y + 53.0, "• Khởi tạo stub runner: func(...) error { return nil }",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col_split_x + 8.0, top_box_y + 40.0, "• Vòng lặp kiểm tra: probe.Check(ctx, service, run)",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col_split_x + 8.0, top_box_y + 27.0, "• Lỗi probe: Ghi stdout (\"%s: %v\"), tiếp tục vòng lặp",
                 fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col_split_x + 8.0, top_box_y + 15.0, "• Thành công: Ghi stdout (\"%s healthy=true\")",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))

    # ------------------------------------------------------------------
    # 3. INTERACTION ZONE: Two Downward Dependency Arrows & Badges
    # ------------------------------------------------------------------
    mid_arrow_y1 = top_box_y
    mid_arrow_y2 = 215.0

    # Left arrow down to internal/config
    left_arrow_x = x_left + 83.0
    draw_arrow(d, left_arrow_x, mid_arrow_y1, left_arrow_x, mid_arrow_y2,
               color=COLOR_INK_DARK, width=1.1, head_size=4.5)

    # Left Arrow Badge
    left_badge_w = 120.0
    left_badge_h = 16.5
    left_badge_x = left_arrow_x - (left_badge_w / 2.0)
    left_badge_y = mid_arrow_y2 + 8.0
    d.add(Rect(left_badge_x, left_badge_y, left_badge_w, left_badge_h,
               fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    # Number badge 1
    d.add(Circle(left_badge_x + 9.0, left_badge_y + 8.2, 5.0,
                 fillColor=COLOR_INK_DARK, strokeColor=None))
    d.add(String(left_badge_x + 9.0, left_badge_y + 5.7, "1",
                 fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_BG_CARD, textAnchor="middle"))
    d.add(String(left_badge_x + 18.0, left_badge_y + 4.8, "Nạp cấu hình mục tiêu",
                 fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))

    # Right arrow down to probe
    right_arrow_x = x_left + box_w - 83.0
    draw_arrow(d, right_arrow_x, mid_arrow_y1, right_arrow_x, mid_arrow_y2,
               color=COLOR_INK_DARK, width=1.1, head_size=4.5)

    # Right Arrow Badge
    right_badge_w = 120.0
    right_badge_h = 16.5
    right_badge_x = right_arrow_x - (right_badge_w / 2.0)
    right_badge_y = mid_arrow_y2 + 8.0
    d.add(Rect(right_badge_x, right_badge_y, right_badge_w, right_badge_h,
               fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    # Number badge 2
    d.add(Circle(right_badge_x + 9.0, right_badge_y + 8.2, 5.0,
                 fillColor=COLOR_INK_DARK, strokeColor=None))
    d.add(String(right_badge_x + 9.0, right_badge_y + 5.7, "2",
                 fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_BG_CARD, textAnchor="middle"))
    d.add(String(right_badge_x + 18.0, right_badge_y + 4.8, "Khởi tạo & gọi Check",
                 fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))

    # ------------------------------------------------------------------
    # 4. LOWER LEVEL: Two Side-by-Side Packages (config & probe)
    # ------------------------------------------------------------------
    col_w = (box_w - 14.0) / 2.0  # 165.56 pt
    col_h = 148.0
    bot_box_y = 66.0

    # --- LEFT PACKAGE: internal/config ---
    cfg_x = x_left
    d.add(Rect(cfg_x, bot_box_y, col_w, col_h,
               fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=1.0, rx=3, ry=3))

    # Header bar
    d.add(Rect(cfg_x, bot_box_y + col_h - 22.0, col_w, 22.0,
               fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=1.0, rx=3, ry=3))
    d.add(Rect(cfg_x, bot_box_y + col_h - 22.0, col_w, 4.0,
               fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(Line(cfg_x, bot_box_y + col_h - 22.0, cfg_x + col_w, bot_box_y + col_h - 22.0,
               strokeColor=COLOR_BORDER, strokeWidth=1.0))

    d.add(String(cfg_x + 6.0, bot_box_y + col_h - 15.0, "internal/config",
                 fontName="BookSansBold", fontSize=8.5, fillColor=COLOR_INK_DARK))
    d.add(String(cfg_x + col_w - 6.0, bot_box_y + col_h - 15.0, "[QUY TẮC: internal/]",
                 fontName="BookSansBold", fontSize=6.4, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    # Toolchain boundary notice tag
    d.add(Rect(cfg_x + 6.0, bot_box_y + col_h - 35.5, col_w - 12.0, 10.5,
               fillColor=COLOR_TAG_BG, strokeColor=None, rx=1.5, ry=1.5))
    d.add(String(cfg_x + (col_w / 2.0), bot_box_y + col_h - 32.5,
                 "internal/ giới hạn theo cây thư mục cha",
                 fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # Internal details
    d.add(String(cfg_x + 6.0, bot_box_y + 100.0, "• Tệp: config.go  |  Mô hình: Target{Name, Host, Port}",
                 fontName="BookSans", fontSize=6.3, fillColor=COLOR_INK_DARK))

    d.add(String(cfg_x + 6.0, bot_box_y + 87.0, "• DefaultTargets() []Target:",
                 fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(cfg_x + 12.0, bot_box_y + 76.0, "- Cấp phát & trả về slice độc lập mới",
                 fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cfg_x + 12.0, bot_box_y + 66.0, "- Bảo toàn ownership, chống mutate cấu hình chung",
                 fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    d.add(String(cfg_x + 6.0, bot_box_y + 53.0, "• LoadTargets(lookup LookupEnv) ([]Target, error):",
                 fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(cfg_x + 12.0, bot_box_y + 42.0, "- Tách host:port bằng net.SplitHostPort chuẩn socket",
                 fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cfg_x + 12.0, bot_box_y + 32.0, "- Kiểm tra cổng 1..65535, chặn input không tin cậy",
                 fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cfg_x + 12.0, bot_box_y + 22.0, "- Inject LookupEnv func để test không sửa env máy",
                 fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Policy footer on left box (Monochrome style)
    d.add(Rect(cfg_x + 6.0, bot_box_y + 5.5, col_w - 12.0, 12.5,
               fillColor=COLOR_POLICY_BG, strokeColor=COLOR_POLICY_BORDER, strokeWidth=0.8, rx=2, ry=2))
    draw_vector_x(d, cfg_x + 14.0, bot_box_y + 11.5, r=2.6, color=COLOR_INK_DARK, width=1.1)
    d.add(String(cfg_x + 21.0, bot_box_y + 8.5,
                 "CHÍNH SÁCH: Không import probe hay cmd",
                 fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_POLICY_TEXT))

    # --- RIGHT PACKAGE: probe ---
    prb_x = x_left + col_w + 14.0
    d.add(Rect(prb_x, bot_box_y, col_w, col_h,
               fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=1.0, rx=3, ry=3))

    # Header bar
    d.add(Rect(prb_x, bot_box_y + col_h - 22.0, col_w, 22.0,
               fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=1.0, rx=3, ry=3))
    d.add(Rect(prb_x, bot_box_y + col_h - 22.0, col_w, 4.0,
               fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(Line(prb_x, bot_box_y + col_h - 22.0, prb_x + col_w, bot_box_y + col_h - 22.0,
               strokeColor=COLOR_BORDER, strokeWidth=1.0))

    d.add(String(prb_x + 6.0, bot_box_y + col_h - 15.0, "probe",
                 fontName="BookSansBold", fontSize=8.5, fillColor=COLOR_INK_DARK))
    d.add(String(prb_x + col_w - 6.0, bot_box_y + col_h - 15.0, "[PUBLIC API CONTRACT]",
                 fontName="BookSansBold", fontSize=6.4, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    # Public boundary notice tag
    d.add(Rect(prb_x + 6.0, bot_box_y + col_h - 35.5, col_w - 12.0, 10.5,
               fillColor=COLOR_TAG_BG, strokeColor=None, rx=1.5, ry=1.5))
    d.add(String(prb_x + (col_w / 2.0), bot_box_y + col_h - 32.5,
                 "Thư viện tái sử dụng (Public API contract)",
                 fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # Domain details (strictly check.go & doc.go, no probe.go)
    d.add(String(prb_x + 6.0, bot_box_y + 100.0, "• Tệp: check.go, doc.go  |  Mô hình: Service, Endpoint",
                 fontName="BookSans", fontSize=6.3, fillColor=COLOR_INK_DARK))

    d.add(String(prb_x + 6.0, bot_box_y + 87.0, "• type Result struct { Service string }:",
                 fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(prb_x + 12.0, bot_box_y + 76.0, "- Chỉ định danh service đã kiểm tra thành công",
                 fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(prb_x + 12.0, bot_box_y + 66.0, "- Không chứa Healthy bool giả; lỗi qua error chain",
                 fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    d.add(String(prb_x + 6.0, bot_box_y + 53.0, "• Check(ctx, Service, Runner) (Result, error):",
                 fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(prb_x + 12.0, bot_box_y + 42.0, "- Kiểm tra ctx.Err(), huỷ ngay nếu context huỷ",
                 fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(prb_x + 12.0, bot_box_y + 32.0, "- Hoàn toàn độc lập thiết bị đầu ra (output device)",
                 fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(prb_x + 12.0, bot_box_y + 22.0, "- Tuyệt đối không chứa fmt.Println hay cờ CLI",
                 fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Policy footer on right box (Monochrome style)
    d.add(Rect(prb_x + 6.0, bot_box_y + 5.5, col_w - 12.0, 12.5,
               fillColor=COLOR_POLICY_BG, strokeColor=COLOR_POLICY_BORDER, strokeWidth=0.8, rx=2, ry=2))
    draw_vector_x(d, prb_x + 14.0, bot_box_y + 11.5, r=2.6, color=COLOR_INK_DARK, width=1.1)
    d.add(String(prb_x + 21.0, bot_box_y + 8.5,
                 "CHÍNH SÁCH: Không import config hay cmd",
                 fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_POLICY_TEXT))

    # --- CENTRAL BARRIER (Between config and probe) ---
    mid_barrier_x = x_left + col_w + 7.0
    d.add(Line(mid_barrier_x, bot_box_y + 18.0, mid_barrier_x, bot_box_y + col_h - 18.0,
               strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.9, strokeDashArray=[2, 2]))

    # Small circular forbidden sign in the center (Monochrome)
    barrier_cy = bot_box_y + (col_h / 2.0)
    d.add(Circle(mid_barrier_x, barrier_cy, 6.0,
                 fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    draw_vector_x(d, mid_barrier_x, barrier_cy, r=2.8, color=COLOR_INK_DARK, width=1.2)

    # ------------------------------------------------------------------
    # 5. BOTTOM TECHNICAL FOOTER: Mandatory Rules vs Architectural Policy
    # ------------------------------------------------------------------
    foot_y = 10.0
    foot_h = 48.0

    d.add(Rect(x_left, foot_y, box_w, foot_h,
               fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.8, rx=3, ry=3))

    d.add(String(x_left + 8.0, foot_y + foot_h - 12.0,
                 "RÀNG BUỘC ĐỒ THỊ NHẬP KHẨU // QUY TẮC BẮT BUỘC VS CHÍNH SÁCH KIẾN TRÚC",
                 fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))

    d.add(String(x_left + 8.0, foot_y + foot_h - 23.0,
                 "• Quy tắc bắt buộc của Go: internal/ giới hạn import theo cây thư mục cha; compiler từ chối mọi chu trình (import cycle not allowed).",
                 fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_MID))
    d.add(String(x_left + 8.0, foot_y + foot_h - 33.0,
                 "• Chính sách kiến trúc dự án: Dependency đi một chiều từ cmd; probe và config độc lập hoàn toàn, không import ngược hoặc chéo.",
                 fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_MID))
    d.add(String(x_left + 8.0, foot_y + foot_h - 43.0,
                 "• Phân định luồng lỗi: Config lỗi ghi stderr và thoát exit 2; probe lỗi ghi stdout (\"%s: %v\") và tiếp tục vòng lặp.",
                 fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    return d


def export_diagrams_to_png(target_dir: Path | None = None, dpi: int = 320) -> list[Path]:
    """Render Chapter 5 drawing to high-resolution publication PNG at 320 DPI."""
    register_fonts()
    if target_dir is None:
        target_dir = ROOT / "assets/diagrams"
    target_dir.mkdir(parents=True, exist_ok=True)

    diagrams = [
        ("package-boundary-graph.png", build_package_boundary_graph_drawing()),
    ]

    exported = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for filename, drawing in diagrams:
            tmp_pdf = Path(tmpdir) / f"{Path(filename).stem}.pdf"
            renderPDF.drawToFile(drawing, str(tmp_pdf))

            doc = pymupdf.open(str(tmp_pdf))
            page = doc[0]
            pix = page.get_pixmap(dpi=dpi)
            out_png = target_dir / filename
            pix.save(str(out_png))
            doc.close()
            exported.append(out_png)
            print(f"Exported: {out_png} ({pix.width}x{pix.height} px, {out_png.stat().st_size} bytes)")

    return exported


if __name__ == "__main__":
    export_diagrams_to_png()
