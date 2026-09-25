<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Chương 8 — Một race bắt đầu từ đâu

Một chương trình kiểm tra nhiều endpoint thường có một người thu thập kết quả và một người trình bày. Bản chạy thử có thể luôn in đúng trên laptop, nên ta rất dễ gọi nó là “chạy song song được”. Nhưng kết quả đúng trong một lượt không tạo ra một lời hứa đúng cho lượt kế tiếp.

Mô hình tinh thần của chương này là **race không phải là hai goroutine cùng tồn tại; race là các lần chạm vào cùng dữ liệu mà không có thứ tự an toàn giữa chúng**. Trước khi chọn channel, mutex hay atomic, ta phải lần được những lần truy cập đó và hỏi: thứ tự nào thực sự được thiết lập?

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

func show() summary {
	for !ready {
	}
	return latest
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

## Vẽ chứng minh thay vì đoán lịch chạy

Chương 6 đã dùng race detector để tìm một lần truy cập thực sự xung đột. Ở đây bước kế tiếp không phải chạy lại cùng báo cáo, mà là viết được lời giải thích cho phiên bản đúng trước khi chạy. Ta phân tích trật tự bộ nhớ thông qua ba quan hệ định chuẩn được xác định trong Go Memory Model:

| Quan hệ thứ tự | Bản chất ngữ nghĩa trong Go | Ví dụ áp dụng thực tế |
| :--- | :--- | :--- |
| **Sequenced-before** | Trật tự thực thi tuần tự của các câu lệnh bên trong cùng một goroutine đơn lẻ. | Thao tác `append` vào slice bắt buộc phải hoàn tất trước khi gọi `wg.Done()`. |
| **Synchronized-before** | Cạnh đồng bộ hóa liên goroutine do ngôn ngữ hoặc thư viện runtime công bố. | Lệnh `mu.Unlock()` được đồng bộ hóa trước lệnh `mu.Lock()` diễn ra kế tiếp trên cùng một Mutex; hoặc `wg.Done()` trước lệnh `wg.Wait()` mở khóa. |
| **Happens-before** | Quan hệ bao đóng bắc cầu giữa sequenced-before và synchronized-before. | Nếu thao tác ghi dữ liệu có đường dẫn happens-before tới thao tác đọc, bên đọc được ngôn ngữ bảo đảm nhìn thấy giá trị ghi mới nhất. |

Cần phân biệt rạch ròi hai cặp khái niệm thường bị nhầm lẫn trong môi trường đồng thời:

Tính đồng thời (Concurrency) và Tính song song (Parallelism): Đồng thời là đặc tính cấu trúc của chương trình, chia bài toán thành nhiều phần việc có thể xử lý độc lập về mặt logic; trong khi song song là đặc tính phần cứng khi nhiều dòng chỉ thị thực sự chạy cùng một lúc trên các lõi CPU vật lý khác nhau. Go goroutines mang lại mô hình đồng thời, nhưng việc chúng có chạy song song hay không phụ thuộc hoàn toàn vào số luồng `M`, số logical CPU `GOMAXPROCS`, và quyết định điều phối của nhân hệ điều hành.

Xung đột truy cập bộ nhớ (Data Race) và Lỗi điều kiện tranh chấp logic (Race Condition): Data race là lỗi xảy ra ở mức vi kiến trúc khi hai goroutine cùng truy xuất một ô nhớ mà không có quan hệ happens-before bảo vệ, trong đó có ít nhất một thao tác ghi; đây là hành vi sinh lỗi không xác định (undefined behavior). Ngược lại, Race Condition là lỗi logic nghiệp vụ khi thứ tự hoàn thành giữa các tác vụ độc lập dẫn tới kết quả không mong muốn (ví dụ kiểm tra số dư rồi mới rút tiền, nhưng hai giao dịch cùng vượt qua bước kiểm tra), ngay cả khi toàn bộ các biến đều được bảo vệ bằng Mutex và hoàn toàn sạch data race.

Đừng biến ba tên thành câu thần chú. Với mỗi kết quả cần đọc, hãy vẽ đường cụ thể. Trong ví dụ `ready`, không có cạnh nào từ `latest = ...` sang việc `show` đọc `latest`; vì vậy lời giải không thể chỉ là thêm một vòng lặp chờ.

## Một khóa bảo vệ một bất biến, không bảo vệ một dòng

Một `Mutex` hợp với dữ liệu thật sự được sở hữu chung, khi nhiều goroutine cần lần lượt sửa hoặc chụp lại cùng một trạng thái. Bất biến của lab mới là: **sau khi người điều phối đã chờ tất cả worker hoàn tất, snapshot chứa đúng một report của mỗi worker**. Mutex bảo vệ slice `reports` trong lúc thêm và sao chép; `WaitGroup` cho người điều phối biết khi nào có thể đánh giá bất biến.

Trước khi mở `fixed/registry.go`, chỉ đọc `exercise/registry_test.go`. Test đang đòi một `Registry`, một `Add(Report)` và một `Snapshot() []Report`. Hãy tự quyết định field nào cần có, method nào dùng pointer receiver, và vùng lock cần bao trùm đến đâu. Lệnh khởi đầu cố ý đỏ vì phần hiện thực chưa tồn tại:

~~~powershell
go test -tags exercise ./exercise
~~~

Đừng đáp bằng cách trả slice nội bộ. Bài cũ về aliasing đã cho ta lý do: người gọi giữ slice trả về có thể thay phần tử của nó. `Snapshot` ở đây hứa một ảnh chụp của container, nên lab dùng `copy` để người gọi không ghi đè phần tử bên trong registry. `Report` chỉ có string value để câu hỏi của bài vẫn là thứ tự; quyền sở hữu sâu hơn của object lồng nhau sẽ quay lại khi nó có nhu cầu thật.

Một phần hiện thực được chấp nhận không cần biết bộ lập lịch sẽ chạy worker nào trước. Nó chỉ cần khiến mỗi `Add` lock trước khi append, unlock sau đó, và `Snapshot` lock trong lúc tạo bản sao. Tài liệu `sync` cam kết `Unlock` xảy ra trước một `Lock` về sau trên cùng mutex. Đây là lời hứa API, không phải suy luận từ số core hay một lần test xanh.

## WaitGroup tạo mốc hoàn tất, không thay Mutex

Test đặt `wg.Add(workers)` trước khi tạo goroutine. Mỗi worker gọi `registry.Add(report)` rồi mới `wg.Done()` qua `defer`. Khi `wg.Wait()` trả về, mỗi `Done` đã mở khóa nó; do đó mọi `Add` trước `Done` đã nằm trước thời điểm assertion gọi `Snapshot`.

Đường chứng minh cho một worker có thể đọc thành lời:

~~~text
Add append reports
  → Unlock registry.mu
  → Done
  → Wait returns
  → Snapshot Lock
  → copy reports
~~~

Mũi tên đầu, thứ hai và mũi tên sau `Wait` là thứ tự trong code; `Done → Wait returns` là điều `sync.WaitGroup` công bố. Mutex giữ các access vào slice không chồng lên nhau. `WaitGroup` không thay thế lock: nếu các worker cùng append vào một slice mà không khóa, chúng vẫn race dù main có chờ đến khi tất cả xong mới đếm kết quả.

Sau khi tự làm, chạy bản tham chiếu độc lập:

~~~powershell
go test -race ./fixed
~~~

Kết quả xanh ở đây là hai loại bằng chứng cùng lúc: test kiểm tra bất biến cụ thể, còn race detector không thấy lần truy cập racy trên đường chạy của test. Nó vẫn không phải lời khẳng định rằng mọi API tương lai thêm vào `Registry` đều an toàn. Bất cứ method mới nào đọc hoặc ghi `reports` đều phải quay lại bất biến và phạm vi lock.

## Điều `go` cho phép, điều nó không hứa

Lệnh `go f()` thiết lập một quan hệ từ nơi khởi động đến lúc `f` bắt đầu. Điều đó đủ để goroutine mới thấy dữ liệu đã được chuẩn bị trước lệnh `go`; nó không cho chiều ngược lại. Việc `f` return hay goroutine kết thúc không tự báo cho goroutine khác rằng công việc đã xong. Đó là lý do `WaitGroup` trong lab là một phần của chứng minh, không phải nghi thức để test bớt flake.

Không dùng `time.Sleep` để thay mũi tên còn thiếu. Sleep chỉ đoán rằng worker có đủ thời gian trên một lần chạy; nó không công bố thứ tự nào và làm test vừa chậm vừa không chắc. Cũng chưa dùng channel hoặc atomic để vá ví dụ `ready`: chúng có nghĩa riêng và sẽ được dạy đầy đủ ở Chương 9, nơi câu hỏi chuyển sang truyền công việc, quyền sở hữu và áp suất của dòng dữ liệu.

Chương này kết thúc khi anh nhìn hai goroutine không còn hỏi “có chạy cùng lúc không?”, mà hỏi “lần truy cập nào cùng dữ liệu, bất biến nào cần giữ, và đường happens-before nào làm điều đó đúng?”. Câu hỏi ấy đi cùng anh qua channel, HTTP handler, cache và code runtime; cơ chế có thể đổi, nhưng trách nhiệm chứng minh thứ tự không đổi.

## Ghi chú kiểm chứng

@references
1. Go Team. The Go Memory Model, phiên bản 6 June 2022. go.dev/ref/mem
2. Go Team. Data Race Detector. go.dev/doc/articles/race_detector
3. Go Team. Package sync. pkg.go.dev/sync
