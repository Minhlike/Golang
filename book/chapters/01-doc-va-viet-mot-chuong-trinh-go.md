<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Chương 1 — Đọc và viết một chương trình Go

Một tệp mã nguồn Go có cấu trúc giải tích chặt chẽ: phần đầu xác định không gian tên của gói, các dòng khai báo đặt ở cấp độ tệp, và các khối lệnh lồng nhau được bao bọc bởi những cặp ngoặc nhọn. Ta sẽ bắt đầu từ một chương trình thực tế: tiếp nhận mã trạng thái HTTP của một dịch vụ hạ tầng, phân loại tình trạng hoạt động và xuất thông tin chẩn đoán ra thiết bị đầu ra. Ví dụ này chứa đầy đủ các thành phần nguyên tử gồm dữ liệu, phép toán, rẽ nhánh và gọi hàm, phản ánh trực quan cách Go tổ chức luồng điều khiển.

~~~go
package main

import "fmt"

const service = "checkout"

func classify(status int) string {
	if status >= 500 {
		return "failed"
	}
	return "healthy"
}

func main() {
	status := 503
	label := classify(status)
	fmt.Println(service, label)
}
~~~

<!-- pagebreak -->

![Giải phẫu source file: mỗi vùng trong chương trình có một vai trò nhìn thấy được.](../../assets/diagrams/go-source-anatomy.png)

@figure Giải phẫu trực quan cấu trúc một tệp nguồn Go. Tên gói, các khai báo cấp tệp và hàm khởi điểm có ranh giới rõ ràng.

Để thấu suốt chương trình trên, ta lần theo luồng chuyển dịch trạng thái qua ba câu hỏi: chương trình bắt đầu thực thi ở đâu, giá trị nào được tạo ra trong bộ nhớ, và thông điệp nào được gửi ra ngoài? Câu trả lời lần lượt là: điểm khởi đầu nằm tại hàm `main`, giá trị số nguyên `503` được cấp phát trên khung ngăn xếp (stack frame) rồi truyền qua hàm `classify` để nhận lại mô tả chuỗi, và cuối cùng lời gọi hàm `fmt.Println` gửi dữ liệu qua lời gọi hệ thống ra console.

## Bản đồ Cấu trúc của một Tệp Nguồn

Từ trên xuống dưới, tệp mã nguồn được phân chia thành bốn vùng không gian cú pháp rõ rệt:

Khai báo gói (`package`): Xác định không gian tên và đơn vị biên dịch mà tệp trực thuộc.

Nạp thư viện (`import`): Cho phép tệp tham chiếu các kiểu dữ liệu và hàm được xuất khẩu từ các gói khác trong thư viện chuẩn hoặc module bên ngoài.

Khai báo cấp tệp: Không gian định nghĩa hằng số (`const`), biến toàn cục của gói (`var`), hoặc các kiểu dữ liệu và hàm dùng chung (`func`).

Hàm khởi điểm (`func main`): Điểm neo mà Go runtime kích hoạt để bắt đầu thực thi logic sau khi hoàn tất giai đoạn khởi tạo môi trường.

| Dòng mã | Vai trò ngữ pháp | Tác động thực thi |
| :--- | :--- | :--- |
| `package main` | Khai báo gói | Báo hiệu cho compiler tạo tệp thực thi độc lập. |
| `import "fmt"` | Khai báo nhập gói | Nạp không gian tên `fmt` vào phạm vi tệp. |
| `const service = "checkout"` | Khai báo hằng | Gắn định danh `service` với chuỗi bất biến tại lúc biên dịch. |
| `func classify(status int) string` | Khai báo hàm | Xác lập chữ ký hàm nhận `int` và trả về `string`. |
| `status >= 500` | Biểu thức so sánh | Đánh giá điều kiện nhị phân, sinh giá trị `bool`. |
| `return "failed"` | Câu lệnh trả về | Chấm dứt khung ngăn xếp hiện tại, trả chuỗi cho nơi gọi. |
| `status := 503` | Khai báo biến ngắn | Cấp phát vị trí lưu trữ trên stack và gán giá trị 503. |
| `fmt.Println(service, label)` | Lời gọi hàm | Triệu gọi hàm xuất dữ liệu qua mô tả tệp stdout. |

