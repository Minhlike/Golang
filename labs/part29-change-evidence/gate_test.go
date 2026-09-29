package changegate

import (
	"errors"
	"strings"
	"testing"
	"time"
)

func TestContract(t *testing.T) {
	now := time.Date(2026, 9, 29, 0, 0, 0, 0, time.UTC)
	base := Plan{"restart-demo", "local-demo", strings.Repeat("a", 64)}
	policy := Policy{map[string]bool{"local-demo": true}, time.Minute}
	actor := Principal{"operator-1", true}
	evidence := Evidence{base.Digest(), true, now.Add(-time.Second)}
	approval := Approval{base.Digest(), actor.ID, now.Add(time.Minute)}
	if err := policy.Check(now, actor, base, evidence, approval); err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		name   string
		mutate func(*Plan, *Principal, *Evidence, *Approval)
	}{
		{"changed diff", func(p *Plan, _ *Principal, _ *Evidence, _ *Approval) { p.DiffSHA = strings.Repeat("b", 64) }},
		{"different target", func(p *Plan, _ *Principal, _ *Evidence, _ *Approval) { p.Target = "production" }},
		{"different action", func(p *Plan, _ *Principal, _ *Evidence, _ *Approval) { p.Action = "shell" }},
		{"bad hash", func(p *Plan, _ *Principal, _ *Evidence, _ *Approval) { p.DiffSHA = "not-a-hash" }},
		{"anonymous", func(_ *Plan, w *Principal, _ *Evidence, _ *Approval) { w.ID = "" }},
		{"viewer", func(_ *Plan, w *Principal, _ *Evidence, _ *Approval) { w.Operator = false }},
		{"other caller", func(_ *Plan, w *Principal, _ *Evidence, _ *Approval) { w.ID = "operator-2" }},
		{"failed tests", func(_ *Plan, _ *Principal, e *Evidence, _ *Approval) { e.Passed = false }},
		{"stale tests", func(_ *Plan, _ *Principal, e *Evidence, _ *Approval) { e.CheckedAt = now.Add(-2 * time.Minute) }},
		{"future tests", func(_ *Plan, _ *Principal, e *Evidence, _ *Approval) { e.CheckedAt = now.Add(time.Second) }},
		{"expired", func(_ *Plan, _ *Principal, _ *Evidence, a *Approval) { a.ExpiresAt = now }},
		{"missing evidence", func(_ *Plan, _ *Principal, e *Evidence, _ *Approval) { *e = Evidence{} }},
		{"missing approval", func(_ *Plan, _ *Principal, _ *Evidence, a *Approval) { *a = Approval{} }},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			plan, who, e, a := base, actor, evidence, approval
			tc.mutate(&plan, &who, &e, &a)
			if err := policy.Check(now, who, plan, e, a); !errors.Is(err, ErrDenied) {
				t.Fatalf("expected denial, got %v", err)
			}
		})
	}
}

func TestDigestDeterministicAndBoundToMeaning(t *testing.T) {
	p := Plan{"restart-demo", "local-demo", strings.Repeat("a", 64)}
	if p.Digest() != p.Digest() {
		t.Fatal("non-deterministic")
	}
	q := p
	q.Target = "other"
	if p.Digest() == q.Digest() {
		t.Fatal("unbound target")
	}
}
