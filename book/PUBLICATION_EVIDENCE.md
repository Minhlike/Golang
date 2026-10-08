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
- **Số trang được xem trực tiếp (Direct Visual Reviews)**: **352 trang**
  - Danh sách và phạm vi trang:
    - Trang 1 (Bìa) & Trang 2 (Mục lục)
    - Trang 3–13: Lời mở đầu & Toàn bộ Chương 00 (11 trang)
    - Trang 14–34: Toàn bộ Chương 01 (21 trang: cú pháp, kiểu dữ liệu, điều khiển luồng, hàm, con trỏ, compiler Plan 9 vs objdump)
    - Trang 35–44: Toàn bộ Chương 02 (10 trang: mảng, slice header, mutation, growslice, full slice expression, UTF-8 strings)
    - Trang 45–67: Toàn bộ Chương 03 (23 trang: pass-by-value, pointer semantics, struct nesting, map internals, type identity, method receiver, embedding, interfaces, typed nil, comparability)
    - Trang 68–80: Toàn bộ Chương 04 (13 trang: biên lỗi, sentinel errors, %w wrapping, errors.Is/As, error contracts, context cancellation vs health, defer cleanup, recover anti-pattern, Bảng 3 & Bảng 4, Hình 17 & Hình 18)
    - Trang 81–93: Toàn bộ Chương 05 (13 trang: package boundary, DAG khởi tạo gói, import cycle, cấu hình an toàn, net.SplitHostPort, IPv6, loại bỏ bool không rõ nghĩa, go.mod/MVS/replace, go.work, toolchain Go 1.27 vs language version, build tags //go:build, cross-compilation, Hình 19)
    - Trang 94–113: Toàn bộ Chương 06 (20 trang: refactor kiểm chứng quanh app.Run, Bảng 3 phạm vi unit test, Bảng 4 policy lỗi cấu hình vs probe, table-driven test, ngữ nghĩa biến lặp Go 1.22+, bẫy &tt, lọc test -run, race detector, Bảng 5 race report, sync.Mutex, sync.WaitGroup, fuzzing với invariant property, seed corpus, benchmark với b.Loop() Go 1.24/1.27.1, contract stdout/stderr process boundary)
    - Trang 114–123: Toàn bộ Chương 07 (10 trang: mô hình stream byte-by-byte, io.Reader/Writer contract, io.EOF, Bảng 6 kết quả Read, io.LimitReader, json.NewDecoder xử lý trailing data, encoding/json v1 vs v2 duplicate keys, flush/close defer, short write sentinel, bufio user-space buffering 4096B, Bảng đối chiếu 5 Reader vs Syscall, Linux fd_unix vs Windows IOCP, io/fs, embed.FS, os.Root, bufio.Scanner giới hạn token)
    - Trang 124–131: Toàn bộ Chương 08 (8 trang: race hazards, Go Memory Model, Happens-before, Mutex vs WaitGroup, sync.Once, sync.Cond, atomic.Pointer, Hình 20, Bảng 7)
    - Trang 132–139: Toàn bộ Chương 09 (8 trang: channel backpressure, select timeout/cancellation, buffer backlog, ownership đóng kênh, worker pool contract, G/M/P coordination, hchan internals, Hình 21, Bảng 8)
    - Trang 140–152: Toàn bộ Chương 10 (13 trang: compiler escape analysis, SSA prove / bounds check elimination, GC mark-sweep & mgcpacer, Green Tea GC, GOGC, GOMEMLIMIT, benchmark b.Loop(), pprof CPU/mem, execution trace G/M/P states, PGO, Hình 22, Bảng đối chiếu chẩn đoán)
    - Trang 153–159: Toàn bộ Chương 11 (7 trang: HTTP request lifecycle, net/http/httptrace, TLS handshake, context deadlines, connection reuse, body draining contract, Hình 23, Bảng 9)
    - Trang 160–169: Toàn bộ Chương 12 (10 trang: service graceful shutdown, ServeUntilStopped, signal.NotifyContext, MaxBytesReader, JSON decoding EOF strictness, server timeouts, Hình 24, Bảng 10)
    - Trang 170–181: Toàn bộ Chương 13 (12 trang: transaction atomicity, db.BeginTx, defer tx.Rollback, RowsAffected, database/sql connection pool, SetMaxOpenConns/IdleConns, prepared statements, Hình 25, migration ordering, cache-aside, transaction boundaries)
    - Trang 182–196: Toàn bộ Chương 14 (15 trang: reflection, reflect.Type/ValueOf, rtype/abi.Type, CanSet, Bảng 11 Type vs Kind, struct tags, ApplyEnv, unsafe.Pointer, uintptr GC hazard, unsafe.StringData/SliceData, Cgo boundaries, runtime pinning, cgo memory leaks, Bảng so sánh đánh đổi)
    - Trang 197–207: Toàn bộ Chương 15 (11 trang: os/exec CLI automation, exec.Cmd, môi trường và cwd, Hình 26 sequence diagram, Bảng 12 exit methods, CommandContext, timeout, orphan process trees, Setpgid, ProcessRunner buffer pipeline, test runner exit codes)
    - Trang 208–220: Toàn bộ Chương 16 (13 trang: observability, log/slog, JSONHandler/TextHandler, Hình 27 tree handler, Bảng 13 slog.Attr/Group, trace context propagation, OpenTelemetry Tracing, TracerProvider, batch processor, Metrics types, Hình 28 Prometheus architecture, Bảng 14 telemetry hazards, SLO dashboards)
    - Trang 221–235: Toàn bộ Chương 17 (15 trang: Linux namespaces và cgroups, Bảng 15 namespaces, Hình 29 controller reconciliation loop, multi-stage Dockerfile, distroless/scratch tradeoffs, Hình 30 NASA servers, non-root user, GOMEMLIMIT, NextAction controller reconciler, Bảng 16 Pod lifecycle, Hình 31 Kubernetes architecture, Kind cluster, rollout status / ImagePullBackOff, client-go observer, Generation vs ObservedGeneration, Bảng 17 control layers, Dừng để dự đoán)
    - Trang 236–247: Toàn bộ Chương 18 (12 trang: đóng gói OCI, ký số Cosign, tự động hóa chuyển giao, 7 lớp delivery, Hình 32 & 33, Bảng 18 & 19, promote-gate CLI, OIDC IAM constraints, Terraform)
    - Trang 248–263: Toàn bộ Chương 19 (16 trang: generic vs interface, Unique[T comparable], Measurable constraints, Hình 34, generic method Go 1.27, typed nil, probe layout, labs/part19)
    - Trang 264–276: Toàn bộ Chương 20 (13 trang: capstone dự án opsprobe, Bảng 20, worker pool backpressure, SQLite transaction atomic BeginTx, bounded drain 16 KiB, socket leak incident, distroless, curl commands)
    - Trang 277–286: Toàn bộ Chương 21 (10 trang: reconcile loop, level vs edge trigger, Hình 35, 4 pha điều hòa, WorkQueue dirty/processing, exponential backoff, SelfHealingReconciler, graceful shutdown, labs/part21)
    - Trang 287–304: Toàn bộ Chương 22 (18 trang: Từ watch đến một controller Kubernetes thật, Informer cache, Reflector, DeltaFIFO, SharedInformer, giao thức List/Watch và resourceVersion, xử lý Tombstone và DeletedFinalStateUnknown, cấu trúc WorkQueue với 3 tập hợp queue/dirty/processing, Reconciler interface và Run loop, WaitForNamedCacheSyncWithContext, processNextItem, AddRateLimited, xử lý xung đột 409 qua retry.RetryOnConflict, 6 bài kiểm thử controller đạt PASS, bài tập CleanUpReconciler).
    - Trang 305–321: Toàn bộ Chương 23 (17 trang: Từ Controller đến Operator, định nghĩa Operator, kiến trúc controller-runtime, Manager/Scheme/Controller, 4 trụ cột controller-runtime, CRD Spec vs Status subresource, OwnerReference cascading deletion, vòng đời Finalizer và deadlock pitfall, Reconcile loop đa nhánh return error/RequeueAfter/Requeue, ExternalCleaner, đồng bộ drift cấu hình, meta.SetStatusCondition, 5 bài kiểm thử Operator đạt PASS).
    - Trang 322–338: Toàn bộ Chương 24 (17 trang: Tự động hóa AWS bằng Go, Default credential chain, STS temporary credentials qua AssumeRoleWithWebIdentity, IRSA, ECS Task Role, EKS Pod Identity, CredentialsCache, đường ống thực thi Smithy middleware với 5 giai đoạn Initialize/Serialize/Build/Finalize/Deserialize, SigV4 signing, NewListObjectsV2Paginator xử lý phân trang S3 1000 items, phân loại lỗi smithy.APIError và NoSuchKey/NoSuchBucket, AuditHeaderMiddleware, S3 Waiters; trong đó trang 322 đã có bản ghi PASS từ trước).
    - Trang 339–345: Phần mở đầu và cơ chế then chốt Chương 25 (7 trang: Git và GitHub Automation, so sánh hai mô hình dữ liệu Local Git repo vs Hosted GitHub service, xác thực Webhook HMAC an toàn với hmac.Equal chống tấn công kênh kề timing attack, cơ chế Delivery ID & Idempotency ledger, khử trùng lặp redelivery, WebhookReceiver Process trong bộ nhớ).
    - 7 trang chốt trọng yếu rải đều các chương sau: Trang 397 (Ch27 End Transition), Trang 399 (Ch28 Opener), Trang 419 (Ch29 Opener), Trang 424 (Ch29 Policy figure / text break), Trang 429 (Back Matter 50 Libraries Opener), Trang 484 (Phụ lục A Error Atlas Opener), Trang 493 (Trang kết thúc sách / J06–J11). (Trang 224 đã nằm trong Chương 17, Trang 322 đã nằm trong Chương 24).
  - Trạng thái kiểm tra trực quan: 352/352 trang đạt chuẩn layout, không tràn viền, không mất nét, không orphan heading, typography sắc nét, sơ đồ kiến trúc và bảng biểu căn giữa chuẩn xác.
- **Số trang chỉ được kiểm bằng thuật toán hình học (Automated-only Geometry Reviews)**: **141 trang** (`visual_status = PENDING`).
- **Số trang chưa có evidence (Not Verifiable)**: 0 trang (toàn bộ 493 trang đều có bản ghi kiểm định hình học).
- **Ledger bằng chứng thị giác chi tiết**:
  - Đường dẫn: [book/publication/page_visual_evidence.csv](publication/page_visual_evidence.csv)
  - Bao gồm từng hàng với: `page`, `pdf_sha256`, `render_sha256`, `review_method`, `reviewer_type`, `visual_status`, `reviewed_at`, `observation`.
- **Thư mục ảnh render để tái kiểm tra**:
  - Lệnh render: `page.get_pixmap(dpi=150)` qua PyMuPDF.
  - Vị trí tệp: `.workspace/final-publication-gate/renders/page_XXX.png`.
  - Manifest mã băm 493 ảnh: `.workspace/final-publication-gate/render_manifest.json`.

## 3. Bằng chứng đối soát Atlas 50 Thư viện & 85 Mục Lỗi

### 3.1. Atlas 50 Thư viện DevOps & Cloud (`LIBRARY_ATLAS_SEMANTIC_AUDIT`)
- **Tập tin bản thảo**: `book/appendices/devops-library-atlas.md` (50 mục Rank 01–50).
- **Bảng đối soát chi tiết**: [book/publication/library_atlas_evidence_ledger.md](publication/library_atlas_evidence_ledger.md)
  - **`SEMANTIC_CLAIM_VERIFIED`**: **24/50 thư viện** (48%)
    - Đã clone/checkout và đối soát toàn diện mã nguồn nội bộ tại repo local ở commit đã ghim trong `library_sources/repos/`, đối chiếu trực tiếp tập tin source, symbol triển khai và cơ chế hỗ trợ claim:
      1. `k8s-client-go` (`28076445520055420e3be4255b4cd27fd19df1f9`)
      2. `controller-runtime` (`67b72c2517be1d2b0dec612477eb20c3c959a8aa`)
      3. `aws-sdk-go-v2` (`b189f382f4924bc6c948c9942e17c547553faf0d`)
      4. `prometheus-client-golang` (`d6087ee482e06716ee21dc03819432d5d40f72db`)
      5. `opentelemetry-go` (`58db4c898f5b5594f8ba78f156475bf48486e2f2`)
      6. `opentelemetry-collector` (`0bf928af5487d3c4e0b4174eabb7ba075c322517`)
      7. `moby` (`89c5e8fd66634b6128fc4c0e6f1236e2540e46e0`)
      8. `containerd` (`a7fe631d96c08fb14cf8eff0afdc280e99c30a94`)
      9. `terraform-plugin-framework` (`c7ac25e86333d194946fb5e3fd1114e7d101fc23`)
      10. `helm` (`144ca65f8501953fa8b41cd1d37c7223051c85b7`)
      11. `go-git` (`3eeb238da61eb9c7a324f3ee04f990ce89175642`)
      12. `golang-crypto` (`3f62bf119e84c6e35e8518a2958089ade622d1a3`)
      13. `opa` (`b2c26708e9d55645d7f837db495031f7e4152594`)
      14. `cosign` (`3e82f50a2839855693aacf7b3d0e7e2f30774cb4`)
      15. `grpc-go` (`e84aa5ab15d1d2b29d54f838312ad490cb7551a8`)
      16. `protobuf-go` (`cdd4c5f7406e82462949c7a65defa9f3029c162d`)
      17. `go-containerregistry` (`8a72a424fdecb4caa14f2d525e5d2503331442b5`)
      18. `oras-go` (`105715ee12eac6895ec736a075285c34d9f2eeb6`)
      19. `cni` (`3f51e8803ebbdba0ebeed735b42137e4c7302403`)
      20. `cilium-ebpf` (`e55144e17360b60cc4583229c35c2dbf0935b308`)
      21. `netlink` (`17daef607c6442d47b0565343cf8a69f985a4cb7`)
      22. `crossplane-runtime` (`84fc49a3e3b88733677824b1a4dcce5097ca0c59`)
      23. `go-github` (`5149b4d74590b63154fcc43c4dac05e881f9aea3`)
      24. `mcp-go-sdk` (`3f3b699b2b67e1ed033a63d6651671dab53c2d32`)
  - **`SOURCE_FILE_VERIFIED`**: **26/50 thư viện** (52%)
    - Đã xác thực tập tin mã nguồn và symbol tồn tại tại commit đã ghim từ kho lưu trữ chính thức; khôi phục toàn vẹn nội dung claim kỹ thuật từ Atlas không rút gọn.
  - **`SOURCE_IDENTITY_VERIFIED`**: **0/50 thư viện** (0%)

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

- Vì 352/493 trang đã được trực tiếp quan sát bằng hình ảnh raster và 141/493 trang đang ở trạng thái kiểm định hình học (`VISUAL_PENDING`), theo tiêu chuẩn khắt khe dựa trên bằng chứng:
- **Trạng thái chính thức**:
  ```
  PUBLICATION_STATUS=BLOCKED_PENDING_EVIDENCE
  ```
  *(Lưu ý: Đây là trạng thái ghi nhận sự thiếu hụt bằng chứng nghiệm thu trực quan 141/493 trang còn lại; bản thân tệp PDF hiện tại hoàn toàn hợp lệ về mặt kỹ thuật, hình học và nội dung).*
