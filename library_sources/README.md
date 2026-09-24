# ONLINE GO DEVOPS LIBRARY SOURCE LAB
## Live Upstream Sync, Immutable Source Lock & Zero-Guess Protocol

Hệ thống phòng thí nghiệm nguồn (**Library Source Lab**) phục vụ việc nghiên cứu, trích dẫn và mổ xẻ mã nguồn thực tế của **50 thư viện Go** trọng yếu trong hệ sinh thái Cloud Native, DevOps, SRE, Platform Engineering, DevSecOps, Networking, Observability, IaC, CI/CD, Supply Chain, Kubernetes, AIOps và AI Agent Infrastructure.

---

## 1. Mệnh Lệnh Tối Cao: Zero-Guess Protocol

Mọi khẳng định kỹ thuật về hành vi, giải thuật, kiểu dữ liệu, cơ chế hủy context, pooling, retry hay goroutine lifecycle trong sách **bắt buộc phải xuất phát từ mã nguồn thực tế đã được đồng bộ và khóa bất biến**.

```
┌─────────────────────────────────────────────────────────────┐
│                   ZERO-GUESS PROTOCOL                       │
│                                                             │
│       NO VERIFIED SOURCE = NO IMPLEMENTATION CLAIM          │
│                                                             │
│  1. Tuyệt đối không đoán version, tag, module path.         │
│  2. Tuyệt đối không trích dẫn function/type từ trí nhớ.     │
│  3. Tuyệt đối không chạy lệnh build/make/run của upstream.  │
│  4. Nếu chưa đối soát source code: gắn UNVERIFIED / BLOCKED │
│  5. Phát hiện tag upstream bị dịch chuyển: khóa bảo mật     │
└─────────────────────────────────────────────────────────────┘
```

### Quy tắc An toàn Vận hành (Safety Guarantees):
1. **Cô lập Git (`.gitignore`):** Thư mục `library_sources/repos/` chứa mã nguồn third-party được Git bỏ qua hoàn toàn. Không bao giờ commit mã nguồn bên ngoài vào repository của sách.
2. **Không thực thi mã nguồn lạ:** Hệ thống chỉ thực hiện `git ls-remote`, `git clone/fetch` (detached HEAD) và tính fingerprint file tĩnh. Tuyệt đối không gọi `go run`, `go generate`, `make`, shell scripts hoặc test suites của upstream để ngăn chặn supply chain execution rủi ro.
3. **Bảo vệ dịch chuyển Tag (Tag Move Protection):** Nếu một Git tag trên upstream bị force-push hoặc re-tag trỏ sang một commit hash khác với giá trị đã ghi trong `lock.json`, tiến trình lập tức dừng với trạng thái `TAG_MOVED_SECURITY_REVIEW_REQUIRED`.
4. **An toàn vùng làm việc (Dirty Safety):** Nếu thư mục local checkout có uncommitted changes, tiến trình từ chối cập nhật và trả về `DIRTY_BLOCKED`.
5. **Fingerprint bất biến:** Mỗi phiên bản thư viện được gắn một mã băm xác định `source_tree_sha256` tính trên toàn bộ cây file mã nguồn được track.

---

## 2. Vị Trí Cấu Trúc Sách (Back Matter Invariant)

Toàn bộ nội dung mổ xẻ 50 thư viện là **Back Matter** (Phụ bản chuyên sâu cuối sách):
- **KHÔNG PHẢI Chapter:** Không đánh số chương, không tạo `book/chapters/chXX-...`.
- **KHÔNG PHẢI Part:** Không gom thành phần đánh số trong mục lục chính.
- **KHÔNG CHEN VÀO NỘI DUNG HIỆN HỮU:** Tuyệt đối không chèn ngang vào Chương 13, 16, 17, 20 hay bất kỳ chương nào khác.
- **VỊ TRÍ TUYỆT ĐỐI:** Nằm **sau chương cuối cùng** (hiện tại và tương lai) và **ngay trước Phụ lục A (Error Atlas)**. Phụ lục A — Atlas Lỗi Go luôn là thành phần cuối cùng bất biến của toàn bộ ấn bản.

```
Frontmatter ──────► Các Chương (Chương 01 ──► Chương N) ──────► Back Matter (50 Thư Viện) ──────► Phụ lục A: Atlas Lỗi Go (Cuối Sách)
```

---

## 3. Cấu Trúc Thư Mục

