# -*- coding: utf-8 -*-
"""Independent Preview Renderer for Chapters 16, 17, 18 Diagrams (Batch 03 - Agent 2 Specification).

Builds a standalone, publication-grade preview PDF displaying each of the 5 diagrams
at its exact publication dimensions (1:1 with Master PDF):
- Page 1 (Chapter 16): Figure 27: 476.22 x 312.02 pt (Page 283, xref 328)
- Page 2 (Chapter 16): Figure 28: 476.22 x 264.46 pt (Page 292, xref 338)
- Page 3 (Chapter 17): Figure 29: 335.89 x 362.83 pt (Page 300, xref 347)
- Page 4 (Chapter 17): Figure 31: 476.22 x 238.11 pt (Page 310, xref 359)
- Page 5 (Chapter 18): Figure 32: 476.22 x 216.73 pt (Page 321, xref 371)

Outputs:
- book/design/agent2-ch16-18/ch16_18_preview.pdf
- book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p01.png to p05.png
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
import ch16_18_vector_diagrams as vd

OUT_DIR = ROOT / "book/design/agent2-ch16-18"
PREVIEW_PDF = OUT_DIR / "ch16_18_preview.pdf"
SPECIMENS_DIR = OUT_DIR / "specimens"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_H = (PAGE_WIDTH - 476.22) / 2.0  # Centers widest diagram horizontally (59.53 pt)
MARGIN_TOP = 36.0
MARGIN_BOTTOM = 32.0


def build_preview() -> Path:
    """Build Chapters 16, 17, 18 preview PDF containing all 5 technical diagrams."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ensure diagrams are up to date in assets/diagrams/
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

    doc = SimpleDocTemplate(
        str(PREVIEW_PDF),
        pagesize=A4,
        title="GOLANG - CHƯƠNG 16-18 (DIAGRAM SPECIMEN BATCH 03)",
        author="Đoàn Ngọc Hoàng Minh",
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    diagram_items = [
        (
            "Chương 16 — Hình 27: Các phép chiếu observability (476.22 x 312.02 pt, Trang 283, xref 328)",
            ROOT / "assets/diagrams/observability-projections.png",
            476.22,
            312.02,
        ),
        (
            "Chương 16 — Hình 28: Các đường ghi nhận kết quả của một request probe (476.22 x 264.46 pt, Trang 292, xref 338)",
            ROOT / "assets/diagrams/probe-observation-path.png",
            476.22,
            264.46,
        ),
        (
            "Chương 17 — Hình 29: Vòng lặp điều hòa reconciliation (335.89 x 362.83 pt, Trang 300, xref 347)",
            ROOT / "assets/diagrams/reconciliation-loop.png",
            335.89,
            362.83,
        ),
        (
            "Chương 17 — Hình 31: Từ image đến workload và quan sát trong cluster (476.22 x 238.11 pt, Trang 310, xref 359)",
            ROOT / "assets/diagrams/container-cluster-observation.png",
            476.22,
            238.11,
        ),
        (
            "Chương 18 — Hình 32: Chuỗi bằng chứng delivery (476.22 x 216.73 pt, Trang 321, xref 371)",
            ROOT / "assets/diagrams/delivery-evidence-chain.png",
            476.22,
            216.73,
        ),
    ]

    story = []

    for i, (fig_title, img_path, w_pt, h_pt) in enumerate(diagram_items):
        if i > 0:
            story.append(PageBreak())

        story.append(Paragraph(f"BẢN DUYỆT SƠ ĐỒ KỸ THUẬT // ĐỢT 03 (TRANG {i+1}/5)", title_style))
        story.append(Paragraph(fig_title, fig_title_style))
        story.append(Spacer(1, 10))
        story.append(Image(str(img_path), width=w_pt, height=h_pt, hAlign="CENTER"))

    doc.build(story)
    print(f"Generated Chapters 16-18 preview PDF: {PREVIEW_PDF}")

    # Generate visual specimens from preview PDF
    pdf_doc = pymupdf.open(str(PREVIEW_PDF))
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        pix = page.get_pixmap(dpi=200)
        out_specimen = SPECIMENS_DIR / f"ch16_18_diagrams_p{page_num + 1:02d}.png"
        pix.save(str(out_specimen))
        print(f"  Diagram specimen page {page_num + 1:02d}: {out_specimen.name} ({pix.width}x{pix.height})")
    pdf_doc.close()
    print(f"Rendered {len(diagram_items)} specimen pages to {SPECIMENS_DIR}")

    return PREVIEW_PDF


if __name__ == "__main__":
    build_preview()
