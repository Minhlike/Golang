package probe

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"sync"
	"time"
)

// Outcome đại diện cho kết quả phân loại vận hành của một lần probe.
type Outcome string

const (
	OutcomeSuccess Outcome = "success"
	OutcomeFailure Outcome = "failure"
	OutcomeTimeout Outcome = "timeout"
	OutcomeCancel  Outcome = "cancel"
)

// Target khai báo một endpoint cần kiểm tra.
type Target struct {
	ID             string        `json:"id"`
	URL            string        `json:"url"`
	Method         string        `json:"method,omitempty"`
	ExpectedStatus int           `json:"expected_status,omitempty"`
	Timeout        time.Duration `json:"timeout,omitempty"`
}

// Result lưu trữ kết quả và telemetry của một lần probe hoàn tất.
type Result struct {
	TargetID   string        `json:"target_id"`
	URL        string        `json:"url"`
	StatusCode int           `json:"status_code"`
	Duration   time.Duration `json:"duration_ms"`
	Outcome    Outcome       `json:"outcome"`
	Error      string        `json:"error,omitempty"`
	Timestamp  time.Time     `json:"timestamp"`
}

// Pool thực thi các lượt probe với số lượng worker bị chặn (bounded concurrency).
type Pool struct {
	client         *http.Client
	concurrency    int
	defaultTimeout time.Duration
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
		},
		concurrency:    4,
		defaultTimeout: 3 * time.Second,
	}

	for _, opt := range opts {
		opt(p)
	}

	return p
}

// ValidateTarget kiểm tra cấu trúc của Target trước khi thực thi.
func ValidateTarget(t Target) error {
	if t.ID == "" {
		return errors.New("target id must not be empty")
	}
	if t.URL == "" {
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
	return nil
}

// ProbeSingle thực hiện kiểm tra một target đơn lẻ với deadline và phân loại lỗi rõ ràng.
func (p *Pool) ProbeSingle(ctx context.Context, target Target) Result {
	start := time.Now()
	res := Result{
		TargetID:  target.ID,
		URL:       target.URL,
		Timestamp: start,
	}

	// 1. Kiểm tra cấu trúc URL trước khi gửi request
	if err := ValidateTarget(target); err != nil {
		res.Outcome = OutcomeFailure
		res.Error = err.Error()
		res.Duration = time.Since(start)
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
		method = target.Method
	}

	req, err := http.NewRequestWithContext(probeCtx, method, target.URL, nil)
	if err != nil {
		res.Outcome = OutcomeFailure
		res.Error = fmt.Sprintf("create request failed: %v", err)
		res.Duration = time.Since(start)
		return res
	}

	// 3. Thực thi HTTP request
	resp, err := p.client.Do(req)
	duration := time.Since(start)
	res.Duration = duration

	if err != nil {
		// Phân loại nguyên nhân failure theo contract context & network
		if errors.Is(probeCtx.Err(), context.DeadlineExceeded) {
			res.Outcome = OutcomeTimeout
			res.Error = "probe deadline exceeded"
			return res
		}
		if errors.Is(ctx.Err(), context.Canceled) || errors.Is(probeCtx.Err(), context.Canceled) {
			res.Outcome = OutcomeCancel
			res.Error = "probe context canceled"
			return res
		}

		var netErr net.Error
		if errors.As(err, &netErr) && netErr.Timeout() {
			res.Outcome = OutcomeTimeout
			res.Error = fmt.Sprintf("network timeout: %v", err)
			return res
		}

		res.Outcome = OutcomeFailure
		res.Error = err.Error()
		return res
	}

	// 4. Giải phóng và đọc cạn body để connection pool của Transport được tái sử dụng
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, 8192))

	res.StatusCode = resp.StatusCode

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
						URL:       j.target.URL,
						Outcome:   OutcomeCancel,
						Error:     ctx.Err().Error(),
						Timestamp: time.Now(),
					}
					continue
				}

				results[j.index] = p.ProbeSingle(ctx, j.target)
			}
		}()
	}

	wg.Wait()
	return results
}
