# BÁO CÁO NGHIỆM THU KỸ THUẬT SƠ ĐỒ (BATCH 03 - ROUND 1 REVIEW)
## CHƯƠNG 16, 17, 18 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả thiết kế:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch16-18-agent2-redesign` (baseline: `a0db7a21556fa2e3ffde41acf2b459d4549b2822`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt` (Mục 7: `SCIENTIFIC DIAGRAM QUALITY CONTRACT`), đối chiếu mã nguồn và test của lab (`labs/part16-observability-evidence`, `labs/part16-real-signals`, `labs/part17-reconciliation-contract`, `labs/part17-container-kubernetes`, `labs/part18-promotion-evidence`, `labs/part18-workflow-delivery`), in ấn grayscale thuần túy.

---

## 1. Bảng Đối chiếu Preflight Bắt buộc (5 Sơ đồ Kế tiếp)

| Chương | Số hình | Trang PDF | Xref PDF | Kích thước 1:1 (pt) | File Asset PNG | Nguồn Lab / Source đối chiếu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Chương 16** | **Hình 27** | Trang 283 | xref 328 | $476.22 \times 312.02$ | `assets/diagrams/observability-projections.png` | `labs/part16-observability-evidence` & `book/chapters/16-thay-duoc-he-thong.md` |
| **Chương 16** | **Hình 28** | Trang 292 | xref 338 | $476.22 \times 264.46$ | `assets/diagrams/probe-observation-path.png` | `labs/part16-real-signals` (`cmd/probe-api`, `probeapi/server.go`) |
| **Chương 17** | **Hình 29** | Trang 300 | xref 347 | $335.89 \times 362.83$ | `assets/diagrams/reconciliation-loop.png` | `labs/part17-reconciliation-contract` (`fixed/reconcile.go`) |
| **Chương 17** | **Hình 31** | Trang 310 | xref 359 | $476.22 \times 238.11$ | `assets/diagrams/container-cluster-observation.png` | `labs/part17-container-kubernetes` (`observation.go`, `Dockerfile`, `k8s/`) |
| **Chương 18** | **Hình 32** | Trang 321 | xref 371 | $476.22 \times 216.73$ | `assets/diagrams/delivery-evidence-chain.png` | `labs/part18-promotion-evidence` (`fixed/admission.go`), `labs/part18-workflow-delivery` |

*(Lưu ý: Hình 30 tại Trang 302, xref 350 là ảnh tư liệu lịch sử NASA Pleiades Wikimedia public domain, không phải sơ đồ vẽ từ mã; giữ nguyên 100%).*

---

## 2. Các Điểm Hiệu chỉnh Kỹ thuật Chính (Round 1 Changes)

1. **Hình 27 (Observability):** Giữ nguyên mô hình 4 phép chiếu (Logs, Metrics, Traces, Health); xác nhận các tên metric (`probe_requests_total`, `probe_request_duration_seconds`), span (`probe.request`, `probe.dependency`) và health endpoints (`/livez`, `/readyz`) khớp 100% source.
2. **Hình 28 (Request Probe):**
   - Sửa phát biểu sai về context timeout: Nêu rõ deadline 20 ms do `context.WithTimeout` tạo trong nhánh `ModeTimeout` của `runDependency`, không phải từ request header.
   - Trình bày `duration_ms: ~20 (đo)` là phép đo runtime minh họa (`time.Since(started)`), không phải hằng số tất định.
   - Đồng bộ metrics với source: `m.requests.WithLabelValues(out).Inc()`, `m.duration.WithLabelValues(out).Observe(sec)`.
   - Khắc phục lỗi tràn viền cột Histogram: Tách tên metric thành `probe_request_` / `duration_seconds` (2 dòng), giữ nguyên độ dài tên đầy đủ và font $\ge 6.0\text{ pt}$ mà không bị tràn viền (margin $\ge 40\text{ pt}$).
