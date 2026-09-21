//go:build exercise

package exercise

import (
	"context"
	"fmt"
	"sync"
	"testing"
	"time"
)

func TestRunReturnsEveryCompletedJobThenCloses(t *testing.T) {
	jobs := []Job{{Name: "billing"}, {Name: "checkout"}, {Name: "search"}}
	out := Run(context.Background(), jobs, 2, func(_ context.Context, job Job) error {
		if job.Name == "checkout" {
			return fmt.Errorf("%s unavailable", job.Name)
		}
		return nil
	})

	got := map[string]error{}
	for result := range out {
		got[result.Job.Name] = result.Err
	}

	if len(got) != len(jobs) {
		t.Fatalf("received %d results, want %d: %#v", len(got), len(jobs), got)
	}
	if got["billing"] != nil || got["search"] != nil {
		t.Fatalf("successful jobs have errors: %#v", got)
	}
	if got["checkout"] == nil {
		t.Fatal("checkout error was lost")
	}
}

func TestRunNeverExceedsWorkerLimit(t *testing.T) {
	jobs := []Job{{Name: "a"}, {Name: "b"}, {Name: "c"}, {Name: "d"}}
	started := make(chan struct{}, len(jobs))
	release := make(chan struct{})

	var mu sync.Mutex
	active, peak := 0, 0
	work := func(_ context.Context, _ Job) error {
		mu.Lock()
		active++
		if active > peak {
			peak = active
		}
		mu.Unlock()

		started <- struct{}{}
		<-release

		mu.Lock()
		active--
		mu.Unlock()
		return nil
	}

	out := Run(context.Background(), jobs, 2, work)
	<-started
	<-started
	select {
	case <-started:
		t.Fatal("third job started while both workers were busy")
	default:
	}

	close(release)
	for range out {
	}

	mu.Lock()
	defer mu.Unlock()
	if peak != 2 {
		t.Fatalf("peak workers = %d, want 2", peak)
	}
}

func TestRunCancellationDoesNotLeaveAnUnconsumedSend(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	started := make(chan struct{})
	out := Run(ctx, []Job{{Name: "billing"}}, 1, func(ctx context.Context, _ Job) error {
		close(started)
		<-ctx.Done()
		return ctx.Err()
	})

	<-started
	cancel()
	select {
	case _, ok := <-out:
		if ok {
			t.Fatal("canceled worker sent a result to an abandoned consumer")
		}
	case <-time.After(time.Second):
		t.Fatal("output did not close after cancellation")
	}
}

func TestRunWithNoWorkersReturnsClosedOutput(t *testing.T) {
	out := Run(context.Background(), []Job{{Name: "billing"}}, 0, func(context.Context, Job) error {
		t.Fatal("Work ran with no workers")
		return nil
	})

	if _, ok := <-out; ok {
		t.Fatal("output remained open with no workers")
	}
}
