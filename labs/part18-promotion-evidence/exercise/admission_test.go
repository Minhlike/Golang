//go:build exercise

package exercise

import (
	"errors"
	"strings"
	"testing"
)

const digest = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

func validCandidate() Candidate {
	return Candidate{
		Digest:             digest,
		Revision:           "4e4f7b0",
		TestsPassed:        true,
		ProvenanceVerified: true,
	}
}

func TestEvaluateAllowsOnlyACompleteCandidate(t *testing.T) {
	got, err := Evaluate(validCandidate())
	if err != nil {
		t.Fatalf("Evaluate() error = %v", err)
	}
	if got != (Decision{Allowed: true, Digest: digest}) {
		t.Fatalf("Evaluate() = %#v", got)
	}
}

func TestEvaluateRejectsMalformedIdentity(t *testing.T) {
	tests := []struct {
		name string
		edit func(*Candidate)
		want error
	}{
		{"wrong digest", func(c *Candidate) { c.Digest = "latest" }, ErrInvalidDigest},
		{"uppercase digest", func(c *Candidate) { c.Digest = "sha256:" + strings.Repeat("A", 64) }, ErrInvalidDigest},
		{"missing revision", func(c *Candidate) { c.Revision = "  " }, ErrMissingRevision},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			candidate := validCandidate()
			test.edit(&candidate)
			got, err := Evaluate(candidate)
			if !errors.Is(err, test.want) {
				t.Fatalf("Evaluate() error = %v, want %v", err, test.want)
			}
			if got != (Decision{}) {
				t.Fatalf("Evaluate() decision = %#v", got)
			}
		})
	}
}

func TestEvaluateFailsClosedWhenEvidenceIsMissing(t *testing.T) {
	tests := []struct {
		name string
		edit func(*Candidate)
		want string
	}{
		{"tests", func(c *Candidate) { c.TestsPassed = false }, ReasonTestsNotPassed},
		{"provenance", func(c *Candidate) { c.ProvenanceVerified = false }, ReasonProvenanceMissing},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			candidate := validCandidate()
			test.edit(&candidate)
			got, err := Evaluate(candidate)
			if err != nil {
				t.Fatalf("Evaluate() error = %v", err)
			}
			if got.Allowed || got.Digest != "" || got.Reason != test.want {
				t.Fatalf("Evaluate() = %#v", got)
			}
		})
	}
}
