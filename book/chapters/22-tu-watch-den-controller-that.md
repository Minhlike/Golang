<!-- BOOK_ROLE: APPLICATION_SYSTEMS -->

# Chương 22 — Từ watch đến một controller Kubernetes thật

Trong Chương 21, chúng ta đã tự tay dựng một vòng lặp điều hòa tối giản bằng Mutex, Channel và slice trong bộ nhớ. Mô hình đó giúp ta nắm vững tinh thần cốt lõi: *quan sát thực tế, đo lường sai lệch và hội tụ về trạng thái mong muốn*. Nhưng khi bước ra hạ tầng phân tán thật — nơi hàng chục nghìn Pod, Node và Service biến đổi liên tục qua mạng — việc dùng một channel thô để lắng nghe sự kiện sẽ nhanh chóng dẫn đến thảm họa.

Khi kết nối mạng chập chờn, khi API Server chịu tải cao, hay khi 500 sự kiện cập nhật cùng ùa về trong một giây, một chương trình ngây thơ sẽ rơi vào tình trạng:
1. Làm tràn bộ đệm kênh hoặc bỏ sót sự kiện.
2. Xử lý các bản tin cũ rích đè lên trạng thái mới nhất.
3. Tạo ra bão thử lại (retry storm) vắt kiệt CPU của cụm máy chủ.

Chương này đưa bạn từ tư duy "lắng nghe sự kiện ngây thơ" bước sang kiến trúc chuẩn mực của một **Production Kubernetes Controller** được xây dựng trên thư viện chính thức `k8s.io/client-go`.

---

## 1. Bản chất: Tín hiệu thông báo không phải là Chân lý

Câu hỏi trung tâm của chương này là:
> *Khi nhận được một sự kiện từ Kubernetes API Server, ta có nên tin vào dữ liệu đính kèm bên trong sự kiện đó để ra quyết định điều hòa hay không?*

Câu trả lời dứt khoát là: **Không**.

Trong các hệ thống phân tán quy mô lớn, **Sự kiện thông báo (Notification Hint)** chỉ là một lời nhắc nhở: *"Tài nguyên X tại namespace Y dường như vừa có biến đổi, hãy kiểm tra lại đi!"*. Bản thân sự kiện không phải là **Trạng thái thẩm quyền (Authoritative State)**. 

Trạng thái thẩm quyền duy nhất của hệ thống nằm tại cơ sở dữ liệu phân tán (etcd) phía sau Kubernetes API Server, và được phản chiếu trung thực nhất qua bộ nhớ đệm cục bộ (**Local Informer Cache**) của controller tại thời điểm hiện hành.

### Bẫy tư duy: Xử lý theo payload của sự kiện

Hãy tưởng tượng kịch bản sau:
1. Lúc `t₀`: Pod `web-app` có trạng thái `Pending`. API Server phát sự kiện `E₁(Pending)`.
2. Lúc `t₁`: Kubelet khởi động xong container, Pod chuyển sang `Running`. API Server phát sự kiện `E₂(Running)`.
3. Do độ trễ mạng hoặc hàng đợi bận rộn, worker trong controller nhận `E₁` chậm mất 3 giây.
4. Nếu worker dùng ngay dữ liệu bên trong `E₁`, nó sẽ tưởng Pod vẫn đang `Pending` và ra lệnh hủy Pod để tạo lại. Hành động này phá hủy trực tiếp Pod vừa khởi động lành lặn lúc `t₁`.

Quy tắc bất biến của Kubernetes Controller:
> **Chỉ đẩy định danh (Key: `namespace/name`) vào hàng đợi. Khi worker thức dậy, nó luôn truy vấn trạng thái mới nhất từ Informer Cache để quyết định hành động.**

---

## 2. Kiến trúc toàn cảnh của một client-go Controller

Sơ đồ khái niệm phân nhánh dưới đây mô tả chính xác luồng dữ liệu một chiều từ cụm Kubernetes qua `client-go` vào worker điều hòa:

