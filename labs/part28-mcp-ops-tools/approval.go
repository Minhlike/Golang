package mcpopstools

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"sync"
	"time"
)

// ApprovalManager models a human approval boundary. It binds a secret token to
// the exact operation and target, expires it, and consumes it on confirmation.
// It is process-local teaching code; a replicated service needs durable,
// transactional storage and a separately authenticated human approver.
type ApprovalManager struct {
	mu       sync.Mutex
	pending  map[string]PendingApproval
	now      func() time.Time
	random   func([]byte) (int, error)
	tokenTTL time.Duration
}

type PendingApproval struct {
	Action    string
	Target    string
	ExpiresAt time.Time
}

func NewApprovalManager(tokenTTL time.Duration) *ApprovalManager {
	if tokenTTL <= 0 {
		tokenTTL = 5 * time.Minute
	}
	return &ApprovalManager{
		pending:  make(map[string]PendingApproval),
		now:      time.Now,
		random:   rand.Read,
		tokenTTL: tokenTTL,
	}
}

func (m *ApprovalManager) RequestApproval(action, target string) (string, error) {
	if action == "" || target == "" {
		return "", errors.New("approval action and target are required")
	}
	bytes := make([]byte, 32)
	if _, err := m.random(bytes); err != nil {
		return "", errors.New("generate approval token: " + err.Error())
	}
	token := base64.RawURLEncoding.EncodeToString(bytes)
	m.mu.Lock()
	defer m.mu.Unlock()
	m.pending[token] = PendingApproval{
		Action: action, Target: target, ExpiresAt: m.now().Add(m.tokenTTL),
	}
	return token, nil
}

// Confirm consumes a token only when it still authorizes this exact action and
// target. A token cannot be replayed, including after a mismatched attempt.
func (m *ApprovalManager) Confirm(token, action, target string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()
	pending, found := m.pending[token]
	if found {
		delete(m.pending, token)
	}
	return found && m.now().Before(pending.ExpiresAt) &&
		pending.Action == action && pending.Target == target
}
