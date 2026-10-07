# Final whole-book publication gate — 08-10-2026

Biên bản thẩm định và nghiệm thu xuất bản toàn diện (Final Whole-Book Publication Gate) cho toàn bộ cuốn sách Golang Living Textbook.

- STARTING_HEAD: `0a4cea0bef424430cae87519697c5eeed60a7aad`
- FINAL_HEAD: `0a4cea0bef424430cae87519697c5eeed60a7aad`
- SOURCE_FREEZE_HEAD: `0a4cea0bef424430cae87519697c5eeed60a7aad`
- PDF_SHA256: `f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09`
- PAGE_COUNT: `493`
- PUBLICATION_STATUS: `READY_FOR_THIS_PDF_SHA`
- BOOK_STATUS: `READY`

## Bảng chỉ số kiểm định toàn diện (Whole-Book Gate Metrics)

| Tiêu chí thẩm định | Kết quả | Ghi chú & Ranh giới kỹ thuật |
|---|---|---|
| **LIBRARY_ATLAS_SEMANTIC_AUDIT** | PASS | `ENTRIES_REVIEWED=50` (50/50 thư viện đối chiếu source ghim trong `library_sources/repos` và `lock.json`) |
| **ERROR_ATLAS_SEMANTIC_AUDIT** | PASS | `ENTRIES_REVIEWED=85` (85/85 lỗi thuộc 10 taxonomy A–J, 89 patterns, cross-reference chính xác) |
| **FRONT_MATTER_INTEGRITY** | PASS | Tiêu đề, số chương (Ch00, Ch01–Ch29), Part X, Back Matter, Phụ lục A ở cuối sách |
| **CROSS_REFERENCES_INTEGRITY** | PASS | 124 tham chiếu chéo giữa các chương được kiểm chứng đúng ngữ nghĩa và thứ tự |
| **LAB_MODULES_TOTAL** | 38 | 38 modules Go (37 labs + 1 project opsprobe) |
| **LAB_TEST_PASS** | 38/38 | 100% unit/integration tests vượt qua |
| **LAB_VET_PASS** | 38/38 | `go vet` sạch 100% |
| **LAB_RACE_PASS** | 38/38 | `go test -race` sạch 100% không phát hiện race condition |
| **ENVIRONMENT_LIMITATIONS** | RECORDED | Windows host: `LIVE_EBPF_KERNEL_STATUS=NOT_LIVE_KERNEL_VERIFIED` (mock/userspace unit tests PASS); không tạo tài nguyên đám mây/production thực tế |
| **SOURCE_VALIDATORS** | PASS | 10/10 validators PASS (no-bullets, prose ratio 76.94%, code width, publication contracts 16/16, diagram encoding, visual manifest 58 assets) |
| **PDF_PREFLIGHT** | PASS | A4 geometry, 4 font nhúng đầy đủ, 0 broken glyph, 0 clipping, 0 blank page, 0 duplicate page, 34 bookmarks |
| **VISUAL_REVIEWED_PAGES** | 493/493 | Toàn bộ 493 trang candidate PDF được thẩm định trực quan |
| **VISUAL_PASS** | 493 | 493 trang đạt chuẩn visual |
| **VISUAL_FAIL** | 0 | Không có lỗi cắt chữ, tràn khung, orphan heading, bể bảng hay hỏng hình ảnh |
| **NOT_REVIEWED** | 0 | 0 trang bị bỏ sót |
| **OPEN_P0** | 0 | Không có lỗi nghiêm trọng tồn đọng |
| **OPEN_P1** | 0 | Không có lỗi kỹ thuật mức cao tồn đọng |
| **OPEN_P2_PUBLICATION_BLOCKERS** | 0 | Không có blocker xuất bản tồn đọng |

## Chi tiết kết quả các pha kiểm định

1. **Library Atlas Semantic Audit (50/50 entries)**:
   - Toàn bộ 50 mục thư viện từ Rank 01 đến 50 được rà soát đối chiếu với `library_sources/catalog.json`, `library_sources/lock.json`, và các repo ghim trong `library_sources/repos`.
   - Đường dẫn module, tag release, commit hash 8 ký tự, tập tin mã nguồn trọng yếu và năng lực API đều khớp với cam kết đã khóa.

2. **Error Atlas Semantic Audit (85/85 entries)**:
   - Toàn bộ 85 mục tra cứu lỗi thuộc 10 nhóm Taxonomy (A: Compiler & Type System, B: Runtime & Panic, C: Error Values & I/O, D: Context & Cancellation, E: Filesystem & Process, F: Network / HTTP / TLS, G: Database, H: Concurrency, I: Modules / Test / Toolchain, J: Container / Kubernetes / CI-CD) bao phủ 89 diagnostic patterns.
   - Các chuỗi chẩn đoán (EXACT), giá trị sentinel chuẩn (SENTINEL), trạng thái runtime/k8s (STATUS) và họ hiện tượng (FAMILY) phản ánh chính xác hành vi của compiler, runtime Go 1.27.1 và môi trường Linux/k8s. Dòng hướng dẫn hành động (`→`) và liên kết chương (`[ChX]`) được đối chiếu nhất quán.

