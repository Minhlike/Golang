package automation

import (
	"errors"
	"math"
	"net/http"
	"strconv"
	"testing"
	"time"

	"github.com/go-git/go-billy/v5"
)

func TestJitterRejectsNonFiniteAndOverflow(t *testing.T) {
	for _, value := range []float64{math.NaN(), math.Inf(1), math.Inf(-1), -0.01, 1} {
		if _, err := CalculateBackoffWithJitter(time.Second, func() float64 { return value }); err == nil {
			t.Fatalf("accepted invalid jitter %v", value)
		}
	}
	if _, err := CalculateBackoffWithJitter(math.MaxInt64, func() float64 { return .5 }); err == nil {
		t.Fatal("backoff overflow accepted")
	}
}

func TestRateLimitNeverShortensKnownWaitOrWraps(t *testing.T) {
	now := time.Unix(1_000_000, 0)
	h := http.Header{}
	h.Set("X-RateLimit-Remaining", "0")
	h.Set("X-RateLimit-Reset", strconv.FormatInt(now.Add(time.Hour).Unix(), 10))
	h.Set("Retry-After", "1")
	if got := ParseRateLimit(h, now).RetryAfter; got != time.Hour {
		t.Fatalf("shortened reset wait to %v", got)
	}
	h = http.Header{}
	h.Set("Retry-After", "9223372036854775807")
	if got := ParseRateLimit(h, now); !got.IsExhausted || got.RetryAfter != math.MaxInt64 {
		t.Fatalf("overflow=%+v", got)
	}
	h.Set("Retry-After", "-1")
	if got := ParseRateLimit(h, now); got.IsExhausted || got.RetryAfter != 0 {
		t.Fatalf("negative=%+v", got)
	}
}

type faultyFS struct {
	billy.Filesystem
	fault string
	err   error
}
type faultyFile struct {
	billy.File
	fault string
	err   error
}

func (f faultyFS) Create(path string) (billy.File, error) {
	file, err := f.Filesystem.Create(path)
	if err != nil {
		return nil, err
	}
	return faultyFile{file, f.fault, f.err}, nil
}
func (f faultyFile) Write(p []byte) (int, error) {
	if f.fault == "write" {
		return 0, f.err
	}
	if f.fault == "short" {
		return len(p) - 1, nil
	}
	return f.File.Write(p)
}
func (f faultyFile) Close() error {
	err := f.File.Close()
	if f.fault == "close" {
		return f.err
	}
	return err
}

func TestCommitDoesNotAdvanceOnWriteOrCloseFailure(t *testing.T) {
	for _, fault := range []string{"write", "short", "close"} {
		t.Run(fault, func(t *testing.T) {
			r, err := NewInMemGitRepository()
			if err != nil {
				t.Fatal(err)
			}
			head, err := r.WriteFileAndCommit("initial.txt", []byte("ok"), "bot", "initial")
			if err != nil {
				t.Fatal(err)
			}
			r.fs = faultyFS{r.fs, fault, errors.New("injected file failure")}
			if _, err := r.WriteFileAndCommit("config.txt", []byte("bad"), "bot", "must not commit"); err == nil {
				t.Fatal("file failure was swallowed")
			}
			got, err := r.GetHeadCommitHash()
			if err != nil || got != head {
				t.Fatalf("HEAD advanced: %s %v", got, err)
			}
		})
	}
}

func TestEmptyWebhookSecretFailsClosed(t *testing.T) {
	payload := []byte(`{"action":"opened"}`)
	sig := computeHMAC(payload, nil)
	if VerifyHMACSHA256(payload, sig, nil) {
		t.Fatal("empty shared secret authenticated webhook")
	}
	r := NewWebhookReceiver("")
	called := false
	if _, err := r.Process("id", sig, payload, func() error { called = true; return nil }); !errors.Is(err, ErrInvalidSignature) || called {
		t.Fatalf("empty-secret delivery accepted: %v %v", err, called)
	}
}
