# -*- coding: utf-8 -*-
"""render_catalog_pages.py
Renders all pages of 'book/design/agent2-2026/design_catalog.pdf' into PNG images
at 150 DPI in 'book/design/agent2-2026/renders/' for visual inspection and QA.
"""
from pathlib import Path
import pymupdf as fitz

PDF_PATH = Path("D:/Golang/book/design/agent2-2026/design_catalog.pdf")
RENDERS_DIR = Path("D:/Golang/book/design/agent2-2026/renders")
RENDERS_DIR.mkdir(parents=True, exist_ok=True)

def render_all():
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f"Rendering {total_pages} pages from {PDF_PATH.name}...")

    # 150 DPI is standard for high-fidelity screen review (zoom 150 / 72 = 2.0833)
    zoom = 150.0 / 72.0
    mat = fitz.Matrix(zoom, zoom)

    for i in range(total_pages):
        page = doc[i]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_file = RENDERS_DIR / f"catalog_p{i+1:02d}.png"
        pix.save(str(out_file))
        print(f"  Rendered Page {i+1:02d}/{total_pages:02d} -> {out_file.name}")

    print("All pages rendered successfully!")

if __name__ == "__main__":
    render_all()
