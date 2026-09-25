<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Chương 14 — Khi kiểu trở thành dữ liệu

Một function nhận `any` thường tạo hai phản ứng trái ngược. Có người thấy nó “linh hoạt” rồi bắt đầu nhét mọi thứ vào. Có người thấy nó đáng sợ rồi cấm hoàn toàn. Cả hai phản ứng đều bỏ qua câu hỏi quan trọng hơn: khi compiler không còn biết type cụ thể tại chỗ gọi, code nào sẽ kiểm tra shape của value, và code nào được quyền thay đổi nó?

Hãy xét một loader cấu hình nhỏ. `opsprobe` có thể nhận giá trị từ environment, nhưng module đọc environment không nên phải biết trước mọi struct config của các command sau này. Nó nhận một destination và một map giá trị đã đọc; destination quyết định field nào được phép nhận value. Nếu caller truyền `Config{}` thay vì `&Config{}`, loader không được silently tạo bản copy rồi để caller tưởng config đã đổi. Nếu một field có tag nhưng type không phải `string`, loader không được đoán cách parse.

Mental model của chương là: **reflection làm type và value trở thành dữ liệu có thể kiểm tra ở runtime; nó không xóa contract, mà chuyển một phần contract từ compiler sang các guard cụ thể trong code.** `unsafe` nằm ở rìa của mô hình này: nó vượt qua guard của type system, nên chỉ có chỗ khi representation và lifetime đã được chứng minh ở một boundary hẹp.

## Một value có shape mà compiler chưa biết

Trong hàm gọi bình thường, compiler biết `config.Endpoint` là `string`; `config.Endpoint = raw` được kiểm tra trước khi chương trình chạy. Với `func ApplyEnv(dst any, values map[string]string) error`, compiler chỉ biết `dst` là interface value. Dynamic type và dynamic value đi cùng `dst` đến runtime, và `reflect.ValueOf` cho ta một view để hỏi chúng.

~~~go
config := Config{}

value := reflect.ValueOf(config)
fmt.Println(value.Kind())   // struct
fmt.Println(value.CanSet()) // false

pointer := reflect.ValueOf(&config)
target := pointer.Elem()
fmt.Println(target.Kind())   // struct
fmt.Println(target.CanSet()) // true
~~~

Bản chất của `reflect.Value` trong runtime (`src/reflect/value.go`) là một struct gồm ba trường: con trỏ siêu dữ liệu kiểu `typ_ *abi.Type`, con trỏ dữ liệu `ptr_ unsafe.Pointer`, và một trường cờ bit `flag uintptr`:

~~~go
type Value struct {
	typ_ *abi.Type
	ptr_ unsafe.Pointer
	flag
}
~~~

Cờ `flag` chứa thông tin về `Kind`, trạng thái chỉ đọc (`flagStickyRO`, `flagEmbedRO`), và đặc biệt là cờ địa chỉ hóa `flagAddr`. Khi truyền `config` vào `reflect.ValueOf(config)`, biến được đóng gói qua tham số `any`, tạo ra một bản sao giá trị độc lập trên stack hoặc heap; `reflect.Value` được sinh ra không có cờ `flagAddr`, do đó `CanSet()` trả về `false`.

Ngược lại, khi truyền `&config`, `reflect.ValueOf(&config)` lưu con trỏ trỏ tới chính biến `config` gốc. Lệnh `pointer.Elem()` giải tham chiếu con trỏ đó và sinh ra một `reflect.Value` mới được bật cờ `flagAddr`. `CanSet()` chỉ trả về `true` khi cả hai điều kiện cùng thỏa mãn: giá trị có cờ `flagAddr` (tức có ô nhớ gốc xác định để ghi đè) và trường mục tiêu được export công khai.

`ApplyEnv(nil, nil)` còn có một bẫy nhỏ hơn. `reflect.ValueOf(nil)` trả zero `reflect.Value`, có `Kind` là `Invalid`; nhiều operation khác trên value không hợp lệ có thể panic. Vì vậy boundary phải kiểm tra `IsValid` trước khi làm các operation phụ thuộc shape. Đây là guard cho một value runtime thực sự không tồn tại, không phải một trường hợp `nil` pointer thông thường.

