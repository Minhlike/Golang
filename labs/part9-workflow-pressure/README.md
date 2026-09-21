# Lab: dòng công việc có áp suất

Mở `exercise/pool_test.go` trước. Nó là contract cho một worker pool nhỏ, không
phải đề bài chép code. Tự tạo `Job`, `Result`, `Work` và `Run` trong
`exercise/pool.go`.

Khởi đầu bằng một test đỏ có chủ đích:

```powershell
go test -tags exercise ./exercise
```

Đừng sửa test, đừng thêm buffer lớn để né áp suất, và đừng để worker tự đóng
output. Một goroutine coordinator phải chờ toàn bộ worker rồi đóng output đúng
một lần. `Run` có thể trả output đã đóng nếu `workers <= 0`; đó là policy của
lab để API vẫn nhỏ.

Khi test xanh, chạy lại với race detector:

```powershell
go test -race -tags exercise ./exercise
```

Chỉ sau đó mới mở `fixed/`. Bản tham chiếu dùng unbuffered channel để contract
về áp suất lộ rõ; nó không phải lời khuyên rằng mọi worker pool production đều
phải unbuffered.
