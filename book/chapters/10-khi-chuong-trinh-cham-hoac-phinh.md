<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Chương 10 — Khi chương trình chậm hoặc phình

Một chương trình bị phán xét là "chậm" hoặc "tốn bộ nhớ" thường kéo theo những nỗ lực tối ưu hóa mù quáng: thay thế gói `fmt` bằng phép cộng chuỗi thủ công, mở thêm hàng loạt goroutine không kiểm soát, hoặc viết lại thuật toán theo những mẹo vặt phức tạp. Những can thiệp này thường làm mã nguồn suy giảm độ trong sáng nghiêm trọng mà không giải quyết được nguyên nhân gốc rễ khiến người dùng hoặc hệ thống phải chờ đợi.

Mô hình tư duy nền tảng của chương này xác lập: tối ưu hóa là việc kiểm chứng một giả thuyết khoa học dưới một khối lượng công việc (workload) mang tính đại diện; một phép đo chỉ trả lời câu hỏi mà nó được thiết kế để đo lường. Benchmark không bảo đảm một dịch vụ mạng sẽ phản hồi nhanh trong mọi tình huống thực tế. Bản ghi CPU profile không phản ánh việc bộ nhớ đang phình to. Dấu vết thực thi (Execution trace) không phải là bản chụp toàn cảnh ngữ nghĩa của mã nguồn. Mỗi công cụ là một dụng cụ đo lường chuyên biệt nhằm thu hẹp không gian suy đoán.

Giả sử một tiến trình kiểm tra dịch vụ định kỳ (`opsprobe`) cần kết xuất báo cáo trạng thái cho hàng nghìn endpoint mạng. Khi chạy trên môi trường tích hợp liên tục (CI), thao tác này tiêu tốn nhiều giây và dung lượng vùng nhớ động (heap) tăng vọt. Thay vì phỏng đoán cảm tính, kỹ sư chuyển hóa vấn đề thành câu hỏi kỹ thuật có thể đo đạc: với một danh sách đầu vào xác định, hàm `Render` tiêu tốn bao nhiêu thời gian CPU và bao nhiêu lần cấp phát bộ nhớ; chu kỳ xử lý đắt đỏ tập trung ở đâu; và một thiết kế thay thế có bảo toàn từng byte đầu ra trong khi giảm thiểu chi phí tài nguyên hay không?

## Bản chất Chuỗi Tối ưu hóa: Từ Source đến Mã máy

Hiệu năng của một chương trình Go là kết quả của sự tương tác chặt chẽ giữa các pass tối ưu hóa của trình biên dịch và các hệ thống con bên trong Go runtime:

```
[Mã nguồn Go]
       │
       ▼
[Pass Inlining (Budget = 80)]
       │ Triệt tiêu chi phí gọi hàm, mở rộng ngữ cảnh
       ▼
[Pass Escape Analysis]
       │ Phân tích vòng đời: Cấp phát Stack vs Heap
       ▼
[Pass SSA & Bounds Elimination]
       │ Chứng minh biến quy nạp, loại bỏ kiểm tra biên
       ▼
[Phát sinh Mã máy Target]
       │ Thanh ghi vi kiến trúc, tập lệnh CPU
       ▼
[Go Runtime Subsystems]
         Bộ cấp phát mallocgc (TCMalloc), Tracing GC
```

Một quyết định ở tầng trình biên dịch (như hàm có được inline hay không) sẽ làm thay đổi kết quả phân tích thoát bộ nhớ (escape analysis), từ đó quyết định xem đối tượng được cấp phát tức thì trên ngăn xếp (stack) hay phải gọi vào bộ quản lý bộ nhớ động (`mallocgc`), và cuối cùng tác động trực tiếp lên tần suất chạy của bộ thu gom rác (Garbage Collector).

## Phân tích Thoát Bộ nhớ: Ngăn xếp đối đầu Vùng nhớ Động

Trình biên dịch Go sử dụng phân tích thoát bộ nhớ tĩnh (`cmd/compile/internal/escape`) để xác định xem vòng đời của một biến có vượt ra khỏi khung ngăn xếp (stack frame) của hàm khởi tạo hay không.

