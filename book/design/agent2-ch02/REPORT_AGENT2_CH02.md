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
| **Chapter Opener & Metadata** | Tiêu đề chương đơn giản, chưa có bảng tóm lược đặc tả thông số kỹ thuật đầu chương. | Banner định vị kiến trúc (`GOLANG ARCHITECTURAL SPECIFICATION`), Title 1 dòng thanh thoát cân đối (`CHƯƠNG 2 — KHI MỘT BẢN SAO VẪN CHIA SẺ DỮ LIỆU`), kèm **Bảng Đặc Tả Kiến Trúc Chương (Chapter 02 Specification)** phân biệt rạch ròi giữa quy chuẩn Go spec và mô hình triển khai runtime gc 64-bit. |
| **Sơ đồ Hình 1 (Array Bitwise Copy)** | PlantUML bitmap mờ hạt, styling cơ bản. | Vector ReportLab: Thể hiện biến `a` (@ 0x1040*) và biến `b` (@ 0x1060*) trên bộ nhớ độc lập theo đúng ngữ nghĩa Go spec; ghi rõ footnote: địa chỉ mang tính minh họa, vị trí Stack/Heap do escape analysis quyết định. Header: `BẢO ĐẢM TỪ GO SPEC`. |
| **Sơ đồ Hình 2 (Slice Aliasing)** | PlantUML dạng khối tĩnh. | Vector ReportLab: Áp dụng **Vertical Memory Struct Layout** (+0x00 Data, +0x08 Len, +0x10 Cap) của gc runtime 64-bit; đường dẫn vector trực giao (orthogonal routing) nối từ Data cell sang Backing Array (@ 0x8040*); ghi rõ disclaimer cấu trúc 3 word là chi tiết triển khai gc, vị trí do escape analysis tối ưu. |
| **Sơ đồ Hình 3 (Lát cắt 3D Axonometric)** | Chưa có trong bản cũ (chỉ có sơ đồ 2D). | **Bổ sung lát cắt không gian 3 chiều (3D Axonometric Memory Section)** theo chuẩn *Manual of Section*: Lát cắt phân tầng logic giữa Descriptor và mảng liên tiếp; loại bỏ nhãn kỹ thuật trang trí; chú thích rõ vị trí vật lý phụ thuộc escape analysis. |
| **Sơ đồ Hình 4 (Slice Window Geometry)** | Text vẽ bằng ký tự ASCII đơn giản trong code block. | Bản vẽ vector trực quan hóa cấu trúc `x := base[1:3]` theo quy chuẩn Go Spec: dải ô nhớ `[10, 20, 30, 40, 50]`, thước đo `len(x) = 2` (vùng quan sát) và `cap(x) = 4` (vùng mở rộng tối đa không cần re-alloc). |
| **Sơ đồ Hình 5 (Append Mechanics)** | Chưa có hình vẽ phân nhánh trực quan. | Phân định rạch ròi giữa ngữ nghĩa ngôn ngữ Go và cơ chế runtime: **Nhánh 1** (Đủ sức chứa `len+1 <= cap`: ngôn ngữ tái sử dụng mảng nền) vs **Nhánh 2** (Vượt sức chứa `len+1 > cap`: ngôn ngữ cấp phát mảng mới; runtime gc dùng `growslice` tính toán block size). |
| **Trình bày Code Block** | Khối nền xám thô ráp, không phân biệt code vs terminal. | Header bar tối giản, trang nhã: Loại bỏ triệt để các nhãn kỹ thuật trang trí vô căn cứ (`amd64 compiled`, `status: 0 (verified)`). Phân biệt tinh tế giữa Go code (`#F8F9FA`, viền trái solid 2.5pt `#111111`) và Terminal output (`#F4F5F7`, viền `#555555`). **TUYỆT ĐỐI 0 SỐ DÒNG (NO LINE NUMBERS).** |
| **Bảng biểu (Tables)** | Bảng mặc định viền dày. | Phong cách **Technical Grid** thanh lịch chuẩn sách kỹ thuật chuyên nghiệp: Header nền xám rất nhạt (`#F0F2F5`), chữ đen (`COLOR_BLACK`), viền hộp ngoài (`BOX` 0.6pt `#777777`), lưới chia trong đầy đủ cạnh dọc và ngang (`INNERGRID` 0.4pt `#D0D0D0`), phân cách header 1.0pt `#444444`. 100% đầy đủ cạnh dọc, loại bỏ hoàn toàn tương phản nặng nề của nền đen, tối ưu khi in ấn đen trắng. |
| **Khối bài tập & Giải mã hành vi** | Văn bản thông thường, dễ trôi mất điểm nhấn. | Đóng hộp chuyên biệt: `THỰC HÀNH // BUG HUNT CÓ KIỂM CHỨNG` (lab `part2-values`) và `ĐỐI CHIẾU KIẾN TRÚC // GIẢI MÃ BẢN CHẤT HÀNH VI`. |
| **Phân trang & Recto/Verso Parity** | Header/Footer đối xứng đơn giản. | Phân trang sách in chuẩn quốc tế: Trang chẵn (Verso, lề trái mang tên sách/phần), Trang lẻ (Recto, lề phải mang tên chương), số trang đặt ở góc lề ngoài. Trang 1 là Portal Opener độc lập; §2.1 khởi đầu trang 2. Toàn chương đúng 12 trang hoàn hảo, không có heading mồ côi. |

