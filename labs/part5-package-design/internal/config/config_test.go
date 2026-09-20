package config

import "testing"

func TestDefaultTargetsReturnsFreshSlice(t *testing.T) {
	first := DefaultTargets()
	first[0].Name = "changed-by-caller"

	second := DefaultTargets()
	if second[0].Name != "billing" {
		t.Fatalf("second default name = %q, want billing", second[0].Name)
	}
}
