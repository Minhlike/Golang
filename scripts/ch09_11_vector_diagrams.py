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
    - Dispatcher owns in (chan Job); registers defer close(in) at start, executes when return.
    - Workers receive from in, execute work(), send to out, call defer workersDone.Done(). Never close channels.
    - Coordinator waits on workersDone.Wait() and closes out (results chan) exactly once.
    - Consumer ranges over out until closed.
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
    footer_h = 26.0
    footer_y = 6.0
    d.add(Rect(6.0, footer_y, w - 12.0, footer_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_POLICY_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(
        String(
            12.0,
            footer_y + 15.5,
            "BẤT BIẾN KỸ THUẬT: Chỉ sender mới được đóng kênh. Dispatcher đóng in; Coordinator đóng out sau WaitGroup.",
            fontName="BookSansBold",
            fontSize=6.1,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            12.0,
            footer_y + 5.0,
            "defer close(in) đăng ký lúc khởi chạy nhưng chỉ thực thi khi dispatcher return; worker thoát vòng lặp khi in đóng sạch.",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MUTED,
        )
    )

    # Main layout geometry
    body_y = footer_y + footer_h + 5.0  # 37.0 pt
    body_h = (h - header_h) - body_y - 6.0  # 190.62 pt

    # 3 Columns Layout
    col1_x = 8.0
    col1_w = 112.0

    col2_x = 148.0
    col2_w = 176.0

    col3_x = 342.0
    col3_w = w - col3_x - 8.0  # 126.22 pt

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

    d1_x = col1_x + 6.0
    d1_w = col1_w - 12.0  # 100.0 pt

    # Box 1: Ownership of in
    d1_y = body_y + body_h - 48.0
    d.add(Rect(d1_x, d1_y, d1_w, 24.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(d1_x + 5.0, d1_y + 14.5, "in := make(chan Job)", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(d1_x + 5.0, d1_y + 4.5, "Khởi tạo kênh nhận việc unbuffered", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow D1 -> D2
    draw_arrow(d, d1_x + d1_w / 2.0, d1_y, d1_x + d1_w / 2.0, d1_y - 6.0, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # Box 2: Feed jobs loop with ctx check (Full valid Go syntax with {})
    d2_h = 58.0
    d2_y = d1_y - 6.0 - d2_h
    d.add(Rect(d1_x, d2_y, d1_w, d2_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(d1_x + 5.0, d2_y + 47.0, "for _, job := range jobs {", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(d1_x + 9.0, d2_y + 38.0, "select {", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(d1_x + 9.0, d2_y + 29.0, "case in <- job:", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(d1_x + 9.0, d2_y + 20.0, "case <-ctx.Done():", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(d1_x + 16.0, d2_y + 11.5, "return", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(d1_x + 9.0, d2_y + 3.0, "}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrow D2 -> D3
    draw_arrow(d, d1_x + d1_w / 2.0, d2_y, d1_x + d1_w / 2.0, d2_y - 6.0, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # Box 3: defer close(in) - explicit registration vs execution timing
    d3_h = 44.0
    d3_y = body_y + 8.0
    d.add(Rect(d1_x, d3_y, d1_w, d3_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(d1_x + 5.0, d3_y + 31.5, "defer close(in)", fontName="BookMono", fontSize=6.4, fillColor=COLOR_INK_DARK))
    d.add(String(d1_x + 5.0, d3_y + 21.0, "• Đăng ký: khi bắt đầu goroutine", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(d1_x + 5.0, d3_y + 11.5, "• Thực thi: khi return (hết việc/hủy)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(d1_x + 5.0, d3_y + 3.0, "• Tác dụng: báo worker thoát lặp", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # TRANSFER: Dispatcher -> in channel -> Workers
    # ------------------------------------------------------------------
    chan_jobs_x = col1_x + col1_w + 3.0
    chan_jobs_w = col2_x - chan_jobs_x - 3.0  # 30.0 pt
    chan_jobs_y = d2_y + 13.0
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
    w_box_w = col2_w - 12.0  # 164.0 pt

    # Worker Row 1: Receive job or exit
    w1_y = body_y + body_h - 52.0
    d.add(Rect(w_box_x, w1_y, w_box_w, 29.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(w_box_x + 5.0, w1_y + 19.0, "case job, ok := <-in:", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 5.0, w1_y + 10.5, "if !ok || ctx.Err() != nil { return }", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(w_box_x + 5.0, w1_y + 2.5, "Thoát sạch khi in đóng hoặc context hết hạn", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow W1 -> W2
    draw_arrow(d, w_box_x + w_box_w / 2.0, w1_y, w_box_x + w_box_w / 2.0, w1_y - 6.0, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # Worker Row 2: Execute work() (2-line wrapped with full valid Go syntax)
    w2_y = w1_y - 44.0
    d.add(Rect(w_box_x, w2_y, w_box_w, 38.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(w_box_x + 5.0, w2_y + 28.0, "result := Result{", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 12.0, w2_y + 19.0, "Job: job, Err: work(ctx, job),", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(w_box_x + 5.0, w2_y + 10.5, "} ; if ctx.Err() != nil { return }", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(w_box_x + 5.0, w2_y + 3.0, "Không bàn giao result nếu context bị hủy giữa chừng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow W2 -> W3
    draw_arrow(d, w_box_x + w_box_w / 2.0, w2_y, w_box_x + w_box_w / 2.0, w2_y - 6.0, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # Worker Row 3: Send out or ctx.Done (full valid Go select block)
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
    - Stage 1: Triệu chứng ban đầu (Latency cao / Phình bộ nhớ)
    - Stage 2: Bài toán & Workload đại diện (1.000 Reading endpoint-0000..0999)
    - Stage 3: Hợp đồng & Benchmark cơ sở (b.Loop, -benchmem, -count=6 đồng bộ bài giảng)
    - Stage 4: Trích xuất từng hồ sơ riêng biệt từ trace.out (sync.pprof, sched.pprof, syscall.pprof)
    - Stage 5: Tối ưu phẫu thuật & Đối chứng thực nghiệm (strings.Builder vs +=; bằng chứng đại diện)
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
    footer_h = 36.0
    footer_y = 6.0
    d.add(Rect(6.0, footer_y, w - 12.0, footer_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_POLICY_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(
        String(
            10.0,
            footer_y + 25.0,
            "KỶ LUẬT: Số liệu đo đạc chỉ đại diện cho workload & môi trường thử nghiệm cụ thể.",
            fontName="BookSansBold",
            fontSize=6.1,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            10.0,
            footer_y + 14.5,
            "• Không phỏng đoán; số liệu benchmark không phải cam kết hiệu năng phổ quát.",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MID,
        )
    )
    d.add(
        String(
            10.0,
            footer_y + 4.5,
            "• Nếu cải thiện không bù đắp được độ phức tạp mã nguồn, kiên quyết giữ code đơn giản nhất.",
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
    body_bot = footer_y + footer_h + 8.0  # 50.0 pt

    # 5 Stages with precise heights to fit rich technical content
    b_h1 = 38.0
    b_h2 = 38.0
    b_h3 = 38.0
    b_h4 = 56.0  # Expanded for 3 distinct pprof commands
    b_h5 = 58.0  # Expanded for baseline vs fixed metrics & notice

    stage_heights = [b_h1, b_h2, b_h3, b_h4, b_h5]
    total_boxes_h = sum(stage_heights)
    available_h = body_top - body_bot
    gap = (available_h - total_boxes_h) / 4.0  # Exactly calculated gap

    # Stage 1: Triệu chứng ban đầu
    y1 = body_top - b_h1
    d.add(Rect(card_x, y1, card_w, b_h1, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 5.0, y1 + b_h1 - 13.0, 18.0, 9.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 14.0, y1 + b_h1 - 10.5, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 28.0, y1 + b_h1 - 10.5, "1. TRIỆU CHỨNG BAN ĐẦU", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 8.0, y1 + 14.0, "Chậm (latency / ns/op cao) hoặc phình bộ nhớ (allocs/bytes lớn)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, y1 + 4.5, "Lưu ý: Triệu chứng là điểm bắt đầu, không phải kết luận nguyên nhân.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, card_x + card_w / 2.0, y1, card_x + card_w / 2.0, y1 - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Stage 2: Bài toán & Workload đại diện
    y2 = y1 - gap - b_h2
    d.add(Rect(card_x, y2, card_w, b_h2, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 5.0, y2 + b_h2 - 13.0, 18.0, 9.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 14.0, y2 + b_h2 - 10.5, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 28.0, y2 + b_h2 - 10.5, "2. BÀI TOÁN & WORKLOAD ĐẠI DIỆN", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 8.0, y2 + 14.0, "Xác định workload thực tế: 1.000 Reading (endpoint-0000..0999)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, y2 + 4.5, "Tách riêng môi trường đo đạc độc lập, không lẫn side-effect ngoài lề.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, card_x + card_w / 2.0, y2, card_x + card_w / 2.0, y2 - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Stage 3: Hợp đồng & Benchmark cơ sở (Đồng bộ -count=6 với bài giảng)
    y3 = y2 - gap - b_h3
    d.add(Rect(card_x, y3, card_w, b_h3, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 5.0, y3 + b_h3 - 13.0, 18.0, 9.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 14.0, y3 + b_h3 - 10.5, "03", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 28.0, y3 + b_h3 - 10.5, "3. KIỂM THỬ HỢP ĐỒNG & BENCHMARK CƠ SỞ", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 8.0, y3 + 14.0, "TestRenderPreservesWireFormat: Cố định hợp đồng định dạng đầu ra.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, y3 + 4.5, "BenchmarkRender (b.Loop, -benchmem -count=6): Lấy baseline định lượng.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, card_x + card_w / 2.0, y3, card_x + card_w / 2.0, y3 - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Stage 4: Trích xuất từng hồ sơ riêng biệt từ trace.out
    y4 = y3 - gap - b_h4
    d.add(Rect(card_x, y4, card_w, b_h4, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 5.0, y4 + b_h4 - 13.0, 18.0, 9.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 14.0, y4 + b_h4 - 10.5, "04", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 28.0, y4 + b_h4 - 10.5, "4. TRÍCH XUẤT HỒ SƠ PPROF TỪ TRACE", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 8.0, y4 + 32.5, "• go tool trace -pprof=sync trace.out > sync.pprof   (khóa/channel)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, y4 + 22.5, "• go tool trace -pprof=sched trace.out > sched.pprof (điều phối P/G)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, y4 + 12.5, "• go tool trace -pprof=syscall trace.out > syscall.pprof (tầng nhân)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, y4 + 3.0, "Phân tích: go tool pprof -top sync.pprof để xác định chính xác điểm trễ.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, card_x + card_w / 2.0, y4, card_x + card_w / 2.0, y4 - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Stage 5: Tối ưu phẫu thuật & Đối chứng thực nghiệm
    y5 = y4 - gap - b_h5
    d.add(Rect(card_x, y5, card_w, b_h5, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 5.0, y5 + b_h5 - 13.0, 18.0, 9.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 14.0, y5 + b_h5 - 10.5, "05", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 28.0, y5 + b_h5 - 10.5, "5. TỐI ƯU PHẪU THUẬT & ĐỐI CHỨNG THỰC NGHIỆM", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 8.0, y5 + 34.5, "Can thiệp nhỏ: strings.Builder & FormatInt thay thế toán tử +=", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, y5 + 24.5, "Workload 1.000 Reading, i5-12500H, Go 1.27.1, 6 lần chạy (-count=6):", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, y5 + 14.5, "• baseline (+=): 1.306–3.394 ms/op; ~10.4 MB/op; 1.900 allocs/op", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 8.0, y5 + 5.0, "• fixed (Builder): 26.442–89.994 µs/op; ~87.6 KB/op; 917 allocs/op", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # ------------------------------------------------------------------
    # FEEDBACK RETURN LOOP: Stage 5 -> Stage 3 (Contract & Benchmark)
    # ------------------------------------------------------------------
    s5_y = y5 + b_h5 / 2.0
    s3_y = y3 + b_h3 / 2.0

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
    - Request initiated with context & deadline (http.NewRequestWithContext vs httptrace.WithClientTrace).
    - Connection reuse fork:
      * GotConnInfo.Reused == true (WasIdle == true when from idle pool) -> skips DNS, TCP, TLS.
      * Conditional new connection stages (DNS, TCP, TLS do not automatically appear in all requests).
    - Request transmission & first response byte (GotFirstResponseByte).
    - Response body caller obligation: caller MUST read to EOF and call resp.Body.Close() to enable reuse,
      and distinguish StatusError lab Fetch policy from default net/http behavior.
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
    footer_h = 36.0
    footer_y = 6.0
    d.add(Rect(6.0, footer_y, w - 12.0, footer_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(
        String(
            10.0,
            footer_y + 25.0,
            "HỢP ĐỒNG BẮT BUỘC: QUẢN LÝ VÀ ĐÓNG RESPONSE BODY",
            fontName="BookSansBold",
            fontSize=6.4,
            fillColor=COLOR_INK_DARK,
        )
    )
    d.add(
        String(
            10.0,
            footer_y + 14.5,
            "• Trách nhiệm caller: defer resp.Body.Close() để tránh leak socket / connection.",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MID,
        )
    )
    d.add(
        String(
            10.0,
            footer_y + 4.5,
            "• Đọc đến EOF rồi đóng hỗ trợ tạo điều kiện reuse, KHÔNG bảo đảm chắc chắn reuse.",
            fontName="BookSans",
            fontSize=6.0,
            fillColor=COLOR_INK_MUTED,
        )
    )

    # Layout coordinates
    body_top = h - header_h - 7.0  # 335.83 pt
    center_x = w / 2.0  # 137.985 pt

    # 1. Top Card: Request Initiation (Explicitly separates NewRequestWithContext vs WithClientTrace)
    r1_x = 8.0
    r1_w = w - 16.0  # 259.97 pt
    r1_h = 34.0
    r1_y = body_top - r1_h
    d.add(Rect(r1_x, r1_y, r1_w, r1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(r1_x + 6.0, r1_y + 22.5, "1. KHỞI TẠO REQUEST & GẮN TRACE HOOK", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(r1_x + 6.0, r1_y + 12.5, "http.NewRequestWithContext(ctx, method, url, nil): Ràng buộc context/deadline", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(r1_x + 6.0, r1_y + 3.5, "httptrace.WithClientTrace(req.Context(), trace): Gắn hook quan sát độc lập", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow Down to Connection Decision
    draw_arrow(d, center_x, r1_y, center_x, r1_y - 8.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # 2. Decision Fork Box: Check Connection Reuse
    fork_y = r1_y - 8.0 - 24.0
    fork_h = 24.0
    fork_w = 208.0
    fork_x = center_x - fork_w / 2.0
    d.add(Rect(fork_x, fork_y, fork_w, fork_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    d.add(String(center_x, fork_y + 13.5, "Connection Pool: Kiểm tra kết nối tái sử dụng?", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(center_x, fork_y + 4.5, "Phân biệt GotConnInfo.Reused vs GotConnInfo.WasIdle", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="middle"))

    # Branch geometry
    branch_top_y = fork_y
    left_branch_x = 8.0
    left_branch_w = 104.0

    right_branch_x = 120.0
    right_branch_w = w - right_branch_x - 8.0  # 147.97 pt

    # Right 3 Steps (Conditional stages when new connection is needed)
    step_a_h = 25.0
    step_a_y = branch_top_y - 15.0 - step_a_h
    step_b_h = 25.0
    step_b_y = step_a_y - 4.0 - step_b_h
    step_c_h = 32.0
    step_c_y = step_b_y - 4.0 - step_c_h

    # Match left box vertically with right branch
    left_box_top = step_a_y + step_a_h
    left_box_y = step_c_y
    left_box_h = left_box_top - left_box_y  # 86.0 pt

    # Left Branch: Reused == true (Idle connection reused)
    d.add(Line(fork_x + 15.0, branch_top_y, left_branch_x + left_branch_w / 2.0, branch_top_y - 8.0, strokeColor=COLOR_INK_DARK, strokeWidth=1.0))
    draw_arrow(d, left_branch_x + left_branch_w / 2.0, branch_top_y - 8.0, left_branch_x + left_branch_w / 2.0, branch_top_y - 15.0, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Left Badge
    d.add(Rect(left_branch_x + 6.0, branch_top_y - 13.0, 42.0, 11.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(left_branch_x + 27.0, branch_top_y - 9.5, "TÁI SỬ DỤNG", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Left Box: Reused Connection (Explains Reused vs WasIdle clearly)
    d.add(Rect(left_branch_x, left_box_y, left_branch_w, left_box_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(left_branch_x + 5.0, left_box_y + left_box_h - 12.0, "TÁI SỬ DỤNG KẾT NỐI", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(left_branch_x + 5.0, left_box_y + left_box_h - 23.0, "GotConnInfo.Reused == true", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(left_branch_x + 5.0, left_box_y + left_box_h - 34.0, "(WasIdle == true khi từ pool)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(left_branch_x + 5.0, left_box_y + 36.0, "• Reused: kết nối đã dùng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(left_branch_x + 5.0, left_box_y + 24.0, "• WasIdle: lấy từ idle pool", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(left_branch_x + 5.0, left_box_y + 12.0, "• Bỏ qua DNS, TCP, TLS mới", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(left_branch_x + 5.0, left_box_y + 3.0, "→ Giảm tối đa độ trễ", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Right Branch: Reused == false (New connection with conditional stages)
    d.add(Line(fork_x + fork_w - 15.0, branch_top_y, right_branch_x + right_branch_w / 2.0, branch_top_y - 8.0, strokeColor=COLOR_INK_DARK, strokeWidth=1.0))
    draw_arrow(d, right_branch_x + right_branch_w / 2.0, branch_top_y - 8.0, right_branch_x + right_branch_w / 2.0, branch_top_y - 15.0, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Right Badge
    d.add(Rect(right_branch_x + 8.0, branch_top_y - 13.0, 50.0, 11.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(right_branch_x + 33.0, branch_top_y - 9.5, "KẾT NỐI MỚI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Step A: DNS (Conditional)
    d.add(Rect(right_branch_x, step_a_y, right_branch_w, step_a_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(right_branch_x + 5.0, step_a_y + 14.0, "2a. Phân giải DNS (net.Resolver.LookupHost)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(right_branch_x + 5.0, step_a_y + 4.5, "DNSStart/Done: Chỉ khi host là tên miền; bỏ qua nếu là IP", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow A -> B
    draw_arrow(d, right_branch_x + right_branch_w / 2.0, step_a_y, right_branch_x + right_branch_w / 2.0, step_a_y - 4.0, color=COLOR_INK_DARK, width=0.9, head_size=3.0)

    # Step B: TCP Dial (Conditional)
    d.add(Rect(right_branch_x, step_b_y, right_branch_w, step_b_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(right_branch_x + 5.0, step_b_y + 14.0, "2b. Khởi tạo TCP Socket (net.Dialer)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(right_branch_x + 5.0, step_b_y + 4.5, "ConnectStart/Done: Chỉ khi cần mở socket mạng mới", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow B -> C
    draw_arrow(d, right_branch_x + right_branch_w / 2.0, step_b_y, right_branch_x + right_branch_w / 2.0, step_b_y - 4.0, color=COLOR_INK_DARK, width=0.9, head_size=3.0)

    # Step C: TLS Handshake (Conditional)
    d.add(Rect(right_branch_x, step_c_y, right_branch_w, step_c_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(right_branch_x + 5.0, step_c_y + 20.5, "2c. TLS Handshake (chỉ khi scheme là HTTPS)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(right_branch_x + 5.0, step_c_y + 11.5, "TLSHandshakeStart/Done: Bỏ qua nếu là HTTP thường", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(right_branch_x + 5.0, step_c_y + 3.0, "Xác minh hostname (ServerName == SAN); cấm tắt verify", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Convergence from Left and Right branches
    converge_y = left_box_y - 12.0
    draw_arrow(d, left_branch_x + left_branch_w / 2.0, left_box_y, left_branch_x + left_branch_w / 2.0, converge_y + 2.0, color=COLOR_INK_DARK, width=1.0, head_size=3.5)
    draw_arrow(d, right_branch_x + right_branch_w / 2.0, step_c_y, right_branch_x + right_branch_w / 2.0, converge_y + 2.0, color=COLOR_INK_DARK, width=1.0, head_size=3.5)

    # Convergence horizontal bar
    d.add(Line(left_branch_x + left_branch_w / 2.0, converge_y, right_branch_x + right_branch_w / 2.0, converge_y, strokeColor=COLOR_BORDER, strokeWidth=0.8))
    draw_arrow(d, center_x, converge_y, center_x, converge_y - 7.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # 3. Step 3: Request Transmission & First Byte
    step3_y = converge_y - 7.0 - 30.0
    step3_h = 30.0
    d.add(Rect(r1_x, step3_y, r1_w, step3_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(r1_x + 6.0, step3_y + 19.5, "3. TRUYỀN DỮ LIỆU & CHỜ PHẢN HỒI (HTTP ROUND-TRIP)", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(r1_x + 6.0, step3_y + 10.5, "WroteHeaders -> WroteRequest: Gửi headers và payload request", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(r1_x + 6.0, step3_y + 2.5, "GotFirstResponseByte: Server hoàn tất xử lý và phản hồi byte đầu tiên", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow Down to Step 4
    draw_arrow(d, center_x, step3_y, center_x, step3_y - 7.0, color=COLOR_INK_DARK, width=1.0, head_size=4.0)

    # 4. Step 4: Stream Response Body & Lab Fetch Policy Notice
    step4_y = step3_y - 7.0 - 34.0
    step4_h = 34.0
    d.add(Rect(r1_x, step4_y, r1_w, step4_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(r1_x + 6.0, step4_y + 22.5, "4. ĐỌC DỮ LIỆU & XỬ LÝ PHẢN HỒI", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(r1_x + 6.0, step4_y + 12.5, "Caller nhận *http.Response; đọc dữ liệu qua stream hoặc io.ReadAll(resp.Body)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(r1_x + 6.0, step4_y + 3.0, "Chính sách lab Fetch: status ngoài 2xx thành StatusError (net/http không tự trả lỗi)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MUTED))

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
