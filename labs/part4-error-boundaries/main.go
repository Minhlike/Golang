package main

import (
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

type ProbeFunc func(Endpoint) error

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

func applyProbe(registry map[string]Service, name string, run ProbeFunc) error {
	service, found := registry[name]
	if !found {
		return fmt.Errorf("unknown %q: %w", name, ErrUnknownService)
	}

	if err := run(service.Endpoint); err != nil {
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

	err := applyProbe(registry, "billing", func(Endpoint) error {
		return errors.New("connection refused")
	})

	var failure *ProbeFailure
	if errors.As(err, &failure) {
		fmt.Printf("%s %s:%d retries=%d\n", failure.Service, failure.Endpoint.Host, failure.Endpoint.Port, registry["billing"].Retries)
	}
}
