# Diagram repair close-out — 02-10-2026

Biên bản sửa sơ đồ này áp dụng cho `Golang_Master.pdf` SHA-256
`1e82d255ae16b288915b09f282d872f065db9d78d4d324a5f7478e25dfadde62`,
480 trang, xuất phát từ HEAD `7b0d61470b18e34933f096625fe95091f683d50b`.
Bản 470 trang bên dưới là lịch sử: kết quả visual toàn sách của bản đó không
được chuyển thành kết quả visual toàn sách của PDF mới.

## Phạm vi sửa và bằng chứng hiện tại

Thay 25 sơ đồ luồng/kiến trúc bằng ký tự trong Ch08, Ch16–18, Ch21, Ch23–27
và Library Atlas bằng sơ đồ PlantUML có source chỉnh sửa được. Hai khung chữ
trang trí được chuyển thành callout thực. Giữ hai cây thư mục, code và output
chẩn đoán nguyên văn. Không thêm chương, không sửa labs, không thay font thân
bài hoặc thu nhỏ font code. Sơ đồ AWS từng ở trang 309 nay nằm ở trang 313.

Các sơ đồ mới dùng cùng theme trắng/xám, không bóng đổ, heading sans-serif,
nhãn và mũi tên thực. Cỡ chữ nhỏ nhất theo kích thước figure thực tế là
12.458 pt; không ép một sơ đồ rộng vào trang bằng chữ nhỏ. Caption phân biệt
bản đồ khái niệm với thứ tự thực thi. AWS credential resolution và Smithy
request/response được đối chiếu tài liệu chính thức tương ứng trước khi vẽ.

Build chặn character-art diagram trước khi render; năm regression test giữ
riêng sơ đồ ký tự, cây thư mục, code và output compiler. Manifest kiểm tra cả
checksum source, ảnh và shared style. 16 publication contract test cũng PASS.

Render lại toàn bộ 480 trang bằng Poppler ở 150 dpi. Kiểm tra độc lập đạt A4,
MediaBox/CropBox, rotation, embedded fonts thực sự được dùng, blank pages,
effective raster DPI, printable text frame và vị trí folio ngoài trên 479
trang có số trang. Pixel scan không có pixel màu ngoài dung sai R/G/B = 1.
Đối chiếu 33 entry TOC với heading thực, 34 bookmark với destination thực;
không có mismatch. Perceptual dHash pairwise không có cặp gần trùng ở ngưỡng
Hamming <= 10. Tham chiếu đánh số Chương/Hình/Bảng và Atlas ID hợp lệ; phép
kiểm tra này không phải chứng minh ý nghĩa của mọi tham chiếu trong prose.

Visual thực tế: 25 trang chứa 25 sơ đồ mới đã được mở riêng ở độ phân giải
gốc, cùng 27 trang mục lục, lân cận và đầu/cuối Atlas: tổng cộng 52 trang
cuối có bằng chứng quan sát, 52 PASS, không issue mở. D01 ở trang 219
(mũi tên cắt tiêu đề khung Kubernetes) đã sửa trong source và mở lại bản cuối.
24 quyết định quan sát từ candidate trước được giữ bằng đối chiếu SHA-256
PNG byte-identical với render cuối; chỉ trang 219 thay đổi giữa hai candidate.
Không dùng contact sheet để thay kiểm tra từng trang hoặc tự điền PASS.

Checkpoint cuối vẫn giữ 428 trang khác ở NOT_REVIEWED trong lượt sửa này.
Do đó trạng thái hiện tại là `SCOPED_DIAGRAM_REPAIR_QA_PASS`, không phải
chứng nhận mới `PUBLICATION_READY` cho toàn bộ 480 trang. Không chuyển PASS
tự động thành VISUAL_PASS. Go/labs không đổi nên không chạy lại Go suite.

