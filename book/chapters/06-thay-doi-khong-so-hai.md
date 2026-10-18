<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Chương 6 — Thay đổi không sợ hãi

Ở cuối Chương 5, công cụ `opsprobe` đã biết lấy một điểm cuối (*endpoint*) từ cấu hình và gọi `probe.Check`. Nhưng một yêu cầu rất bình thường vẫn khó chứng minh: khi người vận hành đặt `OPS_PROBE_TARGET=payments.internal:9443`, điểm cuối nào thực sự đi tới hàm thực thi (*runner*)? Chạy lệnh dòng lệnh và nhìn dòng `billing healthy=true` không trả lời được câu hỏi đó. Dòng đó không in tên máy chủ hay cổng; kể cả có in, một lần chạy thử thủ công vẫn không phải giao ước (*contract*) mà mã nguồn bảo toàn được khi tiếp tục thay đổi.

Đây là lúc nhiều dự án đi sai hướng. Có người viết kiểm thử gọi trực tiếp hàm `main`, sửa biến môi trường của tiến trình chung, chụp luồng xuất chuẩn, rồi hy vọng không chạm vào lệnh `os.Exit`. Có người khác bỏ qua kiểm thử vì nghĩ rằng “mã dòng lệnh chỉ có vài dòng”. Cả hai đều né tránh câu hỏi thiết kế: phần nào là logic điều phối (*orchestration*) có thể kiểm chứng, phần nào là ranh giới tiến trình (*process boundary*) chỉ nên giữ thật mỏng và rõ ràng?

## Một kiểm thử khói không biết điều ta cần biết

Hàm `main` hiện đang gánh quá nhiều trách nhiệm: đọc môi trường thực tế, nạp cấu hình, gọi hàm thăm dò, quyết định mã thoát và in ra thiết bị đầu cuối. Một ca kiểm thử gọi nó chỉ quan sát được một nhánh luồng chạy thử. Với thiết kế hiện tại, kiểm thử rất khó truyền môi trường giả lập vào một cách an toàn, không thể quan sát điểm cuối mà hàm thực thi nhận được, hoặc không thể bóc tách lỗi cấu hình khỏi lỗi thăm dò mà không kích hoạt các tác dụng phụ của tiến trình.

Vấn đề không phải bản thân `main` được viết tệ. Các lệnh `os.LookupEnv`, xuất ra luồng chuẩn và `os.Exit` đều có vị trí phù hợp: chúng là ranh giới nơi chương trình tiếp xúc với tiến trình hệ điều hành. Vấn đề là toàn bộ logic cần xử lý trước khi chạm tới ranh giới ấy chưa được tổ chức thành một đơn vị độc lập để kiểm thử có thể kích hoạt.

Chúng ta tạo gói nội bộ `internal/app`. Gói này không thay thế `probe` hay `config`, mà đảm nhiệm việc điều phối hai gói đó. Hàm `Run` tiếp nhận đúng hai quan hệ phụ thuộc (*dependency*) có thể hoán đổi trong kiểm thử: hàm đọc môi trường và hàm thực thi thăm dò. Nó trả về kết quả cấu trúc (*outcome*) thay vì in trực tiếp ra màn hình:

~~~go
type Outcome struct {
	Service string
	Err     error
}

func Run(
	ctx context.Context,
	lookup config.LookupEnv,
	runner probe.Runner,
) ([]Outcome, error)
~~~

Trường `Outcome.Err` đại diện cho sự cố của một mục tiêu đã được cấu hình; công cụ dòng lệnh có thể in lỗi đó ra rồi tiếp tục thăm dò mục tiêu kế tiếp. Ngược lại, giá trị `error` trả về độc lập đại diện cho thất bại nghiêm trọng không thể tạo ra danh sách kết quả có ý nghĩa, chẳng hạn như cấu hình bất hợp lệ hoặc toàn bộ lượt chạy bị hủy bỏ. Việc phân tách hai nhánh xử lý này không nhằm mục đích tạo kiểu cho đẹp mắt: bên gọi có các chính sách xử lý hoàn toàn khác nhau. Chương 4 từng đặt câu hỏi “bên gọi cần quyết định điều gì?”; ở đây câu trả lời sẽ định hình trực tiếp kiểu dữ liệu trả về.

## Tái cấu trúc đến khi kiểm thử có điểm tựa vững chắc

Hàm `Run` nạp mục tiêu, ánh xạ cấu hình `config.Target` sang `probe.Service`, gọi `probe.Check`, rồi lưu giữ từng kết quả trong một giá trị `Outcome`. Nó không trực tiếp đọc `os.LookupEnv`, không gọi `fmt.Printf` và tuyệt đối không gọi `os.Exit`. Các tác dụng phụ đó thuộc về tệp `cmd/opsprobe/main.go`:

~~~go
outcomes, err := app.Run(
	context.Background(),
	os.LookupEnv,
	runner,
)
if err != nil {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(2)
}

for _, outcome := range outcomes {
	if outcome.Err != nil {
		fmt.Printf("%s: %v\n", outcome.Service, outcome.Err)
		continue
	}
	fmt.Printf("%s healthy=true\n", outcome.Service)
}
~~~

Đoạn mã `main` vẫn duy trì logic tối thiểu: chính sách trình bày và mã thoát tiến trình hiển lộ rõ ràng, rất dễ duyệt xét. Nhưng kiểm thử không cần phải gọi tới nó. Kiểm thử nằm ngay cạnh `Run`, truyền một hàm đóng kín (*closure*) thay thế cho `LookupEnv` và một hàm `probe.Runner` ghi nhận điểm cuối được gọi. Không hề có socket mạng, biến môi trường toàn cục hay thiết bị đầu cuối nào bị can thiệp.

Trước khi viết lời khẳng định kiểm thử (*assertion*), hãy phân định rạch ròi ba phạm vi bằng mắt. Điều này ngăn việc biến ca kiểm thử thành bản sao chép thụ động của mã triển khai:

@table Phạm vi của unit test quanh `Run`

| Test kiểm soát | Test quan sát | Test không cần chạm |
| --- | --- | --- |
| `LookupEnv` trả target nào; runner thành công hay lỗi | endpoint runner nhận; `Outcome` hoặc error trả về | environment process, stdout, stderr, `os.Exit` |

Nếu một yêu cầu nghiệp vụ chỉ xuất hiện ở cột cuối cùng, hàm `Run` chưa phải đơn vị phù hợp để kiểm thử; đó là nhiệm vụ của kiểm thử tích hợp (*integration test*) vào thời điểm cần thiết. Nếu nó nằm ở hai cột đầu, kiểm thử đơn vị (*unit test*) có thể cung cấp phản hồi cực nhanh mà không cần giả lập toàn bộ tiến trình hệ điều hành.

