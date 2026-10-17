# BÁO CÁO HIỆU CHỈNH KỸ THUẬT SƠ ĐỒ (BATCH 02 - CORRECTIVE REVIEW)
## CHƯƠNG 12, 13, 15 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả hiệu chỉnh:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch12-15-agent2-redesign` (baseline: `0c72c9dd943c338350465beaac8ff915d9d4f9e6`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt`, Corrective Review Feedback, đối chiếu mã nguồn và test của lab (`labs/part12-service-lifecycle`, `labs/part13-transaction-boundary`, `labs/part15-incident-command`), quy chuẩn in ấn grayscale thuần túy.

---

## 1. Phân tích Nguyên nhân Gốc & Giải pháp Kiến trúc (Root-Cause Resolutions)

Qua quá trình rà soát đối chiếu toàn diện giữa sơ đồ kỹ thuật và mã nguồn thực tế của thư viện chuẩn Go cũng như các lab mẫu, các vấn đề kỹ thuật trước đó đã được giải quyết triệt để theo đúng nguyên lý cốt lõi:

1. **CH12 — Bổ sung Nhánh Rẽ Select Ban Đầu & Khoảng đệm An toàn:**
   - *Nguyên nhân trước đó:* Sơ đồ chỉ thể hiện nhánh dừng graceful (`<-ctx.Done()`) mà bỏ quên nhánh `case err := <-serveErr:` trong `select` ban đầu của `ServeUntilStopped`. Nếu `srv.Serve(ln)` gặp lỗi sớm trước khi có tín hiệu dừng (port in use, lỗi socket mạng), helper thoát ngay với `fmt.Errorf("serve: %w", err)` mà không đi vào shutdown.
   - *Giải pháp:* Tại **Stage 3 (SELECT BAN ĐẦU)**, thể hiện rõ ràng `select` với hai nhánh phân định:
     * Nhánh 1 (Lỗi sớm trước signal): `case err := <-serveErr:` $\rightarrow$ thoát lỗi với `return fmt.Errorf("serve: %w", err)`.
     * Nhánh 2 (Tín hiệu dừng): `case <-ctx.Done():` $\rightarrow$ chuyển tiếp sang quy trình Graceful Shutdown.
   - *Khắc phục lỗi khoảng đệm:* Điều chỉnh vị trí dòng chữ sát đáy tại Stage 4 và Stage 5 từ `y + 1.5 pt` lên `y + 4.5 pt` / `y + 5.0 pt`, đảm bảo khoảng đệm an toàn $\ge 4.0\text{ pt}$ so với viền thẻ và đường nối.

2. **CH13 — Loại bỏ Biến Chưa Định nghĩa (`queryUpd`, `queryIns`) & Bảo toàn Tính Trung thực Kỹ thuật:**
   - *Nguyên nhân trước đó:* Việc cố gắng nén lời gọi `tx.ExecContext` trên 1 dòng dẫn tới việc tự ý giới thiệu hai biến giả định `queryUpd` và `queryIns` mà không khai báo, gây hiểu sai cú pháp Go.
   - *Giải pháp triệt để:* Chuyển sang mô hình sơ đồ kiến trúc khái niệm chuẩn mực:
     * Thể hiện rõ ràng câu lệnh SQL: `UPDATE checks SET enabled = 0 WHERE id = ?` và `INSERT INTO check_events(check_id, action) VALUES (?, 'disabled')`.
     * Giữ nguyên 100% nguyên văn chuỗi bọc lỗi theo `fixed/disable.go`: `"begin disable transaction: %w"`, `"disable check: %w"`, `"count disabled checks: %w"`, `ErrCheckNotFound`, `"record disable event: %w"`, `"commit disable: %w"`.
     * Thể hiện đầy đủ luồng thực thi liên tục `BeginTx → UPDATE → RowsAffected → INSERT → Commit`, thứ tự các guard và các nhánh lỗi kích hoạt `defer tx.Rollback()`.

3. **CH15 — Khôi phục Thao tác Thực thi `err := cmd.Run()` & Cú pháp Chuẩn `errors.As`:**
   - *Nguyên nhân trước đó:* Thanh điều phối trung gian bị thiếu lời gọi thực thi trung tâm `err := cmd.Run()`; thẻ kết quả 3 thiếu tham số `err` trong lời gọi `errors.As(&exitErr)`.
   - *Giải pháp:*
     * Khôi phục rõ ràng tại Middle Bar: `THỰC THI & GIÁM SÁT TIẾN TRÌNH: err := cmd.Run()`.
     * Chuẩn hóa cú pháp thẻ 3 với đầy đủ 2 tham số: `var exitErr *exec.ExitError` và `errors.As(err, &exitErr)`.
     * Giữ đúng hợp đồng phân loại Outcome 4: phân biệt rõ giữa chưa start (`cmd.ProcessState == nil`, ExitCode = -1) và đã start nhưng lỗi copy stream I/O / pipe setup (`cmd.ProcessState != nil`).

