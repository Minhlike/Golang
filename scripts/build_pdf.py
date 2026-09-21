"""Render the current Markdown edition into a checked, replace-safe PDF.

This is deliberately a small local renderer, not a general Markdown engine.
It supports the book constructs currently used (headings, paragraphs, lists,
code, horizontal rules, and local diagrams) and fails loudly on missing assets.
"""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate


ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = [
    ROOT / "book/chapters/00-truoc-khi-viet-dong-go-dau-tien.md",
    ROOT / "book/chapters/00-mo-cua-vao-go.md",
    ROOT / "book/chapters/01-doc-va-viet-mot-chuong-trinh-go.md",
    ROOT / "book/chapters/02-gia-tri-slice-va-aliasing.md",
    ROOT / "book/chapters/03-mo-hinh-du-lieu-va-trach-nhiem-thay-doi.md",
    ROOT / "book/chapters/04-bien-loi.md",
    ROOT / "book/chapters/05-thiet-ke-package.md",
    ROOT / "book/chapters/06-thay-doi-khong-so-hai.md",
    ROOT / "book/chapters/07-du-lieu-di-vao-va-di-ra.md",
    ROOT / "book/chapters/08-mot-race-bat-dau-tu-dau.md",
    ROOT / "book/chapters/09-dong-cong-viec-co-ap-suat.md",
    ROOT / "book/chapters/10-khi-chuong-trinh-cham-hoac-phinh.md",
    ROOT / "book/chapters/11-mot-request-thuc-su-di-dau.md",
    ROOT / "book/chapters/12-mot-service-song-va-tat-the-nao.md",
]
TMP = ROOT / "tmp/pdfs"
CANDIDATE = TMP / "Golang_Master.candidate.pdf"
CURRENT = ROOT / "Golang_Master.pdf"
PREVIOUS = ROOT / "Golang_Master.prev.pdf"


def register_fonts() -> tuple[str, str, str, str, str]:
    """Embed the approved reading fonts; never depend on a system font."""
    fonts = ROOT / "assets/fonts"
    body = fonts / "SourceSerif4-Regular.ttf"
    body_bold = fonts / "SourceSerif4-Semibold.ttf"
    heading = fonts / "SourceSans3-Regular.ttf"
    heading_bold = fonts / "SourceSans3-Semibold.ttf"
    mono = fonts / "JetBrainsMono-Regular.ttf"
    for path in (body, body_bold, heading, heading_bold, mono):
        if not path.exists():
            raise FileNotFoundError(f"Thiếu font cần cho PDF: {path}")
    pdfmetrics.registerFont(TTFont("BookSerif", str(body)))
    pdfmetrics.registerFont(TTFont("BookSerifBold", str(body_bold)))
    pdfmetrics.registerFont(TTFont("BookSans", str(heading)))
    pdfmetrics.registerFont(TTFont("BookSansBold", str(heading_bold)))
    pdfmetrics.registerFont(TTFont("BookMono", str(mono)))
    return "BookSerif", "BookSerifBold", "BookSans", "BookSansBold", "BookMono"


def inline(text: str, mono: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(
        r"`([^`]+)`",
        lambda m: f'<font name="{mono}" color="#111111">{m.group(1)}</font>',
        escaped,
    )
    return re.sub(
        r"\*\*(.+?)\*\*",
        r'<font name="BookSansBold">\1</font>',
        escaped,
    )


def styles(body: str, body_bold: str, heading: str, heading_bold: str,
           mono: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "BookTitle", parent=base["Title"], fontName=heading_bold, fontSize=30,
            leading=36, alignment=TA_CENTER, textColor=colors.black,
            spaceAfter=18,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["BodyText"], fontName=heading, fontSize=13,
            leading=19, alignment=TA_CENTER, textColor=colors.HexColor("#333333"),
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName=heading_bold, fontSize=23,
            leading=29, textColor=colors.black, spaceBefore=5,
            spaceAfter=15, keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName=heading_bold, fontSize=16.5,
            leading=22, textColor=colors.black, spaceBefore=17,
            spaceAfter=8, keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontName=heading_bold, fontSize=14,
            leading=19, textColor=colors.black, spaceBefore=13,
            spaceAfter=6, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName=body, fontSize=14,
            leading=21.4, alignment=TA_LEFT, textColor=colors.black, spaceAfter=9,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base["BodyText"], fontName=body, fontSize=14,
            leading=21, textColor=colors.black, leftIndent=18, firstLineIndent=-10,
            spaceAfter=4, bulletFontName=body,
        ),
        "toc": ParagraphStyle(
            "TOC", parent=base["BodyText"], fontName=body, fontSize=14,
            leading=21, textColor=colors.black, leftIndent=7, spaceAfter=5,
        ),
        "code": ParagraphStyle(
            "Code", fontName=mono, fontSize=12, leading=16.5,
            textColor=colors.black, spaceBefore=0, spaceAfter=0,
        ),
        "table": ParagraphStyle(
            "Table", parent=base["BodyText"], fontName=body, fontSize=11.2,
            leading=14.8, textColor=colors.black,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", parent=base["BodyText"], fontName=body_bold,
            fontSize=11.2, leading=14.8, textColor=colors.black,
        ),
        "caption": ParagraphStyle(
            "Caption", parent=base["BodyText"], fontName=body, fontSize=10.8,
            leading=14.2, textColor=colors.HexColor("#333333"), spaceAfter=10,
        ),
        "reference": ParagraphStyle(
            "Reference", parent=base["BodyText"], fontName=heading, fontSize=9.7,
            leading=13.0, textColor=colors.HexColor("#333333"), leftIndent=14,
            firstLineIndent=-12, spaceAfter=4,
        ),
    }


