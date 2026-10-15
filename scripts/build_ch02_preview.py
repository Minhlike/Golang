# -*- coding: utf-8 -*-
"""Independent Preview Renderer for Chapter 2 Redesign (Agent 2 Specification).

Builds a standalone, publication-grade preview PDF of Chapter 2 using the
EXACT engine, typography, layout, and styling of scripts/build_pdf.py,
with only the 4 upgraded vector diagrams in assets/diagrams/.

Outputs:
- book/design/agent2-ch02/ch02_preview.pdf
- book/design/agent2-ch02/specimens/ch02_page_XX.png
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure scripts directory is in path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import pymupdf
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.platypus.frames import Frame

from book_style import (
    MARGIN_BOTTOM,
    MARGIN_INSIDE,
    MARGIN_OUTSIDE,
    MARGIN_TOP,
    PAGE_SIZE,
    PRINTABLE_HEIGHT,
    PRINTABLE_WIDTH,
    MirroredDocTemplate,
    footer_recto,
    footer_verso,
    get_book_styles,
)
from build_pdf import (
    add_markdown,
    keep_headings_with_content,
    register_fonts,
)
import ch02_vector_diagrams as vd

CHAPTER_FILE = ROOT / "book/chapters/02-gia-tri-slice-va-aliasing.md"
OUT_DIR = ROOT / "book/design/agent2-ch02"
PREVIEW_PDF = OUT_DIR / "ch02_preview.pdf"
SPECIMENS_DIR = OUT_DIR / "specimens"


def build_preview() -> Path:
    """Build Chapter 2 preview PDF using the exact book layout and renderer."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ensure the 4 diagrams are up to date in assets/diagrams/
    vd.export_diagrams_to_png()

    # 2. Register standard book fonts
    body, body_bold, heading, heading_bold, mono = register_fonts()
    s = get_book_styles()

    # 3. Setup Mirrored Layout matching scripts/build_pdf.py
    frame_recto = Frame(
        MARGIN_INSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="frame_book_recto", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    template_recto = PageTemplate(id="book_recto", frames=[frame_recto], onPage=footer_recto)

    frame_verso = Frame(
        MARGIN_OUTSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="frame_book_verso", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    template_verso = PageTemplate(id="book_verso", frames=[frame_verso], onPage=footer_verso)

    doc = MirroredDocTemplate(
        str(PREVIEW_PDF),
        pagesize=PAGE_SIZE,
        title="GOLANG - CHƯƠNG 02 (PREVIEW)",
        author="Đoàn Ngọc Hoàng Minh",
        subject="Chương 2: Giá trị, Slice và Aliasing",
        leftMargin=MARGIN_INSIDE,
        rightMargin=MARGIN_OUTSIDE,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )
    doc.addPageTemplates([template_recto, template_verso])

    # 4. Parse Chapter 2 markdown using standard book parser
    story = []
    numbering = {"table": 0, "figure": 0}
    add_markdown(story, CHAPTER_FILE, s, mono, page_break_before=False, numbering=numbering)
    story = keep_headings_with_content(story)

    # 5. Build PDF
    doc.build(story)
    print(f"Generated Chapter 2 preview: {PREVIEW_PDF}")

    # 6. Render specimens for every page
    render_specimens(PREVIEW_PDF)
    return PREVIEW_PDF


def render_specimens(pdf_path: Path, dpi: int = 150) -> list[Path]:
    """Render all pages of the preview PDF to specimen PNGs."""
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf_path))
    num_pages = len(doc)
    specimen_paths = []

    # Clean up obsolete specimen images if page count changed
    for old_file in SPECIMENS_DIR.glob("ch02_page_*.png"):
        try:
            p_idx = int(old_file.stem.split("_")[-1])
            if p_idx > num_pages:
                old_file.unlink()
        except ValueError:
            pass

    for page_idx, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=dpi)
        out_path = SPECIMENS_DIR / f"ch02_page_{page_idx:02d}.png"
        pix.save(str(out_path))
        specimen_paths.append(out_path)
        print(f"  Specimen page {page_idx:02d}: {out_path.name} ({pix.width}x{pix.height})")

    doc.close()
    print(f"Rendered {len(specimen_paths)} specimen pages to {SPECIMENS_DIR}")
    return specimen_paths


if __name__ == "__main__":
    build_preview()
