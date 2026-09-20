package main

import "testing"

func TestSliceAssignmentSharesElements(t *testing.T) {
	a := []int{10, 20, 30}
	b := a
	b[0] = 99
	if a[0] != 99 {
		t.Fatalf("a[0] = %d, want shared mutation", a[0])
	}
}

func TestRedactedCopyDoesNotMutateInput(t *testing.T) {
	input := []string{"api-key", "region"}
	got := redactedCopy(input)
	if got[0] != "***" {
		t.Fatalf("preview[0] = %q, want redacted", got[0])
	}
	if input[0] != "api-key" {
		t.Fatalf("input was mutated: %q", input[0])
	}
}