Nếu biến không thoát, nó được cấp phát trực tiếp trên stack. Chi phí cấp phát trên stack gần như bằng không: CPU chỉ cần giảm giá trị con trỏ ngăn xếp (`SP`), và khi hàm kết thúc, con trỏ `SP` được hoàn trả vị trí cũ, giải phóng toàn bộ vùng nhớ mà không gây bất kỳ gánh nặng nào cho bộ thu gom rác. Ngược lại, nếu con trỏ của biến được trả về cho bên ngoài, gán vào biến toàn cục, hoặc đóng gói vào interface, biến đó bắt buộc phải thoát ra heap arena (`runtime.newobject` hoặc `runtime.makeslice`), chịu sự quản lý của cơ chế TCMalloc và GC.

Thí nghiệm kiểm chứng trên Go 1.27.1 với cờ phân tích chuyên sâu `-gcflags=all=-m=2` đối với hàm kết xuất báo cáo cho thấy chi tiết dòng dữ liệu (data flow) dẫn đến quyết định thoát:

~~~text
./render.go:13:6: cannot inline Render:
    function too complex: cost 231 exceeds budget 80
./render.go:16:18: inlining call to
    strings.(*Builder).WriteString
./render.go:18:36: inlining call to strconv.FormatInt
./render.go:13:13: readings does not escape
./render.go:16:18: append(strings.b.buf, strings.s...)
    escapes to heap in Render:
  flow: {heap} <- &{storage for append(...)}:
    from append(strings.b.buf, strings.s...) (spill)
    from strings.b.buf = append(...) (assign)
~~~

Kết quả phân tích từ compiler chứng minh hai sự thật kỹ thuật rõ ràng:

Thứ nhất, tham số `readings []Reading` không hề thoát ra heap (`readings does not escape`). Mặc dù nó là một slice, dữ liệu chỉ được duyệt đọc nội bộ trong hàm nên descriptor của nó tồn tại an toàn trên ngăn xếp của bên gọi.

Thứ hai, bộ đệm byte nội bộ của `strings.Builder` (`strings.b.buf`) bắt buộc phải thoát ra heap vì mảng byte này liên tục tăng trưởng kích thước thông qua lời gọi `append`, vượt quá kích thước cố định có thể dự đoán trước trên stack frame.

## Tối ưu hóa SSA và Loại bỏ Kiểm tra Biên (Bounds Check Elimination)

Một trong những tối ưu hóa mạnh mẽ nhất của backend SSA (Static Single Assignment) trong Go là pass loại bỏ kiểm tra biên (`ssa/prove`). Trong Go, mỗi thao tác truy cập mảng hoặc slice theo chỉ số (như `s[i]`) về nguyên tắc đòi hỏi một phép kiểm tra an toàn tại thời gian chạy: nếu `i >= len(s)`, chương trình phải kích hoạt `runtime.panicIndex`. Phép kiểm tra này chèn thêm các lệnh rẽ nhánh điều kiện `CMPQ` và lệnh nhảy `JAE`, làm phân mảnh pipeline thực thi của CPU.

Bằng cách kích hoạt cờ gỡ lỗi SSA `-gcflags=all=-d=ssa/prove/debug=1`, ta có thể quan sát cách compiler suy luận toán học để triệt tiêu các lệnh kiểm tra thừa:

~~~text
./render.go:15:20: Induction variable: limits [0,?), increment 1
./render.go:15:20: Inverted loop iteration
./render.go:21:19: Disproved Less64
strings/strings.go:987:27: Proved IsInBounds
strings/strings.go:988:38: Proved IsSliceInBounds
~~~

Khi duyệt tập hợp qua `for range`, trình biên dịch nhận diện được biến quy nạp (induction variable) khởi đầu từ 0 và tăng đều đặn 1 đơn vị cho tới khi chạm biên độ dài logic. Bằng chứng toán học đó cho phép pass `ssa/prove` chứng minh tiên nghiệm rằng chỉ số không bao giờ vượt biên (`Proved IsInBounds`), từ đó loại bỏ hoàn toàn các lệnh nhảy kiểm tra lỗi thời gian chạy, cho phép CPU thực thi vòng lặp với tốc độ tối đa của phần cứng.

