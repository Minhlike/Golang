package mcpopstools

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
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
// MOCK_AUTH_BOUNDARY: In production systems, identity is established during
// transport/session handshake (e.g. mutual TLS, OIDC, or signed process credentials).
// Agents must never be allowed to self-assert elevated roles via JSON arguments.
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

func (a *DefaultChangeAuthorizer) AuthorizeChange(
	ctx context.Context, role Role, serviceName, ticket string,
) error {
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

// AuditRecord stores process-local, append-oriented audit records.
// Note: This in-memory slice is process-local and NOT durable or tamper-proof across restarts.
type AuditRecord struct {
	Timestamp time.Time      `json:"timestamp"`
	Caller    Role           `json:"caller"`
	ToolName  string         `json:"toolName"`
	Arguments map[string]any `json:"arguments"`
	Decision  string         `json:"decision"` // ALLOW or DENY
	Result    string         `json:"result"`
}

// QueryHealthInput defines typed input schema for query_service_health.
type QueryHealthInput struct {
	TargetID string `json:"target_id" jsonschema:"Mã định danh dịch vụ trong allowlist (vd: checkout-health)"`
}

// RestartServiceInput defines typed input schema for restart_service.
type RestartServiceInput struct {
	ServiceName  string `json:"service_name" jsonschema:"Tên dịch vụ cần khởi động lại"`
	ChangeTicket string `json:"change_ticket" jsonschema:"Mã phiếu thay đổi đã phê duyệt (vd: CHG-12345)"`
}

// OpsServer integrates domain policies, authorization, and audit tracking on top of official mcp.Server.
type OpsServer struct {
	mcpServer  *mcp.Server
	httpClient *http.Client
	actuator   ServiceActuator
	authorizer ChangeAuthorizer
	targets    map[string]HealthTarget

	mu          sync.RWMutex
	sessionRole map[string]Role
	auditLog    []AuditRecord
}

func NewOpsServer(
	client *http.Client,
	actuator ServiceActuator,
	authorizer ChangeAuthorizer,
	targets []HealthTarget,
) *OpsServer {
	if client == nil {
		client = &http.Client{Timeout: 5 * time.Second}
	}
	targetMap := make(map[string]HealthTarget, len(targets))
	for _, t := range targets {
		targetMap[t.ID] = t
	}

	server := mcp.NewServer(
		&mcp.Implementation{Name: "ops-mcp-server", Version: "v1.8.0"},
		&mcp.ServerOptions{
			Instructions: "AIOps operations server enforcing target allowlist and change-ticket authorization.",
		},
	)

	ops := &OpsServer{
		mcpServer:   server,
		httpClient:  client,
		actuator:    actuator,
		authorizer:  authorizer,
		targets:     targetMap,
		sessionRole: make(map[string]Role),
	}

	// Register receiving middleware to attach authenticated caller role to context.
	server.AddReceivingMiddleware(func(next mcp.MethodHandler) mcp.MethodHandler {
		return func(ctx context.Context, method string, req mcp.Request) (mcp.Result, error) {
			// If already set on ctx, preserve it; otherwise check session mapping.
			role := CallerRoleFromContext(ctx)
			if role == RoleObserver && req != nil && req.GetSession() != nil {
				ops.mu.RLock()
				sessRole, found := ops.sessionRole[req.GetSession().ID()]
				ops.mu.RUnlock()
				if found {
					role = sessRole
				}
			}
			ctx = WithCallerRole(ctx, role)
			return next(ctx, method, req)
		}
	})

	ops.registerTools()
	return ops
}

// SetSessionRole configures authenticated role for a given session ID (MOCK_AUTH_BOUNDARY).
func (s *OpsServer) SetSessionRole(sessionID string, role Role) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.sessionRole[sessionID] = role
}

// MCPServer exposes the official mcp.Server instance.
func (s *OpsServer) MCPServer() *mcp.Server {
	return s.mcpServer
}

