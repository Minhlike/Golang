# BÁO CÁO HIỆU CHỈNH KỸ THUẬT SƠ ĐỒ (BATCH 02 - SOURCE-ACCURACY & FINAL QUALITY REVIEW)
## CHƯƠNG 12, 13, 15 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả hiệu chỉnh:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch12-15-agent2-redesign` (baseline: `a84e79a8ae583765cf5250e0d4fcfc4b446bd549`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt`, Source-Accuracy & Final Quality Review Feedback, đối chiếu mã nguồn và test của lab (`labs/part12-service-lifecycle`, `labs/part13-transaction-boundary`, `labs/part15-incident-command`), quy chuẩn in ấn grayscale thuần túy.

---

## 1. Phân tích Nguyên nhân Gốc Toàn diện (Systemic Root-Cause Analysis)

Qua quá trình rà soát đối chiếu trực tiếp giữa sơ đồ kiến trúc và mã nguồn thực tế của thư viện chuẩn Go cũng như các lab mẫu, các sai lệch kỹ thuật trước đó xuất phát từ các nguyên nhân có hệ thống sau:

1. **Ranh giới giữa Trích đoạn Mã (Code Snippet) và Sơ đồ Khái niệm (Conceptual Diagram):**
   - Khi cố gắng đưa mã nguồn Go hoàn chỉnh vào các khung thẻ có kích thước in hạn chế (đặc biệt là hình dọc $185.80\text{ pt}$ của Chương 12), việc nén dòng buộc phải cắt ngắn cú pháp, vô tình làm biến mất các bước xử lý lỗi trọng yếu (như kiểm tra lỗi `srv.Shutdown` và hứng kết quả từ `serveErr`).
   - *Giải pháp triệt để:* Rà soát toàn bộ luồng thực thi: Khai báo biến $\rightarrow$ Lời gọi API $\rightarrow$ Giá trị trả về $\rightarrow$ Kiểm tra lỗi $\rightarrow$ Nhánh phân loại $\rightarrow$ Kết quả. Nếu không gian không đủ cho toàn bộ khối mã Go dài 10 dòng, sử dụng nhãn khái niệm chuẩn xác kết hợp định dạng logic có cấu trúc rõ ràng, không cắt xén làm méo mó cú pháp Go.

2. **Đồng bộ Thông điệp Lỗi (Error Wrapping Strings) với Mã Nguồn Lab:**
   - Trong Chương 13, các chuỗi bọc lỗi trước đó bị rút ngắn thành `"begin: %w"`, `"update: %w"`, `"count: %w"`, `"event: %w"`, `"commit: %w"`, không đồng nhất với thông điệp thực tế trong `fixed/disable.go`.
   - *Giải pháp triệt để:* Đồng bộ 100% nguyên văn các chuỗi định dạng bọc lỗi theo đúng source lab:
     * `fmt.Errorf("begin disable transaction: %w", err)`
     * `fmt.Errorf("disable check: %w", err)`
     * `fmt.Errorf("count disabled checks: %w", err)`
     * `fmt.Errorf("record disable event: %w", err)`
     * `fmt.Errorf("commit disable: %w", err)`
   - Đồng thời, minh bạch hóa trong tiêu đề và chú thích: Đây là mô hình logic tương đương thể hiện cấu trúc `ExecContext → kiểm tra lỗi → Commit/Rollback`, không phải trích dẫn nguyên văn toàn bộ tệp nguồn Go.

