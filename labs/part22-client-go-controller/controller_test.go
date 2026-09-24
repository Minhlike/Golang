package controller

import (
	"context"
	"errors"
	"fmt"
	"sync/atomic"
	"testing"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/util/workqueue"
)

// TestEventDeduplication proves that multiple events for the same key collapse
// into a single reconcile action while queued, preventing redundant work.
func TestEventDeduplication(t *testing.T) {
	indexer := cache.NewIndexer(cache.MetaNamespaceKeyFunc, cache.Indexers{})
	queue := workqueue.NewTypedRateLimitingQueue[string](workqueue.DefaultTypedItemBasedRateLimiter[string]())

	pod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Namespace:       "production",
			Name:            "web-proxy",
			ResourceVersion: "100",
		},
	}
	if err := indexer.Add(pod); err != nil {
		t.Fatalf("indexer.Add failed: %v", err)
	}

	ctrl := NewController(Config{
		Indexer: indexer,
		Queue:   queue,
	})

	// Inject 10 rapid duplicate events into workqueue
	for i := 0; i < 10; i++ {
		ctrl.enqueue(pod, "rapid-update")
	}

	// Verify workqueue depth is exactly 1 due to dirty set deduplication
	if queue.Len() != 1 {
		t.Fatalf("expected queue length 1 after 10 duplicate adds, got %d", queue.Len())
	}

	// Process the item
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	ok := ctrl.processNextItem(ctx)
	if !ok {
		t.Fatalf("expected processNextItem to return true")
	}

	// Queue should now be empty
	if queue.Len() != 0 {
		t.Fatalf("expected queue length 0 after processing, got %d", queue.Len())
	}

	if ctrl.ReconcileCount() != 1 {
		t.Fatalf("expected exactly 1 reconcile pass, got %d", ctrl.ReconcileCount())
	}

	results := ctrl.Results()
	if len(results) != 1 || results[0].ObservedVersion != "100" {
		t.Fatalf("unexpected results: %+v", results)
	}
}

// TestCacheNewerThanEvent proves that the controller reconciles from current cache state
// rather than using potentially stale event payloads.
func TestCacheNewerThanEvent(t *testing.T) {
	indexer := cache.NewIndexer(cache.MetaNamespaceKeyFunc, cache.Indexers{})
	queue := workqueue.NewTypedRateLimitingQueue[string](workqueue.DefaultTypedItemBasedRateLimiter[string]())

	// Pod starts at version 1
	podV1 := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Namespace:       "default",
			Name:            "payment-api",
			ResourceVersion: "1",
		},
	}
	if err := indexer.Add(podV1); err != nil {
		t.Fatalf("indexer.Add failed: %v", err)
	}

	ctrl := NewController(Config{
		Indexer: indexer,
		Queue:   queue,
	})

	// An event was triggered by version 1 and enqueued
	ctrl.enqueue(podV1, "old-event-version-1")

	// Before worker processes the key, two rapid updates arrive and update local cache to version 3
	podV3 := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Namespace:       "default",
			Name:            "payment-api",
			ResourceVersion: "3",
		},
	}
	if err := indexer.Update(podV3); err != nil {
		t.Fatalf("indexer.Update failed: %v", err)
	}

	ctx := context.Background()
	ctrl.processNextItem(ctx)

	results := ctrl.Results()
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	// Crucial invariant: Reconcile observed version 3 (current cache), NOT version 1!
	if results[0].ObservedVersion != "3" {
		t.Fatalf("expected reconcile to observe current cache version '3', got %q", results[0].ObservedVersion)
	}
}

// TestRateLimitedRetryDecoupledFromDomain proves retry mechanisms are managed
// cleanly by the rate-limiting queue without leaking into domain business logic.
func TestRateLimitedRetryDecoupledFromDomain(t *testing.T) {
	indexer := cache.NewIndexer(cache.MetaNamespaceKeyFunc, cache.Indexers{})
	queue := workqueue.NewTypedRateLimitingQueue[string](workqueue.DefaultTypedItemBasedRateLimiter[string]())

	var attempts atomic.Int64
	errTransient := errors.New("database connection temporarily busy")

	ctrl := NewController(Config{
		Indexer:    indexer,
		Queue:      queue,
		MaxRetries: 4,
		ReconcileFn: func(ctx context.Context, key string) error {
			current := attempts.Add(1)
			if current < 3 {
				// Fail on first 2 attempts
				return errTransient
			}
			// Succeed on 3rd attempt
			return nil
		},
	})

	// Enqueue key
	queue.Add("production/auth-service")
	ctx := context.Background()

	// Attempt 1: Fails, gets re-enqueued via AddRateLimited
	ctrl.processNextItem(ctx)
	if ctrl.RetryCount() != 1 {
		t.Fatalf("expected retry count 1, got %d", ctrl.RetryCount())
	}

	// Attempt 2: Fails again, requeued
	ctrl.processNextItem(ctx)
	if ctrl.RetryCount() != 2 {
		t.Fatalf("expected retry count 2, got %d", ctrl.RetryCount())
	}

	// Attempt 3: Succeeds!
	ctrl.processNextItem(ctx)
	if ctrl.DropCount() != 0 {
		t.Fatalf("expected 0 drops, got %d", ctrl.DropCount())
	}
	if attempts.Load() != 3 {
		t.Fatalf("expected 3 reconcile attempts, got %d", attempts.Load())
	}
}

