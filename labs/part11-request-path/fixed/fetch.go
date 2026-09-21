package fixed

import (
	"context"
	"fmt"
	"io"
	"net/http"
)

type Reply struct {
	StatusCode int
	Body       []byte
}

type StatusError struct {
	Code int
}

func (e *StatusError) Error() string {
	return fmt.Sprintf("unexpected HTTP status: %d", e.Code)
}

func Fetch(ctx context.Context, client *http.Client, rawURL string) (Reply, error) {
	if client == nil {
		return Reply{}, fmt.Errorf("HTTP client is required")
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, rawURL, nil)
	if err != nil {
		return Reply{}, fmt.Errorf("create request: %w", err)
	}
	resp, err := client.Do(req)
	if err != nil {
		return Reply{}, fmt.Errorf("do request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return Reply{}, fmt.Errorf("read response body: %w", err)
	}
	if resp.StatusCode < http.StatusOK || resp.StatusCode >= http.StatusMultipleChoices {
		return Reply{}, &StatusError{Code: resp.StatusCode}
	}
	return Reply{StatusCode: resp.StatusCode, Body: body}, nil
}
