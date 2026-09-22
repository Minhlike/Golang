# Part 17 — Reconciliation contract

`exercise/` chỉ có API và contract test. Đọc test, tự hoàn thành `NextAction`, rồi chạy:

```powershell
go test -tags exercise ./exercise
go test ./fixed
go vet ./fixed
go test -race ./fixed
```

Lab không chạy Docker hay Kubernetes. Nó mô hình hóa một vòng quyết định: desired/current
đi vào, một action bounded đi ra. `fixed/` chỉ là lời giải tham chiếu sau khi đã tự làm.
