package failurelab

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"runtime"
	"sort"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"example.com/golang-master/projects/opsprobe/internal/probe"
	"example.com/golang-master/projects/opsprobe/internal/telemetry"
)

func wait(t *testing.T, c <-chan struct{}) {
	t.Helper()
	select {
	case <-c:
	case <-time.After(5 * time.Second):
		t.Fatal("owned operation did not finish")
	}
}

func signals(t *testing.T) (*telemetry.Telemetry, *bytes.Buffer, *bytes.Buffer) {
	t.Helper()
	logs, traces := new(bytes.Buffer), new(bytes.Buffer)
	tel, err := telemetry.New(telemetry.Config{LogWriter: logs, TraceWriter: traces, ServiceName: "failurelab"})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := tel.Shutdown(ctx); err != nil {
			t.Error(err)
		}
	})
	return tel, logs, traces
}

func pool(s *httptest.Server, tel *telemetry.Telemetry) *probe.Pool {
	return probe.NewPool(probe.WithHTTPClient(s.Client()), probe.WithTracer(tel.Tracer), probe.WithDefaultTimeout(100*time.Millisecond))
}

func TestBoundedAdmission(t *testing.T) {
	entered, release := make(chan struct{}, 2), make(chan struct{})
	var once sync.Once
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		entered <- struct{}{}
		select {
		case <-release:
			io.WriteString(w, "ok")
		case <-r.Context().Done():
		}
	}))
	t.Cleanup(func() { once.Do(func() { close(release) }); s.Close() })
	tel, _, _ := signals(t)
	r, err := New(context.Background(), 2, 2, 5*time.Second, pool(s, tel), tel)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { r.Cancel(); once.Do(func() { close(release) }); wait(t, r.Done()) })
	for i := 0; i < 2; i++ {
		if err := r.Submit(probe.Target{ID: fmt.Sprint(i), URL: s.URL, Timeout: 5 * time.Second}); err != nil {
			t.Fatal(err)
		}
	}
	for i := 0; i < 2; i++ {
		select {
		case <-entered:
		case <-time.After(5 * time.Second):
			t.Fatal("dependency not entered")
		}
	}
	for i := 2; i < 4; i++ {
		if err := r.Submit(probe.Target{ID: fmt.Sprint(i), URL: s.URL}); err != nil {
			t.Fatal(err)
		}
	}
	for i := 0; i < 100; i++ {
		if err := r.Submit(probe.Target{ID: "shed", URL: s.URL}); !errors.Is(err, ErrFull) {
			t.Fatalf("overload=%v", err)
		}
	}
	if v := r.Stats(); v.Running != 2 || v.Queue != 2 || v.Rejected != 100 {
		t.Fatalf("bound=%+v", v)
	}
	r.CloseAdmission()
	once.Do(func() { close(release) })
	count := 0
	for range r.Results() {
		count++
	}
	wait(t, r.Done())
	if v := r.Stats(); count != 4 || v.Running != 0 || v.PeakRunning > 2 || v.Queue != 0 {
		t.Fatalf("cleanup count=%d stats=%+v", count, v)
	}
	t.Logf("bounded stats=%+v", r.Stats())
}

func TestConsumerStopsContract(t *testing.T) {
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { io.WriteString(w, "ok") }))
	defer s.Close()
	tel, _, _ := signals(t)
	beforeSend, rescue := make(chan struct{}), make(chan struct{})
	broken := os.Getenv("RELIABILITY_MUTANT") == "uncancellable_send"
	send := func(ctx context.Context, out chan<- probe.Result, result probe.Result) {
		close(beforeSend)
		if broken {
			select {
			case out <- result:
			case <-rescue:
			}
			return
		}
		offer(ctx, out, result)
	}
	r, err := newRunner(context.Background(), 1, 1, time.Second, pool(s, tel), tel, send)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { close(rescue); r.Cancel(); wait(t, r.Done()) })
	if err := r.Submit(probe.Target{ID: "abandoned", URL: s.URL}); err != nil {
		t.Fatal(err)
	}
	wait(t, beforeSend) // Probe finished; consumer intentionally never reads.
	if err := r.Submit(probe.Target{ID: "queued-then-abandoned", URL: s.URL}); err != nil {
		t.Fatal(err)
	}
	r.Cancel()
	select {
	case <-r.Done():
	case <-time.After(time.Second):
		t.Fatal("contract: cancellation must release result handoff")
	}
	if v := r.Stats(); v.Running != 0 || v.Queue != 0 || v.Dropped != 1 {
		t.Fatalf("cancelled resources retained: %+v", v)
	}
	t.Log("consumer stopped: joined owned worker without draining results")
}

