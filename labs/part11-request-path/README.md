# Lab: ownership của HTTP response

Mở `exercise/fetch_test.go`. Hãy tự viết `Fetch`, `Reply` và `StatusError` để
thỏa contract của test. `Fetch` nhận một `*http.Client` đã được caller cấu hình;
không được gọi `http.Get` hay dùng `http.DefaultClient`.

```powershell
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
```

Test dùng transport giả để chứng minh context đi tới request và body đã đóng.
Khi test xanh mới so sánh với `fixed/`. Bản tham chiếu đọc toàn bộ body nên phù
hợp cho response nhỏ; nó không thay thế API streaming.
