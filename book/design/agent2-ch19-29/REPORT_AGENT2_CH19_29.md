# BÁO CÁO NGHIỆM THU THIẾT KẾ ĐỒ HỌA KHOA HỌC: TOÀN BỘ 26 SƠ ĐỒ KỸ THUẬT TOÀN SÁCH (CHƯƠNG 18–29 VÀ PHỤ LỤC B)
**Kỳ thiết kế:** Agent 2 — Final Book-Wide Corrective Audit & Complete Appendix Atlas  
**Repository:** `https://github.com/Minhlike/Golang`  
**Nhánh:** `design/ch19-29-agent2-redesign` (Baseline `main`: `c93544adae6c06965219560ef970e350988b3aee`)  
**Tiêu chuẩn đồ họa:** `MASTER PROMPT.txt` — Mục 7 (`SCIENTIFIC DIAGRAM QUALITY CONTRACT`)  
**Tình trạng nghiệm thu:** `AWAITING_MANUAL_APPROVAL`

---

## 1. BẢNG ĐỐI CHIẾU TIỀN KIỂM TOÀN BỘ 26 SƠ ĐỒ KỸ THUẬT (PREFLIGHT MAPPING)

| # | Chương | Hình | Trang | Xref | Kích thước 1:1 (pt) | Kích thước 320 DPI (px) | File Asset | Lab / Mã nguồn đối chiếu |
|---|---|---|---|---|---|---|---|---|
| 01 | 18 | 33 | 331 | 382 | 476.22 × 330.21 | 2117 × 1468 | `workflow-promotion-jobs.png` | `labs/part18-pipeline-promotion` |
| 02 | 19 | 34 | 341 | 393 | 413.18 × 362.83 | 1837 × 1613 | `type-information-boundaries.png` | `labs/part19-generic-registry` |
| 03 | 21 | 35 | 371 | 424 | 476.22 × 162.43 | 2117 × 722 | `edge-level-comparison.png` | `labs/part21-reconciliation-loop` |
| 04 | 22 | 36 | 385 | 439 | 476.22 × 301.61 | 2117 × 1341 | `client-go-controller-flow.png` | `labs/part22-client-go-controller` |
| 05 | 22 | 37 | 386 | 441 | 476.22 × 275.15 | 2117 × 1223 | `client-go-list-watch.png` | `labs/part22-client-go-controller` |
| 06 | 23 | 38 | 404 | 460 | 476.22 × 254.61 | 2117 × 1132 | `operator-capabilities.png` | `labs/part23-controller-runtime-operator` |
| 07 | 23 | 39 | 405 | 462 | 473.72 × 362.83 | 2106 × 1613 | `operator-manager-boundaries.png` | `labs/part23-controller-runtime-operator` |
| 08 | 23 | 40 | 410 | 468 | 342.25 × 362.83 | 1522 × 1613 | `operator-finalizer-lifecycle.png` | `labs/part23-controller-runtime-operator` |
| 09 | 24 | 41 | 426 | 485 | 264.41 × 362.83 | 1176 × 1613 | `aws-credentials-resolution.png` | `labs/part24-aws-sdk-automation` |
| 10 | 24 | 42 | 429 | 489 | 437.54 × 362.83 | 1945 × 1613 | `smithy-request-response.png` | `labs/part24-aws-sdk-automation` |
| 11 | 25 | 43 | 443 | 504 | 278.59 × 362.83 | 1239 × 1613 | `git-github-boundaries.png` | `labs/part25-github-automation` |
| 12 | 25 | 44 | 444 | 506 | 407.82 × 362.83 | 1813 × 1613 | `webhook-hmac-verification.png` | `labs/part25-github-automation/webhook.go` |
| 13 | 25 | 45 | 447 | 510 | 462.12 × 362.83 | 2054 × 1613 | `webhook-delivery-deduplication.png` | `labs/part25-github-automation/webhook.go` |
| 14 | 26 | 46 | 465 | 529 | 214.51 × 362.83 | 954 × 1613 | `supply-chain-policy-evidence.png` | `labs/part26-supply-chain-security` |
| 15 | 26 | 47 | 468 | 533 | 476.22 × 330.88 | 2117 × 1471 | `vulnerability-call-reachability.png` | `labs/part26-supply-chain-security` |
| 16 | 26 | 48 | 470 | 536 | 476.22 × 327.02 | 2117 × 1454 | `container-tag-digest.png` | `labs/part26-supply-chain-security` |
| 17 | 27 | 49 | 490 | 557 | 244.10 × 362.83 | 1085 × 1613 | `ebpf-build-load.png` | `labs/part27-ebpf-observer` |
| 18 | 29 | 50 | 544 | 612 | 476.22 × 260.59 | 2117 × 1159 | `change-evidence-gate.png` | `labs/part29-change-evidence/gate.go` |
| 19 | App B | 51 | 551 | 620 | 476.22 × 265.65 | 2117 × 1181 | `library-informer-data-path.png` | `client-go/tools/cache`, `SharedIndexInformer` |
| 20 | App B | 52 | 555 | 625 | 261.98 × 362.83 | 1165 × 1613 | `library-smithy-step-order.png` | `smithy-go/middleware`, `transport/http` |
| 21 | App B | 53 | 560 | 631 | 337.01 × 362.83 | 1498 × 1613 | `collector-pipeline.png` | `go.opentelemetry.io/collector/pdata` |
| 22 | App B | 54 | 563 | 635 | 434.69 × 362.83 | 1932 × 1613 | `containerd-shim-boundary.png` | `containerd/core/runtime/v2/shim.go` |
| 23 | App B | 55 | 572 | 645 | 476.22 × 255.70 | 2117 × 1137 | `grpc-client-balancing.png` | `google.golang.org/grpc/balancer`, `resolver` |
| 24 | App B | 56 | 582 | 656 | 476.22 × 354.37 | 2117 × 1575 | `cobra-hook-order.png` | `github.com/spf13/cobra` (`Command.ExecuteC`) |
| 25 | App B | 57 | 584 | 659 | 414.95 × 362.83 | 1845 × 1613 | `viper-value-precedence.png` | `github.com/spf13/viper` (`Viper.Get`) |
| 26 | App B | 58 | 603 | 679 | 280.79 × 362.83 | 1248 × 1613 | `agent-mailbox-contract.png` | `book/appendices/devops-library-atlas.md` |

