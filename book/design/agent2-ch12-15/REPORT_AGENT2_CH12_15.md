# BÁO CÁO NGHIỆM THU KỸ THUẬT SƠ ĐỒ (BATCH 02 - FINAL ACCEPTANCE)
## CHƯƠNG 12, 13, 15 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả hiệu chỉnh:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch12-15-agent2-redesign` (baseline: `8e022089fb077adcd9a27592565735997d667404`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt` (Mục 7: `SCIENTIFIC DIAGRAM QUALITY CONTRACT`), đối chiếu mã nguồn và test của lab (`labs/part12-service-lifecycle`, `labs/part13-transaction-boundary`, `labs/part15-incident-command`), quy chuẩn in ấn grayscale thuần túy.

---

## 1. Chuẩn hóa Quy chuẩn Thiết kế Sơ đồ Khoa học (MASTER PROMPT.txt Mục 7)

Trong nguyên tắc `8. PUBLICATION QUALITY` tại Mục 7 của [MASTER PROMPT.txt](file:///d:/Golang/MASTER%20PROMPT.txt), hai định nghĩa kỹ thuật đã được chuẩn hóa chính xác theo yêu cầu:
1. **DPI là thuộc tính của artifact raster, không phải của hình vector gốc:** Nguồn vector ReportLab hoàn toàn độc lập độ phân giải; thông số $\ge 300\text{ DPI}$ là thuộc tính đo lường của artifact raster khi xuất bản (PNG/pixmap).
2. **Khoảng đệm an toàn tối thiểu $\ge 4.0\text{ pt}$ đo từ bounding box chữ thực tế đến viền khung:** Không chỉ tính từ text baseline; khoảng đệm được đo từ điểm thấp nhất của glyph (bao gồm descenders và dấu phụ tiếng Việt như dấu nặng `.` dưới ký tự) tới viền card, loại bỏ hoàn toàn nguy cơ chạm viền.

---

## 2. Chi tiết Hiệu chỉnh Nghiệm thu Cuối cùng (Final Acceptance Scope)

Theo xác nhận của Reviewer, **Chương 13 và Chương 15 đã đạt yêu cầu nghiệm thu và được giữ nguyên vẹn 100%**. Phạm vi hiệu chỉnh kỹ thuật duy nhất được thực hiện tại Chương 12:

1. **CH12 — Chuỗi Điều phối Chính xác tại Stage 4 (Server.Shutdown):**
   - *Đối chiếu mã nguồn:* Trong [`fixed/server.go#L125-L131`](file:///d:/Golang/labs/part12-service-lifecycle/fixed/server.go#L125-L131):
     ```go
     if err := srv.Shutdown(shutdownCtx); err != nil {
         return fmt.Errorf("shutdown: %w", err)
     }
     if err := <-serveErr; !errors.Is(err, http.ErrServerClosed) {
         return fmt.Errorf("serve after shutdown: %w", err)
     }
     return nil
     ```
   - *Trình bày trên sơ đồ Stage 4:*
     * Dòng 1-2: `shutdownCtx, cancel := context.WithTimeout(context.Background(), grace); defer cancel()`
     * Dòng 3-4: `1. err := srv.Shutdown(shutdownCtx)` $\rightarrow$ `• Lỗi Shutdown => return fmt.Errorf("shutdown: %w", err)` (thoát lỗi ngay lập tức, không chờ `serveErr`).
     * Dòng 5-7: `2. Chỉ khi Shutdown thành công mới nhận <-serveErr:` $\rightarrow$ `• Khớp ErrServerClosed => return nil (sạch)` / `• Khác ErrServerClosed => bọc lỗi và trả về`.
   - *Bảo toàn kiến trúc:* Giữ nguyên toàn bộ cấu trúc Stage 3 (Left sub-card return sớm, Right sub-card chuyển tiếp vào shutdown) và bố cục dọc 5 stage đã đạt nghiệm thu.

2. **CH13 & CH15 — Khóa Nội dung Nghiệm thu (Content Locked):**
   - Chương 13 (`assets/diagrams/transaction-boundary.png`): Giữ nguyên vẹn SQL tham số hóa `VALUES (?, ?)`, tham số runtime `checkID, "disabled"`, các chuỗi bọc lỗi và ranh giới atomicity.
   - Chương 15 (`assets/diagrams/incident-command-lifecycle.png`): Giữ nguyên vẹn mô hình thác quyết định 4 nhánh ưu tiên, `cmd.Run()`, `errors.As(err, &exitErr)` và phân loại `ProcessState`.

---

## 3. Bảng Đối chiếu Preflight Mã nguồn (Mandatory Preflight Mapping)

| Sơ đồ | Phần tử trên sơ đồ | Dòng mã nguồn / Hợp đồng Go | Ý nghĩa kỹ thuật & Invariant |
| :--- | :--- | :--- | :--- |
| **Ch12** | `ctx, stop := signal.NotifyContext(...)` | `fixed/server.go` / `main()` | Process boundary đăng ký OS signal (`SIGINT`, `SIGTERM`), quản lý lifecycle dừng |
| **Ch12** | `go func() { serveErr <- srv.Serve(ln) }()` | `fixed/server.go#L112` | Helper mở goroutine chạy listener socket, truyền error qua buffered channel |
| **Ch12** | Sub-card Trái: `err := <-serveErr` | `fixed/server.go#L115-L119` | Nhánh lỗi sớm: trả `fmt.Errorf("serve: %w", err)` ngay, không đi vào Shutdown |
| **Ch12** | Sub-card Phải: `<-ctx.Done()` | `fixed/server.go#L120` | Nhánh nhận tín hiệu dừng: mũi tên duy nhất chuyển tiếp sang Graceful Shutdown |
| **Ch12** | `srv.Shutdown(shutdownCtx); err != nil` | `fixed/server.go#L125-L127` | Lỗi Shutdown thoát ngay lập tức: `return fmt.Errorf("shutdown: %w", err)` |
| **Ch12** | `err := <-serveErr; errors.Is(..., ErrServerClosed)` | `fixed/server.go#L128-L131` | Chỉ khi Shutdown thành công mới nhận `serveErr`; cả hai thỏa mãn mới trả `nil` |
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
| **Khoảng đệm an toàn bounding box** | Khoảng đệm từ bounding box chữ thực tế đến viền $\ge 4.0\text{ pt}$ | Baseline cách viền đáy $\ge 6.0\text{ pt}$; khoảng đệm thực tế sau descenders $\ge 4.05\text{ pt}$ | **PASS (100%)** |
| **Tràn viền Canvas** | 0 text overflow trên mọi canvas | 0 string overflow trên cả 3 sơ đồ | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests passed (0.301s) | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn (Usable width: 448.22 pt) | **PASS (100%)** |

---

## 5. Danh mục Tệp Bàn giao

1. [MASTER PROMPT.txt](file:///d:/Golang/MASTER%20PROMPT.txt) (Chuẩn hóa định nghĩa DPI raster artifact và khoảng đệm bounding box trong Principle 8)
2. [assets/diagrams/http-service-lifecycle.png](file:///d:/Golang/assets/diagrams/http-service-lifecycle.png) (Hình 24, Chương 12: Stage 4 làm rõ Shutdown error return ngay lập tức, chỉ nhận `serveErr` khi Shutdown thành công)
3. [assets/diagrams/transaction-boundary.png](file:///d:/Golang/assets/diagrams/transaction-boundary.png) (Hình 25, Chương 13: Đã nghiệm thu, giữ nguyên 100%)
4. [assets/diagrams/incident-command-lifecycle.png](file:///d:/Golang/assets/diagrams/incident-command-lifecycle.png) (Hình 26, Chương 15: Đã nghiệm thu, giữ nguyên 100%)
5. [scripts/ch12_15_vector_diagrams.py](file:///d:/Golang/scripts/ch12_15_vector_diagrams.py) (Generator vector hoàn thiện)
6. [scripts/build_ch12_15_preview.py](file:///d:/Golang/scripts/build_ch12_15_preview.py) (Script build preview và specimen)
7. [book/design/agent2-ch12-15/ch12_15_preview.pdf](file:///d:/Golang/book/design/agent2-ch12-15/ch12_15_preview.pdf) (Preview PDF 3 trang 1:1)
8. [book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png](file:///d:/Golang/book/design/agent2-ch12-15/specimens/ch12_diagrams_p01.png) (Specimen Trang 1: Chương 12)
9. [book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png](file:///d:/Golang/book/design/agent2-ch12-15/specimens/ch12_diagrams_p02.png) (Specimen Trang 2: Chương 13)
10. [book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png](file:///d:/Golang/book/design/agent2-ch12-15/specimens/ch12_diagrams_p03.png) (Specimen Trang 3: Chương 15)
11. [book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md](file:///d:/Golang/book/design/agent2-ch12-15/REPORT_AGENT2_CH12_15.md) (Báo cáo kỹ thuật chi tiết)

---

## 6. Cổng Phê duyệt (Hard Approval Gate)

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**
> - Mọi yêu cầu nghiệm thu cuối cùng đã được đáp ứng chính xác 100%.
> - **KHÔNG MERGE:** Nhánh thiết kế được giữ riêng biệt trên `design/ch12-15-agent2-redesign`, không merge vào `main`.
> - **KHÔNG PUSH MAIN:** Chỉ push lên remote branch `design/ch12-15-agent2-redesign`.
> - **KHÔNG CHỈNH SỬA MASTER PDF:** `Golang_Master.pdf` được bảo vệ nguyên vẹn 100%.
> - Dừng tại trạng thái này để người dùng phê duyệt thủ công.
