<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Chương 14 — Khi kiểu trở thành dữ liệu

Một hàm nhận `any` có thể tiếp nhận nhiều kiểu cụ thể, nhưng chữ ký ấy không cho phần thân hàm biết đích có phải con trỏ tới cấu trúc cấu hình hay không. Trình biên dịch vẫn kiểm tra biểu thức ở nơi gọi; điều còn thiếu là hợp đồng hẹp hơn bên trong hàm. Đoạn mã nào sẽ kiểm tra hình thái của giá trị, và đoạn mã nào được trao quyền thay đổi giá trị đó?

Hãy xét một bộ tải cấu hình nhỏ. Ứng dụng `opsprobe` có thể tiếp nhận giá trị từ các biến môi trường, nhưng mô-đun đọc môi trường không nên phụ thuộc hay biết trước mọi cấu trúc cấu hình của từng lệnh con sau này. Bộ tải tiếp nhận một đích đến (*destination*) cùng một bảng ánh xạ các giá trị đã đọc; đối tượng đích quyết định trường dữ liệu nào được phép nhận giá trị. Nếu bên gọi truyền `Config{}` theo dạng giá trị thay vì con trỏ `&Config{}`, bộ tải không được phép âm thầm tạo bản sao rồi khiến bên gọi ngộ nhận cấu hình đã được áp dụng. Nếu một trường có gắn thẻ dữ liệu (*struct tag*) nhưng kiểu dữ liệu không phải `string`, bộ tải không được tùy tiện suy đoán cách phân tích cú pháp.

Mô hình tư duy của chương là: cơ chế soi chiếu (*reflection*) biến kiểu dữ liệu và giá trị thành các đối tượng dữ liệu có thể khảo sát tại thời gian chạy (*runtime*); cơ chế này không hề xóa bỏ hợp đồng hành vi, mà chuyển giao một phần việc thực thi hợp đồng từ trình biên dịch sang các khối kiểm tra phòng vệ (*guard clauses*) tường minh trong mã nguồn. Gói `unsafe` nằm ở rìa của mô hình này: nó vượt qua các chốt chặn an toàn của hệ thống kiểu dữ liệu, vì vậy chỉ có chỗ đứng khi biểu diễn bộ nhớ và vòng đời dữ liệu đã được chứng minh chặt chẽ tại một ranh giới cục bộ hẹp.

## Một value có shape mà compiler chưa biết

Trong lời gọi hàm tĩnh thông thường, trình biên dịch nhận biết rõ `config.Endpoint` mang kiểu `string`; thao tác gán `config.Endpoint = raw` được kiểm tra tính hợp lệ trước khi chương trình khởi chạy. Tuy nhiên với hàm `func ApplyEnv(dst any, values map[string]string) error`, trình biên dịch chỉ biết đối số `dst` là một giá trị giao diện (*interface value*). Kiểu động (*dynamic type*) và giá trị động (*dynamic value*) đi cùng `dst` tới thời gian chạy, và hàm `reflect.ValueOf` cung cấp một góc nhìn phản chiếu để ta truy vấn thông tin của chúng.

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

Trong mã nguồn của Go 1.27.1, cấu trúc `reflect.Value` hiện chứa các trường nội bộ sau. Chúng chỉ nhằm làm sáng tỏ một quan sát cơ chế của chuỗi công cụ; hợp đồng mà mã ứng dụng được phép dựa vào là các phương thức đã công bố trong tài liệu chuẩn như `CanSet`, `Kind` và `Elem`, tuyệt đối không phải tên trường hay các cờ bit nội bộ:

~~~go
type Value struct {
	typ_ *abi.Type
	ptr unsafe.Pointer
	flag
}
~~~

Cờ nội bộ hiện lưu giữ thông tin về danh mục loại kiểu `Kind`, trạng thái chỉ đọc và khả năng định vị địa chỉ bộ nhớ (*addressability*). Ở tầng giao diện lập trình, điều cần ghi nhớ rất rõ ràng: hàm `reflect.ValueOf(config)` tiếp nhận một bản sao giá trị nên không cho phép ghi đè ngược lại vào biến của bên gọi; phương thức `CanSet()` vì thế trả về `false`.

