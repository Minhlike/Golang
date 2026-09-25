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

Lỗi chuẩn được quy ước cho tình huống này là `io.ErrShortWrite`. Nếu một đối tượng triển khai `io.Writer` chỉ ghi được một phần dữ liệu mà vẫn trả về `err == nil`, đối tượng đó đã vi phạm nghiêm trọng hợp đồng ngôn ngữ, khiến bên gọi ngộ nhận rằng toàn bộ thông điệp đã được gửi đi an toàn trong khi thực tế dữ liệu đã bị rơi rụng ngầm.

### Bộ đệm User-space với `bufio`

Mỗi lần một chương trình gửi yêu cầu đọc hoặc ghi trực tiếp xuống mô tả tệp của hệ điều hành, CPU phải thực hiện một quá trình chuyển đổi ngữ cảnh tốn kém từ không gian người dùng (user space) sang không gian nhân (kernel space), kèm theo chi phí lưu và khôi phục các thanh ghi phần cứng. Nếu một ứng dụng ghi một tệp log một megabyte bằng cách gọi hàm `Write` riêng rẽ cho từng byte đơn lẻ, nó sẽ phát sinh một triệu lời gọi hệ thống, làm suy sụp thông lượng của toàn bộ máy chủ.

Các kiểu dữ liệu như `bufio.Reader` và `bufio.Writer` giải quyết bài toán này bằng cách bọc một `io.Reader` hoặc `io.Writer` bất kỳ và thiết lập một vùng đệm trung gian trong bộ nhớ người dùng (mặc định là 4096 byte). Khi ghi vào `bufio.Writer`, các byte được tích lũy tuần tự vào mảng đệm nội bộ trong user space. Khi bộ đệm đầy hoặc khi lập trình viên chủ động kích hoạt lệnh `Flush()`, dữ liệu tích lũy mới được chuyển tiếp tới `io.Writer` bên dưới; nếu writer bên dưới là một mô tả tệp của hệ điều hành (`*os.File`), việc gom đệm này giúp giảm hàng nghìn lượt chuyển đổi ngữ cảnh xuống nhân, dù bản thân `Flush` không cam kết luôn tương ứng đúng một syscall duy nhất vì writer bên dưới có thể tự chia nhỏ lượt ghi.

### Lời gọi `Read` không đồng nghĩa với Syscall

Một ngộ nhận kỹ thuật phổ biến là mặc định rằng mọi lệnh `r.Read(p)` trong mã nguồn Go đều tương ứng với một chỉ thị CPU `SYSCALL` trực tiếp xuống kernel.

Trong thực tế, ranh giới giữa việc xử lý trong không gian người dùng và lời gọi hệ thống phụ thuộc hoàn toàn vào kiểu cụ thể ẩn sau giao diện:

| Kiểu cụ thể của Reader | Bản chất cơ chế khi gọi `Read(p)` | Có phát sinh Syscall xuống OS không? |
| :--- | :--- | :--- |
| `*bytes.Buffer` hoặc `*strings.Reader` | Sao chép byte trực tiếp từ mảng nhớ này sang mảng nhớ khác trong RAM qua hàm `runtime.memmove`. | Không. Toàn bộ thao tác diễn ra trong user-space với tốc độ băng thông bộ nhớ. |
| `*bufio.Reader` (khi còn dữ liệu trong đệm) | Cắt lát cắt byte từ bộ đệm nội bộ có sẵn trong RAM và chuyển cho bên gọi (user-space buffer read). | Không. Chỉ truy cập bộ nhớ người dùng thuần túy mà không chuyển ngữ cảnh. |
| `*bufio.Reader` (khi bộ đệm đã cạn) | Gọi `Read` lên đối tượng `io.Reader` bên dưới để nạp lại bộ đệm nội bộ. | Phụ thuộc underlying Reader. Nếu bọc in-memory buffer thì không có syscall; nếu bọc file hoặc socket thì do reader bên dưới quyết định. |
| `*os.File` chưa đệm | Gửi yêu cầu I/O trực tiếp tới kernel qua bảng mô tả tệp (OS file I/O path). | Có. Thực hiện syscall đọc tệp của hệ điều hành (`read` trên Linux hoặc `ReadFile` trên Windows). |
| `*net.TCPConn` | Thao tác non-blocking OS I/O kết hợp với Network Poller của runtime khi chưa sẵn sàng dữ liệu. | Có. Vẫn phát sinh syscall đọc non-blocking từ kernel; Network Poller chỉ điều phối việc đỗ và thức của goroutine. |

Đối với I/O mạng (`*net.TCPConn`), Go đưa file descriptor về chế độ non-blocking. Chu trình đọc vận hành theo mô hình phối hợp chặt chẽ giữa syscall và runtime Network Poller: ứng dụng gọi `Read` -> runtime thử thực hiện một non-blocking OS I/O syscall -> nếu dữ liệu đã có sẵn trong socket buffer thì hệ điều hành trả về dữ liệu ngay lập tức -> nếu gặp lỗi chờ (như `EAGAIN` hoặc `EWOULDBLOCK`), runtime sẽ tạm dừng (park) goroutine và đăng ký file descriptor vào Network Poller (`epoll` trên Linux, `kqueue` trên macOS, `IOCP` trên Windows) -> khi hệ điều hành thông báo socket đã sẵn sàng, runtime đánh thức goroutine chuyển về trạng thái runnable -> goroutine được scheduler xếp lịch để thử lại hoặc tiếp tục thao tác đọc dữ liệu qua syscall. Network Poller vì thế quản lý tính sẵn sàng (readiness) và việc đỗ goroutine, chứ không loại bỏ hay thay thế thao tác đọc dữ liệu của syscall.

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
