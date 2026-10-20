<!-- BOOK_ROLE: APPLICATION_SYSTEMS -->

# Chương 28 — MCP và AIOps bằng Go: trao công cụ cho Agent mà không trao toàn quyền

Xét một tác tử (Agent) có công cụ đọc trạng thái sức khỏe dịch vụ (*health check*), xem nhật ký (*logs*) và đề xuất khởi động lại dịch vụ (*restart service*). Đọc dữ liệu và thay đổi hệ thống mang lại tác động hoàn toàn khác nhau; việc kết nối chúng qua một giao thức không đồng nghĩa hệ thống đã tự phân định quyền hạn. Chương này bắt đầu từ khế ước (*contract*) về quyền thực thi hành động, không dựa trên mức độ tự tin trong câu trả lời của mô hình trí tuệ nhân tạo.

Khi tool nối tới production, cần hỏi cụ thể:

> *Nếu trao cho Agent quyền truy cập vào một công cụ, làm sao ta bảo đảm tác tử không bị tấn công tiêm lời nhắc (Prompt Injection) để vô tình hoặc cố ý phá hủy cơ sở dữ liệu, rò rỉ token truy cập đám mây, hay làm sập toàn bộ hạ tầng?*

Giao thức bối cảnh mô hình (MCP, tức *Model Context Protocol*) chuẩn hóa ranh giới giao tiếp, nhưng không tự động cấp quyền hay làm cho công cụ trở nên an toàn. Chương này sử dụng thư viện chính thức **`github.com/modelcontextprotocol/go-sdk/mcp`** (phiên bản v1.8.0) để dựng một máy chủ mẫu mang tính sư phạm theo nguyên tắc đặc quyền tối thiểu, có sổ đăng ký mục tiêu (*target registry*) và dấu vết kiểm toán (*audit trail*). Chính sách ủy quyền (*authorization policy*), độ tin cậy của sổ đăng ký mục tiêu và bộ chấp hành (*actuator*) thực tế vẫn là trách nhiệm của cấu hình triển khai.

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

Cơ chế truyền nhận qua dòng nhập/xuất chuẩn (*stdio*) tránh việc mở cổng lắng nghe HTTP trên máy chủ nhưng không ngăn chặn được các tiến trình cục bộ trên cùng máy có đặc quyền phù hợp. Lược đồ (*schema*) chỉ kiểm tra các ràng buộc dữ liệu đã khai báo; quyền hạn phải dựa trên định danh tin cậy cùng hành động và mục tiêu cụ thể. Sổ đăng ký mục tiêu của bài lab là cấu hình tĩnh đáng tin cậy, không chấp nhận bất kỳ URL tùy ý nào do tác tử tự ý cung cấp. Dấu vết kiểm toán chỉ thực sự phát huy tác dụng khi bộ ghi, kênh lưu trữ và phương án xử lý khi mất nhật ký được quy định bằng một khế ước rõ ràng.

---

## 2. Model Context Protocol: Thư viện Go SDK Chính thức

MCP là giao thức mở cho phép ứng dụng khách (*client*) trao đổi với máy chủ cung cấp công cụ và dữ liệu. Giao thức này định nghĩa định dạng thông điệp và vòng đời kết nối; độ phổ biến hay nhãn “tiêu chuẩn công nghiệp” không chứng minh chính sách bảo mật của một hệ thống triển khai là chính xác.

Ở tầng kiến trúc giao vận, MCP vận hành trên nền giao thức **JSON-RPC 2.0**. Máy chủ Go công bố danh sách các công cụ khả dụng kèm mô tả chức năng và JSON Schema qua phương thức `tools/list`. Khi tác tử quyết định sử dụng một công cụ, nó phát thông điệp `tools/call` chứa tên công cụ và các tham số tương ứng.