Ngược lại, biểu thức `reflect.ValueOf(&config).Elem()` quan sát biến gốc thông qua con trỏ. Đối với trường cấu trúc, phương thức `CanSet()` còn phụ thuộc vào việc trường đó có thể chỉnh sửa theo quy tắc hiển thị công khai (*exported*) hay không. Đây là chốt chặn phòng vệ cấp giao diện cần sử dụng thay vì suy diễn từ các cờ bit nội bộ.

`CanAddr` và `CanSet` trả lời hai câu hỏi khác nhau. Một trường không công khai lấy từ `reflect.ValueOf(&config).Elem()` có thể có địa chỉ nhưng vẫn không được gán hoặc lấy ra qua `Interface`. Ngược lại, việc sao chép giá trị vào interface không sao chép sâu dữ liệu mà giá trị ấy tham chiếu: `reflect.ValueOf(slice).CanSet()` là `false`, nhưng phần tử của slice vẫn có thể được gán qua `Index`. Trực giác đúng là xét quyền của từng `Value`, không suy rằng mọi dữ liệu nằm sau `any` đều là bản sao độc lập.

Lời gọi `ApplyEnv(nil, nil)` còn tiềm ẩn một cạm bẫy khác. Biểu thức `reflect.ValueOf(nil)` trả về giá trị rỗng của `reflect.Value`, có loại kiểu `Kind()` là `Invalid`; nhiều thao tác tiếp theo trên một giá trị không hợp lệ sẽ gây sập tiến trình (`panic`). Do đó, ranh giới xử lý bắt buộc phải kiểm tra phương thức `IsValid()` trước khi thực hiện các phép toán phụ thuộc hình thái. Đây là chốt chặn phòng vệ cho một giá trị thời gian chạy thực sự không tồn tại, không phải trường hợp con trỏ `nil` thông thường.

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

Reflection vì thế không thể thay thế cho kiểu chung (*generics*). Nếu một hàm chỉ cần thực thi một thao tác trên tập hợp các kiểu dữ liệu đã xác định từ trước, tham số kiểu (*type parameter*) sẽ giúp trình biên dịch duy trì hợp đồng tĩnh một cách hiệu quả hơn. Cơ chế soi chiếu chỉ thực sự hợp lý khi thao tác phụ thuộc hoàn toàn vào siêu dữ liệu (*metadata*) tại thời gian chạy: các bộ tuần tự hóa (*serializer*), giải mã (*decoder*), công cụ quản lý lược đồ dữ liệu, ranh giới phần mở rộng (*plugin*), hoặc bộ nạp đọc thẻ cấu trúc. Chính gói `encoding/json` là minh chứng quen thuộc về giao diện lập trình tiếp nhận giá trị có hình thái do thời gian chạy quyết định; tuy nhiên điều đó không đồng nghĩa với việc mọi tiện ích chuyển đổi trong ứng dụng đều nên tự viết bằng reflection.

### Interface, generics, reflection và unsafe giải quyết bốn bài toán khác nhau

Giao diện (*interface*) là cơ chế trừu tượng hóa theo hành vi: kiểu cụ thể (*concrete type*) có thể thay đổi linh hoạt lúc chạy, nhưng trình biên dịch vẫn kiểm tra chặt chẽ hợp đồng phương thức. Tham số kiểu (*generics*) là cơ chế trừu tượng hóa tại thời điểm biên dịch dựa trên tập hợp kiểu có ràng buộc (*constraints*); trình biên dịch vẫn nắm bắt đầy đủ thông tin kiểu cần thiết để tối ưu hóa. Cơ chế soi chiếu (*reflection*) khảo sát hoặc thao tác trên `Type` và `Value` tại thời gian chạy khi siêu dữ liệu hay hình thái động là đầu vào. Gói `unsafe` là lối thoát hiểm vượt ra ngoài phạm vi an toàn kiểu thông thường; công cụ này chỉ có chỗ đứng khi cách thức biểu diễn bộ nhớ và vòng đời dữ liệu đã có bằng chứng xác minh cụ thể. Bốn công cụ có thể cùng hiện diện trong một dự án, nhưng không phải là bốn phương án có thể hoán đổi tùy tiện cho nhau.

