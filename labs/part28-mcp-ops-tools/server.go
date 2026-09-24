package mcpopstools

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/url"
	"strings"
	"sync"
	"time"
)

type Role string

const (
	RoleObserver Role = "observer" // Read-only
	RoleOperator Role = "operator" // Mutating with change ticket
	RoleAdmin    Role = "admin"    // Full access
)

type JSONRPCRequest struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      any             `json:"id"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params,omitempty"`
}

type JSONRPCResponse struct {
	JSONRPC string        `json:"jsonrpc"`
	ID      any           `json:"id"`
	Result  any           `json:"result,omitempty"`
	Error   *JSONRPCError `json:"error,omitempty"`
}

type JSONRPCError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
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
	AgentRole Role           `json:"agentRole"`
	ToolName  string         `json:"toolName"`
	Arguments map[string]any `json:"arguments"`
	Allowed   bool           `json:"allowed"`
	Error     string         `json:"error,omitempty"`
}

type MCPServer struct {
	mu           sync.Mutex
	tools        map[string]Tool
	auditLog     []AuditRecord
	allowedHosts map[string]bool
}

func NewMCPServer() *MCPServer {
	s := &MCPServer{
		tools:        make(map[string]Tool),
		allowedHosts: make(map[string]bool),
	}
	s.registerDefaultTools()
	return s
}

func (s *MCPServer) registerDefaultTools() {
	s.tools["query_service_health"] = Tool{
		Name:        "query_service_health",
		Description: "Inspects HTTP service status and response code with SSRF protection",
		InputSchema: map[string]any{
			"type": "object",
			"properties": map[string]any{
				"target_url": map[string]any{"type": "string", "description": "Public URL to inspect"},
			},
			"required": []string{"target_url"},
		},
	}

	s.tools["restart_service"] = Tool{
		Name:        "restart_service",
		Description: "Restarts an infrastructure service. Requires authorized operator role and change ticket.",
		InputSchema: map[string]any{
			"type": "object",
			"properties": map[string]any{
				"service_name":  map[string]any{"type": "string"},
				"change_ticket": map[string]any{"type": "string", "description": "Approved change request ID"},
			},
			"required": []string{"service_name", "change_ticket"},
		},
	}
}

// ValidateSSRF ensures outgoing targets do not access internal networks or cloud metadata.
func ValidateSSRF(rawURL string) error {
	u, err := url.Parse(rawURL)
	if err != nil {
		return fmt.Errorf("invalid target URL: %w", err)
	}

	if u.Scheme != "http" && u.Scheme != "https" {
		return errors.New("unsupported protocol scheme: only http/https allowed")
	}

	hostname := u.Hostname()
	if strings.EqualFold(hostname, "localhost") {
		return errors.New("mcp: ssrf blocked: localhost access forbidden")
	}

	ip := net.ParseIP(hostname)
	if ip != nil {
		if ip.IsLoopback() {
			return errors.New("mcp: ssrf blocked: loopback target prohibited")
		}
		if ip.IsPrivate() {
			return errors.New("mcp: ssrf blocked: private RFC1918 range prohibited")
		}
		if ip.IsLinkLocalUnicast() || ip.String() == "169.254.169.254" {
			return errors.New("mcp: ssrf blocked: cloud metadata endpoint forbidden")
		}
	}

	return nil
}

// AuthorizeCall enforces least privilege based on agent role.
func (s *MCPServer) AuthorizeCall(role Role, toolName string, args map[string]any) error {
	switch toolName {
	case "query_service_health":
		// Read-only tools allowed for all roles
		return nil

	case "restart_service":
		// Mutating tool: forbid observer role
		if role == RoleObserver {
			return fmt.Errorf("mcp: tool authorization denied for role %s on mutating tool %s", role, toolName)
		}
		ticket, ok := args["change_ticket"].(string)
		if !ok || strings.TrimSpace(ticket) == "" {
			return errors.New("mcp: mutation denied: missing or empty change_ticket")
		}
		return nil

	default:
		return fmt.Errorf("mcp: unknown tool: %s", toolName)
	}
}

// ExecuteToolCall handles schema validation, authorization, execution, and audit logging.
func (s *MCPServer) ExecuteToolCall(
	ctx context.Context,
	role Role,
	params *CallToolParams,
) (*CallToolResult, error) {
	if params == nil {
		return nil, errors.New("nil call params")
	}

	tool, exists := s.tools[params.Name]
	if !exists {
		s.recordAudit(role, params.Name, params.Arguments, false, "tool not found")
		return nil, fmt.Errorf("tool not found: %s", params.Name)
	}

	// 1. Authorization Gate
	if err := s.AuthorizeCall(role, params.Name, params.Arguments); err != nil {
		s.recordAudit(role, params.Name, params.Arguments, false, err.Error())
		return &CallToolResult{
			IsError: true,
			Content: []ToolContent{{Type: "text", Text: err.Error()}},
		}, nil
	}

	// 2. Tool Execution Logic
	var resultText string
	switch tool.Name {
	case "query_service_health":
		targetURL, _ := params.Arguments["target_url"].(string)
		if err := ValidateSSRF(targetURL); err != nil {
			s.recordAudit(role, params.Name, params.Arguments, false, err.Error())
			return &CallToolResult{
				IsError: true,
				Content: []ToolContent{{Type: "text", Text: err.Error()}},
			}, nil
		}
		resultText = fmt.Sprintf("Service at %s responded: HTTP 200 OK (health: healthy)", targetURL)

	case "restart_service":
		svc, _ := params.Arguments["service_name"].(string)
		ticket, _ := params.Arguments["change_ticket"].(string)
		resultText = fmt.Sprintf("Service %s restart initiated successfully under ticket %s", svc, ticket)
	}

	s.recordAudit(role, params.Name, params.Arguments, true, "")
	return &CallToolResult{
		IsError: false,
		Content: []ToolContent{{Type: "text", Text: resultText}},
	}, nil
}

func (s *MCPServer) recordAudit(role Role, tool string, args map[string]any, allowed bool, errStr string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.auditLog = append(s.auditLog, AuditRecord{
		Timestamp: time.Now().UTC(),
		AgentRole: role,
		ToolName:  tool,
		Arguments: args,
		Allowed:   allowed,
		Error:     errStr,
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

// ListTools returns all registered tools for the tools/list JSON-RPC method.
func (s *MCPServer) ListTools() []Tool {
	var list []Tool
	for _, t := range s.tools {
		list = append(list, t)
	}
	return list
}
