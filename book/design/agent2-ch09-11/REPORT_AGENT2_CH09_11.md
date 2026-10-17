# BÁO CÁO THIẾT KẾ SƠ ĐỒ KỸ THUẬT ĐỢT 01: CHƯƠNG 09–11 (AGENT 2)
**Ngày thực hiện:** 17/10/2026  
**Nhánh công việc:** `design/ch09-11-agent2-redesign` (baseline: `3fbebef`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và reviewer kiểm tra độc lập trước khi phê duyệt tích hợp)

---

## 1. Tổng quan & Phạm vi công việc
Thực hiện thiết kế lại toàn diện theo chuẩn đồ họa kỹ thuật vector xuất bản cao cấp (Publication-Grade Vector Technical Graphics) cho đúng 3 sơ đồ thuộc Đợt 01 (Chương 09, 10, 11), tuân thủ nghiêm ngặt `MASTER PROMPT.txt` và các quy chuẩn đã được nghiệm thu tại các chương trước:
1. **Chương 09:** `assets/diagrams/channel-work-lifecycle.png` — Vòng đời và quyền sở hữu kênh trong Worker Pool (`labs/part9-workflow-pressure`).
2. **Chương 10:** `assets/diagrams/performance-evidence-path.png` — Chu trình điều tra hiệu năng và đường đi của bằng chứng định lượng (`labs/part10-measure-first`).
3. **Chương 11:** `assets/diagrams/http-client-request-path.png` — Các chặng của HTTP Client Request và cơ chế tái sử dụng kết nối (`labs/part11-request-path`).

**STRICT CONTENT LOCK:**
- Giữ nguyên tuyệt đối 100% văn bản Markdown trong `book/chapters/` (`git diff main -- book/chapters/` = 0).
- Không sửa code block, bảng biểu, caption, heading, typography hay các lab.
- Giữ nguyên tuyệt đối `Golang_Master.pdf` (chưa can thiệp vào Master PDF).

---

## 2. Chi tiết kỹ thuật & Đối chiếu mã nguồn thực tế

### 2.1. Chương 09 — `channel-work-lifecycle.png`
- **Vị trí xuất bản:** Trang 172, xref 384 trong `Golang_Master.pdf`.
- **Kích thước hình học:** `476.22 × 253.62 pt` (tỷ lệ 1.87768 : 1, khổ ngang banner).
- **Mã nguồn thực tế:** `labs/part9-workflow-pressure/fixed/pool.go`.
- **Mô hình tư duy (Mental Model):** Sơ đồ thể hiện quyền sở hữu (Channel Ownership) đối với thao tác gửi và đóng kênh; không mô tả dòng thời gian (scheduler timeline).
- **Các thành phần cốt lõi:**
  1. **Dispatcher Goroutine (Cột trái):**
     - Độc quyền khởi tạo kênh nhận việc: `in := make(chan Job)`.
     - Vòng lặp cấp phát: `for _, job := range jobs` với `select { case in <- job: case <-ctx.Done(): return }`.
     - Sở hữu việc đóng kênh: `defer close(in)` kích hoạt khi hết job hoặc hủy ngữ cảnh, phát tín hiệu cho các worker thoát vòng lặp.
  2. **Workers Pool (Cột giữa - N Goroutine chạy đồng thời):**
     - Nhận việc an toàn: `case job, ok := <-in: if !ok || ctx.Err() != nil { return }`.
     - Thực thi công việc: `result := Result{Job: job, Err: work(ctx, job)}` (ngắt ngay nếu context hủy).
     - Bàn giao kết quả có lối thoát: `select { case out <- result: case <-ctx.Done(): return }`, ngăn chặn tuyệt đối rò rỉ goroutine (leak) khi consumer dừng nhận sớm.
     - Đăng ký báo hoàn tất: `defer workersDone.Done()` khi goroutine worker thoát.
     - **Bất biến quyền sở hữu:** CẤM worker tự đóng `in` (vì là bên nhận) và CẤM worker tự đóng `out` (không worker nào biết mình có phải worker cuối cùng hay không).
  3. **Coordinator Goroutine (Góc trên bên phải):**
     - Chờ toàn bộ worker hoàn tất: `workersDone.Wait()`.
     - Độc quyền sở hữu việc đóng output: `close(out)` duy nhất một lần sau khi tất cả worker đã return sạch sẽ.
  4. **Consumer / Caller (Góc dưới bên phải):**
     - Rút cạn kết quả: `for res := range results`.
     - Tự động dừng vòng lặp khi `out` đóng và cạn đệm. Consumer không can thiệp vào vòng đời đóng kênh.