| Cơ chế thực thi | Đặc tính điều phối lời gọi | Xu hướng đóng gói và cấp phát | Khả năng Compiler Tối ưu |
| :--- | :--- | :--- | :--- |
| Lời gọi hàm hoặc phương thức tĩnh | Gọi trực tiếp qua địa chỉ cố định đã xác định khi biên dịch | Không phát sinh chi phí bao bọc đối số riêng cho cơ chế gọi | Rộng mở cơ hội inlining triệt tiêu lời gọi, phân bổ thanh ghi SSA |
| Lời gọi gián tiếp qua Interface | Thường cần điều phối gián tiếp tra cứu phương thức qua `itab` | Phụ thuộc vào việc đối tượng cụ thể có thoát lên heap hay không | Trình biên dịch đôi khi có thể devirtualize thành lời gọi tĩnh nếu chứng minh được kiểu cụ thể |
| Lời gọi động qua Reflection (`Value.Call`) | Phải giải mã metadata và kiểm tra kiểu động ở runtime | Cần biểu diễn đối số trong `[]reflect.Value` và boxing giao diện | Rất khó tối ưu hóa tĩnh, hầu như không thể inline và chịu thêm chi phí kiểm tra động |

@table Compiler và reflection chia việc khác nhau

| Câu hỏi | Code có type tĩnh | Code reflection có `any` |
| --- | --- | --- |
| Value có phải `*Config` không? | Compiler đã biết ở call site | Kiểm tra pointer, `nil` và `Elem().Kind()` khi chạy. |
| Field có đúng builtin `string` không? | Compiler kiểm tra assignment | So exact `StructField.Type` với `reflect.TypeFor[string]()`. |
| Có quyền ghi field không? | Quy tắc visibility và addressability của Go | `CanSet` và exported field vẫn giữ ranh giới đó. |
| Sai thì xảy ra khi nào? | Thường compile error | Phải là `error` có context, không phải panic do đoán shape. |

Reflection vì thế không thay generics. Nếu function chỉ cần một operation trên tập type biết trước, type parameter cho compiler giữ contract tốt hơn. Reflection hợp lý khi operation thực sự phụ thuộc vào metadata runtime: serializer, decoder, schema tool, plugin boundary, hoặc loader đọc struct tag. Chính `encoding/json` là ví dụ quen thuộc về API nhận value với shape do runtime quyết định; điều đó không có nghĩa mọi map-to-struct helper trong application đều cần tự viết reflection.

### Interface, generics, reflection và unsafe giải quyết bốn bài toán khác nhau

Interface là abstraction theo behavior: concrete type có thể thay đổi lúc runtime, nhưng compiler vẫn kiểm tra method contract. Generics hay type parameter là abstraction ở compile time trên một tập type có constraint; compiler vẫn biết type information cần thiết cho bài toán phù hợp. Reflection inspect hoặc thao tác `Type` và `Value` ở runtime khi metadata hay shape mới là input. `unsafe` là escape hatch vượt ra ngoài một phần type safety thông thường; nó chỉ có chỗ khi representation và lifetime đã có proof cụ thể. Bốn công cụ có thể cùng xuất hiện trong một codebase, nhưng không phải bốn cách thay thế cho nhau.

## Struct tag là schema nhỏ, không phải comment bí mật

Một struct tag là metadata gắn vào declaration. Compiler lưu nó trong type; `reflect.StructField.Tag.Lookup` có thể đọc nó ở runtime. Tag không tự parse environment hay validate domain. Nó chỉ cho loader biết field nào đã tham gia vào schema này.

~~~go
type Config struct {
	Endpoint string `env:"OPS_PROBE_ENDPOINT"`
	Token    string `env:"OPS_PROBE_TOKEN"`
	Ignored  string `env:"-"`
}
~~~

