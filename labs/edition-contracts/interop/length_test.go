//go:build cgo

package interop

import "testing"

func TestCStringBoundary(t *testing.T) {
	for _, tc := range []struct {
		input string
		want  int
	}{{"hello", 5}, {"a\x00b", 1}, {"", 0}} {
		if got := Length(tc.input); got != tc.want {
			t.Fatalf("Length(%q)=%d, want %d", tc.input, got, tc.want)
		}
	}
}
