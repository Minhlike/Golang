package main

import (
	"runtime"
	"testing"
	"unsafe"
)

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

func TestRedactedCopyEmptyInput(t *testing.T) {
	for _, input := range [][]string{nil, {}} {
		if got := redactedCopy(input); len(got) != 0 {
			t.Fatalf("empty input produced %v", got)
		}
	}
}

func TestRedactedCopyOwnsElements(t *testing.T) {
	input := []string{"api-key", "region"}
	got := redactedCopy(input)
	got[1] = "preview-only"
	if input[1] != "region" {
		t.Fatal("preview mutation reached input")
	}
	input[1] = "input-only"
	if got[1] != "preview-only" {
		t.Fatal("input mutation reached preview")
	}
}

func TestCapacityLimitDoesNotIsolateExistingElements(t *testing.T) {
	base := []int{10, 20, 30}
	view := base[:2:2]
	view[0] = 99
	if base[0] != 99 {
		t.Fatal("full slice expression unexpectedly copied existing elements")
	}
	grown := append(view, 40)
	grown[0] = 77
	if base[0] != 99 || base[2] != 30 || grown[2] != 40 {
		t.Fatalf("append must allocate when capacity is exhausted: %v %v", base, grown)
	}
}

func TestPointerElementsRemainSharedAfterCopy(t *testing.T) {
	value := 10
	input := []*int{&value}
	clone := make([]*int, len(input))
	copy(clone, input)
	*clone[0] = 99
	if *input[0] != 99 {
		t.Fatal("copy of pointer elements should still share their pointee")
	}
	other := 20
	clone[0] = &other
	if *input[0] != 99 {
		t.Fatal("replacing the copied pointer should not replace input's element")
	}
}

func TestSliceDescriptorImplementationMeasurement(t *testing.T) {
	// This is a measurement of this toolchain, not a language layout guarantee.
	var s []int
	t.Logf("toolchain=%s GOOS=%s GOARCH=%s slice=%d uintptr=%d",
		runtime.Version(), runtime.GOOS, runtime.GOARCH,
		unsafe.Sizeof(s), unsafe.Sizeof(uintptr(0)))
}
