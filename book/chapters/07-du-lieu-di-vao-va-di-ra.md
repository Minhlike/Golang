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

## Failing test trước parser

Lab `labs/part7-stream-boundaries` không gắn ngay file JSON vào `opsprobe`. Project xuyên suốt hiện chưa có requirement file config; nhét nó vào lúc này chỉ khiến một mental model mới bị lẫn với policy endpoint cũ. Ta dùng minimal reproducer để thấy ranh giới stream trước.

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

Vì vậy lab đặt việc mở resource sau một function value và trả close error nếu write đã thành công:

~~~go
func Save(
	open func() (io.WriteCloser, error),
	targets []Target,
) (err error) {
	w, err := open()
	if err != nil {
		return fmt.Errorf("open target output: %w", err)
	}
	defer func() {
		if closeErr := w.Close(); err == nil &&
			closeErr != nil {
			err = fmt.Errorf(
				"close target output: %w",
				closeErr,
			)
		}
	}()
	return Encode(w, targets)
}
~~~

Named result ở đây không phải mẹo cú pháp để dùng khắp nơi. Nó cho defer một nơi rõ ràng để giữ error chính nếu `Encode` đã fail, hoặc đưa close error ra nếu ghi trước đó thành công. `TestSaveReturnsCloseError` dùng một writer giả có `Close` fail để giữ policy này. Đó là test boundary nhỏ: nó không cần filesystem thật để chứng minh caller không nuốt result cuối của resource.

`Encode` dùng `json.Encoder`; newline chỉ là presentation tiện cho tool dòng lệnh, không phải một phần của data model. Nếu output thành machine contract của `opsprobe`, command boundary phải quyết định và test riêng như Chương 6 đã làm.

## Tự kiểm tra trước khi tích hợp

Chạy từ `labs/part7-stream-boundaries`:

~~~powershell
go test ./...
go vet ./...
~~~

Thử lần lượt: bỏ lượt `Decode` thứ hai; cho `chunkReader` nhả một byte; rồi cho fake writer fail ở `Write` trước `Close`. Trước mỗi lượt, dự đoán test nào vỡ. `Save` không được che write error.

**Đáp án — chỉ đọc sau khi đã tự làm.** Bỏ lượt decode thứ hai làm `TestDecodeRejectsAdditionalDocument` thất bại vì parser chấp nhận hai document. Chunk nhỏ hơn không đổi contract của reader. Khi write và close đều fail, write error giữ nguyên vì defer chỉ thay result khi chưa có error trước đó.

Chương này không thêm file config vào `opsprobe`: chưa có yêu cầu vận hành nào bắt nó phải có. Đó là giữ teaching vehicle phục vụ bài học. Khi một yêu cầu thật cần import/export target, stream boundary và close policy ở lab này sẽ là nền để tích hợp có chủ đích.

Trước khi chạm một API I/O mới, hãy tự hỏi ba câu. Byte đến theo từng lượt nào, đâu là dấu kết thúc được chấp nhận, và ai quan sát failure của resource sau cùng? Ba câu này không thay thế tài liệu của format hay protocol cụ thể, nhưng chúng ngăn một sai lầm rất phổ biến: coi input/output là vài dòng plumbing nằm ngoài contract của chương trình.

Phần tiếp theo sẽ đặt một áp lực khác lên chương trình: nhiều goroutine cùng sống trong một process. Trước khi chọn channel hay mutex, ta cần nhìn một race không phải như một câu thần chú về thread safety, mà như hai access không có thứ tự an toàn.
