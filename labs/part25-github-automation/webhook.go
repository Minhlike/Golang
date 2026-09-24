package automation

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"strings"
	"sync"
	"time"
)

var (
	ErrInvalidSignature = errors.New("invalid webhook signature")
	ErrMissingDelivery  = errors.New("missing X-GitHub-Delivery header")
	ErrDuplicateDelivery = errors.New("duplicate delivery ignored")
)

// VerifyHMACSHA256 validates the X-Hub-Signature-256 header using constant-time comparison
// to prevent side-channel timing attacks.
func VerifyHMACSHA256(payload []byte, signatureHeader string, secret []byte) bool {
	if !strings.HasPrefix(signatureHeader, "sha256=") {
		return false
	}
	actualHex := strings.TrimPrefix(signatureHeader, "sha256=")
	actualSig, err := hex.DecodeString(actualHex)
	if err != nil {
		return false
	}

	mac := hmac.New(sha256.New, secret)
	mac.Write(payload)
	expectedSig := mac.Sum(nil)

	return hmac.Equal(actualSig, expectedSig)
}

// WebhookReceiver processes GitHub Webhook events with signature verification
// and delivery ID deduplication for idempotency.
type WebhookReceiver struct {
	mu        sync.Mutex
	secret    []byte
	delivered map[string]time.Time
}

// NewWebhookReceiver creates a WebhookReceiver with the specified webhook secret.
func NewWebhookReceiver(secret string) *WebhookReceiver {
	return &WebhookReceiver{
		secret:    []byte(secret),
		delivered: make(map[string]time.Time),
	}
}

// Process validates and registers a webhook delivery event.
func (r *WebhookReceiver) Process(deliveryID, signature string, payload []byte) (isDuplicate bool, err error) {
	if deliveryID == "" {
		return false, ErrMissingDelivery
	}

	if !VerifyHMACSHA256(payload, signature, r.secret) {
		return false, ErrInvalidSignature
	}

	r.mu.Lock()
	defer r.mu.Unlock()

	// Check idempotency store
	if _, exists := r.delivered[deliveryID]; exists {
		return true, nil
	}

	r.delivered[deliveryID] = time.Now()
	return false, nil
}

// DeliveryCount returns the number of distinct deliveries processed.
func (r *WebhookReceiver) DeliveryCount() int {
	r.mu.Lock()
	defer r.mu.Unlock()
	return len(r.delivered)
}
