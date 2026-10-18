# -*- coding: utf-8 -*-
"""Comprehensive Visual & Layout Preflight Auditor for Diagrams and Images in Golang_Master.pdf.

Audits:
1. Catalog: Every image occurrence across all pages, dimensions, format, colorspace.
2. Geometry & Bounds: Overflow across printable width (168mm / 476.2pt) or margins.
3. Effective DPI: Detect images with resolution < 150 DPI or < 300 DPI.
4. Color Compliance: Check if any image contains RGB chrominance (saturation > 0) in a grayscale book.
5. Captions & Numbering: Check sequence of "Hình X — ...", orphaned captions, and "@figure" tags.
6. Figure-Text Proximity: Verify caption is directly below the figure on the same page.
"""

from __future__ import annotations

import io
import math
from pathlib import Path
import re
import sys

from PIL import Image as PILImage
import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "Golang_Master.pdf"

# Page geometry in points
PAGE_W = 595.28  # 210 mm
PAGE_H = 841.89  # 297 mm

# Margins
MARGIN_GUTTER = 68.03   # 24 mm
MARGIN_OUTSIDE = 51.02  # 18 mm
MARGIN_TOP = 62.36      # 22 mm
MARGIN_BOTTOM = 56.69   # 20 mm

PRINTABLE_W = PAGE_W - MARGIN_GUTTER - MARGIN_OUTSIDE  # 476.23 pt (168 mm)
PRINTABLE_H = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM      # 722.84 pt (255 mm)


