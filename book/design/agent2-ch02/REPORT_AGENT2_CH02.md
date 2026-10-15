# BÁO CÁO THIẾT KẾ KIẾN TRÚC CHƯƠNG 2 — AGENT 2 PROTOTYPE & SUBMISSION

> **Trạng thái:** `AWAITING_MANUAL_APPROVAL`  
> **Repository:** `https://github.com/Minhlike/Golang.git`  
> **Branch thiết kế:** `design/ch02-agent2-redesign`  
> **BASE_HEAD (main):** `bb00a9ad33e3cd5115928dc3542d2ce66c8d08d8`  
> **Bản PDF Master (`Golang_Master.pdf`):** Giữ nguyên trạng 100%, không bị tác động.  
> **Tài liệu kiểm định độc lập dành cho:** Người dùng & ChatGPT Reviewer.

---

## 1. TỔNG QUAN YÊU CẦU & HIẾN PHÁP THIẾT KẾ

Thực hiện nhiệm vụ **AGENT 2 — CHƯƠNG 2: THIẾT KẾ, TRÌNH DUYỆT VÀ CHỜ PHÊ DUYỆT** theo đúng chỉ đạo tại `MASTER PROMPT.txt`:
1. **Bảo toàn 100% nội dung & tính chính xác kỹ thuật:** Giữ nguyên vẹn toàn bộ câu chữ, mã nguồn Go, bảng biểu, chú giải của Chương 2 (`book/chapters/02-gia-tri-slice-va-aliasing.md`).
2. **Quy chuẩn hiển thị Code Block (LUẬT MỚI BẤT BIẾN):**
   - **TUYỆT ĐỐI KHÔNG ĐƯỢC THÊM SỐ DÒNG VÀO CÁC ĐOẠN CODE (NO LINE NUMBERS).**
   - Đã ghi khắc vĩnh viễn vào `MASTER PROMPT.txt` tại:
     - *Điều 8 Hiến pháp bất biến:* `CODE-WIDTH-PREFLIGHT & NO-LINE-NUMBERS`.
     - *Mục 10:* `CHẤT LƯỢNG TRÌNH BÀY PDF`.
     - *Mục 40 Điều 7:* `LUẬT BIÊN TẬP VĨNH VIỄN: PROSE-FIRST TECHNICAL WRITING`.
   - Toàn bộ các khối code specification và terminal output trong bản thiết kế Chương 2 đều tuân thủ nghiêm ngặt: không có gutter số dòng, thụt lề chuẩn xác, hiển thị mã nguồn nguyên bản để học viên tập trung tối đa vào cấu trúc ngôn ngữ.
3. **Phân loại Object thiết kế:**
   - **Object kỹ thuật (Code, Memory Layout, Terminal):** Phong cách đặc tả phần mềm kỹ thuật cao (Software Specification Standard), đơn sắc (Black & White Technical Minimalist), typography nghiêm cẩn.
   - **Object minh họa kiến trúc 3D (Axonometric Section):** Minh họa nghệ thuật kỹ thuật không gian 3 chiều (Manual of Section style) thể hiện liên kết giữa Stack Frame và Heap Memory.

---

## 2. SO SÁNH CHI TIẾT BEFORE (BẢN CŨ) VS AFTER (PROTOTYPE AGENT 2)

