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
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate


ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = [
    ROOT / "book/chapters/00-loi-noi-dau.md",
    ROOT / "book/chapters/01-go-toolchain-va-vong-lap.md",
    ROOT / "book/chapters/02-chuong-trinh-dau-tien.md",
]
TMP = ROOT / "tmp/pdfs"
CANDIDATE = TMP / "Golang_Master.candidate.pdf"
CURRENT = ROOT / "Golang_Master.pdf"
PREVIOUS = ROOT / "Golang_Master.prev.pdf"


def register_fonts() -> tuple[str, str, str]:
    fonts = Path("C:/Windows/Fonts")
    regular = fonts / "arial.ttf"
    bold = fonts / "arialbd.ttf"
    mono = fonts / "consola.ttf"
    for path in (regular, bold, mono):
        if not path.exists():
            raise FileNotFoundError(f"Thiếu font cần cho PDF: {path}")
    pdfmetrics.registerFont(TTFont("BookSans", str(regular)))
    pdfmetrics.registerFont(TTFont("BookSansBold", str(bold)))
    pdfmetrics.registerFont(TTFont("BookMono", str(mono)))
    return "BookSans", "BookSansBold", "BookMono"


def inline(text: str, mono: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(
        r"`([^`]+)`",
        lambda m: f'<font name="{mono}" color="#154360">{m.group(1)}</font>',
        escaped,
    )
    return re.sub(
        r"\*\*(.+?)\*\*",
        r'<font name="BookSansBold">\1</font>',
        escaped,
    )


def styles(regular: str, bold: str, mono: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "BookTitle", parent=base["Title"], fontName=bold, fontSize=28,
            leading=34, alignment=TA_CENTER, textColor=colors.HexColor("#123B52"),
            spaceAfter=18,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["BodyText"], fontName=regular, fontSize=12,
            leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#45636F"),
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName=bold, fontSize=20,
            leading=26, textColor=colors.HexColor("#123B52"), spaceBefore=4,
            spaceAfter=13, keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName=bold, fontSize=14,
            leading=19, textColor=colors.HexColor("#176B87"), spaceBefore=14,
            spaceAfter=7, keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontName=bold, fontSize=11.5,
            leading=15, textColor=colors.HexColor("#176B87"), spaceBefore=10,
            spaceAfter=5, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName=regular, fontSize=10.3,
            leading=15.4, alignment=TA_LEFT, spaceAfter=7,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base["BodyText"], fontName=regular, fontSize=10.3,
            leading=15, leftIndent=14, firstLineIndent=-9, spaceAfter=3,
            bulletFontName=regular,
        ),
        "toc": ParagraphStyle(
            "TOC", parent=base["BodyText"], fontName=regular, fontSize=11,
            leading=17, leftIndent=5, spaceAfter=4,
        ),
        "code": ParagraphStyle(
            "Code", fontName=mono, fontSize=8.2, leading=11.4,
            textColor=colors.HexColor("#17202A"), backColor=colors.HexColor("#F2F5F7"),
            borderColor=colors.HexColor("#D5DDE1"), borderWidth=0.45,
            borderPadding=7, spaceBefore=4, spaceAfter=10,
        ),
    }


def cover(story: list, s: dict[str, ParagraphStyle]) -> None:
    story.extend([
        Spacer(1, 5.4 * cm),
        Paragraph("GOLANG", s["title"]),
        Paragraph("Living Textbook cho Software Engineering và DevOps/SRE", s["subtitle"]),
        Spacer(1, 1.1 * cm),
        HRFlowable(width="64%", thickness=1.2, color=colors.HexColor("#1F7A8C"),
                   hAlign="CENTER"),
        Spacer(1, 1.1 * cm),
        Paragraph("Edition nền móng", s["subtitle"]),
        Paragraph("Được kiểm chứng với Go 1.27.1 - 20-09-2026", s["subtitle"]),
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
                 page_break_before: bool) -> None:
    if page_break_before:
        story.append(PageBreak())
    lines = chapter.read_text(encoding="utf-8").splitlines()
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    in_code = False

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            story.append(Paragraph(inline(" ".join(paragraph_lines), mono), s["body"]))
            paragraph_lines = []

    for line in lines:
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(Preformatted("\n".join(code_lines), s["code"]))
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        image = re.fullmatch(r"!\[[^]]*\]\(([^)]+)\)", line)
        if image:
            flush_paragraph()
            asset = (chapter.parent / image.group(1)).resolve()
            if not asset.exists():
                raise FileNotFoundError(f"Thiếu diagram: {asset}")
            drawing = Image(str(asset))
            drawing._restrictSize(16.0 * cm, 10.7 * cm)
            story.extend([Spacer(1, 4), drawing, Spacer(1, 6)])
            continue
        if not line.strip():
            flush_paragraph()
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            story.append(Paragraph(inline(heading.group(2), mono), s[f"h{level}"]))
            continue
        if line.strip() == "---":
            flush_paragraph()
            story.extend([Spacer(1, 3), HRFlowable(width="100%", thickness=0.55,
                         color=colors.HexColor("#AAB7B8")), Spacer(1, 5)])
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        numbered = re.match(r"^(\d+)\.\s+(.+)$", line)
        if bullet or numbered:
            flush_paragraph()
            text = (bullet or numbered).group(1 if bullet else 2)
            marker = "•" if bullet else f"{numbered.group(1)}."
            story.append(Paragraph(inline(text, mono), s["bullet"], bulletText=marker))
            continue
        paragraph_lines.append(line.strip())
    if in_code:
        raise ValueError(f"Unclosed code fence: {chapter}")
    flush_paragraph()


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#B8C7CC"))
    canvas.line(2.0 * cm, 1.55 * cm, A4[0] - 2.0 * cm, 1.55 * cm)
    canvas.setFont("BookSans", 8)
    canvas.setFillColor(colors.HexColor("#56717A"))
    canvas.drawString(2.0 * cm, 1.08 * cm, "Golang Living Textbook - Edition nền móng")
    canvas.drawRightString(A4[0] - 2.0 * cm, 1.08 * cm, str(doc.page))
    canvas.restoreState()


def build() -> None:
    for chapter in CHAPTERS:
        if not chapter.exists():
            raise FileNotFoundError(f"Thiếu chapter: {chapter}")
    regular, bold, mono = register_fonts()
    s = styles(regular, bold, mono)
    TMP.mkdir(parents=True, exist_ok=True)
    frame = Frame(2.0 * cm, 2.0 * cm, A4[0] - 4.0 * cm, A4[1] - 3.9 * cm,
                  id="book", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(str(CANDIDATE), pagesize=A4, title="Golang Master",
                          author="Golang Living Textbook", leftMargin=2.0 * cm,
                          rightMargin=2.0 * cm, topMargin=2.0 * cm, bottomMargin=2.0 * cm)
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
    for index, chapter in enumerate(CHAPTERS):
        add_markdown(story, chapter, s, mono, page_break_before=index > 0)
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
