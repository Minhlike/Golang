# ĐẶC TẢ HỆ THỐNG THIẾT KẾ ĐỐI TƯỢNG XUẤT BẢN 2026
## Object Design Specification & Architectural Specimen Inventory

**Dự án:** Sách *GOLANG — Giáo trình cập nhật liên tục về Kỹ nghệ phần mềm và DevOps/SRE*  
**Tác giả:** Đoàn Ngọc Hoàng Minh  
**Chế bản & Art Direction:** Agent 2  
**Nhánh Git:** `design/agent2-object-specimens` (Baseline commit: `bb00a9ad33e3cd5115928dc3542d2ce66c8d08d8`)  
**Khổ sách & Môi trường:** ISO A4 Dọc (210 × 297 mm), Đơn sắc / Grayscale Print-First  
**Tài liệu phê duyệt chính:** `book/design/agent2-2026/design_catalog.pdf`  

---

## I. MỤC TIÊU VÀ NGUYÊN TẮC THIẾT KẾ

Tài liệu này xác lập quy chuẩn kỹ thuật cho toàn bộ hơn 30 đối tượng hiển thị (Object Inventory) trong cuốn sách. Thiết kế tuân thủ nghiêm ngặt các nguyên tắc:
1. **Đơn sắc chuẩn mực (Monochrome First):** Không phụ thuộc vào màu sắc để truyền tải thông tin kỹ thuật; tạo chiều sâu bằng phân cấp nét vẽ (stroke weight), sắc độ xám trung tính (grayscale tones) và tỷ lệ không gian quang học.
2. **Lưới lề đối xứng qua gáy (Mirrored Margin Spreads):** Đảm bảo khoảng hở gáy sách (spine clearance) 24 mm cho mọi trang chẵn và lẻ, loại bỏ hoàn toàn nguy cơ chữ bị chìm vào khe gáy khi đóng cuốn dày trên 450 trang.
3. **Tính trung thực sư phạm:** Mọi mẫu vật hiển thị (specimens) trong Catalog đều trích xuất trực tiếp từ các file nguồn bản thảo và thư viện diagrams thật trong repository; không sử dụng văn bản giả lập (Lorem Ipsum).

---

## II. MA TRẬN PHÂN LOẠI & KẾ HOẠCH XỬ LÝ (KEEP / IMPROVE / REPLACE)

