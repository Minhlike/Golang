# opsprobe — Dự án tổng kết (Capstone)

`opsprobe` là hệ thống kiểm tra sức khỏe phụ thuộc (dependency probe) và quan sát trạng thái vận hành, được thiết kế theo đúng triết lý của cuốn sách: **không trừu tượng hóa suy đoán, ưu tiên contract, failure và evidence**.

---

## 1. Kiến trúc gói và ranh giới trách nhiệm

```
projects/opsprobe/
├── cmd/opsprobe/          # Composition root, CLI oneshot và HTTP daemon
├── internal/
│   ├── probe/             # Bounded concurrency pool, phân loại kết quả (Outcome)
│   ├── store/             # SQLite persistence, transaction nguyên tử, CHECK constraints
│   ├── telemetry/         # JSON logger (slog), Prometheus metrics, OpenTelemetry
│   └── httpapi/           # REST HTTP API, middleware, backpressure, health probes
├── incident/              # Bài tập chẩn đoán sự cố cạn kiệt TCP socket (reproducer & httptrace)
├── deploy/
│   ├── Dockerfile         # Multi-stage Distroless non-root
│   ├── k8s/               # Deployment (replicas: 1), Service, ConfigMap, PVC
│   └── terraform/         # AWS OIDC least-privilege bridge
└── scenarios_test.go      # Kiểm thử 6 kịch bản sự cố vận hành
```

---

## 2. Các nguyên tắc kỹ thuật cốt lõi

1. **Phân loại kết quả (Outcome Classification):**
   Mỗi lần probe được phân loại rành mạch: `success`, `failure`, `timeout`, `cancel`. Không bao giờ đánh đồng timeout với hủy ngang hay lỗi kết nối mạng. Kết quả ghi nhận độ trễ cả ở đơn vị nano-giây (`DurationNs`) và mili-giây (`DurationMs`).

2. **Đồng thời có kiểm soát (Bounded Concurrency & Backpressure):**
   Worker pool giới hạn số lượng goroutine hoạt động (`--concurrency`), ngăn chặn bão goroutine. Trạng thái worker thực tế được đồng bộ trực tiếp qua `WorkerObserver` tới metric `opsprobe_active_workers`. HTTP API áp dụng semaphore từ chối đợt chạy vượt ngưỡng với mã `429 Too Many Requests`.

3. **Giao dịch nguyên tử (Atomic Transactions):**
   Toàn bộ kết quả của một đợt chạy và các probe thành phần được ghi vào SQLite trong một transaction duy nhất qua `database/sql`. Bất kỳ lỗi hoặc context cancellation nào xảy ra giữa chừng đều kích hoạt `tx.Rollback()`. Schema áp dụng ràng buộc `CHECK (status_code >= 0)` cho phép kiểm chứng rollback tất định khi có lỗi ở giữa tiến trình ghi.

4. **Chính sách Bounded Drain & Connection Reuse:**
   Luôn đóng `resp.Body.Close()`. Sử dụng bounded reader (`io.LimitedReader`, tối đa 16 KiB) để đọc dữ liệu thừa. Chỉ những response thực sự đọc đến EOF trong phạm vi 16 KiB mới đủ điều kiện tái sử dụng socket HTTP/1.x (`reused_eligible = true`). Các response vượt ngưỡng sẽ bị ngắt và đóng socket thay vì tiêu tốn tài nguyên vô ích, đánh đổi có chủ đích giữa an toàn bộ nhớ và tỷ lệ tái sử dụng kết nối.

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
go run ./cmd/opsprobe --addr=127.0.0.1:8080 --db=opsprobe.db --concurrency=4
```

Gửi yêu cầu kiểm tra hàng loạt target:

```powershell
curl -X POST http://127.0.0.1:8080/runs `
  -H "Content-Type: application/json" `
  -d '{"targets":[{"id":"local","url":"http://127.0.0.1:8080/livez"}]}'
```

Xem metrics Prometheus:

```powershell
curl http://127.0.0.1:8080/metrics
```

---

## 4. Ranh giới triển khai và công cụ

- Thư mục `deploy/` cung cấp cấu hình reviewable chuẩn mẫu:
  - `deploy/k8s/deployment.yaml` cấu hình `replicas: 1` kết hợp `pvc.yaml` (`ReadWriteOnce`) và `strategy: Recreate` vì SQLite là cơ sở dữ liệu file cục bộ, không hỗ trợ đa tiến trình ghi đồng thời từ nhiều Pod độc lập. Nếu cần scale ngang (`replicas > 1`), tầng storage cần chuyển sang PostgreSQL.
  - Image sử dụng placeholder digest có chú thích rõ ràng (`# REPLACE_WITH_VERIFIED_DIGEST_BEFORE_APPLY`), không dùng fake digest hay tag trôi nổi.
- **Lưu ý môi trường:** Máy trạm hiện tại không cài đặt `docker`, `kubectl`, `terraform` hay `aws`. Các artifact này là mã nguồn kiểm tra thiết kế, không tự ý cài đặt công cụ hoặc khởi tạo tài nguyên đám mây thật.
