# -*- coding: utf-8 -*-
"""Centralized Print-Ready Design System for Golang Living Textbook.

Defines page geometry, mirrored margins (facing pages), typography,
grayscale-first color palette, vector cover artwork, and standard layout contracts.
"""

from __future__ import annotations

from reportlab.graphics.shapes import Drawing, Line, Rect, Circle
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
# Top margin: 2.2 cm  (slightly more air at top)
# Bottom margin: 2.0 cm
MARGIN_INSIDE = 2.4 * cm   # 68.03 pt
MARGIN_OUTSIDE = 1.8 * cm  # 51.02 pt
MARGIN_TOP = 2.2 * cm      # 62.36 pt
MARGIN_BOTTOM = 2.0 * cm   # 56.69 pt

# Consistent printable text block
PRINTABLE_WIDTH = PAGE_WIDTH - MARGIN_INSIDE - MARGIN_OUTSIDE  # 16.8 cm (476.22 pt)
PRINTABLE_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM     # 25.5 cm (722.83 pt)

# Error Atlas 2-Column Geometry
ATLAS_GUTTER = 0.8 * cm    # 22.68 pt
ATLAS_COL_WIDTH = (PRINTABLE_WIDTH - ATLAS_GUTTER) / 2  # 8.0 cm (226.77 pt)

# ==============================================================================
# 2. GRAYSCALE-FIRST COLOR PALETTE (PRINT-SAFE & REPRODUCIBLE)
# ==============================================================================
# Primary ink stops — 6-level scale
COLOR_BLACK          = colors.HexColor("#000000")  # 100% black — headings, ruled lines
COLOR_TEXT_PRIMARY   = colors.HexColor("#1A1A1A")  # Near-black — body text
COLOR_TEXT_SECONDARY = colors.HexColor("#3A3A3A")  # Dark gray — captions, secondary
COLOR_TEXT_MUTED     = colors.HexColor("#606060")  # Medium gray — references, folios
COLOR_TEXT_LIGHT     = colors.HexColor("#888888")  # Light gray — decorative rules

# Border stops
COLOR_BORDER_STRONG   = colors.HexColor("#1A1A1A")  # Heavy rule lines
COLOR_BORDER_MEDIUM   = colors.HexColor("#555555")  # Table grid, dividers
COLOR_BORDER_LIGHT    = colors.HexColor("#888888")  # Hairline accents
COLOR_BORDER_HAIRLINE = colors.HexColor("#C8C8C8")  # Very light separators
COLOR_BORDER_SUBTLE   = colors.HexColor("#E0E0E0")  # TOC row underlines

# Background stops
COLOR_BG_LIGHT   = colors.HexColor("#F2F2F0")  # Code block background (cool off-white)
COLOR_BG_HEADER  = colors.HexColor("#E6E6E2")  # Table header background
COLOR_BG_CALLOUT = colors.HexColor("#F5F5F3")  # Blockquote background
COLOR_WHITE      = colors.HexColor("#FFFFFF")

# Cover accent fills
COLOR_COVER_DARK   = colors.HexColor("#1C1C1C")  # Dark focal block
COLOR_COVER_MID    = colors.HexColor("#E8E8E4")  # Medium fill
COLOR_COVER_LIGHT  = colors.HexColor("#F5F5F3")  # Light fill
COLOR_COVER_GHOST  = colors.HexColor("#FAFAFA")  # Near-white fill

# ==============================================================================
# 3. LINE WEIGHTS (POINTS)
# ==============================================================================
LINE_WEIGHT_RULE       = 1.2   # Chapter opener rule
LINE_WEIGHT_ACCENT     = 2.0   # Left accent bar (code, blockquote)
LINE_WEIGHT_BORDER     = 0.6   # Code box border
LINE_WEIGHT_TABLE_GRID = 0.4   # Table interior grid
LINE_WEIGHT_HAIRLINE   = 0.3   # Footer rule, decorative

# ==============================================================================
# 4. FONT DESIGNATORS
# ==============================================================================
FONT_SERIF      = "BookSerif"
FONT_SERIF_BOLD = "BookSerifBold"
FONT_SANS       = "BookSans"
FONT_SANS_BOLD  = "BookSansBold"
FONT_MONO       = "BookMono"

