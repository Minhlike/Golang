# BÁO CÁO HIỆU CHỈNH KỸ THUẬT SƠ ĐỒ (BATCH 02 - REVIEW ROUND 2/3)
## CHƯƠNG 12, 13, 15 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả hiệu chỉnh:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch12-15-agent2-redesign` (baseline: `8dd430f06f4dde0f79cb7f6d8e99309a55128c27`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt`, Review Round 2/3 Feedback, hợp đồng kỹ thuật thư viện chuẩn Go (`net/http`, `database/sql`, `os/exec`), quy chuẩn in ấn grayscale thuần túy.

---

## 1. Tóm tắt các hiệu chỉnh kỹ thuật trong Review Round 2/3

Theo phản hồi từ đợt duyệt kỹ thuật vòng 2/3 (Review Round 2/3), toàn bộ các chỉnh sửa đã được phẫu thuật trực tiếp trên mã nguồn tạo vector `scripts/ch12_15_vector_diagrams.py`, đảm bảo tuân thủ tuyệt đối quy tắc **STRICT CONTENT LOCK** (không sửa bất kỳ tệp Markdown, bài giảng, code block, bảng, caption, renderer chính hay `Golang_Master.pdf`).

### 1.1. Chương 12: `http-service-lifecycle.png`
1. **Signal lifecycle & Vị trí đăng ký context:**
   - Làm rõ: Việc đăng ký `signal.NotifyContext` và `defer stop()` được thiết lập tại **Process Boundary (Stage 1)** ngay trước khi gọi `srv.Serve(ln)`, chứ không phải đợi đến khi server phục vụ request xong mới đăng ký.
   - **Stage 3** được đặt tên và định nghĩa chính xác là **SỰ KIỆN TÍN HIỆU DỪNG (SIGNAL EVENT)**: biểu diễn thời điểm tín hiệu OS (`SIGINT`/`SIGTERM`) kích hoạt `<-ctx.Done()`, báo hiệu rút lui có kiểm soát trên toàn hệ thống.
2. **Shutdown semantics & Ranh giới trách nhiệm:**
   - Làm rõ trạng thái khi hết hạn grace: Việc hết hạn grace chỉ khiến `srv.Shutdown()` dừng chờ drain active handlers và trả về `context.DeadlineExceeded`. Tại thời điểm đó, **TCP listener và pool kết nối idle ĐÃ được đóng thành công từ trước**.
   - Việc cưỡng chế đóng các socket đang hoạt động (`srv.Close()`) hoặc ép thoát process (`os.Exit`) là chính sách riêng của caller, không bị hiểu nhầm là Shutdown chưa thực hiện gì.

### 1.2. Chương 13: `transaction-boundary.png`
1. **Bổ sung guard kiểm tra lỗi sau `BeginTx`:**
   - Khối Box 1 được bổ sung guard bắt buộc: `tx, err := db.BeginTx(ctx, nil)` đi kèm ngay với `if err != nil { return err }` trước khi gọi `defer tx.Rollback()`, phản ánh chính xác cấu trúc phòng vệ chuẩn trong `labs/part13-transaction-boundary/fixed/disable.go`.
2. **Bổ sung guard kiểm tra lỗi sau `RowsAffected`:**
   - Khối Box 2 được chuẩn hóa đầy đủ: sau `changed, err := result.RowsAffected()` có ngay `if err != nil { return err }` trước khi kiểm tra điều kiện nghiệp vụ `if changed == 0 { return ErrCheckNotFound }`.
3. **Giữ nguyên ranh giới kỹ thuật đã đạt:**
   - Bảo toàn trọn vẹn: Phân biệt `Commit` thành công (`err == nil`) với lỗi tại `Commit` (không bảo đảm rollback), ranh giới giữa Atomicity và Isolation, và việc DB rollback không thu hồi được external side effects (email, webhook, message queue).

### 1.3. Chương 15: `incident-command-lifecycle.png`
1. **Fixture kiểm thử thực tế từ bài giảng và lab:**
   - Thay thế toàn bộ tham số giả định bằng fixture helper process thực tế được dùng xuyên suốt bài giảng và test của lab (`fixed/run_test.go`):
     ```go
     spec := Spec{Name: os.Args[0], Timeout: 5*time.Second,
       Args: []string{"-test.run=^TestHelperProcess$",
         "-helper-mode=ok"}}
     ```
