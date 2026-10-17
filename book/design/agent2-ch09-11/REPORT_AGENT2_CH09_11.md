# BÁO CÁO HIỆU CHỈNH KỸ THUẬT SƠ ĐỒ ĐỢT 01: CHƯƠNG 09–11 (AGENT 2 — ROUND 2/3 FINAL MICRO-FIX)
**Ngày thực hiện:** 17/10/2026  
**Nhánh công việc:** `design/ch09-11-agent2-redesign` (baseline: `b59b4a1`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và reviewer kiểm tra độc lập trước khi phê duyệt tích hợp)

---

## 1. Mục tiêu hiệu chỉnh kỹ thuật vi mô (Round 2/3 Technical Micro-Fixes)
1. **STRICT CONTENT LOCK:**
   - Giữ nguyên tuyệt đối 100% văn bản Markdown trong `book/chapters/` (`git diff main -- book/chapters/` = 0).
   - Không sửa code block, bảng biểu, caption, heading, typography bài giảng, các lab hoặc `Golang_Master.pdf`.
2. **Chương 09 — Hoàn thiện dấu ngoặc `}` của vòng lặp & Gắn nhãn `Trích đoạn logic`:**
   - Bổ sung dấu `}` đóng vòng `for` trong Dispatcher Box 2, bảo đảm cấu trúc lặp Go có cặp ngoặc mở `{` và đóng `}` hoàn chỉnh, hợp lệ.
   - Gắn nhãn định danh tường minh `[Trích đoạn logic // Cấp phát]`, `[Trích đoạn logic // Nhận việc]`, `[Trích đoạn logic // Thực thi]`, `[Trích đoạn logic // Bàn giao]`, `[Trích đoạn logic // Tiếp nhận]` cho tất cả các khối code rút gọn, ngăn ngừa mã rút gọn bị hiểu nhầm là chương trình Go độc lập.
3. **Chương 10 — Bảo toàn kết quả Round 1 đã duyệt:**
   - Giữ nguyên 100% các nội dung đã đạt chuẩn: đồng bộ cờ `-count=6`, ba lệnh trích xuất trace pprof độc lập (`sync.pprof`, `sched.pprof`, `syscall.pprof`) và ghi chú tính đại diện thử nghiệm của số liệu đo đạc; không tái thiết kế sơ đồ.
4. **Chương 11 — Chuẩn hóa ngữ nghĩa `GotFirstResponseByte` & Hợp đồng xác minh TLS:**
   - Hiệu chỉnh mô tả sự kiện `GotFirstResponseByte`: Là thời điểm client nhận byte đầu tiên của response headers (`net/http/httptrace`), không đồng nhất với việc server đã hoàn tất toàn bộ quá trình xử lý.
   - Thay thế cú pháp rút gọn `ServerName == SAN` bằng diễn đạt chính xác theo hợp đồng TLS (`crypto/tls`, RFC 6125, RFC 5280): Xác minh chuỗi chứng chỉ CA tin cậy, đối soát hostname khớp với DNS SAN hoặc IP SAN thích hợp, và cấm tắt xác thực (`InsecureSkipVerify: false`).
   - Rà soát toàn bộ các nhãn trong khung nhánh phải 147,97 pt bằng `pdfmetrics.stringWidth` với font thực tế (`BookSans`, `BookSansBold`, `BookMono`); hiệu chỉnh các dòng chữ để có khoảng đệm an toàn $\ge 15.87\text{ pt}$, tuyệt đối không tràn viền và giữ font size $\ge 6.0\text{ pt}$.
   - Bảo toàn các cam kết đã duyệt: phân biệt `Reused` vs `WasIdle`, trách nhiệm đóng `resp.Body.Close()` của caller, và chính sách `StatusError` của hàm `Fetch` trong lab.

---

## 2. Đối chiếu chi tiết với mã nguồn và bài giảng thực tế

