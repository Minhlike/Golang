# Chương 25 — Git và GitHub dưới góc nhìn của một hệ thống tự động hóa

Trong kỷ nguyên GitOps và tự động hóa hạ tầng (Infrastructure as Code), Git không chỉ là công cụ lưu trữ lịch sử mã nguồn của lập trình viên, mà đã trở thành **Nguồn chân lý duy nhất (Single Source of Truth)** điều khiển toàn bộ hệ thống sản xuất. 

Một commit được merge vào nhánh `main` có thể tự động kích hoạt ArgoCD triển khai ứng dụng lên Kubernetes. Một nhãn (label) được gắn vào Pull Request có thể kích hoạt bot tự động cấp phát môi trường kiểm thử tạm thời (Ephemeral Environment) trên AWS.

Nhưng khi bắt tay viết các công cụ tự động hóa bằng Go, hầu hết kỹ sư đều vấp phải hai sai lầm kiến trúc cơ bản:
1. Đánh đồng trạng thái Git cục bộ với trạng thái máy chủ GitHub.
2. Xử lý sự kiện Webhook như một lời gọi hàm thông thường mà bỏ qua các rủi ro bảo mật và tính lũy đẳng phân tán.

Chương này phân tích sâu bản chất kỹ thuật của Git và GitHub dưới góc nhìn của một hệ thống hướng sự kiện (Event-Driven System), từ đó hướng dẫn bạn xây dựng các bot tự động hóa chuẩn mực bằng Go.

---

## 1. Hai thế giới: Trạng thái Git cục bộ và Trạng thái GitHub

Câu hỏi trung tâm của chương này là:
> *Vì sao một hệ thống tự động hóa tin cậy phải tách bạch hoàn toàn giữa Trạng thái Git (Local Git State) và Trạng thái GitHub (GitHub Hosted State)?*

~~~
           [THẾ GIỚI GIT CỤC BỘ]
   (Độc lập, Phi tập trung, Nội dung định danh)
   ├── Object Store: Blob, Tree, Commit, Tag
   ├── DAG:          Đồ thị có hướng không chu trình
   └── Commit SHA:   Khóa băm toàn vẹn SHA-1 / SHA-256
                           ≠
          [THẾ GIỚI GITHUB HOSTED]
       (Tập trung, Phụ thuộc mạng & Quota)
   ├── Pull Requests, Issue Comments, Reviews
   ├── Check Runs, Status API, Releases
   └── Webhooks, Permission RBAC, Rate Limits
~~~

### So sánh hai mô hình dữ liệu:

1. **Trạng thái Git cục bộ (`go-git/v5`):**
   - Vận hành trên cấu trúc dữ liệu đồ thị có hướng không chu trình (DAG). Mỗi commit trỏ tới một cây thư mục (Tree) chứa các tệp tin (Blob).
   - Được định danh hoàn toàn bằng mã băm nội dung (**Content-Addressed Storage**). Nếu nội dung file không đổi, mã băm vĩnh viễn không đổi.
   - Hoạt động offline, độ trễ microsecond, không tốn chi phí mạng.
2. **Trạng thái GitHub (`google/go-github/v68`):**
   - Là tầng ứng dụng quản trị tập trung (Hosted Metadata). Các khái niệm như "Pull Request", "Reviewers", hay "Issue Labels" hoàn toàn không tồn tại trong cấu trúc dữ liệu gốc của Git.
   - Giao tiếp qua REST hoặc GraphQL API, phụ thuộc hoàn toàn vào đường truyền mạng và giới hạn số lượt gọi (Rate Limit).

Một bot tự động hóa chuyên nghiệp luôn biết kết hợp cả hai: dùng `go-git` để thao tác cây thư mục trên bộ nhớ với tốc độ cao, và dùng `go-github` để tương tác với người dùng và quy trình làm việc.

---

## 2. Bảo mật Webhook: Chống Timing Attack bằng HMAC-SHA256

Khi GitHub gửi một sự kiện (ví dụ `pull_request.opened`) đến máy chủ của bạn qua HTTP Webhook, làm sao bạn biết chắc chắn thông điệp này thực sự do GitHub phát ra chứ không phải do một kẻ xấu giả mạo?