### 2.2. Chương 10 — `performance-evidence-path.png`
- **Vị trí xuất bản:** Trang 199, xref 439 trong `Golang_Master.pdf`.
- **Kích thước hình học:** `297.09 × 362.83 pt` (tỷ lệ 0.81879 : 1, khổ dọc portrait).
- **Mã nguồn thực tế:** `labs/part10-measure-first/fixed/render.go` & `render_test.go`.
- **Mô hình tư duy (Mental Model):** Chu trình điều tra hiệu năng hoàn chỉnh và khép kín dựa trên bằng chứng định lượng thực nghiệm (Evidence-Based Engineering Discipline).
- **5 chặng của chu trình thực nghiệm:**
  - **Giai đoạn 01 (Triệu chứng ban đầu):** Hệ thống chậm (latency / `ns/op` cao) hoặc phình bộ nhớ (`allocs/op`, `B/op` lớn). Triệu chứng là điểm bắt đầu, tuyệt đối không phải kết luận nguyên nhân.
  - **Giai đoạn 02 (Bài toán & Workload đại diện):** Xác định bài toán cụ thể và dựng workload đại diện (1.000 `Reading` từ `endpoint-0000` đến `endpoint-0999`). Tách riêng môi trường đo đạc, loại bỏ nhiễu side-effect.
  - **Giai đoạn 03 (Kiểm thử hợp đồng & Benchmark):** Cố định hợp đồng ngữ nghĩa qua unit test (`TestRenderPreservesWireFormat`), sau đó chạy benchmark (`BenchmarkRender` với `b.Loop()`, `-benchmem`, `-count=5`) để ghi nhận số liệu cơ sở (baseline).
  - **Giai đoạn 04 (Trích xuất bằng chứng định lượng):** Trích xuất các hồ sơ pprof chuyên biệt từ trace: `sync.pprof` (độ trễ khóa/channel), `sched.pprof` (độ trễ điều phối P/G), `syscall.pprof` (thời gian dừng I/O tầng nhân). Khoanh vùng chính xác điểm nóng CPU/Memory, không võ đoán từ tên API.
  - **Giai đoạn 05 (Tối ưu hóa phẫu thuật & Đo đạc đối chứng):** Thực hiện một can thiệp nhỏ có kiểm soát (`strings.Builder` thay thế toán tử `+=`). Đo đạc lại: Đối chứng số liệu trước/sau (26 µs vs 1.3 ms; 87 KB vs 10.4 MB; 917 allocs vs 1,900 allocs).
  - **Vòng lặp phản hồi (Feedback Loop):** Mũi tên đối chứng quay trở lại Giai đoạn 03 để kiểm tra hồi quy: Nếu mức cải thiện không bù đắp được độ phức tạp mã nguồn, kiên quyết giữ lại giải pháp đơn giản nhất.

### 2.3. Chương 11 — `http-client-request-path.png`
- **Vị trí xuất bản:** Trang 206, xref 454 trong `Golang_Master.pdf`.
- **Kích thước hình học:** `275.97 × 362.83 pt` (tỷ lệ 0.76059 : 1, khổ dọc portrait).
- **Mã nguồn thực tế:** `labs/part11-request-path/fixed/fetch.go`, `reuse_test.go`, `trace.go`.
- **Mô hình tư duy (Mental Model):** Request HTTP là chuỗi hợp đồng theo từng chặng; một chặng chỉ xuất hiện khi connection pool và policy khiến nó cần thiết.
- **Tiến trình xử lý và cấu trúc rẽ nhánh:**
  - **Chặng 1 (Khởi tạo Request):** `http.NewRequestWithContext(ctx, method, url, nil)` gắn context và deadline của caller, tích hợp `httptrace.ClientTrace`. Lệnh `client.Do(req)` khởi động chu trình.
  - **Rẽ nhánh Connection Pool (Fork):** Kiểm tra bộ đệm kết nối rảnh của `client.Transport`:
    * **Nhánh Tái sử dụng (Có - `GotConnInfo.Reused == true`):** Lấy kết nối rảnh sẵn có từ pool. Bỏ qua toàn bộ phân giải DNS, bỏ qua TCP Dial, bỏ qua TLS Handshake $\rightarrow$ Giảm độ trễ vượt trội và tiết kiệm tài nguyên mạng.
    * **Nhánh Kết nối mới (Không - `Reused == false`):** Phải tuần tự đi qua 3 chặng cơ sở:
      1. *2a. Phân giải DNS:* `DNSStart` $\rightarrow$ `DNSDone` qua `net.Resolver.LookupHost` để đổi tên miền thành địa chỉ IP. Lỗi DNS được phân loại đúng ở lớp resolution.
      2. *2b. Khởi tạo TCP Socket:* `ConnectStart` $\rightarrow$ `ConnectDone` qua `net.Dialer` mở kết nối TCP 3 chiều (TCP 3-way handshake).
      3. *2c. TLS Handshake (nếu URL là HTTPS):* `TLSHandshakeStart` $\rightarrow$ `TLSHandshakeDone` thương lượng mật mã và bắt buộc xác minh chứng chỉ và hostname (`tls.Config.ServerName == SAN`). Tuyệt đối không tắt `InsecureSkipVerify`.
  - **Hội tụ & Chặng 3 (Truyền nhận dữ liệu HTTP):** Gửi headers và payload (`WroteHeaders` $\rightarrow$ `WroteRequest`), server xử lý và phản hồi byte đầu tiên (`GotFirstResponseByte`).
  - **Chặng 4 (Đọc dữ liệu & Hoàn tất vòng đời):** Caller nhận `*http.Response`, đọc dữ liệu qua stream hoặc `io.ReadAll()`, kiểm tra HTTP status code (chuyển status ngoài 2xx thành `StatusError`).
  - **Hộp cam kết bắt buộc (Caller Obligation):** `defer resp.Body.Close()` là nghĩa vụ bắt buộc của caller để hoàn trả connection về pool `Transport` hoặc giải phóng socket. Quên đóng body gây rò rỉ kết nối (connection leak) và cạn kiệt file descriptors.

