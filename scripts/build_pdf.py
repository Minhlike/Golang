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

from pypdf import PdfReader, PdfWriter
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
    NextPageTemplate,
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
ERROR_ATLAS = ROOT / "book/appendices/error-atlas.md"
TMP = ROOT / "tmp/pdfs"
CANDIDATE = TMP / "Golang_Master.candidate.pdf"
CURRENT = ROOT / "Golang_Master.pdf"
PREVIOUS = ROOT / "Golang_Master.prev.pdf"


def chapter_sort_key(p: Path) -> tuple[int, int, str]:
    """Sort chapters by canonical order: 00-truoc-khi..., 00-mo-cua..., then 01, 02..."""
    name = p.stem
    if name == "00-truoc-khi-viet-dong-go-dau-tien":
        return (0, 0, name)
    if name == "00-mo-cua-vao-go":
        return (0, 1, name)
    prefix = name.split("-")[0]
    if prefix.isdigit():
        return (1, int(prefix), name)
    return (2, 0, name)


def get_chapters() -> list[Path]:
    """Discover all chapters dynamically sorted in canonical order."""
    chapters_dir = ROOT / "book/chapters"
    if not chapters_dir.exists():
        return []
    return sorted(chapters_dir.glob("*.md"), key=chapter_sort_key)


def get_appendices() -> list[Path]:
    """Return all appendices, guaranteeing that Error Atlas is ALWAYS last in the book."""
    appendices_dir = ROOT / "book/appendices"
    if not appendices_dir.exists():
        return [ERROR_ATLAS]
    other_appendices = [
        p for p in sorted(appendices_dir.glob("*.md"))
        if p.name != "error-atlas.md"
    ]
    return other_appendices + [ERROR_ATLAS]


def get_manuscript() -> tuple[list[Path], list[Path]]:
    """Return (chapters, appendices) enforcing the strict contract:
    frontmatter -> chapters in order -> appendices -> Error Atlas ALWAYS AT THE END.
    Any newly added chapters (Ch22, Ch23...) are automatically placed before appendices.
    """
    return get_chapters(), get_appendices()


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
            "TOC", parent=base["BodyText"], fontName=body, fontSize=11.5,
            leading=16.0, textColor=colors.black, leftIndent=7, spaceAfter=2.5,
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
        # Error Atlas 2-column styles (Grayscale-first technical handbook typography)
        "atlas_h1": ParagraphStyle(
            "AtlasH1", parent=base["Heading1"], fontName=heading_bold, fontSize=23,
            leading=29, textColor=colors.black, spaceBefore=4, spaceAfter=8, keepWithNext=True,
        ),
        "atlas_subtitle": ParagraphStyle(
            "AtlasSubtitle", parent=base["BodyText"], fontName=heading, fontSize=12,
            leading=16, textColor=colors.HexColor("#333333"), spaceBefore=0, spaceAfter=10, keepWithNext=True,
        ),
        "atlas_group": ParagraphStyle(
            "AtlasGroup", fontName=heading_bold, fontSize=11.2,
            leading=14.5, textColor=colors.black, spaceBefore=4, spaceAfter=1, keepWithNext=True,
        ),
        "atlas_id": ParagraphStyle(
            "AtlasID", fontName=heading_bold, fontSize=9.5, leading=12.5,
            textColor=colors.black, keepWithNext=True,
        ),
        "atlas_bullet": ParagraphStyle(
            "AtlasBullet", fontName=mono, fontSize=9.0, leading=11.6,
            textColor=colors.HexColor("#222222"), leftIndent=8, firstLineIndent=-6, keepWithNext=True,
        ),
        "atlas_desc": ParagraphStyle(
            "AtlasDesc", parent=base["BodyText"], fontName=body, fontSize=9.6,
            leading=12.8, textColor=colors.HexColor("#1A1A1A"), spaceAfter=1.0, keepWithNext=True,
        ),
        "atlas_alert": ParagraphStyle(
            "AtlasAlert", parent=base["BodyText"], fontName=body, fontSize=9.0,
            leading=12.0, textColor=colors.HexColor("#333333"), leftIndent=6, spaceAfter=1.0, keepWithNext=True,
        ),
        "atlas_action": ParagraphStyle(
            "AtlasAction", parent=base["BodyText"], fontName=heading, fontSize=9.2,
            leading=12.2, textColor=colors.black, spaceAfter=1.5,
        ),
        "atlas_table": ParagraphStyle(
            "AtlasTable", parent=base["BodyText"], fontName=body, fontSize=9.2,
            leading=12.5, textColor=colors.black,
        ),
        "atlas_table_header": ParagraphStyle(
            "AtlasTableHeader", parent=base["BodyText"], fontName=heading_bold,
            fontSize=9.2, leading=12.5, textColor=colors.black,
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
        Paragraph("Được kiểm chứng với Go 1.27.1 - 22-09-2026", s["subtitle"]),
        Spacer(1, 4.8 * cm),
        Paragraph("Markdown là nguồn gốc. PDF là bản đọc được, có thể tái tạo cục bộ.", s["subtitle"]),
        PageBreak(),
    ])


