// Package baseline contains deliberately faulty, bounded reproductions.
// Rescue channels and parent cancellation let tests clean up every goroutine.
package baseline

import (
	"context"
	"time"
)

func Prefix(buf []byte, n int) []byte {
	return buf[:n:n]
}

type Cache struct{ values map[string][]byte }

func NewCache() *Cache {
	return &Cache{values: make(map[string][]byte)}
}

func (c *Cache) Put(key string, value []byte) error {
	c.values[key] = value
	return nil
}

func (c *Cache) Len() int { return len(c.values) }

func Wait(_ context.Context, in <-chan struct{}, started chan<- struct{}) <-chan struct{} {
	done := make(chan struct{})
	go func() {
		defer close(done)
		close(started)
		<-in // Caller cancellation cannot interrupt this receive.
	}()
	return done
}

type Worker struct {
	Started    <-chan struct{}
	Done       <-chan struct{}
	StopTicker func()
}

func RunTicker(ctx context.Context, period time.Duration, rescue <-chan struct{}, work func(context.Context)) Worker {
	ticker := time.NewTicker(period)
	started, done := make(chan struct{}), make(chan struct{})
	go func() {
		defer close(done)
		defer ticker.Stop()
		close(started)
		for {
			select {
			case <-ticker.C:
				work(ctx)
			case <-rescue: // Test harness rescue, not a cancellation implementation.
				return
			}
		}
	}()
	return Worker{started, done, ticker.Stop}
}

func BlockingTask(_ context.Context, release <-chan struct{}) error {
	<-release
	return nil
}

// ForgetCancel demonstrates that passing a CancelFunc to another function
// can satisfy a local static check without actually honoring ownership.
func ForgetCancel(_ context.CancelFunc) {}

func DoTimeout(parent context.Context, budget time.Duration, work func(context.Context) error) error {
	ctx, cancel := context.WithTimeout(parent, budget)
	ForgetCancel(cancel)
	return work(ctx)
}
