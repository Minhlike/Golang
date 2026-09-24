# HỢP ĐỒNG KIỂM KÊ VÀ BAO PHỦ KIẾN THỨC GO NỀN TẢNG (BASIC GO COVERAGE CONTRACT)

Tài liệu này đóng vai trò là bản kiểm kê toàn diện (comprehensive inventory) các chủ đề Go nhập môn, đối chiếu giữa danh mục tham khảo người mới bắt đầu (W3Schools Go Syllabus), tài liệu chuẩn kỹ thuật chính thức (Go Specification, A Tour of Go, Effective Go), và hiện trạng triển khai trong các chương sách.

Mục tiêu tối thượng: **BASIC IS NOT SHALLOW** — Một người hoàn toàn chưa biết Go căn bản có thể bắt đầu từ Chương 00, học từng cú pháp, thành phần ngữ pháp, mô hình tinh thần từ nguyên lý đầu tiên mà không phải mở thêm bất kỳ tài liệu nào khác để học vỡ lòng.

---

## 1. BẢNG KIỂM KÊ CHI TIẾT 48 CHỦ ĐỀ NỀN TẢNG

| STT | Chủ đề (Topic) | Beginner Reference Coverage (W3Schools) | Vị trí hiện tại trong sách | Đã dạy đủ từ First Principles chưa? | Tiên quyết (Prerequisite) | Chương cần bổ sung / Tăng cường | Bằng chứng Go chính thức (Go Official Evidence) | Trạng thái (Status) |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| 1 | **file Go (`.go`)** | Go Syntax, Go Environment Setup | Ch00, Ch01 | Cần bổ sung cấu trúc source file, UTF-8 encoding | Không | Ch00, Ch01 | [Go Spec: Source code representation](https://go.dev/ref/spec#Source_code_representation) | REINFORCE |
| 2 | **package** | Go Syntax (`package main`) | Ch00, Ch01, Ch05 | Cần giải thích rõ `package` là đơn vị biên dịch và namespace | file Go | Ch00, Ch01 | [Go Spec: Package clause](https://go.dev/ref/spec#Package_clause) | REINFORCE |
| 3 | **import** | Go Syntax (`import "fmt"`) | Ch00, Ch01, Ch05 | Cần bóc tách đường dẫn import, standard library vs 3rd-party | package | Ch00, Ch01 | [Go Spec: Import declarations](https://go.dev/ref/spec#Import_declarations) | REINFORCE |
| 4 | **comment (`//`, `/* */`)** | Go Comments | Ch01 | Cần bóc tách comment dòng, block, và quy ước GoDoc | file Go | Ch01 | [Go Spec: Comments](https://go.dev/ref/spec#Comments) | REINFORCE |
| 5 | **identifier (định danh)** | Go Variables, Naming rules | Ch01 | Cần quy tắc đặt tên, ký tự Unicode, exported (chữ hoa) vs unexported (chữ thường) | comment | Ch01 | [Go Spec: Identifiers](https://go.dev/ref/spec#Identifiers) | REINFORCE |
| 6 | **naming convention** | Go Variable Naming Rules | Ch01, Ch05 | Cần camelCase, MixedCaps, tên ngắn trong scope nhỏ, không dùng snake_case | identifier | Ch01, Ch05 | [Effective Go: Names](https://go.dev/doc/effective_go#names) | REINFORCE |
| 7 | **var declaration** | Go Variables (`var name type`) | Ch01 | Cần bóc tách cú pháp đầy đủ, vị trí package-level vs function-level | naming | Ch01 | [Go Spec: Variable declarations](https://go.dev/ref/spec#Variable_declarations) | REINFORCE |
| 8 | **short declaration (`:=`)** | Go Variables (`name := value`) | Ch01 | Cần phân biệt rõ với `var` và phép gán `=`, phạm vi trong hàm | var | Ch01 | [Go Spec: Short variable declarations](https://go.dev/ref/spec#Short_variable_declarations) | REINFORCE |
| 9 | **multiple declaration** | Go Multiple Variable Declaration | Ch01 | Cần cú pháp khai báo gom nhóm `var (...)` và khai báo song song | var, := | Ch01 | [Go Spec: Variable declarations](https://go.dev/ref/spec#Variable_declarations) | REINFORCE |
| 10 | **assignment (`=`)** | Go Variables Assignment | Ch01 | Cần phân biệt phép gán thay đổi giá trị với phép khai báo định danh | identifier, var | Ch01 | [Go Spec: Assignments](https://go.dev/ref/spec#Assignments) | REINFORCE |
| 11 | **zero value** | Go Variables (Default values) | Ch01 | Cần bảng zero value cho numeric (0), bool (false), string (""), pointer/slice/map (nil) | var | Ch01 | [Go Spec: The zero value](https://go.dev/ref/spec#The_zero_value) | REINFORCE |
| 12 | **constant (`const`, `iota`)** | Go Constants | Ch01 | Cần giải thích hằng số không kiểu (untyped), typed const, và `iota` | identifier, literal | Ch01 | [Go Spec: Constant declarations](https://go.dev/ref/spec#Constant_declarations) | REINFORCE |
| 13 | **literal (giá trị nguyên văn)** | Go Data Types | Ch01 | Cần phân biệt integer literal, float literal, string literal, composite literal | syntax | Ch01 | [Go Spec: Literals](https://go.dev/ref/spec#Literals) | REINFORCE |
| 14 | **bool type** | Go Data Types (Boolean) | Ch01 | Cần toán tử logic (`&&`, `\|\|`, `!`), truth table | zero value | Ch01 | [Go Spec: Boolean types](https://go.dev/ref/spec#Boolean_types) | REINFORCE |
| 15 | **integer types** | Go Data Types (Integer: int, int64, uint...) | Ch01 | Cần giải thích kích thước bit, `int` phụ thuộc kiến trúc (32/64-bit), tràn số (overflow) | zero value | Ch01 | [Go Spec: Numeric types](https://go.dev/ref/spec#Numeric_types) | REINFORCE |
| 16 | **float types** | Go Data Types (Float32, Float64) | Ch01 | Cần chuẩn IEEE-754, sai số làm tròn số thực, phép so sánh float | zero value | Ch01 | [Go Spec: Numeric types](https://go.dev/ref/spec#Numeric_types) | REINFORCE |
| 17 | **string type** | Go Data Types (String) | Ch01, Ch02 | Cần tính bất biến (immutable), chuỗi UTF-8 bytes, raw string literal (backticks) | zero value | Ch01 | [Go Spec: String types](https://go.dev/ref/spec#String_types) | REINFORCE |
| 18 | **conversion (chuyển đổi kiểu)** | Go Type Casting / Conversion | Ch01 | Cần cú pháp `T(v)`, không có ép kiểu ngầm định (no implicit conversion) | types | Ch01 | [Go Spec: Conversions](https://go.dev/ref/spec#Conversions) | REINFORCE |
| 19 | **type inference (suy luận kiểu)** | Go Type Inference | Ch01 | Cần cơ chế compiler gán default type cho untyped literals khi dùng `:=` | literal, := | Ch01 | [Go Spec: Type inference](https://go.dev/ref/spec#Type_inference) | REINFORCE |
| 20 | **fmt.Print** | Go Output Functions | Ch01 | Cần phân biệt in không xuống dòng, in nối tham số | import | Ch01 | [pkg.go.dev/fmt: Print](https://pkg.go.dev/fmt#Print) | REINFORCE |
| 21 | **fmt.Println** | Go Output Functions | Ch01 | Cần in thêm khoảng trắng giữa tham số và thêm ký tự xuống dòng | import | Ch01 | [pkg.go.dev/fmt: Println](https://pkg.go.dev/fmt#Println) | REINFORCE |
| 22 | **fmt.Printf** | Go Formatting Functions | Ch01 | Cần bóc tách định dạng theo format string | import | Ch01 | [pkg.go.dev/fmt: Printf](https://pkg.go.dev/fmt#Printf) | REINFORCE |
| 23 | **formatting verbs** | Go Formatting Verbs (`%v`, `%+v`, `%T`, `%d`, `%s`, `%q`...) | Ch01 | Cần bảng tra cứu formatting verbs trực quan | fmt.Printf | Ch01 | [pkg.go.dev/fmt: Verbs](https://pkg.go.dev/fmt) | REINFORCE |
| 24 | **operator (toán tử)** | Go Operators (Số học, gán, so sánh, logic) | Ch01 | Cần bảng toán tử đầy đủ, thứ tự ưu tiên (precedence) | literal, variable | Ch01 | [Go Spec: Operators](https://go.dev/ref/spec#Operators) | REINFORCE |
| 25 | **expression (biểu thức)** | Go Expressions | Ch01 | Cần định nghĩa: cấu trúc tính toán sinh ra một giá trị cụ thể | operator, literal | Ch01 | [Go Spec: Expressions](https://go.dev/ref/spec#Expressions) | REINFORCE |
| 26 | **statement (câu lệnh)** | Go Statements | Ch01 | Cần định nghĩa: đơn vị hành động làm thay đổi trạng thái | expression | Ch01 | [Go Spec: Statements](https://go.dev/ref/spec#Statements) | REINFORCE |
| 27 | **block (khối lệnh `{}`)** | Go Blocks | Ch01 | Cần phạm vi sống của biến sinh ra trong block, che khuất biến (shadowing) | statement | Ch01 | [Go Spec: Blocks](https://go.dev/ref/spec#Blocks) | REINFORCE |
| 28 | **array (mảng cố định)** | Go Arrays (`[n]T`) | Ch01, Ch02 | Cần giải thích độ dài là thành phần của kiểu, sao chép toàn bộ giá trị | types, block | Ch01, Ch02 | [Go Spec: Array types](https://go.dev/ref/spec#Array_types) | REINFORCE |
| 29 | **slice (`[]T`)** | Go Slices | Ch02 | Đã có chiều sâu backing array; cần bổ sung bóc tách cú pháp cho beginner | array | Ch01, Ch02 | [Go Spec: Slice types](https://go.dev/ref/spec#Slice_types) | REINFORCE |
| 30 | **len** | Go Slices/Arrays `len()` | Ch02 | Cần bóc tách built-in function trả về số phần tử logic | array, slice | Ch01, Ch02 | [Go Spec: Length and capacity](https://go.dev/ref/spec#Length_and_capacity) | REINFORCE |
| 31 | **cap** | Go Slices `cap()` | Ch02 | Cần bóc tách built-in function đo dung lượng backing array từ phần tử đầu | slice | Ch02 | [Go Spec: Length and capacity](https://go.dev/ref/spec#Length_and_capacity) | ADEQUATE |
| 32 | **make** | Go `make([]T, len, cap)` | Ch02 | Cần bóc tách từng đối số: kiểu, len, cap, cơ chế cấp phát | slice, types | Ch02 | [Go Spec: Making slices, maps and channels](https://go.dev/ref/spec#Making_slices_maps_and_channels) | REINFORCE |
| 33 | **append** | Go `append(slice, elems...)` | Ch02 | Cần cơ chế nhân đôi/mở rộng capacity và nguy cơ tách rời backing array | slice, make | Ch02 | [Go Spec: Appending to and copying slices](https://go.dev/ref/spec#Appending_and_copying_slices) | ADEQUATE |
| 34 | **map (`map[K]V`)** | Go Maps | Ch03 | Cần cú pháp khai báo, khởi tạo `make`, truy xuất comma-ok (`v, ok := m[k]`) | types, zero value | Ch01, Ch03 | [Go Spec: Map types](https://go.dev/ref/spec#Map_types) | REINFORCE |
| 35 | **struct** | Go Structs | Ch03 | Cần cú pháp định nghĩa `type S struct`, khởi tạo trường, field access (`s.Field`) | types | Ch01, Ch03 | [Go Spec: Struct types](https://go.dev/ref/spec#Struct_types) | REINFORCE |
| 36 | **if / else** | Go Conditions (if, else) | Ch01 | Cần cú pháp điều kiện, bắt buộc có ngoặc nhọn `{}` | bool, expression | Ch01 | [Go Spec: If statements](https://go.dev/ref/spec#If_statements) | REINFORCE |
| 37 | **if with short statement** | Go If with initialization | Ch01 | Cần cú pháp `if err := do(); err != nil`, scope của biến khai báo | if, := | Ch01 | [Go Spec: If statements](https://go.dev/ref/spec#If_statements) | REINFORCE |
| 38 | **switch** | Go Switch (basic, expression, condition-less) | Ch01 | Cần switch không cần `break`, `fallthrough`, switch không biểu thức (`switch {}`) | if | Ch01 | [Go Spec: Switch statements](https://go.dev/ref/spec#Switch_statements) | REINFORCE |
| 39 | **for loop** | Go Loops (3 thành phần, while-like, vô tận) | Ch01 | Cần 3 dạng của `for` (Go không có từ khóa `while` hay `do-while`) | statement, bool | Ch01 | [Go Spec: For statements](https://go.dev/ref/spec#For_statements) | REINFORCE |
| 40 | **for range** | Go Range Loops | Ch01, Ch02 | Cần lặp qua array, slice (index, value copy), map (key, value), string (rune) | for, slice, map | Ch01, Ch02 | [Go Spec: For statements with range](https://go.dev/ref/spec#For_statements) | REINFORCE |
| 41 | **function** | Go Functions | Ch01 | Cần từ khóa `func`, chữ ký hàm (signature), gọi hàm | statement, block | Ch01 | [Go Spec: Function declarations](https://go.dev/ref/spec#Function_declarations) | REINFORCE |
| 42 | **parameter vs argument** | Go Function Parameters | Ch01 | Cần phân biệt tham số hình thức (parameter) và đối số thực tế (argument) | function | Ch01 | [Go Spec: Function types](https://go.dev/ref/spec#Function_types) | REINFORCE |
| 43 | **return** | Go Function Return | Ch01 | Cần kiểu trả về, câu lệnh `return`, naked return / named return values | function | Ch01 | [Go Spec: Return statements](https://go.dev/ref/spec#Return_statements) | REINFORCE |
| 44 | **multiple return** | Go Multiple Return Values | Ch01, Ch04 | Cần idiom `(value, error)` kinh điển của Go | return | Ch01, Ch04 | [Effective Go: Multiple return values](https://go.dev/doc/effective_go#multiple-returns) | REINFORCE |
| 45 | **recursion** | Go Recursion | Ch01 | Cần điều kiện dừng (base case), chi phí stack frame | function, if | Ch01 | [Go Spec: Calls](https://go.dev/ref/spec#Calls) | REINFORCE |
| 46 | **method & receiver** | Go Methods (`func (r Receiver) Name()`) | Ch03 | Cần phân biệt value receiver (bản sao) và pointer receiver (sửa đổi trực tiếp) | function, struct | Ch03 | [Go Spec: Method declarations](https://go.dev/ref/spec#Method_declarations) | REINFORCE |
| 47 | **pointer fundamentals** | Go Pointers (`&` address-of, `*` dereference) | Ch02, Ch03 | Cần sơ đồ trực quan địa chỉ ô nhớ, con trỏ trỏ tới vùng dữ liệu | types, zero value | Ch01, Ch02 | [Go Spec: Pointer types](https://go.dev/ref/spec#Pointer_types) | REINFORCE |
| 48 | **interface fundamentals** | Go Interfaces (khai báo, ngầm định, rỗng) | Ch03, Ch04 | Cần thỏa mãn ngầm định (implicit satisfaction), interface header `(type, value)` | method | Ch03, Ch04 | [Go Spec: Interface types](https://go.dev/ref/spec#Interface_types) | REINFORCE |

---

## 2. KẾ HOẠCH BỔ SUNG VÀ PHÂN BỔ SƯ PHẠM VÀO CÁC CHƯƠNG ĐẦU

Để hoàn thành hợp đồng bao phủ này mà **không làm loãng chiều sâu** và **không tạo ra 40 chương nhỏ kiểu tutorial vụn vặt**, cuốn sách phân bổ các mảnh ghép cơ bản vào cấu trúc sư phạm tự nhiên:

1. **Chương 00 (`00-mo-cua-vao-go.md`):**
   - Đặt nền móng: Cấu trúc file Go, lệnh `go run`, giải phẫu chương trình tối thiểu.
   - Thêm phần **Code Anatomy** đầu tiên: Bóc tách từng token của `package main`, `import "fmt"`, `func main()`.
   - Giúp người học làm quen với Compiler phản hồi trước khi tự viết chương trình dài.

2. **Chương 01 (`01-doc-va-viet-mot-chuong-trinh-go.md`):**
   - Là "trung tâm tiếp nhận" toàn diện cho người mới bắt đầu.
   - Bổ sung tuần tự có chủ đích:
     * Khai báo biến: `var` tường minh vs cú pháp ngắn `:=` (Syntax Contrast).
     * Zero values: Giá trị mặc định của từng kiểu dữ liệu nguyên tử (`int`, `float64`, `bool`, `string`).
     * Toán tử & Biểu thức: Phép tính số học, toán tử logic `&&`, `||`, `!`, phép so sánh.
     * Cú pháp điều khiển: `if / else`, `if with short statement`, `switch` (không cần break, switch không điều kiện), `for` (3 thành phần, while-style, vô tận), `for range`.
     * Xuất dữ liệu: Bộ ba `fmt.Print`, `fmt.Println`, `fmt.Printf` và bảng formatting verbs (`%v`, `%+v`, `%T`, `%d`, `%s`, `%q`).
     * Hàm: Tham số, đối số, giá trị trả về đơn/đa, hàm đệ quy với base case rõ ràng.
     * Khái niệm con trỏ vỡ lòng: Toán tử lấy địa chỉ `&` và toán tử giải tham chiếu `*`.

3. **Chương 02 (`02-gia-tri-slice-va-aliasing.md`):**
   - Nối tiếp từ Array sang Slice.
   - Bổ sung so sánh Array cố định (`[N]T`) vs Slice linh hoạt (`[]T`).
   - Củng cố `len`, `cap`, `make([]T, len, cap)`, `append` với mô hình bộ nhớ (Memory Map) rõ ràng.

4. **Chương 03 (`03-mo-hinh-du-lieu-va-trach-nhiem-thay-doi.md`):**
   - Nối tiếp Struct, Map, Method.
   - Khởi tạo Struct literal, truy cập trường.
   - Khởi tạo Map, thao tác đọc ghi, idiom `comma-ok`.
   - Method với Value Receiver vs Pointer Receiver.
