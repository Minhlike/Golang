<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Chương 7 — Dữ liệu đi vào và đi ra

Một lệnh vừa in ra một dòng `billing healthy=true` có vẻ như đã giao tiếp được với thế giới bên ngoài. Nhưng terminal chỉ là một `io.Writer` rất đặc biệt. Khi dữ liệu vào chuyển thành tệp cấu hình, pipe từ lệnh khác, body HTTP hay một stream nén, trực giác “đọc file rồi có dữ liệu” bắt đầu che một sự thật quan trọng: dữ liệu không nhất thiết đến cùng lúc, và tài nguyên không tự hết hạn đúng lúc ta muốn.

Mô hình tinh thần của chương này là stream cung cấp byte theo từng lượt, không phải một slice đã có đủ dữ liệu. Caller phải xử lý byte nhận được, xác nhận điểm kết thúc và biết ai chịu trách nhiệm đóng tài nguyên. `io.Reader` không tự hứa một deadline hay tiến độ trong thời gian hữu hạn; những chính sách ấy thuộc nguồn dữ liệu và application.

## Một lần `Read` không có nghĩa là toàn bộ input

Hãy bắt đầu với một lỗi nhỏ hơn `opsprobe`. Một cấu hình JSON trông như thế này:

~~~json
[
  {
    "name": "billing",
    "endpoint": "https://billing.internal/health"
  }
]
~~~

Một cách nghĩ sai lầm nhưng phổ biến là cấp phát vùng đệm (*buffer*) đủ lớn cho ca kiểm thử, gọi phương thức `Read` một lần duy nhất, rồi suy luận số byte nhận được. Cách làm này thường vượt qua kiểm thử với `strings.NewReader` và dữ liệu đầu vào ngắn. Nhưng `io.Reader` không cam kết sẽ lấp đầy vùng đệm. Nguồn đọc (*reader*) có thể là tệp, ổ cắm mạng (*socket*), đường ống dẫn (*pipe*) hay bộ giải mã khác; mỗi lần gọi phương thức chỉ tiếp nhận một phần lượng byte sẵn có.

Giao ước (*contract*) tối thiểu của `Read(p)` quy định: hàm trả về `n` byte nằm trong lát cắt `p[:n]`, và có thể kèm theo một lỗi. Giá trị `n` hoàn toàn có thể nhỏ hơn `len(p)`. Đặc biệt, một nguồn đọc được phép trả về các byte dữ liệu hữu ích đi kèm mã lỗi lính canh `io.EOF` ngay trong một lượt gọi; bên gọi (*caller*) bắt buộc phải tiêu thụ dữ liệu `p[:n]` trước khi xử lý lỗi. Tín hiệu `io.EOF` biểu thị luồng dữ liệu đã kết thúc hoàn toàn, không đồng nghĩa với việc lần đọc hiện tại không chứa dữ liệu.

@table Cách đọc kết quả `Read`

| Kết quả | Caller phải làm gì | Diễn giải đúng |
| --- | --- | --- |
| `n > 0`, `err == nil` | Xử lý `p[:n]`, rồi đọc tiếp | Stream đang tiến lên nhưng chưa kết thúc. |
| `n > 0`, `err == io.EOF` | Vẫn xử lý `p[:n]`, rồi kết thúc | Lượt cuối vừa có dữ liệu vừa báo hết stream. |
| `n > 0`, error khác `nil` | Xử lý `p[:n]`, rồi trả hoặc phân loại lỗi | Dữ liệu có thể tới cùng lỗi khác EOF; không được bỏ phần đã đọc. |
| `n == 0`, `err == io.EOF` | Kết thúc | Không còn byte để tiêu thụ. |
| `n == 0`, error khác `nil` | Trả hoặc phân loại lỗi | Lượt này không trả byte và có lỗi. |
| `n == 0`, `err == nil` | Không coi là EOF; tránh vòng busy-loop vô hạn | Không có tiến độ trong lượt này; contract không khuyến khích kết quả ấy với buffer không rỗng nhưng caller vẫn phải phân biệt nó. |

