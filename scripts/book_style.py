# -*- coding: utf-8 -*-
"""Centralized Print-Ready Design System for Golang Living Textbook.

Defines page geometry, mirrored margins (facing pages), typography,
grayscale-first color palette, vector cover artwork, and standard layout contracts.
"""

from __future__ import annotations

from reportlab.graphics.shapes import Drawing, Line, Rect
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm

# ==============================================================================
# 1. PAGE GEOMETRY & MIRRORED MARGINS (FACING PAGES)
# ==============================================================================
# Page size: ISO A4 (210mm x 297mm)
PAGE_SIZE = A4
PAGE_WIDTH = 21.0 * cm   # 595.28 pt
PAGE_HEIGHT = 29.7 * cm  # 841.89 pt

# Mirrored Margins (Industry standard for ~300 pages book binding):
# Gutter / Inside margin: 2.4 cm (facing the spine)
# Outside margin: 1.8 cm
# Top margin: 2.0 cm
# Bottom margin: 2.0 cm
MARGIN_INSIDE = 2.4 * cm   # 68.03 pt
MARGIN_OUTSIDE = 1.8 * cm  # 51.02 pt
MARGIN_TOP = 2.0 * cm      # 56.69 pt
MARGIN_BOTTOM = 2.0 * cm   # 56.69 pt

# Consistent printable text block (Preserves 16.8 cm width for all elements)
PRINTABLE_WIDTH = PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE  # 16.8 cm (476.22 pt)
PRINTABLE_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM     # 25.7 cm (728.51 pt)

# Error Atlas 2-Column Geometry
ATLAS_GUTTER = 0.8 * cm    # 22.68 pt
ATLAS_COL_WIDTH = (PRINTABLE_WIDTH - ATLAS_GUTTER) / 2  # 8.0 cm (226.77 pt)

# ==============================================================================
# 2. GRAYSCALE-FIRST COLOR PALETTE (PRINT-SAFE & REPRODUCIBLE)
# ==============================================================================
COLOR_BLACK = colors.HexColor("#000000")          # 100% black text
COLOR_TEXT_PRIMARY = colors.HexColor("#111111")
COLOR_TEXT_SECONDARY = colors.HexColor("#2E2E2E")
COLOR_TEXT_MUTED = colors.HexColor("#555555")

COLOR_BORDER_STRONG = colors.HexColor("#222222")
COLOR_BORDER_MEDIUM = colors.HexColor("#666666")
COLOR_BORDER_LIGHT = colors.HexColor("#888888")
COLOR_BORDER_HAIRLINE = colors.HexColor("#CCCCCC")
COLOR_BORDER_SUBTLE = colors.HexColor("#E2E2E2")

COLOR_BG_LIGHT = colors.HexColor("#F4F4F2")      # Code box background
COLOR_BG_HEADER = colors.HexColor("#EAEAE6")     # Table header background
COLOR_BG_CALLOUT = colors.HexColor("#F6F6F4")    # Blockquote background
COLOR_WHITE = colors.HexColor("#FFFFFF")

# ==============================================================================
# 3. LINE WEIGHTS (POINTS)
# ==============================================================================
LINE_WEIGHT_RULE = 1.0
LINE_WEIGHT_BORDER = 0.65
LINE_WEIGHT_TABLE_GRID = 0.45
LINE_WEIGHT_HAIRLINE = 0.35

# ==============================================================================
# 4. FONT DESIGNATORS
# ==============================================================================
FONT_SERIF = "BookSerif"
FONT_SERIF_BOLD = "BookSerifBold"
FONT_SANS = "BookSans"
FONT_SANS_BOLD = "BookSansBold"
FONT_MONO = "BookMono"