## Cơ chế Thu gom Rác và Đánh đổi Không gian - Thời gian

Bộ thu gom rác (Garbage Collector) của Go là một hệ thống thu gom rác dấu vết đồng thời (Concurrent Tri-color Mark-Sweep Tracer). Trái ngược với quan niệm phổ biến rằng GC hoạt động hoàn toàn miễn phí hoặc ngược lại là luôn gây tắc nghẽn, tài liệu chính thức Go GC Guide khẳng định bản chất của GC là một sự **đánh đổi giữa tài nguyên bộ nhớ (space) và thời gian xử lý CPU (time)**.

Khi chu kỳ GC kích hoạt, runtime phân bổ chính xác 25% tổng năng lực CPU của hệ thống (tương đương 1 trong mỗi 4 logical processor `P`) để phục vụ các goroutine đánh dấu đối tượng sống (GC background workers). 

Hai điểm dừng ngắn của toàn bộ thế giới (Stop-the-World - STW) vẫn xuất hiện ở pha chuẩn bị quét (Sweep Termination) và pha dọn dẹp kết thúc đánh dấu (Mark Termination), nhưng thời gian STW thường được kiểm soát dưới 1 miligiây. Tuy nhiên, nếu tốc độ cấp phát bộ nhớ của ứng dụng (allocation rate) vượt quá tốc độ đánh dấu của GC, runtime sẽ ép các goroutine của người dùng chuyển sang chế độ **GC Mark Assist**. Khi đó, chính goroutine đang xử lý logic nghiệp vụ sẽ bị tạm dừng để đi quét rác hỗ trợ runtime, dẫn đến hiện tượng trễ đuôi (tail latency P99.99) tăng đột biến.

### Chiến lược Thu gom Hiện đại: Kiến trúc Green Tea GC trong Go 1.27.1

Ở tầng trừu tượng cao, Go tiếp tục duy trì mô hình toán học ba màu đồng thời (Tri-color Mark-Sweep). Tuy nhiên, về mặt triển khai thực tế trong runtime của Go 1.27.1, chiến lược quét và đánh dấu đã chuyển dịch sang dòng kiến trúc **Green Tea GC** (được kích hoạt mặc định qua `goexperiment.GreenTeaGC`).

Trong mô hình thu gom truyền thống trước đây, runtime sử dụng các bộ đệm công việc kiểu LIFO (`workbuf`) và thực hiện quét từng đối tượng riêng lẻ (object-at-a-time). Mỗi khi một con trỏ được phát hiện, đối tượng đích chuyển sang màu xám và được đẩy vào hàng đợi; khi lấy ra, CPU phải nhảy tới vùng nhớ của đối tượng đó để quét tiếp. Trên các heap chứa hàng chục triệu đối tượng nhỏ, việc nhảy ngẫu nhiên giữa các địa chỉ nhớ phân tán làm phá vỡ tính cục bộ của bộ nhớ đệm CPU (cache thrashing), khiến các lõi xử lý liên tục bị nghẽn do chờ nạp dữ liệu từ RAM.

Green Tea GC giải quyết điểm nghẽn này bằng chiến lược gom cụm theo từng phân đoạn bộ nhớ (span locality):

Nguyên lý trì hoãn và gom cụm (Batch Scanning): Thay vì quét ngay lập tức từng đối tượng khi vừa tìm thấy, runtime trì hoãn việc quét để tích lũy nhiều đối tượng sống nằm trong cùng một `mspan` (đơn vị quản lý trang nhớ của Go heap). Khi một phân đoạn tích lũy đủ đối tượng, CPU sẽ quét toàn bộ các đối tượng trong phân đoạn đó trong một lượt duy nhất. Việc quét dồn dập trên một dải địa chỉ liên tục tận dụng tối đa đường truyền của cache line L1/L2, giảm thiểu chi phí truy xuất siêu dữ liệu và mở đường cho phần cứng CPU kích hoạt kỹ thuật nạp trước (prefetching).

