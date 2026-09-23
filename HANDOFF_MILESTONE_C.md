# Handoff — Milestone C (Capstone opsprobe & Đóng Sách Hoàn Tất)

Tài liệu này bàn giao toàn bộ trạng thái sau khi hoàn tất **Milestone C: Capstone Project `projects/opsprobe/`** và 2 vi chỉnh kỹ thuật cuối cùng của Milestone B.

Toàn bộ công việc kế thừa `MASTER PROMPT.txt`, các chương từ 1 đến 20, toàn bộ `labs/`, và bản PDF hiện tại `Golang_Master.pdf` (220 trang). Giữ nguyên vẹn giọng văn tiếng Việt tự nhiên ("em" và "anh").

---

## 1. Các hạng mục đã hoàn thành trong đợt làm việc

### A. Đóng triệt để 2 lỗi kỹ thuật cuối của Milestone B

1. **Xóa hoàn toàn Fake Manifest Digest Fallback:**
   - Trong `labs/part18-workflow-delivery/workflows/delivery.yaml`, đã xóa sạch chuỗi digest giả lập `sha256:0123456789abcdef...`.
   - Workflow trích xuất `containerimage.digest` từ metadata JSON của Buildx, kiểm tra định dạng regex `^sha256:[0-9a-f]{64}$`.
   - Nếu không có digest hợp lệ, workflow dừng ngay lập tức với exit code 1, không fallback vào Image ID của daemon cục bộ hay bất kỳ chuỗi giả mạo nào.

2. **Thực thi Fail-Closed Thực Sự trong Workflow Specimen:**
   - Trong job `promote-production`, loại bỏ hoàn toàn `|| echo ...` và mọi cơ chế swallow error. Khi `--provenance-verified=false`, `promote-gate` trả về mã lỗi 1 và job dừng ngay lập tức.
   - Bước deploy được chuyển sang dạng tài liệu mô tả (commented/documented), khẳng định nguyên tắc: ứng viên bị gate từ chối thì tuyệt đối không có bất kỳ lệnh deploy nào được thực thi.
   - Cập nhật Chương 18 và `HANDOFF_MILESTONE_B.md` đồng bộ 100% với failure model này.

### B. Hoàn thành Milestone C: Capstone Project (`projects/opsprobe/`)

Xây dựng trọn vẹn hệ thống `opsprobe` theo đúng các nguyên tắc kỹ thuật chuẩn mực:

1. **Gói Domain & Worker Pool (`internal/probe/`):**
   - Phân loại kết quả rõ ràng: `OutcomeSuccess`, `OutcomeFailure`, `OutcomeTimeout`, `OutcomeCancel`.
   - Worker pool với số lượng goroutine bị chặn (`--concurrency`), ngăn chặn bão goroutine.
   - Gán `context.WithTimeout` riêng cho từng target, phân biệt giữa timeout mạng và hủy ngang của tiến trình.
   - Đọc cạn dữ liệu thừa qua `io.Copy(io.Discard, ...)` trước khi `resp.Body.Close()`, bảo đảm kết nối TCP được tái sử dụng qua `http.Transport` connection pool.

2. **Gói Lưu trữ Nguyên tử (`internal/store/`):**
   - Cài đặt SQLite thuần Go qua `modernc.org/sqlite` và `database/sql` (zero CGO dependency).
   - Thiết lập pool an toàn cho SQLite đơn luồng ghi: `SetMaxOpenConns(1)`.
   - Ghi nhận `runs` và `probe_results` trong **một transaction nguyên tử duy nhất**. Kiểm chứng tính toàn vẹn: nếu lỗi hoặc hủy context giữa chừng, toàn bộ transaction được rollback sạch sẽ, không để lại bản ghi rác.

3. **Gói Quan sát Hệ thống (`internal/telemetry/`):**
   - Structured JSON logging qua thư viện chuẩn `log/slog`.
   - Prometheus metrics cục bộ: `opsprobe_probes_total` (CounterVec theo outcome), `opsprobe_probe_duration_seconds` (HistogramVec), `opsprobe_active_workers` (Gauge), và `opsprobe_runs_total` (CounterVec). Khởi tạo trước các nhãn chuẩn để metric family luôn hiển thị khi scrape.
   - OpenTelemetry spans gắn metadata phân tích đợt chạy và từng probe.

4. **Gói HTTP API & Điều phối Vận hành (`internal/httpapi/`):**
   - Go 1.22+ method-based pattern routing: `POST /runs`, `GET /runs/{id}`, `GET /readyz`, `GET /livez`, `GET /metrics`.
   - Áp suất ngược (backpressure): sử dụng buffered channel semaphore để từ chối đợt chạy thứ `N+1` với mã `429 Too Many Requests` khi quá tải.
   - Kiểm tra readiness thực thụ dựa trên kết nối SQLite (`store.Ping`).
   - Middleware ghi log và phục hồi panic an toàn.

