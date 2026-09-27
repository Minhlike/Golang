# Final Publication QA — Golang Master

- **Ngày chốt:** 2026-09-27
- **Starting HEAD / origin/main:** `2345a91a3c0e0000796a0ba80e96f4c9fade4974`
- **PDF được kiểm:** `Golang_Master.pdf`
- **SHA-256:** `baa743dfd7552e9018cb0f1c8940020b9f689f7e3d2898c8ba1718dcc0aec0cd`
- **Tổng số trang:** 435

## Phạm vi và bằng chứng độc lập

Không dùng lại nhãn PASS hay số liệu của các biên bản trước làm bằng chứng. Toàn bộ 435 trang của đúng PDF SHA-256 nêu trên đã được render và quan sát tuần tự; các trang chứa code, bảng, sơ đồ, Error Atlas hoặc trang sửa đã được mở ở độ phân giải cao. Các sửa ký tự không làm đổi phân trang; sáu trang có lỗi trình bày đã được render và xem lại trên PDF cuối.

- **AUTOMATED_PAGES_CHECKED:** 435/435
- **VISUAL_PAGES_OPENED:** 435/435
- **VISUAL_PAGES_PASS:** 435/435
- **VISUAL_PAGES_WITH_ISSUES:** 6 (đều đã sửa và review lại)
- **NOT_REVIEWED:** 0

## Kết quả preflight và in ấn

- **Geometry / printable frame:** PASS — mọi trang A4 `595.276 × 841.890 pt`, MediaBox = CropBox, rotation 0; vùng chữ nằm trong khung in, không clipping hoặc overlap.
- **Mirror margins / folio:** PASS — kiểm tra độc lập 434 folio: không thiếu và không đặt sai mép ngoài chẵn/lẻ.
- **Fonts / glyphs:** PASS — font render thực tế là Source Serif 4, Source Sans 3 và JetBrains Mono; tất cả được nhúng, không tofu/broken glyph.
- **Grayscale pixel scan:** PASS — scan RGB 0.5× trên 435 trang, không pixel nào có chênh kênh màu lớn hơn 5; bản in đơn sắc vẫn giữ tương phản của prose, code, bảng và sơ đồ.
- **Blank / perceptual duplicate:** PASS — 0 trang trắng ngoài ý muốn; 0 cặp trùng hoặc gần trùng qua fingerprint ảnh đã bỏ vùng folio.
- **Code width / tables / figures:** PASS — 0 dòng code vượt khung in; kiểm tra trực quan không còn code, bảng hoặc sơ đồ bị cắt.
- **TOC / bookmarks:** PASS — 33 bookmark có destination khớp heading tại trang đích; mục lục và thứ tự sách chạy từ front matter, Ch00–Ch28, Library Source Guides đến Error Atlas, là nội dung cuối; không có Ch29.
- **Cross references:** PASS — Error Atlas có 85 entry, validator xác thực toàn bộ chapter reference; không còn marker sản xuất chưa giải quyết. Các từ `placeholder`/`REPLACE_ME` còn lại là mô tả hoặc ví dụ sư phạm có chủ đích, không phải rò rỉ sản xuất.
- **Các validator bổ sung:** PASS — zero-bullet, Error Atlas và code-width.

## Lỗi tìm thấy và sửa tại source

- **P0:** 0 tìm thấy, 0 còn mở.
- **P1:** 2 tìm thấy, 2 đã sửa: webhook chỉ đánh dấu delivery hoàn tất sau khi handler nghiệp vụ thành công; HTTP 500 không còn bị báo là `healthy` trong MCP health probe. Lab liên quan đã được gofmt và test/vet/race trước vòng sửa typography cuối (source Go không đổi sau các test đó).
- **P2:** 6 tìm thấy, 6 đã sửa: một mũi tên render sai và năm biểu thức Markdown/LaTeX lộ ra trong trang sách được thay bằng Unicode/inline technical text ở source, sau đó render và review lại ở độ phân giải cao.
- **P3:** 0.

## Kết luận

`FINAL_STATUS=PUBLICATION_READY`

PDF cuối đạt điều kiện xuất bản A4: không còn P0/P1 mở, `NOT_REVIEWED=0`, và toàn bộ kiểm định ở trên có bằng chứng độc lập từ bản render cuối. Cần giữ nguyên SHA-256 nêu trên khi gửi in; hiệu chỉnh giấy/mực riêng của nhà in nằm ngoài mô phỏng PDF này.