| Hạng mục đối chiếu | Bản cũ (Golang_Master.pdf trang 35–44) | Bản thiết kế mới (Agent 2 Prototype) |
| :--- | :--- | :--- |
| **Chapter Opener & Metadata** | Tiêu đề chương đơn giản, chưa có bảng tóm lược đặc tả thông số kỹ thuật đầu chương. | Banner định vị kiến trúc (`GOLANG ARCHITECTURAL SPECIFICATION`), Title 1 dòng thanh thoát cân đối (`CHƯƠNG 2 — KHI MỘT BẢN SAO VẪN CHIA SẺ DỮ LIỆU`), kèm **Bảng Đặc Tả Kiến Trúc Chương (Chapter 02 Specification)** tổng hợp 4 invariant cốt lõi ngay đầu bài học. |
| **Sơ đồ Hình 1 (Array Bitwise Copy)** | PlantUML bitmap mờ hạt, styling cơ bản. | Vector ReportLab độ phân giải vô hạn: thể hiện biến `a` (@ 0x1040) và biến `b` (@ 0x1060) trên Stack độc lập, ô `[0]=99` đổi màu tương phản, chú thích callout chính xác. |
| **Sơ đồ Hình 2 (Slice Aliasing)** | PlantUML dạng khối tĩnh. | Vector ReportLab: Áp dụng **Vertical Memory Struct Layout** (+0x00 Data, +0x08 Len, +0x10 Cap) đúng chuẩn bộ nhớ 64-bit; đường dẫn vector trực giao (orthogonal routing) nối từ Data cell sang Backing Array tại Heap (@ 0x8040), không đè chữ hay cắt ngang qua các trường khác. |
| **Sơ đồ Hình 3 (Lát cắt 3D Axonometric)** | Chưa có trong bản cũ (chỉ có sơ đồ 2D). | **Bổ sung lát cắt không gian 3 chiều (3D Axonometric Memory Section)** theo chuẩn *Manual of Section*: Lát cắt phối cảnh trực quan hóa việc Stack Frame trỏ thẳng xuống ô nhớ Backing Array căn lề 8-byte word trên Heap. |
| **Sơ đồ Hình 4 (Slice Window Geometry)** | Text vẽ bằng ký tự ASCII đơn giản trong code block. | Bản vẽ vector trực quan hóa cấu trúc `x := base[1:3]`: hiển thị dải ô nhớ `[10, 20, 30, 40, 50]`, thước đo trực quan `len(x) = 2` (vùng quan sát) và `cap(x) = 4` (vùng mở rộng tối đa không cần re-alloc). |
| **Sơ đồ Hình 5 (Append Mechanics)** | Chưa có hình vẽ phân nhánh trực quan. | Sơ đồ phân nhánh nhị phân (Growth Contract): **Nhánh A** (Còn capacity: Zero-alloc in-place reuse) vs **Nhánh B** (Hết capacity: `growslice` cấp phát mảng mới độc lập). |
| **Trình bày Code Block** | Khối nền xám thô ráp, không phân biệt code vs terminal. | Header bar chuẩn kỹ thuật: `CODE SPECIFICATION // PACKAGE MAIN // amd64 compiled` (nền `#F8F9FA`, viền trái solid 2.5pt) vs `TERMINAL OUTPUT // status: 0 (verified)` (nền `#F4F5F7`, viền slate). **TUYỆT ĐỐI 0 SỐ DÒNG.** |
| **Bảng biểu (Tables)** | Bảng mặc định viền dày. | Chuẩn mực **Booktabs**: Header thanh lịch nền đen `#1A1A1A` chữ trắng, đường kẻ hairline phân cách dữ liệu tinh tế, tỷ lệ cột tối ưu cho khổ in B5. Bổ sung bảng 3 bước `API BOUNDARY OWNERSHIP PROTOCOL` ở mục 2.9. |
| **Khối bài tập & Giải mã hành vi** | Văn bản thông thường, dễ trôi mất điểm nhấn. | Đóng hộp chuyên biệt: `THỰC HÀNH // BUG HUNT CÓ KIỂM CHỨNG` (lab `part2-values`) và `ĐỐI CHIẾU KIẾN TRÚC // GIẢI MÃ BẢN CHẤT HÀNH VI`. |
| **Phân trang & Recto/Verso Parity** | Header/Footer đối xứng đơn giản. | Phân trang sách in chuẩn quốc tế: Trang chẵn (Verso, lề trái mang tên sách/phần), Trang lẻ (Recto, lề phải mang tên chương), số trang đặt ở góc lề ngoài. 100% không có heading mồ côi (orphan heading) hay ngắt trang gãy đoạn. |

---

## 3. DANH SÁCH FILE VÀ ARTIFACT TRÌNH DUYỆT

1. **File cấu hình & kịch bản thực thi:**
   - `MASTER PROMPT.txt`: Khắc sâu luật cấm số dòng trong code block vào 3 vị trí then chốt.
   - `scripts/ch02_vector_diagrams.py`: Module vẽ 5 sơ đồ kỹ thuật vector thuần ReportLab.
   - `scripts/build_ch02_preview.py`: Engine dựng PDF preview độc lập và xuất ảnh specimen từng trang.
