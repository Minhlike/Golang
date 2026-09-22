# Lab: supervisor nhỏ cho process con

Mở `exercise/run_test.go` trước. Test binary tự đóng vai helper process, nên
đừng thay nó bằng `ping`, `curl`, `sleep`, hoặc một executable có sẵn riêng trên
máy anh.

```powershell
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
go test ./fixed
go vet ./fixed
go test -race ./fixed
```

Contract: `Spec` rỗng hoặc timeout không dương bị từ chối; `Run` giữ `stdout`
và `stderr` riêng; exit khác 0 vẫn giữ `Result`, exit code và `*exec.ExitError`;
deadline trả error khớp `context.DeadlineExceeded` và gắn `TimedOut`. Không dùng
shell, không ghép command line thành string, không hứa cleanup cả process tree.
