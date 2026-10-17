# BÁO CÁO HIỆU CHỈNH KỸ THUẬT SƠ ĐỒ ĐỢT 01: CHƯƠNG 09–11 (AGENT 2 — ROUND 3/3 FINAL REVIEW)
**Ngày thực hiện:** 17/10/2026  
**Nhánh công việc:** `design/ch09-11-agent2-redesign` (baseline: `d655341`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và reviewer kiểm tra độc lập trước khi phê duyệt tích hợp)

---

## 1. Mục tiêu hiệu chỉnh kỹ thuật vòng cuối (Round 3/3 Final Review)
1. **STRICT CONTENT LOCK:**
   - Giữ nguyên tuyệt đối 100% văn bản Markdown trong `book/chapters/` (`git diff main -- book/chapters/` = 0).
   - Chỉ sửa sơ đồ Chương 9 và Chương 11; giữ nguyên sơ đồ Chương 10 đã đạt chuẩn.
   - Không sửa code block, bảng biểu, caption, heading, typography bài giảng, các lab hoặc `Golang_Master.pdf`.
2. **Chương 09 — Chuẩn hóa quyền sở hữu kênh (Channel Ownership):**
   - Sửa câu “Chỉ sender mới được đóng kênh” thành: *"Chỉ đóng kênh khi bảo đảm không còn sender nào hoạt động"*. Coordinator không gửi dữ liệu vào `out` nhưng sở hữu quyền đóng `out` an toàn sau khi toàn bộ worker đã thoát (`workersDone.Wait()`).
   - Phân biệt rõ hàm `Run()` trong `fixed/pool.go` là nơi khởi tạo cả hai channel `in` và `out`, trong khi Dispatcher goroutine là bên độc quyền gửi việc và đóng `in` (`defer close(in)`).
3. **Chương 09 — Ngữ nghĩa hủy bỏ (Cancellation Semantics):**
   - Không đưa ra cam kết tuyệt đối rằng không có kết quả nào được gửi sau khi context bị hủy.
   - Làm rõ: Worker kiểm tra `ctx.Err() != nil` trước khi gửi để giảm tối đa bàn giao dư thừa; tuy nhiên trong câu lệnh `select`, nếu cả nhánh `out <- result` và `<-ctx.Done()` đều ready đồng thời, Go runtime sẽ chọn nhánh thực thi hoàn toàn ngẫu nhiên (pseudo-random).
4. **Chương 11 — Gắn context mới vào Request (HTTP Trace Context Binding):**
   - Bổ sung chính xác bước tái gán context: `traceCtx := httptrace.WithClientTrace(req.Context(), trace)` và `req = req.WithContext(traceCtx)`.
   - Làm rõ tính bắt buộc của bước này: Nếu không gọi `req.WithContext(traceCtx)`, các hook của `httptrace` sẽ không bao giờ được kích hoạt trong `client.Do(req)`.
   - Giữ nguyên toàn bộ các chi tiết đã đạt: `GotFirstResponseByte`, `Reused` vs `WasIdle`, các chặng có điều kiện DNS/TCP/TLS, xác minh chứng chỉ CA & DNS/IP SAN, quyền sở hữu Body và `StatusError`.

---

## 2. Đối chiếu chi tiết với mã nguồn và bài giảng thực tế

### 2.1. Chương 09: `channel-work-lifecycle.png`
- **Kích thước:** `476.22 × 253.62 pt` (Trang 172, xref 384 trong `Golang_Master.pdf`).
- **Mã nguồn lab:** `labs/part9-workflow-pressure/fixed/pool.go`.
- **Cấu trúc quyền sở hữu và khởi tạo channel:**
  * `Run()`: Khởi tạo `in := make(chan Job)` và `out := make(chan Result)`.
  * Dispatcher Header & Box 1: `DISPATCHER [Độc quyền gửi in]` — `Run() tạo in; Dispatcher gửi & đóng`.
  * Dispatcher Box 2: `[Trích đoạn logic // Cấp phát]` với vòng lặp `for/select` đầy đủ cặp ngoặc `{}`.
  * Dispatcher Box 3: `defer close(in)` (đăng ký lúc spawn, thực thi khi return, báo worker thoát lặp).
  * Worker Row 2: `[Trích đoạn logic // Thực thi]` — `Kiểm tra ctx.Err() trước gửi; giảm tối đa bàn giao dư thừa`.
  * Worker Row 3: `[Trích đoạn logic // Bàn giao]` — `} // Nếu out và Done cùng ready, Go chọn ngẫu nhiên`.
  * Coordinator Header: `COORDINATOR [Sở hữu đóng out]` — `workersDone.Wait()` chờ $N$ worker gọi `Done()`, sau đó `close(out) // DUY NHẤT 1 LẦN`.
  * Consumer Header: `CONSUMER (CALLER) [Nhận out]` — `for res := range results { ... }`, dừng khi `out` đóng và cạn đệm.
  * Băng footer: `BẤT BIẾN KỸ THUẬT: Chỉ đóng kênh khi bảo đảm không còn sender nào hoạt động. Dispatcher đóng in; Coordinator đóng out sau WaitGroup.`

