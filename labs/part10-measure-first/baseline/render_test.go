package baseline

import (
	"fmt"
	"testing"
)

func TestRenderPreservesWireFormat(t *testing.T) {
	readings := []Reading{{Name: "api", Millis: 17}, {Name: "cache", Millis: 3}}
	if got, want := Render(readings), "api=17ms\ncache=3ms\n"; got != want {
		t.Fatalf("Render() = %q, want %q", got, want)
	}
}

func BenchmarkRender(b *testing.B) {
	readings := representativeReadings(1_000)
	b.ReportAllocs()
	for b.Loop() {
		Render(readings)
	}
}

func representativeReadings(n int) []Reading {
	readings := make([]Reading, n)
	for i := range readings {
		readings[i] = Reading{Name: fmt.Sprintf("endpoint-%04d", i), Millis: int64(i)}
	}
	return readings
}
