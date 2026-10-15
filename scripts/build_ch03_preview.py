# -*- coding: utf-8 -*-
"""Independent Preview Renderer for Chapter 3 Diagrams (Agent 2 Specification).

Builds a standalone, publication-grade preview PDF displaying ONLY the 6 diagrams
at their full publication dimensions (448.22 pt), accompanied by identifying labels
and captions, with zero chapter prose, tables, code blocks, or running headers/footers.

Outputs:
- book/design/agent2-ch03/ch03_preview.pdf
- book/design/agent2-ch03/specimens/ch03_diagrams_p01.png
- book/design/agent2-ch03/specimens/ch03_diagrams_p02.png
- book/design/agent2-ch03/specimens/ch03_diagrams_p03.png
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
import ch03_vector_diagrams as vd

OUT_DIR = ROOT / "book/design/agent2-ch03"
PREVIEW_PDF = OUT_DIR / "ch03_preview.pdf"
SPECIMENS_DIR = OUT_DIR / "specimens"

PAGE_WIDTH, PAGE_HEIGHT = A4
DIAGRAM_WIDTH = 448.22
MARGIN_H = (PAGE_WIDTH - DIAGRAM_WIDTH) / 2.0  # 73.53 pt, perfectly centered
MARGIN_TOP = 46.0
MARGIN_BOTTOM = 42.0


def build_preview() -> Path:
    """Build Chapter 3 preview PDF containing only the 6 technical diagrams."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ensure the 6 diagrams are up to date in assets/diagrams/
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
        title="GOLANG - CHƯƠNG 03 (DIAGRAM SPECIMEN)",
        author="Đoàn Ngọc Hoàng Minh",
        subject="Chương 3: Bản duyệt 6 sơ đồ kỹ thuật",
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    story = []

    # ================= PAGE 1 =================
    # Document Header
    story.append(Paragraph("CHƯƠNG 03: BẢN DUYỆT SƠ ĐỒ KỸ THUẬT (TECHNICAL DIAGRAM SPECIMEN)", title_style))
    story.append(Paragraph("Hiển thị 100% kích thước xuất bản (448.22 pt) • Phong cách đen trắng tối giản • Chuẩn Go spec vs runtime", subtitle_style))
    story.append(Spacer(1, 4))

    # Figure 3.1: Pass-by-value function call semantics
    story.append(Paragraph("HÌNH 3.1 — TRUYỀN THAM SỐ // LỜI GỌI HÀM SAO CHÉP GIÁ TRỊ (PASS-BY-VALUE)", fig_title_style))
    story.append(Paragraph("Lời gọi addBonus(balance) copy value 100 vào parameter x. Sơ đồ biểu diễn semantics của variable và value, không khẳng định vị trí vật lý trong RAM.", fig_caption_style))
    story.append(Image(str(ROOT / "assets/diagrams/pointer-value-call.png"), width=DIAGRAM_WIDTH, height=162.0))
    story.append(Spacer(1, 18))

    # Figure 3.2: Pointer value & pointee dereference
    story.append(Paragraph("HÌNH 3.2 — POINTER & POINTEE // GIẢI THAM CHIẾU VÀ ĐÍCH TRỎ BIẾN GỐC", fig_title_style))
    story.append(Paragraph("balance trong function là pointer value được truyền theo value. *balance truy cập pointee; sơ đồ không dùng địa chỉ số hay stack/heap runtime.", fig_caption_style))
    story.append(Image(str(ROOT / "assets/diagrams/pointer-pointee.png"), width=DIAGRAM_WIDTH, height=168.0))

    # ================= PAGE 2 =================
    story.append(PageBreak())

    # Figure 3.3: Field-by-field struct copy semantics
    story.append(Paragraph("HÌNH 3.3 — PHÉP GÁN STRUCT // SAO CHÉP ĐỘC LẬP THEO TỪNG TRƯỜNG (FIELD-BY-FIELD COPY)", fig_title_style))
    story.append(Paragraph("Hai struct value sau phép gán: field được copy, nên thay đổi field của candidate không quay lại billing (nếu field chứa reference thì tiếp tục phân tích reference).", fig_caption_style))
    story.append(Image(str(ROOT / "assets/diagrams/struct-copy.png"), width=DIAGRAM_WIDTH, height=175.0))
    story.append(Spacer(1, 22))

    # Figure 3.4: Map assignment copies descriptor, shares storage
    story.append(Paragraph("HÌNH 3.4 — PHÉP GÁN MAP // SAO CHÉP DESCRIPTOR, CHIA SẺ MAP STORAGE", fig_title_style))
    story.append(Paragraph("Hai map value sau assignment: map descriptor được copy, còn map data được cả hai value dùng để lookup và cập nhật (sơ đồ khái niệm, không mô tả bucket).", fig_caption_style))
    story.append(Image(str(ROOT / "assets/diagrams/map-sharing.png"), width=DIAGRAM_WIDTH, height=175.0))

    # ================= PAGE 3 =================
    story.append(PageBreak())

    # Figure 3.5: Method receiver trace (Value receiver vs Pointer receiver)
    story.append(Paragraph("HÌNH 3.5 — ĐIỀU PHỐI METHOD RECEIVER // VALUE RECEIVER VS POINTER RECEIVER", fig_title_style))
    story.append(Paragraph("Hai lời gọi method trên cùng Service variable: Summary nhận bản sao value (chỉ đọc), Record đi qua &billing để mutate trực tiếp pointee.", fig_caption_style))
    story.append(Image(str(ROOT / "assets/diagrams/method-receiver-trace.png"), width=DIAGRAM_WIDTH, height=188.0))
    story.append(Spacer(1, 20))

    # Figure 3.6: Interface contract & implicit satisfaction
    story.append(Paragraph("HÌNH 3.6 — KIỂU CẤU TRÚC // HỢP ĐỒNG INTERFACE NHỎ VÀ THỎA MÃN NGẦM ĐỊNH", fig_title_style))
    story.append(Paragraph("Một consumer phụ thuộc vào contract SummarySource nhỏ; Service và StaticTarget độc lập thỏa contract bằng method set của chính chúng (không từ khóa implements).", fig_caption_style))
    story.append(Image(str(ROOT / "assets/diagrams/interface-contract.png"), width=DIAGRAM_WIDTH, height=188.0))

    # Build PDF
    doc.build(story)
    print(f"Generated Chapter 3 diagrams preview: {PREVIEW_PDF}")

    # Render specimens
    render_specimens(PREVIEW_PDF)
    return PREVIEW_PDF


def render_specimens(pdf_path: Path, dpi: int = 200) -> list[Path]:
    """Render all pages of the preview PDF to specimen PNGs."""
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(str(pdf_path))
    specimen_paths = []

    for page_idx, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=dpi)
        out_path = SPECIMENS_DIR / f"ch03_diagrams_p{page_idx:02d}.png"
        pix.save(str(out_path))
        specimen_paths.append(out_path)
        print(f"  Diagram specimen page {page_idx:02d}: {out_path.name} ({pix.width}x{pix.height})")

    doc.close()
    print(f"Rendered {len(specimen_paths)} specimen pages to {SPECIMENS_DIR}")
    return specimen_paths


if __name__ == "__main__":
    build_preview()