### 2.1. Chương 09: `channel-work-lifecycle.png`
- **Kích thước:** `476.22 × 253.62 pt` (Trang 172, xref 384 trong `Golang_Master.pdf`).
- **Mã nguồn lab:** `labs/part9-workflow-pressure/fixed/pool.go`.
- **Dispatcher Box 2:** Cú pháp Go chuẩn hóa với đầy đủ dấu đóng ngoặc `}`:
  ```go
  // [Trích đoạn logic // Cấp phát]
  for _, job := range jobs {
    select {
    case in <- job:
    case <-ctx.Done():
      return
    }
  }
  ```
- **Hệ thống nhãn trích đoạn logic:**
  * Box 1: `in := make(chan Job)` (Kênh nhận việc unbuffered).
  * Box 2: `[Trích đoạn logic // Cấp phát]` kèm vòng lặp kiểm tra hủy ngữ cảnh đầy đủ 2 cặp ngoặc `{}`.
  * Box 3: `defer close(in)` (Đăng ký lúc spawn goroutine; thực thi lúc return; báo worker thoát lặp).
  * Worker Row 1: `[Trích đoạn logic // Nhận việc]` (`case job, ok := <-in:`, thoát sạch khi `!ok` hoặc `ctx.Err() != nil`).
  * Worker Row 2: `[Trích đoạn logic // Thực thi]` (`result := Result{Job: job, Err: work(ctx, job)}`, hủy bàn giao nếu `ctx.Err() != nil`).
  * Worker Row 3: `[Trích đoạn logic // Bàn giao]` (`select { case out <- result: case <-ctx.Done(): return }`).
  * Coordinator: `workersDone.Wait()` chờ $N$ worker gọi `Done()`; `close(out) // DUY NHẤT 1 LẦN`.
  * Consumer: `[Trích đoạn logic // Tiếp nhận]` (`for res := range results { ... }`, dừng khi `out` đóng và cạn đệm).

### 2.2. Chương 10: `performance-evidence-path.png`
- **Kích thước:** `297.09 × 362.83 pt` (Trang 199, xref 439 trong `Golang_Master.pdf`).
- **Trạng thái:** Giữ nguyên 100% thiết kế Round 1 đã được thẩm tra đạt chuẩn:
  * Chặng 03: `BenchmarkRender` (-benchmem -count=6 cố định đối chứng).
  * Chặng 04: 3 lệnh riêng biệt `sync.pprof`, `sched.pprof`, `syscall.pprof`.
  * Chặng 05: Bằng chứng đo đạc đối chứng `baseline (+=)` vs `fixed (Builder)`, kèm lưu ý số liệu chỉ mang tính đại diện cho fixture kiểm thử.

### 2.3. Chương 11: `http-client-request-path.png`
- **Kích thước:** `275.97 × 362.83 pt` (Trang 206, xref 454 trong `Golang_Master.pdf`).
- **Mã nguồn lab & bài giảng:** `labs/part11-request-path/fixed/fetch.go`, `reuse_test.go`, `trace.go`.
- **Hiệu chỉnh ngữ nghĩa vi mô:**
  * *Chặng 3:* Cập nhật nhãn `GotFirstResponseByte: Nhận byte đầu tiên của response headers` (đúng chuẩn `net/http/httptrace.ClientTrace.GotFirstResponseByte`).
  * *Chặng 2c (TLS Handshake):* Phân tách 4 dòng rõ ràng:
    - Tiêu đề: `2c. TLS Handshake (chỉ khi scheme là HTTPS)`
    - Dòng 1: `TLSHandshakeStart/Done: Bỏ qua nếu là HTTP`
    - Dòng 2: `Xác minh chuỗi CA & hostname khớp DNS/IP SAN`
    - Dòng 3: `Bắt buộc xác thực chứng chỉ; cấm tắt verify`
  * *Kiểm tra độ rộng (Khung 147,97 pt, chiều rộng khả dụng 137,97 pt):*
    - Nhãn DNS 2a: `118.42 pt` (khoảng đệm an toàn `19.55 pt`).
    - Nhãn TCP 2b: `116.66 pt` (khoảng đệm an toàn `21.31 pt`).
    - Nhãn TLS 2c (dòng dài nhất): `122.10 pt` (khoảng đệm an toàn `15.87 pt`).
    - 100% các dòng đều $\le 122.10\text{ pt}$, loại bỏ hoàn toàn nguy cơ tràn lề in ấn.