func TestLocalFaultsAndSignals(t *testing.T) {
	for _, mode := range []string{"ok", "slow", "timeout", "5xx", "truncated", "cut"} {
		t.Run(mode, func(t *testing.T) {
			entered, release, stopped := make(chan struct{}), make(chan struct{}), make(chan struct{})
			var once sync.Once
			s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				close(entered)
				defer close(stopped)
				if mode == "slow" {
					select {
					case <-release:
					case <-r.Context().Done():
						return
					}
				}
				if mode == "timeout" {
					<-r.Context().Done()
					return
				}
				if mode == "cut" {
					c, _, err := w.(http.Hijacker).Hijack()
					if err == nil {
						c.Close()
					}
					return
				}
				if mode == "5xx" {
					w.WriteHeader(503)
					return
				}
				if mode == "truncated" {
					w.Header().Set("Content-Length", "100")
					io.WriteString(w, "short")
					return
				}
				io.WriteString(w, "ok")
			}))
			t.Cleanup(func() { once.Do(func() { close(release) }); s.Close() })
			tel, logs, traces := signals(t)
			r, err := New(context.Background(), 1, 1, time.Second, pool(s, tel), tel)
			if err != nil {
				t.Fatal(err)
			}
			t.Cleanup(func() { r.Cancel(); once.Do(func() { close(release) }); wait(t, r.Done()) })
			if err := r.Submit(probe.Target{ID: mode, URL: s.URL}); err != nil {
				t.Fatal(err)
			}
			r.CloseAdmission()
			wait(t, entered)
			if mode == "slow" {
				once.Do(func() { close(release) })
			}
			var result probe.Result
			select {
			case result = <-r.Results():
			case <-time.After(5 * time.Second):
				t.Fatal("probe stalled")
			}
			wait(t, r.Done())
			wait(t, stopped)
			want := probe.OutcomeFailure
			if mode == "ok" || mode == "slow" {
				want = probe.OutcomeSuccess
			}
			if mode == "timeout" {
				want = probe.OutcomeTimeout
			}
			if result.Outcome != want {
				t.Fatalf("%s got=%+v", mode, result)
			}
			flushCtx, flushCancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer flushCancel()
			if err := tel.TracerProvider.ForceFlush(flushCtx); err != nil {
				t.Fatal(err)
			}
			if !bytes.Contains(logs.Bytes(), []byte(`"outcome":"`+string(want)+`"`)) || !bytes.Contains(traces.Bytes(), []byte("opsprobe.probe")) {
				t.Fatal("log/span evidence missing")
			}
			families, err := tel.Registry.Gather()
			if err != nil {
				t.Fatal(err)
			}
			var samples uint64
			for _, f := range families {
				if f.GetName() == "opsprobe_probe_duration_seconds" {
					for _, m := range f.Metric {
						samples += m.GetHistogram().GetSampleCount()
					}
				}
			}
			if samples != 1 {
				t.Fatalf("metric samples=%d", samples)
			}
			t.Logf("REAL_LOCAL_VERIFIED mode=%s outcome=%s status=%d duration_ns=%d log+metric+span=present", mode, result.Outcome, result.StatusCode, result.DurationNs)
		})
	}
}

func TestCancelDoesNotProveDependencyStopped(t *testing.T) {
	entered, release, stopped := make(chan struct{}), make(chan struct{}), make(chan struct{})
	var once sync.Once
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		close(entered)
		defer close(stopped)
		<-release
		io.WriteString(w, "late")
	}))
	t.Cleanup(func() { once.Do(func() { close(release) }); s.Close() })
	tel, _, _ := signals(t)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	r, err := New(ctx, 1, 1, time.Second, pool(s, tel), tel)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { r.Cancel(); once.Do(func() { close(release) }); wait(t, r.Done()) })
	if err := r.Submit(probe.Target{ID: "noncooperative", URL: s.URL}); err != nil {
		t.Fatal(err)
	}
	wait(t, entered)
	cancel()
	wait(t, r.Done())
	select {
	case <-stopped:
		t.Fatal("fixture unexpectedly finished")
	default:
	}
	once.Do(func() { close(release) })
	wait(t, stopped)
	t.Log("caller joined; dependency handler needed independent release")
}

