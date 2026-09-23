package main

import (
	"context"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"example.com/golang-master/projects/opsprobe/internal/httpapi"
	"example.com/golang-master/projects/opsprobe/internal/probe"
	"example.com/golang-master/projects/opsprobe/internal/store"
	"example.com/golang-master/projects/opsprobe/internal/telemetry"
)

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	fs := flag.NewFlagSet("opsprobe", flag.ContinueOnError)

	addr := fs.String("addr", ":8080", "Dia chi TCP lang nghe cua HTTP server (vd :8080)")
	dbPath := fs.String("db", "opsprobe.db", "Duong dan tep SQLite luu tru (vd opsprobe.db hoac :memory:)")
	concurrency := fs.Int("concurrency", 4, "So worker goroutine thuc thi probe dong thoi")
	timeout := fs.Duration("timeout", 3*time.Second, "Timeout mac dinh cho moi luot probe target")
	maxActiveRuns := fs.Int("max-active-runs", 10, "So luot run dong thoi toi da truoc khi ap dung backpressure")
	logLevelStr := fs.String("log-level", "info", "Cap do log: debug, info, warn, error")
	oneshotURL := fs.String("oneshot-url", "", "Neu duoc chi dinh, chay kiem tra mot URL don le qua CLI roi thoat")

	if err := fs.Parse(args); err != nil {
		return err
	}

	// 1. Parse log level
	var logLevel slog.Level
	switch *logLevelStr {
	case "debug":
		logLevel = slog.LevelDebug
	case "warn":
		logLevel = slog.LevelWarn
	case "error":
		logLevel = slog.LevelError
	default:
		logLevel = slog.LevelInfo
	}

	// 2. Khoi tao Telemetry (Logger, Metrics, Tracing)
	tel, err := telemetry.New(telemetry.Config{
		ServiceName: "opsprobe",
		Environment: "production",
		LogWriter:   os.Stdout,
		LogLevel:    logLevel,
	})
	if err != nil {
		return fmt.Errorf("init telemetry: %w", err)
	}
	defer func() {
		_ = tel.Shutdown(context.Background())
	}()

	// 3. Khoi tao Probe Pool
	pool := probe.NewPool(
		probe.WithConcurrency(*concurrency),
		probe.WithDefaultTimeout(*timeout),
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
		tel.RecordProbe(res.TargetID, res.URL, string(res.Outcome), res.Duration.Seconds(), res.Error)

		if res.Outcome != probe.OutcomeSuccess {
			return fmt.Errorf("probe failed: outcome=%s error=%s", res.Outcome, res.Error)
		}
		fmt.Printf("probe success: target=%s status=%d duration=%s\n", res.URL, res.StatusCode, res.Duration)
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
