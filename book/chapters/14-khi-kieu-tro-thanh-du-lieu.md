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

`ValueOf(config)` giữ struct value đã copy vào interface; nó không phải variable `config` mà caller có thể gán qua reflection. `ValueOf(&config)` giữ pointer value, và `Elem()` dereference nó để lấy variable struct. `CanSet` không phải một permission system mới: nó cho biết value cụ thể này có addressable và được phép set qua reflection hay không. Nếu nó false, gọi `SetString` sẽ panic. Vì API của ta hứa trả `error` cho input shape sai, guard phải xuất hiện trước setter.

`ApplyEnv(nil, nil)` còn có một bẫy nhỏ hơn. `reflect.ValueOf(nil)` trả zero `reflect.Value`, có `Kind` là `Invalid`; nhiều operation khác trên value không hợp lệ có thể panic. Vì vậy boundary phải kiểm tra `IsValid` trước khi làm các operation phụ thuộc shape. Đây là guard cho một value runtime thực sự không tồn tại, không phải một trường hợp `nil` pointer thông thường.

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

Đoạn dưới là code xấu để review, không phải mẹo cần chép. Nó lấy `Data` từ `reflect.StringHeader` rồi trả `uintptr` ra khỏi scope của string:

~~~go
func badDataAddress(s string) uintptr {
	header := (*reflect.StringHeader)(unsafe.Pointer(&s))
	return header.Data
}
~~~

Trước khi chấp nhận code kiểu này, hãy hỏi: typed pointer nào còn giữ object sống, lifetime proof nằm ở đâu, representation proof nào cho phép dùng header này, và GC còn nhìn thấy reference typed hay chỉ còn một số nguyên? `uintptr` không tự giữ object sống. Package `unsafe` cũng nêu các pattern chuyển đổi pointer hợp lệ rất hẹp; tách conversion ra để giữ địa chỉ lâu hơn không phải cùng một proof. Nếu một use case đòi pointer arithmetic, hãy dừng trước khi viết code và ghi được owner của memory, offset/alignment được chứng minh ở đâu, cùng test trên mọi target hỗ trợ. Không trả lời được chúng thì chưa có lý do dùng `unsafe`.

Chương này không dạy cách “né Go”. Nó dạy một boundary có trách nhiệm khi type chỉ xuất hiện lúc runtime. Reflection có thể giữ code generic nhỏ và thành thật nếu contract về shape, metadata và mutation được viết lộ ra. Khi proof ấy không đủ, quay lại type tĩnh, interface nhỏ hoặc API cụ thể thường là thiết kế tốt hơn.

@references
1. Go Team. Package `reflect`: `Value`, `CanSet`, `Type`, `TypeFor`, `StructField` và `StructTag`. pkg.go.dev/reflect
2. Go Team. Package `unsafe`: `Pointer`, `Sizeof`, `Alignof`, `Offsetof` và quy tắc sử dụng pointer. pkg.go.dev/unsafe
3. Go Team. The Go Programming Language Specification: struct tags, type identity và address operators. go.dev/ref/spec
