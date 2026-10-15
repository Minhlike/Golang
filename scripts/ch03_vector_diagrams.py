# -*- coding: utf-8 -*-
"""High-precision vector technical diagrams for Chapter 3.

Follows the Master Prompt's architectural design language:
- Pure monochrome black & white / grayscale palette.
- Embedded fonts: BookSans, BookSansBold, BookMono, BookSerif.
- Strict technical accuracy based on Go specification vs runtime.
- Zero text collisions, orthogonal routing, balanced layout.
- Generates 300 DPI publication-grade PNGs in assets/diagrams/.
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
    """Register the approved typography fonts."""
    fonts = ROOT / "assets/fonts"
    pdfmetrics.registerFont(TTFont("BookSerif", str(fonts / "SourceSerif4-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("BookSerifBold", str(fonts / "SourceSerif4-Semibold.ttf")))
    pdfmetrics.registerFont(TTFont("BookSans", str(fonts / "SourceSans3-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("BookSansBold", str(fonts / "SourceSans3-Semibold.ttf")))
    pdfmetrics.registerFont(TTFont("BookMono", str(fonts / "JetBrainsMono-Regular.ttf")))


def draw_arrow(d: Drawing, x1: float, y1: float, x2: float, y2: float,
               color=COLOR_BLACK, width: float = 1.0, head_size: float = 5.0):
    """Draw a clean vector line with an arrowhead pointing to (x2, y2)."""
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width))
    angle = math.atan2(y2 - y1, x2 - x1)
    left_angle = angle + math.radians(150)
    right_angle = angle - math.radians(150)
    hx1 = x2 + head_size * math.cos(left_angle)
    hy1 = y2 + head_size * math.sin(left_angle)
    hx2 = x2 + head_size * math.cos(right_angle)
    hy2 = y2 + head_size * math.sin(right_angle)
    d.add(Polygon([x2, y2, hx1, hy1, hx2, hy2], fillColor=color, strokeColor=color, strokeWidth=0.5))


# ----------------------------------------------------------------------
# 1. Figure 3.1: pointer-value-call.png (Pass-by-value call semantics)
# ----------------------------------------------------------------------
def build_pointer_value_call_drawing(w: float = 448.22, h: float = 168.0) -> Drawing:
    """Figure 3.1: Pass-by-value function call semantics (caller balance vs callee x)."""
    d = Drawing(w, h)

    # Outer frame container
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))

    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "NGỮ NGHĨA TRUYỀN THAM SỐ // LỜI GỌI addBonus(balance)",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 110, h - 14, "PASS-BY-VALUE",
                 fontName="BookMono", fontSize=7.4, fillColor=COLOR_INK_MUTED))

    # Left Box: Caller Scope (main)
    c_x, c_y, c_w, c_h = 14.0, 30.0, 150.0, 102.0
    d.add(Rect(c_x, c_y, c_w, c_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(c_x, c_y + c_h - 18, c_w, 18, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(c_x + 8, c_y + c_h - 13, "BÊN GỌI (CALLER SCOPE)", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))

    d.add(String(c_x + 8, c_y + c_h - 32, "Biến cục bộ bên gọi:", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    d.add(String(c_x + 8, c_y + c_h - 44, "var balance int = 100", fontName="BookMono", fontSize=7.4, fillColor=COLOR_INK_DARK))

    # Cell for balance
    d.add(Rect(c_x + 8, c_y + 24, c_w - 16, 24, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_MID, strokeWidth=0.6))
    d.add(String(c_x + 14, c_y + 36, "balance (int):", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    d.add(String(c_x + c_w - 18, c_y + 30, "100", fontName="BookMono", fontSize=11.0, fillColor=COLOR_BLACK, textAnchor="end"))

    d.add(String(c_x + 8, c_y + 9, "[KẾT QUẢ] balance vẫn là 100", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))

    # Right Box: Callee Scope (func addBonus)
    f_x, f_y, f_w, f_h = 265.0, 30.0, 169.0, 102.0
    d.add(Rect(f_x, f_y, f_w, f_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(f_x, f_y + f_h - 18, f_w, 18, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(f_x + 8, f_y + f_h - 13, "BÊN NHẬN (CALLEE: addBonus)", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))

    # Vertical sequence inside Callee
    d.add(String(f_x + 8, f_y + f_h - 30, "1. Khởi tạo parameter x bằng value:", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    d.add(Rect(f_x + 8, f_y + 44, f_w - 16, 18, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_MID, strokeWidth=0.5))
    d.add(String(f_x + 14, f_y + 49, "x : int = 100", fontName="BookMono", fontSize=7.4, fillColor=COLOR_INK_DARK))
    d.add(String(f_x + f_w - 14, f_y + 49, "(bản sao value)", fontName="BookSans", fontSize=7.0, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    # Down arrow for local mutation
    draw_arrow(d, f_x + 40, f_y + 44, f_x + 40, f_y + 32, color=COLOR_BLACK, width=0.8, head_size=3.0)
    d.add(String(f_x + 46, f_y + 35, "x += 20 (gán cục bộ)", fontName="BookMono", fontSize=7.0, fillColor=COLOR_INK_DARK))

    # Mutated box
    d.add(Rect(f_x + 8, f_y + 8, f_w - 16, 20, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_BLACK, strokeWidth=0.7))
    d.add(String(f_x + 14, f_y + 14, "x : int = 120", fontName="BookMono", fontSize=7.5, fillColor=COLOR_BLACK))
    d.add(String(f_x + f_w - 14, f_y + 14, "[cục bộ trong frame]", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK, textAnchor="end"))

    # Transfer Arrow between Scope 1 and Scope 2 (Ample 101 pt gap)
    mid_gap_x = (c_x + c_w + f_x) / 2
    draw_arrow(d, c_x + c_w + 4, c_y + 54, f_x - 4, f_y + 54, color=COLOR_BLACK, width=1.0, head_size=4.5)
    d.add(String(mid_gap_x, c_y + 66, "addBonus(balance)", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(mid_gap_x, c_y + 42, "Sao chép giá trị 100", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_MUTED, textAnchor="middle"))

    # Footnote - 2 lines, strictly fitting width
    d.add(String(12, 17.0, "* Go specification: Lời gọi hàm sao chép giá trị (pass-by-value) theo ngữ nghĩa ngôn ngữ.",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))
    d.add(String(12, 7.0, "  Sơ đồ biểu diễn quan hệ biến và giá trị; không khẳng định thao tác copy vật lý hay phân bổ stack/heap.",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))

    return d


# ----------------------------------------------------------------------
# 2. Figure 3.2: pointer-pointee.png (Pointer value & pointee dereference)
# ----------------------------------------------------------------------
def build_pointer_pointee_drawing(w: float = 448.22, h: float = 175.0) -> Drawing:
    """Figure 3.2: Pointer value and pointee relationship (dereference *balance)."""
    d = Drawing(w, h)

    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))

    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "QUAN HỆ POINTER & POINTEE // GIẢI THAM CHIẾU (DEREFERENCE)",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 120, h - 14, "CON TRỎ & BIẾN ĐÍCH",
                 fontName="BookMono", fontSize=7.4, fillColor=COLOR_INK_MUTED))

    # Left Container: Caller Variable amount (Pointee)
    p_x, p_y, p_w, p_h = 14.0, 32.0, 155.0, 105.0
    d.add(Rect(p_x, p_y, p_w, p_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(p_x, p_y + p_h - 18, p_w, 18, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(p_x + 8, p_y + p_h - 13, "BIẾN ĐÍCH (POINTEE: amount)", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))

    d.add(String(p_x + 8, p_y + p_h - 32, "Biến addressable bên caller:", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    d.add(String(p_x + 8, p_y + p_h - 44, "var amount int = 100", fontName="BookMono", fontSize=7.4, fillColor=COLOR_INK_DARK))

    # amount memory slot showing initial -> mutated state
    d.add(Rect(p_x + 8, p_y + 26, p_w - 16, 26, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_BLACK, strokeWidth=0.7))
    d.add(String(p_x + 14, p_y + 36, "100", fontName="BookMono", fontSize=8.5, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, p_x + 36, p_y + 38, p_x + 58, p_y + 38, color=COLOR_BLACK, width=0.8, head_size=3.0)
    d.add(String(p_x + 64, p_y + 36, "120 (đích gán)", fontName="BookMono", fontSize=8.5, fillColor=COLOR_BLACK))

    d.add(String(p_x + 8, p_y + 11, "• Trực tiếp nhận 120 qua dereference", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))

    # Right Container: Callee Parameter balance (Pointer value)
    f_x, f_y, f_w, f_h = 265.0, 32.0, 169.0, 105.0
    d.add(Rect(f_x, f_y, f_w, f_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(f_x, f_y + f_h - 18, f_w, 18, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(f_x + 8, f_y + f_h - 13, "THAM SỐ HÀM (balance : *int)", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))

    d.add(String(f_x + 8, f_y + f_h - 32, "func addBonus(balance *int)", fontName="BookMono", fontSize=7.4, fillColor=COLOR_INK_DARK))

    # Pointer slot holding &amount
    d.add(Rect(f_x + 8, f_y + 36, f_w - 16, 26, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_MID, strokeWidth=0.6))
    d.add(String(f_x + 14, f_y + 49, "Pointer value (bản sao):", fontName="BookSans", fontSize=7.0, fillColor=COLOR_INK_MUTED))
    d.add(String(f_x + 14, f_y + 38, "địa chỉ logic &amount", fontName="BookMono", fontSize=8.0, fillColor=COLOR_BLACK))

    d.add(String(f_x + 8, f_y + 20, "• Phép gán *balance += 20", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(f_x + 8, f_y + 8, "• Ghi thẳng vào pointee amount", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))

    # Middle Area: 96 pt clear gap
    mid_x = (p_x + p_w + f_x) / 2

    # Top Arrow: Call & Copy pointer value (&amount)
    draw_arrow(d, p_x + p_w + 4, p_y + 78, f_x - 4, f_y + 78, color=COLOR_BLACK, width=1.0, head_size=4.5)
    d.add(String(mid_x, p_y + 86, "addBonus(&amount)", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(mid_x, p_y + 70, "(Copy pointer value)", fontName="BookSans", fontSize=7.0, fillColor=COLOR_INK_MUTED, textAnchor="middle"))

    # Bottom Arrow: Dereference (*balance) targets amount directly
    draw_arrow(d, f_x - 4, f_y + 42, p_x + p_w + 4, p_y + 42, color=COLOR_BLACK, width=1.2, head_size=5.0)
    d.add(String(mid_x, f_y + 48, "*balance giải tham chiếu", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(mid_x, f_y + 34, "chọn amount làm đích gán", fontName="BookSans", fontSize=7.0, fillColor=COLOR_INK_MUTED, textAnchor="middle"))

    # Footnote - 2 lines, strictly fitting width
    d.add(String(12, 17.0, "* Phân biệt rõ bản sao pointer value (tham số balance) với biến đích (pointee amount).",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))
    d.add(String(12, 7.0, "  Phép dereference (*balance) truy cập trực tiếp biến đích; không giả định địa chỉ số hay phân bổ stack/heap.",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))

    return d


# ----------------------------------------------------------------------
# 3. Figure 3.3: struct-copy.png (Field-by-field struct copy semantics)
# ----------------------------------------------------------------------
def build_struct_copy_drawing(w: float = 448.22, h: float = 180.0) -> Drawing:
    """Figure 3.3: Struct assignment performs a field-by-field copy."""
    d = Drawing(w, h)

    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))

    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "NGỮ NGHĨA GÁN STRUCT // SAO CHÉP GIÁ TRỊ CÁC FIELD (VALUE SEMANTICS)",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 120, h - 14, "VALUE SEMANTICS",
                 fontName="BookMono", fontSize=7.4, fillColor=COLOR_INK_MUTED))

    # Balanced width for struct containers leaving 128.22 pt gap in middle
    box_w, box_h = 146.0, 118.0
    y_pos = 32.0

    # Left Container: billing (Original Struct)
    b_x = 14.0
    d.add(Rect(b_x, y_pos, box_w, box_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(b_x, y_pos + box_h - 18, box_w, 18, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(b_x + 8, y_pos + box_h - 13, "GỐC: billing : Service", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))

    # Fields for billing
    fields = [
        ("Name", '"billing"', False),
        ("Port", "8080", False),
        ("Healthy", "true", True),      # Preserved field
        ("Retries", "1", False),
    ]
    f_y = y_pos + box_h - 38
    for fname, fval, is_focus in fields:
        bg = COLOR_BG_BLOCK if not is_focus else COLOR_BG_WHITE
        stroke = COLOR_HAIRLINE if not is_focus else COLOR_BLACK
        d.add(Rect(b_x + 8, f_y, box_w - 16, 17, fillColor=bg, strokeColor=stroke, strokeWidth=0.7 if is_focus else 0.4))
        d.add(String(b_x + 14, f_y + 5, f"{fname}:", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
        d.add(String(b_x + box_w - 14, f_y + 5, fval, fontName="BookMono", fontSize=7.4, fillColor=COLOR_BLACK, textAnchor="end"))
        f_y -= 19

    d.add(String(b_x + 8, y_pos + 7, "[BẢO TOÀN] billing.Healthy = true", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))

    # Right Container: candidate (Copy Struct)
    c_x = w - 14.0 - box_w  # 288.22
    d.add(Rect(c_x, y_pos, box_w, box_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(c_x, y_pos + box_h - 18, box_w, 18, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(c_x + 8, y_pos + box_h - 13, "BẢN SAO: candidate : Service", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))

    # Fields for candidate
    c_fields = [
        ("Name", '"billing"', False),
        ("Port", "8080", False),
        ("Healthy", "false", True),     # Mutated field
        ("Retries", "1", False),
    ]
    f_y = y_pos + box_h - 38
    for fname, fval, is_focus in c_fields:
        bg = COLOR_BG_BLOCK if not is_focus else COLOR_BG_ACCENT
        stroke = COLOR_HAIRLINE if not is_focus else COLOR_BLACK
        d.add(Rect(c_x + 8, f_y, box_w - 16, 17, fillColor=bg, strokeColor=stroke, strokeWidth=0.8 if is_focus else 0.4))
        d.add(String(c_x + 14, f_y + 5, f"{fname}:", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
        d.add(String(c_x + box_w - 14, f_y + 5, fval, fontName="BookMono", fontSize=7.4, fillColor=COLOR_BLACK, textAnchor="end"))
        f_y -= 19

    d.add(String(c_x + 8, y_pos + 7, "[MUTATED] candidate.Healthy = false", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))

    # Center Copy Arrow & Clear Annotations (128.22 pt gap between 160.0 and 288.22)
    mid_x = (b_x + box_w + c_x) / 2  # 224.11
    draw_arrow(d, b_x + box_w + 6, y_pos + box_h - 38, c_x - 6, y_pos + box_h - 38, color=COLOR_BLACK, width=1.0, head_size=4.5)
    d.add(String(mid_x, y_pos + box_h - 30, "candidate := billing", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(mid_x, y_pos + box_h - 48, "Sao chép giá trị", fontName="BookSans", fontSize=7.0, fillColor=COLOR_INK_MUTED, textAnchor="middle"))
    d.add(String(mid_x, y_pos + box_h - 58, "các field hiện tại", fontName="BookSans", fontSize=7.0, fillColor=COLOR_INK_MUTED, textAnchor="middle"))

    # Middle explanatory note card (Width 110 pt, ample ~9.1 pt clearance on both sides!)
    card_w = 110.0
    d.add(Rect(mid_x - card_w / 2, y_pos + 10, card_w, 36, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(mid_x, y_pos + 34, "candidate.Healthy = false", fontName="BookMono", fontSize=6.6, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(mid_x, y_pos + 23, "Chỉ đổi field trên bản sao,", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MUTED, textAnchor="middle"))
    d.add(String(mid_x, y_pos + 14, "struct billing gốc độc lập", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Footnote - 2 lines, strictly fitting width
    d.add(String(12, 17.0, "* Go spec: Phép gán struct sao chép giá trị các field theo ngữ nghĩa Go (không bắt buộc copy vật lý từng lệnh).",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))
    d.add(String(12, 7.0, "  Sao chép struct không đồng nghĩa deep copy; nếu có field chứa pointer/slice/map, chúng vẫn chia sẻ dữ liệu tham chiếu.",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))

    return d


# ----------------------------------------------------------------------
# 4. Figure 3.4: map-sharing.png (Map assignment copies map value, shares data)
# ----------------------------------------------------------------------
def build_map_sharing_drawing(w: float = 448.22, h: float = 175.0) -> Drawing:
    """Figure 3.4: Map assignment copies map value, shares underlying map storage."""
    d = Drawing(w, h)

    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))

    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "NGỮ NGHĨA GÁN MAP // SAO CHÉP MAP VALUE, CHIA SẺ MAP DATA",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 120, h - 14, "SHARED MAP DATA",
                 fontName="BookMono", fontSize=7.4, fillColor=COLOR_INK_MUTED))

    # Left Column: Two Map Value Boxes (registry and alias)
    val_w, val_h = 150.0, 46.0
    r_x, r_y = 14.0, 92.0
    a_x, a_y = 14.0, 30.0

    # registry map value box
    d.add(Rect(r_x, r_y, val_w, val_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(r_x, r_y + val_h - 16, val_w, 16, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(r_x + 8, r_y + val_h - 11, "registry : map[string]int", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))
    d.add(String(r_x + 8, r_y + 17, "• Biến chứa map value ban đầu", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    d.add(String(r_x + 8, r_y + 6, "• Tham chiếu tới map data chung", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_DARK))

    # alias map value box
    d.add(Rect(a_x, a_y, val_w, val_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(a_x, a_y + val_h - 16, val_w, 16, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(a_x + 8, a_y + val_h - 11, "alias : map[string]int", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))
    d.add(String(a_x + 8, a_y + 17, "• Bản sao map value (alias := registry)", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    d.add(String(a_x + 8, a_y + 6, "• Cùng tham chiếu tới map data chung", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))

    # Vertical arrow between registry and alias (copy map value)
    draw_arrow(d, r_x + 35, r_y, a_x + 35, a_y + val_h, color=COLOR_BLACK, width=0.8, head_size=3.5)
    d.add(String(r_x + 42, (r_y + a_y + val_h) / 2 - 2, "alias := registry (sao chép map value)", fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_MUTED))

    # Right Container: Shared Map Storage (Conceptual Data)
    s_x, s_y, s_w, s_h = 250.0, 30.0, 184.0, 108.0
    d.add(Rect(s_x, s_y, s_w, s_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_BLACK, strokeWidth=0.9))
    d.add(Rect(s_x, s_y + s_h - 18, s_w, 18, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_BLACK, strokeWidth=0.5))
    d.add(String(s_x + 8, s_y + s_h - 13, "DỮ LIỆU MAP DÙNG CHUNG (MAP DATA)", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))

    d.add(String(s_x + 8, s_y + s_h - 32, "Lưu trữ các cặp key → value ở tầng ngữ nghĩa:", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_MUTED))

    # Entry Box: "billing" -> 1 / 2
    d.add(Rect(s_x + 8, s_y + 40, s_w - 16, 30, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_MID, strokeWidth=0.7))
    d.add(String(s_x + 14, s_y + 58, 'Khóa "billing":', fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    d.add(String(s_x + 16, s_y + 46, "1 (ban đầu)", fontName="BookMono", fontSize=8.0, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, s_x + 72, s_y + 49, s_x + 94, s_y + 49, color=COLOR_BLACK, width=0.8, head_size=3.0)
    d.add(String(s_x + 102, s_y + 46, "2 (sau mutate)", fontName="BookMono", fontSize=8.0, fillColor=COLOR_BLACK))

    d.add(String(s_x + 8, s_y + 24, "• alias[\"billing\"]++ cập nhật map data chung", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(s_x + 8, s_y + 11, "• registry[\"billing\"] lập tức đọc thấy giá trị 2", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_DARK))

    # Connecting Arrows from Map Values into Shared Map Data
    draw_arrow(d, r_x + val_w + 4, r_y + val_h / 2, s_x - 4, s_y + s_h - 40, color=COLOR_BLACK, width=1.0, head_size=4.5)
    draw_arrow(d, a_x + val_w + 4, a_y + val_h / 2, s_x - 4, s_y + 40, color=COLOR_BLACK, width=1.0, head_size=4.5)

    # Footnote - 2 lines, strictly fitting width
    d.add(String(12, 17.0, "* Ngữ nghĩa Go: Gán map sao chép map value; cả hai map value cùng tham chiếu đến map data dùng chung.",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))
    d.add(String(12, 7.0, "  Sơ đồ biểu diễn chia sẻ ở tầng ngữ nghĩa ngôn ngữ, không giả định cấu trúc header hay bucket hash table của runtime.",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))

    return d


# ----------------------------------------------------------------------
# 5. Figure 3.5: method-receiver-trace.png (Value receiver vs Pointer receiver)
# ----------------------------------------------------------------------
def build_method_receiver_trace_drawing(w: float = 448.22, h: float = 188.0) -> Drawing:
    """Figure 3.5: Value receiver vs Pointer receiver dispatch semantics."""
    d = Drawing(w, h)

    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))

    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "ĐIỀU PHỐI METHOD RECEIVER // VALUE RECEIVER VS POINTER RECEIVER",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 128, h - 14, "RECEIVER SEMANTICS",
                 fontName="BookMono", fontSize=7.4, fillColor=COLOR_INK_MUTED))

    # Left Container: billing : Service (Addressable variable)
    b_x, b_y, b_w, b_h = 14.0, 32.0, 122.0, 122.0
    d.add(Rect(b_x, b_y, b_w, b_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(b_x, b_y + b_h - 18, b_w, 18, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(b_x + 8, b_y + b_h - 13, "BIẾN GỐC: billing", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))

    d.add(String(b_x + 8, b_y + b_h - 30, "Biến addressable (Service):", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MUTED))

    # Inner state box (Height 52 pt from b_y + 30 to b_y + 82, zero collision)
    d.add(Rect(b_x + 6, b_y + 30, b_w - 12, 52, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_MID, strokeWidth=0.6))
    d.add(String(b_x + 9, b_y + 70, "Trạng thái ban đầu:", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MUTED))
    d.add(String(b_x + 9, b_y + 59, "Healthy: true | Retries: 0", fontName="BookMono", fontSize=6.4, fillColor=COLOR_INK_DARK))
    d.add(String(b_x + 9, b_y + 46, "Sau Record(false):", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(b_x + 9, b_y + 35, "Healthy: false | Retries: 1", fontName="BookMono", fontSize=6.4, fillColor=COLOR_BLACK))

    d.add(String(b_x + 8, b_y + 17, "• billing là biến có địa chỉ", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(b_x + 8, b_y + 7, "• Tự động lấy được &billing", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))

    # Right Containers: width 206 pt, positioned at x = 228.22
    # This leaves 228.22 - 136.0 = 92.22 pt of clear space in the middle!
    r_w = 206.0
    r_x = w - 14.0 - r_w  # 228.22

    # Right Container 1 (Top): Value Receiver func (service Service) Summary()
    v_y, v_h = 96.0, 58.0
    d.add(Rect(r_x, v_y, r_w, v_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(r_x, v_y + v_h - 16, r_w, 16, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(r_x + 8, v_y + v_h - 11, "NHÁNH 1: VALUE RECEIVER (Summary)", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))

    d.add(String(r_x + 8, v_y + 28, "• func (service Service) Summary() string", fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(r_x + 8, v_y + 16, "• Nhận bản sao struct value của billing", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(r_x + 8, v_y + 5, "• Trong ví dụ này, Summary chỉ đọc service.Name", fontName="BookSans", fontSize=7.0, fillColor=COLOR_INK_MUTED))

    # Right Container 2 (Bottom): Pointer Receiver func (service *Service) Record(healthy bool)
    p_y, p_h = 32.0, 58.0
    d.add(Rect(r_x, p_y, r_w, p_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(r_x, p_y + p_h - 16, r_w, 16, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(r_x + 8, p_y + p_h - 11, "NHÁNH 2: POINTER RECEIVER (Record)", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))

    # Exact signature from lecture: func (service *Service) Record(healthy bool)
    # BookMono 6.5 pt has width 179.4 pt, leaving a generous 18.6 pt right margin before r_w=206!
    d.add(String(r_x + 8, p_y + 28, "• func (service *Service) Record(healthy bool)", fontName="BookMono", fontSize=6.5, fillColor=COLOR_INK_DARK))
    d.add(String(r_x + 8, p_y + 16, "• Go tự động lấy địa chỉ: &billing", fontName="BookMono", fontSize=7.0, fillColor=COLOR_INK_MUTED))
    d.add(String(r_x + 8, p_y + 5, "• SỬA POINTEE: Healthy=false, Retries=1", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_BLACK))

    # Middle gap is from 136.0 to 228.22 (width 92.22 pt, mid_gap_x = 182.11)
    mid_gap_x = (b_x + b_w + r_x) / 2  # 182.11

    # Branch 1 (Top) - Arrow at y = 125.0
    draw_arrow(d, b_x + b_w + 4, v_y + v_h / 2, r_x - 4, v_y + v_h / 2, color=COLOR_BLACK, width=1.0, head_size=4.5)
    d.add(String(mid_gap_x, v_y + v_h / 2 + 6, "billing.Summary()", fontName="BookMono", fontSize=6.5, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(mid_gap_x, v_y + v_h / 2 - 8, "(Truyền copy value)", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_MUTED, textAnchor="middle"))

    # Branch 2 (Bottom) - Arrow perfectly horizontal at y = 57.0 (zero collision with text!)
    arrow_y = p_y + p_h / 2 - 4.0  # 57.0
    draw_arrow(d, b_x + b_w + 4, arrow_y, r_x - 4, arrow_y, color=COLOR_BLACK, width=1.0, head_size=4.5)
    # Label 8 pt ABOVE the arrow line (ample 5.16 pt clearance to both left and right boxes!)
    d.add(String(mid_gap_x, arrow_y + 8.0, "billing.Record(false)", fontName="BookMono", fontSize=6.5, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    # Label 9 pt BELOW the arrow line
    d.add(String(mid_gap_x, arrow_y - 9.0, "(Truyền &billing)", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Footnote - 2 lines, strictly fitting width
    d.add(String(12, 17.0, "* Sơ đồ trace ngữ nghĩa: Summary chỉ đọc field trong ví dụ này; value receiver không bảo đảm không có side effect",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))
    d.add(String(12, 7.0, "  (nếu struct chứa reference hoặc thực hiện I/O). Go tự lấy (&billing) khi gọi pointer receiver trên biến addressable.",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))

    return d


# ----------------------------------------------------------------------
# 6. Figure 3.6: interface-contract.png (Structural typing & small contract)
# ----------------------------------------------------------------------
def build_interface_contract_drawing(w: float = 448.22, h: float = 196.0) -> Drawing:
    """Figure 3.6: Implicit interface satisfaction & decoupled contract."""
    d = Drawing(w, h)

    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))

    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "KIỂU CẤU TRÚC (STRUCTURAL TYPING) // HỢP ĐỒNG INTERFACE NHỎ GỌN",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 128, h - 14, "IMPLICIT SATISFACTION",
                 fontName="BookMono", fontSize=7.4, fillColor=COLOR_INK_MUTED))

    # Top Box: Consumer function renderSummary(source SummarySource) string
    c_w, c_h = 260.0, 34.0
    c_x, c_y = (w - c_w) / 2, 134.0
    d.add(Rect(c_x, c_y, c_w, c_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(c_x, c_y + c_h - 14, c_w, 14, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(c_x + 8, c_y + c_h - 10, "BÊN SỬ DỤNG (CONSUMER)", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(c_x + c_w / 2, c_y + 6.0, "func renderSummary(source SummarySource) string",
                 fontName="BookMono", fontSize=7.2, fillColor=COLOR_BLACK, textAnchor="middle"))

    # Center Box: Interface Contract SummarySource
    int_w, int_h = 260.0, 32.0
    int_x, int_y = (w - int_w) / 2, 82.0
    d.add(Rect(int_x, int_y, int_w, int_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    d.add(Rect(int_x, int_y + int_h - 14, int_w, 14, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_BLACK, strokeWidth=0.5))
    d.add(String(int_x + 8, int_y + int_h - 10, "HỢP ĐỒNG INTERFACE TỐI GIẢN", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(int_x + int_w / 2, int_y + 5.0, "type SummarySource interface { Summary() string }",
                 fontName="BookMono", fontSize=7.0, fillColor=COLOR_BLACK, textAnchor="middle"))

    # Arrow from Consumer down to Interface
    draw_arrow(d, w / 2, c_y, w / 2, int_y + int_h, color=COLOR_BLACK, width=1.0, head_size=4.0)
    d.add(String(w / 2 + 8, (c_y + int_y + int_h) / 2 - 2, "phụ thuộc duy nhất vào contract nhỏ", fontName="BookSans", fontSize=7.0, fillColor=COLOR_INK_MUTED))

    # Bottom Concrete Types: Service (Left) and StaticTarget (Right)
    p_w, p_h = 196.0, 32.0
    p1_x, p1_y = 14.0, 26.0
    p2_x, p2_y = w - p_w - 14.0, 26.0

    # Concrete Type 1: Service
    d.add(Rect(p1_x, p1_y, p_w, p_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(p1_x, p1_y + p_h - 14, p_w, 14, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(p1_x + 8, p1_y + p_h - 10, "CONCRETE TYPE 1: Service", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(p1_x + 8, p1_y + 5.0, "func (service Service) Summary() string", fontName="BookMono", fontSize=7.0, fillColor=COLOR_BLACK))

    # Concrete Type 2: StaticTarget
    d.add(Rect(p2_x, p2_y, p_w, p_h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(p2_x, p2_y + p_h - 14, p_w, 14, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(p2_x + 8, p2_y + p_h - 10, "CONCRETE TYPE 2: StaticTarget", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(p2_x + 8, p2_y + 5.0, "func (target StaticTarget) Summary() string", fontName="BookMono", fontSize=7.0, fillColor=COLOR_BLACK))

    # Implicit satisfaction arrows with straight vertical segments and pill labels (Zero collision!)
    a1_x = p1_x + p_w / 2  # 112.0
    a2_x = p2_x + p_w / 2  # 336.22

    # Left arrow
    draw_arrow(d, a1_x, p1_y + p_h, a1_x, int_y, color=COLOR_BLACK, width=1.0, head_size=4.0)
    # Masked pill for label on left arrow
    d.add(Rect(a1_x - 44, (p1_y + p_h + int_y) / 2 - 6, 88, 12, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(a1_x, (p1_y + p_h + int_y) / 2 - 3, "thỏa mãn ngầm định", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Right arrow
    draw_arrow(d, a2_x, p2_y + p_h, a2_x, int_y, color=COLOR_BLACK, width=1.0, head_size=4.0)
    # Masked pill for label on right arrow
    d.add(Rect(a2_x - 44, (p2_y + p_h + int_y) / 2 - 6, 88, 12, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(a2_x, (p2_y + p_h + int_y) / 2 - 3, "thỏa mãn ngầm định", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Footnote - 2 lines, strictly fitting width
    d.add(String(12, 16.0, "* Go structural typing: Thỏa mãn interface hoàn toàn ngầm định tại compile-time qua method set của từng type.",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))
    d.add(String(12, 6.0, "  Không cần từ khóa implements hay quan hệ kế thừa; Service và StaticTarget hoàn toàn độc lập với nhau.",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))

    return d


def export_diagrams_to_png(target_dir: Path | None = None, dpi: int = 300) -> list[Path]:
    """Render all 6 drawings to high-resolution publication PNGs."""
    register_fonts()
    if target_dir is None:
        target_dir = ROOT / "assets/diagrams"
    target_dir.mkdir(parents=True, exist_ok=True)

    diagrams = [
        ("pointer-value-call.png", build_pointer_value_call_drawing()),
        ("pointer-pointee.png", build_pointer_pointee_drawing()),
        ("struct-copy.png", build_struct_copy_drawing()),
        ("map-sharing.png", build_map_sharing_drawing()),
        ("method-receiver-trace.png", build_method_receiver_trace_drawing()),
        ("interface-contract.png", build_interface_contract_drawing()),
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
