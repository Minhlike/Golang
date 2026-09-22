package exercise

import "errors"

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
	return 0, false
}

type Recorder struct{}

func (r *Recorder) Observe(outcome Outcome) error {
	return errors.New("Observe has not been implemented")
}

func (r *Recorder) Snapshot() Snapshot {
	return Snapshot{}
}
