<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Chương 7 — Dữ liệu đi vào và đi ra

Một lệnh vừa in ra một dòng `billing healthy=true` có vẻ như đã giao tiếp được với thế giới bên ngoài. Nhưng terminal chỉ là một `io.Writer` rất đặc biệt. Khi dữ liệu vào chuyển thành tệp cấu hình, pipe từ lệnh khác, body HTTP hay một stream nén, trực giác “đọc file rồi có dữ liệu” bắt đầu che một sự thật quan trọng: dữ liệu không nhất thiết đến cùng lúc, và tài nguyên không tự hết hạn đúng lúc ta muốn.

Mô hình tinh thần của chương này là **một stream là lời hứa về tiến độ, không phải một slice đã nằm sẵn trong bộ nhớ**. Reader hứa sẽ đưa byte theo từng lượt; người gọi phải xử lý từng lượt, biết khi nào dữ liệu kết thúc và biết ai chịu trách nhiệm đóng tài nguyên. Từ đó JSON, file và output không còn là các API rời rạc.

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

Một cách nghĩ sai nhưng rất tự nhiên là cấp buffer đủ lớn cho mẫu test, gọi `Read` một lần, rồi phân tích số byte nhận được. Nó thường xanh với `strings.NewReader` và input ngắn. Nhưng `io.Reader` không hứa lấp đầy buffer. Reader có thể là file, socket, pipe hay decoder khác; mỗi lần gọi chỉ nhận được một phần byte hiện có.

Contract tối thiểu của `Read(p)` là: nó trả `n` byte nằm trong `p[:n]`, và có thể trả một error. `n` có thể nhỏ hơn `len(p)`. Đặc biệt, một reader được phép trả byte hữu ích cùng `io.EOF` trong một lượt; caller phải tiêu thụ `p[:n]` trước khi xử lý error. `io.EOF` nghĩa là không còn byte nào cho stream đó, không phải là “lần gọi trước không có dữ liệu”.

@table Cách đọc kết quả `Read`

| Kết quả | Caller phải làm gì | Diễn giải đúng |
| --- | --- | --- |
| `n > 0`, `err == nil` | Xử lý `p[:n]`, rồi đọc tiếp | Stream đang tiến lên nhưng chưa kết thúc. |
| `n > 0`, `err == io.EOF` | Vẫn xử lý `p[:n]`, rồi kết thúc | Lượt cuối vừa có dữ liệu vừa báo hết stream. |
| `n == 0`, `err == io.EOF` | Kết thúc | Không còn byte để tiêu thụ. |
| `n == 0`, error khác `nil` | Trả hoặc phân loại lỗi | Reader không tạo được byte kế tiếp. |

Đừng tự viết vòng `Read` chỉ để chứng minh đã hiểu contract nếu standard library đã có primitive đúng. `io.ReadAll` là lựa chọn hợp lý khi input có giới hạn kích thước đáng tin và việc giữ toàn bộ trong memory là chấp nhận được. Khi input có thể lớn hoặc vô hạn, thiết kế phải chuyển sang xử lý dần từng phần. Khác biệt này không phải micro-optimization: nó quyết định chương trình có thể bị ép allocate bao nhiêu memory bởi input không tin cậy.

## Giới hạn byte trước khi gọi parser

“Tệp cấu hình chỉ nhỏ” không phải là một giới hạn. Nếu chương trình nhận một đường dẫn hoặc reader từ bên ngoài, nó cần đặt giới hạn ngay tại ranh giới mình kiểm soát. Chỉ đặt giới hạn sau `json.Decode` là quá muộn: bộ phân tích đã có quyền đọc bất cứ lượng byte nào trước khi chính sách được áp dụng.