def manuscript_titles(chapters: list[Path], appendices: list[Path]) -> list[str]:
    """Extract H1 titles for all manuscript parts in order."""
    result: list[str] = []
    for doc in chapters + appendices:
        first = doc.read_text(encoding="utf-8").splitlines()[0]
        if not first.startswith("# "):
            raise ValueError(f"Manuscript document does not start with H1: {doc}")
        result.append(first[2:].strip())
    return result


def chapter_titles() -> list[str]:
    """Compatibility wrapper returning all manuscript titles."""
    chaps, apps = get_manuscript()
    return manuscript_titles(chaps, apps)


def chapter_pages(reader: PdfReader, titles: list[str]) -> dict[str, int]:
    """Find chapter and appendix opening pages from the first pass, without hard-coding them."""
    pages: dict[str, int] = {}
    first_norm = " ".join(titles[0].split())
    # Locate the actual start of the manuscript (first chapter heading on a page that is not TOC)
    manuscript_start_idx = 2
    for idx, page in enumerate(reader.pages[2:], start=2):
        text = " ".join((page.extract_text() or "").split())
        if first_norm in text and "Mục lục của edition này" not in text:
            manuscript_start_idx = idx
            break

    for page_number, page in enumerate(reader.pages[manuscript_start_idx:], start=manuscript_start_idx + 1):
        text = " ".join((page.extract_text() or "").split())
        for title in titles:
            if title not in pages and " ".join(title.split()) in text:
                pages[title] = page_number
    missing = [title for title in titles if title not in pages]
    if missing:
        raise RuntimeError(f"Không xác định được trang mở đầu: {missing}")
    return pages


def add_outline(candidate: Path, titles: list[str]) -> PdfReader:
    """Add reader navigation after pagination has settled."""
    reader = PdfReader(str(candidate))
    pages = chapter_pages(reader, titles)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.add_outline_item("Mục lục", 1)
    for title in titles:
        writer.add_outline_item(title, pages[title] - 1)
    outlined = candidate.with_name("Golang_Master.outlined.pdf")
    with outlined.open("wb") as stream:
        writer.write(stream)
    outlined.replace(candidate)
    return PdfReader(str(candidate))


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


def footer_2col(canvas, doc) -> None:
    footer(canvas, doc)
    # Subtle hairline column divider between column 1 and column 2
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D8D8D8"))
    canvas.setLineWidth(0.4)
    gx = 2.1 * cm + 8.0 * cm + 0.4 * cm
    canvas.line(gx, 1.8 * cm, gx, A4[1] - 1.9 * cm)
    canvas.restoreState()


