package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRun_OneshotURL_Success(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("healthy"))
	}))
	defer srv.Close()

	args := []string{
		"--oneshot-url=" + srv.URL,
		"--timeout=1s",
		"--log-level=error",
	}

	if err := run(args); err != nil {
		t.Fatalf("expected run to succeed, got %v", err)
	}
}

func TestRun_OneshotURL_Failure(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer srv.Close()

	args := []string{
		"--oneshot-url=" + srv.URL,
		"--timeout=1s",
		"--log-level=error",
	}

	if err := run(args); err == nil {
		t.Fatalf("expected run to fail on 503 status, got nil")
	}
}

func TestRun_InvalidFlags(t *testing.T) {
	args := []string{"--invalid-flag-that-does-not-exist"}
	if err := run(args); err == nil {
		t.Fatalf("expected error on invalid flag, got nil")
	}
}

func TestRun_OneshotURL_WithTraceStdout(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	}))
	defer srv.Close()

	args := []string{
		"--oneshot-url=" + srv.URL,
		"--timeout=1s",
		"--log-level=error",
		"--trace-stdout=true",
	}

	if err := run(args); err != nil {
		t.Fatalf("expected run with trace-stdout to succeed, got %v", err)
	}
}

func TestRun_ConfigValidation(t *testing.T) {
	// 1. Invalid concurrency flag
	if err := run([]string{"--concurrency=0"}); err == nil {
		t.Errorf("expected error for concurrency=0, got nil")
	}

	// 2. Invalid max-active-runs flag
	if err := run([]string{"--max-active-runs=-1"}); err == nil {
		t.Errorf("expected error for max-active-runs=-1, got nil")
	}

	// 3. Invalid timeout flag (negative or excessive)
	if err := run([]string{"--timeout=-1s"}); err == nil {
		t.Errorf("expected error for negative timeout, got nil")
	}
	if err := run([]string{"--timeout=70s"}); err == nil {
		t.Errorf("expected error for timeout > 60s, got nil")
	}

	// 4. Invalid log-level flag
	if err := run([]string{"--log-level=verbose_la_sai"}); err == nil {
		t.Errorf("expected error for invalid log-level, got nil")
	}
}

func TestRun_EnvVarParsingErrors(t *testing.T) {
	// 1. Invalid OPSPROBE_CONCURRENCY env
	t.Setenv("OPSPROBE_CONCURRENCY", "abc")
	if err := run([]string{"--oneshot-url=http://example.com"}); err == nil {
		t.Errorf("expected error when OPSPROBE_CONCURRENCY is non-integer, got nil")
	}

	// 2. Invalid OPSPROBE_TIMEOUT env
	t.Setenv("OPSPROBE_CONCURRENCY", "")
	t.Setenv("OPSPROBE_TIMEOUT", "not-a-duration")
	if err := run([]string{"--oneshot-url=http://example.com"}); err == nil {
		t.Errorf("expected error when OPSPROBE_TIMEOUT is invalid duration, got nil")
	}

	// 3. Invalid OPSPROBE_LOG_LEVEL env
	t.Setenv("OPSPROBE_TIMEOUT", "")
	t.Setenv("OPSPROBE_LOG_LEVEL", "super_debug")
	if err := run([]string{"--oneshot-url=http://example.com"}); err == nil {
		t.Errorf("expected error when OPSPROBE_LOG_LEVEL is invalid, got nil")
	}
}
