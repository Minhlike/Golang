package controller

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/util/runtime"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/util/workqueue"
)

// ReconcileResult captures the recorded outcome of a reconcile pass.
type ReconcileResult struct {
	Key             string
	ObservedVersion string
	Action          string
	Attempt         int
}

// Controller implements an idiomatic, production-grade Kubernetes controller using client-go.
type Controller struct {
	indexer    cache.Indexer
	queue      workqueue.TypedRateLimitingInterface[string]
	informer   cache.SharedIndexInformer
	maxRetries int

	reconcileFn func(ctx context.Context, key string) error

	reconcileCount atomic.Int64
	retryCount     atomic.Int64
	dropCount      atomic.Int64

	resultsMu sync.Mutex
	results   []ReconcileResult
}

// Config provides initial parameters to create a Controller.
type Config struct {
	Indexer     cache.Indexer
	Queue       workqueue.TypedRateLimitingInterface[string]
	Informer    cache.SharedIndexInformer
	MaxRetries  int
	ReconcileFn func(ctx context.Context, key string) error
}

// NewController builds the controller and registers ResourceEventHandler callbacks.
func NewController(cfg Config) *Controller {
	if cfg.MaxRetries <= 0 {
		cfg.MaxRetries = 5
	}
	c := &Controller{
		indexer:     cfg.Indexer,
		queue:       cfg.Queue,
		informer:    cfg.Informer,
		maxRetries:  cfg.MaxRetries,
		reconcileFn: cfg.ReconcileFn,
	}

	if cfg.Informer != nil {
		_, _ = cfg.Informer.AddEventHandler(cache.ResourceEventHandlerFuncs{
			AddFunc: func(obj any) {
				c.enqueue(obj, "add")
			},
			UpdateFunc: func(oldObj, newObj any) {
				c.enqueue(newObj, "update")
			},
			DeleteFunc: func(obj any) {
				c.enqueue(obj, "delete")
			},
		})
	}

	return c
}

// enqueue extracts the namespace/name key and submits it to the rate-limited workqueue.
func (c *Controller) enqueue(obj any, reason string) {
	key, err := cache.DeletionHandlingMetaNamespaceKeyFunc(obj)
	if err != nil {
		runtime.HandleError(fmt.Errorf("failed to extract key from object (%s): %w", reason, err))
		return
	}
	c.queue.Add(key)
}

// Run begins the controller loop after ensuring the local cache is synchronized with the API server.
func (c *Controller) Run(ctx context.Context, workers int) error {
	defer runtime.HandleCrash()
	defer c.queue.ShutDown()

	// Contract: NEVER process workqueue items before cache synchronization
	if c.informer != nil {
		if !cache.WaitForNamedCacheSyncWithContext(ctx, c.informer.HasSynced) {
			return fmt.Errorf("timed out waiting for caches to sync")
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

// processNextItem processes a single item from the queue, enforcing local per-key serialization.
func (c *Controller) processNextItem(ctx context.Context) bool {
	key, quit := c.queue.Get()
	if quit {
		return false
	}
	// Done MUST be called to release the key from the processing set.
	defer c.queue.Done(key)

	err := c.reconcile(ctx, key)
	c.handleError(ctx, key, err)
	return true
}

// reconcile reads the CURRENT authoritative state from local cache, not from stale event data.
func (c *Controller) reconcile(ctx context.Context, key string) error {
	c.reconcileCount.Add(1)
	if c.reconcileFn != nil {
		return c.reconcileFn(ctx, key)
	}

	obj, exists, err := c.indexer.GetByKey(key)
	if err != nil {
		return fmt.Errorf("fetching key %q from cache failed: %w", key, err)
	}

	c.resultsMu.Lock()
	defer c.resultsMu.Unlock()

	if !exists {
		c.results = append(c.results, ReconcileResult{
			Key:    key,
			Action: "delete",
		})
		return nil
	}

	pod, ok := obj.(*corev1.Pod)
	if !ok {
		return fmt.Errorf("expected *corev1.Pod but got %T", obj)
	}

	c.results = append(c.results, ReconcileResult{
		Key:             key,
		ObservedVersion: pod.ResourceVersion,
		Action:          "sync",
	})
	return nil
}

// handleError decouples retry scheduling from business logic.
func (c *Controller) handleError(ctx context.Context, key string, err error) {
	if err == nil {
		c.queue.Forget(key)
		return
	}

	requeues := c.queue.NumRequeues(key)
	if requeues < c.maxRetries {
		c.retryCount.Add(1)
		c.queue.AddRateLimited(key)
		return
	}

	c.dropCount.Add(1)
	c.queue.Forget(key)
	runtime.HandleError(fmt.Errorf("dropping key %q from queue after %d retries: %w", key, requeues, err))
}

// ReconcileCount returns total reconcile passes executed.
func (c *Controller) ReconcileCount() int64 {
	return c.reconcileCount.Load()
}

// RetryCount returns total retry attempts scheduled.
func (c *Controller) RetryCount() int64 {
	return c.retryCount.Load()
}

// DropCount returns count of items dropped after exhausting retries.
func (c *Controller) DropCount() int64 {
	return c.dropCount.Load()
}

// Results returns a slice copy of all recorded reconcile outcomes.
func (c *Controller) Results() []ReconcileResult {
	c.resultsMu.Lock()
	defer c.resultsMu.Unlock()
	copied := make([]ReconcileResult, len(c.results))
	copy(copied, c.results)
	return copied
}
