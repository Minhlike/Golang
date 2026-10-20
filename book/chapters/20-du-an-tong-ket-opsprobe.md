<!-- BOOK_ROLE: APPLICATION_SYSTEMS -->

# Chương 20 — Dự án tổng kết: opsprobe từ mã nguồn đến vận hành

Ở Chương 1, chúng ta sử dụng một kết quả HTTP giả định để làm quen với cách đọc một chương trình Go. Các chương tiếp theo lần lượt bổ sung yêu cầu mạng thực tế, thời hạn kết thúc (*deadline*), cơ chế xử lý đồng thời, lưu trữ bền vững và các tín hiệu vận hành. Chương này kết nối toàn bộ những cấu phần đó vào một công cụ thăm dò điểm cuối hoàn chỉnh: khi một lượt thăm dò thất bại, bên gọi cần biết kết quả thuộc về ranh giới kỹ thuật nào và dữ liệu nào đã được lưu trữ an toàn.

Dự án `projects/opsprobe/` là một mô hình thực nghiệm mẫu hoàn chỉnh gồm logic nghiệp vụ cốt lõi, nhóm tiến trình xử lý giới hạn (*worker pool*), cơ sở dữ liệu SQLite, hệ thống đo lường, truy vết phân tán và giao diện lập trình HTTP. Các bài kiểm thử tái lập chính xác những khế ước kỹ thuật cụ thể, bao gồm cả tình huống điển hình khi bỏ quên việc đóng luồng phản hồi (*response body*). Việc sở hữu một bản mã nguồn chạy được không đồng nghĩa công cụ đã sẵn sàng cho mọi môi trường vận hành thực tế; các phân tích về bảo mật và triển khai dưới đây chỉ rõ những giả định kỹ thuật bắt buộc phải duy trì.

Mô hình tư duy cốt lõi của chương là: một hệ thống Go trưởng thành không phải là tập hợp các bộ khung cồng kềnh, mà là sự khớp nối chuẩn xác giữa các ranh giới kỹ thuật thu hẹp: ngữ nghĩa giá trị, khế ước xử lý lỗi, điều tiết áp suất đồng thời, tính nguyên tử của trạng thái, tín hiệu quan sát trung thực và kỷ luật phát hành có trách nhiệm.

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

| Gói mã nguồn | Trách nhiệm vận hành | Khế ước bảo vệ |
| :--- | :--- | :--- |
| `probe` | Kiểm tra điểm cuối, phân loại kết quả. | Giới hạn tiến trình làm việc, phân định kết quả rõ ràng, giải phóng luồng dữ liệu. |
| `store` | Lưu trữ siêu dữ liệu và kết quả thăm dò. | Giao dịch nguyên tử qua gói `database/sql`. |
| `telemetry` | Ghi nhận nhật ký, chỉ số đo lường và vết phân tán. | Không suy đoán cảm tính, đo lường chuẩn xác nhãn kết quả. |
| `httpapi` | Tiếp nhận yêu cầu, điều phối tải, trả về dữ liệu JSON. | Điều tiết áp suất ngược mã 429, kiểm tra tính sẵn sàng, rút cạn kết nối an toàn. |
| `cmd` | Điểm khởi đầu cấu hình toàn cục (*Composition Root*). | Phân tích tham số dòng lệnh, đón bắt tín hiệu hệ điều hành, tắt tiến trình an toàn. |

Hai gói `probe` và `store` hoàn toàn không phụ thuộc vào `httpapi` hay `cmd`, do đó có thể kiểm thử độc lập mà không cần khởi động toàn bộ ứng dụng. Điều đó không biến mọi bài kiểm thử thành các phép tính toán thuần túy: kiểm thử vào ra dữ liệu của `probe` sử dụng máy chủ HTTP cục bộ, trong khi kiểm thử của `store` đòi hỏi cơ sở dữ liệu thực sự. Chiều hướng phụ thuộc giúp phân định ranh giới rõ ràng; các bộ dữ liệu kiểm thử (*fixtures*) vẫn phải tái lập trung thực đúng hành vi cần kiểm chứng.

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

Việc phân định ranh giới giữa `OutcomeTimeout` và `OutcomeCancel` giúp bên gọi lưu giữ nguyên nhân kết thúc đúng theo khế ước kỹ thuật của bài thực hành. Cơ chế này không tự động phân loại được nguyên nhân gốc rễ từ tầng mạng hay chứng minh mọi hành động hủy bỏ đều xuất phát từ việc dừng ứng dụng; kỹ sư cần đối chiếu với vòng đời tiến trình, thời hạn kết thúc và các dữ liệu quan sát bổ trợ.