3. **Cấu trúc bản thảo và tham chiếu chéo**:
   - Khẳng định tính bất biến: Bìa -> Mục lục -> Front Matter -> Ch00 (2 chương) -> Ch01–Ch29 -> Back Matter (Atlas 50 Thư viện) -> Phụ lục A (Atlas Lỗi Go) luôn nằm ở vị trí cuối cùng của cuốn sách.
   - Toàn bộ 124 liên kết cross-reference giữa các chương được quét tự động và đối chiếu ngữ nghĩa, không có liên kết nào trỏ ngoài phạm vi Ch00–Ch29.

4. **Lab Regression Matrix (38 modules)**:
   - 38/38 Go modules đạt `test PASS`, `vet PASS`, và `test -race PASS`.
   - Riêng `labs/part27-ebpf-observer`: Các unit test mô phỏng userspace (decoding 156-byte ABI, ring buffer mock, event parsing, detection logic) đều PASS; trạng thái kernel thực tế được ghi nhận chính xác theo ranh giới môi trường host Windows: `LIVE_EBPF_KERNEL_STATUS=NOT_LIVE_KERNEL_VERIFIED`.

5. **Nghiệm thu Candidate và Xuất bản Promoted PDF**:
   - Candidate build sạch tại `tmp/pdfs/Golang_Master.candidate.pdf` (493 trang, SHA-256 `f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09`).
   - Kết quả Preflight tự động: `OVERALL_STATUS=PASS`.
   - Kết quả Visual Audit: 493/493 trang đạt `VISUAL_PASS`, `VISUAL_FAIL=0`, `NOT_REVIEWED=0` (ledger ghi tại `.workspace/final-publication-gate/page_review.csv`).
   - Candidate được promote nguyên trạng sang `Golang_Master.pdf`, bảo toàn bản sao lưu lùi `Golang_Master.prev.pdf`. SHA-256 của tệp xuất bản sau cùng khớp tuyệt đối từng byte với candidate đã nghiệm thu.

---

# Final upper-book content audit close-out (Ch25–Ch29) — 08-10-2026

Biên bản kiểm định tính đúng nội dung và sửa chữa có trọng tâm toàn diện cho khối chương thượng tầng (Ch25–Ch29) này áp dụng cho `Golang_Master.pdf` SHA-256
`cf660f77067daa0d890684f4a135a668289b1dd8b54616302ed6aa7cd038bed8`,
493 trang, xuất phát từ baseline HEAD `1c118ffb7f29894d38f9637c1e9cada4a23e5b7f`.

## Bảng kết quả thẩm định từng chương (Chapter Verdicts)

| Chapter | Verdict | P0 | P1 | P2 | Ranh giới chứng cứ cốt lõi | Hành động thực hiện |
|---|---|---:|---:|---:|---|---|
| **Ch25** | FIXED | 0 | 0 | 3 | Webhook HMAC constant-time; delivery GUID deduplication; lack of automatic retries on failure; tiered API rate limits. | Chuẩn hóa threat boundary timing side-channel; lược bỏ từ ngữ drama ("bắt buộc"); làm rõ ranh giới transport. |
| **Ch26** | FIXED | 1 | 2 | 3 | Module directory canonical hash (`dirhash.Hash1`); Cosign keyless ephemeral keys & OIDC certificate; static reachability bounds; model fixture boundaries. | Sửa định nghĩa mã băm `go.sum` sang canonical directory hash; chuẩn hóa khái niệm keyless; bổ sung giới hạn reflection/assembly; đồng bộ 7 kịch bản test trong `gate_test.go`. |
| **Ch27** | PASS | 0 | 0 | 0 | ABI decoding 156B little-endian; ring buffer drop/submit semantics; `RecordReader` mock; privilege/kernel matrix; explicit non-Linux disclaimer. | PASS — no material change required. Bảo toàn nguyên vẹn ranh giới `SKIPPED_WITH_REASON` / `NOT_LIVE_KERNEL_VERIFIED`. |
| **Ch28** | FIXED | 1 | 1 | 2 | Pinned MCP SDK v1.8.0; negotiated protocol revision 2026-07-28; session context role mapping vs transport auth; target allowlist; human-in-the-loop gate. | Sửa lỗi thiếu tham số `target` trong snippet `RequestApproval(action, target string)`; giải thích ranh giới xác thực của `context.Context`; giảm nhẹ giọng điệu áp đặt ("BẮT BUỘC"). |
| **Ch29** | FIXED | 0 | 0 | 1 | Empirical labor/AI studies: Peng et al. 2023, METR 2025 RCT & 2026 update, Go Survey 2025, BLS 2025–2035, DORA 2025; change evidence gate boundaries. | Cập nhật ngày đối chiếu nguồn 08-10-2026; bảo toàn nguyên vẹn các ước lượng điểm, khoảng tin cậy và ranh giới suy luận có điều kiện. |

## Phạm vi sửa và kết quả kiểm định kỹ thuật

