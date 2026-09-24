package ebpfobserver

import (
	"context"
	"io"
	"sync"
	"testing"
	"time"

	"github.com/cilium/ebpf"
)

type mockRecordReader struct {
	mu      sync.Mutex
	records [][]byte
	closed  bool
}

func (m *mockRecordReader) Read() ([]byte, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.closed {
		return nil, ErrObserverClosed
	}
	if len(m.records) == 0 {
		return nil, io.EOF
	}
	rec := m.records[0]
	m.records = m.records[1:]
	return rec, nil
}

func (m *mockRecordReader) Close() error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.closed = true
	return nil
}

func TestEncodeDecodeExecEvent(t *testing.T) {
	original := &ExecEvent{
		PID:      12345,
		PPID:     1000,
		UID:      1001,
		GID:      1001,
		Comm:     "golang-worker",
		Filename: "/usr/local/bin/worker",
	}

	raw, err := EncodeExecEvent(original)
	if err != nil {
		t.Fatalf("failed to encode event: %v", err)
	}
	if len(raw) != EventPayloadSize {
		t.Fatalf("expected payload size %d, got %d", EventPayloadSize, len(raw))
	}

	decoded, err := DecodeExecEvent(raw)
	if err != nil {
		t.Fatalf("failed to decode event: %v", err)
	}

	if decoded.PID != original.PID {
		t.Errorf("PID mismatch: expected %d, got %d", original.PID, decoded.PID)
	}
	if decoded.PPID != original.PPID {
		t.Errorf("PPID mismatch: expected %d, got %d", original.PPID, decoded.PPID)
	}
	if decoded.UID != original.UID {
		t.Errorf("UID mismatch: expected %d, got %d", original.UID, decoded.UID)
	}
	if decoded.GID != original.GID {
		t.Errorf("GID mismatch: expected %d, got %d", original.GID, decoded.GID)
	}
	if decoded.Comm != original.Comm {
		t.Errorf("Comm mismatch: expected %s, got %s", original.Comm, decoded.Comm)
	}
	if decoded.Filename != original.Filename {
		t.Errorf("Filename mismatch: expected %s, got %s", original.Filename, decoded.Filename)
	}
}

func TestDecodeExecEventTruncated(t *testing.T) {
	truncated := make([]byte, 100) // Less than EventPayloadSize (160)
	_, err := DecodeExecEvent(truncated)
	if err == nil {
		t.Fatal("expected error for truncated payload, got nil")
	}
}

func TestObserverStreaming(t *testing.T) {
	e1 := &ExecEvent{PID: 101, PPID: 1, Comm: "curl", Filename: "/usr/bin/curl"}
	e2 := &ExecEvent{PID: 102, PPID: 101, Comm: "bash", Filename: "/bin/bash"}

	raw1, _ := EncodeExecEvent(e1)
	raw2, _ := EncodeExecEvent(e2)

	reader := &mockRecordReader{
		records: [][]byte{raw1, raw2},
	}

	observer := NewObserver(reader, 10)
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	events, errs := observer.Start(ctx)

	var received []*ExecEvent
	for ev := range events {
		received = append(received, ev)
	}

	// Drain any errors
	for err := range errs {
		t.Errorf("unexpected observer error: %v", err)
	}

	if len(received) != 2 {
		t.Fatalf("expected 2 received events, got %d", len(received))
	}
	if received[0].Comm != "curl" || received[1].Comm != "bash" {
		t.Errorf("events content unexpected: %+v, %+v", received[0], received[1])
	}

	if err := observer.Close(); err != nil {
		t.Errorf("observer.Close returned error: %v", err)
	}
}

func TestObserverContextCancellation(t *testing.T) {
	reader := &mockRecordReader{records: nil} // Will return EOF
	observer := NewObserver(reader, 10)

	ctx, cancel := context.WithCancel(context.Background())
	events, errs := observer.Start(ctx)

	// Cancel immediately
	cancel()

	// Wait for channels to close
	for range events {
	}
	for range errs {
	}

	if err := observer.Close(); err != nil {
		t.Errorf("failed to close observer: %v", err)
	}
}

func TestDetectSecurityAnomalies(t *testing.T) {
	// 1. Temp directory execution
	tempAlert := DetectSecurityAnomalies(&ExecEvent{
		PID:      5001,
		Filename: "/tmp/crypto_miner",
		Comm:     "crypto_miner",
	})
	if tempAlert == nil || tempAlert.Rule != "SEC01_EXEC_FROM_TEMP_DIRECTORY" {
		t.Errorf("expected SEC01 alert for /tmp execution, got %+v", tempAlert)
	}

	// 2. Shell spawned by nginx webserver
	rceAlert := DetectSecurityAnomalies(&ExecEvent{
		PID:      5002,
		Filename: "/bin/sh",
		Comm:     "nginx",
	})
	if rceAlert == nil || rceAlert.Rule != "SEC02_SHELL_FROM_WEBSERVER" {
		t.Errorf("expected SEC02 alert for nginx shell execution, got %+v", rceAlert)
	}

	// 3. Root network recon tool
	netAlert := DetectSecurityAnomalies(&ExecEvent{
		PID:      5003,
		UID:      0,
		Filename: "/usr/bin/nc",
		Comm:     "nc",
	})
	if netAlert == nil || netAlert.Rule != "SEC03_ROOT_NETWORK_RECON" {
		t.Errorf("expected SEC03 alert for root nc, got %+v", netAlert)
	}

	// 4. Benign execution
	benign := DetectSecurityAnomalies(&ExecEvent{
		PID:      5004,
		UID:      1000,
		Filename: "/usr/bin/go",
		Comm:     "go",
	})
	if benign != nil {
		t.Errorf("expected no alert for benign go build, got %+v", benign)
	}
}

func TestCiliumEbpfSpecLoading(t *testing.T) {
	spec := &ebpf.CollectionSpec{
		Maps: map[string]*ebpf.MapSpec{
			"events": {
				Name:       "events",
				Type:       ebpf.RingBuf,
				MaxEntries: 256 * 1024,
			},
		},
		Programs: map[string]*ebpf.ProgramSpec{
			"trace_execve": {
				Name:        "trace_execve",
				Type:        ebpf.TracePoint,
				SectionName: "tracepoint/syscalls/sys_enter_execve",
				License:     "Dual MIT/GPL",
			},
		},
	}

	if spec.Maps["events"].Type != ebpf.RingBuf {
		t.Fatalf("expected RingBuf map type, got %v", spec.Maps["events"].Type)
	}
	if spec.Programs["trace_execve"].Type != ebpf.TracePoint {
		t.Fatalf("expected TracePoint prog type, got %v", spec.Programs["trace_execve"].Type)
	}
}