Đừng tự viết vòng lặp `Read` thủ công chỉ để chứng minh mình nắm vững giao ước nếu thư viện chuẩn đã cung cấp sẵn công cụ nguyên thủy (*primitive*) phù hợp. Hàm `io.ReadAll` là lựa chọn xác đáng khi dữ liệu đầu vào có giới hạn kích thước tin cậy và việc lưu trữ toàn bộ dữ liệu trong bộ nhớ là chấp nhận được. Khi dữ liệu đầu vào có khả năng tăng đột biến hoặc vô hạn, thiết kế bắt buộc phải chuyển sang kỹ thuật truyền dữ liệu phân đoạn (*streaming*). Sự khác biệt này không đơn thuần là tối ưu vi mô: nó quyết định chương trình có bị áp lực cấp phát bộ nhớ cưỡng bức bởi dữ liệu đầu vào không kiểm chứng hay không.

## Giới hạn byte trước khi gọi parser

“Tệp cấu hình chỉ nhỏ” không phải là một giới hạn. Nếu chương trình nhận một đường dẫn hoặc reader từ bên ngoài, nó cần đặt giới hạn ngay tại ranh giới mình kiểm soát. Chỉ đặt giới hạn sau `json.Decode` là quá muộn: bộ phân tích đã có quyền đọc bất cứ lượng byte nào trước khi chính sách được áp dụng.

Trước khi mở `bounded.go`, chỉ đọc hai test `TestReadBounded...`. Chúng đòi `ReadBounded` nhận tối đa `max` byte; input lớn hơn đúng một byte phải trả error mà caller nhận diện được bằng `errors.Is`. Hãy tự viết phần thân theo ba bước: bọc reader để chỉ cho phép tối đa `max + 1` byte, đọc phần đã bọc, rồi so độ dài với `max`. Byte thứ `max + 1` không phải dữ liệu cần giữ; nó là bằng chứng phân biệt tệp vừa chạm ngưỡng với tệp thật sự vượt ngưỡng.

Lab từ chối `max < 0` và `max == math.MaxInt64` trước khi đọc: giá trị sau không cho phép tính `max + 1` trong `int64`. Không sửa tràn số bằng cách bỏ lớp giới hạn rồi gọi `io.ReadAll(r)` không giới hạn. Test dùng reader ghi nhận lời gọi để kiểm tra đầu vào bị từ chối mà chưa đọc; không cần tạo tệp khổng lồ. Giới hạn byte cũng không phải trần heap chính xác: buffer, parser và metadata có chi phí riêng.

`io.LimitReader` chỉ giới hạn số byte mà reader bọc ngoài sẽ trả; nó không tự nói JSON có hợp lệ hay không, và cũng không làm input nhỏ trở nên đáng tin. Vì thế giới hạn byte là một chính sách tài nguyên riêng; `Decode` vẫn chịu trách nhiệm cho cấu trúc JSON và số tài liệu. Hai test ngắn bảo vệ hai câu hỏi khác nhau, không gộp chúng thành một assertion mơ hồ kiểu “cấu hình lỗi”.

Đây cũng là điểm cần tránh một cam kết sai lầm về cơ chế hủy bỏ (*cancellation*). Giao diện `io.Reader` chỉ công bố phương thức `Read`; nó không tiếp nhận `context.Context`. Một lớp bọc (*wrapper*) như `ReadBounded` có thể dừng sau khi đọc đủ ngưỡng byte, nhưng không thể tự đánh thức một nguồn đọc cơ sở bên dưới đang bị nghẽn thao tác vào/ra (*blocking I/O*). Với tệp cục bộ, điều đó thường không phải chính sách bắt buộc. Với thân thông điệp HTTP (*HTTP body*), thời hạn chót (*deadline*) và tín hiệu hủy bỏ gắn liền với vòng đời của yêu cầu mạng sẽ được phân tích ở chương mạng, nơi ta xác định rõ quyền sở hữu kết nối và cách tầng vận chuyển phản hồi.

## Failing test trước parser

Lab `labs/part7-stream-boundaries` không gắn ngay tệp JSON vào `opsprobe`. Project xuyên suốt hiện chưa cần tệp cấu hình; nhét nó vào lúc này chỉ khiến trực giác mới bị lẫn với chính sách endpoint cũ. Ta dùng một chương trình tái hiện tối thiểu để thấy ranh giới stream trước.

