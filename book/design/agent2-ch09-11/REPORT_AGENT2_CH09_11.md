# BÁO CÁO HIỆU CHỈNH KỸ THUẬT SƠ ĐỒ ĐỢT 01: CHƯƠNG 09–11 (AGENT 2 — ROUND 1/3)
**Ngày thực hiện:** 17/10/2026  
**Nhánh công việc:** `design/ch09-11-agent2-redesign` (baseline: `a95f958`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và reviewer kiểm tra độc lập trước khi phê duyệt tích hợp)

---

## 1. Mục tiêu hiệu chỉnh kỹ thuật (Round 1/3 Technical Corrections)
1. **STRICT CONTENT LOCK:**
   - Giữ nguyên tuyệt đối 100% văn bản Markdown trong `book/chapters/` (`git diff main -- book/chapters/` = 0).
   - Không sửa code block, bảng biểu, caption, heading, typography, các lab hoặc `Golang_Master.pdf`.
2. **Chương 09 — Chuẩn hóa cú pháp Go & Thời điểm của defer:**
   - Hoàn thiện đầy đủ cặp ngoặc `{}` hợp lệ cho mọi khối lệnh Go trong Dispatcher và Workers; loại bỏ hoàn toàn các trích đoạn cụt gây hiểu nhầm cú pháp.
   - Làm rõ sự khác biệt giữa **thời điểm đăng ký** `defer close(in)` (ngay khi dispatcher goroutine khởi chạy) và **thời điểm thực thi** `close(in)` (chỉ khi dispatcher return do hết job hoặc do `ctx.Done()`).
   - Giữ nguyên mô hình quyền sở hữu (Channel Ownership): Dispatcher sở hữu `in`; Coordinator sở hữu `out` sau `workersDone.Wait()`; Workers tuyệt đối không đóng kênh.
3. **Chương 10 — Cú pháp pprof, đồng bộ `-count=6` & tính đại diện số liệu:**
   - Sửa cú pháp `go tool trace -pprof=...`: Phân tách rành mạch thành 3 lệnh trích xuất độc lập theo đúng source Chương 10 (`sync.pprof`, `sched.pprof`, `syscall.pprof`).
   - Đồng bộ lệnh benchmark với bài giảng: Sử dụng cờ `-count=6` (chạy 6 lần đo trên cùng máy i5-12500H, Windows/amd64, Go 1.27.1), không dùng `-count=5` của exercise.
   - Ghi chú tường minh: Các số liệu benchmark chỉ là bằng chứng đo đạc của workload/môi trường cụ thể trong bài giảng, không phải cam kết hiệu năng phổ quát.
4. **Chương 11 — Phân biệt Reused vs WasIdle, các chặng có điều kiện & Hợp đồng Body:**
   - Phân biệt rõ `GotConnInfo.Reused` (kết nối đã qua sử dụng) và `GotConnInfo.WasIdle` (kết nối được lấy ra từ idle connection pool của `Transport`); không đồng nhất connection reuse với idle pool.
   - Thể hiện nhánh kết nối mới dưới dạng các chặng có điều kiện (conditional stages): DNS (chỉ khi host là tên miền), TCP Dial (chỉ khi cần mở socket mới), TLS Handshake (chỉ khi scheme là HTTPS; xác minh `ServerName == SAN`).
   - Làm rõ hợp đồng Response Body: Đọc đến EOF và gọi `defer resp.Body.Close()` hỗ trợ tạo điều kiện reuse persistent connection, nhưng **không bảo đảm chắc chắn** request sau sẽ reuse. Trách nhiệm bắt buộc của caller là quản lý và đóng Body đúng ownership để tránh leak socket.
   - Phân biệt rõ `http.NewRequestWithContext` (ràng buộc context/deadline) với `httptrace.WithClientTrace` (gắn hook quan sát). Đánh dấu `StatusError` là chính sách của hàm `Fetch` trong lab, không phải mặc định của thư viện chuẩn `net/http`.

---

## 2. Đối chiếu chi tiết với mã nguồn và bài giảng thực tế