GitHub ký toàn bộ nội dung gói tin (raw payload) bằng mã khóa bí mật (Webhook Secret) thông qua thuật toán HMAC-SHA256, và đính kèm vào header:
`X-Hub-Signature-256: sha256=<hex_digest>`

~~~
GitHub phát sự kiện                   Máy chủ nhận sự kiện (Go)
       │                                         │
       ▼                                         ▼
[Tính HMAC-SHA256]                       [Tính HMAC-SHA256]
(Secret + Payload)                       (Secret + Payload)
       │                                         │
       ▼                                         ▼
Header: sha256=a1b2c3...          Expected: sha256=a1b2c3...
       │                                         │
       └────────── Gửi HTTP POST ───────────────>┤
                                                 │
                                       [So sánh an toàn:]
                                    subtle.ConstantTimeCompare
~~~

### Cạm bẫy tấn công thời gian (Timing Attack)

Nếu bạn dùng toán tử thông thường để so sánh chữ ký:

~~~go
// CẢNH BÁO TỬ HUYỆT: Rò rỉ thông tin qua thời gian thực thi!
if actualSig == expectedSig { ... }
~~~

Toán tử `==` trong Go so sánh từng byte từ trái qua phải và trả về `false` ngay khi gặp byte sai lệch đầu tiên. 

Kẻ tấn công có thể gửi hàng ngàn request với các byte đoán trước và đo thời gian phản hồi ở mức nano-giây. Thời gian phản hồi càng lâu chứng tỏ càng nhiều byte đầu tiên khớp đúng. Bằng cách này, kẻ xấu có thể giải mã từng ký tự của chữ ký mà không cần biết khóa bí mật!

### Giải pháp bắt buộc: crypto/subtle

Trong Go, bạn bắt buộc phải dùng hàm `subtle.ConstantTimeCompare`:

~~~go
func VerifyHMACSHA256(
	payload []byte, signatureHeader string, secret []byte,
) bool {
	if !strings.HasPrefix(signatureHeader, "sha256=") {
		return false
	}
	actualHex := strings.TrimPrefix(signatureHeader, "sha256=")
	actualSig, err := hex.DecodeString(actualHex)
	if err != nil {
		return false
	}

	mac := hmac.New(sha256.New, secret)
	mac.Write(payload)
	expectedSig := mac.Sum(nil)

	// So sánh thời gian cố định, chống timing attack
	match := subtle.ConstantTimeCompare(
		actualSig, expectedSig,
	)
	return match == 1
}
~~~

Hàm này luôn duyệt qua toàn bộ chuỗi byte bất kể byte sai nằm ở đâu, triệt tiêu hoàn toàn nguy cơ rò rỉ qua kênh phụ.

---

## 3. Khế ước phân tán: Delivery ID và Tính Lũy Đẳng

GitHub gửi webhook theo nguyên lý **At-Least-Once Delivery** (Phát ít nhất một lần).

Khi mạng chập chờn hoặc máy chủ của bạn xử lý tác vụ quá 10 giây khiến HTTP response bị timeout, GitHub sẽ tự động gửi lại sự kiện đó lần thứ hai hoặc thứ ba.

Mỗi lần gửi, GitHub cấp một mã UUID duy nhất tại header:
`X-GitHub-Delivery: 7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d`

~~~
GitHub Server                           Máy chủ Webhook (Go)
     │                                           │
     ├─ 1. Delivery "7a1b..." ──────────────────>│ (Xử lý OK)
     │  <── HTTP 504 Timeout ────────────────────┤ (Rớt mạng)
     │                                           │
     ├─ 2. Delivery "7a1b..." (Gửi lại) ────────>│
     │                                           ├─ Đã xử lý?
     │  <── HTTP 200 OK (status: duplicate) ─────┴─ BỎ QUA!
~~~

Nếu chương trình của bạn không kiểm tra `X-GitHub-Delivery`, bạn có thể vô tình tạo 2 bản phát hành (release), comment 2 lần lên PR, hoặc kích hoạt 2 pipeline build trùng lặp.