Trước khi mở `bounded.go`, chỉ đọc hai test `TestReadBounded...`. Chúng đòi `ReadBounded` nhận tối đa `max` byte; input lớn hơn đúng một byte phải trả error mà caller nhận diện được bằng `errors.Is`. Hãy tự viết phần thân theo ba bước: bọc reader để chỉ cho phép tối đa `max + 1` byte, đọc phần đã bọc, rồi so độ dài với `max`. Byte thứ `max + 1` không phải dữ liệu cần giữ; nó là bằng chứng phân biệt tệp vừa chạm ngưỡng với tệp thật sự vượt ngưỡng.

Lab đầy đủ còn từ chối `max < 0` và thêm ngữ cảnh cho error. Những chi tiết đó cần có trong code chạy thật, nhưng chúng không được che câu hỏi đang học: vì sao phải xin thêm đúng một byte.

`io.LimitReader` chỉ giới hạn số byte mà reader bọc ngoài sẽ trả; nó không tự nói JSON có hợp lệ hay không, và cũng không làm input nhỏ trở nên đáng tin. Vì thế giới hạn byte là một chính sách tài nguyên riêng; `Decode` vẫn chịu trách nhiệm cho cấu trúc JSON và số tài liệu. Hai test ngắn bảo vệ hai câu hỏi khác nhau, không gộp chúng thành một assertion mơ hồ kiểu “cấu hình lỗi”.

Đây cũng là điểm cần tránh một lời hứa sai về cancellation. `io.Reader` chỉ công bố `Read`; interface không mang `context.Context`. Một wrapper như `ReadBounded` có thể dừng sau khi nhận đủ byte, nhưng không tự làm một underlying reader đang block thức dậy. Với file local, điều đó thường không phải policy cần thêm ở đây. Với body HTTP, deadline và cancellation thuộc lifecycle request sẽ được dạy lại ở chương networking, nơi ta nhìn được owner của connection và cách transport phản ứng.

## Failing test trước parser

Lab `labs/part7-stream-boundaries` không gắn ngay tệp JSON vào `opsprobe`. Project xuyên suốt hiện chưa cần tệp cấu hình; nhét nó vào lúc này chỉ khiến trực giác mới bị lẫn với chính sách endpoint cũ. Ta dùng một chương trình tái hiện tối thiểu để thấy ranh giới stream trước.

Mở `targets/targets_test.go` và chỉ đọc `TestDecodeConsumesChunkedStream`. `chunkReader` cố tình chỉ nhả ba byte trong mỗi lần gọi. Trước khi xem `Decode`, hãy trả lời: nếu implementation giả định một lượt `Read` là đủ, test sẽ mất đoạn nào của document? Sau đó tạm đổi tên `Decode`, chạy test và tự dựng lại function theo contract mà test đòi.

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

`json.Decoder` nhận một `io.Reader`, nên nó tự tiếp tục đọc qua nhiều chunk; caller không cần giả vờ socket hay file là slice. Test thứ hai đặt thêm một JSON value sau document đầu. Chỉ `Decode` một lần là chưa đủ contract: program sẽ im lặng bỏ qua dữ liệu còn lại. Lần `Decode` thứ hai không phải để lấy config mới, mà để chứng minh sau document hợp lệ chỉ còn whitespace và EOF.

Điều này không biến JSON decoder thành lời giải cho mọi format. CSV có record và quoting riêng; line-oriented log có boundary theo newline; body HTTP có lifecycle mạng và limit khác. Chúng sẽ được dạy ở context phù hợp. Ở đây chỉ giữ một câu hỏi trung tâm: input kết thúc ở đâu, và code nào đã xác nhận điều đó?

## Đóng output cũng là một phần của result

Khi đọc file, `defer file.Close()` gần acquisition giúp không rò file descriptor. Khi ghi file, `Close` còn có thể là nơi buffer được flush và failure cuối cùng lộ ra. Nếu function ghi JSON chỉ trả error của `Encode`, caller có thể báo thành công trước khi biết output có được đóng hoàn chỉnh hay không.

Lab đầy đủ mở resource rồi đặt `defer Close` ngay sau acquisition. Để nhìn riêng policy chọn result, phần lõi có thể viết ngắn hơn:

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

