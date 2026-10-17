# BÁO CÁO HIỆU CHỈNH KỸ THUẬT SƠ ĐỒ (BATCH 02 - POST-ROUND-3 QUALITY CORRECTIONS)
## CHƯƠNG 12, 13, 15 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả hiệu chỉnh:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch12-15-agent2-redesign` (baseline: `bb988d0c652ffa598bd7f54ba7205ce0f8a3ecf0`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt`, Post-Round-3 Quality Corrections Feedback, hợp đồng kỹ thuật thư viện chuẩn Go (`net/http`, `database/sql`, `os/exec`), quy chuẩn in ấn grayscale thuần túy.

---

## 1. Phân tích Nguyên nhân Gốc (Root-Cause Analysis)

Trong các vòng trước, một số trích đoạn mã trên sơ đồ gặp hiện tượng rút gọn quá mức (lược bỏ biến trung gian `result`, dùng placeholder `base` chưa khai báo, khuyết hàm `cancel`, khuyết dấu `}` đóng khối lệnh `if`). 

**Nguyên nhân gốc:**  
Khi thiết kế card đồ họa kỹ thuật trong giới hạn chiều cao cố định của trang in sách ($362.83\text{ pt}$), việc nén các bước logic vào từng card khiến tác giả có xu hướng lược bớt câu lệnh gán biến trung gian hoặc gộp dòng mã, vô tình biến trích đoạn Go thành mã giả chưa hoàn chỉnh về mặt cú pháp.

