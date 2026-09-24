package automation

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"net/http"
	"testing"
	"time"
)

// computeHMAC calculates standard GitHub sha256 signature for test payloads.
func computeHMAC(payload []byte, secret []byte) string {
	mac := hmac.New(sha256.New, secret)
	mac.Write(payload)
	return "sha256=" + hex.EncodeToString(mac.Sum(nil))
}

func TestWebhookHMACVerification(t *testing.T) {
	secret := []byte("super-secure-webhook-secret-token")
	payload := []byte(`{"action":"opened","pull_request":{"number":42}}`)

	validSig := computeHMAC(payload, secret)

	// Case 1: Valid signature passes
	if !VerifyHMACSHA256(payload, validSig, secret) {
		t.Errorf("expected valid signature to pass verification")
	}

	// Case 2: Tampered payload fails
	tamperedPayload := []byte(`{"action":"closed","pull_request":{"number":42}}`)
	if VerifyHMACSHA256(tamperedPayload, validSig, secret) {
		t.Errorf("expected tampered payload to fail verification")
	}

	// Case 3: Wrong secret fails
	wrongSecret := []byte("wrong-secret-token")
	if VerifyHMACSHA256(payload, validSig, wrongSecret) {
		t.Errorf("expected wrong secret to fail verification")
	}

	// Case 4: Invalid signature format fails
	if VerifyHMACSHA256(payload, "invalid-format", secret) {
		t.Errorf("expected malformed signature to fail verification")
	}
}

func TestWebhookDeliveryIdempotency(t *testing.T) {
	receiver := NewWebhookReceiver("test-webhook-secret")
	secret := []byte("test-webhook-secret")
	payload := []byte(`{"zen":"Design for failure"}`)
	sig := computeHMAC(payload, secret)

	deliveryID := "7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d"

	// First delivery: should process normally (not duplicate)
	isDuplicate, err := receiver.Process(deliveryID, sig, payload)
	if err != nil {
		t.Fatalf("first delivery failed: %v", err)
	}
	if isDuplicate {
		t.Errorf("expected first delivery to not be duplicate")
	}

	// Second delivery with identical ID: should be recognized as duplicate
	isDuplicate, err = receiver.Process(deliveryID, sig, payload)
	if err != nil {
		t.Fatalf("second delivery returned error: %v", err)
	}
	if !isDuplicate {
		t.Errorf("expected second delivery to be marked as duplicate")
	}

	// Verify count is 1
	if receiver.DeliveryCount() != 1 {
		t.Errorf("expected delivery count to be 1, got %d", receiver.DeliveryCount())
	}
}

func TestRateLimitParsingPrimaryAndSecondary(t *testing.T) {
	now := time.Date(2026, 9, 25, 0, 0, 0, 0, time.UTC)

	// Case 1: Primary rate limit exhausted
	h1 := make(http.Header)
	h1.Set("X-RateLimit-Limit", "5000")
	h1.Set("X-RateLimit-Remaining", "0")
	resetEpoch := now.Add(15 * time.Minute).Unix()
	h1.Set("X-RateLimit-Reset", string(rune(resetEpoch))) // format as string number
	h1.Set("X-RateLimit-Reset", "1790295300")              // epoch timestamp

	status1 := ParseRateLimit(h1, now)
	if !status1.IsExhausted {
		t.Errorf("expected status1 to be exhausted")
	}
	if status1.Limit != 5000 || status1.Remaining != 0 {
		t.Errorf("expected limit 5000 and remaining 0, got %d and %d", status1.Limit, status1.Remaining)
	}

	// Case 2: Secondary rate limit (Abuse triggered Retry-After)
	h2 := make(http.Header)
	h2.Set("Retry-After", "120")
	status2 := ParseRateLimit(h2, now)
	if !status2.IsExhausted {
		t.Errorf("expected status2 to be exhausted due to Retry-After")
	}
	if status2.RetryAfter != 120*time.Second {
		t.Errorf("expected 120s retry-after, got %v", status2.RetryAfter)
	}
}

func TestInMemGitCommitAndHead(t *testing.T) {
	repo, err := NewInMemGitRepository()
	if err != nil {
		t.Fatalf("failed to create in-mem git repo: %v", err)
	}

	// Commit 1: Add initial config
	fileContent := []byte("version: 1\nenvironment: production\n")
	hash1, err := repo.WriteFileAndCommit("config.yaml", fileContent, "deploy-bot", "feat: initial configuration")
	if err != nil {
		t.Fatalf("commit 1 failed: %v", err)
	}
	if hash1 == "" {
		t.Errorf("expected non-empty commit hash")
	}

	headHash, err := repo.GetHeadCommitHash()
	if err != nil {
		t.Fatalf("failed to get head: %v", err)
	}
	if headHash != hash1 {
		t.Errorf("expected HEAD to match commit 1 hash, got %s vs %s", headHash, hash1)
	}

	// Commit 2: Update config
	updatedContent := []byte("version: 2\nenvironment: production\nreplicas: 5\n")
	hash2, err := repo.WriteFileAndCommit("config.yaml", updatedContent, "deploy-bot", "fix: scale replicas to 5")
	if err != nil {
		t.Fatalf("commit 2 failed: %v", err)
	}
	if hash2 == hash1 {
		t.Errorf("expected new commit hash for commit 2")
	}

	headHash2, err := repo.GetHeadCommitHash()
	if err != nil {
		t.Fatalf("failed to get head 2: %v", err)
	}
	if headHash2 != hash2 {
		t.Errorf("expected HEAD to advance to commit 2 hash")
	}
}