~~~
[Kubernetes API Server]
         │ (HTTP Stream / Chunked)
         ▼
    [Reflector] ──> List / Watch
         │
         ▼
    [DeltaFIFO]
         │
         ├── Cập nhật ──> [Indexer Cache]
         │                       ▲
         ▼                       │ (Đọc snapshot)
   [SharedInformer]              │
         │                       │
         ▼                       │
  (ResourceEventHandler)         │
         │ (Chỉ lấy Key)         │
         ▼                       │
[Typed Rate-Limited WorkQueue]   │
  - queue:      thứ tự chờ       │
  - dirty:      gộp trùng lặp    │
  - processing: khóa độc quyền   │
         │                       │
         ▼                       │
     [Worker] ───────────────────┘
         │
         ▼ (Thực thi Reconcile)
   [Ghi API Server / Ngoại vi]
~~~

### Bốn thành phần then chốt trong chuỗi cung ứng dữ liệu

1. **Reflector:** Chịu trách nhiệm mở kết nối tới API Server, thực thi giao thức **List/Watch**, và đổ các biến động vào bộ đệm `DeltaFIFO`.
2. **Indexer (Local Store):** Một bộ nhớ đệm in-memory thread-safe được đồng bộ hóa liên tục với API Server. Mọi tác vụ đọc của controller đều truy vấn vào đây với độ trễ cỡ microsecond thay vì gửi yêu cầu HTTP đè nặng lên API Server.
3. **SharedInformer:** Phân phối các sự kiện từ `DeltaFIFO` tới các hàm lắng nghe (`ResourceEventHandlerFuncs`), đồng thời bảo đảm local cache luôn được cập nhật trước khi event handler kích hoạt.
4. **Typed Rate-Limited WorkQueue:** Hàng đợi chuyên dụng giúp gộp trùng sự kiện (deduplication), kiểm soát tốc độ thử lại (rate-limiting & backoff), và ngăn ngừa xung đột xử lý đồng thời trên cùng một tài nguyên.

---

## 3. Giao thức List/Watch và vai trò của resourceVersion

Vì sao Kubernetes không dùng truy vấn định kỳ (Polling) và cũng không dùng WebSocket đơn thuần? Câu trả lời nằm ở sự kết hợp hoàn hảo giữa **List** và **Watch** thông qua biến định danh **resourceVersion**.

~~~
Client                                    API Server
  │                                           │
  │ 1. GET /api/v1/pods (List)                │
  ├──────────────────────────────────────────>│
  │ <── Danh sách Pods + rv = "1040" ─────────┤
  │                                           │
  │ 2. GET /api/v1/pods?watch=true&rv=1040    │
  ├──────────────────────────────────────────>│
  │ <── HTTP 200 OK (chunked stream) ─────────┤
  │ <── Event: ADDED pod-a (rv=1041) ─────────┤
  │ <── Event: MODIFIED pod-b (rv=1042) ──────┤
  │     ... (Mạng bị ngắt đột ngột) ...       │
  │                                           │
  │ 3. GET /api/v1/pods?watch=true&rv=1042    │
  ├──────────────────────────────────────────>│
  │ <── Nối tiếp stream không mất sự kiện ────┤
~~~

### Cơ chế hoạt động:

1. **Pha List (Khởi tạo nền tảng):** Khi controller vừa bật, Reflector gọi API `List` để lấy toàn bộ các đối tượng hiện hữu. API Server trả về danh sách đối tượng kèm theo giá trị `resourceVersion` đại diện cho commit log mới nhất của etcd tại thời điểm đó (ví dụ: `1040`). Reflector lưu dữ liệu vào `Indexer`.
2. **Pha Watch (Đón nhận gia số):** Ngay sau khi List thành công, Reflector mở một kết nối HTTP dạng chunked stream với tham số `?watch=true&resourceVersion=1040`. API Server chỉ truyền về những thay đổi diễn ra sau mốc `1040`.
3. **Tự phục hồi sau sự cố mạng:** Nếu đường truyền bị đứt ở sự kiện `1042`, Reflector tự động kết nối lại và yêu cầu phát tiếp từ `1042`. Nó không cần phải tải lại hàng nghìn Pod từ đầu!
4. **Lỗi HTTP 410 Gone:** Nếu kết nối bị gián đoạn quá lâu khiến etcd đã dọn dẹp các bản ghi lịch sử (compact log), API Server sẽ trả về mã lỗi `410 Gone (Too old resource version)`. Khi đó, Reflector hiểu rằng khoảng trống dữ liệu không thể bù đắp, nó sẽ tự động kích hoạt một chu kỳ `List` mới từ đầu để tái lập snapshot chuẩn.