def add_error_atlas(story: list, atlas: Path, s: dict[str, ParagraphStyle], mono: str) -> None:
    """Render the Living Error Atlas (Grayscale-first, 2-column layout)."""
    story.append(PageBreak())
    lines = atlas.read_text(encoding="utf-8").splitlines()

    intro_lines: list[str] = []
    entry_lines: list[str] = []
    in_entries = False

    for line in lines:
        if line.startswith("## A — "):
            in_entries = True
        if in_entries:
            entry_lines.append(line)
        else:
            intro_lines.append(line)

    # 1. Front page of Atlas (1 column)
    table_lines: list[str] = []
    for line in intro_lines:
        ls = line.strip()
        if ls.startswith("# PHỤ LỤC A"):
            story.append(Paragraph(inline("PHỤ LỤC A — ATLAS LỖI GO", mono), s["atlas_h1"]))
            continue
        if ls.startswith("## Đọc lỗi"):
            story.append(Paragraph(inline("Đọc lỗi từ triệu chứng đến nguyên nhân", mono), s["atlas_subtitle"]))
            continue
        if ls.startswith("### "):
            story.append(Paragraph(inline(f"**{ls[4:]}**", mono), s["atlas_subtitle"]))
            continue
        if ls.startswith("|"):
            table_lines.append(line)
            continue
        if table_lines:
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table_lines]
            data = []
            for r_idx, r in enumerate([rows[0], *rows[2:]]):
                st = s["atlas_table_header"] if r_idx == 0 else s["atlas_table"]
                data.append([Paragraph(inline(c, mono), st) for c in r])
            if "Phạm vi" in rows[0][2]:
                col_widths = [1.4 * cm, 4.6 * cm, 8.8 * cm, 2.0 * cm]
            else:
                col_widths = [6.3 * cm, 2.1 * cm, 6.3 * cm, 2.1 * cm]
            t = Table(data, colWidths=col_widths, hAlign="LEFT")
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAE7")),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#777777")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ]))
            story.extend([Spacer(1, 2), t, Spacer(1, 6)])
            table_lines = []

        if ls.startswith("---"):
            story.extend([Spacer(1, 2), HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#999999")), Spacer(1, 4)])
            continue
        if ls:
            story.append(Paragraph(inline(ls, mono), s["body"]))

    if table_lines:
        rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table_lines]
        data = []
        for r_idx, r in enumerate([rows[0], *rows[2:]]):
            st = s["atlas_table_header"] if r_idx == 0 else s["atlas_table"]
            data.append([Paragraph(inline(c, mono), st) for c in r])
        if "Phạm vi" in rows[0][2]:
            col_widths = [1.4 * cm, 4.6 * cm, 8.8 * cm, 2.0 * cm]
        else:
            col_widths = [6.3 * cm, 2.1 * cm, 6.3 * cm, 2.1 * cm]
        t = Table(data, colWidths=col_widths, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAE7")),
            ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#777777")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        story.extend([Spacer(1, 2), t, Spacer(1, 6)])
        table_lines = []

    # Switch to 2 columns for Error Entries
    story.append(NextPageTemplate("atlas_2col"))
    story.append(PageBreak())

    # 2. Error entries (2 columns)
    current_entry: list = []
    for line in entry_lines:
        ls = line.strip()
        if ls.startswith("## "):
            if current_entry:
                story.append(KeepTogether(current_entry))
                current_entry = []
            g_title = ls[3:].upper()
            story.append(KeepTogether([
                Spacer(1, 4),
                Paragraph(f"<b>{g_title}</b>", s["atlas_group"]),
                HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#333333")),
                Spacer(1, 2),
            ]))
            continue

        if ls.startswith("### "):
            if current_entry:
                story.append(KeepTogether(current_entry))
                current_entry = []
            m = re.match(r"^###\s+([A-J]\d{2})\s+(.+)$", ls)
            if m:
                eid, raw_title = m.group(1), m.group(2).strip()
                if raw_title.startswith("`") and raw_title.endswith("`"):
                    clean_title = raw_title.strip("`")
                    p = Paragraph(f"<b>{eid}</b>&nbsp;&nbsp;<font name=\"{mono}\" color=\"#111111\"><b>{html.escape(clean_title)}</b></font>", s["atlas_id"])
                else:
                    p = Paragraph(f"<b>{eid}</b>&nbsp;&nbsp;<font color=\"#111111\"><b>{html.escape(raw_title)}</b></font>", s["atlas_id"])
                current_entry.extend([p, Spacer(1, 1)])
            continue

        if ls.startswith(("* ", "- ")):
            bullet_raw = ls[2:].strip()
            if bullet_raw.startswith("`") and bullet_raw.endswith("`"):
                bullet_txt = bullet_raw.strip("`")
                current_entry.append(Paragraph(f"• <font name=\"{mono}\">{html.escape(bullet_txt)}</font>", s["atlas_bullet"]))
            else:
                current_entry.append(Paragraph(f"• {inline(bullet_raw, mono)}", s["atlas_bullet"]))
            continue

        if ls.startswith("!"):
            alert_txt = ls[1:].strip()
            current_entry.append(Paragraph(f"<font color=\"#444444\"><b>!</b> <i>{inline(alert_txt, mono)}</i></font>", s["atlas_alert"]))
            continue

        if ls.startswith("→"):
            m_ref = re.search(r"\[?(Ch\d+(?:,\s*\d+)*)\]?\s*$", ls)
            if m_ref:
                action_txt = ls[:m_ref.start()].strip()
                ref_txt = m_ref.group(1)
                full_html = f"{inline(action_txt, mono)}&nbsp;&nbsp;<font name=\"BookSansBold\" color=\"#444444\">{ref_txt}</font>"
            else:
                full_html = inline(ls, mono)
            current_entry.extend([
                Paragraph(full_html, s["atlas_action"]),
                Spacer(1, 1.2),
            ])
            continue

        if ls and not ls.startswith("---"):
            current_entry.append(Paragraph(inline(ls, mono), s["atlas_desc"]))

    if current_entry:
        story.append(KeepTogether(current_entry))


def build_document(story: list, body: str, body_bold: str, heading: str,
                   heading_bold: str, mono: str, toc_pages: dict[str, int] | None) -> None:
    s = styles(body, body_bold, heading, heading_bold, mono)
    margin = 2.1 * cm
    printable_w = A4[0] - 4.2 * cm
    frame_book = Frame(margin, 2.0 * cm, printable_w, A4[1] - 3.9 * cm,
                       id="book", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    gutter = 0.8 * cm
    col_w = (printable_w - gutter) / 2
    frame_col1 = Frame(margin, 1.85 * cm, col_w, A4[1] - 3.65 * cm,
                       id="atlas_col1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_col2 = Frame(margin + col_w + gutter, 1.85 * cm, col_w, A4[1] - 3.65 * cm,
                       id="atlas_col2", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    doc = BaseDocTemplate(str(CANDIDATE), pagesize=A4, title="Golang Master",
                          author="Golang Living Textbook", leftMargin=margin,
                          rightMargin=margin, topMargin=2.0 * cm, bottomMargin=2.0 * cm)
    doc.addPageTemplates([
        PageTemplate(id="book", frames=[frame_book], onPage=footer),
        PageTemplate(id="atlas_2col", frames=[frame_col1, frame_col2], onPage=footer_2col),
    ])
    cover(story, s)
    story.append(Paragraph("Mục lục của edition này", s["h1"]))
    story.append(Paragraph(
        "Đây là edition nền móng. Mục lục tổng thể và thứ tự các phần tiếp theo "
        "được giữ trong `book/README.md` để có thể mở rộng mà không giả vờ rằng "
        "chúng đã được viết xong.", s["body"]))
    chapters, appendices = get_manuscript()
    titles = manuscript_titles(chapters, appendices)
    for title in titles:
        suffix = f" — trang {toc_pages[title]}" if toc_pages else ""
        story.append(Paragraph(inline(title + suffix, mono), s["toc"], bulletText="•"))
    story.append(PageBreak())
    numbering = {"figure": 0, "table": 0}
    for index, chapter in enumerate(chapters):
        add_markdown(story, chapter, s, mono, page_break_before=index > 0, numbering=numbering)
    for appendix in appendices:
        if appendix.name == "error-atlas.md":
            add_error_atlas(story, appendix, s, mono)
        else:
            add_markdown(story, appendix, s, mono, page_break_before=True, numbering=numbering)
    doc.build(story)


def build() -> None:
    chapters, appendices = get_manuscript()
    for doc_path in chapters + appendices:
        if not doc_path.exists():
            raise FileNotFoundError(f"Thiếu tài liệu bản thảo: {doc_path}")
    body, body_bold, heading, heading_bold, mono = register_fonts()
    TMP.mkdir(parents=True, exist_ok=True)
    titles = manuscript_titles(chapters, appendices)
    build_document([], body, body_bold, heading, heading_bold, mono, toc_pages=None)
    toc_pages = chapter_pages(PdfReader(str(CANDIDATE)), titles)
    build_document([], body, body_bold, heading, heading_bold, mono, toc_pages=toc_pages)
    reader = add_outline(CANDIDATE, titles)
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    if (len(reader.pages) < 6 or "GOLANG" not in extracted or "Chương 1" not in extracted
            or "ATLAS LỖI GO" not in extracted):
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
