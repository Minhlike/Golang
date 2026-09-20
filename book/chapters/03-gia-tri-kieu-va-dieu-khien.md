# Chương 3. Giá trị, kiểu và điều khiển luồng

Sau khi chương trình đã có điểm bắt đầu, câu hỏi kế tiếp không phải là Go có
bao nhiêu keyword mà là dữ liệu này có ý nghĩa gì, và chương trình được phép
làm gì với nó. Kiểu trả lời phần đầu; control flow trả lời phần sau. Nếu hai
thứ mơ hồ, một tool vận hành nhỏ cũng nhanh chóng thành chuỗi if mà không ai
dám sửa.

## Kiểu là ràng buộc có ích

Go có suy luận kiểu ở chỗ dễ thấy nhất: attempts := 3 tạo biến attempts có
kiểu int. Nhưng compiler vẫn phải biết kiểu chính xác trước khi chạy. Vì vậy
đoạn sau không hợp lệ; Go không tự đổi string sang số chỉ vì người đọc đoán
được ý định.

~~~go
var timeoutMS int = 500
timeoutMS = "500" // compile error
~~~

Sự từ chối này hơi bất tiện vào ngày đầu, nhưng rất có ích với cấu hình và dữ
liệu từ network. Một field "500" trong JSON, một duration 500ms, và một con số
500 có thể cùng trông giống nhau nhưng là ba biểu diễn khác nhau. Chọn đúng
kiểu sớm sẽ để compiler bắt những nhầm lẫn rẻ nhất.

Khi ý nghĩa không rõ từ biểu thức bên phải, hãy viết kiểu. var retries uint8
không chỉ thông báo phạm vi số; nó còn buộc người đọc hỏi liệu giới hạn 255 có
phải quy tắc nghiệp vụ thật hay không. Với port, latency hay số byte, int là
điểm bắt đầu thường tiện, nhưng API public nên thể hiện đơn vị trong tên:
timeoutMS, maxBytes, attempts. Go không có type an toàn đơn vị dựng sẵn; tên tốt
và boundary validation vẫn rất quan trọng.

## Hằng số, conversion và phép toán

const biểu diễn một giá trị không được gán lại trong source. Hằng số số học
không kiểu có thể mang giá trị chính xác cho tới khi ngữ cảnh buộc nó vào kiểu;
đó là lý do const secondsPerMinute = 60 dùng được linh hoạt. Còn biến có kiểu
thì mọi phép gán và conversion phải tuân luật kiểu của nó.

~~~go
const kib = 1024
var bytes int64 = 8 * kib

workers := 3
perWorker := bytes / int64(workers) // conversion là chủ đích
~~~

Conversion không phải validation. int64(3.9) cắt phần lẻ, và ép một int lớn về
kiểu nhỏ hơn có thể mất dữ liệu. Nếu dữ liệu đến từ config hoặc request, hãy
kiểm tra range trước khi conversion. Đó là chỗ ta bảo vệ boundary, thay vì hy
vọng loại dữ liệu ở phía ngoài sẽ luôn tử tế.

## Scope và shadowing: hai biến cùng tên không phải một

Biến sống trong scope được bao bởi block. Điều này giúp giữ trạng thái cục bộ,
nhưng := có thể tạo biến mới và che biến cũ. Đây là lỗi rất hay gặp khi một
nhánh xử lý error rồi vô tình trả biến bên ngoài chưa được cập nhật.

~~~go
result := "unknown"
if ok := true; ok {
    result := "healthy" // biến mới, chỉ sống trong if
    _ = result
}
fmt.Println(result) // unknown
~~~

Khởi tạo ngắn trước điều kiện if là hợp lệ và thường hữu ích với err, vì nó
giới hạn vòng đời biến. Nhưng nếu anh cần giá trị sau block, đừng dùng := một
cách phản xạ. Viết result = "healthy", hoặc chọn tên khác, làm ý định rõ hơn
và giảm một bug mà compiler không thể luôn đoán giúp.

## if, switch và for là ít hơn để kiểm tra nhiều hơn

