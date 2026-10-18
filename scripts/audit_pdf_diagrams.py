# -*- coding: utf-8 -*-
"""Comprehensive Visual & Layout Preflight Auditor for Diagrams and Images in Golang_Master.pdf.

Audits:
1. Catalog: Every image occurrence across all pages, dimensions, format, colorspace.
2. Geometry & Bounds: Overflow across printable width (168mm / 476.2pt) or margins.
3. Effective DPI: Detect images with resolution < 150 DPI or < 300 DPI.
4. Color Compliance: Check if any image contains RGB chrominance (saturation > 0) in a grayscale book.
5. Captions & Numbering: Check sequence of "Hình X — ...", orphaned captions, and "@figure" tags.
6. Figure-Text Proximity: Verify caption is directly below the figure on the same page.
7. Robust 1:1 Pairing: Bipartite matching between image placements and caption blocks,
   verifying reading order, distance thresholds, and detecting ambiguous placements.
8. Semantic Correspondence: Cross-reference captions against manuscript source metadata.
"""

from __future__ import annotations

import io
import math
from pathlib import Path
import re
import sys

from PIL import Image as PILImage, ImageChops
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

MAX_CAPTION_GAP = 70.0  # Max vertical distance (pt) from image bottom to caption top


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


def load_manuscript_figures() -> dict[int, dict]:
    """Extract canonical list of figures and captions from manuscript markdown files."""
    chapters_dir = ROOT / "book/chapters"
    appendices_dir = ROOT / "book/appendices"
    if not chapters_dir.exists():
        return {}
    chapters = sorted(chapters_dir.glob("*.md"), key=chapter_sort_key)
    other_appendices = [
        p for p in sorted(appendices_dir.glob("*.md"))
        if p.name != "error-atlas.md"
    ] if appendices_dir.exists() else []
    error_atlas = [appendices_dir / "error-atlas.md"] if (appendices_dir / "error-atlas.md").exists() else []
    all_files = chapters + other_appendices + error_atlas

    fig_map = {}
    fig_idx = 0
    img_regex = re.compile(r"!\[[^]]*\]\(([^)]+)\)")
    for md_file in all_files:
        try:
            lines = md_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines):
            img_m = img_regex.fullmatch(line.strip())
            if img_m:
                for j in range(i + 1, min(i + 6, len(lines))):
                    if lines[j].strip().startswith("@figure "):
                        fig_idx += 1
                        cap_text = lines[j].strip()[8:].strip()
                        fig_map[fig_idx] = {
                            "num": fig_idx,
                            "file": md_file.name,
                            "image_rel": img_m.group(1),
                            "caption": cap_text,
                        }
                        break
    return fig_map