func TestExpiredQueueBudgetDoesNotStartHTTP(t *testing.T) {
	var calls atomic.Int32
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls.Add(1)
		io.WriteString(w, "unexpected")
	}))
	defer s.Close()
	tel, _, _ := signals(t)
	r, err := New(context.Background(), 1, 1, time.Second, pool(s, tel), tel)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { r.Cancel(); wait(t, r.Done()) })
	// Inject a job whose admission timestamp is already outside its budget.
	// No assertion depends on sleeping long enough for a queue to age.
	r.jobs <- job{target: probe.Target{ID: "expired", URL: s.URL}, admitted: time.Now().Add(-2 * time.Second)}
	r.CloseAdmission()
	var result probe.Result
	select {
	case result = <-r.Results():
	case <-time.After(5 * time.Second):
		t.Fatal("expired job stalled")
	}
	wait(t, r.Done())
	if result.Outcome != probe.OutcomeTimeout || calls.Load() != 0 {
		t.Fatalf("budget reset: outcome=%s HTTP calls=%d", result.Outcome, calls.Load())
	}
}

func TestAlreadyCancelledAndInvalidConfiguration(t *testing.T) {
	tel, _, _ := signals(t)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	p := probe.NewPool()
	r, err := New(ctx, 1, 1, time.Second, p, tel)
	if err != nil {
		t.Fatal(err)
	}
	defer r.Cancel()
	if err := r.Submit(probe.Target{}); !errors.Is(err, ErrClosed) {
		t.Fatalf("cancelled admission=%v", err)
	}
	wait(t, r.Done())
	if _, err := New(context.Background(), 0, 1, time.Second, p, tel); err == nil {
		t.Fatal("zero workers accepted")
	}
	if _, err := New(context.Background(), 1, 1025, time.Second, p, tel); err == nil {
		t.Fatal("unbounded queue accepted")
	}
	if _, err := New(context.Background(), 1, 1, 0, p, tel); err == nil {
		t.Fatal("missing budget accepted")
	}
}

// Optional bounded workload, not a universal speed/performance contract.
func TestBoundedWorkloadObservation(t *testing.T) {
	if os.Getenv("RUN_BOUNDED_LOAD") != "1" {
		t.Skip("optional 64-attempt load observation")
	}
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/fail":
			w.WriteHeader(503)
		case "/timeout":
			<-r.Context().Done()
		default:
			io.WriteString(w, "ok")
		}
	}))
	defer s.Close()
	tel, _, _ := signals(t)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	r, err := New(ctx, 4, 16, 500*time.Millisecond, pool(s, tel), tel)
	if err != nil {
		t.Fatal(err)
	}
	var latencies []int64
	outcomes := map[probe.Outcome]int{}
	consumed := make(chan struct{})
	t.Cleanup(func() {
		r.Cancel()
		wait(t, r.Done())
		wait(t, consumed)
	})
	go func() {
		defer close(consumed)
		for result := range r.Results() {
			latencies = append(latencies, result.DurationNs)
			outcomes[result.Outcome]++
		}
	}()
	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	g0 := runtime.NumGoroutine()
	start := time.Now()
	for i := 0; i < 64; i++ {
		path := []string{"/ok", "/fail", "/timeout"}[i%3]
		err := r.Submit(probe.Target{ID: fmt.Sprint(i), URL: s.URL + path})
		if err != nil && !errors.Is(err, ErrFull) {
			t.Fatal(err)
		}
	}
	r.CloseAdmission()
	wait(t, consumed)
	wait(t, r.Done())
	elapsed := time.Since(start)
	runtime.ReadMemStats(&after)
	sort.Slice(latencies, func(i, j int) bool { return latencies[i] < latencies[j] })
	if len(latencies) == 0 {
		t.Fatal("no accepted work")
	}
	n := len(latencies)
	t.Logf("attempts=64 completed=%d elapsed=%s throughput=%.2f/s p50_ns=%d p95_ns=%d timeout_rate=%.4f failure_rate=%.4f rejection_rate=%.4f outcomes=%v stats=%+v goroutines_before=%d after=%d heap_before=%d after=%d total_alloc_delta=%d", n, elapsed, float64(n)/elapsed.Seconds(), latencies[(n*50+99)/100-1], latencies[(n*95+99)/100-1], float64(outcomes[probe.OutcomeTimeout])/float64(n), float64(outcomes[probe.OutcomeFailure])/float64(n), float64(r.Stats().Rejected)/64, outcomes, r.Stats(), g0, runtime.NumGoroutine(), before.HeapAlloc, after.HeapAlloc, after.TotalAlloc-before.TotalAlloc)
}
