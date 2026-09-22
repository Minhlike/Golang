package probeapi

import (
	"bytes"
	"context"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/prometheus/client_golang/prometheus"
	"go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
)

func TestProbeEmitsBoundedMetricsAndParentChildTrace(t *testing.T) {
	registry := prometheus.NewRegistry()
	var logs bytes.Buffer
	recorder := tracetest.NewSpanRecorder()
	provider := trace.NewTracerProvider(trace.WithSpanProcessor(recorder))
	t.Cleanup(func() { _ = provider.Shutdown(context.Background()) })

	h := NewHandler(
		slog.New(slog.NewJSONHandler(&logs, nil)),
		provider.Tracer("probe-api"),
		registry,
	)
	response := httptest.NewRecorder()
	h.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/probe?mode=ok", nil))
	if response.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", response.Code, http.StatusOK)
	}

	spans := recorder.Ended()
	if len(spans) != 2 {
		t.Fatalf("ended spans = %d, want 2", len(spans))
	}
	var parent, child bool
	for _, span := range spans {
		if span.Name() == "probe.request" {
			parent = true
		}
		if span.Name() == "probe.dependency" && span.Parent().IsValid() {
			child = true
		}
	}
	if !parent || !child {
		t.Fatalf("missing request/child relation: %#v", spans)
	}

	metrics := httptest.NewRecorder()
	h.ServeHTTP(metrics, httptest.NewRequest(http.MethodGet, "/metrics", nil))
	body := metrics.Body.String()
	if !strings.Contains(body, `probe_requests_total{outcome="success"} 1`) {
		t.Fatalf("success counter missing from metrics:\n%s", body)
	}
	if strings.Contains(body, "mode=") {
		t.Fatalf("mode must not be a metric label:\n%s", body)
	}
	if !strings.Contains(logs.String(), `"outcome":"success"`) {
		t.Fatalf("structured log lacks outcome: %s", logs.String())
	}
}

func TestProbeFailureModesHaveDistinctOutcomes(t *testing.T) {
	for _, tc := range []struct {
		mode   string
		status int
		body   string
	}{
		{ModeFail, http.StatusServiceUnavailable, `"outcome":"failure"`},
		{ModeTimeout, http.StatusGatewayTimeout, `"outcome":"timeout"`},
		{"bad", http.StatusServiceUnavailable, `"outcome":"failure"`},
	} {
		t.Run(tc.mode, func(t *testing.T) {
			h := NewHandler(slog.New(slog.NewTextHandler(&bytes.Buffer{}, nil)), nil, prometheus.NewRegistry())
			response := httptest.NewRecorder()
			h.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/probe?mode="+tc.mode, nil))
			if response.Code != tc.status {
				t.Fatalf("status = %d, want %d", response.Code, tc.status)
			}
			if !strings.Contains(response.Body.String(), tc.body) {
				t.Fatalf("body = %s, want %s", response.Body.String(), tc.body)
			}
		})
	}
}
