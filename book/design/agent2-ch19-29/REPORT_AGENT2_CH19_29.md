# BÁO CÁO NGHIỆM THU THIẾT KẾ ĐỒ HỌA KHOA HỌC: TOÀN BỘ SƠ ĐỒ KỸ THUẬT CUỐI SÁCH (CHƯƠNG 19-29 VÀ HÌNH 33)
**Kỳ thiết kế:** Agent 2 — Final Book-Wide Technical Diagram Redesign  
**Repository:** `https://github.com/Minhlike/Golang`  
**Nhánh:** `design/ch19-29-agent2-redesign` (Baseline `main`: `c93544adae6c06965219560ef970e350988b3aee`)  
**Tiêu chuẩn đồ họa:** `MASTER PROMPT.txt` — Mục 7 (`SCIENTIFIC DIAGRAM QUALITY CONTRACT`)  
**Tình trạng nghiệm thu:** `AWAITING_MANUAL_APPROVAL`

---

## 1. BẢNG ĐỐI CHIẾU TIỀN KIỂM TOÀN BỘ SƠ ĐỒ KỸ THUẬT (PREFLIGHT MAPPING)

Kết quả kiểm toán đối chiếu giữa mã nguồn Markdown, `Golang_Master.pdf` (614 trang), assets và PlantUML xác nhận:
- **18 sơ đồ kỹ thuật trong phần nội dung chính** cần thiết kế lại đồng bộ. Bảng liệt kê ban đầu của User gồm 17 sơ đồ từ Ch 19–29; qua kiểm toán tự động phát hiện thêm **Hình 33** (`workflow-promotion-jobs.png`, Ch 18, trang 331, xref 382, $476.22 \times 330.21\text{ pt}$) bị sót lại khi Batch 03 dừng ở Hình 32. Do đó, Hình 33 đã được đưa vào phạm vi thiết kế trọn vẹn trong đợt này.
- **8 sơ đồ DevOps Library Atlas trong Back Matter** (`book/appendices/devops-library-atlas.md`, Hình 51–58) thuộc phần phụ lục tra cứu thư viện, được ghi nhận đầy đủ siêu dữ liệu kiểm toán ở mục 1.2.

### 1.1. Bảng 18 sơ đồ kỹ thuật đã thiết kế lại (Chương 18 đến 29)

