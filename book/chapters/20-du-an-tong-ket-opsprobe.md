# Chương 20 — Dự án tổng kết: opsprobe từ mã nguồn đến vận hành

Một chương trình Go không bắt đầu bằng Kubernetes hay kiến trúc microservice phức tạp. Nó bắt đầu từ một câu hỏi thực tế rất khiêm tốn: một endpoint dependency của hệ thống hiện còn sống không, và nếu nó chết thì chết ở chặng nào? Ở Chương 1, ta đã viết những dòng lệnh đầu tiên để đọc một URL. Trải qua mười chín chương, câu hỏi ấy dần được đặt vào những áp lực khắc nghiệt nhất của thực tế: áp lực đồng thời, ranh giới lỗi, tính nguyên tử của dữ liệu, rò rỉ socket mạng, khả năng quan sát không suy đoán, và kỷ luật phát hành an toàn ra production.

Chương này là điểm hội tụ của toàn bộ hành trình: **xây dựng hoàn chỉnh hệ thống `opsprobe`**. Đây không phải là một bài tập giả lập với các mock rỗng, mà là một hệ thống phần mềm có đầy đủ domain logic, worker pool bị chặn, kho lưu trữ giao dịch nguyên tử SQLite, telemetry Prometheus và OpenTelemetry, HTTP API có backpressure, container distroless non-root, và kịch bản ứng cứu sự cố rò rỉ tài nguyên mạng được chứng minh bằng thực nghiệm.

Mental model của chương là: **một hệ thống Go trưởng thành không phải là một tập hợp các framework cồng kềnh, mà là sự khớp nối chính xác giữa các boundary kỹ thuật nhỏ: value semantics, error contract, áp suất đồng thời, tính nguyên tử của state, tín hiệu quan sát trung thực, và kỷ luật phát hành có trách nhiệm.**

## Bản đồ kiến trúc và hướng phụ thuộc

Mã nguồn hoàn chỉnh của dự án nằm tại thư mục `projects/opsprobe/`. Ta tổ chức hệ thống theo nguyên tắc phân tách ranh giới rõ ràng, bảo đảm các tầng lõi không bị ô nhiễm bởi các chi tiết vận hành bên ngoài:

~~~
projects/opsprobe/
├── cmd/opsprobe/          # CLI oneshot và HTTP daemon
├── internal/
│   ├── probe/             # Bounded concurrency pool, Outcome
│   ├── store/             # SQLite, transaction nguyên tử
│   ├── telemetry/         # slog JSON, Prometheus, OTel
│   └── httpapi/           # REST API, backpressure, health check
├── incident/              # Kịch bản sự cố rò rỉ socket TCP
├── deploy/                # Dockerfile, Kubernetes, Terraform
└── scenarios_test.go      # Kiểm thử 6 kịch bản sự cố
~~~

@table Phân tách trách nhiệm và ranh giới contract trong opsprobe

| Package | Trách nhiệm vận hành | Contract bảo vệ |
| --- | --- | --- |
| `probe` | Kiểm tra target, phân loại kết quả. | Giới hạn worker, outcome rõ, đóng stream. |
| `store` | Lưu trữ metadata và kết quả probe. | Giao dịch nguyên tử qua `database/sql`. |
| `telemetry` | Ghi nhận log, metrics và trace. | Không đoán mò, đo lường đúng nhãn outcome. |
| `httpapi` | Nhận request, điều phối, trả JSON. | Backpressure 429, readiness, graceful drain. |
| `cmd` | Điểm khởi đầu (Composition Root). | Parse cờ, bắt tín hiệu OS, graceful shutdown. |

Đặc điểm quan trọng nhất của kiến trúc này là **hướng phụ thuộc một chiều (unidirectional dependency)**: `probe` và `store` hoàn toàn độc lập, không import `httpapi` hay `cmd`. Điều này cho phép ta kiểm thử riêng rẽ từng năng lực lõi bằng unit test thuần túy mà không cần dựng HTTP server hay giả lập môi trường mạng phức tạp.

## Bốn trụ cột kỹ thuật của một hệ thống đáng tin

### 1. Phân loại kết quả (Outcome Classification) và Context Deadline