---

## 2.1 CÁC HIỆU CHỈNH CHÍNH XÁC KỸ THUẬT & DỌN DẸP METADATA (ROUND 2)

Thực hiện chuẩn hóa kỹ thuật sâu theo chỉ đạo nghiêm ngặt từ User & Reviewer:
1. **Quy chuẩn địa chỉ bộ nhớ & Escape Analysis (Memory Diagrams):**
   - Không gắn nhãn tĩnh xem biến nằm cố định trên Stack hay Heap nếu không có bằng chứng phân tích thoát (escape analysis).
   - Mọi địa chỉ bộ nhớ (@ 0x1040, @ 0x1060, @ 0x8040) đều được chú thích rõ là **địa chỉ minh họa logic**, không phải cam kết của Go spec.
   - Thêm footnote và caption trên cả 5 sơ đồ nêu rõ: *Vị trí Stack/Heap do trình biên dịch quyết định thông qua escape analysis.*
2. **Phân định Go Specification vs GC Runtime Implementation (Slice Internals):**
   - Phân biệt rõ ngữ nghĩa cửa sổ quan sát mảng nền được Go Specification bảo đảm với cấu trúc thực thi cụ thể của compiler `gc` trên kiến trúc 64-bit (3 từ máy: `Data pointer`, `len int`, `cap int`, tổng cộng 24 bytes).
   - Ghi chú rõ ràng: Go specification chỉ chuẩn hóa ngữ nghĩa gán/tham chiếu, không áp đặt kích thước cố định cho mọi implementation.
3. **Cơ chế Append (Append Mechanics):**
   - Loại bỏ các khẳng định tuyệt đối hoặc gây nhầm lẫn về việc cấp phát bộ nhớ.
   - Phân tách 2 nhánh minh bạch: Ngữ nghĩa ngôn ngữ (Language semantics: tái sử dụng mảng nền hiện tại vs cấp phát mảng mới khi vượt capacity) và Chi tiết hiện thực (Runtime implementation: `runtime.growslice` tính toán khối nhớ theo size class).
4. **Loại bỏ Metadata trang trí giả hiệu (Faux Metadata Stripping):**
   - Xóa bỏ triệt để các nhãn trang trí mang tính hình thức như `amd64 compiled` hay `status: 0 (verified)` ở các khối code block và terminal output.
