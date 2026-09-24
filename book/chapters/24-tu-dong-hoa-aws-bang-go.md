# Chương 24 — Tự động hóa AWS bằng Go mà không biến credential thành bí mật dài hạn

Trong hành trình xây dựng các công cụ vận hành và nền tảng hạ tầng, giao tiếp với các dịch vụ điện toán đám mây là nhiệm vụ thiết yếu của kỹ sư DevOps/SRE. Cho dù bạn viết công cụ dọn dẹp snapshot định kỳ, sao lưu cơ sở dữ liệu lên Amazon S3, hay điều phối máy chủ qua EC2, bạn đều phải trả lời một câu hỏi bảo mật sống còn:

> *Làm thế nào để chương trình Go giao tiếp an toàn với AWS API mà không bao giờ nhúng Access Key dài hạn vào mã nguồn, file cấu hình hay biến môi trường?*

Theo các báo cáo bảo mật đám mây, việc để lộ cặp khóa `AWS_ACCESS_KEY_ID` và `AWS_SECRET_ACCESS_KEY` dài hạn (static credentials) trên kho mã nguồn công khai hoặc nhật ký CI/CD là nguyên nhân hàng đầu khiến các doanh nghiệp bị xâm phạm hạ tầng.

Chương này trang bị cho bạn tư duy thiết kế hệ thống tự động hóa đám mây hiện đại dựa trên thư viện chính thức **AWS SDK for Go v2**: từ cơ chế cấp quyền động ngắn hạn (Temporary Credentials), ngăn xếp middleware Smithy, ký chữ ký số **SigV4**, đến duyệt dữ liệu lớn qua **Paginator** và phân loại lỗi chuẩn mực.

---

## 1. Chuỗi định danh ngầm định và Quyền tạm thời

Thay vì lưu trữ khóa tĩnh dài hạn, nguyên lý bảo mật đám mây hiện đại yêu cầu mọi chương trình chạy trên hạ tầng phải sử dụng **Thông tin xác thực tạm thời (Temporary Credentials)** được cấp phát động bởi dịch vụ AWS Security Token Service (STS).

Các khóa tạm thời này có thời hạn hiệu lực hữu hạn: thời lượng phiên của IAM Role có thể cấu hình linh hoạt từ 15 phút tới 12 giờ tùy theo cấu hình vai trò, trong khi các cơ chế phiên liên kết (chained roles) hay `AssumeRoleWithWebIdentity` áp dụng giới hạn riêng. Mỗi bộ thông tin xác thực tạm thời luôn gắn liền với một Session Token (`AWS_SESSION_TOKEN`). Cần đặc biệt lưu ý: nếu khóa tạm thời bị rò rỉ trong thời gian còn hiệu lực, kẻ tấn công vẫn có thể sử dụng hợp lệ cho đến khi hết hạn hoặc cho đến khi quản trị viên chủ động thu hồi phiên (thông qua IAM revocation policy, cập nhật inline policy, hoặc vô hiệu hóa IAM role).

~~~
[Chương trình Go gọi config.LoadDefaultConfig]
                   │
                   ▼
    [Default Credential Provider Chain]
    ├── 1. Biến môi trường (AWS_ACCESS_KEY_ID, Web Identity)
    ├── 2. Tệp cấu hình (~/.aws/config, credentials, SSO)
    ├── 3. Container credentials (ECS Task Role / Pod ID)
    └── 4. EC2 Instance Metadata Service (IMDSv2 / IMDSv1)
                   │
                   ▼
     [aws.Credentials struct]
     - AccessKeyID:     ASIA... (Khóa tạm thời)
     - SecretAccessKey: ...
     - SessionToken:    ...     (Bắt buộc có)
     - CanExpire:       true    (Đánh dấu có hạn dùng)
     - Expires:         2026-09-24T13:00:00Z
~~~

### Cơ chế bộ đệm và xác thực đồng bộ của SDK (`aws.CredentialsCache`)

