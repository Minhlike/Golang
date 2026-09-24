# Chương 6 — Thay đổi không sợ hãi

Ở cuối Chương 5, `opsprobe` đã biết lấy một điểm cuối từ cấu hình và gọi `probe.Check`. Nhưng một yêu cầu rất bình thường vẫn khó chứng minh: khi operator đặt `OPS_PROBE_TARGET=payments.internal:9443`, điểm cuối nào thực sự đi tới runner? Chạy CLI và nhìn dòng `billing healthy=true` không trả lời được. Dòng đó không in host hay cổng; kể cả có in, một lần chạy tay vẫn không phải contract mà mã nguồn giữ được khi nó đổi tiếp.

Đây là lúc nhiều codebase đi sai hướng. Có người viết test gọi `main`, sửa environment tiến trình chung, chụp stdout, rồi hy vọng không đụng `os.Exit`. Có người khác bỏ test vì “CLI chỉ vài dòng”. Cả hai đều né câu hỏi thiết kế: phần nào là orchestration có thể kiểm chứng, phần nào là tiến trình boundary chỉ nên mỏng và rõ?

## Một smoke test không biết điều ta cần biết

`main` hiện làm bốn việc cùng lúc: lấy environment thật, gọi cấu hình, gọi probe, quyết định exit mã nguồn và in terminal. Một test gọi nó chỉ cho biết tiến trình không chết ở đường happy path. Nó không thể đưa một environment giả vào an toàn, không thể quan sát điểm cuối runner nhận được, và không thể tách cấu hình error khỏi probe error mà không đụng side effect của tiến trình.

Vấn đề không phải `main` là xấu. `os.LookupEnv`, stdout, stderr và `os.Exit` đều có chỗ đúng: chúng là ranh giới nơi chương trình gặp tiến trình. Vấn đề là logic cần quyết định trước khi chạm ranh giới ấy chưa có một đơn vị để test gọi.

Ta tạo package nội bộ `internal/app`. Nó không thay thế `probe` hay `config`; nó phối hợp hai package đó. `Run` nhận đúng hai phụ thuộc biến đổi được trong test: hàm đọc environment và runner thực hiện probe. Nó trả outcome thay vì in:

~~~go
type Outcome struct {
	Service string
	Err     error
}

func Run(
	ctx context.Context,
	lookup cấu hình.LookupEnv,
	runner probe.Runner,
) ([]Outcome, error)
~~~

`Outcome.Err` là failure của một target đã được cấu hình; CLI có thể in nó rồi tiếp tục target khác. `error` return riêng là failure không tạo được danh sách outcome có nghĩa, như cấu hình không hợp lệ hoặc hủy thực thi của toàn bộ run. Việc tách hai đường này không phải để tạo type cho đẹp: bên gọi có policy khác nhau. Chương 4 từng đặt câu hỏi “bên gọi cần quyết định gì?”; ở đây câu trả lời quyết định shape của result.

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

Đoạn `main` vẫn có logic tối thiểu: policy trình bày và tiến trình exit nằm lộ ra, dễ review. Nhưng test không cần gọi nó. Test nằm cạnh `Run`, đưa một closure làm `LookupEnv` và một `probe.Runner` ghi lại điểm cuối được gọi. Không có socket, environment toàn cục hay terminal nào bị đụng tới.

Trước khi viết assertion, hãy tách ba thứ bằng mắt. Chúng ngăn test biến thành bản sao của implementation:

@table Phạm vi của unit test quanh `Run`

| Test kiểm soát | Test quan sát | Test không cần chạm |
| --- | --- | --- |
| `LookupEnv` trả target nào; runner thành công hay lỗi | điểm cuối runner nhận; `Outcome` hoặc error trả về | environment tiến trình, stdout, stderr, `os.Exit` |

Nếu một requirement chỉ hiện ra ở cột cuối, `Run` chưa phải đơn vị đúng để test; đó là việc của integration test ở một thời điểm có lý do. Nếu nó nằm ở cột đầu và cột giữa, unit test có thể cho feedback nhanh mà không giả lập cả tiến trình.

