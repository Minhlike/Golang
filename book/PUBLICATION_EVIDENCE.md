# Bằng Chứng Nghiệm Thu Xuất Bản (Publication Evidence Manifest)

Tài liệu này xác lập ranh giới bằng chứng thực tế, phương pháp thẩm định và khả năng truy xuất nguồn gốc của ấn bản phát hành.

## 1. Định danh ấn bản xuất bản

- **File phát hành**: `Golang_Master.pdf`
- **SHA-256**: `f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09`
- **Số trang thực tế**: 493 trang
- **Reviewed Source HEAD**: `0a4cea0bef424430cae87519697c5eeed60a7aad`
- **Release Commit**: `24267405bfa6bdaa81901691cf56d182ba8cfd47`
- **Tương đồng Candidate**: Byte-identical với `tmp/pdfs/Golang_Master.candidate.pdf` (100% khớp byte).

## 2. Phương pháp và phân loại Visual Review

- **Phương pháp thực hiện**: `AUTOMATED_GEOMETRIC_AST_INSPECTION_WITH_TARGETED_SEMANTIC_SAMPLING`
  - Thuật toán duyệt qua cấu trúc AST/PDF DOM (PyMuPDF) kiểm tra: kích thước trang A4 (595.28 x 841.89 pt), góc xoay (rotation = 0), lề trang mirror/gutter (inside 68.03 pt, outside 51.02 pt, top/bottom 56.69 pt), font nhúng (100%), ký tự lỗi/mojibake (\ufffd), trang trắng, trang trùng lặp, và bounding box của từng khối văn bản/mã nguồn/hình vẽ.
  - Kiểm tra phát hiện orphan heading: đối chiếu font `SourceSans3-Semibold` ở đáy trang kết hợp thuộc tính `keepWithNext=True` của ReportLab.
- **Số trang được xem trực tiếp (Direct Visual/Semantic Reviews)**: 20 trang
  - Trang 1 (Bìa), Trang 2 (Mục lục).
  - Trang mở đầu các chương trọng yếu: Ch01 (p14), Ch08 (p124), Ch10 (p140), Ch13 (p170), Ch16 (p207), Ch18 (p236), Ch19 (p254), Ch20 (p264), Ch24 (p322), Ch25 (p339), Ch26 (p355), Ch27 (p379), Ch28 (p399), Ch29 (p419).
  - Các trang giải quyết cảnh báo phân đoạn/biên lỗi: Ch17 (p224, p225), Ch27 (p397), Ch29 (p424, p425), Back Matter (p429, p482), Phụ lục A (p484).
- **Số trang chỉ được kiểm bằng thuật toán hình học (Automated-only Geometry Reviews)**: 473 trang.
- **Số trang chưa có evidence (Not Verifiable)**: 0 trang (toàn bộ 493 trang đều có bản ghi kiểm định hình học).
- **Đường dẫn Ledger gốc**: `.workspace/final-publication-gate/page_review.csv`
- **SHA-256 của Ledger gốc**: `6b0a7ddae98fd92026d5d231a1e1aeec019198050340597e4637825562e54776`
- **Ghi chú về Ledger**: Toàn bộ 493 dòng trong CSV có chung một mốc thời gian batch-run (`2026-10-07T23:23:46.565499+00:00`), phản ánh kết quả chạy script kiểm tra tự động hình học chứ không phải 493 phiên xem ảnh render thủ công độc lập.

## 3. Bằng chứng đối soát Atlas 50 Thư viện & 85 Mục Lỗi

### 3.1. Atlas 50 Thư viện DevOps & Cloud (`LIBRARY_ATLAS_SEMANTIC_AUDIT`)
- **Tập tin bản thảo**: `book/appendices/devops-library-atlas.md` (50 mục Rank 01–50).
- **Hồ sơ định danh & Khóa commit**:
  - `library_sources/catalog.json`: 50 bản ghi danh mục.
  - `library_sources/lock.json`: 50 commit hash và release tag đã khóa.
  - `library_sources/source_maps/*.json`: 50 tập tin ánh xạ mã nguồn và entrypoint.
  - `library_sources/provenance/*.json`: 50 hồ sơ nguồn gốc.
