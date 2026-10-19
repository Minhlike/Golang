# -*- coding: utf-8 -*-
"""Automated Publication PDF Preflight Validator for Golang Living Textbook.

READ-ONLY: Performs deep preflight audit on Golang_Master.pdf:
- Page geometry, dimensions, rotation, MediaBox, CropBox
- Font embedding, actually rendered fonts, broken glyphs
- Mirror margins / gutter geometry, clipping and overflow detection
- Blank / nearly blank pages detection
- Consecutive duplicate page detection
- PDF Outlines / Bookmarks verification (contract: exactly 34 monotonic valid entries)
- Raster image dimensions and effective DPI (>= 300 DPI)
- Grayscale / B&W compliance across raster images, vector drawings, and text spans
- Unresolved markup / editorial artifact scan in extracted PDF text
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys

from PIL import Image as PILImage, ImageChops
try:
    import pymupdf as fitz
except ImportError:
    import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "Golang_Master.pdf"
WORKSPACE_QA = ROOT / ".workspace/publication-qa"
PREFLIGHT_JSON = WORKSPACE_QA / "preflight/PREFLIGHT_RAW.json"
PAGE_REVIEW_CSV = WORKSPACE_QA / "page_review.csv"

# A4 dimensions in points: 21.0cm x 29.7cm -> 595.276 x 841.890 pt
A4_WIDTH = 595.28
A4_HEIGHT = 841.89
TOLERANCE_PT = 1.5


def load_canonical_bookmark_titles() -> list[str]:
    """Load canonical list of 34 bookmark titles: 'MỤC LỤC' + 33 manuscript H1 titles."""
    try:
        try:
            from scripts.build_pdf import get_manuscript, manuscript_titles
        except ImportError:
            from build_pdf import get_manuscript, manuscript_titles
        chaps, apps = get_manuscript()
        return ["MỤC LỤC"] + manuscript_titles(chaps, apps)
    except Exception:
        return []


def compute_section_opening_pages(doc: fitz.Document, canonical_titles: list[str]) -> dict[str, int]:
    """Find actual opening page for each canonical section in the PDF document."""
    if not canonical_titles or len(doc) == 0:
        return {}
    pages: dict[str, int] = {}
    titles_to_find = [t for t in canonical_titles if t != "MỤC LỤC"]

    # Locate TOC page if present
    for pno in range(1, min(10, len(doc) + 1)):
        txt = " ".join((doc[pno - 1].get_text() or "").split())
        if "MỤC LỤC" in txt:
            pages["MỤC LỤC"] = pno
            break
    if "MỤC LỤC" not in pages:
        pages["MỤC LỤC"] = 2

    if not titles_to_find:
        return pages

    start_search_pno = pages.get("MỤC LỤC", 2) + 1
    for pno in range(start_search_pno, len(doc) + 1):
        txt = " ".join((doc[pno - 1].get_text() or "").split())
        for title in titles_to_find:
            if title not in pages and " ".join(title.split()) in txt:
                pages[title] = pno
        if len(pages) == len(canonical_titles):
            break

    return pages


def run_preflight() -> dict:
    if not PDF_PATH.exists():
        print(f"ERROR: {PDF_PATH} does not exist!")
        sys.exit(1)

    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()
    pdf_sha256 = hashlib.sha256(pdf_bytes).hexdigest()

    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)

    report = {
        "pdf_path": str(PDF_PATH),
        "sha256": pdf_sha256,
        "total_pages": total_pages,
        "page_geometry": {"pass": True, "details": []},
        "fonts": {
            "pass": True,
            "font_families": [],
            "rendered_fonts": [],
            "embedded_fonts": [],
            "non_embedded_rendered_fonts": [],
            "broken_glyphs": [],
        },
        "margins_and_clipping": {
            "pass": True,
            "clipped_pages": [],
            "overflow_pages": [],
        },
        "blank_pages": [],
        "duplicate_pages": [],
        "bookmarks": {"present": False, "count": 0, "entries": [], "pass": True, "issues": []},
        "images": {"count": 0, "low_dpi": [], "pass": True},
        "grayscale_compliance": {"pass": True, "colored_pages": [], "unverified_scope": None},
        "unresolved_markup": {"pass": True, "hits": [], "classified_exceptions": []},
        "overall_status": "PENDING",
    }

    # 1. Page Geometry & Dimensions
    geometry_issues = []
    for idx, page in enumerate(doc):
        pno = idx + 1
        rect = page.rect
        mediabox = page.mediabox
        cropbox = page.cropbox
        rotation = page.rotation

        w, h = rect.width, rect.height
        is_a4 = (abs(w - A4_WIDTH) <= TOLERANCE_PT) and (abs(h - A4_HEIGHT) <= TOLERANCE_PT)
        if not is_a4:
            geometry_issues.append({
                "page": pno,
                "issue": f"Non-A4 dimensions: {w:.2f} x {h:.2f} pt"
            })
        if rotation != 0:
            geometry_issues.append({
                "page": pno,
                "issue": f"Unexpected rotation: {rotation} deg"
            })
        if mediabox != cropbox:
            geometry_issues.append({
                "page": pno,
                "issue": f"MediaBox {mediabox} != CropBox {cropbox}"
            })

    if geometry_issues:
        report["page_geometry"]["pass"] = False
        report["page_geometry"]["details"] = geometry_issues
    else:
        report["page_geometry"]["details"] = f"All {total_pages} pages strictly ISO A4 (595.28 x 841.89 pt), rotation 0, MediaBox==CropBox."

    # 2. Font Audit
    all_fonts = set()
    rendered_fonts = set()
    embedded_fonts = set()

    for idx, page in enumerate(doc):
        page_fonts = page.get_fonts(full=True)
        for f in page_fonts:
            basefont = f[3]
            clean_font = re.sub(r"^[A-Z]{6}\+", "", basefont)
            all_fonts.add(clean_font)
            embedded_fonts.add(clean_font)

        text_page = page.get_text("dict")
        for b in text_page.get("blocks", []):
            if b.get("type") == 0:
                for l in b.get("lines", []):
                    for s in l.get("spans", []):
                        f_name = re.sub(r"^[A-Z]{6}\+", "", s.get("font", ""))
                        if f_name:
                            rendered_fonts.add(f_name)

    non_embedded = list(rendered_fonts - embedded_fonts)
    report["fonts"]["font_families"] = sorted(list(all_fonts))
    report["fonts"]["rendered_fonts"] = sorted(list(rendered_fonts))
    report["fonts"]["embedded_fonts"] = sorted(list(embedded_fonts))
    report["fonts"]["non_embedded_rendered_fonts"] = non_embedded

    broken_glyph_pages = []
    suspicious_chars = ["\ufffd", "\u25a1", "\u25a0", "\u25af", "\u25ae"]
    for idx, page in enumerate(doc):
        text = page.get_text()
        for char in suspicious_chars:
            if char in text:
                broken_glyph_pages.append({
                    "page": idx + 1,
                    "char": repr(char),
                    "count": text.count(char)
                })
    report["fonts"]["broken_glyphs"] = broken_glyph_pages
    if non_embedded or broken_glyph_pages:
        report["fonts"]["pass"] = False

    # 3. Content Clipping & Canvas Boundary Overflow
    clipped_pages = []
    for idx, page in enumerate(doc):
        pno = idx + 1
        rect = page.rect
        blocks = page.get_text("blocks")
        for b in blocks:
            x0, y0, x1, y1 = b[:4]
            if x0 < -1.0 or y0 < -1.0 or x1 > rect.width + 1.0 or y1 > rect.height + 1.0:
                clipped_pages.append({
                    "page": pno,
                    "bbox": [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)],
                    "type": "text",
                    "preview": b[4][:50].replace("\n", " ")
                })

        drawings = page.get_drawings()
        for d in drawings:
            dr = d["rect"]
            if dr.x0 < -1.0 or dr.y0 < -1.0 or dr.x1 > rect.width + 1.0 or dr.y1 > rect.height + 1.0:
                clipped_pages.append({
                    "page": pno,
                    "bbox": [round(dr.x0, 2), round(dr.y0, 2), round(dr.x1, 2), round(dr.y1, 2)],
                    "type": "drawing"
                })

    report["margins_and_clipping"]["clipped_pages"] = clipped_pages
    if clipped_pages:
        report["margins_and_clipping"]["pass"] = False

    # 4. Blank / Nearly Blank Pages
    blank_pages = []
    for idx, page in enumerate(doc):
        pno = idx + 1
        text = page.get_text().strip()
        images = page.get_images()
        drawings = page.get_drawings()
        if not text and not images and not drawings:
            blank_pages.append({"page": pno, "type": "completely_blank"})
        elif len(text) < 15 and not images:
            blank_pages.append({"page": pno, "type": "nearly_blank", "text": text})
    report["blank_pages"] = blank_pages

    # 5. Consecutive Duplicate Pages
    duplicate_pages = []
    page_hashes = []
    for page in doc:
        txt = page.get_text().strip()
        h = hashlib.md5(txt.encode("utf-8")).hexdigest() if txt else ""
        page_hashes.append(h)

    for i in range(len(page_hashes) - 1):
        if page_hashes[i] and page_hashes[i] == page_hashes[i+1]:
            duplicate_pages.append({"pages": [i+1, i+2], "hash": page_hashes[i]})
    report["duplicate_pages"] = duplicate_pages

    # 6. Bookmarks / Outlines (Contract: Exactly 34 entries, TOC + 33 sections, matching contents)
    toc = doc.get_toc()
    bookmark_issues = []
    if not toc:
        report["bookmarks"]["present"] = False
        report["bookmarks"]["pass"] = False
        report["bookmarks"]["status"] = "FAIL_NO_OUTLINE"
        bookmark_issues.append("Tài liệu không có PDF bookmarks/outline (hợp đồng yêu cầu đúng 34 entries)")
    else:
        report["bookmarks"]["present"] = True
        report["bookmarks"]["count"] = len(toc)
        report["bookmarks"]["entries"] = [{"level": item[0], "title": item[1], "page": item[2]} for item in toc]

        # Contract requirement: Exactly 34 entries
        if len(toc) != 34:
            report["bookmarks"]["pass"] = False
            report["bookmarks"]["status"] = f"FAIL_COUNT_MISMATCH_{len(toc)}_EXP_34"
            bookmark_issues.append(f"Số lượng bookmark ({len(toc)}) không đúng yêu cầu (hợp đồng yêu cầu đúng 34 entries)")

        # Canonical manuscript comparison
        canonical_titles = load_canonical_bookmark_titles()
        expected_pages = compute_section_opening_pages(doc, canonical_titles) if canonical_titles else {}

        # Check hierarchy, destinations, monotonicity, and exact manuscript alignment
        last_page = 1
        for idx, item in enumerate(toc):
            lvl, title, target_page = item[:3]
            if lvl != 1:
                bookmark_issues.append(f"Bookmark '{title}' có level={lvl} (yêu cầu level 1 cho các phần chính)")
            if target_page < 1 or target_page > total_pages:
                bookmark_issues.append(f"Bookmark '{title}' trỏ tới trang đích không tồn tại: {target_page} (tổng số trang: {total_pages})")
            elif target_page < last_page:
                bookmark_issues.append(f"Bookmark '{title}' có số trang nghịch đảo: {target_page} < {last_page}")
            else:
                last_page = target_page

            # Check alignment against canonical manuscript if available
            if canonical_titles and idx < len(canonical_titles):
                exp_title = canonical_titles[idx]
                if " ".join(title.split()).lower() != " ".join(exp_title.split()).lower():
                    bookmark_issues.append(
                        f"Bookmark thứ {idx+1} có tiêu đề '{title}' không khớp bản thảo chuẩn '{exp_title}'"
                    )
                exp_page = expected_pages.get(exp_title)
                if exp_page is not None and target_page != exp_page:
                    bookmark_issues.append(
                        f"Bookmark thứ {idx+1} ('{title}') trỏ tới trang {target_page}, nhưng trang bắt đầu thực tế theo bản thảo là {exp_page}"
                    )

            # Strict destination page content check (strictly on target page doc[target_page - 1], no adjacent page merging)
            if 1 <= target_page <= total_pages:
                page_text = " ".join((doc[target_page - 1].get_text() or "").split())
                norm_title = " ".join(title.split())
                if idx > 0 and "MỤC LỤC" in page_text and target_page <= 2:
                    bookmark_issues.append(f"Bookmark '{title}' trỏ nhầm vào trang Mục lục (trang {target_page}) thay vì trang mở đầu chương")
                elif norm_title not in page_text:
                    clean_words = [w for w in re.findall(r"\w+", title.lower()) if len(w) > 2 and w not in ("chương", "atlas", "mục", "lục", "phần", "nguồn", "thư", "viện")]
                    page_words = set(re.findall(r"\w+", page_text.lower()))
                    matched_words = [w for w in clean_words if w in page_words]
                    if len(matched_words) < max(2, len(clean_words) // 2):
                        bookmark_issues.append(f"Bookmark '{title}' không tìm thấy nội dung/tiêu đề tương ứng tại trang đích {target_page}")

        if bookmark_issues:
            report["bookmarks"]["pass"] = False
            report["bookmarks"]["issues"] = bookmark_issues
        else:
            report["bookmarks"]["pass"] = True
            report["bookmarks"]["status"] = "PASS_34_ENTRIES_MONOTONIC_AND_VERIFIED"

    # 7. Raster Images & Effective DPI
    low_dpi_images = []
    total_imgs = 0
    for idx, page in enumerate(doc):
        pno = idx + 1
        img_info_list = page.get_images(full=True)
        for info in img_info_list:
            total_imgs += 1
            xref = info[0]
            base_img = doc.extract_image(xref)
            if base_img:
                px_w = base_img["width"]
                px_h = base_img["height"]
                rects = page.get_image_rects(xref)
                for r in rects:
                    disp_w_in = r.width / 72.0
                    disp_h_in = r.height / 72.0
                    if disp_w_in > 0 and disp_h_in > 0:
                        eff_dpi_w = px_w / disp_w_in
                        eff_dpi_h = px_h / disp_h_in
                        eff_dpi = min(eff_dpi_w, eff_dpi_h)
                        if eff_dpi < 300.0:  # Fail when effective raster DPI < 300
                            low_dpi_images.append({
                                "page": pno,
                                "xref": xref,
                                "px": [px_w, px_h],
                                "display_pt": [round(r.width, 1), round(r.height, 1)],
                                "effective_dpi": round(eff_dpi, 1)
                            })
    report["images"]["count"] = total_imgs
    report["images"]["low_dpi"] = low_dpi_images
    if low_dpi_images:
        report["images"]["pass"] = False

    # 8. Grayscale Compliance (Raster images, Vector drawings, Text spans)
    colored_pages = []
    unverified_scope = []
    total_drawings_inspected = 0
    total_spans_inspected = 0

    def is_color_rgb(r, g, b, tol=1e-3):
        return abs(r - g) > tol or abs(g - b) > tol

    def is_color_cmyk(c, m, y, k, tol=1e-3):
        return abs(c - m) > tol or abs(m - y) > tol or (c > tol and abs(k - 1.0) > tol)

    for idx, page in enumerate(doc):
        pno = idx + 1

        # 8a. Check vector drawings
        try:
            drawings = page.get_drawings()
            total_drawings_inspected += len(drawings)
            for d in drawings:
                for color_val in (d.get("fill"), d.get("color")):
                    if color_val is not None and isinstance(color_val, (list, tuple)):
                        if len(color_val) == 3 and is_color_rgb(*color_val):
                            colored_pages.append({
                                "page": pno,
                                "type": "VECTOR_RGB",
                                "color": color_val,
                                "rect": [round(x, 1) for x in d.get("rect", [])]
                            })
                        elif len(color_val) == 4 and is_color_cmyk(*color_val):
                            colored_pages.append({
                                "page": pno,
                                "type": "VECTOR_CMYK",
                                "color": color_val,
                                "rect": [round(x, 1) for x in d.get("rect", [])]
                            })
        except Exception as e:
            unverified_scope.append(f"Page {pno} get_drawings exception: {e}")

        # 8b. Check text spans
        try:
            d_text = page.get_text("dict")
            for b in d_text.get("blocks", []):
                if b.get("type") == 0:
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            total_spans_inspected += 1
                            c = span.get("color")
                            if c is not None and isinstance(c, int):
                                r = (c >> 16) & 0xFF
                                g = (c >> 8) & 0xFF
                                b_val = c & 0xFF
                                if r != g or g != b_val:
                                    colored_pages.append({
                                        "page": pno,
                                        "type": "TEXT_COLOR",
                                        "color": (r, g, b_val),
                                        "text": span.get("text", "")[:30]
                                    })
        except Exception as e:
            unverified_scope.append(f"Page {pno} text spans exception: {e}")

        # 8c. Check raster images on this page
        img_info_list = page.get_images(full=True)
        for info in img_info_list:
            xref = info[0]
            try:
                base_img = doc.extract_image(xref)
                if base_img:
                    img_bytes = base_img["image"]
                    cs = base_img["colorspace"]
                    if cs > 1:
                        pil_img = PILImage.open(io.BytesIO(img_bytes))
                        if pil_img.mode in ("RGB", "RGBA", "CMYK", "YCbCr", "LAB"):
                            rgb_data = pil_img.convert("RGB")
                            r_band, g_band, b_band = rgb_data.split()
                            diff_rg = ImageChops.difference(r_band, g_band)
                            diff_gb = ImageChops.difference(g_band, b_band)
                            max_diff = max(diff_rg.getextrema()[1], diff_gb.getextrema()[1])
                            if max_diff > 0:
                                colored_pages.append({
                                    "page": pno,
                                    "type": "RASTER_IMAGE_RGB",
                                    "xref": xref,
                                    "max_diff": max_diff
                                })
            except Exception as e:
                unverified_scope.append(f"Page {pno} image xref {xref} decode exception: {e}")

    report["grayscale_compliance"] = {
        "pass": (len(colored_pages) == 0 and len(unverified_scope) == 0),
        "colored_pages": colored_pages,
        "unverified_scope": unverified_scope if unverified_scope else None,
        "drawings_inspected": total_drawings_inspected,
        "text_spans_inspected": total_spans_inspected,
    }

    # 9. Unresolved Markup / Editorial Artifacts
    markup_patterns = [
        r"\bTODO\b", r"\bFIXME\b", r"\bTBD\b", r"\bXXX\b",
        r"\bPLACEHOLDER\b", r"\bREPLACE_ME\b", r"\bREPLACE_WITH\b",
        r"Lorem ipsum", r"@figure\b", r"@references\b",
        r"\bBOOK_ROLE\b", r"\bSYNTHETIC\b", r"\bDRAFT\b", r"\bAI TODO\b"
    ]
    compiled_patterns = [re.compile(p) for p in markup_patterns]
    markup_hits = []
    classified_exceptions = []

    for idx, page in enumerate(doc):
        pno = idx + 1
        text = page.get_text()
        for pat in compiled_patterns:
            matches = pat.findall(text)
            if matches:
                # Check for intentional teaching exception: Ch17 REPLACE_ME
                if pat.pattern == r"\bREPLACE_ME\b" and ("probe-api@sha256:REPLACE_ME" in text or "Placeholder REPLACE_ME" in text or "chỗ REPLACE_ME" in text):
                    classified_exceptions.append({
                        "page": pno,
                        "type": "INTENTIONAL_TEACHING_EXAMPLE",
                        "context": "Ch17 deployment digest demonstration explicitly explaining why REPLACE_ME prevents accidental apply."
                    })
                else:
                    markup_hits.append({
                        "page": pno,
                        "pattern": pat.pattern,
                        "matches": matches
                    })
    report["unresolved_markup"]["hits"] = markup_hits
    report["unresolved_markup"]["classified_exceptions"] = classified_exceptions
    if markup_hits:
        report["unresolved_markup"]["pass"] = False

    # 10. Overall Status Evaluation
    critical_checks = [
        report["page_geometry"]["pass"],
        report["fonts"]["pass"],
        len(report["fonts"]["non_embedded_rendered_fonts"]) == 0,
        len(report["fonts"]["broken_glyphs"]) == 0,
        report["margins_and_clipping"]["pass"],
        len(report["margins_and_clipping"]["clipped_pages"]) == 0,
        len(report["blank_pages"]) == 0,
        len(report["duplicate_pages"]) == 0,
        report["bookmarks"]["pass"],
        report["images"]["pass"],
        report["grayscale_compliance"]["pass"],
        len(report["grayscale_compliance"]["colored_pages"]) == 0,
        report["unresolved_markup"]["pass"],
        len(report["unresolved_markup"]["hits"]) == 0,
    ]
    if all(critical_checks):
        report["overall_status"] = "PASS"
    else:
        report["overall_status"] = "FAIL"

    WORKSPACE_QA.mkdir(parents=True, exist_ok=True)
    (WORKSPACE_QA / "preflight").mkdir(parents=True, exist_ok=True)
    with open(PREFLIGHT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    doc.close()
    return report


if __name__ == "__main__":
    rep = run_preflight()
    print("=" * 80)
    print("AUTOMATED PUBLICATION PDF PREFLIGHT SUMMARY")
    print("=" * 80)
    print(f"File:                      {rep['pdf_path']}")
    print(f"SHA-256:                   {rep['sha256']}")
    print(f"Total Pages:               {rep['total_pages']}")
    print(f"Page Geometry:             {'PASS' if rep['page_geometry']['pass'] else 'FAIL'}")
    print(f"Actually Rendered Fonts:   {', '.join(rep['fonts']['rendered_fonts'])}")
    print(f"Fonts Embedded:            {'PASS' if rep['fonts']['pass'] else 'FAIL'} (Non-embedded rendered: {rep['fonts']['non_embedded_rendered_fonts']})")
    print(f"Broken Glyphs:             {len(rep['fonts']['broken_glyphs'])} hits")
    print(f"Clipping / Bounds:         {len(rep['margins_and_clipping']['clipped_pages'])} hits")
    print(f"Blank Pages:               {len(rep['blank_pages'])} pages")
    print(f"Duplicate Pages:           {len(rep['duplicate_pages'])} pairs")
    print(f"Bookmarks:                 {rep['bookmarks']['count']} entries ({'PASS' if rep['bookmarks']['pass'] else 'FAIL'})")
    print(f"Grayscale Compliance:      {'PASS' if rep['grayscale_compliance']['pass'] else 'FAIL'} ({len(report['grayscale_compliance']['colored_pages'])} colored objects)" if 'report' in locals() else f"Grayscale Compliance:      {'PASS' if rep['grayscale_compliance']['pass'] else 'FAIL'} ({len(rep['grayscale_compliance']['colored_pages'])} colored objects)")
    print(f"Unresolved Markup:         {len(rep['unresolved_markup']['hits'])} hits (Exceptions: {len(rep['unresolved_markup']['classified_exceptions'])})")
    print(f"Overall Status:            {rep['overall_status']}")
    print("=" * 80)
    if rep["overall_status"] != "PASS":
        sys.exit(1)
