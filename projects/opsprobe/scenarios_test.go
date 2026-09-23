package main

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

	"example.com/golang-master/projects/opsprobe/internal/httpapi"
	"example.com/golang-master/projects/opsprobe/internal/probe"
	"example.com/golang-master/projects/opsprobe/internal/store"
	"example.com/golang-master/projects/opsprobe/internal/telemetry"
)

// TestFailureInjections kiểm tra có hệ thống 6 kịch bản sự cố vận hành:
// 1. Target trả HTTP 5xx
// 2. Target timeout vượt quá deadline
// 3. Target URL malformed
// 4. Backpressure rejection khi quá tải
// 5. Transaction rollback bảo toàn tính nguyên tử
// 6. Mid-run shutdown (hủy ngang trong khi đang probe)
func TestFailureInjections(t *testing.T) {
	// Kịch bản 1: Target trả HTTP 500
	t.Run("Scenario1_HTTP_5xx", func(t *testing.T) {
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
		}))
		defer srv.Close()

		p := probe.NewPool()
		res := p.ProbeSingle(context.Background(), probe.Target{ID: "err-500", URL: srv.URL})
		if res.Outcome != probe.OutcomeFailure {
			t.Fatalf("expected OutcomeFailure, got %s", res.Outcome)
		}
		if res.StatusCode != 500 {
			t.Fatalf("expected status 500, got %d", res.StatusCode)
		}
	})

	// Kịch bản 2: Target timeout
	t.Run("Scenario2_Timeout_DeadlineExceeded", func(t *testing.T) {
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			time.Sleep(150 * time.Millisecond)
			w.WriteHeader(http.StatusOK)
		}))
		defer srv.Close()

		p := probe.NewPool(probe.WithDefaultTimeout(40 * time.Millisecond))
		res := p.ProbeSingle(context.Background(), probe.Target{ID: "timeout-target", URL: srv.URL})
		if res.Outcome != probe.OutcomeTimeout {
			t.Fatalf("expected OutcomeTimeout, got %s (err: %s)", res.Outcome, res.Error)
		}
	})

	// Kịch bản 3: Malformed target URL
	t.Run("Scenario3_Malformed_Target", func(t *testing.T) {
		p := probe.NewPool()
		res := p.ProbeSingle(context.Background(), probe.Target{ID: "bad-url", URL: "not-a-valid-http-url"})
		if res.Outcome != probe.OutcomeFailure {
			t.Fatalf("expected OutcomeFailure, got %s", res.Outcome)
		}
		if res.Error == "" {
			t.Fatalf("expected non-empty error message for malformed URL")
		}
	})

	// Kịch bản 4: Backpressure rejection
	t.Run("Scenario4_Backpressure_Rejection", func(t *testing.T) {
		s, _ := store.NewSQLiteStore(":memory:")
		_ = s.Init(context.Background())
		defer s.Close()

		tel, _ := telemetry.New(telemetry.Config{LogWriter: io.Discard, LogLevel: slog.LevelError})
		defer func() { _ = tel.Shutdown(context.Background()) }()

		api := httpapi.NewAPI(httpapi.Config{
			Store:         s,
			ProbePool:     probe.NewPool(),
			Telemetry:     tel,
			MaxActiveRuns: 1, // Chỉ cho 1 run
		})
		handler := api.Routes()

		// Chiếm slot duy nhất
		apiRunPayload := []byte(`{"targets":[{"id":"t1","url":"http://127.0.0.1:1"}]}`)

		// Tạo một kênh đồng bộ để giữ một run đang chạy
		holdCh := make(chan struct{})
		slowSrv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			select {
			case <-holdCh:
				w.WriteHeader(http.StatusOK)
			case <-r.Context().Done():
				return
			}
		}))
		defer func() {
			select {
			case <-holdCh:
			default:
				close(holdCh)
			}
			slowSrv.Close()
		}()

		slowPayload, _ := json.Marshal(map[string]interface{}{
			"targets": []map[string]string{{"id": "slow", "url": slowSrv.URL}},
		})

		// Run 1 bắt đầu và block ở slowSrv
		go func() {
			rec := httptest.NewRecorder()
			req := httptest.NewRequest(http.MethodPost, "/runs", bytes.NewReader(slowPayload))
			handler.ServeHTTP(rec, req)
		}()

		time.Sleep(20 * time.Millisecond) // Chờ run 1 chiếm semaphore

		// Run 2 gửi vào ngay lập tức -> phải bị từ chối với 429
		rec2 := httptest.NewRecorder()
		req2 := httptest.NewRequest(http.MethodPost, "/runs", bytes.NewReader(apiRunPayload))
		handler.ServeHTTP(rec2, req2)

		if rec2.Code != http.StatusTooManyRequests {
			t.Fatalf("expected 429 Too Many Requests, got %d (body: %s)", rec2.Code, rec2.Body.String())
		}
	})

	// Kịch bản 5: Transaction rollback bảo toàn tính nguyên tử
	t.Run("Scenario5_Transaction_Rollback", func(t *testing.T) {
		s, _ := store.NewSQLiteStore(":memory:")
		_ = s.Init(context.Background())
		defer s.Close()

		// Context bị hủy ngay lập tức
		ctx, cancel := context.WithCancel(context.Background())
		cancel()

		run := store.RunRecord{
			ID:           "run-tx-fail",
			CreatedAt:    time.Now(),
			TargetCount:  2,
			SuccessCount: 2,
			FailureCount: 0,
			Status:       "completed",
		}
		results := []probe.Result{
			{TargetID: "t1", URL: "http://example.com", Outcome: probe.OutcomeSuccess, Timestamp: time.Now()},
			{TargetID: "t2", URL: "http://example.com", Outcome: probe.OutcomeSuccess, Timestamp: time.Now()},
		}

		err := s.RecordRun(ctx, run, results)
		if err == nil {
			t.Fatalf("expected transaction error on canceled context")
		}

		// Chứng minh database hoàn toàn sạch
		_, _, getErr := s.GetRun(context.Background(), "run-tx-fail")
		if getErr != store.ErrNotFound {
			t.Fatalf("expected ErrNotFound due to rollback, got: %v", getErr)
		}
	})

	// Kịch bản 6: Mid-run cancellation
	t.Run("Scenario6_MidRun_Cancellation", func(t *testing.T) {
		blockCh := make(chan struct{})
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			select {
			case <-blockCh:
				w.WriteHeader(http.StatusOK)
			case <-r.Context().Done():
				return
			}
		}))
		defer func() {
			select {
			case <-blockCh:
			default:
				close(blockCh)
			}
			srv.Close()
		}()

		ctx, cancel := context.WithCancel(context.Background())
		p := probe.NewPool(probe.WithConcurrency(2))

		targets := []probe.Target{
			{ID: "t1", URL: srv.URL},
			{ID: "t2", URL: srv.URL},
			{ID: "t3", URL: srv.URL},
		}

		go func() {
			time.Sleep(20 * time.Millisecond)
			cancel() // Hủy ngang giữa chừng
		}()

		results := p.Execute(ctx, targets)
		hasCanceled := false
		for _, r := range results {
			if r.Outcome == probe.OutcomeCancel {
				hasCanceled = true
				break
			}
		}

		if !hasCanceled {
			t.Fatalf("expected at least one probe with OutcomeCancel upon mid-run cancellation")
		}
	})
}
