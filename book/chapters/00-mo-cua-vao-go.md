<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Mở cửa vào Go

Một tệp mã nguồn Go trước hết chỉ là một chuỗi byte văn bản thuần túy được lưu trữ trên hệ thống tệp. Trình biên dịch không có khả năng suy đoán ý định chủ quan của lập trình viên; nó chỉ vận hành như một cỗ máy trạng thái khắt khe: bóc tách văn bản thành các từ vựng cú pháp (tokens), đối chiếu cấu trúc với ngữ pháp chính thức được quy định trong Go Specification, kiểm tra tính hợp lệ của hệ thống kiểu tĩnh, và chuyển đổi logic đó thành chỉ thị mã máy cho bộ xử lý.

Để bắt đầu, ta không học thuộc lòng danh sách từ khóa trừu tượng. Việc quan trọng nhất là giải phẫu cấu trúc giải tích của một tệp Go: phần nào xác lập không gian tên của gói, phần nào nạp công cụ từ thư viện chuẩn, và cơ chế nào cho phép runtime điều phối quyền thực thi trước khi câu lệnh đầu tiên trong hàm chính bắt đầu vận hành.

## Chương trình tối thiểu và Luồng thực thi

Hãy quan sát một chương trình Go nguyên tử có thể biên dịch và thực thi độc lập, được lưu trong tệp `main.go`:

~~~go
package main

import "fmt"

func main() {
	fmt.Println("he thong san sang")
}
~~~

Để chỉ thị bộ công cụ biên dịch và chạy tệp mã nguồn trên môi trường dòng lệnh, ta thực thi:

~~~bash
go run main.go
~~~

Chương trình xuất ra dòng chữ `he thong san sang` trên thiết bị đầu ra tiêu chuẩn (stdout). Đằng sau bốn dòng mã ngắn gọn này là toàn bộ chuỗi khép kín của mô hình biên dịch tĩnh và khởi tạo thời gian chạy (runtime bootstrap).

## Bóc tách Cú pháp Nguyên tử

Mỗi thành phần trong chương trình trên đại diện cho một vai trò ngữ pháp không thể thay thế trong đồ thị biên dịch của Go.

### Khai báo gói và Không gian tên: `package main`

Từ khóa `package` là chỉ thị bắt buộc mở đầu mọi tệp nguồn Go hợp lệ. Nó xác định rằng mọi định danh nằm trong tệp này thuộc về một đơn vị biên dịch có tên là `main`.

Theo đặc tả chính thức của Go, một chương trình hoàn chỉnh có thể thực thi độc lập (complete program) được tạo thành bằng cách liên kết một package không được package nào khác import, gọi là main package, cùng toàn bộ các package phụ thuộc bắc cầu của nó. Main package này bắt buộc phải có tên package là `main` và phải chứa một khai báo hàm `main` không nhận tham số và không trả về kết quả (`func main()`). Khai báo `package main` đơn thuần chưa đủ để sinh ra file thực thi nếu thiếu định nghĩa hàm `main`. Ngược lại, một package không phải `main` đại diện cho một thư viện; khi chạy lệnh `go build` trên một thư viện như vậy, bộ công cụ Go sẽ biên dịch mã nguồn để kiểm tra tính hợp lệ về cú pháp và kiểu dữ liệu nhưng mặc định không phát sinh tệp thực thi nào trên đĩa.

### Nhập thư viện chuẩn: `import "fmt"`

Từ khóa `import` nạp giao diện và kiểu dữ liệu từ gói thư viện bên ngoài vào phạm vi tệp hiện tại. Định danh chuỗi `"fmt"` trỏ tới gói thư viện định dạng dữ liệu vào ra (Format I/O) thuộc Go Standard Library.

Trình biên dịch Go thiết lập một quy tắc khắt khe về độ sạch của mã nguồn tại thời điểm biên dịch: mọi package được khai báo trong mệnh đề `import` đều bắt buộc phải được sử dụng thông qua tên package đó trong mã nguồn, ngoại trừ các trường hợp nhập khẩu đặc biệt như định danh trống `_` để kích hoạt hiệu ứng khởi tạo (`init()`) hoặc dấu chấm `.` để đưa định danh vào phạm vi cục bộ. Nếu một gói được nạp nhưng không có mã nào tham chiếu tới, trình biên dịch sẽ lập tức báo lỗi và từ chối phát sinh mã máy. Đây là quy tắc giữ gìn vệ sinh mã nguồn ở tầng cú pháp, giúp lập trình viên không tích tụ các import thừa trong quá trình tái cấu trúc.

