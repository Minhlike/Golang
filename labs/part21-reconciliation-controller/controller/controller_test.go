package controller

import (
	"context"
	"errors"
	"sync/atomic"
	"testing"
	"time"

	"example.com/golang-master/part21-reconciliation-controller/queue"
)

func TestSelfHealingReconciler_ActionSuccessDoesNotInventObservation(t *testing.T) {
	var healCalls int64
	reconciler := NewSelfHealingReconciler(3, func(context.Context, string) error {
		atomic.AddInt64(&healCalls, 1)
		return nil
	})

	reconciler.SetActualState(TargetState{ID: "payment-service", Replicas: 1})
	if _, err := reconciler.Reconcile(context.Background(), "payment-service"); err != nil {
		t.Fatalf("Reconcile() error = %v", err)
	}

	state, ok := reconciler.GetActualState("payment-service")
	if !ok || state.Healthy || state.Replicas != 1 {
		t.Fatalf("actuator success must not overwrite observation, got %+v", state)
	}

	// Một quan sát độc lập sau đó xác nhận hội tụ. Lần reconcile kế tiếp là no-op.
	reconciler.SetActualState(TargetState{ID: "payment-service", Healthy: true, Replicas: 3})
	if _, err := reconciler.Reconcile(context.Background(), "payment-service"); err != nil {
		t.Fatalf("Reconcile() after observation error = %v", err)
	}
	if got := atomic.LoadInt64(&healCalls); got != 1 {
		t.Fatalf("expected one action after convergence observation, got %d", got)
	}
}

func TestSelfHealingReconciler_ActuatorReceivesCancellation(t *testing.T) {
	started := make(chan struct{})
	reconciler := NewSelfHealingReconciler(1, func(ctx context.Context, _ string) error {
		close(started)
		<-ctx.Done()
		return ctx.Err()
	})
	reconciler.SetActualState(TargetState{ID: "worker-1"})

	ctx, cancel := context.WithCancel(context.Background())
	errCh := make(chan error, 1)
	go func() {
		_, err := reconciler.Reconcile(ctx, "worker-1")
		errCh <- err
	}()
	<-started
	cancel()

	if err := <-errCh; !errors.Is(err, context.Canceled) {
		t.Fatalf("Reconcile() error = %v, want context.Canceled", err)
	}
}

func TestSelfHealingReconciler_DoesNotOverwriteFreshObservation(t *testing.T) {
	started := make(chan struct{})
	release := make(chan struct{})
	reconciler := NewSelfHealingReconciler(2, func(context.Context, string) error {
		close(started)
		<-release
		return nil
	})
	reconciler.SetActualState(TargetState{ID: "api", Replicas: 0})

	errCh := make(chan error, 1)
	go func() {
		_, err := reconciler.Reconcile(context.Background(), "api")
		errCh <- err
	}()
	<-started

	// Hệ thống bên ngoài hội tụ khi Act đang chạy; quan sát mới không được bị ghi đè.
	reconciler.SetActualState(TargetState{ID: "api", Healthy: true, Replicas: 2})
	close(release)
	if err := <-errCh; err != nil {
		t.Fatalf("Reconcile() error = %v", err)
	}
	state, _ := reconciler.GetActualState("api")
	if !state.Healthy || state.Replicas != 2 {
		t.Fatalf("fresh observation was overwritten: %+v", state)
	}
}

func TestController_HealFailure_RateLimitedBackoff(t *testing.T) {
	var failAttempts int64
	reconciler := NewSelfHealingReconciler(2, func(context.Context, string) error {
		atomic.AddInt64(&failAttempts, 1)
		return errors.New("underlying infrastructure unavailable")
	})
	reconciler.SetActualState(TargetState{ID: "database-cluster"})

	ctrl := NewController(Config{
		Name:        "fail-backoff-controller",
		Reconciler:  reconciler,
		RateLimiter: queue.RateLimiterConfig{BaseDelay: 20 * time.Millisecond, MaxDelay: 100 * time.Millisecond, MaxRetries: 3},
		Concurrency: 1,
	})
	ctx, cancel := context.WithTimeout(context.Background(), 250*time.Millisecond)
	defer cancel()
	ctrl.Enqueue("database-cluster")
	_ = ctrl.Run(ctx)
	if attempts := atomic.LoadInt64(&failAttempts); attempts < 2 {
		t.Fatalf("expected multiple backoff retry attempts, got %d", attempts)
	}
}
