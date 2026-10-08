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

Trong source của Go 1.27.1, `reflect.Value` hiện có các trường nội bộ sau. Chúng chỉ giúp giải thích một quan sát của toolchain này; contract mà code application được dựa vào là các method document như `CanSet`, `Kind` và `Elem`, không phải tên field hay bit flag:

~~~go
type Value struct {
	typ_ *abi.Type
	ptr_ unsafe.Pointer
	flag
}
~~~

Cờ nội bộ hiện giữ thông tin về `Kind`, trạng thái chỉ đọc và addressability. Ở tầng API, điều cần nhớ đơn giản hơn: `reflect.ValueOf(config)` nhận một bản sao value nên không cho phép ghi ngược vào biến của caller; `CanSet()` trả về `false`.

Ngược lại, `reflect.ValueOf(&config).Elem()` nhìn vào variable gốc qua pointer. Với struct field, `CanSet()` còn phụ thuộc việc field có thể được sửa theo quy tắc export/visibility. Đây là guard API cần dùng thay vì suy luận từ flag nội bộ.

`ApplyEnv(nil, nil)` còn có một bẫy nhỏ hơn. `reflect.ValueOf(nil)` trả zero `reflect.Value`, có `Kind` là `Invalid`; nhiều operation khác trên value không hợp lệ có thể panic. Vì vậy boundary phải kiểm tra `IsValid` trước khi làm các operation phụ thuộc shape. Đây là guard cho một value runtime thực sự không tồn tại, không phải một trường hợp `nil` pointer thông thường.

| Cơ chế thực thi | Đặc tính điều phối lời gọi | Xu hướng đóng gói và cấp phát | Khả năng Compiler Tối ưu |
| :--- | :--- | :--- | :--- |
| Lời gọi hàm hoặc phương thức tĩnh | Compiler biết target từ type tĩnh | Không cần cơ chế reflection riêng | Có thể inline hay tối ưu thêm tùy toolchain. |
| Lời gọi qua interface | Target phụ thuộc dynamic type | Representation và allocation là quyết định triển khai | Có thể được devirtualize khi compiler chứng minh được điều kiện; không có bảo đảm. |
| Lời gọi qua reflection (`Value.Call`) | Metadata và kiểm tra động là một phần thao tác | API nhận/trả `reflect.Value` | Thường đắt hơn đường tĩnh; nếu chi phí quan trọng, phải benchmark contract cụ thể. |

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

Đây chỉ là cầu nối để đặt reflection vào đúng ranh giới, chưa phải bài học về tham số kiểu. Chương 19 sẽ bắt đầu lại từ một phép lặp cụ thể, rồi xây type parameter, constraint và cách giữ thông tin kiểu mà không biến mọi API thành `any`. Đến lúc đó, câu hỏi không còn là “reflection có linh hoạt hơn không?”, mà là contract nào compiler vẫn có thể giữ giúp ta.

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

> **Dừng để dự đoán.** Xét tình huống caller gọi hàm với một struct truyền theo giá trị thay vì con trỏ:
> ~~~go
> cfg := Config{}
> err := ApplyEnv(cfg, values)
> ~~~
> 1. Bên trong `ApplyEnv`, phương thức `fieldValue.CanSet()` đối với từng trường của `cfg` sẽ trả về `true` hay `false`?
> 2. Nếu hàm âm thầm bỏ qua và trả về `nil`, biến `cfg` ban đầu của caller có nhận được dữ liệu từ `values` không?
> 3. Vì sao việc trả về `nil` trong tình huống này là một "lời nói dối" nguy hiểm của API, và tại sao kiểm tra `value.Kind() != reflect.Pointer` là ranh giới phòng vệ bắt buộc?

#### Đáp án — chỉ đọc sau khi đã tự làm
1. **`fieldValue.CanSet()` trả về `false`** vì khi truyền struct theo giá trị (by-value), hàm chỉ nhận một bản sao (copy) trên stack. Bản sao này không có địa chỉ bộ nhớ gắn liền với biến gốc của caller (unaddressable). Gói `reflect` nghiêm cấm việc ghi đè lên một `reflect.Value` không thể gán; nếu cố tình gọi `SetString()`, runtime sẽ lập tức gây panic.
2. **Biến `cfg` ban đầu hoàn toàn không thay đổi.** Mọi đột biến dữ liệu (nếu cố tình làm) cũng chỉ diễn ra trên bản sao tạm thời rồi biến mất khi hàm return.
3. **Trả về `nil` là một thiết kế API độc hại:** Nó báo thành công giả tạo, khiến ứng dụng tiếp tục vận hành với cấu hình rỗng và gây sự cố ngầm. Ranh giới guard clause kiểm tra `value.Kind() != reflect.Pointer` và con trỏ không nil ở đầu hàm là điều kiện bắt buộc nhằm từ chối sớm (fail-fast) mọi input không đáp ứng quyền ghi (mutation capability).

## Thực hành: viết kiểm tra bảo vệ trước khi gán giá trị (setter)

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

Thứ nhất, phân biệt rạch ròi giữa việc di dời ngăn xếp (stack movement) và thu gom rác trên heap (heap GC). Go runtime hiện tại dùng heap non-moving và có thể copy stack khi stack goroutine lớn lên; đó là implementation detail, không phải permission để giữ địa chỉ theo ý mình. Một `unsafe.Pointer` vẫn được GC nhận diện là pointer trong những pattern mà package `unsafe` cho phép; hãy chỉ dựa vào các conversion được tài liệu hóa.