| Nhóm Đối Tượng | Mã Đối Tượng | Tên Đối Tượng | Hiện Trạng (Baseline / Catalog Cũ) | Quyết Định Thiết Kế 2026 | Lý Do Kỹ Thuật & Sư Phạm |
|---|---|---|---|---|---|
| **Nhóm A: Bìa & Khối Khởi Đầu** | OBJ-A01 | Bìa sách ngoài (Full Cover) | Bìa phẳng đa giác A–D (`catalog-2026`) | **REPLACE** | Tác giả đã bác bỏ vì thiếu chiều sâu. Thay bằng 3 Concept mới có cơ sở nghệ thuật và phối cảnh 3D. |
| | OBJ-A02 | Trang lót / Tiêu đề (Half Title) | Đơn giản, phông sans thường | **IMPROVE** | Chuẩn hóa thông số metadata, chữ ký nghệ thuật của tác giả, khổ A4 trang trọng. |
| | OBJ-A03 | Mục lục tổng thể (Table of Contents) | Danh sách dạng text phẳng | **IMPROVE** | Thêm liên kết tương tác hai chiều (clickable hyperlinks), hairline dividers, căn số trang chuẩn BookMono. |
| | OBJ-A04 | Trang mở đầu chương (Chapter Opener) | Heading 1 thông thường | **IMPROVE** | Thêm đường caliper đôi kiến trúc (1.4pt / 0.4pt), số chương định dạng lớn, mục tiêu chương rõ ràng. |
| **Nhóm B: Phân Cấp Chữ & Văn Bản** | OBJ-B01 | Tiêu đề cấp 1 (H1) | Size 24pt, spaceBefore chưa tối ưu | **IMPROVE** | Chuẩn hóa `22pt / leading 27pt`, `keepWithNext=True`, triệt tiêu khoảng cách khi đứng đầu trang mới. |
| | OBJ-B02 | Tiêu đề cấp 2 (H2) | Size 15.5pt | **KEEP** | Duy trì `Source Sans 3 Bold`, `15pt / leading 19pt`, `keepWithNext=True`. |
| | OBJ-B03 | Tiêu đề cấp 3 (H3) | Size 13pt | **KEEP** | Duy trì `12.5pt / leading 16pt`, tạo nhịp ngắt phân đoạn mạch lạc. |
| | OBJ-B04 | Tiêu đề cấp 4 (H4) | Size 11pt | **KEEP** | Duy trì `10.5pt / leading 14pt`, in đậm, dùng cho các tiểu tiết kỹ thuật. |
| | OBJ-B05 | Văn bản chính văn (Body Prose) | Source Serif 4 | **KEEP** | Duy trì `10.5pt / leading 15.2pt`, độ dài dòng 65–75 ký tự tối ưu quang học, không mỏi mắt. |
| | OBJ-B06 | Tiêu đề dài nhiều dòng (Multi-line) | Có nguy cơ đè chữ nếu leading sai | **IMPROVE** | Thử nghiệm stress-test tiêu đề dài 3 dòng trong Catalog, kiểm chứng ngắt dòng tự nhiên. |
| | OBJ-B07 | Khóa mồ côi (Orphan / Widow Guard) | Thiếu kiểm soát ở một số bảng | **IMPROVE** | Bắt buộc `keepWithNext=True` trên 100% heading styles và đóng gói bảng bằng `KeepTogether`. |
| | OBJ-B08 | Danh sách có thứ tự / Gạch đầu dòng | Dùng bullet tròn to mặc định | **IMPROVE** | Chuyển sang bullet vuông vi mô hoặc thụt lề chuẩn 12pt, căn chỉnh thụt dòng treo (hanging indent). |
| | OBJ-B09 | Trích dẫn & Định nghĩa thuật ngữ | Dùng blockquote xám mờ | **IMPROVE** | Khung viền đơn sắc nét mảnh 0.6pt, nền xám nhạt `#F7F7F7`, phân biệt rõ với mã nguồn. |
| | OBJ-B10 | Số trang & Tiêu đề chạy (Header/Footer) | Chỉ có số trang đơn giản | **IMPROVE** | Thiết lập đối xứng: Trang chẵn header/folio bên trái; Trang lẻ header/folio bên phải; đường hairline 0.4pt. |
| **Nhóm C: Đối Tượng Kỹ Thuật & Code** | OBJ-C01 | Khối mã nguồn Go (Code Block) | Nền xám, thiếu thanh nhấn | **IMPROVE** | Bổ sung thanh nhấn trái 2.4pt đen tuyền, nền xám `#F6F6F6`, phông `JetBrains Mono 8.5pt/12pt`. |
| | OBJ-C02 | Số dòng trong mã nguồn (Line Numbers) | Không có hoặc lẫn vào text | **IMPROVE** | Đánh số dòng căn phải màu xám `#888888`; phân tích rõ ràng hành vi trích xuất clipboard trong QA. |
| | OBJ-C03 | Khối phiên làm việc Terminal | Chung style với code | **IMPROVE** | Tách biệt hoàn toàn: Dấu nhắc lệnh `$ ` in đậm đen, output xám `#444444`, viền hairline `#CCCCCC`. |
| | OBJ-C04 | Bảng Booktabs kinh điển | Dùng lưới ô vuông cho mọi bảng | **IMPROVE** | Áp dụng cho bảng lý thuyết: Chỉ dùng đường kẻ ngang (đỉnh 1.2pt, header 0.6pt, đáy 1.2pt), bỏ kẻ dọc. |
| | OBJ-C05 | Bảng Ma trận Kỹ thuật DevOps | Bảng không đồng nhất nét kẻ | **IMPROVE** | Áp dụng cho ma trận tham số: Lưới ô vuông mỏng 0.4pt `#CCCCCC`, header xám `#EEEEEE`. |
| | OBJ-C06 | Hình vẽ kỹ thuật (Technical Figure) | Caption không đồng nhất | **IMPROVE** | Khung hình căn giữa trang in, caption phông `Source Sans 3 8.5pt` có nhãn **Hình X.Y:** in đậm. |
| | OBJ-C07 | Sơ đồ Kiến trúc & Tuần tự (Diagrams) | Nhiều sơ đồ thiếu chuẩn mực | **KEEP** | Sử dụng trực tiếp tài nguyên vector/raster chuẩn từ `assets/diagrams/` (`reconciliation-loop.png`...). |
| **Nhóm D: Đối Tượng Sư Phạm Đặc Thù** | OBJ-D01 | Điểm dừng Suy luận (Deduction Stop) | Hộp callout chung chung | **IMPROVE** | Hộp viền kép hoặc viền đen 1.2pt, tiêu đề chữ hoa đậm nét, nhắc nhở người đọc dừng lại suy nghĩ. |
| | OBJ-D02 | Lời giải văn xuôi liên tục (Solution) | Thường dùng bullet giải thích | **IMPROVE** | Tuân thủ tuyệt đối MASTER PROMPT: Giải thích bản chất bằng văn xuôi liên tục, không dùng bullet hời hợt. |
| | OBJ-D03 | Thử thách Thực hành (Lab Challenge) | Mục lục bài tập rời rạc | **IMPROVE** | Khung thẻ công tác: Thanh nhấn trái 3.0pt, 3 mục rõ rệt: Mục tiêu, Ràng buộc, Tiêu chí kiểm chứng. |
| | OBJ-D04 | Hộp đo lường Benchmark / Test | Dạng text thô | **IMPROVE** | Bảng đối chiếu định lượng thời gian (`ns/op`) và cấp phát heap (`B/op`), tính toán độ biến thiên. |
| | OBJ-D05 | Hồ sơ Thư viện DevOps (Library Atlas) | Chưa có khung nhận diện | **IMPROVE** | Khối thẻ thư viện: Phân hạng (Tier), Import Path, Bản quyền, Ranh giới kiến trúc và Mẫu sử dụng tối ưu. |
| | OBJ-D06 | Bố cục tra cứu Error Atlas | Bố cục 1 cột dài dòng | **IMPROVE** | Hiện thực hóa bố cục 2 cột chuẩn xác: Cột 1 (8.0 cm) = Mã lỗi & Triệu chứng; Cột 2 (8.0 cm) = Nguyên nhân & Khắc phục. |
| | OBJ-D07 | Huy hiệu Provenance Nguồn | Chưa có trong các ấn bản trước | **NEW** | Huy hiệu đầu trang đôi ghi rõ: Tệp nguồn, dòng bắt đầu, dòng kết thúc, commit git baseline. |