2. **Quy tắc `ProcessState` và `ExitCode`:**
   - Làm rõ tại thanh giám sát (Middle Bar) và thẻ kết cục 4: `cmd.ProcessState != nil` mới ghi nhận `ExitCode()`. Trường hợp không thể khởi chạy tiến trình (Start Failure), `ProcessState == nil` và `ExitCode` có giá trị mặc định là `-1` (chưa chạy).
3. **Mô hình bọc lỗi (`fmt.Errorf("%w")`) và bóc tách qua `errors.As`:**
   - Trong cả 3 kết cục lỗi (Outcome 2: Exit != 0, Outcome 3: Timeout/Cancel, Outcome 4: Start Failure), thể hiện đúng mã nguồn lab: hàm trả về `(Result, wrappedErr)` với các lỗi được bọc qua `fmt.Errorf("...: %w", err)`.
   - Nhấn mạnh caller sử dụng `errors.As(err, &exitErr)` để bóc tách `*exec.ExitError` xuyên qua chuỗi bọc `%w` của lab.
4. **Bố cục typography & Ngắt dòng chống tràn viền:**
   - Tinh chỉnh tọa độ và ngắt dòng hợp lý trong từng cột ($103.67\text{ pt}$), đảm bảo 100% nhãn có font size $\ge 6.0\text{ pt}$ và khoảng đệm an toàn lề $\ge 7.3\text{ pt}$, tuyệt đối không chạm viền.

---

## 2. Kết quả kiểm định chất lượng xuất bản (QA Test Matrix)

| Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Kết quả đo lường thực tế | Đánh giá |
| :--- | :--- | :--- | :--- |
| **Bảng màu thuần Grayscale** | $R = G = B$ trên 100% điểm ảnh; 0% màu pha | `max|R-G| = 0, max|R-B| = 0` trên cả 3 file PNG và 3 specimen | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của Master PDF | Ch12: $185.80 \times 362.83\text{ pt}$<br>Ch13: $422.77 \times 362.83\text{ pt}$<br>Ch15: $444.69 \times 362.83\text{ pt}$ | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | Ch12: $826 \times 1613\text{ px}$<br>Ch13: $1879 \times 1613\text{ px}$<br>Ch15: $1977 \times 1613\text{ px}$ | **PASS (100%)** |
| **Tiêu chuẩn Typography** | 100% nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | Min fontSize = $6.00\text{ pt}$; 0 nhãn dưới $6.0\text{ pt}$<br>• Ch12: 39 strings, $\min = 6.00\text{ pt}, \max = 6.60\text{ pt}$<br>• Ch13: 49 strings, $\min = 6.00\text{ pt}, \max = 7.40\text{ pt}$<br>• Ch15: 71 strings, $\min = 6.00\text{ pt}, \max = 7.00\text{ pt}$ | **PASS (100%)** |
| **Độ an toàn lề & Tràn chữ** | Không tràn khung, khoảng đệm an toàn $\ge 4.0\text{ pt}$ | 100% nhãn nằm gọn trong bounding box của từng card;<br>Zero text overflow trên mọi canvas; Ch15 đệm $\ge 7.3\text{ pt}$ | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests pass in 0.297s | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn (Usable width: 448.22 pt) | **PASS (100%)** |

---

## 3. Danh mục Tệp bàn giao trên Branch `design/ch12-15-agent2-redesign`

1. `assets/diagrams/http-service-lifecycle.png` (Hình 24, Chương 12: Đã chuẩn hóa signal lifecycle tại process boundary, ranh giới shutdown semantics)
2. `assets/diagrams/transaction-boundary.png` (Hình 25, Chương 13: Bổ sung guard lỗi BeginTx & RowsAffected, giữ ranh giới atomicity & isolation)
3. `assets/diagrams/incident-command-lifecycle.png` (Hình 26, Chương 15: Helper fixture thực tế, ProcessState guard, bọc lỗi %w & errors.As)
4. `scripts/ch12_15_vector_diagrams.py` (Script vẽ vector ReportLab cập nhật toàn diện theo Review Round 2/3)
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
> - Đây là **vòng sửa 2/3 (Review Round 2/3)** của đợt thiết kế sơ đồ Chương 12–15.
> - Toàn bộ các yêu cầu kỹ thuật đã được hiệu chỉnh chính xác, nghiệm thu và cô lập an toàn trên branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG MERGE:** Nhánh thiết kế được giữ riêng biệt, không merge vào `main`.
> - **KHÔNG PUSH MAIN:** Chỉ push lên remote branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG CHỈNH SỬA MASTER PDF:** `Golang_Master.pdf` được bảo vệ nguyên vẹn 100%.
> - Tiến trình dừng tại đây để ChatGPT review độc lập và người dùng phê duyệt thủ công.
