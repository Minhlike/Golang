package httpapi

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"time"
)

// Server bọc http.Server để quản lý vòng đời và graceful shutdown.
type Server struct {
	httpServer *http.Server
	api        *API
}

// ServerConfig chứa cấu hình khởi tạo HTTP Server.
type ServerConfig struct {
	Addr         string
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
	IdleTimeout  time.Duration
	APIConfig    Config
}

// NewServer tạo instance Server mới với timeout an toàn.
func NewServer(cfg ServerConfig) *Server {
	if cfg.Addr == "" {
		cfg.Addr = ":8080"
	}
	if cfg.ReadTimeout <= 0 {
		cfg.ReadTimeout = 10 * time.Second
	}
	if cfg.WriteTimeout <= 0 {
		cfg.WriteTimeout = 30 * time.Second
	}
	if cfg.IdleTimeout <= 0 {
		cfg.IdleTimeout = 60 * time.Second
	}

	api := NewAPI(cfg.APIConfig)

	httpServer := &http.Server{
		Addr:              cfg.Addr,
		Handler:           api.Routes(),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       cfg.ReadTimeout,
		WriteTimeout:      cfg.WriteTimeout,
		IdleTimeout:       cfg.IdleTimeout,
	}

	return &Server{
		httpServer: httpServer,
		api:        api,
	}
}

// Start bắt đầu lắng nghe request trên background.
func (s *Server) Start() error {
	if err := s.httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		return fmt.Errorf("http server failed: %w", err)
	}
	return nil
}

// Shutdown thực hiện graceful shutdown, chờ các request đang xử lý hoàn tất.
func (s *Server) Shutdown(ctx context.Context) error {
	return s.httpServer.Shutdown(ctx)
}