### Hàm khởi điểm và Giai đoạn Runtime Bootstrap: `func main()`

Từ khóa `func` định nghĩa một hàm. Tên hàm `main` đại diện cho điểm nhập cuộc thực thi logic của người dùng. Hàm `main` khởi điểm không nhận bất kỳ tham số nào và không trả về giá trị.

Tuy nhiên, hàm `main` của người dùng không phải là thứ đầu tiên chạy khi tiến trình được tải vào bộ nhớ hệ điều hành. Trước khi lệnh đầu tiên trong `func main()` được kích hoạt, Go runtime phải trải qua giai đoạn khởi tạo nền tảng (runtime bootstrap): thiết lập bộ cấp phát bộ nhớ (`mallocgc`), khởi tạo bộ điều phối luồng (`schedinit`), tạo goroutine chính đầu tiên, gán giá trị cho toàn bộ các biến ở cấp độ gói, và gọi tuần tự toàn bộ các hàm khởi tạo `init()` theo thứ tự đồ thị phụ thuộc giữa các package. Chỉ khi mọi ràng buộc khởi tạo đó hoàn tất, runtime mới chính thức chuyển quyền điều khiển sang `main.main()`.

### Truy xuất định danh công khai và Xuất dữ liệu: `fmt.Println`

Định danh `fmt` tham chiếu tới gói thư viện đã nạp. Toán tử dấu chấm `.` là toán tử truy xuất thành viên thuộc gói.

Trong Go, quy tắc xuất khẩu định danh (export rule) được mã hóa trực tiếp vào cú pháp: mọi hàm, biến hoặc kiểu dữ liệu bắt đầu bằng chữ cái in hoa (như `Println`) đều được công khai để bên ngoài sử dụng. Ngược lại, những định danh bắt đầu bằng chữ cái in thường là riêng tư cục bộ bên trong gói. Hàm `Println` nhận chuỗi ký tự nguyên văn `"he thong san sang"` và phát tín hiệu ghi dữ liệu ra mô tả tệp số 1 (stdout) của hệ điều hành.

## Biên dịch Mã máy: Phân biệt `go run` và `go build`

Bộ công cụ Go cung cấp hai lệnh cơ bản với vai trò rõ ràng trong vòng đời phát triển:

| Câu lệnh | Hợp đồng công cụ (Tool Contract) | Hành vi tệp trên đĩa | Bối cảnh sử dụng |
| :--- | :--- | :--- | :--- |
| `go run [packages/files]` | Biên dịch và thực thi ngay main package được chỉ định (`compiles and runs the named main package`). | Không phát sinh tệp nhị phân trong thư mục làm việc hiện hành. | Thử nghiệm nhanh cục bộ, chạy kịch bản tự động hóa hoặc kiểm tra logic tức thời. |
| `go build [packages/files]` | Biên dịch mã nguồn và liên kết toàn bộ phụ thuộc thành tệp thực thi độc lập. | Phát sinh trực tiếp tệp nhị phân tại thư mục hiện hành (`main.exe` trên Windows, `main` trên Linux/macOS). | Đóng gói bản phát hành, triển khai môi trường máy chủ và hệ thống production. |

Về mặt chi tiết triển khai (implementation behavior) của toolchain Go 1.27.1, lệnh `go run` tạo file nhị phân tạm thời trong thư mục làm việc tạm của tiến trình xây dựng (`work directory`), chạy tiến trình từ đó rồi tự động xóa sạch khi kết thúc. Cần phân biệt rõ thư mục tạm này với bộ đệm biên dịch (`GOCACHE`) — nơi Go lưu trữ siêu dữ liệu và tệp đối tượng tái sử dụng giữa các lần biên dịch độc lập.

