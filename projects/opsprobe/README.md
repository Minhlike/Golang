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
   Worker pool giới hạn số lượng goroutine hoạt động (`--concurrency`), ngăn chặn bão goroutine. Trạng thái worker thực tế được đồng bộ trực tiếp qua `WorkerObserver` tới metric `opsprobe_active_workers`. HTTP API áp dụng semaphore từ chối đợt chạy vượt ngưỡng với mã `429 Too Many Requests`. Slot semaphore chỉ được cấp phát SAU KHI JSON payload và target list đã được validate cú pháp hợp lệ, bảo vệ hệ thống trước tấn công cạn kiệt slot bởi request rác.

3. **Giao dịch nguyên tử (Atomic Transactions) & Quản lý tiến trình bị hủy:**
   Toàn bộ kết quả của một đợt chạy và các probe thành phần được ghi vào SQLite trong một transaction duy nhất qua `database/sql`. Bất kỳ lỗi nào xảy ra giữa chừng đều kích hoạt `tx.Rollback()`. Schema áp dụng ràng buộc `CHECK (status_code >= 0)` cho phép kiểm chứng rollback tất định khi có lỗi ở giữa tiến trình ghi. Khi client hủy request context, probe dừng ngay lập tức và tiến trình ghi nhận trạng thái đã hủy (`status: "canceled"`) được thực thi trong một context độc lập có bounded timeout (5s), bảo đảm sổ cái vận hành luôn được cập nhật chính xác.

4. **Chính sách Bounded Drain & Connection Reuse Semantics:**
   Thời lượng probe (`Duration`) được định nghĩa chuẩn xác từ trước khi gửi request tới khi kết thúc toàn bộ cleanup/drain policy.
   Luôn đóng `resp.Body.Close()`. Sử dụng bounded reader (`io.LimitedReader`, tối đa 16 KiB) để đọc dữ liệu thừa nhằm giải phóng stream mà không tiêu tốn tài nguyên vô ích hay nạp toàn bộ vào RAM.
   Chỉ những response thực sự đọc đến EOF trong phạm vi 16 KiB mới đủ điều kiện tái sử dụng socket HTTP/1.x (`reused_eligible = true`). Response vượt ngưỡng sẽ bị ngắt và đóng socket thay vì tiêu tốn tài nguyên, đánh đổi có chủ đích giữa an toàn bộ nhớ và tỷ lệ tái sử dụng kết nối. Lưu ý rằng `reused_eligible` là điều kiện cần trên tầng stream, không phải bảo đảm tuyệt đối của mọi tầng Transport.

5. **Lan truyền ngữ cảnh phân tán (Distributed Tracing Propagation):**
   Tự động chèn W3C `traceparent` header vào mọi outbound probe request dựa trên child span context, liên kết chuỗi vết (trace chain) từ opsprobe xuyên suốt sang target service.

6. **Mô hình đe dọa và Ranh giới an toàn (Threat Model & Security Boundary):**
   - **Mục đích sử dụng:** `opsprobe` được thiết kế như một công cụ chẩn đoán vận hành nội bộ (trusted-operator diagnostic tool) dành cho SRE/Platform engineer trong mạng nội bộ tin cậy.
   - **Giới hạn kiểm tra URL:** Hàm `ValidateTarget` kiểm tra cú pháp URL (scheme `http`/`https`, host không rỗng, cấm userinfo credential `user:pass@host`) là validation tầng ứng dụng cơ bản, **KHÔNG PHẢI là cơ chế phòng vệ chống SSRF (Server-Side Request Forgery) toàn diện**.
   - **Yêu cầu bảo vệ mạng:** Khi triển khai trong môi trường nhận input từ bên ngoài, `opsprobe` bắt buộc phải đặt sau reverse proxy bảo vệ, cấu hình egress firewall / NetworkPolicy chặn các dải IP nội bộ nhạy cảm (Private RFC 1918, Loopback RFC 1122, Link-local RFC 3927, Metadata service `169.254.169.254`).
   - **Bảo mật nhật ký:** Toàn bộ query string và credential trong URL đều được lược bỏ (redacted) trước khi ghi log hoặc trace span attributes (`SanitizeURL`).
   - **Hợp đồng JSON:** Trường `timeout_ms` trong request payload sử dụng kiểu số nguyên milli-giây (`0 <= timeout_ms <= 60000`), bảo đảm tính tương thích đa ngôn ngữ thay vì parse chuỗi duration đặc thù của riêng Go.

7. **Tắt nguồn mềm mại (Graceful Shutdown):**
   Bắt tín hiệu `SIGINT`/`SIGTERM` qua `signal.NotifyContext`, đóng listener mới, cho phép các probe đang dở dang hoàn tất với deadline tối đa 10s trước khi đóng database và flush telemetry. Cấu hình biến môi trường và cờ dòng lệnh áp dụng validation nghiêm ngặt (fail-fast, không fallback ngầm khi giá trị cấu hình sai).

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
