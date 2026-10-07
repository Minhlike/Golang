<!-- BOOK_ROLE: APPLICATION_SYSTEMS -->

# Chương 28 — MCP và AIOps bằng Go: trao công cụ cho Agent mà không trao toàn quyền

Xét một Agent có tool đọc health, xem log và đề xuất restart service. Đọc dữ liệu và thay đổi hệ thống có tác động khác nhau; nối chúng qua một protocol không tự định nghĩa ai được phép làm gì. Chương này bắt đầu từ contract quyền hành động, không từ độ tự tin của câu trả lời.

Khi tool nối tới production, cần hỏi cụ thể:

> *Nếu trao cho Agent quyền truy cập vào một công cụ, làm sao bạn bảo đảm tác tử không bị tấn công tiêm lời nhắc (Prompt Injection) để vô tình hoặc cố ý phá hủy cơ sở dữ liệu, rò rỉ token truy cập đám mây, hay làm sập toàn bộ hạ tầng?*

MCP chuẩn hóa ranh giới giao tiếp, nhưng không tự cấp quyền hay làm tool an toàn. Chương này dùng thư viện chính thức **`github.com/modelcontextprotocol/go-sdk/mcp`** (v1.8.0) để dựng một server sư phạm có đặc quyền tối thiểu, target registry và audit trail. Policy authorization, trust của target registry và actuator thật vẫn là trách nhiệm của deployment.

---

## 1. Mental Model: Ranh giới phòng thủ đa tầng từ Agent đến Hạ tầng

Mô hình trung tâm của lab là mỗi lời gọi phải đi qua các kiểm tra riêng. Danh tính do transport xác thực, không do argument tự khai; schema hợp lệ chưa đủ để cấp quyền thực thi:

| Kiểm tra | Đối tượng thật của lab | Không suy ra |
| :--- | :--- | :--- |
| Giao thức/transport | MCP SDK; stdio khi chạy server, transport trong memory khi test. | In-memory fixture không phải chứng minh authentication của HTTP deployment. |
| Schema | Struct và constraint của argument. | Chuỗi đúng schema chưa là target được phép hay instruction đáng tin. |
| Authorization | Identity trong session context, role và action. | Caller tự ghi `operator` vào argument không tạo quyền. |
| Target và side effect | Target registry được tin, handler và actuator đã cấu hình. | Allowlist tên không bảo vệ nếu chính registry hay credential bị đổi trái phép. |
| Audit | Ghi cả quyết định cho phép/từ chối ở boundary tương ứng. | Log không chỉ xảy ra sau hành động thành công; không có bảo đảm bền vững từ interface logger. |

Stdio tránh mở listener HTTP của chính server nhưng không bảo vệ trước process local có quyền thích hợp. Schema kiểm tra constraint đã khai báo; quyền dựa trên identity tin cậy và action/target cụ thể. Registry target của lab là cấu hình tin cậy, không phải bất kỳ URL Agent đưa vào. Audit chỉ có ích khi recorder, đường lưu và phản ứng khi mất log có contract riêng.

---

## 2. Model Context Protocol: Thư viện Go SDK Chính thức

MCP là giao thức mở cho client trao đổi với server cung cấp tool và dữ liệu. Nó định nghĩa thông điệp và lifecycle kết nối; mức phổ biến hay nhãn “tiêu chuẩn công nghiệp” không chứng minh policy của một deployment đúng.

Về bản chất kỹ thuật, MCP vận hành trên nền giao thức **JSON-RPC 2.0**. Máy chủ Go công bố danh sách các công cụ khả dụng kèm mô tả chức năng và JSON Schema qua phương thức `tools/list`. Khi tác tử quyết định sử dụng một công cụ, nó phát thông điệp `tools/call` chứa tên công cụ và các tham số tương ứng. 

Dự án thực hành tại `labs/part28-mcp-ops-tools/` ghim SDK v1.8.0. Theo compatibility matrix của chính SDK, bản này hỗ trợ và thương lượng revision mới nhất `2026-07-28` với peer hỗ trợ nó, đồng thời còn tương thích các revision cũ. Vì protocol revision được thương lượng theo kết nối, server không được tự suy ra wire behavior chỉ từ version của dependency. SDK vẫn cho phép typed handler, JSON Schema từ struct tags và `ReceivingMiddleware` cho các policy cục bộ.

### Giao vận Stdio và Kết nối Cục bộ