**Giải pháp triệt để:**  
1. **Tái cấu trúc không gian hình vẽ:** Điều chỉnh phân bổ chiều cao của các khối (`s4_h` tăng lên $70.0\text{ pt}$, `b2_h` tăng lên $72.0\text{ pt}$, `b3_h` tăng lên $66.0\text{ pt}$, `b4_h` tăng lên $50.0\text{ pt}$) và khoảng hở giữa các card (`gap_col1 = 5.61\text{ pt}$), bảo đảm đủ diện tích thể hiện đầy đủ khai báo, gán biến và kiểm tra lỗi.
2. **Khai báo tường minh 100%:** Mọi biến, hằng số và hàm được sử dụng đều phải được khai báo rõ ràng (`const query = ...`, `result, err := tx.ExecContext(...)`, `shutdownCtx, cancel := context.WithTimeout(context.Background(), grace)`).
3. **Cú pháp Go hợp lệ tuyệt đối:** Mọi khối điều kiện `if` đều có đóng mở ngoặc `{ ... }` đầy đủ, không để cụt cú pháp.

---

## 2. Chi tiết các Hiệu chỉnh Kỹ thuật Post-Round-3

Tuân thủ nghiêm ngặt **STRICT CONTENT LOCK** (không sửa bất kỳ tệp Markdown bài giảng nào trong `book/chapters/`, code lab, bảng, caption, renderer chính hay `Golang_Master.pdf`), toàn bộ hiệu chỉnh được thực hiện tập trung trên bộ generator vector ReportLab `scripts/ch12_15_vector_diagrams.py`:

### 2.1. Chương 12: `http-service-lifecycle.png` (Hình 24, Trang 217, xref 477)
1. **Shutdown Context độc lập (`context.Background()`):**
   - Thay thế hoàn toàn dòng rút gọn `shutdownCtx, _ := context.WithTimeout(base, grace)` bằng mã Go chuẩn xác đối chiếu trực tiếp `fixed/server.go`:
     ```go
     shutdownCtx, cancel := context.WithTimeout(
         context.Background(), grace)
     defer cancel(); srv.Shutdown(shutdownCtx)
     ```
   - Nêu rõ ràng: Đây là **context rút lui mới**, độc lập hoàn toàn với `ctx` nhận signal/cancellation từ caller/OS.
   - Thể hiện đầy đủ đăng ký `defer cancel()` giải phóng timer resource.
2. **Bảo toàn ranh giới vòng đời:** Giữ nguyên trình tự 5 giai đoạn đã đạt chuẩn (Khởi tạo `signal.NotifyContext` tại `main`, `ServeHTTP` active serving, `<-ctx.Done()` signal arrival, `Server.Shutdown` drain, và 2 kết cục tại boundary deadline).

### 2.2. Chương 13: `transaction-boundary.png` (Hình 25, Trang 233, xref 510)
1. **Hoàn thiện trình tự UPDATE tại Box 2 (Statement 1):**
   - Thể hiện đầy đủ lời gọi `tx.ExecContext`, nhận cặp `(result, err)`, kiểm tra lỗi thực thi trước khi gọi `result.RowsAffected()`:
     ```go
     result, err := tx.ExecContext(ctx,
         "UPDATE checks SET enabled = 0 WHERE id = ?", checkID)
     if err != nil { return fmt.Errorf("update: %w", err) }
     changed, err := result.RowsAffected()
     if err != nil { return fmt.Errorf("count: %w", err) }
     if changed == 0 { return ErrCheckNotFound }
     ```
   - Thể hiện đầy đủ nhánh bảo vệ: nếu target không tồn tại (`changed == 0`) hoặc DB lỗi $\rightarrow$ `return` sớm $\rightarrow$ kích hoạt `defer tx.Rollback()`.
2. **Khai báo tường minh Hằng số SQL tại Box 3 (Statement 2):**
   - Khai báo rõ ràng hằng số SQL `const query`:
     ```go
     const query = "INSERT INTO check_events" +
         "(check_id, action) VALUES (?, ?)"
     _, err = tx.ExecContext(ctx, query, checkID, "disabled")
     if err != nil { return fmt.Errorf("event: %w", err) }
     ```
   - Không để `query` xuất hiện mà không được định nghĩa. Bind lỗi tường minh `_, err = ...` và kiểm tra lỗi trước khi tiếp tục.
3. **Đóng khối cú pháp Commit tại Box 4:**
   - Bổ sung dấu ngoặc nhọn `}` đóng khối lệnh `if`, bảo đảm cú pháp Go toàn vẹn:
     ```go
     if err := tx.Commit(); err != nil {
         return fmt.Errorf("commit: %w", err)
     }
     ```
   - Phân biệt rõ: `err == nil` là hai câu lệnh cùng áp dụng nguyên tử; `err != nil` thì không bảo đảm rollback hoàn toàn do lỗi mạng/commit.

### 2.3. Chương 15: `incident-command-lifecycle.png` (Hình 26, Trang 272, xref 589)
1. **Chuẩn hóa Tiêu đề & Ranh giới Outcome 4:**
   - Đổi tiêu đề thành: `4. LỖI START / NON-EXIT`.
   - Phân định rạch ròi 2 trường hợp theo đúng `fixed/run.go`:
     * **Chưa start (`cmd.ProcessState == nil`):** Chỉ xảy ra khi executable không tìm thấy (file not found), không có quyền thực thi (permission denied) hoặc cấu hình spec lỗi. `ExitCode` giữ nguyên giá trị khởi tạo mặc định `-1`.
     * **Đã start (`cmd.ProcessState != nil`):** Tiến trình con đã được cấp phát PID và khởi chạy, nhưng gặp lỗi I/O copy stream (`io.Copy`), pipe setup hoặc wait trước khi thoát bình thường.
2. **Hợp đồng Trả về chuẩn xác:**
   - Thể hiện đúng hợp đồng trả về của `fixed/run.go`:
     `=> Trả (Result, wrappedErr)` bọc chuỗi `"start command: %w"`.

---

## 3. Kết quả Kiểm định Chất lượng Xuất bản (QA Test Matrix)

| Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Kết quả đo lường thực tế | Đánh giá |
| :--- | :--- | :--- | :--- |
| **Bảng màu thuần Grayscale** | $R = G = B$ trên 100% điểm ảnh; 0% màu pha | `max|R-G| = 0, max|R-B| = 0` trên cả 3 file PNG và 3 specimen | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của Master PDF | Ch12: $185.80 \times 362.83\text{ pt}$<br>Ch13: $422.77 \times 362.83\text{ pt}$<br>Ch15: $444.69 \times 362.83\text{ pt}$ | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | Ch12: $826 \times 1613\text{ px}$ ($190\text{ KB}$)<br>Ch13: $1879 \times 1613\text{ px}$ ($337\text{ KB}$)<br>Ch15: $1977 \times 1613\text{ px}$ ($311\text{ KB}$) | **PASS (100%)** |
| **Tiêu chuẩn Typography** | 100% nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | Min fontSize = $6.00\text{ pt}$; 0 nhãn dưới $6.0\text{ pt}$<br>• Ch12: 42 strings, $\min = 6.00\text{ pt}, \max = 6.60\text{ pt}$<br>• Ch13: 56 strings, $\min = 6.00\text{ pt}, \max = 7.40\text{ pt}$<br>• Ch15: 76 strings, $\min = 6.00\text{ pt}, \max = 7.00\text{ pt}$ | **PASS (100%)** |
| **Độ an toàn lề & Tràn chữ** | Không tràn khung, đệm an toàn $\ge 4.0\text{ pt}$ | 100% nhãn nằm gọn trong bounding box của từng card;<br>Zero text overflow trên mọi canvas | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests pass in 0.332s | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn (Usable width: 448.22 pt) | **PASS (100%)** |

---

## 4. Danh mục Tệp bàn giao trên Branch `design/ch12-15-agent2-redesign`

1. `assets/diagrams/http-service-lifecycle.png` (Hình 24, Chương 12: Đã chuẩn hóa `context.Background()`, `defer cancel()`, và graceful shutdown timeout)
2. `assets/diagrams/transaction-boundary.png` (Hình 25, Chương 13: Đã hoàn thiện `tx.ExecContext` UPDATE $\rightarrow$ `RowsAffected`, khai báo `const query` INSERT, và đóng ngoặc `}` commit)
3. `assets/diagrams/incident-command-lifecycle.png` (Hình 26, Chương 15: Đổi tiêu đề `4. LỖI START / NON-EXIT`, phân định `ProcessState == nil` vs `ProcessState != nil`, trả `(Result, wrappedErr)`)
4. `scripts/ch12_15_vector_diagrams.py` (Script vẽ vector ReportLab cập nhật theo toàn bộ phản hồi chất lượng Post-Round-3)
5. `scripts/build_ch12_15_preview.py` (Script dựng Preview PDF độc lập và xuất visual specimens tối giản)
6. `book/design/agent2-ch12-15/ch12_15_preview.pdf` (Preview PDF 3 trang 1:1 độc lập)
7. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png` (Specimen trực quan Trang 1: Chương 12)
8. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png` (Specimen trực quan Trang 2: Chương 13)
9. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png` (Specimen trực quan Trang 3: Chương 15)
10. `book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md` (Tài liệu báo cáo kỹ thuật này)

---

## 5. Hard Approval Gate

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**
> - Toàn bộ các yêu cầu hiệu chỉnh kỹ thuật Post-Round-3 đã được giải quyết triệt để, đối chiếu chính xác mã nguồn lab và tài liệu chính thức của Go.
> - Kết quả kiểm định đạt 100% trên toàn bộ các chỉ tiêu chất lượng xuất bản.
> - **KHÔNG MERGE:** Nhánh thiết kế được giữ riêng biệt trên `design/ch12-15-agent2-redesign`, không merge vào `main`.
> - **KHÔNG PUSH MAIN:** Chỉ push lên remote branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG CHỈNH SỬA MASTER PDF:** `Golang_Master.pdf` được bảo vệ nguyên vẹn 100%.
> - Dừng lại ở trạng thái này để người dùng kiểm tra độc lập và phê duyệt nghiệm thu thủ công.
