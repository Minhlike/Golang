package fixed

import "testing"

func TestCheckReturnsExpectedErrorBoundary(t *testing.T) {
	if err := Check(true); err != nil {
		t.Fatalf("Check(true) error = %v, want nil", err)
	}
	err := Check(false)
	if err == nil {
		t.Fatal("Check(false) error = nil, want ProbeError")
	}
	if _, ok := err.(*ProbeError); !ok {
		t.Fatalf("Check(false) type = %T, want *ProbeError", err)
	}
}