~~~go
func TestRunMapsEnvironmentTargetToRunner(t *testing.T) {
	var got probe.Endpoint

	outcomes, err := Run(context.Background(), lookup(
		"OPS_PROBE_TARGET", "payments.internal:9443",
	), func(_ context.Context, endpoint probe.Endpoint) error {
		got = endpoint
		return nil
	})

	if err != nil {
		t.Fatalf("Run() error = %v", err)
	}
	if got != (probe.Endpoint{
		Host: "payments.internal",
		Port: 9443,
	}) {
		t.Fatalf("runner endpoint = %+v", got)
	}
	if len(outcomes) != 1 {
		t.Fatalf("outcomes = %+v", outcomes)
	}
	if outcomes[0].Err != nil ||
		outcomes[0].Service != "billing" {
		t.Fatalf("outcome = %+v", outcomes[0])
	}
}
~~~

Đây là một ca kiểm thử đơn vị chuẩn mực không phải vì nó ngắn gọn, mà vì nó kiểm chứng một đơn vị có ranh giới khoanh vùng hẹp. Ca kiểm thử đặt ra một câu hỏi hoàn toàn có thể quan sát được: dữ liệu cấu hình đầu vào có truyền tới hàm thực thi chính xác hay không, và kết quả có gắn đúng với dịch vụ tương ứng hay không. Nó không săm soi chi tiết triển khai nội bộ như việc hàm `Run` khai báo bao nhiêu biến cục bộ hay viết vòng lặp bằng cú pháp nào.

## Hai loại lỗi, hai chính sách ứng xử

Hãy bổ sung thêm hai ca kiểm thử trước khi đọc toàn bộ phần triển khai. Với cấu hình `OPS_PROBE_TARGET=payments.internal:0`, gói cấu hình phải báo lỗi ngay trước khi hàm thực thi được kích hoạt. Đây là dữ liệu đầu vào bất hợp lệ của toàn bộ lượt chạy, do đó `Run` trả về lỗi và không tạo ra bất kỳ kết quả dở dang nào. Trong khi đó, với hàm thực thi trả về `errors.New("connection refused")`, mục tiêu đã tồn tại và thao tác đã bắt đầu; hàm `Run` sẽ lưu giữ `Outcome{Service: "billing", Err: ...}` để công cụ có thể báo một dòng lỗi rồi tiếp tục thăm dò các mục tiêu kế tiếp khi danh sách sau này mở rộng.

Tín hiệu hủy bỏ (*cancellation*) lại khác biệt hoàn toàn với cả hai trường hợp trên. Phương thức `probe.Check` bảo toàn danh tính lỗi `context.Canceled`, trong khi hàm `Run` dừng vòng lặp thay vì biến việc hủy bỏ toàn bộ lượt chạy thành kết quả thất bại cục bộ của từng dịch vụ. Nhìn từ bên ngoài, ba chính sách phân định rõ ràng:

@table Policy cho lỗi cấu hình, lỗi probe và cancellation

| Tình huống | `Run` trả gì | Command nên làm gì? |
| --- | --- | --- |
| Config không hợp lệ | `error` | In stderr, exit 2, không gọi runner. |
| Một probe thất bại | `Outcome.Err` | Báo service đó; policy hiện tại cho phép đi tiếp. |
| Context bị cancel | `error` giữ identity | Dừng run; không ghi health signal giả. |

Không phải ca kiểm thử nào cũng cần dùng đối tượng giả lập. Bộ phân tích cấu hình đã sở hữu các bài kiểm thử đầu vào/đầu ra chuyên biệt ở Chương 5; phương thức `probe.Check` cũng đã có kiểm thử cho cơ chế hủy bỏ và bọc lỗi. Hàm `Run` chỉ cần kiểm thử phần liên kết ba giao ước đó lại với nhau. Nếu một ca kiểm thử chỉ lặp lại y hệt các khẳng định của gói tầng dưới, nó sẽ gây cản trở cho quá trình tái cấu trúc mà không hề gia tăng độ tin cậy của hệ thống.

### Bài thực hành: Tách bỏ và tái thiết lập

Mở `labs/part6-testable-command`, đọc `internal/app/run_test.go` trước. Đừng chạy lệnh vội; hãy dự đoán mỗi kiểm thử đang bảo vệ chính sách nào. Sau đó tạm đổi tên `Run` để trình biên dịch báo các điểm mà kiểm thử đang đòi hỏi khế ước, rồi tự dựng lại hàm từ kiểm thử và các kiểu dữ liệu đã có. Khi kiểm thử đơn vị thành công, chạy `go run ./cmd/opsprobe`. Cuối cùng đổi runner trong `main` thành một runner trả lỗi và xác minh CLI in tên dịch vụ thay vì nuốt chửng lỗi thất bại. Khôi phục runner thành công trước khi rời bài lab.

---

#### Gợi ý giải pháp (chỉ đọc sau khi đã tự làm)

Hàm `Run` cần gọi `config.LoadTargets` đúng một lần trước vòng lặp, ánh xạ từng `Target` sang `probe.Service`, rồi nối kết quả thành công hoặc thất bại của từng kiểm tra. Chỉ lỗi cấu hình và tín hiệu hủy bỏ mới thoát khỏi `Run` qua lỗi trả về. Hàm `main` giữ môi trường thực tế, dữ liệu xuất ra và mã thoát. Lời giải không phải là “dùng khung giả lập mock”; hai giá trị hàm hiện có đã là điểm ghép nối vừa đủ.

## Khi một test case che mất các policy khác

Ca kiểm thử đầu tiên của `Run` cố ý chỉ dùng một trường hợp ghi đè hợp lệ. Nó trả lời câu hỏi khi tái cấu trúc (*refactor*): điểm cuối (*endpoint*) có thực sự truyền tới runner hay không? Nhưng nếu cứ nhân bản kiểu kiểm thử đó cho từng dữ liệu đầu vào xấu, bộ kiểm thử sẽ dần biến thành một chuỗi dài các hàm gần như giống hệt nhau. Lúc ấy người đọc không còn nhìn thấy các quy tắc của cấu hình; họ chỉ thấy rất nhiều lần gọi lặp lại `LoadTargets`.

Với `OPS_PROBE_TARGET`, chính sách của lab là: biến vắng mặt hoặc có chuỗi rỗng dùng cấu hình mặc định; chuỗi không rỗng phải tách được `host:port`, có host và port trong khoảng 1–65535. Một giá trị `found == true, raw == ""` không bị từ chối trong code hiện tại. Bảng kiểm thử phải có hàng riêng cho trường hợp đó, thay vì gọi mọi biến “có mặt” là một override hợp lệ. Những hàng khác nhau bảo vệ quyết định khác nhau, không chỉ làm tăng coverage.