~~~go
func TestRunMapsEnvironmentTargetToRunner(t *testing.T) {
	var got probe.điểm cuối

	outcomes, err := Run(context.Background(), lookup(
		"OPS_PROBE_TARGET", "payments.internal:9443",
	), func(_ context.Context, điểm cuối probe.điểm cuối) error {
		got = điểm cuối
		return nil
	})

	if err != nil {
		t.Fatalf("Run() error = %v", err)
	}
	if got != (probe.điểm cuối{
		Host: "payments.internal",
		cổng: 9443,
	}) {
		t.Fatalf("runner điểm cuối = %+v", got)
	}
	if outcomes[0].Err != nil ||
		outcomes[0].Service != "billing" {
		t.Fatalf("outcome = %+v", outcomes[0])
	}
}
~~~

Đây là unit test không vì nó ngắn, mà vì nó kiểm chứng một đơn vị có boundary hẹp. Test hỏi một điều quan sát được: input cấu hình có đi tới runner đúng không, và result có được gán với service đúng không. Nó không kiểm tra implementation detail như `Run` dùng bao nhiêu local biến hay loop viết thế nào.

## Hai error, hai policy

Thử thêm hai test trước khi đọc hết implementation. Với `OPS_PROBE_TARGET=payments.internal:0`, cấu hình phải error trước khi runner chạy. Đây là invalid input của cả run, nên `Run` return error và không có outcome nửa vời. Với runner trả `errors.New("connection refused")`, target đã tồn tại và thao tác đã bắt đầu; `Run` giữ `Outcome{Service: "billing", Err: ...}` để command có thể báo một dòng lỗi rồi tiếp tục khi danh sách target sau này dài hơn.

hủy thực thi khác với cả hai. `probe.Check` giữ identity `context.Canceled`, còn `Run` dừng thay vì biến hủy thực thi của toàn bộ run thành một outcome per-service. Từ bên ngoài, ba policy hiện rõ:

@table Policy cho lỗi cấu hình, lỗi probe và hủy thực thi

| Tình huống | `Run` trả gì | Command nên làm gì? |
| --- | --- | --- |
| cấu hình không hợp lệ | `error` | In stderr, exit 2, không gọi runner. |
| Một probe thất bại | `Outcome.Err` | Báo service đó; policy hiện tại cho phép đi tiếp. |
| Context bị cancel | `error` giữ identity | Dừng run; không ghi health signal giả. |

Không phải test nào cũng cần fake. cấu hình parser đã có test input/output riêng ở Chương 5; `probe.Check` đã có test hủy thực thi và wrapping. `Run` chỉ test phần nối ba contract ấy. Nếu một test chỉ lặp lại assertion của package dưới nó, nó làm refactor khó hơn mà không tăng niềm tin.

**Thực hành - remove and rebuild.** Mở `labs/part6-testable-command`, đọc `internal/app/run_test.go` trước. Đừng chạy command trước; hãy dự đoán mỗi test đang bảo vệ policy nào. Sau đó tạm đổi tên `Run` để compiler báo các điểm mà test đang đòi contract, rồi tự dựng lại hàm từ test và các type đã có. Khi unit test xanh, chạy `go run ./cmd/opsprobe`. Cuối cùng đổi runner trong `main` thành một runner trả error và xác minh CLI in service name thay vì nuốt failure. Khôi phục runner thành công trước khi rời lab.

---

**Đáp án — chỉ đọc sau khi đã tự làm.** `Run` cần gọi `config.LoadTargets` đúng một lần trước loop, map từng `Target` sang `probe.Service`, rồi append outcome thành công hoặc failure của từng probe. Chỉ cấu hình error và hủy thực thi thoát khỏi `Run` qua return error. `main` giữ environment thật, output và exit mã nguồn. Lời giải không phải “dùng mock framework”; hai hàm giá trị đang có đã là seams vừa đủ.

## Khi một test case che mất các policy khác

Test đầu tiên của `Run` cố ý chỉ dùng một override hợp lệ. Nó trả lời câu hỏi của refactor: điểm cuối có thật sự đi tới runner không? Nhưng nếu cứ nhân bản kiểu test đó cho từng input xấu, test suite sẽ dần thành một hành lang dài của những hàm gần giống nhau. Lúc ấy người đọc không còn nhìn thấy các rule của cấu hình; họ chỉ thấy rất nhiều lần gọi `LoadTargets`.

