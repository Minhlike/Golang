package main

import (
	"context"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"example.com/golang-master/part16-real-signals/probeapi"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	"go.opentelemetry.io/otel/sdk/trace"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stderr, nil))
	address, err := listenAddress(os.Getenv("PORT"))
	if err != nil {
		logger.Error("invalid configuration", "error", err)
		os.Exit(1)
	}
	exporter, err := stdouttrace.New(stdouttrace.WithPrettyPrint())
	if err != nil {
		fmt.Fprintln(os.Stderr, "create trace exporter:", err)
		os.Exit(1)
	}
	provider := trace.NewTracerProvider(trace.WithBatcher(exporter))
	defer func() { _ = provider.Shutdown(context.Background()) }()

	server := &http.Server{
		Addr:              address,
		Handler:           probeapi.NewHandler(logger, provider.Tracer("probe-api"), nil),
		ReadHeaderTimeout: 5 * time.Second,
	}
	stopped := make(chan error, 1)
	go func() { stopped <- server.ListenAndServe() }()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	select {
	case err := <-stopped:
		if err != nil && err != http.ErrServerClosed {
			logger.Error("server stopped unexpectedly", "error", err)
			os.Exit(1)
		}
	case <-ctx.Done():
		shutdown, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := server.Shutdown(shutdown); err != nil {
			logger.Error("graceful shutdown failed", "error", err)
			os.Exit(1)
		}
	}
}

func listenAddress(port string) (string, error) {
	if port == "" {
		return ":8080", nil
	}
	number, err := strconv.Atoi(port)
	if err != nil || number < 1 || number > 65535 {
		return "", fmt.Errorf("PORT must be an integer from 1 to 65535")
	}
	return ":" + port, nil
}