Cặp bitset kép (`marks` và `scans`): Để quản lý việc gom cụm mà vẫn bảo đảm tính chính xác tuyệt đối của GC, Green Tea nhúng trực tiếp hai tập hợp bit vào từng span (`spanInlineMarkBits`). Tập hợp `marks` ghi nhận các đối tượng vừa được phát hiện con trỏ trỏ tới (pre-mark). Tập hợp `scans` ghi nhận các đối tượng đã thực sự được quét xong nội dung. Khi lấy một span từ hàng đợi FIFO ra xử lý, runtime thực hiện phép toán logic tìm hợp và giao giữa hai bitset để xác định chính xác danh sách đối tượng cần quét, thậm chí áp dụng các tập lệnh SIMD (như AVX2) để tăng tốc độ quét bit trên các size class đồng nhất.

Đánh đổi kỹ thuật: Green Tea GC không phải là giải pháp đem lại hiệu năng vượt trội cho mọi trường hợp. Nó tối ưu hóa vượt bậc cho các ứng dụng web và vi dịch vụ sở hữu mật độ đối tượng nhỏ cao và thời gian sống tập trung. Ngược lại, đối với các khối lượng công việc có đồ thị con trỏ thưa thớt hoặc các hệ thống bị ép chặt dung lượng bộ nhớ, cơ chế trì hoãn có thể tạo áp lực nhất thời lên bộ điều tốc chu kỳ (GC Pacer). Hiểu được kiến trúc phân đoạn giúp kỹ sư không xem GC như một chiếc hộp đen thần bí, mà là một hệ thống gom cụm bộ nhớ có chủ đích.

Hai biến số môi trường chi phối trực tiếp hành vi đánh đổi không gian và thời gian này:

Tham số `GOGC`: Xác định tỷ lệ phần trăm tăng trưởng của heap trước khi chu kỳ GC tiếp theo được kích hoạt (mặc định là `100`, tức kích hoạt khi heap đạt 200% lượng dữ liệu sống). Tăng `GOGC` giúp giảm tần suất GC và tiết kiệm chu kỳ CPU, nhưng đổi lại tiến trình sẽ chiếm dụng nhiều RAM hơn.

Tham số `GOMEMLIMIT`: Được đưa vào từ Go 1.19, thiết lập ngưỡng giới hạn bộ nhớ mềm cho tiến trình. Trong môi trường container hóa (như Kubernetes pod), `GOMEMLIMIT` bảo đảm khi bộ nhớ chạm ngưỡng an toàn, GC sẽ tự động điều chỉnh chu kỳ chạy dày đặc hơn để thu hồi bộ nhớ, ngăn chặn tiến trình bị nhân Linux tiêu diệt bởi cơ chế OOM-Killer.

## Đo lường Hiệu năng: Benchmark là Hợp đồng Thực nghiệm

Một bài kiểm thử hiệu năng (benchmark) chỉ có giá trị khi nó cô lập được đúng thao tác nghiệp vụ cần đo lường, loại bỏ toàn bộ các công việc chuẩn bị dữ liệu khỏi vòng lặp tính giờ.

Từ phiên bản Go 1.24, cú pháp chuẩn mực cho benchmark sử dụng phương thức `b.Loop()`. Cơ chế này tự động kích hoạt bộ đếm thời gian sau khi giai đoạn khởi tạo hoàn tất và tự ngắt bộ đếm khi hoàn thành số vòng lặp mục tiêu:

~~~go
func BenchmarkRender(b *testing.B) {
	readings := representativeReadings(1_000)

	for b.Loop() {
		Render(readings)
	}
}
~~~

Lệnh thực thi đo đạc thống kê nhiều lần:

~~~powershell
go test -bench BenchmarkRender -benchmem -count=6 ./fixed
~~~

Chỉ số `ns/op` phản ánh thời gian trung bình để hoàn thành một lượt xử lý. Chỉ số `B/op` và `allocs/op` ghi nhận chính xác khối lượng byte và số lần yêu cầu cấp phát bộ nhớ lên heap. Một kết quả đo lường đơn lẻ không đại diện cho chân lý phổ quát; việc chạy 6 lượt liên tiếp (`-count=6`) giúp kỹ sư nhận diện được độ biến thiên (nhiễu đo lường) trước khi đưa ra kết luận.

