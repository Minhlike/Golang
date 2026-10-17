# BÁO CÁO NGHIỆM THU KỸ THUẬT SƠ ĐỒ (BATCH 03 - ROUND 2 REVIEW)
## CHƯƠNG 16, 17, 18 — SÁCH CHUYÊN KHẢO GO

**Dự án:** Sách Chuyên Khảo Go (Golang Master)  
**Tác giả thiết kế:** Agent 2 (Technical Diagram Designer)  
**Nhánh Git:** `design/ch16-18-agent2-redesign` (baseline: `545a15a7974b9ac9c4a2c11e30f8b701c8592ff7`)  
**Quy chuẩn áp dụng:** `MASTER PROMPT.txt` (Mục 7: `SCIENTIFIC DIAGRAM QUALITY CONTRACT`), in ấn grayscale thuần túy, 0 diff Markdown/PDF gốc.

---

## 1. Bảng Đối chiếu Preflight Bắt buộc (5 Sơ đồ Batch 03)

| Chương | Số hình | Trang PDF | Xref PDF | Kích thước 1:1 (pt) | File Asset PNG | Trạng thái Round 2 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Chương 16** | **Hình 27** | Trang 283 | xref 328 | $476.22 \times 312.02$ | `assets/diagrams/observability-projections.png` | **LOCKED (PASS Round 1)** |
| **Chương 16** | **Hình 28** | Trang 292 | xref 338 | $476.22 \times 264.46$ | `assets/diagrams/probe-observation-path.png` | **REVISED (Clean Concept Labels)** |
| **Chương 17** | **Hình 29** | Trang 300 | xref 347 | $335.89 \times 362.83$ | `assets/diagrams/reconciliation-loop.png` | **REVISED (Safe Bounding Box $\ge 4.3$ pt)** |
| **Chương 17** | **Hình 31** | Trang 310 | xref 359 | $476.22 \times 238.11$ | `assets/diagrams/container-cluster-observation.png` | **REVISED (Readiness & Kube-API Query)** |
| **Chương 18** | **Hình 32** | Trang 321 | xref 371 | $476.22 \times 216.73$ | `assets/diagrams/delivery-evidence-chain.png` | **REVISED (Zíc-zắc 1 chiều, Model Label)** |

*(Lưu ý: Hình 30 tại Trang 302, xref 350 là ảnh tư liệu NASA, bảo toàn 100%).*

---

## 2. Các Điểm Hiệu chỉnh Kỹ thuật Round 2

1. **Hình 27 (Observability):** Giữ nguyên tuyệt đối 100% (đã PASS ở Round 1).
2. **Hình 28 (Probe Observation Path):**
   - Loại bỏ toàn bộ chuỗi mã giả có dấu chấm lửng (`...`) gây hiểu lầm là cú pháp thật (`m.requests.WithLabel...`, `Values(out).Inc()`).
   - Chuẩn hóa thành các nhãn khái niệm rõ ràng: `Ghi nhận Counter Inc:` kèm `m.requests.WithLabelValues(out).Inc()` và `Ghi nhận Histogram Observe:` kèm `m.duration.WithLabelValues(out).Observe(sec)`.
   - Giữ nguyên `duration_ms: ~20 (đo)` là thời gian thực thi đo bằng `time.Since(started)`, không khẳng định tất định.
3. **Hình 29 (Reconciliation Loop):**
   - Tái cấu trúc ngân sách tọa độ dọc của Card 2: nâng chiều cao lên $156.0\text{ pt}$, bố trí lại 3 sub-card $42.0\text{ pt}$, $46.0\text{ pt}$, $34.0\text{ pt}$.
   - Khắc phục triệt để lỗi baseline sát đáy ở Bước 2B: khoảng đệm từ glyph bounds tới viền đạt $\ge 4.3\text{ pt}$ (vượt chuẩn tối thiểu $4.0\text{ pt}$).
4. **Hình 31 (Container Cluster Observation):**
   - Chuẩn hóa ngữ nghĩa Service readiness: Service chỉ định tuyến traffic tới Pod có condition Ready. EndpointSlice vẫn lưu Pod chưa ready (`ready=false`); Service chỉ gửi traffic khi `/readyz` đạt 200 OK.
   - Sửa mũi tên và chú thích Section 3: Observer Go truy vấn trạng thái Deployment qua Kubernetes API Server (`Get`/`Watch`), không phải Deployment chủ động push.
5. **Hình 32 (Delivery Evidence Chain):**
   - Tái thiết kế toàn bộ luồng tiến trình thành chuỗi zíc-zắc (Boustrophedon) 1 chiều liên tục: Hàng 1 Left-to-Right (`01` $\to$ `02` $\to$ `03`), mũi tên rẽ xuống từ `03` sang `04`, Hàng 2 Right-to-Left (`04` $\to$ `05` $\to$ `06`). Zero giao cắt.
   - Card 05: đổi mã giả thành nhãn mô hình khái niệm chuẩn: `Pod template image ← Digest`.
   - Card 06: làm rõ giới hạn rollout: `Available == Desired` (kèm `UpdatedReplicas` & `Generation`) chỉ chứng minh controller đã hoàn tất chu kỳ cập nhật Pod; không đồng nghĩa hết lỗi tiềm ẩn và không thay thế cam kết SLO 24h.

