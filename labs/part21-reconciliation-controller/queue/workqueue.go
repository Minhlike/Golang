package queue

import (
	"sync"
	"time"
)

// RateLimiterConfig xác định các tham số cho thuật toán Exponential Backoff.
type RateLimiterConfig struct {
	BaseDelay  time.Duration
	MaxDelay   time.Duration
	MaxRetries int
}

// DefaultRateLimiterConfig trả về cấu hình an toàn mặc định cho worker queue.
func DefaultRateLimiterConfig() RateLimiterConfig {
	return RateLimiterConfig{
		BaseDelay:  50 * time.Millisecond,
		MaxDelay:   2 * time.Second,
		MaxRetries: 5,
	}
}

// WorkQueue là hàng đợi công việc hỗ trợ deduplication, rate limiting và xử lý song song an toàn.
// Kiến trúc này phản ánh chính xác thiết kế lõi của Kubernetes client-go workqueue:
// 1. Deduplication: Nhiều sự kiện dồn về cùng một resource key chỉ sinh ra một lượt reconcile.
// 2. Serialized processing per key: Tại một thời điểm, chỉ có tối đa một worker xử lý một key cụ thể.
// 3. Rate-limited backoff: Tránh bão retry (retry storm) khi tài nguyên đích gặp sự cố kéo dài.
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

// NewWorkQueue khởi tạo một WorkQueue mới với cấu hình rate limiter tùy chọn.
func NewWorkQueue(cfg RateLimiterConfig) *WorkQueue {
	if cfg.BaseDelay <= 0 {
		cfg.BaseDelay = 50 * time.Millisecond
	}
	if cfg.MaxDelay <= 0 {
		cfg.MaxDelay = 2 * time.Second
	}
	if cfg.MaxRetries <= 0 {
		cfg.MaxRetries = 5
	}

	q := &WorkQueue{
		dirty:      make(map[string]struct{}),
		processing: make(map[string]struct{}),
		failures:   make(map[string]int),
		config:     cfg,
	}
	q.cond = sync.NewCond(&q.mu)
	return q
}

// Add đưa một item vào hàng đợi. Nếu item đã nằm trong dirty set (đang đợi xử lý),
// lời gọi này sẽ được deduplicate (gộp lại) mà không tốn thêm slot trong slice.
func (q *WorkQueue) Add(item string) {
	q.mu.Lock()
	defer q.mu.Unlock()

	if q.shuttingDown {
		return
	}

	// Nếu đã nằm trong dirty, sự kiện mới được gộp vào đợt xử lý sắp tới
	if _, exists := q.dirty[item]; exists {
		return
	}

	q.dirty[item] = struct{}{}

	// Nếu item đang được một worker xử lý, ta không đẩy vào slice ngay
	// để tránh 2 worker cùng reconcile một key song song. Khi worker hiện tại
	// gọi Done(), item sẽ được tự động đẩy vào slice tiếp.
	if _, isProcessing := q.processing[item]; isProcessing {
		return
	}

	q.queue = append(q.queue, item)
	q.cond.Signal()
}

// Get lấy phần tử tiếp theo từ hàng đợi. Hàm sẽ block cho đến khi có item
// hoặc hàng đợi được yêu cầu tắt (ShutDown).
func (q *WorkQueue) Get() (item string, shutdown bool) {
	q.mu.Lock()
	defer q.mu.Unlock()

	for len(q.queue) == 0 && !q.shuttingDown {
		q.cond.Wait()
	}

	if len(q.queue) == 0 {
		// Hàng đợi đã tắt và không còn việc dở dang
		return "", true
	}

	item = q.queue[0]
	q.queue = q.queue[1:]

	q.processing[item] = struct{}{}
	delete(q.dirty, item)

	return item, false
}

// Done thông báo worker đã hoàn tất xử lý item.
// Nếu trong lúc worker đang xử lý, có một lời gọi Add(item) khác xuất hiện
// (item nằm lại trong dirty set), item sẽ lập tức được đẩy lại vào queue slice.
func (q *WorkQueue) Done(item string) {
	q.mu.Lock()
	defer q.mu.Unlock()

	delete(q.processing, item)

	// Nếu trong lúc chạy có sự kiện mới cho cùng key này
	if _, exists := q.dirty[item]; exists {
		q.queue = append(q.queue, item)
		q.cond.Signal()
	}
}

// AddRateLimited tính toán thời gian trễ theo Exponential Backoff và xếp lịch đưa item
// trở lại hàng đợi sau khoảng thời gian đó. Nếu số lần thất bại vượt quá MaxRetries,
// hàm trả về false và từ bỏ retry để tránh làm cạn kiệt tài nguyên hệ thống.
func (q *WorkQueue) AddRateLimited(item string) bool {
	q.mu.Lock()
	defer q.mu.Unlock()

	if q.shuttingDown {
		return false
	}

	failures := q.failures[item] + 1
	q.failures[item] = failures

	if failures > q.config.MaxRetries {
		return false
	}

	// Exponential backoff: base * 2^(failures-1)
	backoffMultiplier := 1 << (failures - 1)
	delay := q.config.BaseDelay * time.Duration(backoffMultiplier)
	if delay > q.config.MaxDelay {
		delay = q.config.MaxDelay
	}

	time.AfterFunc(delay, func() {
		q.Add(item)
	})

	return true
}

// Forget xóa bỏ lịch sử thất bại của item sau khi reconcile thành công,
// giúp các lần lỗi trong tương lai được tính toán lại từ mức delay cơ sở ban đầu.
func (q *WorkQueue) Forget(item string) {
	q.mu.Lock()
	defer q.mu.Unlock()

	delete(q.failures, item)
}

// NumRequeues trả về số lần item đã bị retry thất bại.
func (q *WorkQueue) NumRequeues(item string) int {
	q.mu.Lock()
	defer q.mu.Unlock()

	return q.failures[item]
}

// ShutDown đóng hàng đợi và đánh thức toàn bộ goroutine đang chờ trong Get().
func (q *WorkQueue) ShutDown() {
	q.mu.Lock()
	defer q.mu.Unlock()

	q.shuttingDown = true
	q.cond.Broadcast()
}

// Len trả về số lượng item đang chờ trong hàng đợi.
func (q *WorkQueue) Len() int {
	q.mu.Lock()
	defer q.mu.Unlock()

	return len(q.queue)
}