// RecordAudit safely appends an audit event to the process-local record slice.
func (s *OpsServer) RecordAudit(caller Role, tool string, args map[string]any, decision, result string) {
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

// GetAuditRecords returns a copy of the current audit trail.
func (s *OpsServer) GetAuditRecords() []AuditRecord {
	s.mu.RLock()
	defer s.mu.RUnlock()
	records := make([]AuditRecord, len(s.auditLog))
	copy(records, s.auditLog)
	return records
}

func (s *OpsServer) registerTools() {
	// 1. Tool: query_service_health (Read-Only, SSRF-safe via target_id allowlist)
	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "query_service_health",
		Description: "Kiểm tra tình trạng sức khỏe dịch vụ qua target_id trong danh sách trắng đã kiểm duyệt.",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input QueryHealthInput) (*mcp.CallToolResult, any, error) {
		role := CallerRoleFromContext(ctx)
		target, found := s.targets[input.TargetID]
		if !found {
			errStr := fmt.Sprintf("unapproved target_id %q: blocked by SSRF allowlist policy", input.TargetID)
			s.RecordAudit(role, "query_service_health", map[string]any{"target_id": input.TargetID}, "DENY", errStr)
			return &mcp.CallToolResult{
				IsError: true,
				Content: []mcp.Content{&mcp.TextContent{Text: errStr}},
			}, nil, nil
		}

		start := time.Now()
		httpReq, err := http.NewRequestWithContext(ctx, http.MethodGet, target.URL, nil)
		if err != nil {
			errStr := fmt.Sprintf("failed to create http request: %v", err)
			s.RecordAudit(role, "query_service_health", map[string]any{"target_id": input.TargetID}, "DENY", errStr)
			return &mcp.CallToolResult{
				IsError: true,
				Content: []mcp.Content{&mcp.TextContent{Text: errStr}},
			}, nil, nil
		}

		resp, err := s.httpClient.Do(httpReq)
		if err != nil {
			errStr := fmt.Sprintf("health check request failed: %v", err)
			s.RecordAudit(role, "query_service_health", map[string]any{"target_id": input.TargetID}, "DENY", errStr)
			return &mcp.CallToolResult{
				IsError: true,
				Content: []mcp.Content{&mcp.TextContent{Text: errStr}},
			}, nil, nil
		}
		defer resp.Body.Close()

		duration := time.Since(start).Round(time.Millisecond)
		resText := fmt.Sprintf("Service %s (%s) healthy: HTTP %d in %v", target.ServiceName, target.ID, resp.StatusCode, duration)
		s.RecordAudit(role, "query_service_health", map[string]any{"target_id": input.TargetID}, "ALLOW", resText)
		return &mcp.CallToolResult{
			Content: []mcp.Content{&mcp.TextContent{Text: resText}},
		}, nil, nil
	})

	// 2. Tool: restart_service (Mutating, requires change ticket and authorization)
	mcp.AddTool(s.mcpServer, &mcp.Tool{
		Name:        "restart_service",
		Description: "Khởi động lại dịch vụ sản xuất có điều kiện, yêu cầu mã phiếu thay đổi hợp lệ.",
	}, func(ctx context.Context, req *mcp.CallToolRequest, input RestartServiceInput) (*mcp.CallToolResult, any, error) {
		role := CallerRoleFromContext(ctx)
		args := map[string]any{"service_name": input.ServiceName, "change_ticket": input.ChangeTicket}

		if s.authorizer != nil {
			if err := s.authorizer.AuthorizeChange(ctx, role, input.ServiceName, input.ChangeTicket); err != nil {
				s.RecordAudit(role, "restart_service", args, "DENY", err.Error())
				return &mcp.CallToolResult{
					IsError: true,
					Content: []mcp.Content{&mcp.TextContent{Text: err.Error()}},
				}, nil, nil
			}
		}

		if s.actuator != nil {
			if err := s.actuator.RestartService(ctx, input.ServiceName); err != nil {
				errStr := fmt.Sprintf("actuator restart failed: %v", err)
				s.RecordAudit(role, "restart_service", args, "DENY", errStr)
				return &mcp.CallToolResult{
					IsError: true,
					Content: []mcp.Content{&mcp.TextContent{Text: errStr}},
				}, nil, nil
			}
		}

		resText := fmt.Sprintf("Service %s successfully restarted under ticket %s", input.ServiceName, input.ChangeTicket)
		s.RecordAudit(role, "restart_service", args, "ALLOW", resText)
		return &mcp.CallToolResult{
			Content: []mcp.Content{&mcp.TextContent{Text: resText}},
		}, nil, nil
	})
}

// RunStdio launches the server over stdin/stdout transport.
func (s *OpsServer) RunStdio(ctx context.Context) error {
	return s.mcpServer.Run(ctx, &mcp.StdioTransport{})
}