Hãy mở tệp `targets/targets_test.go` và quan sát ca kiểm thử `TestDecodeConsumesChunkedStream`. Cấu trúc `chunkReader` cố ý chỉ giải phóng ba byte dữ liệu trong mỗi lần gọi. Trước khi đọc phần triển khai của hàm `Decode`, hãy trả lời: nếu mã nguồn giả định ngây thơ rằng một lượt `Read` là đủ, ca kiểm thử sẽ đánh mất đoạn nào của tài liệu? Sau đó, hãy tạm đổi tên hàm `Decode`, chạy kiểm thử và tự xây dựng lại hàm theo đúng giao ước mà ca kiểm thử đòi hỏi.

Function kết thúc có thể nhỏ:

~~~go
func Decode(r io.Reader) ([]Target, error) {
	dec := json.NewDecoder(r)
	var targets []Target
	if err := dec.Decode(&targets); err != nil {
		return nil, fmt.Errorf(
			"decode target document: %w", err,
		)
	}

	var extra any
	if err := dec.Decode(&extra); !errors.Is(err, io.EOF) {
		if err == nil {
			return nil, errors.New(
				"target config must contain one JSON value",
			)
		}
		return nil, fmt.Errorf(
			"read after target document: %w", err,
		)
	}
	return targets, nil
}
~~~

`json.Decoder` tiếp nhận một `io.Reader`, do đó nó tự động đọc qua nhiều khối dữ liệu (*chunk*); bên gọi không cần giả định sai lầm rằng ổ cắm mạng hay tệp tin là một lát cắt bộ nhớ có sẵn. Ca kiểm thử thứ hai đặt thêm một giá trị JSON phía sau tài liệu đầu tiên. Việc chỉ gọi `Decode` một lần duy nhất chưa đáp ứng đầy đủ giao ước: chương trình sẽ âm thầm bỏ qua phần dữ liệu dư thừa còn lại. Lần gọi `Decode` thứ hai không nhằm mục đích lấy cấu hình mới, mà để kiểm chứng rằng sau tài liệu hợp lệ chỉ còn khoảng trắng và ký hiệu kết thúc luồng `io.EOF`.

Điều này không biến bộ giải mã JSON thành lời giải vạn năng cho mọi định dạng. Tệp CSV có quy tắc phân tách bản ghi (*record*) và dấu trích dẫn (*quoting*) riêng; tệp nhật ký dòng lệnh (*line-oriented log*) có ranh giới phân tách theo ký tự xuống dòng; thân thông điệp HTTP có vòng đời mạng và giới hạn kích thước khác biệt. Các cơ chế đó sẽ được phân tích trong ngữ cảnh phù hợp. Ở đây, trọng tâm là câu hỏi kỹ thuật cốt lõi: dữ liệu đầu vào kết thúc ở đâu, và đoạn mã nào đã xác minh điều đó?

### Đủ một document chưa có nghĩa mọi decoder hiểu giống nhau

Dữ liệu đầu vào `{"port":80,"port":443}` là một tài liệu có khóa bị trùng lặp. Giao diện `encoding/json` mà phòng thực hành sử dụng giữ nguyên ngữ nghĩa v1: với trường số trong ví dụ này, giá trị khai báo sau sẽ ghi đè lên giá trị trước. Go 1.27 chính thức đưa `encoding/json/v2` và `encoding/json/jsontext` thành giao diện tiêu chuẩn; theo mặc định, phiên bản v2 sẽ từ chối các khóa trùng tên và chuỗi UTF-8 không hợp lệ. Giao diện v1 vẫn tiếp tục được hỗ trợ đầy đủ, mặc dù cơ chế cài đặt bên dưới có thể thay đổi và câu chữ chẩn đoán lỗi có thể khác biệt. Không được tùy tiện thay đổi đường dẫn nhập khẩu (*import path*) rồi xem đó là một đợt chuyển đổi mã nguồn (*migration*) tương đương.