Đây là lúc kỹ thuật kiểm thử hướng bảng (*table-driven test*) phát huy giá trị. Không phải vì cộng đồng Go áp đặt một nghi thức cố định, mà vì bảng cấu trúc làm hiển lộ rõ ràng phần dữ liệu thay đổi và phần logic giữ nguyên. Các giá trị `raw`, `found` và `want` thay đổi theo từng ca kiểm thử; trong khi cách thức gọi bộ phân tích cú pháp (*parser*) và lời khẳng định kiểm thử (*assertion*) về một mục tiêu duy nhất được dùng chung:

~~~go
for _, tt := range tests {
	t.Run(tt.name, func(t *testing.T) {
		targets, err := LoadTargets(
			func(string) (string, bool) {
				return tt.raw, tt.found
			},
		)
		if err != nil {
			t.Fatalf("LoadTargets() error = %v", err)
		}
		if len(targets) != 1 || targets[0] != tt.want {
			t.Fatalf("LoadTargets() = %+v", targets)
		}
	})
}
~~~

Hàm `t.Run` không chỉ giúp kết quả in ra trông có tổ chức. Khi một ca kiểm thử thất bại, lệnh `go test -v` sẽ chỉ rõ chính xác ca nào bị lỗi, thay vì buộc người kiểm tra phải đếm số thứ tự từng hàng trong lát cắt (*slice*). Do đó, trường tên ca kiểm thử cần mô tả hành vi rõ ràng: đặt tên “port zero” tốt hơn “case 4”, còn “uses the documented default” giúp nhắc nhở người bảo trì rằng giá trị mặc định là một phần trong giao ước (*contract*).

### Đánh giá một bảng kiểm thử trước khi đặt niềm tin

Thêm các dữ liệu đầu vào bị từ chối vào một bảng kiểm thử thứ hai trong tệp `internal/config/config_test.go`:

~~~go
tests := []struct {
	name string
	raw  string
}{
	{name: "missing port", raw: "payments.internal"},
	{name: "empty host", raw: ":8443"},
	{name: "non-numeric port", raw: "payments.internal:https"},
	{name: "port zero", raw: "payments.internal:0"},
	{
		name: "port above TCP range",
		raw:  "payments.internal:65536",
	},
}
~~~

Điểm dễ bỏ sót không nằm ở vòng lặp `for`, mà ở lời khẳng định kiểm thử (*assertion*). Ca kiểm thử này chỉ bảo đảm rằng từng dữ liệu không hợp lệ đều bị từ chối; nó không bảo đảm nguyên văn thông điệp lỗi (*error message*). Thông điệp lỗi là chi tiết kỹ thuật có thể hiệu chỉnh để hỗ trợ tốt hơn cho người vận hành. Quy tắc “dữ liệu đầu vào này không được phép tạo ra mục tiêu” mới chính là giao ước cốt lõi. Nếu giao diện dòng lệnh (*CLI*) hoặc giao diện lập trình (*API*) cần phân loại lỗi tự động bằng chương trình, khi đó mới phát sinh lý do thiết kế kiểu lỗi chuyên biệt (*custom error type*) hoặc lỗi lính gác (*sentinel error*); không nên dùng phép so sánh chuỗi thô sơ để thay thế cho thiết kế kiến trúc chuẩn mực.

Với phiên bản Go 1.27.1 này, biến vòng lặp khai báo bằng `:=` sở hữu một biến riêng biệt ở mỗi lần lặp (ngữ nghĩa bắt đầu từ Go 1.22), nên hàm bao đóng (*closure*) không còn vô tình giữ chung một biến `tt` như tập quán Go cũ. Tuy nhiên, một cạm bẫy con trỏ khác vẫn tồn tại: biểu thức `&tt` trỏ tới bản sao của lần lặp đó, chứ không phải phần tử thật trong lát cắt `tests`. Nếu mục tiêu là biến đổi trực tiếp phần tử gốc, hãy lặp lấy chỉ số rồi dùng `&tests[i]`. Ở đây hàm `t.Run` chạy tuần tự đồng bộ và hàm bao đóng chỉ đọc giá trị `tt`, nên con trỏ và vòng đời của goroutine đều không phải vấn đề mà chính sách bộ phân tích cần bận tâm.

Quy tắc biến vòng lặp còn phụ thuộc phiên bản ngôn ngữ có hiệu lực của module hoặc tệp, không chỉ phiên bản toolchain được cài. Lab khai báo `go 1.27`, nên dùng ngữ nghĩa mới. Ngay cả với biến riêng mỗi vòng, `t.Parallel()` không nhân bản map, pointer hay phụ thuộc toàn cục mà các case cùng sử dụng. Chỉ bật nó khi từng case có dữ liệu và tài nguyên độc lập; `t.Setenv` không được dùng trong test parallel hoặc có tổ tiên parallel vì môi trường thuộc cả tiến trình.

Có một điểm dễ làm test xanh giả: `t.Run` chỉ chờ tới khi subtest gọi `t.Parallel`, không đợi phần còn lại của subtest lúc ấy. Subtest parallel tiếp tục sau khi hàm cha trở về. Nếu cần kiểm tra tổng hợp sau tất cả case, hãy đặt chúng trong một nhóm `t.Run("group", ...)` rồi kiểm tra sau khi nhóm trả về; dùng `t.Cleanup` của nhóm để dọn tài nguyên, không dùng defer của cha làm tài nguyên biến mất trước lúc con chạy. Test `TestParallelSubtestsWaitForTheirGroup` ghi nhận thứ tự bằng primitive đồng bộ, không bằng sleep hay phỏng đoán scheduler.

### Bài thực hành: Ôn tập phân loại dữ liệu đầu vào

Trước khi chạy kiểm thử, hãy tự phân loại năm hàng trên: hàng nào bị `net.SplitHostPort` từ chối, hàng nào đi qua bộ phân tích nhưng bị bước xác thực (*validation*) của sách từ chối? Sau đó thêm một ca hợp lệ cho IPv6 theo dạng `[2001:db8::10]:443`. Khẳng định kiểm thử của nó phải xác minh `Host` không còn dấu ngoặc vuông và `Port == 443`, thay vì chỉ kiểm tra sơ sài `err == nil`.

---

#### Gợi ý giải pháp (chỉ đọc sau khi đã tự làm)

Trường hợp thiếu cổng và `:8443` không tạo được mục tiêu hợp lệ ở bước phân tích cú pháp hoặc kiểm tra tên máy chủ. Các giá trị `https`, `0` và `65536` đi xa hơn: chúng đòi hỏi chuyển đổi kiểu hoặc xác thực phạm vi số. Với địa chỉ IPv6, hàm `net.SplitHostPort` tách chuỗi có ngoặc thành máy chủ `2001:db8::10` và cổng `443`; do đó ca kiểm thử nên ghi nhận điều đó thành giao ước rõ ràng. Khi bảng kiểm thử bắt đầu chứa các cột không cùng chung một quy tắc, hoặc mỗi hàng đòi hỏi thiết lập quá khác biệt, việc tách thành các hàm kiểm thử riêng biệt sẽ sáng sủa hơn là cố nhồi nhét thêm cột.

