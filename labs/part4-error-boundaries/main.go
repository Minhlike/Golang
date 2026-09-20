package main

import (
	"context"
	"errors"
	"fmt"
)

type Endpoint struct {
	Host string
	Port int
}

type Service struct {
	Name     string
	Endpoint Endpoint
	Healthy  bool
	Retries  int
}

func (service *Service) Record(healthy bool) {
	service.Healthy = healthy
	if !healthy {
		service.Retries++
	}
}

type ProbeFunc func(context.Context, Endpoint) error

type ProbeSession interface {
	Close() error
}

type OpenSession func(Endpoint) (ProbeSession, error)
type SessionProbe func(context.Context, Endpoint, ProbeSession) error

var ErrUnknownService = errors.New("service is not configured")

type ProbeFailure struct {
	Service  string
	Endpoint Endpoint
	Cause    error
}

func (failure *ProbeFailure) Error() string {
	return fmt.Sprintf(
		"probe %s at %s:%d: %v",
		failure.Service,
		failure.Endpoint.Host,
		failure.Endpoint.Port,
		failure.Cause,
	)
}

func (failure *ProbeFailure) Unwrap() error {
	return failure.Cause
}

func runWithSession(
	ctx context.Context,
	endpoint Endpoint,
	open OpenSession,
	run SessionProbe,
) (err error) {
	if err := ctx.Err(); err != nil {
		return err
	}

	session, err := open(endpoint)
	if err != nil {
		return fmt.Errorf("open session: %w", err)
	}
	defer func() {
		if closeErr := session.Close(); closeErr != nil {
			if err == nil {
				err = fmt.Errorf("close session: %w", closeErr)
			}
		}
	}()

	return run(ctx, endpoint, session)
}

func applyProbe(ctx context.Context, registry map[string]Service, name string, run ProbeFunc) error {
	service, found := registry[name]
	if !found {
		return fmt.Errorf("unknown %q: %w", name, ErrUnknownService)
	}
	if err := ctx.Err(); err != nil {
		return fmt.Errorf("probe canceled: %w", err)
	}

	if err := run(ctx, service.Endpoint); err != nil {
		if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
			return fmt.Errorf("probe incomplete: %w", err)
		}
		service.Record(false)
		registry[name] = service
		failed := &ProbeFailure{
			Service:  service.Name,
			Endpoint: service.Endpoint,
			Cause:    err,
		}
		return fmt.Errorf("probe %q: %w", name, failed)
	}

	service.Record(true)
	registry[name] = service
	return nil
}

func main() {
	registry := map[string]Service{
		"billing": {
			Name:     "billing",
			Endpoint: Endpoint{Host: "billing.internal", Port: 8443},
			Healthy:  true,
		},
	}

	err := applyProbe(context.Background(), registry, "billing", func(context.Context, Endpoint) error {
		return errors.New("connection refused")
	})

	var failure *ProbeFailure
	if errors.As(err, &failure) {
		fmt.Printf("%s %s:%d retries=%d\n", failure.Service, failure.Endpoint.Host, failure.Endpoint.Port, registry["billing"].Retries)
	}
}
