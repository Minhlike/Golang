# Chương 28 — MCP và AIOps bằng Go: trao công cụ cho Agent mà không trao toàn quyền

Trong bức tranh công nghệ hiện đại, các mô hình ngôn ngữ lớn (LLMs) và Tác tử Trí tuệ Nhân tạo (AI Agents) không còn dừng lại ở vai trò trợ lý trả lời câu hỏi văn bản thuần túy. 

Các hệ thống vận hành tự động (AIOps) thế hệ mới đang trao quyền trực tiếp cho AI Agent:
- Tự động điều tra các cảnh báo từ hệ thống giám sát Prometheus.
- Truy vấn Kubernetes API để thu thập log của các Pod bị `CrashLoopBackOff`.
- Gọi AWS SDK để kiểm tra tình trạng sức khỏe của Auto Scaling Group.
- Thậm chí tự động thực thi các hành động khắc phục sự cố (remediation) như khởi động lại dịch vụ hoặc điều chỉnh lưu lượng mạng.

Tuy nhiên, việc kết nối AI Agent với hạ tầng sản xuất tiềm ẩn những rủi ro an ninh nghiêm trọng bậc nhất:
> *Nếu bạn trao cho Agent quyền truy cập vào một công cụ, làm sao bạn đảm bảo Agent không bị tấn công Prompt Injection để vô tình hoặc cố ý phá hủy cơ sở dữ liệu, rò rỉ token truy cập đám mây, hay làm sập toàn bộ cụm máy chủ?*

Giải pháp của ngành công nghiệp là chuẩn hóa ranh giới giao tiếp thông qua **Model Context Protocol (MCP)** kết hợp với kiến trúc phòng thủ đa tầng trong Go. Chương này hướng dẫn bạn cách xây dựng một máy chủ công cụ MCP an toàn, thiết lập cơ chế phân quyền đặc quyền tối thiểu (Least Privilege), rào chắn chống tấn công SSRF và lưu vết kiểm toán bất biến (Audit Trail).

---

## 1. Mental Model: Ranh giới phòng thủ đa tầng từ Agent đến Hạ tầng

Mô hình tư duy cốt lõi của một hệ thống AIOps an toàn được xây dựng dựa trên nguyên tắc **Không tin tưởng tuyệt đối (Zero Trust)**:

~~~
[Yêu cầu từ AI Agent] (JSON-RPC tool call)
          │
          ▼
[Giao thức MCP] (Transport an toàn qua Stdio / SSE)
          │
          ▼
[Xác thực JSON Schema] (Kiểm tra kiểu dữ liệu đầu vào)
          │
          ▼
[Cổng phân quyền RBAC] (Chỉ cho phép role phù hợp)
          │
          ▼
[Rào chắn ngữ nghĩa] (Chặn đứng SSRF & Path Traversal)
          │
          ▼
[Go Handler có giới hạn] (Thực thi trong Sandbox)
          │
          ▼
[Hạ tầng thực tế] (Kubernetes / AWS / Linux OS)
          │
          ▼
[Nhật ký kiểm toán] (Lưu vết bất biến mọi hành vi)
~~~

Trong kiến trúc này:
1. **Ranh giới giao thức (Protocol Boundary):** Agent giao tiếp qua luồng nhập xuất chuẩn (`os.Stdin`/`os.Stdout`), loại bỏ hoàn toàn bề mặt tấn công mạng từ bên ngoài.
2. **Ranh giới kiểu dữ liệu (Schema Boundary):** Đảm bảo các tham số truyền vào đúng định dạng kỹ thuật.
3. **Ranh giới phân quyền (Authorization Boundary):** Tác tử quan sát (Observer) tuyệt đối không thể kích hoạt các công cụ làm thay đổi trạng thái hạ tầng (Mutating Tools).
4. **Ranh giới ngữ nghĩa (Semantic Boundary):** Ngăn chặn Agent bị lừa truy cập vào các địa chỉ mạng nội bộ hoặc dịch vụ siêu dữ liệu nhạy cảm của đám mây (AWS IMDS).
5. **Ranh giới kiểm toán (Audit Boundary):** Mọi hành động đều được ghi lại vĩnh viễn để phục vụ điều tra sự cố.