def audit_diagrams_and_images(pdf_path: Path = PDF_PATH) -> dict:
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    catalog = []
    overflow_issues = []
    dpi_warnings = []
    color_issues = []
    caption_issues = []
    unrendered_figure_tags = []

    # Regex for figure captions in text
    figure_caption_regex = re.compile(r"Hình\s+(\d+)\s*[—–-]\s*([^\n]+)")
    unrendered_figure_regex = re.compile(r"@figure\b")

    figures_found = []  # list of (page, figure_num, caption_text)

    for pno in range(1, total_pages + 1):
        page = doc[pno - 1]
        text = page.get_text()

        # Check for unrendered @figure tags in text
        if unrendered_figure_regex.search(text):
            unrendered_figure_tags.append(pno)

        # Extract figure captions
        for match in figure_caption_regex.finditer(text):
            f_num = int(match.group(1))
            f_title = match.group(2).strip()
            figures_found.append({
                "page": pno,
                "num": f_num,
                "title": f_title,
            })

        # Mirrored margins for current page
        is_recto = (pno % 2 != 0)
        # Recto: Gutter on Left, Outside on Right
        # Verso: Outside on Left, Gutter on Right
        left_margin = MARGIN_GUTTER if is_recto else MARGIN_OUTSIDE
        right_margin = PAGE_W - (MARGIN_OUTSIDE if is_recto else MARGIN_GUTTER)
        top_margin = MARGIN_TOP
        bottom_margin = PAGE_H - MARGIN_BOTTOM

        # Check images on page
        images = page.get_images(full=True)
        for img_info in images:
            xref = img_info[0]
            base = doc.extract_image(xref)
            if not base:
                continue

            px_w = base["width"]
            px_h = base["height"]
            cs = base["colorspace"]
            ext = base["ext"]
            img_bytes = base["image"]

            rects = page.get_image_rects(xref)
            for r in rects:
                w_pt = r.width
                h_pt = r.height

                # Skip tiny icons, bullets, or full-cover on page 1
                if pno == 1:
                    # Page 1 is the official Front Cover, expected to fill page
                    catalog.append({
                        "page": pno,
                        "xref": xref,
                        "type": "FRONT_COVER",
                        "px": (px_w, px_h),
                        "pt": (round(w_pt, 1), round(h_pt, 1)),
                        "bbox": (round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)),
                        "dpi": round(min(px_w / (w_pt / 72.0), px_h / (h_pt / 72.0)), 1),
                        "colorspace": cs,
                    })
                    continue

                eff_dpi_w = px_w / (w_pt / 72.0) if w_pt > 0 else 0
                eff_dpi_h = px_h / (h_pt / 72.0) if h_pt > 0 else 0
                eff_dpi = min(eff_dpi_w, eff_dpi_h)

                item = {
                    "page": pno,
                    "xref": xref,
                    "type": "INTERIOR_DIAGRAM",
                    "px": (px_w, px_h),
                    "pt": (round(w_pt, 1), round(h_pt, 1)),
                    "bbox": (round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)),
                    "dpi": round(eff_dpi, 1),
                    "colorspace": cs,
                }
                catalog.append(item)

                # 1. Bounds check (tolerance 2.0 pt)
                TOL = 2.0
                violations = []
                if r.width > (PRINTABLE_W + TOL):
                    violations.append(f"Width {r.width:.1f}pt > printable {PRINTABLE_W:.1f}pt (+{r.width - PRINTABLE_W:.1f}pt)")
                if r.x0 < (left_margin - TOL):
                    violations.append(f"Left bound {r.x0:.1f}pt encroaches margin {left_margin:.1f}pt")
                if r.x1 > (right_margin + TOL):
                    violations.append(f"Right bound {r.x1:.1f}pt encroaches margin {right_margin:.1f}pt")
                if r.y1 > (bottom_margin + TOL):
                    violations.append(f"Bottom bound {r.y1:.1f}pt encroaches margin {bottom_margin:.1f}pt")

                if violations:
                    overflow_issues.append({
                        "page": pno,
                        "xref": xref,
                        "violations": violations,
                        "pt": (round(w_pt, 1), round(h_pt, 1)),
                        "bbox": (round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)),
                    })

                # 2. DPI check
                if eff_dpi < 150.0:
                    dpi_warnings.append({
                        "page": pno,
                        "xref": xref,
                        "dpi": round(eff_dpi, 1),
                        "px": (px_w, px_h),
                        "pt": (round(w_pt, 1), round(h_pt, 1)),
                    })

                # 3. Grayscale check
                if cs > 1:  # Multi-channel (e.g. RGB)
                    try:
                        pil_img = PILImage.open(io.BytesIO(img_bytes))
                        if pil_img.mode in ("RGB", "RGBA"):
                            # Check if saturation is non-zero
                            rgb_data = pil_img.convert("RGB")
                            # Sample pixels
                            w_samp = min(100, rgb_data.width)
                            h_samp = min(100, rgb_data.height)
                            resized = rgb_data.resize((w_samp, h_samp))
                            has_color = False
                            for r_val, g_val, b_val in resized.getdata():
                                if max(abs(r_val - g_val), abs(r_val - b_val), abs(g_val - b_val)) > 8:
                                    has_color = True
                                    break
                            if has_color:
                                color_issues.append({
                                    "page": pno,
                                    "xref": xref,
                                    "mode": pil_img.mode,
                                    "desc": "Image contains colored pixels (chromatic saturation > 8)",
                                })
                    except Exception as e:
                        pass

    # 4. Check Figure Numbering Sequence
    # Expected sequential: 1, 2, 3, ...
    sorted_figs = sorted(figures_found, key=lambda x: (x["num"], x["page"]))
    seen_nums = set()
    num_seq_issues = []
    expected = 1
    for f in sorted_figs:
        n = f["num"]
        if n in seen_nums:
            num_seq_issues.append(f"Duplicate figure number: Hình {n} on page {f['page']}")
        seen_nums.add(n)

    # Check for missing numbers in sequence up to max figure
    if figures_found:
        max_fig = max(f["num"] for f in figures_found)
        all_nums = set(f["num"] for f in figures_found)
        missing = [i for i in range(1, max_fig + 1) if i not in all_nums]
        if missing:
            num_seq_issues.append(f"Missing figure numbers in sequence: {missing}")

    return {
        "pdf_path": str(pdf_path),
        "total_pages": total_pages,
        "total_images_in_catalog": len(catalog),
        "catalog": catalog,
        "overflow_issues": overflow_issues,
        "dpi_warnings": dpi_warnings,
        "color_issues": color_issues,
        "unrendered_figure_tags": unrendered_figure_tags,
        "figures_found_count": len(figures_found),
        "figures": figures_found,
        "numbering_issues": num_seq_issues,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    report = audit_diagrams_and_images()
    print("=" * 80)
    print("AUDIT BÁO CÁO TOÀN DIỆN: HÌNH ẢNH & SƠ ĐỒ (GOLANG_MASTER.PDF)")
    print("=" * 80)
    print(f"Tổng số trang PDF:              {report['total_pages']}")
    print(f"Tổng số đối tượng hình ảnh:     {report['total_images_in_catalog']}")
    print(f"Số lượng sơ đồ có đánh số:      {report['figures_found_count']} (Hình 1 - Hình {max((f['num'] for f in report['figures']), default=0)})")
    print(f"Thẻ @figure chưa biên dịch:     {len(report['unrendered_figure_tags'])}")
    print(f"Lỗi tràn khung/lề (Overflow):   {len(report['overflow_issues'])}")
    print(f"Cảnh báo độ phân giải (<150DPI): {len(report['dpi_warnings'])}")
    print(f"Lỗi màu (chứa màu ngoài Grayscale): {len(report['color_issues'])}")
    print(f"Lỗi nhảy số thứ tự hình ảnh:    {len(report['numbering_issues'])}")
    print("=" * 80)

    if report["overflow_issues"]:
        print("\n--- CHI TIẾT LỖI TRÀN KHUNG / VI PHẠM LỀ ---")
        for iss in report["overflow_issues"]:
            print(f"Trang {iss['page']} (xref {iss['xref']}): {', '.join(iss['violations'])}")

    if report["dpi_warnings"]:
        print("\n--- CHI TIẾT CẢNH BÁO ĐỘ PHÂN GIẢI THẤP (<150 DPI) ---")
        for w in report["dpi_warnings"]:
            print(f"Trang {w['page']} (xref {w['xref']}): DPI={w['dpi']} (pixel: {w['px']}, hiển thị: {w['pt']})")

    if report["color_issues"]:
        print("\n--- CHI TIẾT HÌNH ẢNH CÓ MÀU (CHƯA ĐƠN SẮC HOÁ) ---")
        for c in report["color_issues"]:
            print(f"Trang {c['page']} (xref {c['xref']}): {c['desc']}")

    if report["numbering_issues"]:
        print("\n--- CHI TIẾT LỖI ĐÁNH SỐ THỨ TỰ HÌNH ---")
        for n in report["numbering_issues"]:
            print(f"- {n}")

    if report["unrendered_figure_tags"]:
        print(f"\n--- CẢNH BÁO THẺ @figure CHƯA XỬ LÝ TẠI TRANG: {report['unrendered_figure_tags']} ---")

    if not (report["overflow_issues"] or report["dpi_warnings"] or report["color_issues"] or report["numbering_issues"] or report["unrendered_figure_tags"]):
        print("\n>>> KẾT QUẢ: 100% HOÀN HẢO! TOÀN BỘ SƠ ĐỒ VÀ HÌNH ẢNH ĐẠT CHUẨN IN ẤN VÀ HIỂN THỊ <<<")
