package main

import (
	"errors"
	"testing"
)

func testRegistry() map[string]Service {
	return map[string]Service{
		"billing": {
			Name:     "billing",
			Endpoint: Endpoint{Host: "billing.internal", Port: 8443},
			Healthy:  true,
		},
	}
}

func TestApplyProbeRejectsUnknownServiceWithoutRunningProbe(t *testing.T) {
	registry := testRegistry()
	ran := false

	err := applyProbe(registry, "search", func(Endpoint) error {
		ran = true
		return nil
	})

	if !errors.Is(err, ErrUnknownService) {
		t.Fatalf("errors.Is(err, ErrUnknownService) = false; err = %v", err)
	}
	if ran {
		t.Fatal("probe ran for a service that is not configured")
	}
}

func TestApplyProbePreservesFailureCauseAndContext(t *testing.T) {
	registry := testRegistry()
	errConnectionRefused := errors.New("connection refused")

	err := applyProbe(registry, "billing", func(Endpoint) error {
		return errConnectionRefused
	})

	if !errors.Is(err, errConnectionRefused) {
		t.Fatalf("errors.Is(err, errConnectionRefused) = false; err = %v", err)
	}

	var failure *ProbeFailure
	if !errors.As(err, &failure) {
		t.Fatalf("errors.As(err, *ProbeFailure) = false; err = %v", err)
	}
	if failure.Service != "billing" || failure.Endpoint != (Endpoint{Host: "billing.internal", Port: 8443}) {
		t.Fatalf("ProbeFailure = %+v", failure)
	}

	service := registry["billing"]
	if service.Healthy || service.Retries != 1 {
		t.Fatalf("service after failed probe = %+v", service)
	}
}

func TestApplyProbePassesConfiguredEndpointAndRecordsSuccess(t *testing.T) {
	registry := testRegistry()
	registry["billing"] = Service{
		Name:     "billing",
		Endpoint: Endpoint{Host: "billing.internal", Port: 8443},
		Healthy:  false,
		Retries:  2,
	}
	var got Endpoint

	err := applyProbe(registry, "billing", func(endpoint Endpoint) error {
		got = endpoint
		return nil
	})

	if err != nil {
		t.Fatalf("applyProbe() error = %v", err)
	}
	if got != (Endpoint{Host: "billing.internal", Port: 8443}) {
		t.Fatalf("probe endpoint = %+v", got)
	}
	service := registry["billing"]
	if !service.Healthy || service.Retries != 2 {
		t.Fatalf("service after successful probe = %+v", service)
	}
}