Thiết kế bộ tiếp nhận có kiểm tra trùng lặp:

~~~go
type WebhookReceiver struct {
	mu        sync.Mutex
	secret    []byte
	delivered map[string]time.Time
}

func (r *WebhookReceiver) Process(
	deliveryID, signature string, payload []byte,
) (bool, error) {
	if !VerifyHMACSHA256(payload, signature, r.secret) {
		return false, ErrInvalidSignature
	}

	r.mu.Lock()
	defer r.mu.Unlock()

	// Khử trùng lặp: Nếu ID đã xử lý, báo duplicate và bỏ qua
	if _, exists := r.delivered[deliveryID]; exists {
		return true, nil
	}

	r.delivered[deliveryID] = time.Now()
	return false, nil
}
~~~

---

## 4. Quản trị Rate Limit: Primary và Secondary

Khi bot tự động hóa tương tác với GitHub API, rào cản lớn nhất trên môi trường production là chính sách kiểm soát tần suất (**Rate Limiting**).

GitHub áp dụng hai tầng rào chắn:

| Tầng rào chắn | Hạn mức áp dụng | Dấu hiệu phản hồi | Chiến lược ứng phó |
| :--- | :--- | :--- | :--- |
| **Primary Rate Limit** | 5.000 requests/giờ cho tài khoản xác thực. | `X-RateLimit-Remaining: 0`<br>`X-RateLimit-Reset: <epoch>` | Ngủ (Sleep) chính xác tới mốc `ResetAt`, không gửi thêm request. |
| **Secondary Rate Limit** | Chống spam và gọi đồng thời quá nhanh. | HTTP `403` hoặc `429`<br>`Retry-After: <seconds>` | Ngừng ngay lập tức trong số giây quy định, áp dụng backoff có jitter. |

### Thuật toán bóc tách Rate Limit trong Go

~~~go
func ParseRateLimit(
	header http.Header, now time.Time,
) RateLimitStatus {
	status := RateLimitStatus{}

	remStr := header.Get("X-RateLimit-Remaining")
	if remStr != "" {
		if rem, err := strconv.Atoi(remStr); err == nil {
			status.Remaining = rem
			if rem == 0 {
				status.IsExhausted = true
			}
		}
	}

	resetStr := header.Get("X-RateLimit-Reset")
	if resetStr != "" {
		epoch, err := strconv.ParseInt(resetStr, 10, 64)
		if err == nil {
			status.ResetAt = time.Unix(epoch, 0)
			if status.IsExhausted && status.ResetAt.After(now) {
				status.RetryAfter = status.ResetAt.Sub(now)
			}
		}
	}

	// Secondary rate limit dùng header Retry-After
	retryStr := header.Get("Retry-After")
	if retryStr != "" {
		if sec, err := strconv.Atoi(retryStr); err == nil {
			status.RetryAfter = time.Duration(sec) * time.Second
			status.IsExhausted = true
		}
	}
	return status
}
~~~

---

## 5. Thao tác Git trên bộ nhớ (In-memory Git) với go-git

Khi viết bot tự động tạo commit hoặc cập nhật file cấu hình (GitOps bot), việc gọi lệnh `exec.Command("git", ...)` ra ngoài hệ điều hành mang lại nhiều phiền toái:
- Phải cài đặt binary `git` trong Docker container.
- Phải quản lý thư mục tạm trên ổ đĩa, dễ bị xung đột file hoặc rò rỉ dữ liệu khi container crash.

Thư viện `github.com/go-git/go-git/v5` cho phép bạn khởi tạo một kho lưu trữ Git hoàn toàn trên bộ nhớ RAM (**In-memory Repository**) bằng cách kết hợp `memory.NewStorage()` và `memfs.New()`:

~~~go
func NewInMemGitRepository() (*InMemGitRepository, error) {
	fs := memfs.New()
	storer := memory.NewStorage()

	repo, err := git.Init(storer, fs)
	if err != nil {
		return nil, fmt.Errorf("lỗi init git mem: %w", err)
	}

	return &InMemGitRepository{repo: repo, fs: fs}, nil
}
~~~

