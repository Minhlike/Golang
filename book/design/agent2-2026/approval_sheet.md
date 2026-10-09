# PHIẾU ĐỆ TRÌNH PHÊ DUYỆT HỆ THỐNG THIẾT KẾ 2026
## Executive Approval Sheet — Golang Book Design System 2026

**Kính gửi:** Tác giả Đoàn Ngọc Hoàng Minh  
**Người lập phiếu:** Agent 2 (Art Direction, Editorial Design & Print Production)  
**Tài liệu nghiệm thu chính:** `book/design/agent2-2026/design_catalog.pdf` (28 trang A4, hoàn chỉnh)  
**Ảnh kết xuất 28 trang:** `book/design/agent2-2026/renders/catalog_p01.png` đến `catalog_p28.png`  
**Nhánh Git:** `design/agent2-object-specimens`  
**Baseline commit:** `bb00a9ad33e3cd5115928dc3542d2ce66c8d08d8`  
**Ngày đệ trình:** 09/10/2026  

---

## I. TỔNG QUAN KẾT QUẢ CÔNG TÁC THIẾT KẾ CỦA AGENT 2

Sau khi Tác giả bác bỏ các mẫu bìa A–D phẳng trước đây từ `catalog-2026`, Agent 2 đã tái cấu trúc toàn diện hệ thống mỹ thuật và chế bản xuất bản:
1. **Thiết lập 3 Concept Bìa Sách Hoàn Toàn Mới:** Bắt nguồn từ các nghiên cứu nghệ thuật và kiến trúc kinh điển (*Manual of Section* của Princeton Architectural Press, *Envisioning Information* của Edward Tufte, và *Typographie* của Emil Ruder). Mỗi concept đều có bản in phẳng 300 DPI, nguồn vector có thể chỉnh sửa (`.svg`, `.pdf`), phối cảnh 3D gáy 3.5cm và tài liệu phân tích không gian.
2. **Quy chuẩn Toàn Bộ Hơn 30 Đối Tượng Thiết Kế:** Xây dựng ma trận KEEP / IMPROVE / REPLACE chi tiết cho Nhóm A (Bìa), Nhóm B (Typography H1–H4, khóa mồ côi), Nhóm C (Code block, Terminal, Booktabs, DevOps Grid, Sơ đồ kỹ thuật thật từ repository) và Nhóm D (Điểm dừng suy luận, Lời giải văn xuôi liên tục, Thử thách Lab, Bố cục 2 cột Error Atlas).
3. **Thực Hiện 8 Trang Mẫu Thực Tế (4 Cặp Trang Đôi Spreads):** Sử dụng $100\%$ văn bản và mã nguồn thật từ Ch01, Ch02, Ch10, Ch23; kiểm chứng lề đối xứng qua gáy (Lề trong 24mm, Lề ngoài 18mm) và huy hiệu Provenance truy xuất nguồn gốc chính xác đến từng dòng mã.
4. **Kiểm Toán Trực Quan & Sao Chép Mã Nguồn (QA Audit):** Đảm bảo $100\%$ ký tự Unicode tiếng Việt không lỗi font; phân tích trung thực cơ chế `expandtabs(4)` của ReportLab và đề xuất giải pháp kỹ thuật triệt để.

---

## II. CÁC QUYẾT ĐỊNH CẦN TÁC GIẢ PHÊ DUYỆT (DECISION GATE)

Kính đề nghị Tác giả xem xét và đưa ra quyết định lựa chọn đối với 4 hạng mục trọng tâm sau:

### 1. Lựa Chọn Phương Án Bìa Sách Chính Thức (Cover Concept Selection)

| Phương Án | Tên Concept | Nguồn Cảm Hứng & Bản Chất Kỹ Thuật | Đánh Giá Của Agent 2 |
|---|---|---|---|
| **LỰA CHỌN A (Khuyến nghị)** | **Concept 1: Mặt Cắt Kiến Trúc & Phân Tầng Không Gian** | *Manual of Section* (Princeton Arch Press) & Peter Eisenman (MoMA). Chiếu trục đo axonometric 28° phân tầng 4 lớp: Linux Kernel Ring-0 → Go Runtime GMP → Service Mesh Deck → K8s / eBPF Tower. | **Khuyến nghị nhiệt liệt nhất.** Phản ánh chính xác $100\%$ cấu trúc đi từ sâu lên cao của cuốn sách; mang phong thái bản thiết kế cơ khí chính xác của kỹ sư trưởng. |
| **LỰA CHỌN B** | **Concept 2: Khắc Đồng Khoa Học & Trường Dòng Chảy Tô-pô** | Edward Tufte (*Envisioning Information*) & Ernst Haeckel (*Kunstformen der Natur*). Mô hình toán học CSP: Streamline biến thiên độ dày nét (0.3–1.2pt) mô tả rendezvous barrier, áp suất ngược và kênh đệm. | **Rất tốt.** Phù hợp nếu Tác giả muốn định vị cuốn sách như một công trình bách khoa toàn thư toán học hàn lâm kinh điển của thế kỷ. |
| **LỰA CHỌN C** | **Concept 3: Monolith Kiến Tạo & Kiểu Chữ Động Thụy Sĩ** | Emil Ruder (*Typographie*) & Josef Müller-Brockmann. Lưới Thụy Sĩ 12 cột, kiểu chữ 3D extruded đúc khối bê tông kiên cố, tương phản cực hạn. | **Tốt.** Thể hiện tinh thần tối giản, thực dụng, đơn khối vững chắc của Go trong hạ tầng hiện đại. |

