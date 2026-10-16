# BÁO CÁO VI CHỈNH KỸ THUẬT SƠ ĐỒ CHƯƠNG 05 (AGENT 2)
**Ngày thực hiện:** 16/10/2026  
**Nhánh công việc:** `design/ch05-agent2-redesign` (baseline: `4870844`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và reviewer kiểm tra độc lập trước khi phê duyệt tích hợp)

---

## 1. Mục tiêu vi chỉnh kỹ thuật chính xác mã nguồn (Technical Corrections & Visual Redesign)
1. **Strict Content Lock:** Giữ nguyên tuyệt đối 100% nội dung Markdown `book/chapters/05-thiet-ke-package.md`, toàn bộ code block, bảng, caption, typography và file sách gốc `Golang_Master.pdf`.
2. **Đối chiếu mã nguồn thực tế trong `labs/part5-package-design/`:**
   - **Gói `probe`:** Loại bỏ `probe.go` (tệp không tồn tại trong repository). Chỉ ghi nhận đúng các tệp hiện hữu: `check.go` và `doc.go`.
   - **Mô tả Runner:** Sửa lại đúng bản chất implementation trong `main.go`: đây là `stub runner: func(...) error { return nil }` (hàm giả lập trả `nil`), không phải network runner thực sự.
   - **Xử lý luồng lỗi (Output Separation):**
     * Lỗi config: Ghi `os.Stderr` và dừng process với mã thoát `os.Exit(2)`.
     * Lỗi probe: Ghi `stdout` (`fmt.Printf("%s: %v\n", ...)`) và tiếp tục vòng lặp (`continue`).
     * Thành công: Ghi `stdout` (`fmt.Printf("%s healthy=true\n", ...)`).
   - **Đầu vào cấu hình:** Loại bỏ mô tả về cờ lệnh CLI (flags chưa được triển khai); đồng bộ chính xác với `config.LoadTargets(os.LookupEnv)` và quy trình mapping struct sang `probe.Service`.
   - **Chuẩn hóa nhãn `Result`:** Sử dụng đúng định nghĩa kiểu Go đầy đủ `type Result struct { Service string }`, giải thích rõ chỉ định danh service đã kiểm tra thành công, không chứa trường `Healthy bool` giả định.
   - **Phân định rõ ràng giữa quy tắc bắt buộc của Go vs chính sách kiến trúc dự án:**
     * *Quy tắc bắt buộc của Go (Compiler Enforced):* Cơ chế `internal/` giới hạn import theo cây thư mục cha; trình biên dịch từ chối mọi chu trình import (`import cycle not allowed`).
     * *Chính sách kiến trúc dự án (Project Architectural Policy):* Hướng phụ thuộc một chiều từ `cmd/opsprobe`; `probe` và `config` hoàn toàn độc lập, không import ngược `cmd`, không import chéo nhau.
3. **Visual Redesign (Thuần đen trắng / Grayscale & Giảm mật độ):**
   - Loại bỏ hoàn toàn các chi tiết màu đỏ (khung đỏ, nền đỏ, chữ đỏ). Chuyển sang phong cách đơn sắc xuất bản chuyên nghiệp của sách (`#1A1A1A`, `#2D3748`, `#CBD5E1`, `#F1F5F9`).
   - Huy hiệu `1` và `2` dạng vector sắc nét trên đường mũi tên phụ thuộc.
   - Ký hiệu cấm vector `✕` đơn sắc ở rào cản trung tâm và dải chính sách chân hộp.
   - Mật độ chữ thông thoáng, nhãn đọc rõ ràng ở kích thước 369,13 × 362,83 pt (khớp 1:1 với bounding box của Hình 19 trên Trang 104 của `Golang_Master.pdf`).

---

## 2. Kết quả kiểm định tự động (Verification Suite)
- `python scripts/test_publication_contracts.py`: **16/16 PASS (100%)**
- `python scripts/validate_code_width.py`: **PASS (0 dòng tràn lề)**
- `git diff main -- book/chapters/05-thiet-ke-package.md`: **0 DIFF (Tài liệu bài giảng hoàn toàn nguyên vẹn)**
- `git diff main -- book/chapters/`: **0 DIFF (Toàn bộ Markdown sách được bảo toàn)**
- `Golang_Master.pdf`: **KHÔNG THAY ĐỔI** (Bảo toàn 614 trang nguyên bản)

---

## 3. Danh mục tệp cập nhật trên branch `design/ch05-agent2-redesign`
1. `assets/diagrams/package-boundary-graph.png` (PNG vector xuất bản 320 DPI, 1641 × 1613 px, thuần đen trắng)
2. `book/design/agent2-ch05/ch05_preview.pdf` (PDF preview độc lập 1 trang tại kích thước 1:1)
3. `book/design/agent2-ch05/specimens/ch05_diagrams_p01.png` (Specimen trực quan của trang preview)
4. `scripts/ch05_vector_diagrams.py` (Script ReportLab cập nhật các vi chỉnh kỹ thuật)
5. `scripts/build_ch05_preview.py` (Script dựng PDF preview và xuất specimen)
6. `book/design/agent2-ch05/REPORT_AGENT2_CH05.md` (Báo cáo vi chỉnh này)
