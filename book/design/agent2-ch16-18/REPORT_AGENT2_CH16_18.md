# BÁO CÁO NGHIỆM THU KỸ THUẬT SƠ ĐỒ (BATCH 03 - AGENT 2 REDESIGN)
## CHƯƠNG 16, 17, 18 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả thiết kế:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch16-18-agent2-redesign` (baseline: `4b9b6cc` trên `main`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt` (Mục 7: `SCIENTIFIC DIAGRAM QUALITY CONTRACT`), đối chiếu mã nguồn và test của lab (`labs/part16-observability-evidence`, `labs/part16-real-signals`, `labs/part17-reconciliation-contract`, `labs/part17-container-kubernetes`, `labs/part18-promotion-evidence`, `labs/part18-workflow-delivery`), in ấn grayscale thuần túy.

---

## 1. Bảng Đối chiếu Preflight Bắt buộc (Mandatory Preflight Mapping)

Quét toàn bộ từ Chương 16 đến Chương 18 trong `Golang_Master.pdf` xác định **đúng 5 sơ đồ kỹ thuật kế tiếp** theo thứ tự xuất hiện trong sách:

| Chương | Số hình | Trang PDF | Xref PDF | Kích thước 1:1 (pt) | File Asset PNG | Nguồn Lab / Source đối chiếu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Chương 16** | **Hình 27** | Trang 283 | xref 328 | $476.22 \times 312.02$ | `assets/diagrams/observability-projections.png` | `labs/part16-observability-evidence` & `book/chapters/16-thay-duoc-he-thong.md` |
| **Chương 16** | **Hình 28** | Trang 292 | xref 338 | $476.22 \times 264.46$ | `assets/diagrams/probe-observation-path.png` | `labs/part16-real-signals` (`cmd/probe-api`) & `book/chapters/16-thay-duoc-he-thong.md` |
| **Chương 17** | **Hình 29** | Trang 300 | xref 347 | $335.89 \times 362.83$ | `assets/diagrams/reconciliation-loop.png` | `labs/part17-reconciliation-contract` (`fixed/reconcile.go`) & `book/chapters/17-dong-goi-va-dieu-phoi.md` |
| **Chương 17** | **Hình 31** | Trang 310 | xref 359 | $476.22 \times 238.11$ | `assets/diagrams/container-cluster-observation.png` | `labs/part17-container-kubernetes` (`client-observer/observation.go`, `Dockerfile`, `k8s/`) |
| **Chương 18** | **Hình 32** | Trang 321 | xref 371 | $476.22 \times 216.73$ | `assets/diagrams/delivery-evidence-chain.png` | `labs/part18-promotion-evidence` (`fixed/admission.go`), `labs/part18-workflow-delivery` |

> [!NOTE]
> **Phân định rõ Hình 30 tại Trang 302 (xref 350):**  
> Đối tượng nằm giữa Hình 29 và Hình 31 là tệp `assets/photos/pleiades-grayscale.jpg` ($476.22 \times 317.48\text{ pt}$). Theo `book/VISUAL_ASSET_AUDIT.md`, đây là ảnh tư liệu lịch sử chụp siêu máy tính NASA Pleiades tại Trung tâm Nghiên cứu Ames (Wikimedia Commons public domain), không phải sơ đồ kỹ thuật vẽ bằng mã. Do đó, theo nguyên tắc bảo vệ tài nguyên ảnh thực, Hình 30 được **giữ nguyên vẹn 100%**, và 5 sơ đồ kỹ thuật trong phạm vi thiết kế của Batch 03 là chính xác: **Hình 27, Hình 28, Hình 29, Hình 31 và Hình 32**.

---

## 2. Luận cứ Khoa học và Kiến trúc Thiết kế Chi tiết Từng Sơ đồ