Lab có đường Stdio để client khởi chạy server và trao đổi qua stdin/stdout, cùng `NewInMemoryTransports` cho test. Stdio không cần endpoint HTTP hay chứng chỉ TLS cho pipe cục bộ, nhưng vẫn cần kiểm soát executable, quyền process và cấu hình client. Không gán một latency hoặc ưu tiên transport chung cho mọi hệ DevOps.

---

## 3. Cạm bẫy thiết kế: SSRF qua URL tùy ý và Giải pháp Target Allowlist

Một sai lầm rất phổ biến của các kỹ sư khi mới thiết kế MCP Server cho AIOps là cho phép Agent truyền trực tiếp một URL tùy ý:

~~~json
{
  "name": "query_service_health",
  "arguments": {"target_url": "https://..."}
}
~~~

Đây là một khiếm khuyết an ninh nghiêm trọng. Các bộ xác thực JSON Schema chỉ kiểm tra định dạng hình thức của chuỗi ký tự mà không hiểu ngữ nghĩa của địa chỉ đích. Khi tác tử bị tấn công tiêm lời nhắc hoặc gặp hiện tượng ảo giác, nó có thể gửi yêu cầu nhắm tới địa chỉ siêu dữ liệu nhạy cảm của điện toán đám mây (`http://169.254.169.254/latest/meta-data/...`), cổng quản trị nội bộ trên `localhost:9090`, hoặc các máy chủ cơ sở dữ liệu chưa mã hóa trong mạng riêng (VPC).

Để giảm bề mặt SSRF do **caller** chọn, agent không được truyền URL trực tiếp mà chỉ truyền `target_id` đã được duyệt trước. Server ánh xạ ID sang URL từ target registry và từ chối ID lạ. Đây không tự chứng minh URL trong registry là an toàn: registry bị ghi sai hoặc bị xâm phạm vẫn là một trust boundary riêng, cần review cấu hình, DNS/egress policy và quyền sửa registry.

---

## 4. Cấu hình Target Allowlist và Đăng ký Công cụ Typed Go

Dưới đây là cấu trúc định danh mục tiêu và mô hình tham số đầu vào được trích xuất từ `labs/part28-mcp-ops-tools/server.go`:

~~~go
type HealthTarget struct {
	ID          string `json:"id"`
	ServiceName string `json:"serviceName"`
	URL         string `json:"url"`
}

// QueryHealthInput định nghĩa schema đầu vào
type QueryHealthInput struct {
	TargetID string `json:"target_id"`
}

// RestartServiceInput định nghĩa tham số mutating tool
type RestartServiceInput struct {
	ServiceName  string `json:"service_name"`
	ChangeTicket string `json:"change_ticket"`
}
~~~

Các trường struct có thể được bổ sung thêm tag `jsonschema` để cung cấp phần mô tả chi tiết cho từng tham số khi máy chủ MCP công bố danh sách công cụ tới tác tử qua lệnh `tools/list`.

---

## 5. Phân quyền vai trò theo Ngữ cảnh Phiên và Rào chắn Đột biến

Policy phải lấy quyền của caller từ nguồn tin cậy:
> *Vai trò của Agent phải được xác định qua Ngữ cảnh Phiên (Session Context), không để Agent tự khai báo vai trò trong tham số JSON của công cụ.*

Nếu để Agent gửi `{"role": "admin"}` trong JSON arguments, việc prompt injection có thể dẫn tới việc Agent mạo danh quản trị viên để chiếm quyền điều khiển hệ thống.

### Gắn danh tính vào context.Context

~~~go
type Role string

const (
	RoleObserver Role = "observer" // Chỉ đọc
	RoleOperator Role = "operator" // Đột biến có phiếu
	RoleAdmin    Role = "admin"    // Toàn quyền
)

type contextKey string
const roleContextKey contextKey = "mcp_caller_role"

func WithCallerRole(
	ctx context.Context, role Role,
) context.Context {
	return context.WithValue(ctx, roleContextKey, role)
}

func CallerRoleFromContext(ctx context.Context) Role {
	if r, ok := ctx.Value(roleContextKey).(Role); ok {
		return r
	}
	return RoleObserver // Mặc định đặc quyền tối thiểu
}
~~~

### Tách bạch hai nhóm công cụ và Rào chắn Đột biến