Khi ứng dụng gọi `config.LoadDefaultConfig(ctx)`, SDK không chỉ nạp một chuỗi khóa tĩnh duy nhất vào bộ nhớ. Nó thiết lập chuỗi tìm kiếm định danh theo thứ tự ưu tiên chuẩn mực: bắt đầu từ các biến môi trường trực tiếp (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, hoặc đường dẫn token liên kết web identity), chuyển tiếp qua tệp cấu hình chia sẻ cục bộ (`~/.aws/config`), định danh gán cho container (ECS Task Role), và sau cùng là dịch vụ siêu dữ liệu máy chủ ảo EC2 (IMDSv2).

Trên các cụm Kubernetes hoặc ECS, SDK phát hiện tệp token do hệ thống cung cấp và gửi yêu cầu `AssumeRoleWithWebIdentity` tới AWS STS để nhận quyền IAM Role. Nhằm giảm thiểu số lượt gọi mạng lặp lại trước mỗi HTTP request, SDK v2 bọc provider bên trong cấu trúc `aws.CredentialsCache`. Cần lưu ý rằng `CredentialsCache` không vận hành một goroutine chạy ngầm trong nền để quét chu kỳ làm mới. Thay vào đó, mỗi khi mã nguồn gọi `Retrieve(ctx)`, bộ đệm kiểm tra trực tiếp thời điểm hết hạn của khóa hiện tại. Nếu khóa còn hiệu lực và nằm ngoài ngưỡng cửa sổ làm mới (`ExpiryWindow`), cache trả về giá trị đã lưu ngay lập tức. Nếu khóa đã hết hạn hoặc bước vào cửa sổ an toàn, chính lượt gọi `Retrieve(ctx)` đó sẽ kích hoạt provider nền tảng lấy bộ khóa mới một cách đồng bộ, bảo đảm mọi phiên làm việc duy trì tính liên tục mà không gây nghẽn tài nguyên.

---

## 2. Luồng thực thi của AWS SDK v2 và Smithy Middleware

Khác với SDK v1 trước đây, AWS SDK for Go v2 được tái cấu trúc hoàn toàn dựa trên kiến trúc **Smithy** — một giao thức mô hình hóa dịch vụ mở của Amazon.

Mọi yêu cầu gửi tới AWS (như `s3.PutObject`) không đi thẳng ra mạng, mà phải di chuyển qua một ngăn xếp gồm 5 pha xử lý tuần tự (**Middleware Stack**):

~~~
Ý định gọi hàm (PutObjectInput)
             │
             ▼
   [Smithy Middleware Stack]
   ├── 1. Initialize  ──> Khởi tạo tham số và kiểm tra đầu vào
   ├── 2. Serialize   ──> Chuyển Go Struct sang HTTP Request
   ├── 3. Build       ──> Gắn header, định tuyến endpoint
   ├── 4. Finalize    ──> Ký chữ ký số SigV4 & Checksum
   └── 5. Deserialize ──> Đọc HTTP Response thành Go Struct
             │
             ▼
  [HTTP RoundTripper / Mạng] ──> [AWS Cloud Service Endpoint]
~~~

### Chữ ký số SigV4 (Signature Version 4)

Tại pha **Finalize**, middleware bảo mật của SDK thực hiện thuật toán ký số SigV4 để bảo đảm tính toàn vẹn và nguồn gốc của gói tin. Quá trình này bắt đầu bằng việc chuẩn hóa phương thức HTTP, đường dẫn tài nguyên, tham số truy vấn và các header thành một chuỗi đại diện duy nhất (Canonical Request). Chuỗi này được băm bằng thuật toán SHA-256 để tạo mã tóm lược nội dung.