def audit_diagrams_and_images(pdf_path: Path = PDF_PATH) -> dict:
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    catalog = []
    overflow_issues = []
    dpi_warnings = []
    color_issues = []
    unrendered_figure_tags = []
    decoding_issues = []
    pairing_issues = []
    position_issues = []
    order_issues = []
    semantic_issues = []

    # Regex for figure captions in text blocks
    caption_block_regex = re.compile(r"^\s*H[iì]nh\s+(\d+)\s*[—–-]\s*([^\n]+)", re.MULTILINE)
    unrendered_figure_regex = re.compile(r"@figure\b")

    figures_found = []  # list of (page, figure_num, caption_text, bbox)
    expected_fig_num = 1
    last_fig_page = 1

    for pno in range(1, total_pages + 1):
        page = doc[pno - 1]
        text = page.get_text()

        # Check for unrendered @figure tags in text
        if unrendered_figure_regex.search(text):
            unrendered_figure_tags.append(pno)

        # Mirrored margins for current page
        is_recto = (pno % 2 != 0)
        left_margin = MARGIN_GUTTER if is_recto else MARGIN_OUTSIDE
        right_margin = PAGE_W - (MARGIN_OUTSIDE if is_recto else MARGIN_GUTTER)
        top_margin = MARGIN_TOP
        bottom_margin = PAGE_H - MARGIN_BOTTOM

        # 1. Collect all actual image occurrences (placements) on current page
        img_occurrences = []
        raw_img_info = page.get_image_info(xrefs=True)
        if raw_img_info:
            for item in raw_img_info:
                bbox = fitz.Rect(item["bbox"])
                if bbox.width < 10.0 or bbox.height < 10.0:
                    continue
                img_occurrences.append({
                    "xref": item.get("xref", 0),
                    "bbox": bbox,
                    "width": item.get("width", 0),
                    "height": item.get("height", 0),
                    "cs": item.get("cs-name", ""),
                })
        else:
            # Fallback for synthetic/in-memory PDFs where get_image_info might return empty
            for img_entry in page.get_images(full=True):
                xref = img_entry[0]
                for r in page.get_image_rects(xref):
                    if r.width < 10.0 or r.height < 10.0:
                        continue
                    img_occurrences.append({
                        "xref": xref,
                        "bbox": r,
                        "width": 0,
                        "height": 0,
                        "cs": "",
                    })

        # Sort images by vertical reading order (top-to-bottom, left-to-right)
        img_occurrences.sort(key=lambda x: (round(x["bbox"].y0, 1), round(x["bbox"].x0, 1)))

        # 2. Extract figure captions strictly from text blocks starting with "Hình N —"
        page_captions = []
        blocks = page.get_text("blocks")
        for b in blocks:
            if b[6] == 0:  # text block
                txt = b[4].strip()
                m = caption_block_regex.match(txt)
                if m:
                    f_num = int(m.group(1))
                    f_title = m.group(2).strip()
                    c_bbox = fitz.Rect(b[:4])
                    item_cap = {
                        "page": pno,
                        "num": f_num,
                        "title": f_title,
                        "bbox": c_bbox,
                    }
                    figures_found.append(item_cap)
                    page_captions.append(item_cap)

                    # Global Monotonic order check
                    if f_num != expected_fig_num:
                        order_issues.append(
                            f"Caption numbering out of sequence on page {pno}: found Hình {f_num}, expected Hình {expected_fig_num}"
                        )
                    if pno < last_fig_page:
                        order_issues.append(
                            f"Caption page order non-monotonic: Hình {f_num} on page {pno} appears after page {last_fig_page}"
                        )
                    expected_fig_num = f_num + 1
                    last_fig_page = pno

        # Sort captions by vertical reading order
        page_captions.sort(key=lambda c: (round(c["bbox"].y0, 1), round(c["bbox"].x0, 1)))

        # 3. Robust 1:1 Image-Caption Pairing on interior pages
        if pno > 1:
            num_imgs = len(img_occurrences)
            num_caps = len(page_captions)

            if num_imgs != num_caps:
                if num_imgs > num_caps:
                    pairing_issues.append({
                        "page": pno,
                        "images": num_imgs,
                        "captions": num_caps,
                        "desc": f"Trang {pno} có {num_imgs} hình ảnh nhưng chỉ có {num_caps} chú thích (thiếu chú thích cho hình)",
                    })
                else:
                    pairing_issues.append({
                        "page": pno,
                        "images": num_imgs,
                        "captions": num_caps,
                        "desc": f"Trang {pno} có {num_caps} chú thích nhưng chỉ có {num_imgs} hình ảnh (chú thích mồ côi không có hình)",
                    })

            # Ambiguity check: images side-by-side at roughly identical vertical positions
            if num_imgs >= 2:
                for i in range(num_imgs - 1):
                    if abs(img_occurrences[i]["bbox"].y0 - img_occurrences[i + 1]["bbox"].y0) < 15.0:
                        pairing_issues.append({
                            "page": pno,
                            "desc": f"Trang {pno} chứa nhiều hình ảnh ở cùng cao độ (AMBIGUOUS_PAIRING: không phân biệt được đối ứng 1:1 theo thứ tự đọc)",
                        })
                        break

            # Pair each image with its corresponding caption by reading order
            for k in range(min(num_imgs, num_caps)):
                img = img_occurrences[k]
                cap = page_captions[k]
                ib = img["bbox"]
                cb = cap["bbox"]

                # Vertical position check: caption must be below image
                if cb.y0 < (ib.y1 - 10.0):
                    position_issues.append({
                        "page": pno,
                        "num": cap["num"],
                        "img_bottom": round(ib.y1, 1),
                        "cap_top": round(cb.y0, 1),
                        "desc": f"Chú thích Hình {cap['num']} (y0={cb.y0:.1f}pt) nằm phía trên hoặc đè lên hình ảnh (y1={ib.y1:.1f}pt)",
                    })
                elif (cb.y0 - ib.y1) > MAX_CAPTION_GAP:
                    position_issues.append({
                        "page": pno,
                        "num": cap["num"],
                        "img_bottom": round(ib.y1, 1),
                        "cap_top": round(cb.y0, 1),
                        "gap": round(cb.y0 - ib.y1, 1),
                        "desc": f"Chú thích Hình {cap['num']} nằm quá xa hình ảnh (khoảng cách {cb.y0 - ib.y1:.1f}pt > {MAX_CAPTION_GAP}pt)",
                    })

                # Sequence check across multiple pairs on same page
                if k < min(num_imgs, num_caps) - 1:
                    next_img = img_occurrences[k + 1]
                    next_cap = page_captions[k + 1]
                    if cb.y0 > next_img["bbox"].y1:
                        order_issues.append(
                            f"Trang {pno}: Thứ tự chú thích đảo ngược (Hình {cap['num']} nằm bên dưới hình kế tiếp)"
                        )
                    if cap["num"] >= next_cap["num"]:
                        order_issues.append(
                            f"Trang {pno}: Thứ tự đánh số chú thích không tăng dần (Hình {cap['num']} đứng trước Hình {next_cap['num']})"
                        )

        # 4. Detailed image stream checks (catalog, DPI, colorspace, decoding, bounds)
        images = page.get_images(full=True)
        for img_info in images:
            xref = img_info[0]
            try:
                base = doc.extract_image(xref)
                if not base:
                    decoding_issues.append({
                        "page": pno,
                        "xref": xref,
                        "desc": f"Không thể giải mã/trích xuất luồng ảnh xref {xref} tại trang {pno}",
                    })
                    continue
            except Exception as e:
                decoding_issues.append({
                    "page": pno,
                    "xref": xref,
                    "desc": f"Lỗi giải mã ảnh xref {xref} tại trang {pno}: {e}",
                })
                continue

            px_w = base["width"]
            px_h = base["height"]
            cs = base["colorspace"]
            img_bytes = base["image"]

            rects = page.get_image_rects(xref)
            for r in rects:
                w_pt = r.width
                h_pt = r.height

                # Page 1 is official front cover
                if pno == 1:
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

                # Bounds check (tolerance 2.0 pt)
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

                # DPI check: fail when effective raster DPI < 300.0 (preferred >= 320.0)
                if eff_dpi < 300.0:
                    dpi_warnings.append({
                        "page": pno,
                        "xref": xref,
                        "dpi": round(eff_dpi, 1),
                        "px": (px_w, px_h),
                        "pt": (round(w_pt, 1), round(h_pt, 1)),
                        "error": f"DPI {eff_dpi:.1f} < 300.0 (preferred >= 320.0)",
                    })

                # Grayscale check & decoding check: fail when ANY pixel violates R == G == B (zero tolerance)
                try:
                    pil_img = PILImage.open(io.BytesIO(img_bytes))
                    if cs > 1 and pil_img.mode in ("RGB", "RGBA", "CMYK", "YCbCr", "LAB"):
                        rgb_data = pil_img.convert("RGB")
                        r_band, g_band, b_band = rgb_data.split()
                        diff_rg = ImageChops.difference(r_band, g_band)
                        diff_gb = ImageChops.difference(g_band, b_band)
                        max_diff = max(diff_rg.getextrema()[1], diff_gb.getextrema()[1])
                        if max_diff > 0:
                            color_issues.append({
                                "page": pno,
                                "xref": xref,
                                "mode": pil_img.mode,
                                "max_diff": max_diff,
                                "desc": f"Image contains colored pixels (R!=G!=B, max diff={max_diff})",
                            })
                except Exception as e:
                    decoding_issues.append({
                        "page": pno,
                        "xref": xref,
                        "desc": f"Lỗi đọc dữ liệu pixel ảnh xref {xref} tại trang {pno}: {e}",
                    })

    # 5. Check Figure Numbering Sequence
    sorted_figs = sorted(figures_found, key=lambda x: (x["num"], x["page"]))
    seen_nums = set()
    num_seq_issues = []
    for f in sorted_figs:
        n = f["num"]
        if n in seen_nums:
            num_seq_issues.append(f"Duplicate figure number: Hình {n} on page {f['page']}")
        seen_nums.add(n)

    if figures_found:
        max_fig = max(f["num"] for f in figures_found)
        all_nums = set(f["num"] for f in figures_found)
        missing = [i for i in range(1, max_fig + 1) if i not in all_nums]
        if missing:
            num_seq_issues.append(f"Missing figure numbers in sequence: {missing}")

    # 6. Semantic verification against manuscript
    ms_figures = load_manuscript_figures()
    if ms_figures and len(figures_found) == len(ms_figures):
        for cap in figures_found:
            f_num = cap["num"]
            if f_num in ms_figures:
                exp = ms_figures[f_num]
                cap_words = set(re.findall(r"\w+", cap["title"].lower()))
                exp_words = set(re.findall(r"\w+", exp["caption"].lower()))
                common = cap_words.intersection(exp_words)
                if len(exp_words) > 3 and len(common) < 2:
                    semantic_issues.append({
                        "num": f_num,
                        "found_title": cap["title"],
                        "expected_caption": exp["caption"],
                        "desc": f"Hình {f_num} có tiêu đề không khớp ngữ nghĩa bản thảo: '{cap['title']}' != '{exp['caption']}'",
                    })

    doc.close()

    return {
        "pdf_path": str(pdf_path),
        "total_pages": total_pages,
        "total_images_in_catalog": len(catalog),
        "catalog": catalog,
        "overflow_issues": overflow_issues,
        "dpi_issues": dpi_warnings,
        "dpi_warnings": dpi_warnings,
        "color_issues": color_issues,
        "unrendered_figure_tags": unrendered_figure_tags,
        "decoding_issues": decoding_issues,
        "pairing_issues": pairing_issues,
        "position_issues": position_issues,
        "order_issues": order_issues,
        "semantic_issues": semantic_issues,
        "figures_found_count": len(figures_found),
        "figures": figures_found,
        "numbering_issues": num_seq_issues,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    target_pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_PATH
    report = audit_diagrams_and_images(target_pdf)
    print("=" * 80)
    print(f"AUDIT BÁO CÁO TOÀN DIỆN: HÌNH ẢNH & SƠ ĐỒ ({target_pdf.name.upper()})")
    print("=" * 80)
    print(f"Tổng số trang PDF:              {report['total_pages']}")
    print(f"Tổng số đối tượng hình ảnh:     {report['total_images_in_catalog']}")
    print(f"Số lượng sơ đồ có đánh số:      {report['figures_found_count']} (Hình 1 - Hình {max((f['num'] for f in report['figures']), default=0)})")
    print(f"Thẻ @figure chưa biên dịch:     {len(report['unrendered_figure_tags'])}")
    print(f"Lỗi tràn khung/lề (Overflow):   {len(report['overflow_issues'])}")
    print(f"Lỗi độ phân giải (<300 DPI):    {len(report['dpi_issues'])}")
    print(f"Lỗi màu (chứa pixel R!=G!=B):   {len(report['color_issues'])}")
    print(f"Lỗi giải mã ảnh (Decoding):     {len(report['decoding_issues'])}")
    print(f"Lỗi ghép cặp 1:1 hình-caption:  {len(report['pairing_issues'])}")
    print(f"Lỗi vị trí hình-caption:        {len(report['position_issues'])}")
    print(f"Lỗi thứ tự trang caption:       {len(report['order_issues'])}")
    print(f"Lỗi ngữ nghĩa (Semantic):       {len(report['semantic_issues'])}")
    print(f"Lỗi nhảy số thứ tự hình ảnh:    {len(report['numbering_issues'])}")
    print("=" * 80)

    if report["overflow_issues"]:
        print("\n--- CHI TIẾT LỖI TRÀN KHUNG / VI PHẠM LỀ ---")
        for iss in report["overflow_issues"]:
            print(f"Trang {iss['page']} (xref {iss['xref']}): {', '.join(iss['violations'])}")

    if report["dpi_issues"]:
        print("\n--- CHI TIẾT LỖI ĐỘ PHÂN GIẢI THẤP (<300 DPI) ---")
        for w in report["dpi_issues"]:
            print(f"Trang {w['page']} (xref {w['xref']}): DPI={w['dpi']} (pixel: {w['px']}, hiển thị: {w['pt']})")

    if report["color_issues"]:
        print("\n--- CHI TIẾT HÌNH ẢNH CÓ MÀU (R!=G!=B) ---")
        for c in report["color_issues"]:
            print(f"Trang {c['page']} (xref {c['xref']}): {c['desc']}")

    if report["decoding_issues"]:
        print("\n--- CHI TIẾT LỖI GIẢI MÃ ẢNH ---")
        for d in report["decoding_issues"]:
            print(f"Trang {d['page']} (xref {d['xref']}): {d['desc']}")

    if report["pairing_issues"]:
        print("\n--- CHI TIẾT LỖI GHÉP CẶP 1:1 HÌNH - CHÚ THÍCH ---")
        for p in report["pairing_issues"]:
            print(f"- {p['desc']}")

    if report["position_issues"]:
        print("\n--- CHI TIẾT LỖI VỊ TRÍ HÌNH - CHÚ THÍCH ---")
        for pos in report["position_issues"]:
            print(f"- {pos['desc']}")

    if report["order_issues"]:
        print("\n--- CHI TIẾT LỖI THỨ TỰ TRANG CHÚ THÍCH ---")
        for o in report["order_issues"]:
            print(f"- {o}")

    if report["semantic_issues"]:
        print("\n--- CHI TIẾT LỖI KHÔNG KHỚP NGỮ NGHĨA CHÚ THÍCH ---")
        for sem in report["semantic_issues"]:
            print(f"- {sem['desc']}")

    if report["numbering_issues"]:
        print("\n--- CHI TIẾT LỖI ĐÁNH SỐ THỨ TỰ HÌNH ---")
        for n in report["numbering_issues"]:
            print(f"- {n}")

    if report["unrendered_figure_tags"]:
        print(f"\n--- CẢNH BÁO THẺ @figure CHƯA XỬ LÝ TẠI TRANG: {report['unrendered_figure_tags']} ---")

    has_errors = bool(
        report["overflow_issues"]
        or report["dpi_issues"]
        or report["color_issues"]
        or report["numbering_issues"]
        or report["unrendered_figure_tags"]
        or report["decoding_issues"]
        or report["pairing_issues"]
        or report["position_issues"]
        or report["order_issues"]
        or report["semantic_issues"]
    )
    if not has_errors:
        print("\n>>> KẾT QUẢ: 100% HOÀN HẢO! TOÀN BỘ SƠ ĐỒ VÀ HÌNH ẢNH ĐẠT CHUẨN IN ẤN VÀ HIỂN THỊ <<<")
    else:
        sys.exit(1)
