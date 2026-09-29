package changegate

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"time"
)

var ErrDenied = errors.New("change denied")

type Plan struct {
	Action  string
	Target  string
	DiffSHA string
}

func (p Plan) Digest() string {
	// Fixed struct field order is part of this lab's versioned encoding.
	b, _ := json.Marshal(struct {
		Version int
		Plan    Plan
	}{1, p})
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

type Evidence struct {
	PlanDigest string
	Passed     bool
	CheckedAt  time.Time
}

type Approval struct {
	PlanDigest string
	Caller     string
	ExpiresAt  time.Time
}

type Principal struct {
	ID       string
	Operator bool
}

type Policy struct {
	AllowedTargets map[string]bool
	MaxEvidenceAge time.Duration
}

// Check is a local teaching policy. Evidence/Approval must be supplied by
// trusted verifier/approval storage, never decoded from the agent's own input.
// A returned nil is not an executor, a distributed lock or a replay guard.
func (p Policy) Check(now time.Time, who Principal, plan Plan, e Evidence, a Approval) error {
	if who.ID == "" || !who.Operator || p.MaxEvidenceAge <= 0 {
		return ErrDenied
	}
	if plan.Action != "restart-demo" || !p.AllowedTargets[plan.Target] {
		return ErrDenied
	}
	decoded, err := hex.DecodeString(plan.DiffSHA)
	if err != nil || len(decoded) != sha256.Size {
		return ErrDenied
	}
	digest := plan.Digest()
	if !e.Passed || e.PlanDigest != digest || e.CheckedAt.IsZero() || e.CheckedAt.After(now) || now.Sub(e.CheckedAt) > p.MaxEvidenceAge {
		return ErrDenied
	}
	if a.PlanDigest != digest || a.Caller != who.ID || !now.Before(a.ExpiresAt) {
		return ErrDenied
	}
	return nil
}
