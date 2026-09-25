<!-- BOOK_ROLE: APPLICATION_SYSTEMS -->

# Chương 21 — Vòng lặp điều hòa và Controller Pattern

Trong Chương 20, dự án `opsprobe` đã trang bị cho ta một hệ thống thăm dò trạng thái hoàn chỉnh: kiểm tra định kỳ, phân loại kết quả rành mạch (`OutcomeSuccess`, `OutcomeFailure`, `OutcomeTimeout`), bảo toàn dữ liệu bằng giao dịch nguyên tử SQLite, và đo lường độ trễ qua Prometheus. Nhưng khi một dịch vụ phụ thuộc sập nguồn khiến dashboard chuyển màu đỏ rực, câu hỏi tiếp theo của một kỹ sư vận hành không còn là "làm sao để phát hiện?", mà là: "làm sao để hệ thống tự khôi phục trạng thái lành lặn mà không cần con người thức dậy lúc nửa đêm bấm nút restart?".

Đây là bước chuyển từ **Quan sát thụ động (Passive Observation)** sang **Tự điều hòa chủ động (Active Self-Healing)**. Trái tim của mọi nền tảng hạ tầng đám mây hiện đại — từ Kubernetes Controller, Nomad, Terraform đến ArgoCD — đều vận hành dựa trên một mẫu kiến trúc cốt lõi: **Vòng lặp điều hòa (Reconciliation Loop)** được điều phối bởi **Controller Pattern**.

## Kích hoạt theo mức và Kích hoạt theo cạnh

Để hiểu vì sao các hệ thống phân tán đáng tin cậy đều lựa chọn vòng lặp điều hòa, trước hết ta cần phân biệt hai triết lý thiết kế cơ bản: **Edge-Triggered (Kích hoạt theo cạnh)** và **Level-Triggered (Kích hoạt theo mức)**.

~~~
Edge:  Bắn sự kiện "Down" -> [Drop mạng] -> Mất tín hiệu
Level: "Actual != Desired" -> Can thiệp -> Hội tụ về chuẩn
~~~

Trong mô hình **Edge-Triggered**, hệ thống chỉ phát tín hiệu khi có một biến cố chuyển đổi trạng thái (chẳng hạn: `Target X chuyển từ Healthy sang Down`). Cách tiếp cận này rất trực quan và tiết kiệm tài nguyên khi hệ thống hoạt động lý tưởng. Tuy nhiên, trong môi trường phân tán thực tế, mạng có thể bị phân mảnh (network partition), tiến trình nhận có thể bị crash, hoặc bộ đệm hàng đợi có thể bị tràn. Khi sự kiện chuyển trạng thái bị rơi rớt trên đường truyền, tiến trình xử lý sẽ không bao giờ biết sự cố đã diễn ra. Hệ thống bị kẹt vĩnh viễn ở trạng thái sai lệch dù nguyên nhân gốc đã kết thúc từ lâu.

Ngược lại, mô hình **Level-Triggered** không quan tâm quá khứ đã xảy ra bao nhiêu lần chuyển trạng thái hay bao nhiêu thông điệp bị thất lạc. Ở mỗi chu kỳ, Controller chỉ quan sát **Trạng thái thực tế (Actual State)** hiện hành và so sánh với **Trạng thái mong muốn (Desired State)**:

1. **Trạng thái mong muốn:** Hệ thống cần 3 bản sao `payment-service` khỏe mạnh.
2. **Trạng thái thực tế:** Chỉ có 1 bản sao đang phản hồi 200 OK; 2 bản sao còn lại không thể kết nối.
3. **Sai lệch (Diff):** Thiếu 2 bản sao.
4. **Hành động:** Kích hoạt khởi chạy thêm 2 bản sao mới.

Ngay cả khi controller bị tắt đột ngột lúc đang khởi động bản sao thứ hai, ở lần thức dậy kế tiếp, nó lại tiếp tục so sánh và nhận ra sai lệch vẫn còn (hiện có 2 bản sao, vẫn thiếu 1). Nó lặp lại hành động cho đến khi sai lệch triệt tiêu hoàn toàn. Đặc tính này gọi là **sự hội tụ trạng thái (State Convergence)**.

