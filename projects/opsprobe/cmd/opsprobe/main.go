package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"log/slog"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"example.com/golang-master/projects/opsprobe/internal/httpapi"
	"example.com/golang-master/projects/opsprobe/internal/probe"
	"example.com/golang-master/projects/opsprobe/internal/store"
	"example.com/golang-master/projects/opsprobe/internal/telemetry"
)

func getEnvString(key string) (string, bool) {
	val, ok := os.LookupEnv(key)
	if !ok || val == "" {
		return "", false
	}
	return val, true
}

func getEnvInt(key string) (int, bool, error) {
	val, ok := os.LookupEnv(key)
	if !ok || val == "" {
		return 0, false, nil
	}
	n, err := strconv.Atoi(val)
	if err != nil {
		return 0, true, fmt.Errorf("invalid integer for %s=%q: %w", key, val, err)
	}
	return n, true, nil
}

func getEnvDuration(key string) (time.Duration, bool, error) {
	val, ok := os.LookupEnv(key)
	if !ok || val == "" {
		return 0, false, nil
	}
	d, err := time.ParseDuration(val)
	if err != nil {
		return 0, true, fmt.Errorf("invalid duration for %s=%q: %w", key, val, err)
	}
	return d, true, nil
}

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	defaultConcurrency := 4
	if val, set, err := getEnvInt("OPSPROBE_CONCURRENCY"); err != nil {
		return fmt.Errorf("config error: %w", err)
	} else if set {
		defaultConcurrency = val
	}

	defaultTimeout := 3 * time.Second
	if val, set, err := getEnvDuration("OPSPROBE_TIMEOUT"); err != nil {
		return fmt.Errorf("config error: %w", err)
	} else if set {
		defaultTimeout = val
	}

	defaultMaxActiveRuns := 10
	if val, set, err := getEnvInt("OPSPROBE_MAX_ACTIVE_RUNS"); err != nil {
		return fmt.Errorf("config error: %w", err)
	} else if set {
		defaultMaxActiveRuns = val
	}

	defaultAddr := "127.0.0.1:8080"
	if val, set := getEnvString("OPSPROBE_ADDR"); set {
		defaultAddr = val
	}

	defaultDB := "opsprobe.db"
	if val, set := getEnvString("OPSPROBE_DB"); set {
		defaultDB = val
	}

	defaultLogLevel := "info"
	if val, set := getEnvString("OPSPROBE_LOG_LEVEL"); set {
		defaultLogLevel = val
	}

	defaultEnv := "development"
	if val, set := getEnvString("OPSPROBE_ENV"); set {
		defaultEnv = val
	}

	fs := flag.NewFlagSet("opsprobe", flag.ContinueOnError)

	addr := fs.String("addr", defaultAddr, "Dia chi TCP lang nghe cua HTTP server (mac dinh 127.0.0.1:8080 de tranh open exposure)")
	dbPath := fs.String("db", defaultDB, "Duong dan tep SQLite luu tru (vd opsprobe.db hoac :memory:)")
	concurrency := fs.Int("concurrency", defaultConcurrency, "So worker goroutine thuc thi probe dong thoi")
	timeout := fs.Duration("timeout", defaultTimeout, "Timeout mac dinh cho moi luot probe target (0 < t <= 60s)")
	maxActiveRuns := fs.Int("max-active-runs", defaultMaxActiveRuns, "So luot run dong thoi toi da truoc khi ap dung backpressure")
	logLevelStr := fs.String("log-level", defaultLogLevel, "Cap do log: debug, info, warn, error")
	envStr := fs.String("env", defaultEnv, "Moi truong chay: development, staging, production")
	traceStdout := fs.Bool("trace-stdout", false, "In OpenTelemetry traces truc tiep ra stdout de debug cuc bo")
	oneshotURL := fs.String("oneshot-url", "", "Neu duoc chi dinh, chay kiem tra mot URL don le qua CLI roi thoat")

	if err := fs.Parse(args); err != nil {
		return err
	}

	// 1. Validation cac rang buoc tham so
	if *concurrency <= 0 {
		return fmt.Errorf("invalid concurrency: %d (must be > 0)", *concurrency)
	}
	if *maxActiveRuns <= 0 {
		return fmt.Errorf("invalid max-active-runs: %d (must be > 0)", *maxActiveRuns)
	}
	if *timeout <= 0 || *timeout > 60*time.Second {
		return fmt.Errorf("invalid timeout: %v (must be > 0 and <= 60s)", *timeout)
	}

	var logLevel slog.Level
	switch *logLevelStr {
	case "debug":
		logLevel = slog.LevelDebug
	case "info":
		logLevel = slog.LevelInfo
	case "warn":
		logLevel = slog.LevelWarn
	case "error":
		logLevel = slog.LevelError
	default:
		return fmt.Errorf("invalid log-level %q: must be one of debug, info, warn, error", *logLevelStr)
	}

	// 2. Khoi tao Telemetry (Logger, Metrics, Tracing)
	var traceWriter io.Writer
	if *traceStdout {
		traceWriter = os.Stdout
	}

	tel, err := telemetry.New(telemetry.Config{
		ServiceName: "opsprobe",
		Environment: *envStr,
		LogWriter:   os.Stdout,
		LogLevel:    logLevel,
		TraceWriter: traceWriter,
	})
	if err != nil {
		return fmt.Errorf("init telemetry: %w", err)
	}
	defer func() {
		_ = tel.Shutdown(context.Background())
	}()

	// 3. Khoi tao Probe Pool voi worker observer va tracer
	pool := probe.NewPool(
		probe.WithConcurrency(*concurrency),
		probe.WithDefaultTimeout(*timeout),
		probe.WithWorkerObserver(tel),
		probe.WithTracer(tel.Tracer),
	)

	// 4. Neu co co --oneshot-url, chay che do CLI mot lan duy nhat
	if *oneshotURL != "" {
		ctx, cancel := context.WithTimeout(context.Background(), *timeout)
		defer cancel()

		target := probe.Target{
			ID:  "cli-target",
			URL: *oneshotURL,
		}
		res := pool.ProbeSingle(ctx, target)
		tel.RecordProbe(res.TargetID, res.URL, string(res.Outcome), float64(res.DurationNs)/1e9, res.Error)

		if res.Outcome != probe.OutcomeSuccess {
			return fmt.Errorf("probe failed: outcome=%s error=%s", res.Outcome, res.Error)
		}
		fmt.Printf("probe success: target=%s status=%d duration=%.2fms reused_eligible=%t\n",
			res.URL, res.StatusCode, res.DurationMs, res.ReusedEligible)
		return nil
	}

	// 5. Khoi tao Store (SQLite)
	s, err := store.NewSQLiteStore(*dbPath)
	if err != nil {
		return fmt.Errorf("open store: %w", err)
	}
	defer s.Close()

	initCtx, initCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer initCancel()
	if err := s.Init(initCtx); err != nil {
		return fmt.Errorf("init store schema: %w", err)
	}

	// 6. Thiet lap graceful shutdown context bat tin hieu he dieu hanh
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	// 7. Khoi tao HTTP Server
	server := httpapi.NewServer(httpapi.ServerConfig{
		Addr: *addr,
		APIConfig: httpapi.Config{
			Store:         s,
			ProbePool:     pool,
			Telemetry:     tel,
			MaxActiveRuns: *maxActiveRuns,
		},
	})

	serverErr := make(chan error, 1)
	go func() {
		tel.Logger.Info("starting opsprobe daemon",
			slog.String("addr", *addr),
			slog.String("db", *dbPath),
			slog.Int("concurrency", *concurrency),
			slog.Duration("timeout", *timeout),
			slog.Bool("trace_stdout", *traceStdout),
		)
		serverErr <- server.Start()
	}()

	// 8. Cho doi tin hieu shutdown hoac loi tu server
	select {
	case err := <-serverErr:
		return fmt.Errorf("server runtime error: %w", err)
	case <-ctx.Done():
		tel.Logger.Info("shutdown signal received, draining active requests...")
	}

	// 9. Graceful shutdown voi timeout toi da 10 giay
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		return fmt.Errorf("server graceful shutdown failed: %w", err)
	}

	tel.Logger.Info("opsprobe shutdown complete")
	return nil
}
