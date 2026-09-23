package incident

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptrace"
	"sync/atomic"
)

// BuggyProbe thực hiện HTTP request nhưng BỎ QUÊN việc đóng response body.
// Lỗi này vi phạm hợp đồng cơ bản của net/http: nếu không gọi resp.Body.Close(),
// Go Transport không thể thu hồi TCP connection về pool, buộc mỗi request tiếp theo
// phải mở một kết nối TCP mới, dẫn đến cạn kiệt socket file descriptors.
func BuggyProbe(ctx context.Context, client *http.Client, url string) (int, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return 0, err
	}

	resp, err := client.Do(req)
	if err != nil {
		return 0, err
	}
	// BUG: Quên gọi resp.Body.Close()!
	// Socket bị chiếm giữ vĩnh viễn và không bao giờ được hoàn trả về Transport pool.

	return resp.StatusCode, nil
}

// FixedProbe thực hiện đúng contract của net/http:
// đọc cạn body với LimitReader rồi mới close, đảm bảo TCP socket được trả lại pool.
func FixedProbe(ctx context.Context, client *http.Client, url string) (int, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return 0, err
	}

	resp, err := client.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()

	// Đọc cạn tối đa 16KB dữ liệu thừa để tái sử dụng kết nối an toàn
	_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, 16384))

	return resp.StatusCode, nil
}

// TraceConnectionReused tạo ClientTrace đếm số lần kết nối mới được tạo vs số lần tái sử dụng.
func TraceConnectionReused(newConns *int32, reusedConns *int32) *httptrace.ClientTrace {
	return &httptrace.ClientTrace{
		GetConn: func(hostPort string) {},
		GotConn: func(info httptrace.GotConnInfo) {
			if info.Reused {
				atomic.AddInt32(reusedConns, 1)
			} else {
				atomic.AddInt32(newConns, 1)
			}
		},
	}
}

// RunTraceBenchmark chạy N lượt probe và ghi nhận số TCP connection mới phát sinh.
func RunTraceBenchmark(ctx context.Context, client *http.Client, url string, probeFunc func(context.Context, *http.Client, string) (int, error), iterations int) (newConns int32, reusedConns int32, err error) {
	for i := 0; i < iterations; i++ {
		trace := TraceConnectionReused(&newConns, &reusedConns)
		traceCtx := httptrace.WithClientTrace(ctx, trace)

		status, probeErr := probeFunc(traceCtx, client, url)
		if probeErr != nil {
			return newConns, reusedConns, fmt.Errorf("iteration %d failed: %w", i, probeErr)
		}
		if status != http.StatusOK {
			return newConns, reusedConns, fmt.Errorf("unexpected status %d", status)
		}
	}
	return newConns, reusedConns, nil
}
