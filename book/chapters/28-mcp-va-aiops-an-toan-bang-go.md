# Chương 28 — MCP và AIOps bằng Go: trao công cụ cho Agent mà không trao toàn quyền

Trong bức tranh công nghệ hiện đại, các mô hình ngôn ngữ lớn (LLMs) và Tác tử Trí tuệ Nhân tạo (AI Agents) không còn dừng lại ở vai trò trợ lý hỏi đáp thụ động. Các hệ thống vận hành tự động (AIOps) thế hệ mới bắt đầu giao phó cho tác tử quyền điều tra các cảnh báo từ hệ thống giám sát Prometheus, truy vấn Kubernetes API để thu thập nhật ký của các Pod gặp lỗi vòng lặp sập đổ (`CrashLoopBackOff`), gọi AWS SDK kiểm tra dung lượng máy chủ, và thậm chí kích hoạt các hành động khắc phục sự cố như khởi động lại tiến trình dịch vụ hoặc điều phối lưu lượng mạng.

Tuy nhiên, việc kết nối trực tiếp tác tử AI với hạ tầng sản xuất tiềm ẩn những hiểm họa an ninh nghiêm trọng bậc nhất:

> *Nếu trao cho Agent quyền truy cập vào một công cụ, làm sao bạn bảo đảm tác tử không bị tấn công tiêm lời nhắc (Prompt Injection) để vô tình hoặc cố ý phá hủy cơ sở dữ liệu, rò rỉ token truy cập đám mây, hay làm sập toàn bộ hạ tầng?*

Giải pháp của ngành công nghiệp là chuẩn hóa ranh giới giao tiếp thông qua **Model Context Protocol (MCP)** kết hợp với kiến trúc phòng thủ đa tầng trong Go. Chương này hướng dẫn bạn cách xây dựng máy chủ công cụ MCP an toàn dựa trên thư viện chính thức **`github.com/modelcontextprotocol/go-sdk/mcp`** (v1.8.0), thiết lập cơ chế phân quyền đặc quyền tối thiểu (Least Privilege), rào chắn chống tấn công giả mạo yêu cầu từ máy chủ (SSRF) và lưu vết kiểm toán có cấu trúc.

---

## 1. Mental Model: Ranh giới phòng thủ đa tầng từ Agent đến Hạ tầng

Mô hình tư duy cốt lõi của một hệ thống AIOps an toàn được xây dựng dựa trên nguyên tắc **Không tin tưởng tuyệt đối (Zero Trust)**:

~~~
[Yêu cầu từ AI Agent] (JSON-RPC tool call)
          │
          ▼
[Giao thức MCP] (Transport qua Stdio / SSE / InMemory)
          │
          ▼
[Xác thực Schema] (Typed Struct & jsonschema tags)
          │
          ▼
[Middleware Phân quyền] (Session Context RBAC)
          │
          ▼
[Rào chắn Ngữ nghĩa] (Chặn đứng SSRF qua Allowlist)
          │
          ▼
[Handler & Actuator] (Thực thi có kiểm soát)
          │
          ▼
[Hạ tầng Thực tế] (Kubernetes / AWS / Linux OS)
          │
          ▼
[Nhật ký Kiểm toán] (Lưu vết append-oriented có cấu trúc)
~~~

Trong kiến trúc này, sự an toàn không đến từ một điểm kiểm soát đơn lẻ mà là sự phối hợp của nhiều ranh giới bảo vệ nối tiếp nhau. Ở tầng giao vận, việc sử dụng luồng nhập xuất chuẩn (`os.Stdin`/`os.Stdout`) hoặc kết nối tiến trình cục bộ giúp giảm thiểu bề mặt phơi nhiễm mạng từ xa so với việc mở cổng HTTP công khai, song việc kiểm soát tham số, cô lập tiến trình và phân quyền phiên vẫn là điều kiện bắt buộc. Tầng schema bảo đảm dữ liệu đầu vào tuân thủ định dạng kỹ thuật nghiêm ngặt. Tầng phân quyền phiên tách bạch rõ ràng giữa tác tử chỉ đọc (Observer) và tác tử có thẩm quyền thay đổi trạng thái (Operator). Tầng rào chắn ngữ nghĩa ngăn ngừa việc tác tử bị lừa truy cập vào các địa chỉ mạng nội bộ nhạy cảm, và cuối cùng tầng kiểm toán lưu vết chi tiết từng quyết định cho phép hay từ chối để phục vụ điều tra sự cố.

---

## 2. Model Context Protocol: Thư viện Go SDK Chính thức

Giao thức **Model Context Protocol (MCP)** do Anthropic khởi xướng đã nhanh chóng trở thành tiêu chuẩn công nghiệp mở giúp kết nối các mô hình AI với các nguồn dữ liệu và công cụ bên ngoài.

