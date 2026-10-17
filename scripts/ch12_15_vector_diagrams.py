# -*- coding: utf-8 -*-
"""High-precision publication-grade vector technical diagrams for Chapters 12, 13, 15.

Generates 3 diagrams matching the exact publication dimensions from Golang_Master.pdf:
1. Chapter 12: http-service-lifecycle.png (185.80 x 362.83 pt, Page 217, xref 477)
   - HTTP Service Lifecycle, Graceful Shutdown & Context Boundaries (labs/part12-service-lifecycle)
2. Chapter 13: transaction-boundary.png (422.77 x 362.83 pt, Page 233, xref 510)
   - Transaction Boundary & Atomicity Guarantees (labs/part13-transaction-boundary)
3. Chapter 15: incident-command-lifecycle.png (444.69 x 362.83 pt, Page 272, xref 589)
   - Process Supervision, Stream Isolation & Four Exit Outcomes (labs/part15-incident-command)

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
# 1. CHAPTER 12: HTTP SERVICE LIFECYCLE (185.80 x 362.83 pt)
# ==============================================================================

def build_http_service_lifecycle_drawing(w: float = 185.80, h: float = 362.83) -> Drawing:
    """Render Chapter 12 technical diagram: HTTP Service Lifecycle & Graceful Shutdown.

    Publication size: 185.80 x 362.83 pt (Page 217, xref 477).
    """
    d = Drawing(w, h)

    # Outer border / Canvas boundary
    d.add(Rect(0, 0, w, h, fillColor=colors.white, strokeColor=COLOR_BORDER, strokeWidth=1.0, rx=3, ry=3))

    # Header Bar
    header_h = 20.0
    header_y = h - header_h - 4.0
    d.add(Rect(4.0, header_y, w - 8.0, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(8.0, header_y + 6.5, "VÒNG ĐỜI HTTP SERVICE", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(w - 8.0, header_y + 6.5, "[net/http & signal]", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    # Footer Callout Banner
    footer_h = 32.0
    footer_y = 5.0
    footer_w = w - 10.0
    footer_x = 5.0
    d.add(Rect(footer_x, footer_y, footer_w, footer_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(footer_x + 5.0, footer_y + 22.0, "BẤT BIẾN KỸ THUẬT // RANH GIỚI SHUTDOWN", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(footer_x + 5.0, footer_y + 12.5, "• Shutdown đóng listener & pool; KHÔNG tự cancel r.Context().", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(footer_x + 5.0, footer_y + 3.5, "• Hết grace chỉ dừng drain; caller tự định đoạt ngắt socket/exit.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Usable vertical space between header and footer
    body_top = header_y - 5.0  # 333.83 pt
    body_bot = footer_y + footer_h + 5.0  # 42.0 pt
    card_x = 5.0
    card_w = w - 10.0  # 175.80 pt

    # Heights of 5 stages (Total stages = 262.0 pt)
    s1_h = 44.0
    s2_h = 38.0
    s3_h = 58.0
    s4_h = 66.0
    s5_h = 56.0
    total_stages_h = s1_h + s2_h + s3_h + s4_h + s5_h  # 262.0 pt
    gap = (body_top - body_bot - total_stages_h) / 4.0  # (291.83 - 262.0) / 4 = 7.4575 pt

    # ------------------------------------------------------------------
    # Stage 1: Khởi tạo & Process Boundary (Startup)
    # ------------------------------------------------------------------
    y1 = body_top - s1_h
    d.add(Rect(card_x, y1, card_w, s1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 4.0, y1 + s1_h - 11.0, 15.0, 8.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 11.5, y1 + s1_h - 9.0, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 23.0, y1 + s1_h - 9.0, "1. KHỞI TẠO & PROCESS BOUNDARY", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, y1 + 25.5, "ctx, stop := signal.NotifyContext(...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, y1 + 17.5, "defer stop() // main quản lý signal", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 6.0, y1 + 10.0, "• main gọi ServeUntilStopped(ctx, ...)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, y1 + 4.5, "• Helper mở goroutine: srv.Serve(ln)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, card_x + card_w / 2.0, y1, card_x + card_w / 2.0, y1 - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # ------------------------------------------------------------------
    # Stage 2: Tiếp nhận & Phục vụ (Active Serving)
    # ------------------------------------------------------------------
    y2 = y1 - gap - s2_h
    d.add(Rect(card_x, y2, card_w, s2_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 4.0, y2 + s2_h - 11.0, 15.0, 8.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 11.5, y2 + s2_h - 9.0, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 23.0, y2 + s2_h - 9.0, "2. TIẾP NHẬN & PHỤC VỤ (ACTIVE)", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, y2 + 22.5, "Incoming Request -> ServeHTTP(w, r)", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, y2 + 15.5, "• r.Context() gắn theo vòng đời request", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 6.0, y2 + 9.5, "• Có thể kế thừa từ Server.BaseContext", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(card_x + 6.0, y2 + 4.5, "• Handler chạy độc lập với shutdown ctx", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    draw_arrow(d, card_x + card_w / 2.0, y2, card_x + card_w / 2.0, y2 - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # ------------------------------------------------------------------
    # Stage 3: Nhánh rẽ Select ban đầu (fixed/server.go)
    # ------------------------------------------------------------------
    y3 = y2 - gap - s3_h
    d.add(Rect(card_x, y3, card_w, s3_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 4.0, y3 + s3_h - 11.0, 15.0, 8.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 11.5, y3 + s3_h - 9.0, "03", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 23.0, y3 + s3_h - 9.0, "3. SELECT BAN ĐẦU (fixed/server.go)", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))

    sub_gap = 4.0
    sub_w = (card_w - 8.0 - sub_gap) / 2.0  # 81.9 pt each
    sub_h = 42.0
    sub_y = y3 + 4.0

    # Left sub-card: Nhánh 1 (Lỗi sớm trước signal -> Thoát sớm, KHÔNG xuống Shutdown)
    sub_left_x = card_x + 4.0
    d.add(Rect(sub_left_x, sub_y, sub_w, sub_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(Rect(sub_left_x, sub_y + sub_h - 10.0, sub_w, 10.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(Rect(sub_left_x, sub_y + sub_h - 10.0, sub_w, 2.0, fillColor=COLOR_TAG_BG, strokeColor=None))
    d.add(String(sub_left_x + sub_w / 2.0, sub_y + sub_h - 7.5, "err := <-serveErr", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(sub_left_x + 4.0, sub_y + 22.5, "• Lỗi trước khi có signal", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(sub_left_x + 4.0, sub_y + 13.5, "  Closed: nil / khác: lỗi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(sub_left_x + 4.0, sub_y + 4.5, "=> THOÁT SỚM (RETURN)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Right sub-card: Nhánh 2 (Tín hiệu dừng -> Tiếp tục quy trình Shutdown)
    sub_right_x = sub_left_x + sub_w + sub_gap
    d.add(Rect(sub_right_x, sub_y, sub_w, sub_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.7, rx=1.5, ry=1.5))
    d.add(Rect(sub_right_x, sub_y + sub_h - 10.0, sub_w, 10.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.7, rx=1.5, ry=1.5))
    d.add(Rect(sub_right_x, sub_y + sub_h - 10.0, sub_w, 2.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(sub_right_x + sub_w / 2.0, sub_y + sub_h - 7.5, "<-ctx.Done()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(sub_right_x + 4.0, sub_y + 22.5, "• Nhận OS signal (SIGINT)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(sub_right_x + 4.0, sub_y + 13.5, "• Hoặc caller hủy context", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(sub_right_x + 4.0, sub_y + 4.5, "=> VÀO SHUTDOWN", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Downward arrow originates ONLY from the Right sub-card down to Stage 4!
    arrow_x = sub_right_x + sub_w / 2.0
    draw_arrow(d, arrow_x, y3, arrow_x, y3 - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # ------------------------------------------------------------------
    # Stage 4: Graceful Shutdown (Điều phối Server.Shutdown)
    # ------------------------------------------------------------------
    y4 = y3 - gap - s4_h
    d.add(Rect(card_x, y4, card_w, s4_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 4.0, y4 + s4_h - 11.0, 15.0, 8.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 11.5, y4 + s4_h - 9.0, "04", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 23.0, y4 + s4_h - 9.0, "4. ĐIỀU PHỐI Server.Shutdown", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, y4 + 50.5, "shutdownCtx, cancel := context.WithTimeout(", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 12.0, y4 + 43.5, "context.Background(), grace); defer cancel()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, y4 + 36.0, "1. err := srv.Shutdown(shutdownCtx)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, y4 + 28.5, "• Lỗi Shutdown => return fmt.Errorf(\"shutdown: %w\", err)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, y4 + 21.0, "2. Chỉ khi Shutdown thành công mới nhận <-serveErr:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, y4 + 13.5, "• Khớp ErrServerClosed => return nil (sạch)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 10.0, y4 + 6.0, "• Khác ErrServerClosed => bọc lỗi và trả về", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, card_x + card_w / 2.0, y4, card_x + card_w / 2.0, y4 - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # ------------------------------------------------------------------
    # Stage 5: Hai kết cục tại Boundary Deadline (Split Cards)
    # ------------------------------------------------------------------
    y5 = y4 - gap - s5_h
    split_w = (card_w - 6.0) / 2.0  # 84.9 pt each

    # Branch Left: Thành công trong hạn grace
    b_left_x = card_x
    d.add(Rect(b_left_x, y5, split_w, s5_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(b_left_x, y5 + s5_h - 13.0, split_w, 13.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(b_left_x, y5 + s5_h - 13.0, split_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(b_left_x + split_w / 2.0, y5 + s5_h - 9.5, "TRONG HẠN GRACE", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(b_left_x + 4.0, y5 + 34.0, "• Shutdown trả nil", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b_left_x + 4.0, y5 + 26.5, "• <-serveErr trả Closed", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b_left_x + 4.0, y5 + 19.0, "• Active handler xong", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b_left_x + 4.0, y5 + 11.5, "• Drain kết nối sạch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b_left_x + 4.0, y5 + 5.0, "=> return nil (Clean)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Branch Right: Hết hạn grace
    b_right_x = card_x + split_w + 6.0
    d.add(Rect(b_right_x, y5, split_w, s5_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(b_right_x, y5 + s5_h - 13.0, split_w, 13.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(b_right_x, y5 + s5_h - 13.0, split_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(b_right_x + split_w / 2.0, y5 + s5_h - 9.5, "QUÁ HẠN GRACE", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(b_right_x + 4.0, y5 + 34.0, "• Trả DeadlineExceeded", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b_right_x + 4.0, y5 + 26.5, "• Listener & pool ĐÃ đóng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b_right_x + 4.0, y5 + 19.0, "• Active socket chưa ngắt", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b_right_x + 4.0, y5 + 11.5, "=> Caller tự định đoạt", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b_right_x + 4.0, y5 + 5.0, "(srv.Close / exit)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    return d


# ==============================================================================
# 2. CHAPTER 13: TRANSACTION BOUNDARY (422.77 x 362.83 pt)
# ==============================================================================

def build_transaction_boundary_drawing(w: float = 422.77, h: float = 362.83) -> Drawing:
    """Render Chapter 13 technical diagram: Transaction Boundary & Atomicity Guarantees.

    Publication size: 422.77 x 362.83 pt (Page 233, xref 510).
    """
    d = Drawing(w, h)

    # Outer border / Canvas boundary
    d.add(Rect(0, 0, w, h, fillColor=colors.white, strokeColor=COLOR_BORDER, strokeWidth=1.0, rx=3, ry=3))

    # Header Bar
    header_h = 22.0
    header_y = h - header_h - 6.0
    d.add(Rect(6.0, header_y, w - 12.0, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(12.0, header_y + 7.5, "RANH GIỚI TRANSACTION // TÍNH NGUYÊN TỬ (ATOMICITY)", fontName="BookSansBold", fontSize=7.4, fillColor=COLOR_INK_DARK))
    d.add(String(w - 12.0, header_y + 7.5, "[labs/part13-transaction-boundary // Disable()]", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    # Footer Callout Banner
    footer_h = 32.0
    footer_y = 6.0
    footer_w = w - 12.0
    footer_x = 6.0
    d.add(Rect(footer_x, footer_y, footer_w, footer_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(footer_x + 6.0, footer_y + 22.0, "BẤT BIẾN KỸ THUẬT: HỢP ĐỒNG NGUYÊN TỬ (ATOMICITY) TRONG TRANSACTION", fontName="BookSansBold", fontSize=6.5, fillColor=COLOR_INK_DARK))
    d.add(String(footer_x + 6.0, footer_y + 12.5, "• Mọi câu lệnh SQL trong tx cùng có hiệu lực khi Commit thành công, hoặc cùng bị loại bỏ khi Rollback trước Commit.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(footer_x + 6.0, footer_y + 3.5, "• Lỗi tại Commit không bảo đảm trạng thái đã rollback; DB không rollback được tác dụng phụ ngoài (HTTP, log, event).", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Usable middle space
    body_y = footer_y + footer_h + 8.0  # 46.0 pt
    body_h = header_y - body_y - 8.0     # 280.83 pt

    # Two Column Layout:
    # Col 1: Transaction Execution Container (Width: 248.0 pt)
    # Col 2: Outcomes & Concept Separation (Width: 154.77 pt)
    col1_x = 6.0
    col1_w = 248.0
    col2_x = col1_x + col1_w + 8.0  # 262.0 pt
    col2_w = w - col2_x - 6.0        # 154.77 pt

    # ------------------------------------------------------------------
    # COLUMN 1: TRANSACTION CONTAINER (Boundary box)
    # ------------------------------------------------------------------
    d.add(Rect(col1_x, body_y, col1_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=1.0, rx=3, ry=3))
    # Container Header
    c_head_h = 16.0
    c_head_y = body_y + body_h - c_head_h
    d.add(Rect(col1_x, c_head_y, col1_w, c_head_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=3, ry=3))
    d.add(Rect(col1_x, c_head_y, col1_w, 4.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(col1_x + 8.0, c_head_y + 4.5, "RANH GIỚI THỰC THI // MÔ HÌNH LOGIC TRANSACTION", fontName="BookSansBold", fontSize=6.5, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + col1_w - 8.0, c_head_y + 4.5, "[mô hình logic tương đương]", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    # Step heights inside Col 1
    box_x = col1_x + 6.0
    box_w = col1_w - 12.0  # 236.0 pt
    
    inner_top = c_head_y - 6.0
    inner_bot = body_y + 6.0

    b1_h = 50.0  # Begin, err check & defer Rollback
    b2_h = 76.0  # Statement 1: UPDATE checks & RowsAffected check
    b3_h = 58.0  # Statement 2: INSERT check_events
    b4_h = 48.0  # Commit
    total_box_h = b1_h + b2_h + b3_h + b4_h  # 232.0 pt
    gap_col1 = (inner_top - inner_bot - total_box_h) / 3.0  # ~6.94 pt

    # Box 1: Begin & Defer Rollback
    y_b1 = inner_top - b1_h
    d.add(Rect(box_x, y_b1, box_w, b1_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_SUBTLE, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(box_x + 6.0, y_b1 + 39.0, "tx, err := db.BeginTx(ctx, nil)", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b1 + 30.5, "• Lỗi khởi tạo: return fmt.Errorf(\"begin disable transaction: %w\", err)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b1 + 21.5, "defer tx.Rollback() // ĐĂNG KÝ BẢO HIỂM HOÀN NGUYÊN", fontName="BookMono", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b1 + 13.0, "• Hoàn nguyên nếu return sớm do lỗi ở các bước sau", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(box_x + 6.0, y_b1 + 5.0, "• Nếu Commit() thành công: Rollback() trả ErrTxDone vô hại", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, box_x + box_w / 2.0, y_b1, box_x + box_w / 2.0, y_b1 - gap_col1, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Box 2: Statement 1 (UPDATE checks & RowsAffected)
    y_b2 = y_b1 - gap_col1 - b2_h
    d.add(Rect(box_x, y_b2, box_w, b2_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(box_x + 5.0, y_b2 + b2_h - 11.0, 16.0, 8.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(box_x + 13.0, y_b2 + b2_h - 9.0, "S1", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(box_x + 25.0, y_b2 + b2_h - 9.0, "CÂU LỆNH 1: UPDATE checks // KIỂM TRA TARGET", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b2 + 52.5, "SQL: UPDATE checks SET enabled = 0 WHERE id = ?", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b2 + 43.5, "• Tham số thực tế: checkID", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(box_x + 6.0, y_b2 + 35.0, "• Lỗi Exec: return fmt.Errorf(\"disable check: %w\", err)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b2 + 26.5, "changed, err := result.RowsAffected()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(box_x + 6.0, y_b2 + 18.0, "• Lỗi Count: return fmt.Errorf(\"count disabled checks: %w\", err)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b2 + 10.5, "• changed == 0: return ErrCheckNotFound (Không tìm thấy target)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b2 + 4.5, "• Lỗi bất kỳ -> return sớm -> defer tx.Rollback() hoàn nguyên", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, box_x + box_w / 2.0, y_b2, box_x + box_w / 2.0, y_b2 - gap_col1, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Box 3: Statement 2 (INSERT check_events)
    y_b3 = y_b2 - gap_col1 - b3_h
    d.add(Rect(box_x, y_b3, box_w, b3_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(box_x + 5.0, y_b3 + b3_h - 11.0, 16.0, 8.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(box_x + 13.0, y_b3 + b3_h - 9.0, "S2", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(box_x + 25.0, y_b3 + b3_h - 9.0, "CÂU LỆNH 2: INSERT check_events // GHI AUDIT EVENT", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b3 + 37.0, "SQL: INSERT INTO check_events(check_id, action) VALUES (?, ?)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b3 + 28.5, "• Tham số thực tế: checkID, \"disabled\"", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(box_x + 6.0, y_b3 + 20.0, "• Lỗi Exec: return fmt.Errorf(\"record disable event: %w\", err)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b3 + 12.0, "• Ràng buộc DB: CHECK (action = 'disabled')", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b3 + 5.0, "• Vi phạm ràng buộc -> return -> defer tx.Rollback()", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    draw_arrow(d, box_x + box_w / 2.0, y_b3, box_x + box_w / 2.0, y_b3 - gap_col1, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Box 4: Commit
    y_b4 = y_b3 - gap_col1 - b4_h
    d.add(Rect(box_x, y_b4, box_w, b4_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(box_x + 6.0, y_b4 + 37.0, "if err := tx.Commit(); err != nil {", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 14.0, y_b4 + 28.5, "return fmt.Errorf(\"commit disable: %w\", err)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b4 + 20.0, "}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b4 + 11.5, "• Thành công (err == nil): Cả hai câu lệnh cùng áp dụng trọn vẹn (atomicity)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(box_x + 6.0, y_b4 + 4.5, "• Thất bại tại Commit: Không chắc chắn rollback (lỗi mạng/DB crash)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # ------------------------------------------------------------------
    # COLUMN 2: OUTCOMES & CONCEPT SEPARATION
    # ------------------------------------------------------------------
    # Card 1: Commit Success
    c2_y1 = body_y + body_h - 66.0
    c2_h1 = 66.0
    d.add(Rect(col2_x, c2_y1, col2_w, c2_h1, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x, c2_y1 + c2_h1 - 13.0, col2_w, 13.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x, c2_y1 + c2_h1 - 13.0, col2_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(col2_x + 6.0, c2_y1 + c2_h1 - 9.5, "KẾT CỤC 1: COMMIT THÀNH CÔNG", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, c2_y1 + 38.0, "• checks.enabled = 0 (Đã tắt)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, c2_y1 + 27.0, "• check_events: 1 dòng 'disabled'", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, c2_y1 + 16.0, "• Cả 2 thay đổi cùng áp dụng trọn vẹn", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 6.0, c2_y1 + 5.0, "=> Hoàn tất atomicity, trả conn về pool", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Connecting arrow: Box 4 (Commit) -> Card 1 (Commit Success)
    draw_arrow(d, box_x + box_w, y_b4 + b4_h / 2.0, col2_x, c2_y1 + 20.0, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Card 2: Rollback on Error
    c2_y2 = c2_y1 - 10.0 - 68.0
    c2_h2 = 68.0
    d.add(Rect(col2_x, c2_y2, col2_w, c2_h2, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x, c2_y2 + c2_h2 - 13.0, col2_w, 13.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x, c2_y2 + c2_h2 - 13.0, col2_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(col2_x + 6.0, c2_y2 + c2_h2 - 9.5, "KẾT CỤC 2: LỖI TRƯỚC COMMIT", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, c2_y2 + 40.0, "• Lỗi tại Update / Rows / Insert", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, c2_y2 + 29.0, "• defer tx.Rollback() hoàn nguyên sạch", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, c2_y2 + 17.0, "• checks giữ nguyên, 0 dòng event rác", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 6.0, c2_y2 + 5.0, "=> Trạng thái DB quay về ban đầu", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Connecting arrow: Box 2/3 error points -> Card 2
    d.add(Line(box_x + box_w, y_b2 + 25.0, box_x + box_w + 10.0, y_b2 + 25.0, strokeColor=COLOR_INK_MID, strokeWidth=0.9, strokeDashArray=[2, 2]))
    d.add(Line(box_x + box_w, y_b3 + 26.0, box_x + box_w + 10.0, y_b3 + 26.0, strokeColor=COLOR_INK_MID, strokeWidth=0.9, strokeDashArray=[2, 2]))
    d.add(Line(box_x + box_w + 10.0, y_b2 + 25.0, box_x + box_w + 10.0, c2_y2 + c2_h2 / 2.0, strokeColor=COLOR_INK_MID, strokeWidth=0.9, strokeDashArray=[2, 2]))
    draw_arrow(d, box_x + box_w + 10.0, c2_y2 + c2_h2 / 2.0, col2_x, c2_y2 + c2_h2 / 2.0, color=COLOR_INK_MID, width=0.9, head_size=3.5, dashed=True)

    # Card 3: Technical Concept Separation (Atomicity vs Isolation & Side effects)
    c2_y3 = body_y
    c2_h3 = c2_y2 - body_y - 8.0  # 128.83 pt
    d.add(Rect(col2_x, c2_y3, col2_w, c2_h3, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x, c2_y3 + c2_h3 - 13.0, col2_w, 13.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(Rect(col2_x, c2_y3 + c2_h3 - 13.0, col2_w, 3.0, fillColor=COLOR_TAG_BG, strokeColor=None))
    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 9.5, "RANH GIỚI KỸ THUẬT & ATOMICITY", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    
    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 22.0, "1. ATOMICITY (TÍNH NGUYÊN TỬ):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 31.0, "• Cả hai câu lệnh cùng áp dụng hoặc cùng hủy.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 40.0, "• Lỗi tại Commit: Không chắc chắn rollback.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 53.0, "2. ISOLATION (MỨC ĐỘ CÔ LẬP):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 62.0, "• Không mặc nhiên là Serializable.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 71.0, "• DB engine & TxOptions quyết định cách", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 80.0, "  giao dịch đồng thời nhìn thấy dữ liệu.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 93.0, "3. EXTERNAL SIDE EFFECTS:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 102.0, "• DB Rollback KHÔNG thu hồi được email,", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 111.0, "  webhook hay message đã publish ngoài.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 6.0, c2_y3 + c2_h3 - 120.0, "• Cần Transactional Outbox pattern.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ==============================================================================
# 3. CHAPTER 15: INCIDENT COMMAND LIFECYCLE (444.69 x 362.83 pt)
# ==============================================================================

def build_incident_command_lifecycle_drawing(w: float = 444.69, h: float = 362.83) -> Drawing:
    """Render Chapter 15 technical diagram: Incident Command Lifecycle & Process Supervision.

    Publication size: 444.69 x 362.83 pt (Page 272, xref 589).
    """
    d = Drawing(w, h)

    # Outer border / Canvas boundary
    d.add(Rect(0, 0, w, h, fillColor=colors.white, strokeColor=COLOR_BORDER, strokeWidth=1.0, rx=3, ry=3))

    # Header Bar
    header_h = 22.0
    header_y = h - header_h - 6.0
    d.add(Rect(6.0, header_y, w - 12.0, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(12.0, header_y + 7.5, "VÒNG ĐỜI TIẾN TRÌNH SỰ CỐ (PROCESS SUPERVISION)", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(w - 12.0, header_y + 7.5, "[LAB 15: labs/part15-incident-command]", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED, textAnchor="end"))

    # Footer Callout Banner
    footer_h = 32.0
    footer_y = 6.0
    footer_w = w - 12.0
    footer_x = 6.0
    d.add(Rect(footer_x, footer_y, footer_w, footer_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(footer_x + 6.0, footer_y + 22.0, "BẤT BIẾN KỸ THUẬT: BẰNG CHỨNG QUAN SÁT vs NGUYÊN NHÂN GỐC", fontName="BookSansBold", fontSize=6.5, fillColor=COLOR_INK_DARK))
    d.add(String(footer_x + 6.0, footer_y + 12.5, "• os/exec chạy executable với mảng args riêng biệt, không tự gọi shell; Result là dữ liệu quan sát.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(footer_x + 6.0, footer_y + 3.5, "• Hàm bọc fmt.Errorf(\"%w\"); caller dùng errors.As bóc ExitError; ProcessState ghi nhận khi hoàn tất.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Usable middle space
    body_y = footer_y + footer_h + 8.0  # 46.0 pt
    body_h = header_y - body_y - 8.0     # 280.83 pt

    # Layout structure:
    # Top section: Spec & Context/Buffer Preparation (Height: 74.0 pt)
    # Middle bar: Supervision & cmd.Run() execution (Height: 42.0 pt)
    # Bottom section: 4 Outcome Cards (Height: 146.83 pt)
    card_x = 6.0
    card_w = w - 12.0  # 432.69 pt

    top_h = 74.0
    top_y = body_y + body_h - top_h

    # Top Left: Spec & Helper fixture (Width: 212.0 pt)
    t_left_w = 212.0
    d.add(Rect(card_x, top_y, t_left_w, top_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x, top_y + top_h - 13.0, t_left_w, 13.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x, top_y + top_h - 13.0, t_left_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(card_x + 6.0, top_y + top_h - 9.5, "1. ĐẶC TẢ LỆNH (Spec) & HELPER FIXTURE", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, top_y + 51.5, "spec := Spec{Name: os.Args[0],", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, top_y + 43.5, "  Timeout: 5*time.Second,", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, top_y + 35.5, "  Args: []string{\"-test.run=^TestHelperProcess$\",", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, top_y + 27.5, "    \"-helper-mode=ok\"}}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, top_y + 19.5, "• Helper fixture dùng xuyên suốt test của lab", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 6.0, top_y + 11.5, "• os/exec khởi chạy executable với args riêng,", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, top_y + 4.5, "  không tự gọi qua shell của hệ điều hành", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Top Right: Context Timeout & Buffer Isolation (Width: 212.69 pt)
    t_right_x = card_x + t_left_w + 8.0  # 226.0 pt
    t_right_w = card_w - t_left_w - 8.0  # 212.69 pt
    d.add(Rect(t_right_x, top_y, t_right_w, top_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(t_right_x, top_y + top_h - 13.0, t_right_w, 13.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(t_right_x, top_y + top_h - 13.0, t_right_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(t_right_x + 6.0, top_y + top_h - 9.5, "2. RÀNG BUỘC CONTEXT & THU THẬP STREAM", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(t_right_x + 6.0, top_y + 51.5, "runCtx, cancel := context.WithTimeout(", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(t_right_x + 12.0, top_y + 43.5, "ctx, spec.Timeout); defer cancel()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(t_right_x + 6.0, top_y + 35.5, "cmd := exec.CommandContext(runCtx,", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(t_right_x + 12.0, top_y + 27.5, "spec.Name, spec.Args...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(t_right_x + 6.0, top_y + 19.5, "cmd.Stdout = &stdout; cmd.Stderr = &stderr", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(t_right_x + 6.0, top_y + 11.5, "• stdout/stderr hứng độc lập vào Buffer riêng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(t_right_x + 6.0, top_y + 4.5, "• runCtx xử lý cả deadline timeout và parent cancel", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow Down to Middle Bar
    mid_h = 42.0
    mid_y = top_y - 9.0 - mid_h
    draw_arrow(d, card_x + card_w / 2.0, top_y, card_x + card_w / 2.0, top_y - 9.0, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # Middle Bar: Process Execution & Supervision
    d.add(Rect(card_x, mid_y, card_w, mid_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.9, rx=2, ry=2))
    d.add(String(card_x + 8.0, mid_y + 31.0, "THỰC THI & GIÁM SÁT TIẾN TRÌNH: err := cmd.Run()", fontName="BookSansBold", fontSize=6.6, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 8.0, mid_y + 22.0, "• cmd.Run() khởi chạy và chờ tiến trình; thu thập stdout/stderr độc lập qua bytes.Buffer", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, mid_y + 13.0, "• Phễu phân loại: [P1] runCtx.Err() != nil -> [P2] err == nil -> [P3] errors.As(err, &exitErr) -> [P4] Fallthrough", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, mid_y + 4.5, "• cmd.ProcessState != nil ghi nhận ExitCode; nếu chưa start (State == nil) thì ExitCode = -1", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Arrow Down to 4 Outcomes
    bot_y = body_y
    bot_h = mid_y - body_y - 9.0  # 146.83 pt
    draw_arrow(d, card_x + card_w / 2.0, mid_y, card_x + card_w / 2.0, mid_y - 9.0, color=COLOR_INK_DARK, width=1.0, head_size=3.8)

    # 4 Outcome Cards Side by Side (Ordered strictly by branch evaluation priority in fixed/run.go)
    col_gap = 5.0
    col_w = (card_w - 3.0 * col_gap) / 4.0  # ~104.42 pt each

    # Outcome 1: Priority 1: Timeout / Cancel (Checked first to avoid misclassifying as ExitError)
    c1_x = card_x
    d.add(Rect(c1_x, bot_y, col_w, bot_h, fillColor=COLOR_POLICY_BG, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c1_x, bot_y + bot_h - 14.0, col_w, 14.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c1_x, bot_y + bot_h - 14.0, col_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(c1_x + col_w / 2.0, bot_y + bot_h - 10.0, "1. TIMEOUT / CANCEL", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(c1_x + 4.0, bot_y + bot_h - 24.5, "runCtx.Err() != nil [P1]", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 4.0, bot_y + bot_h - 34.0, "• DeadlineExceeded:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 8.0, bot_y + bot_h - 43.0, "=> TimedOut = true", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 4.0, bot_y + bot_h - 52.0, "• context.Canceled:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 8.0, bot_y + bot_h - 61.0, "=> TimedOut = false", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 4.0, bot_y + bot_h - 72.0, "DỮ LIỆU THU ĐƯỢC:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 4.0, bot_y + bot_h - 81.5, "• Stdout/Stderr đến ngắt", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 4.0, bot_y + bot_h - 93.0, "HỢP ĐỒNG KỸ THUẬT:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 4.0, bot_y + bot_h - 102.5, "• Ưu tiên kiểm tra trước", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 4.0, bot_y + bot_h - 111.5, "  tránh nhầm với ExitErr", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 4.0, bot_y + bot_h - 123.0, "=> Trả (Result, wrappedErr)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 4.0, bot_y + bot_h - 132.0, "bọc command context: %w", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Outcome 2: Priority 2: Exit 0 // Thành công (Checked when no context error and err == nil)
    c2_x = c1_x + col_w + col_gap
    d.add(Rect(c2_x, bot_y, col_w, bot_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c2_x, bot_y + bot_h - 14.0, col_w, 14.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c2_x, bot_y + bot_h - 14.0, col_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(c2_x + col_w / 2.0, bot_y + bot_h - 10.0, "2. EXIT 0 // THÀNH CÔNG", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 24.5, "err == nil [P2]", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 34.5, "ExitCode: 0", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 44.5, "TimedOut: false", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 54.5, "ProcessState != nil", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 67.5, "DỮ LIỆU THU ĐƯỢC:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 77.0, "• Stdout: output lệnh", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 86.5, "• Stderr: bảo toàn log", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 99.0, "HỢP ĐỒNG KỸ THUẬT:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 108.5, "• Lệnh chạy trọn vẹn,", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 117.5, "  giữ đủ cả hai stream.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 4.0, bot_y + bot_h - 131.0, "=> Trả (Result, nil)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Outcome 3: Priority 3: Exit != 0 // Lệnh lỗi (Checked when err != nil and matches ExitError)
    c3_x = c2_x + col_w + col_gap
    d.add(Rect(c3_x, bot_y, col_w, bot_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c3_x, bot_y + bot_h - 14.0, col_w, 14.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c3_x, bot_y + bot_h - 14.0, col_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(c3_x + col_w / 2.0, bot_y + bot_h - 10.0, "3. EXIT != 0 // LỆNH LỖI", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 23.5, "[P3] Bóc ExitError:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 32.5, "var exitErr *exec.ExitError", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 41.5, "errors.As(err, &exitErr)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 50.5, "ExitCode != 0 (vd: 7)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 59.5, "ProcessState != nil", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 71.0, "DỮ LIỆU THU ĐƯỢC:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 80.0, "• Stderr giữ chẩn đoán!", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 89.0, "• Stdout thu trước exit", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 101.0, "HỢP ĐỒNG KỸ THUẬT:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 110.0, "• errors.As bóc ExitError", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 118.5, "  xuyên qua wrap chain.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 129.5, "=> Trả (Result, wrappedErr)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 4.0, bot_y + bot_h - 138.0, "bọc exit code: %d: %w", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Outcome 4: Priority 4: Start Failure / Non-exit Error (Fallthrough in fixed/run.go)
    c4_x = c3_x + col_w + col_gap
    d.add(Rect(c4_x, bot_y, col_w, bot_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c4_x, bot_y + bot_h - 14.0, col_w, 14.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c4_x, bot_y + bot_h - 14.0, col_w, 3.0, fillColor=COLOR_BG_HEADER, strokeColor=None))
    d.add(String(c4_x + col_w / 2.0, bot_y + bot_h - 10.0, "4. LỖI START / NON-EXIT", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 23.5, "Fallthrough [P4]", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 32.5, "• Chưa start: State==nil", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 41.0, "  (File not found, perm...)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 49.5, "  => ExitCode: -1 (mặc định)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 58.0, "• Đã start: State!=nil", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 66.5, "  (lỗi I/O copy / pipe)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 78.0, "DỮ LIỆU THU ĐƯỢC:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 87.0, "• Stdout/Stderr rỗng/part", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 98.5, "HỢP ĐỒNG KỸ THUẬT:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 107.5, "• Không có ExitError", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 118.5, "=> Trả (Result, wrappedErr)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c4_x + 4.0, bot_y + bot_h - 127.5, "bọc \"start command: %w\"", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    return d


# ==============================================================================
# EXPORT PIPELINE
# ==============================================================================

def export_diagrams_to_png(target_dir: Path | None = None, dpi: int = 320, names: list[str] | None = None) -> list[Path]:
    """Render Chapters 12, 13, 15 diagrams to high-resolution publication PNGs at 320 DPI."""
    register_fonts()
    if target_dir is None:
        target_dir = ROOT / "assets/diagrams"
    target_dir.mkdir(parents=True, exist_ok=True)

    diagrams = [
        ("http-service-lifecycle.png", build_http_service_lifecycle_drawing()),
        ("transaction-boundary.png", build_transaction_boundary_drawing()),
        ("incident-command-lifecycle.png", build_incident_command_lifecycle_drawing()),
    ]
    if names is not None:
        diagrams = [(fn, dr) for fn, dr in diagrams if fn in names]

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