Bằng chứng workspace: `.workspace/diagram-repair/pdf-qa-v3/independent.json`,
`preflight/PREFLIGHT_RAW.json`, `page_review.csv`,
`actual_observation_identity.json` và `diagram-readability.json` ở thư mục
cha. Manifest ghi đúng SHA PDF, trang, số hình và hash render của 25 hình mới;
metadata review của hình cũ vẫn giữ SHA lịch sử. CODE_WIDTH, ZERO_BULLET,
ERROR_ATLAS, encoding, semantics, visual manifest và `git diff --check` PASS.
Rollback giữ nguyên bản PDF 470 trang SHA `6840c1a3…d147d75`.

---

# Content correctness and publication close-out — 01-10-2026 (historical)

Biên bản lịch sử này chỉ áp dụng cho `Golang_Master.pdf` SHA-256
`6840c1a3276ab7e5e4f77aa626252c9a4233ecaead83e3782a3055c4ad147d75`,
470 trang. Các biên bản dưới đây là lịch sử theo SHA riêng, không được dùng thay
cho kiểm tra bản này.

## Nội dung và phạm vi bằng chứng

Từ HEAD `69506ca1f4c1dfa658f2362978b19a1a4e10ebd9`, lượt này đọc 44 file
Markdown của sách, toàn bộ 50 mục Library Atlas, Ch00–29, Error Atlas và các
tài liệu định hướng có liên quan. Inventory ban đầu có 922 ứng viên quét; review
ngữ cảnh bản thảo cuối ghi 866 ứng viên, không còn ứng viên chưa phân xử trước
khi viết biên bản. Ứng viên là vị trí cần đọc, không phải số lỗi. Ghi nhận 47
nhóm nguyên nhân nội dung đã sửa (F01–F47), hai lỗi dàn trang F48–F49 cũng đã
đóng; phân loại có thể giao nhau: FACT 40, LAYER 30, ABSOLUTE 19, NUMERIC 9,
VERSION 4, SLOP 5, GAP 7. Bảy gap học tập đã đóng, không thêm chương. Những
section cũ được thay đổi theo hướng chỉnh đúng claim, ví dụ và ranh giới áp
dụng; không coi số section chạm vào là số section viết lại toàn bộ.

Go 1.27.1 và tài liệu chính thức, source ghim, compiler probes, benchmark sáu
mẫu cục bộ được dùng cho claim tương ứng. Ch29 đối chiếu lại sáu nguồn gốc về
nghiên cứu, khảo sát và dự báo; sample, quần thể, thời điểm, outcome và giới hạn
được giữ riêng. Phép đo cục bộ không chứng minh performance của mọi service.

## Kiểm tra xuất bản của đúng PDF này

- Render lại 470 trang ở 150 dpi. Mỗi trang của bản cuối đã có quyết định quan
  sát: 470 `VISUAL_PASS`, 0 issue mở, 0 `NOT_REVIEWED`. Trang 1–456 được mở
  riêng trên candidate ngay trước bản cuối; ảnh raster của đúng 456 trang này
  khớp SHA-256 từng ảnh với bản cuối. Thực tế cả 1–460 khớp pixel; 457–470 còn
  được mở lại trực tiếp trên bản cuối. Hồ sơ nằm trong
  `.workspace/content-deepening/pdf-qa-final-v7/` cùng biên bản đối chiếu pixel.
- Kiểm tra độc lập: 470/470 A4, MediaBox = CropBox, rotation 0; 0 lỗi printable
  frame và 0 pixel lệch grayscale (R≈G≈B, ngưỡng 1); 469/469 folio ngoài gáy;
  33 mục lục in khớp trang heading; 34 bookmark, không có destination sai; 0
  cặp near-duplicate perceptual; 0 cross-reference đánh số hoặc Atlas ID không
  có đích. 33 visual có caption/asset map duy nhất và ảnh raster nhỏ nhất đạt
  khoảng 227 dpi hiệu dụng; font dùng thực tế đều embedded.