Mỗi kết quả probe ghi nhận thời lượng bằng mili-giây (`DurationMs`) phục vụ bảng điều khiển và nano-giây (`DurationNs`) để tránh mất thông tin do làm tròn số; đơn vị nano-giây không chứng minh đồng hồ đo đạt độ chính xác tuyệt đối đến nano-giây. Thời điểm ghi nhận đợt chạy trong cơ sở dữ liệu phân biệt rõ `StartedAt` (bắt đầu thực thi) và `CompletedAt` (kết thúc toàn bộ tiến trình làm việc), tránh nhầm lẫn độ trễ một yêu cầu đơn lẻ với thời gian hoàn tất toàn bộ lô công việc.

### 2. Giới hạn đồng thời và áp suất ngược

Khi danh sách mục tiêu thăm dò tăng vọt từ 10 lên 10.000, việc khởi tạo tức thời `go p.ProbeSingle(...)` cho từng mục tiêu có thể gây áp lực nghẽn nghiêm trọng lên bộ nhớ, ổ cắm mạng và dịch vụ đích. Mức độ tác động phụ thuộc mật thiết vào khối lượng công việc và hạn ngạch của môi trường; không thể vội vàng suy đoán hệ điều hành chắc chắn sẽ sụp đổ chỉ dựa trên số lượng tiến trình goroutine thuần túy.

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

Đoạn trên lược bỏ instrumentation và một số field kết quả. Trong source, producer đưa toàn bộ job vào kênh đệm rồi đóng kênh trước khi khởi động worker. `WorkerObserver.WorkerStarted/WorkerStopped` bao quanh từng lượt `ProbeSingle`, nên `opsprobe_active_workers` đo thao tác thăm dò đang chạy, không phải tổng số goroutine còn sống hay worker đang chờ việc. Lượt job bị bỏ qua vì context đã hủy không tăng gauge này. `wg.Wait()` là điểm bàn giao kết quả sau khi mọi worker kết thúc; hook quan sát không thay cho phép join đó.

Tại giao diện HTTP API, một kênh đệm vận hành như cờ hiệu (*semaphore*) để giới hạn số lượng lượt chạy đồng thời theo cấu hình. Khi cạn kiệt vị trí xử lý, chính sách của bài thực hành sẽ chủ động từ chối tiếp nhận công việc mới bằng mã trạng thái `429 Too Many Requests`; giới hạn này là định mức của ví dụ mẫu, chưa phải năng lực chịu tải đã được kiểm chứng an toàn cho môi trường thực tế:

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

Trong `internal/store/store.go`, bản ghi đợt chạy (`runs`) và các kết quả probe (`probe_results`) được ghi trong một transaction qua `database/sql`. Đoạn dưới là mã giả về thứ tự thao tác; dấu `...` lược các đối số nên không phải mã Go có thể sao chép để biên dịch. Truy vấn, đối số và nhánh lỗi đầy đủ nằm trong source và được kiểm thử bằng SQLite thật:

~~~text
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

Bên gọi bắt buộc phải luôn đóng luồng dữ liệu `resp.Body`. Việc đọc dữ liệu đến khi cạn dòng (*EOF*) có thể hỗ trợ một số trường hợp tái sử dụng kết nối mạng, nhưng thao tác `Close` hay rút cạn dòng dữ liệu (*drain*) không bảo đảm kết nối chắc chắn sẽ được tái sử dụng: tầng truyền vận (*Transport*), giao thức mạng, máy chủ và trạng thái kết nối tức thời đều tham gia quyết định việc này. Ngược lại, việc rút cạn dòng dữ liệu không giới hạn đòi hỏi phải cân nhắc thận trọng khi dịch vụ đích có thể trả về phần thân phản hồi khổng lồ hoặc không bao giờ kết thúc.

`opsprobe` thiết lập chính sách bounded drain có kiểm soát:

~~~go
const MaxDrainBytes = 16384 // 16 KiB