Việc định vị chính xác vai trò ngữ pháp của từng dòng giúp ta đọc thông điệp lỗi của trình biên dịch một cách bình tĩnh: lỗi có thể bắt nguồn từ một biểu thức sai cú pháp, một phép so sánh cấn kiểu dữ liệu, hay một biến bị gọi ngoài phạm vi sống, thay vì cảm giác hoang mang rằng toàn bộ chương trình đang bị hỏng.

![Sơ đồ khái niệm: compiler đọc source theo các lớp, từ token đến kiểm tra kiểu và chương trình chạy.](../../assets/diagrams/compiler-doc-go.png)

@figure Mô hình các lớp xử lý của Go compiler. Trình biên dịch đọc tệp văn bản từ cấp độ từ vựng (token), dựng cây cú pháp trừu tượng (AST), kiểm tra chặt chẽ tính tương thích của kiểu dữ liệu, rồi mới sinh mã máy thực thi.

## Quan hệ Giữa Khai báo, Biểu thức, Câu lệnh, Kiểu và Giá trị

Để xây dựng một mô hình tư duy vững chắc, ta cần phân biệt rạch ròi các khái niệm nền tảng thường bị đánh đồng trong lập trình:

Khai báo (Declaration): Là hành động giới thiệu một định danh mới vào bảng ký hiệu (symbol table) của trình biên dịch tại một tầm vực xác định, gắn định danh đó với một kiểu dữ liệu, một hằng số, một biến hoặc một hàm. Khai báo thiết lập ý nghĩa tĩnh cho mã nguồn.

Biểu thức (Expression): Là sự kết hợp giữa các toán hạng (toán tử, hằng số, biến, lời gọi hàm) có thể được đánh giá (evaluated) để sinh ra một giá trị duy nhất mang kiểu dữ liệu xác định. Ví dụ `status >= 500` là một biểu thức logic có giá trị kiểu `bool`. Biểu thức tự thân nó không làm thay đổi luồng điều khiển trừ khi được bọc trong một câu lệnh.

Câu lệnh (Statement): Là đơn vị thực thi hoàn chỉnh chỉ dẫn máy tính thực hiện một hành động cụ thể, chẳng hạn như rẽ nhánh điều kiện (`if`), lặp vòng (`for`), gán giá trị (`=`), hoặc trả về từ hàm (`return`). Câu lệnh cấu thành luồng chảy động của chương trình.

Kiểu dữ liệu (Type): Là định nghĩa trừu tượng quy định tập hợp các giá trị hợp lệ và tập hợp các phép toán được phép thực hiện trên các giá trị đó. Kiểu dữ liệu xác định kích thước bộ nhớ (tính bằng byte) và cách CPU diễn giải các bit nhị phân trong ô nhớ.

Giá trị (Value): Là dữ liệu cụ thể được ghi vào các ô nhớ hoặc thanh ghi, mang ngữ nghĩa do kiểu dữ liệu tương ứng quy định.

Lời gọi hàm (Function call): Là cơ chế chuyển giao quyền thực thi từ hàm gọi sang hàm được gọi, kèm theo việc đánh giá các biểu thức đối số và truyền các giá trị đó qua các thanh ghi hoặc ngăn xếp theo quy ước gọi (calling convention) của kiến trúc phần cứng.

## Định danh và Từ khóa