---

## 4. Xử lý xóa và bí ẩn của Tombstone

Trong vòng đời của một tài nguyên, sự kiện xóa (`OnDelete`) ẩn chứa một cạm bẫy kỹ thuật kinh điển mà hầu hết kỹ sư mới tiếp cận `client-go` đều vấp phải: **Tombstone** (Bia mộ dữ liệu).

Thông thường, khi một đối tượng bị xóa, hàm `DeleteFunc` nhận được chính struct của đối tượng đó. Nhưng nếu kết nối mạng bị rớt đúng lúc đối tượng bị xóa trên API Server, đến khi Informer kết nối lại và phát hiện đối tượng đã biến mất, nó không còn giữ struct nguyên vẹn nữa. Thay vào đó, Informer bọc đối tượng vào cấu trúc `cache.DeletedFinalStateUnknown`.

Nếu bạn ép kiểu trực tiếp:
~~~go
// CẢNH BÁO: Panic runtime nếu đối tượng rơi vào Tombstone!
pod := obj.(*corev1.Pod)
~~~
Chương trình sẽ văng lỗi `panic: interface conversion: interface {} is cache.DeletedFinalStateUnknown, not *v1.Pod`.

### Giải pháp an toàn tiêu chuẩn:

Thư viện `client-go` cung cấp hàm chuẩn hóa `cache.DeletionHandlingMetaNamespaceKeyFunc`:

~~~go
func (c *Controller) handleDelete(obj any) {
	key, err := cache.DeletionHandlingMetaNamespaceKeyFunc(obj)
	if err != nil {
		runtime.HandleError(err)
		return
	}
	c.queue.Add(key)
}
~~~

Hàm này tự động kiểm tra: nếu `obj` là một struct thông thường, nó trích xuất key `namespace/name`. Nếu `obj` là `cache.DeletedFinalStateUnknown`, nó sẽ trích xuất key từ bia mộ lưu trữ bên trong một cách an toàn tuyệt đối.

---

## 5. Hàng đợi WorkQueue: Ba tập hợp và Kiểm soát tốc độ

Trong Go chuẩn, `chan` chỉ là một hàng đợi FIFO đơn thuần. `client-go` trang bị cấu trúc `workqueue.TypedRateLimitingInterface[T]` với thuật toán phối hợp ba tập hợp dữ liệu:

| Tập hợp | Ý nghĩa kỹ thuật | Trách nhiệm |
| :--- | :--- | :--- |
| `queue []T` | Danh sách thứ tự chờ | Xác định key nào sẽ được worker lấy ra xử lý kế tiếp. |
| `dirty set[T]` | Tập hợp các key bị bẩn | Lưu các key có sự kiện phát sinh nhưng chưa hoàn tất điều hòa. Giúp **gộp trùng lặp (deduplication)**. |
| `processing set[T]` | Tập hợp key đang xử lý | Khóa độc quyền (exclusive lock logic). Bảo đảm **không bao giờ có 2 worker xử lý cùng một key tại một thời điểm**. |

### Quy trình điều phối của WorkQueue

~~~
Sự kiện tới: Add(key)
  │
  ├─> Đã có trong dirty? ──(Có)──> [Bỏ qua - Đã gộp!]
  │         │ (Không)
  │         ▼
  │     Thêm vào dirty
  │
  ├─> Đang xử lý? ─────────(Có)──> [Chờ worker hiện tại]
  │         │ (Không)
  │         ▼
  └─> Đẩy vào queue slice ──> Worker gọi Get() lấy ra
                                 │
                                 ├─> Xóa khỏi dirty
                                 └─> Thêm vào processing
