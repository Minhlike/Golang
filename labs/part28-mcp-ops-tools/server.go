package mcpopstools

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"sync"
	"time"
)

type Role string

const (
	RoleObserver Role = "observer" // Read-only access
	RoleOperator Role = "operator" // Mutating access with approved change ticket
	RoleAdmin    Role = "admin"    // Full administrative access
)

type contextKey string

const roleContextKey contextKey = "mcp_caller_role"

// WithCallerRole binds authenticated caller identity to session context.
// Agents cannot self-assert elevated roles via JSON arguments.
func WithCallerRole(ctx context.Context, role Role) context.Context {
	return context.WithValue(ctx, roleContextKey, role)
}

// CallerRoleFromContext extracts caller role with safe least-privilege fallback (RoleObserver).
func CallerRoleFromContext(ctx context.Context) Role {
	if r, ok := ctx.Value(roleContextKey).(Role); ok {
		return r
	}
	return RoleObserver
}

// ServiceActuator executes actual stateful operations on managed services.
type ServiceActuator interface {
	RestartService(ctx context.Context, serviceName string) error
}

// ChangeAuthorizer validates human-in-the-loop change tickets and approval policies.
type ChangeAuthorizer interface {
	AuthorizeChange(ctx context.Context, role Role, serviceName, ticket string) error
}

// DefaultChangeAuthorizer verifies tickets against an approved registry.
type DefaultChangeAuthorizer struct {
	ApprovedTickets map[string]string // ticket -> serviceName
}

func (a *DefaultChangeAuthorizer) AuthorizeChange(ctx context.Context, role Role, serviceName, ticket string) error {
	if role == RoleObserver {
		return fmt.Errorf("mcp: role %s not authorized for mutating tool restart_service", role)
	}
	if ticket == "" {
		return errors.New("mcp: missing change_ticket")
	}
	expectedSvc, exists := a.ApprovedTickets[ticket]
	if !exists {
		return fmt.Errorf("mcp: change ticket %s not found in approval system", ticket)
	}
	if expectedSvc != serviceName {
		return fmt.Errorf("mcp: change ticket %s is approved for %s, not %s", ticket, expectedSvc, serviceName)
	}
	return nil
}

// HealthTarget represents a pre-approved internal endpoint in the target allowlist.
type HealthTarget struct {
	ID          string `json:"id"`
	ServiceName string `json:"serviceName"`
	URL         string `json:"url"`
}

type Tool struct {
	Name        string         `json:"name"`
	Description string         `json:"description"`
	InputSchema map[string]any `json:"inputSchema"`
}

type CallToolParams struct {
	Name      string         `json:"name"`
	Arguments map[string]any `json:"arguments"`
}

type ToolContent struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

type CallToolResult struct {
	Content []ToolContent `json:"content"`
	IsError bool          `json:"isError,omitempty"`
}

type AuditRecord struct {
	Timestamp time.Time      `json:"timestamp"`
	Caller    Role           `json:"caller"`
	ToolName  string         `json:"toolName"`
	Arguments map[string]any `json:"arguments"`
	Decision  string         `json:"decision"` // "ALLOW" or "DENY"
	Result    string         `json:"result"`
}

// MCPServer implements an MCP Protocol Architecture & Security Model.
type MCPServer struct {
	mu         sync.Mutex
	tools      map[string]Tool
	targets    map[string]HealthTarget
	httpClient *http.Client
	actuator   ServiceActuator
	authorizer ChangeAuthorizer
	auditLog   []AuditRecord
}

// NewMCPServer instantiates an MCP tools server with target allowlist and policy gates.
func NewMCPServer(
	targets []HealthTarget,
	httpClient *http.Client,
	actuator ServiceActuator,
	authorizer ChangeAuthorizer,
) *MCPServer {
	if httpClient == nil {
		httpClient = &http.Client{Timeout: 3 * time.Second}
	}
	targetMap := make(map[string]HealthTarget)
	for _, t := range targets {
		targetMap[t.ID] = t
	}

	s := &MCPServer{
		tools:      make(map[string]Tool),
		targets:    targetMap,
		httpClient: httpClient,
		actuator:   actuator,
		authorizer: authorizer,
	}
	s.registerDefaultTools()
	return s
}

func (s *MCPServer) registerDefaultTools() {
	s.tools["query_service_health"] = Tool{
		Name:        "query_service_health",
		Description: "Inspects health status of an approved service via target_id allowlist (SSRF-safe)",
		InputSchema: map[string]any{
			"type": "object",
			"properties": map[string]any{
				"target_id": map[string]any{
					"type":        "string",
					"description": "Approved service identifier (e.g. checkout-health, payment-health)",
				},
			},
			"required": []string{"target_id"},
		},
	}

	s.tools["restart_service"] = Tool{
		Name:        "restart_service",
		Description: "Restarts an infrastructure service. Requires authorized operator role and change ticket.",
		InputSchema: map[string]any{
			"type": "object",
			"properties": map[string]any{
				"service_name":  map[string]any{"type": "string"},
				"change_ticket": map[string]any{"type": "string", "description": "Approved change ticket ID"},
			},
			"required": []string{"service_name", "change_ticket"},
		},
	}
}

