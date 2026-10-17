# BÁO CÁO HIỆU CHỈNH KỸ THUẬT SƠ ĐỒ (BATCH 02 - REVIEW ROUND 1/3)
## CHƯƠNG 12, 13, 15 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả hiệu chỉnh:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch12-15-agent2-redesign` (baseline: `bf6bcaa`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt`, Review Round 1/3 Feedback, hợp đồng kỹ thuật thư viện chuẩn Go (`net/http`, `database/sql`, `os/exec`), quy chuẩn in ấn grayscale thuần túy.

---

## 1. Tóm tắt các hiệu chỉnh kỹ thuật trong Review Round 1/3

Theo phản hồi từ đợt duyệt kỹ thuật vòng 1/3 (Review Round 1/3), toàn bộ các chỉnh sửa đã được phẫu thuật trực tiếp trên mã nguồn tạo vector `scripts/ch12_15_vector_diagrams.py`, đảm bảo tuân thủ tuyệt đối quy tắc **STRICT CONTENT LOCK** (không sửa bất kỳ tệp Markdown, bài giảng, code block, bảng, caption, renderer chính hay `Golang_Master.pdf`).

### 1.1. Chương 12: `http-service-lifecycle.png`
1. **Sửa ngữ nghĩa `Server.Shutdown`:**
   - Đính chính: Khi context hết hạn grace (`shutdownCtx.Err() == context.DeadlineExceeded`), phương thức `Shutdown()` **chỉ trả lỗi timeout về cho caller**, tuyệt đối **không tự động cắt hoặc ngắt cưỡng chế các socket/connection đang active**.
   - Thể hiện rõ chính sách ngắt kết nối (gọi `srv.Close()`, phát alarm hoặc ép thoát process) là quyền và trách nhiệm thiết kế riêng của caller/vận hành, không phải hành vi mặc định của thư viện chuẩn `net/http`.
2. **Phân biệt rành mạch thời điểm `Serve` trả `ErrServerClosed` với thời điểm `Shutdown` hoàn thành:**
   - Đưa việc `srv.Serve(ln)` trả về `http.ErrServerClosed` lên Stage 4 (ngay khi `Shutdown` đóng TCP listener để ngừng nhận việc), phân biệt rõ với thời điểm `Shutdown` chờ active connection hoặc trả về ở Stage 5.
3. **Chuẩn hóa nối `signal.NotifyContext` và cleanup `defer stop()`:**
   - Trình bày chính xác: `ctx, stop := signal.NotifyContext(...)` đi kèm `defer stop() // Thu hồi signal handler khi thoát` theo đúng bài giảng và `pkg.go.dev/os/signal`.
4. **Loại bỏ triệt để lỗi tràn nhãn `Serve: ErrServerClosed`:**
   - Nhãn `• Serve: ErrServerClosed` từng nằm trong hộp trái Stage 5 gây tràn $5.5\text{ pt}$ sang hộp phải đã được xóa khỏi nhánh rẽ và chuyển về đúng ngữ cảnh tại Stage 4 (`1. Đóng listener => Serve trả ErrServerClosed`, độ rộng $111.5\text{ pt}$, đệm an toàn $> 64\text{ pt}$).
   - Mọi nhãn trong hộp rẽ nhánh Stage 5 (`TRONG HẠN GRACE` và `QUÁ HẠN GRACE`) đều có đệm an toàn $\ge 18.9\text{ pt}$. Giữ nguyên bố cục dọc và cỡ chữ $\ge 6.0\text{ pt}$.

### 1.2. Chương 13: `transaction-boundary.png`
1. **Bỏ khẳng định Commit ghi dữ liệu vĩnh viễn vào WAL/Storage:**
   - Không đánh đồng transaction với cam kết ghi đĩa cơ lý (WAL/Flash/HDD); phản ánh chính xác lab thực tế sử dụng SQLite in-memory (`file::memory:?cache=shared`) và hợp đồng lý thuyết của tính nguyên tử (Atomicity): các câu lệnh cùng có hiệu lực hoặc cùng bị hủy bỏ.