Policy của lab cho `observer` gọi `query_service_health` trên target đã đăng ký và cấm `restart_service`. Đó không phải quyền “tự do truy vấn” chung: hệ thống thật cần giới hạn dữ liệu, target, budget và identity. Vai trò `operator` vẫn phải qua `ChangeAuthorizer` rồi `ServiceActuator`; tên role không tự đủ để cho phép thay đổi.

~~~go
type ServiceActuator interface {
	RestartService(
		ctx context.Context, serviceName string,
	) error
}

type ChangeAuthorizer interface {
	AuthorizeChange(
		ctx context.Context, role Role, svc, ticket string,
	) error
}
~~~

---

## 6. Xây dựng OpsServer trên nền tảng Official MCP Go SDK

Dưới đây là các phần chính của `OpsServer` trong `labs/part28-mcp-ops-tools/server.go`. Snippet cho thấy các boundary của lab; các phần wiring còn lại nằm trong source:

### 6.1. Khởi tạo server và ranh giới danh tính

Trong kiến trúc của MCP Go SDK, `AddReceivingMiddleware` cho phép can thiệp vào mọi thông điệp RPC gửi đến trước khi điều phối tới handler cụ thể. Ta sử dụng middleware này để bóc tách định danh caller từ phiên làm việc (`Session Context`) và tiêm vai trò bảo mật vào `context.Context`. Cần lưu ý rằng `context.Context` không tự tạo ra authenticated identity; middleware trong bài lab lấy role từ ánh xạ phiên giả lập để phục vụ kiểm thử mô hình. Trên môi trường production, tầng transport hoặc identity provider phải xác thực danh tính caller trước khi tiêm role vào context:

~~~go
type OpsServer struct {
	mcpServer   *mcp.Server
	httpClient  *http.Client
	actuator    ServiceActuator
	authorizer  ChangeAuthorizer
	targets     map[string]HealthTarget

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
		&mcp.Implementation{
			Name: "ops-mcp-server", Version: "v1.8.0",
		},
		&mcp.ServerOptions{
			Instructions: "AIOps server allowlist",
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

	// Test mapping only; not production authentication.
	// Real transport authenticates before dispatch.
	server.AddReceivingMiddleware(
		func(next mcp.MethodHandler) mcp.MethodHandler {
			return func(
				ctx context.Context,
				method string,
				req mcp.Request,
			) (mcp.Result, error) {
				role := CallerRoleFromContext(ctx)
				sess := req.GetSession()
				if role == RoleObserver && sess != nil {
					ops.mu.RLock()
					id := sess.ID()
					sessRole, found := ops.sessionRole[id]
					ops.mu.RUnlock()
					if found {
						role = sessRole
					}
				}
				ctx = WithCallerRole(ctx, role)
				return next(ctx, method, req)
			}
		},
	)

	ops.registerTools()
	return ops
}
~~~

### 6.2. Đăng ký Công cụ Kiểm tra Sức khỏe và Rào chắn SSRF

Công cụ `query_service_health` được đăng ký qua `mcp.AddTool`. SDK tự động giải mã tham số vào `QueryHealthInput` và chuyển giao quyền kiểm soát cho closure handler:

~~~go
mcp.AddTool(s.mcpServer, &mcp.Tool{
	Name:        "query_service_health",
	Description: "Ktra sức khỏe qua target_id allowlist",
}, func(
	ctx context.Context,
	req *mcp.CallToolRequest,
	input QueryHealthInput,
) (*mcp.CallToolResult, any, error) {
	role := CallerRoleFromContext(ctx)
	target, found := s.targets[input.TargetID]
	if !found {
		errStr := fmt.Sprintf(
			"target %q blocked by policy", input.TargetID,
		)
		s.RecordAudit(
			role, "query_service_health",
			map[string]any{"target_id": input.TargetID},
			"DENY", errStr,
		)
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				&mcp.TextContent{Text: errStr},
			},
		}, nil, nil
	}

	start := time.Now()
	httpReq, err := http.NewRequestWithContext(
		ctx, http.MethodGet, target.URL, nil,
	)
	if err != nil {
		errStr := fmt.Sprintf("req err: %v", err)
		s.RecordAudit(
			role, "query_service_health",
			map[string]any{"target_id": input.TargetID},
			"DENY", errStr,
		)
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				&mcp.TextContent{Text: errStr},
			},
		}, nil, nil
	}

	resp, err := s.httpClient.Do(httpReq)
	if err != nil {
		errStr := fmt.Sprintf("health check failed: %v", err)
		s.RecordAudit(
			role, "query_service_health",
			map[string]any{"target_id": input.TargetID},
			"DENY", errStr,
		)
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				&mcp.TextContent{Text: errStr},
			},
		}, nil, nil
	}
	defer resp.Body.Close()

	duration := time.Since(start).Round(time.Millisecond)
	health := "unhealthy"
	if resp.StatusCode >= http.StatusOK &&
		resp.StatusCode < http.StatusMultipleChoices {
		health = "healthy"
	}
	resText := fmt.Sprintf(
		"Service %s (%s) %s: HTTP %d",
		target.ServiceName, target.ID, health, resp.StatusCode,
	)
	s.RecordAudit(
		role, "query_service_health",
		map[string]any{"target_id": input.TargetID},
		"ALLOW", resText,
	)
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: resText},
		},
	}, nil, nil
})
~~~