Trước khi thực thi ca kiểm thử `TestJSONVersionBoundary` trong thư mục `labs/edition-contracts`, hãy dự đoán bộ giải mã nào chấp nhận tài liệu trên và giá trị `port` cuối cùng sẽ là bao nhiêu. Bài kiểm thử chỉ kiểm chứng hai trường hợp khóa trùng lặp và chuỗi UTF-8 không hợp lệ; nó không chứng minh bộ giải mã là công cụ kiểm định toàn bộ chính sách cấu hình. Giới hạn dung lượng byte, tính duy nhất của một tài liệu, lược đồ hợp lệ và ngữ nghĩa lựa chọn giao diện lập trình là bốn bài toán kỹ thuật hoàn toàn độc lập.

## Đóng output cũng là một phần của result

Khi đọc tệp, đăng ký `defer file.Close()` sau khi mở thành công giúp dọn file lúc hàm thoát. Khi ghi, phải quan sát cả lỗi ghi và lỗi đóng; nhưng `io.WriteCloser` không cam kết `Close` flush hay lưu dữ liệu bền vững xuống đĩa. Ý nghĩa ấy thuộc kiểu cụ thể. `bufio.Writer` không có `Close`: phải gọi và kiểm tra `Flush` trước khi đóng file bên dưới. `os.File.Close` không thay thế `File.Sync` nếu hợp đồng yêu cầu commit dữ liệu ổn định. Cả flush lẫn close thành công cũng không tự chứng minh cập nhật tệp là nguyên tử hoặc chống mọi sự cố mất điện.

Mã nguồn đầy đủ mở tài nguyên rồi thiết lập `defer Close` ngay sau điểm tiếp nhận. Để làm nổi bật chính sách chọn lọc kết quả, phần lõi có thể biểu diễn tinh gọn như sau:

~~~go
func save(w io.WriteCloser, targets []Target) error {
	writeErr := Encode(w, targets)
	closeErr := w.Close()
	if writeErr != nil {
		return writeErr
	}
	return closeErr
}
~~~

Mã nguồn thực tế vẫn giải phóng tài nguyên trên mọi nhánh trả về. Đoạn mã trên làm rõ chính sách kỹ thuật: ưu tiên giữ lại lỗi ghi trước, rồi mới phản hồi lỗi đóng tệp. Nguồn ghi giả lập bảo vệ giao ước đó mà không đòi hỏi phải phụ thuộc vào hệ thống tệp vật lý.

## Ranh giới Dữ liệu: Short Write, Bộ đệm và Ngộ nhận về Syscall

Khi làm việc với các dòng nhập xuất dữ liệu, trực giác bề mặt thường dẫn tới hai ngộ nhận tai hại: đánh đồng hành vi của Reader với Writer, và cho rằng mỗi thao tác đọc ghi đều kích hoạt một lời gọi hệ thống xuống nhân hệ điều hành.

### Ràng buộc Khắt khe của `io.Writer` và Khái niệm Short Write

Nếu như `io.Reader` cho phép trả về số byte đọc được `n < len(p)` kèm theo `err == nil` trong các tình huống bình thường (chẳng hạn khi đường ống mạng chưa nhận đủ dữ liệu), thì giao diện `io.Writer` lại áp đặt một hợp đồng nghiêm ngặt hơn nhiều. Theo đặc tả của thư viện chuẩn Go, một hàm `Write(p)` bắt buộc phải trả về một lỗi khác `nil` nếu nó không thể ghi trọn vẹn toàn bộ lát cắt dữ liệu (`n < len(p)`).

Biến lỗi `io.ErrShortWrite` là lỗi lính canh (*sentinel error*) mô tả một lượt ghi thiếu dữ liệu (*short write*) mà không có lỗi cụ thể đi kèm. Bộ ghi có thể trả về lỗi chi tiết khác; giao ước không bắt buộc mọi lượt ghi ngắn phải mang chính lỗi lính canh này. Nếu bộ ghi trả về `n < len(p)` kèm lỗi `nil`, hành vi đó vi phạm nghiêm trọng giao ước của giao diện `io.Writer`. Bên gọi sử dụng giao diện cần chủ động kiểm tra kết quả, không được suy diễn rằng dữ liệu đã tới đích cuối cùng chỉ vì thao tác ghi ở tầng trung gian báo thành công.

### Bộ đệm User-space với `bufio`