Một reviewer tốt sẽ hỏi khác đi: parser này có bao nhiêu *policy* độc lập? Với `OPS_PROBE_TARGET`, ta cần giữ ít nhất hai. biến vắng mặt dùng default đã công bố. biến có mặt phải là một `host:port` hợp lệ, có host và cổng trong khoảng TCP. Mỗi hàng test là một ví dụ cho một policy, không phải một input ngẫu nhiên để tăng coverage.

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

`t.Run` không chỉ để kết quả trông có tổ chức. Khi một case vỡ, `go test -v` sẽ nói case nào vỡ, thay vì để anh đếm hàng trong slice. Vì vậy `name` phải mô tả behavior: “cổng zero” tốt hơn “case 4”, còn “uses the documented default” nhắc cả người bảo trì rằng default là một phần contract.

### Review một bảng test trước khi tin nó

Thêm các input bị từ chối vào một table thứ hai trong `internal/config/config_test.go`:

~~~go
tests := []struct {
	name string
	raw  string
}{
	{name: "missing cổng", raw: "payments.internal"},
	{name: "empty host", raw: ":8443"},
	{name: "non-numeric cổng", raw: "payments.internal:https"},
	{name: "cổng zero", raw: "payments.internal:0"},
	{
		name: "cổng above TCP range",
		raw:  "payments.internal:65536",
	},
}
~~~

Điểm dễ bỏ sót không nằm ở vòng `for`, mà ở assertion. Test này chỉ hứa rằng từng input không hợp lệ bị từ chối; nó không hứa nguyên văn error message. Message là chi tiết có thể sửa để tốt hơn cho operator. Rule “input này không được phép tạo target” mới là contract. Nếu CLI hoặc API cần phân loại lỗi bằng máy, khi đó mới có lý do để thiết kế error type hay sentinel rõ ràng; đừng dùng string comparison như một cách thay thế cho thiết kế đó.

Với edition Go 1.27.1 này, range biến được khai báo bằng `:=` có một biến riêng ở mỗi iteration (semantics từ Go 1.22), nên closure không còn vô tình cùng giữ một biến `tt` như folklore Go cũ. Nhưng một bẫy con trỏ khác vẫn còn: `&tt` trỏ tới bản copy của iteration, không phải phần tử thật trong slice `tests`. Nếu mục tiêu là mutate phần tử gốc, hãy range lấy index rồi dùng `&tests[i]`. Ở đây `t.Run` chạy đồng bộ và closure chỉ đọc `tt`, nên con trỏ lẫn lifetime goroutine đều không phải điều policy parser cần nghĩ.

**Bài review ngắn.** Trước khi chạy test, hãy tự phân loại năm hàng trên: hàng nào bị `net.SplitHostPort` từ chối, hàng nào đi qua parser nhưng bị validation của sách từ chối? Sau đó thêm một case hợp lệ cho IPv6 theo dạng `[2001:db8::10]:443`. Assertion của nó phải kiểm tra `Host` không còn dấu ngoặc và `Port == 443`, thay vì chỉ kiểm tra `err == nil`.

---


**Đáp án — chỉ đọc sau khi đã tự làm.** Thiếu cổng và `:8443` không tạo được target hợp lệ ở bước parse/host check. `https`, `0` và `65536` đi xa hơn: chúng cần conversion hoặc range validation. Với IPv6, `net.SplitHostPort` tách dạng có ngoặc thành host `2001:db8::10` và cổng `443`; chính vì vậy test nên ghi điều đó thành contract. Khi bảng bắt đầu chứa các cột không cùng một rule, hoặc mỗi row cần setup rất khác, tách test ra sẽ rõ hơn là nhồi thêm cột.

## Chạy đúng bằng chứng

Khi suite xanh, `go test ./...` trả lời câu hỏi có giá trị nhưng rộng: có package nào vi phạm contract không? Lúc điều tra một report cụ thể, chạy tất cả test nhiều lần lại làm mất ngữ cảnh. Nếu operator báo rằng cổng `0` từng lọt qua validation, ta cần nhìn đúng rule đó trước, rồi mới mở rộng phạm vi.

Từ thư mục `labs/part6-testable-command`, lệnh sau chọn một subtest bằng đường dẫn tên của nó:

~~~powershell
$case = 'TestLoadTargetsRejectsMalformedOverrides/port_zero'
go test -run $case -v ./internal/cấu hình
~~~

