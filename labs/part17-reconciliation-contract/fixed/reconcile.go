package fixed

import "errors"

var ErrNegativeReplicaCount = errors.New("replica counts must not be negative")

type ActionKind string

const (
	ActionNone   ActionKind = "none"
	ActionCreate ActionKind = "create"
	ActionDelete ActionKind = "delete"
)

type Action struct {
	Kind  ActionKind
	Count int
}

func NextAction(desired, current int) (Action, error) {
	if desired < 0 || current < 0 {
		return Action{}, ErrNegativeReplicaCount
	}
	if current < desired {
		return Action{Kind: ActionCreate, Count: desired - current}, nil
	}
	if current > desired {
		return Action{Kind: ActionDelete, Count: current - desired}, nil
	}
	return Action{Kind: ActionNone}, nil
}
