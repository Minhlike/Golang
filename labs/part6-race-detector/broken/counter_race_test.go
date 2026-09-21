//go:build raceexercise

package broken

import (
	"sync"
	"testing"
)

func TestCounterRecordsConcurrently(t *testing.T) {
	var counter Counter
	const workers = 128

	var wg sync.WaitGroup
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func() {
			defer wg.Done()
			counter.RecordSuccess()
		}()
	}
	wg.Wait()
}