---

## 2. Bảng Đối chiếu Preflight Mã nguồn (Mandatory Preflight Mapping)

| Sơ đồ | Phần tử trên sơ đồ | Dòng mã nguồn / Hợp đồng Go | Ý nghĩa kỹ thuật & Invariant |
| :--- | :--- | :--- | :--- |
| **Ch12** | `ctx, stop := signal.NotifyContext(...)` | `fixed/server.go` / `main()` | Process boundary đăng ký OS signal (`SIGINT`, `SIGTERM`), quản lý lifecycle dừng |
| **Ch12** | `go func() { serveErr <- srv.Serve(ln) }()` | `fixed/server.go#L112` | Helper mở goroutine chạy listener socket, truyền error qua buffered channel |
| **Ch12** | `case err := <-serveErr:` | `fixed/server.go#L115-L119` | Nhánh lỗi sớm trước signal: trả `fmt.Errorf("serve: %w", err)` ngay lập tức |
| **Ch12** | `case <-ctx.Done():` | `fixed/server.go#L120` | Nhánh nhận tín hiệu dừng: kích hoạt quy trình graceful shutdown |
| **Ch12** | `shutdownCtx, cancel := context.WithTimeout(Background(), grace)` | `fixed/server.go#L123-L124` | Context graceful shutdown hoàn toàn độc lập với root signal context |
| **Ch12** | `srv.Shutdown(shutdownCtx)` | `fixed/server.go#L125-L127` | Đóng listener, đóng idle pool, drain active requests; lỗi bọc `"shutdown: %w"` |
| **Ch12** | `err := <-serveErr; errors.Is(..., ErrServerClosed)` | `fixed/server.go#L128-L131` | Đồng bộ chờ `Serve` kết thúc với `ErrServerClosed`; cả hai thỏa mãn mới trả `nil` |
| **Ch13** | `tx, err := db.BeginTx(ctx, nil)` | `fixed/disable.go#L17-L20` | Mở transaction, bọc `"begin disable transaction: %w"` |
| **Ch13** | `defer tx.Rollback()` | `fixed/disable.go#L21` | Bảo hiểm hoàn nguyên tự động nếu return sớm; an toàn sau `Commit()` |
| **Ch13** | `UPDATE checks SET enabled = 0 WHERE id = ?` | `fixed/disable.go#L23-L28` | Câu lệnh 1, kiểm tra lỗi Exec bọc `"disable check: %w"` |
| **Ch13** | `changed, err := result.RowsAffected()` | `fixed/disable.go#L29-L35` | Bọc `"count disabled checks: %w"`; `changed == 0` trả `ErrCheckNotFound` |
| **Ch13** | `INSERT INTO check_events(check_id, action)` | `fixed/disable.go#L37-L42` | Câu lệnh 2, kiểm tra lỗi Exec bọc `"record disable event: %w"` |
| **Ch13** | `tx.Commit()` | `fixed/disable.go#L43-L46` | Commit transaction, bọc `"commit disable: %w"`; hoàn tất nguyên tử (atomicity) |
| **Ch15** | `err := cmd.Run()` | `fixed/run.go#L44` | Khởi chạy executable con và chờ hoàn tất; thu thập stdout/stderr qua buffer riêng |
| **Ch15** | `[P1] runCtx.Err() != nil` | `fixed/run.go#L55-L58` | Ưu tiên 1: Deadline timeout / cancel; bọc `"command context: %w"` |
| **Ch15** | `[P2] err == nil` | `fixed/run.go#L59-L61` | Ưu tiên 2: Exit 0 thành công, trả `(Result, nil)` |
| **Ch15** | `[P3] errors.As(err, &exitErr)` | `fixed/run.go#L62-L69` | Ưu tiên 3: Lệnh lỗi `ExitCode != 0`, bọc `"command exited with code %d: %w"` |
| **Ch15** | `[P4] Fallthrough` | `fixed/run.go#L70` | Ưu tiên 4: Lỗi start / non-exit, bọc `"start command: %w"` |

---

## 3. Ma trận Kiểm định Chất lượng Xuất bản (QA Matrix)

