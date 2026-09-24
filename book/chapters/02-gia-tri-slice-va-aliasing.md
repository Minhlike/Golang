# Chương 2 — Khi một bản sao vẫn chia sẻ dữ liệu

Chạy đoạn này trước khi cố giải thích nó. Nếu bạn đoán a và b khác nhau sau dòng b[0] = 99, đó là một dự đoán rất hợp lý - và cũng là cánh cửa vào phần này.

~~~go
a := []int{10, 20, 30}
b := a
b[0] = 99

fmt.Println(a)
fmt.Println(b)
~~~

Kết quả từ lab part2-các giá trị là:

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

Go đã copy giá trị của a vào b. Sau đó b nhận giá trị mới; a không có lý do gì để đổi. Đây là quy tắc nền: assignment copy giá trị. Điều còn thiếu là một giá trị có thể chứa gì.

Array giúp ta kiểm tra quy tắc ấy với nhiều phần tử. Độ dài là một phần của type, nên [3]int và [4]int là hai array type khác nhau. Khi array được gán, toàn bộ array giá trị được copy.

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

[]int không phải array không ghi độ dài. Nó là slice type. Một slice giá trị mô tả một đoạn liên tiếp của mảng nền. Ngôn ngữ định nghĩa slice giá trị có length, capacity và một reference tới mảng nền. Đó là mental model hữu ích cho semantics; nó không phải lời hứa rằng mọi Go implementation phải dùng đúng một struct hay ABI như hình.

![Hai slice value sau assignment: descriptor được copy, backing storage được chia sẻ.](../../assets/diagrams/slice-sharing.png)

@figure b := a copy slice giá trị, gồm cửa sổ nhìn vào dữ liệu, len và cap. Cả hai bộ mô tả (descriptor) vẫn dẫn tới cùng mảng nền, nên b[0] thay đổi phần tử mà a cũng nhìn thấy.

Vì vậy hai câu sau cùng đúng, và không mâu thuẫn:

@table Copy giá trị và chia sẻ storage là hai tầng khác nhau của cùng một phép gán.

| Câu nói | Đúng ở đâu? |
| --- | --- |
| Assignment copy giá trị. | b nhận một slice giá trị riêng: đổi len của b bằng cắt lại lát cắt không tự đổi len của a. |
| Hai slice có thể cùng đổi dữ liệu. | Slice giá trị có thể cùng reference một mảng nền; biến đổi dữ liệu một element hiện ra qua mọi slice cùng nhìn element đó. |

Từ chồng lấn ô nhớ (aliasing) dùng cho tình huống nhiều đường tham chiếu đến cùng dữ liệu. Nó không phải lỗi tự thân. chồng lấn ô nhớ (aliasing) giúp cắt một cửa sổ trên vùng đệm mà không copy cả vùng đệm. Nó thành bug khi một người đọc tưởng mình có dữ liệu riêng nhưng thực tế lại đang sửa vùng dùng chung.

## Cửa sổ, length và capacity

Đặt một slice lên một slice khác để thấy bộ mô tả (descriptor) thực sự đang mô tả gì.

~~~go
base := []int{10, 20, 30, 40, 50}
x := base[1:3]

fmt.Println(x)      // [20 30]
fmt.Println(len(x)) // 2
fmt.Println(cap(x)) // 4
~~~

x bắt đầu ở phần tử 20 của base và kết thúc trước 40. Vì thế length là 2. Capacity đếm số phần tử từ điểm bắt đầu của x đến cuối mảng nền mà x hiện có thể mở rộng tới; ở đây là 20, 30, 40, 50, nên là 4.

![Một slice window: vùng thấy được là len; phần còn có thể mở rộng là capacity.](../../assets/diagrams/slice-window.png)

@figure x nhìn thấy hai phần tử đầu của cửa sổ. cap(x) không nói x đang có bốn phần tử; nó nói x có thể được cắt lại lát cắt hoặc append trong phạm vi mảng nền hiện tại.

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

append không hứa luôn dùng lại array cũ, cũng không hứa luôn tạo array mới. Nó trả về resulting slice. Khi mảng nền còn chỗ, implementation có thể dùng lại; khi capacity không đủ, append phải cấp mảng nền mới đủ lớn cho kết quả. Vì return giá trị mang bộ mô tả (descriptor) có thể đã đổi, viết s = append(s, giá trị) là dạng thông thường.

~~~go
s := make([]int, 2, 4)
s[0], s[1] = 10, 20
old := s

s = append(s, 30)
s[0] = 99

fmt.Println(old) // [99 20]
fmt.Println(s)   // [99 20 30]
~~~

Ở đây s còn capacity. old và s có length khác nhau, nhưng vẫn có thể cùng nhìn hai element đầu của mảng nền. Ngược lại, full slice biểu thức bên dưới giới hạn capacity của view ở 2, nên append buộc phải có storage khác cho grown:

~~~go
old := []int{10, 20}
s := old[:2:2]
grown := append(s, 30)
grown[0] = 99

fmt.Println(old)   // [10 20]
fmt.Println(grown) // [99 20 30]
~~~

![Hai kết quả của append: còn capacity thì có thể chia sẻ; hết capacity thì resulting slice đi tới storage mới.](../../assets/diagrams/append-storage.png)

@figure Hình mô tả hai semantics mà mã nguồn phải chịu được. Đừng suy luận allocation từ một capacity tình cờ; nếu mã nguồn cần một kết quả riêng, hãy tạo bản copy có chủ ý.

## Một chồng lấn ô nhớ (aliasing) bug có người dùng thật

Một hàm “chỉ chuẩn bị preview” đôi khi phá dữ liệu của bên gọi.

~~~go
func redactPreview(fields []string) {
	fields[0] = "***"
}