Lab đầy đủ vẫn đóng tài nguyên trên mọi đường return. Đoạn trên chỉ làm policy lộ ra: giữ write error trước, rồi mới trả close error. Writer giả giữ contract ấy mà không cần filesystem thật.

## Ranh giới Dữ liệu: Short Write, Bộ đệm và Ngộ nhận về Syscall

Khi làm việc với các dòng nhập xuất dữ liệu, trực giác bề mặt thường dẫn tới hai ngộ nhận tai hại: đánh đồng hành vi của Reader với Writer, và cho rằng mỗi thao tác đọc ghi đều kích hoạt một lời gọi hệ thống xuống nhân hệ điều hành.

### Ràng buộc Khắt khe của `io.Writer` và Khái niệm Short Write

Nếu như `io.Reader` cho phép trả về số byte đọc được `n < len(p)` kèm theo `err == nil` trong các tình huống bình thường (chẳng hạn khi đường ống mạng chưa nhận đủ dữ liệu), thì giao diện `io.Writer` lại áp đặt một hợp đồng nghiêm ngặt hơn nhiều. Theo đặc tả của thư viện chuẩn Go, một hàm `Write(p)` bắt buộc phải trả về một lỗi khác `nil` nếu nó không thể ghi trọn vẹn toàn bộ lát cắt dữ liệu (`n < len(p)`).

`io.ErrShortWrite` là sentinel mô tả một lượt ghi ngắn không có error thích hợp. Writer có thể trả error cụ thể khác; contract không bắt mọi short write mang chính sentinel này. Nếu writer trả `n < len(p)` và error `nil`, nó vi phạm contract API của `io.Writer`, không phải một quy tắc ngôn ngữ. Caller dùng API ấy cần kiểm tra kết quả, không suy ra rằng byte đã tới đích cuối chỉ vì một lượt ghi ở tầng trung gian thành công.

### Bộ đệm User-space với `bufio`

Một syscall đưa việc thực thi qua ranh giới user/kernel. Nó có chi phí, nhưng không đồng nghĩa với context switch của scheduler sang thread khác; việc block và chuyển lịch còn phụ thuộc operation và trạng thái tài nguyên. Ghi từng byte qua file chưa đệm thường tăng số lượt I/O so với gom nhiều byte. Không thể suy ra một số syscall cố định hay mức giảm throughput chỉ từ số lần gọi interface `Write`; phải xác định concrete writer và đo đường chạy trên OS cụ thể.

`bufio.Reader` và `bufio.Writer` gom dữ liệu trong đệm user-space. Trong source Go 1.27.1, constructor mặc định dùng buffer 4096 byte; con số ấy không phải quy tắc của `io.Reader` hay cam kết mọi buffer đều cùng kích thước. Writer chuyển byte xuống underlying writer khi cần chỗ hoặc khi Flush; caller phải kiểm tra lỗi Flush. Buffer có thể giảm số lượt gọi tầng dưới, không bảo đảm một tỷ lệ syscall hay throughput cố định.

### Lời gọi `Read` không đồng nghĩa với Syscall

Một ngộ nhận kỹ thuật phổ biến là mặc định rằng mọi lệnh `r.Read(p)` trong mã nguồn Go đều tương ứng với một chỉ thị CPU `SYSCALL` trực tiếp xuống kernel.

Trong thực tế, ranh giới giữa việc xử lý trong không gian người dùng và lời gọi hệ thống phụ thuộc hoàn toàn vào kiểu cụ thể ẩn sau giao diện:

| Kiểu cụ thể của Reader | Bản chất cơ chế khi gọi `Read(p)` | Có phát sinh Syscall xuống OS không? |
| :--- | :--- | :--- |
| `*bytes.Buffer` hoặc `*strings.Reader` | Sao chép byte vào buffer của caller từ dữ liệu trong bộ nhớ. | Không cần syscall I/O cho phần sao chép; cách compiler hiện thực `copy` không phải contract của Reader. |
| `*bufio.Reader` (khi còn dữ liệu trong đệm) | `Read` sao chép byte từ đệm vào buffer của caller; khác với các API trả một slice nhìn vào đệm. | Không cần gọi underlying Reader trong lượt được phục vụ đủ từ đệm. |
| `*bufio.Reader` (khi bộ đệm đã cạn) | Gọi `Read` lên đối tượng `io.Reader` bên dưới để nạp lại bộ đệm nội bộ. | Phụ thuộc underlying Reader. Nếu bọc in-memory buffer thì không có syscall; nếu bọc file hoặc socket thì do reader bên dưới quyết định. |
| `*os.File` chưa đệm | Gửi yêu cầu I/O trực tiếp tới kernel qua bảng mô tả tệp (OS file I/O path). | Có. Thực hiện syscall đọc tệp của hệ điều hành (`read` trên Linux hoặc `ReadFile` trên Windows). |
| `*net.TCPConn` | Thao tác non-blocking OS I/O kết hợp với Network Poller của runtime khi chưa sẵn sàng dữ liệu. | Có. Vẫn phát sinh syscall đọc non-blocking từ kernel; Network Poller chỉ điều phối việc đỗ và thức của goroutine. |

Với Go 1.27.1 trên Linux, đường đọc socket trong `internal/poll/fd_unix.go` có thể thử non-blocking read, gặp `EAGAIN`, chờ poller rồi thử lại. Đây là mô hình triển khai được pin, không phải lời hứa của `net.Conn`. Không áp nguyên trace readiness Linux cho Windows: backend IOCP dùng completion và đường triển khai khác. API chung vẫn là đọc byte, error và deadline; poller giúp điều phối goroutine chứ không loại bỏ I/O xuống OS. Chương 11 sẽ đặt cơ chế đó vào một request thật.

## Một filesystem là một khả năng, không phải một đường dẫn

Parser ở trên chỉ cần byte, không cần quyền mở mọi file trên máy. Khi một application có nhiều nguồn file, `fs.FS` mô tả khả năng `Open(name)` với tên logic dùng dấu `/`. Consumer có thể nhận `embed.FS` chứa asset lúc build, `os.DirFS` nhìn vào directory lúc chạy, hoặc filesystem giả trong test. Consumer không cần đổi parser theo nguồn.

~~~go
// Đặt trong package có thư mục fixtures tại build time.
//go:embed fixtures/*.txt
var files embed.FS

data, err := fs.ReadFile(files, "fixtures/message.txt")
~~~

Imports của đoạn này là `embed` và `io/fs`; bản chạy được nằm trong `labs/edition-contracts`. Directive phải ở package scope, gắn với variable phù hợp. Byte được đưa vào binary lúc build, không tự cập nhật khi file ngoài máy đổi. `embed.FS` có API đọc, không phải nơi lưu runtime secret hoặc config cần sửa sau triển khai. Những byte được bundle có thể bị trích xuất từ binary; “không còn file rời” không phải bảo mật.

Tên hợp lệ theo `fs.ValidPath` không có `..` hoặc dấu `/` ở đầu; điều đó không tự biến mọi implementation thành sandbox. Đặc biệt `os.DirFS` và `fs.Sub` không ngăn symlink bên dưới trỏ ra ngoài directory. Nếu nhận tên file từ bên không tin cậy và cần confinement thực sự, đọc contract `os.Root` cùng giới hạn theo OS trong Go 1.27.1, thay vì ghép path rồi tin `Clean` đã chặn mọi lối thoát. Quyền mở file và quyền parse dữ liệu là hai boundary khác nhau.

