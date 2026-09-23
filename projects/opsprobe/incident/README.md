# Bài tập chẩn đoán sự cố: Bão cạn kiệt Socket và Quản lý vòng đời HTTP Connection

## 1. Kịch bản mô phỏng sư phạm (Scenario Narrative)

> [!NOTE]
> **Lưu ý phương pháp luận:** Đây là kịch bản giả định (narrative context) mô phỏng tình huống sự cố điển hình thường gặp trong thực tế vận hành khi rò rỉ socket file descriptor. Các chỉ số trong phần này phục vụ mục đích xây dựng bối cảnh bài toán, không phải số liệu đo đạc trực tiếp từ một benchmark cụ thể.

Hệ thống probe giả định được triển khai để thăm dò trạng thái (health-check) liên tục cho 50 microservices nội bộ. Sau một thời gian hoạt động, hệ thống giám sát ghi nhận các triệu chứng suy thoái hiệu năng:

1. **Tỷ lệ Timeout tăng cao:** Tỷ lệ timeout của các lượt probe tăng dần khi tải tăng.
2. **Độ trễ thăm dò leo thang:** Thời gian phản hồi trung bình chạm trần deadline quy định.
3. **Mâu thuẫn dữ liệu:** Các kỹ sư phụ trách target service khẳng định dịch vụ đích vẫn phản hồi bình thường khi cURL độc lập từ máy trạm, nhưng probe từ ứng dụng lại thất bại.
4. **Hệ điều hành tích tụ kết nối:** Trạng thái socket trên máy chủ ghi nhận số lượng kết nối TCP mở tăng liên tục, tiệm cận giới hạn file descriptors (`ulimit -n`).

---

## 2. Nhiệm vụ thực hành

Hãy đóng vai trò kỹ sư tiếp nhận sự cố:
1. Đọc tệp `projects/opsprobe/incident/incident.go` (so sánh hàm `BuggyProbe` và `FixedProbe`).
2. Chạy kịch bản kiểm chứng thực nghiệm:
   ```powershell
   go test -v ./incident
   go test -race ./incident
   ```
3. Giải thích tại sao một hàm HTTP client đơn giản không báo lỗi compiler, trả về status 200 trong unit test đơn lẻ, nhưng lại gây rò rỉ kết nối khi chạy lặp lại ở quy mô lớn?
4. Thiết kế chính sách giải phóng tài nguyên thỏa mãn hợp đồng thư viện chuẩn `net/http` mà vẫn an toàn trước các luồng phản hồi độc hại.

---

## 3. Bằng chứng đo đạc thực nghiệm (Empirical Measurements)

Khác với phần mô phỏng định tính ở trên, tệp kiểm thử `incident_test.go` cung cấp số liệu đo đạc thực tế thông qua thư viện `net/http/httptrace`.

### Kết quả đo đạc từ kiểm thử `TestIncident_ConnectionReuseProof`

Với 20 lượt gửi request tuần tự đến cùng một host HTTP/1.1 trả về payload 10 KiB:

| Chỉ số | BuggyProbe (Bỏ quên Close Body) | FixedProbe (Close + Bounded Drain 16 KiB) |
| :--- | :--- | :--- |
| **New TCP Connections (`GotConnInfo.Reused == false`)** | **20** | **1** (chỉ kết nối đầu tiên) |
| **Reused Connections (`GotConnInfo.Reused == true`)** | **0** | **19** (95% tái sử dụng) |
| **Hành vi Transport** | Mỗi request mở socket mới | Socket được trả về pool để tái sử dụng |

### Giới hạn và bản chất kỹ thuật của chính sách Bounded Drain

> [!IMPORTANT]
> **Giới hạn thực nghiệm:** Thử nghiệm drain 16 KiB (`MaxDrainBytes = 16384`) chứng minh connection reuse thành công cho khối lượng công việc cụ thể có kích thước payload nhỏ hơn 16 KiB (ví dụ payload 10 KiB nói trên). Đây **không phải là sự bảo đảm tái sử dụng phổ quát** cho mọi trường hợp.

1. **EOF là điều kiện tiên quyết cho HTTP/1.x reuse:** Để `http.Transport` có thể sử dụng lại cùng một TCP socket cho request tiếp theo trên giao thức HTTP/1.1, Transport bắt buộc phải đọc đến điểm kết thúc (`io.EOF`) của stream dữ liệu hiện tại. Nếu stream chưa cạn, request kế tiếp sẽ đọc nhầm dữ liệu của request trước.
2. **Nguy cơ của unbounded drain:** Nếu gọi `io.Copy(io.Discard, resp.Body)` mà không giới hạn độ dài, một target bị lỗi hoặc ác ý (trả về stream vô hạn hoặc hàng chục GiB) sẽ khiến worker probe bị treo hoặc tiêu tốn tài nguyên vô ích.
3. **Đánh đổi có chủ đích (Tradeoff):** OpsProbe chọn chính sách đọc tối đa 16 KiB (`lr := &io.LimitedReader{R: resp.Body, N: MaxDrainBytes + 1}`).
   - Nếu `lr.N > 0`: Toàn bộ body đã được đọc hết đến EOF trong phạm vi an toàn -> socket **đủ điều kiện tái sử dụng** (`ReusedEligible = true`).
   - Nếu `lr.N == 0`: Payload vượt quá 16 KiB (kiểm chứng tại `TestIncident_BoundedDrainOversizedBody`) -> socket bị ngắt và đóng lại, không tái sử dụng (`ReusedEligible = false`). Đây là sự đánh đổi chấp nhận hy sinh connection reuse để ưu tiên an toàn bộ nhớ và ngăn chặn cạn kiệt tài nguyên.

---

## 4. Bốn tầng chẩn đoán rò rỉ mạng trong Go

Khi điều tra sự cố kết nối mạng trong ứng dụng Go, kỹ sư cần phối hợp 4 tầng thông tin:

- **Tầng 1 (Hệ điều hành / OS Socket):**
  Kiểm tra số lượng socket đang mở:
  ```bash
  ss -s
  lsof -p <PID> | wc -l
  ```
  Nếu số lượng socket mở tăng tuyến tính theo số lượng request mà không giải phóng, hệ thống đang gặp vấn đề ở tầng socket.

- **Tầng 2 (Transport Connection Pool):**
  `http.Transport` quản lý connection pool nội bộ (`MaxIdleConns`, `MaxIdleConnsPerHost`). Socket chỉ được đưa vào idle pool khi response body đã hoàn tất và được đóng đúng quy cách.

- **Tầng 3 (Runtime Client Trace):**
  Tích hợp `net/http/httptrace` với hook `GotConnInfo.Reused` để theo dõi chính xác tỷ lệ kết nối mới so với kết nối tái sử dụng ở cấp độ runtime.

- **Tầng 4 (Resource Ownership trong Go):**
  Rà soát điểm kết thúc của `resp.Body`: luôn đảm bảo `defer resp.Body.Close()` được gọi ngay sau khi kiểm tra `err == nil`, và áp dụng bounded drain trước khi kết thúc xử lý.
