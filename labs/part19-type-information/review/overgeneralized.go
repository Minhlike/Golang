package review

import "errors"

// Load is deliberately under-specified for the review exercise. A type
// parameter alone cannot say which format is read or how bytes become T.
func Load[T any](source string) (T, error) {
	var zero T
	return zero, errors.New("load format is unspecified")
}
