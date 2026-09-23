package incident

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestIncident_ConnectionReuseProof(t *testing.T) {
	// Server tra ve payload 10KB (nam trong gioi han MaxDrainBytes 16KB)
	payload10K := bytes.Repeat([]byte("X"), 10240)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(payload10K)
	}))
	defer srv.Close()

	client := &http.Client{
		Transport: &http.Transport{
			MaxIdleConns:        10,
			MaxIdleConnsPerHost: 10,
		},
	}

	iterations := 20

	// 1. Chay voi BuggyProbe: khong dong body
	newConnsBuggy, reusedConnsBuggy, err := RunTraceBenchmark(context.Background(), client, srv.URL, BuggyProbe, iterations)
	if err != nil {
		t.Fatalf("buggy probe failed: %v", err)
	}

	// 2. Chay voi FixedProbe: dong body + bounded drain 16KB (doc het 10KB -> EOF)
	newConnsFixed, reusedConnsFixed, err := RunTraceBenchmark(context.Background(), client, srv.URL, FixedProbe, iterations)
	if err != nil {
		t.Fatalf("fixed probe failed: %v", err)
	}

	t.Logf("Buggy: NewConns=%d, ReusedConns=%d", newConnsBuggy, reusedConnsBuggy)
	t.Logf("Fixed: NewConns=%d, ReusedConns=%d", newConnsFixed, reusedConnsFixed)

	// Bang chung thuc nghiem qua httptrace:
	// Buggy: Moi request buoc phai mo 1 ket noi moi vi body khong duoc dong/doc can
	if newConnsBuggy < int32(iterations) {
		t.Errorf("expected BuggyProbe to create %d new connections due to abandoned body, got %d", iterations, newConnsBuggy)
	}
	if reusedConnsBuggy > 0 {
		t.Errorf("expected BuggyProbe to reuse 0 connections, got %d", reusedConnsBuggy)
	}

	// Fixed: Chi 1-2 connection moi ban dau, dai da so duoc REUSED tu connection pool
	if newConnsFixed > 2 {
		t.Errorf("expected FixedProbe to create at most 2 new connection, got %d", newConnsFixed)
	}
	if reusedConnsFixed < int32(iterations-2) {
		t.Errorf("expected FixedProbe to reuse majority of connections, got %d", reusedConnsFixed)
	}
}

func TestIncident_BoundedDrainOversizedBody(t *testing.T) {
	// Server tra ve payload 32KB (vuot qua gioi han MaxDrainBytes 16KB)
	payload32K := bytes.Repeat([]byte("Y"), 32768)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(payload32K)
	}))
	defer srv.Close()

	client := &http.Client{}
	status, reusedEligible, err := FixedProbe(context.Background(), client, srv.URL)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if status != http.StatusOK {
		t.Fatalf("expected status 200, got %d", status)
	}
	// Chung minh bang chung: Body vuot qua 16KB se khong dat tieu chuan tai su dung (reusedEligible == false)
	if reusedEligible {
		t.Fatalf("expected reusedEligible to be false for 32KB payload exceeding MaxDrainBytes")
	}
}