Trong ví dụ trên, `service`, `fmt`, `Println`, `classify`, `status` và `label` là các định danh (identifiers) — những cái tên do lập trình viên hoặc thư viện quy ước để đại diện cho biến, kiểu hoặc hàm. Ngược lại, `package`, `import`, `const`, `func`, `if` và `return` là các từ khóa (keywords) bất biến của ngôn ngữ Go, được dành riêng cho trình phân tích cú pháp.

Quy tắc cấu tạo định danh trong Go bắt đầu bằng một chữ cái hoặc dấu gạch dưới `_`, theo sau bởi các chữ cái, chữ số hoặc dấu gạch dưới. Cộng đồng Go áp dụng nhất quán quy ước viết hoa dạng lạc đà (`camelCase` hoặc `MixedCaps`), tránh hoàn toàn kiểu viết dấu gạch dưới (`snake_case`).

Đặc biệt, Go biến quy tắc viết hoa chữ cái đầu tiên thành cơ chế phân quyền truy cập cấp ngôn ngữ. Một định danh bắt đầu bằng chữ cái in hoa (như `Println`) được tự động công khai (exported) ra ngoài gói. Một định danh bắt đầu bằng chữ thường (như `classify`) là định danh nội bộ, bị trình biên dịch từ chối truy cập từ bất kỳ gói nào khác.

## Khai báo Biến và Khởi tạo Bộ nhớ

Biến đại diện cho một vị trí lưu trữ mang kiểu dữ liệu xác định trong bộ nhớ. Go cung cấp bốn hình thức khai báo phản ánh các bối cảnh cấp phát khác nhau:

Khai báo tường minh bằng từ khóa `var`: Cú pháp `var name Type = value` chỉ định tuyệt đối kiểu và giá trị khởi tạo. Cách viết này thường dùng khi cần nhấn mạnh kiểu dữ liệu ở cấp độ gói hoặc interface.

Khai báo suy luận kiểu: Cú pháp `var name = value` cho phép compiler tự động suy diễn kiểu từ giá trị khởi tạo ở vế phải, giúp loại bỏ sự lặp lại thừa thãi.

Khai báo không khởi tạo và Quy tắc Zero Value: Nếu một biến được khai báo dưới dạng `var name Type` mà không gán giá trị, Go bảo đảm ô nhớ đó luôn được điền sạch bằng giá trị mặc định (Zero Value). Cơ chế này loại bỏ hoàn toàn lỗi truy cập rác bộ nhớ (uninitialized memory) vốn phổ biến trong C/C++.

Khai báo ngắn trong thân hàm bằng `:=`: Cú pháp `name := value` kết hợp đồng thời việc khai báo biến mới, suy luận kiểu và gán giá trị. Cú pháp này chỉ hợp lệ bên trong thân hàm, không được phép dùng ở cấp độ tệp.

| Kiểu dữ liệu | Giá trị Zero Value | Biểu diễn bộ nhớ thực tế |
| :--- | :---: | :--- |
| Số nguyên (`int`, `int64`, `byte`...) | `0` | Toàn bộ các bit trong ô nhớ được đặt về 0. |
| Số thực (`float32`, `float64`) | `0.0` | Bit dấu, số mũ và định trị đều bằng 0. |
| Logic (`bool`) | `false` | Byte lưu trữ mang giá trị bit 0. |
| Chuỗi ký tự (`string`) | `""` | Cặp con trỏ dữ liệu `nil` và độ dài bằng 0 (không phải con trỏ rác). |
| Con trỏ, slice, map, channel, func, interface | `nil` | Con trỏ địa chỉ bộ nhớ trỏ về 0 (null pointer). |

Khi sử dụng toán tử khai báo ngắn, vế trái bắt buộc phải giới thiệu ít nhất một biến mới vào phạm vi hiện tại. Phép gán thuần túy `=` chỉ ghi đè giá trị lên biến đã tồn tại và không sinh ra định danh mới.

## Phạm vi Sống và Hiện tượng Che khuất Biến

