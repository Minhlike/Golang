package exercise

import (
	"context"
	"errors"
	"time"
)

var ErrInvalidSpec = errors.New("invalid command specification")

type Spec struct {
	Name    string
	Args    []string
	Timeout time.Duration
}

type Result struct {
	Command  []string
	Stdout   string
	Stderr   string
	ExitCode int
	TimedOut bool
}

func Run(ctx context.Context, spec Spec) (Result, error) {
	return Result{}, errors.New("Run has not been implemented")
}
