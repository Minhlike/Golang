# Lab: orchestration có thể kiểm chứng

Đọc `internal/app/run_test.go` trước. Mỗi test giữ một policy khác nhau:
mapping config, config error trước runner, probe failure theo từng service và
cancellation của cả run.

Sau đó đọc `internal/config/config_test.go`. Hai bảng ở đây không dùng để kiểm
tra từng chi tiết implementation: chúng giữ contract của default, override và
các input phải bị từ chối. Tự thêm case IPv6 `[2001:db8::10]:443` trước khi xem
lời giải trong sách.

Sau khi đã dự đoán, đổi tên `Run` trong `internal/app/run.go` rồi chạy
`go test ./...` để compiler chỉ những contract còn thiếu. Viết lại `Run` từ
test, không gọi `os.LookupEnv`, `fmt.Printf` hoặc `os.Exit` trong package app.
Khi test xanh, chạy `go run ./cmd/opsprobe`.

Để thấy CLI không nuốt config error, chạy trong PowerShell:

```powershell
$env:OPS_PROBE_TARGET = "payments.internal:0"
go run ./cmd/opsprobe
Remove-Item Env:OPS_PROBE_TARGET
```

Lệnh phải in lỗi validation rồi trả exit code khác 0. Không sửa test để chấp
nhận runner chạy sau config error; đó là policy mà lab đang bảo vệ.
