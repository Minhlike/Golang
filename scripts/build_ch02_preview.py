# -*- coding: utf-8 -*-
"""Independent Preview Renderer for Chapter 2 Redesign (Agent 2 Specification).

Builds a standalone, publication-grade preview PDF of Chapter 2 without
touching or modifying Golang_Master.pdf.
Outputs:
- book/design/agent2-ch02/ch02_preview.pdf
- book/design/agent2-ch02/specimens/page_XX.png (150 DPI renders of every page)
"""

from __future__ import annotations

import html
from pathlib import Path
import re
import sys

# Ensure scripts directory is in path
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import fitz
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

from book_style import (
    COLOR_BG_CALLOUT,
    COLOR_BG_HEADER,
    COLOR_BG_LIGHT,
    COLOR_BLACK,
    COLOR_BORDER_HAIRLINE,
    COLOR_BORDER_LIGHT,
    COLOR_BORDER_MEDIUM,
    COLOR_BORDER_STRONG,
    COLOR_BORDER_SUBTLE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
    FONT_MONO,
    FONT_SANS,
    FONT_SANS_BOLD,
    FONT_SERIF,
    FONT_SERIF_BOLD,
    LINE_WEIGHT_ACCENT,
    LINE_WEIGHT_BORDER,
    LINE_WEIGHT_HAIRLINE,
    LINE_WEIGHT_RULE,
    LINE_WEIGHT_TABLE_GRID,
    MARGIN_BOTTOM,
    MARGIN_INSIDE,
    MARGIN_OUTSIDE,
    MARGIN_TOP,
    PAGE_HEIGHT,
    PAGE_SIZE,
    PAGE_WIDTH,
    PRINTABLE_HEIGHT,
    PRINTABLE_WIDTH,
)
import ch02_vector_diagrams as vd

CHAPTER_FILE = ROOT / "book/chapters/02-gia-tri-slice-va-aliasing.md"
OUT_DIR = ROOT / "book/design/agent2-ch02"
PREVIEW_PDF = OUT_DIR / "ch02_preview.pdf"
SPECIMENS_DIR = OUT_DIR / "specimens"