Đây chỉ là cầu nối nhằm định vị cơ chế soi chiếu vào đúng ranh giới trách nhiệm, chưa phải trọng tâm phân tích về tham số kiểu. Chương 19 sẽ bắt đầu lại từ một bài toán lặp cụ thể, sau đó xây dựng tham số kiểu, ràng buộc kiểu và phương thức bảo toàn thông tin kiểu mà không biến mọi giao diện lập trình thành `any`. Khi đó, câu hỏi không còn là việc soi chiếu có linh hoạt hơn hay không, mà là hợp đồng nào trình biên dịch vẫn có thể bảo đảm giúp ta.

## Struct tag là schema nhỏ, không phải comment bí mật

Thẻ cấu trúc (*struct tag*) là siêu dữ liệu gắn liền với phần khai báo trường dữ liệu. Trình biên dịch lưu trữ thông tin này trong mô tả kiểu; phương thức `reflect.StructField.Tag.Lookup` có thể đọc giá trị thẻ tại thời gian chạy. Thẻ dữ liệu không tự phân tích biến môi trường hay kiểm tra tính hợp lệ của miền nghiệp vụ. Nó chỉ cung cấp chỉ dẫn cho bộ tải biết trường nào tham gia vào lược đồ cấu hình này.

~~~go
type Config struct {
	Endpoint string `env:"OPS_PROBE_ENDPOINT"`
	Token    string `env:"OPS_PROBE_TOKEN"`
	Ignored  string `env:"-"`
}
~~~

Hai trường công khai (*exported*) được lựa chọn vì giao diện của bộ nạp chỉ được phép ghi vào phần trạng thái mà kiểu dữ liệu đã chủ động công khai. Giá trị thẻ `env:"-"` là cơ chế từ chối tham gia có chủ đích. Ngược lại, một trường nội bộ (*unexported*) lại khai báo một thẻ `env` thực sự sẽ bị xem là lỗi lược đồ: kiểu dữ liệu sở hữu vừa yêu cầu bộ nạp tham gia lược đồ, lại vừa cấm quyền ghi dữ liệu. Bộ nạp bắt buộc phải trả về lỗi tường minh thay vì âm thầm bỏ qua hoặc lạm dụng `unsafe` để biến trạng thái riêng tư thành cửa sau trái phép.

Đây là mã triển khai tham chiếu cho một ranh giới xử lý thu gọn. Hàm chỉ tiếp nhận dữ liệu chuỗi `string`; việc phân tích cổng mạng (*port*), khoảng thời gian (*duration*), địa chỉ URL hay chính sách bảo mật khóa bí mật thuộc về các hợp đồng chuyên biệt khác, không bị giấu sau một hàm tiện ích tự làm mọi việc.

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

`ApplyEnv` đọc lược đồ và thu thập phép gán trước, sau đó mới ghi vào đích. Trường hợp lệ đứng trước trường sai vì thế không bị cập nhật nếu hàm trả lỗi lược đồ. Cam kết này chỉ dành cho lỗi mà helper kiểm tra; các lệnh gán vẫn diễn ra tuần tự, không phải giao dịch nguyên tử đối với người đọc đồng thời. Bên gọi phải sở hữu đích và giữ map đầu vào ổn định trong lượt gọi, hoặc thiết kế đồng bộ riêng theo Ch08. Reflection không tự thêm khóa hay rollback khi chương trình bị dừng.

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

Đối tượng `Type` giải đáp câu hỏi về phần khai báo: trường thứ `i` có tên là gì, mang thẻ dữ liệu nào, có được công khai hay không, và thuộc chính xác kiểu dữ liệu nào. Phương thức `Kind` chỉ phản ánh danh mục loại kiểu nền tảng tại thời gian chạy; vì một kiểu định danh như `type Token string` vẫn có `Kind() == reflect.String`, nó không đủ chặt chẽ cho một hợp đồng chỉ chấp nhận kiểu nguyên thủy `string`. Lời gọi `TypeFor[string]()` cung cấp định danh chính xác của kiểu dữ liệu cần tiếp nhận. Đối tượng `Value` giải đáp câu hỏi về thể hiện thực tế: giá trị hiện tại là gì và có quyền gán giá trị hay không. Quy tắc nhất quán là: đọc siêu dữ liệu từ `Type`, và đọc hoặc biến đổi dữ liệu thực thông qua `Value`.