Dự án thực hành tại `labs/part28-mcp-ops-tools/` ghim SDK v1.8.0. Theo ma trận tương thích của chính bộ công cụ phát triển (SDK), bản này hỗ trợ và thương lượng phiên bản giao thức (*revision*) mới nhất `2026-07-28` với các đối tác hỗ trợ, đồng thời vẫn tương thích ngược với các phiên bản cũ hơn. Vì phiên bản giao thức được thương lượng theo từng phiên kết nối, máy chủ không được tự suy diễn hành vi trên đường truyền chỉ từ số phiên bản của gói phụ thuộc. Thư viện SDK vẫn cho phép đăng ký hàm xử lý định kiểu rõ ràng, tự sinh JSON Schema từ thẻ cấu trúc Go và cung cấp `ReceivingMiddleware` cho các chính sách kiểm soát cục bộ.

### Giao vận Stdio và Kết nối Cục bộ

Bài lab cung cấp kênh kết nối Stdio để ứng dụng khách khởi chạy tiến trình máy chủ và trao đổi qua `stdin`/`stdout`, cùng hàm `NewInMemoryTransports` phục vụ kiểm thử. Kênh Stdio không cần điểm cuối HTTP hay chứng chỉ TLS cho đường ống dẫn cục bộ, nhưng vẫn đòi hỏi kiểm soát tệp thực thi, quyền hạn tiến trình và cấu hình ứng dụng khách. Không thể áp đặt một độ trễ cố định hay ưu tiên phương thức truyền tải chung cho mọi hệ thống DevOps.

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

Để thu hẹp bề mặt tấn công SSRF do bên gọi tùy ý lựa chọn, tác tử tuyệt đối không được phép truyền trực tiếp địa chỉ URL mà chỉ được truyền mã định danh mục tiêu `target_id` đã được phê duyệt từ trước. Máy chủ thực hiện ánh xạ mã định danh này sang địa chỉ URL tương ứng từ danh bạ mục tiêu và lập tức từ chối các mã lạ. Điều này không tự chứng minh rằng địa chỉ URL trong danh bạ là hoàn toàn an toàn: một danh bạ bị nhập sai hoặc bị can thiệp trái phép vẫn là một ranh giới tin cậy riêng biệt, đòi hỏi phải thẩm định cấu hình, chính sách phân giải tên miền và lưu lượng mạng đi ra ngoài cùng thẩm quyền chỉnh sửa danh bạ.

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

Nếu để tác tử tự ý gửi `{"role": "admin"}` trong các tham số dữ liệu JSON, nguy cơ tiêm lời nhắc có thể dẫn tới việc tác tử mạo danh quản trị viên để chiếm đoạt quyền điều khiển toàn bộ hệ thống.

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

### Một danh tính thật không tự sinh ra quyền tool

Bộ thử nghiệm phiên làm việc của chương giữ nguyên mức độ giả lập kiểm chứng đối với nguồn dữ liệu định danh. Nếu muốn khảo sát ranh giới mạng thực tế mà không cần đưa giao thức MCP vào mọi phép thử, hãy thực thi bài thực hành TLS từ Chương 11 trước: tiến trình đọc dù có chứng chỉ số đã được xác minh vẫn bị từ chối quyền đột biến; tiêu đề tự xưng là quản trị viên không thể thay đổi quyết định an ninh. Đó là bằng chứng về quá trình bắt tay và chính sách HTTP cục bộ, chưa phải là phép thẩm định ủy quyền toàn diện của giao thức truyền tải dạng luồng.

Khi triển khai hệ thống có cơ chế kết thúc TLS tại máy chủ ủy nhiệm, hàm xử lý có thể không còn giữ lại chuỗi chứng chỉ đã xác thực của máy khách ban đầu. Tuyệt đối không sao chép tiêu đề định danh từ mạng Internet vào ngữ cảnh phiên làm việc; hệ thống bắt buộc phải xác định máy chủ ủy nhiệm nào được tin cậy, bảo vệ đường truyền giữa máy chủ ủy nhiệm và dịch vụ nội bộ, đồng thời kiểm tra cơ chế chuyển giao danh tính của kiến trúc triển khai. Các phương thức truyền tải qua dòng dữ liệu chuẩn, xác thực OAuth hay xác thực hai chiều mTLS có cách thức thiết lập bên gọi khác nhau, nhưng đều có chung yêu cầu bắt buộc: ánh xạ bên gọi đã xác thực sang hành động và mục tiêu được phép. Chứng chỉ trong bài thực hành không làm thay đổi chính sách MCP và không khẳng định mọi máy chủ MCP đều bắt buộc phải dùng mTLS.

