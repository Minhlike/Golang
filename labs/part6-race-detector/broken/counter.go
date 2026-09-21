// Package broken contains a deliberately racy counter for a race-detector lab.
package broken

// Counter tracks completed checks without synchronization.
type Counter struct {
	successes int
}

// RecordSuccess records one completed check.
func (c *Counter) RecordSuccess() {
	c.successes++
}

// Successes returns the current count.
func (c *Counter) Successes() int {
	return c.successes
}
