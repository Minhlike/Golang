# Publication QA — Encyclopedia edition, 29-09-2026

Biên bản này thay thế kết luận về PDF 435 trang ngày 27-09-2026. Nó chỉ áp dụng cho bản encyclopedia và phạm vi nghiệm thu của chỉ thị ONE-PASS GO ENCYCLOPEDIA + DEVOPS/SRE/AI-ERA EDITION; không dùng nhãn PASS cũ làm bằng chứng cho PDF mới.

## Định danh

- STARTING_HEAD: `666e0aec1455f46083cbb7e01edc44fce47cc953`.
- PDF: `Golang_Master.pdf`, 457 trang.
- FINAL_PDF_SHA256: `ae2bf4a29fc4f63c45fba2e243caaa86ed460f6d90a01895d38ea5e2f95d760d`.
- ROLLBACK_PDF_SHA256: `68f37d0b099fc667f87df01a7cb8a60369bdba1559ee6261fa8d39d4ce9dd444` — đúng bytes current trước khi promote, không phải bản dựng lại.
- GO_VERSION_VERIFIED: `go1.27.1 windows/amd64`; VERIFICATION_DATE: `2026-09-29`.

## Quan sát thực tế và giới hạn

Phạm vi trực quan gồm toàn bộ hình/ảnh, code block và bảng lớn, trang mở chương/chuyển đoạn, phần bổ sung, hai atlas chữ nhỏ và mẫu văn xuôi lấy có hệ thống. Mỗi trang được kiểm tra bằng actual render riêng; contact sheet không thay cho quan sát trang. Đây không phải chứng nhận mọi trang văn xuôi đã được xem riêng.

- AUTOMATED_PAGES_CHECKED: `457/457`, render lại bằng Poppler RGB 150 dpi.
- PRIORITY_PAGES_REQUIRED: `396`; PRIORITY_NOT_REVIEWED: `0`.
- VISUAL_PAGES_ACCEPTED: `399`; VISUAL_PAGES_WITH_OPEN_ISSUES: `0`.
- FRESHLY_OPENED_FINAL_V11: `11` trang — 362, 363, 449, 450, 451, 452, 453, 454, 455, 456, 457, mở ở 216 dpi.
- BYTE_IDENTICAL_PREVIOUSLY_OBSERVED: `388`. Chỉ chuyển PASS của trang đã thực sự được mở riêng nếu SHA-256 PNG cùng số trang khớp tuyệt đối. Trang thay đổi hoặc có ISSUE không được tự chuyển PASS. Chuỗi bằng chứng chuyển trạng thái được giữ trong workspace của từng candidate.
- NOT_REVIEWED: `58` trang ngoài phạm vi trực quan bắt buộc, không bulk-fill.
- ALL_PAGES_INDIVIDUALLY_OBSERVED: `NO`.

Ledger cuối: `.workspace/encyclopedia-pass/pdf-qa-final-v11/page_review.csv`. Mọi PASS gắn với đúng PDF SHA-256. Hash ledger và ánh xạ 31 hình sang trang đã xem nằm trong `book/EDITION_AUDIT.json` và `assets/visual-manifest.json`. Bằng chứng tự động: `independent.json`, `preflight/PREFLIGHT_RAW.json`, `crossrefs.json` trong cùng workspace QA.

## Kiểm định xuất bản

- Geometry: PASS — 457 trang A4 khoảng `595.28 × 841.89 pt`, MediaBox bằng CropBox, rotation 0.
- Printable frame: PASS — preflight không clipping/overflow; bounding box chữ theo lề đối xứng, dung sai 2 pt, không vi phạm. Trực quan không thấy code/bảng/hình bị cắt trong phạm vi đã xem. Bounding box không tự chứng minh vắng mọi dạng overlap.
- Folio: PASS — đủ 456 số trang đúng mép ngoài chẵn/lẻ; bìa cố ý không có folio.
- Fonts/glyphs: PASS — font thực sự vẽ chữ đều được nhúng: Source Serif 4, Source Sans 3 Regular/Semibold, JetBrains Mono. Không glyph hỏng được detector phát hiện hoặc thấy trên trang đã xem. Helvetica/Times-Roman chỉ là resource không vẽ chữ, không phải fallback đã xuất hiện.
- Grayscale pixel scan: PASS — từng RGB render không có chênh lệch kênh màu vượt 1; các trang đã xem giữ tương phản đơn sắc.
- Blank/perceptual duplicate: PASS — không trang trắng ngoài ý muốn; không cặp gần trùng qua difference hash độ chói 256 bit, Hamming ≤3 trên 457 trang. Không bảo đảm phát hiện mọi sao chép một phần nội dung.
- Raster: 31 ảnh, effective DPI nhỏ nhất `227.39`; tất cả trang ảnh được xem riêng. DPI không thay cho kiểm tra độ đọc được của nhãn.
- TOC independent match: PASS — 33 entry in khớp số trang heading thật.
- Bookmark destinations: PASS — 34 bookmark, gồm mục lục, title khớp heading tại destination.
- Thứ tự: front matter → Ch00–Ch29 → Library Source Guides → Error Atlas. Ch29 bắt đầu trang 388, Library Source Guides trang 396, Error Atlas trang 448–457 và là nội dung cuối.
- Cross references: PASS về cấu trúc — 141 lần nhắc chương không có số đích ngoài 0–29; 31 caption hình, 20 caption bảng đúng chuỗi; mỗi ảnh có caption và trang đích thật. ID Error Atlas qua validator riêng. Không suy ra mọi liên hệ khái niệm trong prose đều đúng.
- Production markup: PASS theo preflight; `REPLACE_ME` tại trang 209–210 là ví dụ có chủ đích, được giải thích để ngăn apply nhầm.

