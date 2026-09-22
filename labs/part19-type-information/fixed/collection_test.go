package fixed

import (
	"fmt"
	"testing"
)

type targetName string

func TestUniquePreservesOrderAndInput(t *testing.T) {
	input := []targetName{"api", "db", "api", "cache"}
	got := Unique(input)
	want := []targetName{"api", "db", "cache"}
	if len(got) != len(want) {
		t.Fatalf("len(Unique()) = %d, want %d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("Unique()[%d] = %q, want %q", i, got[i], want[i])
		}
	}
	if input[2] != "api" {
		t.Fatalf("Unique mutated input: %#v", input)
	}
}

func TestSetAndGenericMethod(t *testing.T) {
	ports := NewSet(443, 8080, 443)
	if !ports.Has(443) || ports.Has(80) {
		t.Fatalf("unexpected set membership: %#v", ports)
	}
	labels := Batch[int]{443, 8080}.Map(func(port int) string {
		return fmt.Sprintf("port=%d", port)
	})
	if len(labels) != 2 || labels[0] != "port=443" {
		t.Fatalf("Map() = %#v", labels)
	}
}
