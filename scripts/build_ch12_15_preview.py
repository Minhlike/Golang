# -*- coding: utf-8 -*-
"""Independent Preview Renderer for Chapters 12, 13, 15 Diagrams (Agent 2 Specification).

Builds a standalone, publication-grade preview PDF displaying each of the 3 diagrams
at its exact publication dimensions (1:1 with Master PDF):
- Page 1 (Chapter 12): Figure: 185.80 x 362.83 pt (Golang_Master.pdf Page 217, xref 477)
- Page 2 (Chapter 13): Figure: 422.77 x 362.83 pt (Golang_Master.pdf Page 233, xref 510)
- Page 3 (Chapter 15): Figure: 444.69 x 362.83 pt (Golang_Master.pdf Page 272, xref 589)

Outputs:
- book/design/agent2-ch12-15/ch12_15_preview.pdf
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
import ch12_15_vector_diagrams as vd

OUT_DIR = ROOT / "book/design/agent2-ch12-15"
PREVIEW_PDF = OUT_DIR / "ch12_15_preview.pdf"
SPECIMENS_DIR = OUT_DIR / "specimens"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_H = (PAGE_WIDTH - 444.69) / 2.0  # Centers widest diagram horizontally (75.29 pt)
MARGIN_TOP = 36.0
MARGIN_BOTTOM = 32.0


def build_preview() -> Path:
    """Build Chapters 12, 13, 15 preview PDF containing all 3 technical diagrams."""
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
        title="GOLANG - CHƯƠNG 12-15 (DIAGRAM SPECIMEN BATCH 02)",
        author="Đoàn Ngọc Hoàng Minh",
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )

    diagram_items = [
        (
            "CHƯƠNG 12: VÒNG ĐỜI PHỤC VỤ VÀ RÚT LUI CỦA HTTP SERVICE",
            "Mô hình khái niệm vòng đời service: Khởi động listener -> nhận request và cấp r.Context() -> nhận tín hiệu dừng OS (SIGINT/SIGTERM) -> điều phối Server.Shutdown với deadline grace độc lập -> phân nhánh kết cục trong hạn grace hoặc quá hạn timeout. Ranh giới bất biến: Shutdown KHÔNG tự cancel handler đang chạy và KHÔNG tự chờ hijacked connection. Kích thước xuất bản: 185.80 x 362.83 pt (Trang 217, xref 477).",
            ROOT / "assets/diagrams/http-service-lifecycle.png",
            185.80,
            362.83,
        ),
        (
            "CHƯƠNG 13: RANH GIỚI TRANSACTION VÀ TÍNH NGUYÊN TỬ (ATOMICITY)",
            "Sơ đồ khái niệm về tính nguyên tử của thao tác Disable(): tx.BeginTx() -> defer tx.Rollback() -> UPDATE checks (RowsAffected kiểm tra sự tồn tại) -> INSERT check_events (Audit event) -> tx.Commit(). Cả hai thay đổi cùng có hiệu lực khi Commit, hoặc cùng bị loại bỏ sạch khi Rollback. Phân biệt rõ Atomicity với Isolation; DB không rollback được tác dụng phụ ngoài (webhook/log). Kích thước xuất bản: 422.77 x 362.83 pt (Trang 233, xref 510).",
            ROOT / "assets/diagrams/transaction-boundary.png",
            422.77,
            362.83,
        ),
        (
            "CHƯƠNG 15: VÒNG ĐỜI GIÁM SÁT TIẾN TRÌNH SỰ CỐ (INCIDENT COMMAND)",
            "Quy trình giám sát process con bằng os/exec: Tách biệt executable và arguments (không gọi shell ngầm) -> gắn context deadline timeout và buffer stdout/stderr độc lập -> cmd.Run() giám sát tiến trình -> phân loại chính xác 4 kết cục (Exit 0, Exit khác 0 có stderr chẩn đoán, Timeout/Cancel, Không thể khởi chạy). Result là bằng chứng quan sát cục bộ, không tự chứng minh nguyên nhân gốc incident. Kích thước xuất bản: 444.69 x 362.83 pt (Trang 272, xref 589).",
            ROOT / "assets/diagrams/incident-command-lifecycle.png",
            444.69,
            362.83,
        ),
    ]

    story = []

    for i, (fig_title, fig_caption, img_path, w_pt, h_pt) in enumerate(diagram_items):
        if i > 0:
            story.append(PageBreak())

        story.append(Paragraph(f"BẢN DUYỆT SƠ ĐỒ KỸ THUẬT // ĐỢT 02 (TRANG {i+1}/3)", title_style))
        story.append(Paragraph("Hiển thị 100% kích thước xuất bản thực tế (1:1 với Master PDF) • Grayscale thuần túy (R=G=B) • Chuẩn đặc tả kỹ thuật Go", subtitle_style))
        story.append(Paragraph(fig_title, fig_title_style))
        story.append(Paragraph(fig_caption, fig_caption_style))
        story.append(Image(str(img_path), width=w_pt, height=h_pt, hAlign="CENTER"))

    doc.build(story)
    print(f"Generated Chapters 12-15 preview PDF: {PREVIEW_PDF}")

    # Generate visual specimens from preview PDF
    pdf_doc = pymupdf.open(str(PREVIEW_PDF))
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        pix = page.get_pixmap(dpi=200)
        out_specimen = SPECIMENS_DIR / f"ch12_diagrams_p{page_num + 1:02d}.png"
        pix.save(str(out_specimen))
        print(f"  Diagram specimen page {page_num + 1:02d}: {out_specimen.name} ({pix.width}x{pix.height})")
    pdf_doc.close()
    print(f"Rendered {len(diagram_items)} specimen pages to {SPECIMENS_DIR}")

    return PREVIEW_PDF


if __name__ == "__main__":
    build_preview()