# ==============================================================================
# 5. TYPOGRAPHY HIERARCHY & PARAGRAPH STYLES
# ==============================================================================
def get_book_styles() -> dict[str, ParagraphStyle]:
    """Return the complete, unified dictionary of typography styles."""
    base = getSampleStyleSheet()
    return {
        # Front Matter & Cover
        "title": ParagraphStyle(
            "BookTitle", parent=base["Title"], fontName=FONT_SANS_BOLD, fontSize=36,
            leading=42, alignment=TA_CENTER, textColor=COLOR_BLACK, spaceAfter=14,
        ),
        "subtitle": ParagraphStyle(
            "BookSubtitle", parent=base["BodyText"], fontName=FONT_SANS, fontSize=13.0,
            leading=18.5, alignment=TA_CENTER, textColor=COLOR_TEXT_SECONDARY, spaceAfter=0,
        ),
        "author": ParagraphStyle(
            "BookAuthor", parent=base["BodyText"], fontName=FONT_SANS_BOLD, fontSize=12.0,
            leading=16.0, alignment=TA_CENTER, textColor=COLOR_TEXT_PRIMARY,
        ),

        # Headings
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName=FONT_SANS_BOLD, fontSize=22,
            leading=28, textColor=COLOR_BLACK, spaceBefore=6, spaceAfter=14,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName=FONT_SANS_BOLD, fontSize=16,
            leading=21, textColor=COLOR_BLACK, spaceBefore=16, spaceAfter=8,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontName=FONT_SANS_BOLD, fontSize=13.5,
            leading=18, textColor=COLOR_BLACK, spaceBefore=12, spaceAfter=6,
            keepWithNext=True,
        ),

        # Body & Lists
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=13.5,
            leading=20.5, alignment=TA_LEFT, textColor=COLOR_BLACK, spaceAfter=8.5,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=13.5,
            leading=20.5, textColor=COLOR_BLACK, leftIndent=16, firstLineIndent=-10,
            spaceAfter=4, bulletFontName=FONT_SERIF,
        ),

        # Code & Containers
        "code": ParagraphStyle(
            "Code", fontName=FONT_MONO, fontSize=11.5, leading=15.5,
            textColor=COLOR_BLACK, spaceBefore=0, spaceAfter=0,
        ),
        "table": ParagraphStyle(
            "Table", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=10.5,
            leading=14.2, textColor=COLOR_BLACK,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", parent=base["BodyText"], fontName=FONT_SERIF_BOLD,
            fontSize=10.5, leading=14.2, textColor=COLOR_BLACK,
        ),
        "caption": ParagraphStyle(
            "Caption", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=10.0,
            leading=13.5, textColor=COLOR_TEXT_SECONDARY, spaceAfter=8,
        ),
        "reference": ParagraphStyle(
            "Reference", parent=base["BodyText"], fontName=FONT_SANS, fontSize=9.5,
            leading=12.8, textColor=COLOR_TEXT_MUTED, leftIndent=14,
            firstLineIndent=-12, spaceAfter=4,
        ),

        # Table of Contents
        "toc_h1": ParagraphStyle(
            "TOCH1", parent=base["Heading1"], fontName=FONT_SANS_BOLD, fontSize=22,
            leading=28, spaceBefore=0, spaceAfter=14, textColor=COLOR_BLACK,
        ),
        "toc_entry": ParagraphStyle(
            "TOCEntry", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=10.5,
            leading=14.5, textColor=COLOR_TEXT_PRIMARY,
        ),
        "toc_entry_bold": ParagraphStyle(
            "TOCEntryBold", parent=base["BodyText"], fontName=FONT_SANS_BOLD, fontSize=10.5,
            leading=14.5, textColor=COLOR_BLACK,
        ),
        "toc_page": ParagraphStyle(
            "TOCPage", parent=base["BodyText"], fontName=FONT_SANS_BOLD, fontSize=10.5,
            leading=14.5, alignment=TA_RIGHT, textColor=COLOR_TEXT_PRIMARY,
        ),

        # Error Atlas 2-column styles
        "atlas_h1": ParagraphStyle(
            "AtlasH1", parent=base["Heading1"], fontName=FONT_SANS_BOLD, fontSize=22,
            leading=28, textColor=COLOR_BLACK, spaceBefore=4, spaceAfter=8, keepWithNext=True,
        ),
        "atlas_subtitle": ParagraphStyle(
            "AtlasSubtitle", parent=base["BodyText"], fontName=FONT_SANS, fontSize=12,
            leading=16, textColor=COLOR_TEXT_SECONDARY, spaceBefore=0, spaceAfter=10, keepWithNext=True,
        ),
        "atlas_group": ParagraphStyle(
            "AtlasGroup", fontName=FONT_SANS_BOLD, fontSize=11.2,
            leading=14.5, textColor=COLOR_BLACK, spaceBefore=4, spaceAfter=1, keepWithNext=True,
        ),
        "atlas_id": ParagraphStyle(
            "AtlasID", fontName=FONT_SANS_BOLD, fontSize=9.5, leading=12.5,
            textColor=COLOR_BLACK, keepWithNext=True,
        ),
        "atlas_bullet": ParagraphStyle(
            "AtlasBullet", fontName=FONT_MONO, fontSize=9.0, leading=11.6,
            textColor=COLOR_TEXT_PRIMARY, leftIndent=8, firstLineIndent=-6, keepWithNext=True,
        ),
        "atlas_desc": ParagraphStyle(
            "AtlasDesc", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=9.6,
            leading=12.8, textColor=COLOR_TEXT_PRIMARY, spaceAfter=1.0, keepWithNext=True,
        ),
        "atlas_alert": ParagraphStyle(
            "AtlasAlert", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=9.0,
            leading=12.0, textColor=COLOR_TEXT_MUTED, leftIndent=6, spaceAfter=1.0, keepWithNext=True,
        ),
        "atlas_action": ParagraphStyle(
            "AtlasAction", parent=base["BodyText"], fontName=FONT_SANS, fontSize=9.2,
            leading=12.2, textColor=COLOR_BLACK, spaceAfter=1.5,
        ),
        "atlas_table": ParagraphStyle(
            "AtlasTable", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=9.2,
            leading=12.5, textColor=COLOR_BLACK,
        ),
        "atlas_table_header": ParagraphStyle(
            "AtlasTableHeader", parent=base["BodyText"], fontName=FONT_SANS_BOLD,
            fontSize=9.2, leading=12.5, textColor=COLOR_BLACK,
        ),
    }