Helper kiểm tra mọi trường có thẻ tham gia, kể cả khi map không chứa giá trị cho trường ấy. Nó chỉ duyệt trường trực tiếp, không tự đi sâu vào cấu trúc nhúng. Alias như `type Token = string` vẫn là chính kiểu `string` và được chấp nhận, khác với định nghĩa `type Token string`. Các thẻ phải có định dạng chuẩn: `StructTag.Lookup` không là bộ kiểm tra cú pháp, và tài liệu không quy định kết quả cho thẻ sai định dạng. Chạy `go vet` để tìm lỗi thẻ khai báo; đừng đọc cam kết “lỗi lược đồ” của helper thành cam kết phát hiện mọi lỗi văn bản trong tag.

> **Dừng để dự đoán:** Nếu caller gọi `cfg := Config{}` rồi thực hiện `ApplyEnv(cfg, values)` bằng giá trị thay vì truyền con trỏ `&cfg`, liệu hàm có thể cập nhật các trường cấu hình không? Vì sao implementation của `ApplyEnv` chặn lỗi ngay từ guard kiểm tra con trỏ ở đầu hàm thay vì duyệt qua từng field rồi kiểm tra `CanSet()`?

#### Gợi ý giải pháp (chỉ đọc sau khi đã tự làm)
Khi truyền struct bằng giá trị vào đối số interface `any`, giá trị được đóng gói thành một bản sao không có địa chỉ liên kết với biến gốc (unaddressable). Đối tượng `reflect.ValueOf(dst)` sinh ra từ một giá trị như vậy đại diện cho một bản sao độc lập, và phương thức `CanSet()` trên các trường của nó luôn trả về `false`. Nếu cố tình gọi `SetString()` lên một `reflect.Value` không có quyền gán, runtime sẽ lập tức gây `panic`. Kể cả khi hàm cố tình bỏ qua mà không `panic`, biến `cfg` ban đầu của caller cũng hoàn toàn không nhận được dữ liệu mới, biến giá trị trả về `nil` thành một tín hiệu thành công giả tạo.

Trong cài đặt thực tế của `ApplyEnv`, ta không đợi đến lúc duyệt từng trường mới kiểm tra `CanSet()`. Guard clause ở ngay đầu hàm kiểm tra trực tiếp `value.Kind() != reflect.Pointer` cùng điều kiện con trỏ không `nil` và trả về `ErrDestination` ngay lập tức. Đây là ranh giới phòng vệ fail-fast: một khi đích đến không phải là con trỏ tham chiếu tới vùng nhớ có quyền đột biến, hàm từ chối dứt khoát toàn bộ thao tác trước khi tốn chi phí duyệt metadata của struct.

### Bài thực hành: Viết kiểm tra bảo vệ trước khi gán giá trị (*setter*)

Thực hành tại `labs/part14-reflection-boundary` bắt đầu bằng kịch bản kiểm thử không đạt. Hãy mở `exercise/apply_test.go`, chỉ đọc định nghĩa kiểu `Config` và các câu lệnh khẳng định (*assertion*) trước. Hãy tự quyết định thứ tự các điều kiện phòng vệ, nhưng tuyệt đối không dùng `unsafe`, không phân tích thẻ dữ liệu bằng cách cắt chuỗi thủ công, và không gây dừng đột ngột (`panic`) khi dữ liệu đầu vào sai lệch hình thái.

~~~powershell
cd labs/part14-reflection-boundary
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
go test ./fixed
go test -race ./fixed
~~~

