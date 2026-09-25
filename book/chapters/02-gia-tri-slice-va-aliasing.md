<!-- BOOK_ROLE: FOUNDATION_CORE -->

# Chương 2 — Khi một bản sao vẫn chia sẻ dữ liệu

Chạy đoạn này trước khi cố giải thích nó. Nếu bạn đoán a và b khác nhau sau dòng b[0] = 99, đó là một dự đoán rất hợp lý - và cũng là cánh cửa vào phần này.

~~~go
a := []int{10, 20, 30}
b := a
b[0] = 99

fmt.Println(a)
fmt.Println(b)
~~~

Kết quả từ lab part2-values là:

~~~text
[99 20 30]
[99 20 30]
~~~

Đừng ghi nhớ riêng một câu “slice nguy hiểm”. Thay vào đó, ta sẽ lần ngược từ kết quả: Go đã copy cái gì khi chạy b := a, và dữ liệu nào không được copy?

## Một baseline để dự đoán

Với một int, assignment tạo ra một giá trị độc lập. Cả a và b đều có giá trị riêng của chính chúng.

~~~go
a := 10
b := a
b = 99

fmt.Println(a, b) // 10 99
~~~

Go đã copy value của a vào b. Sau đó b nhận value mới; a không có lý do gì để đổi. Đây là quy tắc nền: assignment copy value. Điều còn thiếu là một value có thể chứa gì.

Array giúp ta kiểm tra quy tắc ấy với nhiều phần tử. Độ dài là một phần của type, nên [3]int và [4]int là hai array type khác nhau. Khi array được gán, toàn bộ array value được copy.

~~~go
a := [3]int{10, 20, 30}
b := a
b[0] = 99

fmt.Println(a) // [10 20 30]
fmt.Println(b) // [99 20 30]
~~~

![Hai array value sau assignment: phần tử được copy vào vùng dữ liệu riêng.](../../assets/diagrams/array-copy.png)

@figure Assignment của array copy các phần tử. Việc thay b[0] chỉ chạm vào array b.

Đến đây, trực giác “copy nghĩa là độc lập” vẫn đúng. Sự thay đổi xuất hiện chỉ khi ta bỏ một ký tự trong type: [3]int trở thành []int.

## Khoảnh khắc slice đổi kết quả

~~~go
a := []int{10, 20, 30}
b := a
b[0] = 99
~~~

[]int không phải array không ghi độ dài. Nó là slice type. Một slice value mô tả một đoạn liên tiếp của underlying array. 

Về mặt biểu diễn nội bộ trong Go runtime (`src/runtime/slice.go`), một slice được cấu thành từ đúng ba từ máy (3-word descriptor, chiếm 24 byte trên kiến trúc 64-bit): con trỏ dữ liệu `array unsafe.Pointer` trỏ tới phần tử đầu tiên của mảng nền, trường độ dài hiện tại `len int`, và trường sức chứa tối đa `cap int`.

Khi phép gán `b := a` diễn ra, trình biên dịch sao chép nguyên trạng 24 byte của tiêu đề descriptor từ `a` sang `b`. Biến `b` sở hữu một bản sao giá trị riêng biệt về `len` và `cap`, nhưng trường `array` của nó vẫn chứa đúng địa chỉ bộ nhớ trỏ về mảng nền ban đầu.

![Hai slice value sau assignment: descriptor được copy, backing storage được chia sẻ.](../../assets/diagrams/slice-sharing.png)

@figure b := a copy slice value, gồm cửa sổ nhìn vào dữ liệu, len và cap. Cả hai descriptor vẫn dẫn tới cùng underlying array, nên b[0] thay đổi phần tử mà a cũng nhìn thấy.

Vì vậy hai câu sau cùng đúng, và không mâu thuẫn:

@table Copy value và chia sẻ storage là hai tầng khác nhau của cùng một phép gán.

| Câu nói | Đúng ở đâu? |
| --- | --- |
| Assignment copy value. | b nhận một slice descriptor riêng: đổi len của b bằng reslice không tự đổi len của a. |
| Hai slice có thể cùng đổi dữ liệu. | Slice descriptor cùng tham chiếu một backing array; mutation một element hiện ra qua mọi slice cùng nhìn element đó. |

Từ aliasing dùng cho tình huống nhiều đường tham chiếu đến cùng dữ liệu. Nó không phải lỗi tự thân. Aliasing giúp cắt một cửa sổ trên buffer mà không copy cả buffer. Nó thành bug khi một người đọc tưởng mình có dữ liệu riêng nhưng thực tế lại đang sửa vùng dùng chung.

## Cửa sổ, length và capacity

Đặt một slice lên một slice khác để thấy descriptor thực sự đang mô tả gì.

~~~go
base := []int{10, 20, 30, 40, 50}
x := base[1:3]

fmt.Println(x)      // [20 30]
fmt.Println(len(x)) // 2
fmt.Println(cap(x)) // 4
~~~

x bắt đầu ở phần tử 20 của base và kết thúc trước 40. Vì thế length là 2. Capacity đếm số phần tử từ điểm bắt đầu của x đến cuối backing array mà x hiện có thể mở rộng tới; ở đây là 20, 30, 40, 50, nên là 4.

