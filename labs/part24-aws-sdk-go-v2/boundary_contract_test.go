package storage

import (
	"context"
	"errors"
	"sync/atomic"
	"testing"

	"github.com/aws/aws-sdk-go-v2/aws"
)

type controlledCredentialProvider struct {
	started, release chan struct{}
	calls            atomic.Int64
	contextCanceled  atomic.Bool
}

func (p *controlledCredentialProvider) Retrieve(ctx context.Context) (aws.Credentials, error) {
	if p.calls.Add(1) == 1 {
		close(p.started)
	}
	<-p.release
	p.contextCanceled.Store(ctx.Err() != nil)
	return aws.Credentials{AccessKeyID: "dummy", SecretAccessKey: "dummy", Source: "test-only"}, nil
}

func TestCacheCallerCancellationDoesNotCancelSharedRetrieval(t *testing.T) {
	p := &controlledCredentialProvider{started: make(chan struct{}), release: make(chan struct{})}
	cache := aws.NewCredentialsCache(p)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	first := make(chan error, 1)
	go func() { _, err := cache.Retrieve(ctx); first <- err }()
	<-p.started
	cancel()
	if err := <-first; !errors.Is(err, context.Canceled) {
		t.Fatalf("caller cancellation=%v", err)
	}
	// Provider is still blocked after the first caller has returned. Release it,
	// then join a second caller waiting for the same retrieval/cache result.
	second := make(chan error, 1)
	go func() { _, err := cache.Retrieve(context.Background()); second <- err }()
	close(p.release)
	if err := <-second; err != nil {
		t.Fatal(err)
	}
	if p.calls.Load() != 1 || p.contextCanceled.Load() {
		t.Fatalf("shared retrieval: calls=%d canceled=%v", p.calls.Load(), p.contextCanceled.Load())
	}
}