1. **Chương 25 (`book/chapters/25-git-github-automation-event-driven.md`)**:
   - Chuẩn hóa tiêu đề và văn xuôi: chuyển từ nhận định tuyệt đối "Chống Timing Attack" sang "Phòng ngừa Timing Side-Channel bằng HMAC-SHA256".
   - Bảng cạm bẫy: làm rõ rủi ro rò rỉ thông tin qua chênh lệch thời gian so sánh byte thay vì tuyên bố kẻ xấu chắc chắn vét cạn chữ ký số qua Internet công cộng.

2. **Chương 26 (`book/chapters/26-chuoi-cung-ung-co-the-kiem-chung.md`) & Lab Part 26 (`labs/part26-supply-chain-gate/`)**:
   - Sửa chính xác bản chất mã băm `h1:` trong `go.sum`: mô tả đúng giải thuật băm thư mục chuẩn tắc (`dirhash.Hash1`) dựa trên danh sách tệp được sắp xếp thứ tự và băm từng tệp rồi băm tổng thể, thay vì gọi là băm toàn bộ cây sau giải nén.
   - Chuẩn hóa khái niệm "Keyless Signing": làm rõ runner tạo cặp khóa tạm thời (ephemeral keys) và dùng OIDC token để xin chứng chỉ ngắn hạn từ Fulcio, thay vì diễn giải sai là mật mã học vận hành không cần khóa.
   - Bổ sung ranh giới phân tích tĩnh của `govulncheck`: nêu rõ giới hạn của xấp xỉ đồ thị cuộc gọi trước reflection, hàm assembly hay điều phối động.
   - Tinh gọn tên test trong `gate_test.go` (`TestModelAllowsSelfAssertedIdentity`, `TestPolicyGateStopsOnSignatureFailure`) để bảo đảm độ rộng hiển thị mã nguồn không tràn viền (< 64 ký tự), đồng thời đồng bộ toàn bộ 7 kịch bản test vào văn bản chương.

3. **Chương 27 (`book/chapters/27-quan-sat-linux-bang-ebpf-va-go.md`)**:
   - Thẩm định toàn diện: Chương giữ ranh giới cực kỳ chặt chẽ (`NOT_LIVE_KERNEL_VERIFIED`, phân định rõ ABI 156 bytes, TGID/PID shift, rủi ro tràn ring buffer và mô hình mock userspace). Không cần sửa đổi cơ học.

4. **Chương 28 (`book/chapters/28-mcp-va-aiops-an-toan-bang-go.md`)**:
   - Sửa lỗi cú pháp trong đoạn mã mẫu Thử thách 2: bổ sung tham số `target` vào chữ ký hàm `RequestApproval(action, target string)`.
   - Làm rõ ranh giới xác thực: `context.Context` không tự tạo ra authenticated identity; middleware trong lab chỉ ánh xạ session ID cho mô hình kiểm thử, trên production cần transport/IdP xác thực độc lập.
   - Hạ giọng điệu các quy tắc phân quyền, loại bỏ từ ngữ áp đặt ("BẮT BUỘC").

5. **Chương 29 (`book/chapters/29-ky-su-va-bang-chung-trong-ky-nguyen-agent.md`)**:
   - Cập nhật ngày đối chiếu tài liệu và số liệu ngoại kiểm sang 08-10-2026.
   - Giữ nghiêm ngặt các ranh giới phương pháp luận nghiên cứu: đối chiếu chính xác các thông số từ Peng et al. (mức giảm 55.8%, CI 21–89%), METR RCT (tăng 19% thời gian, CI 2–39%), cập nhật phương pháp METR 24-02-2026, Go Survey 2025 (5.379 mẫu), dự báo BLS (+10% giai đoạn 2025–2035 tại Mỹ), và framing năng lực tổ chức của DORA 2025.

## Kiểm tra xuất bản và trạng thái nghiệm thu

- Mã nguồn và validator:
  - ZERO_BULLET (`validate_main_manuscript_no_bullets.py`): PASS.
  - PROSE_LANGUAGE (`audit_prose_language.py`): PASS (76.94% overall; Ch25: 70.5%, Ch26: 71.6%, Ch27: 71.7%, Ch28: 63.5%, Ch29: 80.9%).
  - CODE_WIDTH (`validate_code_width.py`): PASS (0 dòng tràn ở 11.5 pt / 448.22 pt).
  - PUBLICATION_CONTRACTS (`test_publication_contracts.py`): 16/16 PASS.
  - DIAGRAM_ENCODING: MOJIBAKE_HITS=0.
  - DIAGRAM_SEMANTICS: PASS (0 character-art diagrams).
  - VISUAL_MANIFEST: PASS (58 assets).
  - ERROR_ATLAS: PASS (85 entries, 89 patterns).
  - LIBRARY_SOURCES: PASS (50 locked catalog libraries).
  - Go lab tests:
    - `labs/part25-github-automation`: PASS (`test`, `vet`, `race`).
    - `labs/part26-supply-chain-gate`: PASS (`test`, `vet`, `race`).
    - `labs/part27-ebpf-observer`: PASS (`test`, `vet`, `race` cho tầng userspace mock; eBPF kernel load skipped do môi trường Windows).
    - `labs/part28-mcp-ops-tools`: PASS (`test`, `vet`, `race`).
    - `labs/part29-change-evidence`: PASS (`test`, `vet`, `race`).
  - Git diff check (`git diff --check`): PASS (0 lỗi khoảng trắng).