| Số TT | Chương | Tên file asset | Trang PDF | Xref | Kích thước in 1:1 (pt) | Độ phân giải raster | Mã nguồn / Lab đối chiếu | Trạng thái |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---|:---:|
| **H33** | Ch 18 | `workflow-promotion-jobs.png` | 331 | 382 | $476.22 \times 330.21$ | 320 DPI (2117x1468 px) | `book/chapters/18-ci-cd-tu-dong-hoa-kiem-dinh.md` | **HOÀN TẤT** |
| **H34** | Ch 19 | `type-information-boundaries.png` | 341 | 393 | $413.18 \times 362.83$ | 320 DPI (1837x1613 px) | `book/chapters/19-reflection-unsafe-generics-kinh-dien.md` | **HOÀN TẤT** |
| **H35** | Ch 21 | `edge-level-comparison.png` | 371 | 424 | $476.22 \times 162.43$ | 320 DPI (2117x722 px) | `book/chapters/21-tu-duy-level-triggered-trong-he-phan-tan.md` | **HOÀN TẤT** |
| **H36** | Ch 22 | `client-go-controller-flow.png` | 385 | 439 | $476.22 \times 301.61$ | 320 DPI (2117x1341 px) | `labs/part22-client-go-controller` | **HOÀN TẤT** |
| **H37** | Ch 22 | `client-go-list-watch.png` | 386 | 441 | $476.22 \times 275.15$ | 320 DPI (2117x1223 px) | `book/chapters/22-lap-trinh-kubernetes-voi-client-go.md` | **HOÀN TẤT** |
| **H38** | Ch 23 | `operator-capabilities.png` | 404 | 460 | $476.22 \times 254.61$ | 320 DPI (2117x1132 px) | `book/chapters/23-tu-controller-den-operator.md` | **HOÀN TẤT** |
| **H39** | Ch 23 | `operator-manager-boundaries.png` | 405 | 462 | $473.72 \times 362.83$ | 320 DPI (2106x1613 px) | `labs/part23-operator-runtime` | **HOÀN TẤT** |
| **H40** | Ch 23 | `operator-finalizer-lifecycle.png` | 410 | 468 | $342.25 \times 362.83$ | 320 DPI (1522x1613 px) | `book/chapters/23-tu-controller-den-operator.md` | **HOÀN TẤT** |
| **H41** | Ch 24 | `aws-credentials-resolution.png` | 426 | 485 | $264.41 \times 362.83$ | 320 DPI (1176x1613 px) | `book/chapters/24-tu-dong-hoa-aws-bang-go.md` | **HOÀN TẤT** |
| **H42** | Ch 24 | `smithy-request-response.png` | 429 | 489 | $437.54 \times 362.83$ | 320 DPI (1945x1613 px) | `book/chapters/24-tu-dong-hoa-aws-bang-go.md` | **HOÀN TẤT** |
| **H43** | Ch 25 | `git-github-boundaries.png` | 443 | 504 | $278.59 \times 362.83$ | 320 DPI (1239x1613 px) | `book/chapters/25-git-github-automation-event-driven.md` | **HOÀN TẤT** |
| **H44** | Ch 25 | `webhook-hmac-verification.png` | 444 | 506 | $407.82 \times 362.83$ | 320 DPI (1813x1613 px) | `labs/part25-github-webhook-receiver` | **HOÀN TẤT** |
| **H45** | Ch 25 | `webhook-delivery-deduplication.png` | 447 | 510 | $462.12 \times 362.83$ | 320 DPI (2054x1613 px) | `labs/part25-github-webhook-receiver` | **HOÀN TẤT** |
| **H46** | Ch 26 | `supply-chain-policy-evidence.png` | 465 | 529 | $214.51 \times 362.83$ | 320 DPI (954x1613 px) | `labs/part26-supply-chain-gate` | **HOÀN TẤT** |
| **H47** | Ch 26 | `vulnerability-call-reachability.png` | 468 | 533 | $476.22 \times 330.88$ | 320 DPI (2117x1471 px) | `book/chapters/26-chuoi-cung-ung-co-the-kiem-chung.md` | **HOÀN TẤT** |
| **H48** | Ch 26 | `container-tag-digest.png` | 470 | 536 | $476.22 \times 327.02$ | 320 DPI (2117x1454 px) | `book/chapters/26-chuoi-cung-ung-co-the-kiem-chung.md` | **HOÀN TẤT** |
| **H49** | Ch 27 | `ebpf-build-load.png` | 490 | 557 | $244.10 \times 362.83$ | 320 DPI (1085x1613 px) | `labs/part27-ebpf-exec-observer` | **HOÀN TẤT** |
| **H50** | Ch 29 | `change-evidence-gate.png` | 544 | 612 | $476.22 \times 260.59$ | 320 DPI (2117x1159 px) | `labs/part29-change-evidence` | **HOÀN TẤT** |

### 1.2. Kiểm toán sơ đồ Back Matter (Phụ lục B — DevOps Library Atlas)

| Số TT | Vị trí | Tên file asset | Trang PDF | Xref | Kích thước in (pt) | Khế ước nội dung tra cứu |
|:---:|:---:|:---|:---:|:---:|:---:|:---|
| **H51** | App B | `library-informer-data-path.png` | 551 | 620 | $476.22 \times 265.65$ | Informer cập nhật cache rồi phát event tới handler; so sánh với client-go core |
| **H52** | App B | `library-smithy-step-order.png` | 555 | 625 | $261.98 \times 362.83$ | Năm step tổ chức đường gọi vào bên trong; Deserialize giải mã kết quả |
| **H53** | App B | `collector-pipeline.png` | 560 | 631 | $337.01 \times 362.83$ | OpenTelemetry collector: receiver -> processors -> exporter |
| **H54** | App B | `containerd-shim-boundary.png` | 563 | 635 | $434.69 \times 362.83$ | containerd daemon -> containerd-shim v2 -> runc OCI container lifecycle |
| **H55** | App B | `grpc-client-balancing.png` | 572 | 645 | $476.22 \times 255.70$ | gRPC resolver cung cấp endpoint; balancer quản lý SubConn connection pool |
| **H56** | App B | `cobra-hook-order.png` | 582 | 656 | $476.22 \times 354.37$ | Thứ tự chạy hooks của Cobra: PreRun -> Run -> PostRun |
| **H57** | App B | `viper-value-precedence.png` | 584 | 659 | $414.95 \times 362.83$ | Thứ tự ưu tiên nạp config Viper: Explicit -> Flag -> Env -> Config -> Key/Value -> Default |
| **H58** | App B | `agent-mailbox-contract.png` | 603 | 679 | $280.79 \times 362.83$ | Mental model actor mailbox trong giao tiếp agent phân tán |

