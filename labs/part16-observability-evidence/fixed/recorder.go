package fixed

import (
	"errors"
	"sync"
)

var ErrUnknownOutcome = errors.New("unknown outcome")

type Outcome string

const (
	OutcomeSuccess Outcome = "success"
	OutcomeFailure Outcome = "failure"
	OutcomeTimeout Outcome = "timeout"
)

type Snapshot struct {
	Completed uint64
	Succeeded uint64
	Failed    uint64
	TimedOut  uint64
}

func (s Snapshot) SuccessRatio() (float64, bool) {
	if s.Completed == 0 {
		return 0, false
	}
	return float64(s.Succeeded) / float64(s.Completed), true
}

type Recorder struct {
	mu       sync.Mutex
	snapshot Snapshot
}

func (r *Recorder) Observe(outcome Outcome) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	switch outcome {
	case OutcomeSuccess:
		r.snapshot.Succeeded++
	case OutcomeFailure:
		r.snapshot.Failed++
	case OutcomeTimeout:
		r.snapshot.TimedOut++
	default:
		return ErrUnknownOutcome
	}
	r.snapshot.Completed++
	return nil
}

func (r *Recorder) Snapshot() Snapshot {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.snapshot
}
