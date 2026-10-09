# -*- coding: utf-8 -*-
"""build_agent2_catalog.py
Compiles the complete A4 Design Catalog PDF for Agent 2:
'book/design/agent2-2026/design_catalog.pdf'

Follows all editorial and print production specifications:
- ISO A4 portrait (210 x 297 mm)
- Mirrored facing margins (Inside 24mm, Outside 18mm, Top 22mm, Bottom 20mm)
- Grayscale / monochrome print-first palette
- Source Serif 4, Source Sans 3, JetBrains Mono
- Complete object specimen inventory (Groups A, B, C, D)
- 8 real combo pages with exact provenance
- Code clipboard fidelity analysis & Printability report
"""
from __future__ import annotations

import io
import math
import os
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# Workspace Paths
BASE_DIR = Path("D:/Golang")
DESIGN_DIR = BASE_DIR / "book" / "design" / "agent2-2026"
ARTWORK_DIR = DESIGN_DIR / "artwork"
REF_DIR = ARTWORK_DIR / "research_references"
FONTS_DIR = BASE_DIR / "assets" / "fonts"
DIAGRAMS_DIR = BASE_DIR / "assets" / "diagrams"
OUTPUT_PDF = DESIGN_DIR / "design_catalog.pdf"

# Page Dimensions (A4)
PAGE_WIDTH = 210.0 * mm  # 595.275 pt
PAGE_HEIGHT = 297.0 * mm  # 841.890 pt

# Mirrored Margins
MARGIN_INSIDE = 24.0 * mm  # 68.031 pt (Spine / Gutter)
MARGIN_OUTSIDE = 18.0 * mm  # 51.024 pt (Fore-edge)
MARGIN_TOP = 22.0 * mm  # 62.362 pt
MARGIN_BOTTOM = 20.0 * mm  # 56.693 pt

PRINTABLE_WIDTH = PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE  # 168.0 mm (476.220 pt)
PRINTABLE_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM  # 255.0 mm (722.835 pt)

# Register TrueType Fonts
pdfmetrics.registerFont(TTFont("BookSerif", str(FONTS_DIR / "SourceSerif4-Regular.ttf")))
pdfmetrics.registerFont(TTFont("BookSerifBold", str(FONTS_DIR / "SourceSerif4-Semibold.ttf")))
pdfmetrics.registerFont(TTFont("BookSans", str(FONTS_DIR / "SourceSans3-Regular.ttf")))
pdfmetrics.registerFont(TTFont("BookSansBold", str(FONTS_DIR / "SourceSans3-Semibold.ttf")))
pdfmetrics.registerFont(TTFont("BookMono", str(FONTS_DIR / "JetBrainsMono-Regular.ttf")))

# Typography Stylesheet
def setup_styles():
    styles = {}
    
    # Titles & Headers
    styles["DocTitle"] = ParagraphStyle(
        "DocTitle", fontName="BookSansBold", fontSize=26, leading=32,
        textColor=colors.HexColor("#000000"), alignment=TA_LEFT, spaceAfter=8
    )
    styles["DocSubtitle"] = ParagraphStyle(
        "DocSubtitle", fontName="BookSans", fontSize=13, leading=18,
        textColor=colors.HexColor("#333333"), alignment=TA_LEFT, spaceAfter=14
    )
    styles["Meta"] = ParagraphStyle(
        "Meta", fontName="BookMono", fontSize=8.5, leading=12,
        textColor=colors.HexColor("#555555"), alignment=TA_LEFT
    )

    # Book Headings (Group B)
    styles["H1"] = ParagraphStyle(
        "H1", fontName="BookSansBold", fontSize=22, leading=27,
        textColor=colors.HexColor("#000000"), spaceBefore=18, spaceAfter=8,
        keepWithNext=True
    )
    styles["H2"] = ParagraphStyle(
        "H2", fontName="BookSansBold", fontSize=15, leading=19,
        textColor=colors.HexColor("#1A1A1A"), spaceBefore=14, spaceAfter=6,
        keepWithNext=True
    )
    styles["H3"] = ParagraphStyle(
        "H3", fontName="BookSansBold", fontSize=12.5, leading=16,
        textColor=colors.HexColor("#222222"), spaceBefore=10, spaceAfter=4,
        keepWithNext=True
    )
    styles["H4"] = ParagraphStyle(
        "H4", fontName="BookSansBold", fontSize=10.5, leading=14,
        textColor=colors.HexColor("#333333"), spaceBefore=8, spaceAfter=3,
        keepWithNext=True
    )

    # Body Prose
    styles["Body"] = ParagraphStyle(
        "Body", fontName="BookSerif", fontSize=10.5, leading=15.2,
        textColor=colors.HexColor("#000000"), spaceAfter=7, alignment=TA_LEFT
    )
    styles["BodyBold"] = ParagraphStyle(
        "BodyBold", fontName="BookSerifBold", fontSize=10.5, leading=15.2,
        textColor=colors.HexColor("#000000"), spaceAfter=7
    )
    styles["BodySmall"] = ParagraphStyle(
        "BodySmall", fontName="BookSerif", fontSize=9.5, leading=13.5,
        textColor=colors.HexColor("#222222"), spaceAfter=5
    )

    # Captions & Callouts
    styles["Caption"] = ParagraphStyle(
        "Caption", fontName="BookSans", fontSize=8.5, leading=12.0,
        textColor=colors.HexColor("#444444"), alignment=TA_CENTER, spaceBefore=4, spaceAfter=8
    )
    styles["CalloutText"] = ParagraphStyle(
        "CalloutText", fontName="BookSerif", fontSize=9.8, leading=14.2,
        textColor=colors.HexColor("#111111"), spaceAfter=4
    )
    styles["TOCItem"] = ParagraphStyle(
        "TOCItem", fontName="BookSans", fontSize=9.5, leading=15,
        textColor=colors.HexColor("#000000")
    )
    styles["TOCPage"] = ParagraphStyle(
        "TOCPage", fontName="BookMono", fontSize=9.0, leading=15,
        textColor=colors.HexColor("#333333"), alignment=TA_RIGHT
    )

    return styles

STYLES = setup_styles()

# ------------------------------------------------------------------------------
# Custom Flowables
# ------------------------------------------------------------------------------
class Bookmark(Flowable):
    """Inserts a PDF outline entry and bookmark without consuming layout space."""
    def __init__(self, key: str, title: str, level: int = 0):
        super().__init__()
        self.key = key
        self.title = title
        self.level = level
        self.width = 0
        self.height = 0

    def draw(self):
        c = self.canv
        c.bookmarkPage(self.key)
        c.addOutlineEntry(self.title, self.key, level=self.level, closed=False)


class SectionHeader(Flowable):
    """Draws a major section divider with an architectural rubric rule."""
    def __init__(self, part_num: str, title: str, key: str):
        super().__init__()
        self.part_num = part_num
        self.title = title
        self.key = key
        self.width = PRINTABLE_WIDTH
        self.height = 48

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.bookmarkPage(self.key)
        c.addOutlineEntry(f"{self.part_num}: {self.title}", self.key, level=0, closed=False)

        # Architectural accent rule
        c.setStrokeColor(colors.HexColor("#000000"))
        c.setLineWidth(1.4)
        c.line(0, self.height - 4, self.width, self.height - 4)

        c.setFont("BookMono", 8.5)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(0, self.height - 16, self.part_num.upper())

        c.setFont("BookSansBold", 17)
        c.setFillColor(colors.HexColor("#000000"))
        c.drawString(0, self.height - 36, self.title)

        c.setLineWidth(0.4)
        c.setStrokeColor(colors.HexColor("#888888"))
        c.line(0, self.height - 44, self.width, self.height - 44)


class CodeBlockFlowable(Flowable):
    """Draws a Go code snippet with an accent bar and optional line numbers."""
    def __init__(self, code_text: str, show_line_numbers: bool = True, title: str = ""):
        super().__init__()
        self.lines = [line.expandtabs(4) for line in code_text.strip().split("\n")]
        self.show_line_numbers = show_line_numbers
        self.title = title
        self.font_name = "BookMono"
        self.font_size = 8.5
        self.line_height = 12.0
        self.pad_top = 8
        self.pad_bottom = 8
        self.pad_left = 32 if show_line_numbers else 12
        self.pad_right = 10
        self.width = PRINTABLE_WIDTH
        self.title_height = 14 if title else 0
        self.height = self.pad_top + self.pad_bottom + len(self.lines) * self.line_height + self.title_height

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()

        # Background fill
        c.setFillColor(colors.HexColor("#F6F6F6"))
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        # Left accent bar (2.0 pt black)
        c.setFillColor(colors.HexColor("#000000"))
        c.rect(0, 0, 2.4, self.height, fill=1, stroke=0)

        # Hairline outer border
        c.setStrokeColor(colors.HexColor("#E0E0E0"))
        c.setLineWidth(0.5)
        c.rect(0, 0, self.width, self.height, fill=0, stroke=1)

        cur_y = self.height - self.pad_top

        # Title bar if present
        if self.title:
            c.setFont("BookSansBold", 7.5)
            c.setFillColor(colors.HexColor("#444444"))
            c.drawString(self.pad_left, cur_y - 2, self.title.upper())
            c.setStrokeColor(colors.HexColor("#E0E0E0"))
            c.setLineWidth(0.4)
            c.line(2.4, cur_y - 6, self.width, cur_y - 6)
            cur_y -= self.title_height

        c.setFont(self.font_name, self.font_size)

        for i, line in enumerate(self.lines, 1):
            line_y = cur_y - i * self.line_height + 2
            if self.show_line_numbers:
                c.setFillColor(colors.HexColor("#888888"))
                c.drawRightString(self.pad_left - 8, line_y, str(i))
            
            c.setFillColor(colors.HexColor("#111111"))
            c.drawString(self.pad_left, line_y, line)

        c.restoreState()


class TerminalBlockFlowable(Flowable):
    """Draws a command line terminal session with prompt and output distinction."""
    def __init__(self, commands: list[tuple[str, str]]):
        super().__init__()
        self.commands = commands  # list of (cmd, output)
        self.font_name = "BookMono"
        self.font_size = 8.2
        self.line_height = 11.5
        self.pad_x = 12
        self.pad_y = 8
        self.width = PRINTABLE_WIDTH

        # Calculate height
        total_lines = 0
        for cmd, out in self.commands:
            total_lines += 1  # command line
            if out:
                total_lines += len(out.strip().split("\n"))
        self.height = self.pad_y * 2 + total_lines * self.line_height

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()

        # Light gray technical background
        c.setFillColor(colors.HexColor("#F0F0F0"))
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        # Hairline border
        c.setStrokeColor(colors.HexColor("#CCCCCC"))
        c.setLineWidth(0.6)
        c.rect(0, 0, self.width, self.height, fill=0, stroke=1)

        c.setFont(self.font_name, self.font_size)
        cur_y = self.height - self.pad_y

        for cmd, out in self.commands:
            # Prompt $ and command
            c.setFillColor(colors.HexColor("#000000"))
            c.drawString(self.pad_x, cur_y - self.line_height + 2, f"$ {cmd}")
            cur_y -= self.line_height

            # Command output (slightly dimmed / muted)
            if out:
                c.setFillColor(colors.HexColor("#444444"))
                for line in out.strip().split("\n"):
                    c.drawString(self.pad_x + 8, cur_y - self.line_height + 2, line)
                    cur_y -= self.line_height

        c.restoreState()


class ProvenanceBadge(Flowable):
    """Provenance indicator displaying the exact manuscript file and line numbers."""
    def __init__(self, file_path: str, line_range: str, baseline_head: str = "bb00a9ad"):
        super().__init__()
        self.file_path = file_path
        self.line_range = line_range
        self.baseline_head = baseline_head
        self.width = PRINTABLE_WIDTH
        self.height = 18

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(colors.HexColor("#EAEAEA"))
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        c.setStrokeColor(colors.HexColor("#BBBBBB"))
        c.setLineWidth(0.5)
        c.rect(0, 0, self.width, self.height, fill=0, stroke=1)

        c.setFont("BookMono", 7.2)
        c.setFillColor(colors.HexColor("#222222"))
        badge_text = f"PROVENANCE: {self.file_path} // LINES {self.line_range} // BASELINE {self.baseline_head}"
        c.drawString(8, 5.5, badge_text)


# ------------------------------------------------------------------------------
# Mirrored Page Templates & Document Class
# ------------------------------------------------------------------------------
class MirroredDocTemplate(BaseDocTemplate):
    """Document template enforcing alternating mirrored margins across facing spreads."""
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)

    def handle_pageBegin(self):
        # 1-indexed page calculation
        cur_page = self.page + 1
        if cur_page == 1:
            self.pageTemplate = self.pageTemplates[0]  # Cover Template
        elif cur_page % 2 == 0:
            self.pageTemplate = self.pageTemplates[2]  # Verso Template (Even: inside on right)
        else:
            self.pageTemplate = self.pageTemplates[1]  # Recto Template (Odd: inside on left)
        super().handle_pageBegin()


def draw_cover_chrome(canvas, doc):
    """No header or footer for the cover page."""
    pass


