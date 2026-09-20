# Lab: refactor `opsprobe` dưới ràng buộc

Đây là điểm xuất phát trước khi tách package. `main.go` chạy được, nhưng mọi
quyết định đang nằm trong một package `main`.

Chạy `go run .` trước để biết behavior cần giữ. Sau đó chạy:

```powershell
go test -tags exercise ./...
```

Lần đầu lệnh này phải dừng ở compiler vì package `probe` chưa tồn tại. Đó là
feedback cố ý: test mô tả boundary công khai mà refactor phải tạo ra.

Không xem `../part5-package-design` trước khi tự làm. Tạo `probe` với contract
được test gọi, đưa target default vào `internal/config`, và tạo
`cmd/opsprobe` để map config sang probe rồi in output. Giữ các ràng buộc:

- `probe` không import CLI hoặc config;
- config trả data mới cho mỗi caller;
- command là nơi gọi `fmt.Printf` và map hai model;
- output vẫn là `billing healthy=true`.

Acceptance sau refactor:

```powershell
go run ./cmd/opsprobe
go test -tags exercise ./...
go vet ./...
```

Chỉ sau khi một trong các lệnh trên đã cho feedback, mới mở
`../part5-package-design` để so đường dependency và cách tách contract.
