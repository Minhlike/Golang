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

### Hai mô hình dữ liệu song hành

Trạng thái Git cục bộ và trạng thái dịch vụ GitHub đại diện cho hai triết lý lưu trữ hoàn toàn khác biệt. Ở tầng cục bộ thông qua thư viện `go-git/v5`, dữ liệu vận hành trên cấu trúc đồ thị có hướng không chu trình (DAG). Mỗi commit trỏ tới một cây thư mục (Tree) và các khối dữ liệu nhị phân (Blob), được định danh chặt chẽ bằng mã băm nội dung (Content-Addressed Storage). Khi nội dung tệp tin không thay đổi, mã định danh của nó vĩnh viễn bất biến. Toàn bộ thao tác đọc ghi này diễn ra trong không gian tiến trình hoặc trên bộ nhớ RAM với độ trễ micro-giây, hoàn toàn độc lập với kết nối mạng bên ngoài.

Ngược lại, trạng thái lưu trữ trên GitHub thông qua thư viện `go-github/v92` do Google duy trì là tầng siêu dữ liệu quản trị tập trung (Hosted Metadata). Các thực thể như Pull Request, nhãn phân loại, đánh giá mã nguồn hay lượt duyệt đều không tồn tại trong cấu trúc cây nhị phân thuần túy của Git. Mọi giao tiếp với tầng này đều thực hiện qua REST hoặc GraphQL API, đòi hỏi kết nối mạng và chịu sự ràng buộc nghiêm ngặt của hạn ngạch tần suất gọi (Rate Limit). Một hệ thống tự động hóa hoàn chỉnh luôn biết kết hợp cả hai mô hình: sử dụng `go-git` để phân tích và chuẩn bị cây commit tốc độ cao trên bộ đệm, đồng thời sử dụng `go-github` để cập nhật trạng thái kiểm thử và phản hồi với lập trình viên.

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

### Rủi ro rò rỉ thông tin qua thời gian thực thi (Timing Side-Channel)

Nếu bạn dùng toán tử thông thường để so sánh chữ ký:

~~~go
// CẢNH BÁO: Rò rỉ thông tin qua thời gian thực thi!
if actualSig == expectedSig { ... }
~~~

Toán tử so sánh chuỗi hoặc mảng byte mặc định trong hầu hết ngôn ngữ lập trình thường kết thúc sớm (early exit) ngay khi phát hiện byte không trùng khớp đầu tiên. Sự chênh lệch thời gian xử lý này vô tình tạo ra một kênh phụ (side-channel). Dù độ trễ biến thiên trên mạng Internet công cộng có thể làm nhiễu tín hiệu đo đạc, trong các môi trường nội bộ, mạng cục bộ tốc độ cao hoặc qua phương pháp phân tích thống kê trên lượng mẫu thử lớn, việc so sánh không hằng số thời gian vẫn có thể cung cấp manh mối để kẻ tấn công thu hẹp không gian tìm kiếm mã xác thực.

### Giải pháp bắt buộc: crypto/hmac.Equal hoặc crypto/subtle

Trong Go, bạn bắt buộc phải dùng hàm `hmac.Equal` hoặc `subtle.ConstantTimeCompare`:

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

	// So sánh hằng số thời gian (constant-time)
	return hmac.Equal(actualSig, expectedSig)
}
~~~

Hàm `hmac.Equal` là API chuẩn của Go để so sánh hai mã xác thực thông điệp (MAC) mà không làm lộ thông tin qua thời gian thực thi (constant-time comparison), ngăn ngừa các nguy cơ khai thác kênh phụ (timing side-channel).

---

## 3. Khế ước phân tán: Delivery ID và Tính Lũy Đẳng

Trong kiến trúc tích hợp webhook, một ngộ nhận phổ biến là cho rằng GitHub sẽ tự động thử lại (auto-retry) mỗi khi máy chủ nhận trả về mã lỗi 5xx hoặc bị timeout. Trên thực tế, trong các cấu hình webhook tiêu chuẩn, GitHub không tự động redeliver khi endpoint nhận bị lỗi. Việc redelivery chỉ xảy ra khi có thao tác kích hoạt lại từ người vận hành qua giao diện quản trị (Operator UI), lời gọi REST API redeliver từ mã nguồn tự động hóa, hoặc các công cụ nội bộ gọi API này. Khi một lần chuyển giao được kích hoạt lại (redelivered), GitHub giữ nguyên giá trị GUID trong header `X-GitHub-Delivery`.