Một lời gọi hệ thống (*syscall*) đưa luồng thực thi vượt qua ranh giới giữa không gian người dùng (*user space*) và không gian nhân (*kernel space*). Thao tác này phát sinh chi phí tính toán nhất định, nhưng không đồng nghĩa với việc bộ lập lịch (*scheduler*) phải thực hiện chuyển đổi ngữ cảnh (*context switch*) sang luồng hệ điều hành (*OS thread*) khác; việc tạm hoãn (*blocking*) và tái lập lịch còn phụ thuộc vào bản chất thao tác và trạng thái sẵn sàng của tài nguyên. Ghi từng byte riêng lẻ qua tệp không có bộ đệm thường làm tăng đột biến số lượt thao tác vào/ra (*I/O*) so với việc gom thành khối lớn. Không thể suy đoán máy móc số lượng syscall hay mức sụt giảm thông lượng (*throughput*) chỉ từ số lần gọi phương thức `Write`; kỹ sư phải xác định rõ kiểu bộ ghi cụ thể (*concrete writer*) và tiến hành đo đạc trực tiếp trên hệ điều hành mục tiêu.

`bufio.Reader` và `bufio.Writer` thực hiện gom cụm dữ liệu trong vùng đệm thuộc không gian người dùng (*user space buffer*). Trong mã nguồn Go 1.27.1, hàm khởi tạo mặc định phân bổ kích thước vùng đệm 4096 byte; con số này không phải quy tắc bắt buộc của `io.Reader` hay cam kết rằng mọi vùng đệm đều phải có dung lượng tương tự. Bộ ghi chỉ chuyển dữ liệu xuống nguồn ghi cơ sở khi cần giải phóng dung lượng hoặc khi được gọi phương thức `Flush` tường minh; bên gọi bắt buộc phải kiểm tra lỗi trả về từ `Flush`. Vùng đệm hỗ trợ giảm số lượt gọi tầng dưới, chứ không bảo đảm một tỷ lệ cắt giảm syscall hay mức tăng thông lượng cố định.

### Lời gọi `Read` không đồng nghĩa với Syscall

Một ngộ nhận kỹ thuật phổ biến là mặc định rằng mọi lệnh `r.Read(p)` trong mã nguồn Go đều tương ứng với một chỉ thị CPU `SYSCALL` trực tiếp xuống kernel.

Đường dẫn thực thi đi qua vùng nhớ người dùng hay lời gọi hệ thống phụ thuộc vào bản cài đặt cụ thể, hệ điều hành và trạng thái thao tác. Bảng dưới đây phân định rành mạch các trường hợp thường gặp:

| Kiểu cụ thể của Reader | Bản chất cơ chế khi gọi `Read(p)` | Có phát sinh Syscall xuống OS không? |
| :--- | :--- | :--- |
| `*bytes.Buffer` hoặc `*strings.Reader` | Sao chép byte vào buffer của caller từ dữ liệu trong bộ nhớ. | Không cần syscall I/O cho phần sao chép; cách compiler hiện thực `copy` không phải contract của Reader. |
| `*bufio.Reader` (khi còn dữ liệu trong đệm) | `Read` sao chép byte từ đệm vào buffer của caller; khác với các API trả một slice nhìn vào đệm. | Không cần gọi underlying Reader trong lượt được phục vụ đủ từ đệm. |
| `*bufio.Reader` (khi bộ đệm đã cạn) | Gọi `Read` lên đối tượng `io.Reader` bên dưới để nạp lại bộ đệm nội bộ. | Phụ thuộc underlying Reader. Nếu bọc in-memory buffer thì không có syscall; nếu bọc file hoặc socket thì do reader bên dưới quyết định. |
| `*os.File` chưa đệm | Gửi yêu cầu I/O trực tiếp tới kernel qua bảng mô tả tệp (OS file I/O path). | Có. Thực hiện syscall đọc tệp của hệ điều hành (`read` trên Linux hoặc `ReadFile` trên Windows). |
| `*net.TCPConn` trong đường đọc Linux đã pin bên dưới | Thử non-blocking I/O; kết hợp poller nếu chưa sẵn sàng. | Có OS I/O; không có quan hệ một-một giữa số lần gọi `Read` và syscall. Windows dùng đường completion khác. |