### Tách bạch hai nhóm công cụ và Rào chắn Đột biến

Chính sách của bài thực hành cho phép vai trò quan sát viên gọi `query_service_health` trên các mục tiêu đã đăng ký và nghiêm cấm gọi `restart_service`. Đó không phải là đặc quyền tự do truy vấn tùy tiện: hệ thống thực tế đòi hỏi giới hạn phạm vi dữ liệu, mục tiêu cho phép, định mức tài nguyên và danh tính người gọi. Vai trò người vận hành vẫn bắt buộc phải đi qua bộ cấp phép thay đổi `ChangeAuthorizer` rồi mới tới bộ thực thi dịch vụ `ServiceActuator`; tên gọi của vai trò không tự nó mang đủ thẩm quyền để kích hoạt thay đổi.

`DefaultChangeAuthorizer` chỉ chấp nhận đúng `operator` hoặc `admin` rồi mới kiểm phiếu và dịch vụ. Một vai trò rỗng, viết sai hay chưa được định nghĩa phải bị từ chối; kiểm riêng `role != observer` sẽ vô tình mở quyền cho các giá trị ấy. Đây là policy của lab, không phải role model do MCP chuẩn hóa.

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

Dưới đây là các cấu phần trọng tâm của máy chủ `OpsServer` trong tệp `labs/part28-mcp-ops-tools/server.go`. Các đoạn trích được rút gọn để đọc từng ranh giới: phần gắn khóa caller cho điều tốc và phép kiểm tra limiter trong handler không in lại ở đây. Source lab mới là cài đặt đầy đủ; việc biên dịch các đoạn trích không chứng minh policy đã bị lược bỏ vẫn hoạt động.

### 6.1. Khởi tạo máy chủ và ranh giới danh tính

Trong kiến trúc của bộ công cụ MCP Go, hàm `AddReceivingMiddleware` cho phép can thiệp vào mọi thông điệp triệu gọi từ xa gửi đến trước khi điều phối tới hàm xử lý cụ thể. Chúng ta sử dụng phần mềm trung gian này để bóc tách định danh bên gọi từ phiên làm việc và tiêm vai trò bảo mật vào ngữ cảnh `context.Context`. Bản thân `context.Context` không tự bảo đảm tính xác thực của danh tính; phần mềm trung gian trong bài thực hành lấy vai trò từ bảng ánh xạ phiên giả lập để phục vụ kiểm thử mô hình hóa. Trên môi trường vận hành thực tế, tầng truyền tải hoặc nhà cung cấp định danh bắt buộc phải xác thực danh tính bên gọi trước khi tiêm vai trò vào ngữ cảnh:

~~~go
type OpsServer struct {
	mcpServer   *mcp.Server
	httpClient  *http.Client
	actuator    ServiceActuator
	authorizer  ChangeAuthorizer
	limiter     ToolRateLimiter
	targets     map[string]HealthTarget

	mu          sync.RWMutex
	sessionRole map[string]Role
	auditLog    []AuditRecord
}

