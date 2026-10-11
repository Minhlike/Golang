package fixed

import (
	"runtime"
	"sync"
	"sync/atomic"
	"testing"
	"testing/synctest"
)

func TestFieldLocksDoNotMakeAnInvariantSnapshot(t *testing.T) {
	var mu sync.Mutex
	balance, reserved := 100, 0
	firstRead, writeDone := make(chan struct{}), make(chan struct{})
	go func() {
		<-firstRead
		mu.Lock()
		balance, reserved = 60, 40
		mu.Unlock()
		close(writeDone)
	}()

	mu.Lock()
	oldBalance := balance
	mu.Unlock()
	close(firstRead)
	<-writeDone // Join the writer, and force the new version for the second read.
	mu.Lock()
	newReserved := reserved
	mu.Unlock()
	if got := oldBalance + newReserved; got != 140 {
		t.Fatalf("controlled mixed snapshot = %d, want 140", got)
	}
	mu.Lock()
	consistent := balance + reserved
	mu.Unlock()
	if consistent != 100 {
		t.Fatalf("single critical section lost invariant: %d", consistent)
	}
}

func TestAtomicFlagPublishesImmutablePayload(t *testing.T) {
	type payload struct{ completed, total int }
	var ready atomic.Bool
	var data payload
	readerStarted, done := make(chan struct{}), make(chan struct{})
	go func() {
		defer close(done)
		close(readerStarted)
		for !ready.Load() {
			runtime.Gosched() // Progress aid only; not a synchronization edge.
		}
		if data != (payload{3, 3}) {
			t.Errorf("partial payload: %+v", data)
		}
	}()
	<-readerStarted
	data = payload{3, 3}
	ready.Store(true)
	<-done
}

func TestCondNotificationDoesNotMakePredicateTrue(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		var mu sync.Mutex
		cond := sync.NewCond(&mu)
		ready := false
		done := make(chan struct{})
		go func() {
			defer close(done)
			mu.Lock()
			defer mu.Unlock()
			for !ready {
				cond.Wait()
			}
		}()
		synctest.Wait() // Waiter is durably blocked in Cond.Wait.
		cond.Signal()   // Deliberately do not change the protected predicate.
		synctest.Wait()
		select {
		case <-done:
			t.Fatal("notification was mistaken for a true predicate")
		default:
		}
		mu.Lock()
		ready = true
		cond.Broadcast()
		mu.Unlock()
		<-done
	})
}

func TestWaitGroupWaitsForRegisteredTasksNotTheirSuccess(t *testing.T) {
	var wg sync.WaitGroup
	var result error
	wg.Add(1)
	go func() {
		defer wg.Done()
		result = &taskFailure{}
	}()
	wg.Wait()
	if result == nil {
		t.Fatal("completed task should still carry its failure")
	}
}

type taskFailure struct{}

func (*taskFailure) Error() string { return "task failed" }

func TestRWMutexReadersCannotExcludeOtherReaders(t *testing.T) {
	var mu sync.RWMutex
	mu.RLock()
	entered, release, done := make(chan struct{}), make(chan struct{}), make(chan struct{})
	go func() {
		defer close(done)
		mu.RLock()
		close(entered)
		<-release
		mu.RUnlock()
	}()
	<-entered // A different goroutine can read while the first reader holds RLock.
	mu.RUnlock()
	close(release)
	<-done
	mu.Lock()
	mu.Unlock()
}
