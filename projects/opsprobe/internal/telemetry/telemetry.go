package telemetry

import (
	"context"
	"io"
	"log/slog"
	"os"

	"github.com/prometheus/client_golang/prometheus"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/trace"
)

// Telemetry chứa các thành phần observability hợp nhất: Logger, Metrics, và Tracer.
type Telemetry struct {
	Logger   *slog.Logger
	Registry *prometheus.Registry

	// Metrics
	ProbesTotal       *prometheus.CounterVec
	ProbeDurationSecs *prometheus.HistogramVec
	ActiveWorkers     prometheus.Gauge
	RunsTotal         *prometheus.CounterVec

	// OpenTelemetry
	TracerProvider *sdktrace.TracerProvider
	Tracer         trace.Tracer
}

// Config chứa cấu hình khởi tạo telemetry.
type Config struct {
	ServiceName string
	Environment string
	LogWriter   io.Writer
	LogLevel    slog.Level
	TraceWriter io.Writer // nil để disable stdout exporter hoặc ghi vào buffer
}

// New khởi tạo cấu trúc Telemetry độc lập, an toàn khi chạy song song nhiều instance.
func New(cfg Config) (*Telemetry, error) {
	if cfg.ServiceName == "" {
		cfg.ServiceName = "opsprobe"
	}
	if cfg.Environment == "" {
		cfg.Environment = "development"
	}
	if cfg.LogWriter == nil {
		cfg.LogWriter = os.Stdout
	}

	// 1. Cấu hình Structured JSON Logger
	handler := slog.NewJSONHandler(cfg.LogWriter, &slog.HandlerOptions{
		Level: cfg.LogLevel,
	})
	logger := slog.New(handler).With(
		slog.String("service", cfg.ServiceName),
		slog.String("env", cfg.Environment),
	)

	// 2. Cấu hình Prometheus Registry và Metrics cục bộ
	reg := prometheus.NewRegistry()

	probesTotal := prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "opsprobe_probes_total",
			Help: "Tổng số lượt kiểm tra target được thực thi, phân loại theo outcome.",
		},
		[]string{"outcome"},
	)

	probeDurationSecs := prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "opsprobe_probe_duration_seconds",
			Help:    "Thời gian phản hồi của từng lượt probe theo giây.",
			Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0},
		},
		[]string{"outcome"},
	)

	activeWorkers := prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "opsprobe_active_workers",
			Help: "Số worker goroutine đang thực thi probe đồng thời.",
		},
	)

	runsTotal := prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "opsprobe_runs_total",
			Help: "Tổng số đợt chạy probe được gửi qua API.",
		},
		[]string{"status"},
	)

	reg.MustRegister(probesTotal, probeDurationSecs, activeWorkers, runsTotal)

	// Khởi tạo trước các series nhãn chuẩn để metric family luôn xuất hiện khi scrape
	probesTotal.WithLabelValues("success")
	probesTotal.WithLabelValues("failure")
	probesTotal.WithLabelValues("timeout")
	probesTotal.WithLabelValues("cancel")
	runsTotal.WithLabelValues("completed")
	runsTotal.WithLabelValues("failed")

	// 3. Cấu hình OpenTelemetry Tracing
	var tp *sdktrace.TracerProvider
	if cfg.TraceWriter != nil {
		exporter, err := stdouttrace.New(
			stdouttrace.WithWriter(cfg.TraceWriter),
			stdouttrace.WithoutTimestamps(),
		)
		if err != nil {
			return nil, err
		}
		tp = sdktrace.NewTracerProvider(
			sdktrace.WithBatcher(exporter),
		)
	} else {
		// No-op tracer provider an toàn
		tp = sdktrace.NewTracerProvider()
	}

	tracer := tp.Tracer(cfg.ServiceName)

	return &Telemetry{
		Logger:            logger,
		Registry:          reg,
		ProbesTotal:       probesTotal,
		ProbeDurationSecs: probeDurationSecs,
		ActiveWorkers:     activeWorkers,
		RunsTotal:         runsTotal,
		TracerProvider:    tp,
		Tracer:            tracer,
	}, nil
}

// RecordProbe ghi nhận kết quả của một probe vào metrics và logger.
func (t *Telemetry) RecordProbe(targetID, url string, outcome string, durationSeconds float64, err string) {
	t.ProbesTotal.WithLabelValues(outcome).Inc()
	t.ProbeDurationSecs.WithLabelValues(outcome).Observe(durationSeconds)

	if outcome == "success" {
		t.Logger.Info("probe completed",
			slog.String("target_id", targetID),
			slog.String("url", url),
			slog.String("outcome", outcome),
			slog.Float64("duration_s", durationSeconds),
		)
	} else {
		t.Logger.Warn("probe failed",
			slog.String("target_id", targetID),
			slog.String("url", url),
			slog.String("outcome", outcome),
			slog.Float64("duration_s", durationSeconds),
			slog.String("error", err),
		)
	}
}

// StartSpan tạo một OpenTelemetry span cho thao tác.
func (t *Telemetry) StartSpan(ctx context.Context, name string, attrs ...attribute.KeyValue) (context.Context, trace.Span) {
	ctx, span := t.Tracer.Start(ctx, name)
	if len(attrs) > 0 {
		span.SetAttributes(attrs...)
	}
	return ctx, span
}

// Shutdown đóng tracer provider và flush trace dữ liệu.
func (t *Telemetry) Shutdown(ctx context.Context) error {
	if t.TracerProvider != nil {
		return t.TracerProvider.Shutdown(ctx)
	}
	return nil
}