Phạm vi sống (scope) của một định danh là khoảng không gian mã nguồn mà tại đó định danh có giá trị tham chiếu hợp lệ. Trong Go, phạm vi được giới hạn bởi các cặp ngoặc nhọn `{ ... }`.

~~~go
func main() {
	status := 503
	if status >= 500 {
		label := "failed"
		fmt.Println("Bên trong if:", label)
	}
	// Lệnh fmt.Println(label) ở đây sẽ gây lỗi biên dịch:
	// undefined: label
}
~~~

Biến `label` được khai báo bên trong khối lệnh `if`. Khi luồng thực thi đi ra ngoài dấu ngoặc nhọn đóng `}`, tầm vực của `label` kết thúc. Trình biên dịch giải phóng định danh này khỏi bảng ký hiệu cục bộ; mọi nỗ lực truy cập `label` từ bên ngoài đều bị chặn lại với lỗi `undefined: label`.

![Vết của scope: label nằm trong if block, còn status sống ở main block.](../../assets/diagrams/go-scope-trace.png)

@figure Trực quan hóa ranh giới phạm vi sống (scope) của biến. Biến khai báo trong khối lệnh con không thể được tham chiếu từ khối lệnh cha đứng bên ngoài.

Một cạm bẫy kỹ thuật nguy hiểm là hiện tượng che khuất biến (variable shadowing). Khi lập trình viên sử dụng toán tử `:=` bên trong một khối lệnh con với một tên biến trùng với biến đã có ở khối lệnh cha, Go sẽ tạo ra một biến hoàn toàn mới, che khuất biến bên ngoài trong suốt phạm vi của khối con:

~~~go
func main() {
	retries := 0
	if retries == 0 {
		retries := 3
		fmt.Println("Gia tri trong if:", retries)
	}
	fmt.Println("Gia tri ngoai if:", retries)
}
~~~

Chương trình in ra giá trị 3 bên trong khối `if`, nhưng biến `retries` ban đầu ở ngoài vẫn giữ nguyên giá trị 0. Để cập nhật biến của khối cha, ta phải sử dụng phép gán `=` thay vì toán tử khai báo ngắn `:=`.

## Hệ thống Kiểu Dữ liệu Cơ bản

Go là ngôn ngữ định kiểu tĩnh khắt khe. Trình biên dịch không cho phép chuyển đổi kiểu ngầm định (implicit type conversion) giữa các kiểu dữ liệu khác nhau, ngay cả khi chúng có cùng kích thước bit.

Kiểu số nguyên gồm `int` và `uint` có kích thước bit co giãn theo kiến trúc máy tính (32 bit trên máy 32-bit, 64 bit trên máy 64-bit), cùng các kiểu có kích thước bit cố định như `int8`, `int16`, `int32`, `int64` và các bản không dấu tương ứng. Kiểu `byte` là bí danh chính thức của `uint8`, và `rune` là bí danh của `int32` đại diện cho một điểm mã Unicode.

Kiểu số thực gồm `float32` và `float64` tuân theo chuẩn IEEE-754. Trong tính toán hạ tầng, lập trình viên ưu tiên `float64` để giảm thiểu sai số tích lũy dấu phẩy động. Ta không bao giờ so sánh bằng tuyệt đối `==` trên số thực; thay vào đó, ta kiểm tra xem khoảng cách hiệu số tuyệt đối có nằm trong biên sai số cho phép hay không.

Kiểu logic `bool` chỉ nhận một trong hai giá trị `true` hoặc `false`, đồng hành cùng các toán tử logic gồm phép và `&&`, phép hoặc `||`, và phép phủ định `!`.

Kiểu chuỗi ký tự `string` là một chuỗi byte bất biến (immutable sequence of bytes). Chuỗi trong Go không thể bị sửa đổi trực tiếp trên từng ô nhớ sau khi đã khởi tạo; mọi thao tác cắt nối chuỗi đều tạo ra một chuỗi mới hoặc chia sẻ mảng byte nền.