Tiếp đó, SDK sử dụng Secret Access Key kết hợp cùng thông tin ngày tháng, phân vùng địa lý (Region) và tên dịch vụ đích để tính toán khóa ký tạm thời (Signing Key) thông qua hàm băm HMAC. Khóa ký này được dùng để tạo mã băm xác thực cuối cùng, đưa trực tiếp vào HTTP Header dưới định dạng `Authorization: AWS4-HMAC-SHA256 Credential=ASIA...`. Bất kỳ thay đổi trái phép nào đối với gói tin trên đường truyền, dù chỉ một byte trong payload hoặc tiêu đề, đều khiến chữ ký tại máy chủ dịch vụ AWS không khớp và bị từ chối ngay lập tức với mã lỗi `403 SignatureDoesNotMatch`.

Bất kỳ kẻ xấu nào chặn bắt gói tin trên đường truyền và sửa đổi dù chỉ 1 byte trong payload hoặc header, chữ ký số sẽ không khớp và máy chủ dịch vụ AWS (AWS service endpoint như S3, DynamoDB, STS) lập tức từ chối với mã lỗi `403 SignatureDoesNotMatch`.

---

## 3. Quản lý dữ liệu lớn bằng Paginator

Một lỗi sơ đẳng nhưng cực kỳ tai hại khi viết công cụ lưu trữ là sử dụng lệnh liệt kê cơ bản để tải danh sách file trong bucket:

~~~go
// CẢNH BÁO: Chỉ lấy tối đa 1.000 file đầu tiên!
resp, err := client.ListObjectsV2(ctx, &s3.ListObjectsV2Input{
	Bucket: aws.String("big-data-bucket"),
})
~~~

Một bucket trên S3 có thể chứa 10 triệu đối tượng. API `ListObjectsV2` mặc định chỉ trả về tối đa 1.000 file mỗi lần gọi và trả về mã thông báo tiếp tục (`NextContinuationToken`).

Nếu bạn tự viết vòng lặp `for` với token thủ công, mã nguồn sẽ trở nên cồng kềnh và dễ gặp lỗi vòng lặp vô tận nếu xử lý sai điều kiện ngắt. 

### Mẫu hình chuẩn: SDK Paginator

AWS SDK v2 cung cấp cấu trúc `NewListObjectsV2Paginator` giúp duyệt dữ liệu theo phong cách stream O(1) về bộ nhớ:

~~~go
paginator := s3.NewListObjectsV2Paginator(
	client, &s3.ListObjectsV2Input{
		Bucket: aws.String("big-data-bucket"),
	},
)

for paginator.HasMorePages() {
	page, err := paginator.NextPage(ctx)
	if err != nil {
		return fmt.Errorf("lỗi đọc trang: %w", err)
	}
	for _, obj := range page.Contents {
		// Xử lý từng file mà không làm đầy RAM
		processFile(*obj.Key)
	}
}
~~~

Paginator chỉ giữ đúng 1 trang dữ liệu trong RAM tại một thời điểm, cho phép chương trình quét hàng triệu file mà mức tiêu thụ bộ nhớ vẫn phẳng tuyệt đối.

---

## 4. Phân loại lỗi và Thử lại: smithy.APIError

Khi một lệnh gọi AWS thất bại, bạn không thể chỉ so sánh chuỗi lỗi bằng `strings.Contains(err.Error(), "404")`. AWS trả về lỗi có cấu trúc chuẩn mực thông qua interface `smithy.APIError`.

Phân loại lỗi chính xác là điều kiện tiên quyết để chương trình đưa ra phản ứng phù hợp. Các lỗi nghiệp vụ như `NoSuchKey` (đối tượng không tồn tại) hoặc `AccessDenied` (thiếu quyền hạn IAM) phản ánh vi phạm logic hoặc rào chắn phân quyền; việc gửi lại yêu cầu trong tình huống này chỉ gây lãng phí băng thông và làm tắc nghẽn hàng đợi. Ngược lại, các mã lỗi chỉ thị quá tải tạm thời như `SlowDown`, `ThrottlingException`, `RequestTimeout` hay `ServiceUnavailable` đòi hỏi cơ chế thử lại có kiểm soát, áp dụng thuật toán lùi lũy thừa (exponential backoff) kết hợp dao động ngẫu nhiên (jitter) để bảo vệ dịch vụ hạ tầng.

