# -*- coding: utf-8 -*-
"""Vector Diagram Generators for Chapters 16, 17, 18 (Batch 03 - Agent 2 Specification).

Publication-grade, 100% pure grayscale technical diagrams matching exact 1:1
bounding boxes in Golang_Master.pdf:
- Chapter 16 (Hình 27): assets/diagrams/observability-projections.png (476.22 x 312.02 pt, p.283, xref 328)
- Chapter 16 (Hình 28): assets/diagrams/probe-observation-path.png (476.22 x 264.46 pt, p.292, xref 338)
- Chapter 17 (Hình 29): assets/diagrams/reconciliation-loop.png (335.89 x 362.83 pt, p.300, xref 347)
- Chapter 17 (Hình 31): assets/diagrams/container-cluster-observation.png (476.22 x 238.11 pt, p.310, xref 359)
- Chapter 18 (Hình 32): assets/diagrams/delivery-evidence-chain.png (476.22 x 216.73 pt, p.321, xref 371)

Enforces:
1. Pure Grayscale: R = G = B across 100% of pixels (0 tint).
2. Typography: Min font size >= 6.0 pt across all labels.
3. Safe Padding: Margin from text bounding box to card borders >= 4.0 pt.
4. Source Fidelity: 100% alignment with actual lab code, structs, constants, and API contracts.
"""

from __future__ import annotations

import math
from pathlib import Path
import sys

# Ensure scripts directory is in path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import pymupdf
from reportlab.graphics.shapes import Drawing, Group, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

from build_pdf import register_fonts

# ----------------------------------------------------------------------
# Pure Grayscale Editorial Palette (R = G = B)
# ----------------------------------------------------------------------
COLOR_WHITE = colors.HexColor("#FFFFFF")
COLOR_BG_SUBTLE = colors.HexColor("#F8F8F8")
COLOR_BG_HEADER = colors.HexColor("#EEEEEE")
COLOR_BG_CARD = colors.HexColor("#FFFFFF")
COLOR_TAG_BG = colors.HexColor("#E2E2E2")
COLOR_TAG_ACTIVE = colors.HexColor("#D0D0D0")

COLOR_BORDER = colors.HexColor("#777777")
COLOR_BORDER_LIGHT = colors.HexColor("#CCCCCC")
COLOR_BORDER_DARK = colors.HexColor("#333333")

COLOR_INK_DARK = colors.HexColor("#1A1A1A")
COLOR_INK_MID = colors.HexColor("#444444")
COLOR_INK_MUTED = colors.HexColor("#666666")


def draw_arrow(
    d: Drawing,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: colors.HexColor = COLOR_INK_DARK,
    width: float = 1.0,
    head_size: float = 3.6,
    dashed: bool = False,
) -> None:
    """Draw a clean vector arrow with an equilateral arrowhead."""
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-4:
        return

    ux = dx / length
    uy = dy / length

    # Base line
    line = Line(x1, y1, x2 - ux * (head_size * 0.7), y2 - uy * (head_size * 0.7))
    line.strokeColor = color
    line.strokeWidth = width
    if dashed:
        line.strokeDashArray = [3, 2]
    d.add(line)

    # Arrowhead polygon
    cx = x2
    cy = y2
    left_x = cx - head_size * ux + (head_size * 0.5) * uy
    left_y = cy - head_size * uy - (head_size * 0.5) * ux
    right_x = cx - head_size * ux - (head_size * 0.5) * uy
    right_y = cy - head_size * uy + (head_size * 0.5) * ux

    head = Polygon(
        [cx, cy, left_x, left_y, right_x, right_y],
        fillColor=color,
        strokeColor=color,
        strokeWidth=0.4,
    )
    d.add(head)


