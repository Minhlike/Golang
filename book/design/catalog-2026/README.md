# Catalog thiết kế Golang — cổng phê duyệt

Trạng thái: **PROTOTYPE_READY / INTEGRATION_BLOCKED**. Chưa tích hợp vào renderer, chưa merge main. Bốn hướng bìa ở trang 2–5; hệ thống chữ ở trang 6; trang phối hợp 8–16; Atlas hai cột 18–20; thử copy code trang 22.

Baseline source và origin/main lúc bắt đầu: `1cc60d9be0e4a2bac78f8efefadd7a64a02f15bd`. Branch: `design/catalog-2026`.

PDF đối chứng 493 trang giữ SHA-256 `f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09`. PDF này không được dùng để khôi phục nội dung. Catalog 23 trang có SHA-256 `8054281c8c627611b3f6c930ecfc0c6bb061a659035d925672ee247434a4a9e4`.

## Hồ sơ

[Kiểm kê](object_inventory.md), [quyết định thiết kế và nghiên cứu](design_decisions.md), [đối chứng thị giác](baseline_review.md), [QA và giới hạn nghiệm thu](qa_checklist.md), [copy code](copy_code_report.md). `visual_review.json` chứa nhận xét nhập sau khi mở riêng từng trang final; `qa_results.json` chứa phép đo và hash tương ứng. Không tự đánh VISUAL_PASS khi render.

Đã ingest toàn bộ 33 file Markdown, bảo toàn 5.692 block lossless, kiểm kê 57 file PlantUML/style và đọc các renderer liên quan. Review hình thức bằng mắt: 14 trang PDF đối chứng và toàn bộ 23 trang catalog. Đây không phải lượt tái kiểm định học thuật toàn bản thảo, cũng không phải full-publication QA 493 trang.

## Tái tạo

Dùng Python có ReportLab 4.4.9, PyMuPDF 1.28.2, pypdf 6.10.0, Pillow 12.3.0 và numpy 2.3.5. Font lấy nguyên từ `assets/fonts`, không tải font/dependency mới. Không chạy production builder.

```powershell
# Từ D:\Golang, với runtime/dependencies đã có:
python book/design/catalog-2026/build_catalog.py
python book/design/catalog-2026/qa_catalog.py
python -m unittest discover -s book/design/catalog-2026 -v
git diff --check
```

Hai script chỉ ghi vào thư mục prototype này. `build_catalog.py` kiểm tra snapshot 586 file được bảo vệ trước khi build lại. AST giữ cả blank/comment và raw inline syntax; không giả làm parser CommonMark đầy đủ. Mọi specimen có đường dẫn/line/hash trong `specimen_provenance.json`. Không tự viết lại nội dung để lấp trang. Bìa sau/gáy là placeholder được đánh dấu, không phải file chế bản in.

`qa_catalog.py` render mọi trang ở 150 dpi. Nếu SHA catalog đổi, ledger cũ bị vô hiệu; trạng thái trở về NOT_REVIEWED. Các PNG catalog có thể tái tạo và được gitignore; ảnh đối chứng nằm trong `evidence/`.

`.gitattributes` chỉ áp dụng trong prototype: PDF là binary; fixture và raw extraction không bị Git đổi newline hay bỏ trailing spaces có chủ đích. Những byte này là dữ liệu kiểm thử, không phải lỗi format source. Build thứ hai đã có SHA trùng bản đã review.

## Quyết định cần duyệt

Chọn bìa A/B/C/D; duyệt hệ thống H1–H4, chữ Atlas lớn hơn, grid bảng và vector hóa có kiểm chứng từng hình. Copy/paste chính xác trên hai PDF reader vẫn UNKNOWN; thử extract đã FAIL byte identity. Gáy/giấy/đóng và proof in còn UNKNOWN. Không chấp nhận các mục này ngầm bằng cách chọn một bìa.

Dừng tại đây. Tích hợp toàn sách cần nhiệm vụ riêng sau phê duyệt; không tạo candidate sản xuất, không cập nhật MASTER trong lượt này.
