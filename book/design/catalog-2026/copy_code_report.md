# Copy code: chưa đạt cổng byte fidelity

Kết luận: **COPY_BYTE_IDENTITY=FAIL / TWO_READER_CLIPBOARD=UNKNOWN**. Không có số dòng hay gutter trong code mẫu. Baseline thực tế cũng không có số dòng/gutter; thanh accent 2 pt là border, không phải một cột rỗng cần xóa.

`scripts/build_pdf.py:419` đưa `"\n".join(chunk).expandtabs(4)` vào Preformatted. Với TAB thật, biến đổi này làm mất byte 0x09 trước khi sinh PDF. `splitlines()` và join cũng chuẩn hóa newline, vì vậy không thể cam kết giữ CRLF/LF nguyên gốc chỉ nhờ renderer này. Chưa sửa production.

## Thí nghiệm catalog trang 22

`copy_fixture.txt` chứa TAB literal, ă/â/ê/ô/ơ/ư/đ, hai dấu cách cuối dòng, dòng rỗng và LF. SHA `f14408de1de0160565ebf27141450e5b9de4cdb9291da56513d115f41263d831`. Sau expandtabs(4), SHA `ed780f88827933d467c674ca7510b2d357c5f97ca4a2182dcdd8d807d82ec10c`: khác. Unit test xác nhận LF và CRLF cũng khác byte.

Mẫu A dùng text vẽ thông thường, tab-stop hiển thị bốn cột. Mẫu B cùng hình thức nhưng thêm PDF marked-content ActualText UTF-16BE chứa payload nguyên gốc. Đây là experiment, không phải giải pháp đã nghiệm thu.

| Kiểm tra | Kết quả và bằng chứng |
|---|---|
| Text chọn/extract được | PASS bằng hai thư viện extract; Unicode đọc đúng |
| Indentation hiển thị | PASS sau mở ảnh actual trang 22; không phải test clipboard |
| expandtabs giữ TAB byte | FAIL: hash khác, TAB đổi thành space |
| Exact fixture trong PyMuPDF 1.28.2 | FAIL: có 1 TAB do ActualText nhưng thêm newline; payload không xuất hiện nguyên byte |
| Exact fixture trong pypdf 6.10.0 | FAIL: 0 TAB; cả hai mẫu không giữ fixture nguyên byte |
| Unicode trong hai extractor | PASS: chuỗi dấu tiếng Việt có mặt ở cả hai |
| Whitespace/newline nguyên byte | FAIL trên fixture, không chuẩn hóa rồi gọi PASS |
| Clipboard PDF reader thứ nhất | UNKNOWN / NOT_RUN |
| Clipboard PDF reader thứ hai | UNKNOWN / NOT_RUN |

Hai extractor **không** phải hai PDF reader. Phiên này chưa thực hiện chọn/copy/paste tương tác trong hai reader, nên không có tên/version/screenshot reader giả. Native app automation không được cung cấp trong phiên; browser nghiên cứu hình thức không thay thế clipboard acceptance.

Raw extraction nằm trong `copy_extracted_pymupdf.txt` và `copy_extracted_pypdf.txt`, phép đo trong `copy_code_results.json`. Unit test cũng kiểm tra code TAB của câu hỏi Ch1 vẫn nguyên trong object payload trước vẽ. Source preservation PASS không đồng nghĩa clipboard preservation PASS.

## Acceptance trước tích hợp

Trên hai reader độc lập có tên/version rõ, chọn riêng từng block A/B; paste vào file UTF-8 ở thư mục prototype. So raw bytes/hash với fixture, không trim, không expandtabs, không gộp newline. Thử cả code gốc Ch1 và fixture LF/CRLF với tab giữa dòng, indentation, blank/trailing whitespace. Chỉ khi contract được chứng minh trên reader thực mới chốt policy code-copy; ActualText hiện tại chưa đủ. File source tải kèm có thể là đường dự phòng nếu người dùng duyệt, nhưng không được đổi yêu cầu clipboard thành “có file kèm” mà tự gọi PASS.