def cover(story: list, s: dict[str, ParagraphStyle]) -> None:
    story.extend([
        Spacer(1, 5.4 * cm),
        Paragraph("GOLANG", s["title"]),
        Paragraph("Living Textbook cho Software Engineering và DevOps/SRE", s["subtitle"]),
        Spacer(1, 1.1 * cm),
        HRFlowable(width="64%", thickness=1.0, color=colors.black,
                   hAlign="CENTER"),
        Spacer(1, 1.1 * cm),
        Paragraph("Edition nền móng", s["subtitle"]),
        Paragraph("Được kiểm chứng với Go 1.27.1 - 21-09-2026", s["subtitle"]),
        Spacer(1, 4.8 * cm),
        Paragraph("Markdown là nguồn gốc. PDF là bản đọc được, có thể tái tạo cục bộ.", s["subtitle"]),
        PageBreak(),
    ])


def chapter_titles() -> list[str]:
    result: list[str] = []
    for chapter in CHAPTERS:
        first = chapter.read_text(encoding="utf-8").splitlines()[0]
        if not first.startswith("# "):
            raise ValueError(f"Chapter does not start with H1: {chapter}")
        result.append(first[2:])
    return result


def add_markdown(story: list, chapter: Path, s: dict[str, ParagraphStyle], mono: str,
                 page_break_before: bool, numbering: dict[str, int]) -> None:
    if page_break_before:
        story.append(PageBreak())
    lines = chapter.read_text(encoding="utf-8").splitlines()
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    table_lines: list[str] = []
    table_caption: str | None = None
    pending_image: Image | None = None
    in_references = False
    in_code = False

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            story.append(Paragraph(inline(" ".join(paragraph_lines), mono), s["body"]))
            paragraph_lines = []

    def flush_table() -> None:
        nonlocal table_lines, table_caption
        if not table_lines:
            return
        rows = [[cell.strip() for cell in row.strip().strip("|").split("|")]
                for row in table_lines]
        if len(rows) < 2 or not all(re.fullmatch(r"[: -]+", cell) for cell in rows[1]):
            raise ValueError(f"Bảng Markdown không hợp lệ trong {chapter}")
        columns = len(rows[0])
        if columns < 2 or any(len(row) != columns for row in rows):
            raise ValueError(f"Cột bảng không nhất quán trong {chapter}")
        data = []
        for row_index, row in enumerate([rows[0], *rows[2:]]):
            style = s["table_header"] if row_index == 0 else s["table"]
            data.append([Paragraph(inline(cell, mono), style) for cell in row])
        table = Table(data, colWidths=[16.8 * cm / columns] * columns, repeatRows=1,
                      hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAE7")),
            ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#777777")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        flowables = [Spacer(1, 3), table]
        if table_caption:
            numbering["table"] += 1
            flowables.extend([
                Spacer(1, 4),
                Paragraph(f"Bảng {numbering['table']} — {inline(table_caption, mono)}",
                          s["caption"]),
            ])
        flowables.append(Spacer(1, 10))
        story.append(KeepTogether(flowables))
        table_lines = []
        table_caption = None

    def add_code_block() -> None:
        """Make tabs deterministic and keep code distinct in light mode."""
        nonlocal code_lines
        code = Preformatted("\n".join(code_lines).expandtabs(4), s["code"])
        box = Table([[code]], colWidths=[16.8 * cm], hAlign="LEFT")
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F3F1")),
            ("BOX", (0, 0), (-1, -1), 0.65, colors.HexColor("#777777")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))
        story.append(KeepTogether([Spacer(1, 5), box, Spacer(1, 12)]))
        code_lines = []

    def flush_image() -> None:
        nonlocal pending_image
        if pending_image is not None:
            story.extend([Spacer(1, 4), pending_image, Spacer(1, 6)])
            pending_image = None

    for line in lines:
        if pending_image is not None and line.startswith("@figure "):
            numbering["figure"] += 1
            story.append(KeepTogether([
                Spacer(1, 4), pending_image, Spacer(1, 4),
                Paragraph(
                    f"Hình {numbering['figure']} — {inline(line[8:], mono)}",
                    s["caption"],
                ),
            ]))
            pending_image = None
            continue
        if pending_image is not None and not line.strip():
            continue
        flush_image()
        if line.startswith(("```", "~~~")):
            flush_paragraph()
            if in_code:
                add_code_block()
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        if line.startswith("|"):
            flush_paragraph()
            table_lines.append(line)
            continue
        flush_table()
        if line.startswith("@table "):
            flush_paragraph()
            table_caption = line[7:]
            continue
        if line.strip() == "@references":
            flush_paragraph()
            in_references = True
            continue
        if line.strip() == "<!-- pagebreak -->":
            flush_paragraph()
            story.append(PageBreak())
            continue
        image = re.fullmatch(r"!\[[^]]*\]\(([^)]+)\)", line)
        if image:
            flush_paragraph()
            asset = (chapter.parent / image.group(1)).resolve()
            if not asset.exists():
                raise FileNotFoundError(f"Thiếu diagram: {asset}")
            drawing = Image(str(asset))
            drawing._restrictSize(16.8 * cm, 12.8 * cm)
            drawing.hAlign = "CENTER"
            pending_image = drawing
            continue
        quote = re.match(r"^>\s+(.+)$", line)
        if quote:
            flush_paragraph()
            note = Table([[Paragraph(inline(quote.group(1), mono), s["body"])]],
                         colWidths=[16.8 * cm], hAlign="LEFT")
            note.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F2")),
                ("LINEBEFORE", (0, 0), (0, -1), 2.0, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.extend([Spacer(1, 4), note, Spacer(1, 11)])
            continue
        if not line.strip():
            flush_paragraph()
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            in_references = False
            level = len(heading.group(1))
            story.append(Paragraph(inline(heading.group(2), mono), s[f"h{level}"]))
            continue
        if line.strip() == "---":
            flush_paragraph()
            story.extend([Spacer(1, 3), HRFlowable(width="100%", thickness=0.55,
                         color=colors.HexColor("#999999")), Spacer(1, 5)])
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        numbered = re.match(r"^(\d+)\.\s+(.+)$", line)
        if bullet or numbered:
            flush_paragraph()
            text = (bullet or numbered).group(1 if bullet else 2)
            marker = "•" if bullet else f"{numbered.group(1)}."
            paragraph_style = s["reference"] if in_references else s["bullet"]
            story.append(Paragraph(inline(text, mono), paragraph_style, bulletText=marker))
            continue
        paragraph_lines.append(line.strip())
    if in_code:
        raise ValueError(f"Unclosed code fence: {chapter}")
    flush_image()
    flush_table()
    flush_paragraph()


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#B5B5B5"))
    canvas.line(2.0 * cm, 1.55 * cm, A4[0] - 2.0 * cm, 1.55 * cm)
    canvas.setFont("BookSans", 9.5)
    canvas.setFillColor(colors.HexColor("#333333"))
    canvas.drawString(2.0 * cm, 1.08 * cm, "Golang Living Textbook - Edition nền móng")
    canvas.drawRightString(A4[0] - 2.0 * cm, 1.08 * cm, str(doc.page))
    canvas.restoreState()


def build() -> None:
    for chapter in CHAPTERS:
        if not chapter.exists():
            raise FileNotFoundError(f"Thiếu chapter: {chapter}")
    body, body_bold, heading, heading_bold, mono = register_fonts()
    s = styles(body, body_bold, heading, heading_bold, mono)
    TMP.mkdir(parents=True, exist_ok=True)
    frame = Frame(2.1 * cm, 2.0 * cm, A4[0] - 4.2 * cm, A4[1] - 3.9 * cm,
                  id="book", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(str(CANDIDATE), pagesize=A4, title="Golang Master",
                          author="Golang Living Textbook", leftMargin=2.1 * cm,
                          rightMargin=2.1 * cm, topMargin=2.0 * cm, bottomMargin=2.0 * cm)
    doc.addPageTemplates([PageTemplate(id="book", frames=[frame], onPage=footer)])
    story: list = []
    cover(story, s)
    story.append(Paragraph("Mục lục của edition này", s["h1"]))
    story.append(Paragraph(
        "Đây là edition nền móng. Mục lục tổng thể và thứ tự các phần tiếp theo "
        "được giữ trong `book/README.md` để có thể mở rộng mà không giả vờ rằng "
        "chúng đã được viết xong.", s["body"]))
    for title in chapter_titles():
        story.append(Paragraph(inline(title, mono), s["toc"], bulletText="•"))
    story.append(PageBreak())
    numbering = {"figure": 0, "table": 0}
    for index, chapter in enumerate(CHAPTERS):
        add_markdown(story, chapter, s, mono, page_break_before=index > 0, numbering=numbering)
    doc.build(story)

    reader = PdfReader(str(CANDIDATE))
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    if len(reader.pages) < 6 or "GOLANG" not in extracted or "Chương 1" not in extracted:
        raise RuntimeError("Candidate PDF failed semantic validation.")

    if CURRENT.exists():
        shutil.copy2(CURRENT, PREVIOUS)
    else:
        shutil.copy2(CANDIDATE, PREVIOUS)
    next_path = TMP / "Golang_Master.next.pdf"
    shutil.copy2(CANDIDATE, next_path)
    next_path.replace(CURRENT)
    print(f"Built {CURRENT.name}: {len(reader.pages)} pages")
    print(f"Rollback copy: {PREVIOUS.name}")


if __name__ == "__main__":
    build()
