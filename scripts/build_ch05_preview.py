# -*- coding: utf-8 -*-
"""Independent Preview Renderer for Chapter 5 Diagrams (Agent 2 Specification).

Builds a standalone, publication-grade preview PDF displaying the Chapter 5 diagram
at its exact publication dimensions (1:1 with Master PDF):
- Figure 19: 369.13 x 362.83 pt (Page 104, xref 246)

Outputs:
- book/design/agent2-ch05/ch05_preview.pdf
- book/design/agent2-ch05/specimens/ch05_diagrams_p01.png
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
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from build_pdf import register_fonts
import ch05_vector_diagrams as vd

OUT_DIR = ROOT / "book/design/agent2-ch05"
PREVIEW_PDF = OUT_DIR / "ch05_preview.pdf"
SPECIMENS_DIR = OUT_DIR / "specimens"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_H = (PAGE_WIDTH - 369.13) / 2.0  # Centers diagram horizontally
MARGIN_TOP = 42.0
MARGIN_BOTTOM = 38.0


def build_preview() -> Path:
    """Build Chapter 5 preview PDF containing the technical diagram."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ensure diagram is up to date in assets/diagrams/
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
        title="GOLANG - CHƯƠNG 05 (DIAGRAM SPECIMEN)",
        author="Đoàn Ngọc Hoàng Minh",
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    story = [
        Paragraph("CHƯƠNG 05: BẢN DUYỆT SƠ ĐỒ KỸ THUẬT (TECHNICAL DIAGRAM SPECIMEN)", title_style),
        Paragraph("Hiển thị 100% kích thước xuất bản thực tế (1:1 với Master PDF) • Phong cách đen trắng tối giản • Chuẩn Go spec vs runtime", subtitle_style),
    ]

    diagram_items = [
        (
            "HÌNH 19 — HƯỚNG PHỤ THUỘC (DEPENDENCY DIRECTION) // PHÂN TÁCH RANH GIỚI GÓI",
            "cmd/opsprobe là composition root; phối hợp cấu hình nội bộ và gói nghiệp vụ probe. probe độc lập hoàn toàn với CLI/terminal, test và thay thế runner mà không kéo presentation theo. Kích thước xuất bản thực tế: 369.13 x 362.83 pt (Trang 104, xref 246).",
            ROOT / "assets/diagrams/package-boundary-graph.png",
            369.13,
            362.83,
        ),
    ]

    for fig_title, fig_caption, img_path, w_pt, h_pt in diagram_items:
        story.append(Paragraph(fig_title, fig_title_style))
        story.append(Paragraph(fig_caption, fig_caption_style))
        story.append(Image(str(img_path), width=w_pt, height=h_pt, hAlign="CENTER"))
        story.append(Spacer(1, 12))

    doc.build(story)
    print(f"Generated Chapter 5 diagrams preview: {PREVIEW_PDF}")

    # Generate visual specimens from preview PDF
    pdf_doc = pymupdf.open(str(PREVIEW_PDF))
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        pix = page.get_pixmap(dpi=200)
        out_specimen = SPECIMENS_DIR / f"ch05_diagrams_p{page_num + 1:02d}.png"
        pix.save(str(out_specimen))
        print(f"  Diagram specimen page {page_num + 1:02d}: {out_specimen.name} ({pix.width}x{pix.height})")
    pdf_doc.close()
    print(f"Rendered {len(diagram_items)} specimen pages to {SPECIMENS_DIR}")

    return PREVIEW_PDF


if __name__ == "__main__":
    build_preview()