---

## 3. Kết quả kiểm định chất lượng xuất bản (QA Suite)

| Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Bảng màu thuần Grayscale** | $R = G = B$ trên mọi điểm ảnh, 0% sắc màu pha | `max|R-G| = 0, max|R-B| = 0` trên cả 3 PNG | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của Master PDF | Ch09: 476.22 × 253.62 pt<br>Ch10: 297.09 × 362.83 pt<br>Ch11: 275.97 × 362.83 pt | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ở mức 320 DPI | Ch09: 2117 × 1128 px<br>Ch10: 1321 × 1613 px<br>Ch11: 1227 × 1613 px | **PASS (100%)** |
| **Tiêu chuẩn Typography** | Mọi nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | 118/118 nhãn kiểm tra có `fontSize >= 6.0 pt` (nhỏ nhất: 6.0 pt, lớn nhất: 7.8 pt) | **PASS (100%)** |
| **Bố cục & Độ rộng dòng** | Không tràn khung 147,97 pt, khoảng đệm $\ge 10\text{ pt}$ | Dòng dài nhất trong nhánh phải: 122.10 pt (đệm 15.87 pt) | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `Golang_Master.pdf` chưa bị sửa đổi trong giai đoạn thiết kế | 0 diff trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests pass in 0.271s | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn | **PASS (100%)** |

---

## 4. Danh mục tệp cập nhật trên branch `design/ch09-11-agent2-redesign`
1. `assets/diagrams/channel-work-lifecycle.png` (Hình vẽ vector Chương 09, 320 DPI, thuần grayscale, đóng ngoặc Go & nhãn trích đoạn)
2. `assets/diagrams/performance-evidence-path.png` (Hình vẽ vector Chương 10, 320 DPI, thuần grayscale, giữ nguyên Round 1)
3. `assets/diagrams/http-client-request-path.png` (Hình vẽ vector Chương 11, 320 DPI, thuần grayscale, chuẩn hóa GotFirstResponseByte & TLS SAN)
4. `scripts/ch09_11_vector_diagrams.py` (Script ReportLab cập nhật toàn bộ hiệu chỉnh kỹ thuật Round 2)
5. `book/design/agent2-ch09-11/ch09_11_preview.pdf` (Tệp PDF preview độc lập 3 trang hiển thị 1:1)
6. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p01.png` (Ảnh specimen trang 1: Chương 09)
7. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p02.png` (Ảnh specimen trang 2: Chương 10)
8. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p03.png` (Ảnh specimen trang 3: Chương 11)
9. `book/design/agent2-ch09-11/REPORT_AGENT2_CH09_11.md` (Báo cáo hiệu chỉnh kỹ thuật này)

---

## 5. Hard Approval Gate
> [!IMPORTANT]
> Toàn bộ các hiệu chỉnh kỹ thuật vi mô Đợt 01 (Chương 09–11) đã được hoàn tất và cô lập trên branch `design/ch09-11-agent2-redesign`.
> Theo quy tắc Hard Approval Gate của dự án:
> - **KHÔNG** merge vào `main`.
> - **KHÔNG** push trực tiếp vào `main`.
> - **KHÔNG** chỉnh sửa `Golang_Master.pdf`.
> - Dừng tại `AWAITING_MANUAL_APPROVAL` để người dùng và ChatGPT tiến hành review độc lập trước khi phê duyệt tích hợp.

