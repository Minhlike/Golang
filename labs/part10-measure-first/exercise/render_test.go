//go:build exercise

package exercise

import "testing"

func TestRenderPreservesWireFormat(t *testing.T) {
	readings := []Reading{
		{Name: "api", Millis: 17},
		{Name: "cache", Millis: 3},
	}

	if got, want := Render(readings), "api=17ms\ncache=3ms\n"; got != want {
		t.Fatalf("Render() = %q, want %q", got, want)
	}
}

func TestRenderEmpty(t *testing.T) {
	if got := Render(nil); got != "" {
		t.Fatalf("Render(nil) = %q, want empty", got)
	}
}
