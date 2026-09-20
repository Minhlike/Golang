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
