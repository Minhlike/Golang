# Handoff — Milestone C (Capstone opsprobe Hardened & Chốt Baseline Hệ Thống)

Tài liệu này bàn giao toàn bộ trạng thái sau khi hoàn tất **Milestone C Capstone Hardening Pass** cho dự án `projects/opsprobe/`, Chương 20, và đường ống sách PDF. Milestone C hoàn thành, current baseline đã chốt. Sách tiếp tục phát triển tiến về phía trước theo quy tắc Living Textbook.

Toàn bộ công việc kế thừa `MASTER PROMPT.txt`, các chương từ 1 đến 20, toàn bộ `labs/`, và bản PDF chính thức `Golang_Master.pdf`. Giữ nguyên vẹn giọng văn tiếng Việt tự nhiên ("em" và "anh").

---

## 1. Chi tiết các hạng mục đã hoàn thành trong Capstone Hardening Pass

### A. Tầng Domain & Resource Lifecycle (`internal/probe/`)

1. **Chính sách Bounded Drain & Connection Reuse:**
   - Thay thế ngộ nhận "đọc cạn" bằng chính sách đọc có kiểm soát: `io.LimitedReader{R: resp.Body, N: MaxDrainBytes + 1}` (`MaxDrainBytes = 16384` bytes / 16 KiB).
   - Chỉ đánh dấu `ReusedEligible = true` khi luồng dữ liệu thực sự chạm `io.EOF` trong phạm vi 16 KiB (`lr.N > 0`).
   - Body luôn được giải phóng an toàn qua `defer resp.Body.Close()`.
   - Nếu body vượt quá 16 KiB, socket bị ngắt và đóng, chấp nhận hy sinh connection reuse để ưu tiên an toàn bộ nhớ trước các stream độc hại.

2. **Ranh giới Bảo mật Target (Security Boundary):**
   - Hàm `ValidateTarget` từ chối target chứa userinfo credentials (`user:pass@host`).
   - Khóa chặt HTTP methods: chỉ chấp nhận `GET` và `HEAD`.
   - Kiểm tra giới hạn timeout (tối đa 60s) và mã HTTP mong đợi (100–599).
   - Thiết lập `CheckRedirect: http.ErrUseLastResponse` để ngăn chặn chuyển hướng tự động (SSRF pivot).

3. **Chính xác hóa Ngữ nghĩa Thời gian (Time Semantics):**
   - Kết quả `probe.Result` ghi nhận cả `DurationNs` (nano-giây) cho độ chính xác cao và `DurationMs` (mili-giây) phục vụ dashboard.

### B. Tầng Đồng thời & Quan sát (`internal/telemetry/`, `internal/probe/`)

4. **Đo lường Worker Thực Tế (Không Suy Đoán):**
   - Thiết kế interface `WorkerObserver` (`WorkerStarted()`, `WorkerStopped()`) trong gói `probe`.
   - `telemetry.Telemetry` cài đặt interface này để trực tiếp cập nhật gauge `opsprobe_active_workers` khi worker goroutine thực sự khởi chạy và kết thúc trong pool, thay vì gán giá trị danh nghĩa theo số lượng target.

5. **OpenTelemetry Child Spans Chuẩn Mực:**
   - `probe.Pool` tích hợp `WithTracer(tel.Tracer)`. Mỗi lần probe tạo một child span `"opsprobe.probe"` được gắn kết trực tiếp với parent run context.
   - Thêm cờ `--trace-stdout` vào `cmd/opsprobe` phục vụ debug cục bộ.
   - Bộ kiểm thử `TestPool_Execute_ChildSpans` xác thực khẳng định: `childSpan.Parent.SpanID() == parentSpan.SpanContext().SpanID()`.

### C. Tầng Lưu trữ & Giao dịch Nguyên tử (`internal/store/`)