func drainResponseBody(
	body io.ReadCloser, maxBytes int64,
) (bool, error) {
	if body == nil {
		return false, nil
	}
	defer body.Close()
	if maxBytes <= 0 {
		return false, nil
	}
	if maxBytes == int64(^uint64(0)>>1) {
		return false, errors.New(
			"drain limit leaves no room for sentinel byte")
	}
	lr := &io.LimitedReader{R: body, N: maxBytes + 1}
	_, err := io.Copy(io.Discard, lr)
	if err != nil {
		return false, err
	}
	// Body nhỏ đã chạm EOF; không phải guarantee reuse.
	return lr.N > 0, nil
}
~~~

Quy tắc kỹ thuật ở đây rất rõ ràng:

Một là, đóng phần thân phản hồi trên mọi nhánh kết thúc: hoàn tất đầy đủ trách nhiệm với luồng dữ liệu phản hồi theo đúng khế ước kỹ thuật. Thao tác `Close` không đồng nghĩa với việc mỗi lần gọi đều phải đóng hẳn ổ cắm mạng TCP; tầng truyền vận có thể giữ lại kết nối để tái sử dụng.

Hai là, ấn định hạn mức 16 KiB: Đây là chính sách kỹ thuật của bài thực hành, không phải con số thống kê dung lượng phản hồi của các bộ khung bên ngoài. Hàm bổ trợ đọc thêm tối đa một byte để nhận biết phần thân có vượt hạn mức hay không, sử dụng `io.Discard` nhằm loại bỏ dữ liệu thay vì lưu giữ toàn bộ vào bộ nhớ RAM.

Ba là, nhận biết thời điểm cạn dòng dữ liệu: việc đọc tối đa `MaxDrainBytes + 1` giúp phân biệt rõ ràng phần thân nhỏ đã đọc trọn vẹn với phần thân vượt quá hạn mức cho phép. Thao tác rút cạn chỉ được coi là thành công khi phép đọc không phát sinh lỗi và biến đếm `lr.N > 0`; lỗi phát sinh trước khi chạm mốc kết thúc dòng không được phép diễn giải là thành công. Đây là quyết định phân bổ hạn mức của hàm bổ trợ, không phải cờ xác nhận đủ điều kiện tái sử dụng bên trong tầng truyền vận. Khả năng tái sử dụng kết nối HTTP/1.x còn phụ thuộc chặt chẽ vào quy cách đóng gói dữ liệu, máy chủ đích, sự cố đường truyền và trạng thái nội bộ của tầng truyền vận.

Bốn là, đưa ra quyết định đánh đổi kỹ thuật có chủ đích: Nếu phần thân phản hồi vượt quá 16 KiB, biến đếm `lr.N` sẽ nhận giá trị bằng 0. Bài thực hành ghi nhận phần thân chưa được đọc hết và lập tức đóng luồng dữ liệu để giải phóng tài nguyên; không đưa ra kết luận võ đoán rằng tầng truyền vận sẽ hay không thể tái sử dụng một kết nối cụ thể.

Năm là, thời lượng thăm dò phản ánh trọn vẹn toàn bộ vòng đời thao tác: Đồng hồ đo lường thời gian bắt đầu từ trước khi phát yêu cầu mạng cho đến khi quy trình dọn dẹp và rút cạn dòng dữ liệu kết thúc. Nếu mục tiêu trả về tiêu đề thành công 200 nhưng luồng dữ liệu phần thân bị tắc nghẽn kéo dài vượt quá thời hạn, lượt thăm dò sẽ kết luận chính xác là `OutcomeTimeout` thay vì báo nhầm là `OutcomeSuccess`.

### 5. Ranh giới bảo mật, hợp đồng JSON và truy vết phân tán

Một công cụ vận hành chỉ an toàn khi các ranh giới ngoại vi được xác định rành mạch:

Dự án `opsprobe` đặt giả định rằng người vận hành và danh bạ mục tiêu là các thành phần đáng tin cậy. Việc kiểm tra cú pháp địa chỉ URL không thể ngăn chặn triệt để lỗ hổng giả mạo yêu cầu từ phía máy chủ (SSRF). Nếu tiếp nhận dữ liệu đầu vào không tin cậy, hệ thống bắt buộc phải thiết lập chính sách kiểm soát mục tiêu và lưu lượng đi ra, kiểm soát phân giải tên miền và chuyển hướng theo mô hình đe dọa; không thể mặc định ngăn chặn mọi dải mạng nội bộ vì một công cụ vận hành nội bộ có thể cần truy cập chính các điểm cuối đó. Danh sách cho phép hoặc máy chủ ủy nhiệm trung gian cũng cần có chủ thể quản lý và cấu hình được kiểm chứng.