5. **Gói Command & Vòng đời Vận hành (`cmd/opsprobe/`):**
   - Chế độ CLI một lần duy nhất (`--oneshot-url`) in kết quả và trả exit code 0/1.
   - Chế độ HTTP daemon với graceful shutdown: bắt `SIGINT`/`SIGTERM` qua `signal.NotifyContext`, đóng listener và chờ 10s để các request đang dở dang hoàn tất trước khi đóng database.

6. **Kiểm thử 6 Kịch bản Sự cố Vận hành (`scenarios_test.go`):**
   - Scenario 1: Target trả HTTP 5xx (`OutcomeFailure`).
   - Scenario 2: Target timeout vượt quá deadline (`OutcomeTimeout`).
   - Scenario 3: Target URL malformed (`OutcomeFailure`).
   - Scenario 4: Áp suất ngược từ chối khi bão tải (`429 Too Many Requests`).
   - Scenario 5: Transaction rollback bảo toàn trạng thái khi DB hủy context.
   - Scenario 6: Mid-run cancellation khi tiến trình cha hủy ngang (`OutcomeCancel`).

7. **Bài tập Chẩn đoán Sự cố Thực nghiệm (`incident/`):**
   - Kịch bản: Bão cạn kiệt Socket TCP và Treo tầng ngầm do quên đóng response body.
   - Bộ kiểm chứng `incident_test.go` với `net/http/httptrace`:
     - `BuggyProbe`: 20 request tạo ra 20 kết nối mới (`NewConns=20, ReusedConns=0`).
     - `FixedProbe`: 20 request chỉ tạo đúng 1 kết nối và tái sử dụng 19 lần (`NewConns=1, ReusedConns=19`).
   - Tài liệu `incident/README.md` hướng dẫn điều tra qua 4 tầng bằng chứng và phần ĐÁP ÁN được giấu ở cuối trang.

8. **Tài liệu Triển khai Mẫu (Reviewable Manifests trong `deploy/`):**
   - `Dockerfile`: Multi-stage Distroless non-root (`gcr.io/distroless/static-debian12:nonroot`, UID 65532).
   - Kubernetes: `deployment.yaml` (readOnlyRootFilesystem, liveness/readiness probes, volume `/data`), `service.yaml`, `configmap.yaml`.
   - Terraform: `main.tf` với AWS OIDC IAM least privilege, khóa chặt claim `sub` và Account ID caller.
   - **Ghi chú ranh giới:** Máy trạm hiện tại không có `docker`, `kubectl`, `terraform`, `aws`. Toàn bộ các artifact này là mã nguồn kiểm tra cú pháp và thiết kế, không tự ý cài đặt hay tạo tài nguyên đám mây.

### C. Bản thảo Sách và Đường ống PDF

- Biên soạn mới hoàn chỉnh **Chương 20: Dự án tổng kết: opsprobe từ mã nguồn đến vận hành** (`book/chapters/20-du-an-tong-ket-opsprobe.md`).
- Cập nhật mục lục và bản đồ cuốn sách trong `book/README.md`.
- Cập nhật `scripts/build_pdf.py` với cấu hình danh sách chương đầy đủ.
- Biên dịch thành công PDF chính thức: **220 trang** `Golang_Master.pdf`.
- Đã thực hiện Visual QA 100% bằng `pypdfium2` render toàn bộ các trang từ 211 đến 220 ở độ phân giải cao; toàn bộ bảng biểu, khối code và sơ đồ đều vừa vặn hoàn hảo trong lề trang.

---

## 2. Báo cáo Kết quả Kiểm thử Toàn diện (QA)

Đã chạy kiểm tra thực tế trên Go toolchain cục bộ (Go 1.27.1 windows/amd64):

1. **`projects/opsprobe`:**
   - `go test -v ./...` -> PASS (toàn bộ các gói `probe`, `store`, `telemetry`, `httpapi`, `cmd/opsprobe`, `incident`, và `scenarios_test.go`).
   - `go test -race ./...` -> PASS (100% sạch data race).
   - `go vet ./...` -> PASS (không phát hiện bất kỳ cảnh báo tĩnh nào).

2. **`labs/part18-workflow-delivery`:**
   - `go test -v ./...` -> PASS.
   - `go test -race ./...` -> PASS.
   - `go vet ./...` -> PASS.

3. **`gofmt -l`:**
   - Toàn bộ mã nguồn Go trong `projects/opsprobe` và các lab liên quan đều sạch định dạng 100%.

4. **Bảo toàn Tuyệt đối Artifact Cục bộ:**
   - Giữ nguyên vẹn, không sửa, không stage, không xóa:
     - `.tmp-editorial-pages/`
     - `labs/part10-measure-first/baseline-cpu.out`
     - `labs/part10-measure-first/baseline.test.exe`

---

## 3. Trạng thái Sẵn sàng

Toàn bộ các mục tiêu của Milestone B (micro-repairs) và Milestone C (Capstone opsprobe, Chapter 20, PDF 220 trang) đã hoàn thành trọn vẹn và sẵn sàng đồng bộ lên remote `origin/main`.