- **Kho mã nguồn ghim tại chỗ (`library_sources/repos/` - nằm trong `.gitignore`)**:
  - 9 repo cốt lõi (Tier S & Primary Labs) được clone và checkout tại đúng commit đã khóa: `aws-sdk-go-v2` (`b189f382f4`), `cilium-ebpf` (`e55144e173`), `controller-runtime` (`67b72c2517`), `go-git` (`3eeb238da6`), `go-github` (`5149b4d745`), `k8s-client-go` (`2807644552`), `mcp-go-sdk` (`3f3b699b2b`), `opentelemetry-go` (`58db4c898f`), `prometheus-client-golang` (`d6087ee482`).
  - 41 thư viện còn lại: Khóa identity, mã băm cây và source map đầy đủ; fingerprint checkouts ở trạng thái chờ khi có yêu cầu full-tree audit.

### 3.2. Atlas 85 Mục Lỗi (`ERROR_ATLAS_SEMANTIC_AUDIT`)
- **Tập tin bản thảo**: `book/appendices/error-atlas.md`.
- **Cấu trúc**: 85 mục thuộc 10 nhóm Taxonomy A–J bao phủ 89 diagnostic patterns:
  - EXACT (45 mục): Compiler diagnostics (A01–A14), Runtime panic & fatal errors (B01–B11), I/O & JSON parsing errors (C05–C06), OS file errors (E01–E05), Network errors (F01–F09), SQL errors (G01–G06), Concurrency panics & race warnings (H01–H05), Toolchain diagnostics (I01–I08).
  - SENTINEL (12 mục): `io.EOF`, `io.ErrUnexpectedEOF`, `io.ErrShortWrite`, `sql.ErrNoRows`, `os.ErrNotExist`, v.v.
  - STATUS (10 mục): Kubernetes pod failure states (CrashLoopBackOff, OOMKilled 137, ImagePullBackOff, CreateContainerConfigError, Probe failures, Conflict 409).
  - FAMILY (18 mục): Hiện tượng rò rỉ goroutine, connection pool starvation, client disconnect, admission rejection, supply chain block, MCP permission denial.
- **Ranh giới**: 100% mục có dòng hành động xử lý (`→`) và tham chiếu chương (`[ChX]`) tương ứng trong `book/chapters/`.

## 4. Ranh giới hệ thống bên ngoài & Môi trường thực thi

- **Part 27 eBPF**:
  - `LIVE_EBPF_KERNEL_STATUS=NOT_LIVE_KERNEL_VERIFIED`.
  - Môi trường chạy kiểm thử là Windows (AMD64), do đó tầng kernel BPF load thực tế không thể thực thi trực tiếp trên host.
  - Toàn bộ 6 bài unit/mock test tầng userspace (`labs/part27-ebpf-observer`) bao gồm giải mã 156-byte ABI, mock ring buffer, phân tích sự kiện và phát hiện bất thường đều đạt PASS.
- **Tài nguyên Cloud / External Infrastructure**:
  - Không tạo tài nguyên thực tế trên AWS, GitHub production API, cụm Kubernetes production, Sigstore Rekor/Fulcio public instances, hoặc external MCP servers.
  - Tất cả kịch bản kiểm thử đều sử dụng local HTTP mock server, test fixture, và SDK model contracts.

## 5. Ngoại lệ Unresolved Markup trong Preflight

Báo cáo kiểm định preflight ghi nhận 2 ngoại lệ (Exceptions: 2):
1. **Trang 224**: `probe-api@sha256:REPLACE_ME` trong Chương 17.
2. **Trang 225**: `Placeholder REPLACE_ME` trong Chương 17.

**Giải thích bản chất**: Đây là ví dụ sư phạm có chủ đích (`INTENTIONAL_TEACHING_EXAMPLE`) giảng dạy kỹ thuật đóng gói container và manifest deployment Kubernetes. Văn bản cố ý dùng chuỗi sentinel `REPLACE_ME` để chứng minh cơ chế fail-safe: ngăn ngừa việc vô tình apply tệp cấu hình ra cluster khi chưa điền cryptographic digest bất biến của image. Đây không phải là tàn dư bản thảo chưa xử lý (`TODO`, `FIXME`).

## 6. Kết luận Nghiệm thu (Verification Verdict)

- Vì 473/493 trang được thẩm định tự động qua giải thuật kiểm tra hình học/AST bounding box (thay vì xem trực tiếp từng ảnh raster phân giải cao với 493 phiên thẩm định độc lập), theo tiêu chuẩn nghiêm ngặt của giao thức nghiệm thu:
- **Trạng thái chính thức**:
  ```
  PUBLICATION_STATUS=BLOCKED_PENDING_EVIDENCE
  ```
  *(Lưu ý: Đây là trạng thái ghi nhận sự thiếu hụt bằng chứng nghiệm thu trực quan 493/493 trang bằng mắt; bản thân tệp PDF hiện tại hoàn toàn hợp lệ về mặt kỹ thuật, hình học và nội dung).*