Về khế ước JSON tương thích đa nền tảng: Trường `timeout_ms` trong dữ liệu yêu cầu sử dụng kiểu số nguyên mili-giây (`0 <= timeout_ms <= 60000`), bảo đảm tính tương thích cao thay vì phân tích cú pháp chuỗi thời gian đặc thù của riêng Go.

Về cơ chế phân tán ngữ cảnh chuẩn W3C: Các yêu cầu thăm dò gửi ra ngoài được chèn thêm tiêu đề `traceparent` tương ứng với khoảng thời gian con (*child span*) hiện hành. Để kết nối liền mạch chuỗi truy vết, dịch vụ tiếp nhận bắt buộc phải đọc ngữ cảnh đó và cấu hình cơ chế lấy mẫu cùng việc xuất dữ liệu phù hợp; việc gửi đi một tiêu đề không tự nó chứng minh rằng chuỗi quan sát xuyên suốt giữa các dịch vụ đã hoàn chỉnh.

## Bài tập chẩn đoán sự cố: Bão cạn kiệt Socket

Thư mục `projects/opsprobe/incident/` mô phỏng một sự cố kinh điển trong môi trường microservices.

### Kịch bản và Triệu chứng lâm sàng

> **Ghi chú phương pháp luận:** Đây là kịch bản giả định mô phỏng tình huống sự cố thực tế để đặt ra bài toán chẩn đoán cho kỹ sư.

Hệ thống probe giả định được triển khai để kiểm tra sức khỏe các microservice nội bộ. Khi số lượng request tăng lên, hệ thống giám sát ghi nhận tỷ lệ `OutcomeTimeout` tăng vọt và độ trễ probe tăng cao. Tuy nhiên, khi kỹ sư thực hiện một lệnh cURL độc lập trực tiếp tới dịch vụ đích, dịch vụ vẫn phản hồi rất nhanh trong vài phần nghìn giây. Kiểm tra tài nguyên hệ điều hành bằng `ss -s` cho thấy số lượng socket TCP mở tăng liên tục theo từng lượt gọi mà không được thu hồi, tiệm cận giới hạn file descriptors (`ulimit -n`). Đồng thời, khi kiểm tra bằng `net/http/httptrace`, hook `GotConnInfo.Reused` luôn trả về `false`, cho thấy `http.Transport` không tái sử dụng được kết nối rảnh nào giữa các lượt probe.

> **Dừng để dự đoán:** Vì sao kết quả cURL nhanh chỉ là bằng chứng hỗ trợ thu hẹp giả thuyết chứ chưa đủ để bác bỏ hoàn toàn lỗi hạ tầng? Kỹ sư cần thiết kế phép thử nào với `httptrace` để xác minh vòng đời kết nối của client trước khi can thiệp vào cấu hình hệ thống?

#### Gợi ý giải pháp (chỉ đọc sau khi đã tự làm)
Kết quả cURL phản hồi nhanh chỉ cho thấy dịch vụ đích có khả năng phục vụ một kết nối đơn lẻ tại thời điểm thử nghiệm. Nó giúp thu hẹp nghi vấn về việc máy chủ đích bị treo hoàn toàn, nhưng chưa đủ để loại trừ các yếu tố hạ tầng phức tạp như giới hạn kết nối đồng thời trên tường lửa, chính sách cân bằng tải hay tình trạng bão hòa hàng đợi socket.

Để cô lập nguyên nhân, kỹ sư dùng `net/http/httptrace` và trường `info.Reused`. Theo tài liệu `net/http`, nếu body chưa được đọc đến EOF và đóng, Transport có thể không tái sử dụng kết nối HTTP/1.x. Trong fixture cố ý bỏ body, ta quan sát kết nối mới; đó không phải bảo đảm rằng mọi request tiếp theo trong mọi cấu hình đều phải mở TCP mới hay chắc chắn cạn tài nguyên. HTTP/2 còn có vòng đời stream khác; không ngoại suy kết quả này sang mọi giao thức.

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

Trong kịch bản giao thức HTTP/1.x của bài thực hành, hàm xử lý trả về kết quả mà không đọc trọn vẹn hoặc không đóng phần thân phản hồi. Kết nối đang lưu giữ luồng dữ liệu chưa hoàn tất sẽ không thể tái sử dụng cho các yêu cầu khác; việc gia tăng tải trong tình trạng này sẽ làm bùng nổ số lượng kết nối mở. Không áp dụng kết luận này một cách máy móc cho cơ chế dồn kênh phức hợp (*multiplexing*) của giao thức HTTP/2.