Phép chuyển đổi kiểu bắt buộc phải thực hiện tường minh theo cú pháp `T(v)`, trong đó `T` là kiểu đích và `v` là giá trị cần chuyển:

~~~go
var a int = 10
var b int64 = 20
var c int64 = int64(a) + b
~~~

Ngoại lệ duy nhất cho quy tắc chuyển đổi kiểu là các hằng số chưa định kiểu (untyped constants), như số nguyên văn `500`. Chúng mang độ chính xác lý tưởng tại thời điểm biên dịch và có thể được gán linh hoạt cho bất kỳ kiểu số nào tương thích về mặt phạm vi giá trị.

## Toán tử và Biểu thức

Toán tử số học bao gồm cộng `+`, trừ `-`, nhân `*`, chia `/`, và chia lấy dư `%`. Phép chia giữa hai số nguyên `5 / 2` luôn cho kết quả nguyên `2` do phần thập phân bị cắt cụt; nếu muốn nhận kết quả số thực, ít nhất một toán hạng phải mang kiểu số thực như `5.0 / 2`.

Toán tử so sánh bao gồm bằng `==`, khác `!=`, nhỏ hơn `<`, nhỏ hơn hoặc bằng `<=`, lớn hơn `>`, và lớn hơn hoặc bằng `>=`. Mọi biểu thức so sánh đều trả về kiểu `bool`.

Về mặt cú pháp, các phép toán tăng giảm `count++` và `count--` trong Go được phân loại là câu lệnh (statements), không phải biểu thức (expressions). Do đó, Go cấm hoàn toàn các biểu thức gây tác dụng phụ khó lường như `x = count++` hay `++count`.

## Xuất Dữ liệu Định dạng với Gói `fmt`

Gói thư viện chuẩn `fmt` cung cấp ba cơ chế xuất dữ liệu chủ đạo với các đặc tính riêng biệt:

`fmt.Print`: Xuất các đối số nối tiếp nhau ra stdout mà không tự động chèn khoảng trắng phân cách (trừ khi hai đối số liên tiếp không phải là chuỗi) và không tự ngắt dòng.

`fmt.Println`: Xuất các đối số ra stdout, tự động thêm dấu cách giữa các đối số và luôn thêm ký tự xuống dòng ở cuối.

`fmt.Printf`: Định dạng chuỗi theo mẫu (format string) thông qua các ký hiệu động từ định dạng (verbs) bắt đầu bằng ký tự `%`.

| Ký hiệu Verb | Ý nghĩa định dạng | Ví dụ biểu diễn |
| :---: | :--- | :--- |
| `%v` | Biểu diễn giá trị mặc định theo kiểu dữ liệu tự nhiên. | `fmt.Printf("%v", 503)` xuất `503`. |
| `%+v` | Mở rộng biểu diễn struct kèm theo tên từng trường dữ liệu. | `fmt.Printf("%+v", req)` xuất `{Path:/ ID:1}`. |
| `%#v` | Biểu diễn giá trị dưới dạng cú pháp mã nguồn Go hợp lệ. | `fmt.Printf("%#v", "ok")` xuất `"ok"`. |
| `%T` | Xuất tên định danh của kiểu dữ liệu. | `fmt.Printf("%T", 503)` xuất `int`. |
| `%t` | Xuất giá trị logic (`true` hoặc `false`). | `fmt.Printf("%t", true)` xuất `true`. |
| `%d` | Xuất số nguyên theo hệ thập phân cơ số 10. | `fmt.Printf("%d", 255)` xuất `255`. |
| `%x` / `%X` | Xuất số nguyên hoặc mảng byte dưới dạng hệ thập lục phân. | `fmt.Printf("%x", 255)` xuất `ff`. |
| `%f` | Xuất số thực dấu phẩy động (có thể định dạng độ rộng như `%.2f`). | `fmt.Printf("%.2f", 3.14159)` xuất `3.14`. |
| `%s` | Xuất chuỗi ký tự hoặc mảng byte dưới dạng văn bản. | `fmt.Printf("%s", "ready")` xuất `ready`. |
| `%q` | Xuất chuỗi được bao bọc an toàn trong cặp dấu ngoặc kép. | `fmt.Printf("%q", "ready")` xuất `"ready"`. |
| `%p` | Xuất địa chỉ bộ nhớ thực tế dưới dạng con trỏ hệ thập lục phân. | `fmt.Printf("%p", &status)` xuất `0xc000014088`. |