Đây không phải shortcut để né test đầy đủ trước khi commit. Nó là một kính lúp trong lúc debug: output giữ tên parent test và case `port_zero`, nên anh biết mình đang xem policy nào. Sau khi sửa bug, chạy lại package rồi chạy toàn bộ suite; một lỗi parser có thể làm app thất bại trước cả khi runner được gọi.

Hãy thử thay đổi tạm thời điều kiện range trong `LoadTargets` để cổng `0` đi qua, chỉ để xem subtest vỡ như thế nào. Đừng commit thay đổi đó. Bài học không phải thuộc câu lệnh `-run`; nó là phân biệt vòng lặp điều tra ngắn với bằng chứng đủ rộng để nhận một thay đổi vào codebase.

Từ đây Chương 6 đã có hai loại test khác nhau: `Run` kiểm chứng việc nối các boundary, còn cấu hình subtest giữ một ma trận input nhỏ nhưng có ý nghĩa. Phần tiếp theo sẽ tạo một failure mà unit test xanh vẫn chưa bắt được - hai goroutine cùng chạm vào một vùng dữ liệu.

## Một test xanh vẫn có thể bỏ sót race

`opsprobe` hiện chưa chạy probe song song; đó là lựa chọn có chủ đích khi ta còn đang học boundary và policy lỗi. Vì vậy sẽ là sai nếu em giả vờ vừa phát hiện một race trong mã nguồn của nó. Thay vào đó, hãy tách đúng failure cần học: nhiều worker cùng ghi vào một counter hoàn thành. Đây là loại bug có thể trông vô hại khi chạy một lần, vì không có compiler error và unit test tuần tự vẫn xanh.

Data race xảy ra khi nhiều goroutine truy cập cùng một biến đồng thời, có ít nhất một lần ghi, và không có synchronization phù hợp. Đây là định nghĩa về hành vi, không phải một lời phán đoán dựa trên việc count cuối cùng “có vẻ đúng”. `successes++` không phải một hành động nguyên tử ở cấp source; nó đọc giá trị cũ, tạo giá trị mới rồi ghi lại. Hai goroutine có thể xen vào giữa các bước ấy.

Lab `labs/part6-race-detector/broken` giữ một counter cố ý sai. Test tạo 128 goroutine, mỗi goroutine gọi đúng một lần `RecordSuccess`:

~~~go
type Counter struct {
	successes int
}

func (c *Counter) RecordSuccess() {
	c.successes++
}
~~~

Chạy test thường có thể không nói gì đáng ngờ. Để đưa memory access vào quan sát, hãy chạy fixture với race detector:

~~~powershell
go test -race -tags raceexercise ./broken
~~~

Lệnh này được mong đợi là thất bại và in `WARNING: DATA RACE`. Đó là một failure có chủ ý của lab, không phải một check được phép xanh cho milestone. Race detector ghi stack trace ở các access xung đột và nơi các goroutine liên quan được tạo. Khi đọc report, hãy lần theo ba câu hỏi: biến nào được dùng chung, access nào là write, và synchronization nào đáng lẽ phải tạo thứ tự giữa chúng?

@table Ba phần hữu ích nhất của một race report

| Phần report | Nó trả lời gì | Đừng kết luận quá mức |
| --- | --- | --- |
| `Read by goroutine` hoặc `Write by goroutine` | Access hiện tại nằm ở dòng nào? | Dòng đó chưa chắc là nguồn gốc policy sai. |
| `Previous ... by goroutine` | Access xung đột nào chồng lên nó? | Thứ tự in ra không phải timeline đầy đủ của chương trình. |
| `created at` | Goroutine nào mở đường cho access này? | Một report không chứng minh mọi đường chạy đều racy. |

Detector là công cụ tìm bằng chứng khi mã nguồn đã chạy, không phải chứng minh tuyệt đối rằng chương trình không có race. Một đường chưa được test chưa tạo memory access để detector quan sát. Vì thế `go test -race` đứng cạnh test tốt và tải công việc có ý nghĩa; nó không thay thế chúng.

### Sửa invariant, không chỉ làm detector im lặng

Trước khi thêm `sync.Mutex`, hãy nói invariant bằng một câu: `Successes` phải trả về số lần `RecordSuccess` đã hoàn tất, kể cả khi nhiều worker đang chạy. `Counter` vì thế mang một field `mu sync.Mutex` cạnh `successes`. Lock không còn là bùa chú; nó là ranh giới bảo vệ hai access vào state dùng chung:

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

