"""Small regression tests for wrapping, neutral colors and safe promotion."""

from pathlib import Path
from io import BytesIO
import tempfile
import unittest
from unittest.mock import patch

import book_style
import build_pdf
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, NextPageTemplate, PageBreak, PageTemplate, Paragraph,
    SimpleDocTemplate, Spacer, Table,
)
from pypdf import PdfReader


class PublicationContracts(unittest.TestCase):
    def test_current_atlas_intro_fits_one_page_without_losing_last_row(self):
        build_pdf.register_fonts()
        story = []
        build_pdf.add_error_atlas(
            story, build_pdf.ROOT / 'book/appendices/error-atlas.md',
            book_style.get_book_styles(), 'BookMono',
        )
        intro = []
        for flowable in story[1:]:
            if isinstance(flowable, NextPageTemplate):
                break
            intro.append(flowable)
        output = BytesIO()
        doc = BaseDocTemplate(output, pagesize=book_style.PAGE_SIZE)
        doc.addPageTemplates(PageTemplate(id='intro', frames=[Frame(
            book_style.MARGIN_INSIDE, book_style.MARGIN_BOTTOM,
            book_style.PRINTABLE_WIDTH, book_style.PRINTABLE_HEIGHT,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )]))
        doc.build(build_pdf.keep_headings_with_content(intro))
        pages = PdfReader(output).pages
        self.assertEqual(len(pages), 1, 'Atlas introduction must not orphan a table row')
        text = pages[0].extract_text()
        for label in ('A01–A14', 'J01–J11', 'Nhóm E', 'Nhóm J'):
            self.assertIn(label, text)

    def test_atlas_group_moves_with_first_entry(self):
        build_pdf.register_fonts()
        styles = book_style.get_book_styles()
        with tempfile.TemporaryDirectory() as task_dir:
            source = Path(task_dir) / 'atlas.md'
            source.write_text(
                '## A — GROUP_SENTINEL\n### A01 ENTRY_SENTINEL\n'
                + ' '.join(['description'] * 60) + '\n', encoding='utf-8',
            )
            story = []
            build_pdf.add_error_atlas(story, source, styles, 'BookMono')
        entries = [f for f in story if not isinstance(f, (PageBreak, NextPageTemplate))]
        self.assertEqual(len(entries), 1)
        self.assertIsInstance(entries[0], KeepTogether)
        output = BytesIO()
        SimpleDocTemplate(output, pagesize=(400, 600),
                          leftMargin=30, rightMargin=30,
                          topMargin=30, bottomMargin=30).build(
            [Spacer(1, 440), *entries])
        pages = [page.extract_text() for page in PdfReader(output).pages]
        self.assertEqual(len(pages), 2)
        self.assertNotIn('GROUP_SENTINEL', pages[0])
        self.assertIn('GROUP_SENTINEL', pages[1])
        self.assertIn('ENTRY_SENTINEL', pages[1])

    def test_body_split_keeps_two_lines_on_both_pages(self):
        build_pdf.register_fonts()
        for key in ('body', 'bullet'):
            with self.subTest(style=key):
                style = book_style.get_book_styles()[key]
                paragraph = Paragraph(' '.join(['continuation'] * 24), style)
                _, height = paragraph.wrap(200, 1000)
                self.assertGreater(len(paragraph.blPara.lines), 3)
                pieces = paragraph.split(200, height - style.leading + 0.1)
                self.assertEqual(len(pieces), 2)
                for piece in pieces:
                    piece.wrap(200, 1000)
                    self.assertGreaterEqual(len(piece.blPara.lines), 2)
                self.assertEqual(paragraph.split(200, style.leading + 0.1), [])

    def test_heading_merges_with_code_container_not_nested_keep(self):
        heading = Paragraph('Heading', ParagraphStyle('H2', keepWithNext=True))
        code = Paragraph('code', ParagraphStyle('Code'))
        result = build_pdf.keep_headings_with_content([
            heading, KeepTogether([Spacer(1, 6), code, Spacer(1, 13)]),
        ])
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], KeepTogether)
        self.assertEqual(result[0]._content[0], heading)
        self.assertFalse(heading.getKeepWithNext())
        self.assertFalse(any(isinstance(f, KeepTogether) for f in result[0]._content))

    def test_heading_spacing_keeps_real_follower(self):
        heading = Paragraph('Heading', ParagraphStyle('H3', keepWithNext=True))
        spacer = Spacer(1, 5)
        body = Paragraph('body', ParagraphStyle('Body'))
        result = build_pdf.keep_headings_with_content([heading, spacer, body])
        self.assertEqual(result, [heading, spacer, body])
        self.assertTrue(spacer.getKeepWithNext())

    def test_consecutive_headings_move_with_first_answer_box(self):
        section = Paragraph('SECTION_SENTINEL', ParagraphStyle('H2', keepWithNext=True))
        answer = Paragraph('ANSWER_SENTINEL', ParagraphStyle('H3', keepWithNext=True))
        box = Table([['CODE_SENTINEL']], rowHeights=[400])
        story = [Spacer(1, 230), section, answer, KeepTogether([box])]
        output = BytesIO()
        SimpleDocTemplate(output, pagesize=(400, 600),
                          leftMargin=30, rightMargin=30,
                          topMargin=30, bottomMargin=30).build(
            build_pdf.keep_headings_with_content(story))
        pages = [page.extract_text() for page in PdfReader(output).pages]
        self.assertEqual(len(pages), 2)
        for sentinel in ('SECTION_SENTINEL', 'ANSWER_SENTINEL', 'CODE_SENTINEL'):
            self.assertNotIn(sentinel, pages[0])
            self.assertIn(sentinel, pages[1])

    def test_rendered_heading_moves_with_following_box(self):
        heading = Paragraph('HEADING_SENTINEL', ParagraphStyle('H2', keepWithNext=True))
        code = Paragraph('CODE_SENTINEL', ParagraphStyle('Code'))
        box = Table([[code]], rowHeights=[400])
        story = [Spacer(1, 230), heading, KeepTogether([Spacer(1, 6), box])]
        output = BytesIO()
        SimpleDocTemplate(output, pagesize=(400, 600),
                          leftMargin=30, rightMargin=30,
                          topMargin=30, bottomMargin=30).build(
            build_pdf.keep_headings_with_content(story))
        pages = [page.extract_text() for page in PdfReader(output).pages]
        self.assertEqual(len(pages), 2)
        self.assertNotIn('HEADING_SENTINEL', pages[0])
        self.assertIn('HEADING_SENTINEL', pages[1])
        self.assertIn('CODE_SENTINEL', pages[1])

    def test_colon_code_intro_stays_with_example(self):
        build_pdf.register_fonts()
        styles = book_style.get_book_styles()
        with tempfile.TemporaryDirectory() as task_dir:
            source = Path(task_dir) / 'devops-library-atlas.md'
            source.write_text('INTRO_SENTINEL:\n\n```go\nCODE_SENTINEL\n```\n', encoding='utf-8')
            story = []
            build_pdf.add_markdown(story, source, styles, 'BookMono', False,
                                   {'figure': 0, 'table': 0})
        self.assertTrue(story[0].getKeepWithNext())
        output = BytesIO()
        SimpleDocTemplate(output, pagesize=(400, 600),
                          leftMargin=30, rightMargin=30,
                          topMargin=30, bottomMargin=30).build(
            build_pdf.keep_headings_with_content([Spacer(1, 490), *story]))
        pages = [page.extract_text() for page in PdfReader(output).pages]
        self.assertEqual(len(pages), 2)
        self.assertNotIn('INTRO_SENTINEL', pages[0])
        self.assertIn('INTRO_SENTINEL', pages[1])
        self.assertIn('CODE_SENTINEL', pages[1])

    def test_inline_command_can_wrap_at_spaces(self):
        value = build_pdf.inline('`workerID declared and not used`', 'BookMono')
        self.assertIn('workerID declared and not used', value)
        self.assertNotIn('\u00a0', value)

    def test_palette_is_neutral_rgb(self):
        for name in dir(book_style):
            if not name.startswith('COLOR_'):
                continue
            color = getattr(book_style, name)
            with self.subTest(name=name):
                self.assertEqual(color.red, color.green)
                self.assertEqual(color.green, color.blue)

    def test_emphasis_does_not_leak_or_consume_code_asterisks(self):
        value = build_pdf.inline(
            '*một roundtrip* và **contract**, `*Service`, `**int`, `a * b`',
            'BookMono',
        )
        self.assertIn('<font name="BookSansBold">một roundtrip</font>', value)
        self.assertIn('<font name="BookSansBold">contract</font>', value)
        for code in ('*Service', '**int', 'a * b'):
            self.assertIn(f'<font name="BookMono" color="#111111">{code}</font>', value)
        self.assertNotIn('*một roundtrip*', value)

    def test_inline_preserves_escaping_and_plain_multiplication(self):
        value = build_pdf.inline('2 * 3 và `a < b && b > c`', 'BookMono')
        self.assertIn('2 * 3', value)
        self.assertIn('a &lt; b &amp;&amp; b &gt; c', value)

    def test_emphasis_can_contain_inline_code_without_delimiter_leak(self):
        value = build_pdf.inline('**hệ thống `opsprobe`** và *`*Service` hợp lệ*', 'BookMono')
        self.assertIn('<font name="BookSansBold">hệ thống <font name="BookMono" color="#111111">opsprobe</font></font>', value)
        self.assertIn('<font name="BookSansBold"><font name="BookMono" color="#111111">*Service</font> hợp lệ</font>', value)
        self.assertNotIn('**', value)

    def test_code_token_marker_does_not_collide_with_source_text(self):
        value = build_pdf.inline('\ue0000\ue001 **`a < b`**', 'BookMono')
        self.assertTrue(value.startswith('\ue0000\ue001 '))
        self.assertIn('a &lt; b', value)

    def test_promotion_preserves_exact_previous_current(self):
        with tempfile.TemporaryDirectory() as task_dir:
            root = Path(task_dir)
            current, previous, candidate = [root / name for name in ('current.pdf', 'previous.pdf', 'candidate.pdf')]
            current.write_bytes(b'previous accepted artifact')
            previous.write_bytes(b'older artifact')
            candidate.write_bytes(b'accepted candidate')
            with patch.multiple(build_pdf, CURRENT=current, PREVIOUS=previous, CANDIDATE=candidate, TMP=root):
                build_pdf.publish_candidate()
            self.assertEqual(previous.read_bytes(), b'previous accepted artifact')
            self.assertEqual(current.read_bytes(), candidate.read_bytes())


if __name__ == '__main__':
    unittest.main()
