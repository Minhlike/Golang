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
    """Figure 4.1: Error wrapping chain and inspection at caller boundary.
    
    Vertical 4-level chain:
    1. ProbeFunc (underlying cause)
    2. *ProbeFailure (structured context struct + Unwrap())
    3. applyProbe (operation wrapping with %w)
    4. Caller decision fork: errors.Is (sentinel) vs errors.As (data extraction).
    """
    d = Drawing(w, h)

    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))

    # Header strip
    d.add(Rect(0, h - 22, w, 22, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(10, h - 15, "RANH GIỚI LỖI // BẢO TOÀN NGUYÊN NHÂN & DỮ LIỆU CẤU TRÚC",
                 fontName="BookSansBold", fontSize=7.6, fillColor=COLOR_INK_DARK))
    d.add(String(w - 110, h - 15, "ERROR WRAPPING CHAIN",
                 fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_MUTED))

    # Layout constants
    x_left = 14.0
    block_w = 312.0
    center_x = x_left + block_w / 2.0  # 170.0

    # 1. Level 1: Underlying Root Cause (ProbeFunc)
    y1_top = 394.0
    h1 = 44.0
    d.add(Rect(x_left, y1_top - h1, block_w, h1, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(x_left, y1_top - 14, block_w, 14, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(x_left + 8, y1_top - 10, "1. NGUYÊN NHÂN NGUYÊN THỦY (ProbeFunc)",
                 fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(x_left + 8, y1_top - 25, "var ErrRoot = syscall.ECONNREFUSED  // hoặc lỗi mạng / OS",
                 fontName="BookMono", fontSize=6.7, fillColor=COLOR_BLACK))
    d.add(String(x_left + 8, y1_top - 36, "• Tầng thấp nhất trả về error nguyên nhân; chưa có ngữ cảnh nghiệp vụ",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MUTED))

    # Arrow L1 -> L2
    y_arr1_start = y1_top - h1
    y_arr1_end = 320.0
    draw_arrow(d, center_x, y_arr1_start, center_x, y_arr1_end, color=COLOR_BLACK, width=1.0, head_size=4.0)
    # Badge on arrow
    badge1_y = (y_arr1_start + y_arr1_end) / 2.0
    d.add(Rect(center_x - 52, badge1_y - 7, 104, 14, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(center_x, badge1_y - 3, "bọc vào field Cause", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 2. Level 2: Custom Structured Error (*ProbeFailure)
    y2_top = y_arr1_end
    h2 = 72.0
    d.add(Rect(x_left, y2_top - h2, block_w, h2, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(x_left, y2_top - 14, block_w, 14, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(x_left + 8, y2_top - 10, "2. ĐÓNG GÓI DỮ LIỆU CÓ CẤU TRÚC (*ProbeFailure)",
                 fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(x_left + 8, y2_top - 26, "failed := &ProbeFailure{Service: name, Endpoint: ep, Cause: err}",
                 fontName="BookMono", fontSize=6.7, fillColor=COLOR_INK_DARK))
    d.add(String(x_left + 8, y2_top - 38, "func (f *ProbeFailure) Unwrap() error { return f.Cause }",
                 fontName="BookMono", fontSize=6.7, fillColor=COLOR_INK_DARK))
    d.add(String(x_left + 8, y2_top - 51, "• Giữ nguyên vẹn identity của Cause qua Unwrap(); gắn Service & Endpoint",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MUTED))
    d.add(String(x_left + 8, y2_top - 63, "• Không nối chuỗi thủ công; bảo toàn dữ liệu phục vụ điều tra sự cố",
                 fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_MID))

    # Arrow L2 -> L3
    y_arr2_start = y2_top - h2
    y_arr2_end = 216.0
    draw_arrow(d, center_x, y_arr2_start, center_x, y_arr2_end, color=COLOR_BLACK, width=1.0, head_size=4.0)
    # Badge on arrow
    badge2_y = (y_arr2_start + y_arr2_end) / 2.0
    d.add(Rect(center_x - 52, badge2_y - 7, 104, 14, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(center_x, badge2_y - 3, "bọc bằng động từ %w", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 3. Level 3: Operation Boundary (applyProbe)
    y3_top = y_arr2_end
    h3 = 54.0
    d.add(Rect(x_left, y3_top - h3, block_w, h3, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(x_left, y3_top - 14, block_w, 14, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(x_left + 8, y3_top - 10, "3. BIÊN THAO TÁC NGHIỆP VỤ (applyProbe)",
                 fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(x_left + 8, y3_top - 26, 'return fmt.Errorf("probe %q: %w", name, failed)',
                 fontName="BookMono", fontSize=6.7, fillColor=COLOR_BLACK))
    d.add(String(x_left + 8, y3_top - 38, "• Bổ sung bối cảnh operation mà không phá vỡ chuỗi Unwrap() bên dưới",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MUTED))
    d.add(String(x_left + 8, y3_top - 48, "• Cho phép caller lột từng lớp bối cảnh về nguyên nhân sâu nhất",
                 fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_MID))

    # Fork Arrow from L3 down to Caller Stage (4a & 4b)
    fork_y_start = y3_top - h3
    badge3_y = 138.0
    d.add(Line(center_x, fork_y_start, center_x, badge3_y + 8, strokeColor=COLOR_BLACK, strokeWidth=1.0))

    # Badge "err trả về Caller"
    d.add(Rect(center_x - 45, badge3_y - 7, 90, 15, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.7))
    d.add(String(center_x, badge3_y - 3, "err trả về Caller", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Stage 4: Two side-by-side Decision Boxes
    gap4 = 14.0
    w4 = (block_w - gap4) / 2.0  # 149.0 pt
    x4a = x_left
    x4b = x_left + w4 + gap4
    y4_top = 114.0
    h4 = 78.0

    # Diverging arrows from badge bottom to top center of each box
    arrow_fork_y = badge3_y - 7
    draw_arrow(d, center_x - 10, arrow_fork_y, x4a + w4 / 2.0, y4_top, color=COLOR_BLACK, width=1.0, head_size=4.0)
    draw_arrow(d, center_x + 10, arrow_fork_y, x4b + w4 / 2.0, y4_top, color=COLOR_BLACK, width=1.0, head_size=4.0)

    # 4A. errors.Is (SENTINEL MATCHING)
    d.add(Rect(x4a, y4_top - h4, w4, h4, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(x4a, y4_top - 16, w4, 16, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(x4a + 6, y4_top - 11, "4a. errors.Is (SENTINEL)", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(x4a + 6, y4_top - 28, "if errors.Is(err, target)", fontName="BookMono", fontSize=6.6, fillColor=COLOR_BLACK))
    d.add(String(x4a + 6, y4_top - 40, "• Duyệt toàn bộ chuỗi Unwrap()", fontName="BookSans", fontSize=6.5, fillColor=COLOR_INK_MUTED))
    d.add(String(x4a + 6, y4_top - 51, "• So khớp identity sentinel", fontName="BookSans", fontSize=6.5, fillColor=COLOR_INK_MUTED))
    d.add(String(x4a + 6, y4_top - 63, "• Dùng để rẽ nhánh quyết định", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_BLACK))
    d.add(String(x4a + 6, y4_top - 73, "• Không phụ thuộc số lớp bọc", fontName="BookSans", fontSize=6.3, fillColor=COLOR_INK_MUTED))

    # 4B. errors.As (DATA CONTEXT EXTRACTION)
    d.add(Rect(x4b, y4_top - h4, w4, h4, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(x4b, y4_top - 16, w4, 16, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(x4b + 6, y4_top - 11, "4b. errors.As (DATA CONTEXT)", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(x4b + 6, y4_top - 28, "var f *ProbeFailure", fontName="BookMono", fontSize=6.6, fillColor=COLOR_BLACK))
    d.add(String(x4b + 6, y4_top - 39, "if errors.As(err, &f)", fontName="BookMono", fontSize=6.6, fillColor=COLOR_BLACK))
    d.add(String(x4b + 6, y4_top - 51, "• Trích xuất struct an toàn kiểu", fontName="BookSans", fontSize=6.5, fillColor=COLOR_INK_MUTED))
    d.add(String(x4b + 6, y4_top - 63, "• Lấy Service/Endpoint có cấu trúc", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_BLACK))
    d.add(String(x4b + 6, y4_top - 73, "• Tuyệt đối không parse chuỗi", fontName="BookSansBold", fontSize=6.4, fillColor=COLOR_INK_DARK))

    # Footnote - 2 lines, strictly fitting width with good bottom margin
    d.add(String(12, 19.0, "* Go error wrapping: Mỗi tầng dùng %w để bổ sung bối cảnh operation mà không phá vỡ định danh lỗi gốc.",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MID))
    d.add(String(12, 9.0, "  Caller dùng errors.Is để phân loại nhánh quyết định, errors.As để lấy dữ liệu struct; không bao giờ parse chuỗi lỗi.",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MID))

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
    d.add(Rect(col1_x + 6, c1_concl_y, col_w - 12, 48, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.6))
    d.add(String(col1_x + 10, c1_concl_y + 34, "[KẾT QUẢ]", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10, c1_concl_y + 22, "• Zero resource leak", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(col1_x + 10, c1_concl_y + 11, "• Không dọn rác tài nguyên rỗng", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_MUTED))

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

    # State bullets
    y_b2 = cbox2_y - 18
    d.add(String(col2_x + 8, y_b2,      "• open() trả về lỗi kết nối", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8, y_b2 - 13, "• Không có session hợp lệ", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8, y_b2 - 26, "• Scope chưa nhận ownership", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MUTED))
    d.add(String(col2_x + 8, y_b2 - 39, "• KHÔNG gọi Close()", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_BLACK))
    d.add(String(col2_x + 8, y_b2 - 50, "  (tránh nil pointer dereference)", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_MUTED))

    # Conclusion box at bottom
    c2_concl_y = box_y_bot + 8
    d.add(Rect(col2_x + 6, c2_concl_y, col_w - 12, 48, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.6))
    d.add(String(col2_x + 10, c2_concl_y + 34, "[KẾT QUẢ]", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10, c2_concl_y + 22, "• Bảo toàn lỗi khởi tạo ban đầu", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(col2_x + 10, c2_concl_y + 11, "• Không gọi dọn dẹp vô nghĩa", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_MUTED))

    # ------------------ COLUMN 3: ACQUISITION SUCCEEDED (DEFER CLOSE) ------------------
    d.add(Rect(col3_x, box_y_bot, col_w, box_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(col3_x, box_y_top - 20, col_w, 20, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(col3_x + 8, box_y_top - 14, "ĐƯỜNG 3: SỞ HỮU & THOÁT", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))

    d.add(String(col3_x + 8, box_y_top - 36, "3. Nhận ownership & defer:", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))

    # Code snippet box
    cbox3_y = box_y_top - 120
    cbox3_h = 78.0
    d.add(Rect(col3_x + 6, cbox3_y, col_w - 12, cbox3_h, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(col3_x + 10, cbox3_y + 63, "session, err := open(ep)", fontName="BookMono", fontSize=6.6, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, cbox3_y + 51, "defer func() {", fontName="BookMono", fontSize=6.6, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, cbox3_y + 39, "  if cErr := session.Close();", fontName="BookMono", fontSize=6.3, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, cbox3_y + 27, "     cErr != nil && err == nil {", fontName="BookMono", fontSize=6.1, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, cbox3_y + 16, "    err = fmt.Errorf(...)", fontName="BookMono", fontSize=6.3, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, cbox3_y + 6,  "  }", fontName="BookMono", fontSize=6.6, fillColor=COLOR_BLACK))

    # Middle execution bullet
    d.add(String(col3_x + 8, cbox3_y - 12, "• return run(ctx, ep, session)", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK))

    # Error policy box in middle
    pbox_y = box_y_bot + 56
    pbox_h = 48.0
    d.add(Rect(col3_x + 6, pbox_y, col_w - 12, pbox_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_BLACK, strokeWidth=0.8))
    d.add(Rect(col3_x + 6, pbox_y + pbox_h - 14, col_w - 12, 14, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_BLACK, strokeWidth=0.5))
    d.add(String(col3_x + 10, pbox_y + pbox_h - 10, "CHÍNH SÁCH BẢO TOÀN LỖI:", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, pbox_y + 20, "• run() lỗi: GIỮ LỖI CHÍNH (không nuốt)", fontName="BookSansBold", fontSize=6.4, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, pbox_y + 8,  "• run() ok: trả lỗi Close() hoặc nil", fontName="BookSansBold", fontSize=6.4, fillColor=COLOR_INK_DARK))

    # Conclusion box at bottom (aligned with Col 1 and Col 2)
    c3_concl_y = box_y_bot + 8
    d.add(Rect(col3_x + 6, c3_concl_y, col_w - 12, 44, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.6))
    d.add(String(col3_x + 10, c3_concl_y + 30, "[KẾT QUẢ]", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10, c3_concl_y + 19, "• Close() luôn chạy khi thoát", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(col3_x + 10, c3_concl_y + 9,  "• Không nuốt sự cố nghiệp vụ chính", fontName="BookSans", fontSize=6.4, fillColor=COLOR_INK_DARK))

    # Footnote - 2 lines, strictly fitting width with good bottom margin
    d.add(String(12, 21.0, "* Quy tắc defer: Chỉ đăng ký defer ngay sau khi acquire tài nguyên thành công; không đăng ký khi chưa sở hữu session.",
                 fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_MID))
    d.add(String(12, 10.0, "  Chính sách lỗi: Named return (err error) bảo toàn failure chính từ run(), ngăn không cho lỗi dọn dẹp che giấu sự cố gốc.",
                 fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_MID))

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
