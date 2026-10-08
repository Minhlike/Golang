<!-- BOOK_ROLE: APPLICATION_SYSTEMS -->

# Chương 20 — Dự án tổng kết: opsprobe từ mã nguồn đến vận hành

Ở Chương 1, ta dùng một kết quả HTTP giả định để học cách đọc chương trình. Các chương sau lần lượt thêm request thật, deadline, đồng thời, lưu trữ và tín hiệu vận hành. Chương này ghép các phần ấy vào một công cụ thăm dò endpoint: khi một lượt probe thất bại, caller cần biết kết quả thuộc boundary nào và dữ liệu nào đã được lưu.

Dự án `projects/opsprobe/` là teaching vehicle có domain logic, worker pool giới hạn, SQLite, metrics, trace và HTTP API. Test tái lập những contract cụ thể, trong đó có tình huống quên đóng response body. Có implementation chạy được không đồng nghĩa công cụ đã sẵn sàng cho mọi môi trường production; phần bảo mật và triển khai dưới đây chỉ ra những giả định còn phải giữ.

Mental model của chương là: **một hệ thống Go trưởng thành không phải là một tập hợp các framework cồng kềnh, mà là sự khớp nối chính xác giữa các boundary kỹ thuật nhỏ: value semantics, error contract, áp suất đồng thời, tính nguyên tử của state, tín hiệu quan sát trung thực, và kỷ luật phát hành có trách nhiệm.**

## Bản đồ kiến trúc và hướng phụ thuộc

Mã nguồn của dự án nằm tại thư mục `projects/opsprobe/`. Các package tách những trách nhiệm sau:

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

`probe` và `store` không import `httpapi` hay `cmd`, nên có thể kiểm thử mà không khởi động toàn bộ ứng dụng. Điều đó không biến mọi test thành phép tính thuần: test I/O của `probe` dùng HTTP server cục bộ, còn test `store` cần database. Hướng import giúp tách boundary; fixture vẫn phải tái lập đúng hành vi cần kiểm tra.

## Năm trụ cột kỹ thuật của một hệ thống đáng tin

### 1. Phân loại kết quả và thời hạn ngữ cảnh

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

Phân biệt `OutcomeTimeout` với `OutcomeCancel` giúp caller giữ nguyên nhân kết thúc theo contract của lab. Nó không tự phân loại được root cause mạng hay chứng minh mọi cancellation đều là shutdown; cần correlation với lifecycle, deadline và observation khác.

Mỗi kết quả probe ghi nhận thời lượng bằng mili-giây (`DurationMs`) phục vụ dashboard và nano-giây (`DurationNs`) để tránh mất thông tin do làm tròn; đơn vị nano-giây không chứng minh đồng hồ đo chính xác đến nano-giây. Thời điểm ghi nhận run trong database phân biệt `StartedAt` (bắt đầu thực thi) và `CompletedAt` (kết thúc toàn bộ worker), tránh nhầm độ trễ một request với thời gian hoàn tất cả lô công việc.

### 2. Giới hạn đồng thời và áp suất ngược

Khi danh sách target tăng từ 10 lên 10.000, chạy `go p.ProbeSingle(...)` cho từng target có thể tạo áp lực lên bộ nhớ, socket và dịch vụ đích. Mức ảnh hưởng phụ thuộc workload và giới hạn môi trường; không suy ra hệ điều hành chắc chắn sẽ sập từ riêng số goroutine.

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

Gauge `opsprobe_active_workers` đếm worker goroutine đã khởi động và chưa thoát, qua `WorkerObserver`. Nó không đếm riêng worker đang xử lý target: một worker chờ việc vẫn nằm trong gauge. Muốn đo số thao tác đang diễn ra, cần metric khác với điểm tăng/giảm quanh từng thao tác.

Ở HTTP API, buffered channel semaphore giới hạn số đợt chạy đồng thời theo cấu hình. Khi hết slot, policy của lab từ chối thêm việc bằng `429 Too Many Requests`; giới hạn này là budget của ví dụ, chưa phải capacity đã được đo là an toàn cho production:

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

### 4. Vòng đời tài nguyên mạng: Thu hồi có giới hạn và điều kiện tái sử dụng

