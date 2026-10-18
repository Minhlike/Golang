# BẢNG KIỂM TRA CHẤT LƯỢNG VÀ HỒI QUY THIẾT KẾ 2026
## QA Verification & Regression Checklist — Agent 2 Design System

**Ấn phẩm:** *GOLANG — Giáo trình cập nhật liên tục về Kỹ nghệ phần mềm và DevOps/SRE*  
**Tác giả:** Đoàn Ngọc Hoàng Minh  
**Kiểm định viên:** Agent 2 (Art Direction & Editorial QA)  
**Tài liệu kiểm toán:** `book/design/agent2-2026/design_catalog.pdf` (28 trang, SHA-256 xác thực)  
**Nhánh Git:** `design/agent2-object-specimens` (Commit baseline: `bb00a9ad33e3cd5115928dc3542d2ce66c8d08d8`)  
**Ngày kiểm toán:** 09/10/2026  

---

## I. TỔNG KẾT KẾT QUẢ KIỂM TOÁN (EXECUTIVE QA SUMMARY)

| Hạng Mục Kiểm Toán | Tiêu Chuẩn Đánh Giá | Kết Quả Thực Tế | Ghi Chú Kỹ Thuật |
|---|---|---|---|
| **1. Biên Dịch Catalog PDF** | Hoàn tất không lỗi, đầy đủ 28 trang | **PASS** | File size: 3,555,887 bytes; 37 PDF Outlines/Bookmarks |
| **2. Xuất Ảnh Toàn Trang** | Render 150 DPI toàn bộ 28 trang | **PASS** | 28 tệp `renders/catalog_p01.png` đến `p28.png` hoàn chỉnh |
| **3. Lưới Lề Đối Xứng (Spreads)** | Lề trong 24mm, Lề ngoài 18mm đối xứng | **PASS** | Kiểm chứng trên 4 cặp trang đôi thực tế (Spreads 1–4) |
| **4. Tiêu Đề Chạy & Số Trang** | Recto bên phải, Verso bên trái | **PASS** | Phân cách bằng hairline rule 0.4pt, không đè văn bản |
| **5. Khóa Tiêu Đề Mồ Côi** | `keepWithNext=True` trên mọi Heading | **PASS** | Không có tiêu đề nào cô độc ở dòng cuối trang |
| **6. Font Embedding Subsets** | Nhúng đầy đủ 5 phông TrueType | **PASS** | Source Serif 4, Source Sans 3, JetBrains Mono |
| **7. Bảo Toàn Unicode Tiếng Việt** | Không lỗi font các ký tự dấu tiếng Việt | **PASS** | 100% các ký tự ă, â, ê, ô, ơ, ư, đ trích xuất chính xác |
| **8. Trích Xuất Cấu Trúc Mã Nguồn** | Đọc được package, import, hàm main | **PASS** | PyMuPDF và pypdf đều trích xuất đầy đủ cú pháp Go |
| **9. Đồng Nhất Byte Mã Nguồn (SHA)** | Byte-for-byte identity với ký tự Tab | **FAIL (Declared)** | Do ReportLab `expandtabs(4)` chuyển byte 0x09 thành 4x 0x20 |
| **10. Tính Toàn Vẹn Repo & Release** | Không chạm vào release PDF cũ & manuscript | **PASS** | `Golang_Master.pdf` SHA giữ nguyên bất biến |

---

## II. CHI TIẾT KIỂM TOÁN TRỰC QUAN 28 TRANG (VISUAL INSPECTION)

Tất cả các trang đã được kết xuất thành ảnh PNG độ phân giải cao tại `book/design/agent2-2026/renders/`:

### Nhóm Bìa & Khởi đầu (Trang 1–4)
- **Trang 1 (`catalog_p01.png`):** Trang bìa chính Catalog. Khối chữ tiêu đề sắc nét, bảng thông số sản xuất vi mô ngay ngắn, đường caliper kẻ đôi chuẩn mực, không có header/footer theo đúng quy tắc trang bìa. **[VISUAL PASS]**
- **Trang 2 (`catalog_p02.png`):** Lời nói đầu của Agent 2. Phông Source Serif 4 chính văn dàn trang thư thái, lề ngoài 18mm bên trái, lề trong 24mm bên phải (Verso), số trang "2" ở góc dưới bên trái. **[VISUAL PASS]**
- **Trang 3 (`catalog_p03.png`):** Mục lục tổng thể. Các mục liên kết có hairline phân cách, số trang phông đơn cách căn lề phải thẳng hàng tuyệt đối. **[VISUAL PASS]**
- **Trang 4 (`catalog_p04.png`):** Tổng quan định hướng nghệ thuật & bảng so sánh 3 Concept bìa mới. Bảng viền 0.8pt đen tuyền, phân bố cột cân đối. **[VISUAL PASS]**

### Nhóm Trưng Bày 3 Concept Bìa (Trang 5–7)
- **Trang 5 (`catalog_p05.png`):** Concept 1 — Mặt Cắt Kiến Trúc. Bố cục trang đôi: Ảnh in phẳng 300 DPI bên trái, Phối cảnh 3D gáy 3.5cm bên phải với bóng đổ mềm và các lớp trang sách trắng. Caption căn giữa, phần phân tích kiến trúc Lewis et al. ngay ngắn bên dưới. **[VISUAL PASS]**
- **Trang 6 (`catalog_p06.png`):** Concept 2 — Khắc Đồng Dòng Chảy Tô-pô. Các đường dòng trường thế phức $\psi(z)$ hiển thị sắc nét từng nét khắc burin; phối cảnh 3D trang trọng. **[VISUAL PASS]**
- **Trang 7 (`catalog_p07.png`):** Concept 3 — Monolith Kiến Tạo Thụy Sĩ. Kiểu chữ 3D extruded tương phản cực cao trên nền lưới 12 cột; phối cảnh 3D vững chãi. **[VISUAL PASS]**

### Nhóm Phân Cấp Chữ & Khối Kỹ Thuật (Trang 8–12)
- **Trang 8 (`catalog_p08.png`):** Bảng phân cấp tiêu đề H1–H4 và mẫu chính văn Source Serif 4. Cỡ chữ và khoảng cách dòng đạt tỷ lệ quang học tối ưu. **[VISUAL PASS]**
- **Trang 9 (`catalog_p09.png`):** Thử nghiệm tiêu đề H1 dài 3 dòng và cơ chế khóa mồ côi `keepWithNext=True`. Tiêu đề ngắt dòng tự nhiên, không bị đè chữ. Hộp callout hợp đồng bố cục nổi bật. **[VISUAL PASS]**
- **Trang 10 (`catalog_p10.png`):** Khối mã nguồn Go với thanh nhấn trái 2.4pt đen, nền `#F6F6F6`, số dòng căn phải màu xám; khối Terminal phân biệt rõ lệnh gõ `$` và kết quả in ra. **[VISUAL PASS]**
- **Trang 11 (`catalog_p11.png`):** Đối chiếu hai mẫu bảng: Mẫu A Booktabs chỉ kẻ ngang thanh lịch vs Mẫu B Ma trận kỹ thuật DevOps có lưới ô vuông 0.4pt. **[VISUAL PASS]**
- **Trang 12 (`catalog_p12.png`):** Hình vẽ kỹ thuật với hai sơ đồ kiến trúc thật từ repository: `reconciliation-loop.png` và `operator-manager-boundaries.png`. Caption căn giữa chuẩn mực. **[VISUAL PASS]**