---

## 2. MÔ HÌNH KỸ THUẬT VÀ KHẾ ƯỚC NỘI DUNG (TECHNICAL SEMANTICS CONTRACT)

Toàn bộ 18 sơ đồ được dựng bằng ReportLab vector graphics thuần túy (`scripts/ch19_29_vector_diagrams.py`), tuân thủ 100% ngữ nghĩa mã nguồn và bài giảng:

### Nhóm 1: Các cơ chế nền tảng và Kubernetes Core (Hình 33 – 37)
1. **Hình 33 (`workflow-promotion-jobs.png`):** Phân định ranh giới chặt chẽ giữa 3 job: Job 1 (Build & Test - Artifact Producer, runner quyền tối thiểu, tạo container digest và SLSA provenance), Job 2 (Policy Gate Thẩm định - không có quyền deploy, kiểm tra tính hợp lệ của bằng chứng), Job 3 (Deploy Environment - sử dụng OIDC token nhận dạng tạm thời, cập nhật trạng thái mong muốn bằng digest SHA-256). Khẳng định bất biến: Quyền OIDC không thay thế cho cổng chính sách.
2. **Hình 34 (`type-information-boundaries.png`):** Thiết lập 3 ranh giới bảo toàn và xử lý thông tin kiểu: Generic (Compile-time type preservation, zero runtime overhead, không boxing), Interface (Khế ước hành vi khi concrete type thay đổi lúc runtime), Reflection (Khảo sát shape và metadata khi concrete type chưa biết trước).
3. **Hình 35 (`edge-level-comparison.png`):** So sánh mô hình Edge-Triggered (chỉ phát hiện sự kiện đổi trạng thái; nếu mất gói tin thì controller treo vĩnh viễn) và Level-Triggered (liên tục điều hòa trạng thái thực tế `current` về trạng thái mong muốn `desired`; tự phục hồi ngay cả khi mất tín hiệu mạng).
4. **Hình 36 (`client-go-controller-flow.png`):** Kiến trúc chuẩn của client-go: Reflector (List/Watch) -> DeltaFIFO -> Indexer Cache Store cục bộ -> EventHandlers -> WorkQueue (RateLimiter) -> Worker Threads -> Business Handler. Mũi tên nét đứt phân định ranh giới nuôi cache và luồng sự kiện.
5. **Hình 37 (`client-go-list-watch.png`):** Biểu diễn trình tự Reflector khởi tạo ban đầu bằng `List` (nhận snapshot kèm opaque `resourceVersion: "1040"`), sau đó mở `Watch stream` (nhận delta 1041, 1042). Khi đứt kết nối và etcd compact lịch sử dẫn đến lỗi `HTTP 410 Gone (Too old resource version)`, Reflector bắt buộc `Re-List` lại từ đầu để lập snapshot mới (`RV: "2050"`).

