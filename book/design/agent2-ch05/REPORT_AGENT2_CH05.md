# BÁO CÁO THIẾT KẾ SƠ ĐỒ KỸ THUẬT CHƯƠNG 05 (AGENT 2)
**Ngày thực hiện:** 16/10/2026  
**Nhánh công việc:** `design/ch05-agent2-redesign` (baseline: `3389e34` trên `main`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và reviewer kiểm tra độc lập trước khi phê duyệt tích hợp)

---

## 1. Mục tiêu thiết kế lại sơ đồ Chương 05 (Package là ranh giới)
1. **Strict Content Lock:** Giữ nguyên tuyệt đối 100% nội dung Markdown `book/chapters/05-thiet-ke-package.md`, toàn bộ code block, bảng, caption, typography và file sách gốc `Golang_Master.pdf`.
2. **Hình 19 (`package-boundary-graph.png`):**
   - **Thay thế hoàn toàn sơ đồ cũ (đường cong chéo, ghi chú bong bóng PlantUML sơ sài)** bằng sơ đồ véc-tơ độ chính xác cao theo chuẩn kiến trúc đơn sắc tối giản (Monochrome B&W / ReportLab Vector) của sách.
   - **Bố cục phân tầng chuẩn Clean Architecture / Hexagonal / Composition Root:**
     * **Tầng trên (Composition Root - `cmd/opsprobe`):**
       - Thể hiện rõ vai trò điểm khởi đầu của ứng dụng (`main.go`).
       - Cột trái: Tiếp nhận cờ lệnh CLI & `os.LookupEnv`; nạp cấu hình; **ánh xạ ranh giới kiểu** `config.Target → probe.Service` (gán `Name`, `Host`, `Port`, bảo vệ không để cấu hình rò rỉ vào domain).
       - Cột phải: Khởi tạo runner thực thi mạng; điều phối vòng lặp `probe.Check(...)`; **sở hữu tầng hiển thị (Presentation Layer)**: in `healthy=true` ra stdout, in lỗi ra stderr, trả mã thoát exit code.
     * **Tầng tương tác (Hai mũi tên phụ thuộc có thứ tự rõ ràng):**
       - Mũi tên ①: Nạp cấu hình mục tiêu (`config.DefaultTargets()` / `LoadTargets()`).
       - Mũi tên ②: Gọi thực thi (`probe.Check(ctx, service, runner)`).
     * **Tầng dưới (Hai gói độc lập đặt song song đối xứng):**
       - **Gói trái (`internal/config` - Ranh giới cấu hình nội bộ):**
         + Tag cơ chế toolchain: `internal/` giới hạn import theo cây thư mục cha (parent tree).
         + Tệp `config.go`, mô hình `Target{Name, Host, Port}`.
         + Hàm `DefaultTargets() []Target`: Cấp phát và trả về slice độc lập mới (bảo toàn value semantics và ownership, ngăn chặn mutation cấu hình mặc định).
         + Hàm `LoadTargets(lookup LookupEnv)`: Tách `host:port` bằng `net.SplitHostPort` chuẩn socket; kiểm tra range cổng hợp lệ `1..65535`; nhận `LookupEnv` func để kiểm thử độc lập mà không can thiệp biến môi trường process chung.
         + Cảnh báo ranh giới: **CẤM import `probe` & CẤM import ngược `cmd`**.
       - **Gói phải (`probe` - Thư viện nghiệp vụ lõi có thể tái sử dụng):**
         + Tag API contract: Thư viện tái sử dụng (`Public API contract`).
         + Tệp `probe.go`, `doc.go`, `check.go`.
         + Mô hình `Result{Service}`: Tối giản, **loại bỏ hoàn toàn trường `Healthy bool` giả** (thành công trả Result; lỗi đi qua error chain).
         + Hàm `Check(ctx, Service, Runner)`: Kiểm tra `ctx.Err()`, hủy ngay không gọi runner nếu context đã hủy; hoàn toàn độc lập với thiết bị đầu ra (output device); tuyệt đối không chứa `fmt.Println` hay cờ lệnh CLI.
         + Cảnh báo ranh giới: **CẤM import `config` & CẤM import ngược `cmd`**.
     * **Rào cản phân cách trung tâm (Central Barrier):**
       - Đường đứt nét phân cách dọc kèm biểu tượng cấm vector `✕` thể hiện rõ hai gói `internal/config` và `probe` hoàn toàn độc lập, không import lẫn nhau.
     * **Chân trang kỹ thuật (Footer - Import DAG Rules):**
       - Tuyên bố nguyên tắc phụ thuộc một chiều (One-Way Dependency).
       - Tuyên bố tính chất độc lập tuyệt đối của gói thư viện `probe`.
       - Tuyên bố quy tắc Go toolchain: Đồ thị phi chu trình (DAG), compiler từ chối mọi chu trình import (`import cycle not allowed`).
3. **Visual QA & Publication Match:**
   - Kích thước xuất bản thực tế: **369.13 × 362.83 pt** (tỉ lệ AR = 1.01735, khớp 1:1 với bounding box của Hình 19 trên Trang 104 của `Golang_Master.pdf`, xref 246).
   - Xuất bản ảnh độ phân giải cao 320 DPI (1641 × 1613 px), chữ sắc nét, độ tương phản cao, font chữ chính quy `BookSans`, `BookSansBold`, `BookMono` từ 6.0–8.8 pt.
   - Không có hiện tượng cắt chữ, đè nét, mất glyph hay tràn biên.

---

## 2. Kết quả kiểm định tự động (Verification Suite)
- `python scripts/test_publication_contracts.py`: **16/16 PASS (100%)**
- `python scripts/validate_code_width.py`: **PASS (0 dòng tràn lề)**
- `git diff main -- book/chapters/05-thiet-ke-package.md`: **0 DIFF (Tài liệu bài giảng hoàn toàn nguyên vẹn)**
- `git diff main -- book/chapters/`: **0 DIFF (Toàn bộ Markdown sách được bảo toàn)**
- `Golang_Master.pdf`: **KHÔNG THAY ĐỔI** (Bảo toàn 614 trang nguyên bản, giữ nguyên cho đến khi được duyệt)

---

## 3. Danh mục tệp cập nhật & tạo mới trên branch `design/ch05-agent2-redesign`
1. `assets/diagrams/package-boundary-graph.png` (PNG vector xuất bản 320 DPI, 1641 × 1613 px)
2. `book/design/agent2-ch05/ch05_preview.pdf` (PDF preview độc lập hiển thị đúng 100% kích thước 1:1)
3. `book/design/agent2-ch05/specimens/ch05_diagrams_p01.png` (Specimen trực quan của trang preview)
4. `scripts/ch05_vector_diagrams.py` (Script ReportLab sinh sơ đồ véc-tơ độ chính xác cao)
5. `scripts/build_ch05_preview.py` (Script dựng PDF preview và xuất specimen)
6. `book/design/agent2-ch05/REPORT_AGENT2_CH05.md` (Báo cáo này)
