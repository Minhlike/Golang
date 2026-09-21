package fixed

import (
	"net/http/httptrace"
	"sync"
	"testing"
)

func TestTraceRecorderKeepsNamedStages(t *testing.T) {
	recorder := NewTraceRecorder()
	trace := recorder.ClientTrace()
	trace.DNSStart(httptrace.DNSStartInfo{Host: "api.test"})
	trace.GotConn(httptrace.GotConnInfo{Reused: true})
	trace.GotFirstResponseByte()

	got := recorder.Snapshot()
	want := []TraceEvent{
		{Name: "dns start"},
		{Name: "connection reused=true"},
		{Name: "first response byte"},
	}
	if len(got) != len(want) {
		t.Fatalf("event count = %d, want %d: %#v", len(got), len(want), got)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("event %d = %#v, want %#v", i, got[i], want[i])
		}
	}

	got[0] = TraceEvent{Name: "mutated by caller"}
	if again := recorder.Snapshot()[0].Name; again != "dns start" {
		t.Fatalf("Snapshot shared recorder storage: %q", again)
	}
}

func TestTraceRecorderAcceptsConcurrentHooks(t *testing.T) {
	recorder := NewTraceRecorder()
	trace := recorder.ClientTrace()

	const workers = 64
	var wg sync.WaitGroup
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func(reused bool) {
			defer wg.Done()
			trace.GotConn(httptrace.GotConnInfo{Reused: reused})
		}(i%2 == 0)
	}
	wg.Wait()

	if got := len(recorder.Snapshot()); got != workers {
		t.Fatalf("event count = %d, want %d", got, workers)
	}
}
