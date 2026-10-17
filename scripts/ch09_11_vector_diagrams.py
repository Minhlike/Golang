# -*- coding: utf-8 -*-
"""High-precision publication-grade vector technical diagrams for Chapters 09, 10, 11.

Generates 3 diagrams matching the exact publication dimensions from Golang_Master.pdf:
1. Chapter 09: channel-work-lifecycle.png (476.22 x 253.62 pt, Page 172, xref 384)
   - Worker Pool, Channel Ownership & Lifecycle (labs/part9-workflow-pressure)
2. Chapter 10: performance-evidence-path.png (297.09 x 362.83 pt, Page 199, xref 439)
   - Performance Measurement & Evidence Cycle (labs/part10-measure-first)
3. Chapter 11: http-client-request-path.png (275.97 x 362.83 pt, Page 206, xref 454)
   - HTTP Client Request Lifecycle & Connection Reuse (labs/part11-request-path)

Design Rules:
- 100% pure monochrome grayscale (R=G=B everywhere, zero color tint).
- Minimum font size >= 6.0 pt everywhere.
- 1:1 publication dimensions, rendered at 320 DPI.
- Strict technical fidelity with Go standard library contracts and lab source code.
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

# Project root
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
COLOR_TAG_BG = colors.HexColor("#E0E0E0")


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


# ==============================================================================
# 1. CHAPTER 09: CHANNEL WORK LIFECYCLE (476.22 x 253.62 pt)
# ==============================================================================

def build_channel_work_lifecycle_drawing(w: float = 476.22, h: float = 253.62) -> Drawing:
    """Figure: Worker Pool, Channel Ownership & Lifecycle.

    Publication size: 476.22 x 253.62 pt (Page 172, xref 384).
    Contract: labs/part9-workflow-pressure/fixed/pool.go
    - Dispatcher owns and closes `in` (jobs chan).
    - Workers receive from `in`, execute `work()`, send to `out`, call `defer workersDone.Done()`. Never close channels.
    - Coordinator waits on `workersDone.Wait()` and closes `out` (results chan) exactly once.
    - Consumer ranges over `out` until closed.
    """
    d = Drawing(w, h)

    # Outer border
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8))

    # Header strip
    header_h = 20.0
    d.add(Rect(0, h - header_h, w, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    d.add(
        String(
            10.0,
            h - 13.5,
            "VÒNG ĐỜI VÀ QUYỀN SỞ HỮU KÊNH (CHANNEL OWNERSHIP LIFECYCLE) // WORKER POOL",
            fontName="BookSansBold",
            fontSize=7.8,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            w - 10.0,
            h - 13.5,
            "[LAB 09: labs/part9-workflow-pressure]",
            fontName="BookSansBold",
            fontSize=6.6,
            fillColor=COLOR_INK_MUTED,
            textAnchor="end",
        )
    )

    # Footer policy strip
    footer_h = 24.0
    footer_y = 6.0
    d.add(Rect(6.0, footer_y, w - 12.0, footer_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_POLICY_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(
        String(
            12.0,
            footer_y + 14.5,
            "BẤT BIẾN KỸ THUẬT: Chỉ sender mới được đóng kênh. Không worker nào tự đóng results vì không biết ai là worker cuối.",
            fontName="BookSansBold",
            fontSize=6.1,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            12.0,
            footer_y + 4.5,
            "Mọi thao tác bàn giao (in <- job, out <- result) phải select kèm ctx.Done() để giải phóng goroutine khi consumer dừng nhận.",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MUTED,
        )
    )

    # Main layout geometry
    body_y = footer_y + footer_h + 5.0  # 35.0 pt
    body_h = (h - header_h) - body_y - 6.0  # 192.62 pt

    # Layout: 3 Columns with generous breathing room
    col1_x = 8.0
    col1_w = 98.0

    col2_x = 142.0
    col2_w = 186.0

    col3_x = 346.0
    col3_w = w - col3_x - 8.0  # 122.22 pt

    # ------------------------------------------------------------------
    # COLUMN 1: DISPATCHER (Producer)
    # ------------------------------------------------------------------
    d.add(Rect(col1_x, body_y, col1_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    # Header
    d.add(Rect(col1_x, body_y + body_h - 18.0, col1_w, 18.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    d.add(Rect(col1_x, body_y + body_h - 18.0, col1_w, 4.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(Line(col1_x, body_y + body_h - 18.0, col1_x + col1_w, body_y + body_h - 18.0, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    d.add(String(col1_x + 6.0, body_y + body_h - 12.5, "DISPATCHER", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + col1_w - 6.0, body_y + body_h - 12.5, "[Owner in]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    # Dispatcher content boxes
    d1_x = col1_x + 6.0
    d1_w = col1_w - 12.0

    # Box 1: Ownership of in
    d1_y = body_y + body_h - 50.0
    d.add(Rect(d1_x, d1_y, d1_w, 26.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(d1_x + 5.0, d1_y + 16.0, "in := make(chan Job)", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(d1_x + 5.0, d1_y + 6.0, "Khởi tạo kênh nhận việc", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow D1 -> D2
    draw_arrow(d, d1_x + d1_w / 2.0, d1_y, d1_x + d1_w / 2.0, d1_y - 7.0, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # Box 2: Feed jobs loop with ctx check (5 lines cleanly spaced)
    d2_h = 52.0
    d2_y = d1_y - 7.0 - d2_h
    d.add(Rect(d1_x, d2_y, d1_w, d2_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(d1_x + 5.0, d2_y + 41.0, "for _, job := range jobs", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(d1_x + 5.0, d2_y + 31.5, "  select {", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_MID))
    d.add(String(d1_x + 5.0, d2_y + 22.0, "  case in <- job:", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(d1_x + 5.0, d2_y + 12.5, "  case <-ctx.Done():", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(d1_x + 12.0, d2_y + 3.5, "    return", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow D2 -> D3
    draw_arrow(d, d1_x + d1_w / 2.0, d2_y, d1_x + d1_w / 2.0, d2_y - 7.0, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # Box 3: defer close(in)
    d3_y = body_y + 8.0
    d.add(Rect(d1_x, d3_y, d1_w, 36.0, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(d1_x + 5.0, d3_y + 24.5, "defer close(in)", fontName="BookMono", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(d1_x + 5.0, d3_y + 14.0, "Đóng kênh khi hết job hoặc hủy;", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(d1_x + 5.0, d3_y + 4.5, "báo hiệu worker thoát vòng lặp", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # TRANSFER: Dispatcher -> in channel -> Workers
    # ------------------------------------------------------------------
    chan_jobs_x = col1_x + col1_w + 3.0
    chan_jobs_w = col2_x - chan_jobs_x - 3.0  # 30.0 pt
    chan_jobs_y = d2_y + 10.0
    chan_jobs_h = 32.0

    d.add(Rect(chan_jobs_x, chan_jobs_y, chan_jobs_w, chan_jobs_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(chan_jobs_x + chan_jobs_w / 2.0, chan_jobs_y + 19.5, "in", fontName="BookMono", fontSize=6.8, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(chan_jobs_x + chan_jobs_w / 2.0, chan_jobs_y + 8.5, "chan Job", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="middle"))

    draw_arrow(d, col1_x + col1_w, chan_jobs_y + chan_jobs_h / 2.0, chan_jobs_x, chan_jobs_y + chan_jobs_h / 2.0, color=COLOR_INK_DARK, width=1.0, head_size=3.5)
    draw_arrow(d, chan_jobs_x + chan_jobs_w, chan_jobs_y + chan_jobs_h / 2.0, col2_x, chan_jobs_y + chan_jobs_h / 2.0, color=COLOR_INK_DARK, width=1.0, head_size=3.5)

    # ------------------------------------------------------------------
    # COLUMN 2: WORKERS POOL (N Concurrent Goroutines)
    # ------------------------------------------------------------------
    d.add(Rect(col2_x, body_y, col2_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    # Header
    d.add(Rect(col2_x, body_y + body_h - 18.0, col2_w, 18.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    d.add(Rect(col2_x, body_y + body_h - 18.0, col2_w, 4.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(Line(col2_x, body_y + body_h - 18.0, col2_x + col2_w, body_y + body_h - 18.0, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    d.add(String(col2_x + 6.0, body_y + body_h - 12.5, "WORKERS POOL (N GOROUTINES)", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + col2_w - 6.0, body_y + body_h - 12.5, "[workersDone.Done()]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    w_box_x = col2_x + 6.0
    w_box_w = col2_w - 12.0  # 174.0 pt

    # Worker Row 1: Receive job or exit
    w1_y = body_y + body_h - 52.0
    d.add(Rect(w_box_x, w1_y, w_box_w, 30.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(w_box_x + 5.0, w1_y + 20.0, "case job, ok := <-in:", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 5.0, w1_y + 11.0, "if !ok || ctx.Err() != nil { return }", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(w_box_x + 5.0, w1_y + 3.0, "Thoát sạch khi in đóng hoặc context hết hạn", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow W1 -> W2
    draw_arrow(d, w_box_x + w_box_w / 2.0, w1_y, w_box_x + w_box_w / 2.0, w1_y - 6.0, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # Worker Row 2: Execute work() (2-line wrapped for clean padding)
    w2_y = w1_y - 44.0
    d.add(Rect(w_box_x, w2_y, w_box_w, 38.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(w_box_x + 5.0, w2_y + 28.0, "result := Result{", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 12.0, w2_y + 19.0, "Job: job, Err: work(ctx, job)}", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 5.0, w2_y + 10.5, "if ctx.Err() != nil { return }", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(w_box_x + 5.0, w2_y + 3.0, "Không bàn giao result nếu context bị hủy giữa chừng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow W2 -> W3
    draw_arrow(d, w_box_x + w_box_w / 2.0, w2_y, w_box_x + w_box_w / 2.0, w2_y - 6.0, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # Worker Row 3: Send out or ctx.Done (clean 4-line block)
    w3_y = w2_y - 44.0
    d.add(Rect(w_box_x, w3_y, w_box_w, 38.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(w_box_x + 5.0, w3_y + 28.5, "select {", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_MID))
    d.add(String(w_box_x + 12.0, w3_y + 19.5, "case out <- result:", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 12.0, w3_y + 10.5, "case <-ctx.Done(): return", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(w_box_x + 5.0, w3_y + 3.0, "} // Giải phóng goroutine khi consumer dừng nhận", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Warning Box at bottom of workers
    w_warn_y = body_y + 8.0
    d.add(Rect(w_box_x, w_warn_y, w_box_w, 20.0, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(w_box_x + w_box_w / 2.0, w_warn_y + 11.5, "NGUYÊN TẮC: CẤM worker tự đóng in hoặc out!", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(w_box_x + w_box_w / 2.0, w_warn_y + 3.5, "Không worker nào biết mình là worker cuối cùng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="middle"))

    # ------------------------------------------------------------------
    # COLUMN 3 TOP: COORDINATOR (WaitGroup Completion & Close out)
    # ------------------------------------------------------------------
    c_top_h = 86.0
    c_top_y = body_y + body_h - c_top_h
    d.add(Rect(col3_x, c_top_y, col3_w, c_top_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    # Header
    d.add(Rect(col3_x, c_top_y + c_top_h - 18.0, col3_w, 18.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    d.add(Rect(col3_x, c_top_y + c_top_h - 18.0, col3_w, 4.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(Line(col3_x, c_top_y + c_top_h - 18.0, col3_x + col3_w, c_top_y + c_top_h - 18.0, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    d.add(String(col3_x + 6.0, c_top_y + c_top_h - 12.5, "COORDINATOR", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + col3_w - 6.0, c_top_y + c_top_h - 12.5, "[Owner out]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    c_box_x = col3_x + 6.0
    c_box_w = col3_w - 12.0

    # Step 1: workersDone.Wait()
    cw1_y = c_top_y + c_top_h - 44.0
    d.add(Rect(c_box_x, cw1_y, c_box_w, 22.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(c_box_x + 5.0, cw1_y + 12.5, "workersDone.Wait()", fontName="BookMono", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(c_box_x + 5.0, cw1_y + 4.0, "Treo chờ N worker gọi Done()", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow CW1 -> CW2
    draw_arrow(d, c_box_x + c_box_w / 2.0, cw1_y, c_box_x + c_box_w / 2.0, cw1_y - 6.0, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # Step 2: close(out)
    cw2_y = c_top_y + 6.0
    d.add(Rect(c_box_x, cw2_y, c_box_w, 24.0, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(c_box_x + 5.0, cw2_y + 13.5, "close(out) // DUY NHẤT 1 LẦN", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(c_box_x + 5.0, cw2_y + 4.0, "Đóng kênh an toàn sau mọi worker", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # COLUMN 3 BOTTOM: CONSUMER (Reader)
    # ------------------------------------------------------------------
    c_bot_h = 86.0
    c_bot_y = body_y
    d.add(Rect(col3_x, c_bot_y, col3_w, c_bot_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    # Header
    d.add(Rect(col3_x, c_bot_y + c_bot_h - 18.0, col3_w, 18.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    d.add(Rect(col3_x, c_bot_y + c_bot_h - 18.0, col3_w, 4.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(Line(col3_x, c_bot_y + c_bot_h - 18.0, col3_x + col3_w, c_bot_y + c_bot_h - 18.0, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    d.add(String(col3_x + 6.0, c_bot_y + c_bot_h - 12.5, "CONSUMER (CALLER)", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + col3_w - 6.0, c_bot_y + c_bot_h - 12.5, "[Receiver]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    # Consumer Content
    cb1_y = c_bot_y + c_bot_h - 46.0
    d.add(Rect(c_box_x, cb1_y, c_box_w, 24.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(c_box_x + 5.0, cb1_y + 13.5, "for res := range results", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(c_box_x + 5.0, cb1_y + 4.0, "Nhận kết quả bàn giao từ out", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    cb2_y = c_bot_y + 8.0
    d.add(Rect(c_box_x, cb2_y, c_box_w, 26.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(c_box_x + 5.0, cb2_y + 15.0, "Dừng khi out đóng & cạn đệm", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c_box_x + 5.0, cb2_y + 4.5, "Không can thiệp đóng kênh", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # SYNC & DATA EDGES BETWEEN WORKERS, COORDINATOR & CONSUMER
    # ------------------------------------------------------------------
    # WaitGroup Done signal: Workers -> Coordinator
    wg_edge_y = cw1_y + 11.0
    draw_arrow(d, col2_x + col2_w, wg_edge_y, col3_x, wg_edge_y, color=COLOR_INK_MID, width=1.0, head_size=3.8, dashed=True, dash_pattern=[3, 2])

    # Send Result: Workers -> out channel transfer -> Consumer
    send_edge_y = cb1_y + 12.0
    draw_arrow(d, col2_x + col2_w, send_edge_y, col3_x, send_edge_y, color=COLOR_INK_DARK, width=1.1, head_size=4.0)

    # Edge Badge for out transfer in the 18 pt gap
    d.add(Rect(col2_x + col2_w + 2.0, send_edge_y + 2.0, 14.0, 11.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + col2_w + 9.0, send_edge_y + 4.5, "out", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Coordinator close(out) down to out channel / Consumer
    close_down_x = col3_x + col3_w / 2.0
    draw_arrow(d, close_down_x, cw2_y, close_down_x, c_bot_y + c_bot_h, color=COLOR_INK_DARK, width=1.0, head_size=3.8, dashed=True, dash_pattern=[2, 2])

    return d


# ==============================================================================
# 2. CHAPTER 10: PERFORMANCE EVIDENCE PATH (297.09 x 362.83 pt)
# ==============================================================================

def build_performance_evidence_path_drawing(w: float = 297.09, h: float = 362.83) -> Drawing:
    """Figure: Performance Measurement & Evidence Cycle.

    Publication size: 297.09 x 362.83 pt (Page 199, xref 439).
    Contract: labs/part10-measure-first/fixed/render.go & benchmark_test.go
    - Stage 1: Triệu chứng (Latency cao / Phình bộ nhớ)
    - Stage 2: Bài toán & Workload đại diện (1.000 Reading)
    - Stage 3: Kiểm thử hợp đồng & Benchmark (b.Loop, -benchmem, -count=5)
    - Stage 4: Trích xuất bằng chứng định lượng (sync.pprof, sched.pprof, syscall.pprof)
    - Stage 5: Tối ưu hóa phẫu thuật & Đo đạc đối chứng (strings.Builder vs +=)
    - Feedback Loop: Quay lại Stage 3 đối chứng trên cùng hợp đồng ngữ nghĩa
    """
    d = Drawing(w, h)

    # Outer border
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8))

    # Header strip
    header_h = 20.0
    d.add(Rect(0, h - header_h, w, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    d.add(
        String(
            8.0,
            h - 13.5,
            "CHU TRÌNH ĐIỀU TRA HIỆU NĂNG // EVIDENCE PATH",
            fontName="BookSansBold",
            fontSize=7.6,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            w - 8.0,
            h - 13.5,
            "[LAB 10: labs/part10-measure-first]",
            fontName="BookSansBold",
            fontSize=6.4,
            fillColor=COLOR_INK_MUTED,
            textAnchor="end",
        )
    )

    # Footer callout: Engineering discipline
    footer_h = 34.0
    footer_y = 6.0
    d.add(Rect(6.0, footer_y, w - 12.0, footer_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_POLICY_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(
        String(
            10.0,
            footer_y + 23.5,
            "KỶ LUẬT KỸ THUẬT: Không tối ưu hóa trước khi có số liệu định lượng.",
            fontName="BookSansBold",
            fontSize=6.1,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            10.0,
            footer_y + 13.5,
            "• Thu hẹp giả thuyết từ profile/trace, không võ đoán từ tên API hay cảm tính.",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MID,
        )
    )
    d.add(
        String(
            10.0,
            footer_y + 4.0,
            "• Nếu cải thiện không bù đắp được độ phức tạp, kiên quyết giữ code đơn giản nhất.",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MUTED,
        )
    )

    # Main stage layout
    card_x = 8.0
    card_w = 244.0  # Leaves 297.09 - 252 = 45 pt for return loop
    loop_x = card_x + card_w + 22.0  # 274.0 pt

    body_top = h - header_h - 7.0  # 335.83
    body_bot = footer_y + footer_h + 8.0  # 48.0 pt

    # 5 Stages
    b_h = 43.0
    gap = 13.0

    stages = [
        (
            "1. TRIỆU CHỨNG BAN ĐẦU",
            "Chậm (latency / ns/op cao) hoặc phình bộ nhớ (allocs/B lớn)",
            "Lưu ý: Triệu chứng là điểm bắt đầu, không phải kết luận nguyên nhân.",
            COLOR_BG_CARD,
        ),
        (
            "2. BÀI TOÁN & WORKLOAD ĐẠI DIỆN",
            "Xác định workload thực tế (ví dụ: 1.000 Reading endpoint-0000..0999)",
            "Tách riêng môi trường đo đạc độc lập, không đo lẫn side-effect ngoài lề.",
            COLOR_BG_CARD,
        ),
        (
            "3. KIỂM THỬ HỢP ĐỒNG & BENCHMARK",
            "TestRenderPreservesWireFormat: Cố định hợp đồng ngữ nghĩa đầu ra.",
            "BenchmarkRender (b.Loop, -benchmem -count=5): Lấy baseline định lượng.",
            COLOR_BG_SUBTLE,
        ),
        (
            "4. TRÍCH XUẤT BẰNG CHỨNG (PROFILE & TRACE)",
            "go tool trace -pprof=sync/sched/syscall: Bóc tách độ trễ runtime.",
            "go tool pprof -top: Khoanh vùng chính xác điểm nóng CPU và cấp phát.",
            COLOR_BG_CARD,
        ),
        (
            "5. TỐI ƯU PHẪU THUẬT & ĐỐI CHỨNG",
            "Thực hiện một can thiệp nhỏ (ví dụ: strings.Builder thay cho +=).",
            "Đo đạc lại: Đối chứng số liệu (26 µs vs 1.3 ms; 87 KB vs 10.4 MB).",
            COLOR_POLICY_BG,
        ),
    ]

    box_positions = []
    curr_y = body_top - b_h
    for i, (title, line1, line2, bg_col) in enumerate(stages):
        box_y = curr_y
        box_positions.append((box_y, b_h))

        # Main box
        d.add(Rect(card_x, box_y, card_w, b_h, fillColor=bg_col, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))

        # Step tag badge
        tag_w = 18.0
        d.add(Rect(card_x + 5.0, box_y + b_h - 14.0, tag_w, 10.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(String(card_x + 5.0 + tag_w / 2.0, box_y + b_h - 11.2, f"0{i+1}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

        # Title
        d.add(String(card_x + 28.0, box_y + b_h - 11.0, title, fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))

        # Text lines
        d.add(String(card_x + 8.0, box_y + 15.5, line1, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
        d.add(String(card_x + 8.0, box_y + 5.0, line2, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

        # Downward arrow between boxes
        if i < len(stages) - 1:
            arrow_start_y = box_y
            arrow_end_y = box_y - gap
            arrow_x = card_x + card_w / 2.0
            draw_arrow(d, arrow_x, arrow_start_y, arrow_x, arrow_end_y, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

        curr_y -= (b_h + gap)

    # ------------------------------------------------------------------
    # FEEDBACK RETURN LOOP: Stage 5 -> Stage 3 (Contract & Benchmark)
    # ------------------------------------------------------------------
    s5_y = box_positions[4][0] + b_h / 2.0
    s3_y = box_positions[2][0] + b_h / 2.0

    s5_right_x = card_x + card_w
    d.add(Line(s5_right_x, s5_y, loop_x, s5_y, strokeColor=COLOR_INK_MID, strokeWidth=1.1, strokeDashArray=[3, 2]))
    d.add(Line(loop_x, s5_y, loop_x, s3_y, strokeColor=COLOR_INK_MID, strokeWidth=1.1, strokeDashArray=[3, 2]))
    draw_arrow(d, loop_x, s3_y, s5_right_x, s3_y, color=COLOR_INK_MID, width=1.1, head_size=4.0, dashed=True, dash_pattern=[3, 2])

    # Vertical badge along the loop
    mid_loop_y = (s5_y + s3_y) / 2.0
    d.add(Rect(loop_x - 20.0, mid_loop_y - 13.0, 40.0, 26.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(loop_x, mid_loop_y + 3.5, "ĐỐI CHỨNG", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(loop_x, mid_loop_y - 6.5, "HỢP ĐỒNG", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="middle"))

    return d


# ==============================================================================
# 3. CHAPTER 11: HTTP CLIENT REQUEST PATH (275.97 x 362.83 pt)
# ==============================================================================

def build_http_client_request_path_drawing(w: float = 275.97, h: float = 362.83) -> Drawing:
    """Figure: HTTP Client Request Lifecycle & Connection Reuse.

    Publication size: 275.97 x 362.83 pt (Page 206, xref 454).
    Contract: labs/part11-request-path/fixed/fetch.go, reuse_test.go, trace.go
    - Request initiated with context & deadline.
    - Connection reuse fork:
      * Idle connection available (GotConnInfo.Reused == true) -> skips DNS, TCP, TLS.
      * New connection required (Reused == false) -> DNS resolution -> TCP Dial -> TLS Handshake (ServerName verification).
    - Request transmission & first response byte (GotFirstResponseByte).
    - Response body caller obligation: caller MUST read and call resp.Body.Close() to avoid connection leak!
    """
    d = Drawing(w, h)

    # Outer border
    d.add(Rect(0, 0, w, h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8))

    # Header strip
    header_h = 20.0
    d.add(Rect(0, h - header_h, w, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    d.add(
        String(
            8.0,
            h - 13.5,
            "CÁC CHẶNG HTTP CLIENT REQUEST // net/http",
            fontName="BookSansBold",
            fontSize=6.8,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            w - 8.0,
            h - 13.5,
            "[LAB 11]",
            fontName="BookSansBold",
            fontSize=6.2,
            fillColor=COLOR_INK_MUTED,
            textAnchor="end",
        )
    )

    # Footer callout: Response body obligation
    footer_h = 34.0
    footer_y = 6.0
    d.add(Rect(6.0, footer_y, w - 12.0, footer_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(
        String(
            10.0,
            footer_y + 23.5,
            "HỢP ĐỒNG BẮT BUỘC: defer resp.Body.Close()",
            fontName="BookSansBold",
            fontSize=6.4,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            10.0,
            footer_y + 13.5,
            "• Bên gọi phải đọc hết và đóng Body để trả connection về pool Transport.",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MID,
        )
    )
    d.add(
        String(
            10.0,
            footer_y + 4.0,
            "• Quên đóng Body gây rò rỉ socket/goroutine (connection leak), cạn kiệt socket.",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MUTED,
        )
    )

    # Layout coordinates
    body_top = h - header_h - 7.0  # 335.83 pt
    center_x = w / 2.0  # 137.985 pt

    # 1. Top Card: Request Initiation
    r1_x = 8.0
    r1_w = w - 16.0  # 259.97 pt
    r1_h = 32.0
    r1_y = body_top - r1_h
    d.add(Rect(r1_x, r1_y, r1_w, r1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(r1_x + 6.0, r1_y + 20.5, "1. KHỞI TẠO REQUEST: http.NewRequestWithContext", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(r1_x + 6.0, r1_y + 11.0, "Gắn context, deadline caller và móc nối httptrace.ClientTrace", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(r1_x + 6.0, r1_y + 3.0, "client.Do(req): Bắt đầu chu trình xử lý mạng", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow Down to Connection Decision
    draw_arrow(d, center_x, r1_y, center_x, r1_y - 9.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # 2. Decision Diamond / Fork Box: Check Idle Connection Pool
    fork_y = r1_y - 9.0 - 24.0
    fork_h = 24.0
    fork_w = 200.0
    fork_x = center_x - fork_w / 2.0
    d.add(Rect(fork_x, fork_y, fork_w, fork_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    d.add(String(center_x, fork_y + 13.5, "Transport: Có kết nối rảnh (idle) phù hợp?", fontName="BookSansBold", fontSize=6.4, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(center_x, fork_y + 4.5, "Kiểm tra cache pool của client.Transport", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="middle"))

    # Branch geometry
    branch_top_y = fork_y
    left_branch_x = 8.0
    left_branch_w = 104.0

    right_branch_x = 120.0
    right_branch_w = w - right_branch_x - 8.0  # 147.97 pt

    # Right 3 Steps: DNS -> TCP Dial -> TLS Handshake
    step_a_h = 24.0
    step_a_y = branch_top_y - 15.0 - step_a_h
    step_b_h = 23.0
    step_b_y = step_a_y - 5.0 - step_b_h
    step_c_h = 28.0
    step_c_y = step_b_y - 5.0 - step_c_h

    # Align left box exactly with right branch:
    # Top of left box matches top of Step A (step_a_y + step_a_h)
    # Bottom of left box matches bottom of Step C (step_c_y)
    left_box_top = step_a_y + step_a_h
    left_box_y = step_c_y
    left_box_h = left_box_top - left_box_y  # 80.0 pt

    # Left Branch: Reused == true (Idle connection reused)
    d.add(Line(fork_x + 15.0, branch_top_y, left_branch_x + left_branch_w / 2.0, branch_top_y - 8.0, strokeColor=COLOR_INK_DARK, strokeWidth=1.0))
    draw_arrow(d, left_branch_x + left_branch_w / 2.0, branch_top_y - 8.0, left_branch_x + left_branch_w / 2.0, branch_top_y - 15.0, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Left Badge
    d.add(Rect(left_branch_x + 6.0, branch_top_y - 13.0, 42.0, 11.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(left_branch_x + 27.0, branch_top_y - 9.5, "CÓ (Reused)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Left Box: Reused Connection
    d.add(Rect(left_branch_x, left_box_y, left_branch_w, left_box_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(left_branch_x + 5.0, left_box_y + left_box_h - 12.0, "TÁI SỬ DỤNG KẾT NỐI", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(left_branch_x + 5.0, left_box_y + left_box_h - 23.0, "GotConnInfo.Reused == true", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(left_branch_x + 5.0, left_box_y + 38.0, "• Bỏ qua phân giải DNS", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(left_branch_x + 5.0, left_box_y + 26.0, "• Bỏ qua TCP Dial", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(left_branch_x + 5.0, left_box_y + 14.0, "• Bỏ qua TLS Handshake", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(left_branch_x + 5.0, left_box_y + 4.0, "→ Giảm độ trễ vượt trội", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Right Branch: Reused == false (New connection)
    d.add(Line(fork_x + fork_w - 15.0, branch_top_y, right_branch_x + right_branch_w / 2.0, branch_top_y - 8.0, strokeColor=COLOR_INK_DARK, strokeWidth=1.0))
    draw_arrow(d, right_branch_x + right_branch_w / 2.0, branch_top_y - 8.0, right_branch_x + right_branch_w / 2.0, branch_top_y - 15.0, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Right Badge
    d.add(Rect(right_branch_x + 8.0, branch_top_y - 13.0, 46.0, 11.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(right_branch_x + 31.0, branch_top_y - 9.5, "KHÔNG (Mới)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Step A: DNS
    d.add(Rect(right_branch_x, step_a_y, right_branch_w, step_a_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(right_branch_x + 5.0, step_a_y + 13.5, "2a. Phân giải DNS (net.Resolver.LookupHost)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(right_branch_x + 5.0, step_a_y + 4.5, "DNSStart -> DNSDone: Phân giải tên miền thành IP", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow A -> B
    draw_arrow(d, right_branch_x + right_branch_w / 2.0, step_a_y, right_branch_x + right_branch_w / 2.0, step_a_y - 5.0, color=COLOR_INK_DARK, width=0.9, head_size=3.0)

    # Step B: TCP Dial
    d.add(Rect(right_branch_x, step_b_y, right_branch_w, step_b_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(right_branch_x + 5.0, step_b_y + 13.0, "2b. Khởi tạo TCP Socket (net.Dialer)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(right_branch_x + 5.0, step_b_y + 4.0, "ConnectStart -> ConnectDone (TCP 3-way handshake)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow B -> C
    draw_arrow(d, right_branch_x + right_branch_w / 2.0, step_b_y, right_branch_x + right_branch_w / 2.0, step_b_y - 5.0, color=COLOR_INK_DARK, width=0.9, head_size=3.0)

    # Step C: TLS Handshake
    d.add(Rect(right_branch_x, step_c_y, right_branch_w, step_c_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(right_branch_x + 5.0, step_c_y + 17.5, "2c. TLS Handshake (nếu URL là HTTPS)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(right_branch_x + 5.0, step_c_y + 8.5, "TLSHandshakeStart -> TLSHandshakeDone", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(right_branch_x + 5.0, step_c_y + 2.5, "Xác minh chứng chỉ & hostname (ServerName == SAN)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Convergence from Left and Right branches
    converge_y = left_box_y - 12.0
    # Left arrow down
    draw_arrow(d, left_branch_x + left_branch_w / 2.0, left_box_y, left_branch_x + left_branch_w / 2.0, converge_y + 2.0, color=COLOR_INK_DARK, width=1.0, head_size=3.5)
    # Right arrow down
    draw_arrow(d, right_branch_x + right_branch_w / 2.0, step_c_y, right_branch_x + right_branch_w / 2.0, converge_y + 2.0, color=COLOR_INK_DARK, width=1.0, head_size=3.5)

    # Convergence horizontal bar
    d.add(Line(left_branch_x + left_branch_w / 2.0, converge_y, right_branch_x + right_branch_w / 2.0, converge_y, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    # Down arrow to Step 3
    draw_arrow(d, center_x, converge_y, center_x, converge_y - 8.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # 3. Step 3: Request Transmission & First Byte
    step3_y = converge_y - 8.0 - 32.0
    step3_h = 32.0
    d.add(Rect(r1_x, step3_y, r1_w, step3_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(r1_x + 6.0, step3_y + 21.0, "3. TRUYỀN DỮ LIỆU & CHỜ PHẢN HỒI (HTTP ROUND-TRIP)", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(r1_x + 6.0, step3_y + 11.5, "WroteHeaders -> WroteRequest: Gửi headers và payload request", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(r1_x + 6.0, step3_y + 3.0, "GotFirstResponseByte: Server hoàn tất xử lý và phản hồi byte đầu tiên", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow Down to Step 4
    draw_arrow(d, center_x, step3_y, center_x, step3_y - 8.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # 4. Step 4: Stream Response Body & Lifecycle Close
    step4_y = step3_y - 8.0 - 33.0
    step4_h = 33.0
    d.add(Rect(r1_x, step4_y, r1_w, step4_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(r1_x + 6.0, step4_y + 22.0, "4. ĐỌC DỮ LIỆU & HOÀN TẤT VÒNG ĐỜI RESPONSE", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(r1_x + 6.0, step4_y + 12.0, "Caller nhận *http.Response; đọc dữ liệu qua stream hoặc io.ReadAll()", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(r1_x + 6.0, step4_y + 3.0, "Kiểm tra status code: Trả StatusError nếu status < 200 hoặc >= 300", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow Down to Footer Callout
    draw_arrow(d, center_x, step4_y, center_x, footer_y + footer_h + 1.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    return d


# ==============================================================================
# EXPORT PIPELINE
# ==============================================================================

def export_diagrams_to_png(target_dir: Path | None = None, dpi: int = 320) -> list[Path]:
    """Render Chapters 09, 10, 11 diagrams to high-resolution publication PNGs at 320 DPI."""
    register_fonts()
    if target_dir is None:
        target_dir = ROOT / "assets/diagrams"
    target_dir.mkdir(parents=True, exist_ok=True)

    diagrams = [
        ("channel-work-lifecycle.png", build_channel_work_lifecycle_drawing()),
        ("performance-evidence-path.png", build_performance_evidence_path_drawing()),
        ("http-client-request-path.png", build_http_client_request_path_drawing()),
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