5. **Định dạng trang sách hoàn chỉnh (12 trang chuẩn mực):**
   - Thêm `PageBreak()` chủ động trước `§ 2.1 — Một baseline để dự đoán`, biến Trang 1 thành **Chapter Opener Portal** bề thế, độc lập (gồm tiêu đề, bảng đặc tả kiến trúc, ví dụ khởi động, output và đoạn chuyển tiếp).
   - Đảm bảo toàn bộ Chương 2 trải đều trên đúng 12 trang B5, kết thúc trọn vẹn tại Bảng Protocol 3 bước và Thư mục tài liệu tham chiếu chuẩn ở chân Trang 12.

---

## 2.2 HOÀN THIỆN HIỆU CHỈNH THỊ GIÁC & KỸ THUẬT (ROUND 3: FINAL CORRECTIONS)

1. **Khôi phục đầy đủ cạnh dọc và chuẩn hóa bảng biểu (Table Redesign):**
   - Loại bỏ hoàn toàn hàng tiêu đề nền đen đặc, chữ trắng vì tương phản quá nặng, thiếu tính hài hòa thị giác.
   - Thiết kế lại toàn bộ 3 bảng (Bảng Đặc tả Kiến trúc Trang 1, Bảng 1 Đối chiếu Giá trị Trang 4, Bảng Protocol 3 bước Trang 12) theo phong cách **Technical Grid** chuẩn mực sách kỹ thuật:
     - Header nền xám rất nhạt (`#F0F2F5`), chữ đen đậm (`COLOR_BLACK`).
     - Khôi phục 100% các **cạnh dọc** (cả đường biên ngoài bên trái/phải qua `BOX 0.6pt #777777` và đường chia dọc giữa các cột qua `INNERGRID 0.4pt #D0D0D0`).
     - Đường kẻ ngăn cách header rõ nét (`1.0pt #444444`).
     - Các hàng dữ liệu xen kẽ nền trắng và nền `#F8F9FA`, padding thoáng đãng (5.5pt trên/dưới, 7pt trái/phải), tối ưu độ sắc nét và tương phản khi in ấn đen trắng.
2. **Loại bỏ nhãn `VERIFIED SNIPPET`:**
   - Xóa bỏ hoàn toàn nhãn `VERIFIED SNIPPET` khỏi engine render code block; không sử dụng bất kỳ nhãn kỹ thuật giả hiệu nào để trang trí.
   - Code block hiển thị mã nguồn Go và Terminal thuần khiết, thanh lịch với viền trái tinh tế và nền sáng chuẩn mực.
3. **Chuẩn hóa triệt để Slice Descriptor:**
   - Phân biệt rõ ràng giữa đặc tả ngôn ngữ Go (ngữ nghĩa cửa sổ quan sát), mô hình giải thích (pointer, len, cap) và cấu trúc triển khai của compiler `gc` 64-bit (3 từ máy 24B với con trỏ theo dõi bởi GC).
   - Tuyệt đối không trình bày `Data uintptr` như một cam kết ngôn ngữ (thay thế toàn bộ nhãn `uintptr` trong sơ đồ Hình 2, Hình 3 và bảng đặc tả thành `con trỏ mảng (array pointer)`).
4. **Làm rõ kịch bản minh họa & Escape Analysis trên mọi sơ đồ:**
   - Bổ sung footnote và disclaimer trên cả 5 sơ đồ vector: Làm rõ Stack/Heap và địa chỉ bộ nhớ (`@ 0x1040`, `@ 0x8040`...) chỉ là kịch bản minh họa ước lệ; không mặc định mọi slice đều có cách phân bổ bộ nhớ giống nhau, mà phụ thuộc hoàn toàn vào escape analysis của trình biên dịch.
5. **Bảo toàn Hiến pháp cấm số dòng:**
   - Tuyệt đối 0 số dòng (NO LINE NUMBERS) trong toàn bộ code block và terminal block.
6. **Kiểm tra chất lượng trực quan 12 trang:**
   - Xuất và kiểm tra thực tế 12 ảnh specimen PNG 150 DPI; tất cả các bảng, sơ đồ, code block đều hiển thị sắc nét, không tràn lề, không ngắt dòng xấu.

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
