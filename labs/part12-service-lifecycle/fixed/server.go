package fixed

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"time"
)

const maxRequestBody = 4 << 10

type Check struct {
	Target string `json:"target"`
}

type Store interface {
	Create(context.Context, Check) (Check, error)
}

type app struct {
	store Store
}

func NewHandler(store Store) http.Handler {
	a := app{store: store}
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/checks", a.createCheck)
	return mux
}

func (a app) createCheck(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		methodNotAllowed(w)
		return
	}
	if a.store == nil {
		internalError(w)
		return
	}

	r.Body = http.MaxBytesReader(w, r.Body, maxRequestBody)
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	var input Check
	if err := decoder.Decode(&input); err != nil || validateTarget(input.Target) != nil {
		badRequest(w)
		return
	}
	var extra struct{}
	if err := decoder.Decode(&extra); !errors.Is(err, io.EOF) {
		badRequest(w)
		return
	}

	check, err := a.store.Create(r.Context(), input)
	if err != nil {
		internalError(w)
		return
	}
	writeJSON(w, http.StatusCreated, check)
}

func validateTarget(raw string) error {
	u, err := url.ParseRequestURI(raw)
	if err != nil || u.Host == "" {
		return fmt.Errorf("target must be an absolute URL")
	}
	if u.Scheme != "http" && u.Scheme != "https" {
		return fmt.Errorf("target scheme is not allowed")
	}
	return nil
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}

func methodNotAllowed(w http.ResponseWriter) {
	writeError(w, http.StatusMethodNotAllowed, "method not allowed")
}

func badRequest(w http.ResponseWriter) {
	writeError(w, http.StatusBadRequest, "invalid check")
}

func internalError(w http.ResponseWriter) {
	writeError(w, http.StatusInternalServerError, "internal error")
}

func ServeUntilStopped(ctx context.Context, srv *http.Server, ln net.Listener, grace time.Duration) error {
	if srv == nil {
		return fmt.Errorf("HTTP server is required")
	}
	if grace <= 0 {
		return fmt.Errorf("shutdown grace must be positive")
	}
	serveErr := make(chan error, 1)
	go func() { serveErr <- srv.Serve(ln) }()

	select {
	case err := <-serveErr:
		if errors.Is(err, http.ErrServerClosed) {
			return nil
		}
		return fmt.Errorf("serve: %w", err)
	case <-ctx.Done():
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), grace)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		return fmt.Errorf("shutdown: %w", err)
	}
	if err := <-serveErr; !errors.Is(err, http.ErrServerClosed) {
		return fmt.Errorf("serve after shutdown: %w", err)
	}
	return nil
}