Ghi file và tạo commit với chữ ký tác giả trong bộ nhớ:

~~~go
func (r *InMemGitRepository) WriteFileAndCommit(
	filePath string, content []byte, author, msg string,
) (string, error) {
	wt, err := r.repo.Worktree()
	if err != nil {
		return "", err
	}

	f, err := r.fs.Create(filePath)
	if err != nil {
		return "", err
	}
	_, _ = f.Write(content)
	_ = f.Close()

	if _, err := wt.Add(filePath); err != nil {
		return "", err
	}

	hash, err := wt.Commit(msg, &git.CommitOptions{
		Author: &object.Signature{
			Name:  author,
			Email: author + "@bot.local",
			When:  time.Now(),
		},
	})
	if err != nil {
		return "", err
	}
	return hash.String(), nil
}
~~~

Toàn bộ quá trình tạo commit, tính hash SHA, và cập nhật HEAD diễn ra ở tốc độ bộ nhớ RAM mà không ghi dù chỉ 1 byte xuống đĩa cứng vật lý!

---

## 6. Bằng chứng kiểm thử: Chứng minh 4 quy luật tự động hóa

Bộ kiểm thử tại `labs/part25-github-automation/automation_test.go` xác thực toàn diện các ranh giới an toàn:

~~~
=== RUN   TestWebhookHMACVerification
--- PASS: TestWebhookHMACVerification (0.00s)
=== RUN   TestWebhookDeliveryIdempotency
--- PASS: TestWebhookDeliveryIdempotency (0.00s)
=== RUN   TestRateLimitParsingPrimaryAndSecondary
--- PASS: TestRateLimitParsingPrimaryAndSecondary (0.00s)
=== RUN   TestInMemGitCommitAndHead
--- PASS: TestInMemGitCommitAndHead (0.00s)
PASS
ok      part25-github-automation   3.653s
~~~

### 1. Xác thực chữ ký an toàn (TestWebhookHMACVerification)
Kiểm chứng 4 ca biên:
- Chữ ký đúng định dạng `sha256=` và secret hợp lệ: **PASS**.
- Sửa đổi 1 byte trong payload: **TỪ CHỐI**.
- Dùng sai Webhook Secret: **TỪ CHỐI**.
- Header sai định dạng: **TỪ CHỐI**.

### 2. Khử trùng lặp sự kiện (TestWebhookDeliveryIdempotency)
Bắn 2 webhook mang cùng một `X-GitHub-Delivery`. Lần đầu tiên xử lý thành công (`isDuplicate = false`). Lần thứ hai được nhận diện chính xác là sự kiện gửi lặp (`isDuplicate = true`), bảo vệ hệ thống không bị kích hoạt kép.

### 3. Bóc tách Rate Limit hai tầng (TestRateLimitParsing)
Kiểm chứng cả hai tình huống:
- Khi chạm trần Primary Quota (`Remaining: 0`), tính đúng thời gian cần chờ đến mốc `ResetAt`.
- Khi chạm trần Secondary Quota (`Retry-After: 120`), chuyển đổi chính xác thành khoảng chờ 120 giây.

### 4. Vận hành Git trên RAM (TestInMemGitCommitAndHead)
Tạo liên tiếp 2 commit trong bộ nhớ RAM, kiểm tra mã băm SHA của commit thứ nhất và thứ hai, xác nhận con trỏ HEAD dịch chuyển chuẩn xác theo đồ thị DAG.

---

## 7. Các cạm bẫy người học thường gặp (Learner Pitfalls)