- PDF Preflight (`validate_publication_pdf.py`):
  - Kích thước: 493 trang.
  - Kiểm tra tự động: PASS (0 broken glyphs, 0 clipping, 0 blank pages, 34 bookmarks hợp lệ, 0 duplicate pages).

- Trạng thái kiểm định trực quan (Visual QA Scope):
  - Kiểm tra trực quan được giới hạn ở các trang thuộc phạm vi Chương 25 đến 29 (các trang 339–433) và phụ lục tiếp giáp.
  - Trạng thái: `SCOPED_CH25_CH29_CONTENT_QA_PASS`.
  - Kết luận nội dung Ch25–Ch29: `CH25_CH29_CONTENT_STATUS=FROZEN`.
  - Lưu ý xuất bản: Chưa tuyên bố `BOOK_STATUS=READY` / `PUBLICATION_READY` toàn diện theo đúng nguyên tắc giữ ranh giới xuất bản toàn sách.

---

# Scoped Ch24 credential cache evidence pass close-out (Ch24) — 08-10-2026

Biên bản sửa vi chỉnh ranh giới chứng cứ `aws.CredentialsCache` này áp dụng cho `Golang_Master.pdf` SHA-256
`db679f0f90616eb0249369072b2be70dcebd1307693e9574543a730ad23baf50`,
493 trang, xuất phát từ baseline HEAD `26c900f7dac3ef61f51a27c7277e3d2597a1b01b`.

## Phạm vi sửa và kết quả kiểm định kỹ thuật

Lượt sửa vi chỉnh này giải quyết dứt điểm khoảng cách chứng cứ cuối cùng trong Chương 24 về cơ chế bộ đệm xác thực của AWS SDK for Go v2:

1. Lab Part 24 (`labs/part24-aws-sdk-go-v2/storage_test.go`):
   - Đổi tên và nâng cấp test thành `TestCredentialsCacheReuseAndExpiredRefresh`, bọc provider giả lập vào `cache := aws.NewCredentialsCache(provider)` với tùy chọn mặc định thay vì gọi trực tiếp provider.
   - Kiểm chứng tất định cả hai hợp đồng của `aws.CredentialsCache`:
     * Hợp đồng A (Tái sử dụng khi còn hạn): Lần gọi 1 lấy từ provider (`provider.RetrieveCount() == 1`); lần gọi 2 ngay sau đó khi khóa còn hạn trả về cùng credential từ cache mà không gọi lại provider (`provider.RetrieveCount() == 1`).
     * Hợp đồng B (Làm mới sau khi hết hạn): Chờ credential hết hạn và kiểm tra đồng hồ tường tất định; lần gọi 3 kích hoạt cache gọi lại provider (`provider.RetrieveCount() == 2`) và trả về credential mới khác credential cũ.
   - Test chạy ổn định, triệt tiêu nguy cơ flakiness do GC/thread pause bằng ngưỡng thời gian và vòng lặp đồng hồ an toàn; vượt qua `go test -run TestCredentialsCache -count=20` (và 50 lần liên tiếp) với 100% PASS.

2. Chương 24 (`book/chapters/24-tu-dong-hoa-aws-bang-go.md`):
   - Cập nhật mục `### 1. Tự động làm mới khóa hết hạn (TestCredentialsCacheReuseAndExpiredRefresh)` và block kết quả chạy kiểm thử tương ứng.
   - Miêu tả chính xác hành vi test bọc provider trong `aws.CredentialsCache` với cấu hình mặc định (không suy đoán vượt bằng chứng về `ExpiryWindow`).
   - Giữ nghiêm ngặt ranh giới bằng chứng: khẳng định đây là unit test với fake provider cục bộ nhằm kiểm chứng logic cache nội tại của SDK, không gọi AWS STS thật và không chứng minh credential được làm mới thành công khi hạ tầng mạng hoặc IAM gặp lỗi.

## Kiểm tra xuất bản và trạng thái nghiệm thu

- Mã nguồn và validator:
  - ZERO_BULLET (`validate_main_manuscript_no_bullets.py`): PASS.
  - PROSE_LANGUAGE (`audit_prose_language.py`): PASS (76.96% overall; Ch24: 77.6%).
  - CODE_WIDTH (`validate_code_width.py`): PASS (0 dòng tràn ở giới hạn monospace printable width).
  - PUBLICATION_CONTRACTS (`test_publication_contracts.py`): 16/16 PASS.
  - Go lab tests:
    - `labs/part24-aws-sdk-go-v2`: PASS (`test`, `vet`, `race`, `count=20`).
  - Git diff check (`git diff --check`): PASS (0 lỗi khoảng trắng).

