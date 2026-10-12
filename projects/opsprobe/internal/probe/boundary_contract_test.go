package probe

import (
	"errors"
	"io"
	"math"
	"strings"
	"testing"
)

type observedBody struct {
	io.Reader
	closed bool
}

func (b *observedBody) Close() error { b.closed = true; return nil }

type failingBodyReader struct{ err error }

func (r failingBodyReader) Read([]byte) (int, error) { return 0, r.err }

func TestDrainBoundaryContracts(t *testing.T) {
	if ok, err := drainResponseBody(nil, MaxDrainBytes); ok || err != nil {
		t.Fatalf("nil body = %v, %v", ok, err)
	}
	readErr := errors.New("body read failed")
	for _, tc := range []struct {
		name    string
		reader  io.Reader
		limit   int64
		want    bool
		wantErr error
	}{
		{"empty", strings.NewReader(""), 1, true, nil},
		{"exact", strings.NewReader("ab"), 2, true, nil},
		{"over", strings.NewReader("abc"), 2, false, nil},
		{"disabled", strings.NewReader("ab"), 0, false, nil},
		{"error", failingBodyReader{readErr}, 2, false, readErr},
	} {
		t.Run(tc.name, func(t *testing.T) {
			body := &observedBody{Reader: tc.reader}
			ok, err := drainResponseBody(body, tc.limit)
			if ok != tc.want || !errors.Is(err, tc.wantErr) || !body.closed {
				t.Fatalf("drain = %v, %v, closed=%v", ok, err, body.closed)
			}
		})
	}
	body := &observedBody{Reader: strings.NewReader("small")}
	if ok, err := drainResponseBody(body, math.MaxInt64); ok || err == nil || !body.closed {
		t.Fatalf("sentinel overflow must fail closed: %v, %v, closed=%v", ok, err, body.closed)
	}
}