### Nhóm 2: Operator Pattern và AWS Cloud SDK (Hình 38 – 42)
6. **Hình 38 (`operator-capabilities.png`):** Đóng gói tri thức con người (Human Domain Knowledge) vào Operator Core bằng Go, phân nhánh thành 3 vai trò kiến trúc thiết kế song hành: API/CRD (khai báo ý định), Controller Loop (điều hòa trạng thái) và Tích hợp ngoài (vòng đời tài nguyên ngoại vi). Phía bên phải là thang 5 cấp độ năng lực CNCF từ Basic Install (Level 1) đến Auto-Pilot (Level 5).
7. **Hình 39 (`operator-manager-boundaries.png`):** Ranh giới trách nhiệm kiến trúc: Manager quản lý lifecycle runner và Scheme (`GVK <-> struct`); Controller quản lý WorkQueue; Reconciler thực thi tuần tự 4 bước (`r.Get` từ Cache -> Xét finalizer -> So sánh Desired -> Ghi mutation qua HTTP). Phân định ranh giới Split Client: đọc từ In-Memory Cache, ghi qua HTTP REST tới API Server.
8. **Hình 40 (`operator-finalizer-lifecycle.png`):** Vòng đời finalizer: Khi nhận xóa (`deletionTimestamp != nil`), Reconciler gọi `r.cleanupExternalResources()`. Nếu thất bại (`err != nil`), **BẮT BUỘC GIỮ FINALIZER** để requeue thử lại, ngăn chặn etcd xóa vĩnh viễn tài nguyên. Chỉ khi cleanup thành công mới gỡ finalizer và để API server xử lý bước xóa vật lý tiếp theo.
9. **Hình 41 (`aws-credentials-resolution.png`):** Bản đồ nguồn chứng thực của AWS SDK Go v2: `config.LoadDefaultConfig` làm điểm vào; 4 nhóm provider (Environment, Shared Profiles, Web Identity / IRSA, Container / IMDSv2). `aws.CredentialsCache` đứng trung gian kiểm tra `CanExpire` & `Expires`, tự động gọi `Retrieve(ctx)` làm mới token mà không gián đoạn luồng nghiệp vụ.
10. **Hình 42 (`smithy-request-response.png`):** Pipeline 5 bước của Smithy Middleware Stack: Initialize (xác thực tham số), Serialize (dựng `smithyhttp.Request`), Build (tính toán Payload Checksum SHA-256 & Content-Length), Finalize (ký số AWS SigV4 `AWS4-HMAC-SHA256`), và Deserialize (nhận raw HTTP response từ Transport, giải mã JSON/XML thành Go struct hoặc ánh xạ thành `smithy.APIError`).

### Nhóm 3: Tự động hóa Git/GitHub và Bảo mật chuỗi cung ứng (Hình 43 – 48)
11. **Hình 43 (`git-github-boundaries.png`):** Phân định ranh giới bản thể: Git Core là kho cục bộ hướng nội dung (Merkle DAG, blob, tree, commit, tag, hoạt động 100% offline không cần mạng) đối lập với GitHub Platform là dịch vụ SaaS cộng tác trên nền mạng (Pull Requests, Issues, Releases, Webhooks, Actions, REST/GraphQL APIs, OAuth RBAC).
12. **Hình 44 (`webhook-hmac-verification.png`):** Quy trình xác minh chữ ký Webhook HMAC-SHA256: Máy chủ Go đọc raw body có giới hạn (`io.LimitReader`), tính toán `HMAC-SHA256(secret, rawBody)`. **CẢNH BÁO BẢO MẬT:** Tuyệt đối không unmarshal rồi marshal lại JSON vì sẽ làm thay đổi thứ tự key và khoảng trắng. So sánh bằng `subtle.ConstantTimeCompare` để triệt tiêu lỗ hổng tấn công kênh phụ (Timing Side-Channel Attack).
13. **Hình 45 (`webhook-delivery-deduplication.png`):** Cơ chế khử trùng lặp webhook: Sử dụng `X-GitHub-Delivery` làm khóa idempotent. Lần đầu: kiểm tra SQLite chưa có -> chạy side effect -> lưu ID -> trả 200 OK. Lần 2 (redelivery do timeout): kiểm tra đã tồn tại -> **BỎ QUA (DROP) SIDE EFFECT** -> trả ngay 200 OK để GitHub dừng retry.
14. **Hình 46 (`supply-chain-policy-evidence.png`):** Chuỗi 6 mắt xích bằng chứng từ mã nguồn đến Admission Gate: 01 Nguồn (Commit SHA) -> 02 Phụ thuộc (`go.sum`) -> 03 Build Provenance (SLSA attestation) -> 04 Artifact (Container Digest) -> 05 Xác minh chữ ký (Cosign + Rekor + Fulcio) -> 06 Cổng Policy (Fail-Closed: đủ bằng chứng = ALLOW, thiếu = DENY).
15. **Hình 47 (`vulnerability-call-reachability.png`):** Phân tích đồ thị gọi tĩnh bằng `govulncheck`: Phân biệt lỗ hổng có đường gọi tới (Reachable trong `golang.org/x/crypto/bcrypt` -> nguy cơ cao, bắt buộc vá) với lỗ hổng chỉ tồn tại trong dependency nhưng không có đường gọi tới từ ứng dụng (`golang.org/x/crypto/ssh` -> Unreachable symbol -> lọc nhiễu cảnh báo giả).
16. **Hình 48 (`container-tag-digest.png`):** Bản chất kỹ thuật của Tag và Digest: Tag là con trỏ có thể thay đổi (Mutable Pointer, nguy cơ trôi dạt phiên bản và tấn công tráo tag), trong khi Digest là mã băm SHA-256 tính từ Manifest nội dung (Immutable Content Hash), khóa chặt tính tất định trên 100% các node trong cụm Kubernetes.