Phiên bản này nằm trong `labs/part6-race-detector/fixed`. Test của nó chờ mọi worker bằng `sync.WaitGroup`, sau đó kiểm tra count là `128`; `go test -race ./fixed` phải xanh. `WaitGroup` ở đây chỉ giúp test biết khi nào worker xong. Nó không tự bảo vệ `successes`; mutex mới làm việc đó. Phân biệt hai trách nhiệm này ngay từ đầu sẽ tránh rất nhiều “đã Wait rồi, sao vẫn race?” sau này.

`Mutex` và memory ordering sẽ được đào sâu ở phần concurrency. Ở Chương 6, bài học hẹp hơn: một test có assertion đúng vẫn có thể chưa quan sát được cách state bị chạm. Nếu requirement đưa goroutine vào mã nguồn, thêm `-race` vào bằng chứng chấp nhận thay đổi là một quyết định testability, không phải một nghi thức trang trí.

**Bài điều tra.** Chạy fixture `broken` một lần với `-race`, rồi mở `fixed/counter_test.go`. Trước khi chạy phiên bản fixed, khoanh hai method cùng chạm `successes` và dự đoán vì sao cả getter cũng lock. Sau đó thử bỏ lock riêng trong `Successes`; test hiện tại vẫn có thể xanh vì nó đọc sau `wg.Wait`, nhưng public method đã mất contract an toàn cho bên gọi đồng thời.

---

**Đáp án — chỉ đọc sau khi đã tự làm.** `RecordSuccess` ghi còn `Successes` đọc cùng field, nên cả hai cần đi qua cùng mutex nếu API hứa dùng được đồng thời. `wg.Wait` chỉ tạo điểm chờ trong test hiện tại; nó không thay thế synchronization trong API. Fixture broken được tag riêng để repository vẫn có suite mặc định xanh, còn lệnh race được chạy như một thí nghiệm mà failure là kết quả đúng.

## Fuzz khi property đã rõ

Các subtest của cấu hình đã có tên cho những biên mà ta chủ động chọn: cổng `0`, host rỗng, cổng quá lớn. Nhưng parser nhận một `string`; không ai có thể liệt kê trước mọi tổ hợp dấu ngoặc, Unicode, dấu hai chấm hay byte lạ mà input từ environment có thể mang theo. Fuzzing giúp tạo thêm input, nhưng chỉ có giá trị khi target biết phải đòi điều gì ở mọi input đó.

Property của `LoadTargets` không phải “mọi string đều được parse”. Phần lớn string phải bị từ chối. Property đúng là: nếu `LoadTargets` trả thành công, nó trả đúng một target có host không rỗng và cổng trong `1..65535`. Điều này ghép tốt với table test: table nói các case quan trọng nào phải bị từ chối hay được map đúng; fuzz tìm xem còn input nào làm implementation tự mâu thuẫn với invariant đó.

Đừng thay property ấy bằng “hàm không panic”. Không panic là một hygiene check đáng có, nhưng một parser có thể bình tĩnh trả `Target{Host: "", Port: 0}` và vẫn phá command ở chỗ xa hơn. Property mạnh hơn buộc test nhìn vào kết quả thành công. Ngược lại, đừng bắt fuzz phải đoán error message hay bắt mọi input xấu rơi đúng vào một nhánh implementation; những điều đó làm target giòn mà không tăng sự hiểu biết về contract.

Trong thực tế có nhiều họ property: kết quả luôn giữ invariant, encode rồi decode trả về dữ liệu tương đương, hay hai cách biểu diễn phải đồng thuận. Ta chỉ dùng họ đầu tiên ở đây vì parser này chưa có format output để round-trip. Chọn property theo API đang có giúp fuzzing phục vụ thiết kế, thay vì ép mọi hàm phải có một bài test ngẫu nhiên.

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
			target.cổng < 1 ||
			target.cổng > 65535 {
			t.Fatalf("invalid target %+v", target)
		}
	})
}
~~~

`f.Add` không phải danh sách đầy đủ. Nó là seed corpus có chủ đích: một default, một hostname thường, một IPv6, một range error và một chuỗi không có hình dạng target. Khi chạy `go test`, seed corpus này vẫn được chạy như test bình thường. Khi chạy với `-fuzz`, toolchain mutate corpus để tìm input tạo coverage mới. Nếu tìm được failure, Go lưu input tái lập được để lần `go test` sau không làm bug biến mất theo may rủi.