## Chạy đúng bằng chứng

Khi bộ kiểm thử báo xanh, lệnh `go test ./...` trả lời câu hỏi có giá trị bao quát: có gói nào vi phạm giao ước (*contract*) hay không? Tuy nhiên, khi điều tra một báo cáo sự cố cụ thể, việc chạy lặp đi lặp lại toàn bộ kiểm thử sẽ làm phân tán sự tập trung. Nếu người vận hành phản ánh rằng cổng `0` từng lọt qua bước xác thực (*validation*), ta cần khoanh vùng kiểm tra đúng quy tắc đó trước, rồi mới mở rộng phạm vi.

Từ thư mục `labs/part6-testable-command`, lệnh sau chọn một ca kiểm thử con bằng đường dẫn định danh của nó:

~~~powershell
$case = 'TestLoadTargetsRejectsMalformedOverrides/port_zero'
go test -run $case -v ./internal/config
~~~

Đây không phải đường tắt để né tránh việc kiểm thử đầy đủ trước khi lưu mã (*commit*). Nó là chiếc kính lúp trong quá trình gỡ lỗi: kết quả in ra giữ nguyên tên ca kiểm thử cha và ca con `port_zero`, giúp người đọc nhận biết chính xác chính sách nào đang được đánh giá. Sau khi sửa lỗi, hãy chạy lại kiểm thử của gói rồi mới chạy toàn bộ hệ thống; lỗi từ bộ phân tích cú pháp có thể khiến ứng dụng dừng hoạt động trước cả khi hàm thực thi được gọi.

Hãy thử thay đổi tạm thời điều kiện phạm vi trong `LoadTargets` để cổng `0` đi qua, chỉ nhằm quan sát ca kiểm thử con bị phá vỡ như thế nào. Đừng lưu thay đổi mang tính thử nghiệm đó. Bài học không phải là học thuộc cờ lệnh `-run`; nó là việc phân biệt giữa vòng lặp điều tra ngắn gọn với bộ bằng chứng toàn diện cần có trước khi sáp nhập một thay đổi vào mã nguồn.

Từ đây Chương 6 đã phân định hai loại kiểm thử: hàm `Run` kiểm chứng việc liên kết các ranh giới (*boundary*), trong khi các ca kiểm thử con của cấu hình duy trì một ma trận đầu vào nhỏ gọn nhưng mang giá trị nghiệp vụ thiết thực. Phần tiếp theo sẽ tạo ra một thất bại mà kiểm thử đơn vị tuần tự báo xanh vẫn hoàn toàn bỏ lọt: hai luồng nhẹ (*goroutine*) cùng chạm vào một vùng dữ liệu mà không có cơ chế đồng bộ.

## Một test xanh vẫn có thể bỏ sót race

`opsprobe` hiện chưa chạy các tác vụ thăm dò song song; đó là lựa chọn có chủ đích khi chúng ta còn đang tập trung vào ranh giới và chính sách xử lý lỗi. Vì vậy sẽ không thực tế nếu giả định rằng vừa phát hiện một cuộc đua dữ liệu (*data race*) trong mã nguồn của nó. Thay vào đó, hãy cô lập đúng thất bại cần học: nhiều tiến trình xử lý (*worker*) cùng ghi vào một bộ đếm hoàn thành. Đây là loại lỗi có thể trông vô hại khi chạy thử một lần, vì trình biên dịch không báo lỗi và kiểm thử đơn vị tuần tự vẫn vượt qua bình thường.

Cuộc đua dữ liệu (*data race*) xảy ra khi nhiều goroutine truy cập cùng một biến đồng thời, có ít nhất một thao tác ghi, và hoàn toàn thiếu cơ chế đồng bộ hóa phù hợp. Đây là định nghĩa chặt chẽ về hành vi, không phải phán đoán cảm tính dựa trên việc kết quả đếm cuối cùng “có vẻ đúng”. Thao tác `successes++` không phải là một phép toán nguyên tử (*atomic operation*) ở cấp mã nguồn; nó đọc giá trị cũ, tạo giá trị mới rồi ghi đè lại. Hai goroutine hoàn toàn có thể xen ngang vào giữa các bước đó.

Bài thực hành `labs/part6-race-detector/broken` chứa một bộ đếm cố ý viết sai. Ca kiểm thử tạo 128 goroutine, mỗi goroutine gọi đúng một lần `RecordSuccess`:

~~~go
type Counter struct {
	successes int
}

func (c *Counter) RecordSuccess() {
	c.successes++
}
~~~

Chạy kiểm thử thông thường có thể không phát hiện dấu hiệu đáng ngờ nào. Để đưa hành vi truy cập bộ nhớ vào phạm vi quan sát, hãy chạy mã mẫu kiểm thử (*fixture*) cùng bộ phát hiện tương tranh (*race detector*):

~~~powershell
go test -race -tags raceexercise ./broken
~~~

Lệnh này được dự kiến là thất bại và in ra cảnh báo `WARNING: DATA RACE`. Đó là thất bại có chủ ý của bài thực hành, không phải một bước kiểm tra được phép báo xanh. Bộ phát hiện tương tranh ghi lại vết ngăn xếp (*stack trace*) tại các điểm truy cập xung đột và vị trí các goroutine liên quan được khởi tạo. Khi đọc báo cáo chẩn đoán, hãy lần theo ba câu hỏi: biến nào được dùng chung, thao tác nào là ghi dữ liệu, và cơ chế đồng bộ hóa nào đáng lẽ phải xác lập thứ tự giữa chúng?

@table Ba phần hữu ích nhất của một race report

| Phần report | Nó trả lời gì | Đừng kết luận quá mức |
| --- | --- | --- |
| `Read by goroutine` hoặc `Write by goroutine` | Access hiện tại nằm ở dòng nào? | Dòng đó chưa chắc là nguồn gốc policy sai. |
| `Previous ... by goroutine` | Access xung đột nào chồng lên nó? | Thứ tự in ra không phải timeline đầy đủ của chương trình. |
| `created at` | Goroutine nào mở đường cho access này? | Một report không chứng minh mọi đường chạy đều racy. |

Bộ phát hiện tương tranh (*race detector*) là công cụ thu thập bằng chứng khi mã đã chạy thực tế, không phải chứng minh toán học tuyệt đối rằng chương trình hoàn toàn không có tương tranh. Một nhánh luồng chưa được kiểm thử sẽ không kích hoạt truy cập bộ nhớ để công cụ quan sát. Do đó, cờ lệnh `go test -race` phải song hành cùng các ca kiểm thử chặt chẽ và khối lượng công việc có ý nghĩa; nó không thể thay thế cho tư duy thiết kế đồng thời đúng đắn.

### Sửa chữa bất biến, không chỉ làm bộ phát hiện im lặng