Caller phải luôn đóng `resp.Body`. Đọc đến EOF có thể giúp một số đường tái sử dụng kết nối, nhưng `Close` hay drain không bảo đảm reuse: Transport, protocol, server và trạng thái kết nối đều tham gia quyết định. Ngược lại, drain không giới hạn cần được cân nhắc khi target có thể trả body rất lớn hoặc không kết thúc.

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
	// Body nhỏ đã chạm EOF; không phải guarantee reuse.
	return err == nil && lr.N > 0
}
~~~

Quy tắc kỹ thuật ở đây rất rõ ràng:

Một là, đóng body trên đường kết thúc: hoàn tất trách nhiệm với response body theo contract. `Close` không đồng nghĩa mỗi lần phải đóng socket TCP; Transport có thể giữ connection để tái sử dụng.

Hai là, chọn budget 16 KiB: Đây là chính sách của lab, không phải thống kê kích thước body của các framework. Helper đọc thêm tối đa một byte để nhận biết body vượt budget, dùng `io.Discard` thay vì giữ toàn bộ body trong RAM.

Ba là, phát hiện cạn dòng (EOF): đọc tối đa `MaxDrainBytes + 1` phân biệt body nhỏ đã đọc hết với body vượt budget. Chỉ coi drain thành công khi phép đọc không có lỗi và `lr.N > 0`; lỗi đọc trước EOF không được diễn giải là thành công. Đây là quyết định budget của helper, không phải cờ đủ điều kiện reuse bên trong Transport. Đường tái sử dụng HTTP/1.x còn phụ thuộc body framing, server, lỗi kết nối và trạng thái Transport.

Bốn là, đánh đổi có chủ đích: Nếu body vượt quá 16 KiB, `lr.N` sẽ bằng 0. Lab ghi nhận body chưa được đọc hết và đóng body để giải phóng tài nguyên; không suy ra chắc chắn Transport sẽ hay sẽ không tái sử dụng một kết nối cụ thể.

Năm là, thời lượng probe phản ánh toàn bộ lifecycle: Đồng hồ đo thời lượng probe bắt đầu từ trước khi phát request tới sau khi quy trình cleanup/drain kết thúc. Nếu target trả về header 200 nhưng luồng body bị nghẽn (stall) vượt quá deadline, probe sẽ kết luận đúng là `OutcomeTimeout` thay vì báo nhầm `OutcomeSuccess`.

### 5. Ranh giới bảo mật, hợp đồng JSON và truy vết phân tán

Một công cụ vận hành chỉ an toàn khi các ranh giới ngoại vi được xác định rành mạch:

`opsprobe` giả định người vận hành và target registry được tin. Validation URL cú pháp không chặn đầy đủ SSRF. Nếu nhận input không tin cậy, cần policy target/egress, xử lý DNS và redirect theo threat model; không mặc định chặn mọi private IP vì công cụ nội bộ có thể cần truy cập đúng các endpoint ấy. Allowlist hoặc proxy cũng cần owner và cấu hình được kiểm chứng.

Về hợp đồng JSON di động: Trường `timeout_ms` trong request payload sử dụng kiểu số nguyên mili-giây (`0 <= timeout_ms <= 60000`), bảo đảm tương thích đa nền tảng thay vì parse cú pháp chuỗi duration của riêng Go.

Về phân tán ngữ cảnh (W3C TraceContext): Outbound probe request chèn header `traceparent` theo child span hiện tại. Để nối trace, dịch vụ nhận còn phải đọc context và cấu hình lấy mẫu/xuất span phù hợp; gửi header không tự chứng minh chuỗi quan sát xuyên dịch vụ đã đầy đủ.

## Bài tập chẩn đoán sự cố: Bão cạn kiệt Socket

Thư mục `projects/opsprobe/incident/` mô phỏng một sự cố kinh điển trong môi trường microservices.

### Kịch bản và Triệu chứng lâm sàng

> **Ghi chú phương pháp luận:** Đây là kịch bản giả định mô phỏng tình huống sự cố thực tế để đặt ra bài toán chẩn đoán cho kỹ sư.