Bộ kiểm thử đòi hỏi xử lý chuẩn xác các ranh giới dễ gây nhầm lẫn: con trỏ tham chiếu tới cấu trúc được phép cập nhật; biến cấu trúc dạng giá trị, con trỏ mang kiểu nhưng có giá trị `nil`, và giá trị `nil` không định kiểu đều phải bị từ chối; thẻ mang giá trị `-` không được ghi; trường kiểu `int`, kiểu chuỗi có định danh riêng, hoặc trường nội bộ có gắn thẻ đều bị coi là lỗi lược đồ. Một lỗi lược đồ phát hiện sau các trường hợp lệ vẫn không được phép làm biến đổi cục bộ đối tượng đích. Yêu cầu đặt ra không đòi hỏi bộ nạp phải trở thành một khung cấu hình phức tạp.

---

#### Gợi ý giải pháp (chỉ đọc sau khi đã tự làm)

Bắt đầu từ `reflect.ValueOf(dst)`, kiểm tra tuần tự các điều kiện `IsValid`, kiểm tra con trỏ `Pointer`, con trỏ rỗng `IsNil` và kiểm tra đối tượng trỏ tới là cấu trúc `Elem().Kind() == reflect.Struct`. Tiếp theo, duyệt qua từng khai báo trường, bỏ qua thẻ `-`, từ chối thẻ thực trên trường nội bộ, so sánh chính xác kiểu dữ liệu và kiểm tra quyền gán `CanSet`. Chỉ thu thập danh sách phép gán trong giai đoạn A; sang giai đoạn B mới áp dụng các phép gán đó. Nhờ vậy, lược đồ sai định dạng sẽ trở thành lỗi có thể xử lý ở bên gọi thay vì gây sập chương trình hoặc làm biến đổi dở dang dữ liệu.

## `unsafe` không phải nút “mở khóa” field private

Khi cơ chế soi chiếu từ chối ghi dữ liệu vào trường `debug`, một số lập trình viên có thể tìm cách dùng `unsafe.Pointer` để vượt qua ranh giới bảo vệ. Tuyệt đối không làm như vậy. Việc trường dữ liệu không được công khai là một phần của hợp đồng giao diện và quyền sở hữu; mã nguồn generic không thể lường trước bất biến nào của trạng thái riêng tư (*private state*) sẽ bị phá vỡ khi bị gán dữ liệu tùy tiện.

Gói `unsafe` chỉ tồn tại cho một số ranh giới đặc thù: tương tác với vùng nhớ do hệ điều hành hoặc mã nguồn ngôn ngữ khác quản lý, các thành phần tầng thấp có biểu diễn bộ nhớ cố định, hoặc các thao tác cơ bản mà thư viện chuẩn cung cấp. Công cụ này cho phép các phép toán vượt ra ngoài ranh giới an toàn kiểu thông thường, nhưng không biến mọi hành vi thành bất định. Lập trình viên chỉ được phép dựa trên các cam kết mà đặc tả ngôn ngữ và tài liệu gói `unsafe` công bố: các hàm `unsafe.Sizeof`, `unsafe.Alignof` và `unsafe.Offsetof` đều có ngữ nghĩa được tài liệu hóa rõ ràng.

Cái giá phải trả cho việc dùng `unsafe` rất cao: các giả định về cách thức biểu diễn bộ nhớ có thể phụ thuộc vào nền tảng; kiến trúc phần cứng khác nhau có thể sở hữu cách sắp xếp bố cục (*layout*) bộ nhớ khác nhau; các quy tắc về vòng đời, bộ thu gom rác (*GC*) và con trỏ vẫn phải được chứng minh chặt chẽ. Một số đo kiểm nghiệm trên hệ điều hành Windows kiến trúc amd64 chỉ là kết quả đo lường trên mục tiêu đó, không phải giao diện nhị phân (*ABI*) phổ quát hay cam kết chung cho mọi bản dựng.

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