## Điều khiển Luồng: Rẽ nhánh và Lặp

Go tối giản hóa cấu trúc điều khiển luồng, loại bỏ các biến thể cú pháp dư thừa để giữ mã nguồn đồng nhất trên diện rộng.

### Rẽ nhánh Điều kiện với `if / else`

Cú pháp `if` trong Go không yêu cầu cặp ngoặc đơn bọc điều kiện, nhưng bắt buộc phải có cặp ngoặc nhọn `{}` bao quanh khối lệnh, bất kể khối lệnh chỉ có một dòng đơn.

Go hỗ trợ câu lệnh khởi tạo ngắn đặt ngay trước mệnh đề điều kiện, phân cách bởi dấu chấm phẩy `;`:

~~~go
if err := executeCheck(); err != nil {
	fmt.Println("Kiem tra that bai:", err)
}
~~~

Biến `err` được khai báo trong mệnh đề này chỉ tồn tại trong phạm vi của khối `if` và các nhánh `else` liên đới, tự động tiêu hủy khi luồng thực thi rời khỏi cấu trúc rẽ nhánh, tránh gây ô nhiễm không gian tên bên ngoài.

### Lựa chọn Rời rạc với `switch`

Cấu trúc `switch` trong Go tự động kết thúc khi một nhánh `case` thỏa mãn, không đòi hỏi lập trình viên phải chèn lệnh `break` thủ công như các ngôn ngữ họ C. Nếu chủ đích muốn luồng chạy tiếp xuống nhánh kế tiếp, từ khóa `fallthrough` phải được khai báo tường minh.

Go cũng hỗ trợ `switch` không điều kiện (`switch {}`), trong đó mỗi nhánh `case` là một biểu thức logic độc lập, thay thế hoàn toàn cho các chuỗi `if / else if` phức tạp và khó bảo trì:

~~~go
switch {
case status >= 500:
	return "failed"
case status >= 400:
	return "warning"
default:
	return "healthy"
}
~~~

### Vòng lặp Duy nhất: `for`

Go chỉ có một từ khóa lặp duy nhất là `for`. Mọi nhu cầu lặp từ ba thành phần truyền thống, lặp theo điều kiện (tương đương `while`), lặp vô tận, cho đến duyệt tập hợp dữ liệu (`for range`) đều được biểu đạt thông qua `for`.

~~~go
// Dang 1: Lap co bien dem truyen thong
for i := 0; i < 3; i++ {
	fmt.Println("Lan thu:", i)
}

// Dang 2: Lap theo dieu kien (tuong duong while)
for retries < 3 {
	retries++
}

// Dang 3: Lap vo han (cho den khi break hoac return)
for {
	if isDone() {
		break
	}
}

// Dang 4: Duyet mang hoac slice voi range
statuses := []int{200, 404, 500}
for index, code := range statuses {
	fmt.Printf("Chi so %d mang gia tri %d\n", index, code)
}
~~~

Khi duyệt tập hợp bằng `for range`, biến phần tử thứ hai (`code`) nhận một bản sao giá trị của phần tử tại vị trí duyệt. Việc biến đổi giá trị của `code` không làm thay đổi dữ liệu trong tập hợp ban đầu. Nếu không cần dùng đến biến chỉ số, dấu gạch dưới `_` được sử dụng để thông báo cho compiler bỏ qua.

