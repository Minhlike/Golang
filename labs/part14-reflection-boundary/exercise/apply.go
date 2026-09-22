package exercise

import "errors"

var (
	ErrDestination = errors.New("destination must be a non-nil pointer to struct")
	ErrSchema      = errors.New("invalid env schema")
)

func ApplyEnv(dst any, values map[string]string) error {
	return errors.New("ApplyEnv has not been implemented")
}