### Nhóm 4: Quan sát Linux bằng eBPF và Cổng bằng chứng trong kỷ nguyên Agent (Hình 49 – 50)
17. **Hình 49 (`ebpf-build-load.png`):** Tách bạch hai giai đoạn: Build-time (mã nguồn C `exec_observer.bpf.c` + `vmlinux.h` biên dịch qua Clang/bpf2go thành bytecode BPF và Go bindings, đóng gói vào binary Go độc lập CGO-free) và Runtime (Go userspace gọi `cilium/ebpf` nạp qua syscall `bpf(2)`, Linux Kernel Verifier kiểm tra an toàn bộ nhớ và quyền, attach vào `tracepoint/sys_enter_execve`, truyền dữ liệu qua BPF Ring Buffer).
18. **Hình 50 (`change-evidence-gate.png`):** Mô hình quản trị thay đổi 5 bước: 01 Đề xuất (Proposal: gắn artifact, action, diff hash) -> 02 Kiểm chứng (Evidence: test độc lập xanh, freshness < 1 phút) -> 03 Phê duyệt (Approval: caller xác thực, đúng plan digest) -> 04 Thực thi (Scoped Exec: quyền tối thiểu, sandbox cô lập) -> 05 Quan sát (Observe: kiểm tra `/readyz`, đo lường metrics, tự động rollback). Nguyên tắc Fail-Closed: thiếu bất kỳ bằng chứng nào là lập tức từ chối.

---

## 3. MA TRẬN KIỂM TOÁN CHẤT LƯỢNG ĐỒ HỌA KHOA HỌC (SCIENTIFIC QA MATRIX)

### 3.1. Dữ liệu kiểm định đo đạc tự động (18/18 Specimen Đạt Chuẩn Tuyệt Đối)

| Số TT | Tên file asset | Kích thước PDF gốc (pt) | Kích thước Pixel (320 DPI) | Số lượng text node | Cỡ chữ nhỏ nhất (pt) | Bounding-box padding (pt) | Độ tinh khiết Grayscale |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **H33** | `workflow-promotion-jobs.png` | $476.22 \times 330.21$ | 2117 x 1468 | 58 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H34** | `type-information-boundaries.png` | $413.18 \times 362.83$ | 1837 x 1613 | 82 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H35** | `edge-level-comparison.png` | $476.22 \times 162.43$ | 2117 x 722 | 26 | **6.00 pt** | $\ge 5.0\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H36** | `client-go-controller-flow.png` | $476.22 \times 301.61$ | 2117 x 1341 | 60 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H37** | `client-go-list-watch.png` | $476.22 \times 275.15$ | 2117 x 1223 | 31 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H38** | `operator-capabilities.png` | $476.22 \times 254.61$ | 2117 x 1132 | 37 | **6.00 pt** | $\ge 5.0\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H39** | `operator-manager-boundaries.png` | $473.72 \times 362.83$ | 2106 x 1613 | 45 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H40** | `operator-finalizer-lifecycle.png` | $342.25 \times 362.83$ | 1522 x 1613 | 25 | **6.00 pt** | $\ge 5.0\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H41** | `aws-credentials-resolution.png` | $264.41 \times 362.83$ | 1176 x 1613 | 23 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H42** | `smithy-request-response.png` | $437.54 \times 362.83$ | 1945 x 1613 | 44 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H43** | `git-github-boundaries.png` | $278.59 \times 362.83$ | 1239 x 1613 | 34 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H44** | `webhook-hmac-verification.png` | $407.82 \times 362.83$ | 1813 x 1613 | 23 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H45** | `webhook-delivery-deduplication.png` | $462.12 \times 362.83$ | 2054 x 1613 | 25 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H46** | `supply-chain-policy-evidence.png` | $214.51 \times 362.83$ | 954 x 1613 | 22 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H47** | `vulnerability-call-reachability.png` | $476.22 \times 330.88$ | 2117 x 1471 | 37 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H48** | `container-tag-digest.png` | $476.22 \times 327.02$ | 2117 x 1454 | 30 | **6.00 pt** | $\ge 5.0\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H49** | `ebpf-build-load.png` | $244.10 \times 362.83$ | 1085 x 1613 | 27 | **6.00 pt** | $\ge 4.5\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |
| **H50** | `change-evidence-gate.png` | $476.22 \times 260.59$ | 2117 x 1159 | 43 | **6.00 pt** | $\ge 5.0\text{ pt}$ | **100% Grayscale (rg=0, rb=0)** |