func NewOpsServer(
	client *http.Client,
	actuator ServiceActuator,
	authorizer ChangeAuthorizer,
	limiter ToolRateLimiter,
	targets []HealthTarget,
) *OpsServer {
	if client == nil {
		client = &http.Client{Timeout: 5 * time.Second}
	}
	if limiter == nil {
		limiter = NewKeyedIntervalLimiter(10)
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
		limiter:     limiter,
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
				var sess mcp.Session
				if req != nil {
					sess = req.GetSession()
				}
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

Công cụ `query_service_health` được đăng ký qua `mcp.AddTool`. SDK tự động giải mã tham số vào `QueryHealthInput` và chuyển giao quyền kiểm soát cho closure handler. Allowlist dưới đây chỉ chặn ID lạ; `http.Client` vẫn có thể theo redirect, và đích DNS có thể thay đổi. Lab không cài bộ lọc IP hoặc redirect: không dùng test ID lạ làm bằng chứng đã chặn mọi đường SSRF.

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
			"unapproved target_id %q: "+
				"blocked by SSRF allowlist policy",
			input.TargetID,
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
		"Service %s (%s) %s: HTTP %d in %v",
		target.ServiceName, target.ID, health,
		resp.StatusCode, duration,
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
	deny := func(message string) (
		*mcp.CallToolResult, any, error,
	) {
		s.RecordAudit(role, "restart_service", args,
			"DENY", message)
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{
				&mcp.TextContent{Text: message},
			},
		}, nil, nil
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

Nhật ký kiểm toán trong bộ nhớ RAM chỉ lưu giữ các bản ghi trong vòng đời vận hành của tiến trình. Việc lưu trữ bên ngoài tiến trình có thể gia tăng độ bền vững, nhưng các hệ thống lưu trữ phân tán không tự động bảo đảm tính toàn vẹn tuyệt đối. Hệ thống cần xác định rõ ai có quyền ghi hoặc xóa, thời hạn lưu giữ, cấu hình chống sửa đổi và phương thức phát hiện bản ghi bị thất thoát. Việc chuyển giao dữ liệu bất đồng bộ còn tiềm ẩn khoảng thời gian tiến trình bị sập trước khi bản ghi được xác nhận lưu trữ bền vững; chính sách bắt buộc phải xác định rõ có cho phép thao tác đột biến diễn ra khi hệ thống lưu trữ kiểm toán gặp sự cố hay không, đi kèm cơ chế đối soát kết quả rõ ràng.

---

## 7. Kiểm chứng Lab thực tế (`labs/part28-mcp-ops-tools`)

Mã nguồn hoàn chỉnh nằm tại `labs/part28-mcp-ops-tools` (phân loại kiểm chứng: kiểm thử đơn vị và giả lập kiểm chứng cho giao thức MCP chính thức, phân quyền theo ngữ cảnh phiên làm việc, rào chắn chống SSRF qua danh sách mục tiêu cho phép, thực thi yêu cầu HTTP tới máy chủ kiểm thử và kích hoạt bộ thực thi). Chạy kiểm thử:

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

Các bài kiểm thử xác nhận mục tiêu không xác định bị từ chối, vai trò quan sát viên không thể gọi thao tác khởi động lại, và phiếu phê duyệt sai không kích hoạt bộ thực thi trong các trường hợp đã kiểm tra. Bản ghi từ chối được kiểm chứng trực tiếp trong nhật ký bộ nhớ. Kết quả này không chứng minh khả năng phòng chống trước mọi cuộc tấn công SSRF, tiêm lời nhắc hay nguy cơ thất thoát dữ liệu kiểm toán: danh bạ mục tiêu, nhà cung cấp định danh, tầng truyền vận và kho lưu trữ thực tế là các ranh giới kỹ thuật chưa được bộ thử nghiệm này bao quát.

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
Yêu cầu: Thiết kế phần mềm trung gian tiếp nhận cho lệnh gọi công cụ, gắn định mức tốc độ với bên gọi hoặc phiên làm việc đã xác thực. Bài tập ấn định hạn mức 10 yêu cầu/giây, không phải ngưỡng an toàn áp dụng cho môi trường vận hành thực tế. Kiểm thử cả trường hợp bên gọi sử dụng nhiều phiên làm việc đồng thời và dọn dẹp trạng thái bộ điều tốc; bộ công cụ không cung cấp hàm thực thi trực tiếp trong ví dụ này.

### Thử thách 2: Cơ chế Phê duyệt Hai bước (Human-in-the-Loop Gate)
Yêu cầu: Đối với các hành động phá hủy nghiêm trọng (như xóa cơ sở dữ liệu hay thu hồi hạ tầng), hãy thiết kế cơ chế phê duyệt hai bước cho công cụ MCP: hành động ban đầu trả về trạng thái chờ kèm mã xác nhận tạm thời. Thao tác chỉ được thực thi khi nhận được lệnh xác nhận chứa mã thông báo hợp lệ trong thời hạn 5 phút. Cơ chế phải ràng buộc chặt chẽ mã xác nhận với hành động và mục tiêu đã phê duyệt, đồng thời bảo đảm mã xác nhận chỉ được dùng thành công đúng một lần duy nhất.

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

> **Dừng để dự đoán:** Giả sử Agent xin cấp token để khởi động lại dịch vụ cache staging, nhưng sau đó gửi lệnh xác nhận kèm theo hành động xóa database production. Nếu hệ thống chỉ kiểm tra thời hạn của token mà không so sánh hành động và mục tiêu, rủi ro an ninh nào sẽ phát sinh? Khi thiết kế thao tác xác nhận, ta nên xóa token ngay ở lần thử sai đầu tiên hay chỉ hủy token sau khi đã khớp thành công?

#### Gợi ý giải pháp (chỉ đọc sau khi đã tự làm)
Nếu mã xác nhận không gắn chặt với hành động và mục tiêu (`Action` và `Target`), hệ thống sẽ vấp phải lỗ hổng tráo đổi mục tiêu (action substitution). Một lời nhắc độc hại từ bên ngoài có thể lợi dụng sự phê duyệt của con người cho một thao tác vô hại để thực thi lệnh phá hủy trên hệ thống trọng yếu. Vì vậy, bản ghi phê duyệt phải đóng băng bộ đôi hành động và tài nguyên ngay từ thời điểm tạo token.

Về chính sách tiêu thụ token, ta lựa chọn chính sách vô hiệu hóa khi khớp thành công (single-use successful claim). Khi nhận đúng token, đúng hành động, đúng mục tiêu và còn trong thời hạn 5 phút, hàm sẽ xóa token khỏi bộ nhớ để chống tấn công phát lại (replay attack). Ngược lại, nếu chọn chính sách xóa token ngay cả khi tham số truyền vào không khớp, kẻ tấn công hoặc một tiến trình thử lại nhầm lẫn có thể cố tình gửi sai tham số để hủy hoại phiên phê duyệt hợp lệ, tạo ra nguy cơ từ chối dịch vụ (denial-of-service). Việc người dùng gửi một token không tồn tại hoàn toàn không gây ảnh hưởng đến các token hợp lệ khác. Nguy cơ dò đoán tham số khi giữ token được kiểm soát bằng độ hỗn loạn cao của chuỗi sinh ngẫu nhiên từ `crypto/rand` và thời gian hết hạn ngắn.

Cài đặt an toàn của `ApprovalManager` dưới mô hình bộ nhớ cục bộ:

Đoạn dưới là phác thảo của biến thể **chỉ tiêu thụ khi khớp thành công**, không phải source lab nguyên vẹn: nó lược constructor khởi tạo `pendings` và helper sinh token bằng `crypto/rand` có trả lỗi. Source `approval.go` chọn policy khác: một lần xác nhận có token tồn tại sẽ tiêu thụ token, kể cả khi gửi sai action/target. `TestApprovalTokenIsBoundAndOneTime` kiểm policy đó. Hai lựa chọn đánh đổi khả năng thử lại hợp lệ với nguy cơ dò/thử nhiều lần; không dùng test của policy này làm chứng cứ cho policy kia.

~~~go
type PendingApproval struct {
	Action    string
	Target    string
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
	if !exists || !time.Now().Before(item.ExpiresAt) {
		return false
	}
	if item.Action != action || item.Target != target {
		return false
	}
	delete(m.pendings, token)
	return true
}
~~~

Toàn bộ thao tác kiểm tra và tiêu thụ mã xác nhận (`token`) phải diễn ra nguyên tử dưới cùng một khóa `m.mu.Lock()` nhằm ngăn chặn hai goroutine chạy đua cùng lúc với cùng một mã và bảo toàn liên kết chặt chẽ với hành động cùng mục tiêu (`Action` và `Target`). Trong mô hình này, việc chỉ xóa mã khi xác nhận thành công giúp duy trì tính hợp lệ của phiên phê duyệt trước các lần gửi sai tham số hoặc thử lại nhầm lẫn, đồng thời bảo đảm mỗi mã xác nhận chỉ được sử dụng đúng một lần.

Tuy nhiên, việc không xóa token khi kiểm tra thất bại đặt ra yêu cầu bắt buộc về chính sách dọn dẹp: những mã xác nhận đã hết hạn mà không bao giờ được sử dụng sẽ tích tụ vĩnh viễn trong bản đồ nếu không có cơ chế thu gom. Một hệ thống hoàn chỉnh đòi hỏi tiến trình chạy nền dọn dẹp định kỳ (periodic cleanup worker) hoặc cơ chế loại bỏ lười (lazy eviction) để quét và xóa các mục có `time.Now().After(item.ExpiresAt)`. Cấu trúc `ApprovalManager` trên đây là mô hình kiến trúc minh họa trong bộ nhớ cục bộ của một tiến trình, chưa phải giải pháp an toàn cho môi trường sản xuất. Môi trường thực tế đòi hỏi kho dữ liệu bền vững chịu lỗi qua các lần khởi động lại, xác thực danh tính con người độc lập khỏi tác tử AI (`agent`), và nhật ký kiểm toán không thể sửa đổi.

Một yêu cầu HTTP kết thúc thành công không đồng nghĩa dịch vụ đã thực sự khỏe mạnh. Bài lab áp dụng quy ước đơn giản: chỉ mã `2xx` được phân loại là `healthy`; mã `4xx`/`5xx` được trả về như trạng thái `unhealthy`, trong khi lỗi tầng truyền vận (*transport error*) mới tính là lỗi gọi công cụ. Hệ thống thực tế đòi hỏi khế ước kiểm tra trạng thái sức khỏe riêng biệt (chẳng hạn đầu kiểm tra sẵn sàng phục vụ như *readiness probe*, cấu trúc dữ liệu phản hồi và giới hạn thời gian chờ) thay vì chỉ suy diễn tình trạng sức khỏe từ mã trạng thái HTTP.

---

## 11. Điểm dừng: một tool an toàn là một boundary có bằng chứng

Chương 28 kết nối các ranh giới công cụ kỹ thuật đã học. Bảng dưới là bản đồ tra cứu, không phải chứng nhận đã làm chủ production; Chương 29 tiếp tục phân biệt đề xuất, bằng chứng, thẩm quyền và kết quả.

| Chặng đường | Phạm vi kiến thức và kỹ năng | Thành tựu kỹ thuật cốt lõi |
| :--- | :--- | :--- |
| **Phần I: Nền tảng Cơ học & Bộ nhớ Go (Ch. 00–06)** | Cú pháp, value, pointer, slice, error, package và testing. | Dự đoán copy/aliasing, thiết kế package và đọc contract lỗi. |
| **Phần II: Tương tranh & Độ ổn định Hệ thống (Ch. 07–13)** | I/O stream, memory model, race detector, worker pool, GC, client trace và server lifecycle. | Tái lập race, thiết kế đường thoát, đo bottleneck và ranh giới shutdown. |
| **Phần III: Dịch vụ Phân tán & Cơ sở Dữ liệu (Ch. 14–21)** | Reflection, incident CLI, observability, container, CI/CD, generics và dự án opsprobe. | Đặt timeout, transaction boundary, type parameter và điều hòa hệ thống. |
| **Phần IV: Kubernetes Operator & eBPF Nâng cao (Ch. 22–29)** | Controller client-go, Operator CRD, AWS SDK v2, GitHub automation, Cosign, eBPF và MCP. | Xét retry, identity, quyền và evidence của từng boundary an toàn. |

Khi đưa những ý tưởng này vào môi trường vận hành thực tế, hãy rà soát lại mô hình mối đe dọa (*threat model*), ranh giới tin cậy (*trust boundary*), khối lượng công việc thực tế và quy trình xử lý sự cố của từng hệ thống cụ thể. Các bài thực hành chỉ chứng minh những khế ước kỹ thuật trong phạm vi hẹp; chúng không thể thay thế việc xác thực danh tính thực tế, chính sách kiểm soát lưu lượng đi ra (*egress policy*), hệ thống kiểm toán bền bỉ hay quy trình duyệt vận hành của con người.