### 1. Chương 16 — Hình 27: Các phép chiếu quan sát hệ thống (`observability-projections.png`)
- **Câu hỏi kỹ thuật trung tâm:** Mỗi tín hiệu observability trả lời câu hỏi hẹp nào, và nó từ chối hứa hẹn điều gì (tradeoffs)?
- **Bản chất thông tin:** Mô hình tư duy định hướng (Mental Model) với 4 phép chiếu độc lập xuất phát từ cùng một sự kiện hệ thống gốc:
  1. *Logs (Nhật ký):* Trả lời "Lần chạy này fail vì sao?" (bằng chứng chi tiết, có redaction error, request/trace ID). Đánh đổi: Không chứng minh tần suất hay tỷ lệ failure toàn hệ thống.
  2. *Metrics (Số đo):* Trả lời "Tỷ lệ lỗi/timeout tăng từ khi nào?" (time series, aggregation, error budget). Đánh đổi: Không chỉ ra target hay request cụ thể nào là nguyên nhân.
  3. *Traces (Dấu vết):* Trả lời "Lần chạy này chờ ở boundary nào?" (phân tích latency qua các RPC/DB span). Đánh đổi: Không phản ánh tần suất toàn hệ thống nếu trace bị sample.
  4. *Readiness / Health (Trạng thái sẵn sàng):* Trả lời "Có nên đưa traffic vào instance này ngay lúc này?" (hợp đồng control plane ở hiện tại). Đánh đổi: Không chứng minh SLO quá khứ (không nói được trạng thái 24h trước).
- **Invariant bảo đảm:** Bốn tín hiệu là 4 phép chiếu độc lập từ cùng sự kiện; không tín hiệu nào là bản ghi toàn vẹn có thể thay thế các tín hiệu còn lại.

### 2. Chương 16 — Hình 28: Các đường ghi nhận kết quả của một request probe (`probe-observation-path.png`)
- **Câu hỏi kỹ thuật trung tâm:** Khi một HTTP request đến `/probe`, mã nguồn Go thu nhận và phân tán dữ liệu như thế nào qua các đường ống song song?
- **Đối chiếu mã nguồn:** Bám sát chính xác dịch vụ mẫu `labs/part16-real-signals` (`cmd/probe-api/main.go`):
  - Request đi qua hai span: `probe.request` (server span) $\rightarrow$ `probe.dependency` (child span giả lập phụ thuộc).
  - Kết quả request phân nhánh độc lập sang 4 cơ chế mà không phụ thuộc lẫn nhau:
    1. *Structured JSON Log:* Ghi `outcome` ("ok", "fail", "slow", "timeout"), `duration_ms`, `trace_id` ra stdout/stderr riêng biệt.
    2. *OpenTelemetry Span Trace:* Console exporter xuất cây quan hệ parent-child giữa HTTP handler và dependency.
    3. *Prometheus Counter:* `probe_requests_total{outcome=...}` đo tần suất tích lũy theo phân loại outcome.
    4. *Prometheus Histogram:* `probe_duration_seconds_bucket{le=...}` ghi nhận phân phối thời gian trễ theo các ngưỡng bucket.
- **Invariant bảo đảm:** Cùng một request cung cấp dữ liệu độc lập cho 4 cơ chế; không cơ chế nào sinh ra từ cơ chế khác (log không sinh counter, trace không sinh histogram).

### 3. Chương 17 — Hình 29: Vòng lặp điều hòa (`reconciliation-loop.png`)
- **Câu hỏi kỹ thuật trung tâm:** Cơ chế điều khiển kín (closed-loop control) của Kubernetes hội tụ trạng thái thực tế về trạng thái mong muốn như thế nào?
- **Đối chiếu mã nguồn:** Bám sát mã nguồn và hợp đồng kiểm thử `labs/part17-reconciliation-contract` (`fixed/reconcile.go`):
  - *Stage 1 (Desired State / Spec):* Khai báo bền vững qua YAML/API Server (`image: digest`, `replicas: 3`, `probes: /livez, /readyz`). Không dùng mệnh lệnh imperative tức thời.
  - *Stage 2 (Controller / Reconciler Core):* Thực thi 3 bước tuần tự trong mỗi chu kỳ:
    * `Observe:` Đọc trạng thái qua API Server (`obs := Describe(deployment); current := obs.Available`).
    * `Diff:` Gọi hàm giải tích thuần túy `act, err := NextAction(desired, current)`:
      - `current < desired` $\Rightarrow$ `Action{Kind: ActionCreate, Count: desired - current}`.
      - `current > desired` $\Rightarrow$ `Action{Kind: ActionDelete, Count: current - desired}`.
      - `current == desired` $\Rightarrow$ `Action{Kind: ActionNone}` (đã hội tụ).
    * `Act:` Gửi thao tác điều chỉnh nhỏ nhất tới cluster (tạo Pod hoặc gửi tín hiệu dừng SIGTERM).
  - *Stage 3 (Controlled Workload / Pods):* Tiến trình runtime trên node (PID 1 trong container) nhận signal và báo cáo readiness.
