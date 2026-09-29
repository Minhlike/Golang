package app

import (
	"context"
	"testing"

	"example.com/golang-master/part6-testable-command/probe"
)

// These fixtures compile and execute the Chapter 6 benchmark examples. They
// perform no network I/O; their timings are not a production performance claim.
var mockLookup = lookup("OPS_PROBE_TARGET", "payments.internal:9443")
var mockRunner probe.Runner = func(context.Context, probe.Endpoint) error {
	return nil
}

func BenchmarkAppRunLoop(b *testing.B) {
	b.ReportAllocs()
	for b.Loop() {
		res, _ := Run(
			context.Background(), mockLookup, mockRunner,
		)
		if len(res) > 0 && res[0].Service == "" {
			b.Fatal("unexpected empty outcome")
		}
	}
}

var sinkResult []Outcome

func BenchmarkAppRunLegacy(b *testing.B) {
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		res, _ := Run(
			context.Background(), mockLookup, mockRunner,
		)
		if len(res) > 0 {
			sinkResult = res
		}
	}
}