**Thực hành.** Viết một function nhận `fs.FS` và tên logic, đọc một tệp rồi đưa byte cho parser đã có. Test với filesystem giả; test riêng tên không hợp lệ và file thiếu. Sau đó thay bằng `embed.FS` mà không đổi parser. Đừng để test filesystem giả được diễn giải thành bằng chứng rằng symlink hoặc quyền truy cập thật trên OS đã an toàn.

## Parser cũng có ngân sách

Một log “mỗi dòng là một record” khiến `bufio.Scanner` tiện hơn vòng đọc thủ công. Nhưng Scanner có giới hạn token: một dòng dài có thể khiến `Scan()` trả false trước EOF. Caller phải đọc `Err()`, và nếu domain cho phép dòng lớn hơn thì gọi `Buffer` trước khi scan, với mức trần phù hợp. Không nên tăng trần vô hạn để chữa một input hỏng. `TestScannerLimitAndValidation` dùng cùng input với hai giới hạn để phân biệt kết thúc bình thường với token vượt ngân sách.

Byte limit cũng không thay kiểm tra miền số. `strconv.ParseUint(text, 10, 16)` trả error nếu chuỗi không phải số nguyên unsigned biểu diễn được trong 16 bit; sau đó business rule vẫn phải quyết định port 0 có được phép không. `Atoi` chọn `int` của kiến trúc, không định nghĩa một wire format ổn định. Khi format yêu cầu bit width, nói rõ width trong parser và test biên.

Với pattern do người dùng nhập, dùng `regexp.Compile` và xử lý error. `MustCompile` phù hợp với pattern cố định trong source mà lỗi là lỗi lập trình, không phải cách báo lỗi cho người vận hành. Package `regexp` cam kết thời gian match tuyến tính theo độ dài input; điều đó không cam kết chi phí compile, lượng memory hoặc số lượt match không cần giới hạn. Parser, số record, pattern và lifetime của stream vẫn phải có ngân sách của application. Chọn `strings` hay `bytes` khi thao tác chỉ là tìm delimiter hoặc prefix rõ ràng; thêm regexp chỉ khi grammar cần nó.

## Tự kiểm tra trước khi tích hợp

Chạy từ `labs/part7-stream-boundaries`:

~~~powershell
go test ./...
go vet ./...
~~~

Thử lần lượt: bỏ lượt `Decode` thứ hai; cho `chunkReader` nhả một byte; rồi cho writer giả fail ở `Write` trước `Close`. Dự đoán test nào vỡ.

**Đáp án — chỉ đọc sau khi đã tự làm.** Bỏ lượt decode thứ hai làm `TestDecodeRejectsAdditionalDocument` thất bại; chunk nhỏ hơn không đổi contract. Khi write và close cùng fail, phải giữ write error.

Với limit, input dài đúng `max` byte được trả nguyên vẹn; input dài `max + 1` trả error giữ identity `ErrDocumentTooLarge`. Đó là lý do lab không dùng một `if len(data) == max` mơ hồ: bằng chứng cần phân biệt đúng ngưỡng với vượt ngưỡng.

Chương này không thêm file config vào `opsprobe`: chưa có yêu cầu vận hành nào bắt nó phải có. Đó là giữ teaching vehicle phục vụ bài học. Khi một yêu cầu thật cần import/export target, stream boundary và close policy ở lab này sẽ là nền để tích hợp có chủ đích.

Trước khi chạm một API I/O mới, hãy tự hỏi ba câu. Byte đến theo từng lượt nào, đâu là dấu kết thúc được chấp nhận, và ai quan sát failure của resource sau cùng? Ba câu này không thay thế tài liệu của format hay protocol cụ thể, nhưng chúng ngăn một sai lầm rất phổ biến: coi input/output là vài dòng plumbing nằm ngoài contract của chương trình.

Phần tiếp theo sẽ đặt một áp lực khác lên chương trình: nhiều goroutine cùng sống trong một process. Trước khi chọn channel hay mutex, ta cần nhìn một race không phải như một câu thần chú về thread safety, mà như hai access không có thứ tự an toàn.
