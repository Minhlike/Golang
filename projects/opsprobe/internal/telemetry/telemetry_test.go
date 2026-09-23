package telemetry

import (
	"bytes"
	"context"
	"encoding/json"
	"log/slog"
	"testing"

	"github.com/prometheus/client_golang/prometheus/testutil"
	"go.opentelemetry.io/otel/attribute"
)

func TestTelemetry_MetricsAndLogging(t *testing.T) {
	var logBuf bytes.Buffer
	var traceBuf bytes.Buffer

	tel, err := New(Config{
		ServiceName: "test-probe",
		Environment: "test",
		LogWriter:   &logBuf,
		LogLevel:    slog.LevelInfo,
		TraceWriter: &traceBuf,
	})
	if err != nil {
		t.Fatalf("failed to init telemetry: %v", err)
	}
	defer func() {
		_ = tel.Shutdown(context.Background())
	}()

	// Ghi nhận 1 success probe
	tel.RecordProbe("target-1", "http://example.com", "success", 0.045, "")

	// Kiểm tra Prometheus counter
	metricCount := testutil.ToFloat64(tel.ProbesTotal.WithLabelValues("success"))
	if metricCount != 1.0 {
		t.Fatalf("expected 1.0 for probes_total{outcome=success}, got %f", metricCount)
	}

	// Ghi nhận 1 timeout probe
	tel.RecordProbe("target-2", "http://slow.com", "timeout", 2.05, "deadline exceeded")
	timeoutCount := testutil.ToFloat64(tel.ProbesTotal.WithLabelValues("timeout"))
	if timeoutCount != 1.0 {
		t.Fatalf("expected 1.0 for probes_total{outcome=timeout}, got %f", timeoutCount)
	}

	// Kiểm tra log format là JSON hợp lệ
	var logEntry map[string]interface{}
	decoder := json.NewDecoder(&logBuf)
	if err := decoder.Decode(&logEntry); err != nil {
		t.Fatalf("log is not valid JSON: %v, raw: %s", err, logBuf.String())
	}

	if logEntry["service"] != "test-probe" {
		t.Errorf("expected service=test-probe, got %v", logEntry["service"])
	}
	if logEntry["target_id"] != "target-1" {
		t.Errorf("expected target_id=target-1, got %v", logEntry["target_id"])
	}
}

func TestTelemetry_Spans(t *testing.T) {
	tel, err := New(Config{
		ServiceName: "test-probe",
		Environment: "test",
	})
	if err != nil {
		t.Fatalf("failed to init telemetry: %v", err)
	}

	ctx, span := tel.StartSpan(context.Background(), "test-operation",
		attribute.String("test.key", "test.value"),
	)
	if span == nil {
		t.Fatalf("expected non-nil span")
	}
	span.End()

	if err := tel.Shutdown(ctx); err != nil {
		t.Fatalf("telemetry shutdown failed: %v", err)
	}
}
