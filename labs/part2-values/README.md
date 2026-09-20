# Lab: value và aliasing

Đây là một bug hunt ngắn, không phải source để đọc rồi tin. Chạy `go test` trước
để biết contract của `redactedCopy`: preview phải redacted, còn input vẫn giữ
nguyên.

Sau đó thay riêng phần tạo `preview` bằng `preview := fields`, rồi chạy:

```powershell
go test -run TestRedactedCopyDoesNotMutateInput
```

Test phải fail vì mutation đã đi qua alias. Khôi phục code, sau đó xóa thân của
`redactedCopy` và tự viết lại chỉ từ contract trong test. Cuối cùng chạy
`go run .`, `go test ./...` và `go vet ./...`. Đừng sửa expectation để làm test
xanh: input không đổi là phần contract cần giữ.
