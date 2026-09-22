//go:build exercise

package exercise

import (
	"errors"
	"sync"
	"testing"
)

func TestRecorderKeepsBoundedOutcomeCounts(t *testing.T) {
	var recorder Recorder
	for _, outcome := range []Outcome{
		OutcomeSuccess,
		OutcomeFailure,
		OutcomeTimeout,
	} {
		if err := recorder.Observe(outcome); err != nil {
			t.Fatalf("Observe(%q): %v", outcome, err)
		}
	}
	snapshot := recorder.Snapshot()
	if snapshot != (Snapshot{Completed: 3, Succeeded: 1, Failed: 1, TimedOut: 1}) {
		t.Fatalf("Snapshot() = %#v", snapshot)
	}
	if ratio, known := snapshot.SuccessRatio(); !known || ratio != 1.0/3.0 {
		t.Fatalf("SuccessRatio() = (%v, %v), want (1/3, true)", ratio, known)
	}
}

func TestNoDataIsNotPerfectAvailability(t *testing.T) {
	ratio, known := (Snapshot{}).SuccessRatio()
	if known || ratio != 0 {
		t.Fatalf("SuccessRatio() = (%v, %v), want (0, false)", ratio, known)
	}
}

func TestUnknownOutcomeDoesNotMutateSnapshot(t *testing.T) {
	var recorder Recorder
	if err := recorder.Observe(Outcome("upstream-reset")); !errors.Is(err, ErrUnknownOutcome) {
		t.Fatalf("Observe() error = %v, want ErrUnknownOutcome", err)
	}
	if snapshot := recorder.Snapshot(); snapshot != (Snapshot{}) {
		t.Fatalf("Snapshot() after invalid outcome = %#v", snapshot)
	}
}

func TestRecorderIsSafeUnderConcurrentObservations(t *testing.T) {
	const workers = 24
	const observationsPerWorker = 100
	var recorder Recorder
	var group sync.WaitGroup
	errs := make(chan error, workers)
	for worker := 0; worker < workers; worker++ {
		group.Add(1)
		go func(worker int) {
			defer group.Done()
			outcomes := []Outcome{
				OutcomeSuccess,
				OutcomeFailure,
				OutcomeTimeout,
			}
			for observation := 0; observation < observationsPerWorker; observation++ {
				if err := recorder.Observe(outcomes[(worker+observation)%len(outcomes)]); err != nil {
					errs <- err
					return
				}
			}
		}(worker)
	}
	group.Wait()
	select {
	case err := <-errs:
		t.Fatalf("Observe(): %v", err)
	default:
	}
	snapshot := recorder.Snapshot()
	if snapshot.Completed != workers*observationsPerWorker {
		t.Fatalf("Completed = %d", snapshot.Completed)
	}
	if snapshot.Completed != snapshot.Succeeded+snapshot.Failed+snapshot.TimedOut {
		t.Fatalf("invariant broken: %#v", snapshot)
	}
}