- PDF Preflight (`validate_publication_pdf.py`):
  - Kích thước: 493 trang.
  - Kiểm tra tự động: PASS (0 broken glyphs, 0 clipping, 0 blank pages, 34 bookmarks hợp lệ, 0 duplicate pages).

- Trạng thái kiểm định trực quan (Visual QA Scope):
  - Kiểm tra trực quan được giới hạn ở các trang thuộc phạm vi Chương 24 (các trang 321–337).
  - Trạng thái: `SCOPED_CH24_CREDENTIAL_CACHE_EVIDENCE_PASS`.
  - Kết luận nội dung Ch21–24: `CH21_CH24_CONTENT_STATUS=FROZEN`.
  - Lưu ý xuất bản: Chưa tuyên bố `BOOK_STATUS=READY` / `PUBLICATION_READY` toàn diện theo đúng nguyên tắc giữ ranh giới xuất bản toàn sách.

---

# Final micro-correctness repair close-out (Ch23–Ch24) — 08-10-2026

Biên bản sửa vi chỉnh tính đúng kỹ thuật và ranh giới chứng cứ cuối cùng này áp dụng cho `Golang_Master.pdf` SHA-256
`3cfb07121a0b266143f8aa1eded18c4b9ec85c43d46bdc7ebb81f68390ecc250`,
493 trang, xuất phát từ baseline HEAD `db81e9e08a04f540cf4854712194ae3ed531e9de`.

## Phạm vi sửa và kết quả kiểm định kỹ thuật

Lượt sửa vi chỉnh cuối cùng này giải quyết dứt điểm 3 ranh giới chứng cứ/tính đúng kỹ thuật trước khi freeze Ch21–Ch24:

1. Chương 23 (OwnerReference scope semantics & heading):
   - Đổi tiêu đề mục sang tiếng Việt trung tính: `### OwnerReference giúp quản lý vòng đời thế nào` (loại bỏ từ khoa trương "tối cao").
   - Chuẩn hóa chính xác ngữ nghĩa tham chiếu theo Kubernetes Garbage Collection official specification:
     * Đối với namespaced dependent: có thể tham chiếu owner namespaced trong cùng namespace hoặc owner cluster-scoped. Nếu trỏ tới owner namespaced ở namespace khác, tham chiếu không hợp lệ và được coi như owner không tồn tại; dependent có thể bị thu hồi khi mọi owner hợp lệ khác không còn.
     * Đối với cluster-scoped dependent: chỉ được phép tham chiếu owner cluster-scoped. Nếu trỏ tới namespaced owner, tham chiếu trở thành unresolvable; từ Kubernetes v1.20+ garbage collector ghi nhận warning event `OwnerRefInvalidNamespace`, và dependent không thể được thu hồi dựa trên tham chiếu đó.
     * Loại bỏ nhận định chung chung "GC bỏ qua".

2. Chương 24 (S3 PutObject Idempotency boundary):
   - Thu hẹp ranh giới tính lũy đẳng: không mô tả "cùng key trong S3" như một cơ chế lũy đẳng phổ quát.
   - Làm rõ ngữ nghĩa của S3 `PutObject`: đối với bucket bật Versioning, nhiều lượt `PUT` với cùng một key sẽ tạo ra các object version riêng biệt chứ không ghi đè tại chỗ; do đó cùng key không đảm bảo một tác dụng phụ duy nhất.
   - Nêu rõ giải pháp có điều kiện: khi nghiệp vụ đòi hỏi tạo mới hoặc tránh ghi đè, hệ thống có thể cần conditional request (`If-None-Match: *` khi dịch vụ hỗ trợ), nhưng đây không phải giải pháp vạn năng.
   - Nhấn mạnh nguyên tắc cốt lõi: SDK transport retry (`aws.Retryer`) không đồng nghĩa với tính lũy đẳng nghiệp vụ (business idempotency).

3. Chương 24 & Lab Part 24 (Kiểm thử thực sự cho typed S3 errors):
   - Bổ sung unit test xác minh trực tiếp trong `labs/part24-aws-sdk-go-v2/storage_test.go` (`TestErrorClassification`) cho hai kiểu lỗi dịch vụ S3 mô hình hóa: `types.NoSuchKey` và `types.NoSuchBucket` (thông qua `errors.As` với lỗi được bọc qua `fmt.Errorf`).
   - Xác nhận cả hai lỗi đều được phân loại `isRetryable == false` và trích xuất đúng mã lỗi (`"NoSuchKey"`, `"NoSuchBucket"`), bên cạnh các lỗi `SlowDown` và `AccessDenied` của `smithy.GenericAPIError`.
   - Cập nhật văn bản Chương 24 để xác nhận cả nhánh typed error đã được bao phủ bởi test thực sự của lab.

## Kiểm tra xuất bản và trạng thái nghiệm thu

