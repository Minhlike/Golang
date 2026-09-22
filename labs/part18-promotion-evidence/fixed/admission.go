package fixed

import (
	"errors"
	"strings"
)

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
	if !validDigest(candidate.Digest) {
		return Decision{}, ErrInvalidDigest
	}
	if strings.TrimSpace(candidate.Revision) == "" {
		return Decision{}, ErrMissingRevision
	}
	if !candidate.TestsPassed {
		return Decision{Reason: ReasonTestsNotPassed}, nil
	}
	if !candidate.ProvenanceVerified {
		return Decision{Reason: ReasonProvenanceMissing}, nil
	}
	return Decision{Allowed: true, Digest: candidate.Digest}, nil
}

func validDigest(value string) bool {
	const prefix = "sha256:"
	if !strings.HasPrefix(value, prefix) || len(value) != len(prefix)+64 {
		return false
	}
	for _, char := range value[len(prefix):] {
		if !('0' <= char && char <= '9') && !('a' <= char && char <= 'f') {
			return false
		}
	}
	return true
}