Trong vận hành, biết một thao tác thất bại là chưa đủ; ta cần biết nó thất bại vì lý do gì. Trả về một giá trị boolean `false` hay một chuỗi lỗi mơ hồ sẽ xóa sạch thông tin quý giá. Trong `internal/probe/probe.go`, mỗi lần probe được phân loại rành mạch thành một trong bốn `Outcome`:

~~~go
type Outcome string

const (
	OutcomeSuccess Outcome = "success"
	OutcomeFailure Outcome = "failure"
	OutcomeTimeout Outcome = "timeout"
	OutcomeCancel  Outcome = "cancel"
)
~~~

Khi gửi request, ta gắn deadline chặt chẽ cho từng target:

~~~go
targetTimeout := p.defaultTimeout
if target.Timeout > 0 {
	targetTimeout = target.Timeout
}
probeCtx, cancel := context.WithTimeout(ctx, targetTimeout)
defer cancel()

req, err := http.NewRequestWithContext(
	probeCtx, method, target.URL, nil)
~~~

Sự phân biệt giữa `OutcomeTimeout` (hết thời gian chờ từ chối phục vụ) và `OutcomeCancel` (tiến trình cha chủ động hủy đợt kiểm tra) giúp đội ngũ SRE không bao giờ nhầm lẫn giữa sự cố quá tải mạng và hành vi shutdown bình thường của hệ thống.

### 2. Đồng thời có kiểm soát (Bounded Concurrency) và Áp suất ngược

Khi danh sách target tăng từ 10 lên 10.000, một chương trình ngây thơ sẽ chạy `go p.ProbeSingle(...)` cho từng target. Cách làm này sẽ tạo ra hàng chục nghìn goroutine, làm cạn kiệt socket và gây sập hệ điều hành.

`opsprobe` sử dụng mô hình worker pool với số lượng goroutine cố định:

~~~go
numWorkers := p.concurrency
if numWorkers > n {
	numWorkers = n
}

var wg sync.WaitGroup
for w := 0; w < numWorkers; w++ {
	wg.Add(1)
	go func() {
		defer wg.Done()
		for j := range jobs {
			if ctx.Err() != nil {
				results[j.index] = Result{
					TargetID: j.target.ID,
					Outcome:  OutcomeCancel,
				}
				continue
			}
			results[j.index] = p.ProbeSingle(ctx, j.target)
		}
	}()
}
wg.Wait()
~~~

Trên tầng HTTP API, ta áp dụng cơ chế áp suất ngược (backpressure) thông qua buffered channel semaphore. Khi số lượng đợt chạy đồng thời vượt quá ngưỡng an toàn, API lập tức từ chối nhận thêm việc với mã `429 Too Many Requests`:

~~~go
select {
case a.runSem <- struct{}{}:
	defer func() { <-a.runSem }()
default:
	a.tel.RunsTotal.WithLabelValues(
		"rejected_backpressure").Inc()
	a.writeJSON(w, http.StatusTooManyRequests, map[string]string{
		"error": "too many concurrent runs, backpressure applied",
	})
	return
}
~~~

### 3. Giao dịch nguyên tử trên SQLite: Hoặc toàn bộ, hoặc không có gì

Dữ liệu lưu trữ chỉ có giá trị khi nó phản ánh đúng trạng thái nhất quán của thế giới thực. Nếu một đợt chạy gồm 10 target, hệ thống không được phép rơi vào trạng thái: lưu thành công 5 target đầu rồi crash, bỏ lại 5 target sau và làm lệch báo cáo tổng hợp.

Trong `internal/store/store.go`, toàn bộ bản ghi đợt chạy (`runs`) và các kết quả probe (`probe_results`) được thực thi bên trong một transaction duy nhất qua `database/sql`:

~~~go
tx, err := s.db.BeginTx(ctx, nil)
if err != nil {
	return fmt.Errorf("begin transaction: %w", err)
}
defer tx.Rollback() // An toàn: no-op nếu Commit đã thành công

// 1. Chèn bản ghi đợt chạy (runs)
_, err = tx.ExecContext(ctx, insertRunQuery, run.ID, ...)
if err != nil {
	return fmt.Errorf("insert run: %w", err)
}

