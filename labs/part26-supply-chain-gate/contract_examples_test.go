package supplychain

import (
	"context"
	"errors"
	"strings"
	"testing"
)

func TestBaseImageContract(t *testing.T) {
	digest := ComputeContentDigest([]byte("approved fixture"))
	catalog := GoldenCatalog{"registry.example/base": digest}
	for _, tc := range []struct {
		name, ref string
		allow     bool
	}{
		{"approved", "registry.example/base@" + digest, true},
		{"tag", "registry.example/base:latest", false},
		{"other digest", "registry.example/base@" + ComputeContentDigest(nil), false},
		{"unknown repository", "registry.example/other@" + digest, false},
		{"empty repository", "@" + digest, false},
		{"multiple separators", "registry.example/base@@" + digest, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			ok, err := VerifyBaseImage(tc.ref, catalog)
			if ok != tc.allow || (err == nil) != tc.allow {
				t.Fatalf("allow=%v err=%v", ok, err)
			}
		})
	}
	// Even a matching malformed catalog value must not be accepted.
	if ok, err := VerifyBaseImage("registry.example/base@sha256:bad",
		GoldenCatalog{"registry.example/base": "sha256:bad"}); ok || err == nil {
		t.Fatal("matching malformed digest was accepted")
	}
}

func TestRemoteVerificationContract(t *testing.T) {
	if result := SafeRemoteVerify(context.Background(), nil); result.Decision != DecisionDeny {
		t.Fatal("missing verifier allowed")
	}
	if result := SafeRemoteVerify(context.Background(), func(context.Context) error {
		return nil
	}); result.Decision != DecisionAllow {
		t.Fatal("successful local verifier denied")
	}
	result := SafeRemoteVerify(context.Background(), func(context.Context) error {
		return errors.New("fixture unavailable")
	})
	if result.Decision != DecisionDeny || len(result.Violations) != 1 ||
		result.Violations[0] != "fail-closed: aborted: fixture unavailable" {
		t.Fatalf("failure not preserved: %+v", result)
	}
}

func TestRemoteVerificationRejectsAlreadyCancelledContext(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	called := false
	result := SafeRemoteVerify(ctx, func(context.Context) error {
		called = true
		return nil
	})
	if called || result.Decision != DecisionDeny {
		t.Fatalf("called=%v result=%+v", called, result)
	}
}

func TestRemoteVerificationRejectsNilAfterCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	result := SafeRemoteVerify(ctx, func(callbackCtx context.Context) error {
		cancel()
		<-callbackCtx.Done()
		return nil // Deliberately incorrect callback result.
	})
	if result.Decision != DecisionDeny || len(result.Violations) != 1 ||
		!strings.Contains(result.Violations[0], "context canceled") {
		t.Fatalf("cancellation was turned into allow: %+v", result)
	}
}