| Cạm bẫy thực tế | Hậu quả trên Production | Giải pháp phòng ngừa |
| :--- | :--- | :--- |
| **So sánh chữ ký bằng ==** thay vì ConstantTimeCompare. | Rò rỉ thông tin qua thời gian thực thi, bị kẻ xấu tấn công vét cạn chữ ký số. | Bắt buộc dùng `crypto/subtle.ConstantTimeCompare`. |
| **Bỏ qua X-GitHub-Delivery** và xử lý mù quáng mọi webhook. | Gây trùng lặp hành vi (tạo 2 PR, merge 2 lần) khi mạng chập chờn khiến GitHub gửi lại. | Lưu `X-GitHub-Delivery` vào bộ đệm và bỏ qua các sự kiện trùng lặp. |
| **Gọi API ồ ạt trong vòng lặp** mà không kiểm tra Remaining. | Nhanh chóng làm cạn kiệt 5.000 request/giờ, khiến toàn bộ bot của tổ chức bị tê liệt. | Đọc `X-RateLimit-Remaining`. Chủ động ngủ khi quota chạm ngưỡng an toàn (ví dụ còn dưới 50). |
| **Ghi file tạm ra ổ đĩa** khi thao tác Git trong container. | Gây phân mảnh ổ đĩa, rò rỉ dữ liệu nhạy cảm và xung đột tiến trình đồng thời. | Dùng `go-git` kết hợp `memfs` và `memory.NewStorage()` trên RAM. |

---

## 8. Bài tập thực hành thiết kế Bot Tự động hóa

### Thử thách 1: Lọc sự kiện theo nhánh (Branch Filtering Middleware)
**Yêu cầu:** Một webhook `push` được gửi tới mỗi khi có commit mới. Hãy viết hàm lọc sự kiện chỉ cho phép xử lý nếu sự kiện nhắm vào nhánh `refs/heads/main`. Bỏ qua tất cả các sự kiện của nhánh tính năng (`feature/*`) mà không kích hoạt quy trình triển khai.

### Thử thách 2: Bộ điều tốc thông minh (Smart Backoff with Jitter)
**Yêu cầu:** Khi nhận được header `Retry-After: 30`, nếu 100 worker cùng thức dậy sau đúng 30 giây, chúng sẽ tạo ra một cơn bão yêu cầu mới (Thundering Herd) khiến tài khoản bị khóa tiếp. Hãy viết hàm tính toán thời gian ngủ bổ sung một lượng dao động ngẫu nhiên (**Jitter**) từ 10% đến 25% giá trị quy định.

---

## 9. Hướng dẫn giải và Phân tích kiến trúc bài tập

### Lời giải Thử thách 1: Lọc sự kiện theo nhánh đích

~~~go
type PushPayload struct {
	Ref string `json:"ref"`
}

func ShouldDeployFromWebhook(payload []byte) bool {
	var push PushPayload
	if err := json.Unmarshal(payload, &push); err != nil {
		return false
	}

	// Chỉ kích hoạt tự động hóa trên nhánh chính thức
	return push.Ref == "refs/heads/main"
}
~~~

### Lời giải Thử thách 2: Tính toán Backoff kết hợp Jitter

~~~go
func CalculateBackoffWithJitter(
	baseDelay time.Duration,
) time.Duration {
	if baseDelay <= 0 {
		baseDelay = 5 * time.Second
	}

	// Tạo độ lệch ngẫu nhiên từ 10% đến 25%
	jitterFactor := 0.10 + rand.Float64()*0.15
	jitter := time.Duration(
		float64(baseDelay) * jitterFactor,
	)

	return baseDelay + jitter
}
~~~

Bổ sung Jitter giúp phân tán các lượt thử lại của các worker trên trục thời gian, triệt tiêu hoàn toàn hiện tượng bão yêu cầu đồng thời.

---

Nắm vững cách vận hành **HMAC-SHA256 + Delivery Idempotency + Rate-Limit-Aware Client + In-Memory Git** giúp bạn tự tin xây dựng những hệ thống GitOps và CI/CD bot an toàn, vững chắc. Trong Chương 26, chúng ta sẽ mở rộng năng lực bảo vệ phần mềm lên tầm chuỗi cung ứng: xây dựng **Cổng kiểm soát chuỗi cung ứng phần mềm có thể kiểm chứng (Supply Chain Verification Gate)** bằng Go với chữ ký số Cosign không cần khóa (keyless), OCI manifest digest bất biến và quét lỗ hổng mã nguồn bằng `govulncheck`.
