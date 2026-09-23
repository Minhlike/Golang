# Part 18 — Chuỗi delivery, gate kiểm soát và OIDC bridge

Đây là stage hai của Chương 18. Lab đặt mental model "delivery là chuỗi bằng chứng"
vào các công cụ thực tế: một pipeline GitHub Actions có phân quyền tối thiểu, một
promotion gate tự động hóa bằng Go, và một cấu hình Terraform thiết lập quan hệ
tin cậy OIDC với Cloud.

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

### 1. Ứng viên đạt chuẩn (Approved)

```powershell
go run ./cmd/promote-gate `
  --digest "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef" `
  --revision "e69965a" `
  --tests-passed=true `
  --provenance-verified=true
```

Kết quả mong đợi (Exit code 0):
`promotion approved: digest=sha256:... revision=e69965a`

### 2. Ứng viên trượt test (Rejected)

```powershell
go run ./cmd/promote-gate `
  --digest "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef" `
  --revision "e69965a" `
  --tests-passed=false `
  --provenance-verified=true
```

Kết quả mong đợi (Exit code 1):
`promotion rejected: tests not passed`

### 3. Định danh sai quy chuẩn (Malformed Input)

```powershell
go run ./cmd/promote-gate `
  --digest ":latest" `
  --revision "e69965a"
```

Kết quả mong đợi (Exit code 2):
`invalid candidate: digest must be a lowercase sha256 digest`

Điều này chứng minh gate từ chối thẳng thừng các tag trôi nổi như `:latest`,
buộc pipeline phải truyền định danh nội dung bất biến (`sha256:...`).

## Bài 2: Phân tích Workflow GitHub Actions

Đọc tệp `workflows/delivery.yaml`. Các ranh giới an toàn cần chú ý:

1. **Phân quyền tối thiểu ở root:**
   `permissions: { contents: read }` ngăn runner tự động có quyền sửa đổi repository.
2. **Khóa chặt action bằng immutable commit SHA:**
   Thay vì `@v4`, các action được ghim chính xác bằng mã băm SHA đầy đủ kèm
   chú thích phiên bản (ví dụ `actions/checkout@11bd71... # v4.2.2`). Điều này
   chống lại nguy cơ supply chain khi một tag release bị ghi đè mã độc.
3. **Chuyển giao bằng Digest:**
   Job build tính toán mã băm sha256 và truyền sang job promote thông qua
   `outputs`. Job deploy tuyệt đối không kéo `:latest` hoặc tự biên dịch lại.
4. **Quyền OIDC chỉ cấp cho Job Deploy:**
   Chỉ `promote-production` mới được khai báo `id-token: write` để xin token
   xác thực với cloud.

## Bài 3: Đánh giá quan hệ tin cậy AWS OIDC trong Terraform

Đọc thư mục `terraform/`. Đây là cấu hình mẫu nhằm review kiến trúc:

- Không sử dụng static secret `AWS_ACCESS_KEY_ID` hay `AWS_SECRET_ACCESS_KEY`.
- Token OIDC ngắn hạn được cấp phát dựa trên claim `sub` khóa chặt repo và
  environment `repo:Minhlike/Golang:environment:production`.
- Quyền IAM được thiết kế theo nguyên tắc đặc quyền tối thiểu, không dùng wildcard `*`.
