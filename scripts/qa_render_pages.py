import sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import fitz
from pypdf import PdfReader

reader = PdfReader("Golang_Master.pdf")
print(f"Total pages: {len(reader.pages)}")

# Print outline titles and pages
section_pages = {}
for item in reader.outline:
    if hasattr(item, "title"):
        page_num = reader.get_destination_page_number(item) + 1
        print(f"  {item.title} -> page {page_num}")
        section_pages[item.title] = page_num

out_dir = Path("tmp/qa_renders")
out_dir.mkdir(parents=True, exist_ok=True)

doc = fitz.open("Golang_Master.pdf")

# Key pages to inspect:
# 1: Cover
# 2: TOC
# Ch00 start
# Ch01 start and table/code pages
# Devops Library Atlas start
# Error Atlas start and last page (290)
pages_to_render = [1, 2, 4, 8, 14, 15]

# Add specific section starts
for title, p in section_pages.items():
    if "ATLAS MÃ NGUỒN" in title or "ATLAS LỖI GO" in title:
        pages_to_render.append(p)

pages_to_render.append(len(doc))  # Last page
pages_to_render = sorted(list(set(pages_to_render)))

for p in pages_to_render:
    if 1 <= p <= len(doc):
        page = doc[p - 1]
        pix = page.get_pixmap(dpi=150)
        out_file = out_dir / f"page_{p:03d}.png"
        pix.save(str(out_file))
        print(f"Saved: {out_file} (Page {p})")