// 2. Chèn từng kết quả probe bằng prepared statement
stmt, err := tx.PrepareContext(ctx, insertResultQuery)
if err != nil {
	return err
}
defer stmt.Close()

for _, r := range results {
	_, err = stmt.ExecContext(ctx, run.ID, r.TargetID, ...)
	if err != nil {
		return err // defer tx.Rollback() sẽ hủy toàn bộ
	}
}

return tx.Commit()
~~~

Nhờ cơ chế `defer tx.Rollback()`, nếu có bất kỳ lỗi I/O nào xảy ra hoặc context bị hủy ngang trước khi `tx.Commit()` được gọi, cơ sở dữ liệu sẽ quay về trạng thái sạch ban đầu, không để lại bất kỳ bản ghi mồ côi nào.

### 4. Vòng đời tài nguyên mạng: Bài học về việc tái sử dụng kết nối

Một trong những cạm bẫy lớn nhất khi viết network client bằng Go là việc quản lý `http.Response.Body`. Nếu chỉ gọi `resp.Body.Close()` mà không đọc cạn dữ liệu còn thừa trên dây mạng, `http.Transport` không thể tái sử dụng kết nối TCP đó cho các request tiếp theo.

~~~go
resp, err := p.client.Do(req)
if err != nil {
	return res
}
defer resp.Body.Close()

// Đọc cạn tối đa 8KB dữ liệu thừa để hoàn trả socket về pool
_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, 8192))
~~~

Đoạn mã ngắn trên tạo ra sự khác biệt giữa một service chạy ổn định quanh năm và một service bị sập sau 20 phút do cạn kiệt socket file descriptors.

## Bài tập chẩn đoán sự cố: Bão cạn kiệt Socket

Thư mục `projects/opsprobe/incident/` mô phỏng một sự cố kinh điển trong môi trường microservices.

### Hiện tượng sự cố

Hệ thống probe đang chạy bình thường thì Prometheus đồng loạt phát cảnh báo: tỷ lệ `OutcomeTimeout` tăng vọt lên 90%, thời gian phản hồi chạm ngưỡng kịch trần. Tuy nhiên, các kỹ sư phụ trách target service khẳng định dịch vụ của họ hoàn toàn khỏe mạnh; kiểm tra bằng cURL chỉ mất 2ms. Lệnh `netstat` trên máy chủ probe cho thấy hàng nghìn socket TCP ở trạng thái treo.

### Bốn tầng bằng chứng chẩn đoán

1. **Tầng Hệ điều hành:** `ss -s` ghi nhận số lượng socket mở liên tục tăng tuyến tính và chạm ngưỡng `ulimit -n`.
2. **Tầng Transport Pool:** `http.Transport` không có kết nối rảnh (idle connection) nào để tái sử dụng.
3. **Tầng Runtime Trace:** Sử dụng `net/http/httptrace` với hook `GotConnInfo.Reused`. Kết quả cho thấy `info.Reused` luôn bằng `false`.
4. **Tầng Mã nguồn:** Kiểm tra `incident/incident.go` (đoạn hàm `BuggyProbe`):

~~~go
resp, err := client.Do(req)
if err != nil {
	return 0, err
}
// BUG: Quên gọi resp.Body.Close()!
return resp.StatusCode, nil
~~~

Lập trình viên đã return mà quên đóng body. Kết nối TCP bị giữ treo vĩnh viễn ở trạng thái "đang đọc dở", khiến pool bị phong tỏa và buộc mỗi request sau phải mở một socket mới cho đến khi hệ điều hành cạn kiệt tài nguyên.

Chạy kịch bản kiểm chứng thực nghiệm tại `incident/`:

~~~powershell
cd projects/opsprobe
go test -v ./incident
~~~

Kết quả cho thấy sự chênh lệch rõ rệt:
- `BuggyProbe`: 20 request tạo ra 20 kết nối mới (`NewConns=20, ReusedConns=0`).
- `FixedProbe`: 20 request chỉ tạo duy nhất 1 kết nối ban đầu và tái sử dụng 19 lần còn lại (`NewConns=1, ReusedConns=19`).

## Đóng gói, Điều phối và Delivery có trách nhiệm