Từ `labs/part6-testable-command`, chạy một lượt có giới hạn thời gian:

~~~powershell
go test -run=^$ `
  -fuzz=FuzzLoadTargetsNeverReturnsInvalidTarget `
  -fuzztime=2s ./internal/cấu hình
~~~

`-run=^$` bỏ qua ordinary test trong lượt fuzz riêng này; chúng vẫn phải chạy trong suite bình thường. `-fuzztime=2s` là ngân sách cho thí nghiệm local, không phải một con số chứng nhận parser an toàn. Fuzz target xanh chỉ nói rằng các input đã chạy chưa phá property; nó không thay thế review, test case có ý nghĩa hay validation giới hạn tài nguyên.

**Bài thiết kế property.** Một đề xuất nghe có vẻ hợp lý là “nếu `err == nil`, `target.Name` luôn là `billing`”. Hãy quyết định có nên đưa nó vào fuzz target này không. Nếu ngày mai cấu hình hỗ trợ nhiều service, assertion đó sẽ làm test cản refactor dù parser vẫn đúng. Hãy giữ property gần với contract hiện tại nhất: shape hợp lệ của target, không phải một chi tiết của demo.

---

**Đáp án — chỉ đọc sau khi đã tự làm.** `Name == "billing"` là contract hiện tại của fixture nhỏ, nhưng không phải property parser cần giữ khi input model lớn hơn. Fuzz property nên đủ mạnh để bắt target lỗi và đủ hẹp để không đóng băng một thiết kế chưa được hứa. Khi fuzz tìm được failure thật, trước hết biến input đó thành một regression test dễ đọc; corpus là bằng chứng, test có tên là lời giải thích cho người đến sau.

## Đo câu hỏi trước khi tối ưu câu trả lời

Sau khi thấy parser có nhiều validation, một phản xạ quen thuộc là đề nghị cache kết quả: “`net.SplitHostPort` có thể chậm”. Nhưng `LoadTargets` hiện chỉ chạy khi command khởi tạo. Kể cả một benchmark cho thấy override tốn allocation, điều đó chưa biến nó thành bottleneck của một CLI chạy vài probe. Benchmark tốt bắt đầu bằng câu hỏi đủ cụ thể để kết quả có thể thay đổi một quyết định.

Ở đây câu hỏi hẹp là: một lần load default, hostname override và IPv6 override có chi phí tương đối ra sao trên máy đang chạy? Test setup nằm trước `b.Loop()`, nên timer của benchmark hiện đại không tính phần đó; `b.ReportAllocs` yêu cầu output thêm allocation:

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

Chạy từ lab với `go test -run=^$ -bench=BenchmarkLoadTargets -benchmem ./internal/config`. `-run=^$` tránh trộn ordinary test vào lượt đo; `-benchmem` cho `allocs/op` và `B/op`. Đừng copy số `ns/op` của máy này vào một README như một sự thật phổ quát. CPU, Go version, power mode và noise của hệ thống đều làm số đổi. Nếu một thay đổi performance thật sự sắp được nhận, hãy đo trước/sau trên cùng môi trường, lặp lại và ghi đúng tải công việc mà quyết định đang phục vụ.

Trong case này, kết luận có thể là “không tối ưu”. Đó là một kết quả kỹ thuật hoàn toàn hợp lệ: cấu hình parse một lần chưa đáng đổi API, thêm cache hay làm mã nguồn kém đọc. Benchmark đã làm việc của nó khi giúp ta từ chối một tối ưu không có pressure, chứ không chỉ khi nó dẫn tới một patch nhanh hơn.

**Bài review.** Chạy benchmark hai lần. Chỉ đề xuất tối ưu khi có tải công việc như cấu hình reload trong hot loop hoặc profile thật; “số lớn hơn” chưa đủ.

## Contract ở ranh giới tiến trình

Unit test của `app.Run` cố ý không biết terminal hay exit mã nguồn. Điều đó giúp nó giữ boundary hẹp, nhưng cũng tạo một khoảng trống cần kiểm tra ở đúng nơi: command vẫn phải in success vào stdout, đưa cấu hình error sang stderr và trả mã exit `2`. Đây là contract nhìn thấy được của tiến trình; đổi nó có thể làm script của operator hỏng dù các package phía trong vẫn xanh.

