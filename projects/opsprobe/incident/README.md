# Bài tập chẩn đoán sự cố: Bão cạn kiệt Socket và Treo tầng ngầm

## 1. Bối cảnh sự cố

Hệ thống `opsprobe` được triển khai để thăm dò trạng thái (health-check) liên tục cho 50 microservices nội bộ. Sau khoảng 20 phút chạy ổn định, hệ thống giám sát phát tín hiệu cảnh báo P1 khẩn cấp:

1. **Prometheus Alert:** Tỷ lệ `OutcomeTimeout` tăng vọt từ 0.05% lên gần 90%.
2. **Dashboard Tracing:** Thời gian phản hồi trung bình (`opsprobe_probe_duration_seconds`) chạm ngưỡng kịch trần (3.0s).
3. **Mâu thuẫn dữ liệu:** Các kỹ sư phụ trách target service khẳng định hệ thống của họ hoàn toàn khỏe mạnh; các công cụ cURL hay Ping trực tiếp từ máy trạm chỉ mất 2-3ms để trả về HTTP 200 OK.
4. **Hệ điều hành:** Lệnh `netstat` hoặc `ss -tan` trên máy chủ chạy `opsprobe` ghi nhận hàng nghìn kết nối TCP ở trạng thái `ESTABLISHED` hoặc `TIME_WAIT`. Số lượng file descriptors mở vượt ngưỡng `ulimit -n`.

---

## 2. Nhiệm vụ của bạn

Hãy đóng vai trò SRE/DevOps Engineer trực ca tiếp nhận sự cố:
1. Đọc tệp `projects/opsprobe/incident/incident.go` (đoạn hàm `BuggyProbe`).
2. Chạy kịch bản kiểm chứng:
   ~~~powershell
   go test -v ./incident
   go test -race ./incident
   ~~~
3. Giải thích tại sao một hàm gửi HTTP request đơn giản không báo lỗi compiler, unit test một lần chạy vẫn thấy status 200, nhưng lại gây sập toàn bộ tầng mạng khi chạy ở quy mô lớn?
4. Đề xuất bản sửa lỗi thỏa mãn hợp đồng tài nguyên của thư viện chuẩn Go (`net/http`).

---

## 3. Quá trình chẩn đoán 4 tầng bằng chứng

Khi điều tra sự cố rò rỉ tài nguyên mạng trong Go, đừng đoán mò. Hãy lần theo 4 tầng bằng chứng:

- **Tầng 1 (Hệ điều hành / OS Socket):**
  Kiểm tra số lượng socket đang mở:
  ~~~bash
  ss -s
  lsof -p <PID> | wc -l
  ~~~
  Nếu số lượng socket liên tục tăng tuyến tính theo số request gửi đi mà không giảm, hệ thống đang bị rò rỉ TCP socket.

- **Tầng 2 (Transport Connection Pool):**
  Go `http.Transport` duy trì một connection pool (`MaxIdleConns`, `MaxIdleConnsPerHost`). Để một socket TCP được trả lại pool và tái sử dụng cho request sau (Keep-Alive), Go bắt buộc phải biết rằng request trước đó đã hoàn toàn kết thúc.

- **Tầng 3 (Runtime Client Trace):**
  Sử dụng `net/http/httptrace` với hook `GotConnInfo.Reused`.
  Nếu `info.Reused` luôn bằng `false`, mỗi request đều đang phải bắt tay TCP 3-bước (3-way handshake) mới, làm cạn kiệt ephemeral ports và file descriptors.

- **Tầng 4 (Resource Ownership trong Go):**
  Kiểm tra điểm kết thúc của `resp.Body`. Ai sở hữu stream? Khi nào stream đóng? Dữ liệu trên dây mạng đã được đọc cạn chưa?

---

### ĐÁP ÁN — chỉ đọc sau khi đã tự làm

#### Nguyên nhân gốc rễ (Root Cause)

Trong Go, `http.Response.Body` là một `io.ReadCloser` đại diện cho luồng dữ liệu thô đọc trực tiếp từ kết nối TCP socket.

Trong đoạn mã của `BuggyProbe`:
~~~go
resp, err := client.Do(req)
if err != nil {
    return 0, err
}
// BUG: Không gọi resp.Body.Close()
return resp.StatusCode, nil
~~~

Khi lập trình viên quên gọi `resp.Body.Close()` (hoặc return sớm ở nhánh kiểm tra status code mà quên close body):
1. **Chiếm giữ Socket vĩnh viễn:** Kết nối TCP bên dưới vẫn bị xem là "đang bận đọc dở". `http.Transport` không được phép đưa socket này trở lại pool tái sử dụng.
2. **Cạn kiệt Ephemeral Port & File Descriptors:** Mỗi request tiếp theo bắt buộc phải mở một socket TCP mới. Khi số lượng socket đạt giới hạn của hệ điều hành (`ulimit -n`), các lệnh `DialContext` sau đó sẽ bị block hoặc timeout hàng loạt.
3. **Đọc cạn dữ liệu thừa:** Ngay cả khi có gọi `resp.Body.Close()`, nếu payload trả về lớn hơn bộ đệm đọc ngầm của Go (vài KB) mà ta không chủ động đọc cạn (`io.Copy(io.Discard, ...)`), Go Transport buộc phải đóng socket thay vì tái sử dụng.

#### Cách khắc phục chuẩn xác

Tuân thủ nghiêm ngặt quy tắc quản lý vòng đời tài nguyên:
~~~go
resp, err := client.Do(req)
if err != nil {
    return 0, err
}
defer resp.Body.Close()

// Đọc cạn tối đa một lượng byte an toàn để Transport có thể tái sử dụng socket
_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, 16384))
~~~

Chạy lại test để thấy sự khác biệt:
- `BuggyProbe`: 20 requests tạo ra 20 kết nối mới (`NewConns=20, ReusedConns=0`).
- `FixedProbe`: 20 requests chỉ tạo duy nhất 1 kết nối ban đầu, 19 request sau tái sử dụng 100% kết nối (`NewConns=1, ReusedConns=19`).