Mỗi lần phát sự kiện, GitHub đính kèm một mã UUID duy nhất tại header:
`X-GitHub-Delivery: 7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d`

~~~
GitHub / Quản trị viên / API         Máy chủ Webhook (Go)
      │                                       │
      ├─ 1. Delivery "7a1b..." ──────────────>│ (Xử lý OK)
      │                                       │
      ├─ 2. Delivery "7a1b..." (Redeliver) ──>│
      │                                       ├─ Đã lưu ID?
      │  <── HTTP 200 OK (duplicate) ─────────┴─ BỎ QUA!
~~~

Mã định danh `X-GitHub-Delivery` là khóa hữu ích để khử trùng lặp (deduplicate), xử lý redelivery và ngăn ngừa phát lại (replay). Khi một delivery được người vận hành kích hoạt lại (redeliver) qua giao diện quản trị hoặc qua REST API, GitHub giữ nguyên cùng một mã GUID, cho phép ứng dụng nhận diện ID đã qua xử lý để bỏ qua an toàn mà không phát hành release trùng lặp hay kích hoạt triển khai kép.

Tuy nhiên, cần nhận thức rõ ranh giới bền bỉ: trong mã nguồn lab thực hành, danh sách delivery ID chỉ được lưu tạm thời trên bộ nhớ RAM thông qua cấu trúc `map[string]time.Time`. Do đó, cam kết khử trùng lặp chỉ tồn tại trong vòng đời của tiến trình (process lifetime). Ngay khi tiến trình khởi động lại hoặc container bị điều phối lại, toàn bộ trạng thái khử trùng lặp trong bộ nhớ sẽ bị mất.

Trên môi trường production thực tế, một hệ thống tự động hóa chịu lỗi đòi hỏi phải kết hợp một trong các cơ chế sau:
1. **Durable idempotency store**: Lưu trữ delivery ID vào kho dữ liệu phân tán có TTL (như Redis hoặc DynamoDB).
2. **Ràng buộc duy nhất trong cơ sở dữ liệu (Database uniqueness/transaction)**: Ghi delivery ID vào bảng sự kiện với ràng buộc khóa duy nhất (unique constraint) trong cùng transaction xử lý nghiệp vụ.
3. **Mã định danh thao tác (Operation identity)**: Sinh token lũy đẳng gắn với trạng thái cụ thể của tài nguyên đích thay vì chỉ dựa vào sự kiện webhook.
4. **Bản chất nghiệp vụ tự lũy đẳng (Idempotent domain mutation)**: Thiết kế các tác vụ thay đổi hạ tầng theo dạng khai báo (declarative desired-state) để việc thực thi lặp lại nhiều lần vẫn tạo ra cùng một kết quả hội tụ duy nhất.

Thiết kế bộ tiếp nhận có kiểm tra trùng lặp trong bộ nhớ:

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

Tuyệt đối không xem "5.000 requests/giờ" là con số phổ quát cố định. GitHub áp dụng hạn mức phân cấp tùy theo loại định danh và ngữ cảnh ủy quyền:

| Loại định danh (Authentication Context) | Hạn mức Primary Quota | Dấu hiệu nhận diện |
| :--- | :--- | :--- |
| **Chưa xác thực (Unauthenticated)** | 60 requests/giờ (tính theo địa chỉ IP) | Dễ bị nghẽn trong môi trường NAT/CI chung |
| **Personal Access Token (PAT) / OAuth User** | 5.000 requests/giờ cho mỗi người dùng | `X-RateLimit-Limit: 5000` |
| **GitHub App: User-to-Server** | 5.000 requests/giờ cho mỗi người dùng | Áp dụng khi app hành động thay mặt user |
| **GitHub App: Installation (Non-Enterprise)** | Base 5.000 req/h; nếu repos > 20: +50/h/repo; nếu org users > 20: +50/h/user; trần tối đa 12.500 req/h | Phù hợp nhất cho bot tự động hóa cấp tổ chức |
| **GitHub App: Enterprise Cloud Installation** | Trần tối đa 15.000 requests/giờ | Áp dụng cho tổ chức trên GitHub Enterprise Cloud |
| **GITHUB_TOKEN trong GitHub Actions** | 1.000 requests/giờ cho mỗi repository (hoặc Enterprise rate nếu resource thuộc Enterprise Cloud) | Áp dụng cho runner tiêu chuẩn trong GitHub Actions |
| **GitHub Enterprise Server (On-Premises)** | Cấu hình độc lập bởi quản trị viên hệ thống | Tùy biến theo chính sách triển khai tự lưu trữ |