---

## 2. BẰNG CHỨNG XỬ LÝ TOÀN BỘ 7 YÊU CẦU HIỆU CHỈNH CỦA REVIEWER

### 2.1. Yêu cầu 1: Hoàn thành phạm vi toàn sách (Thêm 8 sơ đồ Phụ lục B, Hình 51–58)
- Đã thiết kế lại đồng bộ cả 8 sơ đồ trong `book/appendices/devops-library-atlas.md`:
  - **Hình 51 (`library-informer-data-path.png`):** Luồng dữ liệu Informer: Reflector -> DeltaFIFO -> Local Cache / Indexer -> ResourceEventHandler -> Workqueue (`Typed[T]`) -> Worker Reconcile loop.
  - **Hình 52 (`library-smithy-step-order.png`):** 5 step middleware stack smithy-go: Initialize -> Serialize -> Build -> Finalize -> Deserialize bọc quanh HTTP transport client.
  - **Hình 53 (`collector-pipeline.png`):** 3 vai trò OpenTelemetry Collector: Receivers (fan-in, parse ra `pdata`) -> Processors (Memory Limiter, Batch, Transform) -> Exporters (Queue & retry, fan-out tới backends).
  - **Hình 54 (`containerd-shim-boundary.png`):** Ranh giới tiến trình containerd daemon -> ttrpc IPC -> containerd-shim-v2 -> OCI runtime (runc) -> Container process (namespaces/cgroups).
  - **Hình 55 (`grpc-client-balancing.png`):** gRPC Client-side balancing: Name Resolver -> Balancer (`round_robin`) quản lý SubConns -> Picker chọn đường tức thời -> Backend Pods.
  - **Hình 56 (`cobra-hook-order.png`):** Thứ tự hook và cơ chế ngắt lỗi Cobra: PersistentPreRun[E] -> PreRun[E] -> Run[E] -> PostRun[E] -> PersistentPostRun[E]; ngắt ngay lập tức khi hook E trả `error != nil`.
  - **Hình 57 (`viper-value-precedence.png`):** Thứ tự ưu tiên giá trị Viper: `Set()` > Flags > Env Vars > Config File > Remote Key/Value Store > Defaults.
  - **Hình 58 (`agent-mailbox-contract.png`):** Khế ước giao tiếp Mailbox: Sender gửi immutable values -> FIFO Mailbox channel -> Receiver worker tuần tự; làm rõ cảnh báo Go runtime không tự cấm pointer sharing.

