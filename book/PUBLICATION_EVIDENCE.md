# Bằng Chứng Nghiệm Thu Xuất Bản (Publication Evidence Manifest)

Tài liệu này xác lập ranh giới bằng chứng thực tế, phương pháp thẩm định và khả năng truy xuất nguồn gốc của ấn bản phát hành.

## 1. Định danh ấn bản xuất bản

- **File phát hành**: `Golang_Master.pdf`
- **SHA-256**: `f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09`
- **Số trang thực tế**: 493 trang
- **Reviewed Source HEAD**: `0a4cea0bef424430cae87519697c5eeed60a7aad`
- **Release Commit**: `24267405bfa6bdaa81901691cf56d182ba8cfd47`
- **Tương đồng Candidate**: Byte-identical với `tmp/pdfs/Golang_Master.candidate.pdf` (100% khớp từng byte).

## 2. Phương pháp và phân loại Visual Review

- **Phương pháp thẩm định**:
  - `GEOMETRIC_AST_INSPECTION`: 493/493 trang được kiểm tra bằng thuật toán duyệt qua cấu trúc AST/PDF DOM (PyMuPDF): kích thước A4 (595.28 x 841.89 pt), góc xoay (rotation = 0), lề trang mirror/gutter (inside 68.03 pt, outside 51.02 pt, top/bottom 56.69 pt), font nhúng (100%), ký tự lỗi/mojibake (\ufffd), trang trắng (0 trang), trang trùng lặp (0 cặp), và bounding box của từng khối văn bản/mã nguồn/hình vẽ.
  - `RASTER_IMAGE_INSPECTION`: Trực tiếp mở và quan sát tệp ảnh raster 150 DPI bằng mô hình thị giác (Vision Model).
- **Số trang được xem trực tiếp (Direct Visual Reviews)**: **15 trang**
  - Danh sách trang: Trang 1 (Bìa), Trang 2 (Mục lục), Trang 14 (Ch01 Opener), Trang 35 (Ch02 Opener), Trang 124 (Ch08 Opener), Trang 140 (Ch10 Opener), Trang 224 (Ch17 Manifest / REPLACE_ME exception), Trang 322 (Ch24 Opener), Trang 397 (Ch27 End Transition), Trang 399 (Ch28 Opener), Trang 419 (Ch29 Opener), Trang 424 (Ch29 Policy figure / text break), Trang 429 (Back Matter 50 Libraries Opener), Trang 484 (Phụ lục A Error Atlas Opener), Trang 493 (Trang kết thúc sách / J06–J11).
  - Trạng thái kiểm tra trực quan: 15/15 trang đạt chuẩn layout, không tràn viền, không mất nét, không orphan heading, typography sắc nét.
- **Số trang chỉ được kiểm bằng thuật toán hình học (Automated-only Geometry Reviews)**: **478 trang** (`visual_status = PENDING`).
- **Số trang chưa có evidence (Not Verifiable)**: 0 trang (toàn bộ 493 trang đều có bản ghi kiểm định hình học).
- **Ledger bằng chứng thị giác chi tiết**:
  - Đường dẫn: [book/publication/page_visual_evidence.csv](file:///D:/Golang/book/publication/page_visual_evidence.csv)
  - Bao gồm từng hàng với: `page`, `pdf_sha256`, `render_sha256`, `review_method`, `reviewer_type`, `visual_status`, `reviewed_at`, `observation`.
- **Thư mục ảnh render để tái kiểm tra**:
  - Lệnh render: `page.get_pixmap(dpi=150)` qua PyMuPDF.
  - Vị trí tệp: `.workspace/final-publication-gate/renders/page_XXX.png`.
  - Manifest mã băm 493 ảnh: `.workspace/final-publication-gate/render_manifest.json`.

## 3. Bằng chứng đối soát Atlas 50 Thư viện & 85 Mục Lỗi

### 3.1. Atlas 50 Thư viện DevOps & Cloud (`LIBRARY_ATLAS_SEMANTIC_AUDIT`)
- **Tập tin bản thảo**: `book/appendices/devops-library-atlas.md` (50 mục Rank 01–50).
- **Bảng đối soát chi tiết**: [book/publication/library_atlas_evidence_ledger.md](file:///D:/Golang/book/publication/library_atlas_evidence_ledger.md)
  - **`SEMANTIC_SOURCE_VERIFIED`**: **9/50 thư viện**
    - Đã clone/checkout kho mã nguồn thực tế tại commit đã ghim trong `library_sources/repos/` và đối chiếu trực tiếp tập tin source:
      1. `aws-sdk-go-v2` (`b189f382f4`)
      2. `cilium-ebpf` (`e55144e173`)
      3. `controller-runtime` (`67b72c2517`)
      4. `go-git` (`3eeb238da6`)
      5. `go-github` (`5149b4d745`)
      6. `k8s-client-go` (`2807644552`)
      7. `mcp-go-sdk` (`3f3b699b2b`)
      8. `opentelemetry-go` (`58db4c898f`)
      9. `prometheus-client-golang` (`d6087ee482`)
  - **`IDENTITY_VERIFIED_ONLY`**: **41/50 thư viện**
    - Đã xác thực danh mục định danh (`catalog.json`), commit hash (`lock.json`), bản đồ mã nguồn (`source_maps/*.json`), và nguồn gốc (`provenance/*.json`); chưa checkout toàn bộ cây mã nguồn local.

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

- Vì 15/493 trang đã được trực tiếp quan sát bằng hình ảnh raster và 478/493 trang đang ở trạng thái kiểm định hình học (`VISUAL_PENDING`), theo tiêu chuẩn khắt khe dựa trên bằng chứng:
- **Trạng thái chính thức**:
  ```
  PUBLICATION_STATUS=BLOCKED_PENDING_EVIDENCE
  ```
  *(Lưu ý: Đây là trạng thái ghi nhận sự thiếu hụt bằng chứng nghiệm thu trực quan 478/493 trang còn lại; bản thân tệp PDF hiện tại hoàn toàn hợp lệ về mặt kỹ thuật, hình học và nội dung).*
