# BÁO CÁO VI CHỈNH KỸ THUẬT SƠ ĐỒ CHƯƠNG 04 (AGENT 2)
**Ngày thực hiện:** 16/10/2026  
**Nhánh công việc:** `design/ch04-agent2-redesign` (baseline: `8c5614f`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và ChatGPT review độc lập trước khi tích hợp)

---

## 1. Mục tiêu vi chỉnh chính xác mã nguồn cuối cùng (Last Source-Accuracy Correction)
1. **Strict Content Lock:** Giữ nguyên 100% nội dung Markdown `book/chapters/04-bien-loi.md`, code block, bảng, caption, typography và `Golang_Master.pdf`.
2. **Hình 4.1 (`error-boundary-trace.png`):**
   - **Khôi phục nguyên văn return theo mã nguồn Chương 4 (dòng 135):**
     Khôi phục chuẩn xác định dạng và tham số đầy đủ:
     ```go
     return fmt.Errorf(
       "probe %q: %w", name, failed)
     ```
     Trình bày 2 dòng gọn gàng, không bị tràn hay chạm viền hộp.
   - **Làm rõ tính chất sentinel `ErrUnknownService`:**
     Thay thế khẳng định tuyệt đối `KHÔNG chứa ErrUnknownService` bằng diễn đạt chính xác theo ngữ nghĩa Go:
     `• Không tự tạo ErrUnknownService`
     `  (nguyên nhân run() vẫn có thể chứa)`
     Và chú thích chân trang: `applyProbe không tự sinh ErrUnknownService ở nhánh này`. Tránh gây hiểu lầm cho người học rằng error chain xuất phát từ probe bên ngoài không bao giờ có thể mang sentinel đó.
   - **Bảo toàn toàn bộ thành phần đã đạt:**
     * Thao tác ghi map `registry[name] = service` ngay sau `service.Record(false)` kèm chú thích `// ghi bản sao đã sửa vào map`.
     * Toàn bộ font chữ $\ge 6.0\text{ pt}$ (chủ đạo 6.2–7.0 pt).
     * Bố cục đối xứng hoàn hảo giữa Cột 1 và Cột 2 trên cả 3 tầng (hộp trên `h=124`, huy hiệu giữa `y=124`, hộp caller `h=92`).
3. **Hình 4.2 (`cancellation-cleanup-trace.png`):**
   - Giữ nguyên 100% bản vẽ véc-tơ đã được kiểm định đạt chuẩn ở lượt trước. Cú pháp `defer func() { ... }()`, các khối `if` khép kín, chính sách named return và phạm vi `[PHẠM VI runWithSession]` được bảo toàn nguyên vẹn.
4. **Visual QA:**
   - Cả 2 hình được đối chiếu 1:1 với kích thước Master PDF (`291.21 × 362.83 pt` và `476.22 × 323.91 pt`) và kiểm tra trực quan qua specimen. Không có hiện tượng cắt chữ, đè nét hay tràn lề.

---

## 2. Kết quả kiểm định tự động (Verification Suite)
- `python scripts/test_publication_contracts.py`: **16/16 PASS (100%)**
- `python scripts/validate_code_width.py`: **PASS (0 overflow lines)**
- `git diff main -- book/chapters/04-bien-loi.md`: **0 DIFF (Tài liệu bài giảng Markdown hoàn toàn không đổi)**
- `git diff main -- book/chapters/`: **0 DIFF (Toàn bộ Markdown sách được bảo toàn nguyên vẹn)**
- Visual QA (kiểm tra trực quan bằng `view_file` trên 2 trang specimen):
  - Hình 4.1: Khôi phục chính xác `return fmt.Errorf("probe %q: %w", name, failed)`, chú thích sentinel chuẩn mực, đối xứng hoàn hảo.
  - Hình 4.2: Giữ nguyên vẹn, 3 cột thẳng hàng, cú pháp và hợp đồng chuẩn xác.

---

## 3. Danh mục tệp cập nhật
1. `assets/diagrams/error-boundary-trace.png` (PNG xuất bản 320 DPI, 1295 × 1613 px, tỉ lệ 0.8026)
2. `assets/diagrams/cancellation-cleanup-trace.png` (PNG xuất bản 320 DPI, 2117 × 1440 px, tỉ lệ 1.4702 - giữ nguyên)
3. `book/design/agent2-ch04/ch04_preview.pdf` (PDF preview 2 trang độc lập tại kích thước tích hợp 1:1)
4. `book/design/agent2-ch04/specimens/ch04_diagrams_p01.png` (Specimen Hình 4.1)
5. `book/design/agent2-ch04/specimens/ch04_diagrams_p02.png` (Specimen Hình 4.2)
6. `scripts/ch04_vector_diagrams.py` (Script ReportLab cập nhật Hình 4.1)
7. `scripts/build_ch04_preview.py` (Script dựng PDF preview 2 trang)
8. `book/design/agent2-ch04/REPORT_AGENT2_CH04.md` (Báo cáo vi chỉnh này)
