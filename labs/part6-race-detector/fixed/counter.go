// Package fixed protects a counter shared by concurrent probe workers.
package fixed

import "sync"

// Counter tracks completed checks behind one mutex.
type Counter struct {
	mu        sync.Mutex
	successes int
}

// RecordSuccess records one completed check.
func (c *Counter) RecordSuccess() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.successes++
}

// Successes returns a synchronized snapshot of the count.
func (c *Counter) Successes() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.successes
}
