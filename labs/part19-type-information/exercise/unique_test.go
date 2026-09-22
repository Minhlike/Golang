//go:build exercise

package exercise

import "testing"

type targetName string

func TestUniqueKeepsFirstOccurrencesInOrder(t *testing.T) {
	input := []string{"api", "db", "api", "cache", "db"}
	got := Unique(input)
	want := []string{"api", "db", "cache"}
	if len(got) != len(want) {
		t.Fatalf("len(Unique()) = %d, want %d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("Unique()[%d] = %q, want %q", i, got[i], want[i])
		}
	}
	if input[0] != "api" || input[2] != "api" {
		t.Fatalf("Unique mutated input: %#v", input)
	}
}

func TestUniquePreservesNamedComparableType(t *testing.T) {
	got := Unique([]targetName{"api", "api", "db"})
	want := []targetName{"api", "db"}
	if len(got) != len(want) || got[0] != want[0] || got[1] != want[1] {
		t.Fatalf("Unique(named type) = %#v, want %#v", got, want)
	}
}