# ==============================================================================
# 5. TYPOGRAPHY HIERARCHY & PARAGRAPH STYLES
# ==============================================================================
def get_book_styles() -> dict[str, ParagraphStyle]:
    """Return the complete, unified dictionary of typography styles."""
    base = getSampleStyleSheet()
    return {
        # ── Front Matter & Cover ─────────────────────────────────────────────
        "title": ParagraphStyle(
            "BookTitle", parent=base["Title"], fontName=FONT_SANS_BOLD, fontSize=42,
            leading=48, alignment=TA_CENTER, textColor=COLOR_BLACK, spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "BookSubtitle", parent=base["BodyText"], fontName=FONT_SANS, fontSize=12.5,
            leading=18, alignment=TA_CENTER, textColor=COLOR_TEXT_SECONDARY, spaceAfter=0,
        ),
        "author": ParagraphStyle(
            "BookAuthor", parent=base["BodyText"], fontName=FONT_SANS, fontSize=11.5,
            leading=16.0, alignment=TA_CENTER, textColor=COLOR_TEXT_MUTED,
        ),

        # ── Headings ─────────────────────────────────────────────────────────
        # H1 — Chapter title: large, generous space, followed by rule in renderer
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName=FONT_SANS_BOLD, fontSize=24,
            leading=30, textColor=COLOR_BLACK, spaceBefore=4, spaceAfter=6,
            keepWithNext=True,
        ),
        # H2 — Section heading: clear visual break
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName=FONT_SANS_BOLD, fontSize=15.5,
            leading=21, textColor=COLOR_BLACK, spaceBefore=20, spaceAfter=7,
            keepWithNext=True,
        ),
        # H3 — Subsection: weight distinction only
        "h3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontName=FONT_SANS_BOLD, fontSize=13.0,
            leading=18, textColor=COLOR_TEXT_PRIMARY, spaceBefore=13, spaceAfter=5,
            keepWithNext=True,
        ),

        # ── Body & Lists ─────────────────────────────────────────────────────
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=13.5,
            leading=21.5, alignment=TA_LEFT, textColor=COLOR_TEXT_PRIMARY, spaceAfter=9,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=13.5,
            leading=21.5, textColor=COLOR_TEXT_PRIMARY, leftIndent=16, firstLineIndent=-10,
            spaceAfter=4, bulletFontName=FONT_SERIF,
        ),

        # ── Code & Containers ────────────────────────────────────────────────
        "code": ParagraphStyle(
            "Code", fontName=FONT_MONO, fontSize=11.0, leading=15.0,
            textColor=COLOR_TEXT_PRIMARY, spaceBefore=0, spaceAfter=0,
        ),
        "table": ParagraphStyle(
            "Table", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=10.5,
            leading=14.5, textColor=COLOR_TEXT_PRIMARY,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", parent=base["BodyText"], fontName=FONT_SANS_BOLD,
            fontSize=10.5, leading=14.5, textColor=COLOR_BLACK,
        ),
        "caption": ParagraphStyle(
            "Caption", parent=base["BodyText"], fontName=FONT_SANS, fontSize=9.8,
            leading=13.5, textColor=COLOR_TEXT_SECONDARY, spaceAfter=6,
        ),
        "reference": ParagraphStyle(
            "Reference", parent=base["BodyText"], fontName=FONT_SANS, fontSize=9.5,
            leading=13.0, textColor=COLOR_TEXT_MUTED, leftIndent=14,
            firstLineIndent=-12, spaceAfter=4, bulletFontName=FONT_SANS,
        ),

        # ── Table of Contents ─────────────────────────────────────────────────
        "toc_h1": ParagraphStyle(
            "TOCH1", parent=base["Heading1"], fontName=FONT_SANS_BOLD, fontSize=22,
            leading=28, spaceBefore=0, spaceAfter=14, textColor=COLOR_BLACK,
        ),
        "toc_entry": ParagraphStyle(
            "TOCEntry", parent=base["BodyText"], fontName=FONT_SERIF, fontSize=10.5,
            leading=15.0, textColor=COLOR_TEXT_PRIMARY,
        ),
        "toc_entry_bold": ParagraphStyle(
            "TOCEntryBold", parent=base["BodyText"], fontName=FONT_SANS_BOLD, fontSize=10.5,
            leading=15.0, textColor=COLOR_BLACK,
        ),
        "toc_page": ParagraphStyle(
            "TOCPage", parent=base["BodyText"], fontName=FONT_SANS, fontSize=10.5,
            leading=15.0, alignment=TA_RIGHT, textColor=COLOR_TEXT_MUTED,
        ),

        # ── Error Atlas 2-column styles ───────────────────────────────────────
        "atlas_h1": ParagraphStyle(
            "AtlasH1", parent=base["Heading1"], fontName=FONT_SANS_BOLD, fontSize=22,
            leading=28, textColor=COLOR_BLACK, spaceBefore=4, spaceAfter=8, keepWithNext=True,
        ),
        "atlas_subtitle": ParagraphStyle(
            "AtlasSubtitle", parent=base["BodyText"], fontName=FONT_SANS, fontSize=12,
            leading=16, textColor=COLOR_TEXT_SECONDARY, spaceBefore=0, spaceAfter=10, keepWithNext=True,
        ),
        "atlas_group": ParagraphStyle(
            "AtlasGroup", fontName=FONT_SANS_BOLD, fontSize=11.0,
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
            leading=12.5, textColor=COLOR_TEXT_PRIMARY,
        ),
        "atlas_table_header": ParagraphStyle(
            "AtlasTableHeader", parent=base["BodyText"], fontName=FONT_SANS_BOLD,
            fontSize=9.2, leading=12.5, textColor=COLOR_BLACK,
        ),
    }

