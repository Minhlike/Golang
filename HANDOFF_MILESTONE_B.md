# Handoff — Milestone B hoàn tất, sẵn sàng cho Milestone C (Capstone)

Đọc `MASTER PROMPT.txt`, toàn bộ Chương 16–19, `book/README.md`, toàn bộ `labs/`,
và PDF hiện tại trước khi bắt đầu Milestone C. Đây là cuốn sách Go tiếng Việt;
giữ giọng văn tự nhiên ("em" và "anh"), mỗi chapter có mental model riêng, ưu tiên
contract/failure/evidence trước framework. Không retrofit Chương 1–15.

## Trạng thái đã hoàn tất và được kiểm chứng (Milestone B Done)

1. **Chương 16 Stage hai (`labs/part16-real-signals`):**
   - Service HTTP chạy local bằng Go 1.27.1: JSON structured logs, Prometheus
     `/metrics` (counter + histogram với label `outcome` bounded), OpenTelemetry
     console trace quan hệ `probe.request` → `probe.dependency`.
   - Đã chạy thật các mode `ok`, `slow`, `fail` (503), `timeout` (504).
   - Test, vet, race detector xanh.

2. **Chương 17 Stage hai (`labs/part17-container-kubernetes/`):**
   - Đã thêm section stage hai vào `book/chapters/17-dong-goi-va-dieu-phoi.md`.
   - Giải thích Dockerfile multi-stage, `CGO_ENABLED=0`, `-trimpath`, distroless
     non-root (`USER 65532:65532`), `--read-only`, `--cap-drop ALL`.
   - Signal và graceful shutdown: `docker stop -t 5` kết hợp context timeout.
   - Kubernetes desired state: `Deployment`, `Service`, readiness probe (`/readyz`)
     khác liveness probe (`/livez`), requests/limits, và điều tra sự cố
     `failure-wrong-image.yaml` bằng events và `describe pod`.
   - Module `client-observer` dùng `client-go` v0.37.0 để Get + watch bounded 15s
     một Deployment (`Generation`, `ObservedGeneration`, `Desired`, `Updated`,
     `Available`). Test, race, vet đã pass.

3. **Chương 18 Stage hai (`labs/part18-workflow-delivery/`):**
   - Đã thêm section stage hai vào `book/chapters/18-dua-thay-doi-ra-production.md`.
   - Workflow GitHub Actions mẫu `workflows/delivery.yaml`: quyền mặc định
     `permissions: { contents: read }`, pin action bằng immutable commit SHA đầy
     đủ (kèm comment version), chuyển giao bằng immutable SHA256 digest qua outputs,
     và chỉ job deploy mới có `id-token: write`.
   - Promotion Gate CLI bằng Go (`cmd/promote-gate`): logic fail-closed được kiểm
     chứng qua test và chạy thật (exit 0 khi approved, exit 1 khi test fail, exit 2
     khi digest sai chuẩn như `:latest`).
   - Cầu nối AWS OIDC + Terraform (`terraform/`): quan hệ tin cậy khóa chặt claim
     `sub` theo repo và environment (`repo:Minhlike/Golang:environment:production`),
     quyền IAM theo nguyên tắc đặc quyền tối thiểu (không wildcard `*`).

4. **Navigation và Cross-reference:**
   - Đã cập nhật `book/README.md` phản ánh đầy đủ tiến độ Phần V (Chương 16–18).

5. **QA và Visual Inspection của PDF:**
   - `Golang_Master.pdf` đã build thành công 208 trang (từ candidate kiểm tra hợp lệ).
   - Đã render và kiểm tra trực quan ở tỷ lệ 100% bằng `pypdfium2`: toàn bộ code
     blocks của Chương 16, 17, 18 đã được format và ngắt dòng an toàn, không có
     bất kỳ dòng nào bị tràn lề (overflow) ngoài khung. Bảng biểu và tiêu đề ngay ngắn.
   - Các fixture bài tập cố ý đỏ (`part17-reconciliation-contract/exercise` và
     `part18-promotion-evidence/exercise`) đỏ đúng nguyên nhân chưa implement.
   - Toàn bộ test/race/vet của các module `fixed` và stage hai đều xanh.
   - `gofmt -l` sạch trên toàn bộ các lab mới và sửa đổi.

## Ranh giới môi trường và tính trung thực

Máy tại thời điểm handoff không cài sẵn `docker`, `kubectl`, `kind`, `terraform`,
hay `aws`. Vì vậy:
- Các lệnh trong Chương 17 và 18 được ghi rõ là đường dẫn thực thi chuẩn hóa và
  minh họa nhằm tái lập khi có đủ công cụ; tuyệt đối không tuyên bố là đã chạy
  trên cluster thật ở checkout này.
- Không tự ý cài đặt docker desktop, VM hay tạo tài nguyên cloud có phí.
- Tầng Go (`go test`, `go vet`, `go test -race`, CLI tools) đã được thực thi và
  kiểm chứng 100% trên Go 1.27.1 cục bộ.

## Bảo toàn trạng thái

Tuyệt đối không sửa, stage hay xóa các artefact untracked của người dùng:
- `.tmp-editorial-pages/`
- `labs/part10-measure-first/baseline-cpu.out`
- `labs/part10-measure-first/baseline.test.exe`

## Bước tiếp theo (Milestone C — Capstone Project)

Milestone B đã hoàn tất và đạt chuẩn QA. Agent kế nhiệm có thể mở Milestone C:
- Triển khai dự án Capstone xuyên suốt (`projects/opsprobe/`) kết hợp toàn bộ các
  khái niệm từ Phần I đến Phần VI: CLI chẩn đoán, concurrency có áp suất, telemetry
  (logs/metrics/traces), containerization và delivery contract.