3. **Hình 29 (Reconciliation Loop):**
   - Phân biệt rõ mô hình controller khái niệm với hàm giải tích thuần túy `fixed.NextAction(desired, current)` trong lab (pure function, không side effect, không trực tiếp tạo/xóa Pod).
   - Sử dụng cú pháp Go hợp lệ: `Action{Kind: ActionCreate, Count: desired-current}` và `Action{Kind: ActionDelete, Count: current-desired}`.
   - Sửa kết luận `Action{Kind: ActionNone}`: chỉ có nghĩa chưa cần điều chỉnh số lượng replica ở lần quan sát này; không tự đồng nghĩa toàn bộ Deployment đã hội tụ (rollout có thể đang chạy hoặc observation trễ).
4. **Hình 31 (Image & Kubernetes):**
   - Sửa `probe-api:dev` thành local mutable tag theo đúng YAML manifest; Dockerfile chỉ có `ENTRYPOINT ["/probe-api"]`, loại bỏ `CMD` không tồn tại.
   - Đồng bộ YAML: `spec.replicas: 1`, selector `app.kubernetes.io/name: probe-api`, tách probes thành 2 dòng rõ ràng (`/livez (5s)` và `/readyz (3s)`), loại bỏ hoàn toàn lỗi tràn viền.
   - Thiết kế lại kiến trúc mũi tên: Deployment (trên) quản lý lifecycle Pod (giữa); Service (dưới) chọn Pod qua selector và định tuyến khi Ready; Observer (phải) đọc trạng thái qua API Server (`Get`/`Watch`). Loại bỏ luồng Deployment $\to$ Service $\to$ Pod gây hiểu sai.
5. **Hình 32 (Delivery Evidence Chain):**
   - Thẻ 01: Sửa thành `commitSHA (Git Commit SHA)`, phân biệt rõ Git commit hash với Git tree hash.
   - Thẻ 02: Ghi rõ `sha256:7f8a... (OCI Digest)` là OCI Manifest Digest placeholder, phân biệt với Docker local Image Config ID.
   - Thẻ 03: Làm rõ `candidate.TestsPassed == true` là các giá trị boolean đầu vào của struct trong lab; không thay thế attestation chữ ký số thực tế.
   - Thẻ 04: Ghi rõ `Evaluate(candidate) -> Decision` chỉ kiểm tra format digest, revision và các cờ boolean.
   - Thẻ 05: Sử dụng đường dẫn Kubernetes đúng `spec.containers[0].image: Digest` thay vì field giả `Deployment.Spec.Image`. Ghi rõ `replicas: 1` trong lab manifest (mở rộng minh họa 3/3).
   - Thẻ 06: Ghi rõ `Rollout: Available == Desired` (controller đạt trạng thái quan sát khớp spec; không thay thế SLO 24h).

---

## 3. Ma trận Kiểm định Chất lượng Xuất bản (QA Matrix)