- **Invariant bảo đảm:** Một vòng lặp không cam kết đạt trạng thái cuối ngay tức thì; reconciliation là quá trình hội tụ liên tục qua các chu kỳ Reconcile độc lập.

### 4. Chương 17 — Hình 31: Từ image đến workload và quan sát trong cluster (`container-cluster-observation.png`)
- **Câu hỏi kỹ thuật trung tâm:** Phân định ranh giới giữa Artifact (đóng gói OCI), Workload điều phối (Kubernetes) và Diagnostic Client (Go observer).
- **Đối chiếu mã nguồn:** Bám sát `labs/part17-container-kubernetes`:
  - *Section 1 (Image sau Build / Artifact Boundary):* Phản ánh Dockerfile đa tầng: `CGO_ENABLED=0 -trimpath`, base image `distroless/static-debian12:nonroot`, process contract `ENTRYPOINT ["/probe-api"]`, `CMD ["--config", "..."]`, bảo đảm PID 1 nhận trực tiếp tín hiệu OS, không shell trung gian.
  - *Section 2 (Kubernetes Workload & Runtime Boundary):*
    * `Deployment:` Quản lý Pod template, replica count, probes (`/livez`, `/readyz`).
    * `Service:` Điều phối traffic qua label selector `app=probe-api`; chỉ đưa traffic vào Pod khi probe `/readyz` trả về `200 OK`.
    * `Pod Runtime trên Node:` Tiến trình Go chạy dưới sự kiểm soát của containerd/kubelet với cgroup limits và quy trình graceful drain.
  - *Section 3 (Observer Go / client-go Diagnostic Boundary):* Bám sát 100% struct `Observation` trong `labs/part17-container-kubernetes/client-observer/observation.go`:
    ```go
    type Observation struct {
        Generation         int64
        ObservedGeneration int64
        Desired            int32
        Updated            int32
        Available          int32
    }
    ```
    Khẳng định Observer chỉ là diagnostic client đọc qua API Server (`Get`/`Watch`), không can thiệp runtime trên node.
- **Invariant bảo đảm:** Observer chỉ chẩn đoán trạng thái quan sát được từ API; Pod chỉ được nhận traffic khi probe `/readyz` được kubelet xác nhận đạt chuẩn.