### Bằng chứng đo đạc thực nghiệm

Trong bài kiểm thử 20 yêu cầu tuần tự tới máy chủ kiểm thử ở `incident/incident_test.go`, công cụ `httptrace` ghi nhận các số đếm thực nghiệm sau. Dữ liệu này mô tả chính xác ca kiểm thử cụ thể, không dự đoán tỷ lệ tái sử dụng kết nối cho mọi máy chủ hay mọi khối lượng tải:

| Chỉ số thực nghiệm | BuggyProbe (Bỏ quên Close) | FixedProbe (Close + Drain 16 KiB) |
| :--- | :--- | :--- |
| Kết nối mới (`Reused == false`) | **20** | **1** (trong bài kiểm thử này) |
| Kết nối tái sử dụng (`Reused == true`) | **0** | **19** (trong bài kiểm thử này) |
| Kết quả vận hành | Mỗi yêu cầu mở ổ cắm mạng mới | Tái sử dụng ổ cắm mạng trong nhóm |

Bài kiểm thử `TestIncident_BoundedDrainOversizedBody` xác nhận rằng với phần thân 32 KiB (vượt quá hạn mức 16 KiB), bài thực hành sẽ trả về `reusedEligible == false` và lập tức đóng phần thân phản hồi. Cơ chế rút cạn có giới hạn chỉ kiểm soát lượng dữ liệu mà máy khách chủ động đọc bỏ; nó không phải là cơ chế phòng chống tràn bộ nhớ đệm hay bảo đảm tuyệt đối rằng một kết nối mạng sẽ được tái sử dụng.

## Consumer đã rời đi, worker còn nợ ai kết quả?

Các bài kiểm thử trước đó bảo vệ một tập hợp các mục tiêu đã xác định từ trước. Bây giờ chúng ta thay đổi bài toán: bên sản xuất công việc tiếp tục nhận việc trong khi dịch vụ phụ thuộc phản hồi chậm, hàng đợi bị lấp đầy và bên tiêu thụ ngừng đọc kết quả. Việc bổ sung thêm tiến trình làm việc có thể khiến dịch vụ phụ thuộc chịu tải nặng hơn; việc mở rộng bộ đệm chỉ kéo dài thêm khoản nợ dồn ứ. Phòng thực nghiệm `projects/opsprobe/failurelab` bao bọc hàm `ProbeSingle` hiện có bằng một hàng đợi tiếp nhận hữu hạn mà không cần viết lại nhóm tiến trình hay giao diện lập trình thực tế của dự án.

Hãy khảo sát ca kiểm thử `TestBoundedAdmission` trước khi xem mã nguồn. Bộ thử nghiệm giữ lại hai yêu cầu tại điểm chặn (*barrier*) của máy chủ HTTP cục bộ. Hai công việc tiếp theo được đưa vào hàng đợi; 100 lần nộp thêm sau đó bắt buộc phải nhận lỗi `ErrFull` mà không làm phát sinh thêm bất kỳ tiến trình goroutine nào. Khi giải phóng điểm chặn và tiêu thụ bốn kết quả: số lượng công việc đang chạy và số lượng trong hàng đợi đều trở về 0, đỉnh công việc đang chạy không vượt quá 2. Những con số này đại diện cho khế ước về sức chứa của bộ thử nghiệm, không phải kết quả đo chuẩn phần cứng hay lời khuyên “môi trường thực tế chỉ nên chạy hai tiến trình”.

Tiếp theo, hãy thực thi `TestConsumerStopsContract`. Lượt thăm dò đã hoàn tất, điểm kiểm tra ngay trước lệnh gửi xác nhận tiến trình làm việc đang chuẩn bị bàn giao kết quả; bên tiêu thụ cố tình không đọc dữ liệu đầu ra. Lệnh hủy bỏ (*cancel*) bắt buộc phải cho phép tiến trình trả về và bộ điều phối đóng kênh `Done`. Phiên bản khiếm khuyết đã bỏ qua nhánh xử lý hủy bỏ tại lệnh gửi nên không thể kết thúc trong thời hạn của bài kiểm thử. Khung kiểm thử được trang bị lối thoát khẩn cấp riêng để thu hồi tài nguyên sau khi bộ phán đoán bắt lỗi; phiên bản lỗi tuyệt đối không được phép để lại một tiến trình goroutine bị mắc kẹt bên trong toàn bộ tập kiểm thử.