Với Go 1.27.1 trên Linux, đường dẫn đọc ổ cắm mạng trong `internal/poll/fd_unix.go` có thể thử thao tác đọc không chặn (*non-blocking read*), gặp mã lỗi `EAGAIN`, chuyển quyền chờ cho bộ thăm dò mạng (*network poller*) rồi thử lại sau. Đây là mô hình triển khai cụ thể theo phiên bản, không phải cam kết bất biến của giao diện `net.Conn`. Không được áp đặt vết kiểm tra tính sẵn sàng (*readiness trace*) của Linux sang Windows: nền tảng IOCP sử dụng mô hình hoàn tất thao tác (*completion-based*) và cấu trúc xử lý khác biệt. Giao diện lập trình chung vẫn xoay quanh việc tiếp nhận byte, xử lý lỗi và kiểm soát thời hạn chót; bộ thăm dò mạng hỗ trợ điều phối goroutine hiệu quả chứ không thể triệt tiêu hoàn toàn thao tác vào/ra xuống hệ điều hành. Chương 11 sẽ tích hợp cơ chế này vào một yêu cầu mạng thực tế.

## Một filesystem là một khả năng, không phải một đường dẫn

Bộ phân tích cú pháp ở trên chỉ cần dữ liệu byte, hoàn toàn không đòi hỏi quyền mở mọi tệp tin trên máy chủ. Khi một ứng dụng có nhiều nguồn cung cấp tệp, giao diện `fs.FS` mô tả năng lực `Open(name)` với tên logic phân tách bằng dấu gạch chéo `/`. Bên tiêu dùng (*consumer*) có thể tiếp nhận `embed.FS` chứa tài nguyên nhúng tại thời điểm biên dịch, `os.DirFS` ánh xạ vào thư mục tại thời điểm thực thi, hoặc một hệ thống tệp giả lập phục vụ kiểm thử. Bên tiêu dùng không cần phải thay đổi bộ phân tích cú pháp theo từng nguồn cung cấp tệp.

~~~go
// Đặt trong package có thư mục fixtures tại build time.
//go:embed fixtures/*.txt
var files embed.FS

data, err := fs.ReadFile(files, "fixtures/message.txt")
~~~

Các gói nhập khẩu của đoạn mã này bao gồm `embed` và `io/fs`; bản chạy được đặt tại `labs/edition-contracts`. Chỉ thị tiền biên dịch (*compiler directive*) bắt buộc phải đặt tại phạm vi gói (*package scope*) và gắn liền với biến dữ liệu phù hợp. Dữ liệu byte được đóng gói trực tiếp vào tệp nhị phân tại thời điểm biên dịch, không tự động cập nhật khi tệp bên ngoài thay đổi. Giao diện `embed.FS` chỉ cung cấp năng lực đọc dữ liệu, không phải là nơi lưu trữ khóa bí mật (*secret*) hoặc cấu hình cần điều chỉnh sau khi triển khai. Các byte dữ liệu được đóng gói hoàn toàn có thể bị trích xuất từ tệp nhị phân; việc biến mất tệp tin rời rạc trên đĩa không đồng nghĩa với an ninh bảo mật.

Hàm `fs.ValidPath` không cho phép các thành phần đường dẫn `..` hoặc đường dẫn bắt đầu bằng dấu `/`; những tên như `a..b` vẫn có thể hợp lệ, còn `.` là trường hợp đặc biệt chỉ định thư mục gốc. Một đường dẫn hợp lệ không tự tạo ra vùng cách ly an toàn (*sandbox*). Hàm `os.DirFS` và `fs.Sub` không thể ngăn chặn các liên kết mềm bên dưới trỏ ra ngoài thư mục cơ sở. Nếu tiếp nhận tên tệp từ nguồn không tin cậy và đòi hỏi giới hạn truy cập nghiêm ngặt, hãy tham khảo giao ước của `os.Root` cùng các giới hạn theo hệ điều hành trong Go 1.27.1 thay vì tin tưởng mù quáng rằng hàm `Clean` chặn được mọi đường thoát. Quyền mở tệp và quyền phân tích cú pháp dữ liệu là hai ranh giới hoàn toàn độc lập.