~~~go
func ClassifyError(err error) (bool, string) {
	if err == nil {
		return false, ""
	}

	var apiErr smithy.APIError
	if errors.As(err, &apiErr) {
		code := apiErr.ErrorCode()
		switch code {
		case "SlowDown", "ThrottlingException",
			"TooManyRequestsException", "RequestTimeout":
			return true, code
		default:
			return false, code
		}
	}
	return false, "UnknownError"
}
~~~

---

## 5. Hiện thực Storage Client và Middleware tùy biến

Dưới đây là cấu trúc mã nguồn trích xuất từ dự án mẫu `labs/part24-aws-sdk-go-v2/`. Trong khi mã nguồn triển khai thực tế trên production sẽ sử dụng `config.LoadDefaultConfig(ctx)` để gọi trực tiếp tới các endpoint dịch vụ AWS thật, dự án lab minh họa kiến trúc bằng `httptest.Server` giả lập giao thức S3 nhằm kiểm chứng hành vi nội tại của SDK v2 (middleware, provider, paginator, phân loại lỗi) hoàn toàn cô lập, không yêu cầu tài khoản đám mây thật hay chi phí vận hành:

### 1. Provider cấp khóa tạm thời tự xoay vòng

Mô phỏng chính xác cách thức AWS STS cấp phát temporary credentials với thời hạn hiệu lực:

~~~go
type DynamicCredentialProvider struct {
	retrieveCount atomic.Int64
	ttl           time.Duration
	roleArn       string
}

func (p *DynamicCredentialProvider) Retrieve(
	ctx context.Context,
) (aws.Credentials, error) {
	count := p.retrieveCount.Add(1)
	now := time.Now()

	return aws.Credentials{
		AccessKeyID:     fmt.Sprintf("ASIA-TEMP-KEY-%d", count),
		SecretAccessKey: fmt.Sprintf("SECRET-TOKEN-%d", count),
		SessionToken:    fmt.Sprintf("SESSION-TOKEN-%d", count),
		Source:          "DynamicCredentialProvider",
		CanExpire:       true,
		Expires:         now.Add(p.ttl),
	}, nil
}
~~~

### 2. Can thiệp vào Smithy Middleware để thêm Header Audit

Bạn muốn mọi lệnh gọi từ công cụ tự động hóa nội bộ phải gửi kèm mã định danh phiên làm việc để truy vết trên CloudTrail? Hãy viết một middleware ở pha `Build`:

~~~go
type AuditHeaderMiddleware struct {
	Origin string
}

func (m *AuditHeaderMiddleware) ID() string {
	return "AuditHeaderMiddleware"
}

func (m *AuditHeaderMiddleware) HandleBuild(
	ctx context.Context,
	in middleware.BuildInput,
	next middleware.BuildHandler,
) (middleware.BuildOutput, middleware.Metadata, error) {
	req, ok := in.Request.(*smithyhttp.Request)
	if ok && req != nil {
		req.Header.Set("X-Audit-Origin", m.Origin)
	}
	return next.HandleBuild(ctx, in)
}
~~~

Khi khởi tạo client, ta đăng ký middleware này vào pipeline:

~~~go
s3Client := s3.NewFromConfig(cfg, func(o *s3.Options) {
	o.APIOptions = append(
		o.APIOptions,
		func(stack *middleware.Stack) error {
			return stack.Build.Add(
				&AuditHeaderMiddleware{
					Origin: "automated-backup-worker",
				},
				middleware.After,
			)
		},
	)
})
~~~

---

## 6. Bằng chứng kiểm thử: Kiểm chứng 5 hành vi then chốt
 