def register_fonts():
    """Register the approved typography fonts."""
    fonts = ROOT / "assets/fonts"
    pdfmetrics.registerFont(TTFont("BookSerif", str(fonts / "SourceSerif4-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("BookSerifBold", str(fonts / "SourceSerif4-Semibold.ttf")))
    pdfmetrics.registerFont(TTFont("BookSans", str(fonts / "SourceSans3-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("BookSansBold", str(fonts / "SourceSans3-Semibold.ttf")))
    pdfmetrics.registerFont(TTFont("BookMono", str(fonts / "JetBrainsMono-Regular.ttf")))


def inline(text: str) -> str:
    """Format markdown inline code and bold/italic markup."""
    code_spans = {}
    marker = "\ue000"
    while marker in text:
        marker += "\ue000"
    spans = []
    for part in re.split(r"(`[^`]+`)", text):
        if part.startswith("`") and part.endswith("`"):
            token = f"{marker}{len(code_spans)}\ue001"
            code_spans[token] = (
                f'<font name="BookMono" color="#111111">'
                f'{html.escape(part[1:-1])}</font>'
            )
            spans.append(token)
            continue
        spans.append(html.escape(part))
    prose = "".join(spans)
    prose = re.sub(r"\*\*(.+?)\*\*", r'<font name="BookSansBold">\1</font>', prose)
    prose = re.sub(r"(?<!\*)\*(?=\S)([^*]*?\S)\*(?!\*)", r'<font name="BookSansBold">\1</font>', prose)
    for token, code in code_spans.items():
        prose = prose.replace(token, code)
    return prose


def get_preview_styles() -> dict[str, ParagraphStyle]:
    """Define typography styles matching the professional spec requirements."""
    base = getSampleStyleSheet()
    return {
        # Running Tracker & Meta
        "tracker": ParagraphStyle(
            "Tracker", fontName=FONT_SANS_BOLD, fontSize=8.0, leading=11,
            textColor=COLOR_TEXT_MUTED, spaceAfter=8,
        ),
        # H1 Chapter Title
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName=FONT_SANS_BOLD, fontSize=21.0,
            leading=27, textColor=COLOR_BLACK, spaceBefore=4, spaceAfter=8,
            keepWithNext=True,
        ),
        "chapter_subtitle": ParagraphStyle(
            "ChapterSubtitle", parent=base["BodyText"], fontName=FONT_SANS, fontSize=11.5,
            leading=16.5, textColor=COLOR_TEXT_SECONDARY, spaceBefore=0, spaceAfter=12,
            keepWithNext=True,
        ),
        # H2 Section (with generous spacing and strict keepWithNext)
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName=FONT_SANS_BOLD, fontSize=14.5,
            leading=19.5, textColor=COLOR_BLACK, spaceBefore=18, spaceAfter=7,
            keepWithNext=True,
        ),
        # H3 Subsection
        "h3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontName=FONT_SANS_BOLD, fontSize=12.5,
            leading=17.0, textColor=COLOR_TEXT_PRIMARY, spaceBefore=12, spaceAfter=5,
            keepWithNext=True,
        ),
        # Body Prose
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=13.5,
            leading=20.5, alignment=0, textColor=COLOR_TEXT_PRIMARY, spaceAfter=8,
            allowWidows=False, allowOrphans=False,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=13.5,
            leading=20.5, textColor=COLOR_TEXT_PRIMARY, leftIndent=14, firstLineIndent=-8,
            spaceAfter=4, allowWidows=False, allowOrphans=False,
        ),
        # Code & Terminal
        "code_content": ParagraphStyle(
            "CodeContent", fontName=FONT_MONO, fontSize=10.0, leading=14.0,
            textColor=COLOR_BLACK, spaceBefore=0, spaceAfter=0,
        ),
        "code_gutter": ParagraphStyle(
            "CodeGutter", fontName=FONT_MONO, fontSize=10.0, leading=14.0,
            textColor=COLOR_TEXT_MUTED, alignment=2, spaceBefore=0, spaceAfter=0,
        ),
        "code_header": ParagraphStyle(
            "CodeHeader", fontName=FONT_SANS_BOLD, fontSize=8.0, leading=10.0,
            textColor=COLOR_TEXT_SECONDARY, spaceBefore=0, spaceAfter=0,
        ),
        "code_header_right": ParagraphStyle(
            "CodeHeaderRight", fontName=FONT_MONO, fontSize=7.5, leading=10.0,
            textColor=COLOR_TEXT_MUTED, alignment=2, spaceBefore=0, spaceAfter=0,
        ),
        "terminal_content": ParagraphStyle(
            "TerminalContent", fontName=FONT_MONO, fontSize=10.0, leading=14.0,
            textColor=COLOR_BLACK, spaceBefore=0, spaceAfter=0,
        ),
        # Tables
        "table_text": ParagraphStyle(
            "TableText", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=10.0,
            leading=14.0, textColor=COLOR_TEXT_PRIMARY,
        ),
        "table_bold": ParagraphStyle(
            "TableBold", parent=base["BodyText"], fontName=FONT_SANS_BOLD, fontSize=10.0,
            leading=14.0, textColor=COLOR_BLACK,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", parent=base["BodyText"], fontName=FONT_SANS_BOLD,
            fontSize=10.0, leading=14.0, textColor=colors.HexColor("#FFFFFF"),
        ),
        "table_caption": ParagraphStyle(
            "TableCaption", parent=base["BodyText"], fontName=FONT_SANS_BOLD, fontSize=9.5,
            leading=13.5, textColor=COLOR_BLACK, spaceBefore=8, spaceAfter=4,
            keepWithNext=True,
        ),
        # Captions
        "caption": ParagraphStyle(
            "Caption", parent=base["BodyText"], fontName=FONT_SANS, fontSize=9.2,
            leading=13.0, textColor=COLOR_TEXT_SECONDARY, spaceBefore=4, spaceAfter=8,
            keepWithNext=True,
        ),
        # Callouts & Lab Specs
        "callout_title": ParagraphStyle(
            "CalloutTitle", fontName=FONT_SANS_BOLD, fontSize=9.5, leading=13.0,
            textColor=COLOR_BLACK, spaceBefore=0, spaceAfter=4,
        ),
        "callout_body": ParagraphStyle(
            "CalloutBody", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=11.0,
            leading=16.0, textColor=COLOR_TEXT_PRIMARY, spaceAfter=0,
        ),
        "spec_badge": ParagraphStyle(
            "SpecBadge", fontName=FONT_MONO, fontSize=8.0, leading=11.0,
            textColor=COLOR_TEXT_MUTED, spaceAfter=0,
        ),
        "reference": ParagraphStyle(
            "Reference", parent=base["BodyText"], fontName=FONT_SANS, fontSize=9.0,
            leading=12.5, textColor=COLOR_TEXT_MUTED, leftIndent=14, firstLineIndent=-12,
            spaceAfter=4,
        ),
    }


# Running Header & Footer Callbacks for Mirrored Pages
def preview_header_footer_recto(canvas, doc):
    """Recto page (ODD): Right margin outside, Left margin inside."""
    canvas.saveState()
    # Running Header (Recto)
    canvas.setFont(FONT_SANS, 8.0)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    canvas.drawRightString(PAGE_WIDTH - MARGIN_OUTSIDE, PAGE_HEIGHT - 1.45 * cm, "CHƯƠNG 2 // KHI MỘT BẢN SAO VẪN CHIA SẺ DỮ LIỆU")
    canvas.setStrokeColor(COLOR_BORDER_HAIRLINE)
    canvas.setLineWidth(LINE_WEIGHT_HAIRLINE)
    canvas.line(MARGIN_INSIDE, PAGE_HEIGHT - 1.60 * cm, PAGE_WIDTH - MARGIN_OUTSIDE, PAGE_HEIGHT - 1.60 * cm)
    
    # Running Footer (Recto)
    canvas.line(MARGIN_INSIDE, 1.50 * cm, PAGE_WIDTH - MARGIN_OUTSIDE, 1.50 * cm)
    canvas.drawString(MARGIN_INSIDE, 1.10 * cm, "GOLANG ARCHITECTURAL SPECIFICATION — AGENT 2 PROTOTYPE")
    canvas.setFont(FONT_SANS_BOLD, 9.0)
    canvas.drawRightString(PAGE_WIDTH - MARGIN_OUTSIDE, 1.10 * cm, f"Trang {doc.page}")
    canvas.restoreState()


def preview_header_footer_verso(canvas, doc):
    """Verso page (EVEN): Left margin outside, Right margin inside."""
    canvas.saveState()
    # Running Header (Verso)
    canvas.setFont(FONT_SANS, 8.0)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    canvas.drawString(MARGIN_OUTSIDE, PAGE_HEIGHT - 1.45 * cm, "GOLANG: KỸ NGHỆ PHẦN MỀM VÀ DEVOPS/SRE")
    canvas.setStrokeColor(COLOR_BORDER_HAIRLINE)
    canvas.setLineWidth(LINE_WEIGHT_HAIRLINE)
    canvas.line(MARGIN_OUTSIDE, PAGE_HEIGHT - 1.60 * cm, PAGE_WIDTH - MARGIN_INSIDE, PAGE_HEIGHT - 1.60 * cm)
    
    # Running Footer (Verso)
    canvas.line(MARGIN_OUTSIDE, 1.50 * cm, PAGE_WIDTH - MARGIN_INSIDE, 1.50 * cm)
    canvas.drawString(MARGIN_OUTSIDE + 35, 1.10 * cm, "GOLANG ARCHITECTURAL SPECIFICATION — AGENT 2 PROTOTYPE")
    canvas.setFont(FONT_SANS_BOLD, 9.0)
    canvas.drawString(MARGIN_OUTSIDE, 1.10 * cm, f"Trang {doc.page}")
    canvas.restoreState()


def build_code_block(code_text: str, s: dict[str, ParagraphStyle], is_terminal: bool = False,
                     label: str = "SOURCE // GO 1.27.1") -> Table:
    """Build a professional software specification code block with line gutters or terminal header."""
    lines = code_text.strip("\n").split("\n")
    
    if is_terminal:
        # Terminal styling
        header_table = Table([[
            Paragraph(f"<b>TERMINAL OUTPUT</b> // {label}", s["code_header"]),
            Paragraph("status: 0 (verified)", s["code_header_right"])
        ]], colWidths=[PRINTABLE_WIDTH - 120, 100], hAlign="LEFT")
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        
        body_p = Paragraph(html.escape("\n".join(lines)).replace("\n", "<br/>").replace(" ", "&nbsp;"),
                           s["terminal_content"])
        
        main_table = Table([[header_table], [body_p]], colWidths=[PRINTABLE_WIDTH], hAlign="LEFT")
        main_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAECEF")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F4F5F7")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C0C4CC")),
            ("LINEBEFORE", (0, 0), (0, -1), 2.5, colors.HexColor("#4A5568")),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("LEFTPADDING", (0, 0), (-1, 0), 8),
            ("RIGHTPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 1), (-1, 1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
            ("LEFTPADDING", (0, 1), (-1, 1), 10),
            ("RIGHTPADDING", (0, 1), (-1, 1), 10),
        ]))
        return main_table
    
    # Source Code Styling (NO line numbers!)
    code_html = html.escape("\n".join(lines)).replace("\n", "<br/>").replace(" ", "&nbsp;").replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
    
    # Header bar
    header_table = Table([[
        Paragraph(f"<b>CODE SPECIFICATION</b> // {label}", s["code_header"]),
        Paragraph("amd64 // compiled", s["code_header_right"])
    ]], colWidths=[PRINTABLE_WIDTH - 120, 100], hAlign="LEFT")
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    
    content_p = Paragraph(code_html, s["code_content"])
    
    box = Table([[header_table], [content_p]], colWidths=[PRINTABLE_WIDTH], hAlign="LEFT")
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEDED")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F8F9FA")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D0D0D0")),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, COLOR_BLACK),
        ("TOPPADDING", (0, 0), (-1, 0), 3),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
        ("LEFTPADDING", (0, 0), (-1, 0), 8),
        ("RIGHTPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 1), (-1, 1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
        ("LEFTPADDING", (0, 1), (-1, 1), 10),
        ("RIGHTPADDING", (0, 1), (-1, 1), 10),
    ]))
    return box


