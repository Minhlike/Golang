# BÁO CÁO HIỆU CHỈNH KỸ THUẬT SƠ ĐỒ (BATCH 02 - FINAL REVIEW ROUND 3/3)
## CHƯƠNG 12, 13, 15 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả hiệu chỉnh:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch12-15-agent2-redesign` (baseline: `78155dd6783e868233f82d54206c747dc101a8db`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt`, Final Review Round 3/3 Feedback, hợp đồng kỹ thuật thư viện chuẩn Go (`net/http`, `database/sql`, `os/exec`), quy chuẩn in ấn grayscale thuần túy.

---

## 1. Tóm tắt các hiệu chỉnh kỹ thuật trong Final Review Round 3/3

Đợt hiệu chỉnh vòng cuối 3/3 (Final Review Round 3/3) tập trung hoàn thiện tính chính xác tuyệt đối của mã nguồn mẫu, hợp đồng API và ranh giới trách nhiệm kiến trúc trên cả 3 sơ đồ vector `scripts/ch12_15_vector_diagrams.py`, tuân thủ nghiêm ngặt **STRICT CONTENT LOCK** (không sửa bất kỳ tệp Markdown bài giảng, code block, bảng, caption, lab, renderer chính hay `Golang_Master.pdf`).

### 1.1. Chương 12: `http-service-lifecycle.png`
1. **Source Accuracy tại Stage 1 (Process Boundary vs Helper):**
   - Loại bỏ hoàn toàn đoạn mã giả `ln, _ := net.Listen(); go srv.Serve(ln)` bỏ qua kiểm tra lỗi.
   - Thể hiện chính xác phân định ranh giới giữa `main` và helper `ServeUntilStopped`:
     * `main`: Thiết lập `ctx, stop := signal.NotifyContext(...)` và `defer stop()` để tiếp nhận signal hệ thống.
     * `main` gọi helper: `ServeUntilStopped(ctx, srv, ln, grace)`.
     * Helper `ServeUntilStopped`: Mở goroutine nền `srv.Serve(ln)` hứng lỗi qua channel `serveErr`.
2. **Context Semantics & Ranh giới hủy:**
   - Tại **Stage 2**, bỏ khẳng định tuyệt đối `r.Context()` luôn độc lập với root context; nêu rõ `r.Context()` gắn theo vòng đời request và có thể kế thừa từ `Server.BaseContext` nếu cấu hình.
   - Khẳng định bất biến kỹ thuật: `Server.Shutdown` **KHÔNG tự động cancel context của các handler đang phục vụ (active request)**.
   - Tại **Stage 3**, chuẩn hóa tiêu đề thành `3. SỰ KIỆN DỪNG (SIGNAL / CANCEL)`, phân biệt rõ signal dừng từ OS (`SIGINT`/`SIGTERM`) với việc context bị cancel từ caller/test.
   - Tại Footer Callout: Rút gọn súc tích, nhấn mạnh Shutdown đóng listener và pool idle, không tự ngắt active socket/handler; hết grace chỉ dừng chờ drain, quyền force exit thuộc về caller.

### 1.2. Chương 13: `transaction-boundary.png`
1. **SQL Source Accuracy (Đồng bộ `fixed/disable.go`):**
   - Tại **Box 3 (Statement 2)**, chuyển câu lệnh SQL từ `VALUES (?, 'disabled')` thành dạng tham số hóa đầy đủ đúng nguyên văn mã lab:
     `INSERT INTO check_events(check_id, action) VALUES (?, ?)`
     đi kèm lệnh gọi `tx.ExecContext(ctx, query, checkID, "disabled")`.
2. **Chuẩn hóa Error Wrapping & Gắn nhãn Logic Excerpt:**
   - Tiêu đề container cột 1 được gắn nhãn rõ ràng: `RANH GIỚI THỰC THI // TRÍCH ĐOẠN LOGIC (fixed/disable.go)`.
   - Các điểm trả lỗi rút gọn `return err` được chuẩn hóa thành error wrapping chuẩn Go:
     * Box 1: `if err != nil { return fmt.Errorf("begin: %w", err) }`
     * Box 2: `if err != nil { return fmt.Errorf("count: %w", err) }`
     * Box 3: `if err != nil { return fmt.Errorf("event: %w", err) }`
     * Box 4: `if err := tx.Commit(); err != nil { return fmt.Errorf("commit: %w", err) }`
   - Bảo toàn trọn vẹn: Error guard `BeginTx`, `RowsAffected` check, phân nhánh commit thành công vs commit lỗi, và ranh giới Atomicity vs Isolation.

### 1.3. Chương 15: `incident-command-lifecycle.png`
1. **Cú pháp Go hợp lệ cho `exec.CommandContext`:**
   - Tại **Top Right**, thay nhãn rút gọn `...` bằng lời gọi hợp lệ và đầy đủ:
     `cmd := exec.CommandContext(runCtx, spec.Name, spec.Args...)`
     được ngắt dòng an toàn, tránh hoàn toàn nguy cơ đè viền hộp.
