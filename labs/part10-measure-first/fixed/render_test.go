package fixed

import (
	"fmt"
	"sync"
	"testing"
)

func TestRenderPreservesWireFormat(t *testing.T) {
	readings := []Reading{{Name: "api", Millis: 17}, {Name: "cache", Millis: 3}}
	if got, want := Render(readings), "api=17ms\ncache=3ms\n"; got != want {
		t.Fatalf("Render() = %q, want %q", got, want)
	}
}

func TestRenderConcurrentBatchWorkload(t *testing.T) {
	const workers = 4
	const itemsPerWorker = 250
	readings := representativeReadings(workers * itemsPerWorker)

	var wg sync.WaitGroup
	errCh := make(chan error, workers)

	for w := 0; w < workers; w++ {
		start := w * itemsPerWorker
		end := start + itemsPerWorker
		chunk := readings[start:end]

		wg.Add(1)
		go func(workerID int, slice []Reading) {
			defer wg.Done()
			out := Render(slice)
			if len(out) == 0 {
				errCh <- fmt.Errorf("worker %d produced empty output", workerID)
			}
		}(w, chunk)
	}

	wg.Wait()
	close(errCh)

	for err := range errCh {
		t.Fatal(err)
	}
}

func BenchmarkRender(b *testing.B) {
	readings := representativeReadings(1_000)
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
