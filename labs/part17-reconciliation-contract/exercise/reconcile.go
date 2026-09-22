package exercise

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
	return Action{}, errors.New("NextAction has not been implemented")
}