Tệp nhị phân sinh ra từ `go build` là mã máy thực thi trực tiếp trên vi kiến trúc CPU đích. Nó không chạy trên máy ảo như bytecode của Java và không dựa vào trình thông dịch như Python.
 

Một tệp nhị phân Go chứa sẵn toàn bộ mã máy của ứng dụng, siêu dữ liệu kiểu, và toàn bộ Go runtime thu nhỏ (bao gồm Garbage Collector và Scheduler). Trên Linux mục tiêu, khi biên dịch với cờ vô hiệu hóa cgo (`CGO_ENABLED=0`), bộ công cụ sẽ ưu tiên các bộ phân giải thuần Go (như thuần Go DNS resolver thay vì gọi hàm `getaddrinfo` của `glibc`), tạo ra một file thực thi định dạng ELF liên kết tĩnh. Tệp nhị phân tĩnh này có thể đặt vào một container rỗng tối giản (`scratch`) trên Linux cùng kiến trúc phần cứng. Tuy nhiên, nếu chương trình cần xác thực chứng chỉ TLS khi gọi dịch vụ bên ngoài hoặc xử lý múi giờ địa phương theo tên, container vẫn cần cung cấp kho chứng chỉ gốc CA (`ca-certificates`) và dữ liệu múi giờ (`tzdata`), hoặc chương trình phải chủ động nhúng các tài nguyên này thông qua gói thư viện chuẩn tương ứng.

## Vòng lặp Phản hồi: Giả thuyết, Đo đạc và Giải thích

Học kỹ thuật hệ thống đòi hỏi thói quen xây dựng mô hình dự đoán trước khi thực thi lệnh. Thay vì sửa mã nguồn một cách ngẫu nhiên, kỹ sư luôn đặt câu hỏi: nếu ta làm sai lệch một quy tắc ngữ pháp hoặc kiểu dữ liệu, trình biên dịch sẽ phát hiện lỗi ở tầng phân tích nào?

![Vòng lặp phản hồi khi học và viết Go](../../assets/diagrams/feedback-loop.png)

@figure Vòng lặp phản hồi giả thuyết - đo đạc - sửa mã nguồn. Trình biên dịch không phải là chướng ngại vật; trình biên dịch là công cụ kiểm định tĩnh sớm nhất cho các dự đoán của bạn.

Bảng dưới đây minh họa ba thí nghiệm nhỏ về ranh giới kiểm tra tĩnh của Go compiler:

| Thí nghiệm kiểm chứng | Thao tác thay đổi mã nguồn | Phản hồi từ trình biên dịch | Cơ chế phân tích của Compiler |
| :--- | :--- | :--- | :--- |
| Đổi tên gói khởi điểm | Đổi `package main` thành `package worker`, sau đó chạy `go run main.go`. | `package command-line-arguments is not a main package` | Giai đoạn phân tích ngữ nghĩa (semantic analysis) xác định gói đích không thỏa mãn điều kiện tạo tệp thực thi độc lập. |
| Nạp thư viện không sử dụng | Thêm dòng `import "time"` nhưng không gọi hàm nào của gói `time`. | `imported and not used: "time"` | Trình phân tích AST kiểm tra việc sử dụng định danh; từ chối mọi gói thừa nhằm giữ cây phụ thuộc tinh gọn. |
| Khai báo biến cục bộ thừa | Khai báo `workerID := 1` trong thân hàm `main` nhưng không đọc lại. | `workerID declared and not used` | Phân tích dòng dữ liệu xác định biến cục bộ không đóng góp vào kết quả chương trình, phát hiện mã chết ngay lúc biên dịch. |

Sự khắt khe của trình biên dịch không phải là sự phiền toái ngẫu nhiên. Bằng cách ngăn chặn mã thừa, biến chết và sai lệch không gian tên ngay tại thời điểm biên dịch, Go loại bỏ phần lớn các lỗi vận hành tiềm ẩn trước khi chương trình có cơ hội chạm tới môi trường production. Chương tiếp theo sẽ dẫn dắt bạn đi sâu vào từng khối xây dựng cốt lõi của một chương trình Go: định danh, kiểu dữ liệu, phạm vi biến, và biểu diễn hợp ngữ thực tế của máy tính.
