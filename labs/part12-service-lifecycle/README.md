# Lab: HTTP boundary và graceful shutdown

Mở `exercise/server_test.go`. Hãy tự định nghĩa `Check`, `Store` và `NewHandler`
để thỏa HTTP contract trước; handler không được gọi mạng ra ngoài. Lúc test xanh,
chạy lại với race detector rồi mới so sánh `fixed/`.

```powershell
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
go test ./fixed
```

`fixed/` có thêm `ServeUntilStopped`, một hàm nhỏ để test lifecycle với listener
cục bộ. Nó không thay thế configuration, authentication hay policy deploy của
một service thật.