Toàn bộ bộ kiểm thử tại `labs/part24-aws-sdk-go-v2/storage_test.go` vận hành độc lập bằng `httptest.Server` (phân loại mức kiểm chứng: `MOCK_VERIFIED` đối với tầng HTTP transport và `UNIT_TESTED` đối với logic provider/paginator/middleware), mô phỏng cấu trúc phản hồi XML của S3 và kiểm chứng 5 hành vi kiến trúc then chốt mà không cần tài nguyên AWS thực tế:

~~~
=== RUN   TestTemporaryCredentialRefresh
--- PASS: TestTemporaryCredentialRefresh (0.06s)
=== RUN   TestCustomSmithyMiddlewareAuditHeader
--- PASS: TestCustomSmithyMiddlewareAuditHeader (0.01s)
=== RUN   TestS3OperationsPutAndGet
--- PASS: TestS3OperationsPutAndGet (0.00s)
=== RUN   TestPaginatorListAllKeys
--- PASS: TestPaginatorListAllKeys (0.00s)
=== RUN   TestErrorClassification
--- PASS: TestErrorClassification (0.00s)
PASS
ok      part24-aws-sdk-go-v2   3.665s
~~~

### 1. Tự động làm mới khóa hết hạn (TestTemporaryCredentialRefresh)
Khởi tạo provider với thời hạn sống 50ms. Lần đọc đầu tiên lấy khóa `ASIA-TEMP-KEY-1`. Sau khi chờ 60ms để khóa hết hạn, lần gọi tiếp theo tự động kích hoạt `Retrieve()` lần hai và nhận khóa mới `ASIA-TEMP-KEY-2`, chứng minh cơ chế tự động xoay vòng hoạt động trơn tru.

### 2. Tiêm Header qua Smithy Middleware (TestCustomSmithyMiddlewareAuditHeader)
Máy chủ HTTP cục bộ bắt gói tin `PutObject` và kiểm tra header `X-Audit-Origin`. Giá trị nhận được chính xác là `"automated-backup-worker"`, chứng minh middleware đã can thiệp thành công vào luồng gửi tin của SDK.

### 3. Đọc ghi luồng dữ liệu an toàn (TestS3OperationsPutAndGet)
Kiểm chứng tính toàn vẹn của chuỗi dữ liệu nhị phân khi upload và download qua S3 Client.

### 4. Thu thập toàn bộ danh sách file qua Paginator (TestPaginatorListAllKeys)
Máy chủ giả lập trả về trang 1 kèm `IsTruncated: true` và `NextContinuationToken`, sau đó trả về trang 2 với `IsTruncated: false`. Hàm `ListAllKeys` tự động gọi 2 lần HTTP và thu thập đầy đủ 3 file mà không cần người dùng tự quản lý token phân trang.

### 5. Phân loại lỗi chính xác (TestErrorClassification)
Kiểm chứng hàm phân loại bóc tách chính xác mã lỗi `SlowDown` (đánh dấu `isRetryable = true`) và mã lỗi `AccessDenied` (đánh dấu `isRetryable = false`).

---

## 7. Các cạm bẫy người học thường gặp (Learner Pitfalls)

| Cạm bẫy thực tế | Hậu quả trên Production | Giải pháp phòng ngừa |
| :--- | :--- | :--- |
| **Hardcode Access Key** trong mã nguồn hoặc docker image. | Khóa bị quét và rò rỉ khi đẩy lên kho mã nguồn, gây mất quyền kiểm soát đám mây. | Luôn dùng IAM Role / IRSA và nạp quyền qua `config.LoadDefaultConfig`. |
| **Không đóng Response Body** khi gọi `s3.GetObject`. | Rò rỉ socket HTTP (`file descriptor leak`), làm cạn kiệt tài nguyên mạng của container. | Luôn đặt `defer resp.Body.Close()` ngay sau khi kiểm tra lỗi `GetObject`. |
| **Tự viết vòng lặp phân trang** bằng token thủ công. | Dễ phát sinh lỗi vô tận hoặc tràn bộ đệm RAM khi số lượng object vượt quá dự tính. | Luôn dùng `s3.NewListObjectsV2Paginator` của SDK v2. |
| **Thử lại mù quáng** với lỗi phân quyền `AccessDenied`. | Làm tắc nghẽn hàng đợi và kích hoạt các cảnh báo bảo mật bất thường trong SIEM. | Dùng `errors.As(err, &apiErr)` để chỉ thử lại các lỗi tạm thời (`SlowDown`, `5xx`). |

