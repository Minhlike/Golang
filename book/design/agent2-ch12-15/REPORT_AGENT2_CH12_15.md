# BÁO CÁO THIẾT KẾ SƠ ĐỒ KỸ THUẬT: CHƯƠNG 12, 13, 15 (BATCH 02)

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả thiết kế:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch12-15-agent2-redesign` (tách từ `main`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt`, hợp đồng kỹ thuật thư viện chuẩn Go, quy chuẩn in ấn grayscale thuần túy.

---

## 1. Tổng quan đợt thiết kế (Batch 02)

Đợt 02 tập trung tái thiết kế vector toàn diện cho **duy nhất 3 sơ đồ kỹ thuật** thuộc các Chương 12, 13 và 15 (Chương 14 không có sơ đồ theo đúng cấu trúc sách). Tất cả các sơ đồ đều được xây dựng trực tiếp bằng vector ReportLab (`Drawing`, `Rect`, `String`, `Path`), loại bỏ hoàn toàn sơ đồ raster chất lượng thấp từ PlantUML, đạt độ phân giải xuất bản 320 DPI và tuân thủ bảng màu thuần sắc độ xám ($R=G=B$ tuyệt đối trên mọi điểm ảnh).

| Chương | Tệp sơ đồ | Hình số | Trang Master PDF | Xref ID | Kích thước xuất bản (pt) | Tỷ lệ khung hình (W/H) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Chương 12** | `assets/diagrams/http-service-lifecycle.png` | Hình 24 | Trang 217 | xref 477 | $185.80 \times 362.83\text{ pt}$ | $0.51208$ (Dọc hẹp) |
| **Chương 13** | `assets/diagrams/transaction-boundary.png` | Hình 25 | Trang 233 | xref 510 | $422.77 \times 362.83\text{ pt}$ | $1.16518$ (Ngang rộng) |
| **Chương 15** | `assets/diagrams/incident-command-lifecycle.png` | Hình 26 | Trang 272 | xref 589 | $444.69 \times 362.83\text{ pt}$ | $1.22561$ (Ngang cực đại) |

---

## 2. Phân tích kỹ thuật chuyên sâu & Mô hình tư duy (Technical Preflight)

### 2.1. Chương 12: `http-service-lifecycle.png` — Vòng đời phục vụ và rút lui của HTTP Service
- **Ngữ cảnh & Lab đối chiếu:** `book/chapters/12-service-lifecycle.md`, `labs/part12-service-lifecycle/fixed/service.go`.
- **Thách thức bố cục:** Khung hình rất hẹp theo chiều ngang ($185.80\text{ pt}$) nhưng cao ($362.83\text{ pt}$). Mọi dòng mã Go và nhãn kỹ thuật phải được phân dòng cẩn trọng, kiểm soát độ rộng chính xác để không tràn lề hoặc chạm khung viền.
- **Mô hình tư duy 5 chặng liên hoàn:**
  1. **Khởi động Listener & Phục vụ:** `net.Listen("tcp", addr)` thiết lập TCP listener; `go srv.Serve(lis)` bắt đầu vòng lặp tiếp nhận kết nối (chạy trên goroutine độc lập để không chặn luồng chính).
  2. **Tiếp nhận & Xử lý Request:** Mỗi kết nối được cấp phát goroutine riêng, gắn với `r.Context()`.
  3. **Tín hiệu dừng OS:** `signal.NotifyContext(baseCtx, os.Interrupt, syscall.SIGTERM)` chặn chờ tín hiệu từ hệ điều hành; khi nhận tín hiệu, context kích hoạt quy trình rút lui.
  4. **Graceful Shutdown:** `shutdownCtx, _ := context.WithTimeout(base, grace)` cấp ngân sách thời gian rút lui độc lập; `srv.Shutdown(shutdownCtx)` thực thi tuần tự:
     - Đóng TCP listener ngay lập tức (từ chối kết nối mới).
     - Đóng toàn bộ idle connections trong pool.
     - Chờ các request đang xử lý (active requests) hoàn tất tự nhiên.
  5. **Phân nhánh kết cục:**
     - *Trong hạn grace:* Toàn bộ active request hoàn tất, `srv.Shutdown()` trả về `nil`, service thoát sạch.
     - *Quá hạn timeout:* `shutdownCtx.Err() == context.DeadlineExceeded`, cưỡng chế đóng kết nối còn sót lại.
