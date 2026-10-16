# -*- coding: utf-8 -*-
"""Independent Preview Renderer for Chapter 4 Diagrams (Agent 2 Specification).

Builds a standalone, publication-grade preview PDF displaying the 2 Chapter 4 diagrams
at their exact publication dimensions (1:1 with Master PDF):
- Figure 4.1: 291.21 x 362.83 pt (Page 88, xref 212)
- Figure 4.2: 476.22 x 323.91 pt (Page 99, xref 235)

Outputs:
- book/design/agent2-ch04/ch04_preview.pdf
- book/design/agent2-ch04/specimens/ch04_diagrams_p01.png
- book/design/agent2-ch04/specimens/ch04_diagrams_p02.png
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
import ch04_vector_diagrams as vd

OUT_DIR = ROOT / "book/design/agent2-ch04"
PREVIEW_PDF = OUT_DIR / "ch04_preview.pdf"
SPECIMENS_DIR = OUT_DIR / "specimens"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_H = (PAGE_WIDTH - 476.22) / 2.0  # 59.53 pt, fits full 476.22 pt width
MARGIN_TOP = 42.0
MARGIN_BOTTOM = 38.0


def build_preview() -> Path:
    """Build Chapter 4 preview PDF containing the 2 technical diagrams."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ensure the 2 diagrams are up to date in assets/diagrams/
    vd.export_diagrams_to_png()

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
        spaceAfter=14,
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
        title="GOLANG - CHƯƠNG 04 (DIAGRAM SPECIMEN)",
        author="Đoàn Ngọc Hoàng Minh",
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    story = [
        Paragraph("CHƯƠNG 04: BẢN DUYỆT SƠ ĐỒ KỸ THUẬT (TECHNICAL DIAGRAM SPECIMEN)", title_style),
        Paragraph("Hiển thị 100% kích thước xuất bản thực tế (1:1 với Master PDF) • Phong cách đen trắng tối giản • Chuẩn Go spec vs runtime", subtitle_style),
    ]

    diagram_items = [
        (
            "HÌNH 4.1 — RANH GIỚI LỖI // BẢO TOÀN ĐỊNH DANH GỐC VÀ DỮ LIỆU CÓ CẤU TRÚC",
            "Mỗi tầng kiến trúc chỉ thêm bối cảnh operation bằng %w; caller chọn errors.Is để phân loại theo loại lỗi sentinel hoặc errors.As để trích xuất dữ liệu từ struct ProbeFailure. Kích thước xuất bản thực tế: 291.21 x 362.83 pt.",
            ROOT / "assets/diagrams/error-boundary-trace.png",
            291.21,
            362.83,
        ),
        (
            "HÌNH 4.2 — VÒNG ĐỜI TÀI NGUYÊN & DEFER CLEANUP // 3 ĐƯỜNG ĐI TRONG runWithSession",
            "defer ràng buộc dọn dẹp trực tiếp với scope đã nhận ownership. Error từ Close() chỉ thay result khi run() chưa có failure để bảo toàn nguyên nhân chính. Kích thước xuất bản thực tế: 476.22 x 323.91 pt.",
            ROOT / "assets/diagrams/cancellation-cleanup-trace.png",
            476.22,
            323.91,
        ),
    ]

    for idx, (fig_title, fig_caption, img_path, w_pt, h_pt) in enumerate(diagram_items):
        if idx > 0:
            story.append(PageBreak())
            story.append(Spacer(1, 10))

        story.append(Paragraph(fig_title, fig_title_style))
        story.append(Paragraph(fig_caption, fig_caption_style))
        story.append(Image(str(img_path), width=w_pt, height=h_pt, hAlign="CENTER"))
        story.append(Spacer(1, 12))

    doc.build(story)
    print(f"Generated Chapter 4 diagrams preview: {PREVIEW_PDF}")

    # Generate visual specimens from preview PDF
    pdf_doc = pymupdf.open(str(PREVIEW_PDF))
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        pix = page.get_pixmap(dpi=200)
        out_specimen = SPECIMENS_DIR / f"ch04_diagrams_p{page_num + 1:02d}.png"
        pix.save(str(out_specimen))
        print(f"  Diagram specimen page {page_num + 1:02d}: {out_specimen.name} ({pix.width}x{pix.height})")
    pdf_doc.close()
    print(f"Rendered {len(diagram_items)} specimen pages to {SPECIMENS_DIR}")

    return PREVIEW_PDF


if __name__ == "__main__":
    build_preview()
