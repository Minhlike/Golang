<!-- BOOK_ROLE: APPLICATION_SYSTEMS -->

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
│   └── httpapi/           # REST API, backpressure, health
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

Mỗi kết quả probe ghi nhận đồng thời cả thời lượng tính bằng mili-giây (`DurationMs`) phục vụ dashboard và nano-giây (`DurationNs`) cho độ chính xác cao. Thời điểm ghi nhận run trong database phân định rành mạch giữa `StartedAt` (bắt đầu thực thi) và `CompletedAt` (kết thúc toàn bộ worker), tránh nhầm lẫn giữa độ trễ của từng request đơn lẻ với thời gian hoàn tất của cả lô công việc.

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

Để phản ánh chính xác số worker đang thực sự xử lý công việc mà không suy đoán, `probe.Pool` tích hợp interface `WorkerObserver`. Khi một worker goroutine khởi động và thoát ra, nó thông báo trực tiếp cho hệ thống telemetry cập nhật gauge `opsprobe_active_workers`.

Trên tầng HTTP API, ta áp dụng cơ chế áp suất ngược (backpressure) thông qua buffered channel semaphore. Khi số lượng đợt chạy đồng thời vượt quá ngưỡng an toàn, API lập tức từ chối nhận thêm việc với mã `429 Too Many Requests`:

~~~go
select {
case a.runSem <- struct{}{}:
	defer func() { <-a.runSem }()
default:
	a.tel.RunsTotal.WithLabelValues(
		"rejected_backpressure").Inc()
	a.writeJSON(
		w, http.StatusTooManyRequests,
		map[string]string{
			"error": "too many runs, backpressure applied",
		},
	)
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

Để kiểm chứng tính toàn vẹn của transaction một cách tất định (deterministic) mà không dựa vào thời điểm ngẫu nhiên, schema cơ sở dữ liệu được trang bị ràng buộc `CHECK (status_code >= 0)`. Trong kiểm thử tự động, ta cố tình truyền một kết quả có `status_code = -1` ở bản ghi thứ hai sau khi bản ghi cha đã được chèn. Database lập tức từ chối, transaction rollback toàn bộ, và lệnh đếm số dòng xác nhận cả hai bảng đều không lưu lại bất kỳ dữ liệu rác nào.

### 4. Vòng đời tài nguyên mạng: Bounded Drain và Điều kiện Tái sử dụng

Một trong những sai lầm phổ biến nhất khi viết network client trong Go là ngộ nhận rằng việc chỉ gọi `resp.Body.Close()` là đủ để socket TCP được tái sử dụng. Ngược lại, việc dùng `io.Copy(io.Discard, resp.Body)` mà không giới hạn độ dài lại mở ra nguy cơ bị tấn công cạn kiệt tài nguyên khi gặp target trả về stream vô hạn.

`opsprobe` thiết lập chính sách bounded drain có kiểm soát:

~~~go
const MaxDrainBytes = 16384 // 16 KiB

func drainResponseBody(body io.ReadCloser) bool {
	if body == nil {
		return false
	}
	defer body.Close()

	lr := &io.LimitedReader{R: body, N: MaxDrainBytes + 1}
	_, err := io.Copy(io.Discard, lr)
	// Chỉ đủ điều kiện tái sử dụng khi đã đọc cạn tới EOF
	return err == nil && lr.N > 0
}
~~~

Quy tắc kỹ thuật ở đây rất rõ ràng:

Một là, luôn đóng body (`defer body.Close()`): Giải phóng file descriptor socket ngay cả khi xảy ra lỗi giữa chừng.

Hai là, đọc tối đa 16 KiB: Đủ rộng để xử lý phần lớn body thông điệp sức khỏe hoặc trang lỗi nhỏ của các web framework mà không nạp toàn bộ vào RAM.

Ba là, phát hiện cạn dòng (EOF): Bằng cách đặt giới hạn đọc là `MaxDrainBytes + 1`, nếu `lr.N > 0` nghĩa là luồng đã chạm `io.EOF` trước khi vượt quá 16 KiB. Khi đó và chỉ khi đó, socket mới được đánh dấu đủ điều kiện tái sử dụng (`reused_eligible = true`). Lưu ý rằng đây là điều kiện cần trên tầng stream HTTP/1.x, không phải bảo đảm tuyệt đối của mọi tầng Transport.

Bốn là, đánh đổi có chủ đích: Nếu body vượt quá 16 KiB, `lr.N` sẽ bằng 0. Hệ thống phát hiện luồng bị cắt ngắn và chấp nhận rằng kết nối TCP này không thể tái sử dụng an toàn trên HTTP/1.1; socket sẽ bị đóng để ưu tiên an toàn bộ nhớ.

Năm là, thời lượng probe phản ánh toàn bộ lifecycle: Đồng hồ đo thời lượng probe bắt đầu từ trước khi phát request tới sau khi quy trình cleanup/drain kết thúc. Nếu target trả về header 200 nhưng luồng body bị nghẽn (stall) vượt quá deadline, probe sẽ kết luận đúng là `OutcomeTimeout` thay vì báo nhầm `OutcomeSuccess`.

### 5. Ranh giới Bảo mật, Hợp đồng JSON và Distributed Tracing

Một công cụ vận hành chỉ an toàn khi các ranh giới ngoại vi được xác định rành mạch:

Về mô hình đe dọa (Threat Model): `opsprobe` được thiết kế như công cụ chẩn đoán nội bộ (trusted-operator diagnostic tool). Việc kiểm tra URL trong mã nguồn là validation cú pháp cơ bản, **không thay thế được cơ chế chống SSRF toàn diện**. Khi triển khai nhận input từ ngoài, hệ thống bắt buộc phải có network policy chặn các dải Private IP hoặc đặt sau egress proxy.

Về hợp đồng JSON di động: Trường `timeout_ms` trong request payload sử dụng kiểu số nguyên mili-giây (`0 <= timeout_ms <= 60000`), bảo đảm tương thích đa nền tảng thay vì parse cú pháp chuỗi duration của riêng Go.

Về phân tán ngữ cảnh (W3C TraceContext): Outbound probe request tự động chèn header `traceparent` theo child span hiện tại, bảo đảm chuỗi quan sát phân tán không bị đứt gãy giữa các dịch vụ.

## Bài tập chẩn đoán sự cố: Bão cạn kiệt Socket

Thư mục `projects/opsprobe/incident/` mô phỏng một sự cố kinh điển trong môi trường microservices.

### Kịch bản mô phỏng sư phạm (Scenario Narrative)

> **Ghi chú phương pháp luận:** Đây là kịch bản giả định mô phỏng tình huống sự cố thực tế để đặt ra bài toán chẩn đoán cho kỹ sư.

Hệ thống probe giả định được triển khai để kiểm tra sức khỏe 50 microservices nội bộ. Khi tải tăng cao, hệ thống giám sát ghi nhận tỷ lệ `OutcomeTimeout` tăng vọt và độ trễ chạm trần deadline. Tuy nhiên, khi kỹ sư kiểm tra trực tiếp từ máy trạm bằng lệnh cURL độc lập, target service vẫn phản hồi trong 2ms. Kiểm tra trạng thái hệ điều hành cho thấy số lượng socket TCP mở tăng liên tục, tiệm cận giới hạn file descriptors (`ulimit -n`).

### Bốn tầng bằng chứng chẩn đoán

Thứ nhất ở tầng Hệ điều hành: `ss -s` ghi nhận số lượng socket mở tăng liên tục theo số lượng request mà không được thu hồi.

Thứ hai ở tầng Transport Pool: `http.Transport` không có kết nối rảnh (idle connection) nào được tái sử dụng giữa các lượt gọi.

Thứ ba ở tầng Runtime Trace: Sử dụng `net/http/httptrace` với hook `GotConnInfo.Reused`. Kết quả cho thấy `info.Reused` luôn bằng `false`.

Thứ tư ở tầng Mã nguồn: Kiểm tra `incident/incident.go` (đoạn hàm `BuggyProbe`):

~~~go
resp, err := client.Do(req)
if err != nil {
	return 0, false, err
}
// BUG: Quên gọi resp.Body.Close()!
return resp.StatusCode, false, nil
~~~

Lập trình viên đã return mà quên đóng body. Kết nối TCP bị giữ ở trạng thái "đang đọc dở", khiến connection pool bị phong tỏa và buộc mỗi request sau phải mở một socket mới.

### Bằng chứng đo đạc thực nghiệm (Empirical Measurements)

Khác với phần mô tả giả định ở trên, kiểm thử tự động tại `incident/incident_test.go` cung cấp số liệu thực nghiệm đo đạc chính xác qua `httptrace`:

| Chỉ số thực nghiệm | BuggyProbe (Bỏ quên Close) | FixedProbe (Close + Drain 16 KiB) |
| --- | --- | --- |
| **New Conns (`Reused == false`)** | **20** | **1** (chỉ kết nối đầu tiên) |
| **Reused Conns (`Reused == true`)** | **0** | **19** (95% tái sử dụng) |
| **Kết quả vận hành** | Mỗi request mở socket mới | Tái sử dụng socket trong pool |

Kiểm thử `TestIncident_BoundedDrainOversizedBody` đồng thời chứng minh rằng khi payload trả về là 32 KiB (vượt giới hạn 16 KiB), hệ thống xác định chính xác `reusedEligible == false` và đóng kết nối, bảo vệ bộ nhớ tiến trình khỏi nguy cơ tràn đệm.

## Đóng gói, Điều phối và Delivery có trách nhiệm

Để đưa `opsprobe` ra môi trường production, ta áp dụng toàn bộ các nguyên tắc đã học ở Chương 17 và 18:

Một là, Multi-Stage Dockerfile: Biên dịch tĩnh hoàn toàn với `CGO_ENABLED=0` và sử dụng base image tối giản `gcr.io/distroless/static-debian12:nonroot`, chạy dưới tài khoản không đặc quyền (`USER 65532:65532`).

Hai là, ranh giới lưu trữ và số lượng Pod trong Kubernetes: Manifest `deploy/k8s/deployment.yaml` thiết lập `replicas: 1` kết hợp PersistentVolumeClaim `opsprobe-data-pvc` (`ReadWriteOnce`). Do SQLite là cơ sở dữ liệu file cục bộ, việc chạy nhiều pod đồng thời trên cùng một file dữ liệu sẽ gây tranh chấp khóa và không nhất quán state. Chiến lược triển khai sử dụng `strategy: Recreate` để bảo đảm pod cũ nhả volume trước khi pod mới được gắn. Khi hệ thống có nhu cầu mở rộng quy mô ngang (`replicas > 1`), tầng `store` phải được chuyển sang hệ quản trị cơ sở dữ liệu máy khách - máy chủ (client-server) như PostgreSQL.

Ba là, cấu hình động qua ConfigMap: Các tham số giới hạn như concurrency, timeout, backpressure limit và log level được nạp từ `deploy/k8s/configmap.yaml` vào biến môi trường của container (`OPSPROBE_*`).

Bốn là, định danh bất biến trong CI/CD: Trong manifest Kubernetes thực tế, image phải được gán digest bất biến sha256 (`image: ghcr.io/...@sha256:...`) đã được kiểm chứng bởi pipeline CI/CD, loại bỏ hoàn toàn các tag trôi nổi rủi ro như `:latest`.

## Lệnh kiểm thử và vận hành hệ thống

Anh có thể trực tiếp chạy và kiểm chứng toàn bộ năng lực của `opsprobe` trong terminal:

~~~powershell
cd projects/opsprobe

# 1. Chạy test suite có race detector
go test -race ./...

# 2. Chạy CLI kiểm tra URL đơn lẻ
go run ./cmd/opsprobe `
  --oneshot-url=https://go.dev --timeout=2s

# 3. Khởi chạy HTTP daemon server
go run ./cmd/opsprobe --addr=127.0.0.1:8080 `
  --db=opsprobe.db --concurrency=4
~~~

Trong cửa sổ khác, gửi yêu cầu probe và thu thập metrics:

~~~powershell
$target = '{"id":"t1","url":"http://127.0.0.1:8080/livez"}'
curl -X POST http://127.0.0.1:8080/runs `
  -H "Content-Type: application/json" `
  -d "{`"targets`":[$target]}"