![Một slice window: vùng thấy được là len; phần còn có thể mở rộng là capacity.](../../assets/diagrams/slice-window.png)

@figure x nhìn thấy hai phần tử đầu của cửa sổ. cap(x) không nói x đang có bốn phần tử; nó nói x có thể được reslice hoặc append trong phạm vi backing array hiện tại.

Hãy tự dự đoán trước khi chạy:

~~~go
base := []int{1, 2, 3, 4}
a := base[:2]
b := base[1:3]
a[1] = 99

fmt.Println(base)
fmt.Println(a)
fmt.Println(b)
~~~

Kết quả là [1 99 3 4], [1 99], [99 3]. a[1] và b[0] đều chỉ vào phần tử base[1]. Hình vẽ không thay thế được việc lần index: nó chỉ cho biết vì sao có thể có một phần tử chung để lần.

## append là một phép thử về capacity

append không hứa luôn dùng lại array cũ, cũng không hứa luôn tạo array mới. Nó trả về resulting slice. Khi backing array còn chỗ, implementation có thể dùng lại; khi capacity không đủ, append phải cấp underlying array mới đủ lớn cho kết quả. Vì return value mang descriptor có thể đã đổi, viết s = append(s, value) là dạng thông thường.

~~~go
s := make([]int, 2, 4)
s[0], s[1] = 10, 20
old := s

s = append(s, 30)
s[0] = 99

fmt.Println(old) // [99 20]
fmt.Println(s)   // [99 20 30]
~~~

Ở đây `s` còn capacity. `old` và `s` có length khác nhau, nhưng vẫn cùng nhìn hai element đầu của backing array. Khi một slice cạn sức chứa (`len == cap`), lời gọi `append` kích hoạt hàm nội bộ `runtime.growslice`. Thuật toán cấp phát hiện đại của Go (từ Go 1.18+) chuyển dịch mượt mà thay vì nhân đôi đột ngột: dưới ngưỡng 256 phần tử, dung lượng tăng gấp đôi; trên 256 phần tử, dung lượng tăng dần theo tỷ lệ `newcap += (newcap + 3*256) / 4`. Hơn thế nữa, số byte thực tế được cấp phát sẽ được bộ quản lý heap làm tròn lên kích thước size-class gần nhất, khiến `cap` thực tế sau khi phình to có thể lớn hơn một lượng nhỏ so với công thức toán học.

Để chủ động phòng vệ, Go cung cấp cú pháp lát cắt ba chỉ số đầy đủ `s[low:high:max]` (Full Slice Expression). Cú pháp này giới hạn sức chứa của lát cắt mới ở mức `max - low`. Khi ta đặt `max = high`, sức chứa bị khóa chặt bằng đúng độ dài; bất kỳ thao tác `append` nào kế tiếp đều bắt buộc phải cấp phát mảng nền độc lập, ngăn chặn hoàn toàn việc ghi đè lên các phần tử phía sau:

~~~go
old := []int{10, 20}
s := old[:2:2]
grown := append(s, 30)
grown[0] = 99

fmt.Println(old)   // [10 20]
fmt.Println(grown) // [99 20 30]
~~~

![Hai kết quả của append: còn capacity thì có thể chia sẻ; hết capacity thì resulting slice đi tới storage mới.](../../assets/diagrams/append-storage.png)

@figure Hình mô tả hai semantics mà code phải chịu được. Đừng suy luận allocation từ một capacity tình cờ; nếu code cần một kết quả riêng, hãy tạo bản copy có chủ ý.

## Một aliasing bug có người dùng thật

Một function “chỉ chuẩn bị preview” đôi khi phá dữ liệu của caller.

~~~go
func redactPreview(fields []string) {
	fields[0] = "***"
}

requestFields := []string{"api-key", "region"}
redactPreview(requestFields)
fmt.Println(requestFields) // [*** region]
~~~

Parameter fields nhận một slice value mới, nhưng descriptor ấy vẫn reference storage của requestFields. Việc đổi element là mutation shared storage. Nếu mục tiêu thật sự là tạo preview độc lập, copy phần tử sang một slice mới trước:

~~~go
func redactedCopy(fields []string) []string {
	preview := make([]string, len(fields))
	copy(preview, fields)
	preview[0] = "***"
	return preview
}
~~~

copy sao chép tối đa số phần tử vừa với destination và trả về số phần tử đã copy. Ở đây make tạo backing array mới, nên preview độc lập ở tầng slice elements. Đổi lấy independence là allocation và chi phí copy; với buffer lớn hoặc đường xử lý nóng, đó là một quyết định cần có lý do. Với một preview cần an toàn khỏi mutation, nó diễn đạt đúng intent.

**Thực hành - bug hunt có kiểm chứng.** Mở `labs/part2-values` trong VS Code và chạy riêng `TestRedactedCopyDoesNotMutateInput` trước khi sửa source. Sau đó thay phần tạo `preview` bằng `preview := fields`. Đừng đoán bằng mắt: chạy lại test để thấy nó báo input đã bị mutate. Khôi phục code, xóa thân `redactedCopy`, rồi tự viết lại từ contract của test mà không nhìn implementation cũ. Đây là một bước nhỏ, nhưng nó buộc mental model “copy slice value vẫn có thể chia sẻ storage” đi qua một failure thật.

