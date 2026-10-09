//go:build exercise

package exercise

import (
	"context"
	"testing"
	"time"
)

// Implement the API in this package; do not import fixed as the solution.
func TestOwnershipContract(t *testing.T) {
	source := make([]byte, 1024)
	got := Prefix(source, 16)
	got[0] = 1
	if source[0] != 0 || len(got) != 16 || cap(got) != 16 {
		t.Fatal("Prefix must own exactly the requested byte elements")
	}
	c, err := NewCache(2, 16)
	if err != nil {
		t.Fatal(err)
	}
	for _, key := range []string{"a", "b", "c"} {
		if err := c.Put(key, got); err != nil {
			t.Fatal(err)
		}
		if c.Len() > 2 {
			t.Fatal("cache exceeds entry budget")
		}
	}
}

func TestCompletionContract(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	started, input := make(chan struct{}), make(chan struct{})
	done := Wait(ctx, input, started)
	<-started
	cancel()
	select {
	case <-done:
	case <-time.After(5 * time.Second):
		close(input) // Rescue a receive-only implementation before failing.
		<-done
		t.Fatal("canceled Wait did not finish")
	}
	var child context.Context
	if err := DoTimeout(context.Background(), time.Hour,
		func(ctx context.Context) error { child = ctx; return nil }); err != nil {
		t.Fatal(err)
	}
	if child.Err() != context.Canceled {
		t.Fatal("completed operation still owns a live timeout")
	}
}

func TestTickerCompletionContract(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	rescue := make(chan struct{})
	w := RunTicker(ctx, time.Hour, rescue, func(context.Context) {})
	<-w.Started
	cancel()
	select {
	case <-w.Done:
	case <-time.After(5 * time.Second):
		close(rescue)
		<-w.Done
		t.Fatal("ticker worker has no cancellation exit")
	}
}