curl http://127.0.0.1:8080/metrics
~~~

## Cột mốc hoàn thành Capstone: Chốt baseline hệ thống

Khi bước vào dự án Capstone, một chương trình Go không còn là những tệp mã nguồn rời rạc hay hàm `fmt.Println` đơn lẻ. Ta nhìn thấy toàn bộ chiều sâu kỹ thuật đan kết trong một hệ thống vận hành hoàn chỉnh: một giá trị di chuyển qua bộ nhớ theo value hay pointer semantics; một goroutine được đánh thức bởi scheduler và phối hợp an toàn qua channel; một kết nối TCP được mượn từ pool, đọc cạn dữ liệu và hoàn trả nguyên vẹn; một transaction bảo đảm cơ sở dữ liệu không bao giờ chứa trạng thái dở dang; một tín hiệu OS dừng tiến trình êm ái mà không làm rơi rớt dữ liệu; và một artifact bất biến được định danh bằng digest nội dung, kiểm soát bởi các chốt chặn tự động trước khi bước vào production.

Đó chính là ranh giới giữa một người biết cú pháp ngôn ngữ và một kỹ sư phần mềm thực thụ: **hiểu rõ cái giá của từng quyết định thiết kế và chịu trách nhiệm đến cùng cho sự vận hành của hệ thống.**

Việc hoàn thành dự án `opsprobe` chốt lại baseline vững chắc của cuốn sách sống (*living textbook*), đồng thời mở ra những bài toán hệ thống ở quy mô hạ tầng cao hơn: khi hệ thống không chỉ thăm dò thụ động mà cần liên tục tự điều hòa, dung hòa sai lệch giữa trạng thái mong muốn và thực tế để tự phục hồi.

@references
1. Go Team. The Go Programming Language Specification: memory model, concurrency semantics, channels và types. go.dev/ref/spec
2. Go Team. Package `net/http`: Client, Transport, Request and Response lifecycle. pkg.go.dev/net/http
3. Go Team. Package `database/sql`: connection pooling, transactions, prepared statements. pkg.go.dev/database/sql
4. Go Team. Package `log/slog`: Structured Logging in Go. pkg.go.dev/log/slog
5. Prometheus Authors. Prometheus Go client library documentation. prometheus.io/docs/guides/go-application/
6. OpenTelemetry Authors. OpenTelemetry Go Documentation and Tracing API. opentelemetry.io/docs/languages/go/
7. Google Container Tools. Distroless Container Images. github.com/GoogleContainerTools/distroless
