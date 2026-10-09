// Package fixed implements the ownership contracts of the lab, not a general cache.
package fixed

import (
	"context"
	"errors"
	"strings"
	"time"
)

// Prefix requires 0 <= n <= len(buf) and copies byte elements, not references.
func Prefix(buf []byte, n int) []byte {
	out := make([]byte, n)
	copy(out, buf[:n])
	return out
}

// Cache is single-owner FIFO. Updating a key does not renew its insertion age.
// Values and keys are bounded; metadata overhead is not an exact RSS budget.
type Cache struct {
	values        map[string][]byte
	order         []string
	maxEntries    int
	maxValueBytes int
}

const MaxKeyBytes = 128

var ErrTooLarge = errors.New("cache key or value exceeds budget")

func NewCache(maxEntries, maxValueBytes int) (*Cache, error) {
	if maxEntries <= 0 || maxValueBytes <= 0 {
		return nil, errors.New("cache budgets must be positive")
	}
	return &Cache{
		values:     make(map[string][]byte),
		maxEntries: maxEntries, maxValueBytes: maxValueBytes,
	}, nil
}

func (c *Cache) Put(key string, value []byte) error {
	if len(key) > MaxKeyBytes || len(value) > c.maxValueBytes {
		return ErrTooLarge
	}
	key = strings.Clone(key)
	owned := make([]byte, len(value))
	copy(owned, value)
	if _, exists := c.values[key]; !exists {
		if len(c.order) == c.maxEntries {
			delete(c.values, c.order[0])
			copy(c.order, c.order[1:])
			c.order[len(c.order)-1] = ""
			c.order = c.order[:len(c.order)-1]
		}
		c.order = append(c.order, key)
	}
	c.values[key] = owned
	return nil
}

func (c *Cache) Len() int { return len(c.values) }

func Wait(ctx context.Context, in <-chan struct{}, started chan<- struct{}) <-chan struct{} {
	done := make(chan struct{})
	go func() {
		defer close(done)
		close(started)
		select {
		case <-in:
		case <-ctx.Done():
		}
	}()
	return done
}

type Worker struct {
	Started    <-chan struct{}
	Done       <-chan struct{}
	StopTicker func()
}

// work must return when its context is canceled if bounded shutdown is required.
func RunTicker(ctx context.Context, period time.Duration, rescue <-chan struct{}, work func(context.Context)) Worker {
	ticker := time.NewTicker(period)
	started, done := make(chan struct{}), make(chan struct{})
	go func() {
		defer close(done)
		defer ticker.Stop()
		close(started)
		for {
			select {
			case <-ctx.Done():
				return
			case <-rescue:
				return
			case <-ticker.C:
				if ctx.Err() != nil {
					return
				}
				work(ctx)
			}
		}
	}()
	return Worker{started, done, ticker.Stop}
}

func BlockingTask(ctx context.Context, release <-chan struct{}) error {
	select {
	case <-release:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func DoTimeout(parent context.Context, budget time.Duration, work func(context.Context) error) error {
	ctx, cancel := context.WithTimeout(parent, budget)
	defer cancel()
	return work(ctx)
}