~~~

Khi worker xử lý xong, nó bắt buộc phải gọi `queue.Done(key)`. Lúc này WorkQueue sẽ xóa key khỏi tập `processing`. Nếu trong quá trình worker đang chạy mà có sự kiện mới tới (key đã được đánh dấu vào `dirty`), `Done()` sẽ tự động đưa key đó trở lại `queue` để xử lý tiếp!

### Cơ chế Rate Limiting: Quên hay Phạt?

Một worker sau khi xử lý xong một lượt điều hòa (`reconcile`) sẽ đứng trước hai tình huống:

1. **Thành công:** Gọi `c.queue.Forget(key)` để xóa sạch lịch sử số lần thất bại, đưa bộ đếm backoff về mức 0, và gọi `c.queue.Done(key)`.
2. **Thất bại tạm thời (Transient Error):** Không gọi `Forget`. Thay vào đó, gọi `c.queue.AddRateLimited(key)`. Hàng đợi sẽ áp dụng thuật toán lũy thừa cơ số 2 kết hợp jitter (Exponential Backoff): `T_wait = base * 2^failures ± jitter`. Điều này bảo vệ hệ thống không bị đổ vỡ dây chuyền khi một dịch vụ phụ thuộc tạm thời không phản hồi.

---

## 6. Hiện thực Controller hoàn chỉnh trong Go

Dưới đây là phần hiện thực cốt lõi của controller từ dự án mẫu `labs/part22-client-go-controller/controller.go`. Mã nguồn tuân thủ chặt chẽ API Generic mới nhất của `client-go v0.37.0`:

~~~go
type Reconciler interface {
	Reconcile(ctx context.Context, key string) error
}

type Controller struct {
	indexer    cache.Indexer
	queue      workqueue.TypedRateLimitingInterface[string]
	informer   cache.SharedIndexInformer
	reconciler Reconciler
}
~~~

Hàm khởi chạy `Run` bảo đảm khế ước đồng bộ hóa bộ nhớ đệm trước khi phân phối công việc cho các worker:

~~~go
func (c *Controller) Run(
	ctx context.Context, workers int,
) error {
	defer runtime.HandleCrash()
	defer c.queue.ShutDown()

	// Khế ước bắt buộc: Đợi local cache đồng bộ hoàn tất
	if c.informer != nil {
		synced := cache.WaitForNamedCacheSyncWithContext(
			ctx, c.informer.HasSynced,
		)
		if !synced {
			return fmt.Errorf("hết hạn chờ sync cache")
		}
	}

	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for c.processNextItem(ctx) {
			}
		}()
	}

	<-ctx.Done()
	c.queue.ShutDown()
	wg.Wait()
	return nil
}
~~~

### Vòng lặp điều phối của từng Worker

Mỗi worker lấy một key ra khỏi hàng đợi và bọc trong khối bảo vệ:

~~~go
func (c *Controller) processNextItem(ctx context.Context) bool {
	key, shutdown := c.queue.Get()
	if shutdown {
		return false
	}
	defer c.queue.Done(key)

	err := c.reconcileHandler(ctx, key)
	if err == nil {
		// Thành công: Xóa lịch sử retry để giải phóng bộ nhớ
		c.queue.Forget(key)
		return true
	}

	// Thất bại: Thử lại có kiểm soát tốc độ (tối đa 5 lần)
	if c.queue.NumRequeues(key) < 5 {
		c.queue.AddRateLimited(key)
		return true
	}

	// Đã vượt quá ngưỡng thử lại: Hủy bỏ và ghi log lỗi
	c.queue.Forget(key)
	runtime.HandleError(
		fmt.Errorf(
			"bỏ cuộc sau 5 lần thử key %q: %w", key, err,
		),
	)
	return true
}
~~~

### Logic hòa giải: Đọc từ Cache thay vì Payload sự kiện

