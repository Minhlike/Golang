package mcpopstools

import (
	"context"
	"testing"
)

func TestMCPListTools(t *testing.T) {
	server := NewMCPServer()
	tools := server.ListTools()

	if len(tools) != 2 {
		t.Fatalf("expected 2 registered tools, got %d", len(tools))
	}

	foundHealth := false
	for _, tool := range tools {
		if tool.Name == "query_service_health" {
			foundHealth = true
			if tool.InputSchema["type"] != "object" {
				t.Errorf("expected object type schema for query_service_health")
			}
		}
	}
	if !foundHealth {
		t.Errorf("missing query_service_health tool in tools list")
	}
}

func TestMCPOperatorQueryHealthSuccess(t *testing.T) {
	server := NewMCPServer()
	ctx := context.Background()

	params := &CallToolParams{
		Name: "query_service_health",
		Arguments: map[string]any{
			"target_url": "https://api.example.com/healthz",
		},
	}

	res, err := server.ExecuteToolCall(ctx, RoleObserver, params)
	if err != nil {
		t.Fatalf("unexpected execution error: %v", err)
	}
	if res.IsError {
		t.Fatalf("expected success, got error: %s", res.Content[0].Text)
	}

	logs := server.GetAuditLog()
	if len(logs) != 1 || !logs[0].Allowed {
		t.Errorf("audit log mismatch: %+v", logs)
	}
}

func TestMCPSSRFPrevention(t *testing.T) {
	server := NewMCPServer()
	ctx := context.Background()

	dangerousTargets := []string{
		"http://169.254.169.254/latest/meta-data/iam/security-credentials/",
		"http://localhost:8080/admin",
		"http://127.0.0.1:9090/metrics",
		"http://10.0.1.5:8000/internal",
	}

	for _, target := range dangerousTargets {
		params := &CallToolParams{
			Name: "query_service_health",
			Arguments: map[string]any{
				"target_url": target,
			},
		}

		res, err := server.ExecuteToolCall(ctx, RoleOperator, params)
		if err != nil {
			t.Fatalf("unexpected call error: %v", err)
		}
		if !res.IsError {
			t.Errorf("expected SSRF block for %s, but call was permitted!", target)
		}
	}

	logs := server.GetAuditLog()
	if len(logs) != len(dangerousTargets) {
		t.Errorf("expected %d audit entries, got %d", len(dangerousTargets), len(logs))
	}
	for _, l := range logs {
		if l.Allowed {
			t.Errorf("expected all dangerous targets to be blocked in audit log")
		}
	}
}

func TestMCPAuthorizationBoundaryObserverDenied(t *testing.T) {
	server := NewMCPServer()
	ctx := context.Background()

	// Observer role attempting mutating action
	params := &CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "payment-gateway",
			"change_ticket": "CHG-2026-001",
		},
	}

	res, err := server.ExecuteToolCall(ctx, RoleObserver, params)
	if err != nil {
		t.Fatalf("unexpected execution error: %v", err)
	}
	if !res.IsError {
		t.Fatal("expected authorization denial for observer on restart_service")
	}

	logs := server.GetAuditLog()
	if len(logs) != 1 || logs[0].Allowed {
		t.Errorf("expected denial recorded in audit log: %+v", logs)
	}
}

func TestMCPOperatorRestartSuccess(t *testing.T) {
	server := NewMCPServer()
	ctx := context.Background()

	// Operator role with valid change ticket
	params := &CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "api-router",
			"change_ticket": "CHG-2026-888",
		},
	}

	res, err := server.ExecuteToolCall(ctx, RoleOperator, params)
	if err != nil {
		t.Fatalf("unexpected execution error: %v", err)
	}
	if res.IsError {
		t.Fatalf("expected successful restart, got error: %s", res.Content[0].Text)
	}

	logs := server.GetAuditLog()
	if len(logs) != 1 || !logs[0].Allowed {
		t.Errorf("expected successful execution logged in audit trail: %+v", logs)
	}
}

func TestMCPOperatorMissingTicketDenied(t *testing.T) {
	server := NewMCPServer()
	ctx := context.Background()

	// Operator role attempting mutating action without ticket
	params := &CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "api-router",
			"change_ticket": "", // Empty ticket
		},
	}

	res, err := server.ExecuteToolCall(ctx, RoleOperator, params)
	if err != nil {
		t.Fatalf("unexpected execution error: %v", err)
	}
	if !res.IsError {
		t.Fatal("expected mutation denial when change ticket is empty")
	}
}
