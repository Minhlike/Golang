package main

import (
	"context"
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

	err := applyProbe(context.Background(), registry, "search", func(context.Context, Endpoint) error {
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

	err := applyProbe(context.Background(), registry, "billing", func(context.Context, Endpoint) error {
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

	err := applyProbe(context.Background(), registry, "billing", func(_ context.Context, endpoint Endpoint) error {
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

func TestApplyProbeCancellationDoesNotChangeHealthState(t *testing.T) {
	registry := testRegistry()
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	ran := false

	err := applyProbe(ctx, registry, "billing", func(context.Context, Endpoint) error {
		ran = true
		return nil
	})

	if !errors.Is(err, context.Canceled) {
		t.Fatalf("errors.Is(err, context.Canceled) = false; err = %v", err)
	}
	if ran {
		t.Fatal("probe ran after context cancellation")
	}
	service := registry["billing"]
	if !service.Healthy || service.Retries != 0 {
		t.Fatalf("service after canceled probe = %+v", service)
	}
}

type testSession struct {
	closeCalls int
	closeErr   error
}

func (session *testSession) Close() error {
	session.closeCalls++
	return session.closeErr
}

func TestRunWithSessionCleanupPolicy(t *testing.T) {
	t.Run("canceled context does not acquire a session", func(t *testing.T) {
		ctx, cancel := context.WithCancel(context.Background())
		cancel()
		opened := false

		err := runWithSession(ctx, Endpoint{}, func(Endpoint) (ProbeSession, error) {
			opened = true
			return &testSession{}, nil
		}, func(context.Context, Endpoint, ProbeSession) error {
			return nil
		})

		if !errors.Is(err, context.Canceled) {
			t.Fatalf("errors.Is(err, context.Canceled) = false; err = %v", err)
		}
		if opened {
			t.Fatal("open ran after context cancellation")
		}
	})

	t.Run("cleanup preserves a primary probe failure", func(t *testing.T) {
		session := &testSession{closeErr: errors.New("close failed")}
		probeErr := errors.New("connection refused")

		err := runWithSession(context.Background(), Endpoint{}, func(Endpoint) (ProbeSession, error) {
			return session, nil
		}, func(context.Context, Endpoint, ProbeSession) error {
			return probeErr
		})

		if !errors.Is(err, probeErr) {
			t.Fatalf("errors.Is(err, probeErr) = false; err = %v", err)
		}
		if session.closeCalls != 1 {
			t.Fatalf("Close calls = %d, want 1", session.closeCalls)
		}
	})

	t.Run("cleanup error is returned after success", func(t *testing.T) {
		closeErr := errors.New("close failed")
		session := &testSession{closeErr: closeErr}

		err := runWithSession(context.Background(), Endpoint{}, func(Endpoint) (ProbeSession, error) {
			return session, nil
		}, func(context.Context, Endpoint, ProbeSession) error {
			return nil
		})

		if !errors.Is(err, closeErr) {
			t.Fatalf("errors.Is(err, closeErr) = false; err = %v", err)
		}
		if session.closeCalls != 1 {
			t.Fatalf("Close calls = %d, want 1", session.closeCalls)
		}
	})
}
