# Chương 6 — Thay đổi không sợ hãi

Ở cuối Chương 5, `opsprobe` đã biết lấy một endpoint từ config và gọi `probe.Check`. Nhưng một yêu cầu rất bình thường vẫn khó chứng minh: khi operator đặt `OPS_PROBE_TARGET=payments.internal:9443`, endpoint nào thực sự đi tới runner? Chạy CLI và nhìn dòng `billing healthy=true` không trả lời được. Dòng đó không in host hay port; kể cả có in, một lần chạy tay vẫn không phải contract mà code giữ được khi nó đổi tiếp.

Đây là lúc nhiều codebase đi sai hướng. Có người viết test gọi `main`, sửa environment process chung, chụp stdout, rồi hy vọng không đụng `os.Exit`. Có người khác bỏ test vì “CLI chỉ vài dòng”. Cả hai đều né câu hỏi thiết kế: phần nào là orchestration có thể kiểm chứng, phần nào là process boundary chỉ nên mỏng và rõ?

## Một smoke test không biết điều ta cần biết

`main` hiện làm bốn việc cùng lúc: lấy environment thật, gọi config, gọi probe, quyết định exit code và in terminal. Một test gọi nó chỉ cho biết process không chết ở đường happy path. Nó không thể đưa một environment giả vào an toàn, không thể quan sát endpoint runner nhận được, và không thể tách config error khỏi probe error mà không đụng side effect của process.

Vấn đề không phải `main` là xấu. `os.LookupEnv`, stdout, stderr và `os.Exit` đều có chỗ đúng: chúng là ranh giới nơi chương trình gặp process. Vấn đề là logic cần quyết định trước khi chạm ranh giới ấy chưa có một đơn vị để test gọi.

Ta tạo package nội bộ `internal/app`. Nó không thay thế `probe` hay `config`; nó phối hợp hai package đó. `Run` nhận đúng hai dependency biến đổi được trong test: function đọc environment và runner thực hiện probe. Nó trả outcome thay vì in:

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

`Outcome.Err` là failure của một target đã được cấu hình; CLI có thể in nó rồi tiếp tục target khác. `error` return riêng là failure không tạo được danh sách outcome có nghĩa, như config không hợp lệ hoặc cancellation của toàn bộ run. Việc tách hai đường này không phải để tạo type cho đẹp: caller có policy khác nhau. Chương 4 từng đặt câu hỏi “caller cần quyết định gì?”; ở đây câu trả lời quyết định shape của result.

## Refactor đến khi test có thứ để nắm

`Run` load target, map `config.Target` sang `probe.Service`, gọi `probe.Check`, rồi giữ mỗi kết quả trong một `Outcome`. Nó không đọc `os.LookupEnv`, không gọi `fmt.Printf` và không được gọi `os.Exit`. Những side effect ấy còn ở `cmd/opsprobe/main.go`:

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

Đoạn `main` vẫn có logic tối thiểu: policy trình bày và process exit nằm lộ ra, dễ review. Nhưng test không cần gọi nó. Test nằm cạnh `Run`, đưa một closure làm `LookupEnv` và một `probe.Runner` ghi lại endpoint được gọi. Không có socket, environment toàn cục hay terminal nào bị đụng tới.

Trước khi viết assertion, hãy tách ba thứ bằng mắt. Chúng ngăn test biến thành bản sao của implementation:

@table Phạm vi của unit test quanh `Run`

| Test kiểm soát | Test quan sát | Test không cần chạm |
| --- | --- | --- |
| `LookupEnv` trả target nào; runner thành công hay lỗi | endpoint runner nhận; `Outcome` hoặc error trả về | environment process, stdout, stderr, `os.Exit` |

Nếu một requirement chỉ hiện ra ở cột cuối, `Run` chưa phải đơn vị đúng để test; đó là việc của integration test ở một thời điểm có lý do. Nếu nó nằm ở cột đầu và cột giữa, unit test có thể cho feedback nhanh mà không giả lập cả process.

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
	if got != (probe.Endpoint{Host: "payments.internal", Port: 9443}) {
		t.Fatalf("runner endpoint = %+v", got)
	}
	if outcomes[0].Err != nil || outcomes[0].Service != "billing" {
		t.Fatalf("outcome = %+v", outcomes[0])
	}
}
~~~

