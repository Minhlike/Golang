// Package probeapi exposes a deliberately small HTTP service for the second
// stage of the observability lab. It is not an observability platform.
package probeapi

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/trace"
)

const (
	ModeOK      = "ok"
	ModeSlow    = "slow"
	ModeFail    = "fail"
	ModeTimeout = "timeout"
)

type metrics struct {
	requests *prometheus.CounterVec
	duration *prometheus.HistogramVec
}

// NewHandler creates a handler with a private registry. A private registry
// makes the evidence from this lab and its tests explicit: it contains only
// the two application metrics below.
func NewHandler(logger *slog.Logger, tracer trace.Tracer, registry *prometheus.Registry) http.Handler {
	if logger == nil {
		logger = slog.Default()
	}
	if tracer == nil {
		tracer = trace.NewNoopTracerProvider().Tracer("probe-api")
	}
	if registry == nil {
		registry = prometheus.NewRegistry()
	}

	m := metrics{
		requests: prometheus.NewCounterVec(prometheus.CounterOpts{
			Name: "probe_requests_total",
			Help: "Completed probe requests, grouped by a bounded outcome.",
		}, []string{"outcome"}),
		duration: prometheus.NewHistogramVec(prometheus.HistogramOpts{
			Name:    "probe_request_duration_seconds",
			Help:    "End-to-end probe request duration in seconds.",
			Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25},
		}, []string{"outcome"}),
	}
	registry.MustRegister(m.requests, m.duration)

	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.HandlerFor(registry, promhttp.HandlerOpts{}))
	mux.HandleFunc("/livez", health)
	mux.HandleFunc("/readyz", health)
	mux.HandleFunc("/probe", probe(logger, tracer, m))
	return mux
}

func health(w http.ResponseWriter, _ *http.Request) {
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("ok\n"))
}

func probe(logger *slog.Logger, tracer trace.Tracer, m metrics) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		started := time.Now()
		ctx, span := tracer.Start(r.Context(), "probe.request", trace.WithSpanKind(trace.SpanKindServer))
		defer span.End()

		mode := r.URL.Query().Get("mode")
		outcome, err := runDependency(ctx, tracer, mode)
		status := statusFor(outcome)
		if err != nil {
			span.RecordError(err)
			span.SetStatus(codes.Error, outcome)
		}
		span.SetAttributes(
			attribute.String("probe.mode", mode),
			attribute.String("probe.outcome", outcome),
		)

		duration := time.Since(started)
		m.requests.WithLabelValues(outcome).Inc()
		m.duration.WithLabelValues(outcome).Observe(duration.Seconds())
		logger.Info("probe completed",
			"mode", mode,
			"outcome", outcome,
			"status", status,
			"duration_ms", duration.Milliseconds(),
		)

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(status)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"mode":    mode,
			"outcome": outcome,
		})
	}
}

func runDependency(ctx context.Context, tracer trace.Tracer, mode string) (string, error) {
	ctx, span := tracer.Start(ctx, "probe.dependency", trace.WithSpanKind(trace.SpanKindClient))
	defer span.End()
	span.SetAttributes(attribute.String("probe.mode", mode))

	switch mode {
	case ModeOK:
		return "success", nil
	case ModeSlow:
		if err := wait(ctx, 40*time.Millisecond); err != nil {
			return "timeout", err
		}
		return "success", nil
	case ModeFail:
		err := errors.New("simulated dependency failure")
		span.RecordError(err)
		span.SetStatus(codes.Error, "dependency failure")
		return "failure", err
	case ModeTimeout:
		deadline, cancel := context.WithTimeout(ctx, 20*time.Millisecond)
		defer cancel()
		err := wait(deadline, 80*time.Millisecond)
		span.RecordError(err)
		span.SetStatus(codes.Error, "deadline exceeded")
		return "timeout", err
	default:
		err := errors.New("mode must be one of ok, slow, fail, timeout")
		span.RecordError(err)
		span.SetStatus(codes.Error, "invalid mode")
		return "failure", err
	}
}

func wait(ctx context.Context, d time.Duration) error {
	timer := time.NewTimer(d)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-timer.C:
		return nil
	}
}

func statusFor(outcome string) int {
	switch outcome {
	case "success":
		return http.StatusOK
	case "timeout":
		return http.StatusGatewayTimeout
	default:
		return http.StatusServiceUnavailable
	}
}
