<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Chương 9 — Dòng công việc có áp suất

Mô hình tinh thần của chương này là **một send trên channel là một lần bàn giao còn dang dở cho tới khi bên nhận nhận nó, buffer giữ nó, hoặc người gửi chọn dừng**. Channel không biến công việc thành “song song an toàn” chỉ bằng một dấu `<-`. Nó buộc ta viết rõ ai còn nợ ai một giá trị, ai báo không còn giá trị nào nữa, và điều gì xảy ra khi người nhận không còn chờ.

Hãy bắt đầu bằng một tiện ích có vẻ hợp lý. `firstSuccess` chạy nhiều probe, nhận kết quả đầu tiên rồi return:

~~~go
results := make(chan Result)

for _, probe := range probes {
	go func(probe Probe) {
		result := probe(ctx)
		results <- result
	}(probe)
}

select {
case result := <-results:
	return result, nil
case <-ctx.Done():
	return Result{}, ctx.Err()
}
~~~

Nếu một probe xong trước, caller nhận một `Result` và rời hàm. Những probe xong sau vẫn cố gửi. Vì `results` là unbuffered và không còn receiver, chúng block ở `results <- result`. Đây là goroutine leak: work đã xong nhưng goroutine không thể kết thúc vì nó đang giữ một lần bàn giao không còn ai nhận. `context` không tự cứu đoạn send này; nó chỉ là một tín hiệu mà code phải chọn lắng nghe.

## Dừng đúng chỗ send

Một worker gửi kết quả phải nhìn đồng thời hai khả năng: consumer sẵn sàng nhận, hoặc request đã hết lý do để tiếp tục. `select` đặt hai quyết định ấy cạnh nhau:

~~~go
select {
case out <- result:
	// Consumer đã nhận quyền sở hữu result.
case <-ctx.Done():
	// Không có lần bàn giao nào nữa.
	// Worker được phép kết thúc.
}
~~~

Đây không phải timeout chung chung. Nếu `out` chưa có receiver và context chưa bị hủy, worker chờ có chủ đích: áp suất của consumer đã truyền ngược về worker. Nếu context bị hủy, worker bỏ kết quả chưa bàn giao để không bị kẹt. Còn `Work` đang chạy bên trong worker có dừng ngay hay không lại là contract khác: `ctx` là yêu cầu hủy, không thể cưỡng bức một function hoặc system call bất kỳ dừng tức thì.

`select` chỉ chọn một communication đang có thể tiến lên. Khi nhiều case cùng sẵn sàng, specification yêu cầu chọn một case theo cách pseudo-random đồng đều; nó không hứa ưu tiên, fairness dài hạn hay thứ tự business. `default` khiến `select` không block, vì thế rất dễ vô tình biến “consumer đang chậm” thành “bỏ qua dữ liệu”. Chỉ dùng `default` khi bỏ qua hoặc chuyển sang cơ chế khác là policy được viết rõ.

## Buffer là khoảng nợ hữu hạn

Với channel không buffer, sender và receiver phải gặp nhau tại cùng một lần communication. Với `make(chan Result, 8)`, sender có thể đi trước tối đa tám result chưa được consumer lấy. Số `8` không làm work nhanh hơn, không phải số worker, và không phải bằng chứng hệ thống chịu tải tám request. Nó là lượng backlog chương trình cho phép giữ trong bộ nhớ trước khi áp suất quay lại người gửi.

@table Buffer là backlog hữu hạn, không phải số worker

| Thiết kế | Sender được đi trước bao xa? | Câu hỏi phải trả lời |
| --- | --- | --- |
| `make(chan T)` | Không có chỗ đệm; cần receiver sẵn sàng. | Người gửi có được phép chờ consumer không? |
| `make(chan T, n)` | Tối đa `n` value chưa nhận. | `n` đại diện quota bộ nhớ hay burst nào? Khi đầy thì policy là gì? |
| `select` có `default` | Có thể không gửi dù channel chưa bị đóng. | Bỏ, log, retry hay trả lỗi có được hứa không? |

Đây là semantics ngôn ngữ, không phải mô hình scheduler: buffered channel chỉ thay đổi lúc send/receive có thể tiếp tục. Memory model còn cam kết send xảy ra trước khi receive tương ứng hoàn tất. Cam kết ấy giúp truyền một value và các việc đã được chuẩn bị trước send; nó không cấp quyền cho nhiều goroutine cùng sửa một state tùy ý.

## Close nói về người gửi, không nói “mọi thứ ổn”

`close(results)` có nghĩa là sẽ không còn send nào lên `results`. Nó không có nghĩa consumer đã xử lý hết result, không giết worker, và không làm send đang treo tự biến mất. Các value đã buffer vẫn được nhận trước; sau đó receive trả zero value với `ok == false`. Vì vậy `for result := range results` là contract dễ đọc: consumer tiếp tục lấy mọi result đã bàn giao, rồi dừng khi owner đóng kênh.

