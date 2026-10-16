# -*- coding: utf-8 -*-
"""High-precision vector technical diagram for Chapter 8: WaitGroup Ordering Proof.

Visualizes the Happens-Before relationship and completion barrier between Worker
goroutines and Coordinator (Test Runner), demonstrating:
1. Program Order within each goroutine (solid downward arrows).
2. WaitGroup completion barrier: Done() unblocks Wait() (dashed horizontal arrow).
3. Transitive Happens-Before: Add() -> Done() -> Wait() returns -> Snapshot().
4. Mutex data invariant protection: Mutex Lock/Unlock protects slice reports
   from concurrent access, which WaitGroup alone cannot prevent.

Strictly adheres to Master Prompt:
- 100% pure monochrome grayscale (R=G=B everywhere, zero color tint).
- Exact 1:1 publication dimensions: 476.22 x 277.31 pt (Page 163, xref 365).
- High-resolution rendering at 320 DPI.
"""

from __future__ import annotations

import math
from pathlib import Path
import tempfile

import pymupdf
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
from reportlab.graphics import renderPDF

# Root directory
ROOT = Path(__file__).resolve().parents[1]

# Strict pure grayscale palette (R=G=B everywhere, zero color tint)
COLOR_BLACK = colors.HexColor("#000000")
COLOR_INK_DARK = colors.HexColor("#1A1A1A")
COLOR_INK_MID = colors.HexColor("#2E2E2E")
COLOR_INK_MUTED = colors.HexColor("#555555")
COLOR_INK_LIGHT = colors.HexColor("#777777")
COLOR_BORDER = colors.HexColor("#1A1A1A")
COLOR_BORDER_SUBTLE = colors.HexColor("#CCCCCC")
COLOR_BG_HEADER = colors.HexColor("#EAEAEA")
COLOR_BG_CARD = colors.HexColor("#FFFFFF")
COLOR_BG_SUBTLE = colors.HexColor("#F5F5F5")
COLOR_POLICY_BG = colors.HexColor("#F0F0F0")
COLOR_POLICY_BORDER = colors.HexColor("#CCCCCC")
COLOR_POLICY_TEXT = colors.HexColor("#2E2E2E")
COLOR_TAG_BG = colors.HexColor("#EEEEEE")


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
    dashed: bool = False,
    dash_pattern: list[int] | None = None,
):
    """Draw a clean vector line with an arrowhead, supporting dashed lines."""
    line_kwargs = {"strokeColor": color, "strokeWidth": width}
    if dashed:
        line_kwargs["strokeDashArray"] = dash_pattern or [3, 2]
    d.add(Line(x1, y1, x2, y2, **line_kwargs))

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


