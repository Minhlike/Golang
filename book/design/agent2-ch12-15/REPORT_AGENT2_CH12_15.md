# BÁO CÁO HIỆU CHỈNH KỸ THUẬT SƠ ĐỒ (BATCH 02 - SCIENTIFIC QUALITY STANDARD)
## CHƯƠNG 12, 13, 15 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả hiệu chỉnh:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch12-15-agent2-redesign` (baseline: `68461f7`, commit chuẩn hóa `MASTER PROMPT.txt`: `69c207d`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt` (Mục 7: `SCIENTIFIC DIAGRAM QUALITY CONTRACT`), đối chiếu mã nguồn và test của lab (`labs/part12-service-lifecycle`, `labs/part13-transaction-boundary`, `labs/part15-incident-command`), quy chuẩn in ấn grayscale thuần túy.

---

## 1. Cập nhật Quy chuẩn Thiết kế Sơ đồ Khoa học (Section 7 MASTER PROMPT.txt)

Theo yêu cầu chuẩn hóa vĩnh viễn, tiểu mục `SCIENTIFIC DIAGRAM QUALITY CONTRACT — TIÊU CHUẨN SƠ ĐỒ KHOA HỌC` đã được bổ sung thành công vào **Mục 7** của [MASTER PROMPT.txt](file:///d:/Golang/MASTER%20PROMPT.txt) (Commit `69c207d`):

1. **Mental Model First:** Mỗi sơ đồ trả lời một câu hỏi kỹ thuật trọng tâm; mô tả rõ invariant và ranh giới trách nhiệm.
2. **Scientific Correctness:** Không thỏa hiệp tính đúng đắn kỹ thuật; mọi transition, nhánh rẽ, điều kiện dừng phải tương thích 100% với đặc tả Go runtime và source lab.
3. **Semantic Completeness:** Không bỏ sót nhánh rẽ trọng yếu (ví dụ: lỗi sớm trước signal so với shutdown sau signal).
4. **Right Abstraction Level:** Sơ đồ kiến trúc/vòng đời tập trung vào luồng trạng thái; không cố nén code block dài vào hộp hẹp.
5. **Code is Not Diagram:** Phân biệt rõ SQL tham số hóa (`VALUES (?, ?)`) với giá trị tham số runtime; trích đoạn Go phải syntactically valid hoặc là nhãn khái niệm rõ ràng.
6. **Information Economy:** Mỗi pixel mang thông tin; loại bỏ trang trí thừa.
7. **Visual Hierarchy:** Thứ tự thị giác phản ánh đúng thứ tự thời gian và độ ưu tiên logic.
8. **Publication Quality:** Tọa độ chính xác 1:1 theo Master PDF; grayscale thuần $R=G=B$; font size $\ge 6.0\text{ pt}$; khoảng đệm an toàn $\ge 4.0\text{ pt}$.
9. **Pedagogical Self-Containment:** Sơ đồ tự giải thích được mà không phụ thuộc vào context mơ hồ ngoài trang.
10. **Source Traceability:** Mọi khối hộp trên sơ đồ đều có địa chỉ đối chiếu trực tiếp đến file, hàm, dòng code trong `labs/`.
11. **Two-Stage Quality Gate:** Preflight kỹ thuật (đối chiếu mã nguồn) trước khi render visual.
12. **Acceptance Rule:** Một sơ đồ chỉ đạt khi đồng thời vượt qua bài kiểm tra tính đúng đắn kỹ thuật và bài kiểm tra chất lượng in ấn.

---

## 2. Phân tích Nguyên nhân Gốc & Giải pháp Kiến trúc Batch 02

Áp dụng trực tiếp 12 nguyên tắc trên vào đợt rà soát cuối của Batch 02:

1. **CH12 — Phân nhánh Độc lập tại Stage 3 (SELECT BAN ĐẦU) & Ranh giới Shutdown:**
   - *Vấn đề kỹ thuật:* Trước đây, mũi tên đi xuống từ Stage 3 nối vào Stage 4 (Graceful Shutdown) tạo cảm giác mọi nhánh thoát của Stage 3 đều đi vào Shutdown. Trên thực tế (`fixed/server.go#L115-L121`), `select` có 2 nhánh cạnh tranh hoàn toàn độc lập:
     * Nhánh `case err := <-serveErr:`: Nếu server gặp lỗi sớm (ví dụ: port conflict, network failure) hoặc đóng sớm trước khi nhận signal, helper trả lỗi sớm `fmt.Errorf("serve: %w", err)` (hoặc `nil` nếu `ErrServerClosed`), **hoàn toàn không kích hoạt `srv.Shutdown`**.
     * Nhánh `case <-ctx.Done():`: Khi có tín hiệu dừng (`SIGINT`/`SIGTERM`), helper mới chuyển tiếp sang Stage 4 để thực thi quy trình graceful shutdown.
   - *Giải pháp kiến trúc:* Tách Stage 3 thành 2 sub-card trực quan rõ ràng:
     * **Sub-card Trái:** `err := <-serveErr` $\rightarrow$ `THOÁT SỚM (RETURN)`. Không có mũi tên đi xuống Stage 4!
     * **Sub-card Phải:** `<-ctx.Done()` $\rightarrow$ `VÀO SHUTDOWN`. Mũi tên đi xuống Stage 4 xuất phát **duy nhất** từ sub-card này.
   - *Khoảng đệm an toàn:* Duy trì khoảng đệm sát đáy tại Stage 4 và Stage 5 $\ge 4.5\text{ pt}$ so với viền thẻ.

2. **CH13 — Tách bạch SQL Tham số hóa và Đối số Runtime:**
   - *Vấn đề kỹ thuật:* Câu lệnh INSERT trong Box 3 từng hiển thị `VALUES (?, 'disabled')`, trộn lẫn giữa cú pháp literal SQL và tham số hóa. Trong mã nguồn thực tế (`fixed/disable.go#L38-L40`), câu lệnh là `INSERT INTO check_events(check_id, action) VALUES (?, ?)` với 2 tham số được truyền lúc thực thi là `checkID` và chuỗi `"disabled"`.
   - *Giải pháp kiến trúc:*
     * Box 2 (UPDATE): `SQL: UPDATE checks SET enabled = 0 WHERE id = ?` kèm dòng `• Tham số thực tế: checkID`.
     * Box 3 (INSERT): `SQL: INSERT INTO check_events(check_id, action) VALUES (?, ?)` kèm dòng `• Tham số thực tế: checkID, "disabled"`.
     * Bảo toàn nguyên văn 100% các chuỗi bọc lỗi và ranh giới `defer tx.Rollback()`.

3. **CH15 — Bảo toàn Mô hình Thác Quyết định Đã Kiểm chứng:**
   - Giữ nguyên vẹn thác quyết định 4 nhánh ưu tiên tuần tự theo `fixed/run.go`:
     * Thao tác trung tâm: `err := cmd.Run()`
     * Ưu tiên 1: `runCtx.Err() != nil` $\rightarrow$ timeout/cancellation (`"command context: %w"`).
     * Ưu tiên 2: `err == nil` $\rightarrow$ thành công Exit 0.
     * Ưu tiên 3: `errors.As(err, &exitErr)` $\rightarrow$ non-zero exit code (`"command exited with code %d: %w"`).
     * Ưu tiên 4: Fallthrough $\rightarrow$ lỗi khởi chạy / start failure (`"start command: %w"`) với phân biệt trạng thái `ProcessState`.

---

## 3. Bảng Đối chiếu Preflight Mã nguồn (Mandatory Preflight Mapping)

| Sơ đồ | Phần tử trên sơ đồ | Dòng mã nguồn / Hợp đồng Go | Ý nghĩa kỹ thuật & Invariant |
| :--- | :--- | :--- | :--- |
| **Ch12** | `ctx, stop := signal.NotifyContext(...)` | `fixed/server.go` / `main()` | Process boundary đăng ký OS signal (`SIGINT`, `SIGTERM`), quản lý lifecycle dừng |
| **Ch12** | `go func() { serveErr <- srv.Serve(ln) }()` | `fixed/server.go#L112` | Helper mở goroutine chạy listener socket, truyền error qua buffered channel |
| **Ch12** | Sub-card Trái: `err := <-serveErr` | `fixed/server.go#L115-L119` | Nhánh lỗi sớm: trả `fmt.Errorf("serve: %w", err)` ngay, không đi vào Shutdown |
| **Ch12** | Sub-card Phải: `<-ctx.Done()` | `fixed/server.go#L120` | Nhánh nhận tín hiệu dừng: mũi tên duy nhất chuyển tiếp sang Graceful Shutdown |
| **Ch12** | `shutdownCtx, cancel := context.WithTimeout(Background(), grace)` | `fixed/server.go#L123-L124` | Context graceful shutdown hoàn toàn độc lập với root signal context |
| **Ch12** | `srv.Shutdown(shutdownCtx)` | `fixed/server.go#L125-L127` | Đóng listener, đóng idle pool, drain active requests; lỗi bọc `"shutdown: %w"` |
| **Ch12** | `err := <-serveErr; errors.Is(..., ErrServerClosed)` | `fixed/server.go#L128-L131` | Đồng bộ chờ `Serve` kết thúc với `ErrServerClosed`; cả hai thỏa mãn mới trả `nil` |
| **Ch13** | `tx, err := db.BeginTx(ctx, nil)` | `fixed/disable.go#L17-L20` | Mở transaction, bọc `"begin disable transaction: %w"` |
| **Ch13** | `defer tx.Rollback()` | `fixed/disable.go#L21` | Bảo hiểm hoàn nguyên tự động nếu return sớm; an toàn sau `Commit()` |
| **Ch13** | `UPDATE checks SET enabled = 0 WHERE id = ?` | `fixed/disable.go#L23-L28` | Câu lệnh 1 (tham số: `checkID`), kiểm tra lỗi Exec bọc `"disable check: %w"` |
| **Ch13** | `changed, err := result.RowsAffected()` | `fixed/disable.go#L29-L35` | Bọc `"count disabled checks: %w"`; `changed == 0` trả `ErrCheckNotFound` |
| **Ch13** | `INSERT INTO check_events(check_id, action) VALUES (?, ?)` | `fixed/disable.go#L37-L42` | Câu lệnh 2 (tham số: `checkID`, `"disabled"`), bọc `"record disable event: %w"` |
| **Ch13** | `tx.Commit()` | `fixed/disable.go#L43-L46` | Commit transaction, bọc `"commit disable: %w"`; hoàn tất nguyên tử (atomicity) |
| **Ch15** | `err := cmd.Run()` | `fixed/run.go#L44` | Khởi chạy executable con và chờ hoàn tất; thu thập stdout/stderr qua buffer riêng |
| **Ch15** | `[P1] runCtx.Err() != nil` | `fixed/run.go#L55-L58` | Ưu tiên 1: Deadline timeout / cancel; bọc `"command context: %w"` |
| **Ch15** | `[P2] err == nil` | `fixed/run.go#L59-L61` | Ưu tiên 2: Exit 0 thành công, trả `(Result, nil)` |
| **Ch15** | `[P3] errors.As(err, &exitErr)` | `fixed/run.go#L62-L69` | Ưu tiên 3: Lệnh lỗi `ExitCode != 0`, bọc `"command exited with code %d: %w"` |
| **Ch15** | `[P4] Fallthrough` | `fixed/run.go#L70` | Ưu tiên 4: Lỗi start / non-exit, bọc `"start command: %w"` |

---

## 4. Ma trận Kiểm định Chất lượng Xuất bản (QA Matrix)

| Tiêu chí kỹ thuật | Tiêu chuẩn bắt buộc | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Bảng màu Grayscale thuần** | $R = G = B$ 100% điểm ảnh; $\max\|R-G\|=0, \max\|R-B\|=0$ | $0\text{ tint}$ trên cả 3 PNG sơ đồ và 3 specimen preview | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của `Golang_Master.pdf` | Ch12: $185.80 \times 362.83\text{ pt}$<br>Ch13: $422.77 \times 362.83\text{ pt}$<br>Ch15: $444.69 \times 362.83\text{ pt}$ | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | Ch12: $826 \times 1613\text{ px}$ ($201\text{ KB}$)<br>Ch13: $1879 \times 1613\text{ px}$ ($347\text{ KB}$)<br>Ch15: $1977 \times 1613\text{ px}$ ($330\text{ KB}$) | **PASS (100%)** |
| **Tiêu chuẩn Typography** | 100% nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | Min fontSize = $6.00\text{ pt}$; 0 nhãn dưới $6.0\text{ pt}$<br>• Ch12: 48 strings, $\min = 6.00\text{ pt}$<br>• Ch13: 55 strings, $\min = 6.00\text{ pt}$<br>• Ch15: 77 strings, $\min = 6.00\text{ pt}$ | **PASS (100%)** |
| **An toàn lề & Khoảng đệm đáy** | Khoảng đệm an toàn $\ge 4.0\text{ pt}$ so với viền card | 100% dòng sát đáy có khoảng đệm $\ge 4.5\text{ pt}$:<br>• Ch12: $\min = 4.5\text{ pt}$<br>• Ch13: $\min = 4.5\text{ pt}$<br>• Ch15: $\min = 4.5\text{ pt}$ | **PASS (100%)** |
| **Tràn viền Canvas** | 0 text overflow trên mọi canvas | 0 string overflow trên cả 3 sơ đồ | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests passed (0.301s) | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn (Usable width: 448.22 pt) | **PASS (100%)** |

---

## 5. Danh mục Tệp Bàn giao

1. [assets/diagrams/http-service-lifecycle.png](file:///d:/Golang/assets/diagrams/http-service-lifecycle.png) (Hình 24, Chương 12: Stage 3 phân nhánh sớm không vào shutdown, mũi tên xuống chỉ xuất phát từ `<-ctx.Done()`)
2. [assets/diagrams/transaction-boundary.png](file:///d:/Golang/assets/diagrams/transaction-boundary.png) (Hình 25, Chương 13: SQL tham số hóa `VALUES (?, ?)`, tham số runtime tách riêng, bảo toàn chuỗi bọc lỗi)
3. [assets/diagrams/incident-command-lifecycle.png](file:///d:/Golang/assets/diagrams/incident-command-lifecycle.png) (Hình 26, Chương 15: Mô hình thác quyết định 4 nhánh chuẩn xác)
4. [scripts/ch12_15_vector_diagrams.py](file:///d:/Golang/scripts/ch12_15_vector_diagrams.py) (Generator vector hoàn thiện)
5. [scripts/build_ch12_15_preview.py](file:///d:/Golang/scripts/build_ch12_15_preview.py) (Script build preview và specimen)
6. [book/design/agent2-ch12-15/ch12_15_preview.pdf](file:///d:/Golang/book/design/agent2-ch12-15/ch12_15_preview.pdf) (Preview PDF 3 trang 1:1)
7. [book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png](file:///d:/Golang/book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png) (Specimen Trang 1: Chương 12)
8. [book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png](file:///d:/Golang/book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png) (Specimen Trang 2: Chương 13)
9. [book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png](file:///d:/Golang/book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png) (Specimen Trang 3: Chương 15)
10. [book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md](file:///d:/Golang/book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md) (Báo cáo kỹ thuật chi tiết)

---

## 6. Cổng Phê duyệt (Hard Approval Gate)

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**
> - Quy chuẩn `SCIENTIFIC DIAGRAM QUALITY CONTRACT` đã được cam kết thành công trong commit `69c207d`.
> - Toàn bộ 3 sơ đồ Batch 02 đã được cập nhật và nghiệm thu kỹ thuật theo đúng 12 nguyên tắc chuẩn mực.
> - **KHÔNG MERGE:** Nhánh thiết kế được giữ riêng biệt trên `design/ch12-15-agent2-redesign`, không merge vào `main`.
> - **KHÔNG PUSH MAIN:** Chỉ push lên remote branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG CHỈNH SỬA MASTER PDF:** `Golang_Master.pdf` được bảo vệ nguyên vẹn 100%.
> - Dừng tại trạng thái này để ChatGPT review độc lập và người dùng phê duyệt thủ công.