Đây là unit test không vì nó ngắn, mà vì nó kiểm chứng một đơn vị có boundary hẹp. Test hỏi một điều quan sát được: input config có đi tới runner đúng không, và result có được gán với service đúng không. Nó không kiểm tra implementation detail như `Run` dùng bao nhiêu local variable hay loop viết thế nào.

## Hai error, hai policy

Thử thêm hai test trước khi đọc hết implementation. Với `OPS_PROBE_TARGET=payments.internal:0`, config phải error trước khi runner chạy. Đây là invalid input của cả run, nên `Run` return error và không có outcome nửa vời. Với runner trả `errors.New("connection refused")`, target đã tồn tại và operation đã bắt đầu; `Run` giữ `Outcome{Service: "billing", Err: ...}` để command có thể báo một dòng lỗi rồi tiếp tục khi danh sách target sau này dài hơn.

Cancellation khác với cả hai. `probe.Check` giữ identity `context.Canceled`, còn `Run` dừng thay vì biến cancellation của toàn bộ run thành một outcome per-service. Từ bên ngoài, ba policy hiện rõ:

@table Policy cho lỗi cấu hình, lỗi probe và cancellation

| Tình huống | `Run` trả gì | Command nên làm gì? |
| --- | --- | --- |
| Config không hợp lệ | `error` | In stderr, exit 2, không gọi runner. |
| Một probe thất bại | `Outcome.Err` | Báo service đó; policy hiện tại cho phép đi tiếp. |
| Context bị cancel | `error` giữ identity | Dừng run; không ghi health signal giả. |

Không phải test nào cũng cần fake. Config parser đã có test input/output riêng ở Chương 5; `probe.Check` đã có test cancellation và wrapping. `Run` chỉ test phần nối ba contract ấy. Nếu một test chỉ lặp lại assertion của package dưới nó, nó làm refactor khó hơn mà không tăng niềm tin.

**Thực hành - remove and rebuild.** Mở `labs/part6-testable-command`, đọc `internal/app/run_test.go` trước. Đừng chạy command trước; hãy dự đoán mỗi test đang bảo vệ policy nào. Sau đó tạm đổi tên `Run` để compiler báo các điểm mà test đang đòi contract, rồi tự dựng lại function từ test và các type đã có. Khi unit test xanh, chạy `go run ./cmd/opsprobe`. Cuối cùng đổi runner trong `main` thành một runner trả error và xác minh CLI in service name thay vì nuốt failure. Khôi phục runner thành công trước khi rời lab.

---

**Đáp án — chỉ đọc sau khi đã tự làm.** `Run` cần gọi `config.LoadTargets` đúng một lần trước loop, map từng `Target` sang `probe.Service`, rồi append outcome thành công hoặc failure của từng probe. Chỉ config error và cancellation thoát khỏi `Run` qua return error. `main` giữ environment thật, output và exit code. Lời giải không phải “dùng mock framework”; hai function value đang có đã là seams vừa đủ.

## Khi một test case che mất các policy khác

Test đầu tiên của `Run` cố ý chỉ dùng một override hợp lệ. Nó trả lời câu hỏi của refactor: endpoint có thật sự đi tới runner không? Nhưng nếu cứ nhân bản kiểu test đó cho từng input xấu, test suite sẽ dần thành một hành lang dài của những hàm gần giống nhau. Lúc ấy người đọc không còn nhìn thấy các rule của config; họ chỉ thấy rất nhiều lần gọi `LoadTargets`.

Một reviewer tốt sẽ hỏi khác đi: parser này có bao nhiêu *policy* độc lập? Với `OPS_PROBE_TARGET`, ta cần giữ ít nhất hai. Variable vắng mặt dùng default đã công bố. Variable có mặt phải là một `host:port` hợp lệ, có host và port trong khoảng TCP. Mỗi hàng test là một ví dụ cho một policy, không phải một input ngẫu nhiên để tăng coverage.

Đây là lúc bảng test có ích. Không phải vì Go community có một nghi thức tên là “table-driven test”, mà vì bảng làm lộ phần thay đổi và phần giữ nguyên. `raw`, `found` và `want` thay đổi theo case; cách gọi parser và assertion về một target duy nhất được giữ chung:

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

`t.Run` không chỉ để kết quả trông có tổ chức. Khi một case vỡ, `go test -v` sẽ nói case nào vỡ, thay vì để anh đếm hàng trong slice. Vì vậy `name` phải mô tả behavior: “port zero” tốt hơn “case 4”, còn “uses the documented default” nhắc cả người bảo trì rằng default là một phần contract.

