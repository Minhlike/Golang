# Kiểm kê đối tượng hiện hành

Nguồn sự thật: 33 Markdown hiện hành tại baseline. `object_inventory.json` lưu từng block với source, dòng, loại và raw SHA; không lấy text PDF cũ thay cho Markdown. 5.692 block gồm 2.710 blank, 31 comment, 148 rule và 2 pagebreak; phần còn lại là nội dung. Cách phân loại code/terminal theo nhãn fence là heuristic minh bạch, không đoán mỗi lệnh là output thực nghiệm.

Renderer chính: `scripts/build_pdf.py`; style/frame/cover/footer: `scripts/book_style.py`; riêng Error Atlas dùng `add_error_atlas`. 56 `.puml` + 1 `.iuml`, hai sơ đồ Ch22 dùng `scripts/render_ch22_diagrams.py`; tổng 58 image references và 58 figure directives. Các nguồn này không bị sửa.

## 30 lớp đối tượng

| Object / số thực tế | Nguồn, renderer và chức năng | Quy chuẩn hiện tại / KEEP | Đề xuất, lợi ích và rủi ro hồi quy |
|---|---|---|---|
| 1. Bìa trước / 1 | `cover`, `draw_vector_cover_art`; nhận diện | Sans 42; artwork vector ô chữ nhật | 4 artwork gốc A–D, không sao chép; chỉ nghệ thuật. Rủi ro nét nhỏ khi in, kiểm proof |
| 2. Bìa sau / chưa có | Không có renderer/object riêng | Không tự viết blurb/ISBN | Placeholder catalog, chờ nội dung được duyệt; không coi là bìa in hoàn chỉnh |
| 3. Gáy / chưa có | Không có production source | Không đoán chiều dày | Nhận diện cùng font bìa; width UNKNOWN, phụ thuộc giấy/đóng |
| 4. Part / không có page template riêng | Các heading PHẦN trong Library Atlas | Giữ nhóm/thứ tự source | Một style Part Sans 30/36, chỉ áp vào heading vốn là phần sau duyệt; nguy cơ đổi cấp H2 nhầm |
| 5. Chapter/H1 / 33 | `add_markdown`, Atlas intro; định vị chapter/front/back matter | Sans semibold 24/30, keepWithNext | KEEP cỡ; prototype dùng khoảng trắng thay rule nặng. Không làm opener rỗng cho mọi chương |
| 6. H2 / 275 | Markdown `##`, style h2; mục lớn | 15.5/21; không thêm mục | 17/23 tạo chênh cấp rõ hơn. Rủi ro thêm trang và orphan |
| 7. H3 / 279 | Markdown `###`, Atlas entries; tiểu mục/ID | 13/18 hoặc Atlas ID riêng | Trang ruột 14/19; Atlas ID 11/14.5. Giữ ID và contract kiểu lỗi |
| 8. H4 / 11 | Markdown `####`, ví dụ đáp án Ch1 | Main parser chỉ nhận H1–H3: source-only integration risk | Một style 12.5/17; không in literal hash. Prototype xử lý riêng, không vá production |
| 9. Font / 5 TTF | `assets/fonts`, `register_fonts` | Source Serif 4 regular/semibold; Source Sans 3 regular/semibold; JetBrains Mono | KEEP toàn bộ. Không decorative font cho nội dung; font fallback phải đo glyph, không tự PASS |
| 10. Prose / 1.569 block | `flush_paragraph`; dòng lập luận | Serif 14/21.5, #000 | KEEP, không rewrite. AllowWidows/Orphans=0 trong prototype; không ép lấp trang |
| 11. Code / 262 fence | `flush_code`; implementation/reproducer | Mono 11.5/15.5; không có số dòng/gutter ở baseline | KEEP text/cỡ; bỏ accent bar trong mẫu. TAB expansion mất byte, blocker riêng |
| 12. Terminal/output / 57 fence | Cùng `flush_code`, nhãn text/sh/bash/... | Không thay lệnh/output/version | Cùng code spec, không syntax coloring output. Không khẳng định 57 đều là measured output |
| 13. Table / 61 | `flush_table`, taxonomy/reflex Atlas; phân biệt dữ liệu | Grid, header background, repeatRows, weight theo token | KEEP grid/semantics; body 11/15.5 mẫu. Rủi ro token dài/cột hẹp và split rows |
| 14. Diagram / 58 references | PNG từ PlantUML hoặc Ch22 Python | Label/cạnh/quan hệ/caption đã có source | Vector mẫu array-copy; hình phức tạp KEEP raster 341.2 dpi trong catalog. Không gọi mọi sơ đồ UML/C4 |
| 15. Ảnh/photo / không có lớp photo riêng | Image parser không tách photograph khỏi diagram | Không tự thêm ảnh minh họa | Chỉ thêm nếu có chức năng và source; không dùng AI image làm technical evidence |
| 16. Figure caption / 58 | `@figure`, counter tự động/KeepTogether | Caption Sans 9.8/13.5, text nguồn | 10.5/14; caption mẫu không dùng số global của sách. Nguy cơ caption rời hình/sai context |
| 17. Table caption / 20 | `@table`, counter | Auto-number theo thứ tự | KEEP thứ tự; tăng caption 10.5. 41 bảng còn lại không tự bịa caption |
| 18. Bài tập / prose, chưa có object typed | Requirement/bug/test trong chapters | Giữ đúng thời điểm và mức tự chủ | Dùng prose/callout phù hợp bản chất, không tạo box cuối mọi bài |
| 19. Câu hỏi / prose-callout | Ví dụ dự đoán Ch1; không có tag question riêng | Câu hỏi và code nguyên văn | Mẫu trang 12; pause có lý do. Rủi ro layout chèn đáp án quá sớm |
| 20. Đáp án / H4-prose | Ch1 và các H4 còn lại | Source là authority, không lấy từ PDF cũ | Trang 13 sau câu hỏi; không buộc mọi đáp án sang trang mới khi tích hợp |
| 21. Ghi chú/callout / 52 | Blockquote `>`; policy/cảnh báo | Nền F5, body 14, accent bar | Mẫu border .6, không gutter; phải giữ wording và mức cảnh báo |
| 22. List đặc biệt / 49 block | Ordered references, diagnostics Atlas, số bước | Không biến prose thành bullet factory | Giữ số bước; diagnostic xuống dòng riêng, không ghép thành một chuỗi |
| 23. Tài liệu tham khảo / 17 marker | `@references` đổi mode; nguồn/point of verification | Current 9.5/13, dark gray | Prototype trang 21 giữ 7 reference gốc ở body size để thử chiều dài; style giảm riêng chỉ sau đọc lâu, không tự chốt thiếu mẫu |
| 24. TOC / 1 | `chapter_pages`, TOC table; 33 entry | Page 2, 10.5 pt; H1/source order | KEEP auto page identity; catalog dùng 12 link và 19 bookmarks. Không tuyên bố đã test lại TOC toàn sách |
| 25. Header / không có running header | `MirroredDocTemplate` | KEEP production không header | Banner GOLANG/DESIGN chỉ đánh dấu catalog, không là nội dung sách. Nếu muốn header chapter cần duyệt riêng |
| 26. Footer / 492 trang có folio | `draw_footer`; đường rule/điều hướng | Rule 15.2 mm, folio 11.2 mm từ đáy | KEEP vị trí; catalog 9.5 pt thay 9 cho readability. Bìa phát hành vẫn không folio |
| 27. Folio / ngoài chẵn-lẻ | Frame parity, không theo số trang của prototype | Recto phải, verso trái | KEEP; đo bbox cả 23 trang. Nguy cơ chuyển Atlas làm đảo lề |
| 28. Front matter/phụ lục / 33 H1 bao gồm | Source canonical order, `get_manuscript` | Giữ history → core → Ch29 → Library → Error Atlas | Không reorder/đổi tên, không coi sample excerpt là chương hoàn chỉnh |
| 29. Library Atlas / 50 mục | `devops-library-atlas.md`, main prose renderer | Body 14, version/source anchors chính xác | KEEP body và anchors; sample mục 01 liên tục 3 trang, không cắt tail để tiết kiệm giấy |
| 30. Error Atlas / 85 ID | `error-atlas.md`, `add_error_atlas`, hai cột | Body 9.6/12.8, diagnostic 9/11.6, gutter 8 mm | 10.5/14, giữ entry cùng nhau; samples 20 ID A/J. Không xóa cảnh báo, không làm FAMILY trông như EXACT |

Footnote, glossary, subject index, full wrap cover chưa có renderer chuyên biệt: ABSENT, không tự bịa chức năng. Hard pagebreak có 2 source directives; KEEP lý do sư phạm, không thêm break chỉ để tạo trang đẹp. Các nội dung liên quan code/math inline nằm nguyên trong raw prose; inventory không tách inline token thành một block mới.

Các số lớp phía trên không cộng thành số trang hay số bài tập: một block có thể đóng nhiều vai trò. Những trường hợp source-only (đặc biệt H4) không bị suy thành lỗi đã nhìn thấy trên PDF khóa.