## Bốn pha của Vòng lặp điều hòa

Một chu trình điều hòa chuẩn mực luôn diễn ra theo 4 bước khép kín và lặp lại liên tục:

| Bước | Tên gọi | Nhiệm vụ kỹ thuật trong Go |
| :--- | :--- | :--- |
| **1** | **Observe** | Đọc trạng thái thực tế từ hệ thống hoặc store. |
| **2** | **Diff** | So sánh trạng thái thực tế với trạng thái mong muốn. |
| **3** | **Act** | Thực thi hành động khắc phục để triệt tiêu sai lệch. |
| **4** | **Requeue** | Xếp lịch kiểm tra lại hoặc backoff nếu gặp lỗi. |

Trong Go, ta đóng gói hành vi này thành một interface nhỏ gọn:

~~~go
type Result struct {
	Requeue      bool
	RequeueAfter time.Duration
}

type Reconciler interface {
	Reconcile(
		ctx context.Context, key string,
	) (Result, error)
}
~~~

Quy ước này thể hiện rõ ranh giới trách nhiệm: `Reconciler` chỉ tập trung vào logic điều hòa của một tài nguyên duy nhất được định danh bởi `key`. Việc quản lý hàng đợi, phân phối worker và kiểm soát tần suất thử lại do tầng `Controller` bên ngoài đảm nhiệm.

## Hàng đợi công việc có kiểm soát tốc độ

Một sai lầm thường gặp của lập trình viên Go là sử dụng ngay một unbuffered channel (`chan string`) để làm hàng đợi cho controller. Trên môi trường production, channel thô nhanh chóng bộc lộ ba lỗ hổng nghiêm trọng:

1. **Thiếu khả năng gộp trùng (Deduplication):** Khi một dịch vụ chập chờn, 50 sự kiện báo lỗi liên tiếp có thể dồn về trong một giây. Nếu đẩy cả 50 item vào channel, worker sẽ chạy 50 lần reconcile hoàn toàn trùng lặp, gây lãng phí tài nguyên vô ích.
2. **Xung đột điều hòa song song (Parallel Race):** Nếu hai worker trong pool cùng lấy một `key` ra xử lý song song, chúng có thể cùng nhìn thấy trạng thái thiếu hụt và cùng kích hoạt hành động tạo mới, dẫn đến tình trạng nhân đôi bản sao ngoài ý muốn (split-brain).
3. **Bão thử lại (Retry Storm):** Nếu tài nguyên đích bị sập hoàn toàn, hàm `Act` sẽ liên tục trả về lỗi. Đẩy lại channel ngay lập tức sẽ khiến worker pool quay cuồng trong vòng lặp thử lại vô tận (spin-lock), vắt kiệt CPU và đánh sập chính dịch vụ đang hấp hối.

Để giải quyết triệt để ba bài toán trên, ta thiết kế cấu trúc `WorkQueue` chuyên dụng:

~~~go
type WorkQueue struct {
	mu           sync.Mutex
	cond         *sync.Cond
	queue        []string
	dirty        map[string]struct{}
	processing   map[string]struct{}
	failures     map[string]int
	shuttingDown bool
	config       RateLimiterConfig
}
~~~

Cơ chế phối hợp giữa `dirty` và `processing` tạo nên tính năng then chốt của hàng đợi:

~~~go
func (q *WorkQueue) Add(item string) {
	q.mu.Lock()
	defer q.mu.Unlock()

	if q.shuttingDown {
		return
	}
	// 1. Deduplication: Nếu item đã nằm trong dirty, bỏ qua
	if _, exists := q.dirty[item]; exists {
		return
	}
	q.dirty[item] = struct{}{}

	// 2. Nếu item đang xử lý, không đẩy vào slice
	// để tránh hai worker cùng reconcile một key
	if _, isProcessing := q.processing[item]; isProcessing {
		return
	}

	q.queue = append(q.queue, item)
	q.cond.Signal()
}
~~~

Khi một worker hoàn tất lượt xử lý và gọi `Done(item)`:

