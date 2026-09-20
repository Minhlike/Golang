package app

import (
	"context"
	"errors"
	"testing"

	"example.com/golang-master/part6-testable-command/probe"
)

func lookup(key, value string) func(string) (string, bool) {
	return func(got string) (string, bool) {
		return value, got == key
	}
}

func TestRunMapsEnvironmentTargetToRunner(t *testing.T) {
	var got probe.Endpoint
	outcomes, err := Run(context.Background(), lookup(
		"OPS_PROBE_TARGET", "payments.internal:9443",
	), func(_ context.Context, endpoint probe.Endpoint) error {
		got = endpoint
		return nil
	})

	if err != nil {
		t.Fatalf("Run() error = %v", err)
	}
	if got != (probe.Endpoint{Host: "payments.internal", Port: 9443}) {
		t.Fatalf("runner endpoint = %+v", got)
	}
	if len(outcomes) != 1 || outcomes[0] != (Outcome{Service: "billing"}) {
		t.Fatalf("outcomes = %+v", outcomes)
	}
}

func TestRunRejectsConfigBeforeCallingRunner(t *testing.T) {
	ran := false
	_, err := Run(context.Background(), lookup(
		"OPS_PROBE_TARGET", "payments.internal:0",
	), func(context.Context, probe.Endpoint) error {
		ran = true
		return nil
	})

	if err == nil {
		t.Fatal("Run() returned nil error for invalid target")
	}
	if ran {
		t.Fatal("runner ran after config validation failed")
	}
}

func TestRunKeepsProbeFailureWithItsService(t *testing.T) {
	errRefused := errors.New("connection refused")
	outcomes, err := Run(context.Background(), lookup("", ""), func(context.Context, probe.Endpoint) error {
		return errRefused
	})

	if err != nil {
		t.Fatalf("Run() error = %v", err)
	}
	if len(outcomes) != 1 || outcomes[0].Service != "billing" || !errors.Is(outcomes[0].Err, errRefused) {
		t.Fatalf("outcomes = %+v", outcomes)
	}
}

func TestRunStopsForCanceledContext(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	ran := false

	_, err := Run(ctx, lookup("", ""), func(context.Context, probe.Endpoint) error {
		ran = true
		return nil
	})

	if !errors.Is(err, context.Canceled) {
		t.Fatalf("errors.Is(err, context.Canceled) = false; err = %v", err)
	}
	if ran {
		t.Fatal("runner ran after cancellation")
	}
}