~~~powershell
cd projects/opsprobe
go test -count=1 -v ./failurelab
$env:RELIABILITY_MUTANT='uncancellable_send'
go test -count=1 -run TestConsumerStopsContract ./failurelab
Remove-Item Env:RELIABILITY_MUTANT
~~~

Lệnh thứ hai bắt buộc phải báo lỗi đỏ. Trước khi xem lời giải, hãy chỉ rõ điểm tắc nghẽn khi không còn bên tiếp nhận và lý do tại sao ngữ cảnh trên yêu cầu HTTP không thể giải phóng điểm tắc nghẽn đó. Đây là bước tích hợp khế ước gửi dữ liệu qua kênh từ Chương 9, hoàn toàn không phải là kỹ thuật tinh chỉnh bộ điều phối tiến trình.

*Giải thích:* Quá trình trao đổi HTTP đã hoàn tất nên thời hạn kết thúc tại `ProbeSingle` không còn quản lý tiến trình làm việc nữa. Tiến trình vẫn đang chờ gửi kết quả; chỉ có cấu trúc `select` lắng nghe ngữ cảnh của bộ thực thi mới mở ra lối thoát an toàn. Bên gọi bắt buộc phải phát tín hiệu hủy bỏ rồi chờ kênh `Done` kết thúc khi quyết định ngừng tiêu thụ dữ liệu. Phiên bản khắc phục không bảo đảm bên tiêu thụ sẽ xử lý mọi kết quả sau khi đã hủy bỏ; đó là chính sách hủy bỏ những lượt bàn giao chưa kịp hoàn tất, một điều kiện cần phải chấp nhận trước khi sử dụng các giao diện truyền tải dữ liệu dạng luồng (*streaming*).

### Lấy tín hiệu đủ sức phân biệt nguyên nhân

Ca kiểm thử `TestLocalFaultsAndSignals` lần lượt tiêm vào các trạng thái lỗi: tạm giữ và giải phóng, hết thời hạn, lỗi máy chủ 503, phần thân bị ngắt giữa chừng dù tiêu đề báo 200, và ngắt kết nối trước khi nhận phản hồi. Kỹ thuật tạm giữ và giải phóng tạo ra một phản hồi chậm trễ được kiểm soát bằng điểm chặn, không dựa vào việc tạm dừng thời gian (*sleep*) để suy đoán máy chủ đã nhận yêu cầu. Hết thời hạn là một lỗi thất bại được chờ đợi thực tế. Với mỗi trường hợp, bài kiểm thử đọc kết quả phân loại, một dòng nhật ký tương ứng, mẫu biểu đồ phân bố và khoảng thời gian `opsprobe.probe` từ các thành phần đo lường có sẵn. Nó hoàn toàn không gọi tới hệ thống thu thập tập trung, mạng Internet hay dịch vụ thực tế.

@table Chọn phép đo phân biệt thay vì đổi cấu hình theo triệu chứng

| Triệu chứng vận hành | Các giả thuyết cạnh tranh | Bằng chứng kỹ thuật cần thu thập |
| :--- | :--- | :--- |
| Độ trễ cao | Dịch vụ phụ thuộc giữ phản hồi hay tiến trình chờ lượt chạy? | Điểm chặn máy chủ và khoảng truy vết HTTP; dùng phân tích vết mạng và lịch trình từ Chương 10 để kiểm tra thời gian chờ. |
| Hàng đợi bị đầy | Tải gửi đến vượt năng lực xử lý hay tiến trình không thể thoát? | Tỷ lệ từ chối, số lượng đang chạy và hàng đợi; ngừng nộp việc, hủy bỏ và thu hồi đúng tiến trình. |
| Bên gọi bị quá hạn | Dịch vụ phụ thuộc đã dừng hay chỉ phía máy khách thôi chờ? | Kênh `Done` phía máy khách và tín hiệu kết thúc độc lập của hàm xử lý phía nhận. |
| Bộ nhớ Heap tăng | Cấp phát tạm thời, lượng tồn đọng hợp lệ hay giữ tài nguyên sai? | Khối lượng tải và hàng đợi; hồ sơ bộ nhớ sau giai đoạn lắng dịu từ Chương 10 thay vì một bản chụp tức thời. |
| Thời gian cao, CPU thấp | Chờ dữ liệu vào ra hoặc đồng bộ hay chi phí CPU bị nhìn thiếu? | Phân tích vết thời gian chờ cùng hồ sơ CPU của đúng khối lượng tải; không coi mức sử dụng CPU thấp là bằng chứng tuyệt đối. |