### 2.2. Chương 10: `performance-evidence-path.png`
- **Kích thước:** `297.09 × 362.83 pt` (Trang 199, xref 439 trong `Golang_Master.pdf`).
- **Trạng thái:** Giữ nguyên 100% thiết kế Round 1 đã duyệt (đồng bộ `-count=6`, 3 lệnh trích xuất riêng biệt `sync`, `sched`, `syscall` từ `trace.out`, và ghi chú đối chứng thử nghiệm cụ thể).

### 2.3. Chương 11: `http-client-request-path.png`
- **Kích thước:** `275.97 × 362.83 pt` (Trang 206, xref 454 trong `Golang_Master.pdf`).
- **Mã nguồn lab & bài giảng:** `labs/part11-request-path/fixed/fetch.go`, `reuse_test.go`, `trace.go`.
- **Khởi tạo và gắn Trace Hook (Card 1):**
  ```go
  req, _ := http.NewRequestWithContext(ctx, method, url, nil) // Ràng buộc deadline
  traceCtx := httptrace.WithClientTrace(req.Context(), trace)   // Tạo trace context
  req = req.WithContext(traceCtx) // BẮT BUỘC gán lại vào request để kích hoạt hook
  ```
- **Hệ thống chặng có điều kiện & Hợp đồng Body:**
  * Giữ nguyên `GotFirstResponseByte: Nhận byte đầu tiên của response headers`.
  * Giữ nguyên phân nhánh Reused (`GotConnInfo.Reused == true`) vs WasIdle (`WasIdle == true`).
  * Giữ nguyên các chặng có điều kiện (DNS, TCP, TLS) và 4 dòng xác minh chuỗi CA & DNS/IP SAN không tràn viền.
  * Giữ nguyên hợp đồng `resp.Body.Close()` và chính sách `StatusError` của lab `Fetch`.

---

## 3. Kết quả kiểm định chất lượng xuất bản (QA Suite)

| Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Bảng màu thuần Grayscale** | $R = G = B$ trên mọi điểm ảnh, 0% sắc màu pha | `max|R-G| = 0, max|R-B| = 0` trên cả 3 PNG | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của Master PDF | Ch09: 476.22 × 253.62 pt<br>Ch10: 297.09 × 362.83 pt<br>Ch11: 275.97 × 362.83 pt | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ở mức 320 DPI | Ch09: 2117 × 1128 px<br>Ch10: 1321 × 1613 px<br>Ch11: 1227 × 1613 px | **PASS (100%)** |
| **Tiêu chuẩn Typography** | Mọi nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | 119/119 nhãn kiểm tra có `fontSize >= 6.0 pt` (nhỏ nhất: 6.0 pt, lớn nhất: 7.8 pt) | **PASS (100%)** |
| **Độ rộng dòng & Khoảng đệm** | Không tràn khung, khoảng đệm an toàn $\ge 3.5\text{ pt}$ | Mọi nhãn đều nằm trong giới hạn; Card 1 Ch11 đệm $\ge 35.76\text{ pt}$ | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `Golang_Master.pdf` chưa bị sửa đổi trong giai đoạn thiết kế | 0 diff trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests pass in 0.348s | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn | **PASS (100%)** |

---

## 4. Danh mục tệp cập nhật trên branch `design/ch09-11-agent2-redesign`
1. `assets/diagrams/channel-work-lifecycle.png` (Hình vẽ vector Chương 09, 320 DPI, thuần grayscale, chuẩn hóa ownership & select ngẫu nhiên)
2. `assets/diagrams/performance-evidence-path.png` (Hình vẽ vector Chương 10, 320 DPI, thuần grayscale, giữ nguyên Round 1)
3. `assets/diagrams/http-client-request-path.png` (Hình vẽ vector Chương 11, 320 DPI, thuần grayscale, bổ sung bước req.WithContext)
4. `scripts/ch09_11_vector_diagrams.py` (Script ReportLab cập nhật toàn bộ hiệu chỉnh kỹ thuật Round 3/3)
5. `book/design/agent2-ch09-11/ch09_11_preview.pdf` (Tệp PDF preview độc lập 3 trang hiển thị 1:1)
6. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p01.png` (Ảnh specimen trang 1: Chương 09)
7. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p02.png` (Ảnh specimen trang 2: Chương 10)
8. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p03.png` (Ảnh specimen trang 3: Chương 11)
9. `book/design/agent2-ch09-11/REPORT_AGENT2_CH09_11.md` (Báo cáo hiệu chỉnh kỹ thuật này)

---

## 5. Round Limit & Hard Approval Gate
> [!IMPORTANT]
> Đây là **vòng sửa 3/3 (vòng cuối cùng)** của đợt thiết kế sơ đồ Chương 09–11.
> Toàn bộ các yêu cầu kỹ thuật đã được hoàn thành, nghiệm thu và cô lập trên branch `design/ch09-11-agent2-redesign`.
> Theo quy tắc Hard Approval Gate và Round Limit:
> - **DỪNG HOÀN TOÀN:** Không tự triển khai vòng thứ tư hoặc chuyển sang chương khác.
> - **KHÔNG MERGE:** Không merge hoặc push trực tiếp vào `main`.
> - **KHÔNG SỬA MASTER PDF:** `Golang_Master.pdf` được bảo toàn nguyên vẹn.
> - Dừng tại **`AWAITING_MANUAL_APPROVAL`** để ChatGPT review và người dùng phê duyệt thủ công.

