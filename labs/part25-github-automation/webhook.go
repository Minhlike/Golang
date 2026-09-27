package automation

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"strings"
	"sync"
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

// CompletedCount reports completed transport deliveries only. It deliberately
// excludes attempts still processing or released after a handler failure.
func (l *DeliveryLedger) CompletedCount() int {
	l.mu.Lock()
	defer l.mu.Unlock()
	count := 0
	for _, state := range l.entries {
		if state == DeliveryCompleted {
			count++
		}
	}
	return count
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

// WebhookReceiver verifies a delivery before driving its business handler.
// A completed delivery is recorded only after that handler succeeds.
type WebhookReceiver struct {
	secret []byte
	ledger *DeliveryLedger
}

// NewWebhookReceiver creates a WebhookReceiver with the specified webhook secret.
func NewWebhookReceiver(secret string) *WebhookReceiver {
	return &WebhookReceiver{
		secret: []byte(secret),
		ledger: NewDeliveryLedger(),
	}
}

// Process verifies and reserves a delivery, runs handle, and marks it complete
// only after the domain mutation succeeds. A duplicate is never handed to the
// handler. Production requires an equivalent durable transaction/lease.
func (r *WebhookReceiver) Process(
	deliveryID, signature string,
	payload []byte,
	handle func() error,
) (isDuplicate bool, err error) {
	if deliveryID == "" {
		return false, ErrMissingDelivery
	}

	if !VerifyHMACSHA256(payload, signature, r.secret) {
		return false, ErrInvalidSignature
	}
	if handle == nil {
		return false, errors.New("webhook handler is required")
	}
	if _, accepted := r.ledger.Begin(deliveryID); !accepted {
		return true, nil
	}
	if err := handle(); err != nil {
		r.ledger.Fail(deliveryID)
		return false, err
	}
	r.ledger.Complete(deliveryID)
	return false, nil
}

// DeliveryCount returns the number of distinct deliveries processed.
func (r *WebhookReceiver) DeliveryCount() int {
	return r.ledger.CompletedCount()
}
