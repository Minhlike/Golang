package automation

import (
	"fmt"
	"net/http"
	"strconv"
	"time"
)

// JitterSource supplies one value in [0, 1). Keeping it explicit makes a
// retry contract reproducible in tests instead of relying on process-global
// randomness.
type JitterSource func() float64

// CalculateBackoffWithJitter returns base plus 10%--25% positive jitter.
// Callers own the random source and may replace it with a deterministic value
// in tests.
func CalculateBackoffWithJitter(base time.Duration, next JitterSource) (time.Duration, error) {
	if base < 0 {
		return 0, fmt.Errorf("base backoff must not be negative")
	}
	if next == nil {
		return 0, fmt.Errorf("jitter source is required")
	}
	value := next()
	if value < 0 || value >= 1 {
		return 0, fmt.Errorf("jitter value must be in [0, 1)")
	}
	factor := 0.10 + value*0.15
	return base + time.Duration(float64(base)*factor), nil
}

// RateLimitStatus summarizes the GitHub API quota and required backoff.
type RateLimitStatus struct {
	Limit       int
	Remaining   int
	ResetAt     time.Time
	RetryAfter  time.Duration
	IsExhausted bool
}

// ParseRateLimit extracts rate limit details from GitHub API HTTP response headers.
func ParseRateLimit(header http.Header, now time.Time) RateLimitStatus {
	status := RateLimitStatus{}

	if limitStr := header.Get("X-RateLimit-Limit"); limitStr != "" {
		if limit, err := strconv.Atoi(limitStr); err == nil {
			status.Limit = limit
		}
	}

	if remStr := header.Get("X-RateLimit-Remaining"); remStr != "" {
		if rem, err := strconv.Atoi(remStr); err == nil {
			status.Remaining = rem
			if rem == 0 {
				status.IsExhausted = true
			}
		}
	}

	if resetStr := header.Get("X-RateLimit-Reset"); resetStr != "" {
		if resetEpoch, err := strconv.ParseInt(resetStr, 10, 64); err == nil {
			status.ResetAt = time.Unix(resetEpoch, 0)
			if status.IsExhausted && status.ResetAt.After(now) {
				status.RetryAfter = status.ResetAt.Sub(now)
			}
		}
	}

	// Secondary rate limit (Abuse detection) uses standard Retry-After header
	if retryAfterStr := header.Get("Retry-After"); retryAfterStr != "" {
		if seconds, err := strconv.Atoi(retryAfterStr); err == nil {
			status.RetryAfter = time.Duration(seconds) * time.Second
			status.IsExhausted = true
		}
	}

	return status
}