### 5. Chương 18 — Hình 32: Chuỗi bằng chứng delivery (`delivery-evidence-chain.png`)
- **Câu hỏi kỹ thuật trung tâm:** Làm sao để pipeline không tạo ra "ảo tưởng màu xanh", mà là một chuỗi khế ước thu hẹp với ranh giới trách nhiệm rõ ràng?
- **Đối chiếu mã nguồn:** Bám sát bảng đối chiếu tại Chương 18 ("Mỗi tín hiệu delivery cho phép kết luận đến đâu") và hợp đồng admission trong `labs/part18-promotion-evidence` (`fixed/admission.go`):
  - Bố cục dạng thác 2 hàng 6 thẻ rộng rãi:
    1. *Thẻ 01 (Source Revision):* `commitSHA (Git Tree Hash)` $\rightarrow$ Nhận diện source input đã qua review PR. *Giới hạn:* Chưa chứng minh artifact nào thật sự được build từ source này.
    2. *Thẻ 02 (Build Artifact):* `sha256:7f8a3b2c... (Digest)` $\rightarrow$ Nhận diện byte bất biến qua content addressing. *Giới hạn:* Chưa chứng minh artifact đã qua test hay provenance nào.
    3. *Thẻ 03 (Bằng chứng Kiểm thử):* `TestsPassed && ProvenanceVerified` $\rightarrow$ Xác thực bài test và nguồn gốc build. *Giới hạn:* Chưa chứng minh hành vi khi chạy thực tế trên production.
    4. *Thẻ 04 (Cổng Chính sách):* `Evaluate(candidate) -> Allowed` $\rightarrow$ OIDC token ngắn hạn cấp quyền hẹp; từ chối nếu thiếu digest hoặc revision. *Giới hạn:* Chưa bảo đảm rollout sẽ không gặp lỗi runtime.
    5. *Thẻ 05 (Cập nhật Desired State):* `Deployment.Spec.Image = Digest` $\rightarrow$ Gán digest đã qua gate vào Spec, đặt replica mong muốn. *Giới hạn:* Chưa chứng minh traffic người dùng thật đã được phục vụ.
    6. *Thẻ 06 (Quan sát Phát hành):* `Rollout: 3/3 Available Replicas` $\rightarrow$ Controller đạt trạng thái hội tụ, Pod pass `/readyz`. *Giới hạn:* Không thay thế cam kết SLO 24h hay chi phí tài nguyên thực tế.
- **Invariant bảo đảm:** Mũi tên tiến trình không biến một bài test pass thành lời hứa bảo đảm trước mọi dạng sự cố; mỗi gate chỉ xác minh bằng chứng thuộc phạm vi khế ước của nó.

---

## 3. Ma trận Kiểm định Chất lượng Xuất bản (QA Matrix)

| Tiêu chí kỹ thuật | Tiêu chuẩn bắt buộc | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Bảng màu Grayscale thuần** | $R = G = B$ 100% điểm ảnh; $\max\|R-G\|=0, \max\|R-B\|=0$ | $0\text{ tint}$ trên cả 5 PNG sơ đồ và 5 specimen preview | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của `Golang_Master.pdf` | • Ch16 Hình 27: $476.22 \times 312.02\text{ pt}$<br>• Ch16 Hình 28: $476.22 \times 264.46\text{ pt}$<br>• Ch17 Hình 29: $335.89 \times 362.83\text{ pt}$<br>• Ch17 Hình 31: $476.22 \times 238.11\text{ pt}$<br>• Ch18 Hình 32: $476.22 \times 216.73\text{ pt}$ | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | • Ch16 Hình 27: $2117 \times 1387\text{ px}$ ($154\text{ KB}$)<br>• Ch16 Hình 28: $2117 \times 1176\text{ px}$ ($123\text{ KB}$)<br>• Ch17 Hình 29: $1493 \times 1613\text{ px}$ ($127\text{ KB}$)<br>• Ch17 Hình 31: $2117 \times 1059\text{ px}$ ($132\text{ KB}$)<br>• Ch18 Hình 32: $2117 \times 964\text{ px}$ ($119\text{ KB}$) | **PASS (100%)** |
| **Tiêu chuẩn Typography** | 100% nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | Min fontSize = $6.00\text{ pt}$; 0 nhãn dưới $6.0\text{ pt}$ trên cả 5 hình:<br>• Ch16 Hình 27: $\min = 6.00\text{ pt}$ (0 dưới 6.0)<br>• Ch16 Hình 28: $\min = 6.00\text{ pt}$ (0 dưới 6.0)<br>• Ch17 Hình 29: $\min = 6.00\text{ pt}$ (0 dưới 6.0)<br>• Ch17 Hình 31: $\min = 6.00\text{ pt}$ (0 dưới 6.0)<br>• Ch18 Hình 32: $\min = 6.00\text{ pt}$ (0 dưới 6.0) | **PASS (100%)** |
| **Khoảng đệm an toàn bounding box** | Khoảng đệm từ bounding box chữ thực tế đến viền $\ge 4.0\text{ pt}$ | Đo lường thực tế sau khi tính descenders và dấu tiếng Việt: mọi khoảng cách đến viền card/banner đều $\ge 4.2\text{ pt}$ | **PASS (100%)** |
| **Tràn viền Canvas** | 0 text overflow trên mọi canvas | 0 string overflow trên cả 5 sơ đồ | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests passed (0.297s) | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn (Usable width: 448.22 pt) | **PASS (100%)** |