### 6.3. Công cụ gây đột biến: dependency bắt buộc, không có đường mặc định cho phép

Với công cụ `restart_service`, `ChangeAuthorizer` **và** `ServiceActuator` là dependency bắt buộc. Thiếu một trong hai phải trả `DENY`; không được coi `nil` là “không cần kiểm tra” rồi báo restart thành công. Khi cả hai có mặt, yêu cầu phải qua `AuthorizeChange` trước khi kích hoạt `RestartService`:

~~~go
mcp.AddTool(s.mcpServer, &mcp.Tool{
	Name:        "restart_service",
	Description: "Restart dịch vụ có điều kiện, cần ticket",
}, func(
	ctx context.Context,
	req *mcp.CallToolRequest,
	input RestartServiceInput,
) (*mcp.CallToolResult, any, error) {
	role := CallerRoleFromContext(ctx)
	args := map[string]any{
		"service_name":  input.ServiceName,
		"change_ticket": input.ChangeTicket,
	}

	if s.authorizer == nil || s.actuator == nil {
		return deny(
			"required authorization or actuator missing",
		)
	}
	if err := s.authorizer.AuthorizeChange(
		ctx, role, input.ServiceName, input.ChangeTicket,
	); err != nil {
			s.RecordAudit(
				role, "restart_service", args,
				"DENY", err.Error(),
			)
			return &mcp.CallToolResult{
				IsError: true,
				Content: []mcp.Content{
					&mcp.TextContent{Text: err.Error()},
				},
			}, nil, nil
	}

	if err := s.actuator.RestartService(
		ctx, input.ServiceName,
	); err != nil {
			errStr := fmt.Sprintf("restart failed: %v", err)
			s.RecordAudit(
				role, "restart_service", args, "DENY", errStr,
			)
			return &mcp.CallToolResult{
				IsError: true,
				Content: []mcp.Content{
					&mcp.TextContent{Text: errStr},
				},
			}, nil, nil
	}

	resText := fmt.Sprintf(
		"Service %s restarted under ticket %s",
		input.ServiceName, input.ChangeTicket,
	)
	s.RecordAudit(
		role, "restart_service", args, "ALLOW", resText,
	)
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			&mcp.TextContent{Text: resText},
		},
	}, nil, nil
})
~~~

### 6.4. Ghi Nhật ký Kiểm toán Có Cấu trúc

Để theo dõi mọi hành vi của tác tử, máy chủ lưu vết các quyết định vào cấu trúc `AuditRecord`:

~~~go
type AuditRecord struct {
	Timestamp time.Time      `json:"timestamp"`
	Caller    Role           `json:"caller"`
	ToolName  string         `json:"toolName"`
	Arguments map[string]any `json:"arguments"`
	Decision  string         `json:"decision"` // ALLOW/DENY
	Result    string         `json:"result"`
}