- F48: hình cleanup ở trang 78 đã được mở trực tiếp ở kích thước gốc, chữ đọc
  được. F49: bản nháp 471 trang có một hàng bảng đơn độc ở trang 462. Chỉ giảm
  vertical padding của ô bảng mở đầu Atlas 2.5 xuống 1.5 pt, giữ nguyên cỡ
  chữ và nội dung; bản cuối đặt toàn bảng trên trang 461, nhóm lỗi bắt đầu
  trang 462 và J11 kết thúc sách ở trang 470. Có test hồi quy để ngăn hàng
  bảng lại tràn sang trang riêng.
- Validator: zero-bullet cho `book/chapters/*.md`, code width 0 dòng tràn ở
  11.5 pt, Error Atlas 85 entry/89 pattern, diagram encoding/semantics,
  visual manifest, 50 library locks đều PASS. Go test/vet/race cục bộ PASS
  trên 38 module (114 gate); publication regression 15/15 PASS.

Giới hạn: build/load eBPF trên Linux không được xác nhận tại máy Windows thiếu
Clang/bpftool; test cục bộ không thay thế kiểm định live AWS/Kubernetes hay chứng
minh không còn lỗi chưa phát hiện. Thư viện có 10 mục đã verify source chi tiết,
40 mục còn fingerprint pending; validator lock không chứng minh implementation
cho cả 50 mục. Các chữ “placeholder” trong ví dụ về placeholder hoặc phản ví
dụ `REPLACE_ME` được giữ có chủ ý, không là production note rò rỉ.

CONTENT_STATUS=READY_WITH_STATED_EVIDENCE_BOUNDARIES.
PUBLICATION_STATUS=READY_FOR_THIS_PDF_SHA.

---

# Final completeness & visual editorial pass — 30-09-2026

> Biên bản lịch sử: các kết quả dưới đây chỉ thuộc SHA đã nêu. Lượt content-deepening hiện hành đang sửa source và chưa build/visual-review candidate mới; không kế thừa trạng thái READY cho source đang thay đổi.

Biên bản này áp dụng duy nhất cho PDF có SHA-256 `82f7aac3a59a3e5adef37d462e335f9dd1d131b3108438f0b60190462d3430fc`. Bản nghiệm thu trước (`ae2bf4a29fc4f63c45fba2e243caaa86ed460f6d90a01895d38ea5e2f95d760d`) là baseline, không phải bằng chứng tự động cho trang đã thay đổi. Không thêm chương, thư viện, ảnh trang trí hay mở một content wave mới.

## Định danh và rollback

- STARTING_HEAD: `86a39ed00ac204ca752f1d8f7a6a679a46333077` (origin/main cùng SHA trước khi sửa).
- PDF_SHA256: `82f7aac3a59a3e5adef37d462e335f9dd1d131b3108438f0b60190462d3430fc`; PDF_PAGE_COUNT: `457`.
- ROLLBACK_MATCH: `YES`; `Golang_Master.prev.pdf` có SHA-256 `ae2bf4a29fc4f63c45fba2e243caaa86ed460f6d90a01895d38ea5e2f95d760d`, đúng từng byte của PDF current trước khi promote.
- FINAL_HEAD: xem commit của pass này; chỉ xác nhận sau khi push fast-forward.

## Review trực quan từng trang

Ledger cuối: `.workspace/completeness-pass/final-page-review.csv`, gồm 457 dòng gắn với PDF_SHA256 trên. Từ baseline cũ, 58 trang `NOT_REVIEWED` đã được mở riêng, không bulk-fill. Hai trang có issue ngắt heading (299, 384) và mọi trang thay đổi do sửa Atlas/build đều được render và mở lại trên candidate cuối ở độ phân giải cao.

- FINAL_PAGES: `457`; INDIVIDUALLY_OBSERVED: `457/457`; NOT_REVIEWED: `0`.
- CHANGED_PAGES_REVIEWED: `54/54` mở trực tiếp trên final candidate. `403` trang còn lại chỉ kế thừa quan sát riêng ở baseline khi ảnh pixel của đúng số trang khớp SHA-256 tuyệt đối; các trang có issue cũ không được kế thừa.
- VISUAL_OPEN_ISSUES: `0`; P0_OPEN: `0`; P1_OPEN: `0`; P2_OPEN: `0`.
- Kết quả được giới hạn ở layout/trang quan sát; không đồng nghĩa từng câu văn đã được phản biện khoa học lại.