Bài kiểm thử `TestCancelDoesNotProveDependencyStopped` thiết lập một hàm xử lý cố tình không kiểm tra ngữ cảnh. Phía máy khách hủy bỏ và kết thúc thành công bộ thực thi, nhưng hàm xử lý vẫn chưa dừng lại cho đến khi bộ thử nghiệm giải phóng nó. Một thông báo quá hạn gửi về cho bên gọi không phải là lời xác nhận rằng dịch vụ phía dưới đã hủy bỏ hoàn toàn các hiệu ứng phụ. Đối với các thao tác có làm biến đổi dữ liệu, hãy quay lại bài toán định danh và khoảng thời gian gửi lặp ở Chương 13 và Chương 25 trước khi quyết định bổ sung cơ chế thử lại.

Bộ thực thi tính toán thời hạn kết thúc ngay từ thời điểm tiếp nhận, do đó thời gian nằm chờ trong hàng đợi được tính trực tiếp vào ngân sách thời gian; thời hạn riêng của từng mục tiêu có thể thu hẹp ngân sách này hơn nữa. Nếu công việc tới được tiến trình xử lý khi ngân sách thời gian đã cạn kiệt, yêu cầu sẽ không được cấp thêm một hạn mức mới để che giấu độ trễ chờ đợi. Chính sách ở đây là chủ động ngắt bỏ tải ngay khi hàng đợi bị lấp đầy và không tự động thử lại. Hàng đợi chỉ lưu giữ tối đa sức chứa mục tiêu và số lượng tiến trình cố định; bên gọi vẫn bắt buộc phải giới hạn kích thước của từng dữ liệu đầu vào ngay tại ranh giới của ứng dụng thực tế.

Lượt thực thi với cờ `RUN_BOUNDED_LOAD=1` gửi chính xác 64 lượt thử nghiệm trong tối đa 10 giây, sử dụng bốn tiến trình làm việc và hàng đợi có kích thước 16. Lệnh này ghi nhận thông lượng, các mốc thời lượng p50/p95 của lượt thăm dò, số lượng từng loại kết quả, đỉnh điểm công việc đang chạy và trong hàng đợi, cùng các bản chụp trạng thái tiến trình goroutine và bộ nhớ heap. Biểu đồ phân bố `failurelab_job_seconds` còn tính gộp cả thời gian chờ trong hàng đợi; hai định nghĩa độ trễ này tuyệt đối không được phép trộn lẫn. Dữ liệu đầu ra thực tế và câu lệnh tái lập được lưu giữ trong tài liệu bằng chứng của bài thực hành. Việc so sánh thông lượng giữa các máy tính khác nhau không phải là chuẩn mực chân lý; dữ liệu heap chưa được dọn dẹp sau thu gom rác cũng không phải là bằng chứng rò rỉ bộ nhớ. Hãy áp dụng phòng thực nghiệm bộ nhớ từ Chương 10 để kiểm chứng giả thuyết đó thay vì tự ý dựng lên một công cụ phát hiện rò rỉ dựa trên các con số tùy tiện.

## Đóng gói, điều phối và chuyển giao có trách nhiệm

Để đưa `opsprobe` ra môi trường production, ta áp dụng toàn bộ các nguyên tắc đã học ở Chương 17 và 18:

Một là, tệp cấu hình đóng gói vùng chứa nhiều giai đoạn: bài thực hành biên dịch tệp nhị phân với cờ `CGO_ENABLED=0`, sau đó sử dụng ảnh cơ sở tối giản `gcr.io/distroless/static-debian12:nonroot` và vận hành dưới tài khoản không có đặc quyền quản trị (`USER 65532:65532`). Với các gói phụ thuộc thuần Go của bài thực hành, giải pháp này không đòi hỏi môi trường thực thi ngôn ngữ C; tuy nhiên không thể suy diễn rộng thành lời cam đoan rằng mọi chương trình đều không có phụ thuộc bên ngoài tệp nhị phân.