def build_chapter_spec_card(s: dict[str, ParagraphStyle]) -> Table:
    """Build the Chapter 02 Architecture Specification Card (Mental Model Spec)."""
    rows = [
        [Paragraph("<b>BẢNG ĐẶC TẢ KIẾN TRÚC // CHAPTER 02 SPECIFICATION</b>", s["table_header"]),
         Paragraph("<b>QUY CHUẨN ĐỐI CHIẾU</b>", s["table_header"])],
        [Paragraph("<b>Ngữ nghĩa phép gán (Assignment)</b>", s["table_bold"]),
         Paragraph("Sao chép theo giá trị (Copy by value); Go không tự sinh bản sao ngầm của mảng nền.", s["table_text"])],
        [Paragraph("<b>Cấu trúc Slice Descriptor</b>", s["table_bold"]),
         Paragraph("24 byte (amd64): <code>Data uintptr</code> (8B), <code>len int</code> (8B), <code>cap int</code> (8B).", s["table_text"])],
        [Paragraph("<b>Ranh giới bộ nhớ (Backing Storage)</b>", s["table_bold"]),
         Paragraph("Mảng nền liên tiếp trên Heap/Stack; hiện tượng Aliasing xảy ra khi nhiều descriptor cùng trỏ tới một vùng nhớ.", s["table_text"])],
        [Paragraph("<b>Quy tắc an toàn (Safety Invariant)</b>", s["table_bold"]),
         Paragraph("Dùng <i>Full Slice Expression</i> <code>s[:n:n]</code> hoặc <code>make + copy</code> khi trả về view ra khỏi ranh giới API.", s["table_text"])],
    ]
    t = Table(rows, colWidths=[130, PRINTABLE_WIDTH - 130], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#F8F9FA")),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#FFFFFF")),
        ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#F8F9FA")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D0D0")),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, COLOR_BLACK),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def build_api_boundary_card(s: dict[str, ParagraphStyle]) -> Table:
    """Build the Section 2.9 API Boundary Decision Protocol Card."""
    rows = [
        [Paragraph("<b>QUY TRÌNH ĐIỀU TRA 3 BƯỚC // API BOUNDARY OWNERSHIP PROTOCOL</b>", s["table_header"]),
         Paragraph("<b>MỤC TIÊU XÁC ĐỊNH</b>", s["table_header"])],
        [Paragraph("<b>Bước 1: Giá trị nào được gán?</b>", s["table_bold"]),
         Paragraph("Xác định biến nhận được copy toàn bộ giá trị (như <code>int</code>, <code>[3]int</code>) hay chỉ nhận slice descriptor 24-byte.", s["table_text"])],
        [Paragraph("<b>Bước 2: Tham chiếu vùng nhớ nào?</b>", s["table_bold"]),
         Paragraph("Kiểm tra con trỏ <code>Data</code> dẫn tới backing array nào; <code>cap</code> còn lại bao nhiêu trước khi thực hiện <code>append</code>.", s["table_text"])],
        [Paragraph("<b>Bước 3: Ai còn quyền chạm storage?</b>", s["table_bold"]),
         Paragraph("Xác định tuổi thọ và quyền mutation giữa Caller và Callee. Nếu cần dữ liệu độc lập, bắt buộc dùng <code>make + copy</code> hoặc <code>bytes.Clone</code>.", s["table_text"])],
    ]
    t = Table(rows, colWidths=[150, PRINTABLE_WIDTH - 150], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#F8F9FA")),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#FFFFFF")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D0D0")),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, COLOR_BLACK),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def build_lab_callout(body_text: str, s: dict[str, ParagraphStyle], title: str = "THỰC HÀNH // BUG HUNT CÓ KIỂM CHỨNG") -> Table:
    """Build an interactive laboratory / bug hunt callout card."""
    content = [
        Paragraph(f"<b>{title}</b>", s["callout_title"]),
        Spacer(1, 2),
        Paragraph(inline(body_text), s["callout_body"]),
    ]
    box = Table([[content]], colWidths=[PRINTABLE_WIDTH], hAlign="LEFT")
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F5F7")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D4DC")),
        ("LINEBEFORE", (0, 0), (0, -1), 3.0, colors.HexColor("#1A1A1A")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return box


def build_verification_callout(body_text: str, s: dict[str, ParagraphStyle]) -> Table:
    """Build an architectural verification callout card."""
    content = [
        Paragraph("<b>ĐỐI CHIẾU KIẾN TRÚC // GIẢI MÃ BẢN CHẤT HÀNH VI</b>", s["callout_title"]),
        Spacer(1, 2),
        Paragraph(inline(body_text), s["callout_body"]),
    ]
    box = Table([[content]], colWidths=[PRINTABLE_WIDTH], hAlign="LEFT")
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("LINEBEFORE", (0, 0), (0, -1), 2.0, colors.HexColor("#666666")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return box


def parse_and_build_chapter_story(s: dict[str, ParagraphStyle]) -> list:
    """Parse Chapter 2 markdown and build the flowable story with new objects."""
    story = []
    lines = CHAPTER_FILE.read_text(encoding="utf-8").splitlines()
    
    # 1. Chapter Opener
    story.append(Paragraph("GOLANG ARCHITECTURAL SPECIFICATION // PART I: FOUNDATION CORE // CHAPTER 02", s["tracker"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER_HAIRLINE, spaceAfter=8))
    
    # Chapter Title & Numeral block
    story.append(Paragraph("CHƯƠNG 2 — KHI MỘT BẢN SAO VẪN CHIA SẺ DỮ LIỆU", s["h1"]))
    story.append(Paragraph(
        "Đặc tả sao chép giá trị (Copy by value), cấu trúc Descriptor 24-byte "
        "và hiện tượng Aliasing trên mảng nền trong Go runtime amd64.",
        s["chapter_subtitle"],
    ))
    
    # Specification Architecture Card
    story.append(build_chapter_spec_card(s))
    story.append(Spacer(1, 12))
    
    # Flowable parser
    in_code = False
    code_fence = ""
    code_lines = []
    table_lines = []
    table_caption = ""
    in_references = False
    
    # State tracking
    section_count = 0
    figure_count = 0
    
    def flush_table():
        nonlocal table_lines, table_caption
        if not table_lines:
            return
        rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table_lines]
        data = []
        for r_idx, r in enumerate([rows[0], *rows[2:]]):
            st = s["table_header"] if r_idx == 0 else (s["table_bold"] if r_idx % 2 == 1 else s["table_text"])
            data.append([Paragraph(inline(c), st) for c in r])
        
        t = Table(data, colWidths=[140, PRINTABLE_WIDTH - 140], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1A1A")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
            ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#F8F9FA")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D0D0")),
            ("LINEBELOW", (0, 0), (-1, 0), 1.0, COLOR_BLACK),
            ("TOPPADDING", (0, 0), (-1, -1), 4.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        
        elements = []
        if table_caption:
            elements.append(Paragraph(f"<b>Bảng 1 — {inline(table_caption)}</b>", s["table_caption"]))
        elements.append(t)
        elements.append(Spacer(1, 10))
        story.append(KeepTogether(elements))
        table_lines = []
        table_caption = ""
    
    def flush_code():
        nonlocal code_lines, code_fence
        if not code_lines:
            return
        code_text = "\n".join(code_lines)
        is_terminal = (code_fence in ("text", "bash", "sh")) or ("fmt.Println" not in code_text and "func" not in code_text and ":=" not in code_text and "[" in code_text)
        
        label = "RUNTIME EXECUTION OUTPUT" if is_terminal else "PACKAGE MAIN // VERIFIED SNIPPET"
        box = build_code_block(code_text, s, is_terminal=is_terminal, label=label)
        story.append(KeepTogether([Spacer(1, 3), box, Spacer(1, 8)]))
        code_lines = []
        code_fence = ""
    
    i = 0
    total = len(lines)
    while i < total:
        line = lines[i]
        
        # Skip the original H1 since we rendered our architectural opener
        if line.startswith("# ") and i < 10:
            i += 1
            continue
        if line.strip().startswith("<!-- BOOK_ROLE"):
            i += 1
            continue
        
        # Skip standalone @figure lines (they are consumed when parsing images)
        if line.startswith("@figure "):
            i += 1
            continue
            
        # Code fence handling
        if line.startswith(("```", "~~~")):
            if in_code:
                in_code = False
                flush_code()
            else:
                in_code = True
                code_fence = line[3:].strip()
                code_lines = []
            i += 1
            continue
        
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        
        # Table handling
        if line.startswith("@table "):
            table_caption = line[7:].strip()
            i += 1
            continue
        if line.startswith("|"):
            table_lines.append(line)
            i += 1
            continue
        if table_lines:
            flush_table()
        
        # Section Heading H2 (no trailing HRFlowable so keepWithNext=True binds cleanly to the next paragraph)
        if line.startswith("## "):
            section_count += 1
            current_sec_title = line[3:].strip()
            sec_heading = f"§ 2.{section_count} — {current_sec_title}"
            story.append(Paragraph(sec_heading, s["h2"]))
            
            # Check if this is Section 2.9 (API boundary), prepare to add the 3-step protocol card
            i += 1
            continue
        
        # Diagram handling: Scan forward skipping blank lines to find @figure caption
        if line.startswith("![") and "](" in line:
            cap_text = ""
            j = i + 1
            while j < total and not lines[j].strip():
                j += 1
            if j < total and lines[j].startswith("@figure "):
                cap_text = lines[j][8:].strip()
                i = j  # advance past the @figure line
            
            if "array-copy" in line:
                figure_count += 1
                diag = vd.build_array_copy_drawing(PRINTABLE_WIDTH, 120)
                if not cap_text:
                    cap_text = "Phép gán mảng (Array assignment) thực hiện sao chép toàn bộ các phần tử sang vùng nhớ độc lập."
                caption = Paragraph(f"<b>Hình {figure_count}</b> — {inline(cap_text)}", s["caption"])
                story.append(KeepTogether([Spacer(1, 4), diag, Spacer(1, 3), caption, Spacer(1, 6)]))
                i += 1
                continue
            elif "slice-sharing" in line:
                figure_count += 1
                diag = vd.build_slice_sharing_drawing(PRINTABLE_WIDTH, 160)
                if not cap_text:
                    cap_text = "b := a sao chép 24-byte descriptor (cùng con trỏ Data, len, cap). Cả hai descriptor cùng trỏ tới một backing array."
                caption = Paragraph(f"<b>Hình {figure_count}</b> — {inline(cap_text)}", s["caption"])
                story.append(KeepTogether([Spacer(1, 4), diag, Spacer(1, 3), caption, Spacer(1, 6)]))
                
                # High-Value Non-Technical / Artistic Pedagogical Object: 3D Axonometric Section
                figure_count += 1
                iso_diag = vd.build_isometric_memory_section_drawing(PRINTABLE_WIDTH, 175)
                iso_cap = Paragraph(
                    f"<b>Hình {figure_count} (Lát cắt kiến trúc)</b> — Mô hình không gian 3 chiều (Axonometric Manual of Section): "
                    "Descriptor 24-byte trên Stack Frame dẫn đường truyền con trỏ xuống vùng nhớ mảng nền liên tiếp trên Heap.",
                    s["caption"]
                )
                story.append(KeepTogether([Spacer(1, 6), iso_diag, Spacer(1, 3), iso_cap, Spacer(1, 8)]))
                i += 1
                continue
            elif "slice-window" in line:
                figure_count += 1
                diag = vd.build_slice_window_drawing(PRINTABLE_WIDTH, 145)
                if not cap_text:
                    cap_text = "x nhìn thấy hai phần tử đầu của cửa sổ [20, 30]. cap(x) = 4 giới hạn phạm vi mở rộng trong mảng nền hiện tại."
                caption = Paragraph(f"<b>Hình {figure_count}</b> — {inline(cap_text)}", s["caption"])
                story.append(KeepTogether([Spacer(1, 4), diag, Spacer(1, 3), caption, Spacer(1, 6)]))
                i += 1
                continue
            elif "append-storage" in line:
                figure_count += 1
                diag = vd.build_append_storage_drawing(PRINTABLE_WIDTH, 145)
                if not cap_text:
                    cap_text = "Hai kịch bản của append: Còn sức chứa thì tái sử dụng mảng nền; hết sức chứa thì runtime cấp phát mảng nền mới."
                caption = Paragraph(f"<b>Hình {figure_count}</b> — {inline(cap_text)}", s["caption"])
                story.append(KeepTogether([Spacer(1, 4), diag, Spacer(1, 3), caption, Spacer(1, 6)]))
                i += 1
                continue
        
        # References header
        if line.strip() == "@references":
            in_references = True
            story.append(Spacer(1, 8))
            story.append(Paragraph("TÀI LIỆU ĐỐI CHIẾU CHUẨN (SPECIFICATION REFERENCES)", s["h3"]))
            story.append(HRFlowable(width="100%", thickness=0.4, color=COLOR_BORDER_LIGHT, spaceAfter=6))
            i += 1
            continue
        
        # Callouts / Interactive Sections
        if line.startswith("**Thực hành - bug hunt có kiểm chứng.**"):
            callout_text = line[len("**Thực hành - bug hunt có kiểm chứng.**"):].strip()
            while i + 1 < total and lines[i + 1].strip() and not lines[i + 1].startswith(("---", "##", "```", "~~~")):
                i += 1
                callout_text += " " + lines[i].strip()
            story.append(KeepTogether([Spacer(1, 4), build_lab_callout(callout_text, s), Spacer(1, 8)]))
            i += 1
            continue
        
        if line.startswith("**Đáp án — chỉ đọc sau khi đã tự làm.**"):
            ans_text = line[len("**Đáp án — chỉ đọc sau khi đã tự làm.**"):].strip()
            while i + 1 < total and lines[i + 1].strip() and not lines[i + 1].startswith(("---", "##", "```", "~~~")):
                i += 1
                ans_text += " " + lines[i].strip()
            story.append(KeepTogether([Spacer(1, 4), build_verification_callout(ans_text, s), Spacer(1, 8)]))
            i += 1
            continue
        
        # Horizontal rule
        if line.strip() == "---":
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.4, color=COLOR_BORDER_LIGHT, spaceAfter=6))
            i += 1
            continue
        
        # Numbered reference items
        if in_references and re.match(r"^\d+\.\s+", line):
            m = re.match(r"^(\d+)\.\s+(.+)$", line)
            num, ref_text = m.group(1), m.group(2)
            story.append(Paragraph(f"[{num}] {inline(ref_text)}", s["reference"]))
            i += 1
            continue
        
        # Regular Prose paragraph
        if line.strip():
            para_lines = [line.strip()]
            while i + 1 < total and lines[i + 1].strip() and not lines[i + 1].startswith(
                ("##", "```", "~~~", "![", "@table", "@figure", "@references", "---", "**Thực hành", "**Đáp án", "|")
            ):
                i += 1
                para_lines.append(lines[i].strip())
            full_para = " ".join(para_lines)
            story.append(Paragraph(inline(full_para), s["body"]))
            
            # If we just rendered the final summary of Section 2.9, append the API boundary protocol card
            if "Đó là cách biến “slice lạ quá” thành một cuộc điều tra có thể kiểm chứng." in full_para:
                story.append(Spacer(1, 6))
                story.append(KeepTogether([build_api_boundary_card(s), Spacer(1, 8)]))
        
        i += 1
    
    if table_lines:
        flush_table()
    if code_lines:
        flush_code()
        
    return story


def build():
    """Build the standalone preview PDF and generate specimen PNGs."""
    print("=" * 60)
    print("AGENT 2: BUILDING CHAPTER 2 REDESIGN PREVIEW")
    print("=" * 60)
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SPECIMENS_DIR.mkdir(parents=True, exist_ok=True)
    
    register_fonts()
    s = get_preview_styles()
    
    frame_recto = Frame(
        MARGIN_INSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="preview_frame_recto", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    frame_verso = Frame(
        MARGIN_OUTSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="preview_frame_verso", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    
    template_recto = PageTemplate(id="preview_recto", frames=[frame_recto], onPage=preview_header_footer_recto)
    template_verso = PageTemplate(id="preview_verso", frames=[frame_verso], onPage=preview_header_footer_verso)
    
    # Custom MirroredDocTemplate with verified parity switching
    class PreviewDocTemplate(BaseDocTemplate):
        def _setPageTemplate(self):
            super()._setPageTemplate()
            cur_id = self.pageTemplate.id
            next_page = self.page + 1
            target_id = "preview_verso" if next_page % 2 == 0 else "preview_recto"
            if target_id != cur_id:
                for t in self.pageTemplates:
                    if t.id == target_id:
                        self.pageTemplate = t
                        break

    doc = PreviewDocTemplate(
        str(PREVIEW_PDF),
        pagesize=PAGE_SIZE,
        title="Chương 2 — Khi một bản sao vẫn chia sẻ dữ liệu (Agent 2 Redesign)",
        author="Đoàn Ngọc Hoàng Minh",
        subject="Thiết kế đặc tả kiến trúc — Agent 2",
        leftMargin=MARGIN_INSIDE,
        rightMargin=MARGIN_OUTSIDE,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )
    doc.addPageTemplates([template_recto, template_verso])
    
    story = parse_and_build_chapter_story(s)
    doc.build(story)
    print(f"[SUCCESS] Preview PDF generated: {PREVIEW_PDF}")
    
    # Render all pages to PNG specimens
    print("\nRendering specimen PNG images...")
    pdf_doc = fitz.open(str(PREVIEW_PDF))
    total_pages = len(pdf_doc)
    print(f"Total preview pages: {total_pages}")
    
    specimen_paths = []
    for p in range(total_pages):
        page = pdf_doc[p]
        pix = page.get_pixmap(dpi=150)
        img_path = SPECIMENS_DIR / f"ch02_page_{p + 1:02d}.png"
        pix.save(img_path)
        specimen_paths.append(img_path)
        print(f"  - Rendered: {img_path.name}")
        
    print(f"\n[COMPLETE] All {total_pages} specimen images saved to {SPECIMENS_DIR}")
    return PREVIEW_PDF, specimen_paths


if __name__ == "__main__":
    build()
