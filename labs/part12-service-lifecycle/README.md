# Lab: HTTP boundary và graceful shutdown

Mở `exercise/server_test.go`. Hãy tự định nghĩa `Check`, `Store` và `NewHandler`
để thỏa HTTP contract trước; handler không được gọi mạng ra ngoài. Lúc test xanh,
chạy lại với race detector rồi mới so sánh `fixed/`.

```powershell
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
```

`fixed/` có thêm `ServeUntilStopped`, một hàm nhỏ để test lifecycle với listener
cục bộ. Sau khi handler xanh, tạo lifecycle helper theo test độc lập:

```powershell
go test -tags lifecycleexercise ./exercise
go test -race -tags lifecycleexercise ./exercise
go test ./fixed
```

Helper phải từ chối `srv`, listener hoặc shutdown grace không hợp lệ trước khi
khởi động goroutine. Nó không thay thế configuration, authentication hay policy
deploy của một service thật.
