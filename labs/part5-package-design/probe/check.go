package probe

import (
	"context"
	"fmt"
)

// Endpoint identifies where a service is checked.
type Endpoint struct {
	Host string
	Port int
}

// Service names one configured service to check.
type Service struct {
	Name     string
	Endpoint Endpoint
}

// Runner performs one check against an endpoint.
type Runner func(context.Context, Endpoint) error

// Result describes a completed, successful observation.
type Result struct {
	Service string
	Healthy bool
}

// Check runs a service check unless ctx has already been canceled.
func Check(ctx context.Context, service Service, run Runner) (Result, error) {
	if err := ctx.Err(); err != nil {
		return Result{}, fmt.Errorf("check %q: %w", service.Name, err)
	}
	if err := run(ctx, service.Endpoint); err != nil {
		return Result{}, fmt.Errorf("check %q: %w", service.Name, err)
	}
	return Result{Service: service.Name, Healthy: true}, nil
}
