package fixed

import (
	"context"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"net/http/httptrace"
	"strings"
	"sync/atomic"
	"testing"
)

type contractTransport func(*http.Request) (*http.Response, error)

func (f contractTransport) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

type contractBody struct {
	io.Reader
	closed bool
}

func (b *contractBody) Close() error { b.closed = true; return nil }

type failingReader struct{ err error }

func (r failingReader) Read([]byte) (int, error) { return 0, r.err }

func TestFetchClosesBodyOnSuccessStatusAndReadFailure(t *testing.T) {
	readErr := errors.New("injected body read failure")
	for _, status := range []int{http.StatusOK, http.StatusBadGateway} {
		for _, failRead := range []bool{false, true} {
			body := &contractBody{Reader: strings.NewReader("ready")}
			if failRead {
				body.Reader = failingReader{readErr}
			}
			key := struct{}{}
			ctx := context.WithValue(context.Background(), key, "request-42")
			client := &http.Client{Transport: contractTransport(func(r *http.Request) (*http.Response, error) {
				if r.Context().Value(key) != "request-42" {
					t.Fatal("outbound request lost caller context")
				}
				return &http.Response{StatusCode: status, Body: body, Header: make(http.Header)}, nil
			})}
			_, err := Fetch(ctx, client, "https://service.test")
			if !body.closed {
				t.Fatal("response body was not closed")
			}
			var statusErr *StatusError
			switch {
			case failRead:
				if !errors.Is(err, readErr) {
					t.Fatalf("read error = %v", err)
				}
			case status == http.StatusBadGateway:
				if !errors.As(err, &statusErr) || statusErr.Code != status {
					t.Fatalf("status error = %v", err)
				}
			default:
				if err != nil {
					t.Fatal(err)
				}
			}
		}
	}
}

func TestLiteralIPNeedsNoDNSAndServerMayPreventReuse(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Connection", "close")
		_, _ = io.WriteString(w, "ready")
	}))
	defer server.Close()
	transport := &http.Transport{Proxy: nil}
	defer transport.CloseIdleConnections()
	client := &http.Client{Transport: transport}
	var dns, reused atomic.Int32
	ctx := httptrace.WithClientTrace(context.Background(), &httptrace.ClientTrace{
		DNSStart: func(httptrace.DNSStartInfo) { dns.Add(1) },
		GotConn: func(info httptrace.GotConnInfo) {
			if info.Reused {
				reused.Add(1)
			}
		},
	})
	for range 2 {
		if _, err := Fetch(ctx, client, server.URL); err != nil {
			t.Fatal(err)
		}
	}
	if dns.Load() != 0 {
		t.Fatal("literal loopback IP unexpectedly invoked DNS")
	}
	if reused.Load() != 0 {
		t.Fatal("server-close connection unexpectedly reused")
	}
}
