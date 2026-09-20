package status

import "testing"

func TestClassifyLatency(t *testing.T) {
	tests := []struct {
		name      string
		latencyMS int
		want      string
	}{
		{name: "negative is invalid", latencyMS: -1, want: "invalid"},
		{name: "zero is healthy", latencyMS: 0, want: "healthy"},
		{name: "healthy upper edge", latencyMS: 199, want: "healthy"},
		{name: "degraded lower edge", latencyMS: 200, want: "degraded"},
		{name: "degraded upper edge", latencyMS: 999, want: "degraded"},
		{name: "unhealthy lower edge", latencyMS: 1000, want: "unhealthy"},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if got := ClassifyLatency(test.latencyMS); got != test.want {
				t.Fatalf("ClassifyLatency(%d) = %q, want %q", test.latencyMS, got, test.want)
			}
		})
	}
}
