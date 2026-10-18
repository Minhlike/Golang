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
    def test_character_diagram_preflight_blocks_render_before_pdf_write(self):
        with patch('validate_manuscript_diagrams.validate', return_value=['chapter:21: character diagram']):
            with patch.object(build_pdf, 'build_document') as renderer:
                with self.assertRaisesRegex(RuntimeError, 'Diagram preflight failed'):
                    build_pdf.build(candidate_only=True)
                renderer.assert_not_called()

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

    def test_audit_diagrams_rejects_sub_300_dpi(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as task_dir:
            img_path = Path(task_dir) / 'low_dpi.png'
            PILImage.new('RGB', (100, 100), (200, 200, 200)).save(img_path)
            pdf_path = Path(task_dir) / 'test_low_dpi.pdf'
            doc = SimpleDocTemplate(str(pdf_path), pagesize=(600, 600),
                                    leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img = RLImage(str(img_path), width=100, height=100)
            doc.build([Spacer(1, 10), PageBreak(), img, Paragraph("Hình 1 — Low DPI", book_style.get_book_styles()["caption"])])
            report = audit_pdf_diagrams.audit_diagrams_and_images(pdf_path)
            self.assertTrue(any(iss["dpi"] < 300.0 for iss in report["dpi_issues"]))

    def test_audit_diagrams_rejects_rgb_chroma_zero_tolerance(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as task_dir:
            img_path = Path(task_dir) / 'tinted.png'
            PILImage.new('RGB', (2000, 500), (246, 246, 247)).save(img_path)
            pdf_path = Path(task_dir) / 'test_tinted.pdf'
            doc = SimpleDocTemplate(str(pdf_path), pagesize=(600, 600),
                                    leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img = RLImage(str(img_path), width=450, height=112)
            doc.build([Spacer(1, 10), PageBreak(), img, Paragraph("Hình 1 — Tint", book_style.get_book_styles()["caption"])])
            report = audit_pdf_diagrams.audit_diagrams_and_images(pdf_path)
            self.assertEqual(len(report["color_issues"]), 1)
            self.assertEqual(report["color_issues"][0]["max_diff"], 1)

    def test_audit_diagrams_accepts_pure_grayscale_and_high_dpi(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as task_dir:
            img_path = Path(task_dir) / 'clean.png'
            PILImage.new('RGB', (2000, 500), (240, 240, 240)).save(img_path)
            pdf_path = Path(task_dir) / 'test_clean.pdf'
            doc = SimpleDocTemplate(str(pdf_path), pagesize=(600, 600),
                                    leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img = RLImage(str(img_path), width=400, height=100)
            doc.build([Spacer(1, 10), PageBreak(), img, Paragraph("Hình 1 — Clean", book_style.get_book_styles()["caption"])])
            report = audit_pdf_diagrams.audit_diagrams_and_images(pdf_path)
            self.assertEqual(len(report["dpi_issues"]), 0)
            self.assertEqual(len(report["color_issues"]), 0)
            self.assertEqual(len(report["decoding_issues"]), 0)
            self.assertEqual(len(report["pairing_issues"]), 0)

    def test_audit_diagrams_rejects_out_of_order_captions(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as task_dir:
            img_path = Path(task_dir) / 'img.png'
            PILImage.new('RGB', (1000, 500), (200, 200, 200)).save(img_path)
            pdf_path = Path(task_dir) / 'test_out_of_order.pdf'
            doc = SimpleDocTemplate(str(pdf_path), pagesize=(600, 600),
                                    leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img1 = RLImage(str(img_path), width=200, height=100)
            img2 = RLImage(str(img_path), width=200, height=100)
            # Hình 2 on page 2, Hình 1 on page 3
            doc.build([
                Spacer(1, 10), PageBreak(),
                img1, Paragraph("Hình 2 — Out of order first", book_style.get_book_styles()["caption"]),
                PageBreak(),
                img2, Paragraph("Hình 1 — Out of order second", book_style.get_book_styles()["caption"])
            ])
            report = audit_pdf_diagrams.audit_diagrams_and_images(pdf_path)
            self.assertTrue(len(report["order_issues"]) > 0, "Audit must catch out-of-order captions")

    def test_audit_diagrams_rejects_orphaned_image_without_caption(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as task_dir:
            img_path = Path(task_dir) / 'img.png'
            PILImage.new('RGB', (1000, 500), (200, 200, 200)).save(img_path)
            pdf_path = Path(task_dir) / 'test_orphan.pdf'
            doc = SimpleDocTemplate(str(pdf_path), pagesize=(600, 600),
                                    leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img = RLImage(str(img_path), width=200, height=100)
            # Image without caption on page 2
            doc.build([Spacer(1, 10), PageBreak(), img, Spacer(1, 20)])
            report = audit_pdf_diagrams.audit_diagrams_and_images(pdf_path)
            self.assertTrue(len(report["pairing_issues"]) > 0, "Audit must fail on orphaned image")

    def test_validate_publication_pdf_fails_overall_on_low_dpi(self):
        import validate_publication_pdf
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as task_dir:
            img_path = Path(task_dir) / 'low_dpi.png'
            PILImage.new('RGB', (100, 100), (200, 200, 200)).save(img_path)
            pdf_path = Path(task_dir) / 'test_preflight_fail.pdf'
            doc = SimpleDocTemplate(str(pdf_path), pagesize=(595.28, 841.89),
                                    leftMargin=68.03, rightMargin=51.02, topMargin=56.69, bottomMargin=56.69)
            img = RLImage(str(img_path), width=200, height=200) # 100px / (200/72 in) = 36 DPI
            doc.build([Paragraph("Title", book_style.get_book_styles()["body"]), img])
            with patch.object(validate_publication_pdf, 'PDF_PATH', pdf_path):
                rep = validate_publication_pdf.run_preflight()
                self.assertEqual(rep["overall_status"], "FAIL", "Overall status must fail on low DPI image")

    def test_validate_publication_pdf_fails_overall_on_blank_page(self):
        import validate_publication_pdf
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as task_dir:
            pdf_path = Path(task_dir) / 'test_blank_page.pdf'
            doc = SimpleDocTemplate(str(pdf_path), pagesize=(595.28, 841.89),
                                    leftMargin=68.03, rightMargin=51.02, topMargin=56.69, bottomMargin=56.69)
            doc.build([
                Paragraph("Page 1 Content", book_style.get_book_styles()["body"]),
                PageBreak(),
                Spacer(1, 10), # Blank page 2
                PageBreak(),
                Paragraph("Page 3 Content", book_style.get_book_styles()["body"]),
            ])
            with patch.object(validate_publication_pdf, 'PDF_PATH', pdf_path):
                rep = validate_publication_pdf.run_preflight()
                self.assertTrue(any(b['page'] == 2 for b in rep["blank_pages"]))
                self.assertEqual(rep["overall_status"], "FAIL", "Overall status must fail on blank pages")

    def test_cover_bounding_boxes_have_zero_collisions(self):
        import fitz
        paths = [
            Path('book/design/agent2-2026/artwork/front_cover_page.pdf'),
            Path('book/design/agent2-2026/artwork/full_cover_wrap_print.pdf')
        ]
        for p in paths:
            self.assertTrue(p.exists(), f"Cover file {p} must exist")
            doc = fitz.open(p)
            try:
                page = doc[0]
                blocks = page.get_text('blocks')
                collisions = []
                for i in range(len(blocks)):
                    for j in range(i + 1, len(blocks)):
                        b1, t1 = blocks[i][:4], blocks[i][4].strip().replace('\n', ' ')
                        b2, t2 = blocks[j][:4], blocks[j][4].strip().replace('\n', ' ')
                        ho = max(0.0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
                        vo = max(0.0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
                        if ho > 0.5 and vo > 0.5:
                            collisions.append((t1, t2, ho, vo))
                self.assertEqual(len(collisions), 0, f"Collisions found on {p.name}: {collisions}")
            finally:
                doc.close()


if __name__ == '__main__':
    unittest.main()
