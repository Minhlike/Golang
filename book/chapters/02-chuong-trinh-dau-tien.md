# Chương 2. Một chương trình Go bắt đầu từ package

Một file Go không tự nhiên trở thành một chương trình chỉ vì có `func main`.
Nó trước hết thuộc về một package. Với executable, package đó phải tên `main`
và cần một hàm `main` không tham số, không return. Compiler dùng quy ước này để
biết điểm bắt đầu của binary; nó không phải lời mời gọi nhét toàn bộ project vào
một file.

## Tạo module nhỏ

Trong một thư mục mới, chạy `go mod init example.com/hello`. Module path ở đây
là định danh logic; nếu sau này publish code, nó thường trùng địa chỉ repository
để người khác import được. Với bài lab cục bộ, `example.com` là domain được
dành cho ví dụ, nên không giả vờ rằng ta sở hữu một domain thật.

Tạo `main.go`:

```go
package main

import "fmt"

func main() {
	name := "Anh"
	fmt.Printf("Chào %s, hãy thay đổi một dòng rồi chạy lại.\n", name)
}
```

`:=` vừa khai báo biến mới vừa để compiler suy luận kiểu từ biểu thức bên phải.
Ở đây `name` có kiểu `string`. Suy luận kiểu không có nghĩa Go là dynamically
typed: kiểu vẫn được xác định khi compile, và việc gán sau đó phải phù hợp. Nếu
anh viết `name = 42`, compiler dừng trước khi binary tồn tại. Đây là một lỗi
rẻ: phát hiện lúc build thường rẻ hơn phát hiện lúc service đang phục vụ người
dùng.

Chạy `go run .`. Dấu chấm nghĩa là package trong thư mục hiện tại, chứ không
phải “chạy file vừa mở trong editor”. Thói quen này quan trọng ngay khi package
có nhiều file hoặc build tags. `go run` build một executable tạm rồi chạy nó;
để tạo artifact có thể đưa cho người khác, dùng `go build -o bin/hello .`.

## Đọc lỗi compiler như một tọa độ

Hãy cố ý đổi import thành `"fmtt"` rồi chạy lại. Error message có thể trông
khó chịu, nhưng nó thường nói ba thứ hữu ích: package hoặc file nào lỗi, dòng
nào, và compiler đang thiếu điều gì. Đừng sửa mù theo phần cuối message. Đọc
từ dòng đầu liên quan source, sửa lỗi gốc, rồi chạy lại; một lỗi import có thể
kéo theo nhiều thông báo phụ.

Một lỗi khác hay gặp là import `fmt` rồi không dùng nó. Go coi unused import là
error vì import có thể tạo dependency và tác dụng khởi tạo; giữ import chết làm
đọc code khó hơn. Đây không phải compiler “khó tính cho vui”, mà là một lựa
chọn để dependency nhìn thấy được còn source giữ sạch.

## Zero value là một thiết kế tool

Khai báo `var retries int` mà chưa gán cho nó vẫn hợp lệ: giá trị ban đầu của
`int` là `0`. `bool` là `false`, string là chuỗi rỗng, pointer/map/slice/channel/
function/interface là `nil`. Zero value giúp type có thể dùng được ngay mà không
cần constructor khi điều đó hợp lý, nhưng không biến `nil` thành an toàn. Việc
ghi vào nil map sẽ panic; đọc nil map thì hợp lệ và trả zero value của element.
Ta sẽ quay lại chi tiết aliasing và nil ở chương dữ liệu.

```go
var attempts int
var ready bool

fmt.Println(attempts, ready) // 0 false
```

Đoạn trên in output xác định. Nếu ví dụ sau này phụ thuộc thời gian, network
hoặc scheduler, sách sẽ nói rõ điều đó thay vì hứa hẹn một output đẹp nhưng
không lặp lại được.

## Điểm nối sang DevOps/SRE

Một CLI health check nhỏ hay exporter lớn đều bắt đầu từ package `main`, nhưng
đa số logic không nên sống ở đó. `main` thường chỉ wiring: đọc config, tạo
dependency, gọi luồng chính và quyết định exit code. Logic kiểm tra HTTP, parse
file hay tính retry nên ở package riêng để test không cần fork process. Chưa cần
xây kiến trúc ngay hôm nay; chỉ cần thấy rằng cách ta khởi động chương trình đã
ảnh hưởng trực tiếp tới cách ta kiểm thử và vận hành nó sau này.

## Bài tập

Không chạy code trước. Dự đoán: chương trình dưới đây compile hay không? Nếu
compile, nó in gì? Sau đó hãy tạo module và kiểm tra dự đoán.

```go
package main

import "fmt"

func main() {
	var port int
	port = port + 8080
	fmt.Println(port)
}
```

---

## ĐÁP ÁN - chỉ đọc sau khi đã tự làm

Nó compile và in `8080`. `port` nhận zero value `0`, rồi phép cộng tạo giá trị
mới để gán lại. Cạm bẫy là nhầm zero value với “chưa có giá trị” trong mọi miền
nghiệp vụ. Với port, `0` còn có nghĩa đặc biệt trong một số API network; vì vậy
khi dữ liệu cần phân biệt “không được cấu hình” với số 0, ta cần một biểu diễn
khác như pointer, boolean riêng hoặc type có ý nghĩa rõ ràng.

## Tóm lại

`package main` và `func main` là entry point theo quy ước của executable. `go
run .` chạy package hiện tại; `go build` tạo artifact. Type inference vẫn là
static typing, còn zero value là một tính năng thiết kế có ích nhưng cần được
đọc trong ngữ cảnh. Chương tiếp theo sẽ dùng các kiểu và control flow để biến
một chương trình chỉ in text thành một chương trình có quyết định rõ ràng.

## Nguồn

- Go Language Specification: Packages, Program initialization and execution,
  Variables.
- Effective Go: Formatting; Control structures.
- Go command documentation, `go.dev/cmd/go`.

