"""Regression for a literal Markdown heading leaking into the published PDF."""
from pathlib import Path
from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

import build_pdf


class AnswerHeadingContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fonts = build_pdf.register_fonts()
        cls.styles = build_pdf.styles(*fonts)
        cls.mono = fonts[-1]

    def test_h4_is_a_separate_heading_not_joined_to_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "answer.md"
            path.write_text(
                "#### Gợi ý giải pháp\nĐáp án có nội dung riêng.\n",
                encoding="utf-8",
            )
            story = []
            build_pdf.add_markdown(story, path, self.styles, self.mono, False, {"figure": 0, "table": 0})
        paragraphs = [p for p in story if isinstance(p, Paragraph)]
        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0].getPlainText(), "Gợi ý giải pháp")
        self.assertEqual(paragraphs[0].style.name, "H3")
        self.assertEqual(paragraphs[1].getPlainText(), "Đáp án có nội dung riêng.")

    def test_hashes_in_fenced_code_are_not_headings(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "code.md"
            path.write_text("~~~text\n#### payload\n~~~\n", encoding="utf-8")
            story = []
            build_pdf.add_markdown(story, path, self.styles, self.mono, False, {"figure": 0, "table": 0})
        self.assertFalse(any(isinstance(p, Paragraph) and p.style.name == "H3" for p in story))

    def test_chapter_intro_moves_with_first_code_chunk(self):
        for blank in ["", "\n"]:
            for lines in [1, 40]:
                with self.subTest(blank=bool(blank), lines=lines):
                    with tempfile.TemporaryDirectory() as folder:
                        path = Path(folder) / "02-values.md"
                        path.write_text(
                            "INTRO_SENTINEL:\n" + blank + "~~~go\n"
                            + "\n".join(["CODE_SENTINEL"] * lines) + "\n~~~\n",
                            encoding="utf-8",
                        )
                        story = []
                        build_pdf.add_markdown(story, path, self.styles, self.mono, False,
                                               {"figure": 0, "table": 0})
                    output = BytesIO()
                    SimpleDocTemplate(output, pagesize=(600, 800),
                                      leftMargin=30, rightMargin=30,
                                      topMargin=30, bottomMargin=30).build(
                        build_pdf.keep_headings_with_content([Spacer(1, 680), *story]))
                    pages = [page.extract_text() for page in PdfReader(output).pages]
                    self.assertNotIn("INTRO_SENTINEL", pages[0])
                    self.assertIn("INTRO_SENTINEL", pages[1])
                    self.assertIn("CODE_SENTINEL", pages[1])

    def test_heading_moves_with_intro_and_code_not_a_nested_keep(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "26-policy.md"
            path.write_text(
                "## HEADING_SENTINEL\n"
                + "INTRO_SENTINEL " + "contract evidence " * 30 + ":\n\n"
                + "~~~go\nCODE_SENTINEL\n~~~\n",
                encoding="utf-8",
            )
            story = []
            build_pdf.add_markdown(story, path, self.styles, self.mono, False,
                                   {"figure": 0, "table": 0})
        output = BytesIO()
        SimpleDocTemplate(output, pagesize=(600, 800),
                          leftMargin=30, rightMargin=30,
                          topMargin=30, bottomMargin=30).build(
            build_pdf.keep_headings_with_content([Spacer(1, 600), *story]))
        pages = [page.extract_text() for page in PdfReader(output).pages]
        self.assertNotIn("HEADING_SENTINEL", pages[0])
        self.assertIn("HEADING_SENTINEL", pages[1])
        self.assertIn("INTRO_SENTINEL", pages[1])
        self.assertIn("CODE_SENTINEL", pages[1])


if __name__ == "__main__":
    unittest.main()
