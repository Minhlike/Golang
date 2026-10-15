# BÁO CÁO THIẾT KẾ SƠ ĐỒ KỸ THUẬT CHƯƠNG 04 (AGENT 2)
**Ngày thực hiện:** 16/10/2026  
**Nhánh công việc:** `design/ch04-agent2-redesign`  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng phê duyệt thủ công trước khi tích hợp vào Master PDF)

---

## 1. Mục tiêu & Nguyên tắc thiết kế (Master Prompt)
1. **Strict Content Lock:** Giữ nguyên 100% nội dung văn bản Markdown (`book/chapters/04-bien-loi.md`), code block, bảng, caption và cấu trúc tài liệu. `git diff main -- book/chapters/04-bien-loi.md` = 0.
2. **Kỹ thuật đồ họa véc-tơ cao cấp (ReportLab Vector):**
   - Không dùng PlantUML mờ nhạt hay font Arial đơn điệu cũ.
   - Sử dụng bộ font xuất bản chuẩn: `BookSans`, `BookSansBold`, `BookMono`.
   - Bảng màu đơn sắc tối giản (Monochrome B&W / Grayscale), độ tương phản cao, vạch kẻ sắc nét.
3. **Khớp chính xác tỉ lệ khung hình (Aspect Ratio) với `Golang_Master.pdf`:**
   - **Hình 4.1 (xref 212, trang 88):** Kích thước hiển thị 291.21 × 362.83 pt (tỉ lệ đứng ~0.8026). Thiết kế véc-tơ chuẩn 340.0 × 423.6 pt (tỉ lệ 0.80264), vừa khít 100% không biến dạng khi tích hợp.
   - **Hình 4.2 (xref 235, trang 99):** Kích thước hiển thị 476.22 × 323.91 pt (tỉ lệ ngang ~1.4702). Thiết kế véc-tơ chuẩn 476.0 × 323.8 pt (tỉ lệ 1.4700), vừa khít 100% không biến dạng khi tích hợp.

---

## 2. Chi tiết kỹ thuật 2 sơ đồ Chương 4

### Hình 4.1: `error-boundary-trace.png` (Trang 88 Master PDF)
- **Tên:** RANH GIỚI LỖI // BẢO TOÀN NGUYÊN NHÂN & DỮ LIỆU CẤU TRÚC (ERROR WRAPPING CHAIN)
- **Ngữ nghĩa Go spec & runtime:**
  1. *Tầng nguyên nhân gốc (ProbeFunc):* Trả về lỗi nguyên thủy từ OS/mạng (ví dụ `syscall.ECONNREFUSED`), giữ identity lỗi gốc.
  2. *Tầng cấu trúc (*ProbeFailure):* Bọc nguyên nhân vào struct `ProbeFailure { Service, Endpoint, Cause }` và cung cấp `Unwrap() error { return f.Cause }`. Bảo đảm giữ identity gốc qua chuỗi unwrap mà không nối chuỗi thủ công.
  3. *Tầng biên thao tác (applyProbe):* Bổ sung bối cảnh operation qua `fmt.Errorf("probe %q: %w", name, failed)`. Động từ `%w` cho phép caller bóc tách từng lớp bối cảnh về nguyên nhân sâu nhất.
  4. *Phân nhánh quyết định tại Caller (Bên gọi):*
     - `errors.Is(err, target)`: Duyệt chuỗi `Unwrap()` để so khớp định danh lỗi sentinel (phục vụ rẽ nhánh logic).
     - `errors.As(err, &failure)`: Trích xuất trực tiếp struct `*ProbeFailure` để lấy dữ liệu nghiệp vụ (`Service`, `Endpoint`), loại bỏ hoàn toàn việc parse chuỗi thủ công.

### Hình 4.2: `cancellation-cleanup-trace.png` (Trang 99 Master PDF)
- **Tên:** VÒNG ĐỜI TÀI NGUYÊN & DEFER CLEANUP // 3 ĐƯỜNG ĐI TRONG runWithSession
- **Ngữ nghĩa Go spec & runtime:**
  1. *Đường 1 (Hủy trước khi mở):* `if err := ctx.Err(); err != nil` -> trả về lỗi hủy ngay lập tức; chưa gọi `open()`, chưa nhận tài nguyên; **KHÔNG** gọi `Close()` (zero resource leak, không dọn rác tài nguyên rỗng).
  2. *Đường 2 (Mở thất bại):* `session, err := open(ep); if err != nil` -> trả về lỗi mở; không có session hợp lệ, scope chưa nhận ownership; **KHÔNG** gọi `Close()` (tránh nil pointer dereference).
  3. *Đường 3 (Sở hữu session & thoát):* `defer session.Close()` chỉ được đăng ký ngay sau khi `open()` thành công.
     - *Chính sách bảo toàn lỗi gốc (Primary Error Preservation):* Khi hàm thoát, `defer` luôn chạy. Nếu `run()` phát sinh lỗi, kết quả giữ nguyên lỗi chính từ `run()`, lỗi dọn dẹp phụ từ `Close()` không được che giấu sự cố gốc; nếu `run()` thành công mà `Close()` lỗi thì mới trả lỗi từ `Close()`.
  4. *Căn chỉnh thị giác:* Cả 3 cột đều có các hộp kết quả `[KẾT QUẢ]` được căn thẳng hàng theo phương ngang (`y = 48 đến 92 pt`), tạo nhịp điệu kiến trúc liền mạch.

---

## 3. Kết quả kiểm định tự động (Verification Suite)
- `python scripts/test_publication_contracts.py`: **16/16 PASS (100%)**
- `python scripts/validate_code_width.py`: **PASS (0 overflow lines)**
- `git diff main -- book/chapters/04-bien-loi.md`: **0 DIFF (STRICT LOCK THỎA MÃN)**
- Visual QA (kiểm tra mắt bằng `view_file` trên specimen 200 DPI):
  - Không chồng lấn chữ, không cắt viền.
  - Nhãn phụ 6.4–7.4 pt rõ nét, độ tương phản tuyệt đối.
  - Mũi tên phân nhánh trực giao, nhãn chú thích nằm gọn trong badge trắng viền mảnh.

---

## 4. Danh mục Artifacts tạo mới trên branch
1. `assets/diagrams/error-boundary-trace.png` (1417 × 1765 px, 300 DPI)
2. `assets/diagrams/cancellation-cleanup-trace.png` (1984 × 1350 px, 300 DPI)
3. `book/design/agent2-ch04/ch04_preview.pdf` (Bản xem trước 2 trang kích thước A4)
4. `book/design/agent2-ch04/specimens/ch04_diagrams_p01.png` (Specimen trang 1)
5. `book/design/agent2-ch04/specimens/ch04_diagrams_p02.png` (Specimen trang 2)
6. `scripts/ch04_vector_diagrams.py` (Mã nguồn véc-tơ ReportLab)
7. `scripts/build_ch04_preview.py` (Script xuất preview độc lập)
