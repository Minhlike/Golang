# Quyết định thiết kế đề xuất

Không đổi thiết kế những gì đang đọc tốt. PDF đối chứng có serif đậm rõ, code đủ lớn, bảng có lưới và folio ngoài đúng phía trên các trang đã xem. Lợi ích chính của catalog là phân cấp H2–H4 rõ hơn, Atlas dễ đọc hơn và đường vector có source, không phải thay mọi trang bằng một khuôn mới.

## Một hệ thống trang ruột

| Vai trò | Font / size / leading (pt) | Quyết định |
|---|---|---|
| Part | Source Sans 3 semibold 30/36 | Một style; không tự thêm Part mới |
| Chapter/H1 | Source Sans 3 semibold 24/30 | KEEP cỡ; prototype bỏ rule nặng, không đổi nội dung |
| H2 | Sans semibold 17/23 | Chênh cấp rõ hơn baseline 15.5 |
| H3 | Sans semibold 14/19 | Một style, không tăng số cấp |
| H4 | Sans semibold 12.5/17 | Xử lý semantic heading, nhất là đáp án |
| Prose | Source Serif 4 regular 14/21.5 | KEEP; leading 1.536; đen tuyệt đối |
| Code/terminal | JetBrains Mono 11.5/15.5 | Text, 12 pt padding mỗi bên, không gutter/số dòng |
| Table body | Serif 11/15.5 | Lưới .5 pt; header nền E8; không cần color để phân biệt |
| Caption/metadata | Sans 10.5/14 | Tăng từ 9.8; không dùng xám nhạt cho paragraph |
| Error Atlas body/ID | Serif 10.5/14; Sans semibold 11/14.5 | Giữ gutter 8 mm, entry cùng khối; chấp nhận thêm trang |
| Header | Không running header ở production | KEEP; banner prototype chỉ nhận diện catalog |
| Footer/folio | Sans 9.5, #333 | Folio ngoài, 11.2 mm từ đáy; rule 15.2 mm; bìa sản xuất không folio |

A4 210×297 mm. Inner 24, outer 18, top 22, bottom 20 mm; khối 168×255 mm. Không tuyên bố lề 24 mm phù hợp mọi kiểu đóng. Nền trắng, code F2, callout F5, primary #000. Chỉ một bộ style trang ruột; không có ba phương án body/heading để ép tác giả chọn trong các mẫu gần giống nhau.

Line length phụ thuộc glyph: ưu tiên 65–85 ký tự với body 14 pt, không khóa quota cứng cho bảng/code. Không shrink diagram để giữ một số trang dự kiến. Code dài phải chia tại dòng source hợp lệ, có continuation rõ ràng, không lặp/sửa byte; universal splitting chưa được nghiệm thu qua catalog này.

## Bốn hướng artwork gốc

| Hướng / trang | Ưu | Nhược / in đen trắng | Chọn khi |
|---|---|---|---|
| A / 2 — exploded axonometric | Tách lớp rõ, trắng thoáng, vector | Có thể gợi mô hình bộ nhớ nếu đem vào technical figure: cấm. Nét nhỏ cần proof | Muốn nhận diện kỹ nghệ, cân bằng |
| B / 3 — architectural ink study | Đậm/nhạt nét cắt và đường dựng, nhiều cấu trúc | Fine lines có thể mất trên giấy hút mực; không phải bản vẽ công trình thật | Ưu tiên cảm giác sketchbook kỹ thuật |
| C / 4 — scientific contour | Tiết diện/đồng mức, nhịp hình khác A/B | Dễ moiré khi rasterize thấp; giữ vector, proof giấy | Ưu tiên minh họa trừu tượng như specimen |
| D / 5 — experimental typography | Chữ tạo hình, ít chi tiết nhỏ, tương phản mạnh | Artwork ít chiều sâu 3D; chữ lớn tốn mực tại vài vùng | Ưu tiên đơn giản, bền khi in |

Khuyến nghị thẩm mỹ của người thiết kế: A là hướng cân bằng; D là hướng ít rủi ro chi tiết nhỏ nhất. Đây là nhận định, không kết quả thử nghiệm thị hiếu. B/C cần proof in trước khi chốt. Không có artwork tải về hoặc ảnh AI trong catalog; tất cả đường nét do source prototype dựng, không dùng chúng để chứng minh cơ chế Go.

Bìa sau/gáy trang 7 chỉ thử hệ thống chữ và vùng thông tin. Không có wrap dieline, bleed/trim proof, ISBN hay lời giới thiệu bịa. Độ dày giấy, số tờ thực sau layout và kiểu đóng là dữ liệu đầu vào còn thiếu.

## Nghiên cứu có giới hạn rõ

Ngày tra cứu 2026-10-09. Nguồn sơ cấp dưới đây dùng cho thiết kế, không bổ sung citation mới vào manuscript.