Chỉ owner của phía gửi mới nên close channel. Trong một worker pool, không worker nào tự biết mình là worker cuối; cho worker nào xong trước `close(results)` sẽ khiến worker khác send tiếp panic. Ta cần một coordinator biết tất cả worker đã return rồi mới đóng output đúng một lần.

![Lifecycle ownership của worker pool: dispatcher đóng jobs, coordinator đóng results sau tất cả worker, consumer chỉ nhận.](../../assets/diagrams/channel-work-lifecycle.png)

@figure Sơ đồ này là mental model về ownership, không phải timeline scheduler. Mỗi channel có một owner của tín hiệu kết thúc, và mọi đường worker phải có lối thoát khi consumer không còn nhận.

## Đọc một worker pool như một hợp đồng đóng kênh

Lab `labs/part9-workflow-pressure` không nối thẳng vào `opsprobe`. Ta chưa có requirement production nào buộc CLI ấy phải chạy nhiều endpoint cùng lúc. Dùng reproducer độc lập giữ một câu hỏi đủ sắc: một producer, nhiều worker và một consumer kết thúc với bao nhiêu result, ở thời điểm nào?

Mở `exercise/pool_test.go` trước. Test không cho sẵn hiện thực; nó chỉ đòi các type `Job`, `Result`, `Work` và function `Run`. Bốn cam kết kỹ thuật cấu thành hợp đồng thực thi của `Run` bao gồm:

| Điều khoản hợp đồng | Mục tiêu kiểm chứng | Rủi ro hệ thống nếu vi phạm |
| :--- | :--- | :--- |
| Bảo toàn kết quả đơn trị | Mỗi job hoàn tất bình thường sinh ra đúng một `Result`. | Mất mát dữ liệu hoặc lặp kết quả xử lý. |
| Giới hạn tài nguyên song song | Số lượng lời gọi hàm `Work` thực thi đồng thời không bao giờ vượt quá ngưỡng `workers`. | Tràn bộ đệm, quá tải kết nối cơ sở dữ liệu hoặc cạn kiệt CPU. |
| Cơ chế giải phóng khi hủy bỏ | Khi context bị hủy mà output không được đọc, kênh output vẫn đóng và worker không bị treo ở lệnh gửi. | Rò rỉ goroutine vĩnh viễn (goroutine leak) làm cạn RAM máy chủ. |
| Chu kỳ đóng kênh duy nhất | Khi dispatcher hết job và toàn bộ worker đã thoát, kênh output đóng đúng một lần. | Panic do đóng kênh nhiều lần hoặc deadlock vòng lặp `for range`. |

Có một biên nhỏ nhưng đáng giữ ngay từ đầu: nếu `ctx` đã bị hủy trước khi dispatcher kịp bàn giao job, `Work` không được bắt đầu chỉ vì một worker vừa được tạo. Cancellation là policy dừng nhận việc mới; đưa một `Job` vào `Work` với context đã hết hạn chỉ tạo thêm một kết quả không còn người sở hữu.

Chạy lệnh khởi đầu; nó phải đỏ vì API chưa tồn tại:

~~~powershell
go test -tags exercise ./exercise
~~~

Đừng thêm buffer lớn để làm test im. Test cancellation cố ý không consume output; một implementation chỉ có `out <- result` sẽ lộ goroutine bị kẹt. Cũng đừng đóng `results` từ worker. Hãy phác trên giấy ba owner trước khi code: dispatcher sở hữu send và `close(jobs)`; các worker chỉ receive job rồi send result; coordinator sở hữu `close(results)` sau `WaitGroup.Wait`.

Một khung đủ nhỏ cho điểm send quan trọng là:

~~~go
result := Result{Job: job, Err: work(ctx, job)}

if ctx.Err() != nil {
	return
}

select {
case out <- result:
case <-ctx.Done():
	return
}
~~~

`ctx.Err()` trước `select` là policy có chủ đích của lab: nếu cancellation đã được quan sát sau `Work`, result đó không còn được bàn giao, kể cả khi consumer vừa quay lại. Bên trong `select`, cancellation vẫn là đường thoát cho trường hợp consumer biến mất trong lúc worker đang chờ. Phần còn lại là thiết kế của anh: dispatcher đưa `jobs` vào channel thế nào để cũng nghe `ctx.Done`; worker nhận đến khi `jobs` đóng ra sao; goroutine nào chờ `WaitGroup`; và trường hợp `workers <= 0` trả output đóng ngay hay bị từ chối ở API boundary. Test hiện tại chốt policy thứ nhất để câu hỏi vẫn tập trung vào lifecycle.

