package contracts

import (
	"context"
	"os"
	"os/exec"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestPublicationOnceDoesNotPreventSendAfterClose(t *testing.T) {
	ch := make(chan int)
	var once sync.Once
	once.Do(func() { close(ch) })
	once.Do(func() { close(ch) })
	panicked := false
	func() {
		defer func() { panicked = recover() != nil }()
		ch <- 1
	}()
	if !panicked {
		t.Fatal("Once does not coordinate later sends")
	}
}

func TestPublicationUnlockedMutexIsFatal(t *testing.T) {
	if os.Getenv("GOLANG_PUBLICATION_MUTEX_CHILD") == "1" {
		defer func() {
			if recover() != nil {
				os.Exit(0)
			}
		}()
		var mu sync.Mutex
		mu.Unlock()
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestPublicationUnlockedMutexIsFatal$")
	cmd.Env = append(os.Environ(), "GOLANG_PUBLICATION_MUTEX_CHILD=1")
	output, err := cmd.CombinedOutput()
	if ctx.Err() != nil {
		t.Fatal(ctx.Err())
	}
	if err == nil || !strings.Contains(string(output), "fatal error: sync: unlock of unlocked mutex") {
		t.Fatalf("expected unrecoverable mutex diagnostic; err=%v output=%s", err, output)
	}
}

type publicationValueReceiver struct{}

func (publicationValueReceiver) Summary() string { return "value" }

type publicationPointerReceiver struct{}

func (p *publicationPointerReceiver) Summary() string {
	if p == nil {
		return "absent"
	}
	return "present"
}

func TestPublicationTypedNilReceiver(t *testing.T) {
	var valuePointer *publicationValueReceiver
	var valueInterface interface{ Summary() string } = valuePointer
	if valueInterface == nil {
		t.Fatal("typed nil lost its dynamic type")
	}
	panicked := false
	func() {
		defer func() { panicked = recover() != nil }()
		_ = valueInterface.Summary()
	}()
	if !panicked {
		t.Fatal("nil pointer cannot provide a value receiver")
	}
	var pointer *publicationPointerReceiver
	var pointerInterface interface{ Summary() string } = pointer
	if pointerInterface == nil || pointerInterface.Summary() != "absent" {
		t.Fatal("explicit nil-aware pointer receiver contract failed")
	}
}

// These checks observe language behavior, not generated copy instructions.
func TestPublicationCallValues(t *testing.T) {
	pair := func() (int, string) { return 7, "seven" }
	n, label := pair()
	if n != 7 || label != "seven" {
		t.Fatal("multiple results lost")
	}
	original := 100
	increment := func(value int) int {
		value += 20
		return value
	}
	if increment(original) != 120 || original != 100 {
		t.Fatal("parameter assignment changed caller variable")
	}
	var nilFunction func() int
	recovered := false
	reachedAfterCall := false
	func() {
		defer func() { recovered = recover() != nil }()
		_ = nilFunction()
		reachedAfterCall = true
	}()
	if !recovered || reachedAfterCall {
		t.Fatal("expression evaluation did not interrupt control flow")
	}
}

func TestPublicationAppendCapacity(t *testing.T) {
	spare := make([]int, 2, 4)
	spare[0], spare[1] = 10, 20
	same := append(spare, 30)
	same[0] = 99
	if spare[0] != 99 || &spare[0] != &same[0] {
		t.Fatal("sufficient capacity must reuse underlying array")
	}
	full := []int{10, 20}
	grown := append(full, 30)
	grown[0] = 99
	if full[0] != 10 || grown[0] != 99 || len(grown) != 3 {
		t.Fatal("insufficient capacity must preserve old underlying array")
	}
}