~~~go
func (c *Controller) reconcileHandler(
	ctx context.Context, key string,
) error {
	// 1. Luôn truy vấn snapshot mới nhất từ local indexer
	obj, exists, err := c.indexer.GetByKey(key)
	if err != nil {
		return fmt.Errorf("lỗi đọc cache key %s: %w", key, err)
	}

	if !exists {
		// Tài nguyên đã bị xóa hoàn toàn khỏi cụm
		return c.reconciler.Reconcile(ctx, key)
	}

	pod, ok := obj.(*corev1.Pod)
	if !ok {
		return fmt.Errorf("sai kiểu *corev1.Pod: %T", obj)
	}

	// Không xử lý pod đang trong tiến trình bị xóa dở
	if pod.DeletionTimestamp != nil {
		return nil
	}

	return c.reconciler.Reconcile(ctx, key)
}
~~~

---

## 7. Bằng chứng kiểm thử: Kiểm chứng 6 hành vi then chốt

Để chứng minh controller hoạt động chính xác dưới mọi điều kiện biên khắc nghiệt, bộ kiểm thử tự động tại `labs/part22-client-go-controller/controller_test.go` đã được thiết kế để đo lường 6 đặc tính cốt lõi:

~~~
=== RUN   TestEventDeduplication
--- PASS: TestEventDeduplication (0.00s)
=== RUN   TestCacheNewerThanEvent
--- PASS: TestCacheNewerThanEvent (0.00s)
=== RUN   TestRateLimitedRetryDecoupledFromDomain
--- PASS: TestRateLimitedRetryDecoupledFromDomain (0.00s)
=== RUN   TestSafeDeletionAndTombstone
--- PASS: TestSafeDeletionAndTombstone (0.00s)
=== RUN   TestCleanCancellationShutdown
--- PASS: TestCleanCancellationShutdown (0.05s)
=== RUN   TestCacheNotSyncedGuard
--- PASS: TestCacheNotSyncedGuard (0.02s)
PASS
ok      part22-client-go-controller   3.829s
~~~

### 1. Bằng chứng gộp trùng sự kiện (TestEventDeduplication)
Bắn liên tiếp 10 sự kiện cập nhật cho cùng một Pod `production/payment-api` vào Informer. Nhờ cơ chế `dirty set` của WorkQueue, hàm `Reconcile` chỉ bị kích hoạt **đúng 1 lần duy nhất**, giúp loại bỏ 90% tải điều hòa vô ích.

### 2. Đọc trạng thái mới từ Cache thay vì Payload cũ (TestCacheNewerThanEvent)
Sự kiện đầu tiên phát ra với nhãn `version: "v1"`. Trước khi worker kịp chạy, nhãn trong Informer cache đã được cập nhật thành `version: "v3"`. Khi worker thức dậy, giá trị nó nhận được là `v3`, chứng minh controller không bị đầu độc bởi dữ liệu cũ từ kênh sự kiện.

### 3. Tách biệt lỗi tạm thời và Lũy thừa thử lại (TestRateLimitedRetry)
Giả lập hàm `Reconcile` trả về lỗi kết nối mạng tạm thời. Test kiểm chứng rằng:
- Lần chạy đầu thất bại: key được đẩy vào `AddRateLimited` thay vì vứt bỏ.
- Lần chạy thứ hai thành công: `Forget(key)` được gọi ngay lập tức để xóa sạch vết backoff.

### 4. An toàn trước Tombstone (TestSafeDeletionAndTombstone)
Đưa trực tiếp một struct `cache.DeletedFinalStateUnknown` vào hàm `handleDelete`. Chương trình không hề bị panic runtime mà giải mã chính xác key `default/orphaned-pod` để tiến hành dọn dẹp tài nguyên.

### 5. Dừng sạch tài nguyên (TestCleanCancellationShutdown)
Khi gọi `cancel()` trên `context.Context`, tất cả worker đang chạy trong pool kết thúc vòng lặp, hàng đợi đóng cổng nhận việc (`ShutDown`), và hàm `ctrl.Run` thoát an toàn trong vòng dưới 50 mili-giây mà không để lại bất kỳ goroutine rò rỉ nào.

