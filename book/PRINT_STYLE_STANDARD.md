# Quy chuẩn in ấn — đối chiếu source ngày 01-10-2026

Nguồn thông số là `scripts/book_style.py`; font được đăng ký trong `scripts/build_pdf.py`. Đây là contract cấu hình, không phải nhãn visual QA cho mọi bản build. Render, embedding, printable frame và grayscale phải được kiểm tra trên đúng PDF cuối.

## Trang và khung nội dung

A4 210 × 297 mm. Lề trong 2,4 cm, ngoài 1,8 cm, trên 2,2 cm, dưới 2,0 cm; khung rộng 16,8 cm và cao 25,5 cm. Trang lẻ bắt đầu ở x=2,4 cm, trang chẵn ở x=1,8 cm. Folio ở mép ngoài; bìa không có folio. Gutter này không bảo đảm mọi cách đóng gáy đều đọc thoải mái: nhà in còn cần xét độ dày, loại giấy và binding thực.

## Typography

| Vai trò | Font | Cỡ / leading (pt) | Màu |
| --- | --- | --- | --- |
| Tên sách | Source Sans 3 Semibold | 42 / 48 | #000000 |
| H1 | Source Sans 3 Semibold | 24 / 30 | #000000 |
| H2 | Source Sans 3 Semibold | 15,5 / 21 | #000000 |
| H3 | Source Sans 3 Semibold | 13 / 18 | #000000 |
| Thân bài | Source Serif 4 Regular | 14 / 21,5 | #000000 |
| Code block | JetBrains Mono Regular | 11,5 / 15,5 | #000000 |
| Bảng | Source Serif 4 Regular | 10,5 / 14,5 | #000000 |
| Caption | Source Sans 3 Regular | 9,8 / 13,5 | #3A3A3A |
| Reference | Source Sans 3 Regular | 9,5 / 13 | #606060 |

Body line-height khoảng 1,54; đoạn cách sau 9 pt. Các heading giữ cùng nội dung tiếp theo. Error Atlas là bố cục tra cứu hai cột, có style riêng 9–12 pt, không giả làm body 14 pt. Không giảm font để chữa overflow; tách code hợp lệ, giới hạn table và kiểm tra actual render. Cỡ cấu hình không tự chứng minh readability ở 100%.

## Grayscale và cấu trúc

Nền trắng; code #F2F2F2, table header #E6E6E6, callout #F5F5F5. Viền code 0,6 pt, table grid 0,4 pt. Màu không mang nghĩa duy nhất: nhãn và topology phải còn rõ khi in đen trắng.

Thứ tự xuất bản: bìa và TOC, chương lịch sử mở đầu, Ch00–Ch29 hiện có, Library Atlas, Error Atlas cuối cùng. TOC và bookmark phải khớp heading thật sau pagination; không suy ra từ số chương hoặc build thành công.

## Bằng chứng cần có sau thay đổi

Thông số font/margin là mục tiêu của renderer. Bản PDF cuối cần preflight box/rotation/font/DPI, kiểm tra actual pixels, TOC/bookmark/cross-reference, code/table width và mở từng trang thay đổi cùng trang lân cận có rủi ro reflow. Kết quả chỉ ghi trong `book/FINAL_PUBLICATION_QA.md` sau kiểm tra, gắn đúng SHA-256.
