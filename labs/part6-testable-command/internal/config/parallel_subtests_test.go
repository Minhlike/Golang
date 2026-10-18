package config

import (
	"sync/atomic"
	"testing"
)

func TestParallelSubtestsWaitForTheirGroup(t *testing.T) {
	var completed atomic.Int32
	var cleaned atomic.Bool
	t.Run("group", func(t *testing.T) {
		t.Cleanup(func() { cleaned.Store(true) })
		for range 3 {
			t.Run("case", func(t *testing.T) {
				t.Parallel()
				if cleaned.Load() {
					t.Error("group resource cleaned before child ran")
				}
				completed.Add(1)
			})
		}
		if completed.Load() != 0 {
			t.Fatal("parallel children ran before parent function returned")
		}
	})
	if completed.Load() != 3 || !cleaned.Load() {
		t.Fatalf("group not joined: completed=%d cleaned=%v", completed.Load(), cleaned.Load())
	}
}
