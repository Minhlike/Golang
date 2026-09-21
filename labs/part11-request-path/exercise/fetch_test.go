//go:build exercise

package exercise

import (
	"bytes"
	"context"
	"errors"
	"io"
	"net/http"
	"testing"
)

func TestFetchUsesContextAndClosesBody(t *testing.T) {
	key := struct{}{}
	ctx := context.WithValue(context.Background(), key, "request-42")
	body := &trackingBody{Reader: bytes.NewBufferString("ok")}
	transport := roundTripperFunc(func(req *http.Request) (*http.Response, error) {
		if got := req.Context().Value(key); got != "request-42" {
			t.Fatalf("request lost context value: %v", got)
		}
		if req.Method != http.MethodGet {
			t.Fatalf("method = %s, want GET", req.Method)
		}
		return &http.Response{StatusCode: http.StatusOK, Body: body, Header: make(http.Header)}, nil
	})

	reply, err := Fetch(ctx, &http.Client{Transport: transport}, "https://service.test/health")
	if err != nil {
		t.Fatalf("Fetch() error = %v", err)
	}
	if reply.StatusCode != http.StatusOK || string(reply.Body) != "ok" {
		t.Fatalf("Fetch() = %#v, want 200 and body ok", reply)
	}
	if !body.closed {
		t.Fatal("Fetch() did not close response body")
	}
}

func TestFetchTurnsNon2xxIntoStatusError(t *testing.T) {
	transport := roundTripperFunc(func(*http.Request) (*http.Response, error) {
		return &http.Response{
			StatusCode: http.StatusServiceUnavailable,
			Body:       io.NopCloser(bytes.NewBufferString("try later")),
			Header:     make(http.Header),
		}, nil
	})

	_, err := Fetch(context.Background(), &http.Client{Transport: transport}, "https://service.test/health")
	var statusErr *StatusError
	if !errors.As(err, &statusErr) || statusErr.Code != http.StatusServiceUnavailable {
		t.Fatalf("Fetch() error = %v, want StatusError 503", err)
	}
}

type roundTripperFunc func(*http.Request) (*http.Response, error)

func (f roundTripperFunc) RoundTrip(req *http.Request) (*http.Response, error) { return f(req) }

type trackingBody struct {
	io.Reader
	closed bool
}

func (b *trackingBody) Close() error {
	b.closed = true
	return nil
}
