# AWS OIDC + Terraform Bridge (Dry-run & Reviewable)

Mục này cung cấp cấu hình Terraform minh họa cách thiết lập quan hệ tin cậy
(federated trust relationship) giữa GitHub Actions và AWS IAM mà **không cần lưu
trữ access key dài hạn**.

## Ranh giới bảo đảm an toàn

- **Tài liệu và code kiểm tra (Reviewable):** Đây là mã nguồn nhằm nghiên cứu và
  đánh giá kiến trúc phân quyền.
- **Không tự ý tạo tài nguyên thật:** Không chạy `terraform apply` trên bất kỳ
  tài khoản cloud nào khi chưa có sự phê duyệt rõ ràng từ người dùng.
- **Không chi phí:** Mã nguồn hoàn toàn phi trạng thái (stateless) và không phát
  sinh phí dịch vụ.

## Ba lớp bảo vệ trong thiết kế

1. **OIDC Provider (`aws_iam_openid_connect_provider`):**
   AWS xác thực chữ ký của JSON Web Token (JWT) do chính hạ tầng GitHub cấp phát
   thông qua cặp khóa công khai của `token.actions.githubusercontent.com`.

2. **Khóa chặt claim `sub` trong Trust Policy:**
   Một lỗi phổ biến là cho phép bất kỳ repository nào của GitHub assume role. Cấu
   hình này khóa chặt điều kiện:
   ```json
   "token.actions.githubusercontent.com:sub": "repo:Minhlike/Golang:environment:production"
   ```
   Điều này có nghĩa: ngay cả khi kẻ tấn công fork repository hoặc chạy workflow
   từ branch feature cá nhân, họ vẫn không thể đóng vai role deploy này vì claim
   `sub` sẽ khác giá trị mong đợi.

3. **Đặc quyền tối thiểu (Least Privilege):**
   Role này không có quyền Administrator. Quyền ECR chỉ giới hạn trong repository
   chỉ định; quyền deploy chỉ được phép gọi trên đúng service chỉ định.

## Cách xem xét và kiểm tra cú pháp (nếu có terraform CLI)

```powershell
terraform fmt -check
terraform validate
# Chỉ chạy dry-run plan nếu có backend/credential thử nghiệm hợp lệ:
# terraform plan
```