Trước khi thêm `sync.Mutex`, hãy phát biểu đặc tính bất biến (*invariant*) bằng một câu duy nhất: `Successes` phải trả về đúng số lần `RecordSuccess` đã hoàn tất, kể cả khi nhiều worker đang chạy đồng thời. Cấu trúc `Counter` vì thế mang thêm một trường `mu sync.Mutex` cạnh `successes`. Khóa bảo vệ (*lock*) không phải một nghi thức huyền bí; nó là ranh giới phân định bảo vệ hai thao tác truy cập vào trạng thái dùng chung:

~~~go
func (c *Counter) RecordSuccess() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.successes++
}

func (c *Counter) Successes() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.successes
}
~~~

Phiên bản này nằm trong thư mục `labs/part6-race-detector/fixed`. Ca kiểm thử của nó chờ mọi worker kết thúc bằng `sync.WaitGroup`, sau đó kiểm tra số lượng đếm đạt đúng `128`; lệnh `go test -race ./fixed` phải báo xanh. `WaitGroup` ở đây chỉ có nhiệm vụ giúp ca kiểm thử nhận biết khi nào các worker hoàn tất. Bản thân nó không thể tự bảo vệ biến `successes`; khóa loại trừ tương hỗ (*mutex*) mới đảm nhận trọng trách đó. Phân biệt rõ hai trách nhiệm này ngay từ đầu sẽ giúp tránh được câu hỏi bối rối sau này: “Đã gọi `Wait` rồi, sao vẫn xảy ra xung đột dữ liệu?”

Khóa loại trừ tương hỗ (`sync.Mutex`) và thứ tự bộ nhớ (*memory ordering*) sẽ được đào sâu ở phần xử lý đồng thời (*concurrency*). Ở Chương 6, trọng tâm là: một ca kiểm thử sở hữu khẳng định kiểm thử (*assertion*) đúng đắn vẫn có thể chưa quan sát được cách thức trạng thái bị xung đột truy cập. Nếu yêu cầu bài toán đưa luồng nhẹ vào mã nguồn, việc bổ sung cờ `-race` vào bộ bằng chứng chấp nhận thay đổi là một quyết định thiết kế vì khả năng kiểm thử (*testability*), không phải hình thức trang trí.

### Bài thực hành: Điều tra cuộc đua truy cập bộ nhớ (*race condition*)

Chạy mã mẫu `broken` một lần với cờ `-race`, rồi mở tệp `fixed/counter_test.go`. Trước khi chạy phiên bản đã sửa, hãy khoanh vùng hai phương thức cùng truy cập vào `successes` và giải thích vì sao ngay cả phương thức đọc dữ liệu cũng phải khóa bảo vệ. Sau đó thử bỏ thao tác khóa riêng trong `Successes`; ca kiểm thử hiện tại vẫn có thể báo xanh vì nó đọc kết quả sau lời gọi `wg.Wait`, nhưng phương thức công khai đã đánh mất giao ước an toàn dành cho bên gọi đồng thời.

---

#### Gợi ý giải pháp (chỉ đọc sau khi đã tự làm)

Phương thức `RecordSuccess` thực hiện ghi còn `Successes` thực hiện đọc trên cùng một trường dữ liệu, do đó cả hai bắt buộc phải đi qua cùng một khóa mutex nếu giao diện cam kết an toàn khi sử dụng đồng thời. Lời gọi `wg.Wait` chỉ tạo điểm chờ đồng bộ trong nội bộ ca kiểm thử hiện tại; nó hoàn toàn không thay thế được cơ chế đồng bộ hóa trong giao diện lập trình. Mã mẫu bị hỏng được gắn thẻ phân loại riêng để kho mã nguồn vẫn duy trì bộ kiểm thử mặc định báo xanh, trong khi lệnh kiểm tra cuộc đua dữ liệu được thực thi như một thử nghiệm có kiểm soát mà thất bại chính là kết quả mong đợi.

## Kiểm thử mờ (Fuzzing) khi đặc tính bất biến đã rõ ràng

Các ca kiểm thử con của cấu hình đã định danh rõ những giá trị biên mà chúng ta chủ động lựa chọn: cổng `0`, tên máy chủ rỗng, cổng vượt quá giới hạn. Tuy nhiên, bộ phân tích cú pháp tiếp nhận một chuỗi `string`; không ai có thể lường trước mọi tổ hợp dấu ngoặc, ký tự Unicode, dấu hai chấm hay các byte dị thường mà dữ liệu đầu vào từ môi trường có thể mang theo. Kỹ thuật kiểm thử mờ (*fuzzing*) hỗ trợ sinh thêm dữ liệu đầu vào tự động, nhưng chỉ thực sự có giá trị khi mục tiêu kiểm thử biết rõ cần đòi hỏi điều kiện gì ở mọi dữ liệu sinh ra đó.

Đặc tính bất biến (*property*) của `LoadTargets` không phải là “mọi chuỗi ký tự đều được phân tích cú pháp thành công”. Phần lớn chuỗi bất hợp lệ bắt buộc phải bị từ chối. Đặc tính đúng đắn là: nếu `LoadTargets` trả về thành công, nó phải trả về đúng một mục tiêu có máy chủ không rỗng và cổng nằm trong khoảng 1–65535. Điều này kết hợp rất chặt chẽ với kiểm thử hướng bảng: bảng kiểm thử xác lập các trường hợp then chốt nào phải bị từ chối hoặc ánh xạ chính xác; trong khi kỹ thuật kiểm thử mờ tìm kiếm xem còn dữ liệu đầu vào nào khiến mã nguồn tự mâu thuẫn với bất biến đó hay không.

Đừng thay thế đặc tính ấy bằng khẳng định mơ hồ như “hàm không phát sinh hoảng loạn (`panic`)”. Không hoảng loạn là tiêu chuẩn vệ sinh mã nguồn cơ bản cần có, nhưng một bộ phân tích cú pháp hoàn toàn có thể bình thản trả về `Target{Host: "", Port: 0}` mà không `panic`, để rồi phá vỡ hoạt động của lệnh ở tầng sâu hơn. Một đặc tính kiểm thử mạnh mẽ buộc ca kiểm thử phải soi xét kỹ kết quả khi thành công. Ngược lại, đừng ép bộ kiểm thử mờ phải đoán đúng từng câu chữ của thông điệp lỗi hay bắt mọi dữ liệu đầu vào xấu phải rơi vào đúng một nhánh mã cụ thể; những đòi hỏi ấy chỉ khiến ca kiểm thử trở nên mong manh mà không nâng cao sự thấu hiểu về giao ước.

Trong thực tế có nhiều họ đặc tính kiểm thử: kết quả luôn bảo toàn bất biến nghiệp vụ, quy trình mã hóa rồi giải mã (*encode/decode*) bảo toàn dữ liệu tương đương (*round-trip*), hoặc hai cách biểu diễn khác nhau phải luôn đồng thuận kết quả. Ở đây chúng ta áp dụng họ đặc tính đầu tiên vì bộ phân tích cú pháp này chưa có định dạng xuất dữ liệu để thực hiện đối chiếu hai chiều. Việc chọn lựa đặc tính bám sát giao diện lập trình hiện có giúp kiểm thử mờ phục vụ đắc lực cho thiết kế, thay vì biến tướng thành việc chạy thử dữ liệu ngẫu nhiên vô nghĩa.