func (s *OpsServer) RecordAudit(
	caller Role, tool string, args map[string]any,
	decision, result string,
) {
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
~~~

`auditLog` trong RAM chỉ giữ record trong process lifetime. Storage ngoài process có thể tăng độ bền, nhưng Kafka, Elasticsearch hay S3 Object Lock không tự bảo đảm toàn vẹn. Cần xác định ai được ghi/xóa, retention, cấu hình chống sửa và cách phát hiện mất record. Gửi bất đồng bộ còn có cửa sổ crash trước khi record được xác nhận lưu; policy phải quyết định có cho mutation khi audit sink lỗi hay không, cùng cơ chế đối soát outcome.

---

## 7. Kiểm chứng Lab thực tế (`labs/part28-mcp-ops-tools`)

Mã nguồn hoàn chỉnh nằm tại `labs/part28-mcp-ops-tools` (phân loại kiểm chứng: `UNIT_TESTED` / `MOCK_VERIFIED` cho giao thức MCP chính thức, phân quyền theo session context, rào chắn SSRF qua target allowlist, thực thi HTTP thật tới test server, và kích hoạt actuator). Chạy kiểm thử:

~~~bash
go test -v -race ./...
~~~

Bộ kiểm thử xác thực 6 kịch bản an ninh thực chiến trên nền giao vận in-memory:

~~~
=== RUN   TestMCPListTools
--- PASS: TestMCPListTools (0.00s)
=== RUN   TestMCPQueryHealthRealHTTP
--- PASS: TestMCPQueryHealthRealHTTP (0.00s)
=== RUN   TestMCPSSRFDeniedForUnapprovedTarget
--- PASS: TestMCPSSRFDeniedForUnapprovedTarget (0.00s)
=== RUN   TestMCPOperatorRestartSuccess
--- PASS: TestMCPOperatorRestartSuccess (0.00s)
=== RUN   TestMCPObserverMutatingActionDenied
--- PASS: TestMCPObserverMutatingActionDenied (0.00s)
=== RUN   TestMCPMissingOrInvalidTicketDenied
--- PASS: TestMCPMissingOrInvalidTicketDenied (0.00s)
PASS
ok      part28-mcp-ops-tools   0.234s
~~~

### Phân tích kết quả kiểm thử và Ranh giới xác thực:

Bộ kiểm thử khởi tạo client và server MCP qua kênh `mcp.NewInMemoryTransports()`. Kịch bản kiểm tra `tools/list` xác nhận schema JSON được sinh tự động từ struct tags `jsonschema`. Kịch bản kiểm tra sức khỏe gửi yêu cầu HTTP thực tế tới `httptest.Server`, đo thời gian phản hồi và ghi nhận trạng thái `ALLOW`. 

Các test xác nhận unknown target bị từ chối, observer không gọi được restart, và ticket sai không kích hoạt actuator trong các case đã chạy. Denial record được kiểm tra trong log RAM. Đây không chứng minh chống mọi SSRF, prompt injection hay mất audit: registry, identity provider, transport và storage thật là những boundary chưa được fixture này kiểm chứng.

---

## 8. Các cạm bẫy người học thường gặp (Learner Pitfalls)

| Cạm bẫy thực tế | Hậu quả trên Production | Giải pháp phòng ngừa |
| :--- | :--- | :--- |
| **Phó mặc an ninh cho JSON Schema** của MCP. | Bị tấn công SSRF hoặc Prompt Injection đánh cắp token IAM đám mây. | Luôn coi tham số từ Agent là không tin cậy; kiểm tra ngữ nghĩa và IP trong Go handler. |
| **Cho phép Agent gọi tool mutating** mà không có mã phiếu phê duyệt. | Agent tự ý xóa hoặc khởi động lại các dịch vụ quan trọng khi hiểu nhầm bối cảnh. | Yêu cầu `change_ticket` và chỉ cấp quyền mutating cho vai trò Operator. |
| **Mở HTTP không bảo vệ identity/kênh truyền.** | Có thể bị nghe lén hoặc mạo danh. | Chọn Stdio khi phù hợp; với Streamable HTTP, dùng TLS và authorization theo spec/deployment. mTLS là một lựa chọn, không yêu cầu chung cho mọi MCP transport. |
| **Không ghi nhật ký kiểm toán** (Audit Trail). | Thiếu dữ liệu ở boundary tool để xác định caller và hành động, dù có thể còn log từ các tầng khác. | Ghi structured audit log phù hợp policy lưu trữ và bảo vệ dữ liệu. |

---

## 9. Bài tập thực hành thiết kế MCP Server an toàn

### Thử thách 1: Điều tốc phiên làm việc của Agent (Agent Rate Limiting)
**Yêu cầu:** Thiết kế ReceivingMiddleware cho tools/call, gắn rate limit với caller/session đã xác thực. Bài tập chọn 10 request/giây, không phải ngưỡng an toàn production. Test cả caller dùng nhiều session và cleanup state limiter; SDK không có API `ExecuteToolCall` trong ví dụ này.

### Thử thách 2: Cơ chế Phê duyệt Hai bước (Human-in-the-Loop Gate)
**Yêu cầu:** Đối với các hành động phá hủy nghiêm trọng (ví dụ xóa cụm database hoặc giải phóng tài nguyên AWS), hãy thiết kế một công cụ MCP trả về trạng thái `PENDING_HUMAN_APPROVAL` kèm theo mã `confirmation_token` có hiệu lực trong 5 phút. Công cụ chỉ thực sự hành động khi nhận được lệnh xác nhận thứ hai chứa token hợp lệ do kỹ sư con người nhập vào.

---

## 10. Hướng dẫn giải và Phân tích kiến trúc bài tập

### Lời giải Thử thách 1: Bộ điều tốc theo caller đã xác thực

~~~go
type ToolRateLimiter interface {
	Allow(key string, now time.Time) bool
}

// Giữ state theo session/caller đã xác thực.
// Không chia một lastCall toàn cục giữa các agent.
// Replicas need distributed limiting for a shared quota.
~~~

### Lời giải Thử thách 2: Rào chắn Phê duyệt Hai bước

~~~go
type PendingApproval struct {
	Action string
	Target string
	ExpiresAt time.Time
}

type ApprovalManager struct {
	mu       sync.Mutex
	pendings map[string]PendingApproval
}

func (m *ApprovalManager) RequestApproval(
	action, target string,
) string {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Dùng crypto/rand, không dùng timestamp dự đoán được.
	token := randomTokenFromCryptoRand()
	m.pendings[token] = PendingApproval{
		Action:    action,
		Target:    target,
		ExpiresAt: time.Now().Add(5 * time.Minute),
	}
	return token
}

func (m *ApprovalManager) Confirm(
	token, action, target string,
) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	item, exists := m.pendings[token]
	delete(m.pendings, token)
	return exists && time.Now().Before(item.ExpiresAt) &&
		item.Action == action && item.Target == target
}
~~~