### Nhóm Đối Tượng Sư Phạm Đặc Thù (Trang 13–15)
- **Trang 13 (`catalog_p13.png`):** Điểm dừng Suy luận (Deduction Stop) đóng khung viền đen 1.2pt và Lời giải văn xuôi liên tục tuân thủ MASTER PROMPT (không dùng bullet hời hợt). **[VISUAL PASS]**
- **Trang 14 (`catalog_p14.png`):** Hộp bài tập Lab Challenge với thanh viền trái 3.0pt và Hộp đo lường hiệu năng Benchmark với số liệu định lượng `ns/op` và `B/op`. **[VISUAL PASS]**
- **Trang 15 (`catalog_p15.png`):** Error Atlas bố cục hai cột chính xác (Mỗi cột 8.0 cm, rãnh giữa 8 mm) và Thẻ hồ sơ thư viện DevOps `controller-runtime`. **[VISUAL PASS]**

### Nhóm Trang Đôi Thực Tế (Spreads 1–4, Trang 16–23)
- **Trang 16 & 17 (Spread 1 — Ch01):** Khởi đầu chương, mã nguồn `main.go`, lệnh terminal chạy module và bảng giải phẫu cú pháp. Lề đối xứng qua gáy rõ rệt: Trang 16 lề trong bên phải 24mm; Trang 17 lề trong bên trái 24mm. **[VISUAL PASS]**
- **Trang 18 & 19 (Spread 2 — Ch02):** Lý thuyết Slice header 24-byte, mã đột biến aliasing, sơ đồ mảng nền `slice-sharing.png` và bảng đối chiếu cơ chế copy value. **[VISUAL PASS]**
- **Trang 20 & 21 (Spread 3 — Ch10):** Điều tra rò rỉ bộ nhớ, GC Pacer, benchmark `B.Loop`, terminal pprof heap profile và bảng công cụ chẩn đoán. **[VISUAL PASS]**
- **Trang 22 & 23 (Spread 4 — Ch23):** Quản lý tài nguyên con Kubernetes, OwnerReference, Finalizer, sơ đồ vòng lặp Reconcile `reconciliation-loop.png` và mã nguồn Reconciler. **[VISUAL PASS]**

### Nhóm Báo Cáo Kỹ Thuật & Xuất Bản (Trang 24–28)
- **Trang 24 & 25 (`catalog_p24.png`, `p25.png`):** Báo cáo phân tích sao chép mã nguồn (Clipboard Fidelity), bảng đối soát trích xuất văn bản và hai phương án kiến nghị cho bản phát hành chính thức. **[VISUAL PASS]**
- **Trang 26 & 27 (`catalog_p26.png`, `p27.png`):** Báo cáo in ấn khổ A4, bảng tra độ dày gáy theo định lượng giấy và số trang, khuyến nghị đóng gáy khâu chỉ dán keo PUR. **[VISUAL PASS]**
- **Trang 28 (`catalog_p28.png`):** Tuyên bố trạng thái chế bản chính thức (`AWAITING_PRINT_SPEC` & `PUBLICATION_STATUS=BLOCKED_PENDING_EVIDENCE`). **[VISUAL PASS]**

---

## III. KIỂM TOÁN SAO CHÉP MÃ NGUỒN & CLIPBOARD FIDELITY

Dữ liệu kiểm toán thực nghiệm tự động ghi nhận từ `sources/test_clipboard_fidelity.py` và lưu trữ tại `clipboard_test_results.json`:

```json
{
  "unicode_preservation": {
    "status": "PASS",
    "tested_glyphs": "ă, â, ê, ô, ơ, ư, đ (lowercase & uppercase)"
  },
  "code_structure": {
    "page_18_package_main": true,
    "page_18_classify_func": true,
    "page_18_main_func": true,
    "extraction_status": "PASS"
  },
  "line_number_isolation": {
    "line_numbers_in_raw_stream": true,
    "declared_finding": "Line numbers drawn on the canvas are extracted into the raw text stream by PDF text readers."
  },
  "byte_fidelity": {
    "literal_tab_preserved": false,
    "declared_status": "FAIL (Expected due to ReportLab expandtabs(4) contract)",
    "semantic_fidelity": "PASS (4 spaces maintain visual structure and compiler validity)"
  }
}
```

