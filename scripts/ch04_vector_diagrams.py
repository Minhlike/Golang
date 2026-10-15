# -*- coding: utf-8 -*-
"""High-precision vector technical diagrams for Chapter 4.

Follows the Master Prompt's architectural design language:
- Pure monochrome black & white / grayscale palette.
- Embedded fonts: BookSans, BookSansBold, BookMono, BookSerif.
- Strict technical accuracy based on Go specification vs runtime.
- Zero text collisions, orthogonal routing, balanced layout.
- Exact aspect-ratio match with publication master PDF bounding boxes.
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
    PolyLine,
    Rect,
    String,
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Root directory
ROOT = Path(__file__).resolve().parents[1]

# Palette definitions matching book_style
COLOR_BLACK = colors.HexColor("#000000")
COLOR_INK_DARK = colors.HexColor("#1A1A1A")
COLOR_INK_MID = colors.HexColor("#262626")  # Rich deep charcoal for maximum print legibility
COLOR_INK_MUTED = colors.HexColor("#444444")
COLOR_INK_LIGHT = colors.HexColor("#262626")  # Enhanced contrast for footnotes (no faded gray)
COLOR_HAIRLINE = colors.HexColor("#D4D4D4")
COLOR_SUBTLE = colors.HexColor("#EAEAEA")
COLOR_BG_BLOCK = colors.HexColor("#F6F7F9")
COLOR_BG_WHITE = colors.HexColor("#FFFFFF")
COLOR_BG_ACCENT = colors.HexColor("#EEEEEE")


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
    width: float = 1.0,
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


# ----------------------------------------------------------------------
# 1. Figure 4.1: error-boundary-trace.png (Aspect ratio ~0.8026, 340 x 423.6 pt)
# ----------------------------------------------------------------------
def build_error_boundary_trace_drawing(w: float = 340.0, h: float = 423.6) -> Drawing:
    """Figure 4.1: Error boundary trace separating missing service vs probe failure.
    
    Layout structure:
    - Top dispatch block: applyProbe(registry, name, run) inspecting service existence.
    - Two distinct, independent parallel branches:
      * Branch 1 (Left): Service not found (!found) -> probe is NOT run -> wraps sentinel
        ErrUnknownService -> Caller uses errors.Is to match sentinel and branch logic.
      * Branch 2 (Right): Service found -> runs run(service.Endpoint) -> fails -> wraps
        into *ProbeFailure with Unwrap() returning Cause -> wraps %w at operation boundary ->
        Caller uses errors.As to extract structured metadata (*ProbeFailure) without string parsing.
    """
    d = Drawing(w, h)

    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))

    # Header strip
    d.add(Rect(0, h - 22, w, 22, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(10, h - 15, "RANH GIỚI LỖI // PHÂN TÁCH 2 NHÁNH XỬ LÝ TRONG applyProbe",
                 fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))
    d.add(String(w - 110, h - 15, "ERROR BOUNDARY",
                 fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_MUTED))

    # Layout constants
    x_left = 14.0
    block_w = 312.0
    center_x = x_left + block_w / 2.0  # 170.0

    # Top Dispatch Box: Entry point applyProbe
    y_top_box = 394.0
    h_top_box = 42.0
    y_top_bot = y_top_box - h_top_box  # 352.0
    d.add(Rect(x_left, y_top_bot, block_w, h_top_box, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(x_left, y_top_box - 14, block_w, 14, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(x_left + 8, y_top_box - 10, "ĐIỂM VÀO BIÊN THAO TÁC: func applyProbe(registry, name, run) error",
                 fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(x_left + 8, y_top_box - 24, "service, found := registry[name]",
                 fontName="BookMono", fontSize=6.7, fillColor=COLOR_BLACK))
    d.add(String(x_left + 8, y_top_box - 35, "• Rẽ nhánh dứt khoát: service có tồn tại trong cấu hình hay không",
                 fontName="BookSans", fontSize=6.6, fillColor=COLOR_INK_MUTED))

    # Two column dimensions
    gap_col = 14.0
    col_w = (block_w - gap_col) / 2.0  # (312 - 14) / 2 = 149.0 pt
    x_col1 = x_left                     # 14.0 to 163.0
    x_col2 = x_left + col_w + gap_col   # 177.0 to 326.0

    c1_center = x_col1 + col_w / 2.0   # 88.5
    c2_center = x_col2 + col_w / 2.0   # 251.5

    # Branching arrows from Top Box down to columns
    y_branch_top = y_top_bot
    y_branch_end = 324.0

    # Left branch arrow (!found)
    draw_arrow(d, c1_center, y_branch_top, c1_center, y_branch_end, color=COLOR_BLACK, width=1.0, head_size=4.0)
    badge1_y = (y_branch_top + y_branch_end) / 2.0
    d.add(Rect(c1_center - 54, badge1_y - 7, 108, 14, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(c1_center, badge1_y - 3, "if !found (không chạy probe)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Right branch arrow (found)
    draw_arrow(d, c2_center, y_branch_top, c2_center, y_branch_end, color=COLOR_BLACK, width=1.0, head_size=4.0)
    badge2_y = (y_branch_top + y_branch_end) / 2.0
    d.add(Rect(c2_center - 54, badge2_y - 7, 108, 14, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(c2_center, badge2_y - 3, "if found (gọi run(endpoint))", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # ================== COLUMN 1: NHÁNH THIẾU CẤU HÌNH (!found) ==================
    y_col_top = y_branch_end
    y_col_bot = 38.0
    h_col = y_col_top - y_col_bot  # 286.0 pt

    d.add(Rect(x_col1, y_col_bot, col_w, h_col, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(x_col1, y_col_top - 18, col_w, 18, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(x_col1 + 6, y_col_top - 12, "NHÁNH 1: THIẾU CẤU HÌNH", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))

    # Box 1.1: Trả lỗi sớm tại applyProbe
    b11_y = y_col_top - 114.0
    b11_h = 90.0
    d.add(Rect(x_col1 + 5, b11_y, col_w - 10, b11_h, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(x_col1 + 9, b11_y + 76, "1. Trả lỗi sớm tại applyProbe:", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(x_col1 + 9, b11_y + 63, "// probe KHÔNG được gọi", fontName="BookMono", fontSize=6.3, fillColor=COLOR_INK_MUTED))
    d.add(String(x_col1 + 9, b11_y + 51, "return fmt.Errorf(", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(x_col1 + 9, b11_y + 39, '  "unknown %q: %w",', fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(x_col1 + 9, b11_y + 27, "  name, ErrUnknownService,", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(x_col1 + 9, b11_y + 16, ")", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(x_col1 + 9, b11_y + 5,  "• Không mutate state registry", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_MUTED))

    # Arrow down within Column 1
    y_c1_arr_top = b11_y
    y_c1_arr_bot = y_col_bot + 120.0
    draw_arrow(d, c1_center, y_c1_arr_top, c1_center, y_c1_arr_bot, color=COLOR_BLACK, width=1.0, head_size=4.0)
    badge_c1_y = (y_c1_arr_top + y_c1_arr_bot) / 2.0
    d.add(Rect(c1_center - 40, badge_c1_y - 6, 80, 13, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(c1_center, badge_c1_y - 3, "err trả về Caller", fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # Box 1.2: Caller xử lý bằng errors.Is
    b12_y = y_col_bot + 6.0
    b12_h = 108.0
    d.add(Rect(x_col1 + 5, b12_y, col_w - 10, b12_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.7))
    d.add(Rect(x_col1 + 5, b12_y + b12_h - 16, col_w - 10, 16, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(x_col1 + 9, b12_y + b12_h - 11, "CALLER: errors.Is (SENTINEL)", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    
    d.add(String(x_col1 + 9, b12_y + 77, "if errors.Is(err,", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(x_col1 + 9, b12_y + 65, "   ErrUnknownService) {", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(x_col1 + 9, b12_y + 53, '  // thêm vào config...', fontName="BookMono", fontSize=6.3, fillColor=COLOR_INK_MUTED))
    d.add(String(x_col1 + 9, b12_y + 42, "}", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    
    d.add(String(x_col1 + 9, b12_y + 28, "• Duyệt chuỗi unwrap so khớp sentinel", fontName="BookSans", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(x_col1 + 9, b12_y + 17, "• Phục vụ rẽ nhánh logic bên gọi", fontName="BookSans", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(x_col1 + 9, b12_y + 6,  "• KHÔNG chứa struct ProbeFailure", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_BLACK))

    # ================== COLUMN 2: NHÁNH PROBE THẤT BẠI (run lỗi) ==================
    d.add(Rect(x_col2, y_col_bot, col_w, h_col, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(x_col2, y_col_top - 18, col_w, 18, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(x_col2 + 6, y_col_top - 12, "NHÁNH 2: PROBE THẤT BẠI", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))

    # Box 2.1: Chạy probe & bọc struct
    b21_y = y_col_top - 114.0
    b21_h = 90.0
    d.add(Rect(x_col2 + 5, b21_y, col_w - 10, b21_h, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(x_col2 + 9, b21_y + 76, "1. Chạy probe & đóng gói struct:", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(x_col2 + 9, b21_y + 64, "err := run(service.Endpoint)", fontName="BookMono", fontSize=6.3, fillColor=COLOR_BLACK))
    d.add(String(x_col2 + 9, b21_y + 53, "service.Record(false)", fontName="BookMono", fontSize=6.3, fillColor=COLOR_INK_MUTED))
    d.add(String(x_col2 + 9, b21_y + 41, "failed := &ProbeFailure{", fontName="BookMono", fontSize=6.3, fillColor=COLOR_BLACK))
    d.add(String(x_col2 + 9, b21_y + 30, "  Service, Endpoint, Cause: err}", fontName="BookMono", fontSize=6.1, fillColor=COLOR_BLACK))
    d.add(String(x_col2 + 9, b21_y + 18, 'return fmt.Errorf("...: %w", failed)', fontName="BookMono", fontSize=6.1, fillColor=COLOR_BLACK))
    d.add(String(x_col2 + 9, b21_y + 5,  "• Unwrap() trả về Cause: err", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_MUTED))

    # Arrow down within Column 2
    y_c2_arr_top = b21_y
    y_c2_arr_bot = y_col_bot + 120.0
    draw_arrow(d, c2_center, y_c2_arr_top, c2_center, y_c2_arr_bot, color=COLOR_BLACK, width=1.0, head_size=4.0)
    badge_c2_y = (y_c2_arr_top + y_c2_arr_bot) / 2.0
    d.add(Rect(c2_center - 40, badge_c2_y - 6, 80, 13, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(c2_center, badge_c2_y - 3, "err trả về Caller", fontName="BookSans", fontSize=6.2, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # Box 2.2: Caller xử lý bằng errors.As
    b22_y = y_col_bot + 6.0
    b22_h = 108.0
    d.add(Rect(x_col2 + 5, b22_y, col_w - 10, b22_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.7))
    d.add(Rect(x_col2 + 5, b22_y + b22_h - 16, col_w - 10, 16, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(x_col2 + 9, b22_y + b22_h - 11, "CALLER: errors.As (DATA CONTEXT)", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))

    d.add(String(x_col2 + 9, b22_y + 77, "var failure *ProbeFailure", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(x_col2 + 9, b22_y + 65, "if errors.As(err, &failure) {", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(x_col2 + 9, b22_y + 53, '  fmt.Printf("%s lỗi tại %s",', fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_MUTED))
    d.add(String(x_col2 + 9, b22_y + 42, "    failure.Service, ...)", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_MUTED))
    d.add(String(x_col2 + 9, b22_y + 31, "}", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))

    d.add(String(x_col2 + 9, b22_y + 17, "• Trích xuất struct có dữ liệu cụ thể", fontName="BookSans", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(x_col2 + 9, b22_y + 6,  "• KHÔNG chứa ErrUnknownService", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_BLACK))

    # Footnote - 2 lines, strictly fitting width with good bottom margin
    d.add(String(12, 19.0, "* Hai nhánh độc lập: errors.Is nhận diện sentinel ErrUnknownService khi thiếu config (probe không chạy);",
                 fontName="BookSans", fontSize=6.7, fillColor=COLOR_INK_MID))
    d.add(String(12, 9.0, "  errors.As trích xuất dữ liệu từ *ProbeFailure khi probe thất bại. Hai nhánh không dùng chung một error chain.",
                 fontName="BookSans", fontSize=6.7, fillColor=COLOR_INK_MID))

    return d


# ----------------------------------------------------------------------
# 2. Figure 4.2: cancellation-cleanup-trace.png (Aspect ratio ~1.470, 476 x 323.8 pt)
# ----------------------------------------------------------------------
def build_cancellation_cleanup_trace_drawing(w: float = 476.0, h: float = 323.8) -> Drawing:
    """Figure 4.2: 3 execution paths in runWithSession with defer cleanup & error policy.
    
    Exact match to xref 235 bounding box in Master PDF:
    Rect(68.03, 161.36, 544.25, 485.27), width=476.22, height=323.91, ratio=1.4702.
    """
    d = Drawing(w, h)

    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))

    # Header strip
    d.add(Rect(0, h - 22, w, 22, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 15, "VÒNG ĐỜI TÀI NGUYÊN & DEFER CLEANUP // 3 ĐƯỜNG ĐI TRONG runWithSession",
                 fontName="BookSansBold", fontSize=7.8, fillColor=COLOR_INK_DARK))
    d.add(String(w - 144, h - 15, "RESOURCE OWNERSHIP & POLICY",
                 fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_MUTED))

    # 3 distinct columns corresponding to the 3 execution paths
    margin = 14.0
    col_gap = 12.0
    col_w = (w - 2 * margin - 2 * col_gap) / 3.0  # (476 - 28 - 24) / 3 = 141.33 pt

    col1_x = margin
    col2_x = margin + col_w + col_gap
    col3_x = margin + 2 * (col_w + col_gap)

    box_y_bot = 40.0
    box_y_top = h - 34.0  # 289.8
    box_h = box_y_top - box_y_bot  # 249.8 pt

    # ------------------ COLUMN 1: PRE-ACQUISITION CANCEL ------------------
    d.add(Rect(col1_x, box_y_bot, col_w, box_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(col1_x, box_y_top - 20, col_w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(col1_x + 8, box_y_top - 14, "ĐƯỜNG 1: HUỶ TRƯỚC MỞ", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))

    d.add(String(col1_x + 8, box_y_top - 36, "1. Kiểm tra context:", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))

    # Code box
    cbox1_y = box_y_top - 82
    d.add(Rect(col1_x + 6, cbox1_y, col_w - 12, 42, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(col1_x + 10, cbox1_y + 28, "if err := ctx.Err();", fontName="BookMono", fontSize=6.7, fillColor=COLOR_BLACK))
    d.add(String(col1_x + 10, cbox1_y + 16, "   err != nil {", fontName="BookMono", fontSize=6.7, fillColor=COLOR_BLACK))
    d.add(String(col1_x + 10, cbox1_y + 5,  "    return err", fontName="BookMono", fontSize=6.7, fillColor=COLOR_BLACK))

    # State bullets
    y_b1 = cbox1_y - 18
    d.add(String(col1_x + 8, y_b1,      "• Context đã bị hủy / timeout", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8, y_b1 - 13, "• Chưa thực hiện open(endpoint)", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8, y_b1 - 26, "• Chưa acquire tài nguyên session", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MUTED))
    d.add(String(col1_x + 8, y_b1 - 39, "• KHÔNG gọi Close()", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_BLACK))
    d.add(String(col1_x + 8, y_b1 - 50, "  (vì chưa có session hợp lệ)", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_MUTED))

    # Conclusion box at bottom
    c1_concl_y = box_y_bot + 8
    d.add(Rect(col1_x + 6, c1_concl_y, col_w - 12, 44, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.6))
    d.add(String(col1_x + 10, c1_concl_y + 30, "[KẾT QUẢ]", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10, c1_concl_y + 19, "• Zero resource leak", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(col1_x + 10, c1_concl_y + 9,  "• Không dọn rác tài nguyên rỗng", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_MUTED))

    # ------------------ COLUMN 2: ACQUISITION FAILURE ------------------
    d.add(Rect(col2_x, box_y_bot, col_w, box_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(col2_x, box_y_top - 20, col_w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(col2_x + 8, box_y_top - 14, "ĐƯỜNG 2: MỞ THẤT BẠI", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 8, box_y_top - 36, "2. Cố gắng mở session:", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))

    # Code box
    cbox2_y = box_y_top - 82
    d.add(Rect(col2_x + 6, cbox2_y, col_w - 12, 42, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(col2_x + 10, cbox2_y + 28, "session, err := open(ep)", fontName="BookMono", fontSize=6.7, fillColor=COLOR_BLACK))
    d.add(String(col2_x + 10, cbox2_y + 16, "if err != nil {", fontName="BookMono", fontSize=6.7, fillColor=COLOR_BLACK))
    d.add(String(col2_x + 10, cbox2_y + 5,  '    return fmt.Errorf(...)', fontName="BookMono", fontSize=6.7, fillColor=COLOR_BLACK))

    # State bullets according to contract of runWithSession
    y_b2 = cbox2_y - 18
    d.add(String(col2_x + 8, y_b2,      "• open() trả về lỗi khởi tạo", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8, y_b2 - 13, "• Scope chưa nhận session hợp lệ", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8, y_b2 - 26, "• Theo contract runWithSession:", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8, y_b2 - 38, "  chỉ đăng ký sau khi acquire ok", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_MUTED))
    d.add(String(col2_x + 8, y_b2 - 50, "• Thoát ngay; KHÔNG gọi Close()", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_BLACK))

    # Conclusion box at bottom
    c2_concl_y = box_y_bot + 8
    d.add(Rect(col2_x + 6, c2_concl_y, col_w - 12, 44, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.6))
    d.add(String(col2_x + 10, c2_concl_y + 30, "[KẾT QUẢ]", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10, c2_concl_y + 19, "• Bảo toàn lỗi mở ban đầu", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(col2_x + 10, c2_concl_y + 9,  "• Không gọi Close() trên đối tượng lỗi", fontName="BookSans", fontSize=6.3, fillColor=COLOR_INK_MUTED))

    # ------------------ COLUMN 3: ACQUISITION SUCCEEDED (DEFER CLOSE) ------------------
    d.add(Rect(col3_x, box_y_bot, col_w, box_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(col3_x, box_y_top - 20, col_w, 20, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(col3_x + 8, box_y_top - 14, "ĐƯỜNG 3: SỞ HỮU & THOÁT", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))

    d.add(String(col3_x + 8, box_y_top - 36, "3. Nhận ownership & defer:", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))

    # Code snippet box with logic excerpt indicator
    cbox3_y = box_y_top - 120
    cbox3_h = 78.0
    d.add(Rect(col3_x + 6, cbox3_y, col_w - 12, cbox3_h, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(col3_x + 10, cbox3_y + 64, "// logic excerpt (named return)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(col3_x + 10, cbox3_y + 53, "session, err := open(ep)", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, cbox3_y + 42, "defer func() {", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, cbox3_y + 31, "  if cErr := session.Close();", fontName="BookMono", fontSize=6.2, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, cbox3_y + 20, "     cErr != nil && err == nil {", fontName="BookMono", fontSize=6.0, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, cbox3_y + 10, "    err = fmt.Errorf(...)", fontName="BookMono", fontSize=6.2, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, cbox3_y + 1,  "  }", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))

    # Middle execution bullet
    d.add(String(col3_x + 8, cbox3_y - 12, "• return run(ctx, ep, session)", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))

    # Error policy box in middle
    pbox_y = box_y_bot + 56
    pbox_h = 48.0
    d.add(Rect(col3_x + 6, pbox_y, col_w - 12, pbox_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_BLACK, strokeWidth=0.8))
    d.add(Rect(col3_x + 6, pbox_y + pbox_h - 14, col_w - 12, 14, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_BLACK, strokeWidth=0.5))
    d.add(String(col3_x + 10, pbox_y + pbox_h - 10, "CHÍNH SÁCH LỖI (NAMED RETURN):", fontName="BookSansBold", fontSize=6.5, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, pbox_y + 20, "• run() lỗi: GIỮ LỖI RUN (lỗi chính)", fontName="BookSansBold", fontSize=6.4, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, pbox_y + 8,  "• run() ok: TRẢ LỖI CLOSE (khi err==nil)", fontName="BookSansBold", fontSize=6.4, fillColor=COLOR_INK_DARK))

    # Conclusion box at bottom (aligned with Col 1 and Col 2)
    c3_concl_y = box_y_bot + 8
    d.add(Rect(col3_x + 6, c3_concl_y, col_w - 12, 44, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.6))
    d.add(String(col3_x + 10, c3_concl_y + 30, "[KẾT QUẢ]", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10, c3_concl_y + 19, "• Close() luôn chạy khi thoát", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, c3_concl_y + 9,  "• Lỗi Close không đè lỗi run chính", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_DARK))

    # Footnote - 2 lines, strictly fitting width with good bottom margin
    d.add(String(12, 21.0, "* Quy tắc defer: Theo contract của runWithSession, Close() chỉ đăng ký sau khi acquire thành công; open() lỗi sẽ return ngay.",
                 fontName="BookSans", fontSize=7.0, fillColor=COLOR_INK_MID))
    d.add(String(12, 10.0, "  Chính sách lỗi: Named return (err error) bảo toàn failure chính từ run(), ngăn không cho lỗi dọn dẹp che giấu sự cố gốc.",
                 fontName="BookSans", fontSize=7.0, fillColor=COLOR_INK_MID))

    return d


def export_diagrams_to_png(target_dir: Path | None = None, dpi: int = 300) -> list[Path]:
    """Render all Chapter 4 drawings to high-resolution publication PNGs."""
    register_fonts()
    if target_dir is None:
        target_dir = ROOT / "assets/diagrams"
    target_dir.mkdir(parents=True, exist_ok=True)

    diagrams = [
        ("error-boundary-trace.png", build_error_boundary_trace_drawing()),
        ("cancellation-cleanup-trace.png", build_cancellation_cleanup_trace_drawing()),
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