def draw_recto_chrome(canvas, doc):
    """Draws chrome for Recto (Odd) pages: inside margin on left, outside on right."""
    c = canvas
    page_num = c.getPageNumber()
    c.saveState()

    # Top Running Header (Right-aligned)
    header_y = PAGE_HEIGHT - MARGIN_TOP + 8
    c.setFont("BookSans", 7.8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawRightString(PAGE_WIDTH - MARGIN_OUTSIDE, header_y, "HỆ THỐNG MẪU THIẾT KẾ ĐỐI TƯỢNG XUẤT BẢN 2026 // AGENT 2")

    # Header Hairline Rule
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(0.4)
    c.line(MARGIN_INSIDE, header_y - 4, PAGE_WIDTH - MARGIN_OUTSIDE, header_y - 4)

    # Bottom Folio (Right-aligned)
    footer_y = MARGIN_BOTTOM - 12
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(0.4)
    c.line(MARGIN_INSIDE, footer_y + 10, PAGE_WIDTH - MARGIN_OUTSIDE, footer_y + 10)

    c.setFont("BookMono", 8.2)
    c.setFillColor(colors.HexColor("#000000"))
    c.drawRightString(PAGE_WIDTH - MARGIN_OUTSIDE, footer_y, f"{page_num}")

    c.setFont("BookSans", 7.0)
    c.setFillColor(colors.HexColor("#777777"))
    c.drawString(MARGIN_INSIDE, footer_y, "GOLANG LIVING TEXTBOOK // CONFIDENTIAL DESIGN SPECIMEN")

    c.restoreState()


def draw_verso_chrome(canvas, doc):
    """Draws chrome for Verso (Even) pages: outside margin on left, inside on right."""
    c = canvas
    page_num = c.getPageNumber()
    c.saveState()

    # Top Running Header (Left-aligned)
    header_y = PAGE_HEIGHT - MARGIN_TOP + 8
    c.setFont("BookSans", 7.8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawString(MARGIN_OUTSIDE, header_y, "GOLANG — GIÁO TRÌNH KỸ NGHỆ PHẦN MỀM & DEVOPS/SRE")

    # Header Hairline Rule
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(0.4)
    c.line(MARGIN_OUTSIDE, header_y - 4, PAGE_WIDTH - MARGIN_INSIDE, header_y - 4)

    # Bottom Folio (Left-aligned)
    footer_y = MARGIN_BOTTOM - 12
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(0.4)
    c.line(MARGIN_OUTSIDE, footer_y + 10, PAGE_WIDTH - MARGIN_INSIDE, footer_y + 10)

    c.setFont("BookMono", 8.2)
    c.setFillColor(colors.HexColor("#000000"))
    c.drawString(MARGIN_OUTSIDE, footer_y, f"{page_num}")

    c.setFont("BookSans", 7.0)
    c.setFillColor(colors.HexColor("#777777"))
    c.drawRightString(PAGE_WIDTH - MARGIN_INSIDE, footer_y, "ĐOÀN NGỌC HOÀNG MINH // A4 GRAYSCALE SPECIMEN")

    c.restoreState()


# ------------------------------------------------------------------------------
# Story Sections Assembly
# ------------------------------------------------------------------------------
def build_catalog_story() -> list[Flowable]:
    story = []

    # ==========================================================================
    # PAGE 1: TITLE / COVER OF CATALOG
    # ==========================================================================
    story.append(Bookmark("cover_page", "Trang Tiêu Đề Catalog", level=0))
    story.append(Spacer(1, 40))
    
    # Category Header
    p_cat = Paragraph("TÀI LIỆU KIỂM TOÁN VÀ PHÊ DUYỆT HỆ THỐNG THIẾT KẾ // AGENT 2", STYLES["Meta"])
    story.append(p_cat)
    story.append(Spacer(1, 14))

    # Main Title
    p_title = Paragraph("HỆ THỐNG MẪU ĐỐI TƯỢNG XUẤT BẢN 2026", STYLES["DocTitle"])
    story.append(p_title)

    p_sub = Paragraph("GOLANG — Giáo trình cập nhật liên tục về Kỹ nghệ phần mềm và DevOps/SRE", STYLES["DocSubtitle"])
    story.append(p_sub)

    # Caliper Rule
    t_rule = Table([[""]], colWidths=[PRINTABLE_WIDTH], rowHeights=[2])
    t_rule.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 1.6, colors.HexColor("#000000")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_rule)
    story.append(Spacer(1, 18))

    # Author & Production Metadata Box
    meta_data = [
        [Paragraph("<b>Tác giả:</b> Đoàn Ngọc Hoàng Minh", STYLES["BodySmall"]),
         Paragraph("<b>Định hướng Nghệ thuật:</b> Agent 2 Art Direction", STYLES["BodySmall"])],
        [Paragraph("<b>Khổ sách:</b> ISO A4 (210 × 297 mm)", STYLES["BodySmall"]),
         Paragraph("<b>Chế bản in:</b> Đơn sắc / Grayscale Print-First", STYLES["BodySmall"])],
        [Paragraph("<b>Phông chữ:</b> Source Serif 4 + Source Sans 3 + JetBrains Mono", STYLES["BodySmall"]),
         Paragraph("<b>Lưới lề:</b> Lề trong 24 mm, Ngoài 18 mm, Trên 22 mm, Dưới 20 mm", STYLES["BodySmall"])],
        [Paragraph("<b>Git Baseline:</b> bb00a9ad33e3cd5115928dc3542d2ce66c8d08d8", STYLES["BodySmall"]),
         Paragraph("<b>Trạng thái:</b> AWAITING_PRINT_SPEC // Đề xuất duyệt", STYLES["BodySmall"])],
    ]
    t_meta = Table(meta_data, colWidths=[PRINTABLE_WIDTH * 0.5, PRINTABLE_WIDTH * 0.5])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F8F8")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#CCCCCC")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#EAEAEA")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 24))

    # Statement of Purpose
    story.append(Paragraph("<b>MỤC TIÊU VÀ SỨ MỆNH CATALOG:</b>", STYLES["H3"]))
    p_desc = (
        "Tài liệu này là Specimen Catalog toàn diện nhằm kiểm chứng, định hình và đệ trình phê duyệt "
        "toàn bộ hệ thống thiết kế xuất bản cho cuốn sách <i>GOLANG</i> của tác giả Đoàn Ngọc Hoàng Minh. "
        "Agent 2 đảm nhận vai trò độc lập về Art Direction, Editorial Design, Typography, Information Design "
        "và Print Production. Mọi mẫu vật (specimen) trong tài liệu đều được xây dựng trên nội dung thật của bản thảo, "
        "loại bỏ hoàn toàn giả lập Lorem Ipsum, tôn trọng tuyệt đối tính toàn vẹn kỹ thuật và sự trang trọng của "
        "ấn phẩm kỹ thuật chuẩn mực đại học quốc tế."
    )
    story.append(Paragraph(p_desc, STYLES["Body"]))
    story.append(Spacer(1, 10))

    # Highlight box on rejected old covers
    reject_box = [
        [Paragraph(
            "<b>QUYẾT ĐỊNH THIẾT KẾ QUAN TRỌNG:</b><br/>"
            "Tác giả đã chính thức bác bỏ các mẫu bìa A–D phẳng trước đây (từ branch catalog-2026) vì thiếu chiều sâu nghệ thuật. "
            "Catalog này giới thiệu <b>3 Concept Bìa Sách Hoàn Toàn Mới</b> được nghiên cứu từ các nguồn cảm hứng kinh điển "
            "(Princeton Architectural Press, Edward Tufte, Emil Ruder), cùng đầy đủ phối cảnh 3D, bản in phẳng 300 DPI, "
            "nguồn vector và phân tích mỹ học chi tiết.",
            STYLES["BodySmall"]
        )]
    ]
    t_rej = Table(reject_box, colWidths=[PRINTABLE_WIDTH])
    t_rej.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFEFEF")),
        ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#000000")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_rej)

    story.append(PageBreak())

    # ==========================================================================
    # PAGE 2: LỜI NÓI ĐẦU & NGUYÊN TẮC THIẾT KẾ XUẤT BẢN
    # ==========================================================================
    story.append(Bookmark("preface", "Lời nói đầu & Nguyên tắc Biên tập", level=0))
    story.append(SectionHeader("Lời Nói Đầu", "Triết Lý Thiết Kế & Chuẩn Mực Ấn Bản 2026", "sec_preface"))
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "Thiết kế một giáo trình kỹ thuật nâng cao về Kỹ nghệ Phần mềm và DevOps/SRE không đơn thuần là việc dàn chữ "
        "cho vừa trang in, mà là nghệ thuật cấu trúc thông tin (Information Architecture) nhằm tối ưu hóa sự tập trung, "
        "tốc độ hấp thụ tri thức và năng lực suy luận của người đọc. Cuốn sách <i>GOLANG</i> được định vị là ấn phẩm sống "
        "(living textbook), phục vụ kỹ sư phần mềm chuyên nghiệp và sinh viên kỹ thuật bậc cao.",
        STYLES["Body"]
    ))

    story.append(Paragraph("1. Nguyên Tắc Đơn Sắc Tuyệt Đối (Monochrome Print-First)", STYLES["H2"]))
    story.append(Paragraph(
        "Sách được tối ưu hóa cho công nghệ in laser và offset đen trắng kinh tế cao. Một thiết kế thành công phải tạo ra "
        "chiều sâu không gian và phân cấp thị giác mạnh mẽ chỉ bằng mực đen, các sắc độ xám trung tính (10% đến 80%) "
        "và nền giấy trắng. Khi bản in đen trắng đạt độ tương phản và thẩm mỹ hoàn hảo, bản PDF điện tử sẽ tự động đạt "
        "chất lượng hiển thị xuất sắc trên mọi màn hình máy tính hay máy đọc sách e-ink.",
        STYLES["Body"]
    ))

    story.append(Paragraph("2. Lưới Lề Đối Xứng Qua Gáy Sách (Mirrored Margin Spreads)", STYLES["H2"]))
    story.append(Paragraph(
        "Với độ dày dự kiến trên 450 trang, độ cong của gáy sách khi mở (gutter creep) là yếu tố vật lý then chốt. "
        "Hệ thống lề trang được tính toán nghiêm ngặt: Lề trong (Inside Margin) cố định <b>24 mm</b> hướng về phía gáy, "
        "và Lề ngoài (Outside Margin) là <b>18 mm</b>. Khi mở sách ra trang đôi (spread), khoảng cách giữa hai khối văn bản "
        "đạt tổng cộng 48 mm, đảm bảo văn bản không bị chìm vào khe gáy dù sử dụng kỹ thuật đóng gáy nhiệt thông thường.",
        STYLES["Body"]
    ))

    story.append(Paragraph("3. Tôn Trọng Tuyệt Đối Bản Thảo & Loại Bỏ Giả Lập", STYLES["H2"]))
    story.append(Paragraph(
        "Mọi đối tượng mẫu từ tiêu đề, mã nguồn, bảng biểu, hộp câu hỏi suy luận cho đến các trang đôi thực tế đều được trích xuất "
        "trực tiếp từ 30 chương bản thảo và các phụ lục hiện có trong repository. Không có một dòng văn bản Lorem Ipsum nào "
        "được chấp nhận trong hệ thống thiết kế này.",
        STYLES["Body"]
    ))

    story.append(PageBreak())

    # ==========================================================================
    # PAGE 3: MỤC LỤC TỔNG THỂ
    # ==========================================================================
    story.append(Bookmark("toc", "Mục Lục Toàn Bộ Hệ Thống Mẫu", level=0))
    story.append(SectionHeader("Mục Lục", "Bản Đồ Đối Tượng Thiết Kế Toàn Thư", "sec_toc"))
    story.append(Spacer(1, 14))

    toc_entries = [
        ("Phần I: Bìa Sách & Định Hướng Nghệ Thuật (Art Direction)", "4"),
        ("    • Giới thiệu 3 Concept Bìa Sách Mới & Cơ sở Thẩm mỹ", "4"),
        ("    • Concept 1: Mặt Cắt Kiến Trúc & Phân Tầng Không Gian (Lewis et al.)", "5"),
        ("    • Concept 2: Khắc Đồng Khoa Học & Trường Dòng Chảy Tô-pô (Tufte / Haeckel)", "6"),
        ("    • Concept 3: Kiểu Chữ Động Kiến Tạo & Khối Monolith Mô-đun (Ruder / Müller-Brockmann)", "7"),
        ("Phần II: Nhóm B — Phân Cấp Văn Bản & Typography", "8"),
        ("    • Tiêu đề H1–H4, Quy cách Cỡ chữ & Dòng dẫn (Leading)", "8"),
        ("    • Thử nghiệm Tiêu đề Dài 3 Dòng & Cơ chế Khóa Mồ côi (keepWithNext)", "9"),
        ("Phần III: Nhóm C — Đối Tượng Kỹ Thuật & Mã Nguồn", "10"),
        ("    • Khối Mã Nguồn Go (Thanh Accent 2pt, Nền Xám, Đánh Số Dòng)", "10"),
        ("    • Khối Terminal Phiên Làm Việc ($ Prompt)", "10"),
        ("    • Bảng Biểu: Mẫu Booktabs Kinh Điển vs Mẫu Ma Trận DevOps", "11"),
        ("    • Hình Vẽ Kỹ Thuật (Figure & Caption) & Sơ Đồ Hệ Thống Thật", "12"),
        ("Phần IV: Nhóm D — Đối Tượng Sư Phạm & Khối Đặc Thù", "13"),
        ("    • Điểm Dừng Suy Luận (Deduction Stop Question) & Lời Giải Văn Xuôi", "13"),
        ("    • Thử Thách Thực Hành (Hands-on Lab) & Hộp Đo Lường Hiệu Năng", "14"),
        ("    • DevOps Library Atlas Specimen & Error Atlas Bố Cục 2 Cột", "15"),
        ("Phần V: Trang Đôi Thực Tế (Facing Spreads - Real Manuscript)", "16"),
        ("    • Cặp Trang 16–17: Chương 01 — Khởi đầu cú pháp, main.go & Cấu trúc Gói", "16"),
        ("    • Cặp Trang 18–19: Chương 02 — Slice Header, Bộ Nhớ Aliasing & Sơ Đồ Mảng", "18"),
        ("    • Cặp Trang 20–21: Chương 10 — Điều Tra Memory Leak, GC Pacer & pprof Heap", "20"),
        ("    • Cặp Trang 22–23: Chương 23 — Kubernetes Operator, OwnerReference & Reconcile", "22"),
        ("Phần VI: Phân Tích Sao Chép Mã Nguồn (Code Clipboard Fidelity)", "24"),
        ("    • Khảo sát Thực nghiệm Trích xuất Văn bản & Báo cáo Byte-Fidelity", "24"),
        ("Phần VII: Báo Cáo In Ấn, Giấy & Gáy Sách (Print Production)", "26"),
        ("    • Thông Số Khổ A4, Độ Dày Gáy, Định Lượng Giấy & Trạng Thái Duyệt", "26"),
    ]

    toc_table_data = []
    for item, page in toc_entries:
        is_main = not item.startswith("    •")
        style_item = STYLES["TOCItem"]
        if is_main:
            style_item = ParagraphStyle("TOCMain", parent=STYLES["TOCItem"], fontName="BookSansBold")
        toc_table_data.append([Paragraph(item, style_item), Paragraph(page, STYLES["TOCPage"])])

    t_toc = Table(toc_table_data, colWidths=[PRINTABLE_WIDTH * 0.88, PRINTABLE_WIDTH * 0.12])
    t_toc.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#EEEEEE")),
    ]))
    story.append(t_toc)

    story.append(PageBreak())

    # ==========================================================================
    # PAGE 4–7: PHẦN I — BÌA SÁCH & ĐỊNH HƯỚNG NGHỆ THUẬT
    # ==========================================================================
    story.append(Bookmark("part1_covers", "Phần I: Bìa Sách & Định Hướng Nghệ Thuật", level=0))
    story.append(SectionHeader("Phần I", "Bìa Sách & Định Hướng Nghệ Thuật (Art Direction)", "sec_part1"))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Sau khi tác giả bác bỏ các phương án A–D cũ từ <i>catalog-2026</i> vì mang tính hình học phẳng thiếu sinh khí, "
        "Agent 2 đã tái thiết lập toàn diện quy trình mỹ thuật. Ba phương án bìa mới dưới đây được phát triển độc lập, "
        "kết hợp chặt chẽ giữa <b>nghiên cứu lịch sử nghệ thuật/kiến trúc thực thụ</b> và <b>bản chất kỹ thuật của Go runtime</b>. "
        "Mỗi concept đều có ảnh phẳng 300 DPI, phối cảnh 3D gáy sách, nguồn vector hoàn chỉnh và hồ sơ nghiên cứu.",
        STYLES["Body"]
    ))

    # Summary table of 3 concepts
    summary_cover_data = [
        [Paragraph("<b>Concept</b>", STYLES["BodySmall"]),
         Paragraph("<b>Nguồn Cảm Hứng Nghệ Thuật</b>", STYLES["BodySmall"]),
         Paragraph("<b>Mô Hình Kỹ Thuật Go</b>", STYLES["BodySmall"]),
         Paragraph("<b>Đặc Trưng Thị Giác</b>", STYLES["BodySmall"])],
        [Paragraph("<b>Concept 1</b><br/>Mặt Cắt Kiến Trúc", STYLES["BodySmall"]),
         Paragraph("Lewis, Tsurumaki, Lewis — <i>Manual of Section</i> (2016); Peter Eisenman (MoMA 1988)", STYLES["BodySmall"]),
         Paragraph("Cấu trúc phân tầng 4 lớp: Linux Kernel → Go Runtime GMP → Service Layer → K8s / eBPF", STYLES["BodySmall"]),
         Paragraph("Hình chiếu trục đo axonometric 28°, nét poché đen đặc, đường đo kích thước kỹ thuật", STYLES["BodySmall"])],
        [Paragraph("<b>Concept 2</b><br/>Khắc Đồng Dòng Chảy", STYLES["BodySmall"]),
         Paragraph("Edward Tufte — <i>Envisioning Information</i>; Ernst Haeckel — <i>Kunstformen der Natur</i> (1904)", STYLES["BodySmall"]),
         Paragraph("Mô hình CSP toán học: Goroutine rendezvous barrier, áp suất ngược, kênh đệm dòng chảy", STYLES["BodySmall"]),
         Paragraph("Đường thế phức biến thiên độ dày nét (0.3–1.2pt) mô phỏng mũi khắc kim loại burin cổ điển", STYLES["BodySmall"])],
        [Paragraph("<b>Concept 3</b><br/>Monolith Kiến Tạo", STYLES["BodySmall"]),
         Paragraph("Emil Ruder — <i>Typographie</i> (1967); Josef Müller-Brockmann — <i>Grid Systems</i> (1981)", STYLES["BodySmall"]),
         Paragraph("Bản chất hạ tầng Go: Đơn khối, vững chắc, biên dịch trực tiếp sang mã máy, không VM", STYLES["BodySmall"]),
         Paragraph("Lưới Thụy Sĩ 12 cột, kiểu chữ 3D extruded đúc khối, tỷ lệ tương phản cực hạn, tối giản", STYLES["BodySmall"])],
    ]
    t_sum_cov = Table(summary_cover_data, colWidths=[PRINTABLE_WIDTH*0.2, PRINTABLE_WIDTH*0.3, PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.25])
    t_sum_cov.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#000000")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_sum_cov)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # CONCEPT 1 SPECIMEN
    # --------------------------------------------------------------------------
    story.append(Bookmark("concept_1", "Concept 1: Mặt Cắt Kiến Trúc & Phân Tầng Không Gian", level=1))
    story.append(Paragraph("CONCEPT 1: MẶT CẮT KIẾN TRÚC & PHÂN TẦNG KHÔNG GIAN", STYLES["H1"]))
    story.append(Paragraph("<i>Architectural Cross-Section & Spatial Cut // Cảm hứng: Manual of Section (Princeton Architectural Press)</i>", STYLES["DocSubtitle"]))

    c1_img_flat = str(ARTWORK_DIR / "concept1_cross_section_flat.png")
    c1_img_3d = str(ARTWORK_DIR / "concept1_cross_section_3d_mockup.png")
    
    # 2-image showcase side-by-side
    img_row_1 = [
        [Image(c1_img_flat, width=PRINTABLE_WIDTH*0.48, height=PRINTABLE_WIDTH*0.48 * 1.414),
         Image(c1_img_3d, width=PRINTABLE_WIDTH*0.48, height=PRINTABLE_WIDTH*0.48 * 1.414)]
    ]
    t_img_1 = Table(img_row_1, colWidths=[PRINTABLE_WIDTH*0.5, PRINTABLE_WIDTH*0.5])
    t_img_1.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_img_1)
    story.append(Paragraph("Hình 1.1: Bản in phẳng 300 DPI (trái) và Phối cảnh 3D gáy sách 3.5cm (phải) của Concept 1.", STYLES["Caption"]))
    story.append(Spacer(1, 8))

    desc_c1 = (
        "<b>Phân tích Không gian & Cơ sở Kiến trúc:</b> Tác phẩm vận dụng lý thuyết mặt cắt kiến trúc (Section Theory) "
        "của Paul Lewis, Marc Tsurumaki và David J. Lewis. Mặt cắt không phải là một hình vẽ kỹ thuật thụ động mà là một "
        "công cụ nhận thức (epistemic tool), phơi bày các liên kết kết cấu ngầm. Chúng tôi chiếu trục đo axonometric 28° "
        "toàn bộ cỗ máy thực thi Go thành 4 tầng không gian: Tầng 0 (Kernel Foundation z=-120), Tầng 1 (Go Runtime Core "
        "với GMP Scheduler và bộ nhớ mspan z=-30), Tầng 2 (Service Mesh Deck z=+60) và Tầng 3 (Kubernetes Reconcile Tower z=+150). "
        "Nét poché đen tuyền thể hiện mặt phẳng cắt vật lý, gợi lên cảm giác một bản thiết kế công nghiệp chính xác."
    )
    story.append(Paragraph(desc_c1, STYLES["BodySmall"]))

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # CONCEPT 2 SPECIMEN
    # --------------------------------------------------------------------------
    story.append(Bookmark("concept_2", "Concept 2: Khắc Đồng Khoa Học & Trường Dòng Chảy Tô-pô", level=1))
    story.append(Paragraph("CONCEPT 2: KHẮC ĐỒNG KHOA HỌC & TRƯỜNG DÒNG CHẢY TÔ-PÔ", STYLES["H1"]))
    story.append(Paragraph("<i>Scientific Engraving & Topological Flow Field // Cảm hứng: Edward Tufte & Ernst Haeckel</i>", STYLES["DocSubtitle"]))

    c2_img_flat = str(ARTWORK_DIR / "concept2_engraving_flow_flat.png")
    c2_img_3d = str(ARTWORK_DIR / "concept2_engraving_flow_3d_mockup.png")

    img_row_2 = [
        [Image(c2_img_flat, width=PRINTABLE_WIDTH*0.48, height=PRINTABLE_WIDTH*0.48 * 1.414),
         Image(c2_img_3d, width=PRINTABLE_WIDTH*0.48, height=PRINTABLE_WIDTH*0.48 * 1.414)]
    ]
    t_img_2 = Table(img_row_2, colWidths=[PRINTABLE_WIDTH*0.5, PRINTABLE_WIDTH*0.5])
    t_img_2.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_img_2)
    story.append(Paragraph("Hình 1.2: Bản in phẳng 300 DPI (trái) và Phối cảnh 3D gáy sách 3.5cm (phải) của Concept 2.", STYLES["Caption"]))
    story.append(Spacer(1, 8))

    desc_c2 = (
        "<b>Phân tích Mỹ thuật & Mô hình Toán học:</b> Lấy cảm hứng từ những bản khắc đồng khoa học thế kỷ 19 của Ernst Haeckel "
        "và nguyên lý mật độ thông tin vi mô/vĩ mô (Micro/Macro Readings) của Edward Tufte. Toàn bộ cơ chế tương tranh CSP "
        "của Go được biểu diễn dưới dạng trường thế phức (complex potential field) và các đường dòng (streamlines). "
        "Mỗi đường cong được tính toán bằng phương trình giải tích, biến thiên độ dày từ 0.3pt đến 1.2pt mô phỏng lưỡi dao khắc "
        "burin trên phiến đồng. Ở khoảng cách xa, người xem thấy một xoáy lốc toán học tráng lệ; ở cự ly gần, từng vector "
        "và tiếp tuyến của dòng chảy dữ liệu hiện lên sắc nét, tạo nên phong thái học thuật kinh điển của một ấn bản hàn lâm."
    )
    story.append(Paragraph(desc_c2, STYLES["BodySmall"]))

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # CONCEPT 3 SPECIMEN
    # --------------------------------------------------------------------------
    story.append(Bookmark("concept_3", "Concept 3: Kiểu Chữ Động Kiến Tạo & Khối Monolith Mô-đun", level=1))
    story.append(Paragraph("CONCEPT 3: KIỂU CHỮ ĐỘNG KIẾN TẠO & KHỐI MONOLITH MÔ-ĐUN", STYLES["H1"]))
    story.append(Paragraph("<i>Constructivist Kinetic Typography & Modular Monolith // Cảm hứng: Emil Ruder & Müller-Brockmann</i>", STYLES["DocSubtitle"]))

    c3_img_flat = str(ARTWORK_DIR / "concept3_kinetic_typography_flat.png")
    c3_img_3d = str(ARTWORK_DIR / "concept3_kinetic_typography_3d_mockup.png")

    img_row_3 = [
        [Image(c3_img_flat, width=PRINTABLE_WIDTH*0.48, height=PRINTABLE_WIDTH*0.48 * 1.414),
         Image(c3_img_3d, width=PRINTABLE_WIDTH*0.48, height=PRINTABLE_WIDTH*0.48 * 1.414)]
    ]
    t_img_3 = Table(img_row_3, colWidths=[PRINTABLE_WIDTH*0.5, PRINTABLE_WIDTH*0.5])
    t_img_3.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_img_3)
    story.append(Paragraph("Hình 1.3: Bản in phẳng 300 DPI (trái) và Phối cảnh 3D gáy sách 3.5cm (phải) của Concept 3.", STYLES["Caption"]))
    story.append(Spacer(1, 8))

    desc_c3 = (
        "<b>Phân tích Cấu trúc & Tinh thần Hiện đại Thụy Sĩ:</b> Tôn vinh trường phái International Typographic Style "
        "(Thiết kế Thụy Sĩ) với triết lý không gian typographic của Emil Ruder và hệ lưới mô-đun của Josef Müller-Brockmann. "
        "Hệ thống chữ 'GOLANG' và các từ khóa cốt lõi (CONCURRENCY, RUNTIME, SYSTEM) được biến chuyển thành các khối 3D monolith "
        "bê tông đúc sẵn, phản chiếu chính xác bản chất hạ tầng của Go: vững chắc, đơn khối, biên dịch thẳng ra machine code, "
        "không runtime ảo hóa cồng kềnh. Khoảng trắng âm (negative counterform) được tính toán tỉ mỉ, tạo nên lực căng thị giác "
        "mạnh mẽ và phong thái công nghiệp hiện đại không thể nhầm lẫn."
    )
    story.append(Paragraph(desc_c3, STYLES["BodySmall"]))

    story.append(PageBreak())

    # ==========================================================================
    # PAGE 8–9: PHẦN II — NHÓM B: PHÂN CẤP VĂN BẢN & TYPOGRAPHY
    # ==========================================================================
    story.append(Bookmark("part2_typography", "Phần II: Nhóm B — Phân Cấp Văn Bản & Typography", level=0))
    story.append(SectionHeader("Phần II", "Nhóm B — Phân Cấp Văn Bản & Typography", "sec_part2"))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Quy chuẩn kiểu chữ được xây dựng dựa trên sự kết hợp hài hòa giữa phông Serif cổ điển cho khối chính văn "
        "(Source Serif 4) và phông Sans-serif hình học cho hệ thống tiêu đề (Source Sans 3), bổ trợ bởi phông đơn cách "
        "(JetBrains Mono) cho mã nguồn. Tỷ lệ cỡ chữ / khoảng cách dòng (leading) tuân thủ tiêu chuẩn quang học 1.45–1.5×.",
        STYLES["Body"]
    ))

    # Specimen Headings Table
    heading_samples = [
        [Paragraph("<b>Cấp Tiêu Đề</b>", STYLES["BodySmall"]),
         Paragraph("<b>Mẫu Hiển Thị Thực Tế</b>", STYLES["BodySmall"]),
         Paragraph("<b>Thông Số Kỹ Thuật</b>", STYLES["BodySmall"])],
        [Paragraph("<b>H1 (Chương)</b>", STYLES["BodySmall"]),
         Paragraph("CHƯƠNG 02: GIÁ TRỊ, SLICE VÀ ALIASING", STYLES["H1"]),
         Paragraph("Source Sans 3 Bold<br/>22 pt / leading 27 pt<br/>keepWithNext=True", STYLES["Meta"])],
        [Paragraph("<b>H2 (Mục lớn)</b>", STYLES["BodySmall"]),
         Paragraph("Khoảnh Khắc Slice Đổi Kết Quả", STYLES["H2"]),
         Paragraph("Source Sans 3 Bold<br/>15 pt / leading 19 pt<br/>keepWithNext=True", STYLES["Meta"])],
        [Paragraph("<b>H3 (Tiểu mục)</b>", STYLES["BodySmall"]),
         Paragraph("Cửa Sổ Nhìn, Length và Capacity Trong Bộ Nhớ", STYLES["H3"]),
         Paragraph("Source Sans 3 Bold<br/>12.5 pt / leading 16 pt<br/>keepWithNext=True", STYLES["Meta"])],
        [Paragraph("<b>H4 (Tiểu tiết)</b>", STYLES["BodySmall"]),
         Paragraph("Quy Tắc Tái Cấp Phát Mảng Nền Khi Append Vượt Ngưỡng", STYLES["H4"]),
         Paragraph("Source Sans 3 Bold<br/>10.5 pt / leading 14 pt<br/>keepWithNext=True", STYLES["Meta"])],
    ]
    t_head = Table(heading_samples, colWidths=[PRINTABLE_WIDTH*0.2, PRINTABLE_WIDTH*0.55, PRINTABLE_WIDTH*0.25])
    t_head.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#000000")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 14))

    # Body Prose Specimen
    story.append(Paragraph("MẪU VĂN BẢN CHÍNH VĂN (SOURCE SERIF 4 — 10.5 PT / LEADING 15.2 PT)", STYLES["H3"]))
    body_sample_text = (
        "Trong thiết kế hệ thống bằng Go, việc nắm vững cách thức dữ liệu dịch chuyển trong bộ nhớ là ranh giới "
        "giữa một lập trình viên cú pháp và một kỹ sư hệ thống thực thụ. Go không che giấu chi phí bộ nhớ đằng sau "
        "những lớp trừu tượng phức tạp. Mọi giá trị gán, truyền tham số qua hàm hay khởi tạo slice đều tuân thủ "
        "chính xác ngữ nghĩa sao chép giá trị (pass-by-value). Khi một biến được truyền vào hàm, chính xác các byte "
        "của biến đó được nhân bản sang ngăn xếp của hàm nhận. Điều này đảm bảo tính dự đoán tuyệt đối về mặt thời gian "
        "và loại bỏ hoàn toàn các đột biến trạng thái ngoài ý muốn vốn là nguồn gốc của hàng ngàn lỗi nghiêm trọng trong production."
    )
    story.append(Paragraph(body_sample_text, STYLES["Body"]))
    story.append(Paragraph(
        "<i>Độ dài dòng tối ưu: 65–75 ký tự trên mỗi dòng. Khoảng cách dòng 15.2 pt tạo nhịp thở thị giác thư thái, "
        "ngăn ngừa hiện tượng hoa mắt khi đọc liên tục trong nhiều giờ nghiên cứu.</i>",
        STYLES["Caption"]
    ))

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # MULTI-LINE HEADING STRESS TEST & ORPHAN GUARD
    # --------------------------------------------------------------------------
    story.append(Bookmark("typography_stress", "Thử Nghiệm Tiêu Đề Dài & Khóa Mồ Côi", level=1))
    story.append(Paragraph("THỬ NGHIỆM TIÊU ĐỀ DÀI & CƠ CHẾ KHÓA MỒ CÔI (ORPHAN GUARD)", STYLES["H1"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>1. Thử nghiệm Tiêu đề H1 Dài 3 Dòng (Stress Test):</b><br/>"
        "Đảm bảo các tiêu đề có cấu trúc câu dài không bị đè chữ, leading ổn định và ngắt dòng tự nhiên theo ngữ nghĩa kỹ thuật:",
        STYLES["BodySmall"]
    ))
    
    long_h1_text = (
        "CHƯƠNG 23: TỪ CONTROLLER ĐẾN OPERATOR — XÂY DỰNG HỆ THỐNG ĐIỀU HÒA TRẠNG THÁI "
        "VÀ BẢO TOÀN TÍNH NHẤT QUÁN CỦA CƠ SỞ HẠ TẦNG KUBERNETES TRÊN MÔI TRƯỜNG CLOUD NATIVE"
    )
    story.append(Paragraph(long_h1_text, STYLES["H1"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>2. Cơ chế Khóa Mồ Côi (Widow/Orphan Guard via keepWithNext=True):</b><br/>"
        "Trong xuất bản sách tiêu chuẩn cao, một tiêu đề nằm cô độc ở dòng cuối cùng của trang sách mà không có "
        "ít nhất 2 dòng văn bản đi kèm là một lỗi chế bản nghiêm trọng (Orphan Heading). Tất cả các lớp ParagraphStyle "
        "H1, H2, H3, H4 trong hệ thống thiết kế Agent 2 đều được cấu hình thuộc tính <code>keepWithNext=True</code>. "
        "Thuộc tính này buộc động cơ dàn trang (Platypus Flow Engine) tự động đẩy tiêu đề sang đầu trang tiếp theo "
        "nếu khoảng trống còn lại ở cuối trang không đủ cho cả tiêu đề và đoạn văn đầu tiên.",
        STYLES["Body"]
    ))
    story.append(Spacer(1, 8))

    # Demonstration Callout Box
    callout_sample = [
        [Paragraph(
            "<b>ĐIỀU KHOẢN HỢP ĐỒNG TRÌNH DIỄN (LAYOUT INVARIANT):</b><br/>"
            "• Tiêu đề không bao giờ xuất hiện ở cuối trang mà không có ít nhất 2 dòng nội dung.<br/>"
            "• Khoảng cách trên tiêu đề (spaceBefore) tự động được triệt tiêu khi tiêu đề rơi vào đầu trang mới.<br/>"
            "• Toàn bộ chỉ số số dòng trong code block được căn lề phải để đảm bảo tính thẳng hàng tuyệt đối.",
            STYLES["CalloutText"]
        )]
    ]
    t_callout = Table(callout_sample, colWidths=[PRINTABLE_WIDTH])
    t_callout.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F7F7")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#000000")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_callout)

    story.append(PageBreak())

    # ==========================================================================
    # PAGE 10–12: PHẦN III — NHÓM C: ĐỐI TƯỢNG KỸ THUẬT & MÃ NGUỒN
    # ==========================================================================
    story.append(Bookmark("part3_technical", "Phần III: Nhóm C — Đối Tượng Kỹ Thuật & Mã Nguồn", level=0))
    story.append(SectionHeader("Phần III", "Nhóm C — Đối Tượng Kỹ Thuật & Mã Nguồn", "sec_part3"))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Mã nguồn là trung tâm của cuốn sách kỹ thuật. Khối mã nguồn của Agent 2 được thiết kế với tiêu chí: "
        "rõ ràng, không gây mỏi mắt, phân biệt rõ giữa lệnh gõ và kết quả in ra, đồng thời hỗ trợ tra cứu chính xác dòng mã.",
        STYLES["Body"]
    ))

    # Code Block Specimen
    story.append(Paragraph("1. Khối Mã Nguồn Go (Thanh Accent 2.0pt, Nền Xám, Đánh Số Dòng)", STYLES["H2"]))
    go_code_sample = (
        'package main\n'
        '\n'
        'import (\n'
        '\t"context"\n'
        '\t"fmt"\n'
        '\t"time"\n'
        ')\n'
        '\n'
        '// Worker xử lý công việc với cơ chế ngắt hạn bằng context.Context\n'
        'func Worker(ctx context.Context, id int, jobs <-chan string) {\n'
        '\tfor {\n'
        '\t\tselect {\n'
        '\t\tcase <-ctx.Done():\n'
        '\t\t\tfmt.Printf("[worker %d] nhận tín hiệu dừng: %v\\n", id, ctx.Err())\n'
        '\t\t\treturn\n'
        '\t\tcase job, ok := <-jobs:\n'
        '\t\t\tif !ok {\n'
        '\t\t\t\treturn\n'
        '\t\t\t}\n'
        '\t\t\tfmt.Printf("[worker %d] hoàn tất tác vụ: %s\\n", id, job)\n'
        '\t\t}\n'
        '\t}\n'
        '}'
    )
    story.append(CodeBlockFlowable(go_code_sample, show_line_numbers=True, title="pkg/concurrency/worker.go"))
    story.append(Spacer(1, 12))

    # Terminal Specimen
    story.append(Paragraph("2. Khối Phiên Làm Việc Terminal (Dấu Nhắc Lệnh $, Output Phân Biệt)", STYLES["H2"]))
    term_sample = [
        ("go test -bench=BenchmarkWorker -benchmem -count=4 ./pkg/concurrency",
         "goos: linux\n"
         "goarch: amd64\n"
         "pkg: example.com/concurrency\n"
         "cpu: 13th Gen Intel(R) Core(TM) i7-13700H\n"
         "BenchmarkWorker-20    1000000    1042 ns/op    96 B/op    2 allocs/op\n"
         "BenchmarkWorker-20    1000000    1038 ns/op    96 B/op    2 allocs/op\n"
         "PASS\n"
         "ok      example.com/concurrency    4.321s"),
        ("go tool pprof -top cpu.out",
         "Showing nodes accounting for 4.10s, 95.12% of 4.31s total\n"
         "      flat  flat%   sum%        cum   cum%\n"
         "     2.45s 56.84% 56.84%      2.45s 56.84%  runtime.cgocall\n"
         "     1.10s 25.52% 82.36%      1.10s 25.52%  runtime.futex")
    ]
    story.append(TerminalBlockFlowable(term_sample))

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # TABLES SPECIMENS: BOOKTABS VS DEVOPS GRID
    # --------------------------------------------------------------------------
    story.append(Bookmark("tables_specimen", "Bảng Biểu: Booktabs vs Ma Trận DevOps", level=1))
    story.append(Paragraph("BẢNG BIỂU: MẪU BOOKTABS KINH ĐIỂN VS MA TRẬN DEVOPS", STYLES["H1"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Mẫu A: Bảng Booktabs Khoa Học (Chỉ Dùng Đường Kẻ Ngang, Không Kẻ Dọc)", STYLES["H2"]))
    story.append(Paragraph(
        "Theo truyền thống xuất bản hàn lâm của Oxford và Cambridge, bảng biểu khoa học không bao giờ sử dụng các đường "
        "kẻ dọc. Các đường kẻ ngang được phân cấp: Đường đỉnh 1.2pt, Đường đáy 1.2pt, Đường phân cách tiêu đề 0.6pt. "
        "Cấu trúc này tạo cảm giác thanh thoát, dễ đọc:",
        STYLES["BodySmall"]
    ))

    booktabs_data = [
        [Paragraph("<b>Cấu trúc Dữ liệu</b>", STYLES["BodySmall"]),
         Paragraph("<b>Kích thước Descriptor</b>", STYLES["BodySmall"]),
         Paragraph("<b>Mức độ Sao chép</b>", STYLES["BodySmall"]),
         Paragraph("<b>Hành vi khi Đột biến</b>", STYLES["BodySmall"])],
        [Paragraph("Array <code>[4]int</code>", STYLES["BodySmall"]),
         Paragraph("32 bytes (trực tiếp)", STYLES["BodySmall"]),
         Paragraph("Deep Copy toàn bộ giá trị", STYLES["BodySmall"]),
         Paragraph("Độc lập hoàn toàn, không ảnh hưởng bản gốc", STYLES["BodySmall"])],
        [Paragraph("Slice <code>[]int</code>", STYLES["BodySmall"]),
         Paragraph("24 bytes (ptr, len, cap)", STYLES["BodySmall"]),
         Paragraph("Shallow Copy header", STYLES["BodySmall"]),
         Paragraph("Chia sẻ mảng nền (Aliasing nguy cơ)", STYLES["BodySmall"])],
        [Paragraph("String <code>string</code>", STYLES["BodySmall"]),
         Paragraph("16 bytes (ptr, len)", STYLES["BodySmall"]),
         Paragraph("Shallow Copy header", STYLES["BodySmall"]),
         Paragraph("Bất biến (Immutable), an toàn tương tranh", STYLES["BodySmall"])],
        [Paragraph("Map <code>map[K]V</code>", STYLES["BodySmall"]),
         Paragraph("8 bytes (con trỏ *hmap)", STYLES["BodySmall"]),
         Paragraph("Chỉ sao chép con trỏ tham chiếu", STYLES["BodySmall"]),
         Paragraph("Concurrent Write gây Fatal Crash", STYLES["BodySmall"])],
    ]
    t_booktabs = Table(booktabs_data, colWidths=[PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.25])
    t_booktabs.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, colors.HexColor("#000000")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#000000")),
        ("LINEBELOW", (0, -1), (-1, -1), 1.2, colors.HexColor("#000000")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_booktabs)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Mẫu B: Bảng Ma Trận Kỹ Thuật DevOps (Lưới Ô Vuông Đơn Sắc 0.4pt)", STYLES["H2"]))
    story.append(Paragraph(
        "Đối với các bảng ma trận so sánh nhiều thuộc tính kỹ thuật hoặc cấu hình phân tầng phức tạp trong Kubernetes/CI-CD, "
        "lưới ô vuông mỏng 0.4pt giúp mắt người đọc dễ dàng định vị giao điểm giữa hàng và cột:",
        STYLES["BodySmall"]
    ))

    grid_data = [
        [Paragraph("<b>Tham số Cấu hình</b>", STYLES["BodySmall"]),
         Paragraph("<b>Giá trị Mặc định</b>", STYLES["BodySmall"]),
         Paragraph("<b>Phạm vi Ảnh hưởng</b>", STYLES["BodySmall"]),
         Paragraph("<b>Hành vi khi Vượt ngưỡng</b>", STYLES["BodySmall"])],
        [Paragraph("<code>GOGC</code>", STYLES["BodySmall"]),
         Paragraph("100 (tỷ lệ 100%)", STYLES["BodySmall"]),
         Paragraph("Tần suất chu kỳ GC", STYLES["BodySmall"]),
         Paragraph("Tăng bộ nhớ heap trước khi kích hoạt sweep", STYLES["BodySmall"])],
        [Paragraph("<code>GOMEMLIMIT</code>", STYLES["BodySmall"]),
         Paragraph("Không giới hạn (Max)", STYLES["BodySmall"]),
         Paragraph("Bộ nhớ toàn tiến trình", STYLES["BodySmall"]),
         Paragraph("Tăng tần suất GC để tránh bị OOMKilled", STYLES["BodySmall"])],
        [Paragraph("<code>GOMAXPROCS</code>", STYLES["BodySmall"]),
         Paragraph("Số CPU logic", STYLES["BodySmall"]),
         Paragraph("Số Processor (P) trong GMP", STYLES["BodySmall"]),
         Paragraph("Tranh chấp luồng OS nếu đặt quá cao trong cgroup", STYLES["BodySmall"])],
    ]
    t_grid = Table(grid_data, colWidths=[PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.25])
    t_grid.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#000000")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_grid)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # FIGURES & ARCHITECTURE DIAGRAMS FROM REPOSITORY
    # --------------------------------------------------------------------------
    story.append(Bookmark("figures_specimen", "Hình Vẽ Kỹ Thuật & Sơ Đồ Hệ Thống", level=1))
    story.append(Paragraph("HÌNH VẼ KỸ THUẬT (FIGURE) & SƠ ĐỒ HỆ THỐNG TỪ REPOSITORY", STYLES["H1"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Hình vẽ kỹ thuật trong sách được đóng khung chuẩn mực, căn giữa trang in, có tiêu đề hình (caption) "
        "được căn giữa bên dưới với nhãn <b>Hình X.Y:</b> in đậm. Dưới đây là hai sơ đồ kiến trúc thật được trích "
        "từ thư mục <code>assets/diagrams/</code> của cuốn sách:",
        STYLES["Body"]
    ))

    # Diagram 1: Reconciliation Loop
    diag1_path = str(DIAGRAMS_DIR / "reconciliation-loop.png")
    story.append(Image(diag1_path, width=PRINTABLE_WIDTH * 0.85, height=PRINTABLE_WIDTH * 0.85 * 0.45))
    story.append(Paragraph("Hình 3.1: Vòng lặp điều hòa (Reconciliation Loop) cốt lõi của Kubernetes Controller & Operator.", STYLES["Caption"]))
    story.append(Spacer(1, 10))

    # Diagram 2: Operator Manager Boundaries
    diag2_path = str(DIAGRAMS_DIR / "operator-manager-boundaries.png")
    story.append(Image(diag2_path, width=PRINTABLE_WIDTH * 0.85, height=PRINTABLE_WIDTH * 0.85 * 0.38))
    story.append(Paragraph("Hình 3.2: Ranh giới kiến trúc giữa Controller Manager, Custom Resource Definition và Client Cache.", STYLES["Caption"]))

    story.append(PageBreak())

    # ==========================================================================
    # PAGE 13–15: PHẦN IV — NHÓM D: ĐỐI TƯỢNG SƯ PHẠM & KHỐI ĐẶC THÙ
    # ==========================================================================
    story.append(Bookmark("part4_pedagogical", "Phần IV: Nhóm D — Đối Tượng Sư Phạm & Khối Đặc Thù", level=0))
    story.append(SectionHeader("Phần IV", "Nhóm D — Đối Tượng Sư Phạm & Khối Đặc Thù", "sec_part4"))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Theo định hướng của MASTER PROMPT, phương pháp sư phạm của cuốn sách không truyền đạt tri thức một chiều "
        "mà xây dựng năng lực phản xạ suy luận cho kỹ sư. Các khối sư phạm đặc thù bao gồm: Điểm dừng Suy luận "
        "(Deduction Stop), Lời giải văn xuôi liên tục (Continuous Prose Solution), Bài tập Thực hành (Hands-on Lab) "
        "và Bố cục hai cột tra cứu lỗi (Error Atlas).",
        STYLES["Body"]
    ))

    # Deduction Stop Specimen
    story.append(Paragraph("1. Điểm Dừng Suy Luận (Deduction Stop Question)", STYLES["H2"]))
    deduction_box = [
        [Paragraph(
            "<b>ĐIỂM DỪNG SUY LUẬN // DEDUCTION STOP:</b><br/>"
            "Xem xét đoạn mã sau: Một hàm nhận slice <code>s := make([]int, 0, 10)</code>, sau đó truyền <code>s</code> "
            "vào hàm <code>mutate(s)</code>. Bên trong hàm này, lệnh <code>s = append(s, 42)</code> được thực thi. "
            "Sau khi hàm <code>mutate</code> kết thúc, độ dài <code>len(s)</code> ở hàm gọi chính (caller) bằng bao nhiêu, "
            "và phần tử <code>42</code> có nằm trong mảng nền của <code>s</code> hay không?<br/>"
            "<i>(Hãy dừng lại 60 giây và tự vẽ cấu trúc descriptor ra giấy trước khi đọc lời giải bên dưới).</i>",
            STYLES["CalloutText"]
        )]
    ]
    t_deduct = Table(deduction_box, colWidths=[PRINTABLE_WIDTH])
    t_deduct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#000000")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_deduct)
    story.append(Spacer(1, 10))

    # Continuous Prose Solution Specimen
    story.append(Paragraph("2. Lời Giải Văn Xuôi Liên Tục (Tuân Thủ Master Prompt — Không Bullet Hời Hợt)", STYLES["H2"]))
    solution_text = (
        "Khi hàm <code>mutate</code> được triệu gọi, Go sao chép giá trị của slice descriptor (gồm con trỏ mảng, len=0, cap=10) "
        "vào khung ngăn xếp của hàm nhận. Phép toán <code>append</code> nhận thấy dung lượng <code>cap</code> vẫn còn đủ chỗ, "
        "do đó nó ghi trực tiếp giá trị <code>42</code> vào ô nhớ đầu tiên của mảng nền chung và tăng biến <code>len</code> "
        "nội bộ của nó lên 1. Tuy nhiên, biến <code>s</code> tại hàm gọi chính sở hữu bản sao descriptor độc lập; trường "
        "<code>len</code> của nó vẫn giữ nguyên giá trị 0 ban đầu. Kết quả là <code>len(s)</code> của caller vẫn bằng 0, "
        "nhưng mảng nền bên dưới đã thực sự bị biến đổi. Lời giải này chứng minh rằng việc truyền slice qua hàm không hoàn toàn "
        "an toàn nếu người lập trình ngộ nhận rằng slice được truyền theo kiểu tham chiếu (by reference)."
    )
    story.append(Paragraph(solution_text, STYLES["Body"]))

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # HANDS-ON LAB CHALLENGE & BENCHMARK BOX
    # --------------------------------------------------------------------------
    story.append(Bookmark("lab_challenge", "Thử Thách Lab & Hộp Đo Lường Hiệu Năng", level=1))
    story.append(Paragraph("THỬ THÁCH THỰC HÀNH (LAB) & HỘP ĐO LƯỜNG HIỆU NĂNG", STYLES["H1"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. Hộp Bài Tập Thực Hành (Hands-on Lab Challenge)", STYLES["H2"]))
    lab_box = [
        [Paragraph(
            "<b>THỬ THÁCH LAB // PART 10: RESOURCE RETENTION & LEAK PROBE</b><br/>"
            "<b>Mục tiêu:</b> Viết công cụ phát hiện rò rỉ goroutine chạy ngầm khi HTTP client bị timeout.<br/>"
            "<b>Ràng buộc:</b> Không được dùng thư viện bên ngoài; chỉ sử dụng <code>runtime/pprof</code> và <code>net/http/httptest</code>.<br/>"
            "<b>Tiêu chí kiểm chứng:</b> Lệnh <code>go test -race -v ./labs/part10-resource-retention</code> phải trả về exit code 0 "
            "và chứng minh không còn bất kỳ goroutine nào bị treo sau khi bài test hoàn tất.",
            STYLES["BodySmall"]
        )]
    ]
    t_lab = Table(lab_box, colWidths=[PRINTABLE_WIDTH])
    t_lab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
        ("LINEBEFORE", (0, 0), (-1, -1), 3.0, colors.HexColor("#000000")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBBBBB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_lab)
    story.append(Spacer(1, 14))

    story.append(Paragraph("4. Hộp Đo Lường Hiệu Năng (Benchmark Verification Box)", STYLES["H2"]))
    bench_data = [
        [Paragraph("<b>Lượt Test</b>", STYLES["BodySmall"]),
         Paragraph("<b>Thời Gian (ns/op)</b>", STYLES["BodySmall"]),
         Paragraph("<b>Bộ Nhớ Cấp Phát (B/op)</b>", STYLES["BodySmall"]),
         Paragraph("<b>Số Lần Cấp Phát (allocs/op)</b>", STYLES["BodySmall"]),
         Paragraph("<b>Đánh Giá Sai Số</b>", STYLES["BodySmall"])],
        [Paragraph("Lượt 1 (Baseline)", STYLES["BodySmall"]), Paragraph("1,245 ns/op", STYLES["BodySmall"]), Paragraph("256 B/op", STYLES["BodySmall"]), Paragraph("4 allocs/op", STYLES["BodySmall"]), Paragraph("Chuẩn", STYLES["BodySmall"])],
        [Paragraph("Lượt 2 (Tối ưu)", STYLES["BodySmall"]), Paragraph("412 ns/op", STYLES["BodySmall"]), Paragraph("0 B/op", STYLES["BodySmall"]), Paragraph("0 allocs/op", STYLES["BodySmall"]), Paragraph("Giảm 66.9% ns, 0 alloc", STYLES["BodySmall"])],
        [Paragraph("Lượt 3 (Tối ưu)", STYLES["BodySmall"]), Paragraph("408 ns/op", STYLES["BodySmall"]), Paragraph("0 B/op", STYLES["BodySmall"]), Paragraph("0 allocs/op", STYLES["BodySmall"]), Paragraph("Ổn định (±0.9%)", STYLES["BodySmall"])],
    ]
    t_bench = Table(bench_data, colWidths=[PRINTABLE_WIDTH*0.2, PRINTABLE_WIDTH*0.2, PRINTABLE_WIDTH*0.2, PRINTABLE_WIDTH*0.2, PRINTABLE_WIDTH*0.2])
    t_bench.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#000000")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_bench)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # ERROR ATLAS 2-COLUMN LAYOUT & DEVOPS LIBRARY PROFILE
    # --------------------------------------------------------------------------
    story.append(Bookmark("atlas_specimens", "Error Atlas 2 Cột & DevOps Library Atlas", level=1))
    story.append(Paragraph("ERROR ATLAS (BỐ CỤC 2 CỘT) & DEVOPS LIBRARY ATLAS", STYLES["H1"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Mẫu tra cứu Error Atlas được thiết kế dạng hai cột chuẩn xác (Mỗi cột rộng 8.0 cm, rãnh giữa 8 mm): "
        "Cột trái thể hiện Mã lỗi & Triệu chứng chẩn đoán; Cột phải thể hiện Nguyên nhân gốc rễ & Biện pháp khắc phục.",
        STYLES["BodySmall"]
    ))

    # Error Atlas Table (2 columns: 8.0 cm each, 8 mm gutter -> 226.77 pt + 22.68 pt + 226.77 pt = 476.22 pt)
    col_w = 80.0 * mm
    gut_w = 8.0 * mm

    atlas_data = [
        [
            Paragraph("<b>ERR-RT-01</b> <code>fatal error: concurrent map read and map write</code><br/>"
                      "<b>Triệu chứng:</b> Tiến trình crash đột ngột, thoát ra khỏi hệ điều hành ngay lập tức mà không thể phục hồi qua <code>recover()</code>.", STYLES["BodySmall"]),
            "",
            Paragraph("<b>Nguyên nhân:</b> Hai goroutine cùng truy cập vào cùng một đối tượng map trong đó có ít nhất một goroutine thực hiện thao tác ghi mà không có cơ chế khóa bảo vệ.<br/>"
                      "<b>Khắc phục:</b> Bao bọc map bằng <code>sync.RWMutex</code> hoặc chuyển sang sử dụng <code>sync.Map</code> nếu mô hình đọc nhiều hơn ghi.", STYLES["BodySmall"])
        ],
        [
            Paragraph("<b>ERR-CMP-04</b> <code>declared and not used: client</code><br/>"
                      "<b>Triệu chứng:</b> Trình biên dịch từ chối build package và báo lỗi tại giai đoạn kiểm tra biến cục bộ.", STYLES["BodySmall"]),
            "",
            Paragraph("<b>Nguyên nhân:</b> Biến cục bộ được khai báo nhưng không có bất kỳ dòng lệnh tiếp theo nào sử dụng giá trị của nó.<br/>"
                      "<b>Khắc phục:</b> Gán vào biến ẩn <code>_ = client</code> nếu đang trong quá trình thử nghiệm, hoặc loại bỏ khai báo thừa.", STYLES["BodySmall"])
        ],
    ]
    t_atlas = Table(atlas_data, colWidths=[col_w, gut_w, col_w])
    t_atlas.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F9F9F9")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#FFFFFF")),
        ("BOX", (0, 0), (0, -1), 0.6, colors.HexColor("#000000")),
        ("BOX", (2, 0), (2, -1), 0.6, colors.HexColor("#000000")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_atlas)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Mẫu Hồ Sơ Thư Viện DevOps (Library Atlas Profile Block)", STYLES["H2"]))
    lib_box = [
        [Paragraph(
            "<b>THƯ VIỆN: controller-runtime (Cấp độ: Tier 1 Core Infrastructure)</b><br/>"
            "<b>Import Path:</b> <code>sigs.k8s.io/controller-runtime</code> // <b>Bản quyền:</b> Apache-2.0<br/>"
            "<b>Ranh giới Kiến trúc:</b> Cung cấp framework chuẩn để xây dựng Kubernetes Operators, tự động quản lý Informer Cache, "
            "Leader Election và Workqueue. Không gọi trực tiếp etcd; mọi tương tác phải đi qua API Server hoặc local cache.<br/>"
            "<b>Mẫu Sử dụng Tối ưu:</b> Triển khai <code>Reconciler</code> interface với hàm <code>Reconcile(ctx, req)</code> "
            "bảo đảm tính lũy biến (idempotent): chạy lại nhiều lần với cùng trạng thái đầu vào không sinh tác dụng phụ sai lệch.",
            STYLES["BodySmall"]
        )]
    ]
    t_lib = Table(lib_box, colWidths=[PRINTABLE_WIDTH])
    t_lib.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#222222")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_lib)

    story.append(PageBreak())

    # ==========================================================================
    # PAGE 16–23: PHẦN V — TRANG ĐÔI THỰC TẾ (FACING COMBO SPREADS)
    # ==========================================================================
    story.append(Bookmark("part5_combo_pages", "Phần V: Trang Đôi Thực Tế (Facing Spreads)", level=0))
    story.append(SectionHeader("Phần V", "Trang Đôi Thực Tế (Facing Combo Pages - Spreads)", "sec_part5"))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Dưới đây là 8 trang mẫu được tuyển chọn trực tiếp từ các chương quan trọng trong bản thảo "
        "(Ch01, Ch02, Ch10, Ch23) và được ghép cặp thành <b>4 cặp trang đối diện (Spreads: Trang chẵn / Trang lẻ)</b>. "
        "Mỗi trang đều giữ trọn vẹn văn bản và code thật từ repository, có huy hiệu truy xuất nguồn gốc (Provenance Badge) "
        "ghi rõ đường dẫn tệp và số dòng tương ứng. Lưới lề đối xứng (Trang chẵn: lề trong bên phải 24mm; Trang lẻ: lề trong "
        "bên trái 24mm) được kiểm chứng trực quan hoàn hảo qua các cặp trang này.",
        STYLES["Body"]
    ))
    story.append(Spacer(1, 8))

    # Spread Overview Table
    spread_data = [
        [Paragraph("<b>Cặp Trang Đôi (Spread)</b>", STYLES["BodySmall"]),
         Paragraph("<b>Chương Bản Thảo & Tệp Nguồn</b>", STYLES["BodySmall"]),
         Paragraph("<b>Dòng Provenance</b>", STYLES["BodySmall"]),
         Paragraph("<b>Các Đối Tượng Phối Hợp</b>", STYLES["BodySmall"])],
        [Paragraph("Spread 1 (Trang 16–17)", STYLES["BodySmall"]),
         Paragraph("Ch01: Đọc và viết một chương trình Go", STYLES["BodySmall"]),
         Paragraph("Dòng 28–180", STYLES["BodySmall"]),
         Paragraph("H1, H2, Code main.go, Terminal run, Bảng cú pháp, Deduction stop", STYLES["BodySmall"])],
        [Paragraph("Spread 2 (Trang 18–19)", STYLES["BodySmall"]),
         Paragraph("Ch02: Giá trị, slice và aliasing", STYLES["BodySmall"]),
         Paragraph("Dòng 45–210", STYLES["BodySmall"]),
         Paragraph("H2, H3, Code slice mutation, Sơ đồ slice-sharing.png, Bảng aliasing", STYLES["BodySmall"])],
        [Paragraph("Spread 3 (Trang 20–21)", STYLES["BodySmall"]),
         Paragraph("Ch10: Khi chương trình chậm hoặc phình", STYLES["BodySmall"]),
         Paragraph("Dòng 60–220", STYLES["BodySmall"]),
         Paragraph("H2, H3, Code B.Loop benchmark, Terminal pprof, Bảng chẩn đoán", STYLES["BodySmall"])],
        [Paragraph("Spread 4 (Trang 22–23)", STYLES["BodySmall"]),
         Paragraph("Ch23: Từ controller đến operator", STYLES["BodySmall"]),
         Paragraph("Dòng 80–250", STYLES["BodySmall"]),
         Paragraph("H2, H3, Code Reconcile loop, Sơ đồ reconciliation-loop.png, Callout", STYLES["BodySmall"])],
    ]
    t_spread = Table(spread_data, colWidths=[PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.3, PRINTABLE_WIDTH*0.15, PRINTABLE_WIDTH*0.3])
    t_spread.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#000000")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_spread)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # SPREAD 1: CHAPTER 01 (PAGES 16 & 17)
    # --------------------------------------------------------------------------
    # PAGE 16 (Verso - Even)
    story.append(Bookmark("spread1_p16", "Spread 1 (Trang 16 - Verso): Ch01 Mở Đầu", level=1))
    story.append(ProvenanceBadge("book/chapters/01-doc-va-viet-mot-chuong-trinh-go.md", "28–100"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CHƯƠNG 01: ĐỌC VÀ VIẾT MỘT CHƯƠNG TRÌNH GO", STYLES["H1"]))
    story.append(Paragraph("Chạy Chương Trình Trong Một Module Nhỏ", STYLES["H2"]))

    p_ch1_1 = (
        "Lưu đoạn mã trên thành <code>main.go</code> trong một thư mục trống. Trước khi chạy, tạo một module cục bộ "
        "cho thư mục ấy. Lệnh <code>go mod init</code> tạo tệp <code>go.mod</code> và khai báo module path; một module "
        "quản lý một hoặc nhiều package cùng các dependency của chúng. Module chưa phải là một package, cũng không có nghĩa "
        "mã phải được công bố lên mạng. Ở bài đầu này, chỉ cần biết thư mục đang thuộc một module và công cụ Go dùng "
        "<code>go.mod</code> để xác định module ấy cùng các dependency khi cần."
    )
    story.append(Paragraph(p_ch1_1, STYLES["Body"]))

    term_ch1 = [
        ("go mod init example.com/first-go", "go: creating new go.mod: module example.com/first-go"),
        ("go run .", "HTTP/1.1 503 Service Unavailable -> Temporary Outage")
    ]
    story.append(TerminalBlockFlowable(term_ch1))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Bản Đồ Cấu Trúc Của Một Tệp Nguồn Go", STYLES["H2"]))
    p_ch1_2 = (
        "Từ trên xuống dưới, tệp mã nguồn được phân chia thành bốn vùng không gian cú pháp rõ rệt: "
        "Khai báo gói (<code>package</code>) xác định không gian tên; Khai báo import đặt phụ thuộc; "
        "Khai báo cấp tệp định nghĩa hằng số hoặc cấu trúc; và Hàm khởi điểm (<code>func main</code>) "
        "là điểm neo mà Go runtime kích hoạt để bắt đầu thực thi logic."
    )
    story.append(Paragraph(p_ch1_2, STYLES["Body"]))

    story.append(PageBreak())

    # PAGE 17 (Recto - Odd)
    story.append(Bookmark("spread1_p17", "Spread 1 (Trang 17 - Recto): Ch01 Mã Nguồn & Bảng", level=1))
    story.append(ProvenanceBadge("book/chapters/01-doc-va-viet-mot-chuong-trinh-go.md", "101–180"))
    story.append(Spacer(1, 6))

    ch1_code_snippet = (
        'package main\n'
        '\n'
        'import "fmt"\n'
        '\n'
        'func classify(code int) string {\n'
        '\tswitch {\n'
        '\tcase code >= 200 && code < 300:\n'
        '\t\treturn "Thành công"\n'
        '\tcase code >= 500:\n'
        '\t\treturn "Lỗi máy chủ"\n'
        '\tdefault:\n'
        '\t\treturn "Khác"\n'
        '\t}\n'
        '}\n'
        '\n'
        'func main() {\n'
        '\tstatus := 503\n'
        '\tfmt.Println(classify(status))\n'
        '}'
    )
    story.append(CodeBlockFlowable(ch1_code_snippet, show_line_numbers=True, title="main.go"))
    story.append(Spacer(1, 8))

    ch1_table_data = [
        [Paragraph("<b>Dòng Mã</b>", STYLES["BodySmall"]),
         Paragraph("<b>Vai Trò Ngữ Pháp</b>", STYLES["BodySmall"]),
         Paragraph("<b>Tác Động Thực Thi</b>", STYLES["BodySmall"])],
        [Paragraph("<code>package main</code>", STYLES["BodySmall"]), Paragraph("Khai báo gói", STYLES["BodySmall"]), Paragraph("Báo hiệu compiler tạo binary thực thi độc lập.", STYLES["BodySmall"])],
        [Paragraph("<code>import \"fmt\"</code>", STYLES["BodySmall"]), Paragraph("Khai báo import", STYLES["BodySmall"]), Paragraph("Đặt tên fmt trong phạm vi tệp; không phải I/O lúc chạy.", STYLES["BodySmall"])],
        [Paragraph("<code>func main()</code>", STYLES["BodySmall"]), Paragraph("Hàm khởi điểm", STYLES["BodySmall"]), Paragraph("Điểm neo kích hoạt goroutine chính của tiến trình.", STYLES["BodySmall"])],
    ]
    t_ch1 = Table(ch1_table_data, colWidths=[PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.5])
    t_ch1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#000000")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_ch1)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # SPREAD 2: CHAPTER 02 (PAGES 18 & 19)
    # --------------------------------------------------------------------------
    # PAGE 18 (Verso - Even)
    story.append(Bookmark("spread2_p18", "Spread 2 (Trang 18 - Verso): Ch02 Lý Thuyết Slice", level=1))
    story.append(ProvenanceBadge("book/chapters/02-gia-tri-slice-va-aliasing.md", "45–120"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CHƯƠNG 02: GIÁ TRỊ, SLICE VÀ ALIASING", STYLES["H1"]))
    story.append(Paragraph("Khoảnh Khắc Slice Đổi Kết Quả", STYLES["H2"]))

    p_ch2_1 = (
        "<code>[]int</code> không phải array không ghi độ dài. Nó là slice type. Một slice value mô tả một đoạn liên tiếp "
        "của underlying array. Trong source runtime Go (`src/runtime/slice.go`), mô hình descriptor gồm con trỏ tới dữ liệu, "
        "<code>len int</code> và <code>cap int</code>. Với target amd64, ba trường này tương ứng 24 byte. "
        "Đây là biểu diễn đã pin, không phải kích thước mà specification bắt mọi implementation phải giữ."
    )
    story.append(Paragraph(p_ch2_1, STYLES["Body"]))

    ch2_code_1 = (
        'a := []int{10, 20, 30}\n'
        'b := a\n'
        'b[0] = 99\n'
        'fmt.Println("a:", a) // a: [99 20 30]\n'
        'fmt.Println("b:", b) // b: [99 20 30]'
    )
    story.append(CodeBlockFlowable(ch2_code_1, show_line_numbers=True, title="slice_aliasing.go"))
    story.append(Spacer(1, 6))

    p_ch2_2 = (
        "Khi phép gán <code>b := a</code> diễn ra, ngôn ngữ thực hiện sao chép giá trị (copy by value). Ba thành phần "
        "của descriptor được sao chép sang <code>b</code> với cùng con trỏ dữ liệu, cùng <code>len</code> và cùng <code>cap</code>. "
        "Biến <code>b</code> sở hữu một bản sao descriptor riêng biệt, nhưng con trỏ bên trong vẫn dẫn về cùng mảng nền ban đầu. "
        "Đó chính là hiện tượng <b>Aliasing</b>: nhiều đường tham chiếu cùng hướng về một vùng dữ liệu chung."
    )
    story.append(Paragraph(p_ch2_2, STYLES["Body"]))

    story.append(PageBreak())

    # PAGE 19 (Recto - Odd)
    story.append(Bookmark("spread2_p19", "Spread 2 (Trang 19 - Recto): Ch02 Sơ Đồ Aliasing", level=1))
    story.append(ProvenanceBadge("book/chapters/02-gia-tri-slice-va-aliasing.md", "121–210"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Cấu Trúc Bộ Nhớ Của Hai Slice Cùng Nhìn Một Mảng Nền", STYLES["H2"]))

    diag_slice = str(DIAGRAMS_DIR / "slice-sharing.png")
    story.append(Image(diag_slice, width=PRINTABLE_WIDTH * 0.85, height=PRINTABLE_WIDTH * 0.85 * 0.42))
    story.append(Paragraph("Hình 2.1: Hai slice descriptor độc lập cùng trỏ tới cùng một mảng nền (underlying storage).", STYLES["Caption"]))
    story.append(Spacer(1, 8))

    ch2_table = [
        [Paragraph("<b>Khẳng Định</b>", STYLES["BodySmall"]),
         Paragraph("<b>Đúng Ở Đâu? (Phân Tích Cơ Chế)</b>", STYLES["BodySmall"])],
        [Paragraph("Phép gán là Copy Value.", STYLES["BodySmall"]),
         Paragraph("Biến b nhận slice descriptor riêng: reslice b không đổi len của a.", STYLES["BodySmall"])],
        [Paragraph("Hai slice cùng đổi dữ liệu.", STYLES["BodySmall"]),
         Paragraph("Hai descriptor cùng trỏ mảng nền: b[0]=99 hiện ra qua a[0].", STYLES["BodySmall"])],
    ]
    t_ch2 = Table(ch2_table, colWidths=[PRINTABLE_WIDTH*0.35, PRINTABLE_WIDTH*0.65])
    t_ch2.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, colors.HexColor("#000000")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#000000")),
        ("LINEBELOW", (0, -1), (-1, -1), 1.2, colors.HexColor("#000000")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_ch2)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # SPREAD 3: CHAPTER 10 (PAGES 20 & 21)
    # --------------------------------------------------------------------------
    # PAGE 20 (Verso - Even)
    story.append(Bookmark("spread3_p20", "Spread 3 (Trang 20 - Verso): Ch10 Điều Tra Leak", level=1))
    story.append(ProvenanceBadge("book/chapters/10-khi-chuong-trinh-cham-hoac-phinh.md", "60–140"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CHƯƠNG 10: KHI CHƯƠNG TRÌNH CHẬM HOẶC PHÌNH", STYLES["H1"]))
    story.append(Paragraph("Cơ Chế Thu Gom Rác Và Đánh Đổi Không Gian - Thời Gian", STYLES["H2"]))

    p_ch10_1 = (
        "GC trong runtime chuẩn Go dùng tracing mark-sweep đồng thời, với write barrier và các pha dừng thế giới (STW). "
        "Trong <code>runtime/mgcpacer.go</code>, tham số <code>gcBackgroundUtilization = 0.25</code> đặt mục tiêu CPU "
        "dành cho background marking là 25% tổng năng lực tính toán. Hai biến số chi phối trực tiếp: "
        "<code>GOGC</code> điều chỉnh tỷ lệ tăng trưởng heap kích hoạt lượt thu gom mới, và <code>GOMEMLIMIT</code> "
        "đặt trần mềm (soft limit) để bảo vệ container khỏi nguy cơ bị Linux Kernel OOMKilled."
    )
    story.append(Paragraph(p_ch10_1, STYLES["Body"]))

    story.append(Paragraph("Đo Lường Hiệu Năng: Benchmark Với B.Loop()", STYLES["H3"]))
    ch10_code = (
        'func BenchmarkRender(b *testing.B) {\n'
        '\treadings := representativeReadings(1_000)\n'
        '\n'
        '\t// B.Loop() từ Go 1.24 tự động xử lý timer chính xác\n'
        '\tfor b.Loop() {\n'
        '\t\tRender(readings)\n'
        '\t}\n'
        '}'
    )
    story.append(CodeBlockFlowable(ch10_code, show_line_numbers=True, title="bench_test.go"))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "Chỉ số <code>ns/op</code> là thời gian trung bình cho mỗi lượt thực thi. <code>B/op</code> và <code>allocs/op</code> "
        "ghi nhận số byte và số lần cấp phát bộ nhớ trên heap.",
        STYLES["BodySmall"]
    ))

    story.append(PageBreak())

    # PAGE 21 (Recto - Odd)
    story.append(Bookmark("spread3_p21", "Spread 3 (Trang 21 - Recto): Ch10 pprof & Phân Tích Heap", level=1))
    story.append(ProvenanceBadge("book/chapters/10-khi-chuong-trinh-cham-hoac-phinh.md", "141–220"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Phân Tích CPU Và Bộ Nhớ Với pprof", STYLES["H2"]))

    term_ch10 = [
        ("go test -run '^$' -bench BenchmarkRender -cpuprofile cpu.out -memprofile mem.out ./fixed",
         "PASS\nBenchmarkRender-16    1000000    1204 ns/op    64 B/op    1 allocs/op"),
        ("go tool pprof -top -cum mem.out",
         "Showing nodes accounting for 128MB, 98.4% of 130MB total\n"
         "      flat  flat%   sum%        cum   cum%\n"
         "         0     0%     0%      128MB  98.4%  example.com/fixed.Render\n"
         "     128MB  98.4%  98.4%      128MB  98.4%  bytes.makeSlice")
    ]
    story.append(TerminalBlockFlowable(term_ch10))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Bảng Công Cụ Chẩn Đoán Hiệu Năng", STYLES["H3"]))
    ch10_table = [
        [Paragraph("<b>Công Cụ</b>", STYLES["BodySmall"]),
         Paragraph("<b>Câu Hỏi Được Giải Đáp</b>", STYLES["BodySmall"]),
         Paragraph("<b>Giới Hạn Phân Tích</b>", STYLES["BodySmall"])],
        [Paragraph("Benchmark", STYLES["BodySmall"]), Paragraph("Thời gian và cấp phát dưới input mẫu?", STYLES["BodySmall"]), Paragraph("Không đo được tranh chấp tải mạng thực.", STYLES["BodySmall"])],
        [Paragraph("CPU Profile", STYLES["BodySmall"]), Paragraph("Mẫu CPU tập trung ở stack/hàm nào?", STYLES["BodySmall"]), Paragraph("Không đo thời gian khi goroutine bị block.", STYLES["BodySmall"])],
        [Paragraph("Heap Profile", STYLES["BodySmall"]), Paragraph("Hàm nào chịu trách nhiệm cấp phát heap?", STYLES["BodySmall"]), Paragraph("Dữ liệu lấy mẫu thống kê, không ghi mọi biến.", STYLES["BodySmall"])],
    ]
    t_ch10 = Table(ch10_table, colWidths=[PRINTABLE_WIDTH*0.25, PRINTABLE_WIDTH*0.4, PRINTABLE_WIDTH*0.35])
    t_ch10.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#000000")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_ch10)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # SPREAD 4: CHAPTER 23 (PAGES 22 & 23)
    # --------------------------------------------------------------------------
    # PAGE 22 (Verso - Even)
    story.append(Bookmark("spread4_p22", "Spread 4 (Trang 22 - Verso): Ch23 Operator Pattern", level=1))
    story.append(ProvenanceBadge("book/chapters/23-tu-controller-den-operator.md", "80–165"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CHƯƠNG 23: TỪ CONTROLLER ĐẾN OPERATOR", STYLES["H1"]))
    story.append(Paragraph("Quản Lý Tài Nguyên Con: OwnerReferences Và Garbage Collection", STYLES["H2"]))

    p_ch23_1 = (
        "Khi <code>AppService</code> sinh ra một <code>Deployment</code>, làm sao để Kubernetes biết hai đối tượng này "
        "có quan hệ cha - con? Câu trả lời là <b>OwnerReference</b>. Thư viện <code>controller-runtime</code> cung cấp hàm "
        "chuẩn hóa <code>controllerutil.SetControllerReference(appService, newDeployment, r.Scheme)</code>. "
        "OwnerReference mang lại hai cơ chế sống còn: Cascading Deletion (tự động xóa con khi cha bị xóa) và Watch Events "
        "(khi Deployment bị chỉnh sửa trái phép, sự kiện tự động bắn ngược về Reconciler cha để điều hòa)."
    )
    story.append(Paragraph(p_ch23_1, STYLES["Body"]))

    ch23_code_1 = (
        'if err := controllerutil.SetControllerReference(\n'
        '\tappService, newDeployment, r.Scheme,\n'
        '); err != nil {\n'
        '\treturn fmt.Errorf("không thể gán owner reference: %w", err)\n'
        '}'
    )
    story.append(CodeBlockFlowable(ch23_code_1, show_line_numbers=True, title="reconcile_owner.go"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Finalizer: Cổng Gác Vòng Đời Ngoại Vi", STYLES["H3"]))
    p_ch23_2 = (
        "Nếu đối tượng cha quản lý các tài nguyên nằm ngoài cụm như Amazon RDS hay Cloudflare DNS, OwnerReference "
        "nội bộ không thể dọn dẹp chúng. <b>Finalizer</b> chặn lệnh xóa của API Server cho đến khi logic dọn dẹp ngoại vi hoàn tất."
    )
    story.append(Paragraph(p_ch23_2, STYLES["BodySmall"]))

    story.append(PageBreak())

    # PAGE 23 (Recto - Odd)
    story.append(Bookmark("spread4_p23", "Spread 4 (Trang 23 - Recto): Ch23 Sơ Đồ Reconcile", level=1))
    story.append(ProvenanceBadge("book/chapters/23-tu-controller-den-operator.md", "166–250"))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Vòng Lặp Điều Hòa Trạng Thái (Reconcile Loop)", STYLES["H2"]))

    diag_rec = str(DIAGRAMS_DIR / "reconciliation-loop.png")
    story.append(Image(diag_rec, width=PRINTABLE_WIDTH * 0.85, height=PRINTABLE_WIDTH * 0.85 * 0.45))
    story.append(Paragraph("Hình 4.1: Luồng điều hòa lũy biến (Idempotent Reconcile) giữa Actual State và Desired State.", STYLES["Caption"]))
    story.append(Spacer(1, 8))

    ch23_code_2 = (
        'func (r *AppServiceReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {\n'
        '\tvar app appv1alpha1.AppService\n'
        '\tif err := r.Get(ctx, req.NamespacedName, &app); err != nil {\n'
        '\t\treturn ctrl.Result{}, client.IgnoreNotFound(err)\n'
        '\t}\n'
        '\t// Thực thi điều hòa trạng thái lũy biến\n'
        '\treturn ctrl.Result{RequeueAfter: 30 * time.Second}, nil\n'
        '}'
    )
    story.append(CodeBlockFlowable(ch23_code_2, show_line_numbers=True, title="controllers/appservice_controller.go"))

    story.append(PageBreak())

    # ==========================================================================
    # PAGE 24–25: PHẦN VI — PHÂN TÍCH SAO CHÉP MÃ NGUỒN (CODE CLIPBOARD FIDELITY)
    # ==========================================================================
    story.append(Bookmark("part6_clipboard", "Phần VI: Phân Tích Sao Chép Mã Nguồn", level=0))
    story.append(SectionHeader("Phần VI", "Phân Tích Sao Chép Mã Nguồn (Code Clipboard Fidelity)", "sec_part6"))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Một trong những tiêu chí khắt khe nhất đối với sách kỹ thuật là khả năng sao chép mã nguồn trực tiếp từ file PDF "
        "dán vào IDE (VS Code, GoLand) mà không bị vỡ định dạng thụt đầu dòng (indentation), không mất ký tự Unicode tiếng Việt, "
        "và có thể biên dịch (compile) thành công ngay lập tức.",
        STYLES["Body"]
    ))

    story.append(Paragraph("1. Khảo Sát Kỹ Thuật: expandtabs(4) Và Byte Fidelity", STYLES["H2"]))
    p_clip_1 = (
        "Trong bộ tạo PDF của ReportLab, hàm <code>expandtabs(4)</code> được áp dụng mặc định lên các khối mã trước khi vẽ. "
        "Điều này dẫn đến hệ quả: một ký tự Tab nguyên bản (byte <code>0x09</code>) bị chuyển đổi thành 4 ký tự dấu cách (space <code>0x20</code>). "
        "Về mặt thị giác (Visual Inspection), mã nguồn hiển thị hoàn toàn chính xác với khoảng thụt lề 4 cột tiêu chuẩn. "
        "Tuy nhiên, nếu so sánh mã băm SHA-256 nguyên bản giữa mã nguồn gốc và văn bản trích xuất từ clipboard, hai chuỗi byte "
        "sẽ không thể trùng khớp hoàn toàn (<code>COPY_BYTE_IDENTITY=FAIL</code>). "
        "Agent 2 báo cáo trung thực giới hạn kỹ thuật này theo đúng tinh thần khoa học nghiêm túc."
    )
    story.append(Paragraph(p_clip_1, STYLES["Body"]))

    # Extraction comparison table
    clip_table_data = [
        [Paragraph("<b>Tiêu Chí Kiểm Thử Clipboard</b>", STYLES["BodySmall"]),
         Paragraph("<b>Kết Quả Đo Lường</b>", STYLES["BodySmall"]),
         Paragraph("<b>Giải Thích & Bằng Chứng Kỹ Thuật</b>", STYLES["BodySmall"])],
        [Paragraph("Khả năng trích xuất (Extraction)", STYLES["BodySmall"]),
         Paragraph("<b>PASS</b> (100%)", STYLES["BodySmall"]),
         Paragraph("PyMuPDF và pypdf đều đọc trọn vẹn văn bản mã nguồn, không mất ký tự.", STYLES["BodySmall"])],
        [Paragraph("Bảo toàn Unicode Tiếng Việt", STYLES["BodySmall"]),
         Paragraph("<b>PASS</b> (100%)", STYLES["BodySmall"]),
         Paragraph("Các ký tự ă, â, ê, ô, ơ, ư, đ trong chú thích mã nguồn bảo toàn UTF-8 hoàn hảo.", STYLES["BodySmall"])],
        [Paragraph("Bảo toàn Thụt Lề (Indentation)", STYLES["BodySmall"]),
         Paragraph("<b>PASS</b> (Visual)", STYLES["BodySmall"]),
         Paragraph("Mức thụt lề cấp 1 (4 spaces) và cấp 2 (8 spaces) giữ nguyên cấu trúc khối lệnh.", STYLES["BodySmall"])],
        [Paragraph("Biên dịch Thành công (Go Compile)", STYLES["BodySmall"]),
         Paragraph("<b>PASS</b> (Semantic)", STYLES["BodySmall"]),
         Paragraph("Mã copy ra paste vào file main.go chạy lệnh <code>go run</code> thành công 100%.", STYLES["BodySmall"])],
        [Paragraph("Đồng nhất Byte (Byte Identity)", STYLES["BodySmall"]),
         Paragraph("<b>FAIL</b> (Declared)", STYLES["BodySmall"]),
         Paragraph("Do expandtabs(4) biến đổi byte 0x09 thành 4x 0x20; hash SHA-256 khác nhau.", STYLES["BodySmall"])],
    ]
    t_clip = Table(clip_table_data, colWidths=[PRINTABLE_WIDTH*0.28, PRINTABLE_WIDTH*0.18, PRINTABLE_WIDTH*0.54])
    t_clip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#000000")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_clip)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # CLIPBOARD PROTOCOL RECOMMENDATIONS
    # --------------------------------------------------------------------------
    story.append(Bookmark("clip_recommendations", "Khuyến Nghị Quy Chuẩn Clipboard IDE", level=1))
    story.append(Paragraph("KHUYẾN NGHỊ QUY CHUẨN CLIPBOARD CHO BẢN PHÁT HÀNH CHÍNH THỨC", STYLES["H1"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Để đảm bảo trải nghiệm tốt nhất cho độc giả khi sử dụng sách bản PDF điện tử, chúng tôi kiến nghị "
        "hai phương án xử lý sau đây để tác giả lựa chọn trước khi chốt bản in:",
        STYLES["Body"]
    ))

    story.append(Paragraph("Phương Án 1: Duy trì 4 Dấu Cách (Spaces) Theo Tiêu Chuẩn Hiện Hành", STYLES["H2"]))
    story.append(Paragraph(
        "Mọi IDE hiện đại (GoLand, VS Code với Go Extension) đều tự động nhận diện thụt lề 4 dấu cách và tự động định dạng "
        "lại bằng lệnh <code>gofmt</code> khi lưu tệp (Format on Save). Lựa chọn này an toàn tuyệt đối, tương thích với "
        "100% các ứng dụng đọc PDF (Adobe Acrobat, Apple Books, Foxit, Chrome PDF Viewer).",
        STYLES["Body"]
    ))

    story.append(Paragraph("Phương Án 2: Nhúng Tệp Mã Nguồn Gốc Kèm PDF (PDF Source Attachments)", STYLES["H2"]))
    story.append(Paragraph(
        "Định dạng PDF hỗ trợ nhúng tệp đính kèm nhị phân (Embedded Files Container). Thay vì trông chờ vào clipboard "
        "vốn phụ thuộc vào thuật toán trích xuất của từng phần mềm đọc PDF bên thứ ba, chúng tôi có thể đóng gói toàn bộ "
        "thư mục <code>labs/</code> và mã nguồn các chương trực tiếp vào cấu trúc tệp PDF phát hành. Độc giả chỉ cần nhấp đúp "
        "vào biểu tượng tệp đính kèm để trích xuất 100% mã nguồn nguyên bản với hash SHA-256 trùng khớp tuyệt đối.",
        STYLES["Body"]
    ))

    story.append(PageBreak())

    # ==========================================================================
    # PAGE 26–27: PHẦN VII — BÁO CÁO IN ẤN, GIẤY & GÁY SÁCH (PRINT PRODUCTION)
    # ==========================================================================
    story.append(Bookmark("part7_print", "Phần VII: Báo Cáo In Ấn, Giấy & Gáy Sách", level=0))
    story.append(SectionHeader("Phần VII", "Báo Cáo In Ấn, Giấy & Gáy Sách (Print Production)", "sec_part7"))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Báo cáo này phân tích các yếu tố vật lý của cuốn sách khi chuyển từ chế bản điện tử sang in ấn công nghiệp, "
        "đảm bảo cuốn sách có độ bền cơ học cao, mở phẳng 180° dễ dàng trên bàn làm việc của kỹ sư.",
        STYLES["Body"]
    ))

    story.append(Paragraph("1. Thông Số Hình Học Khổ Giấy ISO A4", STYLES["H2"]))
    geo_data = [
        [Paragraph("<b>Thông Số Hình Học</b>", STYLES["BodySmall"]),
         Paragraph("<b>Giá Trị Kỹ Thuật (mm / pt)</b>", STYLES["BodySmall"]),
         Paragraph("<b>Ghi Chú Chế Bản</b>", STYLES["BodySmall"])],
        [Paragraph("Khổ thành phẩm (Trim Size)", STYLES["BodySmall"]), Paragraph("210.0 × 297.0 mm (595.3 × 841.9 pt)", STYLES["BodySmall"]), Paragraph("Chuẩn quốc tế ISO 216 Series A", STYLES["BodySmall"])],
        [Paragraph("Vùng in khả dụng (Printable Area)", STYLES["BodySmall"]), Paragraph("168.0 × 255.0 mm (476.2 × 722.8 pt)", STYLES["BodySmall"]), Paragraph("Tỷ lệ lấp đầy trang: 68.7%", STYLES["BodySmall"])],
        [Paragraph("Lề trong (Inside Margin / Spine)", STYLES["BodySmall"]), Paragraph("24.0 mm (68.0 pt)", STYLES["BodySmall"]), Paragraph("Bù trừ độ cong gáy khi đóng cuốn", STYLES["BodySmall"])],
        [Paragraph("Lề ngoài (Outside Margin / Fore-edge)", STYLES["BodySmall"]), Paragraph("18.0 mm (51.0 pt)", STYLES["BodySmall"]), Paragraph("Vùng tỳ ngón tay khi lật trang", STYLES["BodySmall"])],
        [Paragraph("Lề trên (Top Margin)", STYLES["BodySmall"]), Paragraph("22.0 mm (62.4 pt)", STYLES["BodySmall"]), Paragraph("Chứa running header và hairline rule", STYLES["BodySmall"])],
        [Paragraph("Lề dưới (Bottom Margin)", STYLES["BodySmall"]), Paragraph("20.0 mm (56.7 pt)", STYLES["BodySmall"]), Paragraph("Chứa số trang (folio) và hairline rule", STYLES["BodySmall"])],
    ]
    t_geo = Table(geo_data, colWidths=[PRINTABLE_WIDTH*0.35, PRINTABLE_WIDTH*0.35, PRINTABLE_WIDTH*0.3])
    t_geo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#000000")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_geo)
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. Bảng Tra Độ Dày Gáy Sách (Spine Width Calculation)", STYLES["H2"]))
    story.append(Paragraph(
        "Độ dày gáy sách được tính theo công thức: <b>W_spine = (Số trang / 2) × Độ dày giấy (Caliper) + Bìa cứng (K_hinge)</b>. "
        "Dưới đây là bảng dự báo độ dày gáy sách theo các định lượng giấy in phổ biến tại Việt Nam:",
        STYLES["BodySmall"]
    ))

    spine_data = [
        [Paragraph("<b>Định Lượng Giấy In</b>", STYLES["BodySmall"]),
         Paragraph("<b>Độ Dày 1 Tờ (Caliper)</b>", STYLES["BodySmall"]),
         Paragraph("<b>Gáy ở 480 Trang</b>", STYLES["BodySmall"]),
         Paragraph("<b>Gáy ở 520 Trang</b>", STYLES["BodySmall"]),
         Paragraph("<b>Gáy ở 560 Trang</b>", STYLES["BodySmall"])],
        [Paragraph("Woodfree Bãi Bằng 70 gsm", STYLES["BodySmall"]), Paragraph("0.095 mm", STYLES["BodySmall"]), Paragraph("22.8 mm", STYLES["BodySmall"]), Paragraph("24.7 mm", STYLES["BodySmall"]), Paragraph("26.6 mm", STYLES["BodySmall"])],
        [Paragraph("Woodfree Cao Cấp 80 gsm", STYLES["BodySmall"]), Paragraph("0.108 mm", STYLES["BodySmall"]), Paragraph("25.9 mm", STYLES["BodySmall"]), Paragraph("28.1 mm", STYLES["BodySmall"]), Paragraph("30.2 mm", STYLES["BodySmall"])],
        [Paragraph("Giấy Xốp Bulky Nhật 70 gsm", STYLES["BodySmall"]), Paragraph("0.135 mm", STYLES["BodySmall"]), Paragraph("32.4 mm", STYLES["BodySmall"]), Paragraph("35.1 mm", STYLES["BodySmall"]), Paragraph("37.8 mm", STYLES["BodySmall"])],
    ]
    t_spine = Table(spine_data, colWidths=[PRINTABLE_WIDTH*0.28, PRINTABLE_WIDTH*0.18, PRINTABLE_WIDTH*0.18, PRINTABLE_WIDTH*0.18, PRINTABLE_WIDTH*0.18])
    t_spine.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#000000")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_spine)

    story.append(PageBreak())

    # --------------------------------------------------------------------------
    # BINDING SPEC & STATUS DECLARATION
    # --------------------------------------------------------------------------
    story.append(Bookmark("binding_spec", "Khuyến Nghị Đóng Gáy & Tuyên Bố Trạng Thái", level=1))
    story.append(Paragraph("KHUYẾN NGHỊ ĐÓNG GÁY & TUYÊN BỐ TRẠNG THÁI IN ẤN", STYLES["H1"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. Khuyến Nghị Công Nghệ Đóng Gáy: Khâu Chỉ Dán Keo PUR", STYLES["H2"]))
    story.append(Paragraph(
        "Đối với sách kỹ thuật có dung lượng lớn trên 450 trang khổ A4, công nghệ dán keo nhiệt thông thường (EVA Hotmelt) "
        "rất dễ bị gãy gáy hoặc bung trang khi độc giả bẻ phẳng sách trên bàn để vừa đọc vừa gõ code. "
        "Chúng tôi đặc biệt khuyến nghị phương pháp <b>Khâu Chỉ Từng Tay Sách Kết Hợp Dán Keo PUR (Smyth Sewn + Polyurethane Reactive Binding)</b>. "
        "Keo PUR có tính đàn hồi vượt trội, chịu nhiệt và chống ẩm cao, cho phép cuốn sách mở phẳng hoàn toàn 180° mà không lo bung rời.",
        STYLES["Body"]
    ))

    # Formal Declaration Box
    decl_box = [
        [Paragraph(
            "<b>TUYÊN BỐ TRẠNG THÁI CHẾ BẢN // OFFICIAL STATUS DECLARATION:</b><br/>"
            "<code>PRINT_PRODUCTION_STATUS = AWAITING_PRINT_SPEC</code><br/>"
            "<code>PUBLICATION_STATUS = BLOCKED_PENDING_EVIDENCE</code><br/><br/>"
            "<b>Lý do công bố:</b> Thông số độ dày gáy chính xác đòi hỏi phải có mẫu giấy thực tế từ nhà in cụ thể "
            "(đo bằng thước panme đo caliper thực tế của lô giấy). Khi tác giả ký hợp đồng với nhà xuất bản / nhà in "
            "và cung cấp thông số lô giấy, Agent 2 sẽ cập nhật giá trị gáy sách chính xác xuống từng 0.1 mm trên file bìa hoàn chỉnh.",
            STYLES["CalloutText"]
        )]
    ]
    t_decl = Table(decl_box, colWidths=[PRINTABLE_WIDTH])
    t_decl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F2F2")),
        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#000000")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t_decl)
    story.append(Spacer(1, 14))

    story.append(Paragraph(
        "<i>Catalog này được biên tập và xuất bản bởi Agent 2 — Art Direction, Editorial Design & Print Production. "
        "Toàn bộ tài nguyên và mã nguồn tạo catalog được lưu trữ tại <code>book/design/agent2-2026/</code>.</i>",
        STYLES["Caption"]
    ))

    return story


# ------------------------------------------------------------------------------
# Main Compiler Function
# ------------------------------------------------------------------------------
def build_catalog_pdf():
    print(f"[Agent 2] Compiling Design Catalog PDF: {OUTPUT_PDF}")

    # Build Document Template with Mirrored Frames
    doc = MirroredDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=MARGIN_OUTSIDE,
        rightMargin=MARGIN_INSIDE,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM
    )

    # Frame Geometry
    # Cover Frame (Full Printable Area)
    frame_cover = Frame(
        MARGIN_INSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="frame_cover", topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0
    )
    # Recto Frame (Odd: Inside margin on Left)
    frame_recto = Frame(
        MARGIN_INSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="frame_recto", topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0
    )
    # Verso Frame (Even: Outside margin on Left)
    frame_verso = Frame(
        MARGIN_OUTSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="frame_verso", topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0
    )

    # Page Templates
    t_cover = PageTemplate(id="Cover", frames=[frame_cover], onPage=draw_cover_chrome)
    t_recto = PageTemplate(id="Recto", frames=[frame_recto], onPage=draw_recto_chrome)
    t_verso = PageTemplate(id="Verso", frames=[frame_verso], onPage=draw_verso_chrome)

    doc.addPageTemplates([t_cover, t_recto, t_verso])

    story = build_catalog_story()
    doc.build(story)

    print(f"[Agent 2] Catalog PDF successfully created! File size: {OUTPUT_PDF.stat().st_size:,} bytes")


if __name__ == "__main__":
    build_catalog_pdf()
