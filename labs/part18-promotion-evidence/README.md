# Part 18 — Promotion evidence

Đọc `exercise/admission_test.go` trước. Hoàn thành `Evaluate` theo contract rồi chạy:

```powershell
go test -tags exercise ./exercise
go test ./fixed
go vet ./fixed
go test -race ./fixed
```

Lab chỉ mô hình hóa admission decision. Nó không xác thực registry, chữ ký hay
provenance thật; các boundary đó phải dùng verifier và policy của hệ thống thật.