---

## 3. Kết quả kiểm định chất lượng xuất bản (QA Suite)

| Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Bảng màu thuần Grayscale** | $R = G = B$ trên mọi điểm ảnh, 0% sắc màu pha | `max|R-G| = 0, max|R-B| = 0` trên cả 3 PNG | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của Master PDF | Ch09: 476.22 × 253.62 pt<br>Ch10: 297.09 × 362.83 pt<br>Ch11: 275.97 × 362.83 pt | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ở mức 320 DPI | Ch09: 2117 × 1128 px<br>Ch10: 1321 × 1613 px<br>Ch11: 1227 × 1613 px | **PASS (100%)** |
| **Tiêu chuẩn Typography** | Mọi nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | 88/88 nhãn kiểm tra có `fontSize >= 6.0 pt` (nhỏ nhất: 6.0 pt, lớn nhất: 7.8 pt) | **PASS (100%)** |
| **Bố cục & Khả năng đọc** | Không chồng chữ, không tràn viền, khoảng đệm an toàn | Tất cả chuỗi code Go dài được bẻ dòng hợp lệ; căn lề đối xứng | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `Golang_Master.pdf` chưa bị sửa đổi trong giai đoạn thiết kế | 0 diff trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests pass in 0.309s | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn | **PASS (100%)** |

---

## 4. Danh mục tệp bàn giao trên branch `design/ch09-11-agent2-redesign`
1. `assets/diagrams/channel-work-lifecycle.png` (Hình vẽ vector xuất bản Chương 09, 320 DPI, thuần grayscale)
2. `assets/diagrams/performance-evidence-path.png` (Hình vẽ vector xuất bản Chương 10, 320 DPI, thuần grayscale)
3. `assets/diagrams/http-client-request-path.png` (Hình vẽ vector xuất bản Chương 11, 320 DPI, thuần grayscale)
4. `scripts/ch09_11_vector_diagrams.py` (Script ReportLab tạo lập toàn bộ vector graphic cho 3 sơ đồ)
5. `scripts/build_ch09_11_preview.py` (Script xây dựng PDF preview độc lập 3 trang)
6. `book/design/agent2-ch09-11/ch09_11_preview.pdf` (Tệp PDF preview độc lập gồm đúng 3 trang hiển thị 1:1)
7. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p01.png` (Ảnh specimen trang 1: Chương 09)
8. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p02.png` (Ảnh specimen trang 2: Chương 10)
9. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p03.png` (Ảnh specimen trang 3: Chương 11)
10. `book/design/agent2-ch09-11/REPORT_AGENT2_CH09_11.md` (Báo cáo kỹ thuật chi tiết này)

---

## 5. Hard Approval Gate
> [!IMPORTANT]
> Toàn bộ công việc thiết kế và kiểm thử cho Đợt 01 (Chương 09–11) đã hoàn tất và được cô lập hoàn toàn trên branch `design/ch09-11-agent2-redesign`.
> Theo quy tắc Hard Approval Gate của dự án:
> - **KHÔNG** merge vào `main`.
> - **KHÔNG** push trực tiếp vào `main`.
> - **KHÔNG** chỉnh sửa `Golang_Master.pdf`.
> - Dừng tại `AWAITING_MANUAL_APPROVAL` để người dùng và ChatGPT tiến hành review độc lập trước khi phê duyệt tích hợp.