Hệ thống probe giả định được triển khai để kiểm tra sức khỏe 50 microservices nội bộ.
- **Triệu chứng giám sát:** Tỷ lệ `OutcomeTimeout` tăng vọt và độ trễ chạm trần deadline (5 giây).
- **Phản nghiệm độc lập:** Kỹ sư kiểm tra trực tiếp từ máy trạm bằng lệnh cURL độc lập: target service vẫn phản hồi cực nhanh trong 2ms!
- **Tầng Hệ điều hành (`ss -s`):** Số lượng socket TCP mở tăng liên tục theo số lượng request mà không được thu hồi, tiệm cận giới hạn file descriptors (`ulimit -n`).
- **Tầng Transport Pool & Trace:** `http.Transport` không có kết nối rảnh (idle connection) nào được tái sử dụng giữa các lượt gọi. Hook `GotConnInfo.Reused` qua `net/http/httptrace` luôn ghi nhận `info.Reused == false`.

> **Dừng để điều tra và phản nghiệm.**
> 1. Dựa trên các triệu chứng trên (target phản hồi trong 2ms nhưng probe client cạn kiệt socket và timeout), hãy nêu 2 giả thuyết đối lập: Sự cố xuất phát từ máy chủ đích hay từ chính vòng đời kết nối của client?
> 2. Kỹ sư cần thiết kế thí nghiệm phản nghiệm (falsification test) nào để xác định chính xác nguyên nhân gốc rễ trong mã nguồn client trước khi can thiệp cấu hình hệ thống?

#### Đáp án — chỉ đọc sau khi đã tự làm
1. **Phân tích giả thuyết:**
   - *Giả thuyết A (Lỗi phía target/hạ tầng mạng):* Server đích bị treo hoặc tường lửa làm rớt gói tin. Giả thuyết này bị bác bỏ ngay lập tức bởi phép thử cURL độc lập: target service vẫn phản hồi cực nhanh trong 2ms.
   - *Giả thuyết B (Rò rỉ kết nối phía client):* Client mở socket mới cho mỗi lượt gọi nhưng không đưa kết nối trở lại pool của `http.Transport`. Khi tiệm cận giới hạn file descriptor hoặc socket, các request tiếp theo bị nghẽn ở khâu thiết lập kết nối (dial backlog), dẫn đến timeout trước khi kịp gửi dữ liệu.
2. **Thí nghiệm phản nghiệm:**
   - Gắn `net/http/httptrace` vào client để ghi nhận số kết nối mở mới vs tái sử dụng (`GotConnInfo.Reused`).
   - Kiểm tra mã nguồn xử lý HTTP response: trong HTTP/1.x của Go, một kết nối TCP chỉ được `http.Transport` đưa vào pool tái sử dụng (keep-alive) khi và chỉ khi response body được đọc hết (drain) và đóng tường minh qua `resp.Body.Close()`.

### Bằng chứng mã nguồn và Đo đạc thực nghiệm

Kiểm tra `incident/incident.go` (đoạn hàm `BuggyProbe`):

~~~go
resp, err := client.Do(req)
if err != nil {
	return 0, false, err
}
// BUG: Quên gọi resp.Body.Close()!
return resp.StatusCode, false, nil
~~~

Trong kịch bản HTTP/1.x của lab, hàm trả về mà không đọc hết hoặc đóng body. Kết nối đang giữ body chưa hoàn tất không được tái sử dụng cho request khác; tải tiếp tục có thể làm tăng số kết nối. Không áp kết luận này nguyên xi cho cơ chế multiplexing của HTTP/2.

### Bằng chứng đo đạc thực nghiệm

Trong fixture 20 request tuần tự tới server kiểm thử ở `incident/incident_test.go`, `httptrace` ghi nhận các số đếm sau. Chúng mô tả đúng fixture này, không dự đoán tỷ lệ tái sử dụng kết nối của mọi server hay workload:

| Chỉ số thực nghiệm | BuggyProbe (Bỏ quên Close) | FixedProbe (Close + Drain 16 KiB) |
| --- | --- | --- |
| **New Conns (`Reused == false`)** | **20** | **1** (trong fixture này) |
| **Reused Conns (`Reused == true`)** | **0** | **19** (trong fixture này) |
| **Kết quả vận hành** | Mỗi request mở socket mới | Tái sử dụng socket trong pool |

Kiểm thử `TestIncident_BoundedDrainOversizedBody` xác nhận rằng với body 32 KiB (vượt giới hạn 16 KiB), lab trả `reusedEligible == false` và đóng body. Bounded drain giới hạn lượng dữ liệu mà client chủ động đọc bỏ; nó không phải cơ chế chống tràn bộ đệm hay bảo đảm một kết nối được tái sử dụng.

