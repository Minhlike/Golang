# Lab: error boundary dưới áp lực

Đọc `main_test.go` trước `main.go`. Bắt đầu với đúng một failure injection:
trong return cuối của nhánh probe lỗi, đổi `%w` thành `%v`, rồi chạy:

```powershell
go test -run TestApplyProbePreservesFailureCauseAndContext
```

Message vẫn trông gần như cũ, nhưng test phải đỏ vì caller không còn lần được
nguyên nhân bằng `errors.Is`. Khôi phục `%w`, không thay assertion.

Tiếp theo, tạm bỏ nhánh nhận diện cancellation trong `applyProbe` và chạy
`go test -run TestApplyProbeCancellationDoesNotChangeHealthState`. Quan sát
failure của state trước khi khôi phục policy. Hai lần sửa này phân biệt failure
có thể đọc được với policy state đúng. Khi xong, chạy `go test ./...` và
`go vet ./...`.
