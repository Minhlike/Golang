# opsprobe — Dự án tổng kết (Capstone)

`opsprobe` là hệ thống kiểm tra sức khỏe phụ thuộc (dependency probe) và quan sát trạng thái vận hành, được thiết kế theo đúng triết lý của cuốn sách: **không trừu tượng hóa suy đoán, ưu tiên contract, failure và evidence**.

---

## 1. Kiến trúc gói và ranh giới trách nhiệm

```
projects/opsprobe/
├── cmd/opsprobe/          # Composition root, CLI oneshot và HTTP daemon
├── internal/
│   ├── probe/             # Bounded concurrency pool, phân loại kết quả (Outcome)
│   ├── store/             # SQLite persistence, transaction nguyên tử
│   ├── telemetry/         # JSON logger (slog), Prometheus metrics, OpenTelemetry
│   └── httpapi/           # REST HTTP API, middleware, backpressure, health probes
├── incident/              # Bài tập chẩn đoán sự cố cạn kiệt TCP socket (reproducer)
├── deploy/
│   ├── Dockerfile         # Multi-stage Distroless non-root
│   ├── k8s/               # Deployment, Service, ConfigMap
│   └── terraform/         # AWS OIDC least-privilege bridge
└── scenarios_test.go      # Kiểm thử 6 kịch bản sự cố vận hành
```

---

## 2. Các nguyên tắc kỹ thuật cốt lõi

1. **Phân loại kết quả (Outcome Classification):**
   Mỗi lần probe được phân loại rành mạch: `success`, `failure`, `timeout`, `cancel`. Không bao giờ đánh đồng timeout với hủy ngang hay lỗi kết nối mạng.

2. **Đồng thời có kiểm soát (Bounded Concurrency & Backpressure):**
   Worker pool giới hạn số lượng goroutine hoạt động (`--concurrency`), ngăn chặn bão goroutine. HTTP API áp dụng semaphore từ chối đợt chạy thứ `N+1` với mã `429 Too Many Requests` khi quá tải.

3. **Giao dịch nguyên tử (Atomic Transactions):**
   Toàn bộ kết quả của một đợt chạy và các probe thành phần được ghi vào SQLite trong một transaction duy nhất qua `database/sql`. Bất kỳ lỗi hoặc context cancellation nào xảy ra giữa chừng đều kích hoạt `tx.Rollback()`, không để lại trạng thái rác.

4. **Tái sử dụng kết nối (Connection Pooling & Resource Lifetime):**
   Đọc cạn dữ liệu thừa qua `io.Copy(io.Discard, ...)` trước khi đóng `resp.Body.Close()`, bảo đảm kết nối TCP được trả về cho `http.Transport` thay vì rò rỉ socket hệ điều hành.

5. **Tắt nguồn mềm mại (Graceful Shutdown):**
   Bắt tín hiệu `SIGINT`/`SIGTERM` qua `signal.NotifyContext`, đóng listener mới, cho phép các probe đang dở dang hoàn tất với deadline tối đa 10s trước khi đóng database và flush telemetry.

---

## 3. Lệnh kiểm thử và vận hành cục bộ

Chạy toàn bộ test suite, kiểm tra race condition và phân tích tĩnh:

```powershell
cd projects/opsprobe
go test -v ./...
go test -race ./...
go vet ./...
```

Chạy CLI kiểm tra một URL đơn lẻ (oneshot mode):

```powershell
go run ./cmd/opsprobe --oneshot-url=https://go.dev --timeout=2s
```

Khởi chạy daemon server:

```powershell
go run ./cmd/opsprobe --addr=:8080 --db=opsprobe.db --concurrency=4
```

Gửi yêu cầu kiểm tra hàng loạt target:

```powershell
curl -X POST http://localhost:8080/runs `
  -H "Content-Type: application/json" `
  -d '{"targets":[{"id":"local","url":"http://localhost:8080/livez"}]}'
```

Xem metrics Prometheus:

```powershell
curl http://localhost:8080/metrics
```

---

## 4. Ranh giới triển khai và công cụ

- Thư mục `deploy/` cung cấp cấu hình reviewable chuẩn mẫu.
- **Lưu ý môi trường:** Máy trạm hiện tại không cài đặt `docker`, `kubectl`, `terraform` hay `aws`. Các artifact này là mã nguồn kiểm tra thiết kế, không tự ý cài đặt công cụ hoặc khởi tạo tài nguyên đám mây thật.