Hai field export được chọn vì API công khai của loader chỉ được phép ghi phần state mà type đã công khai. `env:"-"` là opt-out có chủ đích. Ngược lại, một field unexported lại khai báo một tag `env` thật là schema lỗi: owner type đang vừa yêu cầu loader tham gia schema, vừa cấm nó ghi. Loader phải trả error thay vì âm thầm bỏ qua hoặc dùng `unsafe` để biến private state thành backdoor.

Đây là implementation tham chiếu của boundary nhỏ. Nó chỉ nhận `string`; parse port, duration, URL hay secret policy thuộc các contract khác, nên không bị giấu sau một helper “tự làm mọi thứ”.

~~~go
var (
	ErrDestination = errors.New(
		"destination must be a non-nil pointer to struct",
	)
	ErrSchema      = errors.New("invalid env schema")
)

type assignment struct {
	field reflect.Value
	raw   string
}

func schemaError(field, rule string) error {
	return fmt.Errorf(
		"%w: env field %s %s",
		ErrSchema,
		field,
		rule,
	)
}
~~~

`ApplyEnv` dùng hai phase. Phase A chỉ đọc metadata và thu thập assignment; phase B mới gọi setter. Nhờ vậy, một field hợp lệ đứng trước field schema lỗi không thể để lại destination nửa mới nửa cũ. Đây là cùng một kỷ luật failure state của Chương 13, nhưng ở boundary runtime-generic thay vì transaction: nếu contract tránh được partial state, `error` phải trả caller về state cũ.

~~~go
func ApplyEnv(dst any, values map[string]string) error {
	value := reflect.ValueOf(dst)
	if !value.IsValid() ||
		value.Kind() != reflect.Pointer ||
		value.IsNil() {
		return ErrDestination
	}
	target := value.Elem()
	if target.Kind() != reflect.Struct {
		return ErrDestination
	}
	typ := target.Type()
	stringType := reflect.TypeFor[string]()
	assignments := make([]assignment, 0, typ.NumField())
	for i := 0; i < typ.NumField(); i++ {
		field := typ.Field(i)
		name, tagged := field.Tag.Lookup("env")
		if !tagged || name == "-" {
			continue
		}
		if !field.IsExported() {
			return schemaError(field.Name, "is unexported")
		}
		if field.Type != stringType {
			return schemaError(field.Name, "must be string")
		}
		fieldValue := target.Field(i)
		if !fieldValue.CanSet() {
			return schemaError(field.Name, "cannot be set")
		}
		if raw, found := values[name]; found {
			assignments = append(assignments, assignment{
				field: fieldValue,
				raw:   raw,
			})
		}
	}
	for _, assignment := range assignments {
		assignment.field.SetString(assignment.raw)
	}
	return nil
}
~~~

`Type` trả lời câu hỏi về declaration: field thứ `i` tên gì, tag gì, exported không, exact type nào. `Kind` chỉ là category underlying runtime kind; vì `type Token string` cũng có `Kind() == reflect.String`, nó không đủ cho contract chỉ nhận builtin `string`. `TypeFor[string]()` cung cấp identity của type cần nhận. `Value` trả lời câu hỏi về instance cụ thể: value hiện tại là gì, có set được không. Quy tắc đơn giản là đọc metadata từ `Type`, đọc hoặc ghi dữ liệu từ `Value`.

> **Dừng để dự đoán:** Nếu caller gọi `ApplyEnv(Config{}, values)`, vì sao function không nên chấp nhận rồi return `nil`? Vì không có đường nào để thay variable của caller. Một `nil` ở đây là lời nói dối: input đã không thỏa quyền mutation mà API cần.

## Lab: viết guard trước setter

`labs/part14-reflection-boundary` bắt đầu bằng test đỏ. Mở `exercise/apply_test.go`, chỉ đọc type `Config` và assertion trước. Tự quyết định thứ tự guard, nhưng đừng dùng `unsafe`, đừng parse tag bằng cắt string thủ công, và đừng panic cho input không đúng shape.

~~~powershell
cd labs/part14-reflection-boundary
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
go test ./fixed
go test -race ./fixed
~~~