~~~go
func FuzzLoadTargetsNeverReturnsInvalidTarget(f *testing.F) {
	for _, seed := range []string{
		"",
		"billing.internal:8443",
		"[2001:db8::10]:443",
		"payments.internal:0",
		"not a target",
	} {
		f.Add(seed)
	}

	f.Fuzz(func(t *testing.T, raw string) {
		targets, err := LoadTargets(lookup(raw))
		if err != nil {
			return
		}
		if len(targets) != 1 {
			t.Fatalf("got %d targets", len(targets))
		}
		target := targets[0]
		if target.Host == "" ||
			target.Port < 1 ||
			target.Port > 65535 {
			t.Fatalf("invalid target %+v", target)
		}
	})
}
~~~

`f.Add` không nhằm cung cấp danh sách kiểm thử đầy đủ. Nó là tập hạt giống đầu vào (*seed corpus*) có chủ đích: một giá trị mặc định, một tên máy thông thường, một địa chỉ IPv6, một giá trị vượt ngưỡng phạm vi và một chuỗi sai hoàn toàn định dạng mục tiêu. Khi chạy `go test`, tập hạt giống này được thực thi như các ca kiểm thử thông thường. Khi kích hoạt cờ `-fuzz`, bộ công cụ sẽ biến đổi (*mutate*) tập dữ liệu đầu vào nhằm tìm kiếm những nhánh phủ mã mới. Nếu phát hiện trường hợp thất bại, Go sẽ tự động ghi lại dữ liệu đầu vào tái lập được để lần chạy sau kiểm chứng ngay mà không phụ thuộc vào yếu tố may rủi.

Từ `labs/part6-testable-command`, chạy một lượt có giới hạn thời gian:

~~~powershell
go test -run=^$ `
  -fuzz=FuzzLoadTargetsNeverReturnsInvalidTarget `
  -fuzztime=2s ./internal/config
~~~

Tùy chọn `-run=^$` giúp bỏ qua các ca kiểm thử thông thường trong lượt chạy fuzz này; chúng vẫn được kiểm tra trong bộ kiểm thử định kỳ. Thời lượng `-fuzztime=2s` là hạn mức thời gian cho thử nghiệm cục bộ, không phải chứng chỉ cam kết bộ phân tích an toàn tuyệt đối. Mục tiêu fuzz (*fuzz target*) báo xanh chỉ xác nhận các dữ liệu đã thử nghiệm chưa phá vỡ đặc tính bất biến; nó không thay thế việc duyệt mã (*code review*), các ca kiểm thử biên có ý nghĩa hay việc xác thực giới hạn tài nguyên.

### Bài thực hành: Thiết kế đặc tính bất biến cho kiểm thử fuzzer

Một đề xuất nghe có vẻ hợp lý là “nếu `err == nil`, trường `target.Name` luôn là `billing`”. Hãy quyết định có nên đưa điều kiện đó vào mục tiêu fuzz này hay không. Nếu sau này cấu hình hỗ trợ nhiều dịch vụ khác nhau, khẳng định kiểm thử đó sẽ cản trở việc tái cấu trúc dù bộ phân tích cú pháp vẫn hoạt động hoàn toàn chính xác. Hãy giữ cho đặc tính kiểm thử bám sát nhất với giao ước cốt lõi hiện tại: cấu trúc hợp lệ của mục tiêu, không phải một chi tiết ngẫu nhiên của ca kiểm thử mẫu.

---

#### Gợi ý giải pháp (chỉ đọc sau khi đã tự làm)

Điều kiện `Name == "billing"` là giao ước tạm thời của mẫu kiểm thử nhỏ, chứ không phải đặc tính bất biến mà bộ phân tích cần duy trì khi mô hình dữ liệu đầu vào mở rộng. Đặc tính kiểm thử mờ nên đủ chặt chẽ để bắt lỗi mục tiêu không hợp lệ và đủ tinh gọn để không đóng băng một chi tiết thiết kế chưa từng được cam kết. Khi kiểm thử mờ phát hiện thất bại thực sự, trước hết hãy chuyển dữ liệu đầu vào đó thành một ca kiểm thử hồi quy (*regression test*) dễ đọc; tập dữ liệu sinh ra là bằng chứng, còn ca kiểm thử với tên gọi tường minh là lời giải thích cho những kỹ sư tiếp quản sau này.

Một giới hạn khác nằm ngay trong property đang dùng: parser bỏ qua mọi override và luôn trả default vẫn thỏa host/port hợp lệ. Vì vậy, property này cần đi cùng bảng kiểm thử ánh xạ chính xác, không thay thế nó. Đối chứng âm trong evidence giữ nguyên fuzz target nhưng cố ý bỏ override: seed test vẫn xanh, còn case `maps a host and port from the override` đỏ. Đó là bằng chứng cụ thể về khoảng trống của test, không phải lý do thêm một assertion tùy tiện để khóa mọi thiết kế tương lai. Fake runner cũng chỉ chứng minh đối số và chính sách điều phối; nó không chứng minh DNS, kết nối hay dịch vụ thật đã hoạt động.

## Đo câu hỏi trước khi tối ưu câu trả lời

Sau khi thấy bộ phân tích cú pháp có nhiều bước xác thực, một phản xạ quen thuộc là đề xuất thêm bộ nhớ đệm (*cache*) lưu kết quả: “lệnh `net.SplitHostPort` có thể chậm”. Nhưng hàm `LoadTargets` hiện chỉ thực thi một lần duy nhất khi lệnh khởi tạo. Kể cả khi một bài kiểm chuẩn hiệu năng cho thấy việc ghi đè gây tốn bộ nhớ cấp phát, điều đó vẫn chưa biến nó thành điểm nghẽn cổ chai (*bottleneck*) của một công cụ dòng lệnh chỉ chạy vài thao tác thăm dò. Một bài kiểm chuẩn hiệu năng tốt bắt đầu bằng câu hỏi đủ cụ thể để kết quả có thể trực tiếp làm thay đổi một quyết định thiết kế.

Câu hỏi cần kiểm chứng ở đây là: một lượt nạp giá trị mặc định, một lượt ghi đè tên máy chủ và một lượt ghi đè địa chỉ IPv6 có chi phí tài nguyên tương đối ra sao trên máy đang chạy? Khởi tạo kiểm thử nằm trước vòng lặp `b.Loop()`, nên bộ đếm thời gian của phép đo kiểm chuẩn không tính phần chuẩn bị đó; phương thức `b.ReportAllocs` yêu cầu kết quả xuất ra thêm thông tin cấp phát bộ nhớ:

~~~go
func BenchmarkLoadTargets(b *testing.B) {
	tests := []struct {
		name string
		raw  string
	}{
		{name: "default"},
		{
			name: "hostname override",
			raw:  "payments.internal:9443",
		},
		{name: "IPv6 override", raw: "[2001:db8::10]:443"},
	}

	for _, tt := range tests {
		b.Run(tt.name, func(b *testing.B) {
			lookup := func(string) (string, bool) {
				return tt.raw, tt.raw != ""
			}
			b.ReportAllocs()
			for b.Loop() {
				_, _ = LoadTargets(lookup)
			}
		})
	}
}
~~~

Chạy từ thư mục bài thực hành với `go test -run=^$ -bench=BenchmarkLoadTargets -benchmem ./internal/config`. Tùy chọn `-run=^$` giúp tránh trộn các ca kiểm thử thông thường vào lượt đo hiệu năng; cờ `-benchmem` cung cấp các chỉ số `allocs/op` (số lần cấp phát bộ nhớ trên mỗi thao tác) và `B/op` (số byte tiêu tốn trên mỗi thao tác). Đừng sao chép số đo `ns/op` của máy tính cá nhân vào tệp README như một chân lý phổ quát. Tốc độ vi xử lý, phiên bản Go, chế độ tiết kiệm năng lượng và các tiến trình nền của hệ điều hành đều làm kết quả dao động. Nếu một đề xuất tối ưu hiệu năng sắp được sáp nhập, hãy đo lường trước và sau thay đổi trên cùng một môi trường cố định, lặp lại nhiều lần và ghi nhận chính xác khối lượng công việc mà quyết định kỹ thuật đang phục vụ.

Trong trường hợp này, kết luận hoàn toàn có thể là “không cần tối ưu”. Đó là một kết quả kỹ thuật chuẩn mực: việc nạp cấu hình một lần duy nhất chưa xứng đáng để đánh đổi bằng việc làm xáo trộn giao diện lập trình, bổ sung tầng nhớ đệm phức tạp hay khiến mã nguồn trở nên khó đọc. Bài kiểm chuẩn hiệu năng đã hoàn thành xuất sắc nhiệm vụ khi giúp chúng ta từ chối một tối ưu hóa sớm khi chưa có áp lực thực tế, chứ không chỉ hữu ích khi nó tạo ra một bản vá chạy nhanh hơn.

### Bài thực hành: Đánh giá kết quả đo lường hiệu năng

Chạy benchmark hai lần độc lập. Chỉ đề xuất tối ưu khi xuất hiện áp lực khối lượng công việc thực tế (như nạp lại cấu hình trong vòng lặp cao điểm hoặc có hồ sơ đo lường thực tế); việc “một con số trông lớn hơn” là chưa đủ căn cứ.

## Giao ước ở ranh giới tiến trình

Kiểm thử đơn vị của `app.Run` cố ý không phụ thuộc vào thiết bị đầu cuối (*terminal*) hay mã thoát của tiến trình (*exit code*). Điều đó giúp hàm duy trì ranh giới tinh gọn, nhưng cũng tạo ra một khoảng trống cần kiểm chứng ở đúng vị trí: lệnh vẫn phải ghi nhận kết quả thành công ra luồng xuất chuẩn `stdout`, đưa lỗi cấu hình ra luồng lỗi chuẩn `stderr` và trả mã thoát `2`. Đây là giao ước công khai của tiến trình; việc tự ý thay đổi nó có thể làm gãy đổ hàng loạt tập lệnh tự động hóa của người vận hành dù mã nguồn bên trong vẫn vượt qua kiểm thử.

Lời gọi trực tiếp `main` trong kiểm thử thường khiến khoảng trống ấy rất khó kiểm chứng, vì hàm `os.Exit` sẽ chấm dứt tiến trình chạy kiểm thử. Thay vì cố gắng giả lập toàn bộ tiến trình hệ điều hành, chúng ta bóc tách phần hiển thị kết quả thành một hàm nhỏ tiếp nhận các giao diện ghi dữ liệu (*writer*) và trả về mã thoát. Hàm `main` chỉ đảm nhận nhiệm vụ gắn kết các tài nguyên thực tế của hệ thống vào hàm đó:

~~~go
func main() {
	runner := func(context.Context, probe.Endpoint) error {
		return nil
	}
	os.Exit(run(
		context.Background(),
		os.Stdout,
		os.Stderr,
		os.LookupEnv,
		runner,
	))
}
~~~

Hàm `run` vẫn ủy thác cho `app.Run`; nó chỉ bổ sung chính sách xử lý tiến trình ở mức tối thiểu. Nhờ vậy, ca kiểm thử có thể truyền đối tượng `bytes.Buffer` làm đại diện cho `stdout` và `stderr`, rồi quan sát đúng ba yếu tố mà vỏ hệ điều hành nhìn thấy: mã thoát, dữ liệu thành công và dữ liệu báo lỗi.

~~~go
func TestRunWritesSuccessContract(t *testing.T) {
	var out, errOut bytes.Buffer
	code := run(
		context.Background(),
		&out,
		&errOut,
		func(string) (string, bool) { return "", false },
		func(
			context.Context,
			probe.Endpoint,
		) error { return nil },
	)

	if code != 0 {
		t.Fatalf("code = %d", code)
	}
	if out.String() != "billing healthy=true\n" {
		t.Fatalf("stdout = %q", out.String())
	}
	if errOut.Len() != 0 {
		t.Fatalf("stderr = %q", errOut.String())
	}
}
~~~

Ca kiểm thử này không kiểm chứng xem vòng lặp trả về kết quả ra sao hay `app.Run` phân tích cú pháp cấu hình như thế nào. Các giao ước đó đã thuộc về trách nhiệm của các gói nội bộ riêng biệt. Nó chỉ bảo vệ lời hứa của lệnh: kết quả thành công có thể đọc tự động bằng chương trình trên `stdout` và không làm rò rỉ thông điệp lỗi.

Kiểm thử phía thất bại cũng cần được khoanh vùng chặt chẽ tương tự. Truyền vào một cổng không hợp lệ, để hàm thực thi phát hiện lỗi nếu bị gọi ngoài ý muốn, sau đó khẳng định mã thoát là `2`, luồng `stdout` rỗng và thông tin chẩn đoán xuất hiện ở `stderr`. Đừng so khớp toàn bộ thông điệp: câu chữ mô tả lỗi có thể được biên tập lại, trong khi nơi xuất hiện và chính sách mã thoát mới là giao ước vận hành bất biến.

### Bài thực hành: Đánh giá mã nguồn tại ranh giới tiến trình