Song song với Primary Rate Limit theo giờ, GitHub áp dụng **Secondary Rate Limit** để chống lạm dụng (Abuse Detection) khi bot gửi quá nhiều request đồng thời hoặc tạo tài nguyên quá nhanh (trả về mã HTTP `403` hoặc `429` kèm header `Retry-After`).

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

## 5. Tương tác GitHub API (`go-github/v92`) và Git trên bộ nhớ (`go-git/v5`)

Một công cụ tự động hóa toàn diện cần tương tác đồng thời với cả hai thế giới: giao tiếp với GitHub API thông qua thư viện `go-github/v92` do Google duy trì để truy xuất siêu dữ liệu, và thao tác cây thư mục Git cục bộ thông qua `go-git/v5`.

### Tích hợp GitHub Client

Trong gói `labs/part25-github-automation/github_client.go`, ta đóng gói `github.Client` để hỗ trợ cấu hình linh hoạt endpoint mạng (cho phép trỏ tới máy chủ kiểm thử cục bộ `httptest.Server` hoặc máy chủ GitHub Enterprise):

~~~go
type GitHubClient struct {
	client *github.Client
}

func NewGitHubClient(
	httpClient *http.Client, baseURL string,
) (*GitHubClient, error) {
	var opts []github.ClientOptionsFunc
	if httpClient != nil {
		opts = append(opts, github.WithHTTPClient(httpClient))
	}
	if baseURL != "" {
		if !strings.HasSuffix(baseURL, "/") {
			baseURL += "/"
		}
		opts = append(opts, github.WithURLs(&baseURL, nil))
	}
	gh, err := github.NewClient(opts...)
	if err != nil {
		return nil, fmt.Errorf("bad client options: %w", err)
	}
	return &GitHubClient{client: gh}, nil
}

func (c *GitHubClient) GetRepository(
	ctx context.Context, owner, repo string,
) (*github.Repository, *github.Rate, error) {
	repository, resp, err := c.client.Repositories.Get(
		ctx, owner, repo,
	)
	if err != nil {
		return nil, nil, err
	}
	var rate *github.Rate
	if resp != nil {
		rate = &resp.Rate
	}
	return repository, rate, nil
}
~~~

### Thao tác Git trên bộ nhớ (In-memory Git) với go-git

Khi viết bot tự động tạo commit hoặc cập nhật file cấu hình (GitOps bot), việc gọi trực tiếp lệnh CLI `git` ra ngoài hệ điều hành đòi hỏi phụ thuộc vào môi trường máy chủ và phát sinh các thư mục tạm dễ xung đột. Thư viện `github.com/go-git/go-git/v5` cho phép khởi tạo một kho lưu trữ Git hoàn toàn trên bộ nhớ RAM (`In-memory Repository`) bằng cách kết hợp `memory.NewStorage()` và `memfs.New()`:

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

Toàn bộ quá trình tạo commit, tính hash SHA, và cập nhật HEAD diễn ra ở tốc độ bộ nhớ RAM mà không ghi dù chỉ 1 byte xuống đĩa cứng vật lý.

---

## 6. Bằng chứng kiểm thử: Chứng minh 5 quy luật tự động hóa

Bộ kiểm thử tại `labs/part25-github-automation/` vận hành độc lập (phân loại kiểm chứng: `UNIT_TESTED` cho toàn bộ các thành phần webhook receiver, HMAC validation, idempotency filter, rate-limit parser, in-memory Git DAG, và `MOCK_VERIFIED` cho lời gọi `go-github` qua `httptest.Server`), chứng minh tính đúng đắn ở các ranh giới bảo mật và khế ước dữ liệu:

~~~
=== RUN   TestWebhookHMACVerification
--- PASS: TestWebhookHMACVerification (0.00s)
=== RUN   TestWebhookDeliveryIdempotency
--- PASS: TestWebhookDeliveryIdempotency (0.00s)
=== RUN   TestRateLimitParsingPrimaryAndSecondary
--- PASS: TestRateLimitParsingPrimaryAndSecondary (0.00s)
=== RUN   TestInMemGitCommitAndHead
--- PASS: TestInMemGitCommitAndHead (0.00s)
=== RUN   TestGitHubClientIntegrationWithMockServer
--- PASS: TestGitHubClientIntegrationWithMockServer (0.00s)
PASS
ok      part25-github-automation   0.263s
~~~

### 1. Xác thực chữ ký an toàn (TestWebhookHMACVerification)
Kiểm chứng 4 ca biên: chữ ký đúng định dạng `sha256=` với secret hợp lệ; từ chối khi sửa đổi 1 byte trong payload; từ chối khi dùng sai Webhook Secret; và từ chối khi header sai định dạng.

### 2. Khử trùng lặp sự kiện (TestWebhookDeliveryIdempotency)
Gửi 2 webhook mang cùng một `X-GitHub-Delivery`. Lần đầu tiên xử lý thành công (`isDuplicate = false`). Lần thứ hai được nhận diện chính xác là sự kiện gửi lặp (`isDuplicate = true`), bảo vệ hệ thống không bị kích hoạt kép khi có redelivery từ UI hoặc qua REST API.

### 3. Bóc tách Rate Limit hai tầng (TestRateLimitParsing)
Kiểm chứng cả hai tình huống: khi chạm trần Primary Quota (`Remaining: 0`), tính đúng thời gian cần chờ đến mốc `ResetAt`; khi chạm trần Secondary Quota (`Retry-After: 120`), chuyển đổi chính xác thành khoảng chờ 120 giây.

### 4. Vận hành Git trên RAM (TestInMemGitCommitAndHead)
Tạo liên tiếp 2 commit trong bộ nhớ RAM, kiểm tra mã băm SHA của commit thứ nhất và thứ hai, xác nhận con trỏ HEAD dịch chuyển chuẩn xác theo đồ thị DAG.

### 5. Tương tác GitHub Client (TestGitHubClientIntegrationWithMockServer)
Kiểm chứng việc khởi tạo client `google/go-github/v92`, định tuyến qua máy chủ giả lập `httptest.Server`, trích xuất chính xác cấu trúc repository và thông tin hạn mức `Rate` từ tiêu đề phản hồi.

---

## 7. Các cạm bẫy người học thường gặp (Learner Pitfalls)

| Cạm bẫy thực tế | Hậu quả trên Production | Giải pháp phòng ngừa |
| :--- | :--- | :--- |
| **So sánh chữ ký bằng ==** thay vì `hmac.Equal`. | Rò rỉ thông tin qua thời gian thực thi, bị kẻ xấu tấn công vét cạn chữ ký số. | Bắt buộc dùng `crypto/hmac.Equal` hoặc `crypto/subtle.ConstantTimeCompare`. |
| **Bỏ qua X-GitHub-Delivery** và xử lý mù quáng mọi webhook. | Gây trùng lặp hành vi (tạo 2 PR, merge 2 lần) khi có redelivery từ UI hoặc qua REST API. | Lưu `X-GitHub-Delivery` vào bộ đệm và bỏ qua các sự kiện trùng lặp. |
| **Gọi API ồ ạt trong vòng lặp** mà không kiểm tra Remaining. | Nhanh chóng làm cạn kiệt hạn mức quota (1.000–12.500 req/h), làm tê liệt bot tự động hóa. | Đọc `X-RateLimit-Remaining`. Chủ động ngủ khi quota chạm ngưỡng an toàn (ví dụ còn dưới 50). |
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

	// Chỉ kích hoạt tự động hóa trên nhánh chính (main)
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
