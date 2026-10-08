# Đối chứng hình thức: PDF khóa

SHA-256 `f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09`, 493 trang. Render mới 150 dpi RGB, mở riêng từng trang trong bảng dưới. `baseline_pages.json` lưu hash từng PNG. Đây là sample design review 14 trang, không phải full visual QA. Markdown hiện hành vẫn là nguồn nội dung; khác biệt nội dung không bị hoàn tác.

| Trang / ảnh | Quan sát thực tế | KEEP / đề xuất |
|---|---|---|
| 1 / [ảnh](evidence/baseline-001.png) | Title rõ; artwork ô chữ nhật có mảng đen lớn, ít chi tiết | KEEP title/author; thử bốn artwork khác, không gọi bìa cũ lỗi |
| 2 / [ảnh](evidence/baseline-002.png) | 33 entry TOC có số, rất dày nhưng nhìn thấy từng dòng | KEEP tự động; không ép thêm cấp TOC vào trang này |
| 14 / [ảnh](evidence/baseline-014.png) | H1 và rule rõ; body/code đen, block đầy đủ | KEEP 14/11.5 pt; accent trái không phải gutter/số dòng |
| 15 / [ảnh](evidence/baseline-015.png) | Terminal rồi diagram/caption/prose; figure lớn, label đọc được | KEEP logic/caption; vector là ưu tiên, không shrink |
| 16 / [ảnh](evidence/baseline-016.png) | Grid phân biệt 3 cột; syntax code trong cell xuống dòng | KEEP grid; thử body table 11 pt; không sửa dữ liệu |
| 36 / [ảnh](evidence/baseline-036.png) | Array copy có hai note và cạnh nét đứt; code/caption đọc được | Restyle vector tương đương trang catalog 10, không sửa cơ chế |
| 37 / [ảnh](evidence/baseline-037.png) | Hai descriptor dẫn cùng store; caption rồi table nguyên khối | KEEP ngữ cảnh và prose; không gắn nhãn C4/UML tùy tiện |
| 140 / [ảnh](evidence/baseline-140.png) | Long H1 hai dòng; prose dày, đoạn cuối đủ theo heading | KEEP long-reading body; không tóm tắt nội dung vì chật |
| 160 / [ảnh](evidence/baseline-160.png) | Body, bold mental model và H2 tách rõ; folio bên trái | KEEP; header production không cần thêm nếu không có lợi ích |
| 429 / [ảnh](evidence/baseline-429.png) | Library opener có claim-boundary callout và tier heading | KEEP point-of-verification; không đổi wording |
| 430 / [ảnh](evidence/baseline-430.png) | Continuation rồi informer flow; worker/cache edge nét đứt rõ | KEEP diagram phức tạp, thử cỡ đủ đọc; prototype 341.2 dpi |
| 484 / [ảnh](evidence/baseline-484.png) | Atlas intro 14 pt nhưng taxonomy/reflex table nhỏ hơn rõ | Cỡ chữ tra cứu cần thử lớn hơn; không bỏ grid |
| 485 / [ảnh](evidence/baseline-485.png) | Hai cột có 14 ID; chữ chẩn đoán nhỏ nhưng không thấy clipping | Thử 10.5/14, không giữ quota 14 ID/trang |
| 493 / [ảnh](evidence/baseline-493.png) | J06–J11 có warning, diagnostic dài, action và chỗ wrap | Giữ mọi thành phần; prototype trang 19–20 thử lại các tình huống này |

Folio ở 14/16/36/140/160/430/484 bên trái và 15/37/429/485/493 bên phải trong các ảnh đã mở. Không suy kết luận toàn bộ 493 trang từ sample.

Không tìm thấy overflow/clipping rõ trên 14 trang này. Đây không phải bằng chứng “sách không lỗi”. Nhược điểm thiết kế là độ nhỏ của phần tra cứu và artwork bìa ít chiều sâu, không phải lỗi nội dung. H4 là rủi ro do đối chiếu Markdown/parser hiện hành, chưa được gán nhầm thành defect nhìn thấy ở PDF khóa.