Test yêu cầu các boundary dễ nhầm: pointer tới struct được sửa; struct value, nil typed pointer và untyped `nil` bị từ chối; tag `-` không ghi; tagged `int`, named string type, và tagged unexported field đều là schema lỗi. Một schema lỗi sau field hợp lệ vẫn không được partial mutate destination. Nó không yêu cầu loader trở thành framework config.

**Đáp án — chỉ đọc sau khi đã tự làm.** Bắt đầu ở `reflect.ValueOf(dst)`, kiểm tra `IsValid`, `Pointer`, `IsNil` và `Elem().Kind() == Struct` trước. Sau đó iterate field declaration, bỏ tag `-`, từ chối tag thật trên field unexported, so exact type và kiểm tra `CanSet`. Chỉ thu thập assignment ở phase A; phase B mới set chúng. Nhờ vậy malformed schema thành error mà caller có thể xử lý, thay vì panic hoặc partial mutation.

## `unsafe` không phải nút “mở khóa” field private

Khi reflection từ chối ghi `debug`, có thể thấy một mẹo dùng `unsafe.Pointer` để bỏ qua. Đừng làm vậy. Việc field không export là một phần của API và ownership; code generic không biết invariant nào của state private sẽ bị phá khi nó gán text tùy ý.

`unsafe` tồn tại cho một số boundary thật: interop với memory do hệ điều hành hay foreign code quản lý, implementation thấp tầng đã có representation được chỉ định, hoặc primitive mà standard library cung cấp cho việc đó. Nó cho phép operation vượt ra ngoài type safety thông thường, nhưng không biến mọi thứ thành không được định nghĩa. Chỉ được dựa vào guarantee mà specification và package `unsafe` ghi rõ: `unsafe.Sizeof`, `unsafe.Alignof` và `unsafe.Offsetof` đều có semantics được document.

Điều còn lại vẫn đắt: assumption về representation có thể phụ thuộc platform; architecture khác có thể có layout khác; lifetime, GC và pointer rule vẫn phải được chứng minh. Một số đo trên Windows amd64 là measurement của target đó, không phải ABI phổ quát hay lời hứa cho mọi build.

~~~go
type Header struct {
	Flag byte
	ID   uint64
}

fmt.Println(unsafe.Sizeof(Header{}))
fmt.Println(unsafe.Alignof(Header{}))
fmt.Println(unsafe.Offsetof(Header{}.ID))
// Ghi cùng Go version, GOOS và GOARCH của lần đo.
~~~

Đừng suy luận layout của interface, string header, map hay runtime object từ output ấy. Chúng có implementation detail và có thể thay đổi. Lab chạy experiment này bằng test để code được compiler kiểm tra; output log luôn ghi Go version, `GOOS` và `GOARCH`, còn sách không biến một con số local thành fact phổ quát.

### Code review: đừng giữ địa chỉ trong `uintptr`

Đoạn dưới là mã nguồn tiêu cực để phân tích, không phải kỹ thuật nên áp dụng trong thực tế. Nó trích xuất địa chỉ mảng byte nền tảng từ kiểu cũ `reflect.StringHeader` rồi trả về `uintptr` ra ngoài phạm vi chuỗi:

~~~go
func badDataAddress(s string) uintptr {
	header := (*reflect.StringHeader)(unsafe.Pointer(&s))
	return header.Data
}
~~~

Trước khi chấp nhận đoạn mã này, hãy phân tích bản chất cơ chế của Go Runtime:

Thứ nhất, phân biệt rạch ròi giữa việc di dời ngăn xếp (stack movement) và thu gom rác trên heap (heap GC). Bộ thu gom rác của Go là một non-moving collector đối với vùng nhớ heap: các đối tượng sau khi cấp phát trên heap sẽ cố định tại một địa chỉ nhớ cho đến khi bị thu hồi. Tuy nhiên, ngăn xếp của goroutine lại có thể dịch chuyển: khi ngăn xếp phình to (`runtime.morestack`), runtime sẽ cấp phát một vùng nhớ stack mới lớn hơn, sao chép dữ liệu và cập nhật lại toàn bộ các con trỏ trỏ vào stack cũ. Con trỏ `unsafe.Pointer` là thực thể được runtime và GC theo dõi: trên heap, nó giữ cho đối tượng đích không bị giải phóng; trên stack, runtime tự động hiệu chỉnh địa chỉ của nó khi stack di dời.