Tránh suy diễn bố cục bộ nhớ của giao diện, phần đầu chuỗi (*string header*), bảng ánh xạ hay đối tượng thời gian chạy từ các kết quả in ra. Đó là các chi tiết cài đặt nội bộ và hoàn toàn có thể thay đổi qua các phiên bản Go. Bài thực hành thực thi thí nghiệm này qua kiểm thử tự động để mã nguồn được trình biên dịch kiểm tra; nhật ký kết quả luôn ghi rõ phiên bản Go, hệ điều hành `GOOS` và kiến trúc `GOARCH`, tuyệt đối không xem một số đo cục bộ là quy chuẩn phổ quát.

### Code review: đừng giữ địa chỉ trong `uintptr`

Đoạn dưới là mã nguồn tiêu cực để phân tích, không phải kỹ thuật nên áp dụng trong thực tế. Nó trích xuất địa chỉ mảng byte nền tảng từ kiểu cũ `reflect.StringHeader` rồi trả về `uintptr` ra ngoài phạm vi chuỗi:

~~~go
func badDataAddress(s string) uintptr {
	header := (*reflect.StringHeader)(unsafe.Pointer(&s))
	return header.Data
}
~~~

Trước khi chấp nhận đoạn mã này, hãy phân tích bản chất cơ chế của Go Runtime:

Thứ nhất, phân biệt rạch ròi giữa việc di dời ngăn xếp (*stack movement*) và thu gom rác trên vùng nhớ động (*heap GC*). Cơ chế chạy Go hiện tại sử dụng vùng nhớ heap không di dời và có thể sao chép ngăn xếp khi kích thước ngăn xếp goroutine tăng lên; đó là chi tiết cài đặt nội bộ, không phải sự cho phép để tùy tiện lưu giữ địa chỉ bộ nhớ. Một con trỏ `unsafe.Pointer` vẫn được bộ thu gom rác nhận diện là con trỏ hợp lệ nếu tuân thủ các mẫu quy chuẩn mà gói `unsafe` công bố; hãy chỉ dựa vào các phép chuyển đổi đã được tài liệu hóa.

Thứ hai, kiểu `uintptr` đơn thuần là một số nguyên đủ độ rộng để chứa các bit địa chỉ trên kiến trúc hiện hành, hoàn toàn không phải một tham chiếu sống. Nếu tách địa chỉ khỏi con trỏ `unsafe.Pointer` gốc và lưu vào `uintptr`, bộ thu gom rác không có cơ sở nào để nhận diện số nguyên đó đang giữ đối tượng sống; việc mở rộng ngăn xếp cũng không thể tự động điều chỉnh giá trị của một số nguyên đã sao chép. Vì vậy đối tượng có thể bị thu hồi ngay khi vòng đời con trỏ gốc chấm dứt, và địa chỉ lưu trong biến số nguyên sẽ trở nên lỗi thời (*stale*).

Thứ ba, với pattern chuyển pointer qua `uintptr` để cộng offset rồi chuyển ngược, tài liệu `unsafe.Pointer` yêu cầu conversion và phép tính nằm trong cùng một biểu thức:

~~~go
p = unsafe.Pointer(uintptr(p) + offset)
~~~

Mẫu chuyển đổi trong cùng một biểu thức còn đòi hỏi kết quả ở trong đối tượng đã cấp phát; không được tính con trỏ tới ngay sau phần tử cuối theo quy ước đôi khi dùng trong C. `runtime.KeepAlive` không hợp thức hóa việc tách địa chỉ qua biến trung gian `uintptr`. Quy tắc chuyển đổi dựa trên tài liệu `unsafe`; phần heap không di dời và sao chép stack được đối chiếu source Go1.27.1 Windows/amd64. Ví dụ sai ở trên dùng để đọc và phản biện, không chạy nó rồi coi việc chưa crash là bằng chứng an toàn.

Trong thư viện Go 1.27.1, các kiểu `reflect.StringHeader` và `reflect.SliceHeader` đã bị đánh dấu lỗi thời (*deprecated*); tài liệu chính thức cảnh báo rằng trường `Data uintptr` không đủ năng lực giữ dữ liệu sống và cách biểu diễn này không an toàn cũng như không mang tính khả chuyển (*portable*). Khi thực sự cần thao tác tại ranh giới tầng thấp, hãy tuân thủ hợp đồng của các hàm hỗ trợ trong gói `unsafe` thay vì tự ý định nghĩa cấu trúc đầu mục; các hàm hỗ trợ này vẫn yêu cầu tuân thủ nghiêm ngặt các quy tắc về vòng đời và quyền biến đổi dữ liệu:

