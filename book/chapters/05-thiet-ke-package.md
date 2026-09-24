# Chương 5 — Package là ranh giới

Sau Chương 4, `opsprobe` có một API cho một lần probe. Nhưng lab vẫn là một package `main` chứa model, policy error, cấu hình giả và cách in ra terminal. Khi mọi thứ còn ngắn, một tệp là lựa chọn tốt. Vấn đề xuất hiện không phải vì số tệp tăng, mà vì một thay đổi ở cách in CLI có thể nhìn thấy mọi chi tiết của probe, và một thay đổi cấu hình có thể kéo domain model đi cùng.

Ta sẽ không mở đầu bằng cây thư mục “chuẩn”. Ta bắt đầu bằng một review: mã nguồn nào phải biết `fmt.Println`, mã nguồn nào phải biết điểm cuối, và mã nguồn nào có quyền quyết định cấu hình được đọc từ đâu? Khi câu trả lời khác nhau, boundary cũng phải khác nhau.

## Một phụ thuộc graph có thể đọc từ ngoài vào trong

Refactor đầu tiên của `opsprobe` có ba vai:

- `cmd/opsprobe` là command: nhận các phụ thuộc, gọi use case và trình bày kết quả.
- `probe` là package importable: sở hữu model cho một lần kiểm tra và không in ra terminal.
- `internal/config` là implementation detail của application: biết target mặc định hôm nay, nhưng không trở thành API công khai mà module khác được hứa hỗ trợ.

![Dependency đi một chiều: command phối hợp config nội bộ và package probe; probe không import ngược command hay config.](../../assets/diagrams/package-boundary-graph.png)

@figure phụ thuộc direction là công cụ review. `cmd/opsprobe` là composition root; nó biết các package cụ thể. `probe` không biết CLI hay cấu hình source nên có thể được đọc, test và thay thế runner mà không kéo presentation theo.

`go.mod` đặt module path, còn mỗi directory Go là một package. Vì lab dùng module `example.com/golang-master/part5-package-design`, import path của package `probe` là `example.com/golang-master/part5-package-design/probe`. Một package có thể gồm nhiều tệp trong cùng directory; chia tệp không tạo thêm boundary nếu chúng vẫn khai báo cùng `package probe`.

~~~text
part5-package-design/
├── go.mod
├── cmd/opsprobe/main.go
├── probe/doc.go
├── probe/check.go
└── internal/cấu hình/cấu hình.go
~~~

Tên `cmd` là convention hữu ích khi repository có thể chứa nhiều executable; bản thân compiler không trao ý nghĩa đặc biệt cho nó. `main.go` cũng chỉ là tên tệp theo convention. Boundary thực sự đến từ package clause, import path và hướng phụ thuộc.

## Export là lời hứa, không phải cách sửa compile error

Trong `probe`, bên gọi cần tạo service, truyền một runner và đọc result. Những khái niệm ấy mới cần export:

~~~go
package probe

type điểm cuối struct { Host string; cổng int }
type Service struct { Name string; điểm cuối điểm cuối }

type Runner func(context.Context, điểm cuối) error
type Result struct { Service string }

func Check(
	ctx context.Context,
	service Service,
	run Runner,
) (Result, error)
~~~

Chữ cái đầu viết hoa không làm type “quan trọng hơn”; nó mở một contract cho package khác. `Check` được export vì command thực sự gọi nó. Helper thêm context error ở bên trong có thể giữ unexported vì chưa có bên gọi nào ngoài `probe` cần nó. Export trước rồi hy vọng một consumer xuất hiện là cách tạo API phải mang gánh nặng tương thích không cần thiết.

Package documentation cũng là một phần của contract. tệp `probe/doc.go` bắt đầu bằng comment `Package probe ...`, nói package chịu trách nhiệm gì và không chịu trách nhiệm gì. Comment của export nên mô tả behavior mà bên gọi có thể dựa vào, không chỉ lặp lại tên type.

## `internal` là boundary do compiler kiểm tra

Target mặc định là policy của application hiện tại. Ta để nó trong `internal/config`:

~~~go
package cấu hình

type Target struct {
	Name string
	Host string
	cổng int
}