Đừng chỉ kiểm tra cancellation ở dispatcher. Một job có thể đã được bàn giao đúng lúc cancellation xảy ra; worker cần kiểm tra lại trước khi gọi `Work`. Điều này không cưỡng bức một `Work` đang chạy phải dừng — chính `Work` còn phải tôn trọng context của nó — nhưng nó giữ được lời hứa hẹp hơn và kiểm chứng được: sau khi cancellation đã được quan sát, pool không khởi động một job mới.

Sau khi tự làm, chạy bản tham chiếu với race detector:

~~~powershell
go test -race ./fixed
~~~

## Hướng của channel cho thấy quyền hạn

Trong function nội bộ, `chan Job` có cả quyền send và receive. Nhưng biên API có thể thu hẹp quyền đó:

~~~go
func dispatch(ctx context.Context, jobs []Job) <-chan Job
func consume(in <-chan Job, out chan<- Result)
~~~

`<-chan Job` nói caller chỉ được receive; `chan<- Result` nói caller chỉ được send. Direction không thay thế ownership document - hai function vẫn phải thỏa thuận ai close - nhưng compiler đã ngăn một số nhầm lẫn lộ liễu. Bên nhận `in` không thể vô tình send; consumer của output không thể `close` một receive-only channel.

Khi đọc code channel, đừng bắt đầu bằng câu “channel này buffered hay không?”. Hỏi theo thứ tự khó hơn nhưng hữu ích hơn: value nào đang được bàn giao, bên nào phải còn sống để receive nó, ai có quyền nói không còn send nữa, và cancellation có mở đường thoát cho mọi lần block không. Trả lời được bốn câu ấy trước khi chọn capacity thường ngăn được cả leak, deadlock và queue vô hạn.

## Mô hình Điều phối G/M/P và Giới hạn Thực tế của Concurrency

Để vận hành worker pool ở quy mô lớn, kỹ sư phải hiểu rõ mô hình điều phối của Go Runtime thay vì xem goroutine là những chiếc luồng ma thuật miễn phí. 

Trong runtime Go hiện hành (được định nghĩa tại `src/runtime/proc.go` và `src/runtime/chan.go`), hệ thống điều phối theo mô hình đa ghép nối M:N với ba thực thể: `G` đại diện cho một goroutine (chứa trạng thái thực thi và ngăn xếp co giãn khởi điểm khoảng 2KB); `M` đại diện cho một luồng hệ điều hành thực tế (OS thread do nhân quản lý); và `P` đại diện cho một ngữ cảnh bộ vi xử lý logic (Processor context, với số lượng tối đa bằng `GOMAXPROCS`, sở hữu hàng đợi chạy cục bộ `runq`). Mô hình này thuần túy là chi tiết triển khai thời gian chạy của Go toolchain, không phải là một cam kết trong đặc tả ngôn ngữ Go Specification.

Goroutine có chi phí khởi tạo rẻ hơn nhiều so với luồng hệ điều hành (vốn tốn từ 1MB đến 8MB bộ nhớ stack cố định), nhưng chúng tuyệt đối **không miễn phí**. Việc tạo ra hàng triệu goroutine vô tội vạ mà không có cơ chế giới hạn áp suất (unbounded goroutines) sẽ nhanh chóng gây cạn kiệt RAM thực tế khi các stack buộc phải mở rộng, đồng thời làm tăng vọt gánh nặng quét con trỏ cho bộ thu gom rác (GC stop-the-world scanning).

Bên cạnh đó, Channel trong Go thực chất là một cấu trúc dữ liệu `hchan` nằm trên heap, được bảo vệ nội bộ bởi một khóa `hchan.lock`. Mỗi thao tác gửi và nhận trên channel đều đòi hỏi chi phí khóa và điều phối hàng đợi `waitq`. Đối với những đường ống dữ liệu yêu cầu thông lượng hàng chục triệu thao tác mỗi giây với độ trễ microgiây, việc lạm dụng Channel thường chậm hơn đáng kể so với việc sử dụng `sync.Mutex` cục bộ hoặc các thao tác nguyên tử `sync/atomic`. Channel tỏa sáng ở việc chuyển giao quyền sở hữu luồng công việc và phối hợp sự kiện vòng đời, không phải là giải pháp vạn năng cho mọi bài toán đồng bộ hóa hiệu năng cao.

## Ghi chú kiểm chứng

@references
1. Go Team. The Go Programming Language Specification, mục Channel types, Send statements, Receive operator, Close và Select statements. go.dev/ref/spec
2. Go Team. The Go Memory Model, mục Channel communication; và Package context. go.dev/ref/mem, pkg.go.dev/context
