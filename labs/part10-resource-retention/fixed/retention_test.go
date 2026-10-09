package fixed

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"

	"example.com/golang-master/part10-resource-retention/baseline"
)

func await(t *testing.T, done <-chan struct{}) {
	t.Helper()
	select {
	case <-done:
	case <-time.After(5 * time.Second):
		t.Fatal("owned operation did not finish")
	}
}

func stillOpen(t *testing.T, done <-chan struct{}) {
	t.Helper()
	select {
	case <-done:
		t.Fatal("operation ended unexpectedly")
	default:
	}
}

func TestPrefixOwnership(t *testing.T) {
	buf := make([]byte, 1024)
	buf[0] = 7
	borrowed := baseline.Prefix(buf, 16)
	if len(borrowed) != 16 || cap(borrowed) != 16 || &borrowed[0] != &buf[0] {
		t.Fatal("baseline should have a restricted capacity but shared storage")
	}
	owned := Prefix(buf, 16)
	if len(owned) != 16 || cap(owned) != 16 || &owned[0] == &buf[0] {
		t.Fatal("fixed prefix must own its bytes")
	}
	owned[0] = 9
	if buf[0] != 7 {
		t.Fatal("copy mutated input")
	}
	buf[0] = 11
	if borrowed[0] != 11 || owned[0] != 9 {
		t.Fatal("alias/copy contract broken")
	}
	if got := Prefix(buf, 0); len(got) != 0 || cap(got) != 0 {
		t.Fatal("empty copy retains capacity")
	}
}

func TestCacheBoundAndOwnership(t *testing.T) {
	c, err := NewCache(2, 4)
	if err != nil {
		t.Fatal(err)
	}
	buf := []byte{1, 2}
	if err := c.Put("a", buf); err != nil {
		t.Fatal(err)
	}
	buf[0] = 9
	if c.values["a"][0] != 1 {
		t.Fatal("cache must copy caller bytes")
	}
	for _, key := range []string{"b", "a", "c"} {
		if err := c.Put(key, []byte{3}); err != nil {
			t.Fatal(err)
		}
	}
	if c.Len() != 2 || c.order[0] != "b" || c.order[1] != "c" {
		t.Fatal("update renewed FIFO age or capacity was exceeded")
	}
	if _, ok := c.values["a"]; ok {
		t.Fatal("oldest entry not evicted")
	}
	for _, input := range []struct {
		key string
		val []byte
	}{{"d", make([]byte, 5)}, {strings.Repeat("k", 129), nil}} {
		if err := c.Put(input.key, input.val); !errors.Is(err, ErrTooLarge) {
			t.Fatal("oversized input accepted")
		}
		if c.Len() != 2 || c.order[0] != "b" {
			t.Fatal("rejected input changed cache")
		}
	}
	for i := 0; i < 100; i++ {
		if err := c.Put(strings.Repeat("x", i%100+1), []byte{1}); err != nil {
			t.Fatal(err)
		}
		if c.Len() > 2 || len(c.order) > 2 {
			t.Fatal("capacity contract broken")
		}
	}
	for _, args := range [][2]int{{0, 4}, {2, 0}, {-1, 1}} {
		if _, err := NewCache(args[0], args[1]); err == nil {
			t.Fatal("invalid budget accepted")
		}
	}
}

func TestBaselineCacheKeepsEveryDistinctKey(t *testing.T) {
	c := baseline.NewCache()
	for i := 1; i <= 10; i++ {
		if err := c.Put(strings.Repeat("k", i), []byte{1}); err != nil {
			t.Fatal(err)
		}
		if c.Len() != i {
			t.Fatal("baseline unexpectedly evicted an entry")
		}
	}
}

func TestWaitHonorsCancellationAndInput(t *testing.T) {
	for _, cancelFirst := range []bool{true, false} {
		ctx, cancel := context.WithCancel(context.Background())
		in, started := make(chan struct{}), make(chan struct{})
		done := Wait(ctx, in, started)
		await(t, started)
		if cancelFirst {
			cancel()
		} else {
			close(in)
		}
		await(t, done)
		cancel()
	}
}

