package probe

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/trace"
)

// Outcome đại diện cho kết quả phân loại vận hành của một lần probe.
type Outcome string

const (
	OutcomeSuccess Outcome = "success"
	OutcomeFailure Outcome = "failure"
	OutcomeTimeout Outcome = "timeout"
	OutcomeCancel  Outcome = "cancel"
)

// Target khai báo một endpoint cần kiểm tra với các ràng buộc bảo mật.
type Target struct {
	ID             string        `json:"id"`
	URL            string        `json:"url"`
	Method         string        `json:"method,omitempty"`
	ExpectedStatus int           `json:"expected_status,omitempty"`
	Timeout        time.Duration `json:"timeout,omitempty"`
}

// Result lưu trữ kết quả và telemetry của một lần probe hoàn tất.
type Result struct {
	TargetID       string    `json:"target_id"`
	URL            string    `json:"url"`
	StatusCode     int       `json:"status_code"`
	DurationNs     int64     `json:"duration_ns"`
	DurationMs     float64   `json:"duration_ms"`
	Outcome        Outcome   `json:"outcome"`
	ReusedEligible bool      `json:"reused_eligible"`
	Error          string    `json:"error,omitempty"`
	Timestamp      time.Time `json:"timestamp"`
}

// WorkerObserver nhận thông báo khi một worker thực sự bắt đầu và kết thúc probe.
type WorkerObserver interface {
	WorkerStarted()
	WorkerStopped()
}

// SanitizeURL loại bỏ query parameters và credentials để bảo vệ thông tin nhạy cảm khỏi logs và traces.
func SanitizeURL(rawURL string) string {
	u, err := url.Parse(rawURL)
	if err != nil {
		return rawURL
	}
	u.User = nil
	u.RawQuery = ""
	u.Fragment = ""
	return u.String()
}

// Pool thực thi các lượt probe với số lượng worker bị chặn (bounded concurrency).
type Pool struct {
	client         *http.Client
	concurrency    int
	defaultTimeout time.Duration
	observer       WorkerObserver
	tracer         trace.Tracer
	propagator     propagation.TextMapPropagator
}

// PoolOption cho phép cấu hình tham số khởi tạo Pool.
type PoolOption func(*Pool)

// WithHTTPClient truyền HTTP client tùy chỉnh (thường dùng cho test hoặc proxy).
func WithHTTPClient(client *http.Client) PoolOption {
	return func(p *Pool) {
		if client != nil {
			p.client = client
		}
	}
}

// WithConcurrency cấu hình số lượng worker song song tối đa.
func WithConcurrency(n int) PoolOption {
	return func(p *Pool) {
		if n > 0 {
			p.concurrency = n
		}
	}
}

// WithDefaultTimeout cấu hình timeout mặc định cho mỗi target nếu không được khai báo.
func WithDefaultTimeout(d time.Duration) PoolOption {
	return func(p *Pool) {
		if d > 0 {
			p.defaultTimeout = d
		}
	}
}

// WithWorkerObserver đăng ký hook theo dõi số worker thực sự đang chạy.
func WithWorkerObserver(obs WorkerObserver) PoolOption {
	return func(p *Pool) {
		p.observer = obs
	}
}

// WithTracer gắn OpenTelemetry tracer để tạo child span cho từng probe.
func WithTracer(tr trace.Tracer) PoolOption {
	return func(p *Pool) {
		p.tracer = tr
	}
}

// WithPropagator cấu hình TextMapPropagator cho việc inject distributed trace context vào outbound HTTP headers.
func WithPropagator(prop propagation.TextMapPropagator) PoolOption {
	return func(p *Pool) {
		if prop != nil {
			p.propagator = prop
		}
	}
}