Thứ hai, `uintptr` là số nguyên đủ lớn để chứa bit của địa chỉ trên kiến trúc đang chạy, không phải một tham chiếu sống. Nếu tách địa chỉ khỏi `unsafe.Pointer` gốc và giữ nó trong `uintptr`, GC không có reason để coi số đó là giữ object sống; stack growth cũng không thể sửa một số nguyên đã chép. Vì vậy object có thể bị thu hồi khi liveness của pointer gốc kết thúc, còn địa chỉ stack có thể trở nên stale.

Thứ ba, với pattern chuyển pointer qua `uintptr` để cộng offset rồi chuyển ngược, tài liệu `unsafe.Pointer` yêu cầu conversion và phép tính nằm trong **cùng một biểu thức**:

~~~go
p = unsafe.Pointer(uintptr(p) + offset)
~~~

Pattern một biểu thức còn phải giữ pointer trong cùng object đã cấp phát và trỏ tới dữ liệu hợp lệ theo contract `unsafe`; nó không cho phép tính một địa chỉ tùy ý. Tách địa chỉ qua `uintptr` trung gian không được hợp thức hóa chỉ bằng `KeepAlive`. Các mô tả runtime và ví dụ ở đây được kiểm tra trong bối cảnh Go 1.27.1; chỉ conversion pattern được package công bố mới là phần caller nên dựa vào.

Trong API Go 1.27.1, `reflect.StringHeader` và `reflect.SliceHeader` được đánh dấu deprecated; tài liệu cảnh báo trường `Data uintptr` không đủ giữ dữ liệu sống và representation không dùng an toàn hay portable. Khi thực sự cần boundary tầng thấp, đọc contract của các helper `unsafe` thay vì tự dựng header; helper vẫn không miễn yêu cầu về lifetime và mutation:

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

Cần giữ contract về vòng đời và mutation: pointer Go hợp lệ được GC theo dõi, khác với một địa chỉ đã biến thành số nguyên. `unsafe.String` không cho phép sửa các byte nền trong khi string còn được sử dụng. `runtime.KeepAlive` có vai trò ở những boundary như resource có finalizer mà OS chỉ còn nhìn thấy descriptor; nó không hợp thức hóa conversion ngoài các pattern của `unsafe`, không pin memory và không sửa một địa chỉ `uintptr` đã stale.

## Biên giới với C là một hợp đồng khác

Reflection vẫn hoạt động trong hệ kiểu Go. Khi library chỉ có C ABI, cgo đưa chương trình qua một boundary khác: representation, lifetime, allocator và toolchain của hai phía đều cần được đọc. Một string Go có độ dài và có thể chứa byte NUL; `strlen` của C dừng ở NUL đầu tiên. Hai phép “đo độ dài” không cùng contract.

Lab `labs/edition-contracts/interop` có một hàm nhỏ dùng `C.CString`, gọi `C.strlen`, rồi `C.free` vùng nhớ đã cấp phát. Test đòi `"a\x00b"` có kết quả 1 ở phía C, không phải `len` của string Go. Đừng biến phép thử này thành khuyến nghị chuyển parser sang C: nó chỉ làm lộ một khác biệt dữ liệu. Byte không có NUL cuối, string Unicode và C string cần chính sách chuyển đổi cụ thể; “cùng là text” chưa đủ.

Memory do `C.CString` cấp phát cần được giải phóng theo allocator C; GC Go không tự thu hồi nó. Với pointer Go truyền sang C, tài liệu cgo quy định vùng memory được phép trỏ tới, pinning và thời gian C có thể giữ pointer. Không suy luận rằng thấy một địa chỉ hợp lệ lúc gọi là được lưu nó vô hạn ở C. `runtime.Pinner` và `runtime/cgo.Handle` giải quyết những trường hợp khác nhau; Handle là định danh để giữ giá trị Go, không phải permission cho C giải tham chiếu tùy ý. Chỉ dùng sau khi đã thiết kế lifecycle và đọc contract tương ứng.

cgo còn thay deployment contract: build cần C compiler phù hợp, binary có thể phụ thuộc native library, cross-compilation cần toolchain target. Memory native không nằm trọn trong heap budget Go và crash native có thể vượt khỏi error path mà caller Go kiểm soát. Không có một số nanosecond crossing phổ quát: nếu boundary là hot path, đo đúng payload, tần suất và môi trường, rồi xem có thể gom nhiều operation thành một lượt gọi không. Go thuần thường đơn giản hơn cho tooling tự chứa; C hợp lý khi cần API, driver hoặc implementation đã được kiểm chứng mà việc viết lại tạo rủi ro lớn hơn chi phí interop.

Chương này không dạy cách “né Go”. Nó dạy một boundary có trách nhiệm khi type chỉ xuất hiện lúc runtime. Reflection có thể giữ code generic nhỏ và thành thật nếu contract về shape, metadata và mutation được viết lộ ra. Khi proof ấy không đủ, quay lại type tĩnh, interface nhỏ hoặc API cụ thể thường là thiết kế tốt hơn.

@references
1. Go Team. Package `reflect`: `Value`, `CanSet`, `Type`, `TypeFor`, `StructField` và `StructTag`. pkg.go.dev/reflect
2. Go Team. Package `unsafe`: `Pointer`, `Sizeof`, `Alignof`, `Offsetof`, `String`, `StringData`, `Slice`, `SliceData`. pkg.go.dev/unsafe
3. Go Team. The Go Programming Language Specification: struct tags, type identity và address operators. go.dev/ref/spec
4. Go Team. A Guide to the Go Garbage Collector. go.dev/doc/gc-guide; cơ chế sao chép stack đối chiếu riêng với `src/runtime/stack.go` của Go 1.27.1, không phải contract của ngôn ngữ.
5. Go Team. `cmd/cgo`, Passing pointers; `runtime.Pinner`; `runtime/cgo.Handle`. Contract kiểm tra với Go 1.27.1. pkg.go.dev/cmd/cgo
