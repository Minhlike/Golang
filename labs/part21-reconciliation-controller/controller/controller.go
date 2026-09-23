package controller

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	"example.com/golang-master/part21-reconciliation-controller/queue"
)

// Result thể hiện kết quả sau một chu kỳ reconcile.
type Result struct {
	// Requeue chỉ định có cần đưa key trở lại hàng đợi hay không
	Requeue bool
	// RequeueAfter chỉ định thời gian trễ trước khi đưa key trở lại hàng đợi (periodic sync)
	RequeueAfter time.Duration
}

// Reconciler định nghĩa hợp đồng điều hòa trạng thái cho một tài nguyên.
// Nguyên tắc cốt lõi: Hàm Reconcile phải có tính Lũy Thừa (Idempotent).
// Việc thực thi Reconcile 1 lần hay nhiều lần với cùng một trạng thái
// phải đem lại cùng một kết quả mà không sinh ra tác dụng phụ ngoài ý muốn.
type Reconciler interface {
	Reconcile(ctx context.Context, key string) (Result, error)
}

// Controller quản lý vòng đời của worker pool và điều phối các chu kỳ reconcile.
type Controller struct {
	name        string
	reconciler  Reconciler
	queue       *queue.WorkQueue
	concurrency int
}

// Config chứa các tham số khởi tạo Controller.
type Config struct {
	Name        string
	Reconciler  Reconciler
	RateLimiter queue.RateLimiterConfig
	Concurrency int
}

// NewController khởi tạo một Controller điều hòa với worker pool cố định.
func NewController(cfg Config) *Controller {
	if cfg.Concurrency <= 0 {
		cfg.Concurrency = 2
	}
	if cfg.Name == "" {
		cfg.Name = "generic-controller"
	}

	q := queue.NewWorkQueue(cfg.RateLimiter)
	return &Controller{
		name:        cfg.Name,
		reconciler:  cfg.Reconciler,
		queue:       q,
		concurrency: cfg.Concurrency,
	}
}

// Enqueue đưa một resource key vào hàng đợi điều hòa.
func (c *Controller) Enqueue(key string) {
	c.queue.Add(key)
}

// Run khởi chạy worker pool và chặn cho đến khi ctx bị hủy hoặc hàng đợi tắt hoàn toàn.
func (c *Controller) Run(ctx context.Context) error {
	var wg sync.WaitGroup

	// Đảm bảo khi context bị hủy, hàng đợi sẽ được phát tín hiệu tắt
	// để đánh thức toàn bộ worker goroutine đang block ở queue.Get()
	go func() {
		<-ctx.Done()
		c.queue.ShutDown()
	}()

	// Khởi chạy worker goroutines
	for i := 0; i < c.concurrency; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for c.processNextWorkItem(ctx) {
			}
		}(i)
	}

	// Chờ toàn bộ worker thoát an toàn (graceful shutdown)
	wg.Wait()
	return ctx.Err()
}

// processNextWorkItem lấy một item từ queue và thực thi chu trình điều hòa.
// Trả về false khi hàng đợi đã đóng và không còn item nào cần xử lý.
func (c *Controller) processNextWorkItem(ctx context.Context) bool {
	key, shutdown := c.queue.Get()
	if shutdown {
		return false
	}
	defer c.queue.Done(key)

	// Thực thi vòng lặp điều hòa với timeout cục bộ cho từng lượt reconcile
	reconcileCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	res, err := c.reconciler.Reconcile(reconcileCtx, key)
	cancel()

	if err != nil {
		// Nếu xảy ra lỗi: đưa vào hàng đợi với Exponential Backoff
		if !errors.Is(err, context.Canceled) {
			requeued := c.queue.AddRateLimited(key)
			if !requeued {
				// Đã vượt quá số lần retry tối đa; ghi nhận lỗi để tránh bão retry
				c.queue.Forget(key)
			}
		}
		return true
	}

	// Nếu thành công: xóa lịch sử thất bại để reset backoff
	c.queue.Forget(key)

	// Nếu reconciler yêu cầu định thời RequeueAfter
	if res.RequeueAfter > 0 {
		time.AfterFunc(res.RequeueAfter, func() {
			c.queue.Add(key)
		})
	} else if res.Requeue {
		c.queue.Add(key)
	}

	return true
}

// TargetState thể hiện trạng thái thực tế của một dịch vụ mục tiêu.
type TargetState struct {
	ID        string
	Healthy   bool
	Replicas  int
	LastHeal  time.Time
	FailCount int
}

// SelfHealingReconciler là một implementation mẫu điều hòa tự phục hồi dịch vụ:
// Khi phát hiện dịch vụ bị unhealthy hoặc thiếu hụt số bản sao mong muốn (desired replicas),
// nó sẽ thực hiện hành động tự chữa lành (heal) để đưa trạng thái thực tế về trạng thái mong muốn.
type SelfHealingReconciler struct {
	mu              sync.Mutex
	desiredReplicas int
	actualStates    map[string]*TargetState
	healHook        func(key string) error
}

// NewSelfHealingReconciler khởi tạo reconciler tự phục hồi.
func NewSelfHealingReconciler(desiredReplicas int, healHook func(key string) error) *SelfHealingReconciler {
	return &SelfHealingReconciler{
		desiredReplicas: desiredReplicas,
		actualStates:    make(map[string]*TargetState),
		healHook:        healHook,
	}
}

// SetActualState cập nhật trạng thái thực tế quan sát được (ví dụ từ OpsProbe).
func (r *SelfHealingReconciler) SetActualState(state TargetState) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.actualStates[state.ID] = &state
}

// GetActualState truy vấn trạng thái hiện tại của target.
func (r *SelfHealingReconciler) GetActualState(key string) (TargetState, bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	s, ok := r.actualStates[key]
	if !ok {
		return TargetState{}, false
	}
	return *s, true
}

// Reconcile thực hiện 4 bước của Reconciliation Loop:
// 1. Observe: Đọc trạng thái thực tế của target
// 2. Diff: So sánh với trạng thái mong muốn (Healthy = true, Replicas = desiredReplicas)
// 3. Act: Gọi healHook nếu có sai lệch
// 4. Update: Cập nhật trạng thái mới có tính lũy thừa (idempotency)
func (r *SelfHealingReconciler) Reconcile(ctx context.Context, key string) (Result, error) {
	r.mu.Lock()
	state, exists := r.actualStates[key]
	if !exists {
		r.mu.Unlock()
		// Target không tồn tại: no-op, không requeue
		return Result{}, nil
	}

	// Kiểm tra sai lệch (Diff)
	isDegraded := !state.Healthy || state.Replicas < r.desiredReplicas
	r.mu.Unlock()

	if !isDegraded {
		// Trạng thái thực tế đã khớp với trạng thái mong muốn: Idempotent no-op
		return Result{}, nil
	}

	// Thực hiện hành động tự chữa lành (Act)
	if r.healHook != nil {
		if err := r.healHook(key); err != nil {
			return Result{}, fmt.Errorf("heal target %s failed: %w", key, err)
		}
	}

	// Đưa trạng thái thực tế về trạng thái mong muốn
	r.mu.Lock()
	state.Healthy = true
	state.Replicas = r.desiredReplicas
	state.LastHeal = time.Now()
	r.mu.Unlock()

	return Result{}, nil
}