// NewPool khởi tạo một Pool với HTTP client tái sử dụng connection pool.
func NewPool(opts ...PoolOption) *Pool {
	transport := &http.Transport{
		Proxy: http.ProxyFromEnvironment,
		DialContext: (&net.Dialer{
			Timeout:   5 * time.Second,
			KeepAlive: 30 * time.Second,
		}).DialContext,
		ForceAttemptHTTP2:     true,
		MaxIdleConns:          100,
		MaxIdleConnsPerHost:   10,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   5 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
	}

	p := &Pool{
		client: &http.Client{
			Transport: transport,
			// Chính sách redirect tường minh: Không tự động chuyển hướng ngầm để tránh SSRF và credential leakage
			CheckRedirect: func(req *http.Request, via []*http.Request) error {
				return http.ErrUseLastResponse
			},
		},
		concurrency:    4,
		defaultTimeout: 3 * time.Second,
		propagator:     propagation.TraceContext{},
	}

	for _, opt := range opts {
		opt(p)
	}

	return p
}

// ValidateTarget kiểm tra chặt chẽ cấu trúc và chính sách bảo mật của Target.
func ValidateTarget(t Target) error {
	if strings.TrimSpace(t.ID) == "" {
		return errors.New("target id must not be empty")
	}
	if strings.TrimSpace(t.URL) == "" {
		return errors.New("target url must not be empty")
	}
	parsed, err := url.ParseRequestURI(t.URL)
	if err != nil {
		return fmt.Errorf("invalid target url: %w", err)
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return fmt.Errorf("unsupported url scheme %q: only http/https allowed", parsed.Scheme)
	}
	if parsed.Host == "" {
		return errors.New("target url host must not be empty")
	}
	// Chặn credential/userinfo trong URL để phòng ngừa SSRF và rò rỉ secret
	if parsed.User != nil {
		return errors.New("target url must not contain userinfo/credentials")
	}

	// Chỉ cho phép GET hoặc HEAD cho diagnostic probe
	if t.Method != "" {
		upperMethod := strings.ToUpper(strings.TrimSpace(t.Method))
		if upperMethod != http.MethodGet && upperMethod != http.MethodHead {
			return fmt.Errorf("unsupported method %q: only GET and HEAD allowed", t.Method)
		}
	}

	// Timeout giới hạn an toàn
	if t.Timeout < 0 || t.Timeout > 60*time.Second {
		return fmt.Errorf("timeout %s out of range: must be between 0 and 60s", t.Timeout)
	}

	// ExpectedStatus nếu được gán phải nằm trong dải mã HTTP chuẩn
	if t.ExpectedStatus != 0 && (t.ExpectedStatus < 100 || t.ExpectedStatus > 599) {
		return fmt.Errorf("invalid expected status %d: must be 100..599", t.ExpectedStatus)
	}

	return nil
}

// MaxDrainBytes là giới hạn tối đa số byte body được đọc để thử tái sử dụng TCP connection.
const MaxDrainBytes = 16384 // 16 KiB

// drainResponseBody đóng body và kiểm tra xem toàn bộ response đã được đọc cạn đến EOF chưa.
// Trả về true nếu và chỉ nếu toàn bộ dữ liệu đã được tiêu thụ mà không vượt quá maxBytes.
func drainResponseBody(body io.ReadCloser, maxBytes int64) (bool, error) {
	defer body.Close()
	if body == nil || maxBytes <= 0 {
		return false, nil
	}

	// Giới hạn đọc maxBytes + 1 byte
	lr := &io.LimitedReader{R: body, N: maxBytes + 1}
	_, err := io.Copy(io.Discard, lr)
	if err != nil {
		return false, err
	}

	// Nếu lr.N > 0, chứng tỏ body đã trả về EOF trước khi chạm trần maxBytes + 1
	drainedToEOF := lr.N > 0
	return drainedToEOF, nil
}