Để đưa `opsprobe` ra môi trường production, ta áp dụng toàn bộ các nguyên tắc đã học ở Chương 17 và 18:

1. **Multi-Stage Dockerfile:** Biên dịch tĩnh hoàn toàn với `CGO_ENABLED=0` và sử dụng base image tối giản `gcr.io/distroless/static-debian12:nonroot`, chạy dưới tài khoản không đặc quyền (`USER 65532:65532`).
2. **Kubernetes Desired State:** Manifest `deploy/k8s/deployment.yaml` kích hoạt `readOnlyRootFilesystem: true`, gán liveness probe tại `/livez` và readiness probe tại `/readyz`.
3. **Fail-Closed Gate trong CI/CD:** Tuyệt đối không deploy bằng tag trôi nổi `:latest`. Mọi thay đổi phải đi qua promotion gate bằng Go kiểm tra tính toàn vẹn của OCI manifest digest và provenance chữ ký số. Nếu thiếu bằng chứng, pipeline lập tức dừng lại theo nguyên tắc fail-closed.

## Lệnh kiểm thử và vận hành hệ thống

Anh có thể trực tiếp chạy và kiểm chứng toàn bộ năng lực của `opsprobe` trong terminal:

~~~powershell
cd projects/opsprobe

# 1. Chạy toàn bộ test suite và kiểm tra race condition
go test -v ./...
go test -race ./...
go vet ./...

# 2. Chạy CLI kiểm tra một URL đơn lẻ
go run ./cmd/opsprobe --oneshot-url=https://go.dev --timeout=2s

# 3. Khởi chạy HTTP daemon server
go run ./cmd/opsprobe --addr=:8080 --db=opsprobe.db --concurrency=4
~~~

Trong một cửa sổ terminal khác, gửi yêu cầu kiểm tra hàng loạt endpoint và xem metrics Prometheus:

~~~powershell
# Gửi yêu cầu probe qua REST API
curl -X POST http://localhost:8080/runs `
  -H "Content-Type: application/json" `
  -d '{"targets":[{"id":"t1","url":"http://localhost:8080/livez"}]}'

# Thu thập metrics Prometheus
curl http://localhost:8080/metrics
~~~

## Điểm dừng: khi một kỹ sư nhìn một hệ thống Go

Khi bắt đầu cuốn sách, một chương trình Go có thể chỉ là một tệp `main.go` với hàm `fmt.Println`. Khi kết thúc cuốn sách, ta nhìn thấy toàn bộ thế giới phía sau dòng chữ đó:
- Một giá trị di chuyển qua bộ nhớ theo value hay pointer semantics.
- Một goroutine được đánh thức bởi scheduler và phối hợp an toàn qua channel.
- Một kết nối socket TCP được mượn từ pool, đọc cạn dữ liệu và trả về nguyên vẹn.
- Một transaction bảo đảm cơ sở dữ liệu không bao giờ chứa trạng thái dở dang.
- Một tín hiệu OS dừng tiến trình một cách êm ái mà không làm rơi rớt dữ liệu của người dùng.
- Một artifact bất biến được định danh bằng digest nội dung và được kiểm soát bởi các chốt chặn tự động trước khi bước chân vào môi trường production.

Đó chính là ranh giới giữa một người biết cú pháp ngôn ngữ và một kỹ sư phần mềm thực thụ: **hiểu rõ cái giá của từng quyết định thiết kế và chịu trách nhiệm đến cùng cho sự vận hành của hệ thống.**

@references
1. Go Team. The Go Programming Language Specification: memory model, concurrency semantics, channels và types. go.dev/ref/spec
2. Go Team. Package `net/http`: Client, Transport, Request and Response lifecycle. pkg.go.dev/net/http
3. Go Team. Package `database/sql`: connection pooling, transactions, prepared statements. pkg.go.dev/database/sql
4. Go Team. Package `log/slog`: Structured Logging in Go. pkg.go.dev/log/slog
5. Prometheus Authors. Prometheus Go client library documentation. prometheus.io/docs/guides/go-application/
6. OpenTelemetry Authors. OpenTelemetry Go Documentation and Tracing API. opentelemetry.io/docs/languages/go/
7. Google Container Tools. Distroless Container Images. github.com/GoogleContainerTools/distroless