# ==============================================================================
# 6. VECTOR COVER ARTWORK — Editorial Geometric Composition
# ==============================================================================
def build_cover_artwork(w: float = 400, h: float = 270) -> Drawing:
    """Create editorial geometric vector artwork for the cover.

    A refined asymmetric grid with a strong vertical dark column as focal anchor,
    balanced by lighter fields and ruled horizontal bands. No raster images.
    """
    d = Drawing(w, h)

    # Outer border — clean frame
    d.add(Rect(0, 0, w, h, fillColor=COLOR_COVER_GHOST, strokeColor=None, strokeWidth=0))

    # Grid definition — asymmetric columns for editorial tension
    # Column widths (total = w): narrow | wide-dark | medium | narrow
    col_widths = [w * 0.16, w * 0.34, w * 0.34, w * 0.16]
    row_heights = [h * 0.22, h * 0.34, h * 0.26, h * 0.18]

    xs = [0.0]
    for cw in col_widths:
        xs.append(xs[-1] + cw)
    ys = [0.0]
    for rh in row_heights:
        ys.append(ys[-1] + rh)

    # Fill matrix: (col, row, fill_color)
    fills = [
        # Row 0 — bottom band
        (0, 0, COLOR_COVER_GHOST),
        (1, 0, COLOR_COVER_DARK),    # dark anchor bottom
        (2, 0, COLOR_COVER_LIGHT),
        (3, 0, COLOR_COVER_GHOST),
        # Row 1 — center-low band
        (0, 1, COLOR_COVER_LIGHT),
        (1, 1, COLOR_COVER_DARK),    # dark anchor continues
        (2, 1, COLOR_COVER_MID),
        (3, 1, COLOR_COVER_GHOST),
        # Row 2 — center-high band
        (0, 2, COLOR_COVER_GHOST),
        (1, 2, COLOR_COVER_DARK),    # dark anchor continues
        (2, 2, COLOR_COVER_GHOST),
        (3, 2, COLOR_COVER_LIGHT),
        # Row 3 — top band
        (0, 3, COLOR_COVER_MID),
        (1, 3, COLOR_COVER_DARK),    # dark anchor top
        (2, 3, COLOR_COVER_GHOST),
        (3, 3, COLOR_COVER_MID),
    ]

    for col, row, fill in fills:
        rx = xs[col]
        ry = ys[row]
        rw = col_widths[col]
        rh = row_heights[row]
        d.add(Rect(rx, ry, rw, rh, fillColor=fill, strokeColor=None, strokeWidth=0))

    # Vertical grid rules — architectural uprights
    for x in xs:
        d.add(Line(x, 0, x, h, strokeColor=COLOR_BORDER_STRONG, strokeWidth=0.6))

    # Horizontal band rules
    for y in ys:
        d.add(Line(0, y, w, y, strokeColor=COLOR_BORDER_STRONG, strokeWidth=0.6))

    # Outer border rule
    d.add(Rect(0, 0, w, h, fillColor=None, strokeColor=COLOR_BLACK, strokeWidth=1.0))

    # Fine interior accent — a single horizontal rule at row 2/3 boundary within col 2
    accent_y = ys[2] + row_heights[2] * 0.5
    d.add(Line(xs[2] + 8, accent_y, xs[3] - 8, accent_y,
               strokeColor=COLOR_TEXT_LIGHT, strokeWidth=0.4))

    # Small square accent in upper-right corner cell
    sq_size = min(col_widths[3], row_heights[3]) * 0.32
    sq_x = xs[3] + (col_widths[3] - sq_size) / 2
    sq_y = ys[3] + (row_heights[3] - sq_size) / 2
    d.add(Rect(sq_x, sq_y, sq_size, sq_size,
               fillColor=COLOR_COVER_MID, strokeColor=COLOR_TEXT_LIGHT, strokeWidth=0.4))

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
    canvas.line(MARGIN_INSIDE, 1.52 * cm, PAGE_WIDTH - MARGIN_OUTSIDE, 1.52 * cm)
    canvas.setFont(FONT_SANS, 9.0)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    canvas.drawRightString(PAGE_WIDTH - MARGIN_OUTSIDE, 1.12 * cm, str(doc.page))
    canvas.restoreState()


def footer_verso(canvas, doc) -> None:
    """Even page footer (Verso / left-hand page):
    Inside margin is on the RIGHT; Outside margin is on the LEFT.
    Page number is placed at outer bottom left.
    """
    canvas.saveState()
    canvas.setStrokeColor(COLOR_BORDER_HAIRLINE)
    canvas.setLineWidth(LINE_WEIGHT_HAIRLINE)
    canvas.line(MARGIN_OUTSIDE, 1.52 * cm, PAGE_WIDTH - MARGIN_INSIDE, 1.52 * cm)
    canvas.setFont(FONT_SANS, 9.0)
    canvas.setFillColor(COLOR_TEXT_MUTED)
    canvas.drawString(MARGIN_OUTSIDE, 1.12 * cm, str(doc.page))
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
