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
    @classmethod
    def setUpClass(cls):
        build_pdf.register_fonts()

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


    def test_pairing_one_image_one_caption_pass(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            img_p = Path(td) / 'test.png'
            PILImage.new('L', (400, 200), 128).save(img_p)
            pdf_p = Path(td) / 'test_one_pair.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(600, 800), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img = RLImage(str(img_p), width=200, height=100)
            cap = Paragraph("Hình 1 — Sơ đồ hợp lệ", book_style.get_book_styles()["caption"])
            doc.build([Spacer(1, 10), PageBreak(), img, Spacer(1, 4), cap])
            rep = audit_pdf_diagrams.audit_diagrams_and_images(pdf_p)
            self.assertEqual(len(rep["pairing_issues"]), 0)
            self.assertEqual(len(rep["position_issues"]), 0)

    def test_pairing_two_images_two_captions_pass(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            img_p = Path(td) / 'test.png'
            PILImage.new('L', (400, 200), 128).save(img_p)
            pdf_p = Path(td) / 'test_two_pairs.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(600, 800), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img1 = RLImage(str(img_p), width=200, height=100)
            cap1 = Paragraph("Hình 1 — Sơ đồ số một", book_style.get_book_styles()["caption"])
            img2 = RLImage(str(img_p), width=200, height=100)
            cap2 = Paragraph("Hình 2 — Sơ đồ số hai", book_style.get_book_styles()["caption"])
            doc.build([Spacer(1, 10), PageBreak(), img1, Spacer(1, 4), cap1, Spacer(1, 20), img2, Spacer(1, 4), cap2])
            rep = audit_pdf_diagrams.audit_diagrams_and_images(pdf_p)
            self.assertEqual(len(rep["pairing_issues"]), 0)
            self.assertEqual(len(rep["position_issues"]), 0)
            self.assertEqual(len(rep["order_issues"]), 0)

    def test_pairing_two_images_captions_wrong_order_fails(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            img_p = Path(td) / 'test.png'
            PILImage.new('L', (400, 200), 128).save(img_p)
            pdf_p = Path(td) / 'test_inv_order.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(600, 800), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img1 = RLImage(str(img_p), width=200, height=100)
            cap1 = Paragraph("Hình 1 — Sơ đồ số một", book_style.get_book_styles()["caption"])
            img2 = RLImage(str(img_p), width=200, height=100)
            cap2 = Paragraph("Hình 2 — Sơ đồ số hai", book_style.get_book_styles()["caption"])
            # Inverted captions: cap2 below img1, cap1 below img2
            doc.build([Spacer(1, 10), PageBreak(), img1, Spacer(1, 4), cap2, Spacer(1, 20), img2, Spacer(1, 4), cap1])
            rep = audit_pdf_diagrams.audit_diagrams_and_images(pdf_p)
            self.assertTrue(len(rep["order_issues"]) > 0 or len(rep["pairing_issues"]) > 0)

    def test_pairing_caption_above_image_fails(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            img_p = Path(td) / 'test.png'
            PILImage.new('L', (400, 200), 128).save(img_p)
            pdf_p = Path(td) / 'test_cap_above.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(600, 800), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img = RLImage(str(img_p), width=200, height=100)
            cap = Paragraph("Hình 1 — Sơ đồ đặt sai", book_style.get_book_styles()["caption"])
            # Caption placed ABOVE image
            doc.build([Spacer(1, 10), PageBreak(), cap, Spacer(1, 10), img])
            rep = audit_pdf_diagrams.audit_diagrams_and_images(pdf_p)
            self.assertTrue(len(rep["position_issues"]) > 0, "Audit must fail when caption is above image")

    def test_pairing_caption_too_far_fails(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            img_p = Path(td) / 'test.png'
            PILImage.new('L', (400, 200), 128).save(img_p)
            pdf_p = Path(td) / 'test_cap_far.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(600, 800), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img = RLImage(str(img_p), width=200, height=100)
            cap = Paragraph("Hình 1 — Sơ đồ quá xa", book_style.get_book_styles()["caption"])
            # Caption placed 120pt below image (> MAX_GAP 70pt)
            doc.build([Spacer(1, 10), PageBreak(), img, Spacer(1, 120), cap])
            rep = audit_pdf_diagrams.audit_diagrams_and_images(pdf_p)
            self.assertTrue(len(rep["position_issues"]) > 0, "Audit must fail when caption is too far from image")

    def test_pairing_two_captions_one_image_fails(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            img_p = Path(td) / 'test.png'
            PILImage.new('L', (400, 200), 128).save(img_p)
            pdf_p = Path(td) / 'test_two_caps_one_img.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(600, 800), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img = RLImage(str(img_p), width=200, height=100)
            cap1 = Paragraph("Hình 1 — Chú thích một", book_style.get_book_styles()["caption"])
            cap2 = Paragraph("Hình 2 — Chú thích hai", book_style.get_book_styles()["caption"])
            doc.build([Spacer(1, 10), PageBreak(), img, Spacer(1, 4), cap1, cap2])
            rep = audit_pdf_diagrams.audit_diagrams_and_images(pdf_p)
            self.assertTrue(len(rep["pairing_issues"]) > 0, "Audit must fail on count mismatch (2 captions, 1 image)")

    def test_pairing_same_image_used_twice_checked(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            img_p = Path(td) / 'test.png'
            PILImage.new('L', (400, 200), 128).save(img_p)
            pdf_p = Path(td) / 'test_same_img_twice.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(600, 800), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img1 = RLImage(str(img_p), width=200, height=100)
            cap1 = Paragraph("Hình 1 — Lần xuất hiện một", book_style.get_book_styles()["caption"])
            img2 = RLImage(str(img_p), width=200, height=100)
            cap2 = Paragraph("Hình 2 — Lần xuất hiện hai", book_style.get_book_styles()["caption"])
            doc.build([Spacer(1, 10), PageBreak(), img1, Spacer(1, 4), cap1, Spacer(1, 20), img2, Spacer(1, 4), cap2])
            rep = audit_pdf_diagrams.audit_diagrams_and_images(pdf_p)
            self.assertEqual(len(rep["pairing_issues"]), 0)

    def test_pairing_ambiguous_side_by_side_fails(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage, Table
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            img_p = Path(td) / 'test.png'
            PILImage.new('L', (400, 200), 128).save(img_p)
            pdf_p = Path(td) / 'test_ambig.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(600, 800), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img1 = RLImage(str(img_p), width=200, height=100)
            img2 = RLImage(str(img_p), width=200, height=100)
            tbl = Table([[img1, img2]], colWidths=[250, 250])
            cap1 = Paragraph("Hình 1 — Sơ đồ một", book_style.get_book_styles()["caption"])
            cap2 = Paragraph("Hình 2 — Sơ đồ hai", book_style.get_book_styles()["caption"])
            doc.build([Spacer(1, 10), PageBreak(), tbl, Spacer(1, 10), cap1, Spacer(1, 10), cap2])
            rep = audit_pdf_diagrams.audit_diagrams_and_images(pdf_p)
            self.assertTrue(any("AMBIGUOUS_PAIRING" in p.get("desc", "") for p in rep["pairing_issues"]),
                            "Audit must detect ambiguous side-by-side pairings")

    def test_validate_publication_pdf_fails_without_bookmarks(self):
        import validate_publication_pdf
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            pdf_p = Path(td) / 'test_no_bm.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(595.28, 841.89), leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
            doc.build([Paragraph("Hello", book_style.get_book_styles()["body"])])
            with patch.object(validate_publication_pdf, 'PDF_PATH', pdf_p):
                rep = validate_publication_pdf.run_preflight()
                self.assertFalse(rep["bookmarks"]["pass"])
                self.assertEqual(rep["overall_status"], "FAIL")

    def test_validate_publication_pdf_fails_on_33_bookmarks(self):
        import validate_publication_pdf
        import pymupdf as fitz
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            pdf_p = Path(td) / 'test_bm.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(595.28, 841.89), leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
            doc.build([Paragraph("Hello", book_style.get_book_styles()["body"])])
            fdoc = fitz.open(pdf_p)
            fdoc.set_toc([[1, f"Chap {i}", 1] for i in range(33)])
            out_p = Path(td) / 'test_bm33.pdf'
            fdoc.save(str(out_p))
            fdoc.close()
            with patch.object(validate_publication_pdf, 'PDF_PATH', out_p):
                rep = validate_publication_pdf.run_preflight()
                self.assertFalse(rep["bookmarks"]["pass"])
                self.assertEqual(rep["overall_status"], "FAIL")

    def test_validate_publication_pdf_fails_on_invalid_bookmark_destination(self):
        import validate_publication_pdf
        import pymupdf as fitz
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            pdf_p = Path(td) / 'test_bm.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(595.28, 841.89), leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
            doc.build([Paragraph("Hello", book_style.get_book_styles()["body"])])
            fdoc = fitz.open(pdf_p)
            toc = [[1, f"Chap {i}", 1] for i in range(33)] + [[1, "Invalid Chapter", 9999]]
            fdoc.set_toc(toc)
            out_p = Path(td) / 'test_bm_inv.pdf'
            fdoc.save(str(out_p))
            fdoc.close()
            with patch.object(validate_publication_pdf, 'PDF_PATH', out_p):
                rep = validate_publication_pdf.run_preflight()
                self.assertFalse(rep["bookmarks"]["pass"])
                self.assertEqual(rep["overall_status"], "FAIL")

    def test_validate_publication_pdf_fails_on_colored_vector_or_text(self):
        import validate_publication_pdf
        import pymupdf as fitz
        from reportlab.graphics.shapes import Drawing, Rect
        from reportlab.lib.colors import red
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            pdf_color = Path(td) / 'test_color.pdf'
            d = Drawing(100, 100)
            d.add(Rect(0, 0, 100, 100, fillColor=red))
            doc_c = SimpleDocTemplate(str(pdf_color), pagesize=(595.28, 841.89), leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
            doc_c.build([d])
            fdoc = fitz.open(pdf_color)
            fdoc.set_toc([[1, f"Chap {i}", 1] for i in range(34)])
            out_p = Path(td) / 'test_color_ready.pdf'
            fdoc.save(str(out_p))
            fdoc.close()
            with patch.object(validate_publication_pdf, 'PDF_PATH', out_p):
                rep = validate_publication_pdf.run_preflight()
                self.assertFalse(rep["grayscale_compliance"]["pass"])
                self.assertEqual(rep["overall_status"], "FAIL")

    def test_audit_diagrams_fails_when_diagram_missing_from_end_of_book(self):
        import audit_pdf_diagrams
        from PIL import Image as PILImage
        from reportlab.platypus import Image as RLImage
        build_pdf.register_fonts()
        with tempfile.TemporaryDirectory() as td:
            img_p = Path(td) / 'test.png'
            PILImage.new('L', (400, 200), 128).save(img_p)
            pdf_p = Path(td) / 'test_missing_last_fig.pdf'
            doc = SimpleDocTemplate(str(pdf_p), pagesize=(600, 800), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            img1 = RLImage(str(img_p), width=200, height=100)
            cap1 = Paragraph("Hình 1 — Sơ đồ kiến trúc đầu", book_style.get_book_styles()["caption"])
            doc.build([Spacer(1, 10), PageBreak(), img1, Spacer(1, 4), cap1])
            fake_ms = {
                1: {"num": 1, "file": "chap1.md", "image_rel": "img1.png", "caption": "Sơ đồ kiến trúc đầu"},
                2: {"num": 2, "file": "chap2.md", "image_rel": "img2.png", "caption": "Sơ đồ kiến trúc cuối sách"},
            }
            with patch.object(audit_pdf_diagrams, 'load_manuscript_figures', return_value=fake_ms):
                rep = audit_pdf_diagrams.audit_diagrams_and_images(pdf_p)
                self.assertTrue(len(rep["semantic_issues"]) > 0, "Audit must fail when last diagram is missing")
                self.assertTrue(any("không khớp" in str(x) or "không tìm thấy" in str(x) for x in rep["semantic_issues"]))

    def test_validate_publication_pdf_fails_when_bookmark_points_to_adjacent_page(self):
        import validate_publication_pdf
        import pymupdf as fitz
        candidate_pdf = Path("tmp/pdfs/Golang_Master.candidate.pdf").resolve()
        self.assertTrue(candidate_pdf.exists(), f"Candidate PDF {candidate_pdf} must exist")
        with tempfile.TemporaryDirectory() as td:
            tampered_pdf = Path(td) / "tampered_adjacent.pdf"
            doc = fitz.open(candidate_pdf)
            toc = doc.get_toc()
            self.assertEqual(len(toc), 34, "Candidate must have exactly 34 bookmarks")
            orig_page = toc[7][2]
            toc[7][2] = orig_page - 1
            doc.set_toc(toc)
            doc.save(str(tampered_pdf))
            doc.close()
            with patch.object(validate_publication_pdf, 'PDF_PATH', tampered_pdf):
                rep = validate_publication_pdf.run_preflight()
                self.assertFalse(rep["bookmarks"]["pass"], "Preflight bookmarks must fail when bookmark points to adjacent page")
                self.assertEqual(rep["overall_status"], "FAIL", "Overall status must fail on bookmark destination error")
                self.assertTrue(any("trang" in iss.lower() or "không khớp" in iss.lower() for iss in rep["bookmarks"]["issues"]))

    def test_validate_publication_pdf_candidate_passes_all(self):
        import validate_publication_pdf
        import pymupdf as fitz
        candidate_pdf = Path("tmp/pdfs/Golang_Master.candidate.pdf").resolve()
        self.assertTrue(candidate_pdf.exists(), f"Candidate PDF {candidate_pdf} must exist for preflight QA")
        self.assertGreater(candidate_pdf.stat().st_size, 1_000_000, "Candidate PDF must not be empty")
        with fitz.open(candidate_pdf) as doc:
            self.assertGreater(len(doc), 0, "Candidate PDF must be readable and contain pages")
        with patch.object(validate_publication_pdf, 'PDF_PATH', candidate_pdf):
            rep = validate_publication_pdf.run_preflight()
            self.assertEqual(rep["overall_status"], "PASS", f"Candidate PDF must PASS preflight: {rep.get('bookmarks', {}).get('issues', [])}")

    def test_render_fig1_text_overflow_raises_error_strictly(self):
        import copy
        import sys
        sys.path.insert(0, str(Path("scripts").resolve()))
        import render_figures_1_6
        # 1. Test wrap_text_strictly raises ValueError when line count exceeds max_lines
        long_text = (
            "Đây là một đoạn văn bản rất dài và phức tạp nhằm kiểm tra việc phát hiện tràn dòng tự động "
            "của hệ thống dàn chữ đồ họa khoa học trong render_fig1 mà không được phép cắt bỏ âm thầm hay làm mất dữ liệu."
        )
        with self.assertRaises(ValueError):
            render_figures_1_6.wrap_text_strictly(
                long_text, max_chars_per_line=20, max_lines=2, context="TestMilestone"
            )
        # 2. Test wrap_text_strictly raises ValueError on real glyph width overflow even with few characters
        wide_glyph_token = "W" * 24  # 24 chars (< 30 chars) but physically wider than 31.8 mm at 6.2 pt
        with self.assertRaises(ValueError):
            render_figures_1_6.wrap_text_strictly(
                wide_glyph_token, max_chars_per_line=30, max_lines=3, max_width_mm=31.8, context="WideGlyphTest"
            )
        # 3. Test render_fig1 raises ValueError when milestone description overflows 3 lines
        bad_milestones = copy.deepcopy(render_figures_1_6.FIG1_SPEC)
        bad_milestones['row1'][0]['desc'] = long_text
        with self.assertRaises(ValueError):
            render_figures_1_6.render_fig1(custom_milestones=bad_milestones, save=False)

    def test_render_fig2_negative_arrow_and_conclusion_overflow_detected(self):
        import copy
        import sys
        sys.path.insert(0, str(Path("scripts").resolve()))
        import render_figures_1_6
        # Reproduce old Fig 2 defect 1: single-line wide arrow label colliding with column borders
        bad_spec_arrow = copy.deepcopy(render_figures_1_6.FIG2_SPEC)
        bad_spec_arrow['pillars'][0]['conn_lines'] = ['Cú pháp & hiệu năng biên dịch trực tiếp']
        with self.assertRaises(ValueError):
            render_figures_1_6.render_fig2(custom_spec=bad_spec_arrow, save=False)

        # Reproduce old Fig 2 defect 2: single-line wide bottom conclusion overflowing note_box
        bad_spec_conc = copy.deepcopy(render_figures_1_6.FIG2_SPEC)
        bad_spec_conc['conclusion_lines'] = [
            'Nguyên lý thiết kế: Go kết hợp có chọn lọc các ý tưởng kinh điển đã qua kiểm chứng '
            '(hỗ trợ cả giao tiếp channel lẫn đồng bộ bộ nhớ chia sẻ), đồng thời kiên quyết từ bỏ '
            'các tính năng làm phức tạp hóa mô hình tư duy.'
        ]
        with self.assertRaises(ValueError):
            render_figures_1_6.render_fig2(custom_spec=bad_spec_conc, save=False)

    def test_render_fig3_negative_step_and_connector_collision_detected(self):
        import copy
        import sys
        sys.path.insert(0, str(Path("scripts").resolve()))
        import render_figures_1_6
        # Reproduce old Fig 3 defect 1: Step 1 description overflowing 2 lines / right border
        bad_spec_step1 = copy.deepcopy(render_figures_1_6.FIG3_SPEC)
        bad_spec_step1['steps'][0]['desc'] = (
            "Xác định kỳ vọng cụ thể trước khi chạy: đoạn mã sẽ trả về giá trị gì, "
            "thay đổi trạng thái nào, phát sinh tác dụng phụ gì trên hệ thống hoặc báo lỗi biên dịch gì?"
        )
        with self.assertRaises(ValueError):
            render_figures_1_6.render_fig3(custom_spec=bad_spec_step1, save=False)

        # Reproduce old Fig 3 defect 2: edge label wide enough to collide with vertical dashed connector x=94.0
        bad_spec_edge = copy.deepcopy(render_figures_1_6.FIG3_SPEC)
        bad_spec_edge['branch_yes']['edge_label'] = 'CÓ (Bác bỏ giả thuyết thực nghiệm ban đầu)'
        with self.assertRaises(ValueError):
            render_figures_1_6.render_fig3(custom_spec=bad_spec_edge, save=False)

    def test_render_fig5_negative_subbox_overflow_and_semantic_contract(self):
        import copy
        import sys
        sys.path.insert(0, str(Path("scripts").resolve()))
        import render_figures_1_6
        # Reproduce old Fig 5 defect: text in Layer 3 SSA sub-box touching/exceeding sub-box border
        bad_spec_ssa = copy.deepcopy(render_figures_1_6.FIG5_SPEC)
        bad_spec_ssa['layers'][2]['boxes'][0] = (
            '1. Noding & IR',
            ['Chuyển cây cú pháp sang IR (noder, ir)', 'Inlining & Escape Analysis toàn cục']
        )
        with self.assertRaises(ValueError):
            render_figures_1_6.render_fig5(custom_spec=bad_spec_ssa, save=False)

        # Verify inaccurate "Zero warnings", "zero implicit cast", and "bắt panic, race & logic" claims are absent,
        # and exact Go Specification / toolchain distinctions are present in Fig 2 and Fig 5 specs/PUMLs
        puml_map = render_figures_1_6.build_expected_puml_contents()
        fig2_puml = puml_map['go-idea-lineage.puml'].lower()
        self.assertNotIn("zero implicit cast", fig2_puml)
        self.assertIn("untyped const", fig2_puml)
        fig5_puml = puml_map['compiler-doc-go.puml'].lower()
        self.assertNotIn("zero warnings", fig5_puml)
        self.assertNotIn("mọi sai lệch là lỗi", fig5_puml)
        self.assertNotIn("bắt panic, race & logic", fig5_puml)
        self.assertIn("go test -race", fig5_puml)

    def test_render_fig6_negative_scope2_border_cutting_code_detected(self):
        import sys
        sys.path.insert(0, str(Path("scripts").resolve()))
        import render_figures_1_6
        # Reproduce old Fig 6 defect: Scope 2 left border at x=16.0 cutting across 'if status >= 500 {' and '}' at x=13.5
        with self.assertRaises(ValueError):
            render_figures_1_6.render_fig6(custom_s2_x=16.0, save=False)

    def test_figures_1_6_font_size_and_live_geometric_audit_contract(self):
        import re
        import sys
        sys.path.insert(0, str(Path("scripts").resolve()))
        import render_figures_1_6
        # 1. Static check on script source
        render_script = Path("scripts/render_figures_1_6.py").read_text(encoding="utf-8")
        matches = re.findall(r'fontsize\s*=\s*([0-9\.]+)', render_script)
        self.assertTrue(len(matches) > 0, "Must find fontsize definitions in render_figures_1_6.py")
        for fs_str in matches:
            fs = float(fs_str)
            self.assertGreaterEqual(fs, 6.0, f"All fontsizes in render_figures_1_6.py must be >= 6.0 pt, found {fs}")

        # 2. Live Matplotlib FigureGeometryAuditor check across all 6 figures (verifies real Text.get_fontsize() >= 6.0,
        #    min_container_padding_pt >= 4.0, min_border_clearance_pt >= 4.0, and zero line/text collisions)
        render_fns = [
            render_figures_1_6.render_fig1,
            render_figures_1_6.render_fig2,
            render_figures_1_6.render_fig3,
            render_figures_1_6.render_fig4,
            render_figures_1_6.render_fig5,
            render_figures_1_6.render_fig6,
        ]
        for fn in render_fns:
            report = fn(save=False)
            self.assertGreaterEqual(
                report['min_container_padding_pt'], 4.0,
                f"{report['fig_name']} min_container_padding_pt={report['min_container_padding_pt']} < 4.0 pt"
            )
            self.assertGreaterEqual(
                report['min_border_clearance_pt'], 4.0,
                f"{report['fig_name']} min_border_clearance_pt={report['min_border_clearance_pt']} < 4.0 pt"
            )
            self.assertGreaterEqual(
                report['min_connector_clearance_pt'], 1.2,
                f"{report['fig_name']} min_connector_clearance_pt={report['min_connector_clearance_pt']} < 1.2 pt"
            )

        # 3. Verify companion .puml files are 100% synchronized with authoritative renderer
        drifted = render_figures_1_6.sync_puml_sources(check_only=True)
        self.assertEqual(drifted, [], f"PUML files drifted from authoritative renderer: {drifted}")

    def test_figures_1_6_grayscale_and_dimensions(self):
        from PIL import Image
        import numpy as np
        target_figures = [
            "go-history-timeline.png",
            "go-idea-lineage.png",
            "feedback-loop.png",
            "go-source-anatomy.png",
            "compiler-doc-go.png",
            "go-scope-trace.png",
        ]
        assets_dir = Path("assets/diagrams")
        for fig_name in target_figures:
            fig_path = assets_dir / fig_name
            self.assertTrue(fig_path.exists(), f"Figure file {fig_name} must exist")
            with Image.open(fig_path) as im:
                rgb = im.convert("RGB")
                w, h = rgb.size
                self.assertEqual(w, 2116, f"{fig_name} must have width 2116 px for 320 DPI across 168 mm")
                arr = np.array(rgb)
                r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
                max_diff = np.max(np.abs(r.astype(int) - g.astype(int))) + np.max(np.abs(r.astype(int) - b.astype(int)))
                self.assertEqual(max_diff, 0, f"{fig_name} must be pure grayscale (R=G=B everywhere)")

    def test_figures_1_6_no_line_numbers_in_code_blocks(self):
        fig_script = Path("scripts/render_figures_1_6.py").read_text(encoding="utf-8")
        import re
        self.assertIsNone(re.search(r"\'[0-9]{1,2}:\s*package", fig_script), "Code block must not contain line number prefixes")
        self.assertIsNone(re.search(r"\'[0-9]{1,2}:\s*func", fig_script), "Code block must not contain line number prefixes")

    def test_figure_34_semantic_and_identifier_contract(self):
        import sys
        sys.path.insert(0, str(Path("scripts").resolve()))
        import ch19_29_vector_diagrams as vdiag
        from reportlab.graphics.shapes import String

        drawing = vdiag.build_type_information_boundaries_drawing()
        texts = []

        def collect_strings(node):
            if isinstance(node, String):
                texts.append(node.text)
            elif hasattr(node, "contents"):
                for child in node.contents:
                    collect_strings(child)

        collect_strings(drawing)
        combined = "\n".join(texts)
        combined_lower = combined.lower()

        required_tokens = [
            "Unique[T comparable]",
            "Measurable",
            "Max[T Measurable]",
            "Milliseconds",
            "Set[T comparable]",
            "Batch[E].Map[F any]",
            "Checker",
            "RunOne",
            "httpChecker",
            "ProbeError",
            "reflect.TypeOf",
            "reflect.ValueOf",
        ]
        for token in required_tokens:
            self.assertIn(token, combined, f"Figure 34 must contain Chapter 19 identifier '{token}'")

        forbidden_tokens = [
            "constraints.ordered",
            "summaryreader",
            "gcshape",
            "stenciling",
            "dictionary",
            "itab",
            "fat pointer",
            "func ptr",
            "boxing value type",
            "escape analysis đẩy ra heap",
            "cấp phát heap liên tục",
            "10x",
            "100x",
            "cloneslice",
            "maxordered",
            "writesummary",
            "decodepayload",
        ]
        for bad in forbidden_tokens:
            self.assertNotIn(bad, combined_lower, f"Figure 34 must not contain unverified/contradictory claim '{bad}'")

    def test_figure_33_semantic_and_boundary_contract(self):
        import sys
        sys.path.insert(0, str(Path("scripts").resolve()))
        import ch19_29_vector_diagrams as vdiag
        from reportlab.graphics.shapes import String

        drawing = vdiag.build_workflow_promotion_jobs_drawing()
        texts = []

        def collect_strings(node):
            if isinstance(node, String):
                texts.append(node.text)
            elif hasattr(node, "contents"):
                for child in node.contents:
                    collect_strings(child)

        collect_strings(drawing)
        combined = "\n".join(texts)
        combined_lower = combined.lower()

        required_tokens = [
            "JOB: VERIFY",
            "JOB: BUILD-ARTIFACT",
            "JOB: PROMOTE-PRODUCTION",
            "promote-gate",
            "--provenance-verified=false",
            "fail-closed",
            "exit 1",
        ]
        for token in required_tokens:
            self.assertIn(token.lower(), combined_lower, f"Figure 33 must reflect delivery.yaml step '{token}'")

        forbidden_tokens = [
            "cosign verify",
            "slsa level 3",
            "attestation.json",
            "scan-results.sarif",
        ]
        for bad in forbidden_tokens:
            self.assertNotIn(bad, combined_lower, f"Figure 33 must not overclaim unimplemented feature '{bad}'")

    def test_atlas_figures_51_to_58_header_and_line_spacing_contract(self):
        import sys
        sys.path.insert(0, str(Path("scripts").resolve()))
        import ch19_29_vector_diagrams as vdiag
        from reportlab.graphics.shapes import String

        builders = [
            (51, vdiag.build_library_informer_data_path_drawing),
            (52, vdiag.build_library_smithy_step_order_drawing),
            (53, vdiag.build_collector_pipeline_drawing),
            (54, vdiag.build_containerd_shim_boundary_drawing),
            (55, vdiag.build_grpc_client_balancing_drawing),
            (56, vdiag.build_cobra_hook_order_drawing),
            (57, vdiag.build_viper_value_precedence_drawing),
            (58, vdiag.build_agent_mailbox_contract_drawing),
        ]

        for fig_num, builder in builders:
            drawing = builder()
            strings = []

            def collect(node):
                if isinstance(node, String):
                    strings.append(node)
                elif hasattr(node, "contents"):
                    for c in node.contents:
                        collect(c)

            collect(drawing)
            all_text = " ".join(s.text for s in strings)
            self.assertNotIn("PHỤ LỤC B", all_text, f"Figure {fig_num} header must not reference 'PHỤ LỤC B'")
            self.assertIn(f"ATLAS THƯ VIỆN // HÌNH {fig_num}", all_text, f"Figure {fig_num} header must be 'ATLAS THƯ VIỆN // HÌNH {fig_num}'")

            if fig_num == 54:
                # Test line distance between subreaper and zombie process
                subreaper_s = next(s for s in strings if "Shim làm subreaper tránh" in s.text)
                zombie_s = next(s for s in strings if "zombie process trong OS" in s.text)
                delta_y = abs(subreaper_s.y - zombie_s.y)
                self.assertLessEqual(delta_y, 18.0, f"Figure 54 zombie process text must not fall to bottom: delta_y={delta_y} pt")

    def test_lead_in_colon_stays_with_following_table(self):
        build_pdf.register_fonts()
        styles = book_style.get_book_styles()
        with tempfile.TemporaryDirectory() as task_dir:
            source = Path(task_dir) / 'test_chapter.md'
            source.write_text('TABLE_INTRO_COLON:\n\n| H1 | H2 |\n| --- | --- |\n| CELL_A | CELL_B |\n', encoding='utf-8')
            story = []
            build_pdf.add_markdown(story, source, styles, 'BookMono', False, {'figure': 0, 'table': 0})
        self.assertTrue(story[0].getKeepWithNext())
        merged = build_pdf.keep_headings_with_content(story)
        self.assertTrue(any(isinstance(f, KeepTogether) for f in merged))
        output = BytesIO()
        SimpleDocTemplate(output, pagesize=(400, 600), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30).build(
            build_pdf.keep_headings_with_content([Spacer(1, 490), *story])
        )
        pages = [page.extract_text() for page in PdfReader(output).pages]
        self.assertEqual(len(pages), 2)
        self.assertNotIn('TABLE_INTRO_COLON', pages[0])
        self.assertIn('TABLE_INTRO_COLON', pages[1])
        self.assertIn('CELL_A', pages[1])

    def test_multiline_table_splits_across_pages_with_repeated_header(self):
        build_pdf.register_fonts()
        styles = book_style.get_book_styles()
        with tempfile.TemporaryDirectory() as task_dir:
            source = Path(task_dir) / 'test_chapter.md'
            rows = ["| Verb | Meaning | Example |", "| :--- | :--- | :--- |"]
            for i in range(12):
                rows.append(f"| %v{i} | Description for verb {i} | fmt.Printf example {i} |")
            source.write_text("\n".join(rows) + "\n", encoding='utf-8')
            story = []
            build_pdf.add_markdown(story, source, styles, 'BookMono', False, {'figure': 0, 'table': 0})
        tables = [f for f in story if isinstance(f, Table)]
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0].repeatRows, 1)
        output = BytesIO()
        SimpleDocTemplate(output, pagesize=(400, 300), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30).build(
            build_pdf.keep_headings_with_content(story)
        )
        pages = [page.extract_text() for page in PdfReader(output).pages]
        self.assertGreaterEqual(len(pages), 2, "12-row table should split cleanly across pages")
        for p in pages:
            self.assertIn("Verb", p, "Header row must repeat across split pages")

    def test_heading_with_short_lead_in_moves_with_following_code_box(self):
        build_pdf.register_fonts()
        styles = book_style.get_book_styles()
        with tempfile.TemporaryDirectory() as task_dir:
            source = Path(task_dir) / 'test_chapter.md'
            source.write_text('## HEADING_SENTINEL\n\nShort lead-in sentence.\n\n```go\nCODE_PAYLOAD_SENTINEL\n```\n', encoding='utf-8')
            story = []
            build_pdf.add_markdown(story, source, styles, 'BookMono', False, {'figure': 0, 'table': 0})
        output = BytesIO()
        SimpleDocTemplate(output, pagesize=(400, 600), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30).build(
            build_pdf.keep_headings_with_content([Spacer(1, 480), *story])
        )
        pages = [page.extract_text() for page in PdfReader(output).pages]
        self.assertEqual(len(pages), 2)
        self.assertNotIn('HEADING_SENTINEL', pages[0])
        self.assertIn('HEADING_SENTINEL', pages[1])
        self.assertIn('CODE_PAYLOAD_SENTINEL', pages[1])

    def test_heading_before_figure_moves_with_figure(self):
        heading = Paragraph('FIGURE_HEADING_SENTINEL', ParagraphStyle('H2', keepWithNext=True))
        figure_box = KeepTogether([Spacer(1, 4), Table([['IMAGE']], rowHeights=[350]), Paragraph('Caption', ParagraphStyle('Caption'))])
        merged = build_pdf.keep_headings_with_content([heading, figure_box])
        self.assertEqual(len(merged), 1)
        self.assertIsInstance(merged[0], KeepTogether)
        output = BytesIO()
        SimpleDocTemplate(output, pagesize=(400, 600), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30).build(
            [Spacer(1, 250), *merged]
        )
        pages = [page.extract_text() for page in PdfReader(output).pages]
        self.assertEqual(len(pages), 2)
        self.assertNotIn('FIGURE_HEADING_SENTINEL', pages[0])
        self.assertIn('FIGURE_HEADING_SENTINEL', pages[1])

    def test_long_lead_in_over_160_chars_stays_with_follower(self):
        build_pdf.register_fonts()
        styles = book_style.get_book_styles()
        long_lead_in = (
            "Dưới đây là bảng tổng hợp các quy tắc ngữ nghĩa quan trọng nhất mà kỹ sư cần ghi nhớ "
            "để tránh các lỗi cấp phát vùng nhớ heap không đáng có trong quá trình tối ưu hóa mã nguồn:"
        )
        self.assertGreater(len(long_lead_in), 160)
        self.assertLessEqual(len(long_lead_in), 280)
        with tempfile.TemporaryDirectory() as task_dir:
            source = Path(task_dir) / 'test_chapter.md'
            source.write_text(f"{long_lead_in}\n\n| K1 | K2 |\n| --- | --- |\n| V1 | V2 |\n", encoding='utf-8')
            story = []
            build_pdf.add_markdown(story, source, styles, 'BookMono', False, {'figure': 0, 'table': 0})
        self.assertTrue(story[0].getKeepWithNext())
        self.assertEqual(story[0].style.name, 'body-intro')


    def test_chapter_tail_paragraph_never_splits_before_pagebreak(self):
        """Test that keep_headings_with_content wraps the last paragraph before PageBreak
        in KeepTogether to prevent 1-3 line orphan spills across chapter boundaries."""
        para = Paragraph("Final paragraph of chapter", ParagraphStyle("Body"))
        story = [para, PageBreak()]
        processed = build_pdf.keep_headings_with_content(story)
        self.assertEqual(len(processed), 2)
        self.assertIsInstance(processed[0], KeepTogether)
        self.assertEqual(processed[0]._content[0], para)
        self.assertIsInstance(processed[1], PageBreak)

    def test_no_trailing_chapter_runt_pages(self):
        """Regression test for confirmed P1 pagination defect:
        Assert that no page immediately preceding a new chapter opener contains only
        1-3 continuation lines spilled from the previous page.
        Excludes reference/bibliography lists and intentional structural back matter layouts."""
        import pymupdf as fitz
        candidate_pdf = Path("tmp/pdfs/Golang_Master.candidate.pdf").resolve()
        self.assertTrue(candidate_pdf.exists(), f"Candidate PDF {candidate_pdf} must exist")
        with fitz.open(candidate_pdf) as doc:
            chapter_pages = []
            for pno in range(1, len(doc) + 1):
                text = doc[pno - 1].get_text()
                lines = [l.strip() for l in text.splitlines() if l.strip() and l.strip() != str(pno)]
                if not lines:
                    continue
                first = lines[0]
                if (first.startswith("Chương ") and "—" in first) or first.startswith("Phụ lục ") or first.startswith("Atlas Lỗi"):
                    chapter_pages.append((pno, first))

            self.assertGreaterEqual(len(chapter_pages), 29, "Must detect all chapter openers in the manuscript")

            runt_defects = []
            for pno, title in chapter_pages:
                if pno <= 1:
                    continue
                pre_pno = pno - 1
                pre_text = doc[pre_pno - 1].get_text()
                pre_lines = [l.strip() for l in pre_text.splitlines() if l.strip() and l.strip() != str(pre_pno)]

                # Exclude intentional layouts:
                # 1. Reference/bibliography listings (numbered entries or citation domains)
                is_reference_list = any(
                    l.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.")) or "Go Team" in l or "go.dev" in l
                    for l in pre_lines
                )
                if is_reference_list:
                    continue

                # If pre-chapter page only contains 1-3 lines
                if len(pre_lines) in (1, 2, 3):
                    runt_defects.append({
                        "page": pre_pno,
                        "lines_count": len(pre_lines),
                        "lines": pre_lines,
                        "preceding_chapter": title,
                    })

            self.assertEqual(runt_defects, [], f"Found trailing chapter runt pages with 1-3 lines: {runt_defects}")


    def test_printed_toc_and_bookmarks_exact_1to1_match_actual_pages(self):
        """Regression test for post-repagination TOC and outline fidelity:
        Verifies that every entry in the printed Table of Contents (Page 2)
        and all 34 PDF outline bookmarks match the actual chapter/appendix start
        pages in tmp/pdfs/Golang_Master.candidate.pdf with 1:1 exact equality."""
        import re
        import pymupdf as fitz
        candidate_pdf = Path("tmp/pdfs/Golang_Master.candidate.pdf").resolve()
        self.assertTrue(candidate_pdf.exists(), f"Candidate PDF {candidate_pdf} must exist")
        with fitz.open(candidate_pdf) as doc:
            toc = doc.get_toc()
            self.assertEqual(len(toc), 34, f"Must have exactly 34 bookmarks, got {len(toc)}")

            # Extract printed TOC from Page 2
            p2_text = doc[1].get_text()
            lines = [l.strip() for l in p2_text.splitlines() if l.strip()]
            printed_entries = []
            for i, line in enumerate(lines):
                if line.isdigit() and int(line) >= 2:
                    pno = int(line)
                    title_parts = []
                    j = i - 1
                    while (
                        j >= 0
                        and not lines[j].isdigit()
                        and not lines[j].startswith("PHẦN")
                        and lines[j] != "MỤC LỤC"
                        and lines[j] != "BACK MATTER // TÀI LIỆU TRA CỨU"
                    ):
                        title_parts.insert(0, lines[j])
                        j -= 1
                    title = " ".join(title_parts)
                    printed_entries.append((title, pno))

            self.assertEqual(len(printed_entries), 34, f"Printed TOC must have 34 entries (header + 33 items), got {len(printed_entries)}")

            # 1. First entry must be TOC itself on Page 2
            self.assertEqual(toc[0][2], 2)
            self.assertEqual(printed_entries[0][1], 2)

            # 2. Check each remaining entry for 1:1 exact match
            for idx in range(1, 34):
                bm_lvl, bm_title, bm_pno = toc[idx]
                pr_title, pr_pno = printed_entries[idx]
                self.assertEqual(
                    bm_pno, pr_pno,
                    f"Mismatch at index {idx}: bookmark page {bm_pno} != printed TOC page {pr_pno} ('{bm_title}')"
                )

                # 3. Check actual target page content
                page_text = doc[bm_pno - 1].get_text()
                clean_words = [
                    w for w in re.findall(r"\w+", bm_title.lower())
                    if len(w) > 2 and w not in ("chương", "atlas", "mục", "lục", "phần", "nguồn", "thư", "viện")
                ]
                page_words = set(re.findall(r"\w+", page_text.lower()))
                matched = [w for w in clean_words if w in page_words]
                self.assertGreaterEqual(
                    len(matched), max(2, len(clean_words) // 2),
                    f"Target page {bm_pno} does not contain heading keywords for '{bm_title}'"
                )


if __name__ == '__main__':
    unittest.main()