```
library_sources/
├── README.md                      # Tài liệu này
├── catalog.json                   # Danh mục định danh chuẩn 50 thư viện (Ranks 1..50)
├── lock.json                      # Khóa phiên bản bất biến (Commit, Tag, Tree, SHA-256)
├── status.json                    # Trạng thái đồng bộ chi tiết và mã lỗi
├── UPDATE_REPORT.md               # Báo cáo tổng hợp sau mỗi chu kỳ cập nhật
├── repos/                         [GITIGNORED] Mã nguồn checkout ở trạng thái DETACHED HEAD
├── provenance/                    # Bằng chứng tra cứu mạng và quyết định chọn ref (50 files JSON)
├── source_maps/                   # Sơ đồ giải phẫu kiến trúc, entrypoint và call paths (50 files JSON)
└── update_history/                # Lịch sử cập nhật dạng diffstat theo mốc thời gian UTC
```

---

## 4. Danh Mục 50 Thư Viện & Phân Tầng Nghiên Cứu

| Nhóm | Ranks | Số lượng | Độ sâu nghiên cứu | Các thư viện tiêu biểu |
| :--- | :--- | :--- | :--- | :--- |
| **Tier S** | 01–12 | 12 | Deep Source Dive | `client-go`, `controller-runtime`, `aws-sdk-go-v2`, `prometheus/client_golang`, `otel-go`, `otel-collector`, `moby`, `containerd`, `terraform-plugin-framework`, `helm`, `go-git`, `golang/crypto` |
| **Tier A** | 13–30 | 18 | Phân tích 2–4 trang | `opa`, `cosign`, `grpc-go`, `protobuf-go`, `go-containerregistry`, `oras-go`, `cni`, `ebpf`, `netlink`, `crossplane-runtime`, `fluxcd/pkg`, `go-github`, `cobra`, `viper`, `fsnotify`, `zap`, `automaxprocs`, `go-retryablehttp` |
| **Tier B** | 31–43 | 13 | Phân tích 1–3 trang | `sync`, `time/rate`, `go-plugin`, `hcl`, `terraform-plugin-go`, `prometheus/common`, `sqlite`, `otel-contrib`, `trivy`, `in-toto`, `go-tuf`, `google-cloud-go`, `azure-sdk-for-go` |
| **Frontier** | 44–50 | 7 | Frontier Tooling / AI Agent | `mcp-go-sdk`, `google/adk-go`, `microsoft/agent-framework-go`, `eino`, `trpc-agent-go`, `kagent`, `agentscope-go` |

---

## 5. Hướng Dẫn Vận Hành

### Cập nhật toàn bộ (Mặc định: Online Sync + Update All):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\update_library_sources.ps1
```

### Chỉ kiểm tra phiên bản mới mà không tải mã nguồn:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\update_library_sources.ps1 -CheckOnly
```

### Cập nhật một thư viện cụ thể:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\update_library_sources.ps1 -Library k8s-client-go
```

### Cập nhật theo phân tầng:
```powershell
# Chỉ cập nhật nhóm Tier S
powershell -ExecutionPolicy Bypass -File .\scripts\update_library_sources.ps1 -Tier TIER_S

# Chỉ cập nhật các thư viện Frontier (AI Agent Infra)
powershell -ExecutionPolicy Bypass -File .\scripts\update_library_sources.ps1 -FrontierOnly

# Cập nhật tất cả trừ Frontier (Tier S, A, B)
powershell -ExecutionPolicy Bypass -File .\scripts\update_library_sources.ps1 -CoreOnly
```

### Tính lại toàn bộ mã băm (Fingerprint) khi nghi ngờ file bị thay đổi:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\update_library_sources.ps1 -ForceRehash
```

### Kiểm toán tính hợp lệ toàn diện (Zero-Dependency Python Validator):
```powershell
python scripts/validate_library_sources.py
```
Tiến trình kiểm toán xác minh:
1. Đủ 50 ranks từ 1 đến 50 không trùng lặp, không khuyết thiếu.
2. Tất cả enum `version_strategy`, `release_status`, `sync_status` hợp lệ.
3. 50 files provenance và 50 files source maps tồn tại và đầy đủ trường.
4. Mọi local repo checkout ở đúng commit trong `lock.json`, ở trạng thái Detached HEAD, clean working tree, và trùng khớp source tree fingerprint.
