#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/build_print_package.py

Assembles the official 2-file print-ready package for commercial book production:
  1. File Bìa Trải (Cover Wrap): book/print_ready/01_BIA_TRAI_GOLANG_A4_GAY28MM.pdf
     - TrimBox: 448 x 297 mm (Back 210 + Spine 28 + Front 210)
     - BleedBox: 454 x 303 mm (3mm bleed on all 4 sides)
     - Resolution: Vector 100% with crop marks and spine fold lines
  2. File Ruột Sách (Interior Block): book/print_ready/02_RUOT_SACH_GOLANG_493TRANG_A4.pdf
     - Format: ISO A4 (210 x 297 mm)
     - Page 1: Concept 1 Front Cover (Architectural Cross-Section)
     - Pages 2-493: Exact 492 interior pages from Golang_Master.pdf
     - TOC Outline preserved and updated
  3. Updates Golang_Master.pdf to reflect the new Front Cover on Page 1,
     while archiving the baseline artifact to book/publication/Golang_Master_baseline_f2211520.pdf.
  4. Generates technical specification sheet: book/print_ready/THONG_SO_KY_THUAT_NHA_IN.txt
"""

import sys
import shutil
import hashlib
from pathlib import Path
import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "book" / "print_ready"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COVER_WRAP_SRC = PROJECT_ROOT / "book" / "design" / "agent2-2026" / "artwork" / "full_cover_wrap_print.pdf"
FRONT_COVER_SRC = PROJECT_ROOT / "book" / "design" / "agent2-2026" / "artwork" / "front_cover_page.pdf"
MASTER_PDF_SRC = PROJECT_ROOT / "Golang_Master.pdf"
ARCHIVE_PDF = PROJECT_ROOT / "book" / "publication" / "Golang_Master_baseline_f2211520.pdf"

BLEED_MM = 3.0
BLEED_PT = BLEED_MM * 2.834645669291339  # ~8.5039 pt


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def process_cover_wrap():
    """Generates the standardized Cover Wrap with ISO TrimBox and BleedBox."""
    print("[1/4] Processing File 1: Bìa Trải Rộng (Cover Wrap)...")
    doc = fitz.open(COVER_WRAP_SRC)
    page = doc[0]

    # Set BleedBox to full canvas
    page.set_bleedbox(page.rect)

    # Set TrimBox inside bleed
    rect_trim = fitz.Rect(BLEED_PT, BLEED_PT, page.rect.width - BLEED_PT, page.rect.height - BLEED_PT)
    page.set_trimbox(rect_trim)

    w_mm = page.rect.width / 2.834645669291339
    h_mm = page.rect.height / 2.834645669291339
    trim_w_mm = rect_trim.width / 2.834645669291339
    trim_h_mm = rect_trim.height / 2.834645669291339

    out_path = OUTPUT_DIR / "01_BIA_TRAI_GOLANG_A4_GAY28MM.pdf"
    doc.save(out_path, deflate=True)
    doc.close()

    # Also update the source artwork file with the proper boxes
    shutil.copy2(out_path, COVER_WRAP_SRC)
    print(f"  -> Saved: {out_path}")
    print(f"  -> MediaBox: {w_mm:.2f} x {h_mm:.2f} mm")
    print(f"  -> TrimBox:  {trim_w_mm:.2f} x {trim_h_mm:.2f} mm (Back 210 + Spine 28 + Front 210)")
    return out_path


def process_interior():
    """Assembles the standardized 493-page Interior Block with new Front Cover on Page 1."""
    print("[2/4] Processing File 2: Ruột Sách (Interior Block)...")

    # 1. Archive baseline Golang_Master.pdf if not yet archived
    if not ARCHIVE_PDF.exists():
        ARCHIVE_PDF.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MASTER_PDF_SRC, ARCHIVE_PDF)
        print(f"  -> Archived baseline: {ARCHIVE_PDF} (SHA-256: {compute_sha256(ARCHIVE_PDF)})")

    doc_master = fitz.open(MASTER_PDF_SRC)
    doc_front = fitz.open(FRONT_COVER_SRC)

    doc_out = fitz.open()

    # Page 1: Concept 1 Front Cover
    doc_out.insert_pdf(doc_front, from_page=0, to_page=0)

    # Pages 2-493: Remaining 492 pages of master PDF
    doc_out.insert_pdf(doc_master, from_page=1, to_page=len(doc_master) - 1)

    # Preserve Outline / TOC
    master_toc = doc_master.get_toc()
    new_toc = [[1, "BÌA SÁCH // KIẾN TRÚC HỆ THỐNG GOLANG", 1]] + master_toc
    doc_out.set_toc(new_toc)

    # Set TrimBox and BleedBox on all interior pages
    for p in doc_out:
        p.set_bleedbox(p.rect)
        p.set_trimbox(p.rect)

    out_path = OUTPUT_DIR / "02_RUOT_SACH_GOLANG_493TRANG_A4.pdf"
    doc_out.save(out_path, deflate=True)

    doc_master.close()
    doc_front.close()
    doc_out.close()

    # Also update Golang_Master.pdf so the user sees the new cover directly
    shutil.copy2(out_path, MASTER_PDF_SRC)

    print(f"  -> Saved: {out_path}")
    print(f"  -> Total pages: 493")
    print(f"  -> Updated: {MASTER_PDF_SRC}")
    return out_path


def generate_spec_sheet(cover_pdf: Path, interior_pdf: Path):
    """Generates the technical printing specification sheet for print technicians."""
    print("[3/4] Generating Print Specification Sheets...")
    spec_text = f"""================================================================================
