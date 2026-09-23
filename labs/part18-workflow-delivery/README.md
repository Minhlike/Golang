# Part 18 — Chuỗi delivery, gate kiểm soát và OIDC bridge

Đây là stage hai của Chương 18. Lab đặt mental model "delivery là chuỗi bằng chứng"
vào các công cụ thực tế: một workflow mẫu GitHub Actions có phân quyền tối thiểu,
một promotion gate tự động hóa bằng Go, và một cấu hình Terraform thiết lập quan
hệ tin cậy OIDC với Cloud.

## Bài 1: Chạy và kiểm tra Promotion Gate bằng Go

Trước khi kết nối bất kỳ hệ thống CI nào, ta kiểm chứng logic xét duyệt nhập môn
(admission decision) được viết bằng Go.

```powershell
cd labs/part18-workflow-delivery
go test -v ./...
go vet ./...
go test -race ./...
```

Thử nghiệm chạy trực tiếp CLI `promote-gate` với các tình huống thực tế:

### 1. Ứng viên đạt chuẩn đầy đủ bằng chứng (Approved)

```powershell
$DIGEST = "sha256:0123456789abcdef0123456789abcdef" + `
          "0123456789abcdef0123456789abcdef"

go run ./cmd/promote-gate `
  --digest $DIGEST `
  --revision "bcb3fe0" `
  --tests-passed=true `
  --provenance-verified=true
```

Kết quả mong đợi (Exit code 0):
`promotion approved: digest=sha256:... revision=bcb3fe0`

### 2. Ứng viên trượt test (Rejected on Tests)

```powershell
go run ./cmd/promote-gate `
  --digest $DIGEST `
  --revision "bcb3fe0" `
  --tests-passed=false `
  --provenance-verified=true
```

Kết quả mong đợi (Exit code 1):
`promotion rejected: tests not passed`

### 3. Ứng viên thiếu bằng chứng Provenance (Fail-Closed)

Trong pipeline thật, `tests-passed=true` có thể suy ra từ việc job verify hoàn
thành trong dependency graph. Nhưng `provenance-verified` chỉ có thể là `true`
sau khi có một bước xác thực chữ ký/attestation chuyên trách (như Cosign hoặc
GitHub Attestations). Khi chưa có bước xác thực đó, không được fake boolean thành
`true` (evidence theater). Gate phải từ chối theo nguyên tắc fail-closed:

```powershell
go run ./cmd/promote-gate `
  --digest $DIGEST `
  --revision "bcb3fe0" `
  --tests-passed=true `
  --provenance-verified=false
```

Kết quả mong đợi (Exit code 1):
`promotion rejected: provenance not verified`

### 4. Định danh trôi nổi sai quy chuẩn (Malformed Input)

```powershell
go run ./cmd/promote-gate `
  --digest ":latest" `
  --revision "bcb3fe0"
```

Kết quả mong đợi (Exit code 2):
`invalid candidate: digest must be a lowercase sha256 digest`

Gate từ chối thẳng thừng các tag trôi nổi như `:latest`, buộc pipeline phải dùng
định danh OCI manifest digest bất biến (`sha256:...`).

## Bài 2: Phân tích Workflow Specimen (`workflows/delivery.yaml`)

Tệp `workflows/delivery.yaml` là tài liệu mẫu trong lab học tập (runnable/reviewable
specimen), không phải workflow đang kích hoạt trong `.github/workflows/`. Các ranh
giới kỹ thuật cần lưu ý:

1. **Repo multi-module:**
   Repository gồm nhiều module độc lập và không có `go.work` ở root. Vì vậy job
   `verify` chạy kiểm tra với `working-directory` riêng cho từng module thuộc
   delivery path (`labs/part16-real-signals` và `labs/part18-workflow-delivery`),
   thay vì chạy `go test ./...` tại thư mục gốc.
2. **Phân biệt Local Image ID và OCI Manifest Digest:**
   Khi build local mà chưa push registry, Docker daemon chỉ cấp phát một Image
   Config ID (`.Id`). Chỉ khi build bằng Buildx xuất ra metadata hoặc push lên
   registry, ta mới có OCI Image Manifest Digest đại diện cho toàn bộ manifest và
   các layer descriptors. Pipeline promotion bắt buộc phải dùng Manifest Digest.
3. **Phân quyền tối thiểu và Pinning:**
   `permissions: { contents: read }` ở root; action ghim SHA commit 40 ký tự bất biến;
   quyền `id-token: write` chỉ cấp riêng cho job deploy.

## Bài 3: Đánh giá quan hệ tin cậy AWS OIDC trong Terraform

Đọc thư mục `terraform/` (mã nguồn kiểm tra reviewable, không chạy apply thật):

- Không sử dụng static secret `AWS_ACCESS_KEY_ID` hay `AWS_SECRET_ACCESS_KEY`.
- Token OIDC ngắn hạn được cấp phát dựa trên claim `sub` khóa chặt repo và
  environment: `repo:Minhlike/Golang:environment:production`.
- **Làm rõ về Wildcard trong IAM:** Wildcard `*` trong `Resource = ["*"]` chỉ được
  dùng cho `ecr:GetAuthorizationToken` vì AWS IAM bắt buộc (không hỗ trợ resource
  scoping). Các action khác đều được khóa chặt vào `data.aws_caller_identity.current.account_id`
  và repository/service cụ thể.
- Biến `ecr_repository_name` được validate viết thường, tách biệt khỏi tên GitHub repo.
- Máy hiện tại không có `terraform` hay `aws`; không tự cài và không tạo cloud resource.
