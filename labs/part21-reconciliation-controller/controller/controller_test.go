package controller

import (
	"context"
	"errors"
	"sync/atomic"
	"testing"
	"time"

	"example.com/golang-master/part21-reconciliation-controller/queue"
)

func TestController_SelfHealing_Success(t *testing.T) {
	var healCalls int64

	reconciler := NewSelfHealingReconciler(3, func(key string) error {
		atomic.AddInt64(&healCalls, 1)
		return nil
	})

	// Thiết lập trạng thái ban đầu bị hỏng: unhealthy, 1 replica (desired là 3)
	reconciler.SetActualState(TargetState{
		ID:       "payment-service",
		Healthy:  false,
		Replicas: 1,
	})

	ctrl := NewController(Config{
		Name:        "test-healer",
		Reconciler:  reconciler,
		RateLimiter: queue.DefaultRateLimiterConfig(),
		Concurrency: 2,
	})

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Khởi chạy controller trong nền
	errCh := make(chan error, 1)
	go func() {
		errCh <- ctrl.Run(ctx)
	}()

	// Đưa key vào hàng đợi điều hòa
	ctrl.Enqueue("payment-service")

	// Chờ điều hòa hoàn tất
	time.Sleep(50 * time.Millisecond)

	// Kiểm tra trạng thái đã được đưa về desired state
	state, ok := reconciler.GetActualState("payment-service")
	if !ok {
		t.Fatalf("expected state to exist")
	}
	if !state.Healthy || state.Replicas != 3 {
		t.Fatalf("expected healthy state with 3 replicas, got: %+v", state)
	}

	if atomic.LoadInt64(&healCalls) != 1 {
		t.Fatalf("expected exactly 1 heal action, got %d", atomic.LoadInt64(&healCalls))
	}

	// Kiểm tra tính Lũy Thừa (Idempotency):
	// Enqueue lại lần nữa khi trạng thái đã chuẩn -> không được gọi heal thêm lần nào
	ctrl.Enqueue("payment-service")
	time.Sleep(50 * time.Millisecond)

	if atomic.LoadInt64(&healCalls) != 1 {
		t.Fatalf("expected heal action to remain 1 after redundant reconcile, got %d", atomic.LoadInt64(&healCalls))
	}

	cancel()
	<-errCh
}

func TestController_HealFailure_RateLimitedBackoff(t *testing.T) {
	var failAttempts int64

	reconciler := NewSelfHealingReconciler(2, func(key string) error {
		atomic.AddInt64(&failAttempts, 1)
		return errors.New("underlying infrastructure unavailable")
	})

	reconciler.SetActualState(TargetState{
		ID:       "database-cluster",
		Healthy:  false,
		Replicas: 0,
	})

	cfg := queue.RateLimiterConfig{
		BaseDelay:  20 * time.Millisecond,
		MaxDelay:   100 * time.Millisecond,
		MaxRetries: 3,
	}

	ctrl := NewController(Config{
		Name:        "fail-backoff-controller",
		Reconciler:  reconciler,
		RateLimiter: cfg,
		Concurrency: 1,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 250*time.Millisecond)
	defer cancel()

	ctrl.Enqueue("database-cluster")

	_ = ctrl.Run(ctx)

	// Đảm bảo controller đã thử lại có backoff và không bị crash
	attempts := atomic.LoadInt64(&failAttempts)
	if attempts < 2 {
		t.Fatalf("expected multiple backoff retry attempts, got %d", attempts)
	}
}

func TestController_GracefulShutdown(t *testing.T) {
	reconciler := NewSelfHealingReconciler(1, func(key string) error {
		time.Sleep(30 * time.Millisecond)
		return nil
	})
	reconciler.SetActualState(TargetState{ID: "worker-1", Healthy: false})

	ctrl := NewController(Config{
		Name:        "shutdown-controller",
		Reconciler:  reconciler,
		Concurrency: 2,
	})

	ctx, cancel := context.WithCancel(context.Background())

	ctrl.Enqueue("worker-1")

	runDone := make(chan error, 1)
	go func() {
		runDone <- ctrl.Run(ctx)
	}()

	// Chờ worker bắt đầu nhận việc rồi hủy context
	time.Sleep(10 * time.Millisecond)
	cancel()

	select {
	case err := <-runDone:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("expected context.Canceled error, got %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatalf("controller failed to shutdown gracefully within deadline")
	}
}