---

## 2. Model Context Protocol: "Cổng USB-C" cho AI

Giao thức **Model Context Protocol (MCP)** do Anthropic khởi xướng đã nhanh chóng trở thành tiêu chuẩn công nghiệp mở giúp kết nối các mô hình AI với các nguồn dữ liệu và công cụ bên ngoài.

Về bản chất kỹ thuật, MCP vận hành trên nền giao thức **JSON-RPC 2.0**:
- **`tools/list`:** Máy chủ Go công bố danh sách các công cụ mà nó cung cấp kèm theo mô tả chức năng và JSON Schema quy định các tham số đầu vào.
- **`tools/call`:** Khi Agent quyết định sử dụng một công cụ, nó gửi một yêu cầu JSON-RPC chứa tên công cụ và các tham số tương ứng.

### Vì sao ưu tiên Stdio Transport?
Trong môi trường DevOps và container, MCP thường ưu tiên sử dụng giao vận qua luồng nhập xuất chuẩn (`os.Stdin` và `os.Stdout`) thay vì mở cổng mạng HTTP:
- Không cần mở port trong container hay cấu hình tường lửa.
- Không lo lắng về vấn đề xác thực mạng hay tấn công Man-In-The-Middle (MITM).
- Tiến trình AI Agent trực tiếp fork tiến trình máy chủ công cụ Go, giao tiếp qua pipe hệ điều hành với độ trễ tối thiểu.

---

## 3. Ảo tưởng an ninh của JSON Schema và Hiểm họa Prompt Injection

Một sai lầm rất phổ biến của các kỹ sư khi mới tiếp cận MCP là tin tưởng rằng: *"Công cụ đã có JSON Schema chặt chẽ nên an toàn tuyệt đối trước hacker"*.

Đây là một sự ngộ nhận nguy hiểm:
- **JSON Schema chỉ kiểm tra kiểu hình thức (Type Validation):** Nó chỉ xác nhận xem tham số `target_url` có phải là một chuỗi ký tự hay không.
- **JSON Schema hoàn toàn mù lòa trước nội dung ngữ nghĩa (Semantic Blindness):** Nếu kẻ tấn công chèn một đoạn chỉ thị độc hại vào tài liệu log mà Agent đang đọc, khiến Agent gửi tham số:
  `target_url: "http://169.254.169.254/latest/meta-data/iam/security-credentials/"`
  thì chuỗi này **hoàn toàn hợp lệ** theo JSON Schema!

Nếu Go handler nhắm mắt gửi HTTP GET tới URL đó, toàn bộ khóa bí mật IAM tạm thời của máy chủ AWS sẽ bị Agent đọc và trả về cho kẻ tấn công!

Do đó: **Go Handler ở phía sau MCP bắt buộc phải tự mình thực hiện các rào chắn phòng thủ an ninh nghiêm ngặt nhất.**

---

## 4. Rào chắn phòng vệ SSRF trong Go (`ValidateSSRF`)

Tấn công giả mạo yêu cầu từ máy chủ (**Server-Side Request Forgery - SSRF**) là hiểm họa số 1 khi trao công cụ mạng cho Agent.

Hàm kiểm tra được chia thành các lớp phòng thủ rõ ràng. Đầu tiên là kiểm tra giao thức và tên miền cục bộ:

~~~go
func checkSchemeAndHost(u *url.URL) error {
	// 1. Chỉ chấp nhận giao thức an toàn
	if u.Scheme != "http" && u.Scheme != "https" {
		return errors.New(
			"unsupported protocol: only http/https allowed",
		)
	}

	// 2. Chặn truy cập localhost
	if strings.EqualFold(u.Hostname(), "localhost") {
		return errors.New(
			"mcp: ssrf blocked: localhost access forbidden",
		)
	}
	return nil
}
~~~

Tiếp theo là kiểm tra dải IP nhạy cảm (Private RFC 1918, Loopback và Cloud Metadata):