~~~go
// Trích xuất con trỏ byte nền tảng
ptr := unsafe.StringData(s)

// Tái tạo chuỗi từ con trỏ byte và độ dài
str := unsafe.String(ptr, len(s))

// Lấy con trỏ phần tử đầu của slice
slicePtr := unsafe.SliceData(buf)

// Tạo slice từ con trỏ và độ dài
slice := unsafe.Slice(slicePtr, len(buf))
~~~

Với chuỗi rỗng, `StringData` trả con trỏ không được quy định, có thể là `nil`; không được giải tham chiếu. `SliceData(nil)` trả `nil`, nhưng slice khác `nil` có capacity bằng 0 trả con trỏ khác `nil` tới địa chỉ không được quy định. Dùng độ dài 0 với `unsafe.String` hoặc `unsafe.Slice` không cấp quyền đọc byte ở con trỏ ấy. Ví dụ giữ `len(buf)` để không dựng một vùng nhìn vượt khỏi dữ liệu đã có; phép dựng slice này chia sẻ mảng nền, không sao chép. Kiểm thử `TestUnsafeHelpersEmptyAndSharedStorage` chỉ chạy các trường hợp hợp lệ đó, không thử đọc địa chỉ tùy ý.

Cần bảo đảm tuyệt đối hợp đồng về vòng đời và quyền sửa đổi dữ liệu: con trỏ Go hợp lệ được bộ thu gom rác chủ động theo dõi, khác hoàn toàn với một địa chỉ đã bị biến thành số nguyên vô hồn. Hàm `unsafe.String` không cho phép chỉnh sửa mảng byte nền tảng trong khi chuỗi ký tự vẫn đang được sử dụng. Hàm `runtime.KeepAlive` phát huy tác dụng tại các ranh giới như tài nguyên gắn bộ dọn dẹp (*finalizer*) mà hệ điều hành chỉ còn quản lý qua bộ mô tả tệp; nó không hợp thức hóa các phép chuyển đổi nằm ngoài quy chuẩn của `unsafe`, không khóa cố định vùng nhớ (*pinning*), và không thể khôi phục một địa chỉ số nguyên đã lỗi thời.

## Biên giới với C là một hợp đồng khác

Cơ chế soi chiếu vẫn vận hành bên trong khuôn khổ hệ thống kiểu của Go. Khi một thư viện chỉ cung cấp giao diện nhị phân ngôn ngữ C (*C ABI*), công cụ `cgo` sẽ đưa chương trình vượt qua một ranh giới hoàn toàn khác biệt: quy cách biểu diễn dữ liệu, vòng đời, bộ cấp phát bộ nhớ (*allocator*) và chuỗi công cụ của cả hai phía đều đòi hỏi nghiên cứu cẩn trọng. Một chuỗi Go quản lý độ dài tường minh và có thể chứa byte `NUL`; trong khi hàm `strlen` của C lại dừng ngay tại byte `NUL` đầu tiên. Hai thao tác đo độ dài này sở hữu hai hợp đồng ngữ nghĩa hoàn toàn khác nhau.

Thực hành tại `labs/edition-contracts/interop` có một hàm nhỏ dùng `C.CString`, gọi `C.strlen`, rồi giải phóng vùng nhớ đã cấp phát bằng `C.free`. Kiểm thử yêu cầu chuỗi `"a\x00b"` phải cho kết quả là 1 ở phía C, khác biệt với hàm `len` của chuỗi Go. Phép thử này không phải lời khuyên chuyển bộ phân tích sang C: nó chỉ làm sáng tỏ sự khác biệt về mặt dữ liệu. Chuỗi byte không có ký tự kết thúc `NUL`, chuỗi ký tự Unicode và chuỗi định dạng C đòi hỏi chính sách chuyển đổi rõ ràng; nhận định cảm tính rằng cùng là văn bản là chưa đủ.

