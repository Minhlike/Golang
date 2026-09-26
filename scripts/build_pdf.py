"""Render the current Markdown edition into a checked, replace-safe print-ready PDF.

This is a local publishing renderer, supporting the book constructs
(headings, paragraphs, lists, code, horizontal rules, local diagrams,
tables, mirrored margins, and the living Error Atlas).
"""

from __future__ import annotations

import html
from pathlib import Path
import re
import shutil
import sys

# Ensure scripts directory is in path for book_style
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
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
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.frames import Frame

from book_style import (
    ATLAS_COL_WIDTH,
    ATLAS_GUTTER,
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
    FONT_MONO,
    FONT_SANS,
    FONT_SANS_BOLD,
    FONT_SERIF,
    FONT_SERIF_BOLD,
    LINE_WEIGHT_ACCENT,
    LINE_WEIGHT_BORDER,
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
    MirroredDocTemplate,
    build_cover_artwork,
    cover_canvas,
    footer_atlas_recto,
    footer_atlas_verso,
    footer_recto,
    footer_verso,
    get_book_styles,
)

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
    """Return centralized styles from book_style module."""
    return get_book_styles()


def cover(story: list, s: dict[str, ParagraphStyle]) -> None:
    """Generate the official title page with geometric vector modular grid artwork.
    Completely eliminates build metadata, fake publishing fields, and project slogans.
    """
    story.extend([
        Spacer(1, 2.2 * cm),
        Paragraph("GOLANG", s["title"]),
        Spacer(1, 0.4 * cm),
        Paragraph(
            "Giáo trình cập nhật liên tục về Kỹ nghệ phần mềm và DevOps/SRE",
            s["subtitle"],
        ),
        Spacer(1, 1.8 * cm),
        build_cover_artwork(w=PRINTABLE_WIDTH, h=260),
        Spacer(1, 2.6 * cm),
        Paragraph("Đoàn Ngọc Hoàng Minh", s["author"]),
        NextPageTemplate("book_verso"),
        PageBreak(),
    ])