## Hàm và Ngữ nghĩa Truyền Giá trị

Hàm là đơn vị đóng gói logic độc lập, nhận vào các tham số hình thức và trả về kết quả cho bên gọi.

Go áp dụng nghiêm ngặt ngữ nghĩa truyền theo giá trị (pass by value). Mọi đối số khi truyền vào hàm đều được sao chép nguyên trạng giá trị nhị phân vào khung ngăn xếp hoặc thanh ghi của hàm nhận. Nếu giá trị đó là một số nguyên, hàm nhận một bản sao độc lập; nếu giá trị đó là một con trỏ hoặc một cấu trúc chứa con trỏ trỏ tới vùng nhớ khác, bản sao con trỏ ấy vẫn trỏ về cùng một vùng dữ liệu chung.

Go cho phép hàm trả về cùng lúc nhiều giá trị độc lập, tạo tiền đề cho khuôn mẫu xử lý lỗi tiêu chuẩn của ngôn ngữ bằng cách trả về cặp giá trị gồm kết quả dữ liệu và đối tượng lỗi:

~~~go
func parsePort(raw string) (int, error) {
	if raw == "" {
		return 0, fmt.Errorf("cong mang khong duoc de trong")
	}
	return 8080, nil
}
~~~

Nơi gọi hàm tiếp nhận cả hai giá trị và tiến hành kiểm tra điều kiện lỗi trước khi sử dụng kết quả:

~~~go
port, err := parsePort("8080")
if err != nil {
	fmt.Println("Loi phan tich:", err)
	return
}
fmt.Println("Cong mang:", port)
~~~

## Nhập môn Con trỏ: Địa chỉ Ô nhớ và Phép Giải Tham chiếu

Biến là tên gọi đại diện cho một vị trí lưu trữ trong bộ nhớ. Con trỏ (pointer) là một giá trị đặc biệt chứa địa chỉ bộ nhớ của một biến khác.

Toán tử lấy địa chỉ `&` trích xuất địa chỉ ô nhớ của biến đứng sau nó. Toán tử giải tham chiếu `*` đặt trước một biến con trỏ để đọc hoặc ghi đè giá trị tại ô nhớ mà con trỏ đang tham chiếu.

~~~go
func main() {
	x := 100
	var p *int = &x

	fmt.Printf("Gia tri goc: %d\n", x)     // 100
	fmt.Printf("Dia chi &x:  %p\n", &x)    // Vi du 0xc000014088
	fmt.Printf("Gia tri *p:  %d\n", *p)    // 100

	*p = 200
	fmt.Printf("Gia tri moi: %d\n", x)     // 200
}
~~~

Con trỏ cho phép các hàm khác nhau cùng thao tác và biến đổi một vùng dữ liệu mà không phải sao chép toàn bộ khối dữ liệu đó qua từng lời gọi hàm.

## Thí nghiệm Nhỏ: Từ Mã nguồn Go đến Hợp ngữ Compiler

Để mở cánh cửa mental model về những gì thực sự diễn ra bên dưới cú pháp, ta hãy xem cách trình biên dịch Go chuyển đổi hàm phân loại trạng thái sang biểu diễn hợp ngữ trung gian.

Thí nghiệm được thực hiện trên công cụ Go 1.27.1 với kiến trúc mục tiêu `windows/amd64`. Ta sử dụng lệnh trích xuất danh sách hợp ngữ của trình biên dịch:

~~~bash
go build -gcflags="-S" -o NUL main.go
~~~

Cần phân biệt rõ: bản danh sách phát sinh từ cờ `-S` là biểu diễn hợp ngữ trung gian của trình biên dịch (compiler assembly listing) do backend `cmd/compile/internal/ssagen` phát ra theo cú pháp Plan 9. Nó sử dụng các thanh ghi ảo và chỉ thị nội bộ của runtime, chưa phải là mã nhị phân liên kết cuối cùng được giải mã bằng `go tool objdump`.

