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
	ErrInvalidSignature  = errors.New("invalid webhook signature")
	ErrMissingDelivery   = errors.New("missing X-GitHub-Delivery header")
	ErrDuplicateDelivery = errors.New("duplicate delivery ignored")
)

// DeliveryState tracks transport delivery separately from the business action
// it may trigger. A production implementation persists this state with a TTL
// and commits its completed state with the domain mutation.
type DeliveryState string

const (
	DeliveryProcessing DeliveryState = "processing"
	DeliveryCompleted  DeliveryState = "completed"
)

type DeliveryLedger struct {
	mu      sync.Mutex
	entries map[string]DeliveryState
}

func NewDeliveryLedger() *DeliveryLedger {
	return &DeliveryLedger{entries: make(map[string]DeliveryState)}
}

// Begin reserves one delivery. A failed attempt must call Fail so redelivery
// can retry; completion suppresses only that transport delivery, not an
// independently-defined business operation key.
func (l *DeliveryLedger) Begin(id string) (DeliveryState, bool) {
	l.mu.Lock()
	defer l.mu.Unlock()
	state, found := l.entries[id]
	if found {
		return state, false
	}
	l.entries[id] = DeliveryProcessing
	return DeliveryProcessing, true
}

func (l *DeliveryLedger) Complete(id string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.entries[id] == DeliveryProcessing {
		l.entries[id] = DeliveryCompleted
	}
}

func (l *DeliveryLedger) Fail(id string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.entries[id] == DeliveryProcessing {
		delete(l.entries, id)
	}
}

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