2. **File Artifact kết quả:**
   - **File PDF Preview độc lập:**  
     `book/design/agent2-ch02/ch02_preview.pdf` (12 trang hoàn chỉnh)
   - **Bộ ảnh chụp thực tế từng trang (Specimens PNG 150 DPI):**  
     - [Trang 1: Chapter Opener & Specification Table](specimens/ch02_page_01.png)
     - [Trang 2: §2.1 Baseline Dự Đoán & Hình 1 Array Bitwise Copy](specimens/ch02_page_02.png)
     - [Trang 3: §2.2 Khoảnh Khắc Đổi Kết Quả & Hình 2 Slice Aliasing](specimens/ch02_page_03.png)
     - [Trang 4: Hình 3 Lát Cắt Không Gian 3D Axonometric & §2.3 Cửa Sổ](specimens/ch02_page_04.png)
     - [Trang 5: Hình 4 Hình Học Cửa Sổ (Length vs Capacity)](specimens/ch02_page_05.png)
     - [Trang 6: §2.4 Append Là Phép Thử Về Capacity & Full Slice Expression](specimens/ch02_page_06.png)
     - [Trang 7: Hình 5 Phân Nhánh Append Mechanics & §2.5 Aliasing Bug Thật](specimens/ch02_page_07.png)
     - [Trang 8: Box Thực Hành Bug Hunt & Box Đối Chiếu Kiến Trúc & §2.6](specimens/ch02_page_08.png)
     - [Trang 9: Thí Nghiệm Memory Retention `runtime.KeepAlive`](specimens/ch02_page_09.png)
     - [Trang 10: §2.7 String: Bytes Trước, Text Sau & Terminal Output](specimens/ch02_page_10.png)
     - [Trang 11: §2.8 Pointer Là Câu Hỏi Khác](specimens/ch02_page_11.png)
     - [Trang 12: §2.9 Ranh Giới API, Bảng 3 Bước Protocol & Specification References](specimens/ch02_page_12.png)

---

## 4. KẾT QUẢ KIỂM THỬ VÀ BẢO CHỨNG CHẤT LƯỢNG (QA LEDGER)

- **Code Width Preflight:**
  ```text
  [CODE-WIDTH-PASS] All code blocks within printable width limits.
    - Usable width: 448.22 pt (~64 monospace chars)
    - Overflowing lines: 0
  ```
- **Publication Contracts Suite:**
  ```text
  Ran 16 tests in 0.299s
  OK (16/16 passed)
  ```
- **Visual Inspection Audit:**
  - Lỗi số dòng code block: Đã triệt tiêu 100%.
  - Lỗi giao cắt đường vẽ vector: Đã chuẩn hóa qua Vertical Struct Layout và đường dẫn trực giao (orthogonal routing).
  - Lỗi đè chữ tại lát cắt 3D: Đã dời gốc vector xuống cạnh đáy mặt trước, nhãn đặt an toàn trong không gian mở.
  - Lỗi ngắt trang: Đã loại bỏ HRFlowable sau tiêu đề H2, liên kết chặt chẽ nội dung kế tiếp (`keepWithNext=True`).
  - Lỗi Recto/Verso Parity: 100% khớp quy chuẩn in sách hai mặt.

---

## 5. HARD APPROVAL GATE

```text
================================================================================
                    HARD APPROVAL GATE: AWAITING_MANUAL_APPROVAL
================================================================================
  [X] KHÔNG MERGE VÀO MAIN.
  [X] KHÔNG PUSH THAY ĐỔI LÊN MAIN.
  [X] KHÔNG GHI ĐÈ GOLANG_MASTER.PDF (Bản PDF chính thức 593 trang giữ nguyên vẹn).
  [X] Toàn bộ prototype nằm độc lập trên branch: design/ch02-agent2-redesign.
  [X] Commit và push branch lên GitHub để ChatGPT Reviewer tiến hành đối chiếu.
================================================================================
```