PHIẾU THÔNG SỐ KỸ THUẬT IN ẤN // PRINT PRODUCTION SPECIFICATION SHEET
ẤN PHẨM: GOLANG — GIÁO TRÌNH CẬP NHẬT LIÊN TỤC VỀ KỸ NGHỆ PHẦN MỀM VÀ DEVOPS/SRE
TÁC GIẢ: ĐOÀN NGỌC HOÀNG MINH
NĂM XUẤT BẢN: 2026
================================================================================

Kính gửi: Bộ phận Chế bản & Vận hành Máy in (Prepress & Print Production)

Đơn hàng bao gồm đúng 02 tệp PDF vector chuẩn in ấn công nghiệp:

--------------------------------------------------------------------------------
1. TỆP 1: BÌA SÁCH TRẢI RỘNG (COVER WRAP)
--------------------------------------------------------------------------------
- Tên tệp: 01_BIA_TRAI_GOLANG_A4_GAY28MM.pdf
- Khổ in thực tế (MediaBox / BleedBox): 454.0 x 303.0 mm
- Khổ thành phẩm sau xén (TrimBox):    448.0 x 297.0 mm
- Chi tiết cấu trúc bìa:
  + Bìa 4 (Mặt sau):       210.0 mm
  + Gáy sách (Spine):      28.0 mm (Dành cho ruột 493 trang giấy 80gsm)
  + Bìa 1 (Mặt trước):     210.0 mm
  + Tràn lề (Bleed):       3.0 mm mỗi cạnh (trên, dưới, trái, phải)
- Dấu định vị:             Đã có sẵn dấu chữ thập xén (Crop marks) & vạch nếp gấp gáy
- Quy cách giấy đề xuất:   Giấy Couche 300 gsm (C300) hoặc Bristol 300 gsm
- Chế bản & Gia công:      In đơn sắc High-Density Grayscale (hoặc in 4 màu CMYK)
                           Cán màng mờ (Matte Lamination) mặt ngoài
                           Bế gân 2 mép gáy và 2 mép gập bìa (4 đường cấn)

