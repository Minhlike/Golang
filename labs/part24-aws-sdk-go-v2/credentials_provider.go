package storage

import (
	"context"
	"fmt"
	"sync/atomic"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
)

// DynamicCredentialProvider simulates an IAM Role / STS AssumeRole credential provider
// that dispenses temporary credentials with an expiration timestamp.
type DynamicCredentialProvider struct {
	retrieveCount atomic.Int64
	ttl           time.Duration
	roleArn       string
}

// NewDynamicCredentialProvider returns a provider simulating STS temporary session tokens.
func NewDynamicCredentialProvider(roleArn string, ttl time.Duration) *DynamicCredentialProvider {
	return &DynamicCredentialProvider{
		ttl:     ttl,
		roleArn: roleArn,
	}
}

// Retrieve dispenses temporary credentials with a defined expiration time.
func (p *DynamicCredentialProvider) Retrieve(ctx context.Context) (aws.Credentials, error) {
	select {
	case <-ctx.Done():
		return aws.Credentials{}, ctx.Err()
	default:
	}

	count := p.retrieveCount.Add(1)
	now := time.Now()

	return aws.Credentials{
		AccessKeyID:     fmt.Sprintf("ASIA-TEMP-KEY-%d", count),
		SecretAccessKey: fmt.Sprintf("SECRET-TOKEN-%d", count),
		SessionToken:    fmt.Sprintf("SESSION-TOKEN-%d", count),
		Source:          "DynamicCredentialProvider",
		CanExpire:       true,
		Expires:         now.Add(p.ttl),
	}, nil
}

// RetrieveCount returns how many times Retrieve was called (used to verify automatic refresh).
func (p *DynamicCredentialProvider) RetrieveCount() int64 {
	return p.retrieveCount.Load()
}