// TestSafeDeletionAndTombstone proves that object deletions from cache and
// DeletedFinalStateUnknown tombstones are handled safely without nil-pointer panics.
func TestSafeDeletionAndTombstone(t *testing.T) {
	indexer := cache.NewIndexer(cache.MetaNamespaceKeyFunc, cache.Indexers{})
	queue := workqueue.NewTypedRateLimitingQueue[string](workqueue.DefaultTypedItemBasedRateLimiter[string]())

	ctrl := NewController(Config{
		Indexer: indexer,
		Queue:   queue,
	})

	// Case 1: Standard delete where object is already gone from indexer
	queue.Add("default/deleted-pod")
	ctx := context.Background()
	ctrl.processNextItem(ctx)

	results := ctrl.Results()
	if len(results) != 1 || results[0].Action != "delete" {
		t.Fatalf("expected delete action recorded, got %+v", results)
	}

	// Case 2: Tombstone DeletedFinalStateUnknown unwrapping
	tombstone := cache.DeletedFinalStateUnknown{
		Key: "production/tombstone-pod",
		Obj: &corev1.Pod{
			ObjectMeta: metav1.ObjectMeta{
				Namespace: "production",
				Name:      "tombstone-pod",
			},
		},
	}
	ctrl.enqueue(tombstone, "tombstone-test")
	if queue.Len() != 1 {
		t.Fatalf("expected tombstone key enqueued, got queue len %d", queue.Len())
	}
	ctrl.processNextItem(ctx)

	results = ctrl.Results()
	if len(results) != 2 || results[1].Key != "production/tombstone-pod" {
		t.Fatalf("expected tombstone processed as delete, got %+v", results)
	}
}

// TestCleanCancellationShutdown proves worker goroutines terminate cleanly
// when context is cancelled, without deadlock or goroutine leaks.
func TestCleanCancellationShutdown(t *testing.T) {
	indexer := cache.NewIndexer(cache.MetaNamespaceKeyFunc, cache.Indexers{})
	queue := workqueue.NewTypedRateLimitingQueue[string](workqueue.DefaultTypedItemBasedRateLimiter[string]())

	ctrl := NewController(Config{
		Indexer: indexer,
		Queue:   queue,
	})

	ctx, cancel := context.WithCancel(context.Background())

	runDone := make(chan error, 1)
	go func() {
		runDone <- ctrl.Run(ctx, 3) // 3 concurrent workers
	}()

	// Feed work into queue
	for i := 0; i < 5; i++ {
		queue.Add(fmt.Sprintf("default/worker-test-%d", i))
	}

	// Give workers a moment to process
	time.Sleep(50 * time.Millisecond)

	// Cancel context to trigger shutdown
	cancel()

	select {
	case err := <-runDone:
		if err != nil {
			t.Fatalf("Run returned error on cancellation: %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatalf("Run failed to shut down within 2 seconds of context cancellation")
	}
}

// TestCacheNotSyncedGuard proves that controller aborts if cache fails to synchronize.
func TestCacheNotSyncedGuard(t *testing.T) {
	indexer := cache.NewIndexer(cache.MetaNamespaceKeyFunc, cache.Indexers{})
	queue := workqueue.NewTypedRateLimitingQueue[string](workqueue.DefaultTypedItemBasedRateLimiter[string]())

	// Fake informer whose HasSynced always returns false
	fakeInformer := &fakeUnsyncedInformer{
		SharedIndexInformer: cache.NewSharedIndexInformer(nil, &corev1.Pod{}, 0, cache.Indexers{}),
	}

	ctrl := NewController(Config{
		Indexer:  indexer,
		Queue:    queue,
		Informer: fakeInformer,
	})

	// Cancel context quickly to simulate timeout
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()

	err := ctrl.Run(ctx, 1)
	if err == nil {
		t.Fatalf("expected error when cache sync times out, got nil")
	}
}

type fakeUnsyncedInformer struct {
	cache.SharedIndexInformer
}

func (f *fakeUnsyncedInformer) HasSynced() bool {
	return false
}

func (f *fakeUnsyncedInformer) AddEventHandler(handler cache.ResourceEventHandler) (cache.ResourceEventHandlerRegistration, error) {
	return nil, nil
}
