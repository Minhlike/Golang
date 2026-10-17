"""scripts/ch19_29_vector_diagrams.py.

Vector generator for book-wide technical diagrams in Chapters 19-29,
Chapter 18 (Figure 33), and Appendix B DevOps Library Atlas (Figures 51-58).
Total: 26 diagrams.

Built with ReportLab vector graphics following MASTER PROMPT.txt:
- 100% pure grayscale (R=G=B).
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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from reportlab.graphics.shapes import (
    Drawing,
    Group,
    Line,
    Polygon,
    Rect,
    String,
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
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


def draw_header_banner(
    d: Drawing,
    w: float,
    h: float,
    tag: str,
    title: str,
    subtitle: str,
) -> float:
    """Draw a publication-grade top header banner.

    Returns the y-coordinate of the bottom of the header banner.
    Adapts layout automatically for wide vs narrow canvases.
    """
    if w >= 300.0:
        header_h = 24.0
        header_y = h - header_h - 4.0
        d.add(Rect(4.0, header_y, w - 8.0, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
        tag_w = stringWidth(tag, "BookMono", 6.2) + 12.0
        d.add(Rect(8.0, header_y + 4.5, tag_w, 15.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(String(8.0 + tag_w / 2.0, header_y + 8.5, tag, fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
        d.add(String(8.0 + tag_w + 8.0, header_y + 13.0, title, fontName="BookSansBold", fontSize=7.0, fillColor=COLOR_INK_DARK))
        d.add(String(8.0 + tag_w + 8.0, header_y + 5.5, subtitle, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
        return header_y
    else:
        # Narrow layout (stacked)
        header_h = 36.0
        header_y = h - header_h - 4.0
        d.add(Rect(4.0, header_y, w - 8.0, header_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
        tag_w = stringWidth(tag, "BookMono", 6.0) + 10.0
        d.add(Rect(8.0, header_y + header_h - 13.0, tag_w, 9.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
        d.add(String(8.0 + tag_w / 2.0, header_y + header_h - 10.5, tag, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
        d.add(String(8.0, header_y + 13.0, title, fontName="BookSansBold", fontSize=6.3, fillColor=COLOR_INK_DARK))
        d.add(String(8.0, header_y + 4.5, subtitle, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
        return header_y


def draw_footer_banner(
    d: Drawing,
    w: float,
    text_lines: list[str] | str,
) -> float:
    """Draw a publication-grade bottom invariant footer banner.

    Returns the top y-coordinate of the footer banner.
    Supports single or multi-line text for narrow canvases.
    """
    if isinstance(text_lines, str):
        text_lines = [text_lines]

    if len(text_lines) == 1:
        footer_h = 16.0
        footer_y = 4.0
        d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
        d.add(String(8.0, footer_y + 5.0, text_lines[0], fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        return footer_y + footer_h
    else:
        footer_h = 24.0
        footer_y = 4.0
        d.add(Rect(4.0, footer_y, w - 8.0, footer_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER, strokeWidth=0.6, rx=1.5, ry=1.5))
        d.add(String(8.0, footer_y + 13.0, text_lines[0], fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(8.0, footer_y + 4.5, text_lines[1], fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        return footer_y + footer_h



def wrap_text(text: str, font_name: str, font_size: float, max_width: float) -> list[str]:
    """Wrap text into multiple lines so that each line's stringWidth <= max_width."""
    words = text.split()
    if not words:
        return []
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        if stringWidth(test_line, font_name, font_size) <= max_width or not current_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

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
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 18 // HÌNH 33",
        title="QUY TRÌNH TRUYỀN ĐỊNH DANH VÀ BẰNG CHỨNG QUA CÁC JOB CI/CD",
        subtitle="Phân định ranh giới giữa Artifact Producer, Policy Gate thẩm định và Deploy Environment.",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    col_gap = 12.0
    col_w = (w - 16.0 - 2 * col_gap) / 3.0  # 145.40 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + col_gap
    col3_x = col2_x + col_w + col_gap

    # Job 1: BUILD & TEST
    d.add(Rect(col1_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, body_y + body_h - 13.0, 18.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 15.0, body_y + body_h - 10.5, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 28.0, body_y + body_h - 10.5, "JOB: BUILD & TEST", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col1_x + 8.0, body_y + 242.0, "Runner: runs-on: ubuntu-latest", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, body_y + 232.0, "• Quyền: 0 quyền deploy cloud", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 1A
    b1_h = 100.0
    b1_y = body_y + 120.0
    d.add(Rect(col1_x + 6.0, b1_y, col_w - 12.0, b1_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 10.0, b1_y + 88.0, "ĐÓNG GÓI & KIỂM THỬ", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, b1_y + 76.0, "go test -race ./...", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, b1_y + 64.0, "docker buildx build \\", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 14.0, b1_y + 53.0, "--provenance=mode=max \\", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 14.0, b1_y + 42.0, "--sbom=true -t app:candidate", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, b1_y + 28.0, "• Tạo bằng chứng SLSA", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 10.0, b1_y + 16.0, "• Phân tích call reachability", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 10.0, b1_y + 5.0, "• Sinh SBOM & metadata", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 1B
    b2_h = 86.0
    b2_y = body_y + 18.0
    d.add(Rect(col1_x + 6.0, b2_y, col_w - 12.0, b2_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 10.0, b2_y + 74.0, "OUTPUT ARTIFACTS", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, b2_y + 62.0, "Image Digest (SHA-256):", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, b2_y + 51.0, "sha256:4a8f3b2c1d9e...", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 10.0, b2_y + 38.0, "Tệp attestation.json", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 10.0, b2_y + 26.0, "Tệp scan-results.sarif", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 10.0, b2_y + 10.0, "• Đẩy lên Registry cô lập", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, col1_x + col_w, body_y + 170.0, col2_x, body_y + 170.0, color=COLOR_INK_DARK, width=0.8, head_size=3.2)
    d.add(String((col1_x + col_w + col2_x) / 2.0, body_y + 174.0, "digest &", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String((col1_x + col_w + col2_x) / 2.0, body_y + 164.0, "evidence", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Job 2: POLICY GATE
    d.add(Rect(col2_x, body_y, col_w, body_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 6.0, body_y + body_h - 13.0, 18.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col2_x + 15.0, body_y + body_h - 10.5, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 28.0, body_y + body_h - 10.5, "JOB: POLICY GATE", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 8.0, body_y + 242.0, "Môi trường: Thẩm định độc lập", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, body_y + 232.0, "• 0 quyền ghi hạ tầng production", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 2A
    d.add(Rect(col2_x + 6.0, b1_y, col_w - 12.0, b1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 10.0, b1_y + 88.0, "TIÊU CHÍ THẨM ĐỊNH", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b1_y + 76.0, "1. Xác minh chữ ký Cosign:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 14.0, b1_y + 65.0, "cosign verify --key ...", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 10.0, b1_y + 52.0, "2. SLSA Level 3 Provenance:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 14.0, b1_y + 41.0, "Khớp repository, commit SHA", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 10.0, b1_y + 28.0, "3. Quét lỗ hổng reachability:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 14.0, b1_y + 17.0, "0 CVE nghiêm trọng gọi tới", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 10.0, b1_y + 5.0, "4. SBOM khớp dependency tree", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 2B
    d.add(Rect(col2_x + 6.0, b2_y, col_w - 12.0, b2_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 10.0, b2_y + 74.0, "QUYẾT ĐỊNH CỔNG KIỂM SOÁT", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2_y + 60.0, "[FAIL-CLOSED GATE]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2_y + 48.0, "• Thiếu 1 tiêu chí: DỪNG NGAY", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2_y + 36.0, "• Đạt 100%: Ký duyệt promotion", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 10.0, b2_y + 22.0, "Promotion Ticket phát hành:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 10.0, b2_y + 10.0, "Gắn chặt với Digest đã thẩm định", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, col2_x + col_w, body_y + 170.0, col3_x, body_y + 170.0, color=COLOR_INK_DARK, width=0.8, head_size=3.2)
    d.add(String((col2_x + col_w + col3_x) / 2.0, body_y + 174.0, "approved", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String((col2_x + col_w + col3_x) / 2.0, body_y + 164.0, "decision", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Job 3: DEPLOY
    d.add(Rect(col3_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col3_x + 6.0, body_y + body_h - 13.0, 18.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col3_x + 15.0, body_y + body_h - 10.5, "03", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col3_x + 28.0, body_y + body_h - 10.5, "JOB: DEPLOY PRODUCTION", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col3_x + 8.0, body_y + 242.0, "Xác thực OIDC (Keyless Auth):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, body_y + 232.0, "• Token ngắn hạn gắn IAM Role", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 3A
    d.add(Rect(col3_x + 6.0, b1_y, col_w - 12.0, b1_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 10.0, b1_y + 88.0, "ĐIỀU KIỆN TIÊN QUYẾT", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10.0, b1_y + 76.0, "1. Kiểm tra Quyết định phê duyệt:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 14.0, b1_y + 65.0, "Ticket từ Job 02 còn hiệu lực", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 10.0, b1_y + 52.0, "2. Nhận dạng danh tính OIDC:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 14.0, b1_y + 41.0, "audience: sts.amazonaws.com", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 10.0, b1_y + 28.0, "3. Khóa định danh bất biến:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 14.0, b1_y + 17.0, "Triển khai bằng Digest SHA-256", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10.0, b1_y + 5.0, "• Tuyệt đối không deploy bằng tag", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 3B
    d.add(Rect(col3_x + 6.0, b2_y, col_w - 12.0, b2_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 10.0, b2_y + 74.0, "CẬP NHẬT TRẠNG THÁI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10.0, b2_y + 62.0, "GitOps / Kube-API Server:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10.0, b2_y + 51.0, "image: app@sha256:4a8f3b...", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 10.0, b2_y + 38.0, "RollingUpdate Deployment", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 10.0, b2_y + 26.0, "Health Probe: /livez, /readyz", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 10.0, b2_y + 10.0, "• Tự rollback nếu probe lỗi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_footer_banner(d, w, "• Invariant: Quyền OIDC và môi trường triển khai chỉ cấp kênh kết nối tạm thời; không tự động thay thế cho việc thẩm định bằng chứng tại policy gate.")
    return d


# ======================================================================
# 2. Chapter 19 — Figure 34: Type Information Boundaries (413.18 x 362.83 pt)
# ======================================================================
def build_type_information_boundaries_drawing(w: float = 413.18, h: float = 362.83) -> Drawing:
    """Figure 34: Lựa chọn tầng trừu tượng phù hợp với câu hỏi kỹ thuật cần giải quyết.

    Ba ranh giới độc lập:
    1. Generic: Ràng buộc kiểu thời điểm biên dịch, bảo tồn kiểu cụ thể qua thuật toán.
    2. Interface: Ranh giới khế ước hành vi khi concrete type thay đổi lúc runtime.
    3. Reflection: Khảo sát shape và metadata khi dữ liệu chỉ biết lúc runtime.
    Exact dimensions: 413.18 x 362.83 pt (Page 341, xref 393).
    """
    register_fonts()
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 19 // HÌNH 34",
        title="BA RANH GIỚI BẢO TOÀN VÀ XỬ LÝ THÔNG TIN KIỂU TRONG GO",
        subtitle="Lựa chọn tầng trừu tượng theo câu hỏi kỹ thuật; đây là 3 ranh giới khác nhau, không phải thang tăng dần.",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    col_gap = 8.0
    col_w = (w - 16.0 - 2 * col_gap) / 3.0  # 127.06 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + col_gap
    col3_x = col2_x + col_w + col_gap

    # Column 1: GENERIC
    d.add(Rect(col1_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, body_y + body_h - 13.0, 18.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 15.0, body_y + body_h - 10.5, "01", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 28.0, body_y + body_h - 10.5, "GENERIC (COMPILE-TIME)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    d.add(String(col1_x + 8.0, body_y + 272.0, "Câu hỏi kỹ thuật:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, body_y + 261.0, "Cùng một thuật toán trên", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, body_y + 250.0, "nhiều kiểu; giữ kiểu tĩnh", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, body_y + 239.0, "để compiler bắt lỗi sớm?", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Box 1A
    b1_h = 112.0
    b1_y = body_y + 120.0
    d.add(Rect(col1_x + 5.0, b1_y, col_w - 10.0, b1_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, b1_y + 99.0, "CƠ CHẾ & RÀNG BUỘC KIỂU", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1_y + 87.0, "Unique[T comparable]([]T) []T", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1_y + 75.0, "Max[T constraints.Ordered]", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1_y + 63.0, "• Type unification & inference", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1_y + 51.0, "• Bảo tồn exact named type:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 12.0, b1_y + 40.0, "Max(ms1, ms2) -> Millis", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1_y + 28.0, "• Compiler từ chối gán nhầm", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b1_y + 16.0, "• GCShape stenciling chia sẻ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b1_y + 5.0, "  mã con trỏ qua dictionary", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 1B
    b2_h = 104.0
    b2_y = body_y + 10.0
    d.add(Rect(col1_x + 5.0, b2_y, col_w - 10.0, b2_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col1_x + 8.0, b2_y + 91.0, "ĐÁNH ĐỔI & GIỚI HẠN", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b2_y + 79.0, "[ĐẶC TÍNH RUNTIME]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b2_y + 68.0, "• Type safety tại compile-time", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b2_y + 57.0, "• Alloc tùy cách dùng giá trị", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b2_y + 44.0, "[GIỚI HẠN THIẾT KẾ]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, b2_y + 32.0, "• Không đa hình lúc chạy", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b2_y + 21.0, "• Không hoán đổi plugin động", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, b2_y + 10.0, "• Dictionary passing có chi phí", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Column 2: INTERFACE
    d.add(Rect(col2_x, body_y, col_w, body_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 6.0, body_y + body_h - 13.0, 18.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col2_x + 15.0, body_y + body_h - 10.5, "02", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 28.0, body_y + body_h - 10.5, "INTERFACE (BEHAVIOR)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 8.0, body_y + 272.0, "Câu hỏi kỹ thuật:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, body_y + 261.0, "Hành vi đồng nhất khi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, body_y + 250.0, "concrete type thay đổi hoặc", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, body_y + 239.0, "hoán đổi cài đặt lúc chạy?", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Box 2A
    d.add(Rect(col2_x + 5.0, b1_y, col_w - 10.0, b1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, b1_y + 99.0, "CẤU TRÚC ITAB & DATA", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1_y + 87.0, "type SummaryReader interface {", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 12.0, b1_y + 75.0, "Summary() string", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1_y + 63.0, "}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1_y + 51.0, "• Fat pointer: (itab, data)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b1_y + 40.0, "• itab chứa type descriptor", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b1_y + 28.0, "  và con trỏ hàm (func ptr)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b1_y + 16.0, "• Dynamic dispatch gián tiếp", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b1_y + 5.0, "• Boxing value type vào heap", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 2B
    d.add(Rect(col2_x + 5.0, b2_y, col_w - 10.0, b2_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col2_x + 8.0, b2_y + 91.0, "ĐÁNH ĐỔI & GIỚI HẠN", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2_y + 79.0, "[ƯU ĐIỂM THIẾT KẾ]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2_y + 68.0, "• Đa hình runtime linh hoạt", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2_y + 57.0, "• Decoupling giữa các package", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2_y + 44.0, "[CHI PHÍ RUNTIME]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, b2_y + 32.0, "• Lời gọi qua con trỏ hàm", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2_y + 21.0, "• Escape analysis đẩy ra heap", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, b2_y + 10.0, "• Type assertion có thể panic", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Column 3: REFLECTION
    d.add(Rect(col3_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col3_x + 6.0, body_y + body_h - 13.0, 18.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col3_x + 15.0, body_y + body_h - 10.5, "03", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col3_x + 28.0, body_y + body_h - 10.5, "REFLECTION (METADATA)", fontName="BookSansBold", fontSize=6.1, fillColor=COLOR_INK_DARK))

    d.add(String(col3_x + 8.0, body_y + 272.0, "Câu hỏi kỹ thuật:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, body_y + 261.0, "Dữ liệu chỉ biết lúc chạy,", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, body_y + 250.0, "cần duyệt trường struct,", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, body_y + 239.0, "đọc struct tags động?", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Box 3A
    d.add(Rect(col3_x + 5.0, b1_y, col_w - 10.0, b1_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, b1_y + 99.0, "KHẢO SÁT TYPE & VALUE", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1_y + 87.0, "t := reflect.TypeOf(v)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1_y + 75.0, "val := reflect.ValueOf(v)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1_y + 63.0, "field := t.Field(i).Tag", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1_y + 51.0, "• Kiểm tra Kind() runtime", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1_y + 40.0, "• Duyệt slice, map, pointer", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1_y + 28.0, "• CanSet() kiểm tra gán", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b1_y + 16.0, "• Phù hợp: JSON serializer,", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b1_y + 5.0, "  ORM, dependency injection", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 3B
    d.add(Rect(col3_x + 5.0, b2_y, col_w - 10.0, b2_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(col3_x + 8.0, b2_y + 91.0, "ĐÁNH ĐỔI & GIỚI HẠN", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b2_y + 79.0, "[ĐÁNH ĐỔI NẶNG NỀ]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b2_y + 68.0, "• Mất kiểm tra tĩnh compiler", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b2_y + 57.0, "• Lỗi sai kiểu chuyển sang run", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b2_y + 44.0, "[HIỆU NĂNG RUNTIME]", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col3_x + 8.0, b2_y + 32.0, "• Chậm hơn từ 10x đến 100x", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b2_y + 21.0, "• Cấp phát heap liên tục", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col3_x + 8.0, b2_y + 10.0, "• Chỉ dùng khi không thể tránh", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_footer_banner(d, w, "• Invariant: Generic bảo tồn kiểu tĩnh; Interface trừu tượng hóa hành vi; Reflection phân tích metadata runtime. Chi phí phụ thuộc vào cách dùng cụ thể.")
    return d


# ======================================================================
# 3. Chapter 21 — Figure 35: Edge vs Level Triggered (476.22 x 162.43 pt)
# ======================================================================
def build_edge_level_comparison_drawing(w: float = 476.22, h: float = 162.43) -> Drawing:
    """Figure 35: So sánh cơ chế kích hoạt theo sườn và theo mức.

    Khi một thông điệp bị mất, controller dựa vào trạng thái (level-triggered)
    vẫn có thể tự phục hồi ở lần hòa giải tiếp theo.
    Exact dimensions: 476.22 x 162.43 pt (Page 371, xref 424).
    """
    register_fonts()
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 21 // HÌNH 35",
        title="SO SÁNH CƠ CHẾ KÍCH HOẠT: EDGE-TRIGGERED VS LEVEL-TRIGGERED",
        subtitle="Hệ phân tán chuộng level-triggered vì khả năng tự chữa lành khi thông điệp mạng bị rơi rụng.",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    col_w = (w - 24.0) / 2.0  # 226.11 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + 8.0

    # Left: Edge-Triggered
    d.add(Rect(col1_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, body_y + body_h - 13.0, 84.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 48.0, body_y + body_h - 10.5, "EDGE-TRIGGERED (SỰ KIỆN)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(String(col1_x + 8.0, body_y + 78.0, "Nguyên lý: Chỉ phản ứng khi có biến thiên (sườn xung)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, body_y + 66.0, "• Message: \"Pod X được tạo\" hoặc \"Scale up +1\"", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, body_y + 52.0, "RỦI RO KHI RƠI THÔNG ĐIỆP MẠNG:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, body_y + 40.0, "• Nếu gói tin sự kiện bị mất giữa đường:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 14.0, body_y + 28.0, "Controller không nhận được xung biến thiên", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col1_x + 8.0, body_y + 14.0, "• Hậu quả: Hệ thống lệch trạng thái vĩnh viễn", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, body_y + 4.0, "• Đòi hỏi giao thức tin cậy nặng nề (ACK, Retry, Tx)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Right: Level-Triggered
    d.add(Rect(col2_x, body_y, col_w, body_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 6.0, body_y + body_h - 13.0, 92.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col2_x + 52.0, body_y + body_h - 10.5, "LEVEL-TRIGGERED (MỨC TRẠNG THÁI)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(String(col2_x + 8.0, body_y + 78.0, "Nguyên lý: Liên tục điều hòa Desired về Actual", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, body_y + 66.0, "• Khảo sát trạng thái hiện hữu: current == desired?", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, body_y + 52.0, "KHẢ NĂNG TỰ PHỤC HỒI (SELF-HEALING):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, body_y + 40.0, "• Dù mất 1 hay 10 thông báo sự kiện trước đó:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 14.0, body_y + 28.0, "Vòng lặp Reconcile tiếp theo đọc trạng thái thực", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, body_y + 14.0, "• Tự động đưa cụm về trạng thái mong muốn", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, body_y + 4.0, "• Nền tảng triết lý kiến trúc của Kubernetes", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_footer_banner(d, w, "• Invariant: Khi thông điệp bị rơi rụng, Level-Triggered cho phép controller tự phục hồi dựa trên việc khảo sát trạng thái hiện hữu ở chu kỳ tiếp theo.")
    return d


# ======================================================================
# 4. Chapter 22 — Figure 36: client-go Controller Flow (476.22 x 301.61 pt)
# ======================================================================
def build_client_go_controller_flow_drawing(w: float = 476.22, h: float = 301.61) -> Drawing:
    """Figure 36: Luồng sự kiện của bộ điều khiển client-go.

    Thứ tự chuẩn xác: Reflector -> DeltaFIFO -> cập nhật Indexer Cache ->
    Event Handler -> Workqueue -> Worker Reconcile loop.
    Worker đọc observation từ cache cục bộ (Indexer).
    Exact dimensions: 476.22 x 301.61 pt (Page 385, xref 439).
    """
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 22 // HÌNH 36",
        title="KIẾN TRÚC LUỒNG DỮ LIỆU BỘ ĐIỀU KHIỂN CLIENT-GO",
        subtitle="Reflector -> DeltaFIFO -> Cập nhật Indexer Cache -> Handler -> Workqueue -> Worker.",
    )

    draw_footer_banner(d, w, "• Invariant: Reflector -> DeltaFIFO -> cập nhật Indexer Cache -> Handler phát key vào Workqueue; Worker đọc observation từ cache cục bộ.")

    # 3-Row Layout:
    # Row 1: API Server (left) -> Reflector (mid) -> DeltaFIFO (right)
    # Row 2: Indexer Cache (left) -> Event Handler (right) with 52 pt middle gap
    # Row 3: Worker Pool (left) <- Workqueue (right) with 52 pt middle gap
    row1_h = 56.0
    row1_y = 212.0

    r1_w = 120.0
    r2_w = 126.0
    r3_w = 186.0
    x1 = 8.0
    x2 = 142.0
    x3 = 282.0

    # Box 1: API Server
    d.add(Rect(x1, row1_y, r1_w, row1_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(x1 + r1_w / 2.0, row1_y + row1_h - 11.0, "KUBE-API SERVER", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(x1 + r1_w / 2.0, row1_y + row1_h - 20.0, "Cluster Store (etcd)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
    d.add(String(x1 + 6.0, row1_y + 24.0, "• Nguồn chân lý của cụm", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(x1 + 6.0, row1_y + 13.0, "• Cung cấp List & Watch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(x1 + 6.0, row1_y + 3.0, "• ResourceVersion mốc", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, x1 + r1_w, row1_y + row1_h / 2.0, x2, row1_y + row1_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Box 2: Reflector
    d.add(Rect(x2, row1_y, r2_w, row1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(x2 + r2_w / 2.0, row1_y + row1_h - 11.0, "REFLECTOR", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(x2 + r2_w / 2.0, row1_y + row1_h - 20.0, "ListWatch Controller Loop", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
    d.add(String(x2 + 6.0, row1_y + 24.0, "• List nạp snapshot RV", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(x2 + 6.0, row1_y + 13.0, "• Watch nhận delta sự kiện", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(x2 + 6.0, row1_y + 3.0, "• Re-list khi 410 Gone", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, x2 + r2_w, row1_y + row1_h / 2.0, x3, row1_y + row1_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Box 3: DeltaFIFO
    d.add(Rect(x3, row1_y, r3_w, row1_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(x3 + r3_w / 2.0, row1_y + row1_h - 11.0, "DeltaFIFO", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(x3 + r3_w / 2.0, row1_y + row1_h - 20.0, "Deduplicating FIFO Queue", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
    d.add(String(x3 + 6.0, row1_y + 24.0, "• Hợp nhất delta theo khóa đối tượng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(x3 + 6.0, row1_y + 13.0, "• Lưu delta: Added, Updated, Deleted", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(x3 + 6.0, row1_y + 3.0, "• Pop() cập nhật cache trước khi dispatch", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Stepped arrow: DeltaFIFO (Box 3) -> Indexer Cache (Row 2 Left)
    # Routes through the 24 pt gap (y=188 to 212) with a dedicated horizontal segment at y=200
    line_pop_v1 = Line(320.0, 212.0, 320.0, 200.0)
    line_pop_v1.strokeColor = COLOR_INK_DARK
    line_pop_v1.strokeWidth = 0.8
    d.add(line_pop_v1)
    line_pop_h = Line(320.0, 200.0, 110.0, 200.0)
    line_pop_h.strokeColor = COLOR_INK_DARK
    line_pop_h.strokeWidth = 0.8
    d.add(line_pop_h)
    draw_arrow(d, 110.0, 200.0, 110.0, 188.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    # Centered label above horizontal segment: y=203.5 (4.0 pt clearance to Row 1 bottom, 12.0 pt clearance to Row 2 top)
    d.add(String(215.0, 203.5, "Pop() cập nhật cache", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Row 2: Informer Components (Indexer Cache [left] -> Event Handler [right])
    row2_h = 66.0
    row2_y = 122.0
    col_w = 204.0
    m1_x = 8.0
    m2_x = 264.0  # 52 pt middle gap from 212 to 264

    # Mid 1: Indexer Cache (Local Store)
    d.add(Rect(m1_x, row2_y, col_w, row2_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(m1_x + 6.0, row2_y + row2_h - 13.0, 85.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(m1_x + 48.5, row2_y + row2_h - 10.5, "1. INDEXER CACHE", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(m1_x + 98.0, row2_y + row2_h - 10.5, "In-Memory Store", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    d.add(String(m1_x + 6.0, row2_y + 40.0, "• Cập nhật đồng bộ TRƯỚC callback", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m1_x + 6.0, row2_y + 29.0, "• Lưu trữ snapshot đối tượng của cụm", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m1_x + 6.0, row2_y + 18.0, "• Tra cứu nhanh theo Key (Namespace/Name)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m1_x + 6.0, row2_y + 7.0, "• Giải phóng etcd khỏi các lệnh đọc lặp", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow from Mid 1 (Indexer) to Mid 2 (Handler) across the 52 pt gap
    draw_arrow(d, m1_x + col_w, row2_y + row2_h / 2.0, m2_x, row2_y + row2_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    # Label "phát event" centered in 52 pt gap: 9.5 pt clearance to both box borders
    d.add(String(238.0, row2_y + row2_h / 2.0 + 3.5, "phát event", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Mid 2: ResourceEventHandler
    d.add(Rect(m2_x, row2_y, col_w, row2_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(m2_x + 6.0, row2_y + row2_h - 13.0, 96.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(m2_x + 54.0, row2_y + row2_h - 10.5, "2. EVENT HANDLER", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(m2_x + 106.0, row2_y + row2_h - 10.5, "Callbacks Dispatcher", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    d.add(String(m2_x + 6.0, row2_y + 40.0, "• Nhận callback: OnAdd, OnUpdate, OnDelete", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m2_x + 6.0, row2_y + 29.0, "• Trích xuất khóa định danh Namespace/Name", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m2_x + 6.0, row2_y + 18.0, "• KHÔNG đưa toàn bộ payload vào queue", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m2_x + 6.0, row2_y + 7.0, "• Chỉ enqueue khóa (Level-triggered)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Gap between Row 2 and Row 3: 26 pt (y=96.0 to 122.0)
    # Right: Arrow down from Handler to Workqueue
    draw_arrow(d, 366.0, 122.0, 366.0, 96.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String(372.0, 106.0, "queue.Add(key)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Left: Dashed arrow straight up from Worker Pool to Indexer Cache (Read Observation)
    draw_arrow(d, 48.0, 96.0, 48.0, 122.0, color=COLOR_INK_MID, width=0.8, head_size=3.0, dashed=True)
    d.add(String(54.0, 106.0, "đọc observation từ cache", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Row 3: Worker Pool [left] <--- Workqueue [right]
    row3_h = 72.0
    row3_y = 24.0

    # Bot 1 (Left): Worker Pool
    d.add(Rect(m1_x, row3_y, col_w, row3_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(m1_x + 6.0, row3_y + row3_h - 12.0, "4. WORKER POOL & RECONCILE LOOP", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(m1_x + 6.0, row3_y + 46.0, "• Goroutine worker lấy khóa từ Workqueue", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m1_x + 6.0, row3_y + 35.0, "• Đọc observation từ Indexer Cache (mũi tên đứt)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m1_x + 6.0, row3_y + 24.0, "• Thực thi logic điều hòa: Desired vs Current", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m1_x + 6.0, row3_y + 13.0, "• Áp dụng thay đổi vào cluster nếu có sai lệch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m1_x + 6.0, row3_y + 3.0, "• Báo Done(key) và Forget(key) khi thành công", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Bot 2 (Right): WorkQueue
    d.add(Rect(m2_x, row3_y, col_w, row3_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(m2_x + 6.0, row3_y + row3_h - 12.0, "3. WORKQUEUE (RATELIMITINGQUEUE)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(m2_x + 6.0, row3_y + 46.0, "• Hàng đợi công việc chứa khóa Namespace/Name", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m2_x + 6.0, row3_y + 35.0, "• Deduplication: Tự động gom sự kiện trùng lặp", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m2_x + 6.0, row3_y + 24.0, "• Rate Limiting: Giới hạn tần suất retry khi lỗi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m2_x + 6.0, row3_y + 13.0, "• Processing set: Ngăn xử lý song song cùng khóa", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(m2_x + 6.0, row3_y + 3.0, "• Done(key): Đánh dấu hoàn tất một chu kỳ", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow from Bot 2 (Workqueue) to Bot 1 (Worker Pool) across the 52 pt gap
    draw_arrow(d, m2_x, row3_y + row3_h / 2.0, m1_x + col_w, row3_y + row3_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    # Label "Get()" centered in 52 pt gap: 17.0 pt clearance to both box borders
    d.add(String(238.0, row3_y + row3_h / 2.0 + 3.5, "Get()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    return d

# ======================================================================
# 5. Chapter 22 — Figure 37: client-go List/Watch (476.22 x 275.15 pt)
# ======================================================================
def build_client_go_list_watch_drawing(w: float = 476.22, h: float = 275.15) -> Drawing:
    """Figure 37: Trình tự Reflector List rồi Watch và xử lý HTTP 410 Gone.

    Sequence & Timeline:
    1. List snapshot -> resourceVersion: "1040"
    2. Watch stream: events 1041, 1042
    3. Network break / disconnect at 1042
    4. Reconnect watch?resourceVersion=1042
    5. HTTP 410 Gone (Too old resource version do etcd compact)
    6. Re-list recovery -> fresh snapshot at resourceVersion: "2050" -> new Watch stream.
    Exact dimensions: 476.22 x 275.15 pt (Page 386, xref 441).
    """
    register_fonts()
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 22 // HÌNH 37",
        title="TRÌNH TỰ REFLECTOR LIST/WATCH VÀ PHỤC HỒI KHI GẶP HTTP 410 GONE",
        subtitle="List tạo mốc snapshot ban đầu; Watch tiếp nhận thay đổi; khi lịch sử hết hạn (410 Gone), Reflector bắt buộc List lại từ đầu.",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    actor1_x = 90.0   # Reflector
    actor2_x = 386.0  # Kube-API Server

    act_box_w = 130.0
    act_box_h = 20.0
    act_box_y = header_y - act_box_h - 6.0

    d.add(Rect(actor1_x - act_box_w / 2.0, act_box_y, act_box_w, act_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor1_x, act_box_y + 11.5, "REFLECTOR (CLIENT-GO)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor1_x, act_box_y + 4.5, "Local Store / DeltaFIFO", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    d.add(Rect(actor2_x - act_box_w / 2.0, act_box_y, act_box_w, act_box_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor2_x, act_box_y + 11.5, "KUBE-API SERVER (ETCD)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, act_box_y + 4.5, "Authoritative Cluster Store", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    lifeline_bot = body_y + 6.0
    lifeline_top = act_box_y
    for ax in (actor1_x, actor2_x):
        line = Line(ax, lifeline_top, ax, lifeline_bot)
        line.strokeColor = COLOR_BORDER
        line.strokeWidth = 0.8
        line.strokeDashArray = [3, 2]
        d.add(line)

    steps = [
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
            d.add(Rect(actor1_x - 30.0, sy - 4.0, (actor2_x - actor1_x) + 60.0, 16.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
            d.add(String((actor1_x + actor2_x) / 2.0, sy + 4.5, title, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
            d.add(String((actor1_x + actor2_x) / 2.0, sy - 2.0, desc, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
            continue

        if sdir == "R->S":
            draw_arrow(d, actor1_x, sy, actor2_x, sy, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
            d.add(String(actor1_x + 10.0, sy + 3.0, title, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
            d.add(String(actor1_x + 10.0, sy - 7.0, desc, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
        elif sdir == "S->R":
            draw_arrow(d, actor2_x, sy, actor1_x, sy, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
            d.add(String(actor1_x + 10.0, sy + 3.0, title, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
            d.add(String(actor1_x + 10.0, sy - 7.0, desc, fontName="BookSansBold" if is_err else "BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK if is_err else COLOR_INK_MID))

        tag_w = stringWidth(tag, "BookMono", 5.6) + 6.0
        d.add(Rect(actor2_x + 8.0, sy - 4.0, tag_w, 9.0, fillColor=COLOR_TAG_ACTIVE if is_err else COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.4, rx=1.0, ry=1.0))
        d.add(String(actor2_x + 8.0 + tag_w / 2.0, sy - 1.5, tag, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    draw_footer_banner(d, w, "• Invariant: List tạo mốc snapshot ban đầu; Watch stream thay đổi tiếp theo; khi gặp HTTP 410 Gone, Reflector bắt buộc List lại từ đầu để lập snapshot mới.")
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
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 23 // HÌNH 38",
        title="TRI THỨC VẬN HÀNH VÀ CÁC THÀNH PHẦN KIẾN TRÚC TRONG OPERATOR",
        subtitle="Operator biểu đạt tri thức vận hành qua API, vòng lặp điều hòa và tích hợp ngoài (vai trò thiết kế song hành).",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    left_w = 296.0
    right_x = 310.0
    right_w = w - right_x - 8.0

    # 1. Top Card: Tri thức vận hành
    top_card_h = 52.0
    top_card_y = body_y + body_h - top_card_h
    d.add(Rect(8.0, top_card_y, left_w, top_card_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(14.0, top_card_y + top_card_h - 13.0, 110.0, 10.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(69.0, top_card_y + top_card_h - 10.0, "TRI THỨC VẬN HÀNH", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(14.0, top_card_y + 26.0, "Quy tắc vận hành ứng dụng: backup dữ liệu, failover cụm, điều phối", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(14.0, top_card_y + 16.0, "nâng cấp schema và tự phục hồi do kỹ sư tích lũy qua kinh nghiệm.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(14.0, top_card_y + 6.0, "• Đóng gói tư duy con người thành thuật toán phần mềm tự hành", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, 8.0 + left_w / 2.0, top_card_y, 8.0 + left_w / 2.0, top_card_y - 14.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # 2. Operator Core
    op_card_h = 32.0
    op_card_y = top_card_y - 14.0 - op_card_h
    d.add(Rect(8.0, op_card_y, left_w, op_card_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(8.0 + left_w / 2.0, op_card_y + 19.0, "OPERATOR (HIỆN THỰC BẰNG GO)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(8.0 + left_w / 2.0, op_card_y + 7.5, "Custom Controller runtime quản lý vòng đời tài nguyên trên Kubernetes", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 3 Roles below
    role_w = (left_w - 16.0) / 3.0
    r1_x = 8.0
    r2_x = r1_x + role_w + 8.0
    r3_x = r2_x + role_w + 8.0
    role_y = body_y
    role_h = op_card_y - role_y - 14.0

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

    draw_footer_banner(d, w, "• Invariant: Các thành phần là vai trò thiết kế song hành, không phải 3 bước chạy tuần tự. CRD là nguồn chân lý duy nhất cho ý định khai báo.")
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
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 23 // HÌNH 39",
        title="RANH GIỚI VÀ PHÂN ĐỊNH TRÁCH NHIỆM: MANAGER, RECONCILER VÀ CLIENT",
        subtitle="Manager tổ chức các component; controller gọi Reconciler; Client tách đường đọc cache và ghi HTTP tới API Server.",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    box_w = (w - 24.0) / 2.0  # 224.86 pt each
    col1_x = 8.0
    col2_x = col1_x + box_w + 8.0

    # Top-Left: MANAGER
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

    # Top-Right: SPLIT CLIENT & IN-MEMORY CACHE
    d.add(Rect(col2_x, top_box_y, box_w, top_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 6.0, top_box_y + top_box_h - 13.0, 68.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col2_x + 40.0, top_box_y + top_box_h - 10.5, "CLIENT.CLIENT", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 80.0, top_box_y + top_box_h - 10.5, "SPLIT CLIENT & IN-MEMORY CACHE", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 8.0, top_box_y + 60.0, "Tách biệt đường đọc (Cache) và đường ghi (HTTP):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, top_box_y + 48.0, "• ĐƯỜNG ĐỌC: Đọc từ In-Memory Cache (Informer Store)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 16.0, top_box_y + 36.0, "Zero network roundtrip tới etcd cho kiểu đã watch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, top_box_y + 24.0, "• ĐƯỜNG GHI: Trực tiếp qua HTTP REST tới API Server", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 16.0, top_box_y + 12.0, "Create, Update, Patch, Delete bảo đảm ghi đồng bộ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Mid-Left: CONTROLLER
    mid_box_h = 78.0
    mid_box_y = top_box_y - 14.0 - mid_box_h
    d.add(Rect(col1_x, mid_box_y, box_w, mid_box_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(col1_x + 8.0, mid_box_y + mid_box_h - 12.0, "CONTROLLER (QUEUE & WORKER POOL)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, mid_box_y + 50.0, "• Watch sự kiện từ Informer Cache qua EventHandler", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, mid_box_y + 38.0, "• Coalesce các sự kiện trùng lặp của cùng một khóa", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, mid_box_y + 26.0, "• RateLimitingQueue giữ reconcile.Request{NamespacedName}", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, mid_box_y + 12.0, "• Worker gọi Reconcile(ctx, req) theo cơ chế tuần tự hóa", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Mid-Right: KUBE-API SERVER
    d.add(Rect(col2_x, mid_box_y, box_w, mid_box_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(col2_x + 8.0, mid_box_y + mid_box_h - 12.0, "KUBE-API SERVER (ETCD CLUSTER STORE)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, mid_box_y + 50.0, "• Authoritative State Store của toàn bộ cụm Kubernetes", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, mid_box_y + 38.0, "• Phát Watch Stream nuôi Informer Cache (đường nét đứt)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, mid_box_y + 26.0, "• Tiếp nhận HTTP mutations từ Client ghi vào etcd", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, mid_box_y + 12.0, "• Xét điều kiện deletionTimestamp và finalizers khi xóa", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    draw_arrow(d, col1_x + box_w / 2.0, top_box_y, col1_x + box_w / 2.0, mid_box_y + mid_box_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, col2_x + box_w * 0.3, top_box_y, col2_x + box_w * 0.3, mid_box_y + mid_box_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, col2_x + box_w * 0.7, mid_box_y + mid_box_h, col2_x + box_w * 0.7, top_box_y, color=COLOR_INK_MID, width=0.8, head_size=3.0, dashed=True)

    # Bottom: RECONCILER
    rec_box_y = body_y
    rec_box_h = mid_box_y - rec_box_y - 12.0
    d.add(Rect(8.0, rec_box_y, w - 16.0, rec_box_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(14.0, rec_box_y + rec_box_h - 12.0, "RECONCILER CORE: Reconcile(ctx, req) -> (ctrl.Result, error)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))

    rec_step_w = (w - 32.0 - 24.0) / 4.0
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

    draw_arrow(d, sx1 + rec_step_w, s_y + s_h / 2.0, sx2, s_y + s_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, sx2 + rec_step_w, s_y + s_h / 2.0, sx3, s_y + s_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, sx3 + rec_step_w, s_y + s_h / 2.0, sx4, s_y + s_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    draw_arrow(d, col1_x + box_w / 2.0, mid_box_y, col1_x + box_w / 2.0, rec_box_y + rec_box_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    draw_footer_banner(d, w, "• Invariant: Reconciler chỉ nhận NamespacedName và đọc từ Cache; mọi thay đổi trạng thái bắt buộc ghi qua HTTP REST tới API Server.")
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
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 23 // HÌNH 40",
        title="VÒNG ĐỜI VÀ XỬ LÝ FINALIZER TRONG CONTROLLER",
        subtitle="Finalizer bảo vệ tài nguyên ngoài; cleanup thất bại giữ finalizer để thử lại.",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    center_w = w - 24.0
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

    # Decision
    dec_h = 32.0
    dec_y = s3_y - 12.0 - dec_h
    d.add(Rect(cx, dec_y, center_w, dec_h, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(w / 2.0, dec_y + 19.0, "KẾT QUẢ CLEANUP NGOẠI VI: THÀNH CÔNG HAY THẤT BẠI?", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(w / 2.0, dec_y + 8.0, "Kiểm tra err == nil (Thành công) hoặc err != nil (Thất bại)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    branch_w = (center_w - 12.0) / 2.0
    bx1 = cx
    bx2 = cx + branch_w + 12.0
    b_y = body_y
    b_h = dec_y - b_y - 12.0

    draw_arrow(d, w / 2.0 - 40.0, dec_y, bx1 + branch_w / 2.0, b_y + b_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
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

    draw_footer_banner(d, w, "• Invariant: Cleanup thất bại giữ finalizer để thử lại; gỡ finalizer chỉ cho phép xóa khi không còn finalizer nào khác trên object.")
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
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 24 // HÌNH 41",
        title="PHÂN GIẢI CREDENTIALS AWS SDK V2",
        subtitle="Bản đồ nguồn & vai trò của CredentialsCache.",
    )

    body_bot = draw_footer_banner(
        d, w,
        [
            "• Invariant: Cấu hình quyết định provider được chọn;",
            "  CredentialsCache chỉ gọi Retrieve() khi token hết hạn.",
        ]
    )

    body_y = body_bot + 4.0
    body_h = header_y - body_y - 4.0

    cw = w - 16.0  # 248.41 pt
    cx = 8.0

    # 1. Initiator: LoadDefaultConfig
    c1_h = 42.0
    c1_y = body_y + body_h - c1_h
    d.add(Rect(cx, c1_y, cw, c1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(cx + 8.0, c1_y + c1_h - 12.0, "config.LoadDefaultConfig(ctx, opts...)", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c1_y + 18.0, "Chọn provider phù hợp theo biến môi trường và thiết lập", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c1_y + 8.0, "Khởi tạo chuỗi phân giải credentials mặc định của SDK v2", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, w / 2.0, c1_y, w / 2.0, c1_y - 8.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # 2. Providers Sources Box
    c2_h = 104.0
    c2_y = c1_y - 8.0 - c2_h
    d.add(Rect(cx, c2_y, cw, c2_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(cx + 6.0, c2_y + c2_h - 12.0, 110.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(cx + 61.0, c2_y + c2_h - 9.5, "NGUỒN CẤU HÌNH & WORKLOAD", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    providers = [
        ("1. Môi trường:", "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"),
        ("2. Shared Config:", "~/.aws/credentials, ~/.aws/config, AWS_PROFILE"),
        ("3. Web Identity:", "AWS_WEB_IDENTITY_TOKEN_FILE (EKS IRSA)"),
        ("4. Container/EC2:", "AWS_CONTAINER_CREDENTIALS_URI, EC2 IMDSv2"),
    ]

    py = c2_y + c2_h - 24.0
    for ptitle, pdesc in providers:
        d.add(String(cx + 8.0, py, ptitle, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(cx + 8.0, py - 9.0, pdesc, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
        py -= 20.0

    draw_arrow(d, w / 2.0, c2_y, w / 2.0, c2_y - 8.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # 3. Cache Engine: aws.CredentialsCache
    c3_h = 56.0
    c3_y = c2_y - 8.0 - c3_h
    d.add(Rect(cx, c3_y, cw, c3_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(cx + 8.0, c3_y + c3_h - 11.0, "aws.CredentialsCache (TẦNG ĐỆM & REFRESH)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c3_y + 32.0, "• Retrieve(ctx): Lấy và lưu giữ credentials trong bộ nhớ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c3_y + 20.0, "• Kiểm tra CanExpire & Expires để tự động refresh token", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c3_y + 8.0, "• sync.RWMutex an toàn cho goroutines truy xuất đồng thời", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_arrow(d, w / 2.0, c3_y, w / 2.0, c3_y - 8.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # 4. Value Output: aws.Credentials
    c4_y = body_y
    c4_h = c3_y - c4_y - 8.0
    d.add(Rect(cx, c4_y, cw, c4_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(cx + 8.0, c4_y + c4_h - 11.0, "aws.Credentials (DỮ LIỆU ĐÃ PHÂN GIẢI)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c4_y + 20.0, "AccessKeyID, SecretAccessKey, SessionToken", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(cx + 8.0, c4_y + 8.0, "CanExpire: bool, Expires: time.Time (nếu là token tạm)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

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
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 24 // HÌNH 42",
        title="SMITHY MIDDLEWARE STACK: ĐƯỜNG REQUEST VÀ RESPONSE TRONG AWS SDK V2",
        subtitle="Mũi tên liền là đường lồng gọi xuôi (Request); mũi tên đứt là đường trả về ngược (Response) giải mã kết quả.",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    col_w = (w - 24.0) / 2.0  # 206.77 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + 8.0

    step_gap = 8.0
    step_h = (body_h - 3 * step_gap) / 4.0

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

    draw_arrow(d, col1_x + col_w, s4_y + step_h / 2.0, col2_x, s4_y + step_h / 2.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Right Column: Transport and Deserialize
    trans_h = 100.0
    trans_y = body_y + body_h - trans_h
    d.add(Rect(col2_x, trans_y, col_w, trans_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(col2_x + 8.0, trans_y + trans_h - 12.0, "HTTP ROUND TRIP (TRANSPORT TẦNG DƯỚI)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, trans_y + 68.0, "net/http.RoundTripper (AWS Service Gateway):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, trans_y + 54.0, "• Gửi HTTP Request qua kết nối TLS bảo mật", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, trans_y + 40.0, "• Nhận HTTP raw Response (status, headers, body stream)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, trans_y + 26.0, "• Quản lý Connection Pool, HTTP/2 multiplexing, Keep-Alive", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(col2_x + 8.0, trans_y + 12.0, "• Xử lý network timeout, DNS failover và connection reset", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    deser_y = body_y
    deser_h = trans_y - deser_y - 12.0
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

    draw_arrow(d, col2_x + col_w * 0.35, deser_y + deser_h, col2_x + col_w * 0.35, trans_y, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String(col2_x + col_w * 0.35 - 4.0, deser_y + deser_h + 3.0, "Request", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="end"))

    draw_arrow(d, col2_x + col_w * 0.65, trans_y, col2_x + col_w * 0.65, deser_y + deser_h, color=COLOR_INK_MID, width=0.8, head_size=3.0, dashed=True)
    d.add(String(col2_x + col_w * 0.65 + 4.0, deser_y + deser_h + 3.0, "Response", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MID))

    draw_footer_banner(d, w, "• Invariant: Mũi tên liền là đường lồng handler gọi xuôi (Request); mũi tên nét đứt là đường trả về ngược (Response) giải mã kết quả.")
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
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 25 // HÌNH 43",
        title="RANH GIỚI BẢN THỂ: GIT CORE VÀ GITHUB",
        subtitle="Git quản lý Merkle DAG; GitHub bổ sung API và cộng tác.",
    )

    body_bot = draw_footer_banner(
        d, w,
        [
            "• Invariant: Git quản lý object và lịch sử cục bộ;",
            "  GitHub bổ sung dịch vụ cộng tác có API và giới hạn riêng.",
        ]
    )

    body_y = body_bot + 4.0
    body_h = header_y - body_y - 4.0

    col_w = (w - 20.0) / 2.0  # 129.29 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + 4.0

    # Left Column: Git Core
    d.add(Rect(col1_x, body_y, col_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 5.0, body_y + body_h - 13.0, 72.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 41.0, body_y + body_h - 10.5, "GIT · KHO CỤC BỘ", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 6.0, body_y + body_h - 22.0, "Content Merkle DAG", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    git_items = [
        ("• Quản lý object phân tán", "BookSansBold"),
        ("• 4 loại Object cơ sở:", "BookSansBold"),
        ("  + blob: nội dung file", "BookMono"),
        ("  + tree: thư mục & quyền", "BookMono"),
        ("  + commit: snapshot & cha", "BookMono"),
        ("  + tag: annotated tag", "BookMono"),
        ("• Định danh bằng cryptographic:", "BookSans"),
        ("  SHA-1 hoặc SHA-256 hash", "BookMono"),
        ("• Directed Acyclic Graph (DAG)", "BookSans"),
        ("• Hoạt động 100% offline", "BookSansBold"),
        ("• Không cần mạng, không GitHub", "BookSans"),
        ("• Không có khái niệm PR/Issue", "BookSans"),
        ("• Lịch sử lưu trữ bất biến", "BookSans"),
    ]

    gy = body_y + body_h - 35.0
    for gtext, gfont in git_items:
        d.add(String(col1_x + 6.0, gy, gtext, fontName=gfont, fontSize=6.0, fillColor=COLOR_INK_DARK))
        gy -= 18.0

    # Right Column: GitHub Platform
    d.add(Rect(col2_x, body_y, col_w, body_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 5.0, body_y + body_h - 13.0, 78.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col2_x + 44.0, body_y + body_h - 10.5, "GITHUB · NỀN TẢNG", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 6.0, body_y + body_h - 22.0, "Hosted SaaS Platform", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

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

    hy = body_y + body_h - 35.0
    for htext, hfont in gh_items:
        d.add(String(col2_x + 6.0, hy, htext, fontName=hfont, fontSize=6.0, fillColor=COLOR_INK_DARK))
        hy -= 18.0

    return d


# ======================================================================
# 12. Chapter 25 — Figure 44: Webhook HMAC Verification (407.82 x 362.83 pt)
# ======================================================================
def build_webhook_hmac_verification_drawing(w: float = 407.82, h: float = 362.83) -> Drawing:
    """Figure 44: Xác minh chữ ký HMAC của webhook GitHub.

    Đồng bộ chuẩn xác theo labs/part25-github-automation/webhook.go:
    VerifyHMACSHA256:
    1. strings.HasPrefix(sigHeader, "sha256=")
    2. actualMAC, err := hex.DecodeString(hexSig)
    3. mac := hmac.New(sha256.New, []byte(secret)); mac.Write(rawBody)
    4. hmac.Equal(actualMAC, expectedMAC)
    Exact dimensions: 407.82 x 362.83 pt (Page 444, xref 506).
    """
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 25 // HÌNH 44",
        title="XÁC MINH CHỮ KÝ HMAC-SHA256 CỦA WEBHOOK GITHUB",
        subtitle="Đồng bộ VerifyHMACSHA256: kiểm tra prefix, decode hex, tính HMAC trên raw bytes và so sánh hmac.Equal.",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    actor1_x = 75.0    # GitHub Dispatcher
    actor2_x = 285.0   # Go Webhook Server

    act_box_w1 = 110.0
    act_box_w2 = 120.0
    act_box_h = 20.0
    act_box_y = header_y - act_box_h - 6.0

    d.add(Rect(actor1_x - act_box_w1 / 2.0, act_box_y, act_box_w1, act_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor1_x, act_box_y + 11.5, "GITHUB DISPATCHER", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor1_x, act_box_y + 4.5, "Nguồn phát Webhook Event", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    d.add(Rect(actor2_x - act_box_w2 / 2.0, act_box_y, act_box_w2, act_box_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor2_x, act_box_y + 11.5, "GO WEBHOOK SERVER", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, act_box_y + 4.5, "labs/part25-github-automation", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    lifeline_bot = body_y + 6.0
    lifeline_top = act_box_y
    for ax in (actor1_x, actor2_x):
        line = Line(ax, lifeline_top, ax, lifeline_bot)
        line.strokeColor = COLOR_BORDER
        line.strokeWidth = 0.8
        line.strokeDashArray = [3, 2]
        d.add(line)

    box_w = 210.0
    box_left = actor2_x - box_w / 2.0  # 180.0 to 390.0, margin to 407.82 is 17.82 pt

    # 1. GitHub computes HMAC
    sy1 = act_box_y - 28.0
    d.add(Rect(actor1_x - 55.0, sy1 - 9.0, 110.0, 23.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(actor1_x, sy1 + 5.0, "HMAC-SHA256(secret, payload)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor1_x, sy1 - 4.5, "Tính chữ ký hex từ raw bytes", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 2. HTTP POST Transmission
    sy2 = sy1 - 28.0
    draw_arrow(d, actor1_x, sy2, actor2_x, sy2, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor1_x + actor2_x) / 2.0, sy2 + 3.0, "POST /webhook (Header: X-Hub-Signature-256 + Raw Body bytes)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # 3. Step A: Check prefix & Decode hex
    sy3 = sy2 - 32.0
    d.add(Rect(box_left, sy3 - 11.0, box_w, 28.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(actor2_x, sy3 + 5.0, "1. strings.HasPrefix(sigHeader, \"sha256=\")", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, sy3 - 5.0, "2. actualMAC, err := hex.DecodeString(hexSig)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # 4. Security Invariant Banner
    sy4 = sy3 - 34.0
    d.add(Rect(actor1_x - 30.0, sy4 - 8.0, (actor2_x - actor1_x) + 60.0, 24.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.6, rx=2, ry=2))
    d.add(String((actor1_x + actor2_x) / 2.0, sy4 + 5.5, "KHÔNG UNMARSHAL RỒI MARSHAL LẠI JSON TRƯỚC KHI TÍNH HMAC", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String((actor1_x + actor2_x) / 2.0, sy4 - 3.0, "Phải hash trực tiếp trên raw bytes; re-marshal làm đổi key order và whitespace.", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 5. Step B: Compute expected HMAC (3 separate lines, 0 semicolon cramming)
    sy5 = sy4 - 36.0
    d.add(Rect(box_left, sy5 - 15.0, box_w, 36.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(actor2_x, sy5 + 8.0, "mac := hmac.New(sha256.New, []byte(secret))", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, sy5 - 1.0, "mac.Write(rawBody)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, sy5 - 10.0, "expectedMAC := mac.Sum(nil)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # 6. Step C: hmac.Equal constant time
    sy6 = sy5 - 34.0
    d.add(Rect(box_left, sy6 - 11.0, box_w, 28.0, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=1.5, ry=1.5))
    d.add(String(actor2_x, sy6 + 5.0, "return hmac.Equal(actualMAC, expectedMAC)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, sy6 - 5.0, "So sánh hằng thời gian (constant-time, chống timing attack)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # 7. Two Decisions
    sy7 = sy6 - 36.0
    dec_box_w = 115.0
    dec_box_h = 32.0

    # Left: False
    false_box_x = 70.0
    d.add(Rect(false_box_x, sy7 - 16.0, dec_box_w, dec_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(false_box_x + dec_box_w / 2.0, sy7 + 7.5, "SAI CHỮ KÝ (FALSE)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(false_box_x + dec_box_w / 2.0, sy7 - 1.5, "VerifyHMAC == false", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(false_box_x + dec_box_w / 2.0, sy7 - 10.0, "Process trả ErrInvalidSignature", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    draw_arrow(d, box_left, sy6 - 5.0, false_box_x + dec_box_w, sy7 + 8.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    # Right: True
    true_box_x = actor2_x - dec_box_w / 2.0  # 285.0 - 57.5 = 227.5
    d.add(Rect(true_box_x, sy7 - 16.0, dec_box_w, dec_box_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=1.5, ry=1.5))
    d.add(String(actor2_x, sy7 + 7.5, "HỢP LỆ (TRUE)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, sy7 - 1.5, "VerifyHMAC == true", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, sy7 - 10.0, "Process: tiếp tục ledger.Begin", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    draw_arrow(d, actor2_x, sy6 - 11.0, actor2_x, sy7 + 16.0, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

    draw_footer_banner(d, w, "• Invariant: VerifyHMACSHA256 so sánh hằng thời gian qua hmac.Equal; raw payload giữ nguyên vẹn trước khi decode JSON.")
    return d

# ======================================================================
# 13. Chapter 25 — Figure 45: Webhook Delivery Deduplication (462.12 x 362.83 pt)
# ======================================================================
def build_webhook_delivery_deduplication_drawing(w: float = 462.12, h: float = 362.83) -> Drawing:
    """Figure 45: Mô hình Deduplication và chống Replay Webhook theo Delivery ID.

    Đồng bộ WebhookReceiver.Process và DeliveryLedger trong webhook.go:
    - Begin(id) reserve trạng thái processing trong map cục bộ (sync.Mutex).
    - Đây là in-memory deduplication, không phải distributed lease có TTL.
    - Không đảm bảo khử trùng lặp bền vững qua restart hoặc cross-process.
    Exact dimensions: 462.12 x 362.83 pt (Page 447, xref 510).
    """
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 25 // HÌNH 45",
        title="KHỬ TRÙNG LẶP WEBHOOK THEO DELIVERY ID TRONG BỘ NHỚ",
        subtitle="WebhookReceiver.Process: Begin chuyển trạng thái processing, chỉ gọi handle khi accepted; Complete khi xong.",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    # 4 Actors
    actor1_x = 50.0   # GitHub Dispatcher
    actor2_x = 170.0  # WebhookReceiver
    actor3_x = 320.0  # DeliveryLedger (sync.Mutex)
    actor4_x = 420.0  # Business Handler

    act_box_h = 20.0
    act_box_y = header_y - act_box_h - 6.0

    act1_w = 84.0
    d.add(Rect(actor1_x - act1_w / 2.0, act_box_y, act1_w, act_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor1_x, act_box_y + 11.5, "GITHUB DISPATCHER", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor1_x, act_box_y + 4.5, "At-least-once", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    act2_w = 108.0
    d.add(Rect(actor2_x - act2_w / 2.0, act_box_y, act2_w, act_box_h, fillColor=COLOR_BG_SUBTLE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor2_x, act_box_y + 11.5, "WebhookReceiver", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, act_box_y + 4.5, "Process(deliveryID)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    act3_w = 108.0
    d.add(Rect(actor3_x - act3_w / 2.0, act_box_y, act3_w, act_box_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor3_x, act_box_y + 11.5, "DeliveryLedger", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor3_x, act_box_y + 4.5, "sync.Mutex (RAM map)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    act4_w = 72.0
    d.add(Rect(actor4_x - act4_w / 2.0, act_box_y, act4_w, act_box_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(actor4_x, act_box_y + 11.5, "HANDLER", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor4_x, act_box_y + 4.5, "handle() error", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    lifeline_bot = body_y + 6.0
    lifeline_top = act_box_y
    for ax in (actor1_x, actor2_x, actor3_x, actor4_x):
        line = Line(ax, lifeline_top, ax, lifeline_bot)
        line.strokeColor = COLOR_BORDER
        line.strokeWidth = 0.8
        line.strokeDashArray = [3, 2]
        d.add(line)

    # 1. Delivery 1 (between Actor 1 and Actor 2: 120 pt gap)
    y1 = act_box_y - 22.0
    draw_arrow(d, actor1_x, y1, actor2_x, y1, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor1_x + actor2_x) / 2.0, y1 + 3.0, "1. POST (ID: \"7a1b...\", payload)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # 2. Verify HMAC
    y2 = y1 - 18.0
    d.add(Rect(actor2_x - 55.0, y2 - 8.0, 110.0, 18.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(actor2_x, y2 - 2.0, "VerifyHMACSHA256() == true", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # 3. ledger.Begin (between Actor 2 and Actor 3: 150 pt gap)
    y3 = y2 - 20.0
    draw_arrow(d, actor2_x, y3, actor3_x, y3, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor2_x + actor3_x) / 2.0, y3 + 3.0, "2. ledger.Begin(\"7a1b...\")", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    y4 = y3 - 18.0
    draw_arrow(d, actor3_x, y4, actor2_x, y4, color=COLOR_INK_MID, width=0.8, head_size=3.0)
    d.add(String((actor2_x + actor3_x) / 2.0, y4 + 3.0, "accepted=true (state: processing)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 4. Invoke handle() - bridge over Actor 3 (between Actor 3 and Actor 4: 100 pt gap)
    y5 = y4 - 20.0
    d.add(Rect(actor3_x - 4.0, y5 - 4.0, 8.0, 8.0, fillColor=COLOR_WHITE, strokeColor=None))
    draw_arrow(d, actor2_x, y5, actor4_x, y5, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor3_x + actor4_x) / 2.0, y5 + 3.0, "3. handle()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    y6 = y5 - 18.0
    d.add(Rect(actor3_x - 4.0, y6 - 4.0, 8.0, 8.0, fillColor=COLOR_WHITE, strokeColor=None))
    draw_arrow(d, actor4_x, y6, actor2_x, y6, color=COLOR_INK_MID, width=0.8, head_size=3.0)
    d.add(String((actor3_x + actor4_x) / 2.0, y6 + 3.0, "return nil", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 5. ledger.Complete (between Actor 2 and Actor 3: 150 pt gap)
    y7 = y6 - 20.0
    draw_arrow(d, actor2_x, y7, actor3_x, y7, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor2_x + actor3_x) / 2.0, y7 + 3.0, "4. ledger.Complete(\"7a1b...\")", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Process return on first delivery: (false, nil)
    y8 = y7 - 18.0
    draw_arrow(d, actor2_x, y8, actor1_x, y8, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor1_x + actor2_x) / 2.0, y8 + 3.0, "return false, nil", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Break: Redelivery
    y_break = y8 - 22.0
    d.add(Rect(actor1_x - 20.0, y_break - 9.0, (actor4_x - actor1_x) + 40.0, 22.0, fillColor=COLOR_BG_HEADER, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String((actor1_x + actor4_x) / 2.0, y_break + 4.0, "--- GITHUB GỬI LẠI CÙNG MỘT WEBHOOK (REDELIVERY: CÙNG ID \"7a1b...\") ---", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String((actor1_x + actor4_x) / 2.0, y_break - 4.0, "Map in-memory phát hiện đã completed; triệt tiêu duplicate mà không gọi lại handle()", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 6. Redelivery arriving
    y9 = y_break - 22.0
    draw_arrow(d, actor1_x, y9, actor2_x, y9, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor1_x + actor2_x) / 2.0, y9 + 3.0, "5. POST (CÙNG ID: \"7a1b...\")", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # 7. ledger.Begin check duplicate (between Actor 2 and Actor 3: 150 pt gap)
    y10 = y9 - 18.0
    draw_arrow(d, actor2_x, y10, actor3_x, y10, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor2_x + actor3_x) / 2.0, y10 + 3.0, "6. ledger.Begin(\"7a1b...\")", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    y11 = y10 - 18.0
    draw_arrow(d, actor3_x, y11, actor2_x, y11, color=COLOR_INK_MID, width=0.8, head_size=3.0)
    d.add(String((actor2_x + actor3_x) / 2.0, y11 + 3.0, "accepted=false (duplicate)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # 8. Duplicate suppressed
    y12 = y11 - 22.0
    d.add(Rect(actor2_x - 65.0, y12 - 10.0, 130.0, 22.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=1.5, ry=1.5))
    d.add(String(actor2_x, y12 + 3.5, "DUPLICATE SUPPRESSION", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(actor2_x, y12 - 5.5, "Bỏ qua handle(); không chạy side effect", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))

    # Process return on redelivery: (true, nil)
    y13 = y12 - 20.0
    draw_arrow(d, actor2_x, y13, actor1_x, y13, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String((actor1_x + actor2_x) / 2.0, y13 + 3.0, "7. return true, nil", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    draw_footer_banner(d, w, "• Invariant: DeliveryLedger reserve trạng thái trong map RAM (sync.Mutex); không phải distributed lease có TTL và reset khi restart.")
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
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 26 // HÌNH 46",
        title="CHUỖI BẰNG CHỨNG SUPPLY CHAIN",
        subtitle="6 mắt xích từ nguồn đến Cổng chính sách (Policy Gate).",
    )

    body_bot = draw_footer_banner(
        d, w,
        [
            "• Invariant: Cổng chỉ xác minh bằng chứng policy yêu cầu;",
            "  fail-closed khi thiếu; đủ bằng chứng không chứng minh vô hại.",
        ]
    )

    body_y = body_bot + 4.0
    body_h = header_y - body_y - 4.0

    cw = w - 16.0  # 198.51 pt
    cx = 8.0

    card_gap = 5.0
    card_h = (body_h - 5 * card_gap) / 6.0  # ~43.5 pt each

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
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 26 // HÌNH 47",
        title="PHÂN BIỆT PHỤ THUỘC CÓ SYMBOL VÀ ĐƯỜNG GỌI CÓ THỂ TỚI (CALL REACHABILITY)",
        subtitle="govulncheck phân tích đường gọi tĩnh để lọc nhiễu các lỗ hổng không kích hoạt từ mã nguồn ứng dụng.",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    root_w = 260.0
    root_h = 38.0
    root_x = (w - root_w) / 2.0
    root_y = body_y + body_h - root_h
    d.add(Rect(root_x, root_y, root_w, root_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(String(w / 2.0, root_y + root_h - 11.0, "ỨNG DỤNG NGHIỆP VỤ (cmd/server/main.go)", fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(w / 2.0, root_y + 16.0, "Module: mycompany.com/backend · Root of Call Graph", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID, textAnchor="middle"))
    d.add(String(w / 2.0, root_y + 6.0, "Phụ thuộc module: golang.org/x/crypto", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    col_w = (w - 24.0) / 2.0  # 226.11 pt each
    col1_x = 8.0
    col2_x = col1_x + col_w + 8.0
    col_y = body_y
    col_h = root_y - col_y - 14.0

    draw_arrow(d, root_x + 40.0, root_y, col1_x + col_w / 2.0, col_y + col_h, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    draw_arrow(d, root_x + root_w - 40.0, root_y, col2_x + col_w / 2.0, col_y + col_h, color=COLOR_INK_MID, width=0.8, head_size=3.0, dashed=True)

    # Left Column: Reachable
    d.add(Rect(col1_x, col_y, col_w, col_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col1_x + 6.0, col_y + col_h - 13.0, 96.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col1_x + 54.0, col_y + col_h - 10.5, "ĐƯỜNG GỌI CÓ THỂ TỚI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col1_x + 108.0, col_y + col_h - 10.5, "(REACHABLE FINDING)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    d.add(String(col1_x + 8.0, col_y + col_h - 26.0, "Dependency: golang.org/x/crypto/bcrypt", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col1_x + 8.0, col_y + col_h - 38.0, "Vết đường gọi thực tế (Call Trace):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

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

    # Right Column: Unreachable
    d.add(Rect(col2_x, col_y, col_w, col_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(col2_x + 6.0, col_y + col_h - 13.0, 108.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(col2_x + 60.0, col_y + col_h - 10.5, "KHÔNG CÓ ĐƯỜNG GỌI TỚI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(col2_x + 120.0, col_y + col_h - 10.5, "(UNREACHABLE)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    d.add(String(col2_x + 8.0, col_y + col_h - 26.0, "Dependency: golang.org/x/crypto/ssh", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(col2_x + 8.0, col_y + col_h - 38.0, "Phân tích đồ thị gọi (Call Graph Analysis):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

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

    draw_footer_banner(d, w, "• Invariant: Có phụ thuộc bị ảnh hưởng và có đường gọi tới bcrypt nhưng không thấy đường gọi tới ssh.ParsePrivateKey; kết quả phụ thuộc chế độ build.")
    return d


# ======================================================================
# 16. Chapter 26 — Figure 48: Container Tag vs Digest (476.22 x 327.02 pt)
# ======================================================================
def build_container_tag_digest_drawing(w: float = 476.22, h: float = 327.02) -> Drawing:
    """Figure 48: Thẻ nhãn (tag) và mã băm (digest) của container image.

    Phân biệt OCI manifest digest và image index digest đa kiến trúc.
    Digest cố định định danh nội dung tương ứng, không chứng minh mọi node
    chạy cùng một binary, provenance đã xác thực hoặc phần mềm an toàn.
    Exact dimensions: 476.22 x 327.02 pt (Page 470, xref 536).
    """
    register_fonts()
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 26 // HÌNH 48",
        title="BẢN CHẤT CONTAINER TAG VÀ DIGEST: CON TRỎ ĐỔI ĐÍCH VS MÃ BĂM NỘI DUNG",
        subtitle="Tag là con trỏ có thể thay đổi (Mutable Pointer); Digest là định danh nội dung bất biến (SHA-256).",
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    half_h = (body_h - 8.0) / 2.0
    top_y = body_y + half_h + 8.0
    bot_y = body_y

    # Top Half: CONTAINER TAG
    d.add(Rect(8.0, top_y, w - 16.0, half_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(14.0, top_y + half_h - 13.0, 130.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(79.0, top_y + half_h - 10.5, "TAG: CON TRỎ CÓ THỂ THAY ĐỔI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(150.0, top_y + half_h - 10.5, "(MUTABLE POINTER - NGUY CƠ TRÔI DẠT PHIÊN BẢN)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    t_box_w = 200.0
    d.add(Rect(14.0, top_y + 8.0, t_box_w, half_h - 26.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(20.0, top_y + half_h - 38.0, "Tham chiếu: myorg/app:v1.2.0", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(20.0, top_y + half_h - 52.0, "• Thời điểm T0: Build 1 push v1.2.0", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(28.0, top_y + half_h - 62.0, "-> Trỏ Image A (sha256:7f83b1...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(20.0, top_y + half_h - 74.0, "• Thời điểm T1: Build 2 ghi đè cùng tag v1.2.0", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(28.0, top_y + half_h - 84.0, "-> Trỏ Image B (sha256:4a12c8...)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(20.0, top_y + 14.0, "Tag chỉ là alias có thể đổi đích trong Registry", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    r_box_x = 14.0 + t_box_w + 10.0
    r_box_w = (w - 16.0) - r_box_x - 6.0
    d.add(Rect(r_box_x, top_y + 8.0, r_box_w, half_h - 26.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(r_box_x + 8.0, top_y + half_h - 38.0, "Hậu quả trôi dạt (Drift) trong cụm Kubernetes:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, top_y + half_h - 52.0, "• Node 1 (đã cache Image A) tiếp tục chạy Image A cũ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, top_y + half_h - 64.0, "• Node 2 (node mới tạo) pull Image B mới với cùng tag v1.2.0", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, top_y + half_h - 76.0, "• Pod template hoàn toàn giống nhau nhưng hành vi khác biệt", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, top_y + 14.0, "• Phụ thuộc vào imagePullPolicy, cache node và cấu hình registry", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Bottom Half: CONTAINER DIGEST
    d.add(Rect(8.0, bot_y, w - 16.0, half_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(14.0, bot_y + half_h - 13.0, 140.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(84.0, bot_y + half_h - 10.5, "DIGEST: ĐỊNH DANH NỘI DUNG BẤT BIẾN", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))
    d.add(String(160.0, bot_y + half_h - 10.5, "(IMMUTABLE CONTENT-ADDRESSABLE IDENTIFIER)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    d.add(Rect(14.0, bot_y + 8.0, t_box_w, half_h - 26.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(20.0, bot_y + half_h - 38.0, "Tham chiếu: myorg/app@sha256:7f83b1...", fontName="BookMono", fontSize=6.2, fillColor=COLOR_INK_DARK))
    d.add(String(20.0, bot_y + half_h - 52.0, "• Mã băm SHA-256 tính từ Manifest / Index:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(28.0, bot_y + half_h - 62.0, "Manifest: ghim chính xác config & layers", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(28.0, bot_y + half_h - 72.0, "Index: đa kiến trúc (amd64 / arm64)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(20.0, bot_y + half_h - 84.0, "• Bất biến: Đổi 1 bit nội dung -> Digest đổi", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(20.0, bot_y + 14.0, "Không thể bị ghi đè ngầm trong registry", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    d.add(Rect(r_box_x, bot_y + 8.0, r_box_w, half_h - 26.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(r_box_x + 8.0, bot_y + half_h - 38.0, "Khế ước định danh & Ranh giới bảo mật:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, bot_y + half_h - 52.0, "• Ghim chặt nội dung manifest được tham chiếu tại thời điểm lấy", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, bot_y + half_h - 64.0, "• Multi-arch index digest phân giải sang binary riêng từng arch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, bot_y + half_h - 76.0, "• Loại trừ rủi ro tráo tag; làm đầu vào cho kiểm tra Cosign", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(r_box_x + 8.0, bot_y + 14.0, "• Lưu ý: Digest không tự xác minh người tạo hay độ an toàn mã", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    draw_footer_banner(d, w, "• Invariant: Tag phân giải thành digest tại thời điểm lấy; dùng digest cố định nội dung nhưng không tự xác minh người tạo, provenance hay mã an toàn.")
    return d


def build_ebpf_build_load_drawing(w: float = 244.10, h: float = 362.83) -> Drawing:
    """Figure 49: Tách giai đoạn build eBPF và giai đoạn load trên Linux.

    Clang và bpf2go thuộc toolchain build. Binary Go mang object BPF đến
    runtime; kernel vẫn kiểm tra program, quyền và khả năng hỗ trợ trước
    khi load hoặc attach thành công.
    Exact dimensions: 244.10 x 362.83 pt (Page 490, xref 557).
    """
    register_fonts()
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 27 // HÌNH 49",
        title="TÁCH BẠCH BUILD VÀ LOAD EBPF",
        subtitle="Build Toolchain vs Linux Kernel Runtime Verifier",
    )

    footer_top = draw_footer_banner(
        d, w,
        [
            "• Invariant: Build sinh bytecode & bindings;",
            "  Kernel verifier độc lập kiểm soát an toàn khi load.",
        ]
    )

    body_y = footer_top + 4.0
    body_h = header_y - body_y - 4.0

    # Two main cards: BUILD PHASE (top) vs LOAD PHASE (bottom)
    # Give build phase 125 pt, transition zone 24 pt, load phase 130 pt
    card_w = w - 16.0
    card_x = 8.0

    b_h = 124.0
    b_y = body_y + body_h - b_h

    # --- TOP CARD: BUILD PHASE ---
    d.add(Rect(card_x, b_y, card_w, b_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 6.0, b_y + b_h - 13.0, 115.0, 9.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(card_x + 63.5, b_y + b_h - 10.5, "1. GIAI ĐOẠN BUILD (DEV/CI)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    inner_w = card_w - 12.0
    ix = card_x + 6.0

    # Sub-box: Inputs (C source + vmlinux.h)
    d.add(Rect(ix, b_y + 68.0, inner_w, 40.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(ix + 6.0, b_y + 98.0, "Nguyên liệu mã nguồn:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(ix + 6.0, b_y + 87.0, "• exec_observer.c (C tracepoint logic)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(ix + 6.0, b_y + 76.0, "• vmlinux.h (bpftool dump BTF từ kernel đích)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Toolchain step
    d.add(Rect(ix, b_y + 36.0, inner_w, 26.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(ix + 6.0, b_y + 51.0, "Toolchain: clang -target bpfel -O2 -g", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(ix + 6.0, b_y + 41.0, "Kết hợp bpf2go đóng gói ELF vào Go code", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Artifacts output
    d.add(Rect(ix, b_y + 6.0, inner_w, 24.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(ix + 6.0, b_y + 19.0, "Artifact: bpf_bpfel.o (ELF) + bpf_bpfel.go", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(ix + 6.0, b_y + 10.0, "Tạo binary Go độc lập userspace (không cần CGO)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # --- TRANSITION ZONE (Arrow between build and load) ---
    mid_y = b_y - 12.0
    draw_arrow(d, w / 2.0, b_y - 2.0, w / 2.0, b_y - 18.0, color=COLOR_INK_DARK, width=1.0, head_size=3.5)
    d.add(String(w / 2.0 + 8.0, mid_y, "Deploy binary Go tới Linux", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # --- BOTTOM CARD: LOAD & RUNTIME PHASE ---
    l_h = b_y - 22.0 - body_y
    l_y = body_y

    d.add(Rect(card_x, l_y, card_w, l_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 6.0, l_y + l_h - 13.0, 120.0, 9.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(card_x + 66.0, l_y + l_h - 10.5, "2. GIAI ĐOẠN LOAD (RUNTIME LINUX)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Userspace Go Runtime
    d.add(Rect(ix, l_y + l_h - 38.0, inner_w, 21.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(ix + 6.0, l_y + l_h - 26.0, "Go Userspace: cilium/ebpf loader", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(ix + 6.0, l_y + l_h - 35.0, "Gọi sys_bpf(BPF_PROG_LOAD) nạp bytecode", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Kernel Space Security & Execution
    k_box_h = l_h - 44.0
    d.add(Rect(ix, l_y + 6.0, inner_w, k_box_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(ix + 6.0, l_y + k_box_h - 4.0, "Linux Kernel Space (Bảo mật & Thực thi):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(ix + 6.0, l_y + k_box_h - 15.0, "• BPF Verifier: kiểm tra an toàn con trỏ,", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(ix + 12.0, l_y + k_box_h - 25.0, "vòng lặp hữu hạn, quyền CAP_BPF/root", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(ix + 6.0, l_y + k_box_h - 36.0, "• JIT Compiler: biên dịch ra native machine code", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(ix + 6.0, l_y + k_box_h - 47.0, "• Attach: tracepoint/sched/sched_process_exec", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(ix + 6.0, l_y + k_box_h - 58.0, "• Ring Buffer: stream event nhị phân về Go", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ----------------------------------------------------------------------
# 18. Chapter 29 — Figure 50: Change Evidence Gate (476.22 x 260.59 pt)
# ----------------------------------------------------------------------
def build_change_evidence_gate_drawing(w: float = 476.22, h: float = 260.59) -> Drawing:
    """Figure 50: Cổng bằng chứng thay đổi và ranh giới thực thi.

    Policy.Check chỉ là hàm lượng giá thuần túy (pure evaluation contract),
    nhận (now, who, plan, evidence, approval) và trả về nil hoặc ErrDenied.
    Các khâu dispatch, executor, distributed lock hay rollback không được lab
    này triển khai và thuộc ranh giới kiến trúc bên ngoài.
    Exact dimensions: 476.22 x 260.59 pt (Page 544, xref 612).
    """
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="CHƯƠNG 29 // HÌNH 50",
        title="CỔNG BẰNG CHỨNG THAY ĐỔI: PURE EVALUATION & DISPATCH",
        subtitle="Policy.Check chỉ lượng giá logic thuần túy (nil/ErrDenied); ranh giới ngoài xử lý dispatch & lock.",
    )

    draw_footer_banner(
        d, w,
        "• Invariant: Policy.Check chỉ lượng giá logic thuần túy (nil/ErrDenied); executor, lock phân tán và rollback không triển khai trong lab này."
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    # 3 Columns Layout:
    # Col 1: ĐẦU VÀO ĐỘC LẬP (Independent Inputs) - w = 142 pt (inner = 130 pt)
    # Col 2: POLICY.CHECK (Pure Evaluation) - w = 188 pt (inner = 172 pt)
    # Col 3: RANH GIỚI BÊN NGOÀI (External Boundaries) - w = 118 pt (inner = 106 pt)
    c1_w = 142.0
    c2_w = 188.0
    c3_w = 118.0
    c1_x = 8.0
    c2_x = c1_x + c1_w + 8.0   # 158.0
    c3_x = c2_x + c2_w + 8.0   # 354.0

    # Col 1: INPUTS
    d.add(Rect(c1_x, body_y, c1_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c1_x + 6.0, body_y + body_h - 13.0, 115.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c1_x + 63.5, body_y + body_h - 10.5, "1. ĐẦU VÀO ĐỘC LẬP", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Box 1: Plan & Principal
    d.add(Rect(c1_x + 6.0, body_y + body_h - 72.0, c1_w - 12.0, 54.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c1_x + 10.0, body_y + body_h - 26.5, "Plan & Principal (Đề xuất):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 37.0, "• who: ID=\"ops-agent\", Operator", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 47.0, "• Action: \"restart-demo\"", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 56.5, "• Target: \"demo-service\"", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 10.0, body_y + body_h - 65.5, "• DiffSHA: SHA-256 (32 byte hex)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 2: Evidence
    d.add(Rect(c1_x + 6.0, body_y + body_h - 132.0, c1_w - 12.0, 54.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c1_x + 10.0, body_y + body_h - 86.5, "Evidence (Verifier độc lập):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 97.0, "• PlanDigest: hex(sha256(Plan))", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 107.0, "• Passed: true (CI/Test)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 116.5, "• CheckedAt: timestamp kiểm định", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 10.0, body_y + body_h - 125.5, "  (Độc lập, không tin payload)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 3: Approval
    d.add(Rect(c1_x + 6.0, body_y + 10.0, c1_w - 12.0, 50.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c1_x + 10.0, body_y + 51.5, "Approval (Ký duyệt độc lập):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + 40.5, "• PlanDigest: khớp mã digest", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + 30.0, "• Caller: who.ID (\"ops-agent\")", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + 19.5, "• ExpiresAt: hạn chót hợp lệ", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrow from Col 1 to Col 2
    draw_arrow(d, c1_x + c1_w, body_y + body_h / 2.0, c2_x, body_y + body_h / 2.0, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # Col 2: POLICY.CHECK
    d.add(Rect(c2_x, body_y, c2_w, body_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=1.0, rx=2, ry=2))
    d.add(Rect(c2_x + 6.0, body_y + body_h - 13.0, 176.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c2_x + 94.0, body_y + body_h - 10.5, "2. POLICY.CHECK (EVALUATION ONLY)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(String(c2_x + 8.0, body_y + body_h - 25.0, "Nhận: (now, who, plan, evidence, approval)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 8.0, body_y + body_h - 35.0, "6 Điều kiện kiểm tra khế ước (gate.go):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # 6 checks list formatted to fit strictly within c2_w = 188 pt (inner width = 172 pt)
    checks = [
        "1. who.ID != \"\" && who.Operator == true",
        "2. plan.Action == \"restart-demo\" (whitelist)",
        "3. AllowedTargets[plan.Target] == true",
        "4. hex.DecodeString(DiffSHA): 32 byte valid",
        "5. Evidence: Passed && khớp PlanDigest",
        "   now - CheckedAt <= MaxEvidenceAge",
        "6. Approval: khớp PlanDigest && Caller",
        "   now.Before(approval.ExpiresAt)",
    ]
    cur_y = body_y + body_h - 46.0
    for chk in checks:
        font_to_use = "BookMono" if any(ch in chk for ch in "()[]{}!=<>&") else "BookSans"
        d.add(String(c2_x + 8.0, cur_y, chk, fontName=font_to_use, fontSize=6.0, fillColor=COLOR_INK_DARK))
        cur_y -= 10.5

    # Decision box at bottom of Col 2
    d.add(Rect(c2_x + 8.0, body_y + 8.0, c2_w - 16.0, 38.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.6, rx=1.5, ry=1.5))
    d.add(String(c2_x + 14.0, body_y + 35.5, "KẾT QUẢ ĐÁNH GIÁ (RETURN VALUE):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 14.0, body_y + 24.5, "• Thỏa mãn: return nil -> Cho phép dispatch", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 14.0, body_y + 13.5, "• Vi phạm: return ErrDenied -> Chặn thay đổi", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow from Col 2 to Col 3 (on nil return) - cleanly connects evaluation to external dispatcher
    draw_arrow(d, c2_x + c2_w, body_y + 24.5, c3_x, body_y + 24.5, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # Col 3: EXTERNAL BOUNDARIES
    d.add(Rect(c3_x, body_y, c3_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c3_x + 6.0, body_y + body_h - 13.0, 106.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c3_x + 59.0, body_y + body_h - 10.5, "3. RANH GIỚI BÊN NGOÀI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Box 1: Dispatcher
    d.add(Rect(c3_x + 6.0, body_y + body_h - 72.0, c3_w - 12.0, 54.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c3_x + 10.0, body_y + body_h - 26.5, "Dispatcher & Lock:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 37.0, "• Chống replay, xếp hàng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 47.0, "• Cấp phát lease / lock", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 10.0, body_y + body_h - 56.5, "• Ghi nhật ký audit", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(c3_x + 10.0, body_y + body_h - 65.5, "  (Lab không triển khai)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 2: Executor
    d.add(Rect(c3_x + 6.0, body_y + body_h - 132.0, c3_w - 12.0, 54.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c3_x + 10.0, body_y + body_h - 86.5, "Executor (Tác nhân ngoài):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 97.0, "• Thực thi vào cluster đích", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 107.0, "• Áp dụng timeout/RBAC", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 10.0, body_y + body_h - 116.5, "• Giới hạn quyền theo role", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(c3_x + 10.0, body_y + body_h - 125.5, "  (Lab không triển khai)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Box 3: Monitoring & Rollback
    d.add(Rect(c3_x + 6.0, body_y + 10.0, c3_w - 12.0, 50.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c3_x + 10.0, body_y + 51.5, "Hậu kiểm & Giám sát:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + 40.5, "• Đo đạc metric sau thay đổi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + 30.0, "• Rollback: cần hạ tầng riêng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 10.0, body_y + 19.5, "  (Lab không có auto-rollback)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    return d

def build_library_informer_data_path_drawing(w: float = 476.22, h: float = 265.65) -> Drawing:
    """Figure 51: Đường observation và khóa công việc trong informer.

    Informer cập nhật cache rồi phát event tới handler; handler của ứng dụng
    đưa khóa vào workqueue. Worker đọc observation hiện có khi điều hòa,
    không coi payload event là trạng thái cuối cùng.
    Đường đọc cache từ Worker đi qua khoảng trống ngang giữa Handler và Workqueue.
    Exact dimensions: 476.22 x 265.65 pt (Page 551, xref 620).
    """
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="PHỤ LỤC B // HÌNH 51",
        title="ĐƯỜNG OBSERVATION VÀ KHÓA CÔNG VIỆC TRONG INFORMER",
        subtitle="Cache cập nhật trước khi phát event; Handler chỉ đẩy Key vào Workqueue.",
    )

    draw_footer_banner(
        d, w,
        "• Invariant: Reflector -> DeltaFIFO -> cập nhật cache trước khi phát callback; Handler đẩy key vào queue; Worker đọc observation từ cache."
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    b1_w = 98.0
    b2_w = 115.0
    b3_w = 125.0
    b4_w = 104.0

    b1_x = 8.0
    b2_x = b1_x + b1_w + 6.0
    b3_x = b2_x + b2_w + 6.0
    b4_x = b3_x + b3_w + 6.0

    # Block 1: API Server & Reflector
    d.add(Rect(b1_x, body_y, b1_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(b1_x + 5.0, body_y + body_h - 13.0, 88.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(b1_x + 49.0, body_y + body_h - 10.5, "KUBE API & REFLECTOR", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(b1_x + 5.0, body_y + body_h - 80.0, b1_w - 10.0, 62.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(b1_x + 8.0, body_y + body_h - 26.0, "Kube API Server:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b1_x + 8.0, body_y + body_h - 38.0, "• Nguồn chân lý (etcd)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b1_x + 8.0, body_y + body_h - 49.0, "• Cung cấp List & Watch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b1_x + 8.0, body_y + body_h - 60.0, "• ResourceVersion mốc", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b1_x + 8.0, body_y + body_h - 71.0, "• Trả 410 Gone khi cũ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    d.add(Rect(b1_x + 5.0, body_y + 8.0, b1_w - 10.0, body_h - 94.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(b1_x + 8.0, body_y + body_h - 96.0, "Reflector Loop:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b1_x + 8.0, body_y + body_h - 108.0, "• List nạp snapshot", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b1_x + 8.0, body_y + body_h - 119.0, "• Watch nhận delta sự kiện", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b1_x + 8.0, body_y + body_h - 130.0, "• Đẩy đối tượng vào", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b1_x + 8.0, body_y + body_h - 141.0, "  DeltaFIFO", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Arrow b1 -> b2
    draw_arrow(d, b1_x + b1_w, body_y + body_h - 120.0, b2_x, body_y + body_h - 120.0, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # Block 2: DeltaFIFO & Cache/Indexer
    d.add(Rect(b2_x, body_y, b2_w, body_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(b2_x + 5.0, body_y + body_h - 13.0, 105.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(b2_x + 57.5, body_y + body_h - 10.5, "INFORMER & LOCAL CACHE", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(b2_x + 5.0, body_y + body_h - 80.0, b2_w - 10.0, 62.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(b2_x + 8.0, body_y + body_h - 26.0, "DeltaFIFO:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b2_x + 8.0, body_y + body_h - 38.0, "• Hàng đợi delta có khóa", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b2_x + 8.0, body_y + body_h - 49.0, "• Nén gộp các delta trùng", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b2_x + 8.0, body_y + body_h - 60.0, "• Đảm bảo thứ tự theo khóa", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b2_x + 8.0, body_y + body_h - 71.0, "• Pop() cập nhật cache trước", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    d.add(Rect(b2_x + 5.0, body_y + 8.0, b2_w - 10.0, body_h - 94.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(b2_x + 8.0, body_y + body_h - 96.0, "Local Cache (Indexer):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b2_x + 8.0, body_y + body_h - 108.0, "• ThreadSafeStore cục bộ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b2_x + 8.0, body_y + body_h - 119.0, "• Cập nhật TRƯỚC callback", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b2_x + 8.0, body_y + body_h - 130.0, "• Giảm tải tuyệt đối cho etcd", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b2_x + 8.0, body_y + body_h - 141.0, "• Phục vụ Get(key) tức thì", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow b2 -> b3 (cache updated, then event fired to handler)
    draw_arrow(d, b2_x + b2_w, body_y + body_h - 50.0, b3_x, body_y + body_h - 50.0, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # Block 3: Handler & Workqueue
    d.add(Rect(b3_x, body_y, b3_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(b3_x + 5.0, body_y + body_h - 13.0, 115.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(b3_x + 62.5, body_y + body_h - 10.5, "HANDLER & WORKQUEUE", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Handler Box (ends at body_y + body_h - 80.0)
    d.add(Rect(b3_x + 5.0, body_y + body_h - 80.0, b3_w - 10.0, 62.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(b3_x + 8.0, body_y + body_h - 26.0, "ResourceEventHandler:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b3_x + 8.0, body_y + body_h - 38.0, "• OnAdd, OnUpdate, OnDelete", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b3_x + 8.0, body_y + body_h - 49.0, "• KHÔNG xử lý nặng ở đây", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b3_x + 8.0, body_y + body_h - 60.0, "• Chỉ trích xuất namespace/name", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b3_x + 8.0, body_y + body_h - 71.0, "• Gọi queue.Add(key)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Workqueue Box (starts at body_y + body_h - 94.0)
    d.add(Rect(b3_x + 5.0, body_y + 8.0, b3_w - 10.0, body_h - 102.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(b3_x + 8.0, body_y + body_h - 104.0, "Workqueue (Typed[T]):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b3_x + 8.0, body_y + body_h - 116.0, "• Dirty Set & Processing Set", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b3_x + 8.0, body_y + body_h - 127.0, "• Tự động chống trùng lặp key", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b3_x + 8.0, body_y + body_h - 138.0, "• Rate Limiting Backoff", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b3_x + 8.0, body_y + 14.0, "• Done(key) hoàn tất chu kỳ", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow b3 -> b4
    draw_arrow(d, b3_x + b3_w, body_y + 36.0, b4_x, body_y + 36.0, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # Block 4: Reconciliation Workers
    d.add(Rect(b4_x, body_y, b4_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(b4_x + 5.0, body_y + body_h - 13.0, 94.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(b4_x + 52.0, body_y + body_h - 10.5, "WORKER RECONCILE", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(b4_x + 5.0, body_y + 8.0, b4_w - 10.0, body_h - 26.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(b4_x + 8.0, body_y + body_h - 26.0, "Worker Goroutines:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b4_x + 8.0, body_y + body_h - 38.0, "1. queue.Get() -> key", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b4_x + 8.0, body_y + body_h - 49.0, "2. Đọc observation MỚI:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b4_x + 10.0, body_y + body_h - 60.0, "indexer.GetByKey(key)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b4_x + 8.0, body_y + body_h - 71.0, "3. Reconcile(key):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(b4_x + 10.0, body_y + body_h - 82.0, "So sánh Desired vs Current", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b4_x + 10.0, body_y + body_h - 93.0, "Áp dụng side-effect nếu lệch", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(b4_x + 8.0, body_y + body_h - 106.0, "4. Lỗi -> Rate-limit retry", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))
    d.add(String(b4_x + 8.0, body_y + body_h - 117.0, "5. Xong: Forget & Done", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Read back arrow from Workers to Local Cache (dashed) passing cleanly through the 14 pt gap between Handler and Workqueue
    read_y = body_y + body_h - 87.0
    draw_arrow(d, b4_x, read_y, b2_x + b2_w, read_y, color=COLOR_INK_MID, width=0.8, head_size=3.2, dashed=True)
    d.add(String(b3_x + b3_w / 2.0, read_y + 3.0, "đọc observation từ cache", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    return d

def build_library_smithy_step_order_drawing(w: float = 261.98, h: float = 362.83) -> Drawing:
    """Figure 52: Các step lồng handler trong Smithy middleware stack.

    Năm step tổ chức đường gọi vào bên trong. Deserialize gọi handler HTTP
    trước khi giải mã response; sơ đồ lược bỏ đường response đi ngược ra ngoài các step.
    Đường request và response giữa Deserialize và Transport được tách biệt rõ ràng.
    Exact dimensions: 261.98 x 362.83 pt (Page 555, xref 625).
    """
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="PHỤ LỤC B // HÌNH 52",
        title="5 BƯỚC MIDDLEWARE TRONG SMITHY-GO",
        subtitle="Chuỗi lồng handler tuần tự từ Initialize đến Deserialize",
    )

    footer_top = draw_footer_banner(
        d, w,
        [
            "• Invariant: 5 step lồng nhau; Deserialize bọc lấy",
            "  transport HTTP để giải mã response trả về.",
        ]
    )

    body_y = footer_top + 4.0
    body_h = header_y - body_y - 4.0

    steps = [
        ("1. INITIALIZE STEP", "Kiểm tra hợp lệ tham số đầu vào; nạp default context.", COLOR_BG_CARD),
        ("2. SERIALIZE STEP", "Chuyển struct input thành transport request (HTTP URL/Headers).", COLOR_WHITE),
        ("3. BUILD STEP", "Chuẩn hóa request HTTP (Content-Length, canonical headers).", COLOR_BG_CARD),
        ("4. FINALIZE STEP", "Ký request (AWS SigV4), tính SHA-256 payload checksum.", COLOR_WHITE),
        ("5. DESERIALIZE STEP", "Bọc quanh HTTP client; gọi Do(), nhận response & giải mã.", COLOR_TAG_ACTIVE),
    ]

    card_w = w - 16.0
    card_x = 8.0
    num_steps = len(steps)
    step_gap = 5.0
    trans_h = 36.0
    gap_trans = 14.0

    avail_h = body_h - trans_h - gap_trans
    step_h = (avail_h - (num_steps - 1) * step_gap) / num_steps

    cur_y = body_y + body_h - step_h
    for i, (title, desc, bg_col) in enumerate(steps):
        d.add(Rect(card_x, cur_y, card_w, step_h, fillColor=bg_col, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
        d.add(Rect(card_x + 6.0, cur_y + step_h - 12.0, 100.0, 8.5, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.4, rx=1.0, ry=1.0))
        d.add(String(card_x + 56.0, cur_y + step_h - 9.5, title, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

        # Use wrap_text for word-based glyph wrapping
        wrapped_lines = wrap_text(desc, "BookSans", 6.0, card_w - 16.0)
        line_y = cur_y + 14.0
        for w_line in wrapped_lines[:2]:
            d.add(String(card_x + 8.0, line_y, w_line, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
            line_y -= 8.5

        if i < num_steps - 1:
            draw_arrow(d, card_x + card_w / 2.0, cur_y, card_x + card_w / 2.0, cur_y - step_gap, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

        cur_y -= (step_h + step_gap)

    # Bottom Target: HTTP Client Transport & AWS Service
    trans_y = body_y
    d.add(Rect(card_x, trans_y, card_w, trans_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=1.0, rx=2, ry=2))
    d.add(String(card_x + 8.0, trans_y + trans_h - 11.0, "HTTP Transport & Remote Service Endpoint:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 8.0, trans_y + trans_h - 21.0, "• RoundTripper thực hiện kết nối TLS và truyền byte", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 8.0, trans_y + trans_h - 31.0, "• Nhận HTTP raw response -> Trả ngược về Deserialize Step", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Parallel Request and Response arrows between Step 5 and Transport
    step5_bot = trans_y + trans_h + gap_trans
    trans_top = trans_y + trans_h

    # Left: Request arrow (downward)
    req_x = card_x + card_w / 2.0 - 40.0
    draw_arrow(d, req_x, step5_bot, req_x, trans_top, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String(req_x - 4.0, (step5_bot + trans_top) / 2.0 - 2.0, "Client.Do()", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="end"))

    # Right: Response arrow (upward)
    resp_x = card_x + card_w / 2.0 + 40.0
    draw_arrow(d, resp_x, trans_top, resp_x, step5_bot, color=COLOR_INK_DARK, width=0.8, head_size=3.0)
    d.add(String(resp_x + 4.0, (step5_bot + trans_top) / 2.0 - 2.0, "Raw Response", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="start"))

    return d

def build_collector_pipeline_drawing(w: float = 337.01, h: float = 362.83) -> Drawing:
    """Figure 53: Ba vai trò trong pipeline OpenTelemetry Collector.

    Pipeline nối receiver, các processor được cấu hình và exporter.
    Fan-in, fan-out, queue và retry phụ thuộc cách nối component cùng cấu hình cụ thể.
    Exact dimensions: 337.01 x 362.83 pt (Page 560, xref 631).
    """
    register_fonts()
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="PHỤ LỤC B // HÌNH 53",
        title="PIPELINE OPENTELEMETRY COLLECTOR",
        subtitle="3 Thành phần chính: Receivers -> Processors -> Exporters",
    )

    draw_footer_banner(
        d, w,
        "• Invariant: Dữ liệu chuẩn hóa pdata; fan-in, batching, retry và routing phụ thuộc hoàn toàn vào cấu hình pipeline."
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    # 3 Horizontal Stages:
    # 1. Receivers (top)
    # 2. Processors (mid)
    # 3. Exporters (bottom)
    stage_w = w - 16.0
    stage_x = 8.0
    gap = 8.0
    stage_h = (body_h - 2 * gap) / 3.0

    # STAGE 1: RECEIVERS
    s1_y = body_y + 2 * (stage_h + gap)
    d.add(Rect(stage_x, s1_y, stage_w, stage_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(stage_x + 6.0, s1_y + stage_h - 13.0, 110.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(stage_x + 61.0, s1_y + stage_h - 10.5, "1. RECEIVERS (FAN-IN)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # 3 receiver cards side by side
    rc_w = (stage_w - 18.0) / 3.0
    r_labels = [("OTLP/gRPC", ":4317"), ("OTLP/HTTP", ":4318"), ("Prometheus / Zipkin", "Scrape / Ingest")]
    for j, (proto, port) in enumerate(r_labels):
        rx = stage_x + 6.0 + j * (rc_w + 3.0)
        d.add(Rect(rx, s1_y + 6.0, rc_w, stage_h - 24.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(String(rx + 6.0, s1_y + stage_h - 25.0, proto, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(rx + 6.0, s1_y + stage_h - 37.0, port, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))
        d.add(String(rx + 6.0, s1_y + 12.0, "Parse -> pdata", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Arrow down s1 -> s2
    draw_arrow(d, stage_x + stage_w / 2.0, s1_y, stage_x + stage_w / 2.0, s1_y - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.6)
    d.add(String(stage_x + stage_w / 2.0 + 8.0, s1_y - gap / 2.0 - 2.0, "pdata (Traces, Metrics, Logs)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    # STAGE 2: PROCESSORS
    s2_y = body_y + stage_h + gap
    d.add(Rect(stage_x, s2_y, stage_w, stage_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(stage_x + 6.0, s2_y + stage_h - 13.0, 130.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(stage_x + 71.0, s2_y + stage_h - 10.5, "2. PROCESSORS (CHUỖI BIẾN ĐỔI)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    proc_labels = [
        ("Memory Limiter", "Chặn OOM, drop data khi bộ nhớ vượt ngưỡng an toàn"),
        ("Batch Processor", "Gom nhóm theo kích thước (send_batch_size) hoặc timeout"),
        ("Resource / Transform", "Thêm nhãn cluster/env, chuẩn hóa telemetry attributes"),
    ]
    p_h = (stage_h - 26.0) / 3.0
    for k, (p_title, p_desc) in enumerate(proc_labels):
        py = s2_y + stage_h - 24.0 - (k + 1) * p_h + 2.0
        d.add(Rect(stage_x + 6.0, py, stage_w - 12.0, p_h - 2.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
        d.add(String(stage_x + 12.0, py + p_h - 8.0, f"• {p_title}:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(stage_x + 84.0, py + p_h - 8.0, p_desc, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrow down s2 -> s3
    draw_arrow(d, stage_x + stage_w / 2.0, s2_y, stage_x + stage_w / 2.0, s2_y - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.6)
    d.add(String(stage_x + stage_w / 2.0 + 8.0, s2_y - gap / 2.0 - 2.0, "Processed batches", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    # STAGE 3: EXPORTERS
    s3_y = body_y
    d.add(Rect(stage_x, s3_y, stage_w, stage_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(stage_x + 6.0, s3_y + stage_h - 13.0, 115.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(stage_x + 63.5, s3_y + stage_h - 10.5, "3. EXPORTERS (FAN-OUT)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Left box: Queuing & Retry
    d.add(Rect(stage_x + 6.0, s3_y + 6.0, 110.0, stage_h - 24.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(stage_x + 10.0, s3_y + stage_h - 26.0, "Queue & Retry Layer:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(stage_x + 10.0, s3_y + stage_h - 38.0, "• Bộ đệm RAM / Persistent", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(stage_x + 10.0, s3_y + stage_h - 49.0, "• Exponential backoff", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(stage_x + 10.0, s3_y + stage_h - 60.0, "• Bỏ gói khi retry vượt hạn", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Right destinations
    dst_w = stage_w - 128.0
    d.add(Rect(stage_x + 120.0, s3_y + 6.0, dst_w, stage_h - 24.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(stage_x + 126.0, s3_y + stage_h - 26.0, "Hạ tầng lưu trữ đích (Backends):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(stage_x + 126.0, s3_y + stage_h - 38.0, "• OTLP Exporter (Tempo / Jaeger / Cloud Tracing)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(stage_x + 126.0, s3_y + stage_h - 49.0, "• Prometheus Remote Write (Mimir / Cortex)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(stage_x + 126.0, s3_y + stage_h - 60.0, "• Logging Exporter (Loki / Elasticsearch / S3)", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))

    return d


# ----------------------------------------------------------------------
# 22. Appendix B — Figure 54: Containerd Shim Boundary (434.69 x 362.83 pt)
# ----------------------------------------------------------------------
def build_containerd_shim_boundary_drawing(w: float = 434.69, h: float = 362.83) -> Drawing:
    """Figure 54: Ranh giới daemon, runtime shim và container task.

    Daemon giao tiếp với shim qua endpoint; shim quản lý task qua runtime được chọn.
    Ranh giới tiến trình này không bảo đảm mọi failure của daemon đều vô hại với workload.
    Exact dimensions: 434.69 x 362.83 pt (Page 563, xref 635).
    """
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="PHỤ LỤC B // HÌNH 54",
        title="RANH GIỚI TIẾN TRÌNH: DAEMON, SHIM VÀ CONTAINER TASK",
        subtitle="containerd daemon -> containerd-shim-v2 -> OCI runtime (runc) -> Container",
    )

    draw_footer_banner(
        d, w,
        "• Invariant: Shim cô lập task khỏi daemon lifecycle (live-restore); daemon crash không kéo chết container nhưng không vô hại tuyệt đối."
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    # 3 Main Columns:
    # Col 1: 120 pt, Gap 1: 24 pt, Col 2: 126 pt, Gap 2: 24 pt, Col 3: 120 pt
    # Total = 8 + 120 + 24 + 126 + 24 + 120 = 422 pt (w = 434.69 pt)
    c1_w = 120.0
    c2_w = 126.0
    c3_w = 120.0
    gap = 24.0

    c1_x = 10.0
    c2_x = c1_x + c1_w + gap  # 154.0
    c3_x = c2_x + c2_w + gap  # 304.0

    # TIER 1: DAEMON
    d.add(Rect(c1_x, body_y, c1_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c1_x + 6.0, body_y + body_h - 13.0, 105.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c1_x + 58.5, body_y + body_h - 10.5, "1. CONTAINERD DAEMON", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(c1_x + 6.0, body_y + 8.0, c1_w - 12.0, body_h - 26.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c1_x + 10.0, body_y + body_h - 28.0, "Daemon Trách nhiệm:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 42.0, "• Nhận gRPC từ CRI/Kubelet", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 55.0, "• Image pull, giải nén layers", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 10.0, body_y + body_h - 68.0, "• Snapshotter (overlayfs)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 10.0, body_y + body_h - 81.0, "• Metadata store (BoltDB)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 10.0, body_y + body_h - 100.0, "Khởi tạo Shim:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 114.0, "• Fork/exec shim-v2 process", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 127.0, "• Đọc bootstrap socket path", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 10.0, body_y + body_h - 140.0, "• Kết nối ttrpc endpoint", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + 14.0, "• Live-restore: nếu bật cấu hình", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow c1 -> c2 (ttrpc IPC) - cleanly centered inside gap 1
    arrow1_y = body_y + body_h / 2.0
    draw_arrow(d, c1_x + c1_w, arrow1_y, c2_x, arrow1_y, color=COLOR_INK_DARK, width=1.0, head_size=3.6)
    d.add(String((c1_x + c1_w + c2_x) / 2.0, arrow1_y + 4.0, "ttrpc", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # TIER 2: SHIM
    d.add(Rect(c2_x, body_y, c2_w, body_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c2_x + 6.0, body_y + body_h - 13.0, 114.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c2_x + 63.0, body_y + body_h - 10.5, "2. CONTAINERD-SHIM-V2", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(c2_x + 6.0, body_y + 8.0, c2_w - 12.0, body_h - 26.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c2_x + 10.0, body_y + body_h - 28.0, "Vai trò Shim (Tiến trình riêng):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 10.0, body_y + body_h - 42.0, "• Quản lý 1 hoặc nhóm task", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 10.0, body_y + body_h - 55.0, "  (tùy cấu hình runtime v2)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 10.0, body_y + body_h - 68.0, "• Giữ STDIO pipes và PTY", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 10.0, body_y + body_h - 81.0, "• Theo dõi exit code container", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 10.0, body_y + body_h - 100.0, "Giao tiếp OCI Runtime:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 10.0, body_y + body_h - 114.0, "• Gọi runc create / runc start", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 10.0, body_y + body_h - 127.0, "• runc thoát sau khi khởi tạo", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 10.0, body_y + body_h - 140.0, "• Shim làm subreaper tránh", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 10.0, body_y + 14.0, "  zombie process trong OS", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow c2 -> c3 (runc OCI) - cleanly centered inside gap 2
    arrow2_y = body_y + body_h / 2.0
    draw_arrow(d, c2_x + c2_w, arrow2_y, c3_x, arrow2_y, color=COLOR_INK_DARK, width=1.0, head_size=3.6)
    d.add(String((c2_x + c2_w + c3_x) / 2.0, arrow2_y + 4.0, "runc", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # TIER 3: CONTAINER TASK
    d.add(Rect(c3_x, body_y, c3_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c3_x + 6.0, body_y + body_h - 13.0, 108.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c3_x + 60.0, body_y + body_h - 10.5, "3. CONTAINER WORKLOAD", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(c3_x + 6.0, body_y + 8.0, c3_w - 12.0, body_h - 26.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c3_x + 10.0, body_y + body_h - 28.0, "Linux Namespaces:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 42.0, "• PID, Mount, Net, IPC, UTS", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 55.0, "• Cgroups v2 (CPU/RAM limits)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 10.0, body_y + body_h - 75.0, "Container Process (PID 1):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 89.0, "• Ứng dụng Go/HTTP production", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 102.0, "• Thực thi logic nghiệp vụ", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 10.0, body_y + body_h - 120.0, "Ranh giới sự cố:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 133.0, "• Daemon chết: task vẫn chạy", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + 14.0, "• Shim chết: task bị mồ côi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    return d

def build_grpc_client_balancing_drawing(w: float = 476.22, h: float = 255.70) -> Drawing:
    """Figure 55: Resolver và balancer trong gRPC client.

    Resolver cung cấp endpoint, balancer quản lý SubConn và picker chọn đường cho RPC.
    Ba backend cùng policy round_robin là cấu hình minh họa, không phải mặc định của mọi ClientConn.
    Exact dimensions: 476.22 x 255.70 pt (Page 572, xref 645).
    """
    register_fonts()
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="PHỤ LỤC B // HÌNH 55",
        title="ĐIỀU HƯỚNG VÀ CÂN BẰNG TẢI CLIENT-SIDE TRONG GRPC",
        subtitle="Resolver cung cấp addresses -> Balancer quản lý SubConn -> Picker định tuyến RPC",
    )

    draw_footer_banner(
        d, w,
        "• Invariant: Resolver phân giải địa chỉ; Balancer quản lý SubConn; Picker chọn đường RPC tức thời theo trạng thái kết nối thực tế."
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    # 4 Architecture Columns:
    # 1. Target URI & Resolver (w = 110 pt)
    # 2. Balancer & SubConns (w = 125 pt)
    # 3. Picker (w = 85 pt)
    # 4. Backend Servers (w = 115 pt)
    c1_w = 110.0
    c2_w = 125.0
    c3_w = 85.0
    c4_w = 115.0

    c1_x = 8.0
    c2_x = c1_x + c1_w + 6.0
    c3_x = c2_x + c2_w + 6.0
    c4_x = c3_x + c3_w + 6.0

    # Col 1: Target URI & Resolver
    d.add(Rect(c1_x, body_y, c1_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c1_x + 5.0, body_y + body_h - 13.0, 100.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c1_x + 55.0, body_y + body_h - 10.5, "1. RESOLVER (PHÂN GIẢI)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(c1_x + 5.0, body_y + body_h - 60.0, c1_w - 10.0, 44.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c1_x + 10.0, body_y + body_h - 25.0, "Target URI:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 36.0, "dns:///my-svc:8080", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 48.0, "hoặc k8s:///my-svc", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_MID))

    d.add(Rect(c1_x + 5.0, body_y + 8.0, c1_w - 10.0, body_h - 74.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c1_x + 10.0, body_y + body_h - 76.0, "Name Resolver:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 88.0, "• Phân giải DNS / Headless", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 99.0, "• Trả danh sách endpoint:", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c1_x + 14.0, body_y + body_h - 110.0, "[IP1, IP2, IP3]", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c1_x + 10.0, body_y + body_h - 122.0, "• Kèm Service Config", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrow c1 -> c2
    draw_arrow(d, c1_x + c1_w, body_y + body_h / 2.0, c2_x, body_y + body_h / 2.0, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # Col 2: Balancer & SubConns
    d.add(Rect(c2_x, body_y, c2_w, body_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c2_x + 5.0, body_y + body_h - 13.0, 115.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c2_x + 62.5, body_y + body_h - 10.5, "2. BALANCER (SUBCONNS)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(String(c2_x + 8.0, body_y + body_h - 26.0, "Policy: round_robin (minh họa)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    subconns = [
        ("SubConn 1 (IP1)", "State: READY", COLOR_WHITE),
        ("SubConn 2 (IP2)", "State: READY", COLOR_WHITE),
        ("SubConn 3 (IP3)", "State: TRANSIENT_FAIL", COLOR_BG_CARD),
    ]
    sc_h = (body_h - 48.0) / 3.0
    for m, (sc_name, sc_state, sc_bg) in enumerate(subconns):
        sc_y = body_y + body_h - 38.0 - (m + 1) * sc_h + 2.0
        d.add(Rect(c2_x + 6.0, sc_y, c2_w - 12.0, sc_h - 3.0, fillColor=sc_bg, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(String(c2_x + 12.0, sc_y + sc_h - 12.0, sc_name, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(c2_x + 12.0, sc_y + sc_h - 22.0, sc_state, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrow c2 -> c3 (update picker)
    draw_arrow(d, c2_x + c2_w, body_y + body_h / 2.0, c3_x, body_y + body_h / 2.0, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # Col 3: Picker
    d.add(Rect(c3_x, body_y, c3_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c3_x + 5.0, body_y + body_h - 13.0, 75.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c3_x + 42.5, body_y + body_h - 10.5, "3. PICKER", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(c3_x + 5.0, body_y + 8.0, c3_w - 10.0, body_h - 26.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c3_x + 10.0, body_y + body_h - 28.0, "Hàm Pick():", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 42.0, "• Được gọi mỗi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 53.0, "  khi có RPC mới", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 68.0, "• Chỉ chọn SubConn", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 79.0, "  đang READY", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c3_x + 10.0, body_y + body_h - 94.0, "• Loại trừ IP3 lỗi", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c3_x + 10.0, body_y + 16.0, "• Không block kênh", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow c3 -> c4
    draw_arrow(d, c3_x + c3_w, body_y + body_h / 2.0, c4_x, body_y + body_h / 2.0, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # Col 4: Backends
    d.add(Rect(c4_x, body_y, c4_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c4_x + 5.0, body_y + body_h - 13.0, 105.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c4_x + 57.5, body_y + body_h - 10.5, "4. BACKEND SERVERS", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    backends = [
        ("Backend 1 (IP1)", "Nhận RPC #1, #3...", COLOR_WHITE),
        ("Backend 2 (IP2)", "Nhận RPC #2, #4...", COLOR_WHITE),
        ("Backend 3 (IP3)", "Hỏng mạng / Unreachable", COLOR_BG_CARD),
    ]
    b_h = (body_h - 26.0) / 3.0
    for n, (b_name, b_desc, b_bg) in enumerate(backends):
        by = body_y + body_h - 24.0 - (n + 1) * b_h + 2.0
        d.add(Rect(c4_x + 5.0, by, c4_w - 10.0, b_h - 3.0, fillColor=b_bg, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
        d.add(String(c4_x + 10.0, by + b_h - 12.0, b_name, fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(c4_x + 10.0, by + b_h - 22.0, b_desc, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    return d


# ----------------------------------------------------------------------
# 24. Appendix B — Figure 56: Cobra Hook Order (476.22 x 354.37 pt)
# ----------------------------------------------------------------------
def build_cobra_hook_order_drawing(w: float = 476.22, h: float = 354.37) -> Drawing:
    """Figure 56: Thứ tự hook và đường trả lỗi của Cobra.

    Chỉ các hook được chọn mới chạy; hook có thể vắng.
    Lỗi từ hook E hoặc RunE ngắt đường chạy và lan truyền về caller qua Execute().
    Exact dimensions: 476.22 x 354.37 pt (Page 582, xref 656).
    """
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="PHỤ LỤC B // HÌNH 56",
        title="THỨ TỰ HOOK VÀ CƠ CHẾ LAN TRUYỀN LỖI TRONG COBRA CLI",
        subtitle="PersistentPreRun[E] -> PreRun[E] -> Run[E] -> PostRun[E] -> PersistentPostRun[E]",
    )

    draw_footer_banner(
        d, w,
        "• Invariant: Thứ tự hook xác định; lỗi ở bất kỳ hook E nào ngắt chuỗi thực thi và trả về caller qua Execute(), không tự kết thúc tiến trình OS."
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    c1_w = 265.0
    c2_w = w - 16.0 - c1_w - 8.0
    c1_x = 8.0
    c2_x = c1_x + c1_w + 8.0

    # LEFT: PIPELINE OF 6 STEPS
    d.add(Rect(c1_x, body_y, c1_w, body_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c1_x + 6.0, body_y + body_h - 13.0, 140.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c1_x + 76.0, body_y + body_h - 10.5, "CHUỖI THỰC THI HOOK COBRA", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    steps = [
        ("0. Flag & Arg Parsing", "Phân giải Flags() và PersistentFlags(); validate số lượng args."),
        ("1. PersistentPreRun[E]", "Hook kế thừa từ lệnh cha gần nhất; thiết lập logging/config."),
        ("2. PreRun[E]", "Hook riêng của lệnh con hiện tại; kiểm tra tiền điều kiện."),
        ("3. Run[E] (Core Logic)", "Logic nghiệp vụ chính của lệnh; nơi thực thi tác vụ chính."),
        ("4. PostRun[E]", "Hook dọn dẹp riêng của lệnh con (đóng file, flush telemetry)."),
        ("5. PersistentPostRun[E]", "Hook kết thúc kế thừa từ lệnh cha (báo cáo thời gian, audit)."),
    ]

    num_s = len(steps)
    gap_s = 5.0
    avail_hs = body_h - 26.0
    step_hs = (avail_hs - (num_s - 1) * gap_s) / num_s

    s_y = body_y + body_h - 20.0 - step_hs
    for idx, (s_name, s_detail) in enumerate(steps):
        bg = COLOR_WHITE if idx != 3 else COLOR_TAG_ACTIVE
        d.add(Rect(c1_x + 8.0, s_y, c1_w - 16.0, step_hs, fillColor=bg, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.6, rx=1.5, ry=1.5))
        d.add(String(c1_x + 14.0, s_y + step_hs - 10.0, s_name, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
        d.add(String(c1_x + 14.0, s_y + 6.0, s_detail, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

        if idx < num_s - 1:
            draw_arrow(d, c1_x + (c1_w - 16.0) / 2.0 + 8.0, s_y, c1_x + (c1_w - 16.0) / 2.0 + 8.0, s_y - gap_s, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

        s_y -= (step_hs + gap_s)

    # RIGHT: RULES & ERROR PROPAGATION
    d.add(Rect(c2_x, body_y, c2_w, body_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(c2_x + 6.0, body_y + body_h - 13.0, 160.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(c2_x + 86.0, body_y + body_h - 10.5, "QUY TẮC KẾ THỪA & LAN TRUYỀN LỖI", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    # Box 1: Error Propagation
    d.add(Rect(c2_x + 6.0, body_y + body_h - 96.0, c2_w - 12.0, 78.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c2_x + 10.0, body_y + body_h - 26.0, "Cơ chế lan truyền lỗi (Error Propagation):", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 10.0, body_y + body_h - 38.0, "• Hook dạng E nhận (cmd, args) error", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 10.0, body_y + body_h - 50.0, "• Khi hook trả về error != nil:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 14.0, body_y + body_h - 62.0, "-> Ngắt ngay chuỗi hook kế tiếp", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 14.0, body_y + body_h - 73.0, "-> Bỏ qua Run[E] và mọi PostRun phía sau", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 14.0, body_y + body_h - 84.0, "-> Trả lỗi về caller qua Execute() / ExecuteC()", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))

    # Box 2: Inheritance
    d.add(Rect(c2_x + 6.0, body_y + 8.0, c2_w - 12.0, body_h - 110.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(c2_x + 10.0, body_y + body_h - 112.0, "Kế thừa Persistent Hooks:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 10.0, body_y + body_h - 124.0, "• Cobra tìm cha gần nhất có khai báo hook", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 10.0, body_y + body_h - 136.0, "• Chỉ MỘT Persistent hook chạy (không gộp)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(c2_x + 10.0, body_y + body_h - 148.0, "• Nếu lệnh con tự khai báo PersistentPreRun,", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 14.0, body_y + body_h - 159.0, "hook của lệnh cha bị ghi đè hoàn toàn", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(c2_x + 10.0, body_y + 14.0, "• Caller quyết định in lỗi hoặc thoát OS", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    return d

def build_viper_value_precedence_drawing(w: float = 414.95, h: float = 362.83) -> Drawing:
    """Figure 57: Thứ tự ưu tiên nguồn giá trị trong Viper.

    Với một key, Viper ưu tiên nguồn phía trên khi nguồn ấy có giá trị hợp lệ theo cấu hình.
    Đây là thứ tự ưu tiên khi đọc, không phải lịch nạp file.
    Exact dimensions: 414.95 x 362.83 pt (Page 584, xref 659).
    """
    register_fonts()
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="PHỤ LỤC B // HÌNH 57",
        title="THỨ TỰ ƯU TIÊN NGUỒN CẤU HÌNH TRONG VIPER",
        subtitle="Precedence Hierarchy khi đọc Get(key): Từ cao nhất xuống thấp nhất",
    )

    draw_footer_banner(
        d, w,
        "• Invariant: Viper đọc theo thứ tự ưu tiên; nguồn phía trên có giá trị hợp lệ sẽ che khuất hoàn toàn mọi nguồn phía dưới."
    )

    body_y = 26.0
    body_h = header_y - body_y - 6.0

    # 6 Precedence Layers from Top (Highest) to Bottom (Lowest)
    layers = [
        ("1. EXPLICIT SET (GÁN TRỰC TIẾP)", "viper.Set(key, value) qua code Go — Luôn có quyền cao nhất.", COLOR_TAG_ACTIVE),
        ("2. COMMAND-LINE FLAGS", "Cờ dòng lệnh gắn qua viper.BindPFlag() hoặc pflag — Đè env và config.", COLOR_WHITE),
        ("3. ENVIRONMENT VARIABLES", "Biến môi trường (AutomaticEnv, BindEnv) — Đè file config trên đĩa.", COLOR_BG_CARD),
        ("4. CONFIGURATION FILE", "File nạp trên đĩa (config.yaml, .json, .toml) qua ReadInConfig().", COLOR_WHITE),
        ("5. KEY / VALUE STORE", "Nguồn cấu hình từ xa (etcd, Consul) qua remote provider.", COLOR_BG_CARD),
        ("6. DEFAULT VALUES", "Giá trị mặc định đăng ký qua viper.SetDefault() — Thấp nhất.", COLOR_WHITE),
    ]

    card_w = w - 16.0
    card_x = 8.0
    num_l = len(layers)
    gap_l = 6.0
    layer_h = (body_h - (num_l - 1) * gap_l) / num_l

    ly = body_y + body_h - layer_h
    for idx, (l_title, l_desc, bg_col) in enumerate(layers):
        d.add(Rect(card_x, ly, card_w, layer_h, fillColor=bg_col, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
        
        # Priority tag badge
        p_badge = "ƯU TIÊN CAO NHẤT" if idx == 0 else ("ƯU TIÊN THẤP NHẤT" if idx == num_l - 1 else f"CẤP ĐỘ {idx + 1}")
        d.add(Rect(card_x + 8.0, ly + layer_h - 13.0, 85.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.4, rx=1.0, ry=1.0))
        d.add(String(card_x + 50.5, ly + layer_h - 10.5, p_badge, fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

        d.add(String(card_x + 100.0, ly + layer_h - 10.5, l_title, fontName="BookSansBold", fontSize=6.2, fillColor=COLOR_INK_DARK))
        d.add(String(card_x + 14.0, ly + 8.0, l_desc, fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

        if idx < num_l - 1:
            draw_arrow(d, card_x + card_w - 24.0, ly, card_x + card_w - 24.0, ly - gap_l, color=COLOR_INK_DARK, width=0.8, head_size=3.0)

        ly -= (layer_h + gap_l)

    return d


# ----------------------------------------------------------------------
# 26. Appendix B — Figure 58: Agent Mailbox Contract (280.79 x 362.83 pt)
# ----------------------------------------------------------------------
def build_agent_mailbox_contract_drawing(w: float = 280.79, h: float = 362.83) -> Drawing:
    """Figure 58: Giao tiếp qua mailbox theo contract của ứng dụng.

    Mailbox là mental model của policy giao tiếp. Go và framework không tự cấm
    direct call hay chia sẻ pointer giữa các agent.
    Send vào buffered channel block khi đầy; non-blocking cần select/default.
    Exact dimensions: 280.79 x 362.83 pt (Page 603, xref 679).
    """
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.5, rx=3, ry=3))

    header_y = draw_header_banner(
        d, w, h,
        tag="PHỤ LỤC B // HÌNH 58",
        title="KHẾ ƯỚC GIAO TIẾP MAILBOX TRONG AGENT",
        subtitle="Mental model của Policy giao tiếp; Go không tự cấm chia sẻ con trỏ.",
    )

    footer_top = draw_footer_banner(
        d, w,
        [
            "• Invariant: Mailbox là khế ước kiến trúc; send có thể",
            "  block khi đầy; Go không tự cấm con trỏ chia sẻ.",
        ]
    )

    body_y = footer_top + 4.0
    body_h = header_y - body_y - 4.0

    card_w = w - 16.0
    card_x = 8.0

    gap = 8.0
    a1_h = 76.0
    m_h = 70.0
    a2_h = body_h - a1_h - m_h - 2 * gap

    # STAGE 1: AGENT A (SENDER)
    a1_y = body_y + body_h - a1_h
    d.add(Rect(card_x, a1_y, card_w, a1_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 6.0, a1_y + a1_h - 13.0, 100.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(card_x + 56.0, a1_y + a1_h - 10.5, "1. AGENT A (SENDER)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(card_x + 6.0, a1_y + 6.0, card_w - 12.0, a1_h - 23.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 10.0, a1_y + a1_h - 25.0, "Tác nhân gửi thông điệp:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, a1_y + a1_h - 37.0, "• Tạo tin nhắn dạng struct value (bất biến)", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, a1_y + a1_h - 48.0, "• KHÔNG gửi con trỏ chia sẻ (*Data)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, a1_y + 10.0, "• Gửi qua channel: block nếu buffer đầy", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))

    # Arrow down a1 -> mailbox
    draw_arrow(d, card_x + card_w / 2.0, a1_y, card_x + card_w / 2.0, a1_y - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # STAGE 2: MAILBOX CHANNEL
    my = a1_y - gap - m_h
    d.add(Rect(card_x, my, card_w, m_h, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 6.0, my + m_h - 13.0, 110.0, 9.0, fillColor=COLOR_TAG_ACTIVE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(card_x + 61.0, my + m_h - 10.5, "2. MAILBOX (FIFO QUEUE)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(card_x + 6.0, my + 6.0, card_w - 12.0, m_h - 23.0, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER_DARK, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 10.0, my + m_h - 25.0, "Kênh đệm có giới hạn: chan Message", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, my + m_h - 37.0, "• Hàng đợi độc quyền thuộc quyền sở hữu B", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, my + m_h - 48.0, "• Non-blocking yêu cầu select/default", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, my + 10.0, "• Go runtime không tự cấm direct call", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    # Arrow down mailbox -> a2
    draw_arrow(d, card_x + card_w / 2.0, my, card_x + card_w / 2.0, my - gap, color=COLOR_INK_DARK, width=1.0, head_size=3.6)

    # STAGE 3: AGENT B (RECEIVER)
    a2_y = body_y
    d.add(Rect(card_x, a2_y, card_w, a2_h, fillColor=COLOR_BG_CARD, strokeColor=COLOR_BORDER, strokeWidth=0.8, rx=2, ry=2))
    d.add(Rect(card_x + 6.0, a2_y + a2_h - 13.0, 110.0, 9.0, fillColor=COLOR_TAG_BG, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.0, ry=1.0))
    d.add(String(card_x + 61.0, a2_y + a2_h - 10.5, "3. AGENT B (RECEIVER)", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK, textAnchor="middle"))

    d.add(Rect(card_x + 6.0, a2_y + 6.0, card_w - 12.0, a2_h - 23.0, fillColor=COLOR_WHITE, strokeColor=COLOR_BORDER, strokeWidth=0.5, rx=1.5, ry=1.5))
    d.add(String(card_x + 10.0, a2_y + a2_h - 25.0, "Vòng lặp tiêu thụ thông điệp:", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, a2_y + a2_h - 37.0, "• for msg := range agent.mailbox { ... }", fontName="BookMono", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, a2_y + a2_h - 48.0, "• Xử lý tuần tự: loại trừ data race trên state", fontName="BookSansBold", fontSize=6.0, fillColor=COLOR_INK_DARK))
    d.add(String(card_x + 10.0, a2_y + a2_h - 60.0, "• Trạng thái nội bộ (Isolated State) được cô lập", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MID))
    d.add(String(card_x + 10.0, a2_y + 10.0, "• An toàn là do kỷ luật thiết kế, không do Go tự ép", fontName="BookSans", fontSize=6.0, fillColor=COLOR_INK_MUTED))

    return d

# ======================================================================
# DIAGRAM SPECS REGISTRY (ALL 26 TECHNICAL DIAGRAMS ACROSS THE ENTIRE BOOK)
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
        "title": "Năm cấp độ trưởng thành của Kubernetes Operator",
        "page": 404,
        "xref": 460,
        "w_pt": 476.22,
        "h_pt": 254.61,
    },
    "operator-manager-boundaries.png": {
        "builder": build_operator_manager_boundaries_drawing,
        "chapter": 23,
        "figure": 39,
        "title": "Cấu trúc Controller-Runtime Manager và ranh giới Reconciler",
        "page": 405,
        "xref": 462,
        "w_pt": 473.72,
        "h_pt": 362.83,
    },
    "operator-finalizer-lifecycle.png": {
        "builder": build_operator_finalizer_lifecycle_drawing,
        "chapter": 23,
        "figure": 40,
        "title": "Vòng đời dọn dẹp tài nguyên với Kubernetes Finalizer",
        "page": 410,
        "xref": 468,
        "w_pt": 342.25,
        "h_pt": 362.83,
    },
    "aws-credentials-resolution.png": {
        "builder": build_aws_credentials_resolution_drawing,
        "chapter": 24,
        "figure": 41,
        "title": "Bản đồ nguồn định danh AWS SDK for Go",
        "page": 426,
        "xref": 485,
        "w_pt": 264.41,
        "h_pt": 362.83,
    },
    "smithy-request-response.png": {
        "builder": build_smithy_request_response_drawing,
        "chapter": 24,
        "figure": 42,
        "title": "Vòng đời Request-Response trong Smithy Middleware Stack",
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
        "title": "Ranh giới kỹ thuật giữa Git Core Engine và GitHub Platform",
        "page": 443,
        "xref": 504,
        "w_pt": 278.59,
        "h_pt": 362.83,
    },
    "webhook-hmac-verification.png": {
        "builder": build_webhook_hmac_verification_drawing,
        "chapter": 25,
        "figure": 44,
        "title": "Quy trình xác thực chữ ký HMAC-SHA256 cho GitHub Webhook",
        "page": 444,
        "xref": 506,
        "w_pt": 407.82,
        "h_pt": 362.83,
    },
    "webhook-delivery-deduplication.png": {
        "builder": build_webhook_delivery_deduplication_drawing,
        "chapter": 25,
        "figure": 45,
        "title": "Mô hình Deduplication và chống Replay Webhook theo Delivery ID",
        "page": 447,
        "xref": 510,
        "w_pt": 462.12,
        "h_pt": 362.83,
    },
    "supply-chain-policy-evidence.png": {
        "builder": build_supply_chain_policy_evidence_drawing,
        "chapter": 26,
        "figure": 46,
        "title": "Cổng kiểm soát bằng chứng chuỗi cung ứng phần mềm",
        "page": 465,
        "xref": 529,
        "w_pt": 214.51,
        "h_pt": 362.83,
    },
    "vulnerability-call-reachability.png": {
        "builder": build_vulnerability_call_reachability_drawing,
        "chapter": 26,
        "figure": 47,
        "title": "Phân biệt phụ thuộc bị ảnh hưởng và đường gọi tới ký hiệu tổn thương",
        "page": 468,
        "xref": 533,
        "w_pt": 476.22,
        "h_pt": 330.88,
    },
    "container-tag-digest.png": {
        "builder": build_container_tag_digest_drawing,
        "chapter": 26,
        "figure": 48,
        "title": "Bản chất Container Tag vs Digest: Con trỏ đổi đích vs Mã băm nội dung",
        "page": 470,
        "xref": 536,
        "w_pt": 476.22,
        "h_pt": 327.02,
    },
    # Group 4: Figures 49 and 50 (Chapters 27, 29)
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
        "title": "Luồng đề xuất, kiểm chứng, phê duyệt, hành động và quan sát",
        "page": 544,
        "xref": 612,
        "w_pt": 476.22,
        "h_pt": 260.59,
    },
    # Group 5: Figures 51 to 58 (Appendix B: DevOps Library Atlas)
    "library-informer-data-path.png": {
        "builder": build_library_informer_data_path_drawing,
        "chapter": 30,
        "figure": 51,
        "title": "Đường observation và khóa công việc trong informer",
        "page": 551,
        "xref": 620,
        "w_pt": 476.22,
        "h_pt": 265.65,
    },
    "library-smithy-step-order.png": {
        "builder": build_library_smithy_step_order_drawing,
        "chapter": 30,
        "figure": 52,
        "title": "Các step lồng handler trong Smithy",
        "page": 555,
        "xref": 625,
        "w_pt": 261.98,
        "h_pt": 362.83,
    },
    "collector-pipeline.png": {
        "builder": build_collector_pipeline_drawing,
        "chapter": 30,
        "figure": 53,
        "title": "Ba vai trò trong pipeline OpenTelemetry Collector",
        "page": 560,
        "xref": 631,
        "w_pt": 337.01,
        "h_pt": 362.83,
    },
    "containerd-shim-boundary.png": {
        "builder": build_containerd_shim_boundary_drawing,
        "chapter": 30,
        "figure": 54,
        "title": "Ranh giới daemon, runtime shim và container task",
        "page": 563,
        "xref": 635,
        "w_pt": 434.69,
        "h_pt": 362.83,
    },
    "grpc-client-balancing.png": {
        "builder": build_grpc_client_balancing_drawing,
        "chapter": 30,
        "figure": 55,
        "title": "Resolver và balancer trong gRPC client",
        "page": 572,
        "xref": 645,
        "w_pt": 476.22,
        "h_pt": 255.70,
    },
    "cobra-hook-order.png": {
        "builder": build_cobra_hook_order_drawing,
        "chapter": 30,
        "figure": 56,
        "title": "Thứ tự hook và đường trả lỗi của Cobra",
        "page": 582,
        "xref": 656,
        "w_pt": 476.22,
        "h_pt": 354.37,
    },
    "viper-value-precedence.png": {
        "builder": build_viper_value_precedence_drawing,
        "chapter": 30,
        "figure": 57,
        "title": "Thứ tự ưu tiên nguồn giá trị trong Viper",
        "page": 584,
        "xref": 659,
        "w_pt": 414.95,
        "h_pt": 362.83,
    },
    "agent-mailbox-contract.png": {
        "builder": build_agent_mailbox_contract_drawing,
        "chapter": 30,
        "figure": 58,
        "title": "Giao tiếp qua mailbox theo contract của ứng dụng",
        "page": 603,
        "xref": 679,
        "w_pt": 280.79,
        "h_pt": 362.83,
    },
}


# ======================================================================
# EXPORT AND AUDIT RUNNER
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
    """Export all 26 technical diagrams to the specified output directory."""
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
        ch_str = f"Ch {spec['chapter']:02d}" if spec['chapter'] <= 29 else "App B"
        print(f"  [PASS] Figure {spec['figure']:02d} ({ch_str}, p.{spec['page']:03d}) -> {filename} ({spec['w_pt']}x{spec['h_pt']} pt)")

    return results


def verify_all_diagram_typography() -> bool:
    """Audit all 26 diagrams for typography, 2-axis canvas bounds, and discrete card padding."""
    all_ok = True
    print(f"\nAuditing typography, 2-axis canvas boundaries, and card geometry across all {len(DIAGRAM_SPECS)} diagrams...")
    print("  [SCOPE] Automated audit:")
    print("          1. Minimum font size >= 6.0 pt across all 26 diagrams.")
    print("          2. Canvas 2-axis containment (margin >= 2.0 pt) across all 26 diagrams.")
    print("             - Horizontal glyph width: exact via TTFont advance metrics (pdfmetrics.stringWidth).")
    print("             - Vertical glyph extent: computed using font face metrics (ascent/descent),")
    print("               with visual cap-height approximated as 0.72 * fontSize.")
    print("          3. Card padding check on active targets (Figures 44, 45, 50):")
    print("             - Discrete container cards verified strictly for padding >= 4.0 pt on all 4 sides")
    print("               (PadL >= 4.0 pt, PadR >= 4.0 pt, PadT(cap) >= 4.0 pt, PadB(baseline) >= 4.0 pt).")
    print("             - No negative tolerance (-0.5 pt) is used.")
    print("  [SCOPE] Visual inspection (manual QA): arrow clearances, sequence lifelines, line crossings, semantics.")

    active_targets = {
        "webhook-hmac-verification.png",
        "webhook-delivery-deduplication.png",
        "change-evidence-gate.png",
    }

    for filename, spec in DIAGRAM_SPECS.items():
        w_pt = spec["w_pt"]
        h_pt = spec["h_pt"]
        drawing = spec["builder"](w=w_pt, h=h_pt)
        strings = []
        rects = []

        def walk(node):
            if isinstance(node, String):
                strings.append(node)
            elif isinstance(node, Rect):
                rects.append(node)
            elif hasattr(node, "contents"):
                for c in node.contents:
                    walk(c)

        walk(drawing)
        if not strings:
            print(f"  [FAIL] {filename}: No text elements found!")
            all_ok = False
            continue

        min_font = min(s.fontSize for s in strings)
        font_ok = min_font >= 6.0

        canvas_failures = []
        box_failures = []
        cand_rects = [r for r in rects if r.width < w_pt - 12.0 and r.height < h_pt - 12.0 and r.width >= 40.0 and r.height >= 14.0]

        # 1. Canvas 2-axis check for all strings
        box_strings = {id(r): [] for r in cand_rects}
        for s in strings:
            txt = s.text
            f_name = s.fontName
            f_size = s.fontSize
            txt_w = stringWidth(txt, f_name, f_size)
            anchor = getattr(s, "textAnchor", "start")
            if anchor == "middle":
                x_left = s.x - txt_w / 2.0
                x_right = s.x + txt_w / 2.0
            elif anchor == "end":
                x_left = s.x - txt_w
                x_right = s.x
            else:
                x_left = s.x
                x_right = s.x + txt_w

            font = pdfmetrics.getFont(f_name)
            descent = (font.face.descent / 1000.0) * f_size
            ascent = (font.face.ascent / 1000.0) * f_size

            y_bot = s.y + descent
            y_top = s.y + ascent

            # Canvas 2-axis check (margin >= 2.0 pt)
            if x_left < 2.0 or x_right > w_pt - 2.0:
                canvas_failures.append(f"'{txt}' X=[{x_left:.1f}, {x_right:.1f}] exceeds canvas [2.0, {w_pt - 2.0:.1f}]")
            if y_bot < 2.0 or y_top > h_pt - 2.0:
                canvas_failures.append(f"'{txt}' Y=[{y_bot:.1f}, {y_top:.1f}] exceeds canvas [2.0, {h_pt - 2.0:.1f}]")

            # Map to candidate box
            if filename in active_targets:
                x_mid = (x_left + x_right) / 2.0
                y_mid = s.y
                enclosing = [r for r in cand_rects if r.x <= x_mid <= r.x + r.width and r.y <= y_mid <= r.y + r.height]
                if enclosing:
                    enclosing.sort(key=lambda r: r.width * r.height)
                    box_strings[id(enclosing[0])].append((s, x_left, x_right))

        # 2. Strict card padding check (>= 4.0 pt) for active targets
        if filename in active_targets:
            for box in cand_rects:
                items = box_strings[id(box)]
                if not items:
                    continue
                min_pad_l = min(xl - box.x for s, xl, xr in items)
                min_pad_r = min((box.x + box.width) - xr for s, xl, xr in items)

                top_item = max(items, key=lambda x: x[0].y)
                bot_item = min(items, key=lambda x: x[0].y)

                cap_h = 0.72 * top_item[0].fontSize
                pad_t = (box.y + box.height) - (top_item[0].y + cap_h)
                pad_b = bot_item[0].y - box.y

                if min_pad_l < 4.0 or min_pad_r < 4.0 or pad_t < 4.0 or pad_b < 4.0:
                    box_failures.append(f"Box ({box.x:.1f},{box.y:.1f}, {box.width:.1f}x{box.height:.1f} pt) pads: L={min_pad_l:.1f}, R={min_pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f} pt (< 4.0 pt) | '{items[0][0].text[:30]}'")

        if not font_ok:
            print(f"  [FAIL] {filename}: min fontSize = {min_font:.2f} pt (< 6.0 pt)")
            all_ok = False
        elif canvas_failures:
            print(f"  [FAIL] {filename}: {len(canvas_failures)} canvas boundary violations ({w_pt:.1f}x{h_pt:.1f} pt):")
            for cf in canvas_failures[:3]:
                print(f"    - {cf}")
            all_ok = False
        elif box_failures:
            print(f"  [FAIL] {filename}: {len(box_failures)} card padding violations (< 4.0 pt):")
            for bf in box_failures[:3]:
                print(f"    - {bf}")
            all_ok = False
        else:
            ch_str = f"Ch {spec['chapter']:02d}" if spec['chapter'] <= 29 else "App B"
            target_mark = " [STRICT PAD >= 4.0 pt PASS]" if filename in active_targets else ""
            print(f"  [OK] Figure {spec['figure']:02d} ({ch_str}): {filename:<36} -> {len(strings):2d} text nodes, min font: {min_font:.2f} pt, 2-axis canvas PASS{target_mark}")

    return all_ok


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Full Technical Diagrams Vector Generator")
    parser.add_argument("--export", action="store_true", help="Export PNGs to assets/diagrams/")
    parser.add_argument("--audit", action="store_true", help="Audit typography and specs")
    parser.add_argument("--dpi", type=int, default=320, help="DPI for raster export")
    args = parser.parse_args()

    if args.audit or not (args.export or args.audit):
        ok = verify_all_diagram_typography()
        if not ok:
            print("\n[ERROR] Typography audit failed! Please inspect and fix font sizes.")
            sys.exit(1)
        else:
            print(f"\n[SUCCESS] All {len(DIAGRAM_SPECS)} diagrams pass typography quality contract (min font >= 6.0 pt)!")

    if args.export:
        print("\nStarting raster export...")
        export_all_diagrams(dpi=args.dpi)
        print(f"\n[SUCCESS] Exported all {len(DIAGRAM_SPECS)} technical diagrams to assets/diagrams/ at {args.dpi} DPI!")