`os.OpenRoot(base)` mở một khả năng truy cập có gốc; các thao tác như `root.Open(name)` không cho tên hoặc symlink dẫn ra ngoài cây đó. Nó vẫn đi theo symlink hợp lệ bên trong, không phải cấm mọi symlink. Với Go 1.27.1 trên Windows và Linux, đây là primitive chống traversal, nhưng không phải sandbox tiến trình: không chặn mọi truy cập thiết bị, mount hay hard link có sẵn trong root. Tài liệu còn nêu ngoại lệ TOCTOU trên `GOOS=js`; không suy rộng bảo đảm Windows sang mọi nền tảng.

Test `TestRealFilesystemRootConfinement` của lab tạo tệp và symlink trên filesystem thật trong thư mục tạm. Nó đối chiếu `DirFS` đọc được link ra ngoài với `Root` từ chối, đồng thời kiểm tra link nội bộ vẫn đọc được. Nếu hệ điều hành không cho tạo symlink, nhánh đó ghi SKIP với nguyên nhân, không chuyển thành PASS bằng `fstest.MapFS`. Test traversal `../outside.txt` chạy riêng dù thiếu quyền tạo link. Những phép thử này không mô phỏng kẻ tấn công đổi symlink đồng thời, nên chỉ là kiểm chứng các trường hợp đã chạy của API.

### Bài thực hành: Đọc tệp qua trừu tượng hóa fs.FS

Viết một hàm tiếp nhận `fs.FS` và tên logic, đọc một tệp rồi chuyển các byte dữ liệu cho bộ phân tích cú pháp đã có sẵn. Kiểm thử với hệ thống tệp giả lập; kiểm thử riêng cho các trường hợp tên tệp không hợp lệ và tệp bị thiếu. Sau đó thay thế bằng `embed.FS` mà không cần sửa đổi bộ phân tích cú pháp. Đừng để kiểm thử trên hệ thống tệp giả lập bị ngộ nhận thành bằng chứng khẳng định liên kết mềm (*symlink*) hoặc quyền truy cập thực tế trên hệ điều hành đã được bảo đảm an toàn.

## Parser cũng có ngân sách

Quy ước nhật ký “mỗi dòng là một bản ghi” khiến `bufio.Scanner` trở nên tiện lợi hơn vòng lặp đọc thủ công. Tuy nhiên, `Scanner` có giới hạn độ dài mã thông báo (*token*): một dòng nhật ký quá dài có thể khiến phương thức `Scan()` trả về `false` trước khi chạm tới ký hiệu kết thúc luồng `EOF`. Bên gọi bắt buộc phải kiểm tra `Err()`, và nếu miền nghiệp vụ cho phép độ dài dòng lớn hơn, hãy gọi phương thức `Buffer` trước khi quét với hạn mức trần thích hợp. Không bao giờ nâng mức trần lên vô hạn chỉ để cứu vãn một dữ liệu đầu vào bị hỏng. Ca kiểm thử `TestScannerLimitAndValidation` sử dụng cùng một dữ liệu đầu vào với hai hạn mức khác nhau để phân biệt trường hợp kết thúc hợp lệ với trường hợp vượt quá ngân sách tài nguyên.

Giới hạn dung lượng byte không thể thay thế cho thao tác kiểm tra miền giá trị số học. Hàm `strconv.ParseUint(text, 10, 16)` trả về lỗi nếu chuỗi văn bản không phải là số nguyên không dấu (*unsigned integer*) có thể biểu diễn trong 16 bit; sau đó quy tắc nghiệp vụ vẫn phải đưa ra quyết định liệu cổng mạng 0 có được phép hay không. Hàm `Atoi` chọn kiểu `int` phụ thuộc kiến trúc máy tính, không định nghĩa được một khuôn dạng truyền tải (*wire format*) ổn định. Khi định dạng đòi hỏi bề rộng bit chính xác, hãy chỉ định rõ bề rộng bit trong bộ phân tích cú pháp và kiểm thử kỹ lưỡng các giá trị biên.