- Mã nguồn và validator:
  - ZERO_BULLET (`validate_main_manuscript_no_bullets.py`): PASS.
  - PROSE_LANGUAGE (`audit_prose_language.py`): PASS (76.95% overall; Ch23: 73.5%, Ch24: 77.4%).
  - CODE_WIDTH (`validate_code_width.py`): PASS (0 dòng tràn ở 11.5 pt / 448.22 pt).
  - PUBLICATION_CONTRACTS (`test_publication_contracts.py`): 16/16 PASS.
  - DIAGRAM_ENCODING: MOJIBAKE_HITS=0.
  - DIAGRAM_SEMANTICS: PASS (0 character-art diagrams).
  - VISUAL_MANIFEST: PASS (58 assets).
  - ERROR_ATLAS: PASS (85 entries, 89 patterns).
  - LIBRARY_SOURCES: PASS (50 locked catalog libraries).
  - Go lab tests:
    - `labs/part24-aws-sdk-go-v2`: PASS (`test`, `vet`, `race` 100%).
  - Git diff check (`git diff --check`): PASS (0 lỗi khoảng trắng).

- PDF Preflight (`validate_publication_pdf.py`):
  - Kích thước: 493 trang.
  - Kiểm tra tự động: PASS (0 broken glyphs, 0 clipping, 0 blank pages, 34 bookmarks hợp lệ, 0 duplicate pages).

- Trạng thái kiểm định trực quan (Visual QA Scope):
  - Kiểm tra trực quan được giới hạn ở các trang thuộc phạm vi Chương 23 và 24 (các trang 305–337) và các trang chịu tác động reflow trực tiếp.
  - Trạng thái: `SCOPED_CH23_CH24_FINAL_CORRECTION_PASS`.
  - Kết luận nội dung Ch21–24: `CH21_CH24_CONTENT_STATUS=FREEZE_CANDIDATE`.

---

# Content correctness audit and targeted repair close-out (Ch21–Ch24) — 07-10-2026

Biên bản kiểm định tính đúng nội dung và sửa chữa có trọng tâm này áp dụng cho `Golang_Master.pdf` SHA-256
`95e761b8f09f0ca8190ebb593ff1612a9ca270c56a6c90c9c817fb3931abc51b`,
492 trang, xuất phát từ baseline HEAD `6e778159944c1661c1c41bf40588ce9908f4e649`.

## Phạm vi sửa và kết quả kiểm định kỹ thuật

Lượt kiểm định tập trung vào tính đúng kỹ thuật, ranh giới chứng cứ và mạch sư phạm liên chương của Chương 21 đến Chương 24:

1. Chương 21 (Vòng lặp điều hòa và Controller Pattern):
   - Kết luận: PASS — không có thay đổi mã nguồn/nội dung (no material change). Mô hình điều hòa (Observe -> Diff -> Act -> Observe again), tính lũy đẳng nghiệp vụ, ranh giới thất bại, context cancellation và WorkQueue đã được thiết kế chính xác và đối chiếu đầy đủ với bộ kiểm thử trong `labs/part21-reconciliation-controller`.

2. Chương 22 (Từ watch đến controller Kubernetes thật):
   - Chuẩn hóa ngôn ngữ quan sát cache: sửa chú thích mã nguồn và văn xuôi (dòng 225, 318, 343) để không gọi cache là "snapshot mới nhất" mà xác định đúng là "snapshot quan sát hiện có từ local indexer"; trong thao tác cập nhật khi gặp xung đột (`retry.RetryOnConflict`), xác định rõ việc đọc lại snapshot hiện tại trực tiếp từ API Server.

3. Chương 23 (Từ controller đến operator: API riêng và vòng đời tài nguyên):
   - Ranh giới OwnerReferences: bổ sung quy tắc giới hạn namespace trong Kubernetes — `OwnerReference` không hoạt động xuyên namespace (cross-namespace); Garbage Collector sẽ bỏ qua hoặc từ chối các tham chiếu cross-namespace.
   - Ngữ nghĩa trả về của Result và Error trong controller-runtime: bổ sung tiểu mục giải thích tường minh hợp đồng xử lý bốn nhánh của `reconcileHandler` trong `sigs.k8s.io/controller-runtime` v0.25.1 (`err != nil` kích hoạt rate-limited requeue; `RequeueAfter` lên lịch lại sau khoảng trễ; `Requeue: true` kích hoạt rate-limited requeue; và `ctrl.Result{}, nil` hoàn tất điều hòa).

4. Chương 24 (Tự động hóa AWS bằng Go mà không biến credential thành bí mật dài hạn):
   - Kết nối mạch liên chương: liên kết tư duy điều hòa và tính lũy đẳng từ Chương 21–23 sang việc tự động hóa AWS API.
   - Chuỗi phân giải Region: bổ sung tiểu mục về phân giải Region qua `config.LoadDefaultConfig` (tùy chọn tường minh, biến môi trường, file config, IMDS) và ranh giới hoạt động giữa dịch vụ toàn cầu và dịch vụ vùng (đặc biệt là tính chất vùng của Amazon S3 bucket).
   - Thử lại transport so với tính lũy đẳng nghiệp vụ: phân định rõ việc `aws.Retryer` tự động thử lại ở tầng transport không bảo đảm tính lũy đẳng nghiệp vụ nếu thao tác ghi bị ngắt quãng sau khi server đã tiếp nhận; nhấn mạnh vai trò của `ClientToken` và ghi đè theo key.
   - Bóc tách lỗi có cấu trúc: cập nhật hàm `ClassifyError` để kiểm tra các kiểu lỗi nghiệp vụ mô hình hóa cụ thể (`*types.NoSuchKey`, `*types.NoSuchBucket`) bằng `errors.As` trước khi kiểm tra interface `smithy.APIError`, đồng bộ chính xác với `labs/part24-aws-sdk-go-v2/storage.go`.