*Lựa chọn của Tác giả:* `[ ] Lựa chọn A (Concept 1)` | `[ ] Lựa chọn B (Concept 2)` | `[ ] Lựa chọn C (Concept 3)`

---

### 2. Quy Chuẩn Hiển Thị Mã Nguồn & Tương Tác Clipboard (Code Presentation)

Khi độc giả quét chuột sao chép mã nguồn từ bản PDF điện tử:
- **Phương Án 1 (Chuẩn hiện hành):** Mã nguồn hiển thị thụt lề 4 dấu cách (spaces). Mọi IDE (VS Code, GoLand) tự động chạy `gofmt` chuẩn hóa lại ngay khi lưu tệp.
- **Phương Án 2 (Tách biệt số dòng):** Chỉ hiển thị số dòng trên các khối code lý thuyết ngắn (dưới 15 dòng). Các khối code bài tập thực hành dài sẽ không vẽ số dòng trong text stream để độc giả copy-paste một chạm không bị dính số.
- **Phương Án 3 (Đính kèm tệp nguồn - PDF Attachments):** Nhúng trực tiếp toàn bộ thư mục `labs/` vào container nhị phân của tệp PDF phát hành. Độc giả nhấp đúp để mở file gốc với mã băm SHA-256 trùng khớp $100\%$.

*Khuyến nghị của Agent 2:* **Kết hợp Phương Án 2 + Phương Án 3.**

*Lựa chọn của Tác giả:* `[ ] Phương Án 1` | `[ ] Phương Án 2` | `[ ] Kết hợp Phương Án 2 & 3`

---

### 3. Quy Chuẩn Bảng Biểu Kỹ Thuật (Table Styling Strategy)

- **Mẫu A (Booktabs Kinh Điển):** Chỉ dùng đường kẻ ngang (đỉnh 1.2pt, header 0.6pt, đáy 1.2pt), triệt tiêu hoàn toàn đường kẻ dọc. Áp dụng cho các bảng phân tích lý thuyết, cú pháp và so sánh khái niệm.
- **Mẫu B (Ma Trận DevOps Grid):** Kẻ lưới ô vuông mỏng 0.4pt màu xám `#CCCCCC`. Áp dụng cho các bảng ma trận tham số cấu hình phức tạp (cgroup, kernel tuning, cờ CLI).

*Khuyến nghị của Agent 2:* **Áp dụng theo ngữ cảnh:** Mẫu A cho bảng lý thuyết sư phạm, Mẫu B cho ma trận cấu hình thực chiến.

*Lựa chọn của Tác giả:* `[ ] Đồng ý quy tắc phân loại theo ngữ cảnh` | `[ ] Chỉ dùng đồng nhất Mẫu A` | `[ ] Chỉ dùng đồng nhất Mẫu B`

---

### 4. Định Lượng Giấy & Công Nghệ Đóng Gáy (Paper Stock & Binding)

Cuốn sách có dung lượng dự kiến từ 480 đến 520 trang khổ A4:
- **Định lượng giấy đề xuất:** Giấy Woodfree cao cấp 80 gsm (độ dày $0.108\,\text{mm}$/tờ, độ dày gáy sách dự kiến $\approx 28.1\,\text{mm}$) hoặc Giấy xốp Bulky Nhật 70 gsm (độ dày gáy $\approx 35.1\,\text{mm}$, nhẹ tay, chống lóa).
- **Công nghệ gia công gáy bắt buộc:** **Khâu chỉ từng tay sách kết hợp dán keo nhiệt PUR (Smyth Sewn + PUR Binding)**. Tuyệt đối không dùng dán keo nhiệt thông thường (EVA) vì sẽ gây gãy gáy và không thể mở phẳng 180° trên bàn làm việc.

*Khuyến nghị của Agent 2:* Khâu chỉ dán keo PUR trên giấy Woodfree 80 gsm.

*Lựa chọn của Tác giả:* `[ ] Đồng ý khuyến nghị khâu chỉ + keo PUR` | `[ ] Đề xuất phương án khác`

---

## III. TUYÊN BỐ TRẠNG THÁI XUẤT BẢN HIỆN HÀNH

Theo quy định bất biến của dự án:
- `PRINT_PRODUCTION_STATUS = AWAITING_PRINT_SPEC` (Chờ Tác giả và nhà in xác nhận thông số lô giấy thực tế trước khi chốt độ dày gáy in thương mại).
- `PUBLICATION_STATUS = BLOCKED_PENDING_EVIDENCE` (Không tự ý nâng trạng thái xuất bản khi chưa có chỉ thị chính thức từ Tác giả).
- Toàn bộ thay đổi của Agent 2 được cô lập an toàn trong branch `design/agent2-object-specimens`. Bản phát hành cũ `Golang_Master.pdf` và các tệp trong `main` được bảo vệ nguyên vẹn $100\%$.

---

*Kính trình Tác giả xem xét và cho ý kiến chỉ đạo.*  
**Đại diện Agent 2 — Art Direction & Editorial Design**