def build_waitgroup_completion_proof_drawing(
    w: float = 476.22, h: float = 277.31
) -> Drawing:
    """Figure 20: WaitGroup completion barrier vs Mutex data protection proof.

    Publication size: 476.22 x 277.31 pt (Page 163, xref 365).
    """
    d = Drawing(w, h)

    # Outer border
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8))

    # 1. Main Header Strip
    header_h = 20.0
    d.add(Rect(0, h - header_h, w, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    d.add(
        String(
            10.0,
            h - 13.5,
            "ĐƯỜNG CHỨNG MINH THỨ TỰ (ORDERING PROOF) // WAITGROUP & MUTEX",
            fontName="BookSansBold",
            fontSize=7.8,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            w - 10.0,
            h - 13.5,
            "[LAB 08: sync.WaitGroup vs sync.Mutex]",
            fontName="BookSansBold",
            fontSize=6.6,
            fillColor=COLOR_INK_MUTED,
            textAnchor="end",
        )
    )

    # 2. Sub-banner: Invariant Definition
    sub_y = h - 38.0
    sub_h = 15.0
    d.add(Rect(8.0, sub_y, w - 16.0, sub_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(
        String(
            14.0,
            sub_y + 4.5,
            "BẤT BIẾN CỐT LÕI:",
            fontName="BookSansBold",
            fontSize=6.5,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            78.0,
            sub_y + 4.5,
            "Sau khi bên điều phối chờ tất cả worker xong, Snapshot() chứa đúng 1 report của mỗi worker; không rò rỉ slice nội bộ.",
            fontName="BookSans",
            fontSize=6.2,
            fillColor=COLOR_INK_MID,
        )
    )

    # 3. Bottom Technical Footer (Go Memory Model Contracts)
    foot_h = 44.0
    foot_y = 7.0
    d.add(Rect(8.0, foot_y, w - 16.0, foot_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.7, rx=2, ry=2))
    d.add(
        String(
            14.0,
            foot_y + foot_h - 11.0,
            "ĐỐI CHIẾU HỢP ĐỒNG ĐỒNG THỜI // GO MEMORY MODEL & LAB CONTRACTS",
            fontName="BookSansBold",
            fontSize=6.6,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            14.0,
            foot_y + foot_h - 21.5,
            "• sync.WaitGroup: wg.Add(N) phải xảy ra trước go func(). Mỗi Done() giảm counter; lượt Done() cuối cùng mở khóa cho Wait() trả về.",
            fontName="BookSans",
            fontSize=6.1,
            fillColor=COLOR_INK_MID,
        )
    )
    d.add(
        String(
            14.0,
            foot_y + foot_h - 31.5,
            "• sync.Mutex: WaitGroup chỉ tạo mốc hoàn tất, KHÔNG bảo vệ vùng nhớ! Mutex bắt buộc để cô lập slice reports khi nhiều worker cùng ghi.",
            fontName="BookSansBold",
            fontSize=6.1,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            14.0,
            foot_y + foot_h - 40.5,
            "• Cấm dùng time.Sleep: Sleep chỉ đoán thời gian và không tạo quan hệ happens-before; chỉ có WaitGroup và Mutex tạo bằng chứng tất định.",
            fontName="BookSans",
            fontSize=5.9,
            fillColor=COLOR_INK_MUTED,
        )
    )

    # 4. Main Body: Left Column (Worker) vs Right Column (Coordinator)
    # Optimized spacing: col_w = 198.0 pt, central gap = 64.0 pt
    col_w = 198.0
    col_h = 174.0
    body_y = foot_y + foot_h + 5.0  # 7 + 44 + 5 = 56.0 pt
    x_worker = 8.0
    x_coord = w - 8.0 - col_w       # 476.22 - 8 - 198 = 270.22 pt

    # ==================================================================
    # LEFT COLUMN: WORKER GOROUTINE i
    # ==================================================================
    d.add(Rect(x_worker, body_y, col_w, col_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    # Header bar
    d.add(Rect(x_worker, body_y + col_h - 18.0, col_w, 18.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    d.add(Rect(x_worker, body_y + col_h - 18.0, col_w, 4.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(Line(x_worker, body_y + col_h - 18.0, x_worker + col_w, body_y + col_h - 18.0, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    d.add(
        String(
            x_worker + 8.0,
            body_y + col_h - 12.5,
            "WORKER GOROUTINE i (1 .. N)",
            fontName="BookSansBold",
            fontSize=7.2,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            x_worker + col_w - 8.0,
            body_y + col_h - 12.5,
            "[Thực thi song song]",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MUTED,
            textAnchor="end",
        )
    )

    box_w = col_w - 14.0  # 184.0 pt
    w_box_x = x_worker + 7.0

    # Row 1 (Worker): defer wg.Done()
    w1_h = 24.0
    w1_y = body_y + col_h - 45.0  # 56 + 174 - 45 = 185.0
    d.add(Rect(w_box_x, w1_y, box_w, w1_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(w_box_x + 6.0, w1_y + 14.0, "defer wg.Done()", fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 6.0, w1_y + 4.5, "Đăng ký giảm counter của WaitGroup ngay khi vào hàm", fontName="BookSans", fontSize=5.8, fillColor=COLOR_INK_MUTED))

    # Arrow W1 -> W2 (Program Order)
    draw_arrow(d, w_box_x + box_w / 2.0, w1_y, w_box_x + box_w / 2.0, w1_y - 8.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # Row 2 (Worker): registry.Add(report)
    w2_h = 56.0
    w2_y = w1_y - 8.0 - w2_h  # 185 - 8 - 56 = 121.0
    d.add(Rect(w_box_x, w2_y, box_w, w2_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_INK_DARK, strokeWidth=0.8, rx=2, ry=2))
    # Sub-header in W2
    d.add(Rect(w_box_x, w2_y + w2_h - 14.0, box_w, 14.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_INK_DARK, strokeWidth=0.5, rx=2, ry=2))
    d.add(Rect(w_box_x, w2_y + w2_h - 14.0, box_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(w_box_x + 6.0, w2_y + w2_h - 9.5, "registry.Add(report)  // BẢO VỆ BỘ NHỚ", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))

    d.add(String(w_box_x + 6.0, w2_y + 29.0, "1. r.mu.Lock()", fontName="BookMono", fontSize=6.4, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 72.0, w2_y + 29.0, "→ Chiếm quyền độc quyền slice", fontName="BookSans", fontSize=5.8, fillColor=COLOR_INK_MUTED))

    d.add(String(w_box_x + 6.0, w2_y + 17.5, "2. append(r.reports, report)", fontName="BookMono", fontSize=6.3, fillColor=COLOR_INK_DARK))

    d.add(String(w_box_x + 6.0, w2_y + 6.0, "3. r.mu.Unlock()", fontName="BookMono", fontSize=6.4, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 72.0, w2_y + 6.0, "→ Nhả khóa, bảo toàn bất biến", fontName="BookSans", fontSize=5.8, fillColor=COLOR_INK_MUTED))

    # Arrow W2 -> W3 (Program Order)
    draw_arrow(d, w_box_x + box_w / 2.0, w2_y, w_box_x + box_w / 2.0, w2_y - 8.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # Row 3 (Worker): wg.Done() executes at return
    w3_h = 24.0
    w3_y = w2_y - 8.0 - w3_h  # 121 - 8 - 24 = 89.0
    d.add(Rect(w_box_x, w3_y, box_w, w3_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_POLICY_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(w_box_x + 6.0, w3_y + 14.0, "wg.Done() thực thi (tại return)", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 6.0, w3_y + 4.5, "Giảm atomic counter: counter = counter - 1", fontName="BookSans", fontSize=5.8, fillColor=COLOR_INK_MUTED))

    # Arrow W3 -> W4 (Program Order)
    draw_arrow(d, w_box_x + box_w / 2.0, w3_y, w_box_x + box_w / 2.0, w3_y - 7.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # Row 4 (Worker): Worker Goroutine Terminates
    w4_h = 24.0
    w4_y = w3_y - 7.0 - w4_h  # 89 - 7 - 24 = 58.0
    d.add(Rect(w_box_x, w4_y, box_w, w4_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(w_box_x + 6.0, w4_y + 14.0, "Worker goroutine kết thúc", fontName="BookSansBold", fontSize=6.5, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 6.0, w4_y + 4.5, "Hoàn tất vòng đời; giải phóng stack an toàn", fontName="BookSans", fontSize=5.8, fillColor=COLOR_INK_MUTED))

    # ==================================================================
    # RIGHT COLUMN: BÊN ĐIỀU PHỐI / KIỂM THỬ (Coordinator)
    # ==================================================================
    d.add(Rect(x_coord, body_y, col_w, col_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    # Header bar
    d.add(Rect(x_coord, body_y + col_h - 18.0, col_w, 18.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    d.add(Rect(x_coord, body_y + col_h - 18.0, col_w, 4.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(Line(x_coord, body_y + col_h - 18.0, x_coord + col_w, body_y + col_h - 18.0, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    d.add(
        String(
            x_coord + 8.0,
            body_y + col_h - 12.5,
            "BÊN ĐIỀU PHỐI / TEST RUNNER",
            fontName="BookSansBold",
            fontSize=7.2,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            x_coord + col_w - 8.0,
            body_y + col_h - 12.5,
            "[Goroutine chính]",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MUTED,
            textAnchor="end",
        )
    )

    c_box_x = x_coord + 7.0

    # Row 1 (Coordinator): wg.Add(workers)
    c1_y = w1_y  # Exact horizontal alignment: 185.0
    c1_h = w1_h  # 24.0
    d.add(Rect(c_box_x, c1_y, box_w, c1_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(c_box_x + 6.0, c1_y + 14.0, "wg.Add(workers)", fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(c_box_x + 6.0, c1_y + 4.5, "Thiết lập counter = N TRƯỚC KHI spawn các worker", fontName="BookSans", fontSize=5.8, fillColor=COLOR_INK_MUTED))

    # Arrow C1 -> C2 (Program Order + Spawn)
    draw_arrow(d, c_box_x + box_w / 2.0, c1_y, c_box_x + box_w / 2.0, c1_y - 8.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # Row 2 (Coordinator): wg.Wait() [BLOCKING]
    c2_y = w2_y  # Exact horizontal alignment: 121.0
    c2_h = w2_h  # 56.0
    d.add(Rect(c_box_x, c2_y, box_w, c2_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c_box_x, c2_y + c2_h - 14.0, box_w, 14.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=2, ry=2))
    d.add(Rect(c_box_x, c2_y + c2_h - 14.0, box_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(c_box_x + 6.0, c2_y + c2_h - 9.5, "wg.Wait()  // TREO CHỜ COUNTER = 0", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))

    d.add(String(c_box_x + 6.0, c2_y + 29.0, "• Treo thực thi (blocking) khi counter > 0", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c_box_x + 6.0, c2_y + 17.5, "• Không tiêu tốn CPU chờ bận (busy-wait)", fontName="BookSans", fontSize=5.8, fillColor=COLOR_INK_MUTED))
    d.add(String(c_box_x + 6.0, c2_y + 6.0, "• Chờ tất cả N worker lần lượt gọi Done()", fontName="BookSans", fontSize=5.8, fillColor=COLOR_INK_MUTED))

    # Arrow C2 -> C3 (Program Order)
    draw_arrow(d, c_box_x + box_w / 2.0, c2_y, c_box_x + box_w / 2.0, c2_y - 8.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # Row 3 (Coordinator): wg.Wait() unblocks and returns
    c3_y = w3_y  # Exact horizontal alignment: 89.0
    c3_h = w3_h  # 24.0
    d.add(Rect(c_box_x, c3_y, box_w, c3_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_INK_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(c_box_x + 6.0, c3_y + 14.0, "wg.Wait() giải phóng & trả về", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(c_box_x + 6.0, c3_y + 4.5, "Counter đã về 0; toàn bộ N worker đã hoàn tất", fontName="BookSans", fontSize=5.8, fillColor=COLOR_INK_MUTED))

    # Arrow C3 -> C4 (Program Order)
    draw_arrow(d, c_box_x + box_w / 2.0, c3_y, c_box_x + box_w / 2.0, c3_y - 7.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # Row 4 (Coordinator): reports := registry.Snapshot()
    c4_h = 24.0
    c4_y = w4_y  # Exact horizontal alignment: 58.0
    d.add(Rect(c_box_x, c4_y, box_w, c4_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_INK_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(c_box_x + 6.0, c4_y + 14.0, "reports := registry.Snapshot()", fontName="BookMono", fontSize=6.4, fillColor=COLOR_INK_DARK))
    d.add(String(c_box_x + 6.0, c4_y + 4.5, "Khẳng định: len(reports) == workers (Không data race)", fontName="BookSans", fontSize=5.8, fillColor=COLOR_INK_MUTED))

    # ==================================================================
    # CROSS-THREAD SYNCHRONIZATION EDGES & CALLOUTS (Happens-Before Relations)
    # ==================================================================

    # Central boundary metrics
    w_right_border = x_worker + col_w  # 8 + 198 = 206.0 pt
    c_left_border = x_coord            # 270.22 pt
    mid_gap_center = (w_right_border + c_left_border) / 2.0  # 238.11 pt

    # 1. Top Edge: Spawn relationship from C1 to Worker
    spawn_y = c1_y + c1_h / 2.0
    draw_arrow(d, c_box_x, spawn_y, w_box_x + box_w, spawn_y, color=COLOR_INK_LIGHT, width=0.9, head_size=3.5, dashed=True, dash_pattern=[2, 2])
    # Badge for spawn (width 48 pt, fits well within the 64 pt gap)
    d.add(Rect(mid_gap_center - 24.0, spawn_y - 6.5, 48.0, 13.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(mid_gap_center, spawn_y - 2.5, "go worker(i)", fontName="BookMono", fontSize=5.8, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 2. Main Edge: Done() unblocks Wait() (WAITGROUP COMPLETION BARRIER)
    # Perfect horizontal line from W3 right edge to C3 left edge
    mid_barrier_y = w3_y + w3_h / 2.0  # 89 + 12 = 101.0 pt
    w3_right_x = w_box_x + box_w       # 7 + 184 = 191.0 pt
    c3_left_x = c_box_x                # 277.22 pt

    draw_arrow(
        d,
        w3_right_x,
        mid_barrier_y,
        c3_left_x,
        mid_barrier_y,
        color=COLOR_INK_DARK,
        width=1.2,
        head_size=4.5,
        dashed=True,
        dash_pattern=[3, 2],
    )

    # Central Callout Box for WaitGroup Barrier (Floating cleanly in the gap above arrow)
    callout_w = 56.0
    callout_h = 23.0
    callout_x = mid_gap_center - (callout_w / 2.0)  # 238.11 - 28 = 210.11 pt (> 206 pt, < 270 pt!)
    callout_y = mid_barrier_y + 4.0

    d.add(Rect(callout_x, callout_y, callout_w, callout_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_INK_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(mid_gap_center, callout_y + 13.5, "Done() mở khóa", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(mid_gap_center, callout_y + 4.5, "lượt Wait() này", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    return d


def export_diagrams_to_png(target_dir: Path | None = None, dpi: int = 320) -> list[Path]:
    """Render Chapter 8 diagram to high-resolution publication PNG at 320 DPI."""
    register_fonts()
    if target_dir is None:
        target_dir = ROOT / "assets/diagrams"
    target_dir.mkdir(parents=True, exist_ok=True)

    diagrams = [
        ("waitgroup-completion-proof.png", build_waitgroup_completion_proof_drawing()),
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