func DefaultTargets() []Target {
	return []Target{
		{
			Name: "billing",
			Host: "billing.internal",
			cổng: 8443,
		},
	}
}
~~~

Package ở `internal` không phải “private bằng thỏa thuận”. Go chỉ cho mã nguồn nằm trong cây thư mục của parent import nó. Vì `cmd/opsprobe` nằm dưới module root - parent của `internal` - nó import được `internal/config`. Một module khác import `example.com/golang-master/part5-package-design/internal/config` sẽ bị `go` command từ chối.

Đây không phải lý do để nhét mọi package vào `internal` theo phản xạ. Với binary tự chứa, đó thường là default tốt vì không hứa API ngoài. Với `probe` trong lab này, ta cố tình để nó importable để boundary giữa domain thao tác và CLI được nhìn thấy. Nếu mai kia không còn consumer ngoài application, nó cũng có thể trở thành internal; vị trí phải theo consumer thật, không theo cây thư mục đẹp mắt.

## Composition root chuyển dữ liệu, không giấu phụ thuộc

`config.Target` và `probe.Service` không phải cùng type. Chúng thuộc hai boundary khác nhau: cấu hình nói dữ liệu được khai báo thế nào; probe nói một thao tác cần gì. `cmd/opsprobe` là nơi phù hợp để map giữa chúng:

~~~go
for _, target := range cấu hình.DefaultTargets() {
	service := probe.Service{
		Name: target.Name,
		điểm cuối: probe.điểm cuối{
			Host: target.Host,
			cổng: target.cổng,
		},
	}

	result, err := probe.Check(ctx, service, run)
	if err != nil {
		fmt.Printf("%s: %v\n", service.Name, err)
		continue
	}
	fmt.Printf("%s healthy=true\n", result.Service)
}
~~~

Mapping này trông như boilerplate nhỏ, nhưng nó giữ phụ thuộc direction trung thực: `probe` không cần import cấu hình, cấu hình không cần biết Result, và mã nguồn in terminal không rò vào domain package. Khi source cấu hình chuyển từ default sang tệp hay environment ở chương sau, `probe.Check` không đổi chỉ vì đường đi của cấu hình đã đổi.

## Một refactor có kiểm chứng, không phải một lần dời tệp

Lab kiểm tra ba điều có thể bị hỏng khi tách package:

- `probe.Check` chuyển hủy thực thi thành error có thể nhận diện bằng `errors.Is`, và không chạy runner khi context đã bị cancel.
- Result thành công mang đúng service name.
- `internal/config` trả dữ liệu độc lập theo từng lần gọi; bên gọi sửa slice nhận được không làm thay default của lần sau.

Test cuối không phải để khẳng định “mọi slice đều dangerous”. Nó chứng minh ownership của cấu hình factory: `DefaultTargets` tạo dữ liệu mới cho bên gọi thay vì phát một slice dùng chung. Đây là cùng câu hỏi giá trị semantics của Chương 2, nay được đặt vào một package boundary.

Lần này không bắt đầu từ implementation đã tách. Mở `labs/part5-package-refactor` trong VS mã nguồn: điểm xuất phát là một `main.go` monolithic đang chạy. Chạy `go run .` để giữ behavior làm mốc, rồi chạy `go test -tags exercise ./...`. Lỗi compiler vì package `probe` chưa tồn tại là tín hiệu bắt đầu, không phải lỗi để lờ đi: test đang đòi một public boundary mà mã nguồn chưa có. Từ requirement và test, anh tự quyết định tệp nào đi vào `probe`, tệp nào là `internal/config`, và command map hai model ở đâu. Khi xong, `go run ./cmd/opsprobe` phải giữ output, còn `go test -tags exercise ./...` và `go vet ./...` phải xanh.

---

**Đáp án — chỉ đọc sau khi đã tự làm.** Reference implementation nằm ở `labs/part5-package-design`, nhưng chỉ nên mở sau khi acceptance test đã cho phản hồi đầu tiên. Ranh giới cần giữ là: `probe` export thao tác mà test gọi, `internal/config` giữ policy default và trả slice mới, còn `cmd/opsprobe` là nơi map data rồi in kết quả. Không có lý do để `probe` import ngược cấu hình hoặc terminal.