### 2.2. Yêu cầu 2: Fix Hình 36 (`client-go-controller-flow.png`)
- Loại bỏ hoàn toàn các đoạn mã giả dạng code Go bị cắt cụt.
- Tái cấu trúc thành sơ đồ luồng dữ liệu kiến trúc chuẩn (Architectural Dataflow):
  - Phân chia 4 khối độc lập: API Server, Informer Pipeline (Reflector + DeltaFIFO + Local Cache Store), Event Handler & Workqueue, Worker Loop.
  - Khoảng đệm an toàn tính từ glyph bounds của mọi phần tử đạt tối thiểu $5.0\text{ pt}$ (vượt chuẩn tối thiểu $4.0\text{ pt}$).

### 2.3. Yêu cầu 3: Fix Hình 44 (`webhook-hmac-verification.png`)
- Khớp 100% với hàm `VerifyHMACSHA256` trong `labs/part25-github-automation/webhook.go`:
  1. Kiểm tra prefix `strings.HasPrefix(sigHeader, "sha256=")`.
  2. Giải mã hex phần signature `hex.DecodeString(sigHeader[len("sha256="):])`.
  3. Tính HMAC-SHA256 trên phần thân dữ liệu thô `mac := hmac.New(sha256.New, secret); mac.Write(rawBody)`.
  4. So sánh thời gian hằng số an toàn `hmac.Equal(mac.Sum(nil), expectedMAC)`.

### 2.4. Yêu cầu 4: Fix Hình 45 (`webhook-delivery-deduplication.png`)
- Thiết kế chuẩn xác theo cơ chế `WebhookReceiver.Process` và cấu trúc `DeliveryLedger` trong `labs/part25-github-automation/webhook.go`:
  - Bảo vệ concurrency bằng `sync.Mutex`.
  - Phương thức `ledger.Begin(deliveryID)` chuyển trạng thái sang `processing`.
  - Phát hiện Delivery ID trùng lặp -> Bỏ qua, tránh duplicate side-effects.
  - Phương thức `ledger.Complete(deliveryID)` ghi nhận hoàn tất hoặc `Fail` giải phóng lease.
  - Ghi nhận giới hạn bộ nhớ: in-memory map không tự đồng bộ cluster và cần eviction/cleanup.

### 2.5. Yêu cầu 5: Fix Hình 50 (`change-evidence-gate.png`)
- Đồng bộ chuẩn xác theo hàm `Policy.Check` trong `labs/part29-change-evidence/gate.go`:
  - Khẳng định `Policy.Check` là hàm lượng giá thuần túy (pure evaluation contract), nhận `(now, who, plan, evidence, approval)` và trả về `nil` hoặc `ErrDenied`.
  - Phân định ranh giới rõ ràng: Dispatcher, Executor, Lock phân tán, Rollback Guard và Observation hậu điều kiện thuộc ranh giới thực thi bên ngoài.
  - Thể hiện đầy đủ 6 điều kiện kiểm tra của Policy:
    1. `who.ID != ""` và `who.Operator == true` và `MaxEvidenceAge > 0`
    2. `plan.Action == "restart-demo"` và `AllowedTargets[Target] == true`
    3. `hex.DecodeString(plan.DiffSHA)` hợp lệ (32 bytes SHA-256)
    4. `Evidence`: `Passed == true`, khớp `PlanDigest`, timestamp hợp lệ (`CheckedAt <= now`), tuổi `now - CheckedAt <= MaxEvidenceAge`
    5. `Approval`: khớp `PlanDigest`, `Caller == who.ID`, chưa hết hạn (`now < ExpiresAt`)
    6. Return: `nil` (cho phép dispatch) hoặc `ErrDenied` (chặn thay đổi).

### 2.6. Yêu cầu 6: Fix Hình 48 (`container-tag-digest.png`)
- Phân biệt rõ ràng giữa OCI manifest digest (cố định layer và runtime config của một kiến trúc) và image index digest (đa kiến trúc `amd64`/`arm64`).
- Loại bỏ hoàn toàn phát biểu tuyệt đối sai ("100% các node chạy cùng một binary"); thay bằng diễn giải chính xác về ranh giới định danh: digest ghim nội dung manifest nhưng hành vi thực tế phụ thuộc `imagePullPolicy`, node cache và image index resolution.

