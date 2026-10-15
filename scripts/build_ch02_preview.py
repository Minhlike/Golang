# -*- coding: utf-8 -*-
"""Independent Preview Renderer for Chapter 2 Diagrams (Agent 2 Specification).

Builds a standalone, publication-grade preview PDF displaying ONLY the 4 diagrams
at their full publication dimensions (448.22 pt), accompanied by identifying labels
and captions, with zero chapter prose, tables, code blocks, or running headers/footers.

Outputs:
- book/design/agent2-ch02/ch02_preview.pdf
- book/design/agent2-ch02/specimens/ch02_diagrams_p01.png
- book/design/agent2-ch02/specimens/ch02_diagrams_p02.png
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
import ch02_vector_diagrams as vd

OUT_DIR = ROOT / "book/design/agent2-ch02"
PREVIEW_PDF = OUT_DIR / "ch02_preview.pdf"
SPECIMENS_DIR = OUT_DIR / "specimens"

PAGE_WIDTH, PAGE_HEIGHT = A4
DIAGRAM_WIDTH = 448.22
MARGIN_H = (PAGE_WIDTH - DIAGRAM_WIDTH) / 2.0  # 73.53 pt, perfectly centered
MARGIN_TOP = 50.0
MARGIN_BOTTOM = 46.0


def build_preview() -> Path:
    """Build Chapter 2 preview PDF containing only the 4 technical diagrams."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ensure the 4 diagrams are up to date in assets/diagrams/
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
        spaceAfter=2,
    )
    fig_caption_style = ParagraphStyle(
        "SpecimenFigCaption",
        fontName="BookSerif",
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#444444"),
        spaceAfter=5,
    )

    doc = SimpleDocTemplate(
        str(PREVIEW_PDF),
        pagesize=A4,
        title="GOLANG - CHƯƠNG 02 (DIAGRAM SPECIMEN)",
        author="Đoàn Ngọc Hoàng Minh",
        subject="Chương 2: Bản duyệt 4 sơ đồ kỹ thuật",
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    story = []

    # ================= PAGE 1 =================
    # Document Header
    story.append(Paragraph("CHƯƠNG 02: BẢN DUYỆT SƠ ĐỒ KỸ THUẬT (TECHNICAL DIAGRAM SPECIMEN)", title_style))
    story.append(Paragraph("Hiển thị 100% kích thước xuất bản (448.22 pt) • Phong cách đen trắng tối giản • Chuẩn Go spec vs gc runtime", subtitle_style))
    story.append(Spacer(1, 4))

    # Figure 2.1: Array Copy Semantics
    story.append(Paragraph("HÌNH 2.1 — MÔ HÌNH BỘ NHỚ // PHÉP GÁN MẢNG: SAO CHÉP TOÀN BỘ GIÁ TRỊ", fig_title_style))
    story.append(Paragraph("Hai array value sau assignment: phần tử được copy vào vùng dữ liệu riêng (bảo đảm ngữ nghĩa giá trị độc lập từ Go spec).", fig_caption_style))
    story.append(Image(str(ROOT / "assets/diagrams/array-copy.png"), width=DIAGRAM_WIDTH, height=148.0))
    story.append(Spacer(1, 20))

    # Figure 2.2: Slice Sharing Semantics
    story.append(Paragraph("HÌNH 2.2 — MÔ HÌNH TRIỂN KHAI // SLICE DESCRIPTOR VÀ CHIA SẺ MẢNG NỀN (ALIASING)", fig_title_style))
    story.append(Paragraph("Hai slice value sau assignment: descriptor được copy theo giá trị, backing storage được chia sẻ (mô hình gc 64-bit).", fig_caption_style))
    story.append(Image(str(ROOT / "assets/diagrams/slice-sharing.png"), width=DIAGRAM_WIDTH, height=196.0))

    # ================= PAGE 2 =================
    story.append(PageBreak())

    # Figure 2.3: Slice Window Geometry
    story.append(Paragraph("HÌNH 2.3 — HÌNH HỌC CỬA SỔ SLICE // ĐỘ DÀI (LEN) VÀ SỨC CHỨA (CAP)", fig_title_style))
    story.append(Paragraph("Một slice window trên mảng nền của lát cắt gốc base : []int; vùng thấy được là len(x) = 2; sức chứa tối đa là cap(x) = 4.", fig_caption_style))
    story.append(Image(str(ROOT / "assets/diagrams/slice-window.png"), width=DIAGRAM_WIDTH, height=195.0))
    story.append(Spacer(1, 20))

    # Figure 2.4: Append Mechanics & Capacity Branching
    story.append(Paragraph("HÌNH 2.4 — ĐẶC TẢ PHÂN NHÁNH append // ĐIỂM QUYẾT ĐỊNH THEO SỨC CHỨA (CAPACITY)", fig_title_style))
    story.append(Paragraph("Hai kết quả của append: còn capacity (len(s) + số_phần_tử_thêm <= cap(s)) thì tái sử dụng mảng nền; vượt capacity thì cấp mảng mới (growslice).", fig_caption_style))
    story.append(Image(str(ROOT / "assets/diagrams/append-storage.png"), width=DIAGRAM_WIDTH, height=220.0))

    # Build PDF
    doc.build(story)
    print(f"Generated Chapter 2 diagrams preview: {PREVIEW_PDF}")

    # Render specimens
    render_specimens(PREVIEW_PDF)
    return PREVIEW_PDF


def render_specimens(pdf_path: Path, dpi: int = 200) -> list[Path]:
    """Render all pages of the preview PDF to specimen PNGs and clean up obsolete ones."""
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean up obsolete 12-page specimens from previous runs
    for old_file in SPECIMENS_DIR.glob("ch02_page_*.png"):
        old_file.unlink()
        print(f"  Cleaned up obsolete specimen: {old_file.name}")

    doc = pymupdf.open(str(pdf_path))
    specimen_paths = []

    for page_idx, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=dpi)
        out_path = SPECIMENS_DIR / f"ch02_diagrams_p{page_idx:02d}.png"
        pix.save(str(out_path))
        specimen_paths.append(out_path)
        print(f"  Diagram specimen page {page_idx:02d}: {out_path.name} ({pix.width}x{pix.height})")

    doc.close()
    print(f"Rendered {len(specimen_paths)} specimen pages to {SPECIMENS_DIR}")
    return specimen_paths


if __name__ == "__main__":
    build_preview()
