package fixed

import (
	"bytes"
	"context"
	"encoding/json"
	"net"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestCreateCheckAcceptsValidatedTarget(t *testing.T) {
	store := &memoryStore{}
	handler := NewHandler(store)
	req := httptest.NewRequest(http.MethodPost, "/v1/checks", bytes.NewBufferString(`{"target":"https://api.test/health"}`))
	resp := httptest.NewRecorder()

	handler.ServeHTTP(resp, req)
	result := resp.Result()
	defer result.Body.Close()
	if result.StatusCode != http.StatusCreated {
		t.Fatalf("status = %d, want %d", result.StatusCode, http.StatusCreated)
	}
	var got Check
	if err := json.NewDecoder(result.Body).Decode(&got); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if got.Target != "https://api.test/health" {
		t.Fatalf("response = %#v", got)
	}
}

func TestCreateCheckRejectsUnknownField(t *testing.T) {
	store := &memoryStore{}
	handler := NewHandler(store)
	req := httptest.NewRequest(http.MethodPost, "/v1/checks", bytes.NewBufferString(`{"target":"https://api.test","debug":true}`))
	resp := httptest.NewRecorder()

	handler.ServeHTTP(resp, req)
	if resp.Result().StatusCode != http.StatusBadRequest {
		t.Fatalf("status = %d, want %d", resp.Result().StatusCode, http.StatusBadRequest)
	}
	if len(store.created) != 0 {
		t.Fatalf("store received %#v", store.created)
	}
}

func TestCreateCheckRejectsMethod(t *testing.T) {
	handler := NewHandler(&memoryStore{})
	req := httptest.NewRequest(http.MethodGet, "/v1/checks", nil)
	resp := httptest.NewRecorder()

	handler.ServeHTTP(resp, req)
	if resp.Result().StatusCode != http.StatusMethodNotAllowed {
		t.Fatalf("status = %d, want %d", resp.Result().StatusCode, http.StatusMethodNotAllowed)
	}
}

func TestCreateCheckRejectsUnsafeScheme(t *testing.T) {
	handler := NewHandler(&memoryStore{})
	req := httptest.NewRequest(http.MethodPost, "/v1/checks", bytes.NewBufferString(`{"target":"file:///etc/passwd"}`))
	resp := httptest.NewRecorder()

	handler.ServeHTTP(resp, req)
	if resp.Result().StatusCode != http.StatusBadRequest {
		t.Fatalf("status = %d, want %d", resp.Result().StatusCode, http.StatusBadRequest)
	}
}

func TestCreateCheckRejectsAnotherJSONValue(t *testing.T) {
	store := &memoryStore{}
	handler := NewHandler(store)
	req := httptest.NewRequest(http.MethodPost, "/v1/checks", bytes.NewBufferString(`{"target":"https://api.test"} {"target":"https://other.test"}`))
	resp := httptest.NewRecorder()

	handler.ServeHTTP(resp, req)
	if resp.Result().StatusCode != http.StatusBadRequest {
		t.Fatalf("status = %d, want %d", resp.Result().StatusCode, http.StatusBadRequest)
	}
	if len(store.created) != 0 {
		t.Fatalf("store received %#v", store.created)
	}
}

func TestServeUntilStoppedDrainsAndReturns(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	ctx, cancel := context.WithCancel(context.Background())
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

func TestServeUntilStoppedRejectsNilServer(t *testing.T) {
	if err := ServeUntilStopped(context.Background(), nil, nil, time.Second); err == nil {
		t.Fatal("ServeUntilStopped(nil) error = nil")
	}
}

func TestServeUntilStoppedRejectsNilListener(t *testing.T) {
	if err := ServeUntilStopped(context.Background(), &http.Server{}, nil, time.Second); err == nil {
		t.Fatal("ServeUntilStopped(nil listener) error = nil")
	}
}

func TestServeUntilStoppedRejectsNonPositiveGrace(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	defer ln.Close()

	if err := ServeUntilStopped(context.Background(), &http.Server{}, ln, 0); err == nil {
		t.Fatal("ServeUntilStopped(zero grace) error = nil")
	}
}

type memoryStore struct{ created []Check }

func (s *memoryStore) Create(_ context.Context, check Check) (Check, error) {
	s.created = append(s.created, check)
	return check, nil
}
