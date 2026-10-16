# BÁO CÁO VI CHỈNH KỸ THUẬT SƠ ĐỒ CHƯƠNG 04 (AGENT 2)
**Ngày thực hiện:** 16/10/2026  
**Nhánh công việc:** `design/ch04-agent2-redesign` (baseline: `8422a1f`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và ChatGPT review độc lập trước khi tích hợp)

---

## 1. Mục tiêu vi chỉnh chính xác mã nguồn (Final Source-Accuracy Fix)
1. **Strict Content Lock:** Giữ nguyên 100% nội dung Markdown `book/chapters/04-bien-loi.md`, code block, bảng, caption, typography và `Golang_Master.pdf`.
2. **Hình 4.1 (`error-boundary-trace.png`):**
   - **Đồng bộ chữ ký hàm:** Thay chữ ký rút gọn không hợp lệ bằng chữ ký Go chính xác:
     `func applyProbe(registry map[string]Service, name string, run ProbeFunc) error`
     kèm nhãn khái niệm rõ ràng: `BIÊN THAO TÁC applyProbe // ĐIỂM RẼ NHÁNH NGHIỆP VỤ`.
   - **Khớp 100% cú pháp Go:** Đoạn trích khởi tạo struct khớp từng trường với dòng 96–103 của `04-bien-loi.md`:
     ```go
     failed := &ProbeFailure{
       Service:  service.Name,
       Endpoint: service.Endpoint,
       Cause:    err,
     }
     return fmt.Errorf("...: %w", failed)
     ```
   - **Phân định rõ ràng hai nhánh xử lý lỗi độc lập:**
     * **Nhánh 1 (Trái - Thiếu cấu hình):** `!found` $\rightarrow$ probe không chạy $\rightarrow$ bọc sentinel `ErrUnknownService` $\rightarrow$ Caller dùng `errors.Is(err, ErrUnknownService)` để so khớp định danh lỗi. Nhánh này tuyệt đối không chứa `*ProbeFailure`.
     * **Nhánh 2 (Phải - Probe thất bại):** Service tồn tại $\rightarrow$ gọi probe `run(service.Endpoint)` lỗi $\rightarrow$ đóng gói struct `*ProbeFailure` $\rightarrow$ Caller dùng `errors.As(err, &failure)` để trích xuất cấu trúc dữ liệu metadata `failure.Service`. Nhánh này tuyệt đối không chứa `ErrUnknownService`.
   - **Kích thước tích hợp thực tế:** Thiết kế đúng 1:1 theo geometry của `Golang_Master.pdf` (Trang 88, xref 212: `291.21 × 362.83 pt`, xuất bản 320 DPI = 1295 × 1613 px).
3. **Hình 4.2 (`cancellation-cleanup-trace.png`):**
   - **Đồng bộ tham số với bài giảng:** Đồng bộ biến `endpoint` trong `session, err := open(endpoint)` và `return run(ctx, endpoint, session)` thay vì viết tắt `ep`.
   - **Giới hạn phát biểu trong phạm vi sở hữu session:** Thay khẳng định tuyệt đối `Zero resource leak` bằng kết luận chuẩn xác giới hạn trong hợp đồng hàm:
     `[PHẠM VI runWithSession]`
     `• Không khởi tạo hay rò rỉ session`
     `• Không có session cần giải phóng` (Cột 1) / `• Không gọi Close() trên session lỗi` (Cột 2).
   - **Bảo toàn cơ chế named return:** Thể hiện rõ chính sách `(err error)`: lỗi `run()` luôn được ưu tiên giữ nguyên; lỗi `Close()` phụ chỉ gán đè khi `err == nil`.
   - **Đánh dấu trích đoạn hợp đồng:** Ghi rõ `// trích đoạn runWithSession` để người học không nhầm là toàn bộ mã nguồn có thể biên dịch trực tiếp độc lập.
   - **Kích thước tích hợp thực tế:** Thiết kế đúng 1:1 theo geometry của `Golang_Master.pdf` (Trang 99, xref 235: `476.22 × 323.91 pt`, xuất bản 320 DPI = 2117 × 1440 px).
4. **Visual QA:**
   - Đảm bảo độ sắc nét, phân cấp thị giác rõ ràng, font chữ BookSans / BookMono `>= 5.7 pt`.
   - Không có phần tử cắt viền, chồng nét hay tràn lề ở kích thước in ấn thực tế.

---

## 2. Kết quả kiểm định tự động (Verification Suite)
- `python scripts/test_publication_contracts.py`: **16/16 PASS (100%)**
- `python scripts/validate_code_width.py`: **PASS (0 overflow lines)**
- `git diff main -- book/chapters/04-bien-loi.md`: **0 DIFF (Tài liệu bài giảng Markdown hoàn toàn không đổi)**
- Visual QA (kiểm tra trực quan bằng `view_file` trên 2 trang specimen):
  - Hình 4.1: Chữ ký Go và cú pháp struct chính xác tuyệt đối, 2 nhánh tách bạch, bố cục hài hòa tại 291.21 × 362.83 pt.
  - Hình 4.2: Tên biến `endpoint` đồng bộ, 3 cột thẳng hàng, hộp kết luận giới hạn chính xác phạm vi `runWithSession` tại 476.22 × 323.91 pt.

---

## 3. Danh mục tệp cập nhật
1. `assets/diagrams/error-boundary-trace.png` (PNG xuất bản 320 DPI, 1295 × 1613 px, tỉ lệ 0.8026)
2. `assets/diagrams/cancellation-cleanup-trace.png` (PNG xuất bản 320 DPI, 2117 × 1440 px, tỉ lệ 1.4702)
3. `book/design/agent2-ch04/ch04_preview.pdf` (PDF preview 2 trang độc lập tại kích thước tích hợp 1:1)
4. `book/design/agent2-ch04/specimens/ch04_diagrams_p01.png` (Specimen Hình 4.1)
5. `book/design/agent2-ch04/specimens/ch04_diagrams_p02.png` (Specimen Hình 4.2)
6. `scripts/ch04_vector_diagrams.py` (Script ReportLab cập nhật chữ ký, cú pháp Go và bounds)
7. `scripts/build_ch04_preview.py` (Script dựng PDF preview 2 trang)
8. `book/design/agent2-ch04/REPORT_AGENT2_CH04.md` (Báo cáo vi chỉnh này)
