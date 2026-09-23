package probe

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
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
	if !res.ReusedEligible {
		t.Errorf("expected small body to be eligible for reuse")
	}
	if res.DurationNs <= 0 || res.DurationMs <= 0 {
		t.Errorf("expected positive duration, got ns=%d, ms=%f", res.DurationNs, res.DurationMs)
	}
}

func TestProbeSingle_BoundedDrainPolicy(t *testing.T) {
	// Case 1: Body 4 KiB (nhỏ hơn MaxDrainBytes 16 KiB) => ReusedEligible = true
	srvSmall := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write(bytes.Repeat([]byte("A"), 4096))
	}))
	defer srvSmall.Close()

	pool := NewPool()
	resSmall := pool.ProbeSingle(context.Background(), Target{ID: "small", URL: srvSmall.URL})
	if !resSmall.ReusedEligible {
		t.Errorf("expected 4KiB body to be eligible for reuse")
	}

	// Case 2: Body 32 KiB (lớn hơn MaxDrainBytes 16 KiB) => ReusedEligible = false
	srvLarge := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write(bytes.Repeat([]byte("B"), 32768))
	}))
	defer srvLarge.Close()

	resLarge := pool.ProbeSingle(context.Background(), Target{ID: "large", URL: srvLarge.URL})
	if resLarge.ReusedEligible {
		t.Errorf("expected 32KiB body to NOT be marked ReusedEligible")
	}
}

func TestProbeSingle_SecurityValidation(t *testing.T) {
	pool := NewPool()

	cases := []struct {
		name   string
		target Target
	}{
		{"empty_id", Target{ID: "", URL: "http://example.com"}},
		{"empty_url", Target{ID: "t1", URL: ""}},
		{"unsupported_scheme", Target{ID: "t2", URL: "ftp://example.com"}},
		{"missing_host", Target{ID: "t3", URL: "http://"}},
		{"userinfo_credential", Target{ID: "t4", URL: "http://admin:secret@example.com"}},
		{"unsupported_method_post", Target{ID: "t5", URL: "http://example.com", Method: "POST"}},
		{"unsupported_method_delete", Target{ID: "t6", URL: "http://example.com", Method: "DELETE"}},
		{"negative_timeout", Target{ID: "t7", URL: "http://example.com", Timeout: -1 * time.Second}},
		{"excessive_timeout", Target{ID: "t8", URL: "http://example.com", Timeout: 120 * time.Second}},
		{"invalid_expected_status", Target{ID: "t9", URL: "http://example.com", ExpectedStatus: 99}},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			res := pool.ProbeSingle(context.Background(), tc.target)
			if res.Outcome != OutcomeFailure {
				t.Fatalf("expected OutcomeFailure for insecure/invalid target %s, got %s", tc.name, res.Outcome)
			}
			if res.Error == "" {
				t.Fatalf("expected non-empty error message")
			}
		})
	}
}

type testWorkerObserver struct {
	current int32
	max     int32
}

func (o *testWorkerObserver) WorkerStarted() {
	cur := atomic.AddInt32(&o.current, 1)
	for {
		old := atomic.LoadInt32(&o.max)
		if cur <= old || atomic.CompareAndSwapInt32(&o.max, old, cur) {
			break
		}
	}
}

func (o *testWorkerObserver) WorkerStopped() {
	atomic.AddInt32(&o.current, -1)
}

func TestPool_Execute_ObserverAndBoundedWorkers(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(20 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	obs := &testWorkerObserver{}
	concurrencyLimit := 3
	pool := NewPool(
		WithConcurrency(concurrencyLimit),
		WithWorkerObserver(obs),
	)

	targets := make([]Target, 10)
	for i := 0; i < 10; i++ {
		targets[i] = Target{ID: srv.URL, URL: srv.URL}
	}

	results := pool.Execute(context.Background(), targets)
	if len(results) != 10 {
		t.Fatalf("expected 10 results, got %d", len(results))
	}

	maxObserved := atomic.LoadInt32(&obs.max)
	if maxObserved > int32(concurrencyLimit) {
		t.Fatalf("active workers breached concurrency limit: max observed %d, limit %d", maxObserved, concurrencyLimit)
	}
	if maxObserved < 2 {
		t.Fatalf("expected concurrent worker execution, observed %d", maxObserved)
	}
	if atomic.LoadInt32(&obs.current) != 0 {
		t.Fatalf("expected 0 active workers at completion, got %d", obs.current)
	}
}

func TestPool_Execute_ChildSpans(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	exporter := tracetest.NewInMemoryExporter()
	tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exporter))
	tracer := tp.Tracer("test-opsprobe")

	pool := NewPool(WithTracer(tracer))

	ctx, parentSpan := tracer.Start(context.Background(), "parent.run")
	targets := []Target{
		{ID: "t1", URL: srv.URL},
		{ID: "t2", URL: srv.URL},
	}
	_ = pool.Execute(ctx, targets)
	parentSpan.End()

	spans := exporter.GetSpans()
	if len(spans) < 3 {
		t.Fatalf("expected at least 3 spans (1 parent, 2 children), got %d", len(spans))
	}

	parentSpanID := parentSpan.SpanContext().SpanID()
	childCount := 0
	for _, s := range spans {
		if s.Name == "opsprobe.probe" {
			childCount++
			if s.Parent.SpanID() != parentSpanID {
				t.Errorf("child span parent %s does not match parent span ID %s", s.Parent.SpanID(), parentSpanID)
			}
		}
	}
	if childCount != 2 {
		t.Fatalf("expected 2 child spans, got %d", childCount)
	}
}

