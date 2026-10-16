# BÁO CÁO VI CHỈNH KỸ THUẬT SƠ ĐỒ CHƯƠNG 04 (AGENT 2)
**Ngày thực hiện:** 16/10/2026  
**Nhánh công việc:** `design/ch04-agent2-redesign` (baseline: `5cffe5e`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và ChatGPT review độc lập trước khi tích hợp)

---

## 1. Mục tiêu vi chỉnh kỹ thuật cuối cùng (Final Diagram Corrections)
1. **Strict Content Lock:** Giữ nguyên 100% nội dung Markdown `book/chapters/04-bien-loi.md`, code block, bảng, caption, typography và `Golang_Master.pdf`.
2. **Hình 4.1 (`error-boundary-trace.png`):**
   - **Bổ sung ghi map `registry[name] = service`:** Đặt ngay sau `service.Record(false)` trong nhánh probe thất bại, kèm chú thích rõ ràng `// ghi bản sao đã sửa vào map`. Thể hiện đúng ngữ nghĩa Go: `Service` lấy từ map là bản sao giá trị, nên sau khi mutate trạng thái phải gán ngược lại map `registry` để lưu vết.
   - **Thứ tự thực thi khớp 100% `applyProbe` (dòng 127–135):**
     1. `err := run(service.Endpoint)` (chạy probe)
     2. `service.Record(false)` (cập nhật trạng thái bản sao)
     3. `registry[name] = service` (lưu bản sao vào registry)
     4. `failed := &ProbeFailure{ Service, Endpoint, Cause: err }` (đóng gói struct metadata)
     5. `return fmt.Errorf("probe: %w", failed)` (bọc `%w` tại biên)
   - **Tăng cường Visual QA & độ lớn chữ:**
     * Loại bỏ dòng chữ ký 78 ký tự chữ nhỏ 5.6 pt ở hộp trên cùng; thay bằng tiêu đề súc tích `BIÊN THAO TÁC applyProbe // RẼ NHÁNH THEO REGISTRY` (font 6.8 pt) và lệnh cốt lõi `service, found := registry[name]` (font 7.0 pt).
     * Toàn bộ chữ trong sơ đồ đạt kích thước `>= 6.0 pt` (chủ đạo 6.3–7.0 pt), dễ đọc hoàn toàn tại kích thước in thực tế `291.21 × 362.83 pt`.
     * Tách `return fmt.Errorf(...)` thành 2 dòng, giải quyết triệt để lỗi tràn mép phải.
     * Cân bằng đối xứng hoàn hảo giữa Cột 1 và Cột 2: Hộp trên (`y=134, h=122`), Huy hiệu chuyển tiếp (`y=125`), Hộp Caller (`y=28, h=88`).
3. **Hình 4.2 (`cancellation-cleanup-trace.png`):**
   - **Hoàn chỉnh cú pháp Go trích đoạn `defer func() { ... }()`:** Bổ sung cặp dấu gọi hàm `}()` ở cuối khối anonymous function, bảo đảm tính hợp lệ cú pháp của Go.
   - **Khép kín các khối `if`:** Đóng dấu ngoặc `}` đầy đủ ở Cột 1 (`if err := ctx.Err(); err != nil { return err }`) và Cột 2 (`if err != nil { return fmt.Errorf(...) }`).
   - **Bảo toàn chính sách lỗi:** Giữ nguyên chính sách named return `(err error)` và phạm vi kết luận giới hạn chuẩn xác: `[PHẠM VI runWithSession]`.
4. **Visual QA:**
   - Cả 2 hình được đối chiếu 1:1 với kích thước master PDF và kiểm tra trực quan qua specimen. Không còn tình trạng cắt chữ, đè nét hay tràn viền.

---

## 2. Kết quả kiểm định tự động (Verification Suite)
- `python scripts/test_publication_contracts.py`: **16/16 PASS (100%)**
- `python scripts/validate_code_width.py`: **PASS (0 overflow lines)**
- `git diff main -- book/chapters/04-bien-loi.md`: **0 DIFF (Tài liệu bài giảng Markdown hoàn toàn không đổi)**
- `git diff main -- book/chapters/`: **0 DIFF (Toàn bộ Markdown sách được bảo toàn nguyên vẹn)**
- Visual QA (kiểm tra trực quan bằng `view_file` trên 2 trang specimen):
  - Hình 4.1: Đầy đủ bước `registry[name] = service`, 2 nhánh đối xứng thẳng hàng, font chữ to rõ (>= 6.0 pt), không tràn viền.
  - Hình 4.2: Cú pháp `defer func() { ... }()` hoàn chỉnh, 3 cột thẳng tắp, chính sách lỗi và phạm vi session chính xác tuyệt đối.

---

## 3. Danh mục tệp cập nhật
1. `assets/diagrams/error-boundary-trace.png` (PNG xuất bản 320 DPI, 1295 × 1613 px, tỉ lệ 0.8026)
2. `assets/diagrams/cancellation-cleanup-trace.png` (PNG xuất bản 320 DPI, 2117 × 1440 px, tỉ lệ 1.4702)
3. `book/design/agent2-ch04/ch04_preview.pdf` (PDF preview 2 trang độc lập tại kích thước tích hợp 1:1)
4. `book/design/agent2-ch04/specimens/ch04_diagrams_p01.png` (Specimen Hình 4.1)
5. `book/design/agent2-ch04/specimens/ch04_diagrams_p02.png` (Specimen Hình 4.2)
6. `scripts/ch04_vector_diagrams.py` (Script ReportLab cập nhật logic vẽ sơ đồ)
7. `scripts/build_ch04_preview.py` (Script dựng PDF preview 2 trang)
8. `book/design/agent2-ch04/REPORT_AGENT2_CH04.md` (Báo cáo vi chỉnh này)
