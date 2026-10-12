package queue

import (
	"math"
	"testing"
	"time"
)

func TestRetryDelaySaturatesBeforeOverflow(t *testing.T) {
	for _, tc := range []struct {
		base, max time.Duration
		failures  int
		want      time.Duration
	}{
		{time.Second, 10 * time.Second, 1, time.Second},
		{time.Second, 10 * time.Second, 4, 8 * time.Second},
		{time.Second, 10 * time.Second, 5, 10 * time.Second},
		{time.Second, 10 * time.Second, 65, 10 * time.Second},
		{time.Duration(math.MaxInt64/2 + 1), math.MaxInt64, 2, math.MaxInt64},
		{10 * time.Second, time.Second, 1, time.Second},
	} {
		if got := retryDelay(tc.base, tc.max, tc.failures); got != tc.want {
			t.Fatalf("retryDelay(%v,%v,%d)=%v, want %v", tc.base, tc.max, tc.failures, got, tc.want)
		}
	}
}