func TestBaselineReceiveNeedsRescue(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	in, started := make(chan struct{}), make(chan struct{})
	done := baseline.Wait(ctx, in, started)
	defer func() { close(in); await(t, done) }()
	await(t, started)
	cancel()
	stillOpen(t, done) // Source receives only in; parent cancellation is irrelevant.
}

func TestTickerStopIsNotWorkerShutdown(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	rescue := make(chan struct{})
	w := baseline.RunTicker(ctx, time.Hour, rescue, func(context.Context) {})
	defer func() { close(rescue); await(t, w.Done) }()
	await(t, w.Started)
	cancel()
	w.StopTicker()
	stillOpen(t, w.Done)
	ticker := time.NewTicker(time.Hour)
	ticker.Stop()
	select {
	case _, ok := <-ticker.C:
		if !ok {
			t.Fatal("Stop closed ticker channel")
		}
	default:
	}
}

func TestTickerLoopHonorsCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	rescue := make(chan struct{})
	w := RunTicker(ctx, time.Hour, rescue, func(context.Context) {})
	await(t, w.Started)
	cancel()
	await(t, w.Done)
}

func TestCancellationDoesNotKillNoncooperativeCallback(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	entered, release, rescue := make(chan struct{}), make(chan struct{}), make(chan struct{})
	w := RunTicker(ctx, time.Millisecond, rescue, func(ctx context.Context) {
		close(entered)
		_ = baseline.BlockingTask(ctx, release)
	})
	defer func() { close(release); close(rescue); await(t, w.Done) }()
	await(t, entered)
	cancel()
	stillOpen(t, w.Done)
}

func TestCooperativeCallbackFinishes(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	entered, release, rescue := make(chan struct{}), make(chan struct{}), make(chan struct{})
	w := RunTicker(ctx, time.Millisecond, rescue, func(ctx context.Context) {
		close(entered)
		_ = BlockingTask(ctx, release)
	})
	defer func() { cancel(); close(rescue); await(t, w.Done) }()
	await(t, entered)
	cancel()
	await(t, w.Done)
}

func TestTimeoutResourceLifecycle(t *testing.T) {
	parent, cancelParent := context.WithCancel(context.Background())
	defer cancelParent()
	var forgotten, owned context.Context
	if err := baseline.DoTimeout(parent, time.Hour, func(ctx context.Context) error {
		forgotten = ctx
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := DoTimeout(parent, time.Hour, func(ctx context.Context) error {
		owned = ctx
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if forgotten.Err() != nil || !errors.Is(owned.Err(), context.Canceled) {
		t.Fatal("operation completion and child cleanup were conflated")
	}
	cancelParent()
	await(t, forgotten.Done())
	if !errors.Is(forgotten.Err(), context.Canceled) {
		t.Fatal("parent cancellation did not reach child")
	}
	if err := baseline.DoTimeout(context.Background(), -time.Second,
		func(ctx context.Context) error {
			if !errors.Is(ctx.Err(), context.DeadlineExceeded) {
				t.Fatal("expired deadline should already cancel child")
			}
			return nil
		}); err != nil {
		t.Fatal(err)
	}
}

func TestTimeoutErrorPathCancelsChild(t *testing.T) {
	want := errors.New("operation failed")
	var child context.Context
	err := DoTimeout(context.Background(), time.Hour, func(ctx context.Context) error {
		child = ctx
		return want
	})
	if !errors.Is(err, want) || !errors.Is(child.Err(), context.Canceled) {
		t.Fatal("error path did not preserve result and cancel child")
	}
}

func TestChildUsesEarlierParentDeadline(t *testing.T) {
	parent, cancel := context.WithDeadline(context.Background(), time.Now().Add(time.Hour))
	defer cancel()
	want, _ := parent.Deadline()
	err := DoTimeout(parent, 2*time.Hour, func(ctx context.Context) error {
		if got, ok := ctx.Deadline(); !ok || !got.Equal(want) {
			t.Fatal("child extended the parent deadline")
		}
		return nil
	})
	if err != nil || parent.Err() != nil {
		t.Fatal("child cleanup incorrectly canceled parent")
	}
}
