package fixed

import (
	"fmt"
	"net/http/httptrace"
	"sync"
)

// TraceEvent is one stage observed by an HTTP client trace.
type TraceEvent struct {
	Name string
}

// TraceRecorder collects events from ClientTrace hooks safely.
type TraceRecorder struct {
	mu     sync.Mutex
	events []TraceEvent
}

// NewTraceRecorder creates an empty recorder for one round trip.
func NewTraceRecorder() *TraceRecorder {
	return &TraceRecorder{}
}

// ClientTrace returns hooks that record a small set of useful request stages.
func (r *TraceRecorder) ClientTrace() *httptrace.ClientTrace {
	return &httptrace.ClientTrace{
		DNSStart: func(httptrace.DNSStartInfo) {
			r.record("dns start")
		},
		GotConn: func(info httptrace.GotConnInfo) {
			r.record(fmt.Sprintf("connection reused=%t", info.Reused))
		},
		GotFirstResponseByte: func() {
			r.record("first response byte")
		},
	}
}

// Snapshot returns events collected so far without sharing recorder storage.
func (r *TraceRecorder) Snapshot() []TraceEvent {
	r.mu.Lock()
	defer r.mu.Unlock()

	events := make([]TraceEvent, len(r.events))
	copy(events, r.events)
	return events
}

func (r *TraceRecorder) record(name string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.events = append(r.events, TraceEvent{Name: name})
}
