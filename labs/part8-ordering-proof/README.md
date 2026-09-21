# Lab: chứng minh thứ tự của kết quả

Đọc `exercise/registry_test.go` trước. Nó là contract: nhiều worker thêm một
`Report`, người điều phối chờ, rồi snapshot phải có đủ report và không chia sẻ
slice nội bộ.

Để bắt đầu bài tự làm, chạy:

```powershell
go test -tags exercise ./exercise
```

Lệnh cố ý đỏ vì `Registry`, `Report`, `Add` và `Snapshot` chưa được định nghĩa.
Tạo implementation của anh trong `exercise/registry.go`; không sửa test để đổi
contract. Khi test xanh, chạy `go test -race -tags exercise ./exercise`.

Chỉ sau đó mới mở `fixed/` và chạy:

```powershell
go test -race ./fixed
```

`fixed/` là một lời giải tham chiếu nhỏ, không phải một API để mở rộng.