Với biểu thức chính quy do người dùng nhập vào, hãy sử dụng `regexp.Compile` và xử lý lỗi cẩn trọng. Hàm `MustCompile` chỉ phù hợp với các mẫu biểu thức cố định trong mã nguồn mà sự cố cú pháp được coi là lỗi lập trình, không phải phương thức báo lỗi cho người vận hành. Gói `regexp` cam kết thời gian so khớp tuyến tính theo độ dài chuỗi đầu vào; điều đó không đồng nghĩa với việc chi phí biên dịch mẫu, dung lượng bộ nhớ hay tần suất so khớp không cần đặt giới hạn. Bộ phân tích cú pháp, số lượng bản ghi, mẫu biểu thức và vòng đời của luồng dữ liệu đều phải có ngân sách tài nguyên rõ ràng trong ứng dụng. Hãy ưu tiên các hàm trong gói `strings` hoặc `bytes` khi thao tác chỉ đơn giản là tìm kiếm ký tự phân tách hoặc tiền tố; chỉ bổ sung biểu thức chính quy khi ngữ pháp cú pháp thực sự đòi hỏi.

## Tự kiểm tra trước khi tích hợp

Chạy từ `labs/part7-stream-boundaries`:

~~~powershell
go test ./...
go vet ./...
~~~

> **Dừng để dự đoán:** Thử lần lượt: bỏ lượt `Decode` thứ hai; cho `chunkReader` nhả một byte; rồi cho writer giả fail ở `Write` trước `Close`. Hãy dự đoán ca kiểm thử nào sẽ thất bại.

#### Gợi ý giải pháp (chỉ đọc sau khi đã tự làm)

Bỏ lượt giải mã thứ hai làm `TestDecodeRejectsAdditionalDocument` thất bại; khối dữ liệu nhỏ hơn không làm thay đổi khế ước. Khi ghi và đóng tệp cùng gặp lỗi, phải ưu tiên giữ lại lỗi từ thao tác ghi.

Với limit, input dài đúng `max` byte được trả nguyên vẹn; input dài `max + 1` trả error giữ identity `ErrDocumentTooLarge`. Đó là lý do lab không dùng một `if len(data) == max` mơ hồ: bằng chứng cần phân biệt đúng ngưỡng với vượt ngưỡng.

Chương này không bổ sung tệp cấu hình vào `opsprobe`: hiện tại chưa có yêu cầu vận hành thực tế nào đòi hỏi điều đó. Đây là chủ đích bảo toàn công cụ giảng dạy phục vụ trọng tâm bài học. Khi xuất hiện yêu cầu thực tế đòi hỏi nhập xuất dữ liệu mục tiêu, các ranh giới luồng dữ liệu và chính sách đóng tài nguyên trong phòng thực hành này sẽ trở thành nền tảng vững chắc để tích hợp có chủ đích.

Trước khi tiếp cận một giao diện vào/ra mới, hãy tự đặt ra ba câu hỏi: Các byte dữ liệu truyền đến theo từng lượt phân đoạn nào? Đâu là dấu hiệu kết thúc luồng được chấp thuận? Và thực thể nào sẽ quan sát lỗi thất bại của tài nguyên sau cùng? Ba câu hỏi này không thay thế cho tài liệu đặc tả của định dạng hay giao thức cụ thể, nhưng chúng triệt tiêu một quan niệm sai lầm phổ biến: xem nhẹ thao tác nhập/xuất như những đường ống phụ trợ nằm ngoài giao ước kỹ thuật của chương trình.

Phần tiếp theo sẽ đặt thêm một áp lực vận hành mới lên chương trình: nhiều goroutine cùng đồng thời hoạt động trong một tiến trình. Trước khi lựa chọn kênh truyền (*channel*) hay khóa loại trừ tương hỗ (*mutex*), ta cần nhìn nhận hiện tượng chạy đua dữ liệu (*data race*) không phải như một câu khẩu hiệu mơ hồ về tính an toàn luồng (*thread safety*), mà là hai thao tác truy cập dữ liệu không tồn tại trật tự xảy ra trước (*happens-before*) an toàn.

@references
1. Go Team. Go 1.27 Release Notes, encoding/json/v2 và encoding/json/jsontext. go.dev/doc/go1.27
2. Go Team. Package encoding/json: khác biệt semantics v1/v2. pkg.go.dev/encoding/json