2. **Phân biệt `tx.Commit()` thành công và trả lỗi:**
   - Bổ sung cấu trúc kiểm tra chuẩn: `if err := tx.Commit(); err != nil { return err }`.
   - Phân định rõ ràng: Khi `Commit` thành công (`err == nil`), cả hai thao tác cùng có hiệu lực nguyên tử. Nếu `Commit` trả lỗi (do rớt mạng khi gửi tín hiệu, commit-phase failure, v.v.), **không thể khẳng định transaction chắc chắn đã được rollback** về trạng thái ban đầu, vì server có thể đã commit thành công hoặc driver đã đóng transaction khiến `defer tx.Rollback()` trả về `sql.ErrTxDone`.
3. **Giữ đúng trình tự và kiểm tra lỗi theo source:**
   - Trình tự bất biến: `db.BeginTx(ctx, nil) -> defer tx.Rollback() -> UPDATE checks -> result.RowsAffected() (changed == 0 -> ErrCheckNotFound) -> INSERT check_events -> tx.Commit()`.
   - Không nhầm lẫn Atomicity (nguyên tử) với Isolation (mức cô lập đồng thời).

### 1.3. Chương 15: `incident-command-lifecycle.png`
1. **Sửa literal/cú pháp Go và bám sát mã nguồn lab `fixed/run.go`:**
   - Loại bỏ chuỗi giả định `ping -c` phụ thuộc nền tảng; chuyển sang đặc tả hợp lệ theo lab test helper:
     ```go
     spec := Spec{Name: os.Args[0], Timeout: 5*time.Second,
         Args: []string{"-mode=probe", "-target=svc"}}
     ```
2. **Phân biệt chính xác Deadline Timeout vs Parent Cancellation:**
   - Làm rõ sự khác biệt giữa hai kịch bản context hủy trong hộp kết cục:
     * `context.DeadlineExceeded` $\rightarrow$ `TimedOut = true` (quá ngân sách thời gian thực thi).
     * `context.Canceled` $\rightarrow$ `TimedOut = false` (bị context cha hủy chủ động; hủy không đồng nghĩa với hết hạn).
3. **Bảo toàn cả hai stream trên kịch bản thành công (Exit 0):**
   - Đính chính nhãn: Lệnh kết thúc Exit 0 **vẫn giữ nguyên vẹn cả stdout và stderr** (stderr hoàn toàn có thể chứa log chẩn đoán hoặc cảnh báo không gây fatal, đúng theo kiểm thử `TestRunKeepsStreamsAndSuccessStatus`).
4. **Phân biệt Non-zero Exit với Lỗi Khởi Chạy (Start Failure):**
   - Không quy kết mọi exit khác 0 là lỗi của target; lệnh có thể trả mã lỗi do ứng dụng, cờ sai hoặc dependency từ chối (`ExitCode = 7`).
   - Phân tách rõ ràng với Lỗi Khởi Chạy (`err != nil`, không có `ExitError`, `ProcessState == nil`, `ExitCode = -1`, không sinh ra PID do file không tồn tại hoặc thiếu quyền).
5. **Chuẩn hóa giới hạn an toàn của `os/exec`:**
   - Bỏ khẳng định tuyệt đối `os/exec` loại bỏ mọi command injection; nêu rõ: truyền trực tiếp qua syscall giúp ngăn chặn command injection do việc shell parse chuỗi glob/pipe.
   - Bỏ khẳng định `CommandContext` dọn sạch toàn bộ cây tiến trình (process tree); nêu rõ `CommandContext` chỉ terminate trực tiếp tiến trình con được khởi tạo.
   - Nhấn mạnh `Result` là **bằng chứng quan sát cục bộ**, không tự chứng minh nguyên nhân gốc của sự cố.

