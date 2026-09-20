# Chương 4. Hàm, error và defer: đặt ranh giới trước khi có sự cố

Một hàm tốt không chỉ gom code cho gọn. Nó đặt tên cho một quyết định, thu nhỏ
số trạng thái phải theo dõi, và tạo nơi có thể kiểm thử mà không cần khởi động
cả chương trình. Với tool DevOps/SRE, ranh giới này đặc biệt quan trọng: hàm
parse config không nên âm thầm gọi network; hàm gọi network không nên giấu
timeout; hàm main không nên chứa mọi policy lẫn I/O.

## Parameter và result là hợp đồng nhỏ

Go cho phép nhiều result vì thao tác thực tế thường trả giá trị cùng trạng thái
thất bại. Đây không phải ngoại lệ ngôn ngữ kiểu ném rồi bắt; error là một
interface value được trả về như dữ liệu bình thường.

~~~go
func ParsePort(raw string) (int, error) {
    port, err := strconv.Atoi(raw)
    if err != nil {
        return 0, fmt.Errorf("parse port %q: %w", raw, err)
    }
    if port < 1 || port > 65535 {
        return 0, fmt.Errorf("port %d is outside 1..65535", port)
    }
    return port, nil
}
~~~

0, err ở các nhánh lỗi không khẳng định 0 là một port hợp lệ. Nó chỉ là result
không dùng được khi err khác nil. Caller phải xử lý error trước khi dùng result.
Lời hứa này là convention mạnh của Go, không phải phép kiểm tra tự động của
compiler; vì thế cách trả và kiểm tra error cần nhất quán.

Định dạng percent-w trong fmt.Errorf giữ error gốc để sau này code gọi có thể
dùng errors.Is hoặc errors.As. Ta sẽ đi sâu thiết kế error ở chương abstraction.
Ở đây, hãy giữ nguyên tắc gần hơn: thêm ngữ cảnh tại boundary có ích, nhưng
đừng wrap cùng một lỗi ba lần chỉ để log trông dài hơn.

## Đừng nuốt error

Giả sử startServer đã được khai báo hợp lệ, đoạn sau vẫn compile nhưng đánh mất
bằng chứng quan trọng nhất khi config hỏng:

~~~go
port, _ := strconv.Atoi(raw)
startServer(port)
~~~

Nếu raw là eighty, port nhận 0 và lỗi gốc biến mất. Hậu quả có thể là server
nghe nhầm port hoặc thất bại ở nơi xa nguyên nhân. Dùng dấu gạch dưới chỉ khi
anh đã chứng minh error không thể xảy ra hoặc thật sự không liên quan, và
comment lý do nếu người đọc kế tiếp có thể nghi ngờ. Trong application code,
điều đó hiếm hơn ta tưởng.

## Variadic và named result: tiện, không phải mánh khóe

Parameter variadic như func Join(parts ...string) string nhận zero hoặc nhiều
argument. Nó hợp với API có nghĩa một danh sách cùng loại, nhưng không thay thế
một struct config khi tham số có vai trò khác nhau. Named result có thể làm chữ
ký dễ đọc, song dùng return trần trong hàm dài khiến đường dữ liệu khó theo.
Edition này ưu tiên return value, err rõ ràng trừ khi named result thực sự diễn
đạt domain tốt hơn.

## defer đăng ký cleanup ngay khi có resource

defer đặt một lời gọi để chạy khi hàm bao quanh return. Đối số của lời gọi defer
được đánh giá ngay lúc gặp defer; bản thân lời gọi chạy sau. Điều này làm cleanup
gần nơi acquire resource, nên đường return sớm không bỏ quên nó.

~~~go
file, err := os.Open(path)
if err != nil {
    return err
}
defer file.Close()

return process(file)
~~~

Nhiều defer chạy theo LIFO: cái đăng ký sau chạy trước. Điều này thường đúng
với resource lồng nhau. Nhưng defer không tạo retry, không log error Close một
cách thần kỳ, và không làm một hàm chạy mãi có cleanup sớm hơn. Với vòng lặp
lớn, đặt defer trong cùng một hàm có thể giữ resource tới cuối hàm; hãy tách
thân mỗi iteration vào hàm nhỏ nếu cần release sớm.

## panic và recover không phải đường error thông thường

panic dừng flow bình thường và unwinding stack, chạy các deferred call trên
đường đi. Nó hợp với bất biến bị phá vỡ hoặc lỗi không thể tiếp tục an toàn,
không phải với file không tồn tại, HTTP 500 hay input người dùng. Những tình
huống ấy là expected failure và nên đi qua error.

recover chỉ bắt được panic khi gọi trực tiếp từ deferred function trong cùng
goroutine. Nó không phải hàng rào toàn cục cho mọi goroutine, và dùng nó để che
bug sẽ khiến process trông còn sống nhưng state đã không đáng tin. Ở HTTP server
production, một recovery boundary hẹp có thể giúp cô lập request; nó vẫn phải
ghi log, tăng metric và trả lỗi có kiểm soát. Ta sẽ quay lại khi đã có HTTP và
observability.

## Lab: parse port, giữ nguyên nguyên nhân

labs/ch04-portcheck parse string thành TCP port. Test table-driven bao phủ input
hợp lệ, không phải số, 0 và 65536. Đọc từng test trước; sau đó thử bỏ range
check và quan sát chính xác test nào báo rule bị mất. Đừng đổi expected chỉ để
test xanh: expected là policy của tool, không phải vật cản.

### Bài tập

Đây là snippet cố ý chỉ tập trung vào error path, không phải file hoàn chỉnh.
Hãy chỉ ra hai lỗi thiết kế trong nó và viết lại ý tưởng, chưa cần code:

~~~go
func Run(rawPort string) {
    port, _ := strconv.Atoi(rawPort)
    defer fmt.Println("done")
    panic(startServer(port))
}
~~~

---

### ĐÁP ÁN - chỉ đọc sau khi đã tự làm

Thứ nhất, error từ parse bị nuốt, nên input xấu bị biến thành port 0 mà không
còn bối cảnh. Thứ hai, panic được dùng như đường điều khiển cho lỗi có thể dự
đoán từ startServer; caller không còn lựa chọn xử lý hay trình bày lỗi. Hàm nên
trả error, kiểm tra parse và range trước, rồi để main quyết định log và exit
code. defer có thể giữ cho cleanup hoặc log thật sự cần chạy khi return, chứ
không bù cho policy lỗi sai.

## Tóm lại

Hàm là ranh giới cho logic và test. Multiple result đặt value cạnh error; xử lý
error gần nơi nó xảy ra giữ nguyên bằng chứng. defer là công cụ cleanup có thứ
tự, còn panic và recover là cơ chế hẹp cho trạng thái bất thường, không phải
shortcut để khỏi thiết kế error path. Chương dữ liệu sẽ dùng những ranh giới
này để xem slice, map và pointer chia sẻ hay sao chép điều gì.