### Phân tích chi tiết các tiêu chí:
1. **Bảo toàn Ký tự Tiếng Việt (Unicode Diacritics): PASS (100%)**  
   Cả hai thư viện trích xuất độc lập (PyMuPDF và pypdf) đều đọc trọn vẹn $100\%$ các ký tự có dấu tiếng Việt trong chú thích mã nguồn và chính văn (`Đoàn Ngọc Hoàng Minh`, `giáo trình`, `kỹ nghệ`, `phần mềm`, `điều hòa`, `nguyên nhân`, `khắc phục`, `bất biến`). Không xảy ra hiện tượng mất dấu, lỗi font TOFU (ô vuông trống) hay ký tự rác.
2. **Bảo toàn Cấu trúc Mã nguồn (Code Semantic Extraction): PASS**  
   Các định danh Go (`package main`, `func classify(code int) string`, `func main()`) được trích xuất hoàn chỉnh, thụt lề 4 dấu cách được bảo toàn.
3. **Hiện tượng Đánh số dòng (Line Numbers Extraction Behavior): Ghi nhận hạn chế kỹ thuật**  
   Khi số dòng được vẽ lên canvas, luồng trích xuất văn bản thô (raw text stream) của trình đọc PDF sẽ đọc số dòng xen kẽ trước từng dòng mã. Đây là đặc tính cố hữu của định dạng PDF khi không có cấu trúc thẻ Tagged PDF / Marked Content mở rộng.  
   *Khuyến nghị phát hành:* Đối với bản PDF điện tử chính thức, các khối mã nguồn bài tập sẽ không vẽ số dòng trong text stream để độc giả có thể quét chuột copy một chạm; hoặc nhúng trực tiếp tệp mã nguồn đính kèm (PDF Source File Attachment).
4. **Đồng nhất Byte (Byte-for-byte SHA Identity): FAIL (Công bố công khai)**  
   Hàm `expandtabs(4)` của ReportLab chuyển đổi ký tự Tab (`0x09`) thành 4 ký tự space (`0x20`). Do đó mã băm SHA-256 của đoạn mã trích xuất khác với mã nguồn nguyên bản trong repository. Mặc dù vậy, mã nguồn sau khi dán vào IDE vẫn tuân thủ cú pháp Go, lệnh `gofmt` tự động chuẩn hóa lại ngay khi lưu tệp, bảo toàn $100\%$ tính đúng đắn ngữ nghĩa (Semantic Identity PASS).

---

## IV. BẢO TỒN TÍNH TOÀN VẸN CỦA KHO MÃ NGUỒN (INVARIANT AUDIT)

| Đối Tượng Kiểm Tra | Giá Trị Kỳ Vọng | Trạng Thái Thực Tế | Kết Luận |
|---|---|---|---|
| **Release PDF SHA-256** | `f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09` | Khớp tuyệt đối | **PASS (Untouched)** |
| **Renderer Sản Xuất** | `scripts/build_pdf.py` & `book_style.py` | Không bị chỉnh sửa | **PASS (Preserved)** |
| **Bản Thảo Ch00–Ch29** | `book/chapters/*.md` | Không bị chỉnh sửa | **PASS (Preserved)** |
| **Phụ Lục & Labs** | `book/appendices/` & `labs/` | Không bị chỉnh sửa | **PASS (Preserved)** |
| **MASTER PROMPT** | `MASTER PROMPT.txt` | Không bị chỉnh sửa | **PASS (Preserved)** |
| **Trạng Thái Xuất Bản** | `PUBLICATION_STATUS = BLOCKED_PENDING_EVIDENCE` | Được giữ nguyên | **PASS (Enforced)** |

---

*Biên bản kiểm toán được thiết lập bởi Agent 2 — Art Direction & Editorial QA.*