requestFields := []string{"api-key", "region"}
redactPreview(requestFields)
fmt.Println(requestFields) // [*** region]
~~~

tham số fields nhận một slice giá trị mới, nhưng bộ mô tả (descriptor) ấy vẫn reference storage của requestFields. Việc đổi element là biến đổi dữ liệu shared storage. Nếu mục tiêu thật sự là tạo preview độc lập, copy phần tử sang một slice mới trước:

~~~go
func redactedCopy(fields []string) []string {
	preview := make([]string, len(fields))
	copy(preview, fields)
	preview[0] = "***"
	return preview
}
~~~

copy sao chép tối đa số phần tử vừa với destination và trả về số phần tử đã copy. Ở đây make tạo mảng nền mới, nên preview độc lập ở tầng slice elements. Đổi lấy independence là allocation và chi phí copy; với vùng đệm lớn hoặc đường xử lý nóng, đó là một quyết định cần có lý do. Với một preview cần an toàn khỏi biến đổi dữ liệu, nó diễn đạt đúng intent.

**Thực hành - bug hunt có kiểm chứng.** Mở `labs/part2-values` trong VS mã nguồn và chạy riêng `TestRedactedCopyDoesNotMutateInput` trước khi sửa source. Sau đó thay phần tạo `preview` bằng `preview := fields`. Đừng đoán bằng mắt: chạy lại test để thấy nó báo input đã bị mutate. Khôi phục mã nguồn, xóa thân `redactedCopy`, rồi tự viết lại từ contract của test mà không nhìn implementation cũ. Đây là một bước nhỏ, nhưng nó buộc mental model “copy slice giá trị vẫn có thể chia sẻ storage” đi qua một failure thật.

---

**Đáp án — chỉ đọc sau khi đã tự làm.** `preview := fields` chỉ copy slice bộ mô tả (descriptor), nên `preview[0]` vẫn sửa phần tử chung với `requestFields`. Bản đúng cần một mảng nền mới, chẳng hạn `make` rồi `copy`. Test phải giữ cả hai assertion: preview bị redacted và input không đổi; bỏ assertion thứ hai là bỏ mất contract ownership.

## String: bytes trước, text sau

String cũng là giá trị, nhưng nó có luật riêng: string là immutable sequence of bytes. len đếm byte; index trả về byte. Text thường là UTF-8, song Go không yêu cầu mọi string phải chứa UTF-8 hợp lệ.

~~~go
text := "Việt"
fmt.Println(len(text)) // 6

for index, giá trị := range text {
	fmt.Println(index, giá trị)
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

V và i mỗi chiếm một byte. ệ được mã hóa bằng ba byte UTF-8, vì vậy rune tiếp theo bắt đầu ở byte index 5. range trên string decode UTF-8: giá trị thứ hai là rune, thường dùng để biểu diễn Unicode mã nguồn point. byte là alias của uint8; rune là alias của int32. mã nguồn point vẫn không đồng nghĩa với “một ký tự người dùng nhìn thấy”: một grapheme có thể gồm nhiều mã nguồn point. Ta chưa cần giải quyết segmentation ở đây; chỉ cần không nhầm len với số ký tự hiển thị.

String không cho gán trực tiếp text[0] = 'v'. Khi cần dữ liệu byte có thể sửa, chuyển sang []byte, thao tác, rồi tạo string mới nếu cần. Việc chuyển đổi đó diễn đạt một thay đổi ý định: từ text immutable sang vùng đệm mutable.

## con trỏ là câu hỏi khác

Sau slice, con trỏ dễ bị giải thích sai như “slice nhưng rõ hơn”. con trỏ là một giá trị trực tiếp reference một biến khác; slice là một bộ mô tả (descriptor) cho segment của mảng nền. Chúng có thể cùng dẫn tới sharing, nhưng chúng trả lời hai câu hỏi khác nhau.

~~~go
count := 10
p := &count
*p = 99
fmt.Println(count) // 99
~~~

Ở đây &count tạo con trỏ tới biến count, còn *p truy cập biến đó. con trỏ sẽ có chương riêng khi ta cần thiết kế API quanh biến đổi dữ liệu trực tiếp và nil. Trước khi đến đó, hãy giữ model vừa xây: luôn hỏi giá trị nào được copy, và giá trị ấy có reference tới storage hay biến nào không.

Nếu câu trả lời là “không”, assignment thường tạo independence như int và array. Nếu câu trả lời là “có”, chồng lấn ô nhớ (aliasing) có thể là công cụ tốt hoặc một bug - tùy việc bạn có làm rõ ownership và biến đổi dữ liệu hay không.

## Một quyết định ở ranh giới API

Khi một hàm nhận hoặc trả về slice, câu hỏi thiết kế không phải là “Go có copy không?” mà là: **ai được phép sửa storage này, và trong khoảng thời gian nào?** Một hàm lọc dữ liệu có thể trả về một view để tránh allocation; khi đó bên gọi cần biết view ấy còn dùng chung vùng đệm. Một hàm dựng phản hồi hoặc preview thường nên trả về dữ liệu độc lập, vì bên gọi không có lý do để đoán một thay đổi sau đó sẽ đi ngược vào input.

Không có đáp án mặc định miễn phí. Copy tốn allocation và thời gian; chia sẻ tiết kiệm chúng nhưng làm contract về ownership quan trọng hơn. Trước khi tối ưu, hãy viết test cho hành vi biến đổi dữ liệu mà API hứa. Sau đó, khi đọc một bug khó hiểu, lần theo ba bước: giá trị nào được gán, giá trị đó reference storage nào, và ai còn có thể chạm storage ấy. Đó là cách biến “slice lạ quá” thành một cuộc điều tra có thể kiểm chứng.