3. **Thứ tự Ưu tiên Phân loại Nhánh Kết quả (Branch Priority Waterfall):**
   - Trong Chương 15, việc bố trí 4 thẻ kết quả theo thứ tự ngẫu nhiên (Exit 0 $\rightarrow$ Exit != 0 $\rightarrow$ Timeout $\rightarrow$ Non-exit) tạo cảm giác các nhánh này độc lập ngang hàng, che khuất logic phân loại có thứ tự ưu tiên của `fixed/run.go`.
   - *Giải pháp triệt để:* Sắp xếp lại đúng thứ tự phễu quyết định (Decision Waterfall) từ trái sang phải theo chuỗi `if-else` của hàm `Run()`:
     * **Ưu tiên 1 [P1]:** `runCtx.Err() != nil` (Context Timeout / Cancel) — phải kiểm tra đầu tiên để không nhầm lẫn tiến trình bị kill thành lỗi ExitError thông thường.
     * **Ưu tiên 2 [P2]:** `err == nil` (Exit 0 // Thành công).
     * **Ưu tiên 3 [P3]:** `errors.As(err, &exitErr)` (Exit != 0 // Lệnh lỗi).
     * **Ưu tiên 4 [P4]:** `Fallthrough` (Lỗi Start / Non-exit).

---

## 2. Chi tiết các Hiệu chỉnh Kỹ thuật Đã Hoàn thiện

Tuân thủ nghiêm ngặt **STRICT CONTENT LOCK** (không sửa bất kỳ tệp Markdown nào trong `book/chapters/`, code lab, bảng, caption, renderer chính hay `Golang_Master.pdf`), toàn bộ hiệu chỉnh được thực hiện trên generator vector `scripts/ch12_15_vector_diagrams.py`:

### 2.1. Chương 12: `http-service-lifecycle.png` (Hình 24, Trang 217, xref 477)
1. **Lan truyền Lỗi Shutdown & Đồng bộ `serveErr`:**
   - Tại **Stage 4 (ĐIỀU PHỐI Server.Shutdown)**, thể hiện đầy đủ chuỗi xử lý theo đúng [`fixed/server.go`](file:///d:/Golang/labs/part12-service-lifecycle/fixed/server.go#L123-L132):
     ```
     shutdownCtx, cancel := context.WithTimeout(
         context.Background(), grace)
     defer cancel() // Context rút lui độc lập
     1. srv.Shutdown(shutdownCtx): đóng ln & pool
     2. Lỗi Shutdown: bọc "shutdown: %w"
     3. Đồng bộ <-serveErr: đợi ErrServerClosed
        (nếu khác ErrServerClosed: bọc lỗi)
     4. Cả hai khớp chuẩn => return nil (sạch)
     ```
   - Bảo toàn trọn vẹn sự phân biệt giữa context nhận tín hiệu dừng (OS/caller) và context mới dành riêng cho graceful shutdown timeout.
2. **Đồng bộ Kết cục tại Stage 5:**
   - Thẻ bên trái (**TRONG HẠN GRACE**) thể hiện rõ ràng điều kiện kép để thoát sạch: `Shutdown` trả `nil` VÀ `serveErr` nhận `http.ErrServerClosed` $\rightarrow$ `return nil (Clean)`.
   - Thẻ bên phải (**QUÁ HẠN GRACE**) nhấn mạnh: `Shutdown` trả `DeadlineExceeded`, active sockets caller tự ngắt (`srv.Close()` / exit).

### 2.2. Chương 13: `transaction-boundary.png` (Hình 25, Trang 233, xref 510)
1. **Đồng bộ Chính xác Chuỗi Bọc Lỗi với `fixed/disable.go`:**
   - **Box 1:** `return fmt.Errorf("begin disable transaction: %w", err)`
   - **Box 2:** `return fmt.Errorf("disable check: %w", err)`
   - **Box 2:** `return fmt.Errorf("count disabled checks: %w", err)`
   - **Box 3:** `return fmt.Errorf("record disable event: %w", err)`
   - **Box 4:** `return fmt.Errorf("commit disable: %w", err)`
2. **Minh bạch hóa Ranh giới Mô hình Logic:**
   - Tiêu đề khung Cột 1 được chuẩn hóa: `RANH GIỚI THỰC THI // MÔ HÌNH LOGIC TRANSACTION`, góc phải gắn nhãn: `[mô hình logic tương đương]`.
   - Chú thích rõ ràng tại Box 3: `• Vi phạm ràng buộc -> return -> defer Rollback (SQL tương đương)`, làm rõ đây là biểu diễn logic cô đọng giúp người học nắm chắc luồng `ExecContext → kiểm tra lỗi → Commit/Rollback`.
3. **Cú pháp Toàn vẹn:**
   - Mọi khối lệnh `if err != nil` đều có `{ ... }` đầy đủ.
   - Khối Commit có đóng ngoặc `}` và khẳng định bất biến nguyên tử (atomicity).

### 2.3. Chương 15: `incident-command-lifecycle.png` (Hình 26, Trang 272, xref 589)
1. **Thứ tự Ưu tiên Phân loại Nhánh (Branch Priority):**
   - Thanh trung gian (Middle Bar) công bố rõ ràng trình tự phễu quyết định:
     `• Waterfall: 1. runCtx.Err() != nil [P1] -> 2. err == nil [P2] -> 3. errors.As(&exitErr) [P3] -> 4. Fallthrough [P4]`
   - Bốn thẻ kết quả bên dưới được bố trí chuẩn xác theo đúng thứ tự ưu tiên:
     * **Thẻ 1 [P1]:** `1. TIMEOUT / CANCEL` — Kiểm tra `runCtx.Err() != nil` trước tiên, phân biệt `DeadlineExceeded` (`TimedOut = true`) với `context.Canceled` (`TimedOut = false`), tránh nhầm với `ExitError`.
     * **Thẻ 2 [P2]:** `2. EXIT 0 // THÀNH CÔNG` — Kiểm tra `err == nil`, lệnh chạy trọn vẹn, đủ cả 2 stream.
     * **Thẻ 3 [P3]:** `3. EXIT != 0 // LỆNH LỖI` — Kiểm tra `errors.As(err, &exitErr)`, lấy `ExitCode != 0` từ `cmd.ProcessState.ExitCode()`, Stderr bảo toàn chẩn đoán lỗi.
     * **Thẻ 4 [P4]:** `4. LỖI START / NON-EXIT` — Nhánh Fallthrough khi không có `ExitError`.
2. **Phân định Chuẩn xác Trạng thái của Outcome 4:**
   - **Chưa start (`cmd.ProcessState == nil`):** File not found, permission denied; `ExitCode = -1` (mặc định).
   - **Đã start (`cmd.ProcessState != nil`):** Gặp lỗi copy stream I/O (`io.Copy`), setup pipe hoặc runtime error khác không phải lỗi thoát của tiến trình.
   - Trả về đúng hợp đồng: `(Result, wrappedErr)` bọc chuỗi `"start command: %w"`.

---

## 3. Kết quả Kiểm định Chất lượng Xuất bản (QA Test Matrix)

| Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Kết quả đo lường thực tế | Đánh giá |
| :--- | :--- | :--- | :--- |
| **Bảng màu thuần Grayscale** | $R = G = B$ trên 100% điểm ảnh; 0% màu pha | `max|R-G| = 0, max|R-B| = 0` trên cả 3 file PNG và 3 specimen | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của Master PDF | Ch12: $185.80 \times 362.83\text{ pt}$<br>Ch13: $422.77 \times 362.83\text{ pt}$<br>Ch15: $444.69 \times 362.83\text{ pt}$ | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | Ch12: $826 \times 1613\text{ px}$ ($197\text{ KB}$)<br>Ch13: $1879 \times 1613\text{ px}$ ($325\text{ KB}$)<br>Ch15: $1977 \times 1613\text{ px}$ ($317\text{ KB}$) | **PASS (100%)** |
| **Tiêu chuẩn Typography** | 100% nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | Min fontSize = $6.00\text{ pt}$; 0 nhãn dưới $6.0\text{ pt}$<br>• Ch12: 44 strings, $\min = 6.00\text{ pt}$<br>• Ch13: 57 strings, $\min = 6.00\text{ pt}$<br>• Ch15: 76 strings, $\min = 6.00\text{ pt}$ | **PASS (100%)** |
| **Độ an toàn lề & Tràn chữ** | Không tràn khung, khoảng đệm an toàn $\ge 4.0\text{ pt}$ | 100% nhãn nằm gọn trong bounding box của từng card;<br>Zero text overflow trên mọi canvas | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests pass in 0.318s | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn (Usable width: 448.22 pt) | **PASS (100%)** |

---

## 4. Danh mục Tệp Bàn giao trên Branch `design/ch12-15-agent2-redesign`

1. `assets/diagrams/http-service-lifecycle.png` (Hình 24, Chương 12: Lan truyền lỗi shutdown, đồng bộ serveErr và ranh giới context độc lập)
2. `assets/diagrams/transaction-boundary.png` (Hình 25, Chương 13: Đồng bộ 100% thông điệp bọc lỗi với fixed/disable.go, minh bạch hóa mô hình logic)
3. `assets/diagrams/incident-command-lifecycle.png` (Hình 26, Chương 15: Bố trí theo đúng thứ tự ưu tiên phễu quyết định [P1] $\rightarrow$ [P4], phân định chuẩn xác Outcome 4)
4. `scripts/ch12_15_vector_diagrams.py` (Script vẽ vector ReportLab cập nhật toàn diện theo phản hồi chất lượng)
5. `scripts/build_ch12_15_preview.py` (Script dựng Preview PDF độc lập và xuất visual specimens tối giản)
6. `book/design/agent2-ch12-15/ch12_15_preview.pdf` (Preview PDF 3 trang 1:1 độc lập)
7. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png` (Specimen trực quan Trang 1: Chương 12)
8. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png` (Specimen trực quan Trang 2: Chương 13)
9. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png` (Specimen trực quan Trang 3: Chương 15)
10. `book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md` (Tài liệu báo cáo kỹ thuật này)

---

## 5. Cổng Phê duyệt Nghiêm ngặt (Hard Approval Gate)

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**
> - Toàn bộ các yêu cầu kỹ thuật, đối chiếu mã nguồn và thứ tự ưu tiên phân nhánh đã được giải quyết triệt để và đạt 100% các tiêu chí QA xuất bản.
> - **KHÔNG MERGE:** Nhánh thiết kế được giữ riêng biệt trên `design/ch12-15-agent2-redesign`, không merge vào `main`.
> - **KHÔNG PUSH MAIN:** Chỉ push lên remote branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG CHỈNH SỬA MASTER PDF:** `Golang_Master.pdf` được bảo vệ nguyên vẹn 100%.
> - Dừng lại ở trạng thái này để ChatGPT review độc lập và người dùng phê duyệt thủ công.
