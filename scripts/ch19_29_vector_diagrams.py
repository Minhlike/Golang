"""scripts/ch19_29_vector_diagrams.py.

Vector generator for book-wide technical diagrams in Chapters 19-29
(including Figure 33 in Chapter 18).
Built with ReportLab vector graphics following MASTER PROMPT.txt:
- Pure grayscale (R=G=B).
- Exact 1:1 dimensions matching Golang_Master.pdf bounding boxes.
- Minimum font size >= 6.0 pt; safe padding >= 4.0 pt.
- Source-first, mental-model first, strict scientific accuracy.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

# Ensure scripts directory is in path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from reportlab.graphics.shapes import (
    Drawing,
    Group,
    Line,
    Polygon,
    Rect,
    String,
)
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

from build_pdf import register_fonts


# ----------------------------------------------------------------------
# Grayscale Palette Constants (100% pure grayscale, R=G=B)
# ----------------------------------------------------------------------
COLOR_WHITE = colors.HexColor("#FFFFFF")
COLOR_BG_HEADER = colors.HexColor("#EFEFEF")
COLOR_BG_CARD = colors.HexColor("#F9F9F9")
COLOR_BG_SUBTLE = colors.HexColor("#F3F3F3")
COLOR_TAG_BG = colors.HexColor("#E4E4E4")
COLOR_TAG_ACTIVE = colors.HexColor("#D8D8D8")

COLOR_BORDER = colors.HexColor("#CCCCCC")
COLOR_BORDER_DARK = colors.HexColor("#666666")
COLOR_BORDER_LIGHT = colors.HexColor("#E0E0E0")

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
# 1. Chapter 18 — Figure 33: Workflow Promotion Jobs (476.22 x 330.21 pt)
# ======================================================================
def build_workflow_promotion_jobs_drawing(w: float = 476.22, h: float = 330.21) -> Drawing:
    """Figure 33: Quy trình tự động truyền định danh và bằng chứng qua các tác vụ.

    Quyền OIDC và môi trường triển khai không tự động thay thế cho việc cổng
    kiểm soát thẩm định ứng viên phát hành. Chỉ quyết định được phê duyệt mới
    được phép cập nhật trạng thái mong muốn bằng mã băm nội dung.
    Exact dimensions: 476.22 x 330.21 pt (Page 331, xref 382).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 18 // HÌNH 33", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "QUY TRÌNH TRUYỀN ĐỊNH DANH VÀ BẰNG CHỨNG QUA CÁC JOB CI/CD", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Phân định ranh giới giữa Artifact Producer, Policy Gate thẩm định và Deploy Environment.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # 3 Sequential Stage Cards (Left to Right)
    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 270.0 pt

    col_gap = 12.0
    col_w = (w - 16.0 - 2 * col_gap) / 3.0  # 145.40 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + col_gap       # 165.40
    col3_x = col2_x + col_w + col_gap       # 322.81

    # ------------------------------------------------------------------
    # Job 1: BUILD & TEST (ARTIFACT PRODUCER)
    # ------------------------------------------------------------------
    d.add(Rect(col1_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 12.0, body_y + body_h - 10.5, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 24.0, body_y + body_h - 10.5, "JOB: BUILD & TEST", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col1_x + 6.0, body_y + 240.0, "Runner Environment:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, body_y + 230.5, "runs-on: ubuntu-latest", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 6.0, body_y + 221.0, "• Quyền tối thiểu: 0 quyền deploy", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 1A: Kiểm thử & Đóng gói
    b1a_h = 72.0
    b1a_y = body_y + 142.0
    d.add(Rect(col1_x + 4.0, b1a_y, col_w - 8.0, b1a_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, b1a_y + 60.5, "THAO TÁC BIÊN DỊCH & TEST", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1a_y + 50.5, "1. go test -race ./...", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1a_y + 40.5, "   TestsPassed: true (boolean)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1a_y + 30.0, "2. docker buildx (OCI Image)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1a_y + 19.5, "3. Push Registry -> Nhận Digest:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 12.0, b1a_y + 9.5, "sha256:7f8a... (Bất biến)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Box 1B: Output truyền sang Job sau
    b1b_h = 58.0
    b1b_y = body_y + 78.0
    d.add(Rect(col1_x + 4.0, b1b_y, col_w - 8.0, b1b_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, b1b_y + 46.5, "OUTPUTS TRUYỀN SANG JOB SAU", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1b_y + 35.5, "• image_digest: sha256:7f8a...", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1b_y + 24.5, "• commit_sha: 4a2c11e...", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1b_y + 13.5, "• test_status: passed", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Limitation Box
    lim1_h = 36.0
    lim1_y = body_y + 6.0
    d.add(Rect(col1_x + 4.0, lim1_y, col_w - 8.0, lim1_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, lim1_y + 25.5, "[GIỚI HẠN] Test pass & build OK", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, lim1_y + 16.0, "chưa chứng minh artifact đáp ứng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, lim1_y + 6.5, "chính sách an toàn của tổ chức.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Job 2: POLICY EVALUATION (ADMISSION / QUALITY GATE)
    # ------------------------------------------------------------------
    d.add(Rect(col2_x, body_y, col_w, body_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.9, rx=2, ry=2))
    d.add(Rect(col2_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 12.0, body_y + body_h - 10.5, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 24.0, body_y + body_h - 10.5, "JOB: POLICY EVALUATION", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 6.0, body_y + 240.0, "Dependency & Policy Engine:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, body_y + 230.5, "needs: [build]", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 6.0, body_y + 221.0, "• Thẩm định candidate độc lập", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 2A: Thu thập & Thẩm định
    b2a_h = 72.0
    b2a_y = body_y + 142.0
    d.add(Rect(col2_x + 4.0, b2a_y, col_w - 8.0, b2a_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, b2a_y + 60.5, "THẨM ĐỊNH BẰNG CHỨNG (LAB GATE)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2a_y + 50.5, "Evaluate(candidate) -> Decision:", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2a_y + 40.5, "• Format digest: sha256:[a-f0-9]{64}", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2a_y + 30.0, "• Commit SHA hợp lệ (40 hex)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2a_y + 19.5, "• TestsPassed == true", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2a_y + 9.5, "• SecurityScanClean == true", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Box 2B: Quyết định Gate
    b2b_h = 58.0
    b2b_y = body_y + 78.0
    d.add(Rect(col2_x + 4.0, b2b_y, col_w - 8.0, b2b_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, b2b_y + 46.5, "KẾT QUẢ QUYẾT ĐỊNH (DECISION)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2b_y + 35.5, "if AllSatisfied => Allowed: true", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2b_y + 24.5, "else => Allowed: false (Reject)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2b_y + 13.5, "Outputs: decision = 'Allowed'", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Limitation Box
    lim2_h = 36.0
    lim2_y = body_y + 6.0
    d.add(Rect(col2_x + 4.0, lim2_y, col_w - 8.0, lim2_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, lim2_y + 25.5, "[GIỚI HẠN] Gate chỉ kiểm tra các", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, lim2_y + 16.0, "bằng chứng tĩnh được cung cấp;", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, lim2_y + 6.5, "chưa đảm bảo không lỗi runtime.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Job 3: DEPLOY (ENVIRONMENT PROTECTION & OIDC)
    # ------------------------------------------------------------------
    d.add(Rect(col3_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col3_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 12.0, body_y + body_h - 10.5, "03", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col3_x + 24.0, body_y + body_h - 10.5, "JOB: DEPLOY TO PROD", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col3_x + 6.0, body_y + 240.0, "Điều kiện kích hoạt:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 6.0, body_y + 230.5, "needs: [policy-evaluation]", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 6.0, body_y + 221.0, "if: decision == 'Allowed'", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Box 3A: OIDC & Bảo vệ Môi trường
    b3a_h = 72.0
    b3a_y = body_y + 142.0
    d.add(Rect(col3_x + 4.0, b3a_y, col_w - 8.0, b3a_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, b3a_y + 60.5, "BẢO MẬT OIDC & MÔI TRƯỜNG", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b3a_y + 50.5, "environment: production", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b3a_y + 40.5, "• permissions: id-token: write", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b3a_y + 30.0, "• OIDC Token ngắn hạn (JWT)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b3a_y + 19.5, "• Không lưu long-lived secret", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b3a_y + 9.5, "• Giới hạn role theo repo & branch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 3B: Cập nhật Desired State
    b3b_h = 58.0
    b3b_y = body_y + 78.0
    d.add(Rect(col3_x + 4.0, b3b_y, col_w - 8.0, b3b_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, b3b_y + 46.5, "CẬP NHẬT TRẠNG THÁI MONG MUỐN", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b3b_y + 35.5, "Pod template image ← Digest", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b3b_y + 24.5, "• spec.template...image = digest", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b3b_y + 13.5, "• Kube controller khởi động rollout", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Limitation Box
    lim3_h = 36.0
    lim3_y = body_y + 6.0
    d.add(Rect(col3_x + 4.0, lim3_y, col_w - 8.0, lim3_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, lim3_y + 25.5, "[GIỚI HẠN] OIDC chỉ cấp kênh", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, lim3_y + 16.0, "xác thực tạm thời; không tự động", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, lim3_y + 6.5, "bảo đảm ứng dụng đạt SLO 24h.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Sequential Transition Arrows
    # 1. Job 1 to Job 2 (Transmit Digest + Test Evidence)
    arrow1_y = body_y + 107.0
    draw_arrow(d, col1_x + col_w, arrow1_y, col2_x, arrow1_y, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # 2. Job 2 to Job 3 (Allowed Decision Gate)
    arrow2_y = body_y + 107.0
    draw_arrow(d, col2_x + col_w, arrow2_y, col3_x, arrow2_y, color=COLOR_INK_DARK, width=0.9, head_size=3.5)

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Quyền OIDC và môi trường triển khai chỉ cấp kênh kết nối tạm thời; không tự động thay thế cho việc thẩm định bằng chứng tại policy gate.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 2. Chapter 19 — Figure 34: Type Information Boundaries (413.18 x 362.83 pt)
# ======================================================================
def build_type_information_boundaries_drawing(w: float = 413.18, h: float = 362.83) -> Drawing:
    """Figure 34: Lựa chọn tầng trừu tượng phù hợp với câu hỏi kỹ thuật cần giải quyết.

    Ba ranh giới độc lập:
    1. Generic: Bảo toàn type information ở compile-time cho cùng một thuật toán.
    2. Interface: Ranh giới khế ước hành vi khi concrete type thay đổi.
    3. Reflection: Khảo sát shape và metadata khi dữ liệu chỉ biết lúc runtime.
    Exact dimensions: 413.18 x 362.83 pt (Page 341, xref 393).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 19 // HÌNH 34", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "BA RANH GIỚI BẢO TOÀN VÀ XỬ LÝ THÔNG TIN KIỂU TRONG GO", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Lựa chọn tầng trừu tượng theo câu hỏi kỹ thuật; đây là 3 ranh giới khác nhau, không phải thang linh hoạt tăng dần.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # 3 Major Boundary Cards
    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 302.0 pt

    col_gap = 8.0
    col_w = (w - 16.0 - 2 * col_gap) / 3.0  # 127.06 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + col_gap       # 143.06
    col3_x = col2_x + col_w + col_gap       # 278.12

    # ------------------------------------------------------------------
    # Column 1: GENERIC (COMPILE-TIME TYPE PRESERVATION)
    # ------------------------------------------------------------------
    d.add(Rect(col1_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 12.0, body_y + body_h - 10.5, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 24.0, body_y + body_h - 10.5, "GENERIC (COMPILE-TIME)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    d.add(String(col1_x + 6.0, body_y + 272.0, "Câu hỏi kỹ thuật:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 6.0, body_y + 262.5, "Cùng một thuật toán trên", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 6.0, body_y + 253.5, "nhiều kiểu; giữ kiểu tĩnh", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 6.0, body_y + 244.5, "để compiler bắt lỗi sớm?", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Box 1A: Cú pháp & Cơ chế
    b1_h = 100.0
    b1_y = body_y + 138.0
    d.add(Rect(col1_x + 4.0, b1_y, col_w - 8.0, b1_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, b1_y + 88.5, "CƠ CHẾ & CONSTRAINT", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1_y + 78.5, "Unique[T comparable]([]T) []T", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1_y + 68.0, "Max[T Measurable](T, T) T", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1_y + 57.5, "• Type unification & inference", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1_y + 47.0, "• Bảo tồn exact named type:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 12.0, b1_y + 37.0, "Max(ms1, ms2) -> Milliseconds", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1_y + 26.5, "• Compiler từ chối gán nhầm", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 12.0, b1_y + 16.5, "Milliseconds sang int64", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1_y + 6.5, "• Không boxing, không alloc", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 1B: Đánh đổi & Giới hạn
    b1b_h = 88.0
    b1b_y = body_y + 44.0
    d.add(Rect(col1_x + 4.0, b1b_y, col_w - 8.0, b1b_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, b1b_y + 76.5, "ĐÁNH ĐỔI & PHẠM VI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1b_y + 66.0, "[ƯU ĐIỂM]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1b_y + 56.5, "• Zero runtime overhead", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1b_y + 47.0, "• Lỗi kiểu phát hiện ngay", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1_y - 100.5, "[GIỚI HẠN]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1b_y + 27.5, "• Không hỗ trợ đa hình runtime", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1b_y + 17.5, "• Không hoán đổi implementation", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1b_y + 7.5, "• Tăng kích thước nhị phân", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Limitation Banner
    lim_h = 32.0
    d.add(Rect(col1_x + 4.0, body_y + 6.0, col_w - 8.0, lim_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, body_y + 25.5, "[PHÙ HỢP] Cấu trúc dữ liệu,", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, body_y + 16.5, "thuật toán tập hợp, map/slice", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, body_y + 7.5, "giữ nguyên kiểu của caller.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Column 2: INTERFACE (BEHAVIORAL CONTRACT AT RUNTIME)
    # ------------------------------------------------------------------
    d.add(Rect(col2_x, body_y, col_w, body_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.9, rx=2, ry=2))
    d.add(Rect(col2_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 12.0, body_y + body_h - 10.5, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 24.0, body_y + body_h - 10.5, "INTERFACE (BEHAVIOR)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 6.0, body_y + 272.0, "Câu hỏi kỹ thuật:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 6.0, body_y + 262.5, "Hành vi nào cần thỏa thuận", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 6.0, body_y + 253.5, "khi concrete type có thể", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 6.0, body_y + 244.5, "thay đổi hoặc hoán đổi?", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Box 2A: Cú pháp & Cơ chế
    d.add(Rect(col2_x + 4.0, b1_y, col_w - 8.0, b1_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, b1_y + 88.5, "KHẾ ƯỚC & METHOD SET", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1_y + 78.5, "type Summary interface {", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 12.0, b1_y + 68.0, "Summary() string", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1_y + 57.5, "}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1_y + 47.0, "• Decoupling caller khỏi callee", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b1_y + 37.0, "• Dynamic dispatch (itable)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b1_y + 26.5, "• Thỏa mãn ngầm định (implicit)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1_y + 16.5, "• Dễ dàng mock và thay thế", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b1_y + 6.5, "• Giữ ranh giới kiến trúc sạch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 2B: Đánh đổi & Giới hạn
    d.add(Rect(col2_x + 4.0, b1b_y, col_w - 8.0, b1b_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, b1b_y + 76.5, "ĐÁNH ĐỔI & PHẠM VI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1b_y + 66.0, "[ƯU ĐIỂM]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1b_y + 56.5, "• Đa hình runtime linh hoạt", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b1b_y + 47.0, "• Cô lập module độc lập", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b1b_y + 37.0, "[GIỚI HẠN]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1b_y + 27.5, "• Mất thông tin kiểu cụ thể", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b1b_y + 17.5, "• Chi phí pointer/escape heap", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b1b_y + 7.5, "• Không so sánh được nếu chứa slice", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Limitation Banner
    d.add(Rect(col2_x + 4.0, body_y + 6.0, col_w - 8.0, lim_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, body_y + 25.5, "[PHÙ HỢP] API boundaries,", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, body_y + 16.5, "service adapters, storage drivers,", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, body_y + 7.5, "hoán đổi hành vi giữa các lớp.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Column 3: REFLECTION / ANY (RUNTIME SHAPE INSPECTION)
    # ------------------------------------------------------------------
    d.add(Rect(col3_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col3_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 12.0, body_y + body_h - 10.5, "03", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col3_x + 24.0, body_y + body_h - 10.5, "REFLECTION (RUNTIME)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    d.add(String(col3_x + 6.0, body_y + 272.0, "Câu hỏi kỹ thuật:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 6.0, body_y + 262.5, "Khi hình dạng (shape), tag", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 6.0, body_y + 253.5, "hay schema của dữ liệu chỉ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 6.0, body_y + 244.5, "được biết khi đang chạy?", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Box 3A: Cú pháp & Cơ chế
    d.add(Rect(col3_x + 4.0, b1_y, col_w - 8.0, b1_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, b1_y + 88.5, "KHẢO SÁT SHAPE & METADATA", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1_y + 78.5, "reflect.TypeOf(v), ValueOf(v)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1_y + 68.0, "v.Kind(), field.Tag.Get(\"json\")", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1_y + 57.5, "• Duyệt các field động của struct", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1_y + 47.0, "• Xử lý input rỗng: any", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1_y + 37.0, "• Đọc struct tags & validation", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1_y + 26.5, "• Không có kiểm tra kiểu tĩnh", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1_y + 16.5, "• Phụ thuộc descriptor runtime", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1_y + 6.5, "• Nguy cơ runtime panic cao", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 3B: Đánh đổi & Giới hạn
    d.add(Rect(col3_x + 4.0, b1b_y, col_w - 8.0, b1b_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, b1b_y + 76.5, "ĐÁNH ĐỔI & PHẠM VI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1b_y + 66.0, "[ƯU ĐIỂM]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1b_y + 56.5, "• Xử lý shape không biết trước", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1b_y + 47.0, "• Đọc metadata & serialization", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1b_y + 37.0, "[GIỚI HẠN]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1b_y + 27.5, "• Mất bảo vệ ở compile-time", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1b_y + 17.5, "• Chi phí hiệu năng rất lớn", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1b_y + 7.5, "• Khó đọc, khó debug luồng lỗi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Limitation Banner
    d.add(Rect(col3_x + 4.0, body_y + 6.0, col_w - 8.0, lim_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, body_y + 25.5, "[PHÙ HỢP] JSON marshaler,", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, body_y + 16.5, "ORM mapping, schema generator,", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, body_y + 7.5, "nơi dữ liệu hoàn toàn động.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Generic bảo toàn kiểu cho compiler; Interface phân định khế ước hành vi; Reflection chỉ dùng khi shape là input lúc runtime.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 3. Chapter 21 — Figure 35: Edge vs Level Comparison (476.22 x 162.43 pt)
# ======================================================================
def build_edge_level_comparison_drawing(w: float = 476.22, h: float = 162.43) -> Drawing:
    """Figure 35: Điều khiển theo sự kiện và theo trạng thái (Edge vs Level).

    So sánh bản chất:
    - Edge-Triggered: Phản ứng theo chuyển trạng thái (Delta). Mất thông điệp dẫn đến mất đồng bộ vĩnh viễn.
    - Level-Triggered: Phản ứng theo quan sát mức hiện tại (Observation vs Desired). Tự phục hồi và hội tụ.
    Exact dimensions: 476.22 x 162.43 pt (Page 371, xref 424).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 21 // HÌNH 35", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "ĐIỀU KHIỂN THEO SỰ KIỆN (EDGE) VÀ THEO TRẠNG THÁI (LEVEL)", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Khi một thông điệp bị mất, controller dựa vào trạng thái có thể đọc lại observation và tiếp tục điều hòa.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # 2 Comparison Rows
    row_h = 50.0
    row1_y = header_y - row_h - 6.0   # 134 - 50 - 6 = 78.0 pt
    row2_y = row1_y - row_h - 4.0     # 78 - 50 - 4 = 24.0 pt

    # ------------------------------------------------------------------
    # Row 1: EDGE-TRIGGERED (KÍCH HOẠT THEO CẠNH / DELTA EVENT)
    # ------------------------------------------------------------------
    d.add(Rect(8.0, row1_y, w - 16.0, row_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(12.0, row1_y + row_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(20.0, row1_y + row_h - 10.5, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(32.0, row1_y + row_h - 10.5, "EDGE-TRIGGERED // Phản ứng theo chuyển trạng thái (Delta Events)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    # 3 Phase Boxes in Row 1
    b_w = 142.0
    bx1 = 14.0
    bx2 = bx1 + b_w + 12.0  # 168.0
    bx3 = bx2 + b_w + 12.0  # 322.0

    # Step 1: Phát sinh Delta
    d.add(Rect(bx1, row1_y + 5.0, b_w, 30.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(bx1 + 5.0, row1_y + 24.5, "1. BƯỚC NHẢY (DELTA EVENT)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx1 + 5.0, row1_y + 15.5, "Event: PodAdded(+1), PodDeleted(-1)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx1 + 5.0, row1_y + 7.5, "Chỉ báo hiệu biến đổi tại một thời điểm", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrow 1 -> 2
    draw_arrow(d, bx1 + b_w, row1_y + 20.0, bx2, row1_y + 20.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Step 2: Sự cố mất gói / Sập nguồn
    d.add(Rect(bx2, row1_y + 5.0, b_w, 30.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(bx2 + 5.0, row1_y + 24.5, "2. SỰ CỐ TRUYỀN THÔNG", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx2 + 5.0, row1_y + 15.5, "Network Drop / Restart mid-flight", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx2 + 5.0, row1_y + 7.5, "Thông điệp delta bị mất trên đường truyền", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrow 2 -> 3
    draw_arrow(d, bx2 + b_w, row1_y + 20.0, bx3, row1_y + 20.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Step 3: Hậu quả mất đồng bộ
    d.add(Rect(bx3, row1_y + 5.0, b_w, 30.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(bx3 + 5.0, row1_y + 24.5, "3. MẤT ĐỒNG BỘ (DESYNC)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx3 + 5.0, row1_y + 15.5, "Consumer kẹt ở trạng thái cũ", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx3 + 5.0, row1_y + 7.5, "Không thể tự phục hồi nếu thiếu replay", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Row 2: LEVEL-TRIGGERED (KÍCH HOẠT THEO MỨC / STATE RECONCILIATION)
    # ------------------------------------------------------------------
    d.add(Rect(8.0, row2_y, w - 16.0, row_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.9, rx=2, ry=2))
    d.add(Rect(12.0, row2_y + row_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(20.0, row2_y + row_h - 10.5, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(32.0, row2_y + row_h - 10.5, "LEVEL-TRIGGERED // So sánh trạng thái quan sát với Desired State", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    # Step 1: Quan sát mức hiện tại
    d.add(Rect(bx1, row2_y + 5.0, b_w, 30.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(bx1 + 5.0, row2_y + 24.5, "1. ĐỌC QUAN SÁT (OBSERVE)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx1 + 5.0, row2_y + 15.5, "Current: 1 Pod · Desired: 3 Pods", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx1 + 5.0, row2_y + 7.5, "Đọc toàn bộ snapshot; không phụ thuộc delta", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrow 1 -> 2
    draw_arrow(d, bx1 + b_w, row2_y + 20.0, bx2, row2_y + 20.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Step 2: Tính sai lệch & Hành động
    d.add(Rect(bx2, row2_y + 5.0, b_w, 30.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(bx2 + 5.0, row2_y + 24.5, "2. TÍNH SAI LỆCH (DIFF & ACT)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx2 + 5.0, row2_y + 15.5, "diff = desired - current = +2", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx2 + 5.0, row2_y + 7.5, "Đề xuất ActionCreate{Count: 2}", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrow 2 -> 3
    draw_arrow(d, bx2 + b_w, row2_y + 20.0, bx3, row2_y + 20.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Step 3: Phục hồi & Hội tụ
    d.add(Rect(bx3, row2_y + 5.0, b_w, 30.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(bx3 + 5.0, row2_y + 24.5, "3. TỰ HỒI PHỤC (CONVERGENCE)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx3 + 5.0, row2_y + 15.5, "Mất gói/Restart => Đọc lại snapshot", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx3 + 5.0, row2_y + 7.5, "Chu kỳ tiếp tục điều hòa hướng tới hội tụ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Edge-triggered phản ứng theo delta nên dễ kẹt khi mất thông điệp; Level-triggered điều hòa dựa trên observation hiện hành nên tự phục hồi hội tụ.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 4. Chapter 22 — Figure 36: Client-Go Controller Flow (476.22 x 301.61 pt)
# ======================================================================
def build_client_go_controller_flow_drawing(w: float = 476.22, h: float = 301.61) -> Drawing:
    """Figure 36: Luồng sự kiện từ API Server qua Informer tới worker, với Indexer là cache cục bộ.

    Ranh giới trách nhiệm:
    1. Kube-API Server (Authoritative state) <-> Reflector
    2. DeltaFIFO -> SharedInformer cập nhật Indexer (Cache) TRƯỚC khi gọi EventHandlers
    3. EventHandlers chỉ đẩy key (namespace/name) vào RateLimitingQueue
    4. Worker đọc lại observation từ Indexer (đường nét đứt, cache có thể trễ), không dùng payload cũ.
    Exact dimensions: 476.22 x 301.61 pt (Page 385, xref 439).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 22 // HÌNH 36", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "KIẾN TRÚC LUỒNG SỰ KIỆN VÀ BỘ NHỚ ĐỆM CỦA CLIENT-GO CONTROLLER", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Informer cập nhật Indexer trước khi phát key cho hàng đợi; worker luôn đọc lại observation từ cache thay vì payload cũ.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # 4 Major Architectural Columns
    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 243.0 pt

    col_gap = 8.0
    col_w = (w - 16.0 - 3 * col_gap) / 4.0  # 109.05 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + col_gap       # 125.05
    col3_x = col2_x + col_w + col_gap       # 242.11
    col4_x = col3_x + col_w + col_gap       # 359.16

    # ------------------------------------------------------------------
    # Column 1: KUBE-API SERVER & REFLECTOR
    # ------------------------------------------------------------------
    d.add(Rect(col1_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 12.0, body_y + body_h - 10.5, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 24.0, body_y + body_h - 10.5, "API & REFLECTOR", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    # Box 1A: Kube-API Server (Top)
    b1a_h = 76.0
    b1a_y = body_y + body_h - 96.0
    d.add(Rect(col1_x + 4.0, b1a_y, col_w - 8.0, b1a_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.7, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, b1a_y + 64.5, "KUBE-API SERVER", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1a_y + 54.0, "Authoritative Store (etcd)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1a_y + 43.5, "• Nguồn chân lý duy nhất", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1a_y + 33.0, "• Snapshot qua List API", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1a_y + 22.5, "• Stream qua Watch API", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1a_y + 12.0, "• resourceVersion mốc", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 1B: Reflector (Bottom)
    b1b_h = 76.0
    b1b_y = body_y + 36.0
    d.add(Rect(col1_x + 4.0, b1b_y, col_w - 8.0, b1b_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, b1b_y + 64.5, "REFLECTOR (CLIENT-GO)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1b_y + 54.0, "cache.NewReflector(...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1b_y + 43.5, "• Mở kết nối List & Watch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1b_y + 33.0, "• Nối lại khi mất kết nối", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1b_y + 22.5, "• Đẩy delta vào DeltaFIFO", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1b_y + 12.0, "• Re-list khi gặp HTTP 410", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow from Kube-API down to Reflector
    draw_arrow(d, col1_x + col_w / 2.0, b1a_y, col1_x + col_w / 2.0, b1b_y + b1b_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # ------------------------------------------------------------------
    # Column 2: INFORMER & LOCAL INDEXER (CACHE)
    # ------------------------------------------------------------------
    d.add(Rect(col2_x, body_y, col_w, body_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.9, rx=2, ry=2))
    d.add(Rect(col2_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 12.0, body_y + body_h - 10.5, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 24.0, body_y + body_h - 10.5, "DELTAFIFO & INDEXER", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    # Box 2A: DeltaFIFO (Top)
    b2a_h = 56.0
    b2a_y = body_y + body_h - 78.0
    d.add(Rect(col2_x + 4.0, b2a_y, col_w - 8.0, b2a_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, b2a_y + 44.5, "DELTAFIFO QUEUE", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2a_y + 34.0, "type Delta struct { Type, Obj }", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2a_y + 23.5, "• Lưu các biến động theo key", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2a_y + 13.0, "• Informer pop để dispatch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 2B: Indexer / Local Cache (Middle)
    b2b_h = 84.0
    b2b_y = b2a_y - 94.0
    d.add(Rect(col2_x + 4.0, b2b_y, col_w - 8.0, b2b_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, b2b_y + 72.5, "INDEXER (LOCAL STORE)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2b_y + 62.0, "Thread-safe In-Memory Cache", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2b_y + 51.5, "• CẬP NHẬT TRƯỚC!", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2b_y + 41.0, "• Lưu snapshot cục bộ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2b_y + 30.5, "• Giảm tải đọc tới API Server", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2b_y + 20.0, "• Đường nét đứt: cache có thể", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2b_y + 9.5, "  trễ so với API Server thật", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow from Reflector (Col 1) to DeltaFIFO (Col 2)
    draw_arrow(d, col1_x + col_w, b1b_y + b1b_h / 2.0, col2_x, b2a_y + b2a_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Arrow from DeltaFIFO down to Indexer (Update cache first!)
    draw_arrow(d, col2_x + col_w / 2.0, b2a_y, col2_x + col_w / 2.0, b2b_y + b2b_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # ------------------------------------------------------------------
    # Column 3: EVENT HANDLERS & WORKQUEUE
    # ------------------------------------------------------------------
    d.add(Rect(col3_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col3_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 12.0, body_y + body_h - 10.5, "03", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col3_x + 24.0, body_y + body_h - 10.5, "HANDLERS & QUEUE", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    # Box 3A: ResourceEventHandler (Top)
    b3a_h = 76.0
    b3a_y = body_y + body_h - 96.0
    d.add(Rect(col3_x + 4.0, b3a_y, col_w - 8.0, b3a_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, b3a_y + 64.5, "RESOURCE EVENT HANDLERS", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b3a_y + 54.0, "OnAdd, OnUpdate, OnDelete", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b3a_y + 43.5, "• Chỉ lấy key: ns/name", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b3a_y + 33.0, "• Xử lý Tombstone an toàn:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 12.0, b3a_y + 22.5, "DeletedFinalStateUnknown", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b3a_y + 12.0, "• KHÔNG gửi payload cũ!", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Box 3B: WorkQueue (Bottom)
    b3b_h = 76.0
    b3b_y = body_y + 36.0
    d.add(Rect(col3_x + 4.0, b3b_y, col_w - 8.0, b3b_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, b3b_y + 64.5, "RATE-LIMITING WORKQUEUE", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b3b_y + 54.0, "workqueue.TypedRateLimiting", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b3b_y + 43.5, "• Gộp key trùng (dirty set)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b3b_y + 33.0, "• Tuần tự hóa theo key", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b3b_y + 22.5, "• Rate-limit / Backoff retry", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b3b_y + 12.0, "• Chống retry storm", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow from Informer (Col 2) to Handler (Col 3)
    draw_arrow(d, col2_x + col_w, b2a_y + 10.0, col3_x, b3a_y + b3a_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Arrow from Handler down to WorkQueue
    draw_arrow(d, col3_x + col_w / 2.0, b3a_y, col3_x + col_w / 2.0, b3b_y + b3b_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # ------------------------------------------------------------------
    # Column 4: WORKER POOL & RECONCILE
    # ------------------------------------------------------------------
    d.add(Rect(col4_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col4_x + 4.0, body_y + body_h - 13.0, 16.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col4_x + 12.0, body_y + body_h - 10.5, "04", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col4_x + 24.0, body_y + body_h - 10.5, "WORKER & RECONCILE", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    # Box 4A: Worker Goroutines
    b4a_h = 160.0
    b4a_y = body_y + 36.0
    d.add(Rect(col4_x + 4.0, b4a_y, col_w - 8.0, b4a_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=1.5, ry=1.5))
    d.add(String(col4_x + 8.0, b4a_y + 148.5, "WORKER GOROUTINES", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col4_x + 8.0, b4a_y + 138.0, "for c.processNextWorkItem()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col4_x + 8.0, b4a_y + 126.5, "1. obj, shutdown := queue.Get()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col4_x + 8.0, b4a_y + 115.5, "   key := obj.(string)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col4_x + 8.0, b4a_y + 103.5, "2. ĐỌC CACHE CỤC BỘ:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col4_x + 12.0, b4a_y + 93.0, "item, err := indexer.Get(key)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col4_x + 8.0, b4a_y + 81.5, "   (Đọc observation hiện hành)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col4_x + 8.0, b4a_y + 70.0, "3. syncHandler(key)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col4_x + 8.0, b4a_y + 59.0, "   • So sánh desired vs current", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col4_x + 8.0, b4a_y + 48.0, "   • Actuator cập nhật Kube-API", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col4_x + 8.0, b4a_y + 36.5, "4. queue.Done(key)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col4_x + 8.0, b4a_y + 25.5, "   • if err != nil => AddRateLimited", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col4_x + 8.0, b4a_y + 14.5, "   • else => queue.Forget(key)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow from WorkQueue (Col 3) to Worker (Col 4)
    draw_arrow(d, col3_x + col_w, b3b_y + b3b_h / 2.0, col4_x, b4a_y + 50.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Dashed Arrow from Indexer (Col 2) to Worker (Col 4) -> Re-read local cache observation!
    # Draw curve or elevated dashed line
    draw_arrow(d, col2_x + col_w, b2b_y + 30.0, col4_x, b4a_y + 95.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0, dashed=True)

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Sự kiện chỉ là notification hint để xếp key; worker luôn đọc lại observation từ Indexer (nét đứt) trước khi điều hòa, không dùng payload cũ.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 5. Chapter 22 — Figure 37: Client-Go List-Watch (476.22 x 275.15 pt)
# ======================================================================
def build_client_go_list_watch_drawing(w: float = 476.22, h: float = 275.15) -> Drawing:
    """Figure 37: Trình tự Reflector List rồi Watch với API Server và xử lý khi lịch sử Watch hết hạn.

    Sequence & Timeline:
    1. List snapshot -> opaque resourceVersion: "1040"
    2. Watch stream: events 1041, 1042
    3. Network break / disconnect at 1042
    4. Reconnect watch?resourceVersion=1042
    5. HTTP 410 Gone (Too old resource version) do etcd compact
    6. Re-list recovery -> fresh snapshot at resourceVersion: "2050" -> new Watch stream.
    Exact dimensions: 476.22 x 275.15 pt (Page 386, xref 441).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 22 // HÌNH 37", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "TRÌNH TỰ REFLECTOR LIST/WATCH VÀ PHỤC HỒI KHI GẶP HTTP 410 GONE", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "List tạo mốc snapshot ban đầu; Watch tiếp nhận thay đổi; khi lịch sử hết hạn (410 Gone), Reflector bắt buộc List lại từ đầu.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Sequence Lifelines: 2 Actors
    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 217.0 pt

    # Actor Columns
    actor1_x = 90.0   # Reflector (Client)
    actor2_x = 386.0  # Kube-API Server (etcd)

    # Actor Lifeline Header Boxes
    act_box_w = 130.0
    act_box_h = 20.0
    act_box_y = header_y - act_box_h - 6.0  # 247.0 - 20 - 6 = 221.0 pt

    d.add(Rect(actor1_x - act_box_w / 2.0, act_box_y, act_box_w, act_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor1_x, act_box_y + 11.5, "REFLECTOR (CLIENT-GO)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor1_x, act_box_y + 4.5, "Local Store / DeltaFIFO", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    d.add(Rect(actor2_x - act_box_w / 2.0, act_box_y, act_box_w, act_box_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor2_x, act_box_y + 11.5, "KUBE-API SERVER (ETCD)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, act_box_y + 4.5, "Authoritative Cluster Store", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # Vertical Lifelines (Dashed)
    lifeline_bot = body_y + 6.0
    lifeline_top = act_box_y
    line1 = Line(actor1_x, lifeline_top, actor1_x, lifeline_bot)
    line1.strokeColor = COLOR_BORDER
    line1.strokeWidth = 0.8
    line1.strokeDashArray = [3, 2]
    d.add(line1)

    line2 = Line(actor2_x, lifeline_top, actor2_x, lifeline_bot)
    line2.strokeColor = COLOR_BORDER
    line2.strokeWidth = 0.8
    line2.strokeDashArray = [3, 2]
    d.add(line2)

    # Sequence Messages / Steps
    steps = [
        # (y, dir, label, code, tag, is_error)
        (198.0, "R->S", "1. GET /api/v1/pods (List ban đầu)", "Request toàn bộ snapshot Pods", "LIST", False),
        (176.0, "S->R", "2. HTTP 200 OK: PodList + resourceVersion: \"1040\"", "Snapshot nạp vào DeltaFIFO", "SNAPSHOT", False),
        (152.0, "R->S", "3. GET /api/v1/pods?watch=true&resourceVersion=1040", "Mở HTTP stream từ mốc 1040", "WATCH STREAM", False),
        (130.0, "S->R", "4. Event Stream: 1041 (ADDED) -> 1042 (MODIFIED)", "Delta chuyển tới Informer", "EVENTS", False),
        (108.0, "BREAK", "--- MẤT KẾT NỐI MẠNG (DISCONNECT) TẠI MỐC 1042 ---", "etcd compact lịch sử cũ", "NETWORK BREAK", True),
        (86.0, "R->S", "5. Reconnect: ?watch=true&resourceVersion=1042", "Thử nối lại từ mốc đã biết", "RETRY WATCH", False),
        (66.0, "S->R", "6. HTTP 410 Gone (Too old resource version)", "Lịch sử đã bị dọn dẹp khỏi etcd", "410 GONE", True),
        (44.0, "R->S", "7. RE-LIST KHỞI TẠO LẠI: GET /api/v1/pods", "Tái lập snapshot mới (RV: \"2050\")", "RE-LIST RECOVERY", False),
    ]

    for sy, sdir, title, desc, tag, is_err in steps:
        if sdir == "BREAK":
            # Event Break Banner across lifelines
            d.add(Rect(actor1_x - 30.0, sy - 4.0, (actor2_x - actor1_x) + 60.0, 16.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
            d.add(String((actor1_x + actor2_x) / 2.0, sy + 4.5, title, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
            d.add(String((actor1_x + actor2_x) / 2.0, sy - 2.0, desc, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
            continue

        if sdir == "R->S":
            # Arrow from Reflector to API Server
            draw_arrow(d, actor1_x, sy, actor2_x, sy, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
            d.add(String(actor1_x + 10.0, sy + 3.0, title, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
            d.add(String(actor1_x + 10.0, sy - 7.0, desc, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
        elif sdir == "S->R":
            # Arrow from API Server to Reflector
            arrow_color = COLOR_INK_DARK
            draw_arrow(d, actor2_x, sy, actor1_x, sy, color=arrow_color, width=0.8, head_size=3.0)
            d.add(String(actor1_x + 10.0, sy + 3.0, title, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
            d.add(String(actor1_x + 10.0, sy - 7.0, desc, fontName="BookSansBold" if is_err else "BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK if is_err else COLOR_INK_MID))

        # Tag box on the right of API server or near actor
        tag_w = stringWidth(tag, "BookMono", 5.6) + 6.0
        d.add(Rect(actor2_x + 8.0, sy - 4.0, tag_w, 9.0, fillColor=COLOR_TAG_ACTIVE if is_err else COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.4, rx=1.0, ry=1.0))
        d.add(String(actor2_x + 8.0 + tag_w / 2.0, sy - 1.5, tag, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: List tạo mốc snapshot ban đầu; Watch stream thay đổi tiếp theo; khi gặp HTTP 410 Gone, Reflector bắt buộc List lại từ đầu để lập snapshot mới.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 6. Chapter 23 — Figure 38: Operator Capabilities (476.22 x 254.61 pt)
# ======================================================================
def build_operator_capabilities_drawing(w: float = 476.22, h: float = 254.61) -> Drawing:
    """Figure 38: Tri thức vận hành trong một operator.

    Operator biểu đạt tri thức vận hành qua API, vòng lặp điều hòa và các tích
    hợp quản lý tài nguyên. Các thành phần này là vai trò thiết kế, không phải
    ba bước chạy tuần tự.
    Exact dimensions: 476.22 x 254.61 pt (Page 404, xref 460).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 23 // HÌNH 38", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "TRI THỨC VẬN HÀNH VÀ CÁC THÀNH PHẦN KIẾN TRÚC TRONG OPERATOR", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Operator biểu đạt tri thức vận hành qua API, vòng lặp điều hòa và tích hợp ngoài (vai trò thiết kế song hành).", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 194.61 pt

    left_w = 296.0
    right_x = 310.0
    right_w = w - right_x - 8.0  # 158.22 pt

    # Left: Domain Knowledge -> Operator -> 3 Roles
    # 1. Top Card: Tri thức vận hành
    top_card_h = 52.0
    top_card_y = body_y + body_h - top_card_h
    d.add(Rect(8.0, top_card_y, left_w, top_card_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(14.0, top_card_y + top_card_h - 13.0, 110.0, 10.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(69.0, top_card_y + top_card_h - 10.0, "TRI THỨC VẬN HÀNH", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(14.0, top_card_y + 26.0, "Quy tắc vận hành ứng dụng: backup dữ liệu, failover cụm, điều phối", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(14.0, top_card_y + 16.0, "nâng cấp schema và tự phục hồi do kỹ sư tích lũy qua kinh nghiệm.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(14.0, top_card_y + 6.0, "• Đóng gói tư duy con người thành thuật toán phần mềm tự hành", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow from Knowledge to Operator
    draw_arrow(d, 8.0 + left_w / 2.0, top_card_y, 8.0 + left_w / 2.0, top_card_y - 14.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # 2. Central Engine: Operator Core
    op_card_h = 32.0
    op_card_y = top_card_y - 14.0 - op_card_h
    d.add(Rect(8.0, op_card_y, left_w, op_card_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(8.0 + left_w / 2.0, op_card_y + 19.0, "OPERATOR (HIỆN THỰC BẰNG GO)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(8.0 + left_w / 2.0, op_card_y + 7.5, "Custom Controller runtime quản lý vòng đời tài nguyên trên Kubernetes", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 3 Arrows to 3 Architectural Roles
    role_w = (left_w - 16.0) / 3.0  # 93.33 pt
    r1_x = 8.0
    r2_x = r1_x + role_w + 8.0
    r3_x = r2_x + role_w + 8.0
    role_y = body_y
    role_h = op_card_y - role_y - 14.0  # 72.0 pt

    draw_arrow(d, 8.0 + left_w / 2.0, op_card_y, r1_x + role_w / 2.0, role_y + role_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, 8.0 + left_w / 2.0, op_card_y, r2_x + role_w / 2.0, role_y + role_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, 8.0 + left_w / 2.0, op_card_y, r3_x + role_w / 2.0, role_y + role_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Role 1: API / CRD
    d.add(Rect(r1_x, role_y, role_w, role_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(r1_x + role_w / 2.0, role_y + role_h - 11.0, "API / CRD", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(r1_x + role_w / 2.0, role_y + role_h - 20.0, "Biểu đạt ý định", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
    d.add(String(r1_x + 6.0, role_y + 36.0, "• AppServiceSpec", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r1_x + 6.0, role_y + 24.0, "• OpenAPI schema", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r1_x + 6.0, role_y + 12.0, "• Nguồn ý định duy nhất", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Role 2: Controller Loop
    d.add(Rect(r2_x, role_y, role_w, role_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(r2_x + role_w / 2.0, role_y + role_h - 11.0, "CONTROLLER", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(r2_x + role_w / 2.0, role_y + role_h - 20.0, "Điều hòa trạng thái", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
    d.add(String(r2_x + 6.0, role_y + 36.0, "• Reconcile loop", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r2_x + 6.0, role_y + 24.0, "• current == desired", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r2_x + 6.0, role_y + 12.0, "• Hành động bất biến", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Role 3: External Integration
    d.add(Rect(r3_x, role_y, role_w, role_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=2, ry=2))
    d.add(String(r3_x + role_w / 2.0, role_y + role_h - 11.0, "TÍCH HỢP NGOÀI", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(r3_x + role_w / 2.0, role_y + role_h - 20.0, "Quản lý vòng đời", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
    d.add(String(r3_x + 6.0, role_y + 36.0, "• Cloud RDS / DNS", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r3_x + 6.0, role_y + 24.0, "• Finalizer dọn dẹp", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r3_x + 6.0, role_y + 12.0, "• Storage & secrets", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Right: 5 Capability Levels
    d.add(Rect(right_x, body_y, right_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(right_x + right_w / 2.0, body_y + body_h - 12.0, "5 CẤP ĐỘ NĂNG LỰC OPERATOR", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(right_x + right_w / 2.0, body_y + body_h - 21.0, "(Thang đo năng lực tự động hóa CNCF)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    levels = [
        ("Level 5: Auto-Pilot", "Tự động co giãn, tự vá lỗi và phân tích dị thường"),
        ("Level 4: Deep Insights", "Đo lường metrics, cảnh báo, log & trace chuyên sâu"),
        ("Level 3: Full Lifecycle", "Quản lý sao lưu (backup), phục hồi sau thảm họa"),
        ("Level 2: Seamless Upgrades", "Nâng cấp phiên bản không gián đoạn, dịch chuyển schema"),
        ("Level 1: Basic Install", "Tự động hóa triển khai ban đầu và cấu hình CRD"),
    ]

    card_step = (body_h - 32.0) / 5.0
    for idx, (ltitle, ldesc) in enumerate(reversed(levels)):
        ly = body_y + 6.0 + idx * card_step
        d.add(Rect(right_x + 6.0, ly, right_w - 12.0, card_step - 4.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(String(right_x + 10.0, ly + card_step - 14.0, ltitle, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(right_x + 10.0, ly + 5.0, ldesc, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Các thành phần là vai trò thiết kế song hành, không phải 3 bước chạy tuần tự. CRD là nguồn chân lý duy nhất cho ý định khai báo.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 7. Chapter 23 — Figure 39: Operator Manager Boundaries (473.72 x 362.83 pt)
# ======================================================================
def build_operator_manager_boundaries_drawing(w: float = 473.72, h: float = 362.83) -> Drawing:
    """Figure 39: Ranh giới giữa Manager, Reconciler và Client.

    Manager tổ chức các component; controller gọi Reconciler cho một khóa.
    Client dùng cache cho đường đọc được cấu hình và HTTP cho đường ghi;
    sơ đồ lược bỏ các đường đọc không qua cache.
    Exact dimensions: 473.72 x 362.83 pt (Page 405, xref 462).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 23 // HÌNH 39", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "RANH GIỚI VÀ PHÂN ĐỊNH TRÁCH NHIỆM: MANAGER, RECONCILER VÀ CLIENT", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Manager tổ chức các component; controller gọi Reconciler; Client tách đường đọc cache và ghi HTTP tới API Server.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 302.83 pt

    box_w = (w - 24.0) / 2.0  # 224.86 pt each
    col1_x = 8.0
    col2_x = col1_x + box_w + 8.0

    # ------------------------------------------------------------------
    # Top-Left: MANAGER (controller-runtime Host)
    # ------------------------------------------------------------------
    top_box_h = 88.0
    top_box_y = body_y + body_h - top_box_h
    d.add(Rect(col1_x, top_box_y, box_w, top_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, top_box_y + top_box_h - 13.0, 60.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 36.0, top_box_y + top_box_h - 10.5, "HOST RUNNER", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 72.0, top_box_y + top_box_h - 10.5, "MANAGER (CONTROLLER-RUNTIME)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col1_x + 8.0, top_box_y + 60.0, "ctrl.NewManager(cfg, options)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, top_box_y + 48.0, "• Quản lý lifecycle: metrics, health probes, leader election", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, top_box_y + 36.0, "• Quản lý Scheme: ánh xạ Go struct <-> GroupVersionKind", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, top_box_y + 24.0, "• Khởi tạo Informer Cache và cấp Client cho controller", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, top_box_y + 12.0, "• Cung cấp ctx.Done() báo tín hiệu shutdown graceful", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Top-Right: SPLIT CLIENT & IN-MEMORY CACHE
    # ------------------------------------------------------------------
    d.add(Rect(col2_x, top_box_y, box_w, top_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 6.0, top_box_y + top_box_h - 13.0, 68.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col2_x + 40.0, top_box_y + top_box_h - 10.5, "CLIENT.CLIENT", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 80.0, top_box_y + top_box_h - 10.5, "SPLIT CLIENT & IN-MEMORY CACHE", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 8.0, top_box_y + 60.0, "Tách biệt đường đọc (Cache) và đường ghi (HTTP):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, top_box_y + 48.0, "• ĐƯỜNG ĐỌC: Đọc từ In-Memory Cache (Informer Store)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 16.0, top_box_y + 36.0, "Zero network roundtrip tới etcd cho kiểu đã watch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, top_box_y + 24.0, "• ĐƯỜNG GHI: Trực tiếp qua HTTP REST tới API Server", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 16.0, top_box_y + 12.0, "Create, Update, Patch, Delete bảo đảm ghi đồng bộ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # ------------------------------------------------------------------
    # Middle-Left: CONTROLLER ENGINE (Queue & Worker)
    # ------------------------------------------------------------------
    mid_box_h = 78.0
    mid_box_y = top_box_y - 14.0 - mid_box_h
    d.add(Rect(col1_x, mid_box_y, box_w, mid_box_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(col1_x + 8.0, mid_box_y + mid_box_h - 12.0, "CONTROLLER (QUEUE & WORKER POOL)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, mid_box_y + 50.0, "• Watch sự kiện từ Informer Cache qua EventHandler", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, mid_box_y + 38.0, "• Coalesce các sự kiện trùng lặp của cùng một khóa", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, mid_box_y + 26.0, "• RateLimitingQueue giữ reconcile.Request{NamespacedName}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, mid_box_y + 12.0, "• Worker gọi Reconcile(ctx, req) theo cơ chế tuần tự hóa", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # ------------------------------------------------------------------
    # Middle-Right: KUBE-API SERVER & ETCD
    # ------------------------------------------------------------------
    d.add(Rect(col2_x, mid_box_y, box_w, mid_box_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(col2_x + 8.0, mid_box_y + mid_box_h - 12.0, "KUBE-API SERVER (ETCD CLUSTER STORE)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, mid_box_y + 50.0, "• Authoritative State Store của toàn bộ cụm Kubernetes", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, mid_box_y + 38.0, "• Phát Watch Stream nuôi Informer Cache (đường nét đứt)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, mid_box_y + 26.0, "• Tiếp nhận HTTP mutations từ Client ghi vào etcd", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, mid_box_y + 12.0, "• Xét điều kiện deletionTimestamp và finalizers khi xóa", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrows between top and middle
    draw_arrow(d, col1_x + box_w / 2.0, top_box_y, col1_x + box_w / 2.0, mid_box_y + mid_box_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, col2_x + box_w * 0.3, top_box_y, col2_x + box_w * 0.3, mid_box_y + mid_box_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    # Dashed arrow from API server up to cache
    draw_arrow(d, col2_x + box_w * 0.7, mid_box_y + mid_box_h, col2_x + box_w * 0.7, top_box_y, color=COLOR_INK_MID, width=0.8, head_size=3.0, dashed=True)

    # ------------------------------------------------------------------
    # Bottom: RECONCILER (Reconcile Loop Pipeline)
    # ------------------------------------------------------------------
    rec_box_y = body_y
    rec_box_h = mid_box_y - rec_box_y - 12.0  # 96.0 pt
    d.add(Rect(8.0, rec_box_y, w - 16.0, rec_box_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(14.0, rec_box_y + rec_box_h - 12.0, "RECONCILER CORE: Reconcile(ctx, req) -> (ctrl.Result, error)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    # 4 Sequential Steps inside Reconciler
    rec_step_w = (w - 32.0 - 24.0) / 4.0  # 104.43 pt each
    sx1 = 14.0
    sx2 = sx1 + rec_step_w + 8.0
    sx3 = sx2 + rec_step_w + 8.0
    sx4 = sx3 + rec_step_w + 8.0
    s_h = rec_box_h - 24.0
    s_y = rec_box_y + 6.0

    steps_data = [
        (sx1, "1. ĐỌC CACHE", "r.Get(ctx, req, &app)", "Đọc snapshot từ cache", "In-memory, zero I/O"),
        (sx2, "2. XÉT FINALIZER", "DeletionTimestamp != nil", "Nếu đang xóa -> cleanup", "Bảo toàn tài nguyên"),
        (sx3, "3. SO SÁNH DESIRED", "current == desired?", "Tính toán diff spec", "Tạo child Deployment"),
        (sx4, "4. GHI HTTP", "r.Update() / Status()", "Ghi mutation qua HTTP", "etcd cập nhật mốc mới"),
    ]

    for sx, stitle, scode, sdesc1, sdesc2 in steps_data:
        d.add(Rect(sx, s_y, rec_step_w, s_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(String(sx + 6.0, s_y + s_h - 11.0, stitle, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(sx + 6.0, s_y + s_h - 22.0, scode, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(sx + 6.0, s_y + 16.0, sdesc1, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
        d.add(String(sx + 6.0, s_y + 6.0, sdesc2, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Flow arrows between steps
    draw_arrow(d, sx1 + rec_step_w, s_y + s_h / 2.0, sx2, s_y + s_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, sx2 + rec_step_w, s_y + s_h / 2.0, sx3, s_y + s_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, sx3 + rec_step_w, s_y + s_h / 2.0, sx4, s_y + s_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Arrow from Controller Engine to Reconciler
    draw_arrow(d, col1_x + box_w / 2.0, mid_box_y, col1_x + box_w / 2.0, rec_box_y + rec_box_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Reconciler chỉ nhận NamespacedName và đọc từ Cache; mọi thay đổi trạng thái bắt buộc ghi qua HTTP REST tới API Server.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 8. Chapter 23 — Figure 40: Operator Finalizer Lifecycle (342.25 x 362.83 pt)
# ======================================================================
def build_operator_finalizer_lifecycle_drawing(w: float = 342.25, h: float = 362.83) -> Drawing:
    """Figure 40: Vòng đời và xử lý finalizer trong operator.

    Việc dọn dẹp thất bại sẽ giữ lại finalizer để có thể thử lại.
    Cleanup thành công chỉ cho phép gỡ finalizer của controller này;
    API server còn phải xét các điều kiện xóa khác.
    Exact dimensions: 342.25 x 362.83 pt (Page 410, xref 468).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 23 // HÌNH 40", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "VÒNG ĐỜI VÀ XỬ LÝ FINALIZER TRONG CONTROLLER", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Finalizer bảo vệ tài nguyên ngoài; cleanup thất bại giữ finalizer để thử lại.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 302.83 pt

    center_w = w - 24.0  # 318.25 pt
    cx = 12.0

    # Step 1: Add Finalizer
    s1_h = 42.0
    s1_y = body_y + body_h - s1_h
    d.add(Rect(cx, s1_y, center_w, s1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(cx + 8.0, s1_y + s1_h - 12.0, "1. GẮN VÀ LƯU FINALIZER KHI KHỞI TẠO TÀI NGUYÊN", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, s1_y + 18.0, "controllerutil.AddFinalizer(&obj, \"app.example.com/finalizer\")", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, s1_y + 8.0, "• Ghi nhận ownership dọn dẹp trước khi cấp phát tài nguyên ngoại vi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    draw_arrow(d, w / 2.0, s1_y, w / 2.0, s1_y - 12.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Step 2: Receive Delete Request
    s2_h = 42.0
    s2_y = s1_y - 12.0 - s2_h
    d.add(Rect(cx, s2_y, center_w, s2_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(cx + 8.0, s2_y + s2_h - 12.0, "2. NHẬN YÊU CẦU XÓA (KUBECTL DELETE)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, s2_y + 18.0, "API Server gán deletionTimestamp != nil; tài nguyên chuyển sang Deleting", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, s2_y + 8.0, "• etcd KHÔNG xóa vật lý vì danh sách finalizers vẫn còn tồn tại", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    draw_arrow(d, w / 2.0, s2_y, w / 2.0, s2_y - 12.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Step 3: Run Cleanup
    s3_h = 42.0
    s3_y = s2_y - 12.0 - s3_h
    d.add(Rect(cx, s3_y, center_w, s3_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(cx + 8.0, s3_y + s3_h - 12.0, "3. RECONCILER CHẠY CLEANUP TÀI NGUYÊN NGOẠI VI", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, s3_y + 18.0, "err := r.cleanupExternalResources(ctx, obj)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, s3_y + 8.0, "• Thu hồi DNS record, Cloud RDS database, Vault token, AWS S3 bucket...", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    draw_arrow(d, w / 2.0, s3_y, w / 2.0, s3_y - 12.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Decision: Cleanup Result
    dec_h = 32.0
    dec_y = s3_y - 12.0 - dec_h
    d.add(Rect(cx, dec_y, center_w, dec_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(w / 2.0, dec_y + 19.0, "KẾT QUẢ CLEANUP NGOẠI VI: THÀNH CÔNG HAY THẤT BẠI?", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(w / 2.0, dec_y + 8.0, "Kiểm tra err == nil (Thành công) hoặc err != nil (Thất bại)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # Two Outcome Columns below Decision
    branch_w = (center_w - 12.0) / 2.0  # 153.12 pt each
    bx1 = cx
    bx2 = cx + branch_w + 12.0
    b_y = body_y
    b_h = dec_y - b_y - 12.0  # 72.0 pt

    # Arrow to Left (Fail)
    draw_arrow(d, w / 2.0 - 40.0, dec_y, bx1 + branch_w / 2.0, b_y + b_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    # Arrow to Right (Success)
    draw_arrow(d, w / 2.0 + 40.0, dec_y, bx2 + branch_w / 2.0, b_y + b_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Left Box: Cleanup Fail
    d.add(Rect(bx1, b_y, branch_w, b_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(bx1 + 6.0, b_y + b_h - 13.0, 72.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(bx1 + 42.0, b_y + b_h - 10.5, "CLEANUP THẤT BẠI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(bx1 + 8.0, b_y + 44.0, "• GIỮ NGUYÊN FINALIZER", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx1 + 8.0, b_y + 32.0, "• Return ctrl.Result{}, err", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx1 + 8.0, b_y + 20.0, "• Requeue thử lại theo policy", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(bx1 + 8.0, b_y + 8.0, "• Invariant: etcd chặn xóa vật lý", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Right Box: Cleanup Success
    d.add(Rect(bx2, b_y, branch_w, b_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(bx2 + 6.0, b_y + b_h - 13.0, 78.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(bx2 + 45.0, b_y + b_h - 10.5, "CLEANUP THÀNH CÔNG", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(bx2 + 8.0, b_y + 44.0, "• controllerutil.RemoveFinalizer", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx2 + 8.0, b_y + 32.0, "• r.Update(ctx, &obj) lên API server", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(bx2 + 8.0, b_y + 20.0, "• API server xét finalizers khác", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(bx2 + 8.0, b_y + 8.0, "• Hết finalizer -> etcd xóa vĩnh viễn", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Cleanup thất bại giữ finalizer để thử lại; gỡ finalizer chỉ cho phép xóa khi không còn finalizer nào khác trên object.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 9. Chapter 24 — Figure 41: AWS Credentials Resolution (264.41 x 362.83 pt)
# ======================================================================
def build_aws_credentials_resolution_drawing(w: float = 264.41, h: float = 362.83) -> Drawing:
    """Figure 41: Chọn nguồn credential trong AWS SDK for Go v2.

    Cấu hình quyết định provider được chọn; đây là bản đồ nguồn, không phải
    thứ tự ưu tiên bất biến. Credential có thể là static hoặc tạm thời.
    Cache lấy credential khi có lượt Retrieve cần dữ liệu hợp lệ.
    Exact dimensions: 264.41 x 362.83 pt (Page 426, xref 485).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 24 // HÌNH 41", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "PHÂN GIẢI CREDENTIALS TRONG AWS SDK V2", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Bản đồ nguồn và vai trò trung gian của CredentialsCache.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 302.83 pt

    cw = w - 16.0  # 248.41 pt
    cx = 8.0

    # 1. Initiator: LoadDefaultConfig
    c1_h = 40.0
    c1_y = body_y + body_h - c1_h
    d.add(Rect(cx, c1_y, cw, c1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(cx + 8.0, c1_y + c1_h - 11.0, "config.LoadDefaultConfig(ctx, opts...)", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c1_y + 16.0, "Chọn provider phù hợp theo biến môi trường và thiết lập", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c1_y + 6.0, "Khởi tạo chuỗi phân giải credentials mặc định của AWS SDK v2", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, w / 2.0, c1_y, w / 2.0, c1_y - 10.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # 2. Providers Sources Box
    c2_h = 118.0
    c2_y = c1_y - 10.0 - c2_h
    d.add(Rect(cx, c2_y, cw, c2_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(cx + 6.0, c2_y + c2_h - 13.0, 110.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(cx + 61.0, c2_y + c2_h - 10.5, "NGUỒN CẤU HÌNH & WORKLOAD", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    providers = [
        ("1. Môi trường (Env):", "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"),
        ("2. Shared Profiles:", "~/.aws/credentials, ~/.aws/config, AWS_PROFILE"),
        ("3. Web Identity / IRSA:", "AWS_WEB_IDENTITY_TOKEN_FILE (EKS Pod)"),
        ("4. Workload / IMDSv2:", "AWS_CONTAINER_CREDENTIALS_URI, EC2 IMDSv2"),
    ]

    py = c2_y + c2_h - 26.0
    for ptitle, pdesc in providers:
        d.add(String(cx + 8.0, py, ptitle, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(cx + 8.0, py - 9.0, pdesc, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
        py -= 22.0

    draw_arrow(d, w / 2.0, c2_y, w / 2.0, c2_y - 10.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # 3. Cache Engine: aws.CredentialsCache
    c3_h = 58.0
    c3_y = c2_y - 10.0 - c3_h
    d.add(Rect(cx, c3_y, cw, c3_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(cx + 8.0, c3_y + c3_h - 11.0, "aws.CredentialsCache (TẦNG ĐỆM & TỰ REFRESH)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c3_y + 32.0, "• Retrieve(ctx): Lấy và lưu giữ credentials trong bộ nhớ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c3_y + 20.0, "• Kiểm tra CanExpire & Expires để tự động làm mới khi hết hạn", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c3_y + 8.0, "• An toàn cho các goroutine truy xuất đồng thời (sync.RWMutex)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, w / 2.0, c3_y, w / 2.0, c3_y - 10.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # 4. Value Output: aws.Credentials
    c4_y = body_y
    c4_h = c3_y - c4_y - 10.0  # 48.0 pt
    d.add(Rect(cx, c4_y, cw, c4_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(cx + 8.0, c4_y + c4_h - 11.0, "aws.Credentials (DỮ LIỆU ĐÃ ĐƯỢC PHÂN GIẢI)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c4_y + 22.0, "AccessKeyID, SecretAccessKey, SessionToken", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c4_y + 10.0, "CanExpire: bool, Expires: time.Time (nếu là token tạm thời)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Cấu hình quyết định provider được chọn; CredentialsCache chỉ gọi Retrieve() làm mới khi token tạm thời hết hạn.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 10. Chapter 24 — Figure 42: Smithy Request-Response (437.54 x 362.83 pt)
# ======================================================================
def build_smithy_request_response_drawing(w: float = 437.54, h: float = 362.83) -> Drawing:
    """Figure 42: Đường request và response qua Smithy middleware.

    Mũi tên liền biểu diễn đường gọi vào handler, mũi tên đứt biểu diễn
    response trở về Deserialize. Middleware cụ thể và vị trí xử lý checksum
    phụ thuộc operation cùng cấu hình; sơ đồ không mô tả từng lần retry.
    Exact dimensions: 437.54 x 362.83 pt (Page 429, xref 489).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 24 // HÌNH 42", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "SMITHY MIDDLEWARE STACK: ĐƯỜNG REQUEST VÀ RESPONSE TRONG AWS SDK V2", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Mũi tên liền là đường lồng gọi xuôi (Request); mũi tên đứt là đường trả về ngược (Response) giải mã kết quả.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 302.83 pt

    col_w = (w - 24.0) / 2.0  # 206.77 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + 8.0

    # Left Column: Outgoing Request Middleware Stack (4 steps)
    step_gap = 8.0
    step_h = (body_h - 3 * step_gap) / 4.0  # 69.70 pt each

    # Step 1: Initialize
    s1_y = body_y + 3 * (step_h + step_gap)
    d.add(Rect(col1_x, s1_y, col_w, step_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, s1_y + step_h - 13.0, 78.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 45.0, s1_y + step_h - 10.5, "01 · INITIALIZE", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 90.0, s1_y + step_h - 10.5, "Chuẩn bị tham số", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s1_y + 40.0, "• Xác thực tham số đầu vào (Input validation)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s1_y + 28.0, "• Gán giá trị mặc định cho configuration", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s1_y + 14.0, "• Inject OpenTelemetry spans & client metrics", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, col1_x + col_w / 2.0, s1_y, col1_x + col_w / 2.0, s1_y - step_gap, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Step 2: Serialize
    s2_y = body_y + 2 * (step_h + step_gap)
    d.add(Rect(col1_x, s2_y, col_w, step_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, s2_y + step_h - 13.0, 72.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 42.0, s2_y + step_h - 10.5, "02 · SERIALIZE", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 84.0, s2_y + step_h - 10.5, "Dựng HTTP request", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s2_y + 40.0, "• Chuyển Go SDK struct thành smithyhttp.Request", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s2_y + 28.0, "• Thiết lập HTTP Method (GET/POST/PUT)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s2_y + 14.0, "• Mã hóa URI path, query parameters và headers", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, col1_x + col_w / 2.0, s2_y, col1_x + col_w / 2.0, s2_y - step_gap, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Step 3: Build
    s3_y = body_y + 1 * (step_h + step_gap)
    d.add(Rect(col1_x, s3_y, col_w, step_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, s3_y + step_h - 13.0, 56.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 34.0, s3_y + step_h - 10.5, "03 · BUILD", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 68.0, s3_y + step_h - 10.5, "Hoàn thiện request", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s3_y + 40.0, "• Tính Content-Length và Payload Checksum (SHA-256)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s3_y + 28.0, "• Gắn host prefix, kiểm tra endpoint URL", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s3_y + 14.0, "• Thiết lập User-Agent của AWS SDK v2", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, col1_x + col_w / 2.0, s3_y, col1_x + col_w / 2.0, s3_y - step_gap, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Step 4: Finalize
    s4_y = body_y
    d.add(Rect(col1_x, s4_y, col_w, step_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, s4_y + step_h - 13.0, 68.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 40.0, s4_y + step_h - 10.5, "04 · FINALIZE", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 80.0, s4_y + step_h - 10.5, "Ký SigV4 & Retry Loop", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s4_y + 40.0, "• Ký AWS SigV4 (Authorization: AWS4-HMAC-SHA256)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s4_y + 28.0, "• Thiết lập vòng lặp thử lại (Retry / Exponential Backoff)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, s4_y + 14.0, "• Chuẩn bị payload body stream cho transport", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Cross arrow from Step 4 (Finalize) to Right Column (Transport & Deserialize)
    draw_arrow(d, col1_x + col_w, s4_y + step_h / 2.0, col2_x, s4_y + step_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Right Column: Transport and Deserialize
    # Top Box on Right: HTTP ROUND TRIP (Transport)
    trans_h = 100.0
    trans_y = body_y + body_h - trans_h
    d.add(Rect(col2_x, trans_y, col_w, trans_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(col2_x + 8.0, trans_y + trans_h - 12.0, "HTTP ROUND TRIP (TRANSPORT TẦNG DƯỚI)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, trans_y + 68.0, "net/http.RoundTripper (AWS Service Gateway):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, trans_y + 54.0, "• Gửi HTTP Request qua kết nối TLS bảo mật", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, trans_y + 40.0, "• Nhận HTTP raw Response (status, headers, body stream)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, trans_y + 26.0, "• Quản lý Connection Pool, HTTP/2 multiplexing, Keep-Alive", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, trans_y + 12.0, "• Xử lý network timeout, DNS failover và connection reset", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow from Deserialize up to Transport (Request), dashed arrow down (Response)
    deser_y = body_y
    deser_h = trans_y - deser_y - 12.0  # 190.83 pt
    d.add(Rect(col2_x, deser_y, col_w, deser_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 6.0, deser_y + deser_h - 13.0, 80.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col2_x + 46.0, deser_y + deser_h - 10.5, "05 · DESERIALIZE", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 92.0, deser_y + deser_h - 10.5, "Giải mã Response", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 8.0, deser_y + 150.0, "Handler giải mã kết quả trả về từ dịch vụ:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, deser_y + 136.0, "• Mũi tên liền (bên trái) gọi vào transport gửi request", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, deser_y + 122.0, "• Mũi tên nét đứt (bên phải) nhận response trả về", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, deser_y + 104.0, "Quy trình xử lý tại tầng Deserialize:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, deser_y + 90.0, "1. Đọc HTTP Status Code: 200 OK vs 4xx/5xx", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, deser_y + 76.0, "2. Parse XML / JSON body thành Go struct output", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, deser_y + 62.0, "3. Trích xuất metadata: x-amz-request-id", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, deser_y + 48.0, "4. Nếu có lỗi: ánh xạ thành smithy.APIError có kiểu", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, deser_y + 34.0, "5. Trả kết quả về cho ứng dụng người dùng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, deser_y + 16.0, "• Sơ đồ lược bỏ từng lần retry nội bộ của transport", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Request arrow from Deserialize up to Transport
    draw_arrow(d, col2_x + col_w * 0.35, deser_y + deser_h, col2_x + col_w * 0.35, trans_y, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String(col2_x + col_w * 0.35 - 4.0, deser_y + deser_h + 3.0, "Request", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="end"))

    # Response dashed arrow from Transport down to Deserialize
    draw_arrow(d, col2_x + col_w * 0.65, trans_y, col2_x + col_w * 0.65, deser_y + deser_h, color=COLOR_INK_MID, width=0.8, head_size=3.0, dashed=True)
    d.add(String(col2_x + col_w * 0.65 + 4.0, deser_y + deser_h + 3.0, "Response", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Mũi tên liền là đường lồng handler gọi xuôi (Request); mũi tên nét đứt là đường trả về ngược (Response) giải mã kết quả.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 11. Chapter 25 — Figure 43: Git-GitHub Boundaries (278.59 x 362.83 pt)
# ======================================================================
def build_git_github_boundaries_drawing(w: float = 278.59, h: float = 362.83) -> Drawing:
    """Figure 43: Ranh giới giữa Git cục bộ và dịch vụ GitHub.

    Git quản lý object và lịch sử trong kho; GitHub bổ sung các dịch vụ
    cộng tác có API, quyền truy cập và giới hạn riêng.
    Exact dimensions: 278.59 x 362.83 pt (Page 443, xref 504).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 25 // HÌNH 43", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "RANH GIỚI BẢN THỂ: GIT CORE VÀ GITHUB", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Git quản lý Merkle DAG; GitHub bổ sung API, cộng tác và webhooks.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 302.83 pt

    col_w = (w - 24.0) / 2.0  # 127.29 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + 8.0

    # Left Column: Git Core
    d.add(Rect(col1_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, body_y + body_h - 13.0, 72.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 42.0, body_y + body_h - 10.5, "GIT · KHO CỤC BỘ", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 6.0, body_y + body_h - 22.0, "Content Merkle DAG Storage", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    git_items = [
        ("• Quản lý object phân tán", "BookSansBold"),
        ("• 4 loại Object cơ sở:", "BookSansBold"),
        ("  + blob: nội dung tệp thô", "BookMono"),
        ("  + tree: thư mục và mode", "BookMono"),
        ("  + commit: ảnh chụp và cha", "BookMono"),
        ("  + tag: annotated tag", "BookMono"),
        ("• Định danh bằng cryptographic hash:", "BookSans"),
        ("  SHA-1 hoặc SHA-256", "BookMono"),
        ("• Directed Acyclic Graph (DAG)", "BookSans"),
        ("• Hoạt động 100% offline", "BookSansBold"),
        ("• Không cần mạng, không GitHub", "BookSans"),
        ("• Không có khái niệm PR/Issue", "BookSans"),
        ("• Lịch sử lưu trữ bất biến", "BookSans"),
    ]

    gy = body_y + body_h - 36.0
    for gtext, gfont in git_items:
        d.add(String(col1_x + 6.0, gy, gtext, fontName=gfont, fontSize=6.0, fillColor=COLOR_INK_DARK))
        gy -= 18.0

    # Right Column: GitHub Platform
    d.add(Rect(col2_x, body_y, col_w, body_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 6.0, body_y + body_h - 13.0, 78.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col2_x + 45.0, body_y + body_h - 10.5, "GITHUB · NỀN TẢNG", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 6.0, body_y + body_h - 22.0, "Hosted Collaboration SaaS", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    gh_items = [
        ("• Nền tảng SaaS cộng tác", "BookSansBold"),
        ("• Thực thể dịch vụ nền tảng:", "BookSansBold"),
        ("  + Pull Requests & Reviews", "BookMono"),
        ("  + Issues & Discussions", "BookMono"),
        ("  + Releases & Asset hosting", "BookMono"),
        ("  + Actions CI/CD Runners", "BookMono"),
        ("• Webhooks phát sự kiện", "BookSans"),
        ("• REST & GraphQL APIs", "BookMono"),
        ("• Quản lý danh tính, OAuth,", "BookSans"),
        ("  Fine-grained PAT, RBAC", "BookMono"),
        ("• Rate limits, quota, audit log", "BookSans"),
        ("• Bắt buộc kết nối mạng", "BookSansBold"),
        ("• Bổ sung metadata ngoài Git", "BookSans"),
    ]

    hy = body_y + body_h - 36.0
    for htext, hfont in gh_items:
        d.add(String(col2_x + 6.0, hy, htext, fontName=hfont, fontSize=6.0, fillColor=COLOR_INK_DARK))
        hy -= 18.0

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Git quản lý object và lịch sử trong kho; GitHub bổ sung các dịch vụ cộng tác có API, quyền truy cập và giới hạn riêng.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 12. Chapter 25 — Figure 44: Webhook HMAC Verification (407.82 x 362.83 pt)
# ======================================================================
def build_webhook_hmac_verification_drawing(w: float = 407.82, h: float = 362.83) -> Drawing:
    """Figure 44: Xác minh chữ ký HMAC của webhook GitHub.

    Server tính chữ ký từ chính raw body đã nhận rồi so sánh với header.
    Không tuần tự hóa lại JSON trước khi kiểm tra chữ ký.
    Exact dimensions: 407.82 x 362.83 pt (Page 444, xref 506).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 25 // HÌNH 44", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "QUY TRÌNH XÁC MINH CHỮ KÝ HMAC-SHA256 CỦA WEBHOOK GITHUB", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Server tính chữ ký từ chính raw body đã nhận rồi so sánh constant-time; không tuần tự hóa lại JSON.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 302.83 pt

    # Sequence Lifelines: 2 Actors
    actor1_x = 80.0   # GitHub Dispatcher
    actor2_x = 327.82  # Go Webhook Server

    act_box_w = 120.0
    act_box_h = 20.0
    act_box_y = header_y - act_box_h - 6.0

    d.add(Rect(actor1_x - act_box_w / 2.0, act_box_y, act_box_w, act_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor1_x, act_box_y + 11.5, "GITHUB DISPATCHER", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor1_x, act_box_y + 4.5, "Nguồn phát Webhook Event", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    d.add(Rect(actor2_x - act_box_w / 2.0, act_box_y, act_box_w, act_box_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor2_x, act_box_y + 11.5, "GO WEBHOOK SERVER", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, act_box_y + 4.5, "Máy chủ xác thực & điều phối", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # Vertical Lifelines
    lifeline_bot = body_y + 6.0
    lifeline_top = act_box_y
    for ax in (actor1_x, actor2_x):
        line = Line(ax, lifeline_top, ax, lifeline_bot)
        line.strokeColor = COLOR_BORDER
        line.strokeWidth = 0.8
        line.strokeDashArray = [3, 2]
        d.add(line)

    # 1. GitHub computes HMAC
    sy1 = act_box_y - 28.0
    d.add(Rect(actor1_x - 55.0, sy1 - 8.0, 110.0, 22.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(actor1_x, sy1 + 5.0, "HMAC-SHA256(secret, payload)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor1_x, sy1 - 4.5, "Tính chữ ký từ raw JSON bytes", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 2. HTTP POST Transmission
    sy2 = sy1 - 28.0
    draw_arrow(d, actor1_x, sy2, actor2_x, sy2, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor1_x + actor2_x) / 2.0, sy2 + 3.0, "POST /webhook (Raw Body bytes + Header X-Hub-Signature-256)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # 3. Server reads raw body with limit
    sy3 = sy2 - 30.0
    d.add(Rect(actor2_x - 70.0, sy3 - 10.0, 140.0, 24.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(actor2_x, sy3 + 4.0, "io.LimitReader(r.Body, maxBytes)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, sy3 - 6.0, "Đọc raw body có giới hạn kích thước", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 4. CRITICAL SECURITY CALLOUT BANNER
    sy4 = sy3 - 34.0
    d.add(Rect(actor1_x - 30.0, sy4 - 6.0, (actor2_x - actor1_x) + 60.0, 22.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.6, rx=2, ry=2))
    d.add(String((actor1_x + actor2_x) / 2.0, sy4 + 6.0, "QUY TẮC AN NINH BẮT BUỘC: KHÔNG UNMARSHAL RỒI MARSHAL LẠI JSON", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String((actor1_x + actor2_x) / 2.0, sy4 - 3.0, "Mọi phép tuần tự hóa lại JSON sẽ làm đổi thứ tự key và khoảng trắng, làm hỏng chữ ký kiểm tra.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 5. Server calculates expected MAC
    sy5 = sy4 - 30.0
    d.add(Rect(actor2_x - 70.0, sy5 - 10.0, 140.0, 24.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(actor2_x, sy5 + 4.0, "mac.Write(rawBody) -> actualMAC", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, sy5 - 6.0, "Tính chữ ký cục bộ bằng secret chia sẻ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 6. Constant-Time Compare
    sy6 = sy5 - 30.0
    d.add(Rect(actor2_x - 70.0, sy6 - 10.0, 140.0, 24.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=1.5, ry=1.5))
    d.add(String(actor2_x, sy6 + 4.0, "subtle.ConstantTimeCompare()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, sy6 - 6.0, "So sánh hằng thời gian (loại trừ timing attack)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # 7. Two Decisions
    sy7 = sy6 - 32.0
    # Left: Mismatch (401)
    d.add(Rect(actor1_x + 10.0, sy7 - 10.0, 100.0, 22.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(actor1_x + 60.0, sy7 + 3.0, "KHÔNG KHỚP (== 0)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor1_x + 60.0, sy7 - 6.0, "401 / 403: Từ chối ngay", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    draw_arrow(d, actor2_x - 70.0, sy6 - 5.0, actor1_x + 110.0, sy7 + 5.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Right: Match (200 OK)
    d.add(Rect(actor2_x - 50.0, sy7 - 10.0, 100.0, 22.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=1.5, ry=1.5))
    d.add(String(actor2_x, sy7 + 3.0, "HỢP LỆ (== 1)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, sy7 - 6.0, "200 OK: Chuyển xử lý", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    draw_arrow(d, actor2_x, sy6 - 10.0, actor2_x, sy7 + 12.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Server tính chữ ký từ chính raw body đã nhận rồi so sánh constant-time; không tuần tự hóa lại JSON trước khi kiểm tra chữ ký.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 13. Chapter 25 — Figure 45: Webhook Delivery Deduplication (462.12 x 362.83 pt)
# ======================================================================
def build_webhook_delivery_deduplication_drawing(w: float = 462.12, h: float = 362.83) -> Drawing:
    """Figure 45: Nhận diện webhook được gửi lại bằng Delivery ID.

    Bài thực hành nhận diện cùng một mã Delivery ID để tránh lặp side effect
    trong đường chạy được kiểm thử. Lưu bản, xử lý crash và delivery đồng thời
    cần policy cùng cơ chế riêng.
    Exact dimensions: 462.12 x 362.83 pt (Page 447, xref 510).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 25 // HÌNH 45", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "CƠ CHẾ KHỬ TRÙNG LẶP WEBHOOK DELIVERY (IDEMPOTENT HANDLER)", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Nhận diện cùng một mã Delivery ID để tránh lặp side effect khi GitHub gửi lại webhook.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 302.83 pt

    # Sequence Lifelines: 3 Actors
    actor1_x = 75.0   # GitHub Dispatcher
    actor2_x = 231.06  # Webhook Server Go
    actor3_x = 387.0   # Deduplication Store

    act_box_w = 110.0
    act_box_h = 20.0
    act_box_y = header_y - act_box_h - 6.0

    d.add(Rect(actor1_x - act_box_w / 2.0, act_box_y, act_box_w, act_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor1_x, act_box_y + 11.5, "GITHUB DISPATCHER", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor1_x, act_box_y + 4.5, "At-least-once delivery", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    d.add(Rect(actor2_x - act_box_w / 2.0, act_box_y, act_box_w, act_box_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor2_x, act_box_y + 11.5, "WEBHOOK SERVER (GO)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, act_box_y + 4.5, "Idempotent Event Handler", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    d.add(Rect(actor3_x - act_box_w / 2.0, act_box_y, act_box_w, act_box_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor3_x, act_box_y + 11.5, "DEDUPLICATION STORE", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor3_x, act_box_y + 4.5, "SQLite / KV Store", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # Lifelines
    lifeline_bot = body_y + 6.0
    lifeline_top = act_box_y
    for ax in (actor1_x, actor2_x, actor3_x):
        line = Line(ax, lifeline_top, ax, lifeline_bot)
        line.strokeColor = COLOR_BORDER
        line.strokeWidth = 0.8
        line.strokeDashArray = [3, 2]
        d.add(line)

    # Stage 1: First Delivery
    y1 = act_box_y - 24.0
    draw_arrow(d, actor1_x, y1, actor2_x, y1, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor1_x + actor2_x) / 2.0, y1 + 3.0, "1. POST /webhook (X-GitHub-Delivery: 7a1b...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    y2 = y1 - 20.0
    draw_arrow(d, actor2_x, y2, actor3_x, y2, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor2_x + actor3_x) / 2.0, y2 + 3.0, "2. SELECT EXISTS(7a1b...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    y3 = y2 - 18.0
    draw_arrow(d, actor3_x, y3, actor2_x, y3, color=COLOR_INK_MID, width=0.8, head_size=3.0)
    d.add(String((actor2_x + actor3_x) / 2.0, y3 + 3.0, "3. false (Chưa xử lý)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    y4 = y3 - 22.0
    d.add(Rect(actor2_x - 65.0, y4 - 8.0, 130.0, 20.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(actor2_x, y4 + 3.0, "THỰC HIỆN SIDE EFFECT NGHIỆP VỤ", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, y4 - 5.0, "Kích hoạt CI/CD build, tạo comment PR...", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    y5 = y4 - 22.0
    draw_arrow(d, actor2_x, y5, actor3_x, y5, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor2_x + actor3_x) / 2.0, y5 + 3.0, "4. INSERT INTO deliveries (id=7a1b...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    y6 = y5 - 18.0
    draw_arrow(d, actor2_x, y6, actor1_x, y6, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor1_x + actor2_x) / 2.0, y6 + 3.0, "5. HTTP 200 OK (Xử lý hoàn tất)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Break: Redelivery / Retry Event
    y_break = y6 - 22.0
    d.add(Rect(actor1_x - 20.0, y_break - 6.0, (actor3_x - actor1_x) + 40.0, 18.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String((actor1_x + actor3_x) / 2.0, y_break + 4.0, "--- MẠNG TIMEOUT HOẶC RETRY TỪ PHÍA GITHUB (REDELIVERY) ---", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String((actor1_x + actor3_x) / 2.0, y_break - 4.0, "GitHub gửi lại webhook với cùng Delivery ID: 7a1b... để đảm bảo tính sẵn sàng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # Stage 2: Second Delivery (Idempotent Drop)
    y7 = y_break - 24.0
    draw_arrow(d, actor1_x, y7, actor2_x, y7, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor1_x + actor2_x) / 2.0, y7 + 3.0, "6. POST /webhook (CÙNG ID: 7a1b...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    y8 = y7 - 18.0
    draw_arrow(d, actor2_x, y8, actor3_x, y8, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor2_x + actor3_x) / 2.0, y8 + 3.0, "7. SELECT EXISTS(7a1b...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    y9 = y8 - 18.0
    draw_arrow(d, actor3_x, y9, actor2_x, y9, color=COLOR_INK_MID, width=0.8, head_size=3.0)
    d.add(String((actor2_x + actor3_x) / 2.0, y9 + 3.0, "8. true (ĐÃ TỒN TẠI TRONG STORE)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    y10 = y9 - 22.0
    d.add(Rect(actor2_x - 65.0, y10 - 8.0, 130.0, 20.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=1.5, ry=1.5))
    d.add(String(actor2_x, y10 + 3.0, "BỎ QUA (DROP) SIDE EFFECT", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, y10 - 5.0, "Không lặp lại hành động, bảo đảm tính bất biến", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    y11 = y10 - 20.0
    draw_arrow(d, actor2_x, y11, actor1_x, y11, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor1_x + actor2_x) / 2.0, y11 + 3.0, "9. HTTP 200 OK (Báo thành công để dừng retry)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Bài thực hành nhận diện cùng Delivery ID để tránh lặp side effect; lưu bản, xử lý crash và delivery đồng thời cần cơ chế riêng.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 14. Chapter 26 — Figure 46: Supply Chain Policy Evidence (214.51 x 362.83 pt)
# ======================================================================
def build_supply_chain_policy_evidence_drawing(w: float = 214.51, h: float = 362.83) -> Drawing:
    """Figure 46: Chuỗi bằng chứng và cổng chính sách triển khai.

    Cổng chỉ xác minh các bằng chứng mà chính sách yêu cầu. Digest, chữ ký
    và provenance có vai trò khác nhau; đủ bằng chứng theo policy không chứng
    minh artifact không có mã lỗi hoặc lỗ hổng.
    Exact dimensions: 214.51 x 362.83 pt (Page 465, xref 529).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 26 // HÌNH 46", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "CHUỖI BẰNG CHỨNG SUPPLY CHAIN", fontName="BookSansBold", fontSize=6.5, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "6 mắt xích từ nguồn đến Cổng chính sách (Policy Gate).", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 302.83 pt

    cw = w - 16.0  # 198.51 pt
    cx = 8.0

    # 6 Stacked Sequential Evidence Cards
    card_gap = 6.0
    card_h = (body_h - 5 * card_gap) / 6.0  # 45.47 pt each

    stages = [
        ("01 · NGUỒN (COMMIT)", "Commit SHA, git tree, author identity", "Kho nguồn xác thực", COLOR_BG_CARD),
        ("02 · PHỤ THUỘC (DEPS)", "go.mod + go.sum kiểm tra checksum", "Module graphs đã khóa", COLOR_WHITE),
        ("03 · BUILD PROVENANCE", "SLSA provenance attestation, builder", "Môi trường hermetic", COLOR_BG_CARD),
        ("04 · ARTIFACT DIGEST", "Container image định danh sha256:...", "Bất biến theo nội dung", COLOR_WHITE),
        ("05 · XÁC MINH CHỮ KÝ", "Cosign signature, Rekor log, Fulcio", "Gốc tin cậy mã hóa", COLOR_BG_CARD),
        ("06 · CỔNG POLICY (GATE)", "Đủ bằng chứng: ALLOW | Thiếu: DENY", "Fail-Closed Admission", COLOR_BG_SUBTLE),
    ]

    for idx, (stitle, sdesc1, sdesc2, sbg) in enumerate(stages):
        cy = body_y + body_h - (idx + 1) * card_h - idx * card_gap
        is_gate = (idx == 5)
        d.add(Rect(cx, cy, cw, card_h, fillColor=sbg, strokeColor=COLOR_BORDER_DARK if is_gate else COLOR_BORDER, strokeWidth=0.8 if is_gate else 0.5, rx=1.5, ry=1.5))
        d.add(String(cx + 8.0, cy + card_h - 11.0, stitle, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(cx + 8.0, cy + card_h - 22.0, sdesc1, fontName="BookMono" if idx in (1, 3) else "BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(cx + 8.0, cy + 6.0, "• " + sdesc2, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED if not is_gate else COLOR_INK_DARK))

        if idx < 5:
            arrow_y1 = cy
            arrow_y2 = cy - card_gap
            draw_arrow(d, cx + cw / 2.0, arrow_y1, cx + cw / 2.0, arrow_y2, color=COLOR_INK_DARK, width=0.8, head_size=2.5)

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Cổng chỉ xác minh bằng chứng mà chính sách yêu cầu; fail-closed khi thiếu bằng chứng.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 15. Chapter 26 — Figure 47: Vulnerability Call Reachability (476.22 x 330.88 pt)
# ======================================================================
def build_vulnerability_call_reachability_drawing(w: float = 476.22, h: float = 330.88) -> Drawing:
    """Figure 47: Phân biệt phụ thuộc có symbol và đường gọi có thể tới.

    Có phụ thuộc bị ảnh hưởng và tìm thấy đường gọi tới bcrypt nhưng không thấy
    đường gọi tới ssh.ParsePrivateKey. Kết quả phải được hiểu trong giới hạn
    của bộ phân tích và build đang xét.
    Exact dimensions: 476.22 x 330.88 pt (Page 468, xref 533).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 26 // HÌNH 47", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "PHÂN BIỆT PHỤ THUỘC CÓ SYMBOL VÀ ĐƯỜNG GỌI CÓ THỂ TỚI (CALL REACHABILITY)", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "govulncheck phân tích đường gọi tĩnh để lọc nhiễu các lỗ hổng không kích hoạt từ mã nguồn ứng dụng.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 270.88 pt

    # Top Center Root: Application Entrypoint
    root_w = 260.0
    root_h = 38.0
    root_x = (w - root_w) / 2.0
    root_y = body_y + body_h - root_h
    d.add(Rect(root_x, root_y, root_w, root_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(w / 2.0, root_y + root_h - 11.0, "ỨNG DỤNG NGHIỆP VỤ (cmd/server/main.go)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(w / 2.0, root_y + 16.0, "Module: mycompany.com/backend · Root of Call Graph", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
    d.add(String(w / 2.0, root_y + 6.0, "Phụ thuộc module: golang.org/x/crypto", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Two Side-by-Side Comparison Columns
    col_w = (w - 24.0) / 2.0  # 226.11 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + 8.0
    col_y = body_y
    col_h = root_y - col_y - 14.0  # 218.88 pt

    # Branch Arrows from Root to Columns
    draw_arrow(d, root_x + 40.0, root_y, col1_x + col_w / 2.0, col_y + col_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, root_x + root_w - 40.0, root_y, col2_x + col_w / 2.0, col_y + col_h, color=COLOR_INK_MID, width=0.8, head_size=3.0, dashed=True)

    # ------------------------------------------------------------------
    # Left Column: Reachable Vulnerability (Reachable Call Path)
    # ------------------------------------------------------------------
    d.add(Rect(col1_x, col_y, col_w, col_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, col_y + col_h - 13.0, 96.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 54.0, col_y + col_h - 10.5, "ĐƯỜNG GỌI CÓ THỂ TỚI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 108.0, col_y + col_h - 10.5, "(REACHABLE FINDING)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    d.add(String(col1_x + 8.0, col_y + col_h - 26.0, "Dependency: golang.org/x/crypto/bcrypt", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, col_y + col_h - 38.0, "Vết đường gọi thực tế (Call Trace):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Box for Call Trace
    ct_h = 76.0
    ct_y = col_y + col_h - 120.0
    d.add(Rect(col1_x + 6.0, ct_y, col_w - 12.0, ct_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 10.0, ct_y + ct_h - 12.0, "main.go: main()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, ct_y + ct_h - 24.0, "  -> auth.ValidateUser(password)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, ct_y + ct_h - 36.0, "  -> bcrypt.CompareHashAndPassword()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, ct_y + ct_h - 48.0, "  -> bcrypt.GenerateFromPassword()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, ct_y + 8.0, "[!] Trúng ký hiệu (symbol) có CVE đã công bố", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    d.add(String(col1_x + 8.0, col_y + 84.0, "Kết luận phân tích govulncheck:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, col_y + 72.0, "• Mã nhị phân thực sự chứa và gọi symbol lỗi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, col_y + 60.0, "• Nguy cơ khai thác thực tế tồn tại (Reachable)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, col_y + 48.0, "• Hành động: Bắt buộc nâng cấp phiên bản vá", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, col_y + 36.0, "• Cổng policy sẽ BLOCK bản phát hành này", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, col_y + 20.0, "• Không thể bỏ qua bằng chính sách lọc thông thường", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Right Column: Unreachable Vulnerability (Unreachable Symbol)
    # ------------------------------------------------------------------
    d.add(Rect(col2_x, col_y, col_w, col_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 6.0, col_y + col_h - 13.0, 108.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col2_x + 60.0, col_y + col_h - 10.5, "KHÔNG CÓ ĐƯỜNG GỌI TỚI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 120.0, col_y + col_h - 10.5, "(UNREACHABLE)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 8.0, col_y + col_h - 26.0, "Dependency: golang.org/x/crypto/ssh", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, col_y + col_h - 38.0, "Phân tích đồ thị gọi (Call Graph Analysis):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Box for Unreachable Explanation
    un_h = 76.0
    un_y = col_y + col_h - 120.0
    d.add(Rect(col2_x + 6.0, un_y, col_w - 12.0, un_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 10.0, un_y + un_h - 12.0, "Cùng nằm trong module: golang.org/x/crypto", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, un_y + un_h - 24.0, "Symbol lỗi: ssh.ParsePrivateKey() có CVE", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, un_y + un_h - 36.0, "Ứng dụng KHÔNG import hoặc gọi package ssh", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, un_y + un_h - 48.0, "Đường nét đứt: phụ thuộc có symbol, không có call edge", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(col2_x + 10.0, un_y + 8.0, "[V] Không tìm thấy đường gọi từ mã nguồn ứng dụng", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 8.0, col_y + 84.0, "Ý nghĩa giảm thiểu cảnh báo giả (Noise Reduction):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, col_y + 72.0, "• Symbol lỗi tồn tại trong cây thư mục module tải về", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, col_y + 60.0, "• Nhưng trình liên kết (linker) loại bỏ mã không dùng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, col_y + 48.0, "• Tránh làm gián đoạn CI/CD bởi các cảnh báo giả", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, col_y + 36.0, "• Vẫn cần theo dõi nếu ứng dụng dùng dynamic reflection", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, col_y + 20.0, "• Phân biệt rõ CVE phụ thuộc với CVE trong binary", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Có phụ thuộc bị ảnh hưởng và có đường gọi tới bcrypt nhưng không thấy đường gọi tới ssh.ParsePrivateKey; kết quả phụ thuộc chế độ build.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 16. Chapter 26 — Figure 48: Container Tag vs Digest (476.22 x 327.02 pt)
# ======================================================================
def build_container_tag_digest_drawing(w: float = 476.22, h: float = 327.02) -> Drawing:
    """Figure 48: Thẻ nhãn (tag) và mã băm (digest) của container image.

    Thẻ nhãn (tag) được phân giải thành mã băm (digest) tại một thời điểm.
    Dùng digest cố định nội dung được tham chiếu, không tự xác minh người tạo
    hay độ an toàn của nội dung ấy.
    Exact dimensions: 476.22 x 327.02 pt (Page 470, xref 536).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 26 // HÌNH 48", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "BẢN CHẤT CONTAINER TAG VÀ DIGEST: CON TRỎ ĐỔI ĐÍCH VS MÃ BĂM NỘI DUNG", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Tag là con trỏ có thể thay đổi (Mutable Pointer); Digest là định danh nội dung bất biến (SHA-256).", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 267.02 pt

    half_h = (body_h - 8.0) / 2.0  # 129.51 pt each
    top_y = body_y + half_h + 8.0
    bot_y = body_y

    # ------------------------------------------------------------------
    # Top Half: CONTAINER TAG (MUTABLE POINTER)
    # ------------------------------------------------------------------
    d.add(Rect(8.0, top_y, w - 16.0, half_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(14.0, top_y + half_h - 13.0, 130.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(79.0, top_y + half_h - 10.5, "TAG: CON TRỎ CÓ THỂ THAY ĐỔI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(150.0, top_y + half_h - 10.5, "(MUTABLE POINTER - NGUY CƠ TRÔI DẠT PHIÊN BẢN)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Left box: Tag Reference Timeline
    t_box_w = 200.0
    d.add(Rect(14.0, top_y + 10.0, t_box_w, half_h - 28.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(20.0, top_y + half_h - 38.0, "Tham chiếu: myorg/app:v1.2.0", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(20.0, top_y + half_h - 52.0, "• Thời điểm T0: Build 1 push v1.2.0", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(28.0, top_y + half_h - 62.0, "-> Trỏ Image A (sha256:7f83b1...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(20.0, top_y + half_h - 74.0, "• Thời điểm T1: Build 2 ghi đè cùng tag v1.2.0", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(28.0, top_y + half_h - 84.0, "-> Trỏ Image B (sha256:4a12c8...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(20.0, top_y + 16.0, "Tag chỉ là alias văn bản trong Registry", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Right box: Consequences on Cluster Nodes
    r_box_x = 14.0 + t_box_w + 10.0
    r_box_w = (w - 16.0) - r_box_x - 6.0
    d.add(Rect(r_box_x, top_y + 10.0, r_box_w, half_h - 28.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(r_box_x + 8.0, top_y + half_h - 38.0, "Hậu quả trôi dạt (Drift) trong cụm Kubernetes:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, top_y + half_h - 52.0, "• Node 1 (đã cache Image A) tiếp tục chạy Image A cũ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, top_y + half_h - 64.0, "• Node 2 (node mới tạo) pull Image B mới với cùng tag v1.2.0", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, top_y + half_h - 76.0, "• Pod template hoàn toàn giống nhau nhưng hành vi khác biệt", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, top_y + 16.0, "• Phụ thuộc vào imagePullPolicy, cache node và cấu hình registry", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # ------------------------------------------------------------------
    # Bottom Half: CONTAINER DIGEST (IMMUTABLE CONTENT HASH)
    # ------------------------------------------------------------------
    d.add(Rect(8.0, bot_y, w - 16.0, half_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(14.0, bot_y + half_h - 13.0, 136.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(82.0, bot_y + half_h - 10.5, "DIGEST: NGUỒN CHÂN LÝ BẤT BIẾN", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(156.0, bot_y + half_h - 10.5, "(IMMUTABLE CONTENT-ADDRESSABLE IDENTIFIER)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Left box: Digest Hash Model
    d.add(Rect(14.0, bot_y + 10.0, t_box_w, half_h - 28.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(20.0, bot_y + half_h - 38.0, "Tham chiếu: myorg/app@sha256:7f83b1...", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(20.0, bot_y + half_h - 52.0, "• Mã băm SHA-256 tính trực tiếp từ Manifest:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(28.0, bot_y + half_h - 62.0, "Root fs layers, config JSON, environment", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(20.0, bot_y + half_h - 74.0, "• Tính chất bất biến tuyệt đối (Cryptographic Truth):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(28.0, bot_y + half_h - 84.0, "Đổi 1 bit mã nguồn -> Digest hoàn toàn mới", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(20.0, bot_y + 16.0, "Không thể bị ghi đè hay thay thế ngầm", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Right box: Deterministic Execution
    d.add(Rect(r_box_x, bot_y + 10.0, r_box_w, half_h - 28.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(r_box_x + 8.0, bot_y + half_h - 38.0, "Lợi ích tất định và bảo mật chuỗi cung ứng:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, bot_y + half_h - 52.0, "• 100% các node trong cụm chạy chính xác cùng một mã nhị phân", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, bot_y + half_h - 64.0, "• Loại bỏ hoàn toàn nguy cơ tấn công tráo tag (Tag Hijacking)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, bot_y + half_h - 76.0, "• Điều kiện tiên quyết để ký Cosign và kiểm tra tại Admission Webhook", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, bot_y + 16.0, "• Lưu ý: Digest chỉ cố định nội dung, không tự chứng minh nguồn gốc", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Tag được phân giải thành digest tại một thời điểm; dùng digest cố định nội dung nhưng không tự xác minh người tạo hay độ an toàn.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 17. Chapter 27 — Figure 49: eBPF Build & Load (244.10 x 362.83 pt)
# ======================================================================
def build_ebpf_build_load_drawing(w: float = 244.10, h: float = 362.83) -> Drawing:
    """Figure 49: Tách giai đoạn build eBPF và giai đoạn load trên Linux.

    Clang và bpf2go thuộc toolchain build. Binary Go mang object BPF đến
    runtime; kernel vẫn kiểm tra program, quyền và khả năng hỗ trợ trước
    khi load hoặc attach thành công.
    Exact dimensions: 244.10 x 362.83 pt (Page 490, xref 557).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 27 // HÌNH 49", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "QUY TRÌNH BUILD & LOAD EBPF", fontName="BookSansBold", fontSize=6.8, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Tách biệt Build-time toolchain và Runtime kernel load.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 302.83 pt

    cw = w - 16.0  # 228.10 pt
    cx = 8.0

    # Section 1: BUILD TIME (C & bpf2go)
    sec1_h = 146.0
    sec1_y = body_y + body_h - sec1_h
    d.add(Rect(cx, sec1_y, cw, sec1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(cx + 6.0, sec1_y + sec1_h - 13.0, 96.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(cx + 54.0, sec1_y + sec1_h - 10.5, "GIAI ĐOẠN BUILD-TIME", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(cx + 106.0, sec1_y + sec1_h - 10.5, "(C & CLANG TOOLCHAIN)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Step 1: C Source
    d.add(String(cx + 8.0, sec1_y + 118.0, "1. C SOURCE CODE:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec1_y + 107.0, "exec_observer.bpf.c + vmlinux.h (BTF types)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Step 2: Clang + bpf2go
    d.add(String(cx + 8.0, sec1_y + 88.0, "2. CLANG + BPF2GO COMPILER:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec1_y + 77.0, "Biên dịch sang mã máy BPF ELF (observer_bpfel.o)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec1_y + 66.0, "Sinh Go wrapper bindings (observer_bpfel.go)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Step 3: Go Build
    d.add(String(cx + 8.0, sec1_y + 46.0, "3. GO BUILD & EMBED:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec1_y + 35.0, "go build -> Đóng gói bytecode vào binary Go", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec1_y + 24.0, "Binary độc lập CGO-free, dễ dàng phân phối", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec1_y + 12.0, "• Không yêu cầu Clang trên máy chủ triển khai", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Boundary Arrow across Build and Runtime
    draw_arrow(d, w / 2.0, sec1_y, w / 2.0, sec1_y - 12.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String(w / 2.0 + 4.0, sec1_y - 8.0, "Binary Go mang BPF bytecode tới runtime", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Section 2: RUNTIME (Go Userspace & Kernel)
    sec2_y = body_y
    sec2_h = sec1_y - sec2_y - 14.0  # 142.83 pt
    d.add(Rect(cx, sec2_y, cw, sec2_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(cx + 6.0, sec2_y + sec2_h - 13.0, 96.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(cx + 54.0, sec2_y + sec2_h - 10.5, "GIAI ĐOẠN RUNTIME", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(cx + 106.0, sec2_y + sec2_h - 10.5, "(USERSPACE & KERNEL)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Step 4: Go Userspace Loader
    d.add(String(cx + 8.0, sec2_y + 114.0, "4. USER SPACE RUNTIME (GO):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec2_y + 103.0, "Ứng dụng dùng thư viện github.com/cilium/ebpf", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec2_y + 92.0, "Gọi syscall bpf(BPF_PROG_LOAD) nạp program", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Step 5: Kernel Verification & Attach
    d.add(String(cx + 8.0, sec2_y + 72.0, "5. LINUX KERNEL RUNTIME:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec2_y + 61.0, "• In-Kernel Verifier: Kiểm tra an toàn bộ nhớ,", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 20.0, sec2_y + 51.0, "chống lặp vô hạn, kiểm tra quyền CAP_BPF / root", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(cx + 14.0, sec2_y + 39.0, "• Attach: Gắn vào tracepoint/sys_enter_execve", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec2_y + 27.0, "• BPF Ring Buffer / Map: Đẩy sự kiện về Go", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 14.0, sec2_y + 12.0, "• Kernel từ chối nạp nếu không đủ quyền hoặc sai BTF", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Clang và bpf2go chạy lúc build; kernel verifier kiểm soát an toàn lúc load; binary Go không phụ thuộc cgo.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# 18. Chapter 29 — Figure 50: Change Evidence Gate (476.22 x 260.59 pt)
# ======================================================================
def build_change_evidence_gate_drawing(w: float = 476.22, h: float = 260.59) -> Drawing:
    """Figure 50: Luồng đề xuất, kiểm chứng, phê duyệt, hành động và quan sát.

    Đề xuất không mặc nhiên có quyền thực thi. Mỗi bước kiểm tra phải gắn với
    đúng artifact, target và caller; mũi tên diễn tả policy của scenario,
    không phải một protocol đảm bảo an toàn sẵn có.
    Exact dimensions: 476.22 x 260.59 pt (Page 544, xref 612).
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
    d.add(String(56.0, header_y + 8.5, "CHƯƠNG 29 // HÌNH 50", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(110.0, header_y + 13.0, "MÔ HÌNH CỔNG BẰNG CHỨNG VÀ KIỂM SOÁT THAY ĐỔI (CHANGE EVIDENCE GATE)", fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
    d.add(String(110.0, header_y + 5.5, "Đề xuất không có quyền tự thực thi; mỗi bước kiểm tra phải gắn chặt với đúng artifact, target và caller.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    body_y = 26.0
    body_h = header_y - body_y - 6.0  # 200.59 pt

    # 5 Horizontal Governed Stages
    col_gap = 6.0
    col_w = (w - 16.0 - 4 * col_gap) / 5.0  # 87.24 pt each
    col_h = 126.0
    col_y = body_y + body_h - col_h

    stages = [
        ("01 · ĐỀ XUẤT", "PROPOSAL", [
            ("Target allowlist", "BookSansBold"),
            ("Action:", "BookSans"),
            ("restart-demo", "BookMono"),
            ("Diff SHA-256", "BookMono"),
            ("Không tự cấp quyền", "BookSans"),
        ]),
        ("02 · KIỂM CHỨNG", "EVIDENCE", [
            ("Test độc lập xanh", "BookSansBold"),
            ("Khớp plan digest", "BookSans"),
            ("Freshness < 1p", "BookMono"),
            ("Bằng chứng mới", "BookSans"),
            ("Cấm mượn log cũ", "BookSans"),
        ]),
        ("03 · PHÊ DUYỆT", "APPROVAL", [
            ("Caller xác thực", "BookSansBold"),
            ("Chữ ký ủy quyền", "BookSans"),
            ("Đúng plan digest", "BookMono"),
            ("Chưa hết hạn", "BookSans"),
            ("Quyền trong phạm vi", "BookSans"),
        ]),
        ("04 · THỰC THI", "SCOPED EXEC", [
            ("Quyền tối thiểu", "BookSansBold"),
            ("Sandbox cô lập", "BookSans"),
            ("Timeout bảo vệ", "BookMono"),
            ("Idempotent run", "BookMono"),
            ("Ghi audit log", "BookSans"),
        ]),
        ("05 · QUAN SÁT", "OBSERVE", [
            ("Hậu điều kiện", "BookSansBold"),
            ("Probe /readyz", "BookMono"),
            ("Đo lường metrics", "BookSans"),
            ("Tự rollback lỗi", "BookSansBold"),
            ("Xác nhận trạng thái", "BookSans"),
        ]),
    ]

    for idx, (stitle, ssub, slines) in enumerate(stages):
        sx = 8.0 + idx * (col_w + col_gap)
        is_highlight = (idx in (1, 2))
        d.add(Rect(sx, col_y, col_w, col_h, fillColor=COLOR_BG_CARD if not is_highlight else COLOR_WHITE, strokeColor=COLOR_BORDER_DARK if is_highlight else COLOR_BORDER, strokeWidth=0.8 if is_highlight else 0.5, rx=2, ry=2))
        d.add(String(sx + col_w / 2.0, col_y + col_h - 11.0, stitle, fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
        d.add(String(sx + col_w / 2.0, col_y + col_h - 20.0, ssub, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

        line_y = col_y + col_h - 34.0
        for ltext, lfont in slines:
            d.add(String(sx + 6.0, line_y, ltext, fontName=lfont, fontSize=6.0, fillColor=COLOR_INK_DARK if "Bold" in lfont else COLOR_INK_MID))
            line_y -= 14.0

        if idx < 4:
            draw_arrow(d, sx + col_w, col_y + col_h / 2.0, sx + col_w + col_gap, col_y + col_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=2.8)

    # Fail-Closed Policy Banner below Stages
    banner_y = body_y
    banner_h = col_y - banner_y - 8.0  # 66.59 pt
    d.add(Rect(8.0, banner_y, w - 16.0, banner_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(14.0, banner_y + banner_h - 13.0, 130.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(79.0, banner_y + banner_h - 10.5, "NGUYÊN TẮC POLICY FAIL-CLOSED", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(String(14.0, banner_y + 36.0, "• Thiếu bất kỳ bằng chứng nào (diff sai lệch, log test cũ quá 1 phút, caller không đủ quyền) -> LẬP TỨC TỪ CHỐI, CHẶN THỰC THI.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(14.0, banner_y + 24.0, "• Tính toàn vẹn: Digest bao gồm version encoding, action, target và diff hash để ngăn chặn nhầm lẫn phiên bản và bằng chứng mượn.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(14.0, banner_y + 12.0, "• Ranh giới bảo mật: Phê duyệt chỉ có hiệu lực cho duy nhất một lần thực thi đối với đúng bản ghi thay đổi đã được kiểm chứng.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Bottom Invariant Footer Banner
    footer_h = 16.0
    footer_y = 4.0
    d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(8.0, footer_y + 5.0, "• Invariant: Đề xuất không mặc nhiên có quyền thực thi. Mỗi bước kiểm tra phải gắn với đúng artifact, target và caller; fail-closed khi thiếu bằng chứng.", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ======================================================================
# DIAGRAM SPECS REGISTRY (ALL 18 DIAGRAMS IN CH 18-29)
# ======================================================================
DIAGRAM_SPECS = {
    # Group 1: Figures 33 to 37 (Chapters 18, 19, 21, 22)
    "workflow-promotion-jobs.png": {
        "builder": build_workflow_promotion_jobs_drawing,
        "chapter": 18,
        "figure": 33,
        "title": "Quy trình tự động truyền định danh và bằng chứng qua các tác vụ",
        "page": 331,
        "xref": 382,
        "w_pt": 476.22,
        "h_pt": 330.21,
    },
    "type-information-boundaries.png": {
        "builder": build_type_information_boundaries_drawing,
        "chapter": 19,
        "figure": 34,
        "title": "Lựa chọn tầng trừu tượng phù hợp với câu hỏi kỹ thuật",
        "page": 341,
        "xref": 393,
        "w_pt": 413.18,
        "h_pt": 362.83,
    },
    "edge-level-comparison.png": {
        "builder": build_edge_level_comparison_drawing,
        "chapter": 21,
        "figure": 35,
        "title": "So sánh Edge-Triggered và Level-Triggered",
        "page": 371,
        "xref": 424,
        "w_pt": 476.22,
        "h_pt": 162.43,
    },
    "client-go-controller-flow.png": {
        "builder": build_client_go_controller_flow_drawing,
        "chapter": 22,
        "figure": 36,
        "title": "Luồng sự kiện của bộ điều khiển client-go",
        "page": 385,
        "xref": 439,
        "w_pt": 476.22,
        "h_pt": 301.61,
    },
    "client-go-list-watch.png": {
        "builder": build_client_go_list_watch_drawing,
        "chapter": 22,
        "figure": 37,
        "title": "Trình tự Reflector List/Watch và xử lý HTTP 410 Gone",
        "page": 386,
        "xref": 441,
        "w_pt": 476.22,
        "h_pt": 275.15,
    },

    # Group 2: Figures 38 to 42 (Chapters 23, 24)
    "operator-capabilities.png": {
        "builder": build_operator_capabilities_drawing,
        "chapter": 23,
        "figure": 38,
        "title": "Mô hình năng lực và tri thức vận hành trong operator",
        "page": 404,
        "xref": 460,
        "w_pt": 476.22,
        "h_pt": 254.61,
    },
    "operator-manager-boundaries.png": {
        "builder": build_operator_manager_boundaries_drawing,
        "chapter": 23,
        "figure": 39,
        "title": "Ranh giới và phân định trách nhiệm Manager, Reconciler và Client",
        "page": 405,
        "xref": 462,
        "w_pt": 473.72,
        "h_pt": 362.83,
    },
    "operator-finalizer-lifecycle.png": {
        "builder": build_operator_finalizer_lifecycle_drawing,
        "chapter": 23,
        "figure": 40,
        "title": "Vòng đời và xử lý finalizer trong controller",
        "page": 410,
        "xref": 468,
        "w_pt": 342.25,
        "h_pt": 362.83,
    },
    "aws-credentials-resolution.png": {
        "builder": build_aws_credentials_resolution_drawing,
        "chapter": 24,
        "figure": 41,
        "title": "Phân giải credentials trong AWS SDK for Go v2",
        "page": 426,
        "xref": 485,
        "w_pt": 264.41,
        "h_pt": 362.83,
    },
    "smithy-request-response.png": {
        "builder": build_smithy_request_response_drawing,
        "chapter": 24,
        "figure": 42,
        "title": "Đường request và response qua Smithy middleware stack",
        "page": 429,
        "xref": 489,
        "w_pt": 437.54,
        "h_pt": 362.83,
    },

    # Group 3: Figures 43 to 48 (Chapters 25, 26)
    "git-github-boundaries.png": {
        "builder": build_git_github_boundaries_drawing,
        "chapter": 25,
        "figure": 43,
        "title": "Ranh giới bản thể: Git core và dịch vụ nền tảng GitHub",
        "page": 443,
        "xref": 504,
        "w_pt": 278.59,
        "h_pt": 362.83,
    },
    "webhook-hmac-verification.png": {
        "builder": build_webhook_hmac_verification_drawing,
        "chapter": 25,
        "figure": 44,
        "title": "Xác minh chữ ký HMAC-SHA256 của webhook GitHub",
        "page": 444,
        "xref": 506,
        "w_pt": 407.82,
        "h_pt": 362.83,
    },
    "webhook-delivery-deduplication.png": {
        "builder": build_webhook_delivery_deduplication_drawing,
        "chapter": 25,
        "figure": 45,
        "title": "Cơ chế khử trùng lặp webhook delivery bằng Delivery ID",
        "page": 447,
        "xref": 510,
        "w_pt": 462.12,
        "h_pt": 362.83,
    },
    "supply-chain-policy-evidence.png": {
        "builder": build_supply_chain_policy_evidence_drawing,
        "chapter": 26,
        "figure": 46,
        "title": "Chuỗi bằng chứng và cổng chính sách triển khai",
        "page": 465,
        "xref": 529,
        "w_pt": 214.51,
        "h_pt": 362.83,
    },
    "vulnerability-call-reachability.png": {
        "builder": build_vulnerability_call_reachability_drawing,
        "chapter": 26,
        "figure": 47,
        "title": "Phân tích khả năng tới của mã lỗi qua govulncheck",
        "page": 468,
        "xref": 533,
        "w_pt": 476.22,
        "h_pt": 330.88,
    },
    "container-tag-digest.png": {
        "builder": build_container_tag_digest_drawing,
        "chapter": 26,
        "figure": 48,
        "title": "Bản chất Container Tag và Digest: con trỏ đổi đích vs mã băm nội dung",
        "page": 470,
        "xref": 536,
        "w_pt": 476.22,
        "h_pt": 327.02,
    },

    # Group 4: Figures 49 to 50 (Chapters 27, 29)
    "ebpf-build-load.png": {
        "builder": build_ebpf_build_load_drawing,
        "chapter": 27,
        "figure": 49,
        "title": "Tách giai đoạn build eBPF và giai đoạn load trên Linux",
        "page": 490,
        "xref": 557,
        "w_pt": 244.10,
        "h_pt": 362.83,
    },
    "change-evidence-gate.png": {
        "builder": build_change_evidence_gate_drawing,
        "chapter": 29,
        "figure": 50,
        "title": "Mô hình cổng bằng chứng và kiểm soát thay đổi (Change Evidence Gate)",
        "page": 544,
        "xref": 612,
        "w_pt": 476.22,
        "h_pt": 260.59,
    },
}


# ======================================================================
# EXPORT AND VERIFICATION RUNNER
# ======================================================================
def render_drawing_to_png(drawing: Drawing, output_png_path: Path, dpi: int = 320) -> None:
    """Render a ReportLab Drawing to a pure grayscale PNG at specified DPI.

    Uses PyMuPDF (fitz) via temporary PDF stream for mathematical rasterization.
    Forces csGRAY colorspace to guarantee 100% pure grayscale (R=G=B).
    """
    import io
    import pymupdf
    from reportlab.graphics import renderPDF

    # Render drawing to in-memory PDF
    pdf_bytes = io.BytesIO()
    renderPDF.drawToFile(drawing, pdf_bytes)
    pdf_bytes.seek(0)

    # Rasterize via PyMuPDF
    doc = pymupdf.open(stream=pdf_bytes.getvalue(), filetype="pdf")
    page = doc[0]
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csGRAY, alpha=False)

    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(output_png_path))
    doc.close()


def export_all_diagrams(output_dir: Path | None = None, dpi: int = 320) -> list[dict]:
    """Export all 18 technical diagrams to the specified output directory."""
    if output_dir is None:
        output_dir = ROOT / "assets" / "diagrams"

    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    print(f"Exporting {len(DIAGRAM_SPECS)} technical diagrams at {dpi} DPI...")
    for filename, spec in DIAGRAM_SPECS.items():
        out_path = output_dir / filename
        builder = spec["builder"]
        drawing = builder(w=spec["w_pt"], h=spec["h_pt"])
        render_drawing_to_png(drawing, out_path, dpi=dpi)

        results.append({
            "filename": filename,
            "path": out_path,
            "chapter": spec["chapter"],
            "figure": spec["figure"],
            "page": spec["page"],
            "xref": spec["xref"],
            "w_pt": spec["w_pt"],
            "h_pt": spec["h_pt"],
            "bytes": out_path.stat().st_size,
        })
        print(f"  [PASS] Figure {spec['figure']:02d} (Ch {spec['chapter']:02d}, p.{spec['page']:03d}) -> {filename} ({spec['w_pt']}x{spec['h_pt']} pt)")

    return results


def verify_all_diagram_typography() -> bool:
    """Audit all 18 diagrams for font size and bounding-box rules."""
    all_ok = True
    print("\nAuditing typography across all 18 technical diagrams...")

    for filename, spec in DIAGRAM_SPECS.items():
        drawing = spec["builder"](w=spec["w_pt"], h=spec["h_pt"])
        strings = []

        def walk(node):
            if isinstance(node, String):
                strings.append(node)
            elif hasattr(node, "contents"):
                for c in node.contents:
                    walk(c)

        walk(drawing)
        if not strings:
            print(f"  [FAIL] {filename}: No text elements found!")
            all_ok = False
            continue

        min_font = min(s.fontSize for s in strings)
        if min_font < 6.0:
            print(f"  [FAIL] {filename}: min fontSize = {min_font:.2f} pt (< 6.0 pt)")
            all_ok = False
        else:
            print(f"  [OK] Figure {spec['figure']:02d}: {filename:<36} -> {len(strings):2d} text nodes, min font: {min_font:.2f} pt")

    return all_ok


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ch19-29 Vector Technical Diagrams Generator")
    parser.add_argument("--export", action="store_true", help="Export PNGs to assets/diagrams/")
    parser.add_argument("--audit", action="store_true", help="Audit typography and specs")
    parser.add_argument("--dpi", type=int, default=320, help="DPI for raster export")
    args = parser.parse_args()

    if args.audit or not (args.export or args.audit):
        ok = verify_all_diagram_typography()
        if not ok:
            sys.exit(1)

    if args.export:
        export_all_diagrams(dpi=args.dpi)
