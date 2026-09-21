# Lab: đo trước khi tối ưu

Mở `exercise/render_test.go` trước. Test là contract: `Render` phải giữ đúng
format. Hãy tự chọn implementation trong `exercise/render.go`, rồi chạy:

```powershell
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
```

Sau khi đúng, tự thêm benchmark có input đủ lớn và chạy với `-benchmem`. Đừng
đọc `fixed/` trước khi có một nhận định bằng dữ liệu. Bản tham chiếu giữ nguyên
output, nhưng không phải lời mời gọi thay mọi phép nối chuỗi bằng `Builder`.