### 2.1. Chương 09: `channel-work-lifecycle.png`
- **Kích thước:** `476.22 × 253.62 pt` (Trang 172, xref 384 trong `Golang_Master.pdf`).
- **Mã nguồn lab:** `labs/part9-workflow-pressure/fixed/pool.go`.
- **Cấu trúc thực thi của Dispatcher:**
  ```go
  go func() {
      defer close(in)
      for _, job := range jobs {
          select {
          case in <- job:
          case <-ctx.Done():
              return
          }
      }
  }()
  ```
- **Thể hiện trực quan trên sơ đồ:**
  * Box 1: `in := make(chan Job)` (Kênh nhận việc unbuffered).
  * Box 2: Khối lặp cấp phát công việc với đầy đủ cú pháp `{}`:
    ```go
    for _, job := range jobs {
      select {
      case in <- job:
      case <-ctx.Done():
        return
      }
    }
    ```
  * Box 3: `defer close(in)`:
    - *Đăng ký:* ngay khi dispatcher goroutine khởi chạy.
    - *Thực thi:* khi dispatcher return (do duyệt hết jobs hoặc ngữ cảnh `ctx.Done()`).
    - *Tác dụng:* phát tín hiệu đóng kênh an toàn để các worker thoát vòng lặp.
- **Workers Pool & Coordinator:**
  * Worker: Đăng ký `defer workersDone.Done()` lúc spawn; thoát sạch khi `!ok` hoặc `ctx.Err() != nil`; bàn giao `out <- result` qua `select` kèm `case <-ctx.Done(): return`.
  * Coordinator: `workersDone.Wait()` chờ toàn bộ $N$ worker hoàn tất, sau đó thực hiện `close(out)` **duy nhất một lần**.

### 2.2. Chương 10: `performance-evidence-path.png`
- **Kích thước:** `297.09 × 362.83 pt` (Trang 199, xref 439 trong `Golang_Master.pdf`).
- **Mã nguồn lab & bài giảng:** `labs/part10-measure-first/fixed/render.go`, `render_test.go` và `10-khi-chuong-trinh-cham-hoac-phinh.md`.
- **Đồng bộ lệnh và bằng chứng thực nghiệm:**
  * *Chặng 03 (Hợp đồng & Benchmark):* `BenchmarkRender (b.Loop, -benchmem -count=6)`. Cố định 6 lần chạy có đối chứng.
  * *Chặng 04 (Trích xuất 3 hồ sơ riêng biệt):*
    ```powershell
    go tool trace -pprof=sync trace.out > sync.pprof   # độ trễ khóa / channel (sync.(*WaitGroup).Wait)
    go tool trace -pprof=sched trace.out > sched.pprof # độ trễ điều phối P/G
    go tool trace -pprof=syscall trace.out > syscall.pprof # thời gian dừng ở tầng nhân (ghi file)
    ```
  * *Chặng 05 (Tối ưu hóa & Đối chứng số liệu):*
    - So sánh trực tiếp: `baseline (+=)` (1.306–3.394 ms/op; ~10.4 MB/op; 1.900 allocs/op) vs `fixed (Builder)` (26.442–89.994 µs/op; ~87.6 KB/op; 917 allocs/op).
    - Cảnh báo: Số liệu phản ánh đúng fixture thử nghiệm (workload 1.000 Reading, máy i5-12500H, Go 1.27.1), không đại diện cho latency service production hay cam kết hiệu năng phổ quát.

### 2.3. Chương 11: `http-client-request-path.png`
- **Kích thước:** `275.97 × 362.83 pt` (Trang 206, xref 454 trong `Golang_Master.pdf`).
- **Mã nguồn lab & bài giảng:** `labs/part11-request-path/fixed/fetch.go`, `reuse_test.go`, `trace.go`.
- **Đặc tả chi tiết các chặng:**
  * *Chặng 1:* Tách bạch `http.NewRequestWithContext` (ràng buộc context caller) với `httptrace.WithClientTrace` (gắn hook ghi nhận event).
  * *Rẽ nhánh Connection Reuse:*
    - `GotConnInfo.Reused == true`: Kết nối đã qua sử dụng.
    - `GotConnInfo.WasIdle == true`: Được lấy từ idle connection pool của `Transport`.
    - Phân biệt rõ: Tái sử dụng kết nối (Reused) không đồng nhất với việc lấy từ idle pool (WasIdle).
  * *Các chặng có điều kiện (Conditional Stages):*
    - `2a. Phân giải DNS`: Chỉ xuất hiện khi host là tên miền; bỏ qua khi là IP hoặc loopback.
    - `2b. Khởi tạo TCP Socket`: Chỉ xuất hiện khi cần mở socket mạng mới.
    - `2c. TLS Handshake`: Chỉ xuất hiện khi scheme là HTTPS. Bắt buộc xác minh hostname (`ServerName == SAN`). Bỏ qua nếu là HTTP thường.
  * *Chặng 4 & Phản hồi:* Đánh dấu rõ việc chuyển status code ngoài 2xx thành `StatusError` là chính sách của hàm `Fetch` trong lab; thư viện chuẩn `net/http` mặc định không coi mã 4xx/5xx là lỗi của lệnh gọi mạng.
  * *Hộp cam kết Body:* `defer resp.Body.Close()` là trách nhiệm bắt buộc của caller để giải phóng socket và tránh rò rỉ kết nối; việc đọc đến EOF hỗ trợ tạo điều kiện reuse nhưng không bảo đảm chắc chắn request sau sẽ reuse.

