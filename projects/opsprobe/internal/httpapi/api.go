package httpapi

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"time"

	"example.com/golang-master/projects/opsprobe/internal/probe"
	"example.com/golang-master/projects/opsprobe/internal/store"
	"example.com/golang-master/projects/opsprobe/internal/telemetry"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/otel/attribute"
)

// Config chứa các dependency cần thiết để cấu hình HTTP API.
type Config struct {
	Store         store.Store
	ProbePool     *probe.Pool
	Telemetry     *telemetry.Telemetry
	MaxActiveRuns int
}

// API điều phối các HTTP endpoint của opsprobe.
type API struct {
	store         store.Store
	pool          *probe.Pool
	tel           *telemetry.Telemetry
	maxActiveRuns int
	runSem        chan struct{}
}

// NewAPI khởi tạo instance API với các guardrail vận hành (concurrency limit, metrics).
func NewAPI(cfg Config) *API {
	maxRuns := cfg.MaxActiveRuns
	if maxRuns <= 0 {
		maxRuns = 10
	}

	return &API{
		store:         cfg.Store,
		pool:          cfg.ProbePool,
		tel:           cfg.Telemetry,
		maxActiveRuns: maxRuns,
		runSem:        make(chan struct{}, maxRuns),
	}
}

// Routes thiết lập và trả về http.Handler với đầy đủ routing và middleware.
func (a *API) Routes() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("POST /runs", a.handleCreateRun)
	mux.HandleFunc("GET /runs/{id}", a.handleGetRun)
	mux.HandleFunc("GET /readyz", a.handleReadyz)
	mux.HandleFunc("GET /livez", a.handleLivez)
	mux.Handle("GET /metrics", promhttp.HandlerFor(a.tel.Registry, promhttp.HandlerOpts{}))

	return a.recoveryMiddleware(a.loggingMiddleware(mux))
}

type createRunRequest struct {
	Targets []probe.Target `json:"targets"`
}

type runDetailResponse struct {
	Run     *store.RunRecord `json:"run"`
	Results []probe.Result   `json:"results"`
}

// handleCreateRun nhận danh sách target, thực thi qua pool, cập nhật metric và lưu DB.
func (a *API) handleCreateRun(w http.ResponseWriter, r *http.Request) {
	// 1. Áp dụng backpressure: kiểm tra giới hạn đợt chạy đồng thời
	select {
	case a.runSem <- struct{}{}:
		defer func() { <-a.runSem }()
	default:
		a.tel.RunsTotal.WithLabelValues("rejected_backpressure").Inc()
		a.writeJSON(w, http.StatusTooManyRequests, map[string]string{
			"error": "too many concurrent runs, backpressure applied",
		})
		return
	}

	// 2. Decode và validate JSON payload với MaxBytesReader và kiểm tra EOF chặt chẽ
	const maxBodyBytes = 65536 // 64 KiB
	r.Body = http.MaxBytesReader(w, r.Body, maxBodyBytes)

	var req createRunRequest
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	if err := dec.Decode(&req); err != nil {
		var maxBytesErr *http.MaxBytesError
		if errors.As(err, &maxBytesErr) {
			a.writeJSON(w, http.StatusRequestEntityTooLarge, map[string]string{
				"error": fmt.Sprintf("request body exceeds limit of %d bytes", maxBodyBytes),
			})
			return
		}
		a.writeJSON(w, http.StatusBadRequest, map[string]string{
			"error": fmt.Sprintf("invalid json payload: %v", err),
		})
		return
	}

	// Yêu cầu EOF: từ chối nếu có trailing data hoặc document thứ hai (concatenated JSON)
	var trailing json.RawMessage
	if err := dec.Decode(&trailing); err != io.EOF {
		a.writeJSON(w, http.StatusBadRequest, map[string]string{
			"error": "request body must contain only a single JSON document",
		})
		return
	}

	// 3. Upfront Input Contract Validation: Kiểm tra toàn bộ targets trước khi chạy
	if len(req.Targets) == 0 {
		a.writeJSON(w, http.StatusBadRequest, map[string]string{
			"error": "targets list must not be empty",
		})
		return
	}

	if len(req.Targets) > 100 {
		a.writeJSON(w, http.StatusBadRequest, map[string]string{
			"error": "too many targets: maximum is 100 per run",
		})
		return
	}

	seenIDs := make(map[string]struct{}, len(req.Targets))
	for i, target := range req.Targets {
		if err := probe.ValidateTarget(target); err != nil {
			a.writeJSON(w, http.StatusBadRequest, map[string]string{
				"error": fmt.Sprintf("invalid target at index %d (%s): %v", i, target.ID, err),
			})
			return
		}
		if _, exists := seenIDs[target.ID]; exists {
			a.writeJSON(w, http.StatusBadRequest, map[string]string{
				"error": fmt.Sprintf("duplicate target id: %q", target.ID),
			})
			return
		}
		seenIDs[target.ID] = struct{}{}
	}

	// 4. Khởi tạo Run ID ngẫu nhiên không xung đột
	runID := generateRunID()

	// Khởi tạo span trace cho đợt chạy
	ctx, span := a.tel.StartSpan(r.Context(), "opsprobe.run",
		attribute.String("run.id", runID),
		attribute.Int("target.count", len(req.Targets)),
	)
	defer span.End()

	// Ghi nhận mốc thời gian bắt đầu thực thi
	startedAt := time.Now().UTC()

	// 5. Thực thi probe qua pool có giới hạn
	results := a.pool.Execute(ctx, req.Targets)

	// Ghi nhận mốc thời gian kết thúc
	completedAt := time.Now().UTC()

	// 6. Thống kê kết quả
	successCount := 0
	failureCount := 0
	for _, res := range results {
		if res.Outcome == probe.OutcomeSuccess {
			successCount++
		} else {
			failureCount++
		}
		// Ghi nhận telemetry từng probe với thời gian chính xác
		a.tel.RecordProbe(res.TargetID, res.URL, string(res.Outcome), float64(res.DurationNs)/1e9, res.Error)
	}

	status := "completed"
	if failureCount > 0 && successCount == 0 {
		status = "failed"
	}
	if ctx.Err() != nil {
		status = "canceled"
	}

	run := store.RunRecord{
		ID:           runID,
		StartedAt:    startedAt,
		CompletedAt:  completedAt,
		TargetCount:  len(req.Targets),
		SuccessCount: successCount,
		FailureCount: failureCount,
		Status:       status,
	}

	// 6. Ghi nhận atomic transaction vào store
	if err := a.store.RecordRun(ctx, run, results); err != nil {
		a.tel.RunsTotal.WithLabelValues("db_error").Inc()
		a.tel.Logger.Error("failed to record run in store",
			slog.String("run_id", runID),
			slog.String("error", err.Error()),
		)
		a.writeJSON(w, http.StatusInternalServerError, map[string]string{
			"error": "failed to persist run results",
		})
		return
	}

	a.tel.RunsTotal.WithLabelValues(status).Inc()

	resp := runDetailResponse{
		Run:     &run,
		Results: results,
	}
	a.writeJSON(w, http.StatusCreated, resp)
}