| Công cụ chẩn đoán | Câu hỏi kỹ thuật được giải đáp | Giới hạn phân tích |
| :--- | :--- | :--- |
| Kiểm thử đơn vị (Unit test) | Đầu ra và mã lỗi có bảo toàn đúng cam kết logic? | Không chứng minh được mã chạy nhanh hơn hay tốn ít RAM hơn. |
| Đo lường chuẩn (Benchmark) | Thao tác này tiêu tốn thời gian và phân bổ bộ nhớ ra sao dưới input chuẩn? | Không phản ánh trực tiếp độ trễ mạng hay tải tương tranh thực tế. |
| Phân tích CPU (CPU profile) | Khi chiếm dụng CPU, hàm nào tích lũy chu kỳ xử lý lớn nhất? | Bỏ qua hoàn toàn thời gian goroutine bị chặn do I/O hoặc khóa Mutex. |
| Phân tích Bộ nhớ (Heap profile) | Đường dẫn mã nguồn nào chịu trách nhiệm cho các khối cấp phát trên heap? | Dữ liệu mang tính lấy mẫu thống kê, không ghi nhận từng biến riêng lẻ. |
| Dấu vết thực thi (Execution trace) | Tương tác giữa goroutine, luồng hệ điều hành và scheduler diễn ra theo mốc thời gian nào? | Dung lượng tệp trace rất lớn, gây suy giảm hiệu năng nếu ghi log dài hạn. |

## Phân tích CPU và Bộ nhớ (pprof)

Khi benchmark phát hiện điểm nghẽn hiệu năng, công cụ trích xuất profile (`pprof`) giúp định vị chính xác vị trí tích lũy chi phí trong cây gọi hàm:

