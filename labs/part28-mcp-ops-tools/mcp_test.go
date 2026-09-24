package mcpopstools

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
)

type mockServiceActuator struct {
	restartedServices []string
}

func (m *mockServiceActuator) RestartService(ctx context.Context, serviceName string) error {
	m.restartedServices = append(m.restartedServices, serviceName)
	return nil
}

func TestMCPListTools(t *testing.T) {
	server := NewMCPServer(nil, nil, nil, nil)
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

func TestMCPQueryHealthRealHTTP(t *testing.T) {
	var requestCount atomic.Int32
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestCount.Add(1)
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status":"UP"}`))
	}))
	defer backend.Close()

	targets := []HealthTarget{
		{ID: "checkout-health", ServiceName: "checkout-service", URL: backend.URL},
	}

	server := NewMCPServer(targets, backend.Client(), nil, nil)
	ctx := WithCallerRole(context.Background(), RoleObserver)

	params := &CallToolParams{
		Name: "query_service_health",
		Arguments: map[string]any{
			"target_id": "checkout-health",
		},
	}

	res, err := server.ExecuteToolCall(ctx, params)
	if err != nil {
		t.Fatalf("unexpected execution error: %v", err)
	}
	if res.IsError {
		t.Fatalf("expected successful execution, got error: %s", res.Content[0].Text)
	}
	if requestCount.Load() != 1 {
		t.Errorf("expected 1 HTTP request to backend, got %d", requestCount.Load())
	}
	if !strings.Contains(res.Content[0].Text, "HTTP 200") {
		t.Errorf("expected result to mention HTTP 200, got %s", res.Content[0].Text)
	}

	logs := server.GetAuditLog()
	if len(logs) != 1 || logs[0].Decision != "ALLOW" {
		t.Errorf("expected 1 allowed audit record, got %+v", logs)
	}
}

func TestMCPSSRFDeniedForUnapprovedTarget(t *testing.T) {
	targets := []HealthTarget{
		{ID: "payment-health", ServiceName: "payment-api", URL: "http://internal-payments.local/healthz"},
	}

	server := NewMCPServer(targets, nil, nil, nil)
	ctx := WithCallerRole(context.Background(), RoleOperator)

	maliciousTargets := []string{
		"http://169.254.169.254/latest/meta-data/",
		"http://127.0.0.1:9090",
		"internal-db",
		"arbitrary-target-id",
	}

	for _, target := range maliciousTargets {
		params := &CallToolParams{
			Name: "query_service_health",
			Arguments: map[string]any{
				"target_id": target,
			},
		}

		res, err := server.ExecuteToolCall(ctx, params)
		if err != nil {
			t.Fatalf("unexpected call error: %v", err)
		}
		if !res.IsError {
			t.Errorf("expected SSRF block for %s, but call was permitted!", target)
		}
		if !strings.Contains(res.Content[0].Text, "blocked by SSRF allowlist policy") {
			t.Errorf("expected SSRF block message, got: %s", res.Content[0].Text)
		}
	}

	logs := server.GetAuditLog()
	if len(logs) != len(maliciousTargets) {
		t.Errorf("expected %d audit entries, got %d", len(maliciousTargets), len(logs))
	}
	for _, l := range logs {
		if l.Decision != "DENY" {
			t.Errorf("expected all unapproved targets to be denied in audit log")
		}
	}
}

func TestMCPOperatorRestartSuccess(t *testing.T) {
	actuator := &mockServiceActuator{}
	authorizer := &DefaultChangeAuthorizer{
		ApprovedTickets: map[string]string{
			"CHG-2026-999": "api-gateway",
		},
	}

	server := NewMCPServer(nil, nil, actuator, authorizer)

	// Context carries RoleOperator identity
	ctx := WithCallerRole(context.Background(), RoleOperator)

	params := &CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "api-gateway",
			"change_ticket": "CHG-2026-999",
		},
	}

	res, err := server.ExecuteToolCall(ctx, params)
	if err != nil {
		t.Fatalf("unexpected execution error: %v", err)
	}
	if res.IsError {
		t.Fatalf("expected successful restart, got error: %s", res.Content[0].Text)
	}

	if len(actuator.restartedServices) != 1 || actuator.restartedServices[0] != "api-gateway" {
		t.Errorf("expected api-gateway to be restarted, got %v", actuator.restartedServices)
	}

	logs := server.GetAuditLog()
	if len(logs) != 1 || logs[0].Decision != "ALLOW" {
		t.Errorf("expected ALLOW decision in audit trail: %+v", logs)
	}
}

func TestMCPObserverMutatingActionDenied(t *testing.T) {
	actuator := &mockServiceActuator{}
	authorizer := &DefaultChangeAuthorizer{
		ApprovedTickets: map[string]string{
			"CHG-2026-999": "api-gateway",
		},
	}

	server := NewMCPServer(nil, nil, actuator, authorizer)

	// Context carries RoleObserver identity
	ctx := WithCallerRole(context.Background(), RoleObserver)

	params := &CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "api-gateway",
			"change_ticket": "CHG-2026-999",
		},
	}

	res, err := server.ExecuteToolCall(ctx, params)
	if err != nil {
		t.Fatalf("unexpected call error: %v", err)
	}
	if !res.IsError {
		t.Fatalf("expected observer to be denied mutating action")
	}

	if len(actuator.restartedServices) != 0 {
		t.Errorf("service should NOT have been restarted when observer is denied")
	}

	logs := server.GetAuditLog()
	if len(logs) != 1 || logs[0].Decision != "DENY" {
		t.Errorf("expected DENY in audit trail for unauthorized role: %+v", logs)
	}
}

func TestMCPMissingOrInvalidTicketDenied(t *testing.T) {
	authorizer := &DefaultChangeAuthorizer{
		ApprovedTickets: map[string]string{
			"CHG-2026-111": "cache-service",
		},
	}
	server := NewMCPServer(nil, nil, &mockServiceActuator{}, authorizer)
	ctx := WithCallerRole(context.Background(), RoleOperator)

	// Case 1: unapproved ticket
	params1 := &CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "cache-service",
			"change_ticket": "UNAPPROVED-TICKET",
		},
	}
	res1, _ := server.ExecuteToolCall(ctx, params1)
	if !res1.IsError {
		t.Errorf("expected unapproved ticket to be denied")
	}

	// Case 2: ticket for different service
	params2 := &CallToolParams{
		Name: "restart_service",
		Arguments: map[string]any{
			"service_name":  "database-service",
			"change_ticket": "CHG-2026-111", // only approved for cache-service
		},
	}
	res2, _ := server.ExecuteToolCall(ctx, params2)
	if !res2.IsError {
		t.Errorf("expected ticket mismatch to be denied")
	}
}