- **Ranh giới bất biến kỹ thuật (Card Footer):**
  - `Server.Shutdown` **không tự hủy (`cancel`)** context của các request handler đang chạy; ứng dụng phải tự quản lý context phân tán nếu muốn ngắt sớm.
  - `Shutdown` **không tự động chờ** các kết nối bị hijacked (như WebSocket hoặc raw TCP).
  - Kết nối cơ sở dữ liệu (`db.Close()`) và logger cần được đóng chủ động sau khi `Shutdown` hoàn tất.

### 2.2. Chương 13: `transaction-boundary.png` — Ranh giới Transaction và Tính nguyên tử (Atomicity)
- **Ngữ cảnh & Lab đối chiếu:** `book/chapters/13-transaction-boundary.md`, `labs/part13-transaction-boundary/fixed/store.go`.
- **Thách thức bố cục:** Khung hình ngang rộng ($422.77\text{ pt}$), yêu cầu phân tách rõ ranh giới transaction database với các tác động bên ngoài (side effects).
- **Cấu trúc 2 cột đối xứng:**
  - **Cột trái — Vùng chứa Transaction (`sql.Tx` Container):**
    - `tx, err := db.BeginTx(ctx, &sql.TxOptions{})`: Khởi tạo transaction context trên một kết nối chuyên dụng.
    - `defer tx.Rollback()`: Đăng ký bảo hiểm an toàn ngay sau khi khởi tạo; nếu `Commit()` thành công trước đó thì lệnh Rollback trong defer trở thành vô hại (`sql.ErrTxDone`).
    - *Thao tác 1:* `res, err := tx.ExecContext(ctx, "UPDATE checks SET ...")` đi kèm kiểm tra số dòng ảnh hưởng: `if rows == 0 { return ErrCheckNotFound }`.
    - *Thao tác 2:* `_, err = tx.ExecContext(ctx, "INSERT INTO check_events ... VALUES (?, 'disabled')")` ghi nhận audit event.
    - *Điểm chốt hợp đồng:* `if err := tx.Commit(); err != nil { return err }`.
  - **Cột phải — Hai nhánh kết cục (Outcomes):**
    - *Nhánh 1 (Commit - Thành công):* Cả 2 câu lệnh cùng được ghi bền vững vào cơ sở dữ liệu (Durability); giải phóng kết nối về pool.
    - *Nhánh 2 (Rollback - Thất bại):* Nếu Thao tác 1 hoặc Thao tác 2 lỗi, hoặc quá hạn context, toàn bộ các thay đổi chưa commit bị loại bỏ sạch sẽ; trạng thái dữ liệu quay về mốc ban đầu; trả kết nối về pool.
- **Hộp phân định kỹ thuật (Footer Box):**
  - Phân biệt rành mạch giữa **Tính nguyên tử (Atomicity)** (tất cả hoặc không gì cả) với **Mức cô lập (Isolation)** (mức độ thấy nhau giữa các transaction đồng thời).
  - Ghi nhận bất biến: Cơ sở dữ liệu **chỉ rollback dữ liệu nội bộ**, không thể rollback các tác dụng phụ bên ngoài (external side effects) như lời gọi Webhook, phát Event Kafka hoặc ghi log file.

### 2.3. Chương 15: `incident-command-lifecycle.png` — Vòng đời giám sát tiến trình sự cố (Process Supervision)
- **Ngữ cảnh & Lab đối chiếu:** `book/chapters/15-incident-command.md`, `labs/part15-incident-command/fixed/runner.go`.
- **Thách thức bố cục:** Khung hình cực đại ($444.69 \times 362.83\text{ pt}$), cần thể hiện trọn vẹn quy trình gọi tiến trình hệ thống bằng `os/exec` an toàn và phân loại 4 trạng thái kết thúc.
- **Quy trình giám sát khép kín:**
  1. **Đặc tả Command không qua Shell (Safe Spec):** Sử dụng `Spec{Name: "ping", Args: []string{"-c", "3", host}}`. Khẳng định: `exec.CommandContext` truyền mảng tham số trực tiếp vào system call (`fork/exec` hoặc `CreateProcess`), tuyệt đối **không gọi shell ngầm** (`sh -c` hay `cmd.exe`), triệt tiêu hoàn toàn lỗ hổng Command Injection.
  2. **Thiết lập Ngân sách & Buffer I/O độc lập:**
     - `ctx, cancel := context.WithTimeout(baseCtx, timeout)`
     - Tách riêng hai buffer: `cmd.Stdout = &stdoutBuf` và `cmd.Stderr = &stderrBuf` để bảo toàn thông điệp chẩn đoán lỗi.
  3. **Giám sát thực thi (`cmd.Run()`):** Go runtime chờ tiến trình con; nếu context timeout/canceled trước khi xong, `os/exec` gửi tín hiệu ngắt (SIGKILL) để giải phóng process table.
  4. **Phân loại chính xác 4 kết cục (4 Outcome Cards):**
     - *Thành công (Exit 0):* `err == nil`, lệnh hoàn thành trong hạn timeout, lấy stdout.
     - *Lệnh thất bại (Exit khác 0):* `errors.As(err, &exitErr)`, tiến trình chạy xong nhưng trả về exit code lỗi; stderr được bảo toàn nguyên vẹn làm bằng chứng chẩn đoán.
     - *Timeout / Huỷ bỏ:* `ctx.Err() == context.DeadlineExceeded`, tiến trình bị terminate do quá hạn ngân sách.
     - *Lỗi khởi chạy:* Không tìm thấy file thực thi (`exec.ErrNotFound`) hoặc thiếu quyền cấp phép; không có PID nào được tạo ra.
