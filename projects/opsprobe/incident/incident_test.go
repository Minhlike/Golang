package incident

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestIncident_ConnectionReuseProof(t *testing.T) {
	// Server trả về payload 10KB (vượt quá ngưỡng auto-drain của Go Transport khi Close)
	payload := bytes.Repeat([]byte("X"), 10240)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(payload)
	}))
	defer srv.Close()

	client := &http.Client{
		Transport: &http.Transport{
			MaxIdleConns:        10,
			MaxIdleConnsPerHost: 10,
		},
	}

	iterations := 20

	// 1. Chạy với BuggyProbe: không đọc cạn body
	newConnsBuggy, reusedConnsBuggy, err := RunTraceBenchmark(context.Background(), client, srv.URL, BuggyProbe, iterations)
	if err != nil {
		t.Fatalf("buggy probe failed: %v", err)
	}

	// 2. Chạy với FixedProbe: đọc cạn body rồi mới close
	newConnsFixed, reusedConnsFixed, err := RunTraceBenchmark(context.Background(), client, srv.URL, FixedProbe, iterations)
	if err != nil {
		t.Fatalf("fixed probe failed: %v", err)
	}

	t.Logf("Buggy: NewConns=%d, ReusedConns=%d", newConnsBuggy, reusedConnsBuggy)
	t.Logf("Fixed: NewConns=%d, ReusedConns=%d", newConnsFixed, reusedConnsFixed)

	// Kiểm chứng bản chất:
	// Buggy: Mỗi request buộc phải mở 1 kết nối mới vì body không được đọc cạn!
	if newConnsBuggy < int32(iterations) {
		t.Errorf("expected BuggyProbe to create %d new connections due to abandoned body, got %d", iterations, newConnsBuggy)
	}
	if reusedConnsBuggy > 0 {
		t.Errorf("expected BuggyProbe to reuse 0 connections, got %d", reusedConnsBuggy)
	}

	// Fixed: Chỉ 1 connection mới ban đầu, toàn bộ 19 request sau đều được REUSED từ pool!
	if newConnsFixed > 2 {
		t.Errorf("expected FixedProbe to create at most 2 new connection, got %d", newConnsFixed)
	}
	if reusedConnsFixed < int32(iterations-2) {
		t.Errorf("expected FixedProbe to reuse majority of connections, got %d", reusedConnsFixed)
	}
}