// ProbeSingle thực hiện kiểm tra một target đơn lẻ với deadline và phân loại lỗi rõ ràng.
func (p *Pool) ProbeSingle(ctx context.Context, target Target) Result {
	start := time.Now()
	sanitizedURL := SanitizeURL(target.URL)
	res := Result{
		TargetID:  target.ID,
		URL:       sanitizedURL,
		Timestamp: start,
	}

	// Tạo child span nếu có tracer
	var span trace.Span
	if p.tracer != nil {
		ctx, span = p.tracer.Start(ctx, "opsprobe.probe",
			trace.WithAttributes(
				attribute.String("target.id", target.ID),
				attribute.String("target.url", sanitizedURL),
			),
		)
		defer span.End()
	}

	// 1. Kiểm tra cấu trúc Target trước khi gửi request
	if err := ValidateTarget(target); err != nil {
		res.Outcome = OutcomeFailure
		res.Error = err.Error()
		duration := time.Since(start)
		res.DurationNs = duration.Nanoseconds()
		res.DurationMs = float64(duration.Microseconds()) / 1000.0
		if span != nil {
			span.SetAttributes(
				attribute.String("outcome", string(res.Outcome)),
				attribute.String("error", res.Error),
			)
		}
		return res
	}

	// 2. Thiết lập timeout riêng cho target này
	targetTimeout := p.defaultTimeout
	if target.Timeout > 0 {
		targetTimeout = target.Timeout
	}

	probeCtx, cancel := context.WithTimeout(ctx, targetTimeout)
	defer cancel()

	method := http.MethodGet
	if target.Method != "" {
		method = strings.ToUpper(strings.TrimSpace(target.Method))
	}

	req, err := http.NewRequestWithContext(probeCtx, method, target.URL, nil)
	if err != nil {
		res.Outcome = OutcomeFailure
		res.Error = fmt.Sprintf("create request failed: %v", err)
		duration := time.Since(start)
		res.DurationNs = duration.Nanoseconds()
		res.DurationMs = float64(duration.Microseconds()) / 1000.0
		if span != nil {
			span.SetAttributes(
				attribute.String("outcome", string(res.Outcome)),
				attribute.String("error", res.Error),
			)
		}
		return res
	}

	// Inject W3C Trace Context (traceparent) vào outbound HTTP header
	if p.propagator != nil {
		p.propagator.Inject(ctx, propagation.HeaderCarrier(req.Header))
	}

	// 3. Thực thi HTTP request
	resp, err := p.client.Do(req)
	if err != nil {
		duration := time.Since(start)
		res.DurationNs = duration.Nanoseconds()
		res.DurationMs = float64(duration.Microseconds()) / 1000.0

		// Phân loại nguyên nhân failure theo contract context & network
		if errors.Is(probeCtx.Err(), context.DeadlineExceeded) {
			res.Outcome = OutcomeTimeout
			res.Error = "probe deadline exceeded"
		} else if errors.Is(ctx.Err(), context.Canceled) || errors.Is(probeCtx.Err(), context.Canceled) {
			res.Outcome = OutcomeCancel
			res.Error = "probe context canceled"
		} else {
			var netErr net.Error
			if errors.As(err, &netErr) && netErr.Timeout() {
				res.Outcome = OutcomeTimeout
				res.Error = fmt.Sprintf("network timeout: %v", err)
			} else {
				res.Outcome = OutcomeFailure
				res.Error = err.Error()
			}
		}

		if span != nil {
			span.SetAttributes(
				attribute.String("outcome", string(res.Outcome)),
				attribute.String("error", res.Error),
			)
		}
		return res
	}

	// 4. Giải phóng và kiểm tra khả năng tái sử dụng kết nối có giới hạn (bounded drain).
	// Bounded drain giới hạn lượng dữ liệu và thời gian đọc từ peer nhằm chống cạn kiệt I/O.
	// ReusedEligible chỉ xác nhận body đạt tiêu chí drain đến EOF trong giới hạn cho phép,
	// không phải là bảo đảm tuyệt đối rằng http.Transport chắc chắn tái sử dụng socket.
	drainedToEOF, drainErr := drainResponseBody(resp.Body, MaxDrainBytes)
	duration := time.Since(start) // Đo toàn bộ lifecycle đến khi hoàn tất cleanup/drain
	res.DurationNs = duration.Nanoseconds()
	res.DurationMs = float64(duration.Microseconds()) / 1000.0
	res.StatusCode = resp.StatusCode
	res.ReusedEligible = drainedToEOF

	// Nếu xảy ra lỗi trong quá trình drain body (ví dụ server stall stream tới khi hết timeout):
	if drainErr != nil {
		if errors.Is(probeCtx.Err(), context.DeadlineExceeded) || errors.Is(drainErr, context.DeadlineExceeded) {
			res.Outcome = OutcomeTimeout
			res.Error = fmt.Sprintf("timeout draining response body: %v", drainErr)
		} else if errors.Is(ctx.Err(), context.Canceled) || errors.Is(probeCtx.Err(), context.Canceled) || errors.Is(drainErr, context.Canceled) {
			res.Outcome = OutcomeCancel
			res.Error = fmt.Sprintf("probe canceled during body drain: %v", drainErr)
		} else {
			res.Outcome = OutcomeFailure
			res.Error = fmt.Sprintf("error draining response body: %v", drainErr)
		}

		if span != nil {
			span.SetAttributes(
				attribute.String("outcome", string(res.Outcome)),
				attribute.Int("http.status_code", res.StatusCode),
				attribute.Bool("reused_eligible", res.ReusedEligible),
				attribute.String("error", res.Error),
			)
		}
		return res
	}

	// 5. Đánh giá trạng thái thành công/thất bại theo status code
	expected := target.ExpectedStatus
	if expected > 0 {
		if resp.StatusCode == expected {
			res.Outcome = OutcomeSuccess
		} else {
			res.Outcome = OutcomeFailure
			res.Error = fmt.Sprintf("status code mismatch: expected %d, got %d", expected, resp.StatusCode)
		}
	} else {
		// Mặc định: status < 400 là success
		if resp.StatusCode < 400 {
			res.Outcome = OutcomeSuccess
		} else {
			res.Outcome = OutcomeFailure
			res.Error = fmt.Sprintf("http status failure: code %d", resp.StatusCode)
		}
	}

	if span != nil {
		span.SetAttributes(
			attribute.String("outcome", string(res.Outcome)),
			attribute.Int("http.status_code", res.StatusCode),
			attribute.Bool("reused_eligible", res.ReusedEligible),
		)
		if res.Error != "" {
			span.SetAttributes(attribute.String("error", res.Error))
		}
	}

	return res
}

// Execute chạy danh sách targets thông qua worker pool với số concurrency bị chặn.
func (p *Pool) Execute(ctx context.Context, targets []Target) []Result {
	n := len(targets)
	if n == 0 {
		return []Result{}
	}

	results := make([]Result, n)
	type job struct {
		index  int
		target Target
	}

	jobs := make(chan job, n)
	for i, t := range targets {
		jobs <- job{index: i, target: t}
	}
	close(jobs)

	numWorkers := p.concurrency
	if numWorkers > n {
		numWorkers = n
	}

	var wg sync.WaitGroup
	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobs {
				// Nếu context cha đã bị hủy, đánh dấu các job còn lại là canceled
				if ctx.Err() != nil {
					results[j.index] = Result{
						TargetID:  j.target.ID,
						URL:       SanitizeURL(j.target.URL),
						Outcome:   OutcomeCancel,
						Error:     ctx.Err().Error(),
						Timestamp: time.Now(),
					}
					continue
				}

				if p.observer != nil {
					p.observer.WorkerStarted()
				}
				results[j.index] = p.ProbeSingle(ctx, j.target)
				if p.observer != nil {
					p.observer.WorkerStopped()
				}
			}
		}()
	}

	wg.Wait()
	return results
}