// ExecuteToolCall validates arguments, checks session authorization, performs execution, and audits.
func (s *MCPServer) ExecuteToolCall(
	ctx context.Context,
	params *CallToolParams,
) (*CallToolResult, error) {
	if params == nil {
		return nil, errors.New("nil call params")
	}

	role := CallerRoleFromContext(ctx)

	tool, exists := s.tools[params.Name]
	if !exists {
		errStr := fmt.Sprintf("unknown tool: %s", params.Name)
		s.recordAudit(role, params.Name, params.Arguments, "DENY", errStr)
		return nil, errors.New(errStr)
	}

	switch tool.Name {
	case "query_service_health":
		targetID, ok := params.Arguments["target_id"].(string)
		if !ok || targetID == "" {
			errStr := "missing or invalid target_id"
			s.recordAudit(role, tool.Name, params.Arguments, "DENY", errStr)
			return &CallToolResult{
				IsError: true,
				Content: []ToolContent{{Type: "text", Text: errStr}},
			}, nil
		}

		target, found := s.targets[targetID]
		if !found {
			// SSRF Guard: reject any unapproved target_id immediately
			errStr := fmt.Sprintf("unapproved target_id %q: blocked by SSRF allowlist policy", targetID)
			s.recordAudit(role, tool.Name, params.Arguments, "DENY", errStr)
			return &CallToolResult{
				IsError: true,
				Content: []ToolContent{{Type: "text", Text: errStr}},
			}, nil
		}

		// Real HTTP execution to target URL
		start := time.Now()
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, target.URL, nil)
		if err != nil {
			errStr := fmt.Sprintf("failed to create health check request: %v", err)
			s.recordAudit(role, tool.Name, params.Arguments, "DENY", errStr)
			return &CallToolResult{
				IsError: true,
				Content: []ToolContent{{Type: "text", Text: errStr}},
			}, nil
		}

		resp, err := s.httpClient.Do(req)
		latency := time.Since(start)
		if err != nil {
			errStr := fmt.Sprintf("service %s (%s) health check error: %v", target.ServiceName, target.ID, err)
			s.recordAudit(role, tool.Name, params.Arguments, "DENY", errStr)
			return &CallToolResult{
				IsError: true,
				Content: []ToolContent{{Type: "text", Text: errStr}},
			}, nil
		}
		defer resp.Body.Close()

		resultText := fmt.Sprintf(
			"Service %s (%s) health check returned HTTP %d in %v",
			target.ServiceName, target.ID, resp.StatusCode, latency.Round(time.Millisecond),
		)
		s.recordAudit(role, tool.Name, params.Arguments, "ALLOW", resultText)
		return &CallToolResult{
			IsError: false,
			Content: []ToolContent{{Type: "text", Text: resultText}},
		}, nil

	case "restart_service":
		svc, _ := params.Arguments["service_name"].(string)
		ticket, _ := params.Arguments["change_ticket"].(string)

		// Authorization policy check via authorizer
		if s.authorizer != nil {
			if err := s.authorizer.AuthorizeChange(ctx, role, svc, ticket); err != nil {
				s.recordAudit(role, tool.Name, params.Arguments, "DENY", err.Error())
				return &CallToolResult{
					IsError: true,
					Content: []ToolContent{{Type: "text", Text: err.Error()}},
				}, nil
			}
		}

		// Stateful execution via ServiceActuator
		if s.actuator != nil {
			if err := s.actuator.RestartService(ctx, svc); err != nil {
				errStr := fmt.Sprintf("service %s restart failed: %v", svc, err)
				s.recordAudit(role, tool.Name, params.Arguments, "DENY", errStr)
				return &CallToolResult{
					IsError: true,
					Content: []ToolContent{{Type: "text", Text: errStr}},
				}, nil
			}
		}

		resultText := fmt.Sprintf("Service %s successfully restarted under ticket %s", svc, ticket)
		s.recordAudit(role, tool.Name, params.Arguments, "ALLOW", resultText)
		return &CallToolResult{
			IsError: false,
			Content: []ToolContent{{Type: "text", Text: resultText}},
		}, nil

	default:
		return nil, fmt.Errorf("unhandled tool: %s", tool.Name)
	}
}

func (s *MCPServer) recordAudit(caller Role, tool string, args map[string]any, decision, result string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.auditLog = append(s.auditLog, AuditRecord{
		Timestamp: time.Now().UTC(),
		Caller:    caller,
		ToolName:  tool,
		Arguments: args,
		Decision:  decision,
		Result:    result,
	})
}

// GetAuditLog returns a thread-safe snapshot of audit records.
func (s *MCPServer) GetAuditLog() []AuditRecord {
	s.mu.Lock()
	defer s.mu.Unlock()
	copied := make([]AuditRecord, len(s.auditLog))
	copy(copied, s.auditLog)
	return copied
}

// ListTools returns registered tools following the tools/list MCP protocol definition.
func (s *MCPServer) ListTools() []Tool {
	var list []Tool
	for _, t := range s.tools {
		list = append(list, t)
	}
	return list
}
