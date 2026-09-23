package gate

import (
	"errors"
	"testing"
)

func TestEvaluate_Approved(t *testing.T) {
	c := Candidate{
		Digest:             "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
		Revision:           "abc1234",
		TestsPassed:        true,
		ProvenanceVerified: true,
	}
	dec, err := Evaluate(c)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !dec.Allowed {
		t.Fatalf("expected allowed, got denied with reason: %s", dec.Reason)
	}
	if dec.Digest != c.Digest {
		t.Fatalf("expected digest %s, got %s", c.Digest, dec.Digest)
	}
}

func TestEvaluate_RejectedWhenTestsFail(t *testing.T) {
	c := Candidate{
		Digest:             "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
		Revision:           "abc1234",
		TestsPassed:        false,
		ProvenanceVerified: true,
	}
	dec, err := Evaluate(c)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if dec.Allowed {
		t.Fatal("expected denied when tests fail")
	}
	if dec.Reason != ReasonTestsNotPassed {
		t.Fatalf("expected reason %q, got %q", ReasonTestsNotPassed, dec.Reason)
	}
	if dec.Digest != "" {
		t.Fatalf("denied candidate must not contain digest: %s", dec.Digest)
	}
}

func TestEvaluate_RejectedWhenProvenanceMissing(t *testing.T) {
	c := Candidate{
		Digest:             "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
		Revision:           "abc1234",
		TestsPassed:        true,
		ProvenanceVerified: false,
	}
	dec, err := Evaluate(c)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if dec.Allowed {
		t.Fatal("expected denied when provenance missing")
	}
	if dec.Reason != ReasonProvenanceMissing {
		t.Fatalf("expected reason %q, got %q", ReasonProvenanceMissing, dec.Reason)
	}
}

func TestEvaluate_MalformedInput(t *testing.T) {
	tests := []struct {
		name      string
		candidate Candidate
		wantErr   error
	}{
		{
			name: "invalid digest prefix",
			candidate: Candidate{
				Digest:   "md5:bad",
				Revision: "rev1",
			},
			wantErr: ErrInvalidDigest,
		},
		{
			name: "digest with uppercase characters",
			candidate: Candidate{
				Digest:   "sha256:0123456789ABCDEF0123456789abcdef0123456789abcdef0123456789abcdef",
				Revision: "rev1",
			},
			wantErr: ErrInvalidDigest,
		},
		{
			name: "digest wrong length",
			candidate: Candidate{
				Digest:   "sha256:0123456789abcdef",
				Revision: "rev1",
			},
			wantErr: ErrInvalidDigest,
		},
		{
			name: "missing revision",
			candidate: Candidate{
				Digest:   "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
				Revision: "  ",
			},
			wantErr: ErrMissingRevision,
		},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			_, err := Evaluate(tc.candidate)
			if !errors.Is(err, tc.wantErr) {
				t.Fatalf("expected error %v, got %v", tc.wantErr, err)
			}
		})
	}
}
