# -*- coding: utf-8 -*-
"""High-precision vector technical diagrams and architectural illustrations for Chapter 2.

Follows the Master Prompt's architectural design language:
- Pure monochrome black & white / grayscale palette.
- Embedded fonts: BookSans, BookSansBold, BookMono, BookSerif.
- Manual of Section / Technical specification styling.
- Zero raster artifacts at 1000% zoom.
"""

from __future__ import annotations

import math
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

# Palette definitions matching book_style
COLOR_BLACK = colors.HexColor("#000000")
COLOR_INK_DARK = colors.HexColor("#1A1A1A")
COLOR_INK_MID = colors.HexColor("#444444")
COLOR_INK_MUTED = colors.HexColor("#666666")
COLOR_INK_LIGHT = colors.HexColor("#888888")
COLOR_HAIRLINE = colors.HexColor("#D4D4D4")
COLOR_SUBTLE = colors.HexColor("#EAEAEA")
COLOR_BG_BLOCK = colors.HexColor("#F6F7F9")
COLOR_BG_WHITE = colors.HexColor("#FFFFFF")
COLOR_BG_ACCENT = colors.HexColor("#EEEEEE")


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


def build_array_copy_drawing(w: float = 476.22, h: float = 125.0) -> Drawing:
    """Figure 1: Array Copy Semantics (Deep bitwise copy of elements)."""
    d = Drawing(w, h)
    
    # Outer frame container
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    
    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "ĐẶC TẢ BỘ NHỚ // PHÉP GÁN MẢNG: SAO CHÉP TOÀN BỘ GIÁ TRỊ (BITWISE COPY)",
                 fontName="BookSansBold", fontSize=8.5, fillColor=COLOR_INK_DARK))
    d.add(String(w - 115, h - 14, "BẢO ĐẢM TỪ GO SPEC",
                 fontName="BookMono", fontSize=7.5, fillColor=COLOR_INK_MUTED))
    
    # Left Box: Array a: [3]int
    bx1, by1, bw, bh = 24.0, 32.0, 155.0, 60.0
    d.add(Rect(bx1, by1, bw, bh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(bx1, by1 + bh - 16, bw, 16, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(bx1 + 8, by1 + bh - 12, "Biến a : [3]int (24B)", fontName="BookSansBold", fontSize=8.5, fillColor=COLOR_INK_DARK))
    d.add(String(bx1 + bw - 48, by1 + bh - 12, "@ 0x1040*", fontName="BookMono", fontSize=7.5, fillColor=COLOR_INK_MUTED))
    
    # Elements of a: [10], [20], [30]
    cell_w = (bw - 16) / 3.0
    for i, val in enumerate(["10", "20", "30"]):
        cx = bx1 + 8 + i * cell_w
        cy = by1 + 6
        d.add(Rect(cx, cy, cell_w, 28, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_MID, strokeWidth=0.6))
        d.add(String(cx + 4, cy + 18, f"[{i}]", fontName="BookMono", fontSize=7.0, fillColor=COLOR_INK_MUTED))
        d.add(String(cx + cell_w / 2 - 6, cy + 6, val, fontName="BookMono", fontSize=10.5, fillColor=COLOR_BLACK))
    
    # Middle: Copy transition arrow & note
    mid_x1, mid_x2 = bx1 + bw + 14, bx1 + bw + 95
    arrow_y = by1 + bh / 2 + 4
    draw_arrow(d, mid_x1, arrow_y, mid_x2, arrow_y, color=COLOR_BLACK, width=1.2, head_size=5.5)
    d.add(String(mid_x1 + 10, arrow_y + 8, "b := a", fontName="BookMono", fontSize=10.0, fillColor=COLOR_BLACK))
    d.add(String(mid_x1 + 2, arrow_y - 12, "Sao chép 24B", fontName="BookSans", fontSize=8.0, fillColor=COLOR_INK_MUTED))
    d.add(String(mid_x1 - 2, arrow_y - 22, "từng phần tử", fontName="BookSans", fontSize=8.0, fillColor=COLOR_INK_MUTED))
    
    # Right Box: Array b: [3]int
    bx2 = mid_x2 + 14
    d.add(Rect(bx2, by1, bw, bh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(bx2, by1 + bh - 16, bw, 16, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(bx2 + 8, by1 + bh - 12, "Biến b : [3]int (24B)", fontName="BookSansBold", fontSize=8.5, fillColor=COLOR_INK_DARK))
    d.add(String(bx2 + bw - 48, by1 + bh - 12, "@ 0x1060*", fontName="BookMono", fontSize=7.5, fillColor=COLOR_INK_MUTED))
    
    # Elements of b: [99], [20], [30]
    for i, (val, is_mutated) in enumerate([("99", True), ("20", False), ("30", False)]):
        cx = bx2 + 8 + i * cell_w
        cy = by1 + 6
        cell_bg = COLOR_SUBTLE if is_mutated else COLOR_BG_WHITE
        d.add(Rect(cx, cy, cell_w, 28, fillColor=cell_bg, strokeColor=COLOR_INK_DARK if is_mutated else COLOR_INK_MID,
                   strokeWidth=0.9 if is_mutated else 0.6))
        d.add(String(cx + 4, cy + 18, f"[{i}]", fontName="BookMono", fontSize=7.0, fillColor=COLOR_INK_MUTED))
        d.add(String(cx + cell_w / 2 - 6, cy + 6, val, fontName="BookMono", fontSize=10.5, fillColor=COLOR_BLACK))
    
    # Bottom callout tags & disclaimer
    d.add(String(bx1 + 4, 18, "• a[0] giữ nguyên 10; b[0] = 99 chỉ biến đổi ô nhớ độc lập của biến b", fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MID))
    d.add(String(bx1 + 4, 8, "* Kịch bản minh họa: Địa chỉ (@ 0x1040, @ 0x1060) mang tính ước lệ; vị trí vật lý (Stack/Heap) do escape analysis quyết định tùy ngữ cảnh.", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_LIGHT))
    
    return d


def build_slice_sharing_drawing(w: float = 476.22, h: float = 165.0) -> Drawing:
    """Figure 2: Slice Sharing Semantics (Descriptor copied, Backing Array shared).
    
    Uses vertical struct word layout: Data pointer at +0x00 emerges cleanly from the right
    edge directly into the shared backing array without intersecting any fields.
    """
    d = Drawing(w, h)
    
    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    
    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "MÔ HÌNH TRIỂN KHAI // SLICE DESCRIPTOR VÀ MẢNG NỀN DÙNG CHUNG (ALIASING)",
                 fontName="BookSansBold", fontSize=8.5, fillColor=COLOR_INK_DARK))
    d.add(String(w - 120, h - 14, "MÔ HÌNH TRIỂN KHAI // GC 64-BIT",
                 fontName="BookMono", fontSize=7.0, fillColor=COLOR_INK_MUTED))
    
    # Left Column: Stack Descriptors (a and b) in Vertical Struct Word Layout
    ax, dw = 18.0, 160.0
    row_h = 13.5
    lbl_w = 95.0
    val_w = dw - lbl_w
    
    # ----------------- Descriptor a (Top) -----------------
    ay = 84.0
    dh = 14.0 + 3 * row_h  # 54.5 pt
    
    # Outer container for a
    d.add(Rect(ax, ay, dw, dh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    # Header bar for a
    d.add(Rect(ax, ay + dh - 14, dw, 14, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(ax + 6, ay + dh - 10, "Descriptor a : []int (runtime struct 24B)", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    
    # 3 vertical rows for a (Data at top, Len, Cap)
    rows_a = [
        ("+0x00 Data (pointer)", "0x8040", ay + 2 * row_h),
        ("+0x08 Len  (int)",     "3",      ay + 1 * row_h),
        ("+0x10 Cap  (int)",     "3",      ay + 0 * row_h),
    ]
    for lbl, val, ry in rows_a:
        d.add(Line(ax, ry + row_h, ax + dw, ry + row_h, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
        d.add(Line(ax + lbl_w, ry, ax + lbl_w, ry + row_h, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
        d.add(String(ax + 5, ry + 3.5, lbl, fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_MUTED))
        d.add(String(ax + lbl_w + 6, ry + 3.5, val, fontName="BookMono", fontSize=8.0, fillColor=COLOR_BLACK))
    
    # ----------------- Copy Transition -----------------
    d.add(String(ax + 12, 73.0, "↓ b := a (Sao chép bitwise 24-byte descriptor)", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_MUTED))
    
    # ----------------- Descriptor b (Bottom) -----------------
    by = 16.0
    # Outer container for b
    d.add(Rect(ax, by, dw, dh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    # Header bar for b
    d.add(Rect(ax, by + dh - 14, dw, 14, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(ax + 6, by + dh - 10, "Descriptor b : []int (runtime struct 24B)", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    
    # 3 vertical rows for b
    rows_b = [
        ("+0x00 Data (pointer)", "0x8040", by + 2 * row_h),
        ("+0x08 Len  (int)",     "3",      by + 1 * row_h),
        ("+0x10 Cap  (int)",     "3",      by + 0 * row_h),
    ]
    for lbl, val, ry in rows_b:
        d.add(Line(ax, ry + row_h, ax + dw, ry + row_h, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
        d.add(Line(ax + lbl_w, ry, ax + lbl_w, ry + row_h, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
        d.add(String(ax + 5, ry + 3.5, lbl, fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_MUTED))
        d.add(String(ax + lbl_w + 6, ry + 3.5, val, fontName="BookMono", fontSize=8.0, fillColor=COLOR_BLACK))
    
    # ----------------- Right Column: Shared Backing Array -----------------
    sx, sy, sw, sh = 255.0, 52.0, 205.0, 66.0
    d.add(Rect(sx, sy, sw, sh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    d.add(Rect(sx, sy + sh - 18, sw, 18, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_BLACK, strokeWidth=0.5))
    d.add(String(sx + 8, sy + sh - 13, "Mảng nền (Backing Array)", fontName="BookSansBold", fontSize=8.5, fillColor=COLOR_INK_DARK))
    d.add(String(sx + sw - 8, sy + sh - 13, "@ 0x8040*", fontName="BookMono", fontSize=7.5, fillColor=COLOR_INK_MUTED, textAnchor="end"))
    
    # 3 Cells: [0]=99 (mutated), [1]=20, [2]=30
    scell_w = (sw - 20) / 3.0
    for i, (val, is_mut) in enumerate([("99", True), ("20", False), ("30", False)]):
        cx = sx + 10 + i * scell_w
        cy = sy + 8
        cbg = COLOR_SUBTLE if is_mut else COLOR_BG_WHITE
        d.add(Rect(cx, cy, scell_w, 30, fillColor=cbg, strokeColor=COLOR_INK_DARK if is_mut else COLOR_INK_MID,
                   strokeWidth=0.9 if is_mut else 0.5))
        d.add(String(cx + 4, cy + 20, f"index [{i}]", fontName="BookMono", fontSize=6.5, fillColor=COLOR_INK_MUTED))
        d.add(String(cx + scell_w / 2 - 6, cy + 7, val, fontName="BookMono", fontSize=11.0, fillColor=COLOR_BLACK))
    
    # ----------------- Clean Orthogonal Pointer Vectors -----------------
    src_a_x = ax + dw
    src_a_y = ay + 2 * row_h + row_h * 0.5  # middle of a's Data row
    
    src_b_x = ax + dw
    src_b_y = by + 2 * row_h + row_h * 0.5  # middle of b's Data row
    
    # Circles at source
    d.add(Circle(src_a_x, src_a_y, 2.0, fillColor=COLOR_BLACK, strokeColor=COLOR_BLACK))
    d.add(Circle(src_b_x, src_b_y, 2.0, fillColor=COLOR_BLACK, strokeColor=COLOR_BLACK))
    
    # Target points at Backing Array's index [0] cell entry:
    tgt_a_y = sy + sh - 28.0
    tgt_b_y = sy + 18.0
    
    # Route A
    mid_x = 218.0
    d.add(Line(src_a_x, src_a_y, mid_x, src_a_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    d.add(Line(mid_x, src_a_y, mid_x, tgt_a_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    draw_arrow(d, mid_x, tgt_a_y, sx, tgt_a_y, color=COLOR_BLACK, width=1.0, head_size=4.5)
    
    # Route B
    d.add(Line(src_b_x, src_b_y, mid_x, src_b_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    d.add(Line(mid_x, src_b_y, mid_x, tgt_b_y, strokeColor=COLOR_BLACK, strokeWidth=1.0))
    draw_arrow(d, mid_x, tgt_b_y, sx, tgt_b_y, color=COLOR_BLACK, width=1.0, head_size=4.5)
    
    # Mutation annotation & disclaimer
    d.add(String(sx + 8, 28.0, "▲ b[0] = 99 ghi trực tiếp vào mảng nền tại địa chỉ 0x8040", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))
    d.add(String(sx + 8, 17.0, "▲ a[0] quan sát thấy 99 vì cùng trỏ tới mảng nền chia sẻ", fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_MUTED))
    d.add(String(12, 6.0, "* Kịch bản minh họa: Cấu trúc 3 word là mô hình triển khai của gc 64-bit (Data pointer, len, cap). Go spec bảo đảm ngữ nghĩa cửa sổ; vị trí Stack/Heap do escape analysis quyết định.",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_LIGHT))
    
    return d


def build_slice_window_drawing(w: float = 476.22, h: float = 145.0) -> Drawing:
    """Figure 3: Slice Window Geometry (Length vs Capacity)."""
    d = Drawing(w, h)
    
    # Outer container
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    
    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "ĐẶC TẢ HÌNH HỌC CỬA SỔ // SLICE WINDOW: LENGTH VS CAPACITY (x := base[1:3])",
                 fontName="BookSansBold", fontSize=8.5, fillColor=COLOR_INK_DARK))
    d.add(String(w - 115, h - 14, "QUY CHUẨN GO SPEC",
                 fontName="BookMono", fontSize=7.5, fillColor=COLOR_INK_MUTED))
    
    base_x = 42.0
    base_y = 52.0
    cell_w = 78.0
    cell_h = 30.0
    
    # Backing array label above array (placed safely above pointer)
    d.add(String(base_x, base_y + cell_h + 22, "Mảng nền gốc base: [5]int",
                 fontName="BookSansBold", fontSize=8.5, fillColor=COLOR_INK_DARK))
    
    # Pointer marker to index 1: x.Data
    ptr_x = base_x + 1 * cell_w + cell_w / 2
    ptr_y = base_y + cell_h + 14
    draw_arrow(d, ptr_x, ptr_y, ptr_x, base_y + cell_h + 1, color=COLOR_BLACK, width=1.1, head_size=4.5)
    d.add(String(ptr_x + 8, ptr_y - 3, "x trỏ tới phần tử chỉ số [1]", fontName="BookMono", fontSize=7.5, fillColor=COLOR_BLACK))
    
    values = ["10", "20", "30", "40", "50"]
    for i, val in enumerate(values):
        cx = base_x + i * cell_w
        is_in_len = (1 <= i <= 2)
        is_in_cap = (1 <= i <= 4)
        cbg = COLOR_SUBTLE if is_in_len else (COLOR_BG_WHITE if is_in_cap else COLOR_BG_BLOCK)
        d.add(Rect(cx, base_y, cell_w, cell_h, fillColor=cbg, strokeColor=COLOR_INK_DARK, strokeWidth=0.7))
        d.add(String(cx + 6, base_y + cell_h - 10, f"base[{i}]", fontName="BookMono", fontSize=7.0, fillColor=COLOR_INK_MUTED))
        d.add(String(cx + cell_w / 2 - 7, base_y + 8, val, fontName="BookMono", fontSize=11.5, fillColor=COLOR_BLACK))
    
    # Length Bracket: Covers indices 1 to 2 (width 2 * cell_w)
    len_x1 = base_x + 1 * cell_w
    len_x2 = base_x + 3 * cell_w
    len_y = base_y - 11
    d.add(Line(len_x1, len_y, len_x2, len_y, strokeColor=COLOR_BLACK, strokeWidth=1.3))
    d.add(Line(len_x1, len_y - 3, len_x1, len_y + 3, strokeColor=COLOR_BLACK, strokeWidth=1.3))
    d.add(Line(len_x2, len_y - 3, len_x2, len_y + 3, strokeColor=COLOR_BLACK, strokeWidth=1.3))
    d.add(String((len_x1 + len_x2) / 2, len_y - 9, "len(x) = 2 (Cửa sổ quan sát trực tiếp: [20, 30])",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_BLACK, textAnchor="middle"))
    
    # Capacity Bracket: Covers indices 1 to 4 (width 4 * cell_w)
    cap_x1 = base_x + 1 * cell_w
    cap_x2 = base_x + 5 * cell_w
    cap_y = base_y - 29
    d.add(Line(cap_x1, cap_y, cap_x2, cap_y, strokeColor=COLOR_INK_MID, strokeWidth=0.9))
    d.add(Line(cap_x1, cap_y - 3, cap_x1, cap_y + 3, strokeColor=COLOR_INK_MID, strokeWidth=0.9))
    d.add(Line(cap_x2, cap_y - 3, cap_x2, cap_y + 3, strokeColor=COLOR_INK_MID, strokeWidth=0.9))
    d.add(String((cap_x1 + cap_x2) / 2, cap_y - 9, "cap(x) = 4 (Phạm vi mở rộng tối đa mà không cần cấp phát lại)",
                 fontName="BookSans", fontSize=8.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
    d.add(String(12, 5.0, "* Quy chuẩn Go spec: [1:3] định nghĩa len = 2; khoảng mở rộng tới cuối mảng nền cho cap = 4.",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_LIGHT))
    
    return d


def build_append_storage_drawing(w: float = 476.22, h: float = 145.0) -> Drawing:
    """Figure 4: Append Mechanics & Capacity Branching (Language spec vs runtime)."""
    d = Drawing(w, h)
    
    # Outer frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    
    # Header strip
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_HAIRLINE, strokeWidth=0.5))
    d.add(String(12, h - 14, "ĐẶC TẢ NGỮ NGHĨA append // PHÂN NHÁNH THEO SỨC CHỨA (CAPACITY)",
                 fontName="BookSansBold", fontSize=8.5, fillColor=COLOR_INK_DARK))
    d.add(String(w - 130, h - 14, "NGÔN NGỮ & RUNTIME",
                 fontName="BookMono", fontSize=7.5, fillColor=COLOR_INK_MUTED))
    
    # Branch 1 (Left): Đủ sức chứa (len + 1 <= cap)
    b1_x, b1_w = 16.0, 215.0
    by, bh = 18.0, 98.0
    d.add(Rect(b1_x, by, b1_w, bh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(b1_x, by + bh - 16, b1_w, 16, fillColor=COLOR_BG_ACCENT, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(b1_x + 8, by + bh - 12, "NHÁNH 1: ĐỦ SỨC CHỨA (len + 1 <= cap)", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))
    
    d.add(String(b1_x + 10, by + bh - 28, "• Ngôn ngữ: Tái sử dụng mảng nền hiện tại", fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_DARK))
    d.add(String(b1_x + 10, by + bh - 39, "• Ghi đè phần tử mới vào vị trí index len của mảng nền", fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_DARK))
    d.add(String(b1_x + 10, by + bh - 50, "• Trả về descriptor mới có len = len + 1", fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_DARK))
    
    # Visual mini array for Branch A
    d.add(Rect(b1_x + 10, by + 12, 195, 24, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_MID, strokeWidth=0.5))
    d.add(String(b1_x + 14, by + 19, "old: [99 20]  |  s = append: [99 20 30]", fontName="BookMono", fontSize=7.0, fillColor=COLOR_BLACK))
    d.add(String(b1_x + 10, by + 3, "[HỆ QUẢ] old và s cùng tham chiếu mảng nền chung!", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))
    
    # Branch 2 (Right): Vượt sức chứa (len + 1 > cap)
    b2_x = 245.0
    d.add(Rect(b2_x, by, b1_w, bh, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_DARK, strokeWidth=0.8))
    d.add(Rect(b2_x, by + bh - 16, b1_w, 16, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_INK_DARK, strokeWidth=0.5))
    d.add(String(b2_x + 8, by + bh - 12, "NHÁNH 2: VƯỢT SỨC CHỨA (len + 1 > cap)", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))
    
    d.add(String(b2_x + 10, by + bh - 28, "• Ngôn ngữ: Cấp phát mảng nền mới đủ lớn và sao chép", fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_DARK))
    d.add(String(b2_x + 10, by + bh - 39, "• Runtime gc: growslice tính toán kích thước khối nhớ", fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_DARK))
    d.add(String(b2_x + 10, by + bh - 50, "• Trả về descriptor mới trỏ tới mảng nền vừa cấp phát", fontName="BookSans", fontSize=7.5, fillColor=COLOR_INK_DARK))
    
    # Visual mini array for Branch B
    d.add(Rect(b2_x + 10, by + 12, 195, 24, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_MID, strokeWidth=0.5))
    d.add(String(b2_x + 14, by + 19, "old trỏ mảng cũ  |  grown trỏ mảng MỚI", fontName="BookMono", fontSize=7.0, fillColor=COLOR_BLACK))
    d.add(String(b2_x + 10, by + 3, "[HỆ QUẢ] grown độc lập hoàn toàn, không đổi old", fontName="BookSansBold", fontSize=7.5, fillColor=COLOR_INK_DARK))
    
    # Bottom note
    d.add(String(16, 5.0, "* Kịch bản phân nhánh append: Ngôn ngữ đảm bảo tính độc lập khi vượt sức chứa; runtime gc cấp phát mảng mới qua growslice.", fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_LIGHT))
    
    return d


def build_isometric_memory_section_drawing(w: float = 476.22, h: float = 175.0) -> Drawing:
    """Figure 5: Artistic Non-Technical Object: 3D Axonometric Memory Cutaway.
    
    Follows Rule 7 & Master Prompt: Manual of Section style (Peter Eisenman).
    Axonometric cross-section showing Stack Frame plane (24B slice descriptor)
    descending into Heap Memory Volume (contiguous backing array cells).
    """
    d = Drawing(w, h)
    
    # Outer architectural frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_BLACK, strokeWidth=0.8))
    
    # Title bar
    d.add(Rect(0, h - 20, w, 20, fillColor=COLOR_INK_DARK, strokeColor=COLOR_BLACK, strokeWidth=0.5))
    d.add(String(12, h - 14, "LÁT CẮT KHÔNG GIAN BỘ NHỚ // MÔ HÌNH PHÂN TẦNG LOGIC",
                 fontName="BookSansBold", fontSize=8.0, fillColor=COLOR_BG_WHITE))
    d.add(String(w - 110, h - 14, "MINH HỌA KIẾN TRÚC",
                 fontName="BookMono", fontSize=7.5, fillColor=COLOR_HAIRLINE))
    
    # Axonometric projection: Level 1: DESCRIPTOR PLANE (Top-Left)
    ox, oy = 35.0, 105.0
    dx, dy = 135.0, 30.0
    dz_x, dz_y = 40.0, 24.0
    
    # Stack Top Surface
    p_stack_top = [
        ox, oy,
        ox + dx, oy,
        ox + dx + dz_x, oy + dz_y,
        ox + dz_x, oy + dz_y,
    ]
    d.add(Polygon(p_stack_top, fillColor=COLOR_SUBTLE, strokeColor=COLOR_BLACK, strokeWidth=0.7))
    
    # Stack Front Face (thickness)
    p_stack_front = [
        ox, oy - 14,
        ox + dx, oy - 14,
        ox + dx, oy,
        ox, oy,
    ]
    d.add(Polygon(p_stack_front, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_BLACK, strokeWidth=0.7))
    
    # 3-word descriptor partitions
    w3 = dx / 3.0
    for i in range(1, 3):
        lx = ox + i * w3
        d.add(Line(lx, oy, lx + dz_x, oy + dz_y, strokeColor=COLOR_INK_MID, strokeWidth=0.5))
    
    # Labels on Stack Descriptor fields (placed in top half of parallelogram)
    d.add(String(ox + 5, oy + 11, "+0x00 Data", fontName="BookMono", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(ox + w3 + 5, oy + 11, "+0x08 Len", fontName="BookMono", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(ox + 2 * w3 + 5, oy + 11, "+0x10 Cap", fontName="BookMono", fontSize=6.8, fillColor=COLOR_BLACK))
    d.add(String(ox + 6, oy - 10, "Khung bộ nhớ cục bộ // Slice Descriptor (3 words)",
                 fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    
    # Level 2: HEAP VOLUME (Bottom-Right)
    hx, hy = 230.0, 24.0
    h_dx = 195.0
    h_dz_x, h_dz_y = 35.0, 20.0
    h_depth = 26.0
    
    # Heap Top Face
    p_heap_top = [
        hx, hy + h_depth,
        hx + h_dx, hy + h_depth,
        hx + h_dx + h_dz_x, hy + h_depth + h_dz_y,
        hx + h_dz_x, hy + h_depth + h_dz_y,
    ]
    d.add(Polygon(p_heap_top, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_BLACK, strokeWidth=0.8))
    
    # Heap Front Face
    p_heap_front = [
        hx, hy,
        hx + h_dx, hy,
        hx + h_dx, hy + h_depth,
        hx, hy + h_depth,
    ]
    d.add(Polygon(p_heap_front, fillColor=COLOR_BG_BLOCK, strokeColor=COLOR_BLACK, strokeWidth=0.8))
    
    # Heap Right Side Face
    p_heap_side = [
        hx + h_dx, hy,
        hx + h_dx + h_dz_x, hy + h_dz_y,
        hx + h_dx + h_dz_x, hy + h_depth + h_dz_y,
        hx + h_dx, hy + h_depth,
    ]
    d.add(Polygon(p_heap_side, fillColor=COLOR_SUBTLE, strokeColor=COLOR_BLACK, strokeWidth=0.7))
    
    # Backing Array Cell partitions on Heap Top Face (4 cells)
    hc_w = h_dx / 4.0
    for i in range(1, 4):
        cx = hx + i * hc_w
        d.add(Line(cx, hy + h_depth, cx + h_dz_x, hy + h_depth + h_dz_y, strokeColor=COLOR_INK_MID, strokeWidth=0.5))
        d.add(Line(cx, hy, cx, hy + h_depth, strokeColor=COLOR_INK_MID, strokeWidth=0.5))
    
    # Labels for Heap Cells (positioned cleanly in front face and top)
    for i in range(4):
        cx = hx + i * hc_w + 14
        d.add(String(cx, hy + h_depth + 4, f"[{i}]", fontName="BookMono", fontSize=6.5, fillColor=COLOR_INK_DARK))
        d.add(String(cx, hy + 8, "8B", fontName="BookMono", fontSize=6.5, fillColor=COLOR_INK_MUTED))
    
    d.add(String(hx + 8, hy - 10, "Vùng nhớ mảng nền // Backing Array (Liên tiếp theo word 8B)",
                 fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    
    # Connecting Axonometric Pointer Vector: Data (bottom-front edge) -> Heap origin
    src_px = ox + w3 * 0.5
    src_py = oy - 14
    tgt_px = hx + 10
    tgt_py = hy + h_depth + 8
    
    d.add(Circle(src_px, src_py, 2.2, fillColor=COLOR_BLACK, strokeColor=COLOR_BLACK))
    draw_arrow(d, src_px, src_py, tgt_px, tgt_py, color=COLOR_BLACK, width=1.3, head_size=5.5)
    
    # Coordinate callout badge placed safely in open space above the vector
    badge_x = 205.0
    badge_y = 100.0
    d.add(Rect(badge_x, badge_y, 135, 15, fillColor=COLOR_BG_WHITE, strokeColor=COLOR_INK_MID, strokeWidth=0.5))
    d.add(String(badge_x + 67.5, badge_y + 4, "con trỏ mảng (array pointer)", fontName="BookMono", fontSize=6.5, fillColor=COLOR_BLACK, textAnchor="middle"))
    
    # Technical plane indicators
    d.add(String(14, oy + 4, "DESCRIPTOR", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(w - 38, hy + 10, "STORAGE", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    
    # Bottom note on escape analysis
    d.add(String(12, 6.0, "* Kịch bản minh họa phân tầng logic: Vị trí vật lý (Stack/Heap) phụ thuộc escape analysis; không mặc định mọi slice đều phân bổ giống nhau.",
                 fontName="BookSans", fontSize=6.8, fillColor=COLOR_INK_LIGHT))
    
    return d