## Kiểm định PDF độc lập

Bằng chứng trong `.workspace/completeness-pass/`: `candidate-comparison.json`, `candidate-preflight.json`, `final-independent.json`, `final-crossrefs.json`, `final-page-review.csv` và 54 ảnh trang thay đổi. Preflight và scan độc lập chạy trên đúng candidate SHA trước khi promote; PDF promoted có cùng SHA.

- AUTOMATED_PAGES_CHECKED: `457/457`. A4 `595.28 × 841.89 pt`, MediaBox/CropBox/rotation và mirrored margins đạt; không phát hiện chữ vượt printable frame. Scan bounding box bổ sung không thay thế review trực quan overlap.
- GRAYSCALE_PIXEL_SCAN: `PASS`, quét RGB raster từng trang, không trang nào có chênh lệch kênh >1. FOLIO_POSITION: `PASS`, đủ 456 folio ở mép ngoài chẵn/lẻ; bìa không đánh số.
- TOC_INDEPENDENT_MATCH: `PASS`, 33 entry in đối chiếu trang heading thật. BOOKMARK_DESTINATIONS: `PASS`, 34 bookmark khớp heading tại đích.
- DUPLICATE_PERCEPTUAL_SCAN: `PASS`, không trang trắng hoặc cặp gần trùng với difference hash 256 bit/Hamming ≤3; đây không phải phép chứng minh vắng mọi trùng lặp một phần.
- FONTS/RASTER: `PASS`, bốn font thực vẽ chữ (Source Serif 4, Source Sans 3 Regular/Semibold, JetBrains Mono) được nhúng, không glyph hỏng detector thấy; 31 raster, không ảnh dưới ngưỡng DPI của preflight.
- CROSS_REFERENCES: `PASS` trong phạm vi máy kiểm được: 141 lần nhắc chương hợp lệ, 31 hình và 20 bảng; không thấy markup nội bộ rò rỉ. Error Atlas là 10 trang cuối (448–457), sau Ch00–Ch29 và Library Source Guides.
- CODE_WIDTH: `PASS`, 0 dòng vượt 448.22 pt; ZERO_BULLET: `PASS`; ERROR_ATLAS: `PASS` (10 nhóm, 85 entry, 89 pattern); DIAGRAM_ENCODING/SEMANTICS: `PASS`.

## Atlas thư viện và ranh giới bằng chứng

`book/EDITION_AUDIT.json` ghi disposition cho từng entry và file/symbol tại commit đã pin nếu có claim implementation. `library_sources/lock.json` khóa đủ 50 identity. Kết quả của pass này: LIBRARY_ENTRIES `50/50`; API_DOC_BOUNDARY_ENTRIES `10`; PINNED_IMPLEMENTATION_ENTRIES `40`; PINNED_IMPLEMENTATION_VERIFIED `40/40` claim đích; LIBRARY_EVIDENCE_BOUNDARIES_VERIFIED `50/50`; UNSCOPED_IMPLEMENTATION_CLAIMS `0`; UNSUPPORTED_NUMERIC_PERF_CLAIMS `0`; UNSUPPORTED_ABSOLUTE_CLAIMS `0` trong inventory đã rà. Claim bị bác bỏ được sửa/hạ về contract trong `book/appendices/devops-library-atlas.md`.

Không đánh đồng 40 source-file/symbol review có mục tiêu với full-tree implementation fingerprints: validator cũ vẫn báo `10` fingerprint xác minh và `40` pending theo giao thức riêng. Không có khẳng định “50 implementation đã được khoa học kiểm định” hay behavior của cloud/kernel đã được chạy thực tế.

## Ảnh thật và ngôn ngữ hình

