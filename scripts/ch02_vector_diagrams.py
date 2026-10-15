# -*- coding: utf-8 -*-
"""High-precision vector technical diagrams for Chapter 2.

Follows the Master Prompt's architectural design language:
- Pure monochrome black & white / grayscale palette.
- Embedded fonts: BookSans, BookSansBold, BookMono, BookSerif.
- Strict technical accuracy based on Go specification vs gc runtime.
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
COLOR_INK_MID = colors.HexColor("#333333")
COLOR_INK_MUTED = colors.HexColor("#555555")
COLOR_INK_LIGHT = colors.HexColor("#555555")  # Enhanced contrast for footnotes (no faded gray)
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


def build_array_copy_drawing(w: float = 448.22, h: float = 148.0) -> Drawing:
    """Figure 1: Array Copy Semantics (Independent value semantics)."""
    d = Drawing(w, h)
    
    # Outer frame container
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    
    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "MÔ HÌNH BỘ NHỚ // PHÉP GÁN MẢNG: SAO CHÉP TOÀN BỘ GIÁ TRỊ (VALUE SEMANTICS)",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 118, h - 14, "BẢO ĐẢM TỪ GO SPEC",
                 fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    
    # Left Box: Array a: [3]int
    bx1, by1, bw, bh = 16.0, 48.0, 150.0, 60.0
    d.add(Rect(bx1, by1, bw, bh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(bx1, by1 + bh - 16, bw, 16, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(bx1 + 8, by1 + bh - 12, "Biến a : [3]int", fontName="BookSansBold", fontSize=8.2, fillColor=COLOR_INK_DARK))
    d.add(String(bx1 + bw - 50, by1 + bh - 12, "3 phần tử", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    
    # Elements of a: [10], [20], [30]
    cell_w = (bw - 16) / 3.0
    for i, val in enumerate(["10", "20", "30"]):
        cx = bx1 + 8 + i * cell_w
        cy = by1 + 6
        d.add(Rect(cx, cy, cell_w, 28, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_MID, strokeWidth=0.6))
        d.add(String(cx + 4, cy + 18, f"[{i}]", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
        d.add(String(cx + cell_w / 2, cy + 7, val, fontName="BookMono", fontSize=11.0, fillColor=COLOR_BLACK, textAnchor="middle"))
    
    # Middle: Copy transition arrow & note
    mid_x1, mid_x2 = bx1 + bw + 14, bx1 + bw + 102
    arrow_y = by1 + bh / 2 + 2
    draw_arrow(d, mid_x1, arrow_y, mid_x2, arrow_y, color=COLOR_BLACK, width=1.1, head_size=5.0)
    d.add(String((mid_x1 + mid_x2) / 2, arrow_y + 8, "b := a", fontName="BookMono", fontSize=9.5, fillColor=COLOR_BLACK, textAnchor="middle"))
    d.add(String((mid_x1 + mid_x2) / 2, arrow_y - 11, "Sao chép toàn bộ giá trị", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String((mid_x1 + mid_x2) / 2, arrow_y - 21, "(vùng nhớ độc lập)", fontName="BookSans", fontSize=7.2, fillColor=COLOR_INK_MID, textAnchor="middle"))
    
    # Right Box: Array b: [3]int (after b[0] = 99)
    bx2 = mid_x2 + 14
    d.add(Rect(bx2, by1, bw, bh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(bx2, by1 + bh - 16, bw, 16, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(bx2 + 8, by1 + bh - 12, "Biến b : [3]int (sau b[0] = 99)", fontName="BookSansBold", fontSize=8.2, fillColor=COLOR_INK_DARK))
    
    # Elements of b: [99] (mutated), [20], [30]
    for i, (val, is_mutated) in enumerate([("99", True), ("20", False), ("30", False)]):
        cx = bx2 + 8 + i * cell_w
        cy = by1 + 6
        cell_bg = COLOR_SUBTLE if is_mutated else COLOR_BG_WHITE
        d.add(Rect(cx, cy, cell_w, 28, fillColor=cell_bg, strokeColor=COLOR_INK_DARK if is_mutated else COLOR_INK_MID,
                   strokeWidth=0.9 if is_mutated else 0.6))
        d.add(String(cx + 4, cy + 18, f"[{i}]", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
        d.add(String(cx + cell_w / 2, cy + 7, val, fontName="BookMono", fontSize=11.0, fillColor=COLOR_BLACK, textAnchor="middle"))
    
    # Bottom notes & clean 2-line disclaimer
    d.add(String(bx1 + 2, 32.0, "• a[0] vẫn giữ nguyên giá trị 10 (không bị thay đổi)", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_MID))
    d.add(String(bx2 + 2, 32.0, "• b[0] nhận giá trị mới 99 (vùng nhớ riêng của b)", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))
    d.add(String(12, 16.0, "* Quy chuẩn Go spec: Phép gán array tạo một bản sao giá trị độc lập (value semantics).",
                 fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_MID))
    d.add(String(12, 6.0, "  Kích thước 24B (3 × 8B) minh họa trên amd64; ngôn ngữ bảo đảm ngữ nghĩa giá trị độc lập, không áp đặt sao chép vật lý hay deep copy.",
                 fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_MID))
    
    return d


def build_slice_sharing_drawing(w: float = 448.22, h: float = 196.0) -> Drawing:
    """Figure 2: Slice Sharing Semantics (Descriptor copied, Backing Array shared)."""
    d = Drawing(w, h)
    
    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    
    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "MÔ HÌNH TRIỂN KHAI // SLICE DESCRIPTOR VÀ CHIA SẺ MẢNG NỀN (ALIASING)",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 118, h - 14, "MÔ HÌNH GC 64-BIT",
                 fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    
    # Left Column: Stack Descriptors (a and b) in Vertical Struct Word Layout
    ax, dw = 18.0, 146.0
    row_h = 14.0
    lbl_w = 88.0
    
    # ----------------- Descriptor a (Top) -----------------
    ay = 110.0
    dh = 16.0 + 3 * row_h  # 58.0 pt
    
    d.add(Rect(ax, ay, dw, dh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(ax, ay + dh - 15, dw, 15, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(ax + 6, ay + dh - 11, "Descriptor a : []int", fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(ax + dw - 6, ay + dh - 11, "3 words", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED, textAnchor="end"))
    
    rows_a = [
        ("Data (con trỏ)", "ptr", ay + 2 * row_h),
        ("Len (độ dài)",  "3",   ay + 1 * row_h),
        ("Cap (sức chứa)", "3",   ay + 0 * row_h),
    ]
    for lbl, val, ry in rows_a:
        d.add(Line(ax, ry + row_h, ax + dw, ry + row_h, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
        d.add(Line(ax + lbl_w, ry, ax + lbl_w, ry + row_h, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
        d.add(String(ax + 5, ry + 4.0, lbl, fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
        d.add(String(ax + lbl_w + 6, ry + 4.0, val, fontName="BookMono", fontSize=8.0, fillColor=COLOR_BLACK))
    
    # ----------------- Copy Transition -----------------
    d.add(String(ax + 8, 95.0, "↓ b := a (sao chép descriptor theo giá trị)", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_MID))
    
    # ----------------- Descriptor b (Bottom) -----------------
    by = 34.0
    d.add(Rect(ax, by, dw, dh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(ax, by + dh - 15, dw, 15, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(ax + 6, by + dh - 11, "Descriptor b : []int", fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(ax + dw - 6, by + dh - 11, "3 words", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED, textAnchor="end"))
    
    rows_b = [
        ("Data (con trỏ)", "ptr", by + 2 * row_h),
        ("Len (độ dài)",  "3",   by + 1 * row_h),
        ("Cap (sức chứa)", "3",   by + 0 * row_h),
    ]
    for lbl, val, ry in rows_b:
        d.add(Line(ax, ry + row_h, ax + dw, ry + row_h, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
        d.add(Line(ax + lbl_w, ry, ax + lbl_w, ry + row_h, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
        d.add(String(ax + 5, ry + 4.0, lbl, fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
        d.add(String(ax + lbl_w + 6, ry + 4.0, val, fontName="BookMono", fontSize=8.0, fillColor=COLOR_BLACK))
    
    # ----------------- Right Column: Shared Backing Array -----------------
    sx, sy, sw, sh = 224.0, 70.0, 208.0, 68.0
    d.add(Rect(sx, sy, sw, sh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_BLACK, strokeWidth=0.9))
    d.add(Rect(sx, sy + sh - 16, sw, 16, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_BLACK, strokeWidth=0.5))
    d.add(String(sx + 8, sy + sh - 12, "Mảng nền dùng chung (Backing Array)", fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(sx + sw - 8, sy + sh - 12, "3 phần tử int", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED, textAnchor="end"))
    
    # 3 Cells: [0]=99 (mutated), [1]=20, [2]=30
    scell_w = (sw - 16) / 3.0
    for i, (val, is_mut) in enumerate([("99", True), ("20", False), ("30", False)]):
        cx = sx + 8 + i * scell_w
        cy = sy + 8
        cbg = COLOR_SUBTLE if is_mut else COLOR_BG_WHITE
        d.add(Rect(cx, cy, scell_w, 30, fillColor=cbg, strokeColor=COLOR_INK_DARK if is_mut else COLOR_INK_MID,
                   strokeWidth=0.9 if is_mut else 0.5))
        d.add(String(cx + 4, cy + 20, f"[{i}]", fontName="BookMono", fontSize=7.0, fillColor=COLOR_INK_MUTED))
        d.add(String(cx + scell_w / 2, cy + 8, val, fontName="BookMono", fontSize=11.0, fillColor=COLOR_BLACK, textAnchor="middle"))
    
    # ----------------- Clean Orthogonal Pointer Vectors -----------------
    src_a_x = ax + dw
    src_a_y = ay + 2 * row_h + row_h * 0.5
    
    src_b_x = ax + dw
    src_b_y = by + 2 * row_h + row_h * 0.5
    
    d.add(Circle(src_a_x, src_a_y, 2.0, fillColor=COLOR_BLACK, strokeColor=COLOR_BLACK))
    d.add(Circle(src_b_x, src_b_y, 2.0, fillColor=COLOR_BLACK, strokeColor=COLOR_BLACK))
    
    tgt_a_y = sy + sh - 26.0
    tgt_b_y = sy + 20.0
    mid_x = 194.0
    
    # Route A
    d.add(Line(src_a_x, src_a_y, mid_x, src_a_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    d.add(Line(mid_x, src_a_y, mid_x, tgt_a_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    draw_arrow(d, mid_x, tgt_a_y, sx, tgt_a_y, color=COLOR_BLACK, width=1.0, head_size=4.5)
    
    # Route B
    d.add(Line(src_b_x, src_b_y, mid_x, src_b_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    d.add(Line(mid_x, src_b_y, mid_x, tgt_b_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    draw_arrow(d, mid_x, tgt_b_y, sx, tgt_b_y, color=COLOR_BLACK, width=1.0, head_size=4.5)
    
    # Mutation annotations
    d.add(String(sx + 4, 46.0, "▲ b[0] = 99 ghi trực tiếp vào mảng nền dùng chung qua Data", fontName="BookSansBold", fontSize=7.3, fillColor=COLOR_INK_DARK))
    d.add(String(sx + 4, 34.0, "▲ a[0] quan sát thấy 99 vì cùng tham chiếu mảng nền này", fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_MID))
    
    # 2-line disclaimer
    d.add(String(12, 17.0, "* Quy chuẩn Go spec: Slice là cửa sổ tham chiếu mảng nền; cấu trúc Data/Len/Cap là mô hình triển khai của gc 64-bit.",
                 fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_MID))
    d.add(String(12, 6.0, "  Phép gán b := a sao chép descriptor theo giá trị; cả hai descriptor cùng tham chiếu chung một backing array.",
                 fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_MID))
    
    return d


def build_slice_window_drawing(w: float = 448.22, h: float = 195.0) -> Drawing:
    """Figure 3: Slice Window Geometry (Length vs Capacity)."""
    d = Drawing(w, h)
    
    # Outer container
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    
    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "HÌNH HỌC CỬA SỔ SLICE // ĐỘ DÀI (LEN) VÀ SỨC CHỨA (CAP): x := base[1:3]",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 118, h - 14, "QUY CHUẨN GO SPEC",
                 fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    
    base_x = 34.11
    base_y = 72.0
    cell_w = 76.0
    cell_h = 32.0
    
    # Clear distinction: slice variable base: []int vs underlying 5-element backing array
    d.add(String(base_x, 158.0, "Biến lát cắt gốc: base : []int  (Biểu thức gán: x := base[1:3])",
                 fontName="BookSansBold", fontSize=8.2, fillColor=COLOR_INK_DARK))
    d.add(String(base_x, 145.0, "Mảng nền bên dưới gồm 5 phần tử int:",
                 fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))
    
    # Pointer marker to index 1: x.Data
    ptr_x = base_x + 1 * cell_w + cell_w / 2
    ptr_top_y = 138.0
    ptr_bottom_y = base_y + cell_h + 1
    draw_arrow(d, ptr_x, ptr_top_y, ptr_x, ptr_bottom_y, color=COLOR_BLACK, width=1.1, head_size=4.5)
    d.add(String(ptr_x + 6, 120.0, "x.Data trỏ tới base[1]", fontName="BookMono", fontSize=7.4, fillColor=COLOR_BLACK))
    
    values = ["10", "20", "30", "40", "50"]
    for i, val in enumerate(values):
        cx = base_x + i * cell_w
        is_in_len = (1 <= i <= 2)
        is_in_cap = (1 <= i <= 4)
        cbg = COLOR_SUBTLE if is_in_len else (COLOR_BG_WHITE if is_in_cap else COLOR_BG_BLOCK)
        d.add(Rect(cx, base_y, cell_w, cell_h, fillColor=cbg, strokeColor=COLOR_INK_DARK, strokeWidth=0.7))
        d.add(String(cx + 6, base_y + cell_h - 10, f"base[{i}]", fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
        d.add(String(cx + cell_w / 2, base_y + 8, val, fontName="BookMono", fontSize=11.0, fillColor=COLOR_BLACK, textAnchor="middle"))
    
    # Length Bracket: Covers indices 1 to 2 (width 2 * cell_w)
    len_x1 = base_x + 1 * cell_w
    len_x2 = base_x + 3 * cell_w
    len_y = 56.0
    d.add(Line(len_x1, len_y, len_x2, len_y, strokeColor=COLOR_BLACK, strokeWidth=1.2))
    d.add(Line(len_x1, len_y - 3, len_x1, len_y + 3, strokeColor=COLOR_BLACK, strokeWidth=1.2))
    d.add(Line(len_x2, len_y - 3, len_x2, len_y + 3, strokeColor=COLOR_BLACK, strokeWidth=1.2))
    d.add(String((len_x1 + len_x2) / 2, len_y - 10, "len(x) = 2  (Cửa sổ quan sát trực tiếp: base[1:3] gồm [20, 30])",
                 fontName="BookSansBold", fontSize=7.6, fillColor=COLOR_BLACK, textAnchor="middle"))
    
    # Capacity Bracket: Covers indices 1 to 4 (width 4 * cell_w)
    cap_x1 = base_x + 1 * cell_w
    cap_x2 = base_x + 5 * cell_w
    cap_y = 30.0
    d.add(Line(cap_x1, cap_y, cap_x2, cap_y, strokeColor=COLOR_INK_MID, strokeWidth=0.9))
    d.add(Line(cap_x1, cap_y - 3, cap_x1, cap_y + 3, strokeColor=COLOR_INK_MID, strokeWidth=0.9))
    d.add(Line(cap_x2, cap_y - 3, cap_x2, cap_y + 3, strokeColor=COLOR_INK_MID, strokeWidth=0.9))
    d.add(String((cap_x1 + cap_x2) / 2, cap_y - 10, "cap(x) = 4  (Sức chứa tối đa từ vị trí bắt đầu đến hết mảng nền: [20, 30, 40, 50])",
                 fontName="BookSans", fontSize=7.6, fillColor=COLOR_INK_MID, textAnchor="middle"))
    
    d.add(String(12, 6.0, "* Quy chuẩn Go spec: base[1:3] xác định len = 3 - 1 = 2; cap(x) = 4 tính từ vị trí bắt đầu (index 1) đến hết mảng nền.",
                 fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_MID))
    
    return d


def build_append_storage_drawing(w: float = 448.22, h: float = 220.0) -> Drawing:
    """Figure 4: Append Mechanics & Capacity Branching (Language spec vs runtime)."""
    d = Drawing(w, h)
    
    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    
    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "ĐẶC TẢ NGỮ NGHĨA append // ĐIỂM QUYẾT ĐỊNH THEO SỨC CHỨA (CAPACITY)",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 118, h - 14, "NGÔN NGỮ & RUNTIME",
                 fontName="BookMono", fontSize=7.2, fillColor=COLOR_INK_MUTED))
    
    # Decision Node at Top Center (Uniform condition across diagram)
    dec_w, dec_h = 290.0, 22.0
    dec_x, dec_y = (w - dec_w) / 2, 168.0
    d.add(Rect(dec_x, dec_y, dec_w, dec_h, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_BLACK, strokeWidth=0.8))
    d.add(String(w / 2, dec_y + 7.0, "append(s, ...): Kiểm tra len(s) + số_phần_tử_thêm <= cap(s) ?",
                 fontName="BookSansBold", fontSize=7.8, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    
    # Branch 1 (Left Box): Đủ sức chứa (len(s) + số_phần_tử_thêm <= cap(s))
    b1_x, b1_w = 15.0, 200.0
    by, bh = 26.0, 98.0
    d.add(Rect(b1_x, by, b1_w, bh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(b1_x, by + bh - 16, b1_w, 16, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(b1_x + 8, by + bh - 12, "NHÁNH 1: ĐỦ SỨC CHỨA", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))
    d.add(String(b1_x + b1_w - 8, by + bh - 12, "Tái sử dụng mảng", fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_MUTED, textAnchor="end"))
    
    d.add(String(b1_x + 8, by + bh - 27, "• Ngôn ngữ: Tái sử dụng mảng nền hiện tại", fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_DARK))
    d.add(String(b1_x + 8, by + bh - 39, "• Thao tác: Ghi đè phần tử mới vào index len(s)", fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_DARK))
    d.add(String(b1_x + 8, by + bh - 51, "• Kết quả: Trả về descriptor mới có len tăng", fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_DARK))
    
    # Visual mini array for Branch 1
    d.add(Rect(b1_x + 8, by + 16, b1_w - 16, 20, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_MID, strokeWidth=0.5))
    d.add(String(b1_x + 12, by + 21, "old: [99 20]  |  s = append: [99 20 30]", fontName="BookMono", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(b1_x + 8, by + 5, "[HỆ QUẢ] Chia sẻ mảng nền (aliasing)", fontName="BookSansBold", fontSize=7.3, fillColor=COLOR_INK_DARK))
    
    # Branch 2 (Right Box): Vượt sức chứa (len(s) + số_phần_tử_thêm > cap(s))
    b2_x = 233.0
    d.add(Rect(b2_x, by, b1_w, bh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(b2_x, by + bh - 16, b1_w, 16, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(b2_x + 8, by + bh - 12, "NHÁNH 2: VƯỢT SỨC CHỨA", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))
    d.add(String(b2_x + b1_w - 8, by + bh - 12, "Cấp mảng mới", fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_MUTED, textAnchor="end"))
    
    d.add(String(b2_x + 8, by + bh - 27, "• Ngôn ngữ: Cấp mảng mới và sao chép phần tử", fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_DARK))
    d.add(String(b2_x + 8, by + bh - 39, "• Runtime: growslice chọn capacity và phân bổ", fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_DARK))
    d.add(String(b2_x + 8, by + bh - 51, "• Kết quả: Trả về descriptor trỏ tới mảng mới", fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_DARK))
    
    # Visual mini array for Branch 2
    d.add(Rect(b2_x + 8, by + 16, b1_w - 16, 20, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_MID, strokeWidth=0.5))
    d.add(String(b2_x + 12, by + 21, "old trỏ mảng cũ  |  grown trỏ mảng NỀN MỚI", fontName="BookMono", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(b2_x + 8, by + 5, "[HỆ QUẢ] Phân tách mảng nền (không đổi mảng cũ)", fontName="BookSansBold", fontSize=7.3, fillColor=COLOR_INK_DARK))
    
    # Standard Flowchart Tree Routing (Zero Collision):
    cx = w / 2  # 224.11
    target1_x = b1_x + b1_w / 2  # 115.0
    target2_x = b2_x + b1_w / 2  # 333.0
    h_route_y = 150.0
    
    # Vertical drop from decision box
    d.add(Line(cx, dec_y, cx, h_route_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    
    # Horizontal distribution arms
    d.add(Line(cx, h_route_y, target1_x, h_route_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    d.add(Line(cx, h_route_y, target2_x, h_route_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    
    # Drop arrows into branch boxes
    draw_arrow(d, target1_x, h_route_y, target1_x, by + bh, color=COLOR_BLACK, width=1.0, head_size=4.5)
    draw_arrow(d, target2_x, h_route_y, target2_x, by + bh, color=COLOR_BLACK, width=1.0, head_size=4.5)
    
    # Branch decision conditions placed centered directly over respective boxes (68pt gap between them)
    d.add(String(target1_x, 154.0, "[Có] len(s) + số_phần_tử_thêm <= cap(s)",
                 fontName="BookSansBold", fontSize=7.1, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(target2_x, 154.0, "[Không] len(s) + số_phần_tử_thêm > cap(s)",
                 fontName="BookSansBold", fontSize=7.1, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    
    # 2-line bottom note on shallow vs deep copy
    d.add(String(12, 15.0, "* Kịch bản phân nhánh append: Nhánh 2 tách biệt mảng nền độc lập cho phần tử kiểu giá trị cơ bản.",
                 fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_MID))
    d.add(String(12, 5.0, "  Nếu phần tử chứa con trỏ hoặc struct lồng tham chiếu, đây là shallow copy mảng nền, không phải deep copy dữ liệu đích.",
                 fontName="BookSans", fontSize=7.3, fillColor=COLOR_INK_MID))
    
    return d


def export_diagrams_to_png(target_dir: Path | None = None, dpi: int = 300) -> list[Path]:
    """Render all 4 drawings to high-resolution publication PNGs."""
    register_fonts()
    if target_dir is None:
        target_dir = ROOT / "assets/diagrams"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    diagrams = [
        ("array-copy.png", build_array_copy_drawing()),
        ("slice-sharing.png", build_slice_sharing_drawing()),
        ("slice-window.png", build_slice_window_drawing()),
        ("append-storage.png", build_append_storage_drawing()),
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