---

## 8. Bài tập thực hành thiết kế Cloud Tool

### Thử thách 1: Tích hợp Context Timeout chặt chẽ cho thao tác đám mây
**Yêu cầu:** Mạng đám mây có thể bị nghẽn bất cứ lúc nào. Hãy viết hàm bọc `PutObjectWithTimeout` nhận thêm tham số `timeout time.Duration`. Sử dụng `context.WithTimeout` để bảo đảm nếu việc upload kéo dài quá thời gian quy định, kết nối sẽ bị hủy ngay lập tức để giải phóng tài nguyên.

### Thử thách 2: Thiết kế Waiter kiểm tra Bucket sẵn sàng
**Yêu cầu:** Sau khi gửi lệnh tạo bucket (`CreateBucket`), hạ tầng S3 mất vài giây để đồng bộ DNS toàn cầu. Hãy viết hàm kiểm tra bucket đã tồn tại hay chưa bằng `s3.NewBucketExistsWaiter`. Cấu hình thời gian chờ tối đa 30 giây với khoảng cách thăm dò là 2 giây.

---

## 9. Hướng dẫn giải và Phân tích kiến trúc bài tập

### Lời giải Thử thách 1: Quản trị thời gian chết bằng Context

~~~go
func (s *CloudStorage) PutObjectWithTimeout(
	parentCtx context.Context,
	bucket, key string,
	body io.Reader,
	timeout time.Duration,
) error {
	ctx, cancel := context.WithTimeout(parentCtx, timeout)
	defer cancel()

	err := s.PutObject(ctx, bucket, key, body)
	if err != nil {
		if errors.Is(ctx.Err(), context.DeadlineExceeded) {
			return fmt.Errorf(
				"upload %s/%s quá hạn sau %v: %w",
				bucket, key, timeout, err,
			)
		}
		return err
	}
	return nil
}
~~~

### Lời giải Thử thách 2: Đồng bộ hóa bằng SDK Waiter

~~~go
func WaitForBucketReady(
	ctx context.Context,
	client *s3.Client,
	bucket string,
) error {
	waiter := s3.NewBucketExistsWaiter(
		client,
		func(o *s3.BucketExistsWaiterOptions) {
			o.MaxDelay = 5 * time.Second
			o.MinDelay = 2 * time.Second
		},
	)

	// Chờ tối đa 30 giây
	maxWait := 30 * time.Second
	return waiter.Wait(
		ctx,
		&s3.HeadBucketInput{Bucket: aws.String(bucket)},
		maxWait,
	)
}
~~~

`BucketExistsWaiter` tự động gửi các yêu cầu `HeadBucket` định kỳ với thuật toán lùi thời gian (backoff jitter). Ngay khi S3 trả về mã 200 OK, hàm `Wait` lập tức trở về thành công mà không làm lãng phí dù chỉ 1 mili-giây.

---

Làm chủ kiến trúc **Temporary Credentials + Smithy Middleware + Paginators** giúp bạn xây dựng những hệ thống tự động hóa đám mây có độ tin cậy và bảo mật cấp doanh nghiệp. Trong Chương 25, chúng ta sẽ kết nối chuỗi tự động hóa này với hạ tầng quản lý mã nguồn: xây dựng hệ thống **Tự động hóa Git và GitHub hướng sự kiện** bằng Go với khả năng xác thực Webhook HMAC, phân loại ID phát hàng lũy đẳng và kiểm soát giới hạn tần suất gọi API (Rate Limiting).