# ==============================================================================
# 6. VECTOR COVER ARTWORK (MODULAR RECTANGULAR GRID)
# ==============================================================================
def build_cover_artwork(w: float = 400, h: float = 270) -> Drawing:
    """Create minimalist geometric vector artwork inspired by modular shelving.
    Uses pure ReportLab vector primitives (Rect, Line), grayscale tones,
    and structured negative space. No raster images.
    """
    d = Drawing(w, h)

    grid_w = 360
    grid_h = 240
    ox = (w - grid_w) / 2
    oy = (h - grid_h) / 2

    c_w = [95, 125, 80, 60]  # total 360
    r_h = [55, 75, 65, 45]   # total 240

    xs = [ox]
    for cw in c_w:
        xs.append(xs[-1] + cw)
    ys = [oy]
    for rh in r_h:
        ys.append(ys[-1] + rh)

    modules = [
        # Col 0: Open base module + soft gray mid + open top
        (0, 0, 1, 2, colors.HexColor("#FFFFFF"), COLOR_BORDER_STRONG, 0.7),
        (0, 2, 1, 1, colors.HexColor("#F5F5F3"), COLOR_BORDER_STRONG, 0.7),
        (0, 3, 1, 1, colors.HexColor("#FFFFFF"), COLOR_BORDER_STRONG, 0.7),

        # Col 1: Center focus modules
        (1, 0, 1, 1, colors.HexColor("#EAEAE6"), COLOR_BORDER_STRONG, 0.7),
        (1, 1, 1, 1, colors.HexColor("#FFFFFF"), COLOR_BORDER_STRONG, 0.7),
        (1, 2, 1, 2, colors.HexColor("#FFFFFF"), COLOR_BORDER_STRONG, 0.7),

        # Col 2: Narrow accents with solid focal block
        (2, 0, 1, 1, colors.HexColor("#FFFFFF"), COLOR_BORDER_STRONG, 0.7),
        (2, 1, 1, 1, colors.HexColor("#242424"), COLOR_BORDER_STRONG, 0.7),  # Dark focal accent
        (2, 2, 1, 1, colors.HexColor("#FFFFFF"), COLOR_BORDER_STRONG, 0.7),
        (2, 3, 1, 1, colors.HexColor("#EEEEEC"), COLOR_BORDER_STRONG, 0.7),

        # Col 3: Right edge modules
        (3, 0, 1, 2, colors.HexColor("#F8F8F7"), COLOR_BORDER_STRONG, 0.7),
        (3, 2, 1, 2, colors.HexColor("#FFFFFF"), COLOR_BORDER_STRONG, 0.7),
    ]

    for c_idx, r_idx, c_span, r_span, fill, stroke, sw in modules:
        mx = xs[c_idx]
        my = ys[r_idx]
        mw = xs[c_idx + c_span] - mx
        mh = ys[r_idx + r_span] - my
        d.add(Rect(mx, my, mw, mh, fillColor=fill, strokeColor=stroke, strokeWidth=sw))

    # Architectural uprights: thin lines extending 8pt above and below the grid
    for x in xs:
        d.add(Line(x, oy - 8, x, oy + grid_h + 8, strokeColor=COLOR_BORDER_MEDIUM, strokeWidth=0.5))

    # Internal shelf accents (subtle dividers)
    d.add(Line(xs[0] + 12, ys[1], xs[1] - 12, ys[1], strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.4))
    d.add(Line(xs[1] + 40, ys[2] + 8, xs[1] + 40, ys[4] - 8, strokeColor=COLOR_BORDER_LIGHT, strokeWidth=0.4))
    d.add(Rect(xs[3] + 8, ys[0] + 8, c_w[3] - 16, r_h[0] + r_h[1] - 16, fillColor=None, strokeColor=COLOR_BORDER_HAIRLINE, strokeWidth=0.4))

    return d