Chuyển một lệnh `fmt.Fprintf` từ `out` sang `errOut` rồi quyết định đó là việc tinh chỉnh hiển thị vô hại hay là thay đổi phá vỡ tương thích (*breaking change*) cho đường ống lệnh vỏ hệ thống (*shell pipeline*). Sau đó đặt tình huống có thêm cờ `--json`: kiểm thử khế ước cần có ca kiểm thử riêng cho chế độ được cam kết rõ ràng này, không được nới lỏng khế ước chế độ văn bản đến mức chấp nhận bất kỳ dữ liệu đầu ra nào.

---

#### Gợi ý giải pháp (chỉ đọc sau khi đã tự làm)

Trong đường ống vỏ lệnh, stdout thường mang dữ liệu mà lệnh tiếp theo sẽ tiếp nhận xử lý; việc chuyển kết quả lành mạnh sang stderr có thể là thay đổi phá vỡ tương thích. Kiểm thử không nhằm đóng băng từng dấu câu mãi mãi. Nó bảo vệ ranh giới mà con người và hệ thống tự động hóa dựa vào: thành công thoát với mã `0` và có kết quả trên stdout; lỗi cấu hình thoát với mã `2`, không in dữ liệu thành công, đồng thời đưa thông tin chẩn đoán ra stderr.

Kiểm thử giao ước này không thay thế cho kiểm thử đầu cuối (*end-to-end test*) khởi chạy tệp nhị phân thực tế. Sau này khi lệnh tiếp nhận thêm cờ lệnh, tệp cấu hình, tín hiệu hệ điều hành hoặc kết nối mạng thực sự, một số luồng bắt buộc phải được kiểm chứng qua tiến trình thực. Nhưng việc lạm dụng kiểm thử nhị phân để so khớp từng khoảng trắng hay mọi nhánh xác thực sẽ rất chậm chạp, cồng kềnh và trùng lặp với kiểm thử đơn vị. Ranh giới kiến trúc lành mạnh là: logic chứa các phụ thuộc có thể thay thế được kiểm thử ở gói nội bộ; các cam kết mà tiến trình công bố ra ngoài được giữ ở hàm `run`; và chỉ các luồng tích hợp then chốt mới cần chuyển giao cho kiểm thử tích hợp.

Đây là điểm mấu chốt của mốc thiết kế này: khả năng kiểm thử không đồng nghĩa với việc phủ một lớp giả lập (*mock*) nặng nề lên mọi gói mã nguồn. Nó là năng lực đặt từng chính sách nghiệp vụ vào một ranh giới đủ nhỏ để chúng ta kiến tạo dữ liệu đầu vào, quan sát kết quả và nhận biết chính xác thay đổi nào đang được bảo vệ.

## Kết quả kiểm thử xanh chưa trả lời câu hỏi nào?

Với các bài thực hành vừa hoàn tất, kết quả báo xanh đồng nghĩa các khẳng định kiểm thử (*assertion*) đã được thỏa mãn trên tập dữ liệu và lịch trình thực thi cụ thể đó. Một khẳng định kiểm thử bị bỏ sót vẫn có thể để lọt lỗi trên chính dữ liệu đầu vào ấy. Kiểm thử mờ (*fuzzing*) mở rộng không gian tìm kiếm đầu vào dựa trên thời gian và độ bao phủ mã nguồn; số lượt chạy không cố định, và bộ fuzzer không thể tự sáng tạo thêm một đặc tính bất biến nếu tác giả chưa định nghĩa. Khi phát hiện lỗi sập (*crasher*), hãy lưu trữ mẫu dữ liệu đó cùng một ca kiểm thử hồi quy (*regression test*) có tên rõ ràng để người sửa đổi sau này biết rõ giao ước từng bị phá vỡ ở đâu.

Kiểm chuẩn hiệu năng (*benchmark*) lại giải đáp một câu hỏi hoàn toàn khác. Cấu trúc `b.Loop()` xuất hiện từ Go 1.24; trong phiên bản Go 1.27.1, lần gọi đầu tiên thiết lập lại bộ đếm thời gian và lần trả về `false` sẽ dừng bộ đếm. Với dạng chuẩn `for b.Loop() { ... }`, trình biên dịch bảo đảm duy trì sự sống của các đối số, kết quả lời gọi và biến gán trong thân vòng lặp theo cơ chế được mô tả tại `testing/benchmark.go`. Không nên suy diễn cơ chế tối ưu ấy sang một hàm bọc tùy tiện hoặc ngộ nhận rằng bài đo lường phản ánh đầy đủ môi trường sản xuất. Cách viết truyền thống `b.N` vẫn hoàn toàn hợp lệ; nếu sử dụng, hãy loại trừ phần khởi tạo khỏi bộ đếm thời gian khi cần và bảo đảm phép toán cần đo không bị trình biên dịch loại bỏ do không sử dụng kết quả. Không bao giờ trộn lẫn hai cách viết vòng lặp trong cùng một bài đo lường.

Bộ phát hiện tương tranh (*race detector*) cũng đi kèm chi phí tài nguyên nhất định. Tài liệu kỹ thuật chính thức nêu mức tiêu hao thường gặp khoảng 5–10 lần dung lượng bộ nhớ và 2–20 lần thời gian thực thi tùy cấu trúc chương trình; đây không phải số đo riêng của các bài thực hành trong sách. Bộ phát hiện chỉ quan sát các truy cập bộ nhớ thực sự xảy ra trong lượt chạy, do đó một nhánh mã chưa được kích hoạt sẽ không thể tạo ra báo cáo. Độ trễ mạng có thể làm bộc lộ những lịch trình thực thi đồng thời mới, nhưng điều đó không có nghĩa công cụ bất lực trước các tác vụ mạng. Để nâng cao xác suất phát hiện, hãy thiết kế các kịch bản có giá trị thực tế và bao quát đầy đủ các luồng tương tác then chốt, thay vì chỉ lặp đi lặp lại một kịch bản thuận lợi.

Lệnh `go test -cover` báo cáo độ bao phủ câu lệnh (*statement coverage*) dựa trên cơ chế gắn mã chẩn đoán (*instrumentation*) của Go, không phản ánh tỷ lệ mọi dòng mã nguồn và cũng không phải độ bao phủ nhánh (*branch coverage*) hay độ bao phủ đường dẫn (*path coverage*). Dù đạt mức 100%, con số đó chưa thể chứng minh mọi tổ hợp điều kiện, dữ liệu biên hay tương tác đồng thời đều chính xác. Ví dụ, một cấu trúc điều kiện `if` đã được kiểm thử ở nhánh đúng vẫn có thể chưa từng được kiểm tra ở nhánh sai. Khi đọc báo cáo độ bao phủ, hãy luôn đặt câu hỏi: khẳng định kiểm thử nào đang bảo vệ chính sách nghiệp vụ, nhánh luồng nào chưa từng chạy qua, và công cụ nào có thể phát hiện loại lỗi tiềm ẩn đó. Đó là giới hạn tất yếu của các công cụ thu thập bằng chứng, không phải lý do để buông lỏng việc kiểm thử.
