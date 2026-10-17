# -*- coding: utf-8 -*-
"""Independent Preview Renderer for Chapters 09, 10, 11 Diagrams (Agent 2 Specification).

Builds a standalone, publication-grade preview PDF displaying each of the 3 diagrams
at its exact publication dimensions (1:1 with Master PDF):
- Page 1 (Chapter 09): Figure: 476.22 x 253.62 pt (Golang_Master.pdf Page 172, xref 384)
- Page 2 (Chapter 10): Figure: 297.09 x 362.83 pt (Golang_Master.pdf Page 199, xref 439)
- Page 3 (Chapter 11): Figure: 275.97 x 362.83 pt (Golang_Master.pdf Page 206, xref 454)

Outputs:
- book/design/agent2-ch09-11/ch09_11_preview.pdf
- book/design/agent2-ch09-11/specimens/ch09_diagrams_p01.png
- book/design/agent2-ch09-11/specimens/ch09_diagrams_p02.png
- book/design/agent2-ch09-11/specimens/ch09_diagrams_p03.png
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure scripts directory is in path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import pymupdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from build_pdf import register_fonts
import ch09_11_vector_diagrams as vd

OUT_DIR = ROOT / "book/design/agent2-ch09-11"
PREVIEW_PDF = OUT_DIR / "ch09_11_preview.pdf"
SPECIMENS_DIR = OUT_DIR / "specimens"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_H = (PAGE_WIDTH - 476.22) / 2.0  # Centers widest diagram horizontally (59.53 pt)
MARGIN_TOP = 36.0
MARGIN_BOTTOM = 32.0


def build_preview() -> Path:
    """Build Chapters 09-11 preview PDF containing all 3 technical diagrams."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ensure diagrams are up to date in assets/diagrams/
    vd.export_diagrams_to_png(names=["channel-work-lifecycle.png"])

    # 2. Register standard book fonts
    register_fonts()

    # 3. Typography Styles
    title_style = ParagraphStyle(
        "SpecimenDocTitle",
        fontName="BookSansBold",
        fontSize=10.5,
        leading=14.0,
        textColor=colors.HexColor("#1A1A1A"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "SpecimenDocSubtitle",
        fontName="BookSans",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#555555"),
        spaceAfter=12,
    )
    fig_title_style = ParagraphStyle(
        "SpecimenFigTitle",
        fontName="BookSansBold",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1A1A1A"),
        spaceAfter=3,
    )
    fig_caption_style = ParagraphStyle(
        "SpecimenFigCaption",
        fontName="BookSerif",
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#444444"),
        spaceAfter=10,
    )

    doc = SimpleDocTemplate(
        str(PREVIEW_PDF),
        pagesize=A4,
        title="GOLANG - CHƯƠNG 09-11 (DIAGRAM SPECIMEN BATCH 01)",
        author="Đoàn Ngọc Hoàng Minh",
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    diagram_items = [
        (
            "CHƯƠNG 09: VÒNG ĐỜI VÀ QUYỀN SỞ HỮU KÊNH TRONG WORKER POOL",
            "Mô hình mental model về quyền sở hữu (ownership) của các kênh đồng thời: Dispatcher độc quyền gửi và đóng `jobs`; `N` worker nhận việc, gửi kết quả và báo WaitGroup; Coordinator chờ WaitGroup hoàn tất để đóng `results` duy nhất một lần; Consumer chỉ nhận dữ liệu cho đến khi kênh đóng. Kích thước xuất bản: 476.22 x 253.62 pt (Trang 172, xref 384).",
            ROOT / "assets/diagrams/channel-work-lifecycle.png",
            476.22,
            253.62,
        ),
        (
            "CHƯƠNG 10: CHU TRÌNH ĐIỀU TRA HIỆU NĂNG VÀ BẰNG CHỨNG ĐỊNH LƯỢNG",
            "Đường đi của bằng chứng kỹ thuật: Đi từ triệu chứng đến bài toán và tải đại diện (1.000 Reading), cố định hợp đồng kiểm thử, ghi nhận baseline bằng benchmark (-benchmem -count=6), bóc tách độ trễ runtime qua profile/trace (sync, sched, syscall), thực hiện tối ưu hóa phẫu thuật và đo đạc đối chứng khép kín vòng lặp. Kích thước xuất bản: 297.09 x 362.83 pt (Trang 199, xref 439).",
            ROOT / "assets/diagrams/performance-evidence-path.png",
            297.09,
            362.83,
        ),
        (
            "CHƯƠNG 11: CÁC CHẶNG CỦA HTTP CLIENT REQUEST VÀ TÁI SỬ DỤNG KẾT NỐI",
            "Bản đồ các chặng có thể của một outgoing request: Kiểm tra pool kết nối rảnh (idle connection) để tái sử dụng ngay (GotConnInfo.Reused == true) hoặc thiết lập mới qua DNS -> TCP Dial -> TLS Handshake; truyền nhận dữ liệu qua round-trip; và hợp đồng bắt buộc của bên gọi (caller) phải hoàn tất vòng đời response body (defer resp.Body.Close()). Kích thước xuất bản: 275.97 x 362.83 pt (Trang 206, xref 454).",
            ROOT / "assets/diagrams/http-client-request-path.png",
            275.97,
            362.83,
        ),
    ]

    story = []

    for i, (fig_title, fig_caption, img_path, w_pt, h_pt) in enumerate(diagram_items):
        if i > 0:
            story.append(PageBreak())

        story.append(Paragraph(f"BẢN DUYỆT SƠ ĐỒ KỸ THUẬT // ĐỢT 01 (TRANG {i+1}/3)", title_style))
        story.append(Paragraph("Hiển thị 100% kích thước xuất bản thực tế (1:1 với Master PDF) • Grayscale thuần túy (R=G=B) • Chuẩn đặc tả kỹ thuật Go", subtitle_style))
        story.append(Paragraph(fig_title, fig_title_style))
        story.append(Paragraph(fig_caption, fig_caption_style))
        story.append(Image(str(img_path), width=w_pt, height=h_pt, hAlign="CENTER"))

    doc.build(story)
    print(f"Generated Chapters 09-11 preview PDF: {PREVIEW_PDF}")

    # Generate visual specimens from preview PDF
    pdf_doc = pymupdf.open(str(PREVIEW_PDF))
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        pix = page.get_pixmap(dpi=200)
        out_specimen = SPECIMENS_DIR / f"ch09_diagrams_p{page_num + 1:02d}.png"
        pix.save(str(out_specimen))
        print(f"  Diagram specimen page {page_num + 1:02d}: {out_specimen.name} ({pix.width}x{pix.height})")
    pdf_doc.close()
    print(f"Rendered {len(diagram_items)} specimen pages to {SPECIMENS_DIR}")

    return PREVIEW_PDF


if __name__ == "__main__":
    build_preview()