~~~go
func (q *WorkQueue) Done(item string) {
	q.mu.Lock()
	defer q.mu.Unlock()

	delete(q.processing, item)

	// Nếu trong lúc worker đang chạy, có thêm sự kiện mới
	// cho cùng key này, item lập tức được đưa lại vào queue
	if _, exists := q.dirty[item]; exists {
		q.queue = append(q.queue, item)
		q.cond.Signal()
	}
}
~~~

Nhờ cơ chế này, tại bất kỳ thời điểm nào, mỗi tài nguyên chỉ có tối đa một worker chịu trách nhiệm điều hòa. Mọi biến động xảy ra trong khi worker đang làm việc đều được ghi nhận vào `dirty` để xử lý ngay sau đó mà không bao giờ bị bỏ sót.

## Kiểm soát giãn cách lũy thừa khi có sự cố

Khi `Reconcile` thất bại, thay vì đưa key trở lại hàng đợi ngay lập tức, ta áp dụng thuật toán **Exponential Backoff** thông qua phương thức `AddRateLimited`:

~~~go
func (q *WorkQueue) AddRateLimited(item string) bool {
	q.mu.Lock()
	defer q.mu.Unlock()

	if q.shuttingDown {
		return false
	}
	failures := q.failures[item] + 1
	q.failures[item] = failures

	if failures > q.config.MaxRetries {
		return false // Vượt quá số lần thử lại tối đa
	}

	// Chờ tăng gấp đôi: base * 2^(failures-1)
	multiplier := 1 << (failures - 1)
	delay := q.config.BaseDelay * time.Duration(multiplier)
	if delay > q.config.MaxDelay {
		delay = q.config.MaxDelay
	}

	time.AfterFunc(delay, func() {
		q.Add(item)
	})
	return true
}
~~~

Nếu lần thử đầu tiên thất bại sau 50ms, lần kế tiếp sẽ diễn ra sau 100ms, rồi 200ms, 400ms, cho đến khi chạm trần `MaxDelay`. Khoảng thời gian giãn cách này tạo điều kiện cho hạ tầng mạng hoặc cơ sở dữ liệu có đủ thời gian tự hồi phục, ngăn ngừa triệt để hiện tượng bão retry. Khi đợt reconcile thành công, controller gọi `q.Forget(item)` để xóa bộ đếm thất bại, sẵn sàng cho các chu kỳ trong tương lai.

## Tính lũy thừa: Hợp đồng sống còn của Reconciler

Vì một tài nguyên có thể được đưa vào hàng đợi nhiều lần do sự kiện lặp, resync định kỳ hoặc retry sau lỗi, hàm `Reconcile` bắt buộc phải có **tính lũy thừa (Idempotency)** theo nguyên lý: `f(f(x)) = f(x)`.

Điều này có nghĩa: nếu trạng thái thực tế đã thỏa mãn trạng thái mong muốn, việc chạy lại `Reconcile` không được phép tạo thêm bất kỳ tác dụng phụ (side-effect) nào.

Hãy xem xét một Reconciler tự chữa lành cụ thể:

~~~go
func (r *SelfHealingReconciler) Reconcile(
	ctx context.Context, key string,
) (Result, error) {
	state, exists := r.getObservedState(key)
	if !exists {
		return Result{}, nil // Không tồn tại: No-op
	}

	// 1. Phân tích sai lệch giữa thực tế và mong muốn
	isDegraded := !state.Healthy ||
		state.Replicas < r.desiredReplicas

	// 2. Tính lũy thừa: Nếu đã chuẩn, kết thúc (No-op)
	if !isDegraded {
		return Result{}, nil
	}

	// 3. Thực thi hành động tự chữa lành (Act)
	if err := r.healTarget(ctx, key); err != nil {
		return Result{}, fmt.Errorf("heal %s: %w", key, err)
	}

	// 4. Cập nhật trạng thái sau khi chữa lành
	r.markHealthy(key, r.desiredReplicas)
	return Result{}, nil
}
~~~

