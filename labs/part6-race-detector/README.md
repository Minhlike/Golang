# Lab: một test xanh vẫn chưa đủ

`broken/` là fixture có chủ ý chứa data race. Nó không được chạy trong suite
mặc định. Để xem report, chạy:

```powershell
go test -race -tags raceexercise ./broken
```

Lệnh này phải thất bại với `WARNING: DATA RACE`. Đọc hai stack trace xung đột
và nơi goroutine được tạo, rồi chuyển sang `fixed/` để xem cùng invariant được
bảo vệ bằng `sync.Mutex`:

```powershell
go test -race ./fixed
```

Đừng dùng fixture `broken/` làm mẫu production. Nó tồn tại để detector có một
đường chạy chắc chắn kích hoạt race.