Về bản chất kỹ thuật, MCP vận hành trên nền giao thức **JSON-RPC 2.0**. Máy chủ Go công bố danh sách các công cụ khả dụng kèm mô tả chức năng và JSON Schema qua phương thức `tools/list`. Khi tác tử quyết định sử dụng một công cụ, nó phát thông điệp `tools/call` chứa tên công cụ và các tham số tương ứng. 

Dự án thực hành tại `labs/part28-mcp-ops-tools/` tích hợp trực tiếp thư viện chính thức **`github.com/modelcontextprotocol/go-sdk/mcp`** (phiên bản v1.8.0, tương thích đặc tả giao thức MCP 2026-07-28). Kiến trúc của SDK cho phép lập trình viên định nghĩa các công cụ thông qua các hàm Go có kiểu dữ liệu tường minh (`typed handlers`), tự động sinh JSON Schema từ struct tags, và can thiệp vào luồng xử lý thông qua hệ thống middleware nhận tin (`ReceivingMiddleware`).

### Giao vận Stdio và Kết nối Cục bộ

Trong môi trường DevOps và container, MCP thường ưu tiên giao vận qua luồng nhập xuất chuẩn (`os.Stdin` và `os.Stdout`) thông qua `mcp.StdioTransport` thay vì mở cổng mạng HTTP độc lập. Tiến trình tác tử trực tiếp fork tiến trình máy chủ công cụ Go và trao đổi dữ liệu qua pipe hệ điều hành với độ trễ thấp, loại bỏ sự phụ thuộc vào chứng chỉ mạng công khai. Khi kiểm thử tự động, SDK cung cấp `mcp.NewInMemoryTransports()` cho phép client và server bắt tay trực tiếp trong bộ nhớ RAM mà không cần đụng chạm tới hệ điều hành hay socket mạng.

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

Để loại trừ triệt để nguy cơ SSRF, kiến trúc chuẩn mực áp dụng nguyên tắc danh sách trắng: tác tử tuyệt đối không được phép chỉ định URL trực tiếp, mà chỉ được truyền mã định danh dịch vụ (`target_id`) đã được phê duyệt trước (chẳng hạn `checkout-health`, `payment-health`). Máy chủ Go nắm giữ danh bạ cho phép (`Target Allowlist Registry`) để ánh xạ `target_id` sang URL nội bộ thực tế; bất kỳ mã nào nằm ngoài danh bạ đều bị từ chối ngay lập tức tại ranh giới chính sách.

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

Không phải tác tử nào cũng có quyền như nhau. Tuy nhiên, một nguyên tắc bảo mật tối thượng cần ghi nhớ:
> **Vai trò của Agent BẮT BUỘC phải được xác định qua Ngữ cảnh Phiên (Session Context), tuyệt đối không để Agent tự khai báo vai trò trong tham số JSON của công cụ!**

Nếu bạn để Agent gửi `{"role": "admin"}` trong JSON arguments, một cuộc tấn công Prompt Injection đơn giản có thể ép Agent mạo danh quản trị viên để chiếm quyền điều khiển toàn bộ hệ thống!

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

Về mặt kiểm soát rủi ro, các công cụ phục vụ tác tử được phân thành hai nhóm rõ rệt. Nhóm công cụ chỉ đọc (như `query_service_health`) cho phép vai trò `observer` tự do truy vấn nhằm phục vụ mục đích thu thập thông tin và chẩn đoán sự cố mà không làm thay đổi trạng thái hệ thống. Ngược lại, nhóm công cụ gây đột biến (như `restart_service`) bị nghiêm cấm hoàn toàn đối với vai trò `observer`. Khi tác tử mang vai trò `operator` gửi yêu cầu, thao tác bắt buộc phải thông qua interface `ChangeAuthorizer` để xác minh mã phiếu thay đổi hợp lệ trước khi được chuyển tiếp tới interface `ServiceActuator` để thực thi.

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

Dưới đây là cấu trúc `OpsServer` hoàn chỉnh trích xuất từ `labs/part28-mcp-ops-tools/server.go`, liên kết toàn bộ chuỗi phòng thủ đa tầng trên nền thư viện chính thức `github.com/modelcontextprotocol/go-sdk/mcp`:

### 6.1. Khởi tạo MCP Server và Tiêm Middleware Phân quyền Phiên