def manuscript_titles(chapters: list[Path], appendices: list[Path]) -> list[str]:
    """Extract H1 titles for all manuscript parts in order."""
    result: list[str] = []
    for doc in chapters + appendices:
        lines = [line.strip() for line in doc.read_text(encoding="utf-8").splitlines() if line.strip() and not (line.strip().startswith("<!--") and line.strip().endswith("-->"))]
        if not lines or not lines[0].startswith("# "):
            raise ValueError(f"Manuscript document does not start with H1: {doc}")
        result.append(lines[0][2:].strip())
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
        if first_norm in text and "MỤC LỤC" not in text:
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
    """Add reader navigation and publication metadata after pagination has settled."""
    reader = PdfReader(str(candidate))
    pages = chapter_pages(reader, titles)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.add_metadata({
        "/Title": "GOLANG",
        "/Author": "Đoàn Ngọc Hoàng Minh",
        "/Subject": "Giáo trình cập nhật liên tục về Kỹ nghệ phần mềm và DevOps/SRE",
    })
    writer.add_outline_item("MỤC LỤC", 1)
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

        avail_width = PRINTABLE_WIDTH
        col_max_lens = [max(len(row[c]) for row in [rows[0], *rows[2:]]) for c in range(columns)]
        total_len = sum(col_max_lens) or 1
        if columns > 2 and total_len > 0:
            weights = [max(l, 4) for l in col_max_lens]
            sum_w = sum(weights)
            col_widths = [avail_width * (w / sum_w) for w in weights]
        else:
            col_widths = [avail_width / columns] * columns

        table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_HEADER),
            ("LINEBELOW", (0, 0), (-1, 0), LINE_WEIGHT_RULE, COLOR_BORDER_MEDIUM),
            ("LINEBELOW", (0, 1), (-1, -1), LINE_WEIGHT_TABLE_GRID, COLOR_BORDER_HAIRLINE),
            ("LINEABOVE", (0, 0), (-1, 0), 0.4, COLOR_BORDER_MEDIUM),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        flowables = []
        if table_caption:
            numbering["table"] += 1
            flowables.extend([
                Paragraph(f"Bảng {numbering['table']} — {inline(table_caption, mono)}",
                          s["caption"]),
                Spacer(1, 4),
            ])
        flowables.append(table)
        flowables.append(Spacer(1, 10))
        if len(rows) <= 6:
            story.append(KeepTogether(flowables))
        else:
            story.extend(flowables)
        table_lines = []
        table_caption = None

    def add_code_block() -> None:
        """Make tabs deterministic, keep code distinct, and split long blocks across pages."""
        nonlocal code_lines
        chunk_size = 28
        if len(code_lines) <= chunk_size:
            chunks = [code_lines]
        else:
            chunks = [code_lines[i : i + chunk_size] for i in range(0, len(code_lines), chunk_size)]

        for idx, chunk in enumerate(chunks):
            code = Preformatted("\n".join(chunk).expandtabs(4), s["code"])
            box = Table([[code]], colWidths=[PRINTABLE_WIDTH], hAlign="LEFT")
            box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), LINE_WEIGHT_BORDER, COLOR_BORDER_LIGHT),
                ("LINEBEFORE", (0, 0), (0, -1), LINE_WEIGHT_ACCENT, COLOR_BORDER_STRONG),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]))
            if len(chunks) == 1 and len(chunk) <= 22:
                story.append(KeepTogether([Spacer(1, 6), box, Spacer(1, 13)]))
            else:
                top_spacer = 6 if idx == 0 else 2
                bottom_spacer = 13 if idx == len(chunks) - 1 else 4
                story.extend([Spacer(1, top_spacer), box, Spacer(1, bottom_spacer)])
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
        if line.strip().startswith("<!--") and line.strip().endswith("-->"):
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
            drawing._restrictSize(PRINTABLE_WIDTH, 12.8 * cm)
            drawing.hAlign = "CENTER"
            pending_image = drawing
            continue
        quote = re.match(r"^>\s+(.+)$", line)
        if quote:
            flush_paragraph()
            note = Table([[Paragraph(inline(quote.group(1), mono), s["body"])]],
                         colWidths=[PRINTABLE_WIDTH], hAlign="LEFT")
            note.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_CALLOUT),
                ("LINEBEFORE", (0, 0), (0, -1), LINE_WEIGHT_ACCENT, COLOR_BORDER_MEDIUM),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.extend([Spacer(1, 5), note, Spacer(1, 12)])
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
            if level == 1:
                # Chapter opener: thin rule below title + generous whitespace
                story.append(HRFlowable(width="100%", thickness=LINE_WEIGHT_RULE,
                             color=COLOR_BORDER_STRONG, spaceAfter=14))
            continue
        if line.strip() == "---":
            flush_paragraph()
            story.extend([Spacer(1, 3), HRFlowable(width="100%", thickness=LINE_WEIGHT_BORDER,
                         color=COLOR_BORDER_LIGHT), Spacer(1, 5)])
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
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_HEADER),
                ("GRID", (0, 0), (-1, -1), LINE_WEIGHT_TABLE_GRID, COLOR_BORDER_MEDIUM),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ]))
            story.extend([Spacer(1, 2), t, Spacer(1, 6)])
            table_lines = []

        if ls.startswith("---"):
            story.extend([Spacer(1, 2), HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER_LIGHT), Spacer(1, 4)])
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
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_HEADER),
            ("GRID", (0, 0), (-1, -1), LINE_WEIGHT_TABLE_GRID, COLOR_BORDER_MEDIUM),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        story.extend([Spacer(1, 2), t, Spacer(1, 6)])
        table_lines = []

    # Switch to 2 columns for Error Entries (MirroredDocTemplate auto-selects recto/verso)
    story.append(NextPageTemplate("atlas_recto"))
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
                HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER_STRONG),
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

    # 1. Title/Cover page template (centered, no footer/page number)
    frame_cover = Frame(
        MARGIN_INSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="frame_cover", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    template_cover = PageTemplate(id="cover", frames=[frame_cover], onPage=cover_canvas)

    # 2. Mirrored 1-column body templates
    # Recto (Odd page): inside margin on LEFT (2.4cm), outside margin on RIGHT (1.8cm)
    frame_recto = Frame(
        MARGIN_INSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="frame_book_recto", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    template_recto = PageTemplate(id="book_recto", frames=[frame_recto], onPage=footer_recto)

    # Verso (Even page): inside margin on RIGHT (2.4cm), outside margin on LEFT (1.8cm)
    frame_verso = Frame(
        MARGIN_OUTSIDE, MARGIN_BOTTOM, PRINTABLE_WIDTH, PRINTABLE_HEIGHT,
        id="frame_book_verso", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    template_verso = PageTemplate(id="book_verso", frames=[frame_verso], onPage=footer_verso)

    # 3. Mirrored 2-column Error Atlas templates
    col1_recto = Frame(
        MARGIN_INSIDE, 1.85 * cm, ATLAS_COL_WIDTH, PAGE_HEIGHT - 3.65 * cm,
        id="atlas_col1_recto", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    col2_recto = Frame(
        MARGIN_INSIDE + ATLAS_COL_WIDTH + ATLAS_GUTTER, 1.85 * cm, ATLAS_COL_WIDTH, PAGE_HEIGHT - 3.65 * cm,
        id="atlas_col2_recto", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    template_atlas_recto = PageTemplate(id="atlas_recto", frames=[col1_recto, col2_recto], onPage=footer_atlas_recto)

    col1_verso = Frame(
        MARGIN_OUTSIDE, 1.85 * cm, ATLAS_COL_WIDTH, PAGE_HEIGHT - 3.65 * cm,
        id="atlas_col1_verso", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    col2_verso = Frame(
        MARGIN_OUTSIDE + ATLAS_COL_WIDTH + ATLAS_GUTTER, 1.85 * cm, ATLAS_COL_WIDTH, PAGE_HEIGHT - 3.65 * cm,
        id="atlas_col2_verso", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    template_atlas_verso = PageTemplate(id="atlas_verso", frames=[col1_verso, col2_verso], onPage=footer_atlas_verso)

    doc = MirroredDocTemplate(
        str(CANDIDATE),
        pagesize=PAGE_SIZE,
        title="GOLANG",
        author="Đoàn Ngọc Hoàng Minh",
        subject="Giáo trình cập nhật liên tục về Kỹ nghệ phần mềm và DevOps/SRE",
        leftMargin=MARGIN_INSIDE,
        rightMargin=MARGIN_OUTSIDE,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )
    doc.addPageTemplates([
        template_cover,
        template_recto,
        template_verso,
        template_atlas_recto,
        template_atlas_verso,
    ])

    # Build Front Matter
    cover(story, s)

    # Professional Table of Contents (MỤC LỤC)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("MỤC LỤC", s["toc_h1"]))
    story.append(Spacer(1, 0.4 * cm))

    chapters, appendices = get_manuscript()
    titles = manuscript_titles(chapters, appendices)

    toc_data = []
    for title in titles:
        is_major = "BACK MATTER" in title or "PHỤ LỤC" in title
        st = s["toc_entry_bold"] if is_major else s["toc_entry"]
        pg_str = str(toc_pages[title]) if toc_pages else ""
        toc_data.append([
            Paragraph(title, st),
            Paragraph(pg_str, s["toc_page"]),
        ])

    toc_table = Table(
        toc_data,
        colWidths=[PRINTABLE_WIDTH - 1.6 * cm, 1.6 * cm],
        hAlign="LEFT",
    )
    toc_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 0), (-1, -1), 0.35, COLOR_BORDER_SUBTLE),
    ]))
    story.append(toc_table)
    story.append(PageBreak())

    # Build Chapters and Appendices
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
    # Preflight: code line width validation
    import validate_code_width
    violations = validate_code_width.validate_all_code_blocks()
    if violations:
        raise RuntimeError(
            f"Preflight failed: {len(violations)} code line(s) overflow printable width box. "
            f"Run scripts/validate_code_width.py for details."
        )

    chapters, appendices = get_manuscript()
    for doc_path in chapters + appendices:
        if not doc_path.exists():
            raise FileNotFoundError(f"Thiếu tài liệu bản thảo: {doc_path}")
    body, body_bold, heading, heading_bold, mono = register_fonts()
    TMP.mkdir(parents=True, exist_ok=True)
    titles = manuscript_titles(chapters, appendices)

    # First pass: calculate page numbers
    build_document([], body, body_bold, heading, heading_bold, mono, toc_pages=None)
    toc_pages = chapter_pages(PdfReader(str(CANDIDATE)), titles)

    # Second pass: generate final document with populated TOC page numbers
    build_document([], body, body_bold, heading, heading_bold, mono, toc_pages=toc_pages)
    reader = add_outline(CANDIDATE, titles)
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)

    # Semantic assertions preventing regressions
    forbidden = [
        "Edition nền móng",
        "Được kiểm chứng với Go 1.27.1 - 22-09-2026",
        "Markdown là nguồn gốc. PDF là bản đọc được, có thể tái tạo cục bộ.",
        "Golang Living Textbook - Edition nền móng",
        "Chương đầu không có mục tiêu “biết hết Go”",
    ]
    required = [
        "GOLANG",
        "Giáo trình cập nhật liên tục về Kỹ nghệ phần mềm và DevOps/SRE",
        "Đoàn Ngọc Hoàng Minh",
        "MỤC LỤC",
        "ATLAS LỖI GO",
    ]
    for phrase in forbidden:
        if phrase in extracted:
            raise RuntimeError(f"Candidate PDF contains forbidden text: {phrase}")
    for phrase in required:
        if phrase not in extracted:
            raise RuntimeError(f"Candidate PDF missing required text: {phrase}")

    if len(reader.pages) < 200 or "Chương 1" not in extracted:
        raise RuntimeError("Candidate PDF failed structural page count validation.")

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
