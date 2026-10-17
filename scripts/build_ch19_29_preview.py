# -*- coding: utf-8 -*-
"""Independent Preview Renderer for Chapters 19-29 Diagrams (Agent 2 Final Book-wide Redesign).

Builds a standalone, publication-grade preview PDF displaying each of the 18 diagrams
at its exact publication dimensions (1:1 with Golang_Master.pdf):
- Page 01 (Chapter 18): Figure 33: 476.22 x 330.21 pt (Page 331, xref 382)
- Page 02 (Chapter 19): Figure 34: 413.18 x 362.83 pt (Page 341, xref 393)
- Page 03 (Chapter 21): Figure 35: 476.22 x 162.43 pt (Page 371, xref 424)
- Page 04 (Chapter 22): Figure 36: 476.22 x 301.61 pt (Page 385, xref 439)
- Page 05 (Chapter 22): Figure 37: 476.22 x 275.15 pt (Page 386, xref 441)
- Page 06 (Chapter 23): Figure 38: 476.22 x 254.61 pt (Page 404, xref 460)
- Page 07 (Chapter 23): Figure 39: 473.72 x 362.83 pt (Page 405, xref 462)
- Page 08 (Chapter 23): Figure 40: 342.25 x 362.83 pt (Page 410, xref 468)
- Page 09 (Chapter 24): Figure 41: 264.41 x 362.83 pt (Page 426, xref 485)
- Page 10 (Chapter 24): Figure 42: 437.54 x 362.83 pt (Page 429, xref 489)
- Page 11 (Chapter 25): Figure 43: 278.59 x 362.83 pt (Page 443, xref 504)
- Page 12 (Chapter 25): Figure 44: 407.82 x 362.83 pt (Page 444, xref 506)
- Page 13 (Chapter 25): Figure 45: 462.12 x 362.83 pt (Page 447, xref 510)
- Page 14 (Chapter 26): Figure 46: 214.51 x 362.83 pt (Page 465, xref 529)
- Page 15 (Chapter 26): Figure 47: 476.22 x 330.88 pt (Page 468, xref 533)
- Page 16 (Chapter 26): Figure 48: 476.22 x 327.02 pt (Page 470, xref 536)
- Page 17 (Chapter 27): Figure 49: 244.10 x 362.83 pt (Page 490, xref 557)
- Page 18 (Chapter 29): Figure 50: 476.22 x 260.59 pt (Page 544, xref 612)

Outputs:
- book/design/agent2-ch19-29/ch19_29_preview.pdf
- book/design/agent2-ch19-29/specimens/ch19_29_diagrams_p01.png to p18.png
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
from ch19_29_vector_diagrams import DIAGRAM_SPECS, export_all_diagrams

OUT_DIR = ROOT / "book/design/agent2-ch19-29"
PREVIEW_PDF = OUT_DIR / "ch19_29_preview.pdf"
SPECIMENS_DIR = OUT_DIR / "specimens"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_H = (PAGE_WIDTH - 476.22) / 2.0  # Centers widest diagram horizontally (59.53 pt)
MARGIN_TOP = 32.0
MARGIN_BOTTOM = 28.0


def build_preview() -> Path:
    """Build Chapters 19-29 preview PDF containing all 18 technical diagrams."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ensure diagrams are up to date in assets/diagrams/
    export_all_diagrams(dpi=320)

    # 2. Register standard book fonts
    register_fonts()

    # 3. Typography Styles
    title_style = ParagraphStyle(
        "SpecimenDocTitle",
        fontName="BookSansBold",
        fontSize=10.0,
        leading=13.0,
        textColor=colors.HexColor("#1A1A1A"),
        spaceAfter=2,
    )
    fig_title_style = ParagraphStyle(
        "SpecimenFigTitle",
        fontName="BookSansBold",
        fontSize=8.0,
        leading=11.0,
        textColor=colors.HexColor("#333333"),
        spaceAfter=6,
    )

    doc = SimpleDocTemplate(
        str(PREVIEW_PDF),
        pagesize=A4,
        title="GOLANG - CHƯƠNG 19-29 (FINAL TECHNICAL DIAGRAM REDESIGN)",
        author="Đoàn Ngọc Hoàng Minh",
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    story = []
    total_figs = len(DIAGRAM_SPECS)

    for i, (filename, spec) in enumerate(DIAGRAM_SPECS.items()):
        if i > 0:
            story.append(PageBreak())

        img_path = ROOT / "assets/diagrams" / filename
        fig_label = f"Chương {spec['chapter']:02d} — Hình {spec['figure']:02d}: {spec['title']} ({spec['w_pt']} x {spec['h_pt']} pt, Trang {spec['page']}, xref {spec['xref']})"

        story.append(Paragraph(f"BẢN DUYỆT SƠ ĐỒ KỸ THUẬT // AGENT 2 FINAL REDESIGN (TRANG {i+1:02d}/{total_figs:02d})", title_style))
        story.append(Paragraph(fig_label, fig_title_style))
        story.append(Spacer(1, 6))
        story.append(Image(str(img_path), width=spec['w_pt'], height=spec['h_pt'], hAlign="CENTER"))

    doc.build(story)
    print(f"\nGenerated Chapters 19-29 preview PDF: {PREVIEW_PDF}")

    # Generate visual specimens from preview PDF
    pdf_doc = pymupdf.open(str(PREVIEW_PDF))
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        pix = page.get_pixmap(dpi=200)
        out_specimen = SPECIMENS_DIR / f"ch19_29_diagrams_p{page_num + 1:02d}.png"
        pix.save(str(out_specimen))
        print(f"  Diagram specimen page {page_num + 1:02d}: {out_specimen.name} ({pix.width}x{pix.height})")
    pdf_doc.close()
    print(f"Rendered {len(DIAGRAM_SPECS)} specimen pages to {SPECIMENS_DIR}")

    return PREVIEW_PDF


if __name__ == "__main__":
    build_preview()