- REAL_PHOTOS_BEFORE/AFTER: `1/1`; REAL_PHOTOS_ADDED: `0`; TECH_DIAGRAMS: `30`; AI_ILLUSTRATIONS: `0`.
- Đã tìm/soát ứng viên lịch sử và hạ tầng vật lý: trạm cáp Đà Nẵng trên Wikimedia (quyền CC BY-SA rõ nhưng không minh họa đúng nội dung HTTP Ch11), rack NERSC (CC0 nhưng lặp vai trò với ảnh rack NASA Pleiades đã có ở Ch17), chân dung Ken Thompson (creator/quyền và độ phân giải chưa đủ rõ). Cả ba bị loại; không dùng ảnh chỉ để tăng số lượng.
- VISUAL_PROVENANCE / VISUAL_LICENSE / VI_CAPTION_ALT: `PASS` cho 31 visual đang xuất bản theo manifest; ALL_NEW_REAL_PHOTOS_LICENSE/PROVENANCE/FACTUAL_CAPTION_VERIFIED: `YES` theo tập rỗng, vì không thêm ảnh mới.

## Test và kết luận

- GO_TEST / GO_VET / GO_RACE: `PASS` trên 38 module, 114 gate; không sửa Go source sau lượt chạy này. PYTHON_PUBLICATION_REGRESSION_TESTS: `14/14 PASS`.
- CONTENT_VALIDATORS: `PASS` (visual manifest, library source lock, zero-bullet, code width, diagram encoding/semantics, Error Atlas). PUBLICATION_VALIDATORS: `PASS` (PDF preflight, pixel scan, frame, folio, TOC, bookmark, perceptual duplicate, cross-reference). GIT_DIFF_CHECK: `PASS`.
- BOOK_CONTENT_STATUS: `READY`; PUBLICATION_STATUS: `READY` cho đúng PDF SHA nêu trên. KNOWN_LIMITATIONS: không live AWS/Kubernetes production/eBPF Linux; kiểm định hình ảnh không thay thế xác minh mọi runtime/version trong mọi môi trường. WIP ngoài scope không được đưa vào commit.

Pass dừng tại đây; không mở wave/hotfix tiếp theo.

## Bổ sung 30-09-2026 — thay sơ đồ Chương 22

Bản PDF hiện hành sau micro-pass này có SHA-256 `f7867dad1f79ca1f9efc2801deb367f7aa72bc76500509d08b3471a3d866f8d8`, vẫn gồm `457` trang. Biên bản phía trên tiếp tục mô tả đúng baseline `82f7aac3...`, không được dùng riêng nó để xác nhận trang đã thay đổi.

- Hai sơ đồ kiến trúc và List/Watch ở trang 270–271 thay khối ký tự monospace. Source có thể sửa tại `scripts/render_ch22_diagrams.py`; hai ảnh grayscale có provenance và checksum trong `assets/visual-manifest.json`. Khối ký tự WorkQueue dư thừa được chuyển thành văn xuôi; không đổi hành vi code/lab.
- So sánh raster 2× từng trang với baseline: chính xác 8 trang đổi (`269–275`, `392`), 449 trang còn lại khớp pixel. Cả 8 trang đổi đã được mở riêng từ candidate cuối ở độ phân giải cao; hình/chữ/code/bảng/folio và ngắt trang ở đó không thấy clipping hay lỗi xuất bản mới. Trang 392 chỉ đổi số thứ tự hình do thêm hai hình trước nó. Bằng chứng render và preflight nằm trong `.workspace/ch22-diagram-pass/`.
- Preflight candidate: `PASS` cho 457 trang về A4/box/rotation, font, printable frame, bookmark, DPI ảnh, grayscale và markup. Code-width, zero-bullet, Error Atlas, diagram encoding/semantics, visual manifest, library source lock và 14 publication regression tests: `PASS`. Phạm vi bổ sung này là layout và provenance của thay đổi, không phải một lượt phản biện khoa học toàn sách mới.