---

## III. CHI TIẾT ĐẶC TẢ HÌNH HỌC VÀ LƯỚI KHÔNG GIAN

### 1. Kích thước trang và Lề in (Page Geometry)
- **Định dạng:** ISO 216 Series A — A4 (Dọc).
- **Kích thước cắt (Trim Size):** $210.0 \times 297.0\,\text{mm}$ ($595.28 \times 841.89\,\text{pt}$).
- **Lề trong (Inside Margin / Gutter facing spine):** $24.0\,\text{mm}$ ($68.03\,\text{pt}$).
- **Lề ngoài (Outside Margin / Fore-edge):** $18.0\,\text{mm}$ ($51.02\,\text{pt}$).
- **Lề trên (Top Margin):** $22.0\,\text{mm}$ ($62.36\,\text{pt}$).
- **Lề dưới (Bottom Margin):** $20.0\,\text{mm}$ ($56.69\,\text{pt}$).
- **Vùng in khả dụng (Printable Text Area):**
  - Chiều rộng: $W_{\text{print}} = 210.0 - 24.0 - 18.0 = 168.0\,\text{mm}$ ($476.22\,\text{pt}$).
  - Chiều cao: $H_{\text{print}} = 297.0 - 22.0 - 20.0 = 255.0\,\text{mm}$ ($722.84\,\text{pt}$).