### 6. Khế ước bảo vệ Cache Chưa Đồng Bộ (TestCacheNotSyncedGuard)
Nếu giả lập mạng chập chờn khiến `cache.WaitForNamedCacheSyncWithContext` trả về `false` (timeout), controller lập tức từ chối khởi động worker và trả về lỗi rõ ràng: `timed out waiting for cache sync`. Điều này ngăn chặn triệt để thảm kịch worker xử lý trên một bộ nhớ đệm rỗng.

---

## 8. Kiểm soát đồng thời lạc quan (OCC) và Lỗi 409 Conflict

Khi controller quyết định cập nhật trạng thái Pod lên API Server, nó gửi một lệnh HTTP `PUT` hoặc `PATCH`. Trong môi trường phân tán, một controller khác hoặc người dùng thông qua `kubectl` có thể đã sửa đổi Pod đó trước bạn một phần nghìn giây.

Kubernetes sử dụng cơ chế **Optimistic Concurrency Control (OCC)** dựa trên trường `metadata.resourceVersion`. Nếu `resourceVersion` trong yêu cầu gửi lên không trùng khớp với bản ghi hiện thời trong etcd, API Server sẽ lập tức từ chối với mã lỗi HTTP `409 Conflict`:

~~~
Operation cannot be fulfilled on pods "payment-api":
the object has been modified; please apply your changes
to the latest version and try again
~~~

### Mẫu hình chuẩn: retry.RetryOnConflict

Tuyệt đối không coi 409 là một lỗi hệ thống nghiêm trọng khiến controller sập nguồn. Đây là một hiện tượng bình thường trong hệ phân tán. Cách xử lý chuẩn xác bằng `k8s.io/client-go/util/retry`:

~~~go
func updatePodAnnotation(
	ctx context.Context,
	client kubernetes.Interface,
	namespace, name string,
) error {
	return retry.RetryOnConflict(
		retry.DefaultRetry,
		func() error {
			// 1. Phải Get lại bản ghi mới nhất
			latest, err := client.CoreV1().Pods(namespace).Get(
				ctx, name, metav1.GetOptions{},
			)
			if err != nil {
				return err
			}

			// 2. Thực hiện sửa đổi trên bản sao mới
			if latest.Annotations == nil {
				latest.Annotations = make(map[string]string)
			}
			now := time.Now().UTC().Format(time.RFC3339)
			latest.Annotations["reconciled-at"] = now

			// 3. Ghi đè lại API Server
			_, err = client.CoreV1().Pods(namespace).Update(
				ctx, latest, metav1.UpdateOptions{},
			)
			return err
		},
	)
}
~~~

Mẫu hình này tự động thử lại với backoff ngắn, đọc lại snapshot mới nhất của đối tượng, áp dụng thay đổi và lưu lại.

---

## 9. Các cạm bẫy người học thường gặp (Learner Pitfalls)

| Cạm bẫy thực tế | Hậu quả trên Production | Giải pháp phòng ngừa |
| :--- | :--- | :--- |
| **Đọc trực tiếp API Server** thay vì dùng Informer Cache. | Gây bão yêu cầu (Thundering Herd) làm sập API Server khi có hàng ngàn Pod biến động. | Đọc dữ liệu từ `c.indexer.GetByKey(key)`. Chỉ gọi API Server khi thực hiện lệnh ghi. |
| **Quên gọi Done(key)** khi kết thúc hàm xử lý. | Key bị kẹt vĩnh viễn trong tập `processing`. Mọi sự kiện tiếp theo của Pod này bị bỏ qua hoàn toàn. | Luôn đặt `defer c.queue.Done(key)` ngay sau khi `queue.Get()`. |
| **Gọi Forget(key)** khi Reconcile gặp lỗi. | Làm mất lịch sử thử lại của key. Backoff bị xóa bỏ, dẫn đến bão thử lại liên tục. | Chỉ gọi `Forget(key)` khi điều hòa thành công hoặc khi quyết định từ bỏ sau nhiều lần thử. |
| **Chạy worker pool** trước khi đồng bộ xong cache. | Worker nhìn thấy cache rỗng và tưởng tài nguyên đã bị xóa, kích hoạt hành động phá hủy dữ liệu. | Bắt buộc phải chặn ở hàm `cache.WaitForNamedCacheSyncWithContext` trước khi kích hoạt worker. |