Thứ hai, `uintptr` chỉ là một kiểu số nguyên không dấu (`uint64` trên kiến trúc 64-bit). Trình thu gom rác coi `uintptr` hoàn toàn là một con số vô tri, không phải là một con trỏ tham chiếu sống. Nếu địa chỉ ô nhớ được gán vào một biến `uintptr` rồi tách rời khỏi con trỏ gốc, GC có thể thu hồi đối tượng trên heap ngay lập tức. Đồng thời, nếu đối tượng từng nằm trên stack, runtime sẽ không cập nhật giá trị số nguyên `uintptr` khi stack di dời, biến nó thành một con số trỏ vào vùng nhớ rác nguy hiểm.

Thứ ba, quy tắc chuẩn hóa của Go quy định số học con trỏ (pointer arithmetic) chỉ được phép xuất hiện trong **một biểu thức hợp thành duy nhất**:

~~~go
p = unsafe.Pointer(uintptr(p) + offset)
~~~

Trình biên dịch nhận diện mẫu hình biểu thức đơn này để bảo đảm đối tượng gốc không bị GC thu hồi trong khoảnh khắc tính toán địa chỉ. Việc tách `uintptr` ra một biến trung gian hoặc trả về từ hàm vi phạm trực tiếp cam kết này.

Thứ tư, hai kiểu `reflect.StringHeader` và `reflect.SliceHeader` đã bị Go chính thức đánh dấu deprecated kể từ Go 1.20 vì chúng khuyến khích việc thao tác sai lệch trên trường `uintptr Data`. Trong Go hiện đại, các thao tác chuyển đổi tầng thấp phải sử dụng các hàm chuẩn mực do package `unsafe` cung cấp:

~~~go
// Trích xuất con trỏ byte nền tảng
ptr := unsafe.StringData(s)

// Tái tạo chuỗi từ con trỏ byte và độ dài
str := unsafe.String(ptr, len(s))

// Lấy con trỏ phần tử đầu của slice
slicePtr := unsafe.SliceData(buf)

// Tạo slice từ con trỏ và độ dài
slice := unsafe.Slice(slicePtr, count)
~~~

Cần lưu ý đặc biệt về vòng đời dữ liệu: các hàm như `unsafe.StringData` và `unsafe.SliceData` chỉ trích xuất địa chỉ byte đầu tiên, chúng **không tự động bảo đảm vòng đời** cho khối dữ liệu bên dưới nếu biến chuỗi hoặc slice gốc bị mất tham chiếu. Lập trình viên có trách nhiệm bảo đảm đối tượng gốc vẫn còn sống (sử dụng `runtime.KeepAlive` khi cần thiết) trong suốt khoảng thời gian con trỏ được sử dụng.

Chương này không dạy cách “né Go”. Nó dạy một boundary có trách nhiệm khi type chỉ xuất hiện lúc runtime. Reflection có thể giữ code generic nhỏ và thành thật nếu contract về shape, metadata và mutation được viết lộ ra. Khi proof ấy không đủ, quay lại type tĩnh, interface nhỏ hoặc API cụ thể thường là thiết kế tốt hơn.

@references
1. Go Team. Package `reflect`: `Value`, `CanSet`, `Type`, `TypeFor`, `StructField` và `StructTag`. pkg.go.dev/reflect
2. Go Team. Package `unsafe`: `Pointer`, `Sizeof`, `Alignof`, `Offsetof`, `String`, `StringData`, `Slice`, `SliceData`. pkg.go.dev/unsafe
3. Go Team. The Go Programming Language Specification: struct tags, type identity và address operators. go.dev/ref/spec
4. Go Team. Go Runtime: Garbage Collection Invariants and Stack Copying. go.dev/doc/gc-guide