~~~go
func checkSensitiveIP(ip net.IP) error {
	if ip == nil {
		return nil
	}
	if ip.IsLoopback() {
		return errors.New(
			"mcp: ssrf blocked: loopback target prohibited",
		)
	}
	if ip.IsPrivate() {
		return errors.New(
			"mcp: ssrf blocked: private IP forbidden",
		)
	}
	if ip.IsLinkLocalUnicast() ||
		ip.String() == "169.254.169.254" {
		return errors.New(
			"mcp: ssrf blocked: cloud metadata forbidden",
		)
	}
	return nil
}
~~~

Hàm `ValidateSSRF` chính thức tổng hợp các kiểm tra:

~~~go
func ValidateSSRF(rawURL string) error {
	u, err := url.Parse(rawURL)
	if err != nil {
		return fmt.Errorf("invalid target URL: %w", err)
	}
	if err := checkSchemeAndHost(u); err != nil {
		return err
	}
	return checkSensitiveIP(net.ParseIP(u.Hostname()))
}
~~~

### Ba chốt chặn SSRF bất khả xâm phạm:
1. **Loopback (`127.0.0.1`):** Ngăn Agent tấn công các dịch vụ quản trị nội bộ đang lắng nghe trên cổng cục bộ của máy chủ (ví dụ Prometheus metrics endpoint trên port 9090, Redis trên port 6379).
2. **RFC 1918 Private Ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`):** Ngăn Agent rà quét mạng VPC nội bộ của doanh nghiệp.
3. **Cloud Metadata (`169.254.169.254`):** Ngăn Agent truy cập endpoint AWS Instance Metadata Service (IMDS) để đánh cắp IAM credentials của máy chủ EC2/EKS.

---

## 5. Phân quyền vai trò (RBAC) và Thao tác biến đổi có kiểm soát

Không phải tác tử nào cũng có quyền như nhau. Chúng ta thiết lập mô hình kiểm soát truy cập dựa trên vai trò (Role-Based Access Control):

~~~go
type Role string

const (
	RoleObserver Role = "observer" // Chỉ đọc
	RoleOperator Role = "operator" // Đột biến có phiếu
	RoleAdmin    Role = "admin"    // Toàn quyền
)
~~~

### Tách bạch hai nhóm công cụ:
1. **Công cụ chỉ đọc (Read-Only Tools):** Ví dụ `query_service_health`. Cho phép vai trò `observer` tự do truy vấn để thu thập thông tin chẩn đoán.
2. **Công cụ gây đột biến (Mutating Tools):** Ví dụ `restart_service`. 
   - Từ chối thẳng thừng vai trò `observer`.
   - Đối với vai trò `operator`, bắt buộc phải truyền kèm tham số `change_ticket` (mã phiếu thay đổi đã được phê duyệt trong hệ thống Jira/ServiceNow).

~~~go
func (s *MCPServer) AuthorizeCall(
	role Role, toolName string, args map[string]any,
) error {
	switch toolName {
	case "query_service_health":
		return nil // Công cụ chỉ đọc: Cho phép mọi vai trò

	case "restart_service":
		if role == RoleObserver {
			return fmt.Errorf(
				"mcp: denied for role %s on mutating tool %s",
				role, toolName,
			)
		}
		ticket, ok := args["change_ticket"].(string)
		if !ok || strings.TrimSpace(ticket) == "" {
			return errors.New(
				"mcp: mutation denied: missing change_ticket",
			)
		}
		return nil

	default:
		return fmt.Errorf("mcp: unknown tool: %s", toolName)
	}
}
~~~

---

## 6. Thực thi công cụ và Ghi nhật ký kiểm toán bất biến (Audit Trail)

Phương thức `ExecuteToolCall` liên kết toàn bộ chuỗi bảo vệ:

~~~go
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
		s.recordAudit(
			role, params.Name, params.Arguments,
			false, "tool not found",
		)
		return nil, fmt.Errorf(
			"tool not found: %s", params.Name,
		)
	}

	// 1. Chốt chặn Phân quyền RBAC
	if err := s.AuthorizeCall(
		role, params.Name, params.Arguments,
	); err != nil {
		s.recordAudit(
			role, params.Name, params.Arguments,
			false, err.Error(),
		)
		return &CallToolResult{
			IsError: true,
			Content: []ToolContent{{
				Type: "text", Text: err.Error(),
			}},
		}, nil
	}

	// 2. Chốt chặn Ngữ nghĩa và Thực thi
	return s.dispatchExecution(
		role, tool.Name, params.Arguments,
	)
}
~~~

Hàm phụ trợ điều phối thực thi và ghi nhận audit log an toàn thread-safe:

~~~go
func (s *MCPServer) dispatchExecution(
	role Role, name string, args map[string]any,
) (*CallToolResult, error) {
	var resultText string
	switch name {
	case "query_service_health":
		urlStr, _ := args["target_url"].(string)
		if err := ValidateSSRF(urlStr); err != nil {
			s.recordAudit(role, name, args, false, err.Error())
			return &CallToolResult{
				IsError: true,
				Content: []ToolContent{{
					Type: "text", Text: err.Error(),
				}},
			}, nil
		}
		resultText = fmt.Sprintf(
			"Service at %s responded: HTTP 200 OK", urlStr,
		)

	case "restart_service":
		svc, _ := args["service_name"].(string)
		ticket, _ := args["change_ticket"].(string)
		resultText = fmt.Sprintf(
			"Service %s restart initiated under ticket %s",
			svc, ticket,
		)
	}

	s.recordAudit(role, name, args, true, "")
	return &CallToolResult{
		IsError: false,
		Content: []ToolContent{
			{Type: "text", Text: resultText},
		},
	}, nil
}
~~~

Ghi vết kiểm toán với khóa đồng bộ:

~~~go
func (s *MCPServer) recordAudit(
	role Role, tool string, args map[string]any,
	allowed bool, errStr string,
) {
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
~~~

---

## 7. Kiểm chứng Lab thực tế (`labs/part28-mcp-ops-tools`)

Mã nguồn hoàn chỉnh nằm tại `labs/part28-mcp-ops-tools`. Chạy kiểm thử:

~~~bash
go test -v -race ./...
~~~

Bộ kiểm thử xác thực 6 kịch bản thực chiến:

~~~
=== RUN   TestMCPListTools
--- PASS: TestMCPListTools (0.00s)
=== RUN   TestMCPOperatorQueryHealthSuccess
--- PASS: TestMCPOperatorQueryHealthSuccess (0.00s)
=== RUN   TestMCPSSRFPrevention
--- PASS: TestMCPSSRFPrevention (0.00s)
=== RUN   TestMCPAuthorizationBoundaryObserverDenied
--- PASS: TestMCPAuthorizationBoundaryObserverDenied (0.00s)
=== RUN   TestMCPOperatorRestartSuccess
--- PASS: TestMCPOperatorRestartSuccess (0.00s)
=== RUN   TestMCPOperatorMissingTicketDenied
--- PASS: TestMCPOperatorMissingTicketDenied (0.00s)
PASS
ok      part28-mcp-ops-tools   2.049s
~~~

### Phân tích kết quả kiểm thử:
1. **Khai báo công cụ chuẩn mực (`tools/list`):** Danh sách công cụ phản ánh chính xác JSON Schema của tham số đầu vào.
2. **Thực thi đọc hợp lệ:** Vai trò Observer gọi thành công `query_service_health` với URL công khai, ghi nhận `allowed: true` trong nhật ký kiểm toán.
3. **Phòng chống SSRF toàn diện:** Chặn đứng cả 4 nỗ lực độc hại: AWS metadata (`169.254.169.254`), Localhost (`localhost:8080`), Loopback IP (`127.0.0.1`), và Mạng nội bộ (`10.0.1.5`). Mọi nỗ lực đều bị từ chối và ghi log cảnh báo.
4. **Rào chắn phân quyền tác tử:** Observer cố tình gọi `restart_service` bị chặn ngay từ cổng kiểm tra quyền hạn.
5. **Đột biến hợp lệ có kiểm soát:** Operator có mã phiếu thay đổi hợp lệ được phép kích hoạt khởi động lại dịch vụ.
6. **Chặn đột biến không phiếu:** Operator gọi restart nhưng bỏ trống `change_ticket` lập tức bị từ chối.

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