~~~powershell
go test -run '^$' -bench BenchmarkRender `
  -cpuprofile cpu.out -memprofile mem.out ./fixed
go tool pprof -top cpu.out
~~~

Chỉ số `flat` ghi nhận chi phí tiêu tốn trực tiếp bên trong thân hàm, trong khi chỉ số `cum` (cumulative) ghi nhận tổng chi phí tích lũy của hàm đó cùng toàn bộ các hàm con mà nó triệu gọi. Một hàm có `flat` nhỏ nhưng `cum` lớn là dấu hiệu cho thấy nó đang dẫn lối vào một chuỗi thao tác tiêu tốn nhiều tài nguyên.

![Đường đi của bằng chứng hiệu năng](../../assets/diagrams/performance-evidence-path.png)

@figure Chu trình điều tra hiệu năng hoàn chỉnh. Dữ liệu bắt đầu từ một bài toán đo lường có khối lượng công việc đại diện, kiểm chứng qua profiler, sau đó đối chiếu mã nguồn và tối ưu hóa có đo đạc đối chứng.

## Nghiên cứu Điển cứu Thực tế: Phân tích Bài toán Nối Chuỗi

Thư mục `labs/part10-measure-first` duy trì hai cách hiện thực cho cùng một yêu cầu định dạng văn bản: phương án cơ sở (`baseline`) nối chuỗi bằng toán tử `+=` lặp lại; phương án tối ưu (`fixed`) sử dụng `strings.Builder` và `strconv.FormatInt`.

Khối lượng công việc đại diện gồm đúng 1.000 đối tượng `Reading`, từ `endpoint-0000` đến `endpoint-0999`, được khởi tạo sẵn ngoài vòng lặp đo. Kết quả thực nghiệm đo đạc bằng Go 1.27.1 trên kiến trúc `windows/amd64` (bộ xử lý 12th Gen Intel Core i5-12500H) ghi nhận sự khác biệt căn bản:

| Phương án hiện thực | Thời gian xử lý trung bình | Chi phí phân bổ vùng nhớ động (Heap) |
| :--- | :--- | :--- |
| `baseline` (Toán tử `+=`) | 1.38 – 3.78 ms/op | ~10.44 MB/op trên 1.900 lần cấp phát (`allocs/op`) |
| `fixed` (`strings.Builder`) | 26.1 – 86.1 µs/op | ~87.6 KB/op trên 917 lần cấp phát (`allocs/op`) |

Bản ghi CPU profile của phương án `baseline` cho thấy hàm runtime `runtime.concatstrings` chiếm tới 25.9% thời gian xử lý lũy kế, và hàm sao chép bộ nhớ `runtime.memmove` chiếm 16.1% thời gian thực thi phẳng. Phép cộng chuỗi bất biến trong vòng lặp buộc runtime phải liên tục cấp phát các mảng byte mới và sao chép toàn bộ nội dung chuỗi cũ sang ô nhớ mới, dẫn đến sự suy giảm thông lượng hơn 40 lần.

Bằng chứng thực nghiệm này chỉ ra chính xác nguyên nhân gốc rễ, cho phép kỹ sư thay đổi sang `strings.Builder` dựa trên số liệu định lượng vững chắc.

## Tối ưu hóa Dựa trên Hồ sơ Vận hành (PGO)

Từ Go 1.20 và hoàn thiện ở các phiên bản gần đây, Go hỗ trợ kỹ thuật Tối ưu hóa Dựa trên Hồ sơ (Profile-Guided Optimization - PGO).

Trong quy trình biên dịch thông thường, compiler chỉ có cái nhìn tĩnh về mã nguồn, không biết nhánh rẽ nào trong câu lệnh `if` hay phương thức nào của `interface` được gọi thường xuyên nhất trong thực tế. Với PGO, kỹ sư thu thập một tệp CPU profile đại diện (`default.pgo`) từ hệ thống production đang chịu tải thực. Trình biên dịch nạp hồ sơ này vào pass phân tích để:

Một là, mở rộng ngân sách inlining (inlining budget) cho các hàm nằm trên đường dẫn nóng (hot paths), cho phép inline các hàm phức tạp vượt mức ngân sách 80 thông thường.

Hai là, thực hiện cơ chế hủy ảo hóa (devirtualization): khi một interface method hầu như luôn được hiện thực bởi một kiểu cụ thể duy nhất trong môi trường thực tế, compiler sẽ chuyển đổi lời gọi phương thức ảo gián tiếp qua con trỏ `itab` thành một lời gọi hàm tĩnh trực tiếp, kèm theo kiểm tra kiểu nhanh, giúp CPU dự đoán nhánh rẽ chính xác và kích hoạt tối ưu hóa inline xuyên package.

Tuy nhiên, tài liệu chính thức của Go nhấn mạnh ranh giới nghiêm ngặt: **hồ sơ pprof dùng cho PGO bắt buộc phải đại diện cho tải thực tế của toàn bộ chương trình (whole-program workload)**. Việc sử dụng hồ sơ thu được từ một microbenchmark nhân tạo để biên dịch PGO có thể làm sai lệch hoàn toàn trọng số tối ưu hóa của trình biên dịch, khiến các đường dẫn quan trọng khác trên production bị chậm đi đáng kể.

## Kỷ luật Tối ưu hóa Kỹ thuật

Nâng cao hiệu năng không phải là trò chơi đoán mò cú pháp. Trước khi đưa ra bất kỳ đề xuất thay đổi nào, người kỹ sư luôn tuân thủ quy trình bốn bước:

Một là, xác định khối lượng công việc đại diện phản ánh đúng bài toán thực tế.

Hai là, thiết lập kiểm thử đơn vị để cố định hợp đồng kết quả đầu ra không bị biến dạng.

Ba là, sử dụng benchmark, escape analysis và profiler để thu thập số liệu định lượng trước khi can thiệp mã nguồn.

Bốn là, đối chiếu lại số liệu sau khi sửa đổi; nếu mức cải thiện không đủ lớn để bù đắp cho độ phức tạp gia tăng của mã nguồn, kiên quyết giữ lại giải pháp đơn giản và dễ bảo trì nhất.

@references
1. Go Team. Package testing, phần Benchmarks và `B.Loop`. pkg.go.dev/testing
2. Go Team. Diagnostics, phần Profiling và Tracing. go.dev/doc/diagnostics
3. Go Team. Command trace. go.dev/cmd/trace
4. Go Team. Go Garbage Collector Guide. go.dev/doc/gc-guide
5. Go Team. Profile-guided optimization. go.dev/doc/pgo