---

## 4. Danh mục Tệp Bàn giao

1. [assets/diagrams/observability-projections.png](file:///d:/Golang/assets/diagrams/observability-projections.png) (Chương 16 — Hình 27: 4 phép chiếu quan sát)
2. [assets/diagrams/probe-observation-path.png](file:///d:/Golang/assets/diagrams/probe-observation-path.png) (Chương 16 — Hình 28: Đường ghi nhận probe request)
3. [assets/diagrams/reconciliation-loop.png](file:///d:/Golang/assets/diagrams/reconciliation-loop.png) (Chương 17 — Hình 29: Vòng lặp điều hòa reconciliation)
4. [assets/diagrams/container-cluster-observation.png](file:///d:/Golang/assets/diagrams/container-cluster-observation.png) (Chương 17 — Hình 31: Từ image đến workload và observer)
5. [assets/diagrams/delivery-evidence-chain.png](file:///d:/Golang/assets/diagrams/delivery-evidence-chain.png) (Chương 18 — Hình 32: Chuỗi bằng chứng delivery)
6. [scripts/ch16_18_vector_diagrams.py](file:///d:/Golang/scripts/ch16_18_vector_diagrams.py) (Bộ sinh vector 5 sơ đồ Batch 03)
7. [scripts/build_ch16_18_preview.py](file:///d:/Golang/scripts/build_ch16_18_preview.py) (Script xuất bản preview PDF và 5 trang specimen)
8. [book/design/agent2-ch16-18/ch16_18_preview.pdf](file:///d:/Golang/book/design/agent2-ch16-18/ch16_18_preview.pdf) (Tệp PDF Preview 5 trang chuẩn xuất bản)
9. [book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p01.png](file:///d:/Golang/book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p01.png) (Specimen Trang 1: Hình 27)
10. [book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p02.png](file:///d:/Golang/book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p02.png) (Specimen Trang 2: Hình 28)
11. [book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p03.png](file:///d:/Golang/book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p03.png) (Specimen Trang 3: Hình 29)
12. [book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p04.png](file:///d:/Golang/book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p04.png) (Specimen Trang 4: Hình 31)
13. [book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p05.png](file:///d:/Golang/book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p05.png) (Specimen Trang 5: Hình 32)
14. [book/design/agent2-ch16-18/REPORT_AGENT2_CH16_18.md](file:///d:/Golang/book/design/agent2-ch16-18/REPORT_AGENT2_CH16_18.md) (Báo cáo kỹ thuật chi tiết)

---

## 5. Cổng Phê duyệt (Hard Approval Gate)

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**
> - Toàn bộ 5 sơ đồ kỹ thuật kế tiếp (Hình 27, 28, 29, 31, 32) đã được thiết kế lại hoàn chỉnh và tuân thủ 100% `SCIENTIFIC DIAGRAM QUALITY CONTRACT`.
> - **KHÔNG MERGE:** Nhánh thiết kế được giữ riêng biệt trên `design/ch16-18-agent2-redesign`, không merge vào `main`.
> - **KHÔNG PUSH MAIN:** Chỉ push lên remote branch `design/ch16-18-agent2-redesign`.
> - **KHÔNG CHỈNH SỬA MASTER PDF & MARKDOWN:** `Golang_Master.pdf` và toàn bộ thư mục `book/chapters/` được bảo vệ nguyên vẹn 100% (0 diff).
> - Dừng tại trạng thái này để người dùng kiểm tra trực quan và phê duyệt.
