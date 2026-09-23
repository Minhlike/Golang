# AWS OIDC + Terraform Bridge (Dry-run & Reviewable Specimen)

Mục này cung cấp cấu hình Terraform minh họa cách thiết lập quan hệ tin cậy
(federated trust relationship) giữa GitHub Actions và AWS IAM mà **không cần lưu
trữ access key dài hạn**.

## Ranh giới bảo đảm an toàn và phạm vi kỹ thuật

- **Mã nguồn kiểm tra và học tập (Reviewable Code):** Đây là tài liệu thiết kế và
  code mẫu nhằm đánh giá kiến trúc phân quyền.
- **Không tự ý tạo tài nguyên thật:** Tuyệt đối không chạy `terraform apply` trên
  bất kỳ tài khoản cloud nào khi chưa có sự phê duyệt rõ ràng từ người dùng.
- **Ranh giới công cụ thực tế:** Môi trường hiện tại không có `terraform` hay `aws`.
  Vì vậy, cấu hình này không chứng minh rằng IAM role đã được assume thành công,
  không chứng minh ECR hay App Runner resource thực tế tồn tại, và không chứng minh
  rằng lệnh deploy đã hoàn tất. Lệnh `terraform validate` chỉ có thể coi là đã pass
  nếu máy có cài Terraform CLI và lệnh đã chạy thật.

## Các chốt chặn an toàn trong thiết kế

1. **Khóa chặt claim `sub` trong Trust Policy:**
   Cấu hình này khóa chặt điều kiện:
   ```json
   "token.actions.githubusercontent.com:sub": "repo:Minhlike/Golang:environment:production"
   ```
   Ngay cả khi kẻ tấn công fork repository hoặc chạy workflow từ branch cá nhân,
   họ không thể assume role deploy này vì claim `sub` của repo fork sẽ không khớp.

2. **Làm rõ việc sử dụng Wildcard `*` trong IAM:**
   Ký tự `*` trong `Resource = ["*"]` **chỉ được sử dụng duy nhất** cho hành động
   `ecr:GetAuthorizationToken`. Đây là yêu cầu bắt buộc của chính AWS IAM vì action
   này không hỗ trợ phân quyền ở cấp độ tài nguyên (resource-level scoping).
   Ngược lại, mọi permission khác (`ecr:PutImage`, `apprunner:StartDeployment`, ...)
   đều được khóa chặt vào Account ID và tên tài nguyên cụ thể.

3. **Khóa Account ID động:**
   Không dùng wildcard `*` hay hard-code Account ID trong ARN tài nguyên; cấu hình
   dùng `data.aws_caller_identity.current.account_id` để lấy đúng Account ID của môi
   trường thực thi.

4. **Tên ECR Repository tuân thủ chuẩn:**
   Tách riêng biến `ecr_repository_name` với quy tắc validation bắt buộc viết thường
   (`^[a-z0-9][a-z0-9-_/]*$`), tránh lỗi không tương thích giữa tên GitHub repo viết
   hoa và quy tắc đặt tên của AWS ECR.