> **Bài tập - đặt mã nguồn ở đâu?** Một bạn muốn thêm `fmt.Println` vào `probe.Check` để in progress, và muốn `probe` gọi `config.DefaultTargets` để đỡ mapping ở `main`. Với phụ thuộc graph trên, hai thay đổi đó tạo ra rủi ro gì? Đề xuất nơi thay thế cho mỗi việc.

**Đáp án.** `fmt.Println` kéo presentation vào package có thể import; command nên quyết định format và nơi ghi output. Để `probe` gọi cấu hình đảo phụ thuộc từ domain thao tác sang application policy, khiến test probe phải mang cấu hình theo. Progress có thể là result/event do bên gọi trình bày; mapping nên ở command hoặc một application service nằm phía ngoài cả `probe` lẫn cấu hình.

## Một cấu hình source là dữ liệu không tin cậy, không phải điểm cuối

Requirement tiếp theo đến từ người vận hành: trong một lần chạy, họ muốn đổi điểm cuối mặc định mà không sửa source. Ta chọn một biến môi trường có shape rõ ràng: `OPS_PROBE_TARGET=payments.internal:9443`. Đây là capability của application, không phải capability của `probe`. `probe.Check` chỉ nhận `Endpoint` đã hợp lệ; nó không có lý do để biết chuỗi đó đến từ môi trường, tệp hay một flag tương lai.

Điều này giữ một ranh giới quan trọng. Environment luôn đưa vào string; điểm cuối cần host và cổng có ý nghĩa. Việc tách, chuyển kiểu và kiểm tra range là công việc của `internal/config`. Command đưa implementation thật `os.LookupEnv` vào boundary ấy, rồi chỉ nhận `[]Target` hoặc error. Shape của API đủ nhỏ để test mà không đổi environment của máy:

~~~go
type LookupEnv func(string) (string, bool)

func LoadTargets(lookup LookupEnv) ([]Target, error)
~~~

Đây không phải một phụ thuộc-injection framework. `LookupEnv` chỉ là hàm type nói đúng phụ thuộc mà cấu hình cần: với một key, trả giá trị và cho biết key có tồn tại hay không. Trong test, một closure nhỏ thay `os.LookupEnv`; trong command, `os.LookupEnv` thỏa đúng chữ ký hàm. Nhờ vậy test mô tả input rõ ràng mà không có test nào phải sửa environment tiến trình chung.

`host:port` cũng không nên được cắt bằng `strings.Split`. Dấu `:` xuất hiện trong IPv6, nên `net.SplitHostPort` là parser phù hợp cho grammar socket. `payments.internal:9443` là input hợp lệ; IPv6 cần bracket như `[2001:db8::9]:9443`. Sau khi tách, cổng vẫn là text: `strconv.Atoi` chuyển nó thành `int`, rồi cấu hình kiểm tra range `1..65535` trước khi tạo target. Mọi input lỗi trả error có context để CLI in ra và dừng với exit mã nguồn khác 0.

Ở đây không cần sentinel mới. bên gọi hiện chỉ có một policy cho cấu hình lỗi: báo người dùng và dừng trước khi probe bắt đầu. Nếu sau này CLI cần phân biệt lỗi syntax với secret bị thiếu để đưa remediation khác nhau, đó mới là lúc error identity đáng được đưa vào contract. Chương 4 không dạy “mọi error phải có type”; nó dạy chỉ giữ identity khi bên gọi có quyết định khác nhau.

**Thực hành - requirement thay đổi sau refactor.** Sau khi hoàn thành lần tách package đầu tiên trong `labs/part5-package-refactor`, chạy `go test -tags configexercise ./...`. Test đòi `internal/config.LoadTargets` nhận một hàm đọc environment và đổi điểm cuối khi có `OPS_PROBE_TARGET`. Tự chọn tệp, API và error message; constraints là dùng `net.SplitHostPort`, từ chối host rỗng và cổng ngoài `1..65535`, còn `cmd/opsprobe` mới được gọi `os.LookupEnv`. Khi test xanh, chạy command với `OPS_PROBE_TARGET=payments.internal:9443` để kiểm tra đường đi runtime.