### Review một bảng test trước khi tin nó

Thêm các input bị từ chối vào một table thứ hai trong `internal/config/config_test.go`:

~~~go
tests := []struct {
	name string
	raw  string
}{
	{name: "missing port", raw: "payments.internal"},
	{name: "empty host", raw: ":8443"},
	{name: "non-numeric port", raw: "payments.internal:https"},
	{name: "port zero", raw: "payments.internal:0"},
	{name: "port above TCP range", raw: "payments.internal:65536"},
}
~~~

Điểm dễ bỏ sót không nằm ở vòng `for`, mà ở assertion. Test này chỉ hứa rằng từng input không hợp lệ bị từ chối; nó không hứa nguyên văn error message. Message là chi tiết có thể sửa để tốt hơn cho operator. Rule “input này không được phép tạo target” mới là contract. Nếu CLI hoặc API cần phân loại lỗi bằng máy, khi đó mới có lý do để thiết kế error type hay sentinel rõ ràng; đừng dùng string comparison như một cách thay thế cho thiết kế đó.

Có một bẫy nhỏ khi viết subtest: đừng lấy địa chỉ của biến loop rồi giữ nó để dùng sau vòng lặp. Ở đây `t.Run` chạy đồng bộ, closure đọc `tt` ngay trong body, nên không có goroutine nào sống qua iteration. Bài về parallel subtest sẽ quay lại bẫy này cùng race detector; hiện tại ta giữ test tuần tự để policy parser là thứ duy nhất cần nghĩ.

**Bài review ngắn.** Trước khi chạy test, hãy tự phân loại năm hàng trên: hàng nào bị `net.SplitHostPort` từ chối, hàng nào đi qua parser nhưng bị validation của sách từ chối? Sau đó thêm một case hợp lệ cho IPv6 theo dạng `[2001:db8::10]:443`. Assertion của nó phải kiểm tra `Host` không còn dấu ngoặc và `Port == 443`, thay vì chỉ kiểm tra `err == nil`.

---


**Đáp án — chỉ đọc sau khi đã tự làm.** Thiếu port và `:8443` không tạo được target hợp lệ ở bước parse/host check. `https`, `0` và `65536` đi xa hơn: chúng cần conversion hoặc range validation. Với IPv6, `net.SplitHostPort` tách dạng có ngoặc thành host `2001:db8::10` và port `443`; chính vì vậy test nên ghi điều đó thành contract. Khi bảng bắt đầu chứa các cột không cùng một rule, hoặc mỗi row cần setup rất khác, tách test ra sẽ rõ hơn là nhồi thêm cột.

## Chạy đúng bằng chứng

Khi suite xanh, `go test ./...` trả lời câu hỏi có giá trị nhưng rộng: có package nào vi phạm contract không? Lúc điều tra một report cụ thể, chạy tất cả test nhiều lần lại làm mất ngữ cảnh. Nếu operator báo rằng port `0` từng lọt qua validation, ta cần nhìn đúng rule đó trước, rồi mới mở rộng phạm vi.

Từ thư mục `labs/part6-testable-command`, lệnh sau chọn một subtest bằng đường dẫn tên của nó:

~~~powershell
$case = 'TestLoadTargetsRejectsMalformedOverrides/port_zero'
go test -run $case -v ./internal/config
~~~

Đây không phải shortcut để né test đầy đủ trước khi commit. Nó là một kính lúp trong lúc debug: output giữ tên parent test và case `port_zero`, nên anh biết mình đang xem policy nào. Sau khi sửa bug, chạy lại package rồi chạy toàn bộ suite; một lỗi parser có thể làm app thất bại trước cả khi runner được gọi.

Hãy thử thay đổi tạm thời điều kiện range trong `LoadTargets` để port `0` đi qua, chỉ để xem subtest vỡ như thế nào. Đừng commit thay đổi đó. Bài học không phải thuộc câu lệnh `-run`; nó là phân biệt vòng lặp điều tra ngắn với bằng chứng đủ rộng để nhận một thay đổi vào codebase.

Từ đây Chương 6 đã có hai loại test khác nhau: `Run` kiểm chứng việc nối các boundary, còn config subtest giữ một ma trận input nhỏ nhưng có ý nghĩa. Phần tiếp theo sẽ tạo một failure mà unit test xanh vẫn chưa bắt được - hai goroutine cùng chạm vào một vùng dữ liệu.
