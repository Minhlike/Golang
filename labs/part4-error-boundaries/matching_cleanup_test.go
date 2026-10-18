package main

import (
	"context"
	"errors"
	"fmt"
	"reflect"
	"testing"
)

func TestErrorMatchingBoundaries(t *testing.T) {
	a := errors.New("connection refused")
	b := errors.New("connection refused")
	if errors.Is(a, b) || !errors.Is(fmt.Errorf("operation: %w", a), a) ||
		errors.Is(fmt.Errorf("operation: %v", a), a) {
		t.Fatal("text equality is not error identity")
	}
	first := &ProbeFailure{Service: "first", Cause: a}
	second := &ProbeFailure{Service: "second", Cause: b}
	joined := errors.Join(first, second)
	var got *ProbeFailure
	if !errors.Is(joined, b) || !errors.As(joined, &got) || got != first || errors.Unwrap(joined) != nil {
		t.Fatal("Join traversal differs from Unwrap() error")
	}
	var typedNil *ProbeFailure
	var err error = typedNil
	got = first
	if err == nil || !errors.As(err, &got) || got != nil {
		t.Fatal("typed nil must retain its dynamic type")
	}
	t.Run("invalid As target panics", func(t *testing.T) {
		defer func() {
			if recover() == nil {
				t.Fatal("invalid As target accepted")
			}
		}()
		// An any parameter allows the runtime contract to be tested without
		// deliberately failing the static errorsas analyzer.
		call := func(target any) { errors.As(a, target) }
		call(new(int))
	})
}

func TestDeferIsFunctionScopedAndCapturesArguments(t *testing.T) {
	var trace []int
	func() {
		x := 1
		{
			defer func(n int) { trace = append(trace, n) }(x)
			x = 2
		}
		if len(trace) != 0 {
			t.Fatal("defer ran at block exit")
		}
		defer func() { trace = append(trace, x) }()
	}()
	if !reflect.DeepEqual(trace, []int{2, 1}) {
		t.Fatalf("want LIFO and captured argument: %v", trace)
	}
}

func indirectRecover() any { return recover() }

func controlledPanic() { panic("controlled") }

func TestRecoverMustBeDirectAndDoesNotResumePanicSite(t *testing.T) {
	after := false
	var caught any
	func() {
		defer func() { caught = recover() }()
		defer func() {
			if indirectRecover() != nil {
				t.Error("helper unexpectedly recovered")
			}
		}()
		controlledPanic()
		after = true
	}()
	if caught != "controlled" || after {
		t.Fatal("recover resumed the panic site or lost the panic")
	}
}

func TestSessionCleanupAlsoRunsDuringPanic(t *testing.T) {
	session := &testSession{}
	var caught any
	func() {
		defer func() { caught = recover() }()
		_ = runWithSession(context.Background(), Endpoint{},
			func(Endpoint) (ProbeSession, error) { return session, nil },
			func(context.Context, Endpoint, ProbeSession) error { panic("probe bug") },
		)
	}()
	if caught != "probe bug" || session.closeCalls != 1 {
		t.Fatalf("panic=%v closeCalls=%d", caught, session.closeCalls)
	}
}