Trong kiến trúc của MCP Go SDK, `AddReceivingMiddleware` cho phép can thiệp vào mọi thông điệp RPC gửi đến trước khi điều phối tới handler cụ thể. Ta sử dụng middleware này để bóc tách định danh caller từ phiên làm việc (`Session Context`) và tiêm vai trò bảo mật vào `context.Context`:

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

	// Middleware gắn danh tính caller vào request context
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
	resText := fmt.Sprintf(
		"Service %s (%s) healthy: HTTP %d",
		target.ServiceName, target.ID, resp.StatusCode,
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

### 6.3. Đăng ký Công cụ Gây Đột biến và Ủy quyền Phiếu Thay đổi

Với công cụ `restart_service`, yêu cầu bắt buộc phải qua `AuthorizeChange` trước khi kích hoạt `RestartService`:

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

	if s.authorizer != nil {
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
	}

	if s.actuator != nil {
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

Cần lưu ý về mặt kiến trúc: mảng `auditLog` trong bộ nhớ RAM phục vụ việc truy vết cục bộ trong vòng đời tiến trình. Trong môi trường sản xuất thực tế, nhật ký kiểm toán cần được đẩy bất đồng bộ ra hệ thống lưu trữ bền vững ngoài tiến trình (như Kafka, Elasticsearch hoặc S3 Object Lock) để bảo đảm tính toàn vẹn và không bị xóa bỏ khi tiến trình kết thúc.

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

Các kịch bản phòng thủ chứng minh tính kiên cố của hệ thống: khi tác tử truyền `target_id` trái phép nhằm tấn công SSRF tới địa chỉ AWS metadata (`169.254.169.254`), handler lập tức chặn đứng và trả về lỗi chính sách; khi tác tử mang vai trò `observer` cố tình gọi công cụ khởi động lại dịch vụ `restart_service`, hệ thống từ chối truy cập ngay tại tầng phân quyền; và khi tác tử `operator` gửi phiếu thay đổi không hợp lệ hoặc cấp cho dịch vụ khác, actuator bị khóa cứng không cho phép thực thi. Mọi nỗ lực truy cập đều được ghi vết vào nhật ký kiểm toán với quyết định `DENY` tường minh.

---

## 8. Các cạm bẫy người học thường gặp (Learner Pitfalls)

| Cạm bẫy thực tế | Hậu quả trên Production | Giải pháp phòng ngừa |
| :--- | :--- | :--- |
| **Phó mặc an ninh cho JSON Schema** của MCP. | Bị tấn công SSRF hoặc Prompt Injection đánh cắp token IAM đám mây. | Luôn coi tham số từ Agent là không tin cậy; kiểm tra ngữ nghĩa và IP trong Go handler. |
| **Cho phép Agent gọi tool mutating** mà không có mã phiếu phê duyệt. | Agent tự ý xóa hoặc khởi động lại các dịch vụ quan trọng khi hiểu nhầm bối cảnh. | Bắt buộc yêu cầu `change_ticket` và chỉ cấp quyền mutating cho vai trò Operator. |
| **Giao tiếp MCP qua HTTP công khai** không mã hóa. | Bị nghe lén dữ liệu chẩn đoán hoặc bị tấn công mạo danh yêu cầu công cụ. | Ưu tiên Stdio Transport; nếu bắt buộc dùng SSE qua mạng phải có TLS Mutual Authentication. |
| **Không ghi nhật ký kiểm toán** (Audit Trail). | Khi hệ thống gặp sự cố do Agent gây ra, kỹ sư SRE hoàn toàn không có dữ liệu để truy vết nguyên nhân. | Ghi lại mọi lượt gọi công cụ vào append-only structured audit log. |

---

## 9. Bài tập thực hành thiết kế MCP Server an toàn

### Thử thách 1: Điều tốc phiên làm việc của Agent (Agent Rate Limiting)
**Yêu cầu:** Một tác tử AI gặp lỗi lặp vô hạn (infinite reasoning loop) và gọi công cụ kiểm tra sức khỏe hàng trăm lần mỗi giây, gây quá tải cho endpoint mục tiêu. Hãy thiết kế một middleware Go gắn vào `ExecuteToolCall` để giới hạn tần suất gọi công cụ của mỗi phiên tác tử không vượt quá 10 request/giây.

### Thử thách 2: Cơ chế Phê duyệt Hai bước (Human-in-the-Loop Gate)
**Yêu cầu:** Đối với các hành động phá hủy nghiêm trọng (ví dụ xóa cụm database hoặc giải phóng tài nguyên AWS), hãy thiết kế một công cụ MCP trả về trạng thái `PENDING_HUMAN_APPROVAL` kèm theo mã `confirmation_token` có hiệu lực trong 5 phút. Công cụ chỉ thực sự hành động khi nhận được lệnh xác nhận thứ hai chứa token hợp lệ do kỹ sư con người nhập vào.

---

## 10. Hướng dẫn giải và Phân tích kiến trúc bài tập

### Lời giải Thử thách 1: Bộ điều tốc phiên làm việc của Agent

~~~go
type AgentRateLimiter struct {
	mu       sync.Mutex
	lastCall time.Time
	interval time.Duration
}

func NewAgentRateLimiter(rps int) *AgentRateLimiter {
	return &AgentRateLimiter{
		interval: time.Second / time.Duration(rps),
	}
}

func (l *AgentRateLimiter) Allow() bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	if now.Sub(l.lastCall) < l.interval {
		return false // Vượt ngưỡng tốc độ cho phép
	}
	l.lastCall = now
	return true
}
~~~

### Lời giải Thử thách 2: Rào chắn Phê duyệt Hai bước

~~~go
type PendingApproval struct {
	Action    string
	ExpiresAt time.Time
}

type ApprovalManager struct {
	mu       sync.Mutex
	pendings map[string]PendingApproval
}

func (m *ApprovalManager) RequestApproval(
	action string,
) string {
	m.mu.Lock()
	defer m.mu.Unlock()

	token := fmt.Sprintf("APPV-%d", time.Now().UnixNano())
	m.pendings[token] = PendingApproval{
		Action:    action,
		ExpiresAt: time.Now().Add(5 * time.Minute),
	}
	return token
}

func (m *ApprovalManager) Confirm(token string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	item, exists := m.pendings[token]
	if !exists || time.Now().After(item.ExpiresAt) {
		delete(m.pendings, token)
		return false
	}
	delete(m.pendings, token)
	return true
}
~~~

---

## 11. Nhìn lại Toàn bộ Hành trình: Từ Dòng Code Đầu Tiên đến Vận Hành Tác Tử Thông Minh

Với việc hoàn thành **Chương 28**, bạn đã chính thức khép lại một hành trình học tập và rèn luyện kỹ thuật đồ sộ bậc nhất trong thế giới lập trình Go và Kỹ thuật Hệ thống Hiện đại.

Hãy cùng nhìn lại những nấc thang bạn đã vượt qua:

1. **Phần I–III (Nền tảng Nguyên bản):** Bắt đầu từ nguyên lý đầu tiên về kiến trúc máy tính, bố cục ô nhớ, con trỏ, cơ chế chia sẻ bộ nhớ của slice, hệ thống kiểu và giao diện (interfaces), thiết kế gói (package design) và triết lý xử lý lỗi tường minh của Go.
2. **Phần IV–V (Đồng thời & Vận hành Chuyên sâu):** Chinh phục mô hình Concurrency của Go, thấu hiểu ranh giới goroutine leak, race conditions, áp suất ngược (backpressure) với worker pool, cơ chế điều phối của Go Runtime, bộ thu gom rác (GC) và phân tích hiệu năng bằng pprof.
3. **Phần VI–VII (Hệ thống Mạng & Dịch vụ Production):** Vận chuyển dữ liệu qua mạng với HTTP, gRPC, giao thức TLS, kết nối database an toàn với transaction lifecycle, quản lý vòng đời tiến trình với Graceful Shutdown và công cụ chẩn đoán incident.
4. **Phần VIII (Quan sát Toàn diện & Điều phối):** Triển khai 3 trụ cột Observability (Prometheus, OpenTelemetry Tracing), đóng gói container tối ưu, triển khai Kubernetes, điều hòa trạng thái với Reconciliation Loop và vận hành dự án thực chiến `opsprobe`.
5. **Phần IX (Hạ tầng Nâng cao, Chuỗi Cung ứng & AI):** 
   - Xây dựng **Kubernetes Controller thật** bằng `client-go` với Informer và WorkQueue có giãn cách tốc độ (Ch22).
   - Thiết kế **Operator hoàn chỉnh** với CRD, Scheme và Finalizer bằng `controller-runtime` (Ch23).
   - Tự động hóa hạ tầng đám mây **AWS SDK v2** với chứng chỉ ngắn hạn và ký số SigV4 (Ch24).
   - Xây dựng hệ thống tự động hóa hướng sự kiện với **Git và GitHub** (Ch25).
   - Thiết lập cổng kiểm soát **Chuỗi cung ứng phần mềm có thể kiểm chứng** với Cosign, SLSA Attestation và `govulncheck` (Ch26).
   - Xâm nhập vào tầng sâu nhất của hệ điều hành Linux để **Quan sát Kernel bằng eBPF** và Go mà không cần CGO (Ch27).
   - Và cuối cùng, trao công cụ an toàn cho Tác tử AI bằng **Model Context Protocol (MCP)** với rào chắn chống SSRF, RBAC và Audit Trail (Ch28).

Bạn không còn là một lập trình viên chỉ biết gọi thư viện bên ngoài theo các hướng dẫn rời rạc trên mạng. Bạn đã làm chủ **tư duy kiến trúc hệ thống từ nguyên lý đầu tiên (First-Principles Thinking)**, sở hữu phản xạ chẩn đoán sự cố nhạy bén, và hoàn toàn tự tin thiết kế, xây dựng và vận hành những hệ thống phần mềm hiệu năng cao, kiên cố và bảo mật trong kỷ nguyên Cloud Native và Trí tuệ Nhân tạo.