func TestProbeSingle_BodyStallTimeout(t *testing.T) {
	// Server gửi headers 200 OK ngay lập tức, nhưng stall stream không gửi body
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		if f, ok := w.(http.Flusher); ok {
			f.Flush()
		}
		// Stall lâu hơn deadline của probe
		select {
		case <-r.Context().Done():
		case <-time.After(500 * time.Millisecond):
		}
	}))
	defer srv.Close()

	pool := NewPool(WithDefaultTimeout(50 * time.Millisecond))
	res := pool.ProbeSingle(context.Background(), Target{
		ID:      "stall-target",
		URL:     srv.URL,
		Timeout: 50 * time.Millisecond,
	})

	// Không được nhận 200 headers, body treo tới timeout, rồi vẫn báo success!
	if res.Outcome != OutcomeTimeout {
		t.Fatalf("expected OutcomeTimeout on stalled body, got %s (err=%q, status=%d)", res.Outcome, res.Error, res.StatusCode)
	}
	if !strings.Contains(res.Error, "timeout") {
		t.Errorf("expected error message to mention timeout, got %q", res.Error)
	}
}

func TestProbeSingle_TraceparentPropagation(t *testing.T) {
	var receivedTraceparent string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		receivedTraceparent = r.Header.Get("traceparent")
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	exporter := tracetest.NewInMemoryExporter()
	tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exporter))
	tracer := tp.Tracer("test-propagation")

	pool := NewPool(WithTracer(tracer))

	ctx, parentSpan := tracer.Start(context.Background(), "opsprobe.run")
	res := pool.ProbeSingle(ctx, Target{ID: "trace-target", URL: srv.URL})
	parentSpan.End()

	if res.Outcome != OutcomeSuccess {
		t.Fatalf("probe failed: %v", res.Error)
	}

	if receivedTraceparent == "" {
		t.Fatalf("expected outbound request to carry W3C traceparent header, got empty")
	}

	// traceparent có định dạng: 00-{trace_id}-{span_id}-{trace_flags}
	parts := strings.Split(receivedTraceparent, "-")
	if len(parts) != 4 || parts[0] != "00" {
		t.Fatalf("malformed traceparent header: %q", receivedTraceparent)
	}

	expectedTraceID := parentSpan.SpanContext().TraceID().String()
	if parts[1] != expectedTraceID {
		t.Errorf("traceparent trace ID %q does not match parent trace ID %q", parts[1], expectedTraceID)
	}
}

func TestProbeSingle_URLSanitizationAndSecretRedaction(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	exporter := tracetest.NewInMemoryExporter()
	tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exporter))
	tracer := tp.Tracer("test-redaction")

	pool := NewPool(WithTracer(tracer))

	secretToken := "supersecret123"
	secretQueryURL := srv.URL + "/health?token=" + secretToken + "&api_key=mysecretpass#fragment"
	target := Target{ID: "secret-target", URL: secretQueryURL}

	res := pool.ProbeSingle(context.Background(), target)
	if res.Outcome != OutcomeSuccess {
		t.Fatalf("probe failed: %v", res.Error)
	}

	// 1. Kiểm tra Result URL đã được sanitize
	if strings.Contains(res.URL, secretToken) || strings.Contains(res.URL, "mysecretpass") {
		t.Fatalf("secret leaked into Result.URL: %q", res.URL)
	}
	if strings.Contains(res.URL, "?") {
		t.Errorf("Result.URL still contains query string: %q", res.URL)
	}

	// 2. Kiểm tra Span attributes không chứa secret
	spans := exporter.GetSpans()
	for _, s := range spans {
		for _, attr := range s.Attributes {
			valStr := attr.Value.AsString()
			if strings.Contains(valStr, secretToken) || strings.Contains(valStr, "mysecretpass") {
				t.Fatalf("secret leaked into span attribute %s: %s", attr.Key, valStr)
			}
		}
	}
}
