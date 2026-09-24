package mcpopstools

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

type mockActuator struct {
	mu           sync.Mutex
	restartedSvc []string
}

func (m *mockActuator) RestartService(ctx context.Context, serviceName string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.restartedSvc = append(m.restartedSvc, serviceName)
	return nil
}

func setupTestMCPServer(t *testing.T) (*OpsServer, *httptest.Server, *mockActuator) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"UP"}`))
	}))

	actuator := &mockActuator{}
	authorizer := &DefaultChangeAuthorizer{
		ApprovedTickets: map[string]string{
			"CHG-1001": "payment-service",
			"CHG-1002": "order-service",
		},
	}

	targets := []HealthTarget{
		{ID: "payment-health", ServiceName: "payment-service", URL: ts.URL},
		{ID: "order-health", ServiceName: "order-service", URL: ts.URL},
	}

	ops := NewOpsServer(ts.Client(), actuator, authorizer, targets)
	return ops, ts, actuator
}

func connectClientAndServer(
	t *testing.T, ctx context.Context, ops *OpsServer, callerRole Role,
) (*mcp.ClientSession, func()) {
	client := mcp.NewClient(&mcp.Implementation{Name: "test-client", Version: "v1.0.0"}, nil)

	t1, t2 := mcp.NewInMemoryTransports()
	serverSession, err := ops.MCPServer().Connect(ctx, t1, nil)
	if err != nil {
		t.Fatalf("server connect failed: %v", err)
	}

	clientSession, err := client.Connect(ctx, t2, nil)
	if err != nil {
		t.Fatalf("client connect failed: %v", err)
	}

	// Attach authenticated caller role to server session (MOCK_AUTH_BOUNDARY)
	ops.SetSessionRole(serverSession.ID(), callerRole)

	cleanup := func() {
		clientSession.Close()
		serverSession.Close()
	}
	return clientSession, cleanup
}

func TestMCPListTools(t *testing.T) {
	ctx := context.Background()
	ops, ts, _ := setupTestMCPServer(t)
	defer ts.Close()

	session, cleanup := connectClientAndServer(t, ctx, ops, RoleObserver)
	defer cleanup()

	listRes, err := session.ListTools(ctx, &mcp.ListToolsParams{})
	if err != nil {
		t.Fatalf("ListTools failed: %v", err)
	}

	if len(listRes.Tools) != 2 {
		t.Fatalf("expected 2 tools, got %d", len(listRes.Tools))
	}

	toolNames := make(map[string]bool)
	for _, tool := range listRes.Tools {
		toolNames[tool.Name] = true
	}

	if !toolNames["query_service_health"] || !toolNames["restart_service"] {
		t.Fatalf("missing expected tools: got %v", toolNames)
	}
}

func TestMCPQueryHealthRealHTTP(t *testing.T) {
	ctx := context.Background()
	ops, ts, _ := setupTestMCPServer(t)
	defer ts.Close()

	session, cleanup := connectClientAndServer(t, ctx, ops, RoleObserver)
	defer cleanup()

	callRes, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name: "query_service_health",
		Arguments: map[string]any{
			"target_id": "payment-health",
		},
	})
	if err != nil {
		t.Fatalf("CallTool failed: %v", err)
	}

	if callRes.IsError {
		t.Fatalf("expected success, got error tool call: %+v", callRes)
	}

	if len(callRes.Content) == 0 {
		t.Fatalf("expected content, got empty slice")
	}

	txt, ok := callRes.Content[0].(*mcp.TextContent)
	if !ok || !strings.Contains(txt.Text, "healthy: HTTP 200") {
		t.Fatalf("unexpected content output: %v", callRes.Content[0])
	}

	audits := ops.GetAuditRecords()
	if len(audits) != 1 {
		t.Fatalf("expected 1 audit record, got %d", len(audits))
	}
	if audits[0].Decision != "ALLOW" || audits[0].Caller != RoleObserver {
		t.Fatalf("unexpected audit entry: %+v", audits[0])
	}
}

func TestMCPSSRFDeniedForUnapprovedTarget(t *testing.T) {
	ctx := context.Background()
	ops, ts, _ := setupTestMCPServer(t)
	defer ts.Close()

	session, cleanup := connectClientAndServer(t, ctx, ops, RoleObserver)
	defer cleanup()

	callRes, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name: "query_service_health",
		Arguments: map[string]any{
			"target_id": "http://169.254.169.254/latest/meta-data",
		},
	})
	if err != nil {
		t.Fatalf("CallTool failed unexpectedly at transport level: %v", err)
	}

	if !callRes.IsError {
		t.Fatalf("expected tool error for SSRF target, got success: %+v", callRes)
	}

	txt, ok := callRes.Content[0].(*mcp.TextContent)
	if !ok || !strings.Contains(txt.Text, "blocked by SSRF allowlist policy") {
		t.Fatalf("unexpected error content: %v", callRes.Content[0])
	}

	audits := ops.GetAuditRecords()
	if len(audits) != 1 {
		t.Fatalf("expected 1 audit record, got %d", len(audits))
	}
	if audits[0].Decision != "DENY" {
		t.Fatalf("expected DENY in audit log, got %s", audits[0].Decision)
	}
}

func TestMCPOperatorRestartSuccess(t *testing.T) {
	ctx := context.Background()
	ops, ts, actuator := setupTestMCPServer(t)
	defer ts.Close()

	session, cleanup := connectClientAndServer(t, ctx, ops, RoleOperator)
	defer cleanup()

	callRes, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "payment-service",
			"change_ticket": "CHG-1001",
		},
	})
	if err != nil {
		t.Fatalf("CallTool transport error: %v", err)
	}

	if callRes.IsError {
		t.Fatalf("expected success, got tool error: %+v", callRes)
	}

	if len(actuator.restartedSvc) != 1 || actuator.restartedSvc[0] != "payment-service" {
		t.Fatalf("actuator did not record restart: %v", actuator.restartedSvc)
	}

	audits := ops.GetAuditRecords()
	if len(audits) != 1 || audits[0].Decision != "ALLOW" {
		t.Fatalf("expected ALLOW in audit log: %+v", audits)
	}
}

func TestMCPObserverMutatingActionDenied(t *testing.T) {
	ctx := context.Background()
	ops, ts, actuator := setupTestMCPServer(t)
	defer ts.Close()

	session, cleanup := connectClientAndServer(t, ctx, ops, RoleObserver)
	defer cleanup()

	callRes, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "payment-service",
			"change_ticket": "CHG-1001",
		},
	})
	if err != nil {
		t.Fatalf("CallTool transport error: %v", err)
	}

	if !callRes.IsError {
		t.Fatalf("expected permission denial for observer role, got success: %+v", callRes)
	}

	if len(actuator.restartedSvc) != 0 {
		t.Fatalf("actuator should not have been called on denial!")
	}

	audits := ops.GetAuditRecords()
	if len(audits) != 1 || audits[0].Decision != "DENY" {
		t.Fatalf("expected DENY in audit log: %+v", audits)
	}
}

func TestMCPMissingOrInvalidTicketDenied(t *testing.T) {
	ctx := context.Background()
	ops, ts, actuator := setupTestMCPServer(t)
	defer ts.Close()

	session, cleanup := connectClientAndServer(t, ctx, ops, RoleOperator)
	defer cleanup()

	// 1. Missing ticket
	callRes, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "payment-service",
			"change_ticket": "",
		},
	})
	if err != nil {
		t.Fatalf("CallTool transport error: %v", err)
	}
	if !callRes.IsError {
		t.Fatalf("expected error for empty ticket")
	}

	// 2. Unapproved ticket
	callRes2, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "payment-service",
			"change_ticket": "CHG-9999",
		},
	})
	if err != nil {
		t.Fatalf("CallTool transport error: %v", err)
	}
	if !callRes2.IsError {
		t.Fatalf("expected error for unapproved ticket")
	}

	if len(actuator.restartedSvc) != 0 {
		t.Fatalf("actuator should not have run")
	}
}
