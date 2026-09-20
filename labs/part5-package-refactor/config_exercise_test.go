//go:build configexercise

package main

import (
	"testing"

	"example.com/golang-master/part5-package-refactor/internal/config"
)

func TestLoadTargetsUsesEnvironmentOverride(t *testing.T) {
	targets, err := config.LoadTargets(func(key string) (string, bool) {
		if key == "OPS_PROBE_TARGET" {
			return "payments.internal:9443", true
		}
		return "", false
	})
	if err != nil {
		t.Fatalf("LoadTargets() error = %v", err)
	}
	if len(targets) != 1 {
		t.Fatalf("target count = %d, want 1", len(targets))
	}
	if got := targets[0]; got.Host != "payments.internal" || got.Port != 9443 {
		t.Fatalf("target = %+v, want payments.internal:9443", got)
	}
}