6. **Bằng chứng Rollback Tất Định (Deterministic Transaction Rollback):**
   - Schema SQLite bổ sung các ràng buộc toàn vẹn:
     `CHECK (status_code >= 0)`,
     `CHECK (status IN ('completed', 'failed', 'canceled'))`,
     `CHECK (outcome IN ('success', 'failure', 'timeout', 'cancel'))`.
   - Kiểm thử `TestStore_DeterministicRollbackAfterPartialMutation` cố tình truyền `status_code: -1` ở bản ghi thứ hai sau khi bản ghi cha đã chèn thành công. Transaction rollback toàn bộ; xác nhận `GetRun` trả `ErrNotFound` và số dòng trong cả hai bảng `runs` và `probe_results` bằng 0.

7. **Phân định Thời điểm Run:**
   - Struct `RunRecord` phân định rành mạch giữa `StartedAt` (bắt đầu thực thi) và `CompletedAt` (kết thúc toàn bộ worker), tránh nhầm lẫn giữa latency của một request với tổng thời gian xử lý cả lô.

### D. Tầng HTTP API & Ranh giới Nhận diện (`internal/httpapi/`)

8. **Ranh giới JSON Đầu Vào (HTTP JSON Boundary):**
   - Giới hạn payload request tối đa 64 KiB qua `http.MaxBytesReader` (trả về `413 Request Entity Too Large` khi vượt ngưỡng).
   - Kích hoạt `dec.DisallowUnknownFields()` để từ chối các trường lạ không thuộc contract.
   - Kiểm tra `io.EOF` sau lượt decode đầu tiên để từ chối các chuỗi JSON nối đuôi (trailing / concatenated JSON).
   - Kiểm tra trùng lặp `TargetID` và từ chối upfront với `400 Bad Request`.

9. **Đồng bộ Hóa Tất Định Trong Test (`scenarios_test.go`):**
   - Loại bỏ hoàn toàn các lệnh `time.Sleep` cảm tính trong `Scenario4_Backpressure_Rejection` và `Scenario6_MidRun_Cancellation`.
   - Sử dụng barrier channel (`reqStarted`, `srvStarted`) để đồng bộ trạng thái chính xác 100%.

### E. Tầng Triển khai Kubernetes & Cấu hình (`deploy/k8s/`, `cmd/opsprobe/`)

10. **Số lượng Pod và Ranh giới Lưu trữ (Storage Boundary):**
    - `deploy/k8s/deployment.yaml`: thiết lập `replicas: 1` kết hợp `strategy: Recreate` và `deploy/k8s/pvc.yaml` (`PersistentVolumeClaim`, `ReadWriteOnce`).
    - Nêu rõ trong manifest: SQLite là file-based database cục bộ; việc mở rộng quy mô ngang (`replicas > 1`) đòi hỏi phải refactor tầng `store` sang hệ quản trị cơ sở dữ liệu client-server (PostgreSQL).

11. **Xóa Fake Digest & Nạp Cấu hình Động:**
    - Xóa hoàn toàn chuỗi fake digest; thay bằng placeholder có chỉ dẫn rõ ràng: `image: ghcr.io/minhlike/opsprobe:v1.0.0 # REPLACE_WITH_VERIFIED_DIGEST_BEFORE_APPLY`.
    - `deployment.yaml` truyền các giá trị từ `configmap.yaml` vào biến môi trường (`OPSPROBE_*`).
    - `cmd/opsprobe/main.go` hỗ trợ fallback từ biến môi trường (`OPSPROBE_ADDR`, `OPSPROBE_DB`, `OPSPROBE_CONCURRENCY`, `OPSPROBE_TIMEOUT`, `OPSPROBE_MAX_ACTIVE_RUNS`, `OPSPROBE_LOG_LEVEL`, `OPSPROBE_ENV`).

### F. Bài tập Sự cố Thực nghiệm (`incident/`)

