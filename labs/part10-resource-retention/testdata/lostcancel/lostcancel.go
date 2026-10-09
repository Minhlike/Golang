package lostcancel

import "context"

// Deliberately rejected by go vet; testdata is excluded from ./... discovery.
func Broken(parent context.Context) context.Context {
	child, _ := context.WithCancel(parent)
	return child
}