[C4 notation](https://c4model.com/diagrams/notation): C4 không khóa một notation; diagram cần scope, ý nghĩa component và relationship rõ. Chỉ dùng nhãn C4 khi mô hình thật là context/container/component/code tương ứng. Array-copy là sơ đồ giá trị, không phải C4.

[OMG UML 2.5.1](https://www.omg.org/spec/UML/2.5.1): tham khảo khi object thật là sequence/activity/state theo UML. Mũi tên hay rounded rectangle đơn lẻ không đủ để tự nhận UML-compliant. Không tự đổi semantics bằng một notation mới.

[ISO/IEC/IEEE 42010:2022, abstract chính thức](https://www.iso.org/standard/74393.html): tiêu chuẩn mô tả kiến trúc/viewpoint, không phải preset palette/padding. Chỉ đọc trang abstract công khai, không mua/đọc toàn văn; không chứng nhận catalog đạt chuẩn này.

[RFC 7996](https://www.rfc-editor.org/rfc/rfc7996.txt): profile SVG dành cho RFC với giới hạn riêng, gồm monochrome black/white; không được đánh đồng với grayscale sách. Học tính đơn giản và vai trò hỗ trợ của diagram; catalog không tự nhận tuân thủ SVG 1.2 RFC.

[Manual of Section, Princeton Architectural Press](https://papress.com/products/manual-of-section): xem thực tế bìa trên website nhà xuất bản; đọc mô tả phương pháp cross-section perspective. Vận dụng chênh nét và khoảng trắng, không copy công trình/bố cục/artwork. Chưa mở toàn bộ 63 bản vẽ trong sách.

[Ruder Typography / Ruder Philosophy, Lars Müller](https://www.lars-mueller-publishers.com/ruder-typographyruder-philosophy): đã xem bìa trong browser, nghiên cứu cách chữ có thể là thành phần thị giác. Catalog D là bố cục mới, không sao lại chữ viết tay/hình của mẫu.

[Elements of Architecture, OMA](https://www.oma.com/publications/elements-of-architecture): nguồn publisher/architect về biên tập các thành phần; dùng như nghiên cứu decomposition và framing, không khẳng định đã xem từng spread hoặc tìm thấy mẫu exploded giống bìa A.

[Smithsonian, Drawing Insects](https://www.si.edu/spotlight/buginfo/drawing-insects) và [hồ sơ minh họa khoa học Sydney Prentice](https://repository.si.edu/items/0cd02ba1-bf2e-48bd-beba-a0cbb6215766/full): record nghiên cứu có điểm neo; trang ảnh bị request verification, bitstream timeout. **VISUAL_REFERENCE=UNKNOWN** cho nhánh này; không ghi đã quan sát plate. C là contour study trừu tượng tự dựng, không phải scientific illustration đã được chứng thực.

[Deconstructivist Architecture, catalog MoMA](https://assets.moma.org/documents/moma_catalogue_1813_300062863.pdf): đã mở actual render 150 dpi trang PDF 60–61, folio in 57–58. Trang 60 là ảnh mô hình kiến trúc đen trắng; trang 61 là exploded axonometric Biocenter (hình 47): các khối rời, spine và tổ hợp bên dưới nối bằng đường chiếu chấm. Quan sát trực tiếp cho thấy hiệu quả của trục phân lớp và khoảng trắng, đồng thời nét scan mảnh cho thấy vì sao bản mẫu mới cần contrast mạnh hơn. Đây là tham chiếu editorial 3D/axonometric thực tế, không sao mô hình hoặc đường nét vào artwork A/B. Bản tải nghiên cứu và PNG chỉ nằm trong `renders/` được gitignore, không đưa catalog MoMA vào Git.

[Diasia iridifolia, National Gallery of Art](https://www.nga.gov/artworks/205899-diasia-iridifolia): đã xem hình thực trên browser, không dựa vào visual description tự sinh của trang. Quan sát thân cây mảnh, rễ/củ, các hình chi tiết tách bên cạnh và vùng trống lớn; học cách tách hình chính/chi tiết mà không nhồi chú giải. Mẫu dùng màu, không phải bằng chứng in đen trắng và không chứng thực contour C là minh họa khoa học. Không tải/copy artwork vào catalog.

Đã quan sát mẫu thực cho các nhánh architecture, experimental typography, editorial 3D/exploded và scientific illustration; đây là nghiên cứu mẫu có chủ đích, không khảo sát toàn bộ lịch sử từng phong cách. Smithsonian vẫn UNKNOWN riêng; không dùng lần truy cập lỗi làm bằng chứng. Chỉ artwork prototype gốc đã qua grayscale pixel scan; mẫu nghệ thuật tham khảo không được gọi là đã proof in.

## Diagram mẫu

Trang 10 dùng vector selectable text từ source array-copy: giữ 8 nhãn, hai nút a/b, cạnh nét đứt a→b, hai note gắn đúng nút và caption gốc. `diagram_semantics.json` neo hash PUML. Đây là restyle thủ công của một sơ đồ nhỏ, không phải bộ chuyển PlantUML tổng quát và không claim lại tính đúng của mọi diagram trong sách.

Trang 11/16 giữ informer raster cùng source/caption, kích thước hữu hiệu 341.2 dpi cả hai chiều. Mục đích là chứng minh KEEP cũng là quyết định kỹ thuật. Nhãn raster không selectable; ưu tiên vector khi có pipeline đối chiếu nhãn/cạnh đáng tin, không biến “ưu tiên” thành lý do vẽ lại vội tất cả.