---

## 10. Bài tập thực hành thiết kế Controller

### Thử thách 1: Tích hợp Metric đo đạc độ trễ và chiều sâu hàng đợi
**Yêu cầu:** Hãy thiết kế hai metric Prometheus để giám sát sức khỏe của controller:
1. `controller_workqueue_depth`: Gauge đo số lượng key đang chờ xử lý trong `queue`.
2. `controller_reconcile_duration_seconds`: Histogram đo thời gian thực thi của một chu kỳ `Reconcile`.

*Gợi ý:* Đặt điểm đo `time.Now()` trước khi gọi `c.reconciler.Reconcile` và cập nhật metric trong lệnh `defer`.

### Thử thách 2: Xử lý Pod bị cô lập (Orphaned Pod Cleanup)
**Yêu cầu:** Một dịch vụ bên ngoài tạo ra tài nguyên tạm (ví dụ file log trên ổ đĩa mạng chia sẻ). Khi Pod tương ứng bị xóa khỏi Kubernetes, controller phải dọn dẹp file log này. Hãy viết hàm `Reconcile` xử lý trường hợp `!exists` (đối tượng không còn trong Cache) nhưng vẫn trích xuất được `namespace` và `name` từ `key` để thực hiện dọn dẹp an toàn.

---

## 11. Hướng dẫn giải và Phân tích kiến trúc bài tập

### Lời giải Thử thách 1: Đo lường quan sát controller

Khai báo các bộ đo Prometheus:

~~~go
var (
	queueDepth = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "controller_workqueue_depth",
			Help: "Số lượng phần tử đang chờ trong workqueue",
		},
		[]string{"controller"},
	)
	reconcileDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "controller_reconcile_duration_seconds",
			Help:    "Thời gian thực thi hàm Reconcile",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"controller", "status"},
	)
)
~~~

Thu thập số liệu đo lường trong vòng lặp xử lý:

~~~go
func (c *Controller) processNextItemWithMetrics(
	ctx context.Context,
) bool {
	key, shutdown := c.queue.Get()
	if shutdown {
		return false
	}
	defer c.queue.Done(key)

	start := time.Now()
	err := c.reconcileHandler(ctx, key)
	duration := time.Since(start).Seconds()

	status := "success"
	if err != nil {
		status = "error"
	}
	reconcileDuration.WithLabelValues(
		"pod_controller", status,
	).Observe(duration)
	// ... xử lý retry tiếp theo
	return true
}
~~~

### Lời giải Thử thách 2: Xử lý dọn dẹp tài nguyên cô lập
~~~go
func (r *CleanUpReconciler) Reconcile(
	ctx context.Context, key string,
) error {
	namespace, name, err := cache.SplitMetaNamespaceKey(key)
	if err != nil {
		return fmt.Errorf("key sai %q: %w", key, err)
	}

	obj, exists, err := r.indexer.GetByKey(key)
	if err != nil {
		return err
	}

	if !exists {
		// Pod không còn trong cache -> Đã bị xóa trên cụm
		// Tiến hành dọn dẹp tài nguyên ngoại vi an toàn
		log.Printf("Pod %s/%s mất. Dọn dẹp...", namespace, name)
		return r.externalStorage.DeleteArtifacts(
			ctx, namespace, name,
		)
	}

	// Pod vẫn tồn tại -> Điều hòa trạng thái bình thường
	_ = obj.(*corev1.Pod)
	return nil
}
~~~

---

Kiến trúc **List/Watch + Informer Cache + Rate-Limited WorkQueue** được phân tích trong chương này chính là nền móng của toàn bộ hệ sinh thái Kubernetes. Trong Chương 23, chúng ta sẽ đưa mẫu hình này lên một tầm cao mới: xây dựng một **Kubernetes Operator** thực thụ với Custom Resource Definition (CRD), bộ điều khiển `controller-runtime`, quản lý vòng đời tài nguyên và cơ chế bảo vệ xóa bằng **Finalizer**.