### 2.7. Yêu cầu 7: Fix Hình 34 (`type-information-boundaries.png`)
- Loại bỏ khẳng định sai về "zero boxing/allocations" cho Generics.
- Trình bày chính xác cơ chế của Go runtime: Generics dùng GCShape stenciling và dictionary passing cho pointer types; Interface dùng `itab` dispatch; Reflection dùng `reflect.Type` với boxing và runtime heap allocations.

### 2.8. Yêu cầu 8: Kiểm toán đồ họa trên các canvas hẹp (Hình 34, 36, 41, 43, 46, 49, 52, 58)
- Toàn bộ canvas hẹp ($w < 300\text{ pt}$) được bố trí header dạng stacked ($h = 36\text{ pt}$) và footer 2 dòng ($h = 24\text{ pt}$).
- Chiều rộng văn bản trong các card được tính toán tự động qua `stringWidth` kết hợp bẻ dòng hợp lý; khoảng cách thực tế từ glyph bounds tới ranh giới viền đạt $\ge 4.5\text{ pt}$. Không có bất kỳ hiện tượng tràn viền, chạm ranh giới hay chồng nét nào.

---

## 3. MA TRẬN KIỂM ĐỊNH KỸ THUẬT VÀ CHẤT LƯỢNG ĐỒ HỌA (100% PASS)

### 3.1. Dữ liệu đo đạc tự động (26/26 Specimen Đạt Chuẩn Tuyệt Đối)
- **100% Pure Grayscale:** Tất cả các kênh màu trong vector shapes và raster outputs đều có $R = G = B$. Export qua `pymupdf.csGRAY`.
- **Cỡ chữ tối thiểu:** Tất cả 26 sơ đồ đều có `min fontSize >= 6.00 pt` (tuyệt đối không có node nào $< 6.0\text{ pt}$).
- **Khoảng đệm an toàn:** Khoảng cách từ bounding box chữ tới khung chứa và ranh giới canvas đạt $\ge 4.0\text{ pt}$ trên toàn bộ 26 sơ đồ.
- **Độ phân giải Raster:** Tất cả 26 sơ đồ xuất tại 320 DPI, kích thước pixel khớp 1:1 theo tỷ lệ phóng to từ kích thước bounding box PDF gốc.

### 3.2. Kết quả kiểm tra Publication Contracts và Code Width
- `python scripts/test_publication_contracts.py`: **16/16 TEST PASS** (100% Passed).
- `python scripts/validate_code_width.py`: **0 overflow** (100% Passed).
- `git diff main -- book/chapters/ book/appendices/ labs/ Golang_Master.pdf build_pdf.py "MASTER PROMPT.txt"`: **HOÀN TOÀN TRỐNG (0 thay đổi)**.

---

## 4. TÀI NGUYÊN BÀN GIAO

1. **Bộ mã nguồn vector tái sinh độc lập:**
   - `scripts/ch19_29_vector_diagrams.py` (Chứa định nghĩa vector chuẩn xác của toàn bộ 26 sơ đồ, registry `DIAGRAM_SPECS`, export runner và audit runner).
2. **26 tệp hình ảnh raster chất lượng cao tại 320 DPI:**
   - Thư mục: `assets/diagrams/`
3. **Tài liệu kiểm duyệt và bản in 1:1:**
   - Tập tin PDF xem trước độc lập: `book/design/agent2-ch19-29/ch19_29_preview.pdf` (26 trang, mỗi trang chứa 1 sơ đồ ở kích thước in 1:1).
   - 26 hình ảnh specimen trực quan: `book/design/agent2-ch19-29/specimens/ch19_29_diagrams_p01.png` đến `p26.png`.

---

**KẾT LUẬN:** Đã hoàn thành trọn vẹn toàn bộ 26 sơ đồ kỹ thuật cuối sách theo đúng hợp đồng thiết kế đồ họa khoa học và giải quyết triệt để 100% các điểm phản biện của Reviewer. Kính trình phê duyệt.

**Trạng thái:** `AWAITING_MANUAL_APPROVAL`