---

**Đáp án — chỉ đọc sau khi đã tự làm.** Reference implementation giữ `LoadTargets` trong `internal/config`, bắt đầu từ `DefaultTargets` để ownership của slice không đổi, rồi chỉ override host và cổng của target đầu. Command xử lý error ở tiến trình boundary bằng stderr và exit mã nguồn `2`; `probe` không thay đổi. Đây là dấu hiệu refactor tốt: requirement về source cấu hình đi qua một package, trong khi thao tác kiểm tra điểm cuối không cần biết nguồn dữ liệu vừa đổi.

## mã nguồn review: một field không có trạng thái thứ hai

Sau cấu hình change, ta đọc lại public API thay vì vội thêm feature khác. `Check` có hai outcome: return `error` khi thao tác không hoàn tất, hoặc return `Result` khi runner thành công. Trong contract này, `Result.Healthy` luôn là `true`. Field đó trông vô hại, nhưng nó gợi cho bên gọi một trạng thái thứ hai mà hàm không bao giờ trả về.

Đây là một bug thiết kế, không phải bug compiler. Một bên gọi mới có thể viết `if !result.Healthy { retry() }`, rồi tin rằng branch ấy có ý nghĩa. Thực tế, failure đã đi qua `error`; `result` zero giá trị đi cùng error không phải một observation “unhealthy”. Giữ bool chỉ vì câu in terminal cần chữ `true` làm biên API rộng hơn dữ liệu mà thao tác thực sự cung cấp.

Ta thu hẹp `Result` còn service đã hoàn tất. `cmd/opsprobe` đã có nhánh `err == nil`, nên chính command - nơi sở hữu presentation - in `healthy=true`. Không có information bị mất: success đã là bằng chứng của `true`; failure vẫn là error với context. Đây là một lần refactor đặc biệt đáng làm vì test không đỏ trước khi đổi. Test cũ xanh, nhưng contract cũ làm người đọc có thể suy luận sai.

~~~go
// Result identifies the service whose check
// completed successfully.
type Result struct {
	Service string
}
~~~

Một comment tốt giờ cũng có thể viết chính xác hơn: Result không “chứa health status”, mà định danh service có check thành công. Khi API thật sự cần diễn đạt nhiều trạng thái quan sát - ví dụ healthy, degraded, unreachable với timestamp và latency - đó sẽ là một model khác, được thiết kế cùng requirement và test riêng. Đừng giữ placeholder cho một feature chưa tồn tại chỉ để API trông linh hoạt.

<!-- pagebreak -->

**Thực hành - review dưới ràng buộc.** Trong `labs/part5-package-design`, tạm giữ `Healthy bool` trong `Result` rồi viết ra hai outcome mà `Check` có thể trả. Sau đó bỏ field, sửa test và chỉ sửa presentation ở command cho đến khi `go test ./...` cùng `go run ./cmd/opsprobe` đều xanh. Không được chuyển failure thành `Result{Healthy: false}`: điều đó làm mất error chain mà Chương 4 đã xây. Trong bản refactor độc lập, `public_boundary_test.go` là contract tối thiểu; hãy sửa implementation theo test, không thêm field chỉ để đoán tương lai.

---

**Đáp án — chỉ đọc sau khi đã tự làm.** `Result{Service: service.Name}` là đủ cho nhánh thành công. Sau `err == nil`, command tự in literal `healthy=true`. Nếu một ngày cần health state mà vẫn giữ thao tác failure riêng, API sẽ cần một contract mới nói rõ result nào có thể xuất hiện cùng error nào; đó không phải việc của bool hiện tại.

## Điểm dừng: package đủ nhỏ để thay đổi

Chưa có một “architecture hoàn chỉnh” nào ở đây: chưa parse tệp, chưa dùng generic, chưa tạo package cho từng noun. Ta chỉ có một graph mà mỗi mũi tên trả lời được “vì sao package này cần biết package kia?”. Đó là mức cấu trúc đủ để tiếp tục thay đổi mã nguồn mà không biến mọi thay đổi thành sửa `main`.