Nếu `payment-service` đang có 1 replica trong khi yêu cầu là 3, hàm sẽ gọi `healHook` để nâng lên 3. Nếu ngay sau đó một sự kiện khác kích hoạt `Reconcile("payment-service")`, bước kiểm tra `!isDegraded` lập tức trả về `Result{}, nil`. Không có lệnh spawn thừa thãi nào được phát ra, loại bỏ hoàn toàn nguy cơ mất kiểm soát tài nguyên.

## Tắt nguồn mềm mại cho Controller

Controller quản lý nhiều worker goroutine chạy ngầm liên tục. Khi nhận tín hiệu dừng tiến trình (`SIGTERM` hoặc hủy context cha), toàn bộ worker phải hoàn tất các công việc đang dở dang trước khi trả quyền kiểm soát:

~~~go
func (c *Controller) Run(ctx context.Context) error {
	var wg sync.WaitGroup

	// Đánh thức và đóng hàng đợi khi context bị hủy
	go func() {
		<-ctx.Done()
		c.queue.ShutDown()
	}()

	for i := 0; i < c.concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for c.processNextWorkItem(ctx) {
			}
		}()
	}

	wg.Wait()
	return ctx.Err()
}
~~~

Phương thức `queue.ShutDown()` giải phóng các goroutine đang bị block ở lệnh `cond.Wait()`. Vòng lặp `for c.processNextWorkItem(ctx)` nhận được tín hiệu `shutdown == true` khi hàng đợi đã cạn, kết thúc vòng lặp và thông báo qua `wg.Done()`. Quá trình này bảo đảm không có thao tác ghi dữ liệu nào bị đứt gánh giữa chừng.

## Thực hành Lab: Kiểm chứng Controller và WorkQueue

Toàn bộ kiến trúc trên được đóng gói tại thư mục thực hành `labs/part21-reconciliation-controller`:

~~~powershell
cd labs/part21-reconciliation-controller
go test -v ./...     # Chạy toàn bộ test suite
go test -race ./...  # Kiểm tra race condition
go vet ./...        # Phân tích tĩnh cú pháp
~~~

Bộ kiểm thử tự động xác thực ba đặc tính kỹ thuật quan trọng:
- `TestWorkQueue_Deduplication`: Gộp nhiều sự kiện cùng key thành 1 lượt xử lý duy nhất trong queue.
- `TestController_SelfHealing_Success`: Tự động điều hòa dịch vụ hỏng về trạng thái chuẩn và bảo đảm tính lũy thừa khi enqueue lặp lại.
- `TestController_HealFailure_RateLimitedBackoff`: Tự động lùi lịch thử lại bằng exponential backoff khi hành động chữa lành bị lỗi.

## Bước phát triển tiếp theo

Hiểu và làm chủ Controller Pattern là bước ngoặt đưa kỹ sư Go từ vai trò người xây dựng công cụ đơn lẻ trở thành kiến trúc sư của các hệ thống tự trị (*autonomous control systems*). Bằng cách kết hợp khả năng thu thập tín hiệu của `opsprobe` (Chương 20) với cơ chế điều hòa cấp độ mức của Controller (Chương 21), hệ thống không chỉ biết nói cho ta biết nó đang đau ở đâu, mà còn có thể tự chữa lành vết thương trước khi người dùng kịp nhận ra.

Đây chính là nền tảng trực tiếp để ta mở rộng sang việc xây dựng các Custom Controller và Operator tiêu chuẩn trong hệ sinh thái Kubernetes bằng `client-go` ở các chương chuyên sâu tiếp theo.

@references
1. Kubernetes Authors. Controller pattern and declarative state management. kubernetes.io/docs/concepts/architecture/controller/
2. B. Grant. Declarative application management in Kubernetes. github.com/kubernetes/community
3. Kubernetes Authors. Package `client-go/util/workqueue` reference and design. pkg.go.dev/k8s.io/client-go/util/workqueue
4. S. Newman. Building Microservices: Designing Fine-Grained Systems and Self-Healing Architecture. O'Reilly Media.
5. Go Team. Advanced Go Concurrency Patterns: Pipelines and cancellation. go.dev/blog/pipelines
