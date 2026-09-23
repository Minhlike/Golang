package httpapi

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"example.com/golang-master/projects/opsprobe/internal/probe"
	"example.com/golang-master/projects/opsprobe/internal/store"
	"example.com/golang-master/projects/opsprobe/internal/telemetry"
)

func setupTestAPI(t *testing.T, maxActiveRuns int) (*API, *store.SQLiteStore, *telemetry.Telemetry) {
	t.Helper()

	s, err := store.NewSQLiteStore(":memory:")
	if err != nil {
		t.Fatalf("failed to create sqlite store: %v", err)
	}
	if err := s.Init(context.Background()); err != nil {
		t.Fatalf("failed to init store: %v", err)
	}

	tel, err := telemetry.New(telemetry.Config{
		ServiceName: "test-opsprobe",
		Environment: "test",
		LogWriter:   io.Discard,
		LogLevel:    slog.LevelError,
	})
	if err != nil {
		t.Fatalf("failed to create telemetry: %v", err)
	}

	pool := probe.NewPool(
		probe.WithConcurrency(2),
		probe.WithDefaultTimeout(1*time.Second),
	)

	api := NewAPI(Config{
		Store:         s,
		ProbePool:     pool,
		Telemetry:     tel,
		MaxActiveRuns: maxActiveRuns,
	})

	t.Cleanup(func() {
		_ = s.Close()
		_ = tel.Shutdown(context.Background())
	})

	return api, s, tel
}

func TestAPI_CreateAndGetRun(t *testing.T) {
	// Mock target servers
	target1 := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	}))
	defer target1.Close()

	target2 := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer target2.Close()

	api, _, _ := setupTestAPI(t, 5)
	handler := api.Routes()

	// 1. Gửi request POST /runs
	reqPayload := createRunRequest{
		Targets: []probe.Target{
			{ID: "api-good", URL: target1.URL},
			{ID: "api-bad", URL: target2.URL},
		},
	}
	payloadBytes, _ := json.Marshal(reqPayload)

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodPost, "/runs", bytes.NewReader(payloadBytes))
	req.Header.Set("Content-Type", "application/json")
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusCreated {
		t.Fatalf("expected status 201 Created, got %d, body: %s", rec.Code, rec.Body.String())
	}

	var createResp runDetailResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &createResp); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if createResp.Run == nil || createResp.Run.ID == "" {
		t.Fatalf("expected non-empty run ID")
	}
	if createResp.Run.TargetCount != 2 || createResp.Run.SuccessCount != 1 || createResp.Run.FailureCount != 1 {
		t.Errorf("unexpected counts: %+v", createResp.Run)
	}
	if len(createResp.Results) != 2 {
		t.Fatalf("expected 2 probe results, got %d", len(createResp.Results))
	}

	runID := createResp.Run.ID

	// 2. Gửi request GET /runs/{id}
	recGet := httptest.NewRecorder()
	reqGet := httptest.NewRequest(http.MethodGet, "/runs/"+runID, nil)
	handler.ServeHTTP(recGet, reqGet)

	if recGet.Code != http.StatusOK {
		t.Fatalf("expected status 200 OK, got %d", recGet.Code)
	}

	var getResp runDetailResponse
	if err := json.Unmarshal(recGet.Body.Bytes(), &getResp); err != nil {
		t.Fatalf("failed to decode get response: %v", err)
	}

	if getResp.Run.ID != runID {
		t.Errorf("expected run ID %s, got %s", runID, getResp.Run.ID)
	}
	if len(getResp.Results) != 2 {
		t.Errorf("expected 2 results, got %d", len(getResp.Results))
	}
}

func TestAPI_GetRun_NotFound(t *testing.T) {
	api, _, _ := setupTestAPI(t, 5)
	handler := api.Routes()

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/runs/unknown-id", nil)
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusNotFound {
		t.Fatalf("expected status 404, got %d", rec.Code)
	}
}

func TestAPI_ReadinessAndLiveness(t *testing.T) {
	api, s, _ := setupTestAPI(t, 5)
	handler := api.Routes()

	// Livez luôn 200
	recLive := httptest.NewRecorder()
	reqLive := httptest.NewRequest(http.MethodGet, "/livez", nil)
	handler.ServeHTTP(recLive, reqLive)
	if recLive.Code != http.StatusOK {
		t.Fatalf("expected 200 for /livez, got %d", recLive.Code)
	}

	// Readyz khi DB mở: 200
	recReady := httptest.NewRecorder()
	reqReady := httptest.NewRequest(http.MethodGet, "/readyz", nil)
	handler.ServeHTTP(recReady, reqReady)
	if recReady.Code != http.StatusOK {
		t.Fatalf("expected 200 for /readyz, got %d", recReady.Code)
	}

	// Đóng DB: Readyz phải fail 503
	_ = s.Close()
	recReadyFail := httptest.NewRecorder()
	reqReadyFail := httptest.NewRequest(http.MethodGet, "/readyz", nil)
	handler.ServeHTTP(recReadyFail, reqReadyFail)
	if recReadyFail.Code != http.StatusServiceUnavailable {
		t.Fatalf("expected 503 for /readyz after store close, got %d", recReadyFail.Code)
	}
}

func TestAPI_Metrics(t *testing.T) {
	api, _, _ := setupTestAPI(t, 5)
	handler := api.Routes()

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/metrics", nil)
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200 for /metrics, got %d", rec.Code)
	}

	body := rec.Body.String()
	if !bytes.Contains([]byte(body), []byte("opsprobe_probes_total")) {
		t.Errorf("metrics response does not contain opsprobe_probes_total")
	}
}

func TestAPI_Backpressure(t *testing.T) {
	// Giới hạn chỉ cho phép 1 active run đồng thời
	api, _, _ := setupTestAPI(t, 1)

	// Chiếm trước token trong semaphore
	api.runSem <- struct{}{}

	handler := api.Routes()
	reqPayload := createRunRequest{
		Targets: []probe.Target{
			{ID: "t1", URL: "http://127.0.0.1:12345"},
		},
	}
	payloadBytes, _ := json.Marshal(reqPayload)

	rec := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodPost, "/runs", bytes.NewReader(payloadBytes))
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusTooManyRequests {
		t.Fatalf("expected 429 Too Many Requests under backpressure, got %d", rec.Code)
	}

	// Giải phóng token
	<-api.runSem
}

func TestAPI_MalformedInput(t *testing.T) {
	api, _, _ := setupTestAPI(t, 5)
	handler := api.Routes()

	// 1. JSON sai cú pháp
	rec1 := httptest.NewRecorder()
	req1 := httptest.NewRequest(http.MethodPost, "/runs", bytes.NewReader([]byte("{invalid-json")))
	handler.ServeHTTP(rec1, req1)
	if rec1.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 for bad JSON, got %d", rec1.Code)
	}

	// 2. Targets rỗng
	rec2 := httptest.NewRecorder()
	req2 := httptest.NewRequest(http.MethodPost, "/runs", bytes.NewReader([]byte(`{"targets":[]}`)))
	handler.ServeHTTP(rec2, req2)
	if rec2.Code != http.StatusBadRequest {
		t.Fatalf("expected 400 for empty targets, got %d", rec2.Code)
	}
}