| Tiêu chí kỹ thuật | Tiêu chuẩn bắt buộc | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Bảng màu Grayscale thuần** | $R = G = B$ 100% điểm ảnh; $\max\|R-G\|=0, \max\|R-B\|=0$ | $0\text{ tint}$ trên cả 5 PNG sơ đồ và 5 specimen preview | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của `Golang_Master.pdf` | • Ch16 Hình 27: $476.22 \times 312.02\text{ pt}$<br>• Ch16 Hình 28: $476.22 \times 264.46\text{ pt}$<br>• Ch17 Hình 29: $335.89 \times 362.83\text{ pt}$<br>• Ch17 Hình 31: $476.22 \times 238.11\text{ pt}$<br>• Ch18 Hình 32: $476.22 \times 216.73\text{ pt}$ | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | • Ch16 Hình 27: $2117 \times 1387\text{ px}$ ($154\text{ KB}$)<br>• Ch16 Hình 28: $2117 \times 1176\text{ px}$ ($124\text{ KB}$)<br>• Ch17 Hình 29: $1493 \times 1613\text{ px}$ ($128\text{ KB}$)<br>• Ch17 Hình 31: $2117 \times 1059\text{ px}$ ($143\text{ KB}$)<br>• Ch18 Hình 32: $2117 \times 964\text{ px}$ ($117\text{ KB}$) | **PASS (100%)** |
| **Tiêu chuẩn Typography** | 100% nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | Min fontSize = $6.00\text{ pt}$; 0 nhãn dưới $6.0\text{ pt}$ trên cả 5 sơ đồ | **PASS (100%)** |
| **Khoảng đệm an toàn bounding box** | Khoảng đệm từ bounding box chữ thực tế đến viền $\ge 4.0\text{ pt}$ | Mọi khoảng cách từ glyph bounds tới viền card/banner đều $\ge 4.2\text{ pt}$ | **PASS (100%)** |
| **Tràn viền Canvas** | 0 text overflow trên mọi canvas | 0 string overflow trên cả 5 sơ đồ (đã xử lý triệt để cột Histogram và Section 2) | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests passed (0.304s) | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn (Usable width: 448.22 pt) | **PASS (100%)** |

---

## 4. Danh mục Tệp Bàn giao

1. [assets/diagrams/observability-projections.png](file:///d:/Golang/assets/diagrams/observability-projections.png) (Chương 16 — Hình 27)
2. [assets/diagrams/probe-observation-path.png](file:///d:/Golang/assets/diagrams/probe-observation-path.png) (Chương 16 — Hình 28)
3. [assets/diagrams/reconciliation-loop.png](file:///d:/Golang/assets/diagrams/reconciliation-loop.png) (Chương 17 — Hình 29)
4. [assets/diagrams/container-cluster-observation.png](file:///d:/Golang/assets/diagrams/container-cluster-observation.png) (Chương 17 — Hình 31)
5. [assets/diagrams/delivery-evidence-chain.png](file:///d:/Golang/assets/diagrams/delivery-evidence-chain.png) (Chương 18 — Hình 32)
6. [scripts/ch16_18_vector_diagrams.py](file:///d:/Golang/scripts/ch16_18_vector_diagrams.py) (Bộ sinh vector 5 sơ đồ)
7. [scripts/build_ch16_18_preview.py](file:///d:/Golang/scripts/build_ch16_18_preview.py) (Script xuất bản preview PDF & specimens)
8. [book/design/agent2-ch16-18/ch16_18_preview.pdf](file:///d:/Golang/book/design/agent2-ch16-18/ch16_18_preview.pdf) (Tệp PDF Preview 5 trang)
9. [ch16_18_diagrams_p01.png](file:///d:/Golang/book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p01.png) (Specimen Trang 1: Hình 27)
10. [ch16_18_diagrams_p02.png](file:///d:/Golang/book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p02.png) (Specimen Trang 2: Hình 28)
11. [ch16_18_diagrams_p03.png](file:///d:/Golang/book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p03.png) (Specimen Trang 3: Hình 29)
12. [ch16_18_diagrams_p04.png](file:///d:/Golang/book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p04.png) (Specimen Trang 4: Hình 31)
13. [ch16_18_diagrams_p05.png](file:///d:/Golang/book/design/agent2-ch16-18/specimens/ch16_18_diagrams_p05.png) (Specimen Trang 5: Hình 32)
14. [book/design/agent2-ch16-18/REPORT_AGENT2_CH16_18.md](file:///d:/Golang/book/design/agent2-ch16-18/REPORT_AGENT2_CH16_18.md) (Báo cáo kỹ thuật chi tiết)

---

## 5. Cổng Phê duyệt (Hard Approval Gate)

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**  
> - Đã hoàn thành 100% các yêu cầu chỉnh sửa kỹ thuật Round 1.
> - Không merge vào `main`, không push `main`, không sửa `Golang_Master.pdf`, không sửa Markdown.
> - Dừng tại đây để người dùng kiểm tra trực quan và phê duyệt.