## Kiểm tra xuất bản và trạng thái nghiệm thu

- Mã nguồn và validator:
  - ZERO_BULLET (`validate_main_manuscript_no_bullets.py`): PASS.
  - PROSE_LANGUAGE (`audit_prose_language.py`): PASS (76.93% overall; Ch21: 79.7%, Ch22: 81.3%, Ch23: 73.6%, Ch24: 76.5%).
  - CODE_WIDTH (`validate_code_width.py`): PASS (0 dòng tràn ở 11.5 pt / 448.22 pt).
  - PUBLICATION_CONTRACTS (`test_publication_contracts.py`): 16/16 PASS.
  - DIAGRAM_ENCODING: MOJIBAKE_HITS=0.
  - DIAGRAM_SEMANTICS: PASS (0 character-art diagrams).
  - VISUAL_MANIFEST: PASS (58 assets).
  - ERROR_ATLAS: PASS (85 entries, 89 patterns).
  - LIBRARY_SOURCES: PASS (50 locked catalog libraries).
  - Go lab tests:
    - `labs/part21-reconciliation-controller`: PASS (`test`, `vet`, `race`).
    - `labs/part22-client-go-controller`: PASS (`test`, `vet`, `race`).
    - `labs/part23-controller-runtime-operator`: PASS (`test`, `vet`, `race`).
    - `labs/part24-aws-sdk-go-v2`: PASS (`test`, `vet`, `race`).
  - Git diff check (`git diff --check`): PASS (0 lỗi khoảng trắng).

- PDF Preflight (`validate_publication_pdf.py`):
  - Kích thước: 492 trang.
  - Kiểm tra tự động: PASS (0 broken glyphs, 0 clipping, 0 blank pages, 34 bookmarks hợp lệ, 0 duplicate pages).

- Trạng thái kiểm định trực quan (Visual QA Scope):
  - Kiểm tra trực quan được giới hạn ở các trang thuộc phạm vi Chương 21–24 (trang 277 đến 337) và các trang chịu tác động reflow trực tiếp.
  - Các trang khác toàn sách không nằm trong phạm vi rà soát trực quan lại trong pass này.
  - Trạng thái: `SCOPED_CH21_CH24_CONTENT_QA_PASS`. Không tuyên bố `PUBLICATION_READY` khi chưa có visual ledger toàn sách độc lập.

---

# Middle-book correctness repair close-out — 07-10-2026

Biên bản sửa tính đúng và thu hẹp ranh giới chứng cứ này áp dụng cho `Golang_Master.pdf` SHA-256
`e3cb715a986dc1f2ee42f06d929c8ac5ab633749c55b836ac35b0f5fc2550b17`,
490 trang, xuất phát từ baseline HEAD `c4c25c93b6ac89a9b0d7b1c6de2445b2f12ccc73`.

## Phạm vi sửa và bằng chứng kỹ thuật

Lượt sửa hẹp này tập trung vào tính đúng kỹ thuật và ranh giới chứng cứ của Chương 10 và Chương 13 sau lượt chỉnh lý middle-book:

1. Chương 10 (Execution Trace và pprof):
   - Đưa trace model về đúng tập trạng thái `internal/trace.GoState` trong runtime Go 1.27.1 (`GoUndetermined`, `GoNotExist`, `GoRunnable`, `GoRunning`, `GoWaiting`, `GoSyscall`), tách bạch `GoSyscall` khỏi `GoWaiting` (chặn nhầm lẫn giữa non-blocking runtime handoff và parking).
   - Mô tả execution trace là cơ chế ghi nhận tập sự kiện mở rộng của runtime trong khoảng thời gian kích hoạt, không phải dòng thời gian toàn tri (omniscient) hay profile liên tục mọi thời điểm.
   - Bỏ khẳng định "Runnable trực tiếp chứng minh nghẽn scheduler"; bổ sung 4 pprof profiles phục vụ khoanh vùng tương tranh/hệ thống (`sync`, `sched`, `syscall`, `net`).
   - Loại bỏ suy đoán nội bộ runtime scheduler (ngữ cảnh chuyển đổi user-space, tính bắt buộc của handoffp, GC mark assist tuyệt đối).
   - Lab Part 10 giữ nguyên workload Option A và đối chiếu các độ trễ quan sát thực nghiệm từ profile trích xuất (`sync.pprof`, `sched.pprof`, `syscall.pprof`): `sync.(*WaitGroup).Wait`, `runtime.chanrecv1`, `runtime.(*traceAdvancerState).start`, `sync.(*WaitGroup).Add`, `syscall.syscalln`.

