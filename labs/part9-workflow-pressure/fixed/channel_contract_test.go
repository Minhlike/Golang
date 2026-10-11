package fixed

import (
	"context"
	"testing"
	"testing/synctest"
)

func TestBufferedAdmissionIsNotCompletion(t *testing.T) {
	jobs := make(chan int, 1)
	jobs <- 7 // Completes without any receiver or worker.
	if len(jobs) != 1 {
		t.Fatal("admitted value missing")
	}
	if got := <-jobs; got != 7 {
		t.Fatal("wrong admitted value")
	}
}

func TestFullBufferNeedsAReceive(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		jobs := make(chan int, 1)
		jobs <- 1
		done := make(chan struct{})
		go func() { jobs <- 2; close(done) }()
		synctest.Wait() // Sender is durably blocked: no scheduling guess.
		select {
		case <-done:
			t.Fatal("send completed while buffer was full")
		default:
		}
		if <-jobs != 1 {
			t.Fatal("buffer order changed")
		}
		<-done
		if <-jobs != 2 {
			t.Fatal("second value missing")
		}
	})
}

func TestUnbufferedReceivePublishesBeforeSendReturns(t *testing.T) {
	ch := make(chan struct{})
	var result int
	done := make(chan struct{})
	go func() { result = 42; <-ch; close(done) }()
	ch <- struct{}{}
	if result != 42 { // Safe because receive synchronizes before send completes.
		t.Fatal("publication failed")
	}
	<-done
}

func TestClosedChannelDrainsSentZeroBeforeClosedZero(t *testing.T) {
	ch := make(chan int, 1)
	ch <- 0
	close(ch)
	if value, ok := <-ch; value != 0 || !ok {
		t.Fatal("sent zero mistaken for closed receive")
	}
	if value, ok := <-ch; value != 0 || ok {
		t.Fatal("closed receive contract")
	}
}

func TestClosingAChannelDoesNotSafelyCancelBlockedSend(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		ch := make(chan int)
		done := make(chan bool)
		go func() {
			defer func() { done <- recover() != nil }()
			ch <- 1
		}()
		synctest.Wait()
		close(ch) // Wait establishes order for this deliberately invalid send.
		if !<-done {
			t.Fatal("blocked send did not panic on close")
		}
	})
}

func TestCancelIsNotJoinForNoncooperativeWork(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		ctx, cancel := context.WithCancel(context.Background())
		defer cancel()
		entered, release := make(chan struct{}), make(chan struct{})
		defer func() {
			select {
			case <-release:
			default:
				close(release)
			}
		}()
		out := Run(ctx, []Job{{"job"}}, 1, func(context.Context, Job) error {
			close(entered)
			<-release
			return nil
		})
		<-entered
		cancel()
		synctest.Wait()
		select {
		case <-out:
			t.Fatal("output closed while owned Work was still running")
		default:
		}
		close(release)
		if _, ok := <-out; ok {
			t.Fatal("result must be dropped after observed cancellation")
		}
	})
}
