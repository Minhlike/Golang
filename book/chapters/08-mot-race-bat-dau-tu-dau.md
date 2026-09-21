# Chương 8 — Một race bắt đầu từ đâu

Một chương trình kiểm tra nhiều endpoint thường có một người thu thập kết quả và một người trình bày. Bản chạy thử có thể luôn in đúng trên laptop, nên ta rất dễ gọi nó là “chạy song song được”. Nhưng kết quả đúng trong một lượt không tạo ra một lời hứa đúng cho lượt kế tiếp.

Mô hình tinh thần của chương này là **race không phải là hai goroutine cùng tồn tại; race là các lần chạm vào cùng dữ liệu mà không có thứ tự an toàn giữa chúng**. Trước khi chọn channel, mutex hay atomic, ta phải lần được những lần chạm đó và hỏi: thứ tự nào thực sự được thiết lập?

## Một lá cờ không tự công bố kết quả

Hãy tưởng tượng collector chuẩn bị một báo cáo, rồi đặt cờ `ready` để người in biết đã xong:

~~~go
type summary struct {
	completed int
	last      string
}

var latest summary
var ready bool

func collect() {
	latest = summary{completed: 1, last: "billing"}
	ready = true
}

func show() {
	for !ready {
	}
	fmt.Println(latest)
}
~~~

Nguồn trông có một thứ tự hiển nhiên: gán `latest`, rồi mới gán `ready`. Nhưng đó chỉ là thứ tự **bên trong** `collect`. `show` là một luồng thực thi khác. Nó vừa đọc `ready` khi `collect` có thể ghi `ready`, vừa đọc `latest` khi `collect` có thể ghi `latest`. Không có thao tác đồng bộ nào nối hai bên.

Vì vậy ở đây không chỉ có một vấn đề “đôi khi in cũ”. Có hai cặp truy cập tranh chấp: đọc/ghi `ready` và đọc/ghi `latest`. Việc vòng lặp có tình cờ kết thúc ở một máy không biến các cặp ấy thành có thứ tự. Đặc biệt, nhìn thấy `ready == true` không là bằng chứng ngôn ngữ rằng người đọc cũng nhìn thấy bản `latest` đã chuẩn bị xong.

## Bốn tầng không được trộn lẫn

@table Bốn loại bằng chứng khi điều tra race

| Tầng | Câu hỏi nó trả lời | Không được suy ra thêm |
| --- | --- | --- |
| Nghĩa của ngôn ngữ | Hai lần truy cập thường, cùng vị trí, có ít nhất một lần ghi và không có quan hệ happens-before là race. | Bộ chạy của máy này sẽ xen kẽ ở đúng chỗ nào. |
| Hành vi được tài liệu cam kết | Lệnh `go` khởi động goroutine mới; nhưng goroutine kết thúc không tự tạo quan hệ đồng bộ cho phần còn lại của chương trình. | Một cờ bool tự công bố mọi lần ghi xảy ra trước nó. |
| Chi tiết hiện thực | Bộ lập lịch, số P và thời điểm ngắt để chuyển việc quyết định một lần chạy thực tế xen kẽ ra sao. | Đó là hợp đồng ổn định của Go hay của code. |
| Hành vi đo được | `go test -race` báo những lần truy cập mà lượt chạy đã thực sự đi qua. | Không có báo cáo chứng minh mọi đường chạy đều không có race. |

Hai tầng đầu là lời hứa để thiết kế. Tầng thứ ba chỉ hữu ích khi giải thích một vết chạy hoặc một vấn đề hiệu năng; đừng dùng nó để biện minh rằng race “khó xảy ra”. Tầng cuối là bằng chứng thực nghiệm mạnh cho đường đã chạy, nhưng nó không thay thế lập luận về thứ tự. Một test xanh không cho phép ta đổi “chưa quan sát thấy” thành “được bảo đảm”.

## Đọc báo cáo như bản đồ truy cập

Mở `labs/part6-race-detector/broken/counter_race_test.go`. Từ thư mục `labs/part6-race-detector`, chạy ca kiểm tra có chủ ý hỏng:

~~~powershell
go test -race -tags raceexercise ./broken
~~~

Báo cáo sẽ chỉ ra hai lần truy cập xung đột và nơi goroutine được tạo. Đừng dừng ở dòng `WARNING: DATA RACE`. Với mỗi vết gọi, viết ra ba điều: variable chung nào bị chạm; thao tác là đọc hay ghi; và sự kiện đồng bộ nào, nếu có, đặt một lần truy cập trước lần kia. Ở ca kiểm tra này, câu trả lời cuối cùng là “không có”. Đó mới là nguyên nhân; counter chỉ là vật chứng.

Đây là tầng **đo được**, không phải định nghĩa của race. Công cụ cần chương trình thật sự chạy đến lần truy cập; một nhánh chưa chạy có thể vẫn sai mà báo cáo chưa thấy. Ngược lại, khi công cụ đã chỉ ra hai lần truy cập không đồng bộ, đừng chạy đi chạy lại để hy vọng báo cáo biến mất. Ta cần thay thiết kế sao cho có một quan hệ thứ tự được tài liệu cam kết.

## Chưa chọn cơ chế

Ở điểm này, cố chọn `sync.Mutex` hay channel là sớm. Hai cơ chế đều có thể tạo quan hệ đồng bộ, nhưng chúng kể hai câu chuyện quyền sở hữu khác nhau. Nếu vội biến mọi trạng thái dùng chung thành mutex, người học dễ có một đoạn xanh mà không biết lock đang bảo vệ điều bất biến nào. Nếu vội dùng channel, người học dễ biến nó thành một biến toàn cục vòng vo.

Trước khi thấy lời giải, hãy trả lời cho ví dụ `summary`: dữ liệu nào phải được công bố cùng nhau; ai được phép đọc nó; và sự kiện nào báo người đọc rằng bản đó đã sẵn sàng? Chỉ khi trả lời được ba câu này, chương sau mới chọn cơ chế đồng bộ phù hợp thay vì chọn API theo thói quen.

## Ghi chú kiểm chứng

@references
1. Go Team. The Go Memory Model, phiên bản 6 June 2022. go.dev/ref/mem
2. Go Team. Data Race Detector. go.dev/doc/articles/race_detector
