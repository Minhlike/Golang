# QA prototype và cổng regression

Catalog final: 23 trang; SHA `8054281c8c627611b3f6c930ecfc0c6bb061a659035d925672ee247434a4a9e4`. Tất cả 23 trang đã được mở actual render 150 dpi, từng ảnh riêng, không contact sheet. Ledger nhập tay sau quan sát. **VISUAL_OPENED=23; VISUAL_PASS=23; VISUAL_ISSUES=0; NOT_REVIEWED=0**, chỉ cho hình thức catalog; copy byte FAIL không bị VISUAL_PASS che đi.

| Gate | Kết quả | Phép kiểm tra / giới hạn |
|---|---|---|
| Protected source/PDF/MASTER/labs/deps | PASS | Hash 586 tracked files ngoài book/design trước/sau; research WIP không đụng |
| Markdown block AST | PASS | 33 file, 5.692 block; lossless roundtrip bytes và từng node hash. Không claim full CommonMark inline AST |
| Code/output/table/caption/diagram source | PASS bảo toàn | Snapshot + raw/payload hash + specimen provenance. Không tái nghiệm thu mọi lesson khoa học |
| A4/MediaBox/CropBox/rotation | PASS catalog | 23 trang, 595.276×841.890 pt, CropBox=MediaBox, rotation 0 |
| Mirrored frame/gutter | PASS catalog | Span bbox trong frame, inner24/outer18; Atlas 8 mm gutter; quan sát các transitions |
| Clipping/overlap | PASS catalog | 23 actual pages; span bounds bổ sung. Vector collision chỉ bắt được bằng mắt và đã sửa |
| Heading/caption orphan | PASS mẫu | Không thấy heading/caption bị treo trong 23 trang cuối. Mẫu figure/caption/Q&A giữ đúng ngữ cảnh |
| Paragraph widow/orphan | PASS mẫu | Chặn single-line bằng style, xem các page breaks. Library trang 17 có continuation 3 dòng hợp lý; không shrink để bỏ tail |
| Unicode/fonts | PASS catalog | Source/JetBrains subset embedded được dùng thực tế, glyph tiếng Việt/→/bullet đọc được; Helvetica resource không dùng |
| Grid tables | PASS mẫu | Trang 6/9/14: đường ngang/dọc đủ, cell readable. Universal long-table multi-page behavior NOT_TESTED |
| Code size/selectability | PASS appearance | 11.5/15.5, full blocks; extract có text. Exact clipboard FAIL/UNKNOWN, xem report |
| Diagram vector semantic | PASS một mẫu | Source hash/8 label/2 node/1 dotted edge/2 note; actual trang 10 sau sửa |
| Diagram phức tạp KEEP | PASS appearance | Informer ở 11/16; raster hữu hiệu 341.2 dpi. Không claim vector hóa hết 58 hình |
| Grayscale | PASS catalog | Pixel R/G/B max delta≤1 trên mọi trang render, không chỉ tên palette |
| Footer/folio | PASS catalog | Đo số, bbox outer parity trên cả 23 trang; xem bằng mắt |
| TOC/bookmarks | PASS catalog | 12 internal links, 19 bookmark title/destination đối chiếu heading thực. Không test lại TOC 493 trang |
| Blank/context/density | PASS mẫu | Không trang trắng; sparse cover/pause/gate có mục đích; Atlas thật 20 entry và Library 3 trang |
| Reproducibility | PASS runtime đã ghim | Source + bundled fonts + scripts. PDF invariant; build thứ hai phải kiểm hash trước tự tái dùng ledger |
| Unit tests / staged diff | PASS | 8 test trong bundled runtime; staged diff check sạch. Index PDF/fixture/raw extraction trùng byte file thực; trailing spaces fixture được bảo toàn có chủ đích qua attributes riêng |
| Two-reader clipboard exact | UNKNOWN, blocker | NOT_RUN; không thay bằng PyMuPDF/pypdf |
| Giấy/đóng/gáy/bleed và proof in | UNKNOWN, blocker | Không có stock/binding data hay proof giấy thật; grayscale scan không thay printer proof |
| Artwork visual research | PASS phạm vi mẫu | Đã xem publisher architecture/typography, render MoMA PDF 60–61 (3D/exploded) và hình botanical NGA. Smithsonian riêng UNKNOWN; NGA màu không thay proof in đen trắng |
| Production renderer/all-book QA | NOT_RUN | Approval gate; không được sửa hoặc rebuild publication PDF |

## Lỗi prototype đã đóng

P1-CAT-01: ArrayFigure kế thừa Flowable nhưng chưa cấp height, gây chồng diagram lên prose/code. Sửa __init__/wrap để cấp 210 pt, render lại; final trang 10 sạch. P2-CAT-02: nét bìa B vượt artwork box, chạm subtitle. Sửa transform riêng artwork, không giảm font; final trang 3 sạch. P2-CAT-03: các diagnostic list Atlas bị ghép thành paragraph và giữ literal `*`; đổi renderer prototype thành list từng dòng, final 18–20 sạch. P3-CAT-04: Atlas intro riêng làm trang gần rỗng; đưa intro vào frame cột, giữ entry, không thêm prose lấp chỗ.

Kiểm thử cũng bắt được bullet dùng font mặc định chưa nhúng; explicit Source Sans cho bullet. Đích bookmark heading xuống dòng được đối chiếu qua whitespace-normalization **chỉ cho text heading**, không dùng normalization để cứu code-copy FAIL. Phép đo copy ban đầu nhầm dòng TOC đã được sửa để chọn heading + QA-fixture thật, page 22. Không dùng report trial cũ làm bằng chứng final.

## Khi được duyệt, trước nghiệm thu tích hợp

Checklist bắt buộc: [ ] mapping object/heading semantic; [ ] parser H4; [ ] exact raw code/output/table/caption/references/diagram hashes; [ ] toàn bộ long code/table split; [ ] counter và cross-reference; [ ] actual vector labels/edges/state/caption; [ ] câu hỏi không lộ đáp án; [ ] toàn bộ final pages render/review; [ ] hai reader clipboard; [ ] printer stock/binding/trim proof. Không chạy các bước tích hợp này trong lượt catalog.

Trạng thái bàn giao: **PROTOTYPE_READY / INTEGRATION_BLOCKED / APPROVAL_REQUIRED**. Không PUBLICATION_READY, không merge và không chuyển cổng phê duyệt thành một wave tự động.