## Nội dung và kiểm thử

Inventory trước khi viết có 159 chủ đề: 131 giữ hướng dạy, 28 gap đã xử lý (21 Go, 7 kỹ nghệ/nghề nghiệp). Thêm Ch29; mở rộng Ch1/3/5/7/8/14/17; thêm 17 mục lớn. 23 tệp chương cũ giữ cấu trúc sư phạm, không có nghĩa bytes không đổi: lỗi factual phát hiện được sửa nhỏ tại source.

Có 27 entry bằng chứng chính và 3 entry sửa tiếp theo từ quan sát xuất bản. 239 đoạn claim mạnh đã disposition: 133 giữ sau kiểm tra, 106 sửa/bỏ. Không còn claim quan trọng thiếu bằng chứng/phạm vi trong inventory đã rà; không suy rộng thành chứng minh khoa học mọi câu trong sách. Dữ liệu nghề nghiệp dùng 5 nhóm nguồn, 6 URL, giữ ngày, mẫu, địa lý, phương pháp và giới hạn; không biến kết quả task thành dự báo chắc chắn về nghề.

Sửa xuất bản tại Markdown/PlantUML/style/build, không patch PDF: quote trong hình source-anatomy, nhãn/quan hệ/tỷ lệ sơ đồ, emphasis quanh inline code, heading orphan, widow prose/list, tiêu đề nhóm Error Atlas cuối cột và ghi chú lifecycle/diagnostic. Regression test kiểm tra wrapping, keep-with-next và promotion/rollback.

- LABS_ADDED: `labs/edition-contracts`, `labs/part29-change-evidence`.
- LAB_CHANGED: `labs/part6-testable-command/internal/app/publication_benchmark_test.go`; fixture thật, hai kiểu vòng benchmark. Smoke một iteration không phải số liệu performance so sánh.
- GO_TEST / GO_VET / GO_RACE: PASS trên 38 module, 114 gate thành công. Edition-contracts được gofmt và chạy lại cả ba gate sau hai regression test cuối về Once/send-after-close và fatal unlocked Mutex.
- PYTHON_PUBLICATION_REGRESSION_TESTS: `12/12 PASS`.
- CODE_WIDTH: PASS — 0 dòng vượt khung 448.22 pt.
- ZERO_BULLET: PASS trên narrative chương.
- ERROR_ATLAS: PASS — 10 nhóm, 85 entry, 89 diagnostic pattern.
- DIAGRAM_ENCODING / SEMANTICS / VISUAL_MANIFEST: PASS; 31 visual có provenance, quyền phân phối, caption/alt tiếng Việt; thêm 1 ảnh thật và 1 sơ đồ, không ảnh AI/chart mới.
- LIBRARY_SOURCE_VALIDATOR: PASS về 50 source lock; 10 implementation fingerprint đã xác minh, 40 chưa xác minh ở mức đó. Retrieval không được coi là đã đọc/kiểm định implementation; không gọi cả 50 guide là scientific-review hoàn chỉnh.
- DOCUMENT_CACHE: 8 tài liệu ngoài ingest, 2 cache hit, selective retrieval; không commit generated cache.
- GIT_DIFF_CHECK: PASS.

Native cgo và Linux cross-build đã kiểm tra. Không live AWS provisioning, cài Kubernetes production hay Linux eBPF kernel attach trên máy Windows này. Lab/mock/tài liệu không thay cho chứng nhận production; hướng dẫn nghề nghiệp không bảo đảm tuyển dụng hoặc thu nhập.

## Kết luận

`P0_OPEN=0; P1_OPEN=0; P2_OPEN=0` trong phạm vi nội dung và trang đã kiểm tra.

`BOOK_CONTENT_STATUS=READY; PUBLICATION_STATUS=READY; SCOPE=ONE_PASS_EDITION_ACCEPTANCE`.

`KNOWN_BLOCKERS=NONE` đối với phạm vi này. READY không có nghĩa đã xem riêng 457/457 trang, không chứng nhận cả 50 implementation, không chứng nhận runtime cloud/kernel chưa chạy. Giữ đúng PDF SHA-256 khi giao bản; thay đổi tiếp theo không tự động kế thừa kết luận này.
