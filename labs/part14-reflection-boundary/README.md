# Lab — reflection boundary

Mở `exercise/apply_test.go` trước. Viết `ApplyEnv(dst, values)` để một struct
config được khai báo tag `env` có thể nhận string từ map đã có sẵn. Đây không
phải framework config: lab chỉ luyện cách giữ guard runtime trước setter.

```powershell
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
go test ./fixed
go test -race ./fixed
```

Contract: destination phải là non-nil pointer tới struct; `nil` không typed cũng
phải trả `ErrDestination`. Chỉ field exported có tag `env` và exact builtin type
`string` mới eligible. `env:"-"` là opt-out có chủ đích; field unexported nhưng
có tag `env` thật là schema lỗi, không được âm thầm bỏ qua. Named string type
cũng bị từ chối. Nếu schema lỗi, toàn bộ destination phải giữ state trước lời
gọi; tag thiếu trong map chỉ giữ nguyên field tương ứng. Không dùng `unsafe` để
đi qua field private.
