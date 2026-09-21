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

Contract: destination phải là non-nil pointer tới struct; chỉ field exported có
tag `env` được ghi; field tagged nhưng không phải `string` là schema lỗi; tag
thiếu trong map giữ nguyên field. Không dùng `unsafe` để đi qua field private.
