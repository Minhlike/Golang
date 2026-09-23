package incident

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptrace"
	"sync/atomic"
)

// MaxDrainBytes la gioi han doc toi da (16 KiB) de bao ve bo nho khoi response payload qua lon hoac vo han.
const MaxDrainBytes = 16384

// BuggyProbe thuc hien HTTP request nhung BO QUEN viec dong response body.
// Loi nay vi pham hop dong tai nguyen cua net/http: neu khong goi resp.Body.Close(),
// Go Transport khong the thu hoi TCP connection ve pool, buoc moi request tiep theo
// phai mo mot ket noi TCP moi, gay lang phi file descriptor va ephemeral port.
func BuggyProbe(ctx context.Context, client *http.Client, url string) (int, bool, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return 0, false, err
	}

	resp, err := client.Do(req)
	if err != nil {
		return 0, false, err
	}
	// BUG: Quen goi resp.Body.Close()!
	// Socket bi chiem giu va khong bao gio duoc hoan tra ve Transport pool.

	return resp.StatusCode, false, nil
}

// FixedProbe thuc hien dung contract cua net/http voi chinh sach bounded drain:
// 1. Luon Close body qua defer.
// 2. Doc toi da MaxDrainBytes + 1 de xac nhan da doc den EOF hay chua.
// 3. Chi coi la ReusedEligible khi doc den tan cung (EOF) trong pham vi gioi han.
func FixedProbe(ctx context.Context, client *http.Client, url string) (int, bool, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return 0, false, err
	}

	resp, err := client.Do(req)
	if err != nil {
		return 0, false, err
	}
	defer resp.Body.Close()

	lr := &io.LimitedReader{R: resp.Body, N: MaxDrainBytes + 1}
	_, copyErr := io.Copy(io.Discard, lr)
	reusedEligible := copyErr == nil && lr.N > 0

	return resp.StatusCode, reusedEligible, nil
}

// TraceConnectionReused tao ClientTrace dem so lan ket noi moi duoc tao vs so lan tai su dung.
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

// RunTraceBenchmark chay N luot probe va ghi nhan so TCP connection moi phat sinh qua httptrace.
func RunTraceBenchmark(ctx context.Context, client *http.Client, url string, probeFunc func(context.Context, *http.Client, string) (int, bool, error), iterations int) (newConns int32, reusedConns int32, err error) {
	for i := 0; i < iterations; i++ {
		trace := TraceConnectionReused(&newConns, &reusedConns)
		traceCtx := httptrace.WithClientTrace(ctx, trace)

		status, _, probeErr := probeFunc(traceCtx, client, url)
		if probeErr != nil {
			return newConns, reusedConns, fmt.Errorf("iteration %d failed: %w", i, probeErr)
		}
		if status != http.StatusOK {
			return newConns, reusedConns, fmt.Errorf("unexpected status %d", status)
		}
	}
	return newConns, reusedConns, nil
}