Hai là, bài thực hành triển khai một Pod đơn lẻ và một tệp cơ sở dữ liệu SQLite, với số bản sao `replicas: 1`, ổ lưu trữ `ReadWriteOnce` (RWO) và chiến lược triển khai `Recreate`. Chế độ RWO giới hạn quyền ghi theo từng nút máy chủ, không phải theo từng Pod; nhiều Pod chạy trên cùng một nút máy chủ vẫn có thể cùng gắn ổ lưu trữ đó. Bản thân SQLite có cơ chế khóa cho nhiều kết nối hoặc tiến trình, vì vậy không phải cứ hai tiến trình cùng truy cập là dữ liệu lập tức mất tính nhất quán. Rủi ro chỉ thực sự bùng nổ khi chia sẻ tệp qua hệ thống tệp mạng có ngữ nghĩa khóa và đồng bộ hóa không tương thích. Chiến lược `Recreate` hạn chế việc chồng lấn các phiên bản trong quá trình luân chuyển thông thường, hoàn toàn không thay thế được khóa phân tán hay cơ chế cô lập khi nút máy chủ gặp sự cố. Nếu đòi hỏi nhiều tiến trình cùng ghi từ các nút máy chủ khác nhau, hãy ưu tiên cơ sở dữ liệu theo mô hình máy khách - máy chủ (như PostgreSQL), hoặc thiết kế một tiến trình sở hữu duy nhất cho SQLite đi kèm khế ước chuyển đổi dự phòng rõ ràng.

Ba là, nạp cấu hình lúc khởi động qua đối tượng ConfigMap: Mức độ đồng thời, thời hạn tối đa, giới hạn áp suất ngược và cấp độ nhật ký được nạp từ tệp `deploy/k8s/configmap.yaml` vào các biến môi trường (`OPSPROBE_*`). Việc chỉnh sửa ConfigMap không tự động cập nhật giá trị biến môi trường của các tiến trình đang vận hành; hệ thống cần khởi tạo lại Pod hoặc thiết kế cơ chế nạp lại cấu hình độc lập.

Bốn là, ghim chặt nội dung ảnh container trong đường ống CI/CD: chính sách của dự án yêu cầu bản kê ảnh container phải sử dụng mã băm nội dung (`image: ghcr.io/...@sha256:...`) đã được đường ống kiểm chứng độc lập. Cách làm này loại bỏ hoàn toàn sự phụ thuộc vào nhãn phiên bản (như `:latest`) vốn có thể bị trôi sang ảnh khác; bản thân mã băm nội dung không tự chứng minh ảnh container là đáng tin cậy, tương thích đúng nền tảng phần cứng hay còn được kho lưu trữ duy trì.

## Lệnh kiểm thử và vận hành hệ thống

Có thể trực tiếp chạy và kiểm chứng toàn bộ năng lực của `opsprobe` trong terminal:

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

Dự án tổng kết xâu chuỗi các bằng chứng kỹ thuật thu hẹp: ngữ nghĩa giá trị và hiện tượng trùng tên vùng nhớ, đồng bộ hóa tiến trình goroutine, vòng đời phần thân phản hồi, tính nguyên tử của giao dịch và định danh bất biến của sản phẩm đóng gói. Mỗi bằng chứng đều có phạm vi giới hạn riêng; một giao dịch cơ sở dữ liệu không thể giải quyết mọi hiệu ứng phụ bên ngoài, quy trình tắt ứng dụng có thời hạn tối đa và có thể không kịp xử lý hết mọi yêu cầu dang dở, trong khi mã băm nội dung không tự chứng minh logic bên trong sản phẩm là hoàn toàn đúng đắn. Khi chuyển giao sang môi trường vận hành thực tế, hãy luôn duy trì các giới hạn đó trong ca kiểm thử và hệ thống quan sát.

Khi mở rộng công cụ, hãy luôn duy trì các khế ước kỹ thuật này làm tiêu chí đánh giá mã nguồn: dữ liệu đầu vào nào được tin cậy, tài nguyên nào có chủ thể chịu trách nhiệm, hiệu ứng phụ nào có thể lặp lại an toàn, và quan sát nào xác nhận kết quả cuối cùng. Chương 21 sẽ áp dụng chính những câu hỏi cốt lõi này cho một bộ điều khiển (*controller*).

Việc hoàn thành dự án `opsprobe` chốt lại baseline vững chắc của cuốn sách sống (*living textbook*), đồng thời mở ra những bài toán hệ thống ở quy mô hạ tầng cao hơn: khi hệ thống không chỉ thăm dò thụ động mà cần liên tục tự điều hòa, dung hòa sai lệch giữa trạng thái mong muốn và thực tế để tự phục hồi.
