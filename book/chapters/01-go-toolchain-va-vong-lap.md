# Chương 1. Go toolchain và vòng lặp có thể kiểm chứng

Go không chỉ là compiler. Khi anh cài Go, thứ xuất hiện trước mặt là lệnh `go`,
một cửa vào nhiều công cụ cùng chia sẻ hiểu biết về module và package. Nó có
thể chạy chương trình, build binary, format code, chạy test, tải dependency và
phân tích một phần lỗi tĩnh. Việc có một command thống nhất làm giảm số mảnh
ghép phải nhớ, nhưng không thay thế việc hiểu từng mảnh đang làm gì.

Phiên bản dùng trong edition này là Go 1.27.1. “Mới nhất” không có nghĩa là
chạy theo mọi bản thử nghiệm; nó là stable release mà tài liệu chính thức đang
phát hành. Mỗi ví dụ có thể dùng ngôn ngữ hiện hành, nhưng project thật vẫn cần
chọn `go` directive theo compatibility policy của chính nó. Từ Go 1.26, `go
mod init` có chủ ý tạo directive thấp hơn toolchain một major-minor để khuyến
khích tương thích với các bản còn được hỗ trợ. Vì vậy ta sẽ xem `go.mod` là một
quyết định tương thích, không phải nhãn trang trí.

## Workspace không phải GOPATH cũ

Ngày trước, nhiều Go project bị buộc nằm dưới `GOPATH/src`. Với modules, source
có thể nằm ở nơi hợp lý cho project. Một module là đơn vị quản lý dependency;
file `go.mod` đặt ranh giới của nó và ghi module path cùng Go version. Package
là đơn vị code/import nhỏ hơn: một thư mục thường tạo ra một package, và nhiều
package có thể thuộc cùng module.

Sự phân biệt này cứu anh khỏi một lỗi tư duy phổ biến: thấy tên thư mục rồi
đoán đó là import path. Import path được xác định từ module path cộng vị trí
thư mục; nó không tự sinh từ ổ đĩa. Đó là lý do một project clone từ GitHub có
thể build ở máy khác mà không cần cùng tên người dùng Windows.

```text
module example.com/opsprobe       <- go.mod xác định gốc module
├── cmd/opsprobe                  <- package main, tạo executable
├── internal/check                <- package chỉ module này được import
└── go.mod
```

`go env GOROOT GOPATH GOMOD` giúp kiểm tra ba điều khác nhau. `GOROOT` là nơi
toolchain nằm; `GOPATH` vẫn có ích làm cache và nơi cài một số binary; `GOMOD`
cho biết lệnh đang thấy file module nào. Nếu `GOMOD` là `/dev/null` hoặc đường
dẫn không như dự kiến, đừng vội xoá cache: kiểm tra thư mục hiện tại trước.

## Vòng lặp nhỏ nhưng nghiêm túc

Một thay đổi nhỏ nên đi qua vòng lặp sau. Nó là conceptual diagram, không phải
một protocol cứng: với một thử nghiệm một dòng, ta có thể dừng ở bước chạy; với
code gửi vào production, thêm test tích hợp và review.

![Vòng lặp phản hồi](../../assets/diagrams/feedback-loop.png)

1. Viết một giả thuyết và thay đổi nhỏ nhất có thể kiểm chứng nó.
2. Chạy `go fmt ./...` để bỏ tranh luận vô ích về khoảng trắng.
3. Chạy `go test ./...`; không có file test vẫn là thông tin, không phải thành công giả tạo.
4. Chạy `go vet ./...` khi module đủ hoàn chỉnh để phân tích.
5. Đọc output, sửa nguyên nhân rồi mới lặp lại.

Điểm dễ bị AI che khuất là bước 1. Trước khi hỏi một công cụ, hãy nói được
“em tin lỗi nằm ở đâu và dấu hiệu nào sẽ bác bỏ điều đó”. Điều này biến terminal
từ máy phát thông báo thành một dụng cụ đo.

## Lab: kiểm tra môi trường mà không đoán

Tạo một thư mục rỗng và chạy:

```powershell
go version
go env GOROOT GOPATH GOMOD
go help modules
```

Đừng cố diễn giải tất cả output ngay. Hãy trả lời ba câu: toolchain nào đang
chạy, cache/user workspace nào đang được dùng, và thư mục hiện tại đã nằm trong
một module chưa. Khi ba câu này rõ, rất nhiều lỗi “Go không tìm thấy package”
trở nên có hình dạng cụ thể.

### Bài tập

Bạn A đang đứng trong `D:\work\weather` và `go env GOMOD` cho `/dev/null`.
Bạn ấy kết luận Go hỏng vì project chưa có `go.mod`. Kết luận đó thiếu điều gì?

---

### ĐÁP ÁN - chỉ đọc sau khi đã tự làm

`/dev/null` thường chỉ cho thấy command hiện tại không thấy module file ở thư
mục đang đứng hay thư mục cha. Nó chưa chứng minh Go hỏng. A cần kiểm tra
current directory, xác nhận project có thật sự đã `go mod init`, hoặc đi vào
đúng thư mục gốc. Chỉ sau đó mới xét tới `GOWORK`, environment override hay
toolchain.

## Tóm lại

Module là ranh giới dependency; package là ranh giới code/import. Hãy quan sát
`GOMOD` trước khi sửa, và dùng vòng lặp viết - format - test - vet để tạo phản
hồi ngắn. Chương sau sẽ đặt một chương trình đầu tiên vào đúng các ranh giới
đó, thay vì ném một file `main.go` vào bất kỳ thư mục nào rồi cầu may.

