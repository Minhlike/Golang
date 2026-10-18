package supplychain

import (
	"context"
	"fmt"
	"strings"
	"time"
)

// GoldenCatalog is trusted policy input, not a Dockerfile parser.
type GoldenCatalog map[string]string

func VerifyBaseImage(imageRef string, catalog GoldenCatalog) (bool, error) {
	parts := strings.Split(imageRef, "@")
	if len(parts) != 2 || parts[0] == "" {
		return false, fmt.Errorf("image must be pinned with digest: repo@sha256:hex")
	}
	repo, digest := parts[0], parts[1]
	if err := VerifyDigest(digest); err != nil {
		return false, err
	}
	expectedDigest, exists := catalog[repo]
	if !exists {
		return false, fmt.Errorf("untrusted base image repository: %s", repo)
	}
	if digest != expectedDigest {
		return false, fmt.Errorf("base image digest mismatch: expected %s, got %s", expectedDigest, digest)
	}
	return true, nil
}

// SafeRemoteVerify requires a callback that cooperates with cancellation.
// A context cannot preempt a callback that blocks forever.
func SafeRemoteVerify(ctx context.Context, verifyFunc func(context.Context) error) EvaluationResult {
	timeoutCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()
	if verifyFunc == nil {
		return deniedRemoteVerification(fmt.Errorf("no remote verifier configured"))
	}
	if err := timeoutCtx.Err(); err != nil {
		return deniedRemoteVerification(err)
	}
	err := verifyFunc(timeoutCtx)
	if err == nil {
		err = timeoutCtx.Err()
	}
	if err != nil {
		return deniedRemoteVerification(err)
	}
	return EvaluationResult{Decision: DecisionAllow}
}

func deniedRemoteVerification(err error) EvaluationResult {
	return EvaluationResult{
		Decision:   DecisionDeny,
		Violations: []string{fmt.Sprintf("fail-closed: aborted: %v", err)},
	}
}