Một HTTP request hoàn thành không đồng nghĩa service khỏe. Lab dùng quy ước hẹp: chỉ `2xx` là `healthy`; `4xx`/`5xx` được trả về như trạng thái `unhealthy`, còn lỗi transport mới là lỗi gọi tool. Hệ thống thật cần contract health riêng (ví dụ readiness, body schema và timeout) thay vì suy ra sức khỏe chỉ từ mã HTTP.

Xóa record trước khi return khiến cả một confirmation sai cũng không thể trở thành lượt thử đoán/replay tiếp theo. Mã trong lab còn kiểm chứng token chỉ dùng một lần. Đây vẫn là state process-local; production cần store transactionally bền vững và danh tính con người được xác thực tách khỏi agent.

---

## 11. Điểm dừng: một tool an toàn là một boundary có bằng chứng

Chương 28 nối các boundary công cụ đã học. Bảng dưới là bản đồ tra cứu, không phải chứng nhận đã làm chủ production; Chương 29 tiếp tục phân biệt đề xuất, bằng chứng, thẩm quyền và kết quả.

| Chặng đường | Phạm vi kiến thức và kỹ năng | Thành tựu kỹ thuật cốt lõi |
| :--- | :--- | :--- |
| **Phần I–III: Nền tảng** | Cú pháp, value, pointer, slice, interface và error. | Dự đoán copy/aliasing và đọc contract lỗi. |
| **Phần IV–V: Đồng thời & Vận hành** | Memory model, worker pool, runtime, GC và pprof. | Tái lập race, thiết kế đường thoát và đo bottleneck. |
| **Phần VI–VII: Mạng & Dịch vụ** | HTTP/gRPC, TLS, SQL và lifecycle server. | Đặt timeout, ownership tài nguyên và transaction boundary. |
| **Phần VIII: Quan sát & Điều phối** | Metrics/trace, container, Kubernetes và opsprobe. | Phân biệt tín hiệu, desired state và observation. |
| **Phần IX: Hạ tầng & Agent** | Controller, operator, AWS, Git, supply chain, eBPF và MCP. | Xét retry, identity, quyền và evidence của từng boundary. |

Khi đưa những ý tưởng này vào production, hãy quay lại threat model, trust boundary, workload và incident policy của hệ thống cụ thể. Các lab chứng minh contract hẹp của chúng; chúng không thay thế xác thực danh tính thật, egress policy, durable audit hay review vận hành.
