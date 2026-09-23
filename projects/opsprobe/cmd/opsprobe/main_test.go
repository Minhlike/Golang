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
