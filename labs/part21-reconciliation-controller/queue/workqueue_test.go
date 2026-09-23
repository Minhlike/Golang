package queue

import (
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestWorkQueue_Deduplication(t *testing.T) {
	q := NewWorkQueue(DefaultRateLimiterConfig())

	// Thêm 5 lần cùng một key "service-api"
	for i := 0; i < 5; i++ {
		q.Add("service-api")
	}

	if q.Len() != 1 {
		t.Fatalf("expected queue length 1 after deduplication, got %d", q.Len())
	}

	item, shutdown := q.Get()
	if shutdown || item != "service-api" {
		t.Fatalf("expected item 'service-api', got %s (shutdown=%t)", item, shutdown)
	}

	if q.Len() != 0 {
		t.Fatalf("expected empty queue after get, got %d", q.Len())
	}

	q.Done(item)
}

func TestWorkQueue_SerializedProcessingPerKey(t *testing.T) {
	q := NewWorkQueue(DefaultRateLimiterConfig())

	q.Add("item-1")

	// Worker 1 lấy item-1 ra xử lý
	item, shutdown := q.Get()
	if shutdown || item != "item-1" {
		t.Fatalf("unexpected get: %s, %t", item, shutdown)
	}

	// Trong khi Worker 1 đang xử lý item-1, có sự kiện mới cho cùng key này
	q.Add("item-1")

	// Hàng đợi chưa được cấp phát cho worker khác vì item-1 đang trong processing set
	if q.Len() != 0 {
		t.Fatalf("expected queue length 0 while key is in processing, got %d", q.Len())
	}

	// Worker 1 hoàn thành xử lý
	q.Done(item)

	// Bây giờ item-1 phải tự động xuất hiện trở lại trong queue
	if q.Len() != 1 {
		t.Fatalf("expected item-1 to be re-enqueued after Done, got length %d", q.Len())
	}

	item2, shutdown2 := q.Get()
	if shutdown2 || item2 != "item-1" {
		t.Fatalf("expected re-enqueued item-1, got %s", item2)
	}
	q.Done(item2)
}

func TestWorkQueue_RateLimitingAndMaxRetries(t *testing.T) {
	cfg := RateLimiterConfig{
		BaseDelay:  20 * time.Millisecond,
		MaxDelay:   200 * time.Millisecond,
		MaxRetries: 3,
	}
	q := NewWorkQueue(cfg)

	key := "flaky-target"

	// Lần 1: Retry thành công
	if !q.AddRateLimited(key) {
		t.Fatalf("expected AddRateLimited attempt 1 to succeed")
	}
	if q.NumRequeues(key) != 1 {
		t.Errorf("expected 1 failure recorded, got %d", q.NumRequeues(key))
	}

	// Lần 2
	if !q.AddRateLimited(key) {
		t.Fatalf("expected AddRateLimited attempt 2 to succeed")
	}

	// Lần 3
	if !q.AddRateLimited(key) {
		t.Fatalf("expected AddRateLimited attempt 3 to succeed")
	}

	// Lần 4: Vượt quá MaxRetries (3) -> phải trả về false và từ bỏ
	if q.AddRateLimited(key) {
		t.Fatalf("expected AddRateLimited attempt 4 to fail (exceeded max retries)")
	}

	// Reset qua Forget
	q.Forget(key)
	if q.NumRequeues(key) != 0 {
		t.Errorf("expected 0 failures after Forget, got %d", q.NumRequeues(key))
	}
}

func TestWorkQueue_ConcurrentWorkers(t *testing.T) {
	q := NewWorkQueue(DefaultRateLimiterConfig())

	numItems := 100
	numWorkers := 4

	var processedCount int64
	var wg sync.WaitGroup

	// Khởi chạy worker pool
	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				item, shutdown := q.Get()
				if shutdown {
					return
				}
				// Giả lập xử lý ngắn
				time.Sleep(1 * time.Millisecond)
				atomic.AddInt64(&processedCount, 1)
				q.Done(item)
			}
		}()
	}

	// Bắn 100 items vào queue
	for i := 0; i < numItems; i++ {
		q.Add("key-" + string(rune('A'+(i%26))))
	}

	// Chờ xử lý rồi tắt queue
	time.Sleep(100 * time.Millisecond)
	q.ShutDown()
	wg.Wait()

	if atomic.LoadInt64(&processedCount) == 0 {
		t.Errorf("expected at least some items to be processed")
	}
}