2. **Mô tả Process Contract chính xác và đa nền tảng:**
   - Thay khẳng định “os/exec truyền trực tiếp vào syscall” bằng mô tả chuẩn: `os/exec` khởi chạy executable với mảng arguments riêng biệt, **không tự gọi qua shell của hệ điều hành** (giúp chống shell injection/glob/pipe).
   - Tại **Outcome 4**, chuẩn hóa tiêu đề thành `4. LỖI KHỞI TẠO // NON-EXIT`: không tuyệt đối hóa rằng process chưa từng start, mà làm rõ đây là lỗi khởi tạo/pipe/wait khiến tiến trình không hoàn tất chạy, `ProcessState == nil`, `ExitCode = -1`, và không có `ExitError`.

### 1.4. Preview PDF Tối giản (Minimal 1:1 Preview)
- Cập nhật `scripts/build_ch12_15_preview.py` theo đúng yêu cầu Point 10:
  * Loại bỏ toàn bộ các đoạn mô tả bài giảng dài dòng nằm ngoài sơ đồ.
  * Mỗi trang chỉ hiển thị tiêu đề bản duyệt tối giản, nhãn chương/hình kèm kích thước 1:1 và ảnh vector sơ đồ căn giữa hoàn hảo.
  * Không sinh thêm file rác, không tạo script mới.

---

## 2. Kết quả kiểm định chất lượng xuất bản (QA Test Matrix)

| Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Kết quả đo lường thực tế | Đánh giá |
| :--- | :--- | :--- | :--- |
| **Bảng màu thuần Grayscale** | $R = G = B$ trên 100% điểm ảnh; 0% màu pha | `max|R-G| = 0, max|R-B| = 0` trên cả 3 file PNG và 3 specimen | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của Master PDF | Ch12: $185.80 \times 362.83\text{ pt}$<br>Ch13: $422.77 \times 362.83\text{ pt}$<br>Ch15: $444.69 \times 362.83\text{ pt}$ | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | Ch12: $826 \times 1613\text{ px}$<br>Ch13: $1879 \times 1613\text{ px}$<br>Ch15: $1977 \times 1613\text{ px}$ | **PASS (100%)** |
| **Tiêu chuẩn Typography** | 100% nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | Min fontSize = $6.00\text{ pt}$; 0 nhãn dưới $6.0\text{ pt}$<br>• Ch12: 41 strings, $\min = 6.00\text{ pt}, \max = 6.60\text{ pt}$<br>• Ch13: 51 strings, $\min = 6.00\text{ pt}, \max = 7.40\text{ pt}$<br>• Ch15: 72 strings, $\min = 6.00\text{ pt}, \max = 7.00\text{ pt}$ | **PASS (100%)** |
| **Độ an toàn lề & Tràn chữ** | Không tràn khung, khoảng đệm an toàn $\ge 4.0\text{ pt}$ | 100% nhãn nằm gọn trong bounding box của từng card;<br>Zero text overflow trên mọi canvas; Ch15 đệm lề $\ge 7.8\text{ pt}$ | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests pass in 0.313s | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn (Usable width: 448.22 pt) | **PASS (100%)** |

---

## 3. Danh mục Tệp bàn giao trên Branch `design/ch12-15-agent2-redesign`

1. `assets/diagrams/http-service-lifecycle.png` (Hình 24, Chương 12: Đã chuẩn hóa ranh giới main vs ServeUntilStopped, BaseContext, và cancellation semantics)
2. `assets/diagrams/transaction-boundary.png` (Hình 25, Chương 13: Đồng bộ VALUES (?, ?), bọc lỗi fmt.Errorf %w, và gắn nhãn Logic Excerpt)
3. `assets/diagrams/incident-command-lifecycle.png` (Hình 26, Chương 15: Cú pháp CommandContext chuẩn, process contract đa nền tảng, Non-exit error)
4. `scripts/ch12_15_vector_diagrams.py` (Script vẽ vector ReportLab cập nhật toàn diện theo Final Review Round 3/3)
5. `scripts/build_ch12_15_preview.py` (Script dựng Preview PDF độc lập và xuất visual specimens tối giản)
6. `book/design/agent2-ch12-15/ch12_15_preview.pdf` (Preview PDF 3 trang 1:1 độc lập, không văn bản bài giảng ngoài hình)
7. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png` (Specimen trực quan Trang 1: Chương 12)
8. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png` (Specimen trực quan Trang 2: Chương 13)
9. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png` (Specimen trực quan Trang 3: Chương 15)
10. `book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md` (Tài liệu báo cáo kỹ thuật này)

---

## 4. Hard Approval Gate

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**
> - Đây là **vòng sửa cuối cùng 3/3 (Final Review Round 3/3)** của đợt thiết kế sơ đồ Chương 12–15.
> - Toàn bộ các yêu cầu kỹ thuật đã được hoàn thiện chính xác, kiểm định đạt 100% QA và cô lập an toàn trên branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG MERGE:** Nhánh thiết kế được giữ riêng biệt, không merge vào `main`.
> - **KHÔNG PUSH MAIN:** Chỉ push lên remote branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG CHỈNH SỬA MASTER PDF:** `Golang_Master.pdf` được bảo vệ nguyên vẹn 100%.
> - **KHÔNG THỰC HIỆN VÒNG 4:** Dừng lại ở trạng thái này để ChatGPT review độc lập và người dùng phê duyệt thủ công.
