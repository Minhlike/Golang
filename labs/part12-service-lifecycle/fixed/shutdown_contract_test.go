package fixed

import (
	"bytes"
	"context"
	"errors"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestShutdownExpiredBudgetDoesNotFinishActiveHandler(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	started, release, finished := make(chan context.Context, 1), make(chan struct{}), make(chan struct{})
	srv := &http.Server{Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		started <- r.Context()
		<-release
		w.WriteHeader(http.StatusNoContent)
		close(finished)
	})}
	serveDone := make(chan error, 1)
	go func() { serveDone <- srv.Serve(ln) }()
	client := &http.Client{Timeout: 5 * time.Second}
	clientDone := make(chan error, 1)
	go func() {
		resp, err := client.Get("http://" + ln.Addr().String())
		if err == nil {
			_, _ = io.Copy(io.Discard, resp.Body)
			_ = resp.Body.Close()
		}
		clientDone <- err
	}()
	// Even an assertion failure releases and joins everything the fixture owns.
	defer func() { close(release); _ = srv.Close(); <-finished; <-serveDone; <-clientDone }()
	requestCtx := <-started
	budget, cancel := context.WithDeadline(context.Background(), time.Now().Add(-time.Second))
	defer cancel()
	if err := srv.Shutdown(budget); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("Shutdown expired budget = %v", err)
	}
	if err := requestCtx.Err(); err != nil {
		t.Fatalf("Shutdown canceled active request: %v", err)
	}
	select {
	case <-finished:
		t.Fatal("deadline falsely treated as handler completion")
	default:
	}
}

func TestShutdownCallbackIsNotificationNotJoin(t *testing.T) {
	started, release, finished := make(chan struct{}), make(chan struct{}), make(chan struct{})
	srv := &http.Server{}
	srv.RegisterOnShutdown(func() { close(started); <-release; close(finished) })
	defer func() { close(release); <-finished }()
	if err := srv.Shutdown(context.Background()); err != nil {
		t.Fatal(err)
	}
	<-started
	select {
	case <-finished:
		t.Fatal("blocked callback unexpectedly finished")
	default:
	}
}

func TestJSONBoundaryDocumentsDuplicateCaseAndSizePolicy(t *testing.T) {
	for _, body := range []string{
		`{"target":"https://first.test","target":"https://last.test"}`,
		`{"TARGET":"https://last.test"}`,
	} {
		store := &memoryStore{}
		w := httptest.NewRecorder()
		NewHandler(store).ServeHTTP(w, httptest.NewRequest(http.MethodPost, "/v1/checks", bytes.NewBufferString(body)))
		if w.Code != http.StatusCreated || len(store.created) != 1 || store.created[0].Target != "https://last.test" {
			t.Fatalf("encoding/json compatibility policy changed: status=%d values=%v", w.Code, store.created)
		}
	}
	store := &memoryStore{}
	w := httptest.NewRecorder()
	body := append([]byte(`{"target":"https://last.test"}`), bytes.Repeat([]byte(" "), maxRequestBody)...)
	NewHandler(store).ServeHTTP(w, httptest.NewRequest(http.MethodPost, "/v1/checks", bytes.NewReader(body)))
	if w.Code != http.StatusBadRequest || len(store.created) != 0 {
		t.Fatal("oversized body reached Store")
	}
}
