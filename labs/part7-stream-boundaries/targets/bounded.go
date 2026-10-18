package targets

import (
	"errors"
	"fmt"
	"io"
	"math"
)

// ErrDocumentTooLarge identifies input that exceeds the caller's byte limit.
var ErrDocumentTooLarge = errors.New("target document exceeds byte limit")

// ReadBounded reads at most max bytes and detects input that exceeds that limit.
func ReadBounded(r io.Reader, max int64) ([]byte, error) {
	if max < 0 {
		return nil, fmt.Errorf("negative byte limit: %d", max)
	}
	if max == math.MaxInt64 {
		return nil, fmt.Errorf("byte limit cannot reserve an overflow probe: %d", max)
	}

	data, err := io.ReadAll(io.LimitReader(r, max+1))
	if err != nil {
		return nil, fmt.Errorf("read target document: %w", err)
	}
	if int64(len(data)) > max {
		return nil, fmt.Errorf("%w: max=%d", ErrDocumentTooLarge, max)
	}
	return data, nil
}