# ======================================================================
# 1. Chapter 16 — Figure 27: Observability Projections (476.22 x 312.02 pt)
# ======================================================================
def build_observability_projections_drawing(w: float = 476.22, h: float = 312.02) -> Drawing:
    """Figure 27: Các phép chiếu quan sát hệ thống (Observability Projections).

    Mental model: 4 signal độc lập xuất phát từ cùng sự kiện hệ thống;
    mỗi signal trả lời một câu hỏi kỹ thuật hẹp và đánh đổi phần còn lại.
    Exact dimensions: 476.22 x 312.02 pt (Page 283, xref 328).
    """
    register_fonts()
    d = Drawing(w, h)

    # Canvas Background Frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    # Top Header Banner
    header_h = 24.0
    header_y = h - header_h - 4.0
    d.add(Rect(4.0, header_y, w - 8.0, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(8.0, header_y + 4.5, 96.0, 15.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 16 // HÌNH 27", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "CÁC PHÉP CHIẾU QUAN SÁT HỆ THỐNG (OBSERVABILITY PROJECTIONS)", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Mô hình tư duy định hướng: mỗi signal trả lời một câu hỏi kỹ thuật hẹp và chấp nhận đánh đổi.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Central Event Input Card (Top Section)
    event_y = header_y - 34.0
    event_w = w - 16.0
    d.add(Rect(8.0, event_y, event_w, 28.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(12.0, event_y + 16.0, 42.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(33.0, event_y + 18.5, "SỰ KIỆN", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(60.0, event_y + 18.0, "SỰ KIỆN HỆ THỐNG / BOUNDARY EXECUTION (Event / Probe Execution)", fontName="BookSansBold", fontSize=6.5, fillColor=COLOR_INK_DARK))
    d.add(String(12.0, event_y + 6.0, "• Nguồn dữ liệu gốc duy nhất (HTTP request, worker task, dependency call); cung cấp bằng chứng cho 4 góc nhìn độc lập:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Downward connection arrows from Event card to 4 Projection cards
    col_w = (w - 24.0) / 2.0  # 226.11 pt each
    col1_x = 8.0
    col2_x = 16.0 + col_w
    row1_y = event_y - 105.0  # Height 98 pt
    row2_y = row1_y - 105.0   # Height 98 pt
    card_h = 98.0

    draw_arrow(d, col1_x + col_w / 2.0, event_y, col1_x + col_w / 2.0, event_y - 7.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, col2_x + col_w / 2.0, event_y, col2_x + col_w / 2.0, event_y - 7.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # ------------------------------------------------------------------
    # Card 1: NHẬT KÝ (LOGS) - Top Left
    # ------------------------------------------------------------------
    d.add(Rect(col1_x, row1_y, col_w, card_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 4.0, row1_y + card_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 12.0, row1_y + card_h - 10.5, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 24.0, row1_y + card_h - 10.5, "NHẬT KÝ (LOGS) // IDENTITY & CHI TIẾT", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, row1_y + 71.0, "Câu hỏi: \"Lần probe / request này fail vì sao?\"", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, row1_y + 60.5, "• Bằng chứng giữ lại: JSON có cấu trúc (structured log)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 12.0, row1_y + 51.5, "Fields: mode, outcome, status, duration_ms, error", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, row1_y + 41.5, "• Bản chất: Giữ identity & event detail để điều tra cá thể", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, row1_y + 31.0, "• Tránh: Không parse output trace như application log", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(Rect(col1_x + 4.0, row1_y + 6.0, col_w - 8.0, 18.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, row1_y + 15.5, "[ĐÁNH ĐỔI] Không tự chứng minh tần suất hay tỷ lệ", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, row1_y + 8.5, "failure toàn hệ thống (không dùng để đo trend).", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Card 2: CHỈ SỐ (METRICS) - Top Right
    # ------------------------------------------------------------------
    d.add(Rect(col2_x, row1_y, col_w, card_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 4.0, row1_y + card_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 12.0, row1_y + card_h - 10.5, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 24.0, row1_y + card_h - 10.5, "CHỈ SỐ (METRICS) // TỔNG HỢP THEO THỜI GIAN", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, row1_y + 71.0, "Câu hỏi: \"Tần suất lỗi / timeout tăng từ khi nào?\"", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, row1_y + 60.5, "• Bằng chứng giữ lại: Time-series tổng hợp nhiều event", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 12.0, row1_y + 51.5, "Counter: probe_requests_total{outcome=...}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 12.0, row1_y + 42.5, "Histogram: probe_request_duration_seconds", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, row1_y + 32.5, "• Tránh: Cardinality không giới hạn (không nhét URL/ID vào label)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(Rect(col2_x + 4.0, row1_y + 6.0, col_w - 8.0, 18.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, row1_y + 15.5, "[ĐÁNH ĐỔI] Không chỉ ra target hay request cụ thể nào", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, row1_y + 8.5, "là nguyên nhân (chỉ có con số thống kê tổng hợp).", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Card 3: DẤU VẾT (TRACES) - Bottom Left
    # ------------------------------------------------------------------
    d.add(Rect(col1_x, row2_y, col_w, card_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 4.0, row2_y + card_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 12.0, row2_y + card_h - 10.5, "03", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 24.0, row2_y + card_h - 10.5, "DẤU VẾT (TRACES) // QUAN HỆ NHÂN QUẢ", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, row2_y + 71.0, "Câu hỏi: \"Lần chạy này chờ ở boundary / dependency nào?\"", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, row2_y + 60.5, "• Bằng chứng giữ lại: Cây Span có quan hệ Parent-Child", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 12.0, row2_y + 51.5, "Root Span: probe.request (Server)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 12.0, row2_y + 42.5, "Child Span: probe.dependency -> RecordError(err)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, row2_y + 32.5, "• Context propagation truyền TraceID / SpanID qua ranh giới mạng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(Rect(col1_x + 4.0, row2_y + 6.0, col_w - 8.0, 18.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, row2_y + 15.5, "[ĐÁNH ĐỔI] Không phản ánh tần suất toàn hệ thống nếu", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, row2_y + 8.5, "bị sampling; chi phí lưu trữ và truyền context lớn.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Card 4: SỨC KHỎE (HEALTH) - Bottom Right
    # ------------------------------------------------------------------
    d.add(Rect(col2_x, row2_y, col_w, card_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 4.0, row2_y + card_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 12.0, row2_y + card_h - 10.5, "04", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 24.0, row2_y + card_h - 10.5, "SỨC KHỎE (HEALTH) // CONTRACT CONTROL PLANE", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, row2_y + 71.0, "Câu hỏi: \"Có nên đưa traffic vào instance này ngay bây giờ?\"", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, row2_y + 60.5, "• Bằng chứng giữ lại: Tín hiệu nhị phân (OK / Không OK)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 12.0, row2_y + 51.5, "Liveness (/livez): Process còn sống (tránh restart mù)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 12.0, row2_y + 42.5, "Readiness (/readyz): Sẵn sàng nhận việc (bật traffic)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, row2_y + 32.5, "• Phục vụ quyết định tức thời của Orchestrator (Kubelet probe)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(Rect(col2_x + 4.0, row2_y + 6.0, col_w - 8.0, 18.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, row2_y + 15.5, "[ĐÁNH ĐỔI] Không chứng minh SLO quá khứ (không nói", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, row2_y + 8.5, "về tính khả dụng 24h trước; chỉ có giá trị tại hiện tại).", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Bốn tín hiệu là 4 phép chiếu độc lập; không có tín hiệu nào là bản ghi toàn vẹn có thể thay thế các tín hiệu còn lại.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 2. Chapter 16 — Figure 28: Probe Observation Path (476.22 x 264.46 pt)
# ======================================================================
def build_probe_observation_path_drawing(w: float = 476.22, h: float = 264.46) -> Drawing:
    """Figure 28: Các đường ghi nhận kết quả của một request probe.

    Phân luồng độc lập: một request vào /probe phát sinh đồng thời 4 đường
    ghi nhận bằng chứng riêng biệt (Log, Trace, Counter, Histogram).
    Exact dimensions: 476.22 x 264.46 pt (Page 292, xref 338).
    """
    register_fonts()
    d = Drawing(w, h)

    # Canvas Background Frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    # Top Header Banner
    header_h = 24.0
    header_y = h - header_h - 4.0
    d.add(Rect(4.0, header_y, w - 8.0, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(8.0, header_y + 4.5, 96.0, 15.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 16 // HÌNH 28", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "CÁC ĐƯỜNG GHI NHẬN KẾT QUẢ CỦA MỘT REQUEST PROBE", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Cùng request cung cấp dữ liệu độc lập cho 4 cơ chế; không cơ chế nào sinh ra từ cơ chế khác.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Request Input Box (Top Central Card)
    req_y = header_y - 42.0
    req_w = w - 16.0
    d.add(Rect(8.0, req_y, req_w, 36.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(12.0, req_y + 22.0, 48.0, 10.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(36.0, req_y + 24.5, "INPUT", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(66.0, req_y + 24.0, "MỘT REQUEST CỤ THỂ: curl.exe http://localhost:8080/probe?mode=timeout", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(12.0, req_y + 12.5, "• Nhánh ?mode=timeout: runDependency tạo context.WithTimeout(ctx, 20ms) -> Quá hạn trả 504 Gateway Timeout", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(12.0, req_y + 5.0, "• Đo duration := time.Since(started); handler phát 4 tín hiệu độc lập theo outcome (thời gian là minh họa runtime):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # 4 Output Channels (Columns side by side)
    col_w = (w - 32.0) / 4.0  # 111.05 pt each
    col_gap = 5.33
    cards_y = 30.0
    cards_h = req_y - cards_y - 8.0  # 156.0 pt

    cols_data = [
        (
            "01",
            "LOG (JSON)",
            "STDERR",
            "Structured Log Record:",
            '• mode: "timeout"',
            '• outcome: "timeout"',
            '• status: 504',
            '• duration_ms: ~20 (đo)',
            "• Lưu vết sự kiện cụ thể",
            "• Giữ identity & event",
            "• Tách riêng với stdout trace",
            "• Dùng điều tra cá thể",
        ),
        (
            "02",
            "TRACE (SPANS)",
            "OTEL",
            "Span Hierarchy:",
            "• Server: probe.request",
            "• Child: probe.dependency",
            "• Error: codes.Error",
            "• Attr: probe.mode",
            "• Cây Span cha - con",
            "• Bắt điểm nghẽn boundary",
            "• Ghi nhận event timeout",
            "• Nối mạng phân tán",
        ),
        (
            "03",
            "COUNTER (RATE)",
            "PROMETHEUS",
            "Ghi nhận Counter Inc:",
            "  probe_requests_total",
            '  outcome="timeout"',
            "• Phương thức: Inc()",
            "• Tăng bộ đếm theo nhãn",
            "• Đếm số lần hoàn tất",
            "• Bounded label outcome",
            "• Tính toán Availability SLI",
            "• Mẫu số không bị mất",
        ),
        (
            "04",
            "HISTOGRAM (LATENCY)",
            "PROMETHEUS",
            "Ghi nhận Histogram Observe:",
            "  probe_request_",
            "  duration_seconds",
            "• Đo: Observe(seconds)",
            "• Buckets: 5ms..250ms",
            "• Phân bố thời gian chạy",
            "• Nhận diện đuôi chậm p99",
            "• Không nghẽn cardinality",
            "• Đánh giá SLO thời gian",
        ),
    ]

    for idx, cdata in enumerate(cols_data):
        cx = 8.0 + idx * (col_w + col_gap)
        arrow_x = cx + col_w / 2.0
        draw_arrow(d, arrow_x, req_y, arrow_x, req_y - 6.5, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

        # Card container
        d.add(Rect(cx, cards_y, col_w, cards_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))

        # Card Header
        d.add(Rect(cx + 3.0, cards_y + cards_h - 13.0, 15.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(String(cx + 10.5, cards_y + cards_h - 10.5, cdata[0], fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
        d.add(String(cx + 22.0, cards_y + cards_h - 10.5, cdata[1], fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

        # Code Box inside Card
        code_box_h = 60.0
        code_box_y = cards_y + cards_h - 17.0 - code_box_h
        d.add(Rect(cx + 3.0, code_box_y, col_w - 6.0, code_box_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(Rect(cx + 5.0, code_box_y + code_box_h - 10.0, 44.0, 8.5, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.4, rx=1.0, ry=1.0))
        d.add(String(cx + 27.0, code_box_y + code_box_h - 7.5, cdata[2], fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

        # Code lines (All font sizes >= 6.0 pt)
        d.add(String(cx + 5.0, code_box_y + 39.0, cdata[3], fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(cx + 5.0, code_box_y + 30.0, cdata[4], fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(cx + 5.0, code_box_y + 21.0, cdata[5], fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(cx + 5.0, code_box_y + 12.0, cdata[6], fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(cx + 5.0, code_box_y + 5.0, cdata[7], fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

        # Bullet points (All font sizes >= 6.0 pt)
        d.add(String(cx + 5.0, cards_y + 54.0, cdata[8], fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(cx + 5.0, cards_y + 42.0, cdata[9], fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
        d.add(String(cx + 5.0, cards_y + 30.0, cdata[10], fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
        d.add(String(cx + 5.0, cards_y + 18.0, cdata[11], fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
        d.add(String(cx + 5.0, cards_y + 6.0, "• Không phụ thuộc nhánh khác", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Bottom Invariant Footer Banner
    footer_h = 20.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 11.5, "• Ranh giới kỹ thuật: Cùng một request cung cấp dữ liệu cho cả 4 nhánh; không có nhánh nào sinh ra từ nhánh khác.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(8.0, footer_y + 4.5, "• Console trace và JSON log được tách stdout / stderr có chủ ý; tuyệt đối không parse output trace như log application.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    return d


# ======================================================================
# 3. Chapter 17 — Figure 29: Reconciliation Loop (335.89 x 362.83 pt)
# ======================================================================
def build_reconciliation_loop_drawing(w: float = 335.89, h: float = 362.83) -> Drawing:
    """Figure 29: Vòng lặp điều hòa (Reconciliation Loop).

    Mô hình điều khiển kín: Desired State (Spec) vs Observed State (Status);
    Controller tính NextAction (Create, Delete, None) để hội tụ liên tục.
    Exact dimensions: 335.89 x 362.83 pt (Page 300, xref 347).
    """
    register_fonts()
    d = Drawing(w, h)

    # Canvas Background Frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    # Top Header Banner
    header_h = 24.0
    header_y = h - header_h - 4.0
    d.add(Rect(4.0, header_y, w - 8.0, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(8.0, header_y + 4.5, 96.0, 15.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 17 // HÌNH 29", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "VÒNG LẶP ĐIỀU HÒA (RECONCILIATION LOOP)", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Desired State là đầu vào bền vững; Controller liên tục hội tụ trạng thái qua thời gian.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    card_x = 8.0
    card_w = w - 16.0  # 319.89 pt

    # ------------------------------------------------------------------
    # Card 1: TRẠNG THÁI MONG MUỐN (DESIRED STATE / SPEC) - Top
    # ------------------------------------------------------------------
    c1_h = 66.0
    c1_y = 258.0
    d.add(Rect(card_x, c1_y, card_w, c1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 4.0, c1_y + c1_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 12.0, c1_y + c1_h - 10.5, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 24.0, c1_y + c1_h - 10.5, "TRẠNG THÁI MONG MUỐN (DESIRED STATE / SPEC)", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, c1_y + 41.5, "Khai báo bền vững qua YAML manifest / API Server:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 10.0, c1_y + 30.5, "spec.replicas: 1 (lab manifest) · image: probe-api:dev", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, c1_y + 19.5, "• Kịch bản mở rộng: replicas: 3; health probes /livez, /readyz", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 6.0, c1_y + 8.5, "• Đầu vào bền vững; áp dụng declarative configuration thay cho mệnh lệnh.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Downward arrow to Controller
    draw_arrow(d, card_x + card_w * 0.25, c1_y, card_x + card_w * 0.25, 248.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # ------------------------------------------------------------------
    # Card 2: BỘ ĐIỀU KHIỂN KHÁI NIỆM & HÀM LAB NEXTACTION - Middle
    # ------------------------------------------------------------------
    c2_h = 156.0
    c2_y = 92.0
    d.add(Rect(card_x, c2_y, card_w, c2_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.9, rx=2, ry=2))
    d.add(Rect(card_x + 4.0, c2_y + c2_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 12.0, c2_y + c2_h - 10.5, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 24.0, c2_y + c2_h - 10.5, "BỘ ĐIỀU KHIỂN KHÁI NIỆM & HÀM LAB NEXTACTION", fontName="BookSansBold", fontSize=6.4, fillColor=COLOR_INK_DARK))

    # Sub-card 2A: OBSERVE
    s_w = card_w - 12.0
    s_x = card_x + 6.0
    s2a_y = c2_y + 98.0
    d.add(Rect(s_x, s2a_y, s_w, 42.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(s_x + 6.0, s2a_y + 32.5, "BƯỚC 1: QUAN SÁT (OBSERVE) // Đọc qua Kubernetes API Server", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(s_x + 10.0, s2a_y + 23.5, "obs := Describe(deployment); current := int(obs.Available)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(s_x + 6.0, s2a_y + 14.5, "• Thu nhận ObservedGeneration, Desired, Available replicas", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(s_x + 6.0, s2a_y + 5.5, "• Lưu ý bất biến: Observation có thể trễ so với trạng thái cụm thực tế.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Sub-card 2B: DIFF (NextAction)
    s2b_y = c2_y + 46.0
    d.add(Rect(s_x, s2b_y, s_w, 46.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(s_x + 6.0, s2b_y + 36.5, "BƯỚC 2: PHÁN ĐOÁN // act, err := fixed.NextAction(desired, current)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(s_x + 10.0, s2b_y + 27.5, "• current < desired => Action{Kind: ActionCreate, Count: desired-current}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(s_x + 10.0, s2b_y + 18.0, "• current > desired => Action{Kind: ActionDelete, Count: current-desired}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(s_x + 10.0, s2b_y + 8.5, "• current == desired => Action{Kind: ActionNone} (Chưa cần đổi số replica)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Sub-card 2C: ACT
    s2c_y = c2_y + 6.0
    d.add(Rect(s_x, s2c_y, s_w, 34.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(s_x + 6.0, s2c_y + 25.5, "BƯỚC 3: HÀNH ĐỘNG (ACT) // Controller thực thi từng bước", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(s_x + 6.0, s2c_y + 15.5, "• NextAction là hàm thuần túy (pure function); không trực tiếp tạo/xóa Pod.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(s_x + 6.0, s2c_y + 5.5, "• ActionNone chưa đồng nghĩa toàn bộ hội tụ (rollout có thể đang cập nhật).", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Bidirectional connection arrows between Controller and Workload
    act_arrow_x = card_x + card_w * 0.35
    obs_arrow_x = card_x + card_w * 0.75
    draw_arrow(d, act_arrow_x, c2_y, act_arrow_x, 84.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, obs_arrow_x, 84.0, obs_arrow_x, c2_y, color=COLOR_INK_DARK, width=0.8, head_size=3.0, dashed=True)

    # ------------------------------------------------------------------
    # Card 3: WORKLOAD ĐƯỢC ĐIỀU KHIỂN (CONTROLLED WORKLOAD) - Bottom
    # ------------------------------------------------------------------
    c3_h = 56.0
    c3_y = 28.0
    d.add(Rect(card_x, c3_y, card_w, c3_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 4.0, c3_y + c3_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 12.0, c3_y + c3_h - 10.5, "03", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(card_x + 24.0, c3_y + c3_h - 10.5, "WORKLOAD TRÊN NODE (CONTROLLED WORKLOAD / PODS)", fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, c3_y + 32.5, "Các tiến trình Pod thực tế chạy trên các Node máy chủ:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 10.0, c3_y + 22.5, "Runtime: probe-api instances (PID 1) · Kubelet livez / readyz checks", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 6.0, c3_y + 13.5, "• Trạng thái biến động: Pod có thể bị OOM kill, restart, hoặc mất mạng.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 6.0, c3_y + 5.5, "• Pod Running chưa đồng nghĩa mọi container đều Ready nhận traffic.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Bottom Invariant Footer Banner
    footer_h = 18.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 10.5, "• Invariant: Một vòng lặp không cam kết đạt trạng thái cuối ngay tức thì.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(8.0, footer_y + 4.5, "• Reconciliation là quá trình hội tụ liên tục qua các chu kỳ Reconcile độc lập.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    return d


# ======================================================================
# 4. Chapter 17 — Figure 31: Container Cluster Observation (476.22 x 238.11 pt)
# ======================================================================
def build_container_cluster_observation_drawing(w: float = 476.22, h: float = 238.11) -> Drawing:
    """Figure 31: Từ image đến workload và quan sát trong cluster.

    Kiến trúc ranh giới: Image OCI -> Kubernetes Deployment/Service/Pod ->
    Go Observer (client-go) chẩn đoán chỉ đọc qua API Server.
    Exact dimensions: 476.22 x 238.11 pt (Page 310, xref 359).
    """
    register_fonts()
    d = Drawing(w, h)

    # Canvas Background Frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    # Top Header Banner
    header_h = 24.0
    header_y = h - header_h - 4.0
    d.add(Rect(4.0, header_y, w - 8.0, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(8.0, header_y + 4.5, 96.0, 15.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 17 // HÌNH 31", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "TỪ IMAGE ĐẾN WORKLOAD VÀ QUAN SÁT TRONG CLUSTER", fontName="BookSansBold", fontSize=7.2, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Phân định ranh giới giữa Artifact, Workload điều phối và Chẩn đoán quan sát.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # 3 Major Sections
    body_y = 28.0
    body_h = header_y - body_y - 6.0  # 174.0 pt

    col1_w = 118.0
    col2_w = 208.0
    col3_w = 126.0

    col1_x = 8.0
    col2_x = col1_x + col1_w + 6.0  # 132.0
    col3_x = col2_x + col2_w + 6.0  # 346.0

    # ------------------------------------------------------------------
    # Section 1: IMAGE SAU BUILD (ARTIFACT BOUNDARY)
    # ------------------------------------------------------------------
    d.add(Rect(col1_x, body_y, col1_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 12.0, body_y + body_h - 10.5, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 24.0, body_y + body_h - 10.5, "IMAGE SAU BUILD", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col1_x + 6.0, body_y + 144.0, "Tag hình ảnh (Local):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, body_y + 134.5, "probe-api:dev (Mutable)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, body_y + 124.0, "• Khác OCI Manifest Digest", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(col1_x + 6.0, body_y + 112.5, "• Multi-stage build:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 10.0, body_y + 103.5, "CGO_ENABLED=0 -trimpath", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, body_y + 91.5, "• Base image tối giản:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 10.0, body_y + 82.5, "distroless:nonroot", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, body_y + 70.5, "• Process Contract (Dockerfile):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, body_y + 61.5, "USER 65532:65532", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, body_y + 52.0, "ENTRYPOINT [\"/probe-api\"]", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, body_y + 40.0, "• Không shell, không CMD", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(col1_x + 6.0, body_y + 31.0, "• PID 1 nhận trực tiếp signal", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(Rect(col1_x + 4.0, body_y + 6.0, col1_w - 8.0, 22.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, body_y + 16.5, "Đóng gói filesystem bền vững;", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, body_y + 9.0, "tag :dev có thể bị trôi dạt.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Section 2: KUBERNETES WORKLOAD & TRAFFIC BOUNDARY
    # ------------------------------------------------------------------
    d.add(Rect(col2_x, body_y, col2_w, body_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.9, rx=2, ry=2))
    d.add(Rect(col2_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 12.0, body_y + body_h - 10.5, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 24.0, body_y + body_h - 10.5, "KUBERNETES WORKLOAD & RUNTIME BOUNDARY", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    # Box 2A: Deployment (Spec) - Top Box (h = 44.0 pt)
    b2a_y = body_y + body_h - 60.0
    d.add(Rect(col2_x + 6.0, b2a_y, col2_w - 12.0, 44.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(col2_x + 10.0, b2a_y + 32.5, "DEPLOYMENT // Khai báo Desired State (YAML Manifest)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2a_y + 22.5, "• spec.replicas: 1 · image: probe-api:dev (local tag)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2a_y + 13.5, "• Liveness: /livez (5s) · Readiness: /readyz (3s)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2a_y + 5.0, "• Quản lý lifecycle Pod; ví dụ replicas=3 là kịch bản mở rộng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 2B: Pod Runtime on Nodes - Middle Box (h = 46.0 pt)
    b2b_y = b2a_y - 56.0
    d.add(Rect(col2_x + 6.0, b2b_y, col2_w - 12.0, 46.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(col2_x + 10.0, b2b_y + 34.5, "POD RUNTIME TRÊN NODE (Containerd + Kubelet)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2b_y + 24.5, "• Tiến trình Go thật (PID 1): cgroup limit CPU/RAM, distroless", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 10.0, b2b_y + 14.5, "• Nhận trực tiếp SIGTERM graceful drain; không shell parent", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 10.0, b2b_y + 5.0, "• Bất biến: Pod Running != mọi container đều Ready nhận traffic", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 2C: Service - Bottom Box (h = 44.0 pt)
    b2c_y = body_y + 5.0
    d.add(Rect(col2_x + 6.0, b2c_y, col2_w - 12.0, 44.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(col2_x + 10.0, b2c_y + 33.5, "SERVICE // Định tuyến lưu lượng (Traffic Routing)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2c_y + 24.5, "• selector: app.kubernetes.io/name: probe-api", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2c_y + 15.0, "• Service chỉ định tuyến traffic tới Pod có condition Ready", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2c_y + 5.5, "• (EndpointSlice vẫn lưu Pod; Service chỉ gửi traffic khi readyz OK)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrows in Section 2:
    # 1. Deployment (Top) down to Pod Runtime (Middle) -> Reconcile Pods
    draw_arrow(d, col2_x + 60.0, b2a_y, col2_x + 60.0, b2b_y + 46.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    # 2. Service (Bottom) UP to Pod Runtime (Middle) -> Selector filters Endpoint & routes traffic
    draw_arrow(d, col2_x + 140.0, b2c_y + 44.0, col2_x + 140.0, b2b_y, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Arrow from Image (Section 1) to Pod Runtime (Section 2)
    draw_arrow(d, col1_x + col1_w, b2b_y + 23.0, col2_x, b2b_y + 23.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Dashed Arrow from Deployment to Section 3 Observer (Query via Kube-API Server)
    draw_arrow(d, col2_x + col2_w, b2a_y + 22.0, col3_x, b2a_y + 22.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0, dashed=True)

    # ------------------------------------------------------------------
    # Section 3: OBSERVER Go (CLIENT-GO / API BOUNDARY)
    # ------------------------------------------------------------------
    d.add(Rect(col3_x, body_y, col3_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col3_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 12.0, body_y + body_h - 10.5, "03", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col3_x + 24.0, body_y + body_h - 10.5, "OBSERVER Go (VIA KUBE-API)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col3_x + 6.0, body_y + 144.0, "client-go Observer:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 6.0, body_y + 134.5, "type Observation struct {", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10.0, body_y + 125.5, "Generation         int64", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10.0, body_y + 116.5, "ObservedGeneration int64", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10.0, body_y + 107.5, "Desired            int32", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10.0, body_y + 98.5, "Updated            int32", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10.0, body_y + 89.5, "Available          int32", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 6.0, body_y + 80.5, "}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 6.0, body_y + 68.0, "• Ranh giới chỉ đọc (Read-only):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 6.0, body_y + 58.5, "• Truy vấn qua Kube-API Server (Get/Watch)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 6.0, body_y + 49.0, "• Không nhận push; chủ động thăm dò", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 6.0, body_y + 39.5, "• Không can thiệp node / container", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    d.add(Rect(col3_x + 4.0, body_y + 6.0, col3_w - 8.0, 28.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, body_y + 22.0, "Observation có thể trễ so với", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, body_y + 14.0, "phần cứng; chỉ phản ánh điều", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, body_y + 6.5, "API Server quan sát được.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Observer chỉ chẩn đoán trạng thái qua API (Get/Watch); Pod chỉ được nhận traffic khi probe /readyz được kubelet xác nhận đạt chuẩn.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 5. Chapter 18 — Figure 32: Delivery Evidence Chain (476.22 x 216.73 pt)
# ======================================================================
def build_delivery_evidence_chain_drawing(w: float = 476.22, h: float = 216.73) -> Drawing:
    """Figure 32: Chuỗi bằng chứng của một quy trình phân phối (Delivery Evidence Chain).

    Quy trình phân phối là chuỗi khế ước thu hẹp liên tục:
    Bố cục zíc-zắc (Boustrophedon) 2 hàng, dòng chảy 1 chiều không giao cắt:
    Hàng 1 (trên, Trái sang Phải): [01] Source Revision -> [02] Build Artifact -> [03] Kiểm thử
    Chuyển hàng: [03] rẽ xuống [04]
    Hàng 2 (dưới, Phải sang Trái): [04] Cổng chính sách -> [05] Desired State -> [06] Quan sát rollout.
    Exact dimensions: 476.22 x 216.73 pt (Page 321, xref 371).
    """
    register_fonts()
    d = Drawing(w, h)

    # Canvas Background Frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    # Top Header Banner
    header_h = 24.0
    header_y = h - header_h - 4.0
    d.add(Rect(4.0, header_y, w - 8.0, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(8.0, header_y + 4.5, 96.0, 15.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 18 // HÌNH 32", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "CHUỖI BẰNG CHỨNG CỦA MỘT QUY TRÌNH PHÂN PHỐI (DELIVERY EVIDENCE CHAIN)", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Một delivery đáng tin cậy là chuỗi khế ước thu hẹp: mỗi gate chỉ xác minh bằng chứng thuộc phạm vi của nó.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # 2 Rows of 3 Cards each (Continuous Zic-zac flow, strictly >= 6.0 pt)
    card_gap_x = 8.0
    card_w = (w - 16.0 - 2 * card_gap_x) / 3.0  # 148.07 pt each
    row_h = 72.0
    row1_y = 106.0
    row2_y = 24.0

    cards_info = [
        # Row 1: Left to Right (Col 0 -> Col 1 -> Col 2)
        (
            0, row1_y, "01", "SOURCE REVISION", "GIT COMMIT",
            "commitSHA (Git Commit SHA)",
            "• Nhận diện commit hash đầu vào",
            "• Khác Git tree hash; đã review PR",
            "[CHƯA NÓI] Chưa chứng minh artifact",
            "nào thật sự được build từ source này.",
        ),
        (
            1, row1_y, "02", "BUILD ARTIFACT", "OCI DIGEST",
            "sha256:7f8a... (OCI Digest)",
            "• Định danh byte manifest bất biến",
            "• Khác Docker Image Config ID; :dev",
            "[CHƯA NÓI] Chưa chứng minh artifact",
            "đã qua kiểm thử hay build provenance.",
        ),
        (
            2, row1_y, "03", "BẰNG CHỨNG KIỂM THỬ", "EVIDENCE",
            "candidate.TestsPassed == true",
            "• Booleans đầu vào trong lab struct",
            "• Không thay thế attestation chữ ký",
            "[CHƯA NÓI] Chưa chứng minh hành vi",
            "khi chạy thực tế trên production.",
        ),
        # Row 2: Right to Left (Col 2 -> Col 1 -> Col 0)
        (
            2, row2_y, "04", "CỔNG CHÍNH SÁCH", "ADMISSION",
            "Evaluate(candidate) -> Decision",
            "• Kiểm tra format digest & revision",
            "• Chỉ cấp Allowed khi đủ cờ boolean",
            "[CHƯA NÓI] Chưa bảo đảm rollout",
            "sẽ thành công không gặp lỗi runtime.",
        ),
        (
            1, row2_y, "05", "CẬP NHẬT DESIRED STATE", "SPEC.IMAGE",
            "Pod template image ← Digest",
            "• Gán Digest bất biến vào Spec Pod",
            "• Lab: replicas=1; mở rộng: 3/3",
            "[CHƯA NÓI] Chưa chứng minh traffic",
            "người dùng thật đã được phục vụ.",
        ),
        (
            0, row2_y, "06", "QUAN SÁT PHÁT HÀNH", "ROLLOUT OK",
            "Available == Desired (Controller)",
            "• Kèm: Updated==Desired & Gen khớp",
            "• Pod vượt qua probe /readyz (200)",
            "[CHƯA NÓI] Chỉ kết luận controller hội tụ;",
            "không thay thế cam kết SLO 24h & lỗi trễ.",
        ),
    ]

    for col_idx, ry, badge, title, tag, code_line, b1, b2, lim1, lim2 in cards_info:
        cx = 8.0 + col_idx * (card_w + card_gap_x)

        # Card container
        d.add(Rect(cx, ry, card_w, row_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))

        # Card Header
        d.add(Rect(cx + 3.0, ry + row_h - 13.0, 15.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(String(cx + 10.5, ry + row_h - 10.5, badge, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
        d.add(String(cx + 22.0, ry + row_h - 10.5, title, fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

        # Tag (dynamically sized, strictly >= 6.0 pt)
        w_tag = stringWidth(tag, "BookMono", 6.0)
        tag_box_w = w_tag + 6.0
        tag_box_x = cx + card_w - tag_box_w - 3.0
        d.add(Rect(tag_box_x, ry + row_h - 13.0, tag_box_w, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.4, rx=1.0, ry=1.0))
        d.add(String(tag_box_x + tag_box_w / 2.0, ry + row_h - 10.5, tag, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

        # Identifier / Concept line
        d.add(String(cx + 5.0, ry + 48.0, code_line, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

        # Bullets
        d.add(String(cx + 5.0, ry + 38.5, b1, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
        d.add(String(cx + 5.0, ry + 29.5, b2, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

        # Limitation Box
        lim_h = 22.0
        lim_y = ry + 4.5
        d.add(Rect(cx + 3.0, lim_y, card_w - 6.0, lim_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(String(cx + 6.0, lim_y + 13.5, lim1, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(cx + 6.0, lim_y + 5.0, lim2, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Flow arrows: Continuous Boustrophedon / Zíc-zắc pipeline
    # Row 1 (Left to Right): 01 -> 02 -> 03
    draw_arrow(d, 8.0 + card_w, row1_y + row_h / 2.0, 8.0 + card_w + card_gap_x, row1_y + row_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, 8.0 + 2 * card_w + card_gap_x, row1_y + row_h / 2.0, 8.0 + 2 * card_w + 2 * card_gap_x, row1_y + row_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Downward turn arrow: From Card 03 (Col 2, Row 1) down into Card 04 (Col 2, Row 2)
    turn_x = 8.0 + 2 * card_w + 2 * card_gap_x + card_w / 2.0
    draw_arrow(d, turn_x, row1_y, turn_x, row2_y + row_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Row 2 (Right to Left): 04 -> 05 -> 06
    # From Card 04 (Col 2) left edge to Card 05 (Col 1) right edge
    draw_arrow(d, 8.0 + 2 * card_w + 2 * card_gap_x, row2_y + row_h / 2.0, 8.0 + 2 * card_w + card_gap_x, row2_y + row_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    # From Card 05 (Col 1) left edge to Card 06 (Col 0) right edge
    draw_arrow(d, 8.0 + card_w + card_gap_x, row2_y + row_h / 2.0, 8.0 + card_w, row2_y + row_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Chuỗi phân phối là khế ước thu hẹp liên tục (01→06); controller hội tụ xác nhận Pod đạt desired state, không thay thế cam kết SLO 24h.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# Export Routine for all 5 diagrams
# ======================================================================
def export_diagrams_to_png(dpi: int = 320) -> dict[str, Path]:
    """Export all 5 vector drawings to pure grayscale PNGs in assets/diagrams/."""
    diagrams_dir = ROOT / "assets/diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)

    diagram_specs = [
        ("observability-projections.png", build_observability_projections_drawing, 476.22, 312.02),
        ("probe-observation-path.png", build_probe_observation_path_drawing, 476.22, 264.46),
        ("reconciliation-loop.png", build_reconciliation_loop_drawing, 335.89, 362.83),
        ("container-cluster-observation.png", build_container_cluster_observation_drawing, 476.22, 238.11),
        ("delivery-evidence-chain.png", build_delivery_evidence_chain_drawing, 476.22, 216.73),
    ]

    out_paths = {}
    for filename, builder_func, w, h in diagram_specs:
        out_file = diagrams_dir / filename
        drawing = builder_func(w, h)

        # Render to high-DPI PDF bytes in memory, then convert to PNG pixmap
        pdf_bytes = drawing.asString("pdf")
        doc = pymupdf.open("pdf", pdf_bytes)
        page = doc[0]
        pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
        pix.save(str(out_file))
        doc.close()

        out_paths[filename] = out_file
        print(f"Exported: {out_file} ({pix.width}x{pix.height} px, {out_file.stat().st_size} bytes)")

    return out_paths


if __name__ == "__main__":
    export_diagrams_to_png()