- **Băng kết luận phương pháp luận (Footer Invariant):**
  - Cấu trúc `Result` phản ánh **bằng chứng quan sát cục bộ** tại thời điểm kiểm tra, không tự ý suy diễn hoặc thay thế kết luận nguyên nhân gốc của sự cố hạ tầng.

---

## 3. Kết quả kiểm định chất lượng xuất bản (QA Test Suite)

| Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Kết quả đo lường thực tế | Đánh giá |
| :--- | :--- | :--- | :--- |
| **Bảng màu thuần Grayscale** | $R = G = B$ trên 100% điểm ảnh; không có kênh màu phụ | `max|R-G| = 0, max|R-B| = 0` trên cả 3 file PNG | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác kích thước xref của Master PDF | Ch12: $185.80 \times 362.83\text{ pt}$<br>Ch13: $422.77 \times 362.83\text{ pt}$<br>Ch15: $444.69 \times 362.83\text{ pt}$ | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | Ch12: $826 \times 1613\text{ px}$<br>Ch13: $1879 \times 1613\text{ px}$<br>Ch15: $1977 \times 1613\text{ px}$ | **PASS (100%)** |
| **Tiêu chuẩn Typography** | Mọi nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | 148/148 nhãn văn bản có `fontSize >= 6.00 pt`<br>• Ch12: 37 strings, $\min = 6.00\text{ pt}, \max = 6.60\text{ pt}$<br>• Ch13: 47 strings, $\min = 6.00\text{ pt}, \max = 7.40\text{ pt}$<br>• Ch15: 64 strings, $\min = 6.00\text{ pt}, \max = 7.00\text{ pt}$ | **PASS (100%)** |
| **Độ an toàn lề & Tràn chữ** | Không tràn khung, khoảng đệm an toàn $\ge 4.0\text{ pt}$ | 100% nhãn nằm gọn trong bounding box của từng card;<br>Zero overflow trên mọi canvas | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ file Markdown | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests pass in 0.307s | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn | **PASS (100%)** |

---

## 4. Danh mục tệp cập nhật trên branch `design/ch12-15-agent2-redesign`

1. `assets/diagrams/http-service-lifecycle.png` (Hình 24, Chương 12: Vòng đời HTTP Service)
2. `assets/diagrams/transaction-boundary.png` (Hình 25, Chương 13: Ranh giới Transaction & Atomicity)
3. `assets/diagrams/incident-command-lifecycle.png` (Hình 26, Chương 15: Giám sát tiến trình sự cố)
4. `scripts/ch12_15_vector_diagrams.py` (Script vẽ vector ReportLab và xuất PNG 320 DPI)
5. `scripts/build_ch12_15_preview.py` (Script dựng Preview PDF độc lập và xuất visual specimens)
6. `book/design/agent2-ch12-15/ch12_15_preview.pdf` (Preview PDF 3 trang 1:1 độc lập)
7. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png` (Specimen trực quan Trang 1: Chương 12)
8. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png` (Specimen trực quan Trang 2: Chương 13)
9. `book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png` (Specimen trực quan Trang 3: Chương 15)
10. `book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md` (Tài liệu báo cáo kỹ thuật này)

---

## 5. Hard Approval Gate

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**
> - Toàn bộ công việc tái thiết kế Đợt 02 (Chương 12–15) đã hoàn tất và được cô lập an toàn trên branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG MERGE:** Nhánh thiết kế được giữ riêng biệt, không merge vào `main`.
> - **KHÔNG PUSH MAIN:** Chỉ push lên remote branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG CHỈNH SỬA MASTER PDF:** `Golang_Master.pdf` được bảo vệ nguyên vẹn 100%.
> - Chờ ChatGPT review và người dùng phê duyệt thủ công trước khi chuyển sang các bước tiếp theo.