---

## 3. Ma trận Kiểm định Chất lượng Xuất bản (QA Matrix)

| Tiêu chí kỹ thuật | Tiêu chuẩn bắt buộc | Kết quả thực tế | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Bảng màu Grayscale thuần** | $R = G = B$ 100% pixel; $\max\|R-G\|=0, \max\|R-B\|=0$ | 0 tint trên cả 5 PNG sơ đồ và 5 specimen preview | **PASS (100%)** |
| **Kích thước 1:1 Master PDF** | Khớp chính xác tọa độ xref của `Golang_Master.pdf` | Khớp 1:1 cả 5 sơ đồ theo xref PDF Master | **PASS (100%)** |
| **Độ phân giải xuất bản** | Render vector ReportLab tại 320 DPI | 320 DPI rasterization, sắc nét in ấn | **PASS (100%)** |
| **Tiêu chuẩn Typography** | 100% nhãn chữ có kích thước $\ge 6.0\text{ pt}$ | Min fontSize = $6.00\text{ pt}$; 0 nhãn dưới $6.0\text{ pt}$ | **PASS (100%)** |
| **Khoảng đệm an toàn bounding box** | Glyph bounds tới viền $\ge 4.0\text{ pt}$ | Tất cả sub-cards và banners đạt $\ge 4.3\text{ pt}$ | **PASS (100%)** |
| **Tràn viền Canvas** | 0 text overflow trên mọi canvas | 0 string overflow trên cả 5 sơ đồ | **PASS (100%)** |
| **Bảo toàn văn bản Markdown** | `git diff main -- book/chapters/` bằng 0 | 0 dòng thay đổi trên toàn bộ Markdown sách | **PASS (100%)** |
| **Bảo toàn Master PDF** | `git diff main -- Golang_Master.pdf` bằng 0 | 0 byte thay đổi trên `Golang_Master.pdf` | **PASS (100%)** |
| **Test Suite Xuất bản** | `python scripts/test_publication_contracts.py` | 16/16 tests passed | **PASS (100%)** |
| **Độ rộng khối mã** | `python scripts/validate_code_width.py` | 0 dòng tràn lề in ấn | **PASS (100%)** |

---

## 4. Danh mục Tệp Bàn giao

1. [assets/diagrams/observability-projections.png](file:///d:/Golang/assets/diagrams/observability-projections.png) (Chương 16 — Hình 27, LOCKED)
2. [assets/diagrams/probe-observation-path.png](file:///d:/Golang/assets/diagrams/probe-observation-path.png) (Chương 16 — Hình 28)
3. [assets/diagrams/reconciliation-loop.png](file:///d:/Golang/assets/diagrams/reconciliation-loop.png) (Chương 17 — Hình 29)
4. [assets/diagrams/container-cluster-observation.png](file:///d:/Golang/assets/diagrams/container-cluster-observation.png) (Chương 17 — Hình 31)
5. [assets/diagrams/delivery-evidence-chain.png](file:///d:/Golang/assets/diagrams/delivery-evidence-chain.png) (Chương 18 — Hình 32)
6. [scripts/ch16_18_vector_diagrams.py](file:///d:/Golang/scripts/ch16_18_vector_diagrams.py) (Bộ sinh vector 5 sơ đồ)
7. [scripts/build_ch16_18_preview.py](file:///d:/Golang/scripts/build_ch16_18_preview.py) (Script xuất bản preview PDF & specimens)
8. [book/design/agent2-ch16-18/ch16_18_preview.pdf](file:///d:/Golang/book/design/agent2-ch16-18/ch16_18_preview.pdf) (Tệp PDF Preview 5 trang)
9. Specimens: `ch16_18_diagrams_p01.png` $\to$ `ch16_18_diagrams_p05.png`
10. [book/design/agent2-ch16-18/REPORT_AGENT2_CH16_18.md](file:///d:/Golang/book/design/agent2-ch16-18/REPORT_AGENT2_CH16_18.md) (Báo cáo kỹ thuật chi tiết)

---

## 5. Cổng Phê duyệt (Hard Approval Gate)

> [!IMPORTANT]
> **GATE STATUS: `AWAITING_MANUAL_APPROVAL`**  
> - Đã hoàn thành 100% các yêu cầu chỉnh sửa kỹ thuật Round 2.
> - Không merge vào `main`, không push `main`, không sửa `Golang_Master.pdf`, không sửa Markdown.
> - Dừng tại đây để người dùng kiểm tra trực quan và phê duyệt.
