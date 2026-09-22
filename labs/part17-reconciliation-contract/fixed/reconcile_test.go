package fixed

import (
	"errors"
	"testing"
)

func TestNextActionReturnsOnlyTheReplicaDelta(t *testing.T) {
	tests := []struct {
		name             string
		desired, current int
		want             Action
	}{
		{"creates missing replicas", 3, 1, Action{Kind: ActionCreate, Count: 2}},
		{"deletes surplus replicas", 2, 5, Action{Kind: ActionDelete, Count: 3}},
		{"does nothing when counts match", 4, 4, Action{Kind: ActionNone}},
		{"scales to zero", 0, 2, Action{Kind: ActionDelete, Count: 2}},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			got, err := NextAction(test.desired, test.current)
			if err != nil {
				t.Fatalf("NextAction() error = %v", err)
			}
			if got != test.want {
				t.Fatalf("NextAction() = %#v, want %#v", got, test.want)
			}
		})
	}
}

func TestNextActionRejectsNegativeCounts(t *testing.T) {
	for _, counts := range [][2]int{{-1, 0}, {0, -1}} {
		got, err := NextAction(counts[0], counts[1])
		if !errors.Is(err, ErrNegativeReplicaCount) {
			t.Fatalf("NextAction(%d, %d) error = %v", counts[0], counts[1], err)
		}
		if got != (Action{}) {
			t.Fatalf("NextAction(%d, %d) action = %#v", counts[0], counts[1], got)
		}
	}
}

func TestNextActionConvergesAfterTheCallerAppliesIt(t *testing.T) {
	const desired = 3
	current := 1
	first, err := NextAction(desired, current)
	if err != nil {
		t.Fatalf("first NextAction() error = %v", err)
	}
	if first.Kind != ActionCreate || first.Count != 2 {
		t.Fatalf("first action = %#v", first)
	}
	second, err := NextAction(desired, current+first.Count)
	if err != nil {
		t.Fatalf("second NextAction() error = %v", err)
	}
	if second != (Action{Kind: ActionNone}) {
		t.Fatalf("second action = %#v, want none", second)
	}
}