Vùng nhớ do `C.CString` cấp phát bắt buộc phải được giải phóng qua bộ cấp phát của C; bộ thu gom rác của Go không tự động thu hồi vùng nhớ này. Đối với con trỏ Go truyền sang C, tài liệu `cgo` quy định chặt chẽ phạm vi bộ nhớ được phép trỏ tới, cơ chế ghim vùng nhớ (*pinning*) và khoảng thời gian C được phép giữ con trỏ. Tránh suy diễn rằng việc có một địa chỉ hợp lệ tại thời điểm gọi hàm cho phép phía C lưu trữ địa chỉ đó vô thời hạn. Kiểu `runtime.Pinner` và `runtime/cgo.Handle` giải quyết các bài toán ranh giới khác nhau; `Handle` là định danh an toàn để duy trì giá trị Go, không phải quyền cho phép C giải tham chiếu tùy tiện. Chỉ áp dụng các cơ chế này sau khi đã thiết kế kỹ lưỡng vòng đời đối tượng và nắm vững hợp đồng tương ứng.

Công cụ `cgo` còn làm thay đổi hợp đồng triển khai: quá trình biên dịch đòi hỏi trình biên dịch C phù hợp, tệp nhị phân có thể phụ thuộc vào các thư viện liên kết động của hệ điều hành, và việc biên dịch chéo (*cross-compilation*) cần thiết lập chuỗi công cụ đích phức tạp. Vùng nhớ cấp phát phía C không nằm trong hạn mức quản lý bộ nhớ của Go, và các sự cố sập chương trình tầng native có thể vượt ra khỏi luồng xử lý lỗi mà mã nguồn Go kiểm soát được. Không tồn tại một con số chi phí vượt ranh giới cố định: nếu ranh giới này nằm trên luồng xử lý cao điểm (*hot path*), kỹ sư phải đo đạc với đúng kích thước tải trọng, tần suất gọi và môi trường thực tế, đồng thời xem xét khả năng gộp nhiều thao tác vào một lần gọi duy nhất. Mã nguồn Go thuần túy thường đem lại sự tinh gọn cho quy trình đóng gói tự chứa; việc tích hợp C chỉ hợp lý khi cần tận dụng các giao diện lập trình, trình điều khiển hoặc thành phần đã được kiểm chứng mà chi phí viết lại tiềm ẩn nhiều rủi ro hơn chi phí tương tác.

Chương này không hướng dẫn kỹ thuật lách khỏi các quy tắc an toàn của Go. Nó trang bị tư duy thiết lập ranh giới có trách nhiệm khi kiểu dữ liệu chỉ xuất hiện tại thời gian chạy. Cơ chế soi chiếu có thể giúp mã nguồn xử lý linh hoạt mà vẫn an toàn nếu các hợp đồng về hình thái dữ liệu, siêu dữ liệu và quyền biến đổi được thể hiện tường minh. Khi không có đủ bằng chứng xác nhận tính an toàn, việc quay trở về hệ thống kiểu tĩnh, các giao diện nhỏ hoặc giao diện lập trình cụ thể luôn là giải pháp thiết kế bền vững hơn.

@references
1. Go Team. Package `reflect`: `Value`, `CanSet`, `Type`, `TypeFor`, `StructField` và `StructTag`. pkg.go.dev/reflect
2. Go Team. Package `unsafe`: `Pointer`, `Sizeof`, `Alignof`, `Offsetof`, `String`, `StringData`, `Slice`, `SliceData`. pkg.go.dev/unsafe
3. Go Team. The Go Programming Language Specification: struct tags, type identity và address operators. go.dev/ref/spec
4. Go Team. A Guide to the Go Garbage Collector. go.dev/doc/gc-guide; cơ chế sao chép stack đối chiếu riêng với `src/runtime/stack.go` của Go 1.27.1, không phải contract của ngôn ngữ.
5. Go Team. `cmd/cgo`, Passing pointers; `runtime.Pinner`; `runtime/cgo.Handle`. Contract kiểm tra với Go 1.27.1. pkg.go.dev/cmd/cgo