## Đóng gói, điều phối và chuyển giao có trách nhiệm

Để đưa `opsprobe` ra môi trường production, ta áp dụng toàn bộ các nguyên tắc đã học ở Chương 17 và 18:

Một là, Dockerfile nhiều giai đoạn (multi-stage): lab xây binary với `CGO_ENABLED=0`, rồi dùng base image `gcr.io/distroless/static-debian12:nonroot` và tài khoản không đặc quyền (`USER 65532:65532`). Với dependency thuần Go của lab, cách này không yêu cầu C runtime; không suy rộng thành bảo đảm mọi chương trình đều không có dependency ngoài binary.

Hai là, lab dùng một Pod và một file SQLite, với `replicas: 1`, PVC `ReadWriteOnce` và chiến lược `Recreate`. RWO giới hạn ghi theo node, không phải theo Pod; nhiều Pod trên cùng node vẫn có thể mount volume. SQLite có cơ chế khóa cho nhiều connection/process, nên không phải cứ hai process là dữ liệu mất nhất quán. Rủi ro tăng khi chia sẻ file qua filesystem có semantics khóa/sync không phù hợp. `Recreate` hạn chế chồng lấn rollout thông thường, không phải distributed lock hay fencing khi node lỗi. Nếu cần nhiều writer trên các node, ưu tiên database client-server như PostgreSQL, hoặc thiết kế một owner duy nhất cho SQLite cùng contract failover rõ ràng.

Ba là, cấu hình lúc khởi động qua ConfigMap: Concurrency, timeout, backpressure limit và log level được nạp từ `deploy/k8s/configmap.yaml` vào biến môi trường (`OPSPROBE_*`). Sửa ConfigMap không tự cập nhật biến môi trường của process đang chạy; cần tạo lại Pod hoặc thiết kế cơ chế đọc lại riêng.

Bốn là, ghim nội dung image trong CI/CD: policy của dự án yêu cầu manifest dùng digest (`image: ghcr.io/...@sha256:...`) đã được pipeline kiểm chứng. Cách này không phụ thuộc việc tag như `:latest` có bị trỏ sang image khác hay không; digest tự nó không chứng minh image đáng tin, đúng platform hoặc còn được registry lưu giữ.

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

## Cột mốc hoàn thành dự án tổng kết: Chốt mốc chuẩn hệ thống

Capstone ghép các proof nhỏ: value và aliasing, đồng bộ goroutine, body lifecycle, transaction và artifact identity. Mỗi proof có phạm vi riêng; transaction không giải quyết mọi external side effect, shutdown có deadline và có thể không hoàn tất mọi request, còn digest không chứng minh nội dung artifact đúng. Khi chuyển sang môi trường thật, giữ những giới hạn ấy trong test và observation.

Khi mở rộng công cụ, hãy giữ các contract này thành tiêu chí review: input nào được tin, tài nguyên nào có owner, side effect nào có thể lặp, và observation nào xác nhận kết quả. Chương 21 dùng chính các câu hỏi ấy cho một controller.

Việc hoàn thành dự án `opsprobe` chốt lại baseline vững chắc của cuốn sách sống (*living textbook*), đồng thời mở ra những bài toán hệ thống ở quy mô hạ tầng cao hơn: khi hệ thống không chỉ thăm dò thụ động mà cần liên tục tự điều hòa, dung hòa sai lệch giữa trạng thái mong muốn và thực tế để tự phục hồi.

@references
1. Go Team. The Go Programming Language Specification: memory model, concurrency semantics, channels và types. go.dev/ref/spec
2. Go Team. Package `net/http`: Client, Transport, Request and Response lifecycle. pkg.go.dev/net/http
3. Go Team. Package `database/sql`: connection pooling, transactions, prepared statements. pkg.go.dev/database/sql
4. Go Team. Package `log/slog`: Structured Logging in Go. pkg.go.dev/log/slog
5. Prometheus Authors. Prometheus Go client library documentation. prometheus.io/docs/guides/go-application/
6. OpenTelemetry Authors. OpenTelemetry Go Documentation and Tracing API. opentelemetry.io/docs/languages/go/
7. Google Container Tools. Distroless Container Images. github.com/GoogleContainerTools/distroless
