//go:build lifecycleexercise

package exercise

import (
	"context"
	"net"
	"net/http"
	"testing"
	"time"
)

func TestServeUntilStoppedServesThenStops(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	srv := &http.Server{Handler: http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	})}
	done := make(chan error, 1)
	go func() { done <- ServeUntilStopped(ctx, srv, ln, time.Second) }()

	client := &http.Client{Timeout: time.Second}
	resp, err := client.Get("http://" + ln.Addr().String() + "/healthz")
	if err != nil {
		t.Fatalf("request while serving: %v", err)
	}
	resp.Body.Close()

	cancel()
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("ServeUntilStopped() error = %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("ServeUntilStopped did not return after cancellation")
	}
}

func TestServeUntilStoppedRejectsInvalidInputs(t *testing.T) {
	if err := ServeUntilStopped(context.Background(), nil, nil, time.Second); err == nil {
		t.Fatal("nil server was accepted")
	}
	if err := ServeUntilStopped(context.Background(), &http.Server{}, nil, time.Second); err == nil {
		t.Fatal("nil listener was accepted")
	}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	defer ln.Close()
	if err := ServeUntilStopped(context.Background(), &http.Server{}, ln, 0); err == nil {
		t.Fatal("non-positive shutdown grace was accepted")
	}
}
