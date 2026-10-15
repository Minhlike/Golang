# BÁO CÁO VI CHỈNH KỸ THUẬT SƠ ĐỒ CHƯƠNG 04 (AGENT 2)
**Ngày thực hiện:** 16/10/2026  
**Nhánh công việc:** `design/ch04-agent2-redesign`  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và ChatGPT review độc lập trước khi tích hợp)

---

## 1. Mục tiêu vi chỉnh kỹ thuật (Technical Micro-Fix)
1. **Strict Content Lock:** Giữ nguyên 100% nội dung Markdown `book/chapters/04-bien-loi.md`, code block, bảng, caption, typography và `Golang_Master.pdf`.
2. **Hình 4.1 (`error-boundary-trace.png`):**
   - Tách rời hoàn toàn hai nhánh nghiệp vụ độc lập xuất phát từ `applyProbe`:
     * **Nhánh 1 (Trái - Thiếu cấu hình):** `!found` $\rightarrow$ probe **không bao giờ được chạy**, registry không đổi state, trả lỗi bọc `%w` quanh sentinel `ErrUnknownService`. Caller sử dụng `errors.Is(err, ErrUnknownService)` để so khớp định danh lỗi phục vụ rẽ nhánh logic.
     * **Nhánh 2 (Phải - Probe thất bại):** Service tồn tại $\rightarrow$ gọi `run(service.Endpoint)` $\rightarrow$ probe lỗi $\rightarrow$ ghi nhận `service.Record(false)` $\rightarrow$ đóng gói struct `*ProbeFailure{ Service, Endpoint, Cause: err }` với `Unwrap() error { return f.Cause }` $\rightarrow$ bọc tiếp `%w` tại biên thao tác `applyProbe`. Caller sử dụng `errors.As(err, &failure)` để trích xuất an toàn kiểu struct metadata mà không parse chuỗi.
   - Loại bỏ ví dụ ngoài luồng `syscall.ECONNREFUSED`; toàn bộ biến, struct, error value đều khớp 100% mã nguồn bài giảng.
   - Làm rõ hai nhánh không dùng chung một error chain: chuỗi Nhánh 1 không có `*ProbeFailure`, chuỗi Nhánh 2 không có `ErrUnknownService`.
3. **Hình 4.2 (`cancellation-cleanup-trace.png`):**
   - Giữ bố cục 3 đường thực thi.
   - Làm rõ việc `Close()` chỉ được đăng ký sau khi acquire thành công là theo **contract cụ thể của `runWithSession`**, không tuyên bố tuyệt đối rằng mọi lỗi `open()` đều không có tài nguyên.
   - Thể hiện rõ chính sách named return `(err error)`: lỗi `run()` luôn được ưu tiên giữ nguyên; lỗi `Close()` phụ chỉ thay kết quả khi `run()` không có lỗi (`err == nil`).
   - Đánh dấu rõ khối code là trích đoạn logic contract (`// logic excerpt (named return)`).
4. **Visual QA:**
   - Kiểm tra và đảm bảo độ sắc nét, không chồng lấn tại kích thước xuất bản thực tế:
     * Hình 4.1: 291.21 × 362.83 pt (tỉ lệ 0.8026).
     * Hình 4.2: 476.22 × 323.91 pt (tỉ lệ 1.4702).
   - Căn thẳng hàng ngang các khối kết luận `[KẾT QUẢ]` ở chân cả 3 cột của Hình 4.2.

---

## 2. Kết quả kiểm định tự động (Verification Suite)
- `python scripts/test_publication_contracts.py`: **16/16 PASS (100%)**
- `python scripts/validate_code_width.py`: **PASS (0 overflow lines)**
- `git diff main -- book/chapters/04-bien-loi.md`: **0 DIFF (Tài liệu bài giảng Markdown hoàn toàn không đổi)**
- Visual QA (kiểm tra trực quan bằng `view_file` trên 2 trang specimen 200 DPI):
  - Hình 4.1: Hai cột song song độc lập, rẽ nhánh từ hộp `applyProbe`, nhãn phụ và code rõ ràng, không đè nét.
  - Hình 4.2: Ba cột thẳng hàng, chú thích hợp đồng và named return chuẩn mực, khoảng đệm thoải mái.

---

## 3. Danh mục tệp cập nhật
1. `assets/diagrams/error-boundary-trace.png` (PNG xuất bản 300 DPI, 1417 × 1765 px)
2. `assets/diagrams/cancellation-cleanup-trace.png` (PNG xuất bản 300 DPI, 1984 × 1350 px)
3. `book/design/agent2-ch04/ch04_preview.pdf` (PDF preview 2 trang độc lập)
4. `book/design/agent2-ch04/specimens/ch04_diagrams_p01.png` (Specimen Hình 4.1)
5. `book/design/agent2-ch04/specimens/ch04_diagrams_p02.png` (Specimen Hình 4.2)
6. `scripts/ch04_vector_diagrams.py` (Script vẽ véc-tơ ReportLab cập nhật)
7. `book/design/agent2-ch04/REPORT_AGENT2_CH04.md` (Báo cáo vi chỉnh này)
