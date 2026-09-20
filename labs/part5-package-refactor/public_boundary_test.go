//go:build exercise

package main

import (
	"context"
	"testing"

	"example.com/golang-master/part5-package-refactor/probe"
)

func TestCheckReturnsACompletedObservation(t *testing.T) {
	service := probe.Service{
		Name:     "billing",
		Endpoint: probe.Endpoint{Host: "billing.internal", Port: 8443},
	}

	result, err := probe.Check(context.Background(), service, func(_ context.Context, endpoint probe.Endpoint) error {
		if endpoint != service.Endpoint {
			t.Fatalf("runner endpoint = %+v, want %+v", endpoint, service.Endpoint)
		}
		return nil
	})
	if err != nil {
		t.Fatalf("Check() error = %v", err)
	}
	if result != (probe.Result{Service: "billing", Healthy: true}) {
		t.Fatalf("Check() result = %+v", result)
	}
}
