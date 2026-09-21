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

`ValueOf(config)` giữ struct value đã copy vào interface; nó không phải variable `config` mà caller có thể gán qua reflection. `ValueOf(&config)` giữ pointer value, và `Elem()` dereference nó để lấy variable struct. `CanSet` không phải detail để bỏ qua: gọi `SetString` khi nó false sẽ panic. Vì API của ta hứa trả `error` cho input shape sai, guard phải xuất hiện trước setter.

@table Compiler và reflection chia việc khác nhau

| Câu hỏi | Code có type tĩnh | Code reflection có `any` |
| --- | --- | --- |
| Value có phải `*Config` không? | Compiler đã biết ở call site | Kiểm tra pointer, `nil` và `Elem().Kind()` khi chạy. |
| Field có phải `string` không? | Compiler kiểm tra assignment | Kiểm tra `StructField.Type.Kind()` trước `SetString`. |
| Có quyền ghi field không? | Quy tắc visibility và addressability của Go | `CanSet` và exported field vẫn giữ ranh giới đó. |
| Sai thì xảy ra khi nào? | Thường compile error | Phải là `error` có context, không phải panic do đoán shape. |

Reflection vì thế không thay generics. Nếu function chỉ cần một operation trên tập type biết trước, type parameter cho compiler giữ contract tốt hơn. Reflection hợp lý khi operation thực sự phụ thuộc vào metadata runtime: serializer, decoder, schema tool, plugin boundary, hoặc loader đọc struct tag. Chính `encoding/json` là ví dụ quen thuộc về API nhận value với shape do runtime quyết định; điều đó không có nghĩa mọi map-to-struct helper trong application đều cần tự viết reflection.

## Struct tag là schema nhỏ, không phải comment bí mật

Một struct tag là metadata gắn vào declaration. Compiler lưu nó trong type; `reflect.StructField.Tag.Lookup` có thể đọc nó ở runtime. Tag không tự parse environment hay validate domain. Nó chỉ cho loader biết field nào đã tham gia vào schema này.

~~~go
type Config struct {
	Endpoint string `env:"OPS_PROBE_ENDPOINT"`
	Token    string `env:"OPS_PROBE_TOKEN"`
	debug    string `env:"OPS_PROBE_DEBUG"`
}
~~~

Hai field export được chọn vì API công khai của loader chỉ được phép ghi phần state mà type đã công khai. `debug` có tag nhưng vẫn unexported; cố cố tình đi vòng qua bằng reflection hay `unsafe` sẽ biến private state thành một backdoor. Trong design này, đó là lỗi schema của owner type, không phải lý do để loader phá visibility.

Đây là implementation tham chiếu của boundary nhỏ. Nó chỉ nhận `string`; parse port, duration, URL hay secret policy thuộc các contract khác, nên không bị giấu sau một helper “tự làm mọi thứ”.

~~~go
var ErrDestination = errors.New(
	"destination must be a non-nil pointer to struct",
)

func ApplyEnv(dst any, values map[string]string) error {
	value := reflect.ValueOf(dst)
	if value.Kind() != reflect.Pointer || value.IsNil() ||
		value.Elem().Kind() != reflect.Struct {
		return ErrDestination
	}

	target := value.Elem()
	typ := target.Type()
	for i := 0; i < typ.NumField(); i++ {
		field := typ.Field(i)
		name, ok := field.Tag.Lookup("env")
		if !ok || name == "-" || !field.IsExported() {
			continue
		}
		raw, found := values[name]
		if !found {
			continue
		}
		if field.Type.Kind() != reflect.String {
			return fmt.Errorf(
				"env field %s must be string",
				field.Name,
			)
		}
		fieldValue := target.Field(i)
		if !fieldValue.CanSet() {
			return fmt.Errorf(
				"env field %s cannot be set",
				field.Name,
			)
		}
		fieldValue.SetString(raw)
	}
	return nil
}
~~~

`Type` trả lời câu hỏi về declaration: field thứ `i` tên gì, tag gì, exported không, type nào. `Value` trả lời câu hỏi về instance cụ thể: value hiện tại là gì, có set được không. Trộn hai vai này là nguồn gốc của nhiều code reflection khó đọc. Quy tắc đơn giản là đọc metadata từ `Type`, đọc hoặc ghi dữ liệu từ `Value`.

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

Test yêu cầu ba điều dễ nhầm: pointer tới struct được sửa; struct value và nil pointer bị từ chối; field export có tag nhưng type `int` bị từ chối thay vì nhận text rồi để zero value lặng lẽ đi xa hơn. Nó không yêu cầu loader trở thành framework config. Khi xanh, hãy so với `fixed/`, rồi thử bỏ `field.IsExported()` để thấy đây không phải một permission mà reflection tự cấp.

**Đáp án — chỉ đọc sau khi đã tự làm.** Bắt đầu ở `reflect.ValueOf(dst)`, kiểm tra `Pointer`, `IsNil` và `Elem().Kind() == Struct` trước. Sau đó iterate field declaration, chọn tag có mặt, bỏ tag `-` và field không export, kiểm tra type, rồi mới lấy `target.Field(i)` và gọi setter. Guard đi trước setter làm panic do malformed input trở thành error mà caller có thể xử lý.

## `unsafe` không phải nút “mở khóa” field private

Khi reflection từ chối ghi `debug`, có thể thấy một mẹo dùng `unsafe.Pointer` để bỏ qua. Đừng làm vậy. Việc field không export là một phần của API và ownership; code generic không biết invariant nào của state private sẽ bị phá khi nó gán text tùy ý.

`unsafe` tồn tại cho một số boundary thật: interop với memory do hệ điều hành hay foreign code quản lý, implementation thấp tầng đã có representation được chỉ định, hoặc primitive mà standard library cung cấp cho việc đó. Đổi lại, compiler không còn bảo đảm type, offset, alignment, lifetime hay khả năng portable theo architecture cho anh. `unsafe.Sizeof` có thể hữu ích để *đo* một layout trong build hiện tại, nhưng một số đo trên Windows amd64 không phải hằng số thiết kế cho mọi architecture.

~~~go
fmt.Println(unsafe.Sizeof(Header{}))
// Chỉ là số đo của Header trên target build này.
~~~

Đừng suy luận layout của interface, string header, map hay runtime object từ output ấy. Chúng có implementation detail và có thể thay đổi; đặc biệt đừng dựng `reflect.StringHeader` hoặc `SliceHeader` để tạo aliasing nhanh. Nếu một use case đòi pointer arithmetic, hãy dừng trước khi viết code và ghi được bốn điều: memory do ai sở hữu, object được giữ sống bằng reference typed nào, offset/alignment được chứng minh ở đâu, và test nào chạy trên mọi target được hỗ trợ. Không trả lời được chúng thì chưa có lý do dùng `unsafe`.

Chương này không dạy cách “né Go”. Nó dạy một boundary có trách nhiệm khi type chỉ xuất hiện lúc runtime. Reflection có thể giữ code generic nhỏ và thành thật nếu contract về shape, metadata và mutation được viết lộ ra. Khi proof ấy không đủ, quay lại type tĩnh, interface nhỏ hoặc API cụ thể thường là thiết kế tốt hơn.

@references
1. Go Team. Package `reflect`: `Value`, `CanSet`, `Type`, `StructField` và `StructTag`. pkg.go.dev/reflect
2. Go Team. Package `unsafe`: phạm vi API và quy tắc sử dụng pointer. pkg.go.dev/unsafe
3. Go Team. The Go Programming Language Specification: struct tags, representation of values và address operators. go.dev/ref/spec
