package mcpopstools

import (
	"context"
	"net/http"
	"net/http/httptest"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func TestUnknownRoleCannotAuthorizeChange(t *testing.T) {
	a := &DefaultChangeAuthorizer{ApprovedTickets: map[string]string{"ticket": "svc"}}
	for _, role := range []Role{"", "typo", RoleObserver} {
		if err := a.AuthorizeChange(context.Background(), role, "svc", "ticket"); err == nil {
			t.Fatalf("unknown/read-only role %q authorized mutation", role)
		}
	}
	for _, role := range []Role{RoleOperator, RoleAdmin} {
		if err := a.AuthorizeChange(context.Background(), role, "svc", "ticket"); err != nil {
			t.Fatal(err)
		}
	}
}

// The ID allowlist is not an egress policy: the approved URL can redirect.
// Both servers are owned local fixtures; this test contacts no other network.
func TestApprovedTargetRedirectIsNotEgressIsolation(t *testing.T) {
	var reached atomic.Int64
	destination := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		reached.Add(1)
		w.WriteHeader(http.StatusOK)
	}))
	defer destination.Close()
	origin := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, destination.URL, http.StatusFound)
	}))
	defer origin.Close()
	ops := NewOpsServer(origin.Client(), nil, nil, nil, []HealthTarget{{ID: "approved", URL: origin.URL, ServiceName: "fixture"}})
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	session, cleanup := connectClientAndServer(t, ctx, ops, RoleObserver)
	defer cleanup()
	result, err := session.CallTool(ctx, &mcp.CallToolParams{Name: "query_service_health", Arguments: map[string]any{"target_id": "approved"}})
	if err != nil || result.IsError || reached.Load() != 1 {
		t.Fatalf("redirect boundary: result=%v err=%v destination requests=%d", result, err, reached.Load())
	}
}

func TestApprovalDeadlineAndConcurrentClaim(t *testing.T) {
	manager := NewApprovalManager(time.Minute)
	now := time.Date(2026, 10, 12, 0, 0, 0, 0, time.UTC)
	manager.now = func() time.Time { return now }
	token, err := manager.RequestApproval("restart", "svc")
	if err != nil {
		t.Fatal(err)
	}
	now = now.Add(time.Minute)
	if manager.Confirm(token, "restart", "svc") {
		t.Fatal("accepted at expiry boundary")
	}
	token, err = manager.RequestApproval("restart", "svc")
	if err != nil {
		t.Fatal(err)
	}
	var claims atomic.Int64
	var joined sync.WaitGroup
	for i := 0; i < 20; i++ {
		joined.Add(1)
		go func() {
			defer joined.Done()
			if manager.Confirm(token, "restart", "svc") {
				claims.Add(1)
			}
		}()
	}
	joined.Wait()
	if claims.Load() != 1 {
		t.Fatalf("claims=%d, want 1", claims.Load())
	}
}
