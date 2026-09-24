"""Validator for code block line widths in book chapters and appendices.

Ensures no line inside any fenced code block exceeds the printable
inner width of the code box in the print-ready PDF renderer.
"""

from __future__ import annotations

import glob
from pathlib import Path
import sys

# Ensure scripts dir in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from reportlab.pdfbase import pdfmetrics
import build_pdf
import book_style

SAFETY_MARGIN = 8.0  # pt margin of safety inside box border


def get_code_width_limits() -> tuple[str, float, float]:
    """Return (font_name, font_size, usable_width)."""
    build_pdf.register_fonts()
    font_name = book_style.FONT_MONO
    styles = book_style.get_book_styles()
    code_style = styles["code"]
    font_size = code_style.fontSize

    # Box padding: 10pt left, 10pt right
    box_padding = 20.0
    usable_width = book_style.PRINTABLE_WIDTH - box_padding - SAFETY_MARGIN
    return font_name, font_size, usable_width


def check_file_code_widths(
    filepath: Path, font_name: str, font_size: float, usable_width: float
) -> list[dict]:
    """Scan a single markdown file for code line overflows."""
    lines = filepath.read_text(encoding="utf-8").splitlines()
    in_code = False
    block_index = 0
    violations = []

    for line_num, line in enumerate(lines, 1):
        if line.startswith(("```", "~~~")):
            if not in_code:
                in_code = True
                block_index += 1
            else:
                in_code = False
            continue

        if in_code:
            # Expand tabs exactly as build_pdf.py does (expandtabs(4))
            expanded = line.expandtabs(4)
            measured_width = pdfmetrics.stringWidth(expanded, font_name, font_size)
            if measured_width > usable_width:
                violations.append({
                    "file": str(filepath),
                    "line": line_num,
                    "block": block_index,
                    "measured": measured_width,
                    "allowed": usable_width,
                    "chars": len(expanded),
                    "text": line,
                })

    return violations


def validate_all_code_blocks() -> list[dict]:
    """Validate all markdown chapters and appendices."""
    font_name, font_size, usable_width = get_code_width_limits()
    root = Path(__file__).resolve().parents[1]
    md_files = sorted(
        list((root / "book/chapters").glob("*.md"))
        + list((root / "book/appendices").glob("*.md"))
    )

    all_violations = []
    for md_file in md_files:
        violations = check_file_code_widths(md_file, font_name, font_size, usable_width)
        all_violations.extend(violations)

    return all_violations


def main() -> int:
    all_violations = validate_all_code_blocks()
    if not all_violations:
        print("[CODE-WIDTH-PASS] All code blocks within printable width limits.")
        print(f"  - Usable width: {book_style.PRINTABLE_WIDTH - 20 - SAFETY_MARGIN:.2f} pt (~64 monospace chars)")
        print("  - Overflowing lines: 0")
        return 0

    print(f"[CODE-WIDTH-BLOCKER] Found {len(all_violations)} code lines overflowing box border:")
    for v in all_violations:
        path = Path(v["file"]).name
        print(
            f"  {path}:{v['line']} (Block #{v['block']}) "
            f"width={v['measured']:.1f}pt > allowed={v['allowed']:.1f}pt "
            f"({v['chars']} chars):\n    {v['text']}"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