Trích đoạn hợp ngữ thực tế của hàm `classify` từ công cụ biên dịch:

~~~text
main.classify STEXT nosplit size=55 args=0x8 locals=0x0
	TEXT	main.classify(SB), NOSPLIT|NOFRAME|ABIInternal, $0-8
	CMPQ	AX, $500
	JGE	42
	LEAQ	go:string."healthy"(SB), AX
	MOVL	$7, BX
	RET
	LEAQ	go:string."failed"(SB), AX
	MOVL	$6, BX
	RET
~~~

Bản hợp ngữ trên tiết lộ ba nguyên lý thiết kế then chốt của Go runtime:

Thứ nhất, quy ước gọi hàm nội bộ (Go Internal ABI): Thay vì đẩy tham số vào ngăn xếp như các phiên bản Go cũ, Go 1.27.1 truyền tham số `status` trực tiếp qua thanh ghi phần cứng `AX`.

Thứ hai, câu lệnh so sánh `status >= 500` được chuyển trực tiếp thành chỉ thị CPU `CMPQ AX, $500`, theo sau bởi lệnh nhảy có điều kiện `JGE` (Jump if Greater or Equal).

Thứ ba, cấu trúc của một chuỗi ký tự (`string`) trong Go thực chất là một cặp giá trị gồm con trỏ dữ liệu và độ dài byte. Khi trả về `"healthy"`, lệnh `LEAQ` nạp địa chỉ chuỗi vào `AX`, và lệnh `MOVL $7, BX` nạp độ dài 7 byte vào thanh ghi `BX`. Tương tự, chuỗi `"failed"` nạp độ dài 6 byte vào `BX`.

Mã nguồn Go thanh lịch ở tầng trên đã được trình biên dịch chuyển đổi thành các phép so sánh thanh ghi và dịch chuyển ô nhớ cực kỳ tinh gọn ở tầng dưới.

## Đọc Thông điệp Biên dịch: Phân tích Tĩnh Thay vì Phỏng đoán

Khi gặp lỗi biên dịch, kỹ sư không phỏng đoán mơ hồ mà đối chiếu thông báo lỗi với các tầng phân tích tĩnh của compiler:

| Tình huống kiểm chứng | Thao tác tạo lỗi cú pháp | Thông báo từ Go Compiler | Tầng phân tích của Compiler |
| :--- | :--- | :--- | :--- |
| Biến chưa khai báo | Gán `status = 503` mà chưa từng khai báo biến `status`. | `undefined: status` | Tầng phân tích bảng ký hiệu (Symbol table lookup): Định danh không tồn tại trong scope hiện hành. |
| Xung đột kiểu dữ liệu | Truyền biến `int` vào hàm đòi hỏi tham số `string`. | `cannot use status (type int) as string value in argument` | Tầng kiểm tra kiểu tĩnh (Type checker): Chữ ký hàm từ chối đối số không tương thích. |
| Vượt ngoài tầm vực | Gọi `fmt.Println(label)` ở ngoài khối lệnh `if`. | `undefined: label` | Tầng phân tích tầm vực (Lexical scoping): Biến đã bị hủy khỏi bảng ký hiệu khi khối con kết thúc. |

Thông điệp biên dịch là bản chẩn đoán chính xác về mặt toán học đối với cấu trúc của chương trình. Hiểu được nguyên lý phân tích từ token, cú pháp, kiểu dữ liệu, cho đến biểu diễn thanh ghi giúp bạn tiếp cận mọi sự cố mã nguồn với sự tự tin và chuẩn xác. Chương 2 sẽ tiếp nối hành trình bằng việc giải phẫu sâu cấu trúc dữ liệu linh hoạt và quan trọng bậc nhất của Go: lát cắt (slice) và cơ chế chia sẻ bộ nhớ nền.