---

**Đáp án — chỉ đọc sau khi đã tự làm.** `preview := fields` chỉ copy slice descriptor, nên `preview[0]` vẫn sửa phần tử chung với `requestFields`. Bản đúng cần một backing array mới, chẳng hạn `make` rồi `copy`. Test phải giữ cả hai assertion: preview bị redacted và input không đổi; bỏ assertion thứ hai là bỏ mất contract ownership.

## String: bytes trước, text sau

String cũng là value, nhưng nó có luật riêng: string là immutable sequence of bytes. len đếm byte; index trả về byte. Text thường là UTF-8, song Go không yêu cầu mọi string phải chứa UTF-8 hợp lệ.

~~~go
text := "Việt"
fmt.Println(len(text)) // 6

for index, value := range text {
	fmt.Println(index, value)
}
~~~

Lab chạy đoạn này với kết quả:

~~~text
6
0 86
1 105
2 7879
5 116
~~~

V và i mỗi chiếm một byte. ệ được mã hóa bằng ba byte UTF-8, vì vậy rune tiếp theo bắt đầu ở byte index 5. range trên string decode UTF-8: giá trị thứ hai là rune, thường dùng để biểu diễn Unicode code point. byte là alias của uint8; rune là alias của int32. Code point vẫn không đồng nghĩa với “một ký tự người dùng nhìn thấy”: một grapheme có thể gồm nhiều code point. Ta chưa cần giải quyết segmentation ở đây; chỉ cần không nhầm len với số ký tự hiển thị.

String không cho phép gán trực tiếp `text[0] = 'v'`. Khi cần dữ liệu byte có thể sửa đổi, ta bắt buộc phải chuyển đổi sang `[]byte`, thao tác, rồi tạo chuỗi mới nếu cần. 

Về mặt bộ nhớ, phép chuyển đổi `b := []byte(text)` hoặc `s := string(b)` theo đặc tả Go luôn sao chép toàn bộ dữ liệu byte sang một vùng nhớ mới. Việc sao chép này là bắt buộc để bảo vệ tính bất biến của chuỗi: nếu chia sẻ cùng mảng nền, một thao tác ghi đè `b[0] = 'v'` sẽ làm biến đổi giá trị của chuỗi `text` ban đầu. Mặc dù có chi phí cấp phát, trình biên dịch Go cung cấp cơ chế tối ưu hóa không cấp phát (zero-allocation optimization) trong các ngữ cảnh tra cứu cục bộ: khi tra cứu map dạng `lookup[string(b)]` hoặc so sánh `string(b) == "target"`, compiler phát hiện chuỗi tạm không thoát khỏi biểu thức và tái sử dụng trực tiếp con trỏ của lát cắt byte mà không sinh ra bất kỳ lệnh cấp phát heap nào.

## Pointer là câu hỏi khác

Sau slice, pointer dễ bị giải thích sai như “slice nhưng rõ hơn”. Pointer là một value trực tiếp reference một variable khác; slice là một descriptor cho segment của underlying array. Chúng có thể cùng dẫn tới sharing, nhưng chúng trả lời hai câu hỏi khác nhau.

~~~go
count := 10
p := &count
*p = 99
fmt.Println(count) // 99
~~~

Ở đây &count tạo pointer tới variable count, còn *p truy cập variable đó. Pointer sẽ có chương riêng khi ta cần thiết kế API quanh mutation trực tiếp và nil. Trước khi đến đó, hãy giữ model vừa xây: luôn hỏi value nào được copy, và value ấy có reference tới storage hay variable nào không.

Nếu câu trả lời là “không”, assignment thường tạo independence như int và array. Nếu câu trả lời là “có”, aliasing có thể là công cụ tốt hoặc một bug - tùy việc bạn có làm rõ ownership và mutation hay không.

## Một quyết định ở ranh giới API

Khi một hàm nhận hoặc trả về slice, câu hỏi thiết kế không phải là “Go có copy không?” mà là: **ai được phép sửa storage này, và trong khoảng thời gian nào?** Một hàm lọc dữ liệu có thể trả về một view để tránh allocation; khi đó caller cần biết view ấy còn dùng chung buffer. Một hàm dựng response hoặc preview thường nên trả về dữ liệu độc lập, vì caller không có lý do để đoán một thay đổi sau đó sẽ đi ngược vào input.

Không có đáp án mặc định miễn phí. Copy tốn allocation và thời gian; chia sẻ tiết kiệm chúng nhưng làm contract về ownership quan trọng hơn. Trước khi tối ưu, hãy viết test cho hành vi mutation mà API hứa. Sau đó, khi đọc một bug khó hiểu, lần theo ba bước: value nào được gán, value đó reference storage nào, và ai còn có thể chạm storage ấy. Đó là cách biến “slice lạ quá” thành một cuộc điều tra có thể kiểm chứng.
