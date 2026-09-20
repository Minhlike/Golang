package probe

import (
	"context"
	"errors"
	"testing"
)

func TestCheckSkipsRunnerWhenContextIsCanceled(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	ran := false

	_, err := Check(ctx, Service{Name: "billing"}, func(context.Context, Endpoint) error {
		ran = true
		return nil
	})

	if !errors.Is(err, context.Canceled) {
		t.Fatalf("errors.Is(err, context.Canceled) = false; err = %v", err)
	}
	if ran {
		t.Fatal("runner ran after context cancellation")
	}
}

func TestCheckReturnsSuccessfulObservation(t *testing.T) {
	service := Service{Name: "billing", Endpoint: Endpoint{Host: "billing.internal", Port: 8443}}
	var got Endpoint

	result, err := Check(context.Background(), service, func(_ context.Context, endpoint Endpoint) error {
		got = endpoint
		return nil
	})

	if err != nil {
		t.Fatalf("Check() error = %v", err)
	}
	if got != service.Endpoint {
		t.Fatalf("runner endpoint = %+v, want %+v", got, service.Endpoint)
	}
	if result != (Result{Service: "billing", Healthy: true}) {
		t.Fatalf("Check() result = %+v", result)
	}
}