---

## 2. Kết quả kiểm định chất lượng xuất bản (QA Test Matrix)

| Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Kết quả đo lường thực tế | Đánh giá |
| :--- | :--- | :--- | :--- |
| **Bảng màu thuần Grayscale** | $R = G = B$ trên 100% điểm ảnh; 0% màu pha | `max|R-G| = 0, max|R-B| = 0` trên cả 3 file PNG | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của Master PDF | Ch12: $185.80 \times 362.83\text{ pt}$<br>Ch13: $422.77 \times 362.83\text{ pt}$<br>Ch15: $444.69 \times 362.83\text{ pt}$ | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | Ch12: $826 \times 1613\text{ px}$<br>Ch13: $1879 \times 1613\text{ px}$<br>Ch15: $1977 \times 1613\text{ px}$ | **PASS (100%)** |
| **Tiêu chuẩn Typography** | 100% nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | 151/151 nhãn văn bản có `fontSize >= 6.00 pt`<br>• Ch12: 39 strings, $\min = 6.00\text{ pt}, \max = 6.60\text{ pt}$<br>• Ch13: 47 strings, $\min = 6.00\text{ pt}, \max = 7.40\text{ pt}$<br>• Ch15: 65 strings, $\min = 6.00\text{ pt}, \max = 7.00\text{ pt}$ | **PASS (100%)** |
| **Độ an toàn lề & Tràn chữ** | Không tràn khung, khoảng đệm an toàn $\ge 4.0\text{ pt}$ | 100% nhãn nằm gọn trong bounding box của từng card;<br>Zero text overflow trên mọi canvas; Ch12 đệm $\ge 18.9\text{ pt}$ | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests pass in 0.284s | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn | **PASS (100%)** |

---

## 3. Danh mục Tệp bàn giao trên Branch `design/ch12-15-agent2-redesign`

1. `assets/diagrams/http-service-lifecycle.png` (Hình 24, Chương 12: Đã sửa shutdown semantics, NotifyContext & stop, bỏ tràn nhãn)
2. `assets/diagrams/transaction-boundary.png` (Hình 25, Chương 13: Bỏ WAL/storage, thêm commit error & atomicity contract)
3. `assets/diagrams/incident-command-lifecycle.png` (Hình 26, Chương 15: Cú pháp Go chuẩn, phân biệt timeout vs cancel, giữ stderr khi exit 0)
4. `scripts/ch12_15_vector_diagrams.py` (Script vẽ vector ReportLab cập nhật toàn diện theo Review Round 1/3)
5. `scripts/build_ch12_15_preview.py` (Script dựng Preview PDF độc lập và xuất visual specimens)
6. `book/design/agent2-ch12-15/ch12_15_preview.pdf` (Preview PDF 3 trang 1:1 độc lập)
7. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png` (Specimen trực quan Trang 1: Chương 12)
8. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png` (Specimen trực quan Trang 2: Chương 13)
9. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png` (Specimen trực quan Trang 3: Chương 15)
10. `book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md` (Tài liệu báo cáo kỹ thuật này)

---

## 4. Hard Approval Gate

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**
> - Đây là **vòng sửa 1/3 (Review Round 1/3)** của đợt thiết kế sơ đồ Chương 12–15.
> - Toàn bộ các yêu cầu kỹ thuật đã được hiệu chỉnh chính xác, nghiệm thu và cô lập an toàn trên branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG MERGE:** Nhánh thiết kế được giữ riêng biệt, không merge vào `main`.
> - **KHÔNG PUSH MAIN:** Chỉ push lên remote branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG CHỈNH SỬA MASTER PDF:** `Golang_Master.pdf` được bảo vệ nguyên vẹn 100%.
> - Tiến trình dừng tại đây để ChatGPT review độc lập và người dùng phê duyệt thủ công.
