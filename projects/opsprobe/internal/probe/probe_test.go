package probe

import (
	"context"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"
)

func TestProbeSingle_Success(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	}))
	defer srv.Close()

	pool := NewPool()
	res := pool.ProbeSingle(context.Background(), Target{
		ID:  "srv-1",
		URL: srv.URL,
	})

	if res.Outcome != OutcomeSuccess {
		t.Fatalf("expected OutcomeSuccess, got %s (err: %s)", res.Outcome, res.Error)
	}
	if res.StatusCode != http.StatusOK {
		t.Fatalf("expected status 200, got %d", res.StatusCode)
	}
}

func TestProbeSingle_Failure_5xx(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		_, _ = w.Write([]byte("internal error"))
	}))
	defer srv.Close()

	pool := NewPool()
	res := pool.ProbeSingle(context.Background(), Target{
		ID:  "srv-err",
		URL: srv.URL,
	})

	if res.Outcome != OutcomeFailure {
		t.Fatalf("expected OutcomeFailure, got %s", res.Outcome)
	}
	if res.StatusCode != http.StatusInternalServerError {
		t.Fatalf("expected status 500, got %d", res.StatusCode)
	}
}

func TestProbeSingle_ExpectedStatus(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusTeapot)
	}))
	defer srv.Close()

	pool := NewPool()

	// 1. Khớp expected status: coi là Success
	res1 := pool.ProbeSingle(context.Background(), Target{
		ID:             "srv-teapot-ok",
		URL:            srv.URL,
		ExpectedStatus: http.StatusTeapot,
	})
	if res1.Outcome != OutcomeSuccess {
		t.Fatalf("expected OutcomeSuccess when expected status matches, got %s", res1.Outcome)
	}

	// 2. Không khớp expected status: coi là Failure
	res2 := pool.ProbeSingle(context.Background(), Target{
		ID:             "srv-teapot-mismatch",
		URL:            srv.URL,
		ExpectedStatus: http.StatusOK,
	})
	if res2.Outcome != OutcomeFailure {
		t.Fatalf("expected OutcomeFailure when expected status mismatches, got %s", res2.Outcome)
	}
}

func TestProbeSingle_Timeout(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(200 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	pool := NewPool(WithDefaultTimeout(50 * time.Millisecond))
	res := pool.ProbeSingle(context.Background(), Target{
		ID:  "srv-slow",
		URL: srv.URL,
	})

	if res.Outcome != OutcomeTimeout {
		t.Fatalf("expected OutcomeTimeout, got %s (err: %s)", res.Outcome, res.Error)
	}
}

func TestProbeSingle_MalformedURL(t *testing.T) {
	pool := NewPool()

	cases := []struct {
		name   string
		target Target
	}{
		{"empty_id", Target{ID: "", URL: "http://example.com"}},
		{"empty_url", Target{ID: "t1", URL: ""}},
		{"unsupported_scheme", Target{ID: "t2", URL: "ftp://example.com"}},
		{"missing_host", Target{ID: "t3", URL: "http://"}},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			res := pool.ProbeSingle(context.Background(), tc.target)
			if res.Outcome != OutcomeFailure {
				t.Fatalf("expected OutcomeFailure for malformed target, got %s", res.Outcome)
			}
			if res.Error == "" {
				t.Fatalf("expected non-empty error message")
			}
		})
	}
}

func TestPool_Execute_BoundedConcurrency(t *testing.T) {
	var activeWorkers int32
	var maxObserved int32

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		current := atomic.AddInt32(&activeWorkers, 1)
		for {
			old := atomic.LoadInt32(&maxObserved)
			if current <= old || atomic.CompareAndSwapInt32(&maxObserved, old, current) {
				break
			}
		}
		time.Sleep(20 * time.Millisecond)
		atomic.AddInt32(&activeWorkers, -1)
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	concurrencyLimit := 3
	pool := NewPool(WithConcurrency(concurrencyLimit))

	targets := make([]Target, 10)
	for i := 0; i < 10; i++ {
		targets[i] = Target{
			ID:  srv.URL,
			URL: srv.URL,
		}
	}

	results := pool.Execute(context.Background(), targets)
	if len(results) != 10 {
		t.Fatalf("expected 10 results, got %d", len(results))
	}

	observed := atomic.LoadInt32(&maxObserved)
	if observed > int32(concurrencyLimit) {
		t.Fatalf("concurrency limit breached: max observed %d, limit was %d", observed, concurrencyLimit)
	}
	if observed < 2 {
		t.Fatalf("expected concurrent executions, got %d", observed)
	}
}

func TestPool_Execute_ContextCancellation(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(100 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	pool := NewPool(WithConcurrency(1))
	ctx, cancel := context.WithCancel(context.Background())

	// Hủy context sau 20ms
	go func() {
		time.Sleep(20 * time.Millisecond)
		cancel()
	}()

	targets := []Target{
		{ID: "t1", URL: srv.URL},
		{ID: "t2", URL: srv.URL},
		{ID: "t3", URL: srv.URL},
	}

	results := pool.Execute(ctx, targets)
	hasCanceled := false
	for _, r := range results {
		if r.Outcome == OutcomeCancel {
			hasCanceled = true
			break
		}
	}

	if !hasCanceled {
		t.Fatalf("expected at least one probe with OutcomeCancel upon parent context cancellation")
	}
}