2. Chương 13 (Persistence, Transaction boundary, DDL và Cache-aside):
   - Chuẩn hóa chính sách connection pool: `SetConnMaxLifetime` đóng lười (lazy close) kết nối hết hạn khi hoàn trả thay vì ép hủy giữa chừng khi kết nối đang bận; `SetMaxIdleConns` mặc định 2 được ghim theo tài liệu Go hiện hành cùng lưu ý về khả năng thay đổi trong tương lai.
   - `DB.Stats()` được xác định là dữ liệu quan sát chẩn đoán phục vụ định hướng, không phải bằng chứng nguyên nhân gốc rễ.
   - Ranh giới Prepared Statement: phân biệt rõ ràng vòng đời của `DB.PrepareContext` (gắn với pool) và `Tx.PrepareContext` (gắn với transaction, tự động đóng/vô hiệu khi commit hoặc rollback). Bỏ tuyên bố suy đoán chưa kiểm chứng về tăng gấp đôi gói tin mạng.
   - SQL Injection: phân định ranh giới binding tham số giá trị (`?`, `$1`) chỉ bảo vệ dữ liệu, không tham số hóa được tên bảng/cột/mệnh đề động; các thành phần động bắt buộc phải kiểm tra qua allowlist chặt chẽ theo hướng dẫn `go.dev/doc/database/sql-injection`.
   - Ngữ nghĩa DDL: phân định rõ DDL theo từng hệ CSDL (PostgreSQL hỗ trợ DDL giao dịch có ngoại lệ/lock; SQLite fixture kiểm chứng rollback thành công; MySQL thực thi atomic DDL theo câu lệnh nhưng kích hoạt implicit commit kết thúc giao dịch bao quanh).
   - Lab Part 13: bổ sung test case rollback migration thực sự trong `TestSchemaMigrationOrderingAndRollback`, kiểm tra thất bại migration, rollback, dùng `PRAGMA table_info` và bảng schema version xác nhận cột chưa hề được thêm và version không tăng, trước khi áp dụng v2 thành công.
   - Thu hẹp ranh giới: Expand-Migrate-Contract và forward-fix là chiến lược giảm thiểu rủi ro, không phải giáo điều tuyệt đối; cache-aside coi DB là source of truth trong phạm vi chương này, TTL giới hạn cửa sổ dữ liệu cũ chứ không chứng minh tính nhất quán thời gian thực.
   - Tương thích serialization: chuẩn hóa theo ranh giới hợp đồng giữa bên ghi và bên đọc của Chương 7; `omitempty`/`omitzero` là tùy chọn serialization, không thay thế việc kiểm soát hợp đồng trường dữ liệu.
   - Bổ sung 7 tài liệu tham khảo chính thức từ Go spec, standard library (`database/sql`, `database/sql/driver`), `internal/trace`, và tài liệu bảo mật Go.

## Kiểm tra xuất bản và trạng thái nghiệm thu

- Mã nguồn và validator:
  - ZERO_BULLET (`validate_main_manuscript_no_bullets.py`): PASS.
  - CODE_WIDTH (`validate_code_width.py`): PASS (0 dòng tràn ở 11.5 pt).
  - ERROR_ATLAS: PASS (85 entries).
  - DIAGRAM_ENCODING: MOJIBAKE_HITS=0.
  - DIAGRAM_SEMANTICS: PASS (0 character-art diagrams).
  - VISUAL_MANIFEST: PASS.
  - PUBLICATION_CONTRACTS (`test_publication_contracts.py`): 16/16 PASS.
  - Go lab tests: `labs/part13-transaction-boundary` PASS (`go test -v ./fixed`, `go test -race ./fixed`).
  - Git diff check (`git diff --check`): PASS (0 lỗi khoảng trắng).

- PDF Preflight (`validate_publication_pdf.py`):
  - Kích thước: 490 trang (tăng 2 trang do chuẩn hóa phân tích trace Ch10 và ngữ nghĩa DDL Ch13).
  - Kiểm tra tự động: PASS (0 broken glyphs, 0 clipping, 0 blank pages, 34 bookmarks hợp lệ).

- Trạng thái kiểm định trực quan (Visual QA Scope):
  - Do lượt này là sửa chữa tính đúng cục bộ (scoped correctness repair) tập trung vào Ch10 và Ch13 cùng lab tương ứng, review trực quan chỉ giới hạn ở các trang và nội dung chịu tác động trực tiếp của Ch10, Ch13 và các kiểm định preflight tự động toàn sách.
  - Các trang khác không nằm trong phạm vi rà soát trực quan lại từng trang trong pass này.
  - Trạng thái: `SCOPED_MIDDLE_BOOK_REPAIR_QA_PASS`. Không tuyên bố `PUBLICATION_READY` toàn diện khi chưa thực hiện visual ledger 490 trang đầy đủ.

---

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
