package exercise

import "errors"

var (
	ErrInvalidDigest   = errors.New("digest must be a lowercase sha256 digest")
	ErrMissingRevision = errors.New("source revision is required")
)

const (
	ReasonTestsNotPassed    = "tests not passed"
	ReasonProvenanceMissing = "provenance not verified"
)

type Candidate struct {
	Digest             string
	Revision           string
	TestsPassed        bool
	ProvenanceVerified bool
}

type Decision struct {
	Allowed bool
	Digest  string
	Reason  string
}

func Evaluate(candidate Candidate) (Decision, error) {
	return Decision{}, errors.New("Evaluate has not been implemented")
}