### 2. Quy tắc Lề Đối Xứng Qua Gáy (Mirrored Margin Spreads)
Khi mở hai trang đối diện (Trang Chẵn Verso ở bên trái, Trang Lẻ Recto ở bên phải):
- **Trang Chẵn (Verso):**
  - Lề ngoài (trái): $18.0\,\text{mm}$.
  - Khối văn bản: $168.0\,\text{mm}$.
  - Lề trong (phải, hướng vào gáy): $24.0\,\text{mm}$.
- **Trang Lẻ (Recto):**
  - Lề trong (trái, hướng vào gáy): $24.0\,\text{mm}$.
  - Khối văn bản: $168.0\,\text{mm}$.
  - Lề ngoài (phải): $18.0\,\text{mm}$.
- **Khoảng hở gáy tổng cộng (Total Spine Clearance):** $24.0 + 24.0 = 48.0\,\text{mm}$. Khoảng cách này đảm bảo dù sách được gia công bằng keo nhiệt hay khâu chỉ, toàn bộ khối văn bản và code đều phẳng phiu, không bị uốn cong che khuất tầm mắt độc giả.

### 3. Hình học Bố cục 2 Cột Error Atlas
- **Khổ rộng cột trái (Triệu chứng):** $80.0\,\text{mm}$ ($226.77\,\text{pt}$).
- **Rãnh phân cách giữa (Gutter):** $8.0\,\text{mm}$ ($22.68\,\text{pt}$).
- **Khổ rộng cột phải (Nguyên nhân & Khắc phục):** $80.0\,\text{mm}$ ($226.77\,\text{pt}$).
- **Tổng chiều rộng:** $80.0 + 8.0 + 80.0 = 168.0\,\text{mm}$ (Trùng khớp $100\%$ với vùng in khả dụng).

---

## IV. BẢO TỒN BẤT BIẾN VÀ ĐÁNH GIÁ RỦI RO HỒI QUY

### 1. Các Bất Biến Tuyệt Đối Được Bảo Vệ
- **Không sửa đổi Renderer sản xuất:** Tệp `scripts/build_pdf.py` và `scripts/book_style.py` được giữ nguyên trạng $100\%$. Toàn bộ hệ thống thử nghiệm của Agent 2 hoạt động độc lập bên trong `book/design/agent2-2026/sources/`.
- **Không sửa đổi Nội dung Bản thảo:** Toàn bộ 30 chương sách (`book/chapters/00-*.md` đến `29-*.md`), các bài thực hành (`labs/`) và phụ lục không bị thay đổi bất kỳ ký tự nào.
- **Không thay đổi MASTER PROMPT:** Tệp `MASTER PROMPT.txt` giữ nguyên nguyên tắc sư phạm và cam kết học thuật.
- **Không rebuild Release PDF hiện hành:** Tệp `Golang_Master.pdf` không bị build lại; mã băm SHA-256 bất biến:
  `f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09`.
- **Trạng thái xuất bản:** Tiếp tục duy trì tuyên bố chính thức:
  `PUBLICATION_STATUS = BLOCKED_PENDING_EVIDENCE`.

### 2. Phân Tích Rủi Ro Hồi Quy Khi Tích Hợp Vào Sản Xuất (Production Handoff)
1. **Rủi ro dồn trang (Pagination Cascade):** Khi áp dụng quy chuẩn khoảng cách dòng mới (leading 15.2pt thay vì 15.0pt) và ép buộc `keepWithNext=True` trên toàn bộ tiêu đề, tổng số trang của bản thảo có thể tăng từ 493 trang lên khoảng 510–525 trang. Điều này sẽ làm thay đổi bảng chỉ mục trang (Index) và cần chạy lại quy trình kiểm toán tọa độ trang.
2. **Rủi ro sao chép mã nguồn (Code Clipboard Friction):** Nếu áp dụng giải pháp đánh số dòng bằng canvas, người đọc copy code từ PDF sẽ bị dính số dòng. Do đó, Agent 2 đề xuất phương án chính thức: **Chỉ hiển thị số dòng trên các khối code giải thích ngắn, còn khối code lab lớn sẽ không hiển thị số dòng trong luồng text stream, hoặc cung cấp tệp mã nguồn đính kèm (PDF attachments).**

---

*Đặc tả được phê duyệt nội bộ bởi Agent 2 — Art Direction, Editorial Design & Print Production.*