# ==============================================================================
# 7. FOOTERS & FOLIOS (FACING PAGES / MIRRORED SYSTEM)
# ==============================================================================
def footer_recto(canvas, doc) -> None:
    """Odd page footer (Recto / right-hand page):
    Inside margin is on the LEFT; Outside margin is on the RIGHT.
    Page number is placed at outer bottom right.
    """
    canvas.saveState()
    canvas.setStrokeColor(COLOR_BORDER_HAIRLINE)
    canvas.setLineWidth(LINE_WEIGHT_HAIRLINE)
    canvas.line(MARGIN_INSIDE, 1.55 * cm, PAGE_WIDTH - MARGIN_OUTSIDE, 1.55 * cm)
    canvas.setFont(FONT_SANS, 9.5)
    canvas.setFillColor(COLOR_TEXT_SECONDARY)
    canvas.drawRightString(PAGE_WIDTH - MARGIN_OUTSIDE, 1.15 * cm, str(doc.page))
    canvas.restoreState()


def footer_verso(canvas, doc) -> None:
    """Even page footer (Verso / left-hand page):
    Inside margin is on the RIGHT; Outside margin is on the LEFT.
    Page number is placed at outer bottom left.
    """
    canvas.saveState()
    canvas.setStrokeColor(COLOR_BORDER_HAIRLINE)
    canvas.setLineWidth(LINE_WEIGHT_HAIRLINE)
    canvas.line(MARGIN_OUTSIDE, 1.55 * cm, PAGE_WIDTH - MARGIN_INSIDE, 1.55 * cm)
    canvas.setFont(FONT_SANS, 9.5)
    canvas.setFillColor(COLOR_TEXT_SECONDARY)
    canvas.drawString(MARGIN_OUTSIDE, 1.15 * cm, str(doc.page))
    canvas.restoreState()


def footer_atlas_recto(canvas, doc) -> None:
    """Odd page footer for Error Atlas (2-column recto)."""
    footer_recto(canvas, doc)
    canvas.saveState()
    canvas.setStrokeColor(COLOR_BORDER_HAIRLINE)
    canvas.setLineWidth(LINE_WEIGHT_HAIRLINE)
    gx = MARGIN_INSIDE + ATLAS_COL_WIDTH + (ATLAS_GUTTER / 2)
    canvas.line(gx, 1.85 * cm, gx, PAGE_HEIGHT - 1.95 * cm)
    canvas.restoreState()


def footer_atlas_verso(canvas, doc) -> None:
    """Even page footer for Error Atlas (2-column verso)."""
    footer_verso(canvas, doc)
    canvas.saveState()
    canvas.setStrokeColor(COLOR_BORDER_HAIRLINE)
    canvas.setLineWidth(LINE_WEIGHT_HAIRLINE)
    gx = MARGIN_OUTSIDE + ATLAS_COL_WIDTH + (ATLAS_GUTTER / 2)
    canvas.line(gx, 1.85 * cm, gx, PAGE_HEIGHT - 1.95 * cm)
    canvas.restoreState()


def cover_canvas(canvas, doc) -> None:
    """Empty callback for title page: NO header, NO footer, NO page number."""
    pass


# ==============================================================================
# 8. MIRRORED DOC TEMPLATE (DYNAMIC RECTO / VERSO SELECTION)
# ==============================================================================
from reportlab.platypus import BaseDocTemplate


class MirroredDocTemplate(BaseDocTemplate):
    """Subclass of BaseDocTemplate that automatically selects the appropriate
    recto (odd) or verso (even) template based on the upcoming page parity.
    """
    def _setPageTemplate(self):
        super()._setPageTemplate()
        cur_id = self.pageTemplate.id
        next_page = self.page + 1
        target_id = None
        if cur_id in ("book_recto", "book_verso"):
            target_id = "book_verso" if next_page % 2 == 0 else "book_recto"
        elif cur_id in ("atlas_recto", "atlas_verso"):
            target_id = "atlas_verso" if next_page % 2 == 0 else "atlas_recto"

        if target_id and target_id != cur_id:
            for t in self.pageTemplates:
                if t.id == target_id:
                    self.pageTemplate = t
                    break
