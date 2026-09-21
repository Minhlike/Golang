package fixed

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestFetchReadsLocalServerResponse(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Fatalf("method = %s, want GET", r.Method)
		}
		fmt.Fprint(w, "ready")
	}))
	defer server.Close()

	reply, err := Fetch(context.Background(), server.Client(), server.URL)
	if err != nil {
		t.Fatalf("Fetch() error = %v", err)
	}
	if got, want := string(reply.Body), "ready"; got != want {
		t.Fatalf("body = %q, want %q", got, want)
	}
}

func TestFetchReturnsStatusError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusBadGateway)
	}))
	defer server.Close()

	_, err := Fetch(context.Background(), server.Client(), server.URL)
	statusErr, ok := err.(*StatusError)
	if !ok || statusErr.Code != http.StatusBadGateway {
		t.Fatalf("Fetch() error = %v, want StatusError 502", err)
	}
}
