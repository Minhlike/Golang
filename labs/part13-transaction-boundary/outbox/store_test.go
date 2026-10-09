package outbox

import (
	"context"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"testing"
	"time"
)

func openTest(t *testing.T, path string) *Store {
	t.Helper()
	s, err := Open(context.Background(), path)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := s.Close(); err != nil {
			t.Error(err)
		}
	})
	return s
}

func snapshot(t *testing.T, s *Store) Snapshot {
	t.Helper()
	v, err := s.Snapshot(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	return v
}

// Child exits without defers: this is process death, not a returned error.
func TestCrashChild(t *testing.T) {
	if os.Getenv("OUTBOX_CHILD") != "1" {
		return
	}
	ctx := context.Background()
	s, err := Open(ctx, os.Getenv("OUTBOX_DB"))
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	checkpoint := func(name string) {
		if name == os.Getenv("OUTBOX_AT") {
			os.Exit(77)
		}
	}
	e := Event{Key: "credit-001", Delta: 7}
	switch os.Getenv("OUTBOX_ACTION") {
	case "apply":
		if os.Getenv("OUTBOX_BROKEN") == "1" {
			err = s.BrokenApply(ctx, e, checkpoint)
		} else {
			err = s.Apply(ctx, e, checkpoint)
		}
	case "deliver":
		r, openErr := Open(ctx, os.Getenv("OUTBOX_RECEIVER"))
		if openErr != nil {
			t.Fatal(openErr)
		}
		defer r.Close()
		_, err = s.DeliverOne(ctx, r.Receive, checkpoint)
	default:
		t.Fatal("unknown child action")
	}
	if err != nil {
		t.Fatal(err)
	}
}

func child(t *testing.T, db, receiver, action, at string, broken bool) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	c := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestCrashChild$", "-test.v")
	c.Env = append(os.Environ(), "OUTBOX_CHILD=1", "OUTBOX_DB="+db,
		"OUTBOX_RECEIVER="+receiver, "OUTBOX_ACTION="+action, "OUTBOX_AT="+at,
		"OUTBOX_BROKEN="+map[bool]string{true: "1", false: "0"}[broken])
	out, err := c.CombinedOutput()
	want := 0
	if at != "" {
		want = 77
	}
	got := 0
	if err != nil {
		var e *exec.ExitError
		if !errors.As(err, &e) {
			t.Fatalf("child: %v: %s", err, out)
		}
		got = e.ExitCode()
	}
	if got != want {
		t.Fatalf("child exit=%d want=%d: %s", got, want, out)
	}
	t.Logf("REAL_LOCAL_VERIFIED child action=%s checkpoint=%s exit=%d", action, at, got)
}

func TestRecoveryWindows(t *testing.T) {
	for _, at := range []string{"before_commit", "after_commit", "after_send"} {
		t.Run(at, func(t *testing.T) {
			dir := t.TempDir()
			db, rx := filepath.Join(dir, "sender.db"), filepath.Join(dir, "receiver.db")
			if at == "after_send" {
				child(t, db, rx, "apply", "", false)
				child(t, db, rx, "deliver", at, false)
			} else {
				child(t, db, rx, "apply", at, false)
			}
			s := openTest(t, db)
			before := snapshot(t, s)
			want := Snapshot{Total: 7, Pending: 1, Operations: 1}
			if at == "before_commit" {
				want = Snapshot{}
			}
			if before != want {
				t.Fatalf("after crash=%+v want=%+v", before, want)
			}
			if err := s.Apply(context.Background(), Event{"credit-001", 7}, nil); err != nil {
				t.Fatal(err)
			}
			if err := s.Apply(context.Background(), Event{"credit-001", 8}, nil); !errors.Is(err, ErrConflict) {
				t.Fatalf("conflict=%v", err)
			}
			// All connections close before a NEW dispatcher process starts.
			if err := s.Close(); err != nil {
				t.Fatal(err)
			}
			child(t, db, rx, "deliver", "", false)
			s2, r2 := openTest(t, db), openTest(t, rx)
			if v := snapshot(t, s2); v != (Snapshot{Total: 7, Completed: 1, Operations: 1}) {
				t.Fatalf("sender=%+v", v)
			}
			if v := snapshot(t, r2); v.Total != 7 || v.Received != 1 {
				t.Fatalf("receiver=%+v", v)
			}
			t.Logf("reopened sender=%+v receiver=%+v", snapshot(t, s2), snapshot(t, r2))
		})
	}
}

func TestConcurrentIdentity(t *testing.T) {
	p := filepath.Join(t.TempDir(), "shared.db")
	a, b := openTest(t, p), openTest(t, p)
	start := make(chan struct{})
	errs := make(chan error, 2)
	var wg sync.WaitGroup
	for _, s := range []*Store{a, b} {
		wg.Add(1)
		go func(s *Store) { defer wg.Done(); <-start; errs <- s.Apply(context.Background(), Event{"same", 7}, nil) }(s)
	}
	close(start)
	wg.Wait()
	close(errs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	if v := snapshot(t, a); v != (Snapshot{Total: 7, Pending: 1, Operations: 1}) {
		t.Fatalf("duplicate=%+v", v)
	}
}

func TestSendRetryAndReceiverConflict(t *testing.T) {
	s, r := openTest(t, filepath.Join(t.TempDir(), "s.db")), openTest(t, filepath.Join(t.TempDir(), "r.db"))
	ctx := context.Background()
	if err := s.Apply(ctx, Event{"x", 7}, nil); err != nil {
		t.Fatal(err)
	}
	boom := errors.New("ack lost after receiver committed")
	attempts := 0
	send := func(ctx context.Context, e Event) error {
		attempts++
		if err := r.Receive(ctx, e); err != nil {
			return err
		}
		if attempts == 1 {
			return boom
		}
		return nil
	}
	if ok, err := s.DeliverOne(ctx, send, nil); ok || !errors.Is(err, boom) {
		t.Fatalf("first=%v %v", ok, err)
	}
	if snapshot(t, s).Pending != 1 {
		t.Fatal("ambiguous send lost")
	}
	if ok, err := s.DeliverOne(ctx, send, nil); !ok || err != nil {
		t.Fatalf("retry=%v %v", ok, err)
	}
	if attempts != 2 || snapshot(t, r).Total != 7 {
		t.Fatal("receiver effect repeated")
	}
	if err := r.Receive(ctx, Event{"x", 8}); !errors.Is(err, ErrConflict) {
		t.Fatalf("receiver conflict=%v", err)
	}
	if ok, err := s.DeliverOne(ctx, send, nil); ok || err != nil {
		t.Fatalf("empty=%v %v", ok, err)
	}
	t.Logf("send attempts=%d receiver effects=%d", attempts, snapshot(t, r).Received)
}

// Same oracle, opt-in broken implementation: this command MUST fail.
func TestOutboxContract(t *testing.T) {
	db, rx := filepath.Join(t.TempDir(), "s.db"), filepath.Join(t.TempDir(), "r.db")
	broken := os.Getenv("RELIABILITY_MUTANT") == "split_commit"
	child(t, db, rx, "apply", "after_commit", broken)
	v := snapshot(t, openTest(t, db))
	if v.Total != 7 || v.Pending != 1 {
		t.Fatalf("committed business requires pending event: %+v", v)
	}
}