Go chỉ có for cho lặp. Nó có thể giống while, vòng ba phần cổ điển, hoặc lặp vô
hạn có điều kiện thoát. Không có while riêng nghĩa là người đọc chỉ cần nhận
diện một cấu trúc, không phải ba tên gọi cho ba biến thể gần nhau.

~~~go
for attempts := 0; attempts < 3; attempts++ {
    if attempts == 2 {
        fmt.Println("last planned attempt")
    }
}
~~~

switch trong Go dừng sau case khớp; nó không fall through ngầm như C. Điều này
làm case an toàn hơn để mô tả trạng thái. switch không có biểu thức cũng hữu
ích để thay một chuỗi điều kiện đọc từ trên xuống, nhất là khi điều kiện liên
quan range.

~~~go
switch {
case latencyMS < 0:
    status = "invalid"
case latencyMS < 200:
    status = "healthy"
case latencyMS < 1000:
    status = "degraded"
default:
    status = "unhealthy"
}
~~~

Thứ tự case là một phần logic. Nếu để latencyMS < 1000 lên trước, case dưới
200 sẽ không bao giờ chạy. Với threshold, bảng test tốt hơn cảm giác nhìn có vẻ
đúng: nó ghi lại chính xác 199, 200, 999 và 1000 phải thuộc nhóm nào.

## Zero value cần ngữ cảnh

Zero value giúp code nhỏ khởi động nhanh, nhưng nó không nói liệu dữ liệu có
được cấu hình hay không. var port int là 0; trong một số API network, port 0
có thể yêu cầu hệ điều hành chọn port tạm. Nếu config của anh dùng 0 để biểu
thị không điền, cần kiểm tra nó ở boundary chứ không để ý nghĩa mơ hồ trôi sâu
vào chương trình.

Ta sẽ học slice, map và nil chi tiết hơn ở chương dữ liệu. Hiện tại chỉ cần
nhớ: zero value là giá trị thật theo type, không phải một nhãn chung cho chưa
có gì.

## Lab: phân loại latency có ranh giới rõ

Lab labs/ch03-status có hàm ClassifyLatency. Đọc test trước, tự dự đoán kết quả
ở các biên 0, 199, 200, 999 và 1000, rồi mới chạy test. Khi sửa threshold, anh
phải sửa cả implementation lẫn expectation có chủ đích; đừng chỉ làm test xanh
bằng cách nới điều kiện mơ hồ.

### Bài tập

Hàm sau trả degraded cho latencyMS bằng 200 hay healthy? Không chạy trước. Sau
đó đổi thứ tự hai case đầu và giải thích vì sao test boundary sẽ phát hiện lỗi.

~~~go
func ClassifyLatency(latencyMS int) string {
    switch {
    case latencyMS < 200:
        return "healthy"
    case latencyMS < 1000:
        return "degraded"
    default:
        return "unhealthy"
    }
}
~~~

---

### ĐÁP ÁN - chỉ đọc sau khi đã tự làm

200 không thỏa điều kiện nhỏ hơn 200, nên đi vào case thứ hai và trả degraded.
Nếu đưa điều kiện nhỏ hơn 1000 lên đầu, mọi giá trị nhỏ hơn 200 cũng bị nó bắt
trước; case healthy trở thành unreachable về mặt logic dù compiler không nhất
thiết báo lỗi. Test với 199 sẽ thất bại, cho ta bằng chứng về rule bị đổi chứ
không chỉ một output ngẫu nhiên.

## Tóm lại

Kiểu và conversion làm dữ liệu có hình dạng rõ; tên biến và validation thêm ý
nghĩa mà type đơn lẻ không mang nổi. if, switch và for ít nhưng đủ, miễn anh
coi thứ tự điều kiện là logic có thể kiểm thử. Chương sau sẽ dùng hàm để đặt
ranh giới nhỏ cho logic đó, rồi xử lý error mà không đẩy mọi tình huống xấu vào
panic.

## Nguồn

- Go Language Specification: Constants, Variables, Assignments, Statements.
- Effective Go: Control structures.