| Tiêu chí kỹ thuật | Tiêu chuẩn bắt buộc | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Bảng màu Grayscale thuần** | $R = G = B$ 100% điểm ảnh; $\max\|R-G\|=0, \max\|R-B\|=0$ | $0\text{ tint}$ trên cả 3 PNG sơ đồ và 3 specimen preview | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của `Golang_Master.pdf` | Ch12: $185.80 \times 362.83\text{ pt}$<br>Ch13: $422.77 \times 362.83\text{ pt}$<br>Ch15: $444.69 \times 362.83\text{ pt}$ | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | Ch12: $826 \times 1613\text{ px}$ ($200\text{ KB}$)<br>Ch13: $1879 \times 1613\text{ px}$ ($342\text{ KB}$)<br>Ch15: $1977 \times 1613\text{ px}$ ($330\text{ KB}$) | **PASS (100%)** |
| **Tiêu chuẩn Typography** | 100% nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | Min fontSize = $6.00\text{ pt}$; 0 nhãn dưới $6.0\text{ pt}$<br>• Ch12: 45 strings, $\min = 6.00\text{ pt}$<br>• Ch13: 54 strings, $\min = 6.00\text{ pt}$<br>• Ch15: 77 strings, $\min = 6.00\text{ pt}$ | **PASS (100%)** |
| **An toàn lề & Khoảng đệm đáy** | Khoảng đệm an toàn $\ge 4.0\text{ pt}$ so với viền card | 100% dòng sát đáy có khoảng đệm $\ge 4.5\text{ pt}$:<br>• Ch12: $\min = 4.5\text{ pt}$<br>• Ch13: $\min = 4.5\text{ pt}$<br>• Ch15: $\min = 4.5\text{ pt}$ | **PASS (100%)** |
| **Tràn viền Canvas** | 0 text overflow trên mọi canvas | 0 string overflow trên cả 3 sơ đồ | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests passed (0.318s) | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn (Usable width: 448.22 pt) | **PASS (100%)** |

---

## 4. Danh mục Tệp Bàn giao

1. [assets/diagrams/http-service-lifecycle.png](file:///d:/Golang/assets/diagrams/http-service-lifecycle.png) (Hình 24, Chương 12: Nhánh rẽ select ban đầu, quy trình shutdown và đệm viền an toàn)
2. [assets/diagrams/transaction-boundary.png](file:///d:/Golang/assets/diagrams/transaction-boundary.png) (Hình 25, Chương 13: Mô hình kiến trúc rõ ràng, không biến chưa khai báo, đồng bộ 100% chuỗi bọc lỗi)
3. [assets/diagrams/incident-command-lifecycle.png](file:///d:/Golang/assets/diagrams/incident-command-lifecycle.png) (Hình 26, Chương 15: Khôi phục cmd.Run(), chuẩn hóa errors.As(err, &exitErr) và phân định ProcessState)
4. [scripts/ch12_15_vector_diagrams.py](file:///d:/Golang/scripts/ch12_15_vector_diagrams.py) (Generator vector hoàn thiện)
5. [scripts/build_ch12_15_preview.py](file:///d:/Golang/scripts/build_ch12_15_preview.py) (Script build preview và specimen)
6. [book/design/agent2-ch12-15/ch12_15_preview.pdf](file:///d:/Golang/book/design/agent2-ch12-15/ch12_15_preview.pdf) (Preview PDF 3 trang 1:1)
7. [book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png](file:///d:/Golang/book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png) (Specimen Trang 1: Chương 12)
8. [book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png](file:///d:/Golang/book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png) (Specimen Trang 2: Chương 13)
9. [book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png](file:///d:/Golang/book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png) (Specimen Trang 3: Chương 15)
10. [book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md](file:///d:/Golang/book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md) (Báo cáo kỹ thuật chi tiết)

---

## 5. Cổng Phê duyệt (Hard Approval Gate)

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**
> - Toàn bộ các nguyên nhân gốc và yêu cầu hiệu chỉnh kỹ thuật tại vòng Corrective Review đã được xử lý triệt để và kiểm chứng độc lập.
> - **KHÔNG MERGE:** Nhánh thiết kế được giữ riêng biệt trên `design/ch12-15-agent2-redesign`, không merge vào `main`.
> - **KHÔNG PUSH MAIN:** Chỉ push lên remote branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG CHỈNH SỬA MASTER PDF:** `Golang_Master.pdf` được bảo vệ nguyên vẹn 100%.
> - Dừng tại trạng thái này để ChatGPT review độc lập và người dùng phê duyệt thủ công.
