package fixed

import (
	"math"
	"testing"
)

func TestUniqueInterfaceKeyCanPanic(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("an interface holding a slice must panic as a map key")
		}
	}()
	// any satisfies comparable; the slice's dynamic value does not.
	Unique([]any{[]byte{1}})
}

func TestUniqueNaNUsesGoEqualityNotNormalization(t *testing.T) {
	nan := math.NaN()
	got := Unique([]float64{nan, nan, 1, 1})
	if len(got) != 3 || !math.IsNaN(got[0]) || !math.IsNaN(got[1]) || got[2] != 1 {
		t.Fatalf("Unique() = %v; NaN does not compare equal to itself", got)
	}
	set := NewSet(nan)
	if set.Has(nan) {
		t.Fatal("NaN cannot be retrieved by equality lookup")
	}
}

func TestUniqueAllocatesOuterSliceButDoesNotClonePointees(t *testing.T) {
	n := 1
	input := []*int{&n, &n}
	got := Unique(input)
	if len(got) != 1 {
		t.Fatalf("Unique() = %v", got)
	}
	got[0] = nil
	if input[0] == nil {
		t.Fatal("result outer slice aliases input")
	}
	got = Unique(input)
	*got[0] = 2
	if n != 2 {
		t.Fatal("Unique unexpectedly cloned the pointee")
	}
}