// handleGetRun truy vấn chi tiết một đợt chạy theo ID.
func (a *API) handleGetRun(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if id == "" {
		a.writeJSON(w, http.StatusBadRequest, map[string]string{"error": "missing run id"})
		return
	}

	run, results, err := a.store.GetRun(r.Context(), id)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			a.writeJSON(w, http.StatusNotFound, map[string]string{"error": "run not found"})
			return
		}
		a.writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "failed to query run"})
		return
	}

	a.writeJSON(w, http.StatusOK, runDetailResponse{
		Run:     run,
		Results: results,
	})
}

// handleReadyz kiểm tra sức khỏe của database kết nối.
func (a *API) handleReadyz(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()

	if err := a.store.Ping(ctx); err != nil {
		a.tel.Logger.Warn("readiness check failed", slog.String("error", err.Error()))
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusServiceUnavailable)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"status": "unhealthy",
			"error":  "storage unavailable",
		})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

// handleLivez kiểm tra tiến trình service còn sống.
func (a *API) handleLivez(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "alive"})
}

func (a *API) writeJSON(w http.ResponseWriter, code int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(data)
}

func (a *API) loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
		next.ServeHTTP(rw, r)
		duration := time.Since(start)

		// Bỏ qua ghi log các endpoint liveness/readiness/metrics thường xuyên để tránh log flood
		if r.URL.Path != "/livez" && r.URL.Path != "/readyz" && r.URL.Path != "/metrics" {
			a.tel.Logger.Info("http request",
				slog.String("method", r.Method),
				slog.String("path", r.URL.Path),
				slog.Int("status", rw.statusCode),
				slog.Duration("duration", duration),
			)
		}
	})
}

func (a *API) recoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				a.tel.Logger.Error("panic recovered in http handler",
					slog.Any("recover", rec),
					slog.String("path", r.URL.Path),
				)
				a.writeJSON(w, http.StatusInternalServerError, map[string]string{
					"error": "internal server error",
				})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func generateRunID() string {
	b := make([]byte, 8)
	_, _ = rand.Read(b)
	return fmt.Sprintf("run-%x", hex.EncodeToString(b))
}