### 3.2. Kết quả kiểm tra Publication Contracts và Code Width
1. **Unit Test Khế ước Xuất bản (`scripts/test_publication_contracts.py`):**
   - Chạy 16/16 test case kiểm tra cấu trúc Markdown, heading hierarchy, callout formatting, figure numbering.
   - **Kết quả:** `Ran 16 tests in 0.305s — OK (PASS 100%)`.
2. **Kiểm tra Chiều rộng Khối mã (`scripts/validate_code_width.py`):**
   - Kiểm tra chiều rộng khối mã có thể in (tối đa 448.22 pt / ~64 ký tự monospace).
   - **Kết quả:** `[CODE-WIDTH-PASS] All code blocks within printable width limits. Overflowing lines: 0`.

---

## 4. BẢO TOÀN NỘI DUNG VÀ RANH GIỚI BẢN QUYỀN (STRICT CONTENT LOCK)

Cam kết tuân thủ nguyên tắc khóa nội dung:
- **Tệp Markdown bài giảng (`book/chapters/*.md`):** Hoàn toàn nguyên vẹn, 0 byte thay đổi.
- **Tệp mã nguồn phòng thí nghiệm (`labs/`):** Hoàn toàn nguyên vẹn, không chỉnh sửa mã Go.
- **Tệp PDF cuốn sách gốc (`Golang_Master.pdf`):** Giữ nguyên tuyệt đối, không ghi đè.
- **Bộ tạo PDF chính (`build_pdf.py`) và quy tắc dự án (`MASTER PROMPT.txt`):** Không can thiệp.
- **Kết quả kiểm tra Git Diff đối chiếu với `main`:**
  ```bash
  git diff main -- book/chapters/ Golang_Master.pdf build_pdf.py "MASTER PROMPT.txt"
  # Kết quả: HOÀN TOÀN TRỐNG (0 dòng thay đổi)
  ```
- **Hành động Git:** Toàn bộ công việc nằm trên nhánh thiết kế `design/ch19-29-agent2-redesign`. Không thực hiện merge vào `main`, không push `main`.

---

## 5. TÀI NGUYÊN BÀN GIAO VÀ HƯỚNG DẪN REVIEW

1. **Bộ tạo mã đồ họa vector:** `scripts/ch19_29_vector_diagrams.py`
2. **Bộ tạo tài liệu duyệt:** `scripts/build_ch19_29_preview.py`
3. **Tài liệu PDF duyệt 1:1:** `book/design/agent2-ch19-29/ch19_29_preview.pdf` (18 trang)
4. **Bộ ảnh specimen duyệt:** `book/design/agent2-ch19-29/specimens/ch19_29_diagrams_p01.png` đến `p18.png`
5. **Assets được cập nhật trực tiếp:** 18 tệp `.png` tại `assets/diagrams/`

Dừng tại cổng kiểm soát: **`AWAITING_MANUAL_APPROVAL`**.
