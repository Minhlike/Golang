//go:build exercise

package exercise

import (
	"fmt"
	"testing"
)

func BenchmarkRenderRepresentativeInput(b *testing.B) {
	readings := representativeReadings(1_000)
	for b.Loop() {
		Render(readings)
	}
}

func representativeReadings(n int) []Reading {
	readings := make([]Reading, n)
	for i := range readings {
		readings[i] = Reading{
			Name:   fmt.Sprintf("endpoint-%04d", i),
			Millis: int64(i),
		}
	}
	return readings
}
