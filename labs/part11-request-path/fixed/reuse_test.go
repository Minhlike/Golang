package fixed

import (
	"io"
	"net/http"
	"net/http/httptest"
	"net/http/httptrace"
	"testing"
)

func TestTransportReusesIdleConnection(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		_, _ = io.WriteString(w, "ok")
	}))
	defer server.Close()

	transport := http.DefaultTransport.(*http.Transport).Clone()
	transport.ForceAttemptHTTP2 = false
	defer transport.CloseIdleConnections()
	client := &http.Client{Transport: transport}

	if reused := requestConnectionReuse(t, client, server.URL); reused {
		t.Fatal("first request unexpectedly reused a connection")
	}
	if reused := requestConnectionReuse(t, client, server.URL); !reused {
		t.Fatal("second request did not reuse the idle connection")
	}
}

func requestConnectionReuse(t *testing.T, client *http.Client, url string) bool {
	t.Helper()
	var reused bool
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		t.Fatalf("NewRequest() error = %v", err)
	}
	req = req.WithContext(httptrace.WithClientTrace(req.Context(), &httptrace.ClientTrace{
		GotConn: func(info httptrace.GotConnInfo) { reused = info.Reused },
	}))
	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("Do() error = %v", err)
	}
	if _, err := io.Copy(io.Discard, resp.Body); err != nil {
		resp.Body.Close()
		t.Fatalf("read response body: %v", err)
	}
	if err := resp.Body.Close(); err != nil {
		t.Fatalf("close response body: %v", err)
	}
	return reused
}