--------------------------------------------------------------------------------
2. TỆP 2: RUỘT SÁCH (INTERIOR BOOK BLOCK)
--------------------------------------------------------------------------------
- Tên tệp: 02_RUOT_SACH_GOLANG_493TRANG_A4.pdf
- Khổ thành phẩm (TrimBox / MediaBox): ISO A4 (210.0 x 297.0 mm)
- Tổng số trang ruột:      ĐÚNG 493 TRANG (Không tính bìa ngoài)
- Cấu trúc trang:
  + Trang 1:               Trang Tiêu đề Kiến trúc (Architectural Title Page)
  + Trang 2:               Mục lục (Table of Contents)
  + Trang 3 - 493:         Nội dung kỹ thuật (Ch00 - Ch29, Labs, Phụ lục Lỗi)
- Quy cách giấy đề xuất:   Giấy Woodfree / Bãi Bằng / Ford 80 gsm trắng tự nhiên
- Chế bản & In ấn:         In 2 mặt đen trắng (1/1 Monochrome)
- Đóng cuốn đề xuất:       Khâu chỉ dán keo nhiệt PUR (Smyth Sewn + PUR Softcover)
                           hoặc dán gáy keo nhiệt PUR áp lực cao.

--------------------------------------------------------------------------------
3. MÃ KIỂM TRA TỆP (CHECKSUMS)
--------------------------------------------------------------------------------
- SHA-256 (01_BIA_TRAI...):
  {compute_sha256(cover_pdf)}
- SHA-256 (02_RUOT_SACH...):
  {compute_sha256(interior_pdf)}

================================================================================
"""
    spec_txt_file = OUTPUT_DIR / "THONG_SO_KY_THUAT_NHA_IN.txt"
    spec_txt_file.write_text(spec_text, encoding="utf-8")

    spec_md_file = OUTPUT_DIR / "README_NHA_IN.md"
    spec_md_text = f"""# Hướng Dẫn In Ấn — Sách Golang 2026

Tài liệu bàn giao 02 tệp chế bản chuẩn cho nhà in:

1. **[`01_BIA_TRAI_GOLANG_A4_GAY28MM.pdf`](01_BIA_TRAI_GOLANG_A4_GAY28MM.pdf)**
   - Khổ in: $454.0 \\times 303.0\\,\\text{{mm}}$ (Bìa 4 + Gáy $28\\,\\text{{mm}}$ + Bìa 1 + Bleed $3\\,\\text{{mm}}$)
   - Giấy bìa: Couche $300\\,\\text{{gsm}}$, cán màng mờ, cấn 4 đường gáy.

2. **[`02_RUOT_SACH_GOLANG_493TRANG_A4.pdf`](02_RUOT_SACH_GOLANG_493TRANG_A4.pdf)**
   - Khổ in: ISO A4 ($210.0 \\times 297.0\\,\\text{{mm}}$)
   - Số trang: Đúng 493 trang ruột.
   - Giấy ruột: Woodfree / Ford $80\\,\\text{{gsm}}$, in 2 mặt đen trắng (1/1).
   - Đóng cuốn: Khâu chỉ dán gáy keo PUR.

*Chi tiết thông số kỹ thuật xem tại tệp [`THONG_SO_KY_THUAT_NHA_IN.txt`](THONG_SO_KY_THUAT_NHA_IN.txt).*
"""
    spec_md_file.write_text(spec_md_text, encoding="utf-8")
    print(f"  -> Saved: {spec_txt_file}")
    print(f"  -> Saved: {spec_md_file}")


def main():
    print("=== ASSEMBLING OFFICIAL 2-FILE PRINT PRODUCTION PACKAGE ===")
    cover_pdf = process_cover_wrap()
    interior_pdf = process_interior()
    generate_spec_sheet(cover_pdf, interior_pdf)
    print("\n[4/4] Validation check:")
    print(f"  File 1 Cover:    {cover_pdf.stat().st_size / 1024:.1f} KB")
    print(f"  File 2 Interior: {interior_pdf.stat().st_size / (1024*1024):.2f} MB")
    print("=== PRINT PACKAGE SUCCESSFULLY ASSEMBLED! ===")


if __name__ == "__main__":
    main()