12. **Phân định Rõ Kịch bản vs Bằng chứng Đo đạc:**
    - `incident/README.md`: phân định rành mạch giữa kịch bản giả định sư phạm (Scenario Narrative) và số liệu đo đạc thực nghiệm từ code (Empirical Measurements).
    - `incident.go` và `incident_test.go`: tích hợp `net/http/httptrace` đo lường chính xác `GotConnInfo.Reused`:
      - `BuggyProbe`: 20 request -> 20 kết nối mới (`NewConns=20, ReusedConns=0`).
      - `FixedProbe` (payload 10 KiB): 20 request -> 1 kết nối mới, 19 kết nối tái sử dụng (`NewConns=1, ReusedConns=19`).
      - Thêm kiểm thử `TestIncident_BoundedDrainOversizedBody`: payload 32 KiB vượt giới hạn 16 KiB sẽ bị ngắt và đóng kết nối (`reusedEligible == false`), bảo vệ an toàn bộ nhớ.

---

## 2. Kết quả Biên dịch và Visual QA Bản thảo Sách

1. **Chương 20 (`book/chapters/20-du-an-tong-ket-opsprobe.md`):**
   - Cập nhật toàn bộ các bài học kỹ thuật: Bounded drain policy, WorkerObserver, deterministic rollback, single-replica SQLite, và incident reproducer.
   - Tinh chỉnh định dạng khối code (tối đa 58 ký tự/dòng), không để lệnh dài chạm mép khung.

2. **Biên dịch PDF (`Golang_Master.pdf`):**
   - Biên dịch hoàn tất thành công qua `scripts/build_pdf.py`.
   - Tổng số trang chính thức: **221 trang**.
   - Toàn bộ 7 mục tham khảo (`@references`) nằm trọn vẹn ở cuối trang 221, không còn trang mồ côi 3 dòng.

3. **Visual QA 100% bằng `pypdfium2`:**
   - Render hình ảnh độ phân giải cao toàn bộ các trang từ 211 đến 221 trong thư mục `.tmp-editorial-pages/`.
   - Kiểm tra trực quan xác nhận:
     - 0 lỗi tràn khung code (code box overflow).
     - 0 lỗi va chạm bảng (table collision).
     - Bố cục trang mở đầu, bảng phân tách trách nhiệm, các khối lệnh PowerShell và curl đều thẳng hàng, sắc nét, đúng chuẩn xuất bản.

---

## 3. Báo cáo Kiểm thử Toàn diện (QA)

Đã chạy kiểm tra thực tế trên Go toolchain cục bộ (Go 1.27.1 windows/amd64):

1. **`projects/opsprobe`:**
   - `go test -v ./...` -> **PASS** (tất cả các gói: `cmd/opsprobe`, `incident`, `internal/httpapi`, `internal/probe`, `internal/store`, `internal/telemetry`, và `scenarios_test.go`).
   - `go test -race ./...` -> **PASS** (100% sạch data race).
   - `go vet ./...` -> **PASS** (0 cảnh báo tĩnh).
   - `gofmt -l` -> **PASS** (100% chuẩn format).

2. **`labs/part18-workflow-delivery`:**
   - `go test -v ./...` -> **PASS**.
   - `go test -race ./...` -> **PASS**.
   - `go vet ./...` -> **PASS**.

3. **Bảo tồn Tuyệt đối Artifact Cục bộ:**
   - `.tmp-editorial-pages/` (untracked, được bảo toàn).
   - `labs/part10-measure-first/baseline-cpu.out` (untracked, được bảo toàn).
   - `labs/part10-measure-first/baseline.test.exe` (untracked, được bảo toàn).

---

## 4. Trạng thái Sẵn sàng

Toàn bộ các yêu cầu của Capstone Hardening Pass đã được giải quyết trọn vẹn trong một milestone duy nhất. Hệ thống mã nguồn, kịch bản sự cố, tài liệu kỹ thuật, và bản thảo sách PDF đều ở trạng thái hoàn thiện cao nhất, sẵn sàng commit và push lên remote `origin/main`.