Gọi `main` trong test thường làm khoảng trống ấy khó kiểm chứng, vì `os.Exit` kết thúc tiến trình test. Thay vì fake cả tiến trình, ta rút phần presentation thành một hàm nhỏ nhận writer và trả exit mã nguồn. `main` chỉ nối phụ thuộc thật vào hàm đó:

~~~go
func main() {
	runner := func(context.Context, probe.điểm cuối) error {
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

`run` vẫn gọi `app.Run`; nó chỉ thêm policy tiến trình rất nhỏ. Test vì thế có thể dùng `bytes.Buffer` làm stdout và stderr, rồi quan sát đúng ba thứ mà shell nhìn thấy: mã nguồn, output thành công và output lỗi.

~~~go
func TestRunWritesSuccessContract(t *testing.T) {
	var out, errOut bytes.vùng đệm
	mã nguồn := run(
		context.Background(),
		&out,
		&errOut,
		func(string) (string, bool) { return "", false },
		func(
			context.Context,
			probe.điểm cuối,
		) error { return nil },
	)

	if mã nguồn != 0 {
		t.Fatalf("mã nguồn = %d", mã nguồn)
	}
	if out.String() != "billing healthy=true\n" {
		t.Fatalf("stdout = %q", out.String())
	}
	if errOut.Len() != 0 {
		t.Fatalf("stderr = %q", errOut.String())
	}
}
~~~

Test này không assert `run` loop outcome thế nào hay `app.Run` parse cấu hình ra sao. Những contract đó đã thuộc package riêng. Nó chỉ giữ lời hứa của command: success đọc được bằng máy trên stdout và không rò error message.

Test phía failure cũng phải hẹp như vậy. Đưa vào một cổng không hợp lệ, để runner làm test fail nếu bị gọi, rồi assert exit `2`, stdout rỗng và diagnostic ở stderr. Đừng so toàn bộ message: wording validation có thể được cải thiện, còn nơi xuất hiện và exit policy mới là contract vận hành ổn định.

**Bài mã nguồn review.** Chuyển một `fmt.Fprintf` từ `out` sang `errOut` rồi quyết định đó là chỉnh presentation vô hại hay breaking change cho shell pipeline. Sau đó tưởng tượng một mode `--json`: contract test nên có case riêng cho mode được hứa rõ ràng này, không được làm contract text mode yếu đi đến mức nhận bất cứ output nào.

---

**Đáp án — chỉ đọc sau khi đã tự làm.** Trong shell pipeline, stdout thường mang dữ liệu command sau sẽ tiêu thụ; chuyển healthy result sang stderr có thể là breaking change. Test không cố đóng băng dấu câu mãi mãi. Nó bảo vệ boundary mà con người và automation dựa vào: success exit `0` và có result trên stdout; configuration failure exit `2`, không in success data, đồng thời có diagnostic ở stderr.

Contract test này không thay thế một end-to-end test khởi động binary thật. Khi sau này command nhận flag, tệp cấu hình, signal hoặc network thật, một số luồng cần được kiểm chứng qua tiến trình thật. Nhưng dùng binary test để assert mọi dấu cách và mọi nhánh validation sẽ chậm, khó đọc và trùng với unit test. Ranh giới tốt là: logic có phụ thuộc thay thế được kiểm tra ở package bên trong; vài lời hứa mà tiến trình công bố được giữ ở `run`; chỉ một số đường đi quan trọng mới cần vượt ra integration test.

Vì vậy, việc tách `run` không phải là đổi thiết kế chỉ để làm test pass. Nó làm chính sách vốn đã tồn tại trong `main` có tên, input và output rõ. mã nguồn review có thể hỏi một câu cụ thể: “thay đổi này có làm automation nhận stdout, stderr hoặc exit mã nguồn khác không?” Nếu có, tác giả phải chủ động quyết định đó là compatibility change, chứ không để nó lọt qua dưới vỏ bọc refactor nội bộ.

Đây là điểm dừng của mốc hiện tại: testability không đồng nghĩa phủ một lớp mock lên mọi package. Nó là khả năng đặt từng policy vào một boundary đủ nhỏ để ta tạo input, quan sát kết quả và biết chính xác thay đổi nào đang được bảo vệ.