---

## 3. Kết quả kiểm định chất lượng xuất bản (QA Suite)

| Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Bảng màu thuần Grayscale** | $R = G = B$ trên mọi điểm ảnh, 0% sắc màu pha | `max|R-G| = 0, max|R-B| = 0` trên cả 3 PNG | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của Master PDF | Ch09: 476.22 × 253.62 pt<br>Ch10: 297.09 × 362.83 pt<br>Ch11: 275.97 × 362.83 pt | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ở mức 320 DPI | Ch09: 2117 × 1128 px<br>Ch10: 1321 × 1613 px<br>Ch11: 1227 × 1613 px | **PASS (100%)** |
| **Tiêu chuẩn Typography** | Mọi nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | 111/111 nhãn kiểm tra có `fontSize >= 6.0 pt` (nhỏ nhất: 6.0 pt, lớn nhất: 7.8 pt) | **PASS (100%)** |
| **Bố cục & Khả năng đọc** | Không chồng chữ, không tràn viền, khoảng đệm an toàn | Đã bẻ dòng mã Go hợp lệ; sửa font Box 2c; căn lề đối xứng | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `Golang_Master.pdf` chưa bị sửa đổi trong giai đoạn thiết kế | 0 diff trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests pass in 0.274s | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn | **PASS (100%)** |

---

## 4. Danh mục tệp cập nhật trên branch `design/ch09-11-agent2-redesign`
1. `assets/diagrams/channel-work-lifecycle.png` (Hình vẽ vector Chương 09, 320 DPI, thuần grayscale)
2. `assets/diagrams/performance-evidence-path.png` (Hình vẽ vector Chương 10, 320 DPI, thuần grayscale)
3. `assets/diagrams/http-client-request-path.png` (Hình vẽ vector Chương 11, 320 DPI, thuần grayscale)
4. `scripts/ch09_11_vector_diagrams.py` (Script ReportLab cập nhật toàn bộ hiệu chỉnh kỹ thuật Round 1)
5. `book/design/agent2-ch09-11/ch09_11_preview.pdf` (Tệp PDF preview độc lập 3 trang hiển thị 1:1)
6. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p01.png` (Ảnh specimen trang 1: Chương 09)
7. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p02.png` (Ảnh specimen trang 2: Chương 10)
8. `book/design/agent2-ch09-11/specimens/ch09_diagrams_p03.png` (Ảnh specimen trang 3: Chương 11)
9. `book/design/agent2-ch09-11/REPORT_AGENT2_CH09_11.md` (Báo cáo hiệu chỉnh kỹ thuật này)

---

## 5. Hard Approval Gate
> [!IMPORTANT]
> Toàn bộ các hiệu chỉnh kỹ thuật Đợt 01 (Chương 09–11) đã được hoàn tất và cô lập trên branch `design/ch09-11-agent2-redesign`.
> Theo quy tắc Hard Approval Gate của dự án:
> - **KHÔNG** merge vào `main`.
> - **KHÔNG** push trực tiếp vào `main`.
> - **KHÔNG** chỉnh sửa `Golang_Master.pdf`.
> - Dừng tại `AWAITING_MANUAL_APPROVAL` để người dùng và ChatGPT tiến hành review độc lập trước khi phê duyệt tích hợp.
