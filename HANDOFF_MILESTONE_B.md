# Handoff — Milestone B (Đã hoàn tất sau Micro-Repair)

Đọc `MASTER PROMPT.txt`, toàn bộ Chương 16–19, `book/README.md`, toàn bộ `labs/`,
và PDF hiện tại trước khi bắt đầu Milestone C. Đây là cuốn sách Go tiếng Việt;
giữ giọng văn tự nhiên ("em" và "anh"), mỗi chapter có mental model riêng, ưu tiên
contract/failure/evidence trước framework. Không retrofit Chương 1–15.

## 1. Trạng thái sau Micro-Repair kỹ thuật

Toàn bộ các lỗi kỹ thuật phát hiện ở checkpoint trước đã được khắc phục triệt để:

1. **Multi-Module Testing trong GitHub Actions:**
   - Repository gồm nhiều Go module độc lập và không có `go.mod` hay `go.work` ở root.
   - Workflow specimen `delivery.yaml` không chạy `go test ./...` tại root; thay vào
     đó, job `verify` sử dụng `working-directory` để kiểm tra chính xác hai module
     thuộc delivery path: `labs/part16-real-signals` (service) và `labs/part18-workflow-delivery` (gate).

2. **Quy chế Workflow Specimen (Reviewable Teaching Artifact):**
   - Tệp `labs/part18-workflow-delivery/workflows/delivery.yaml` là tài liệu mẫu
     trong lab học tập, **không phải** workflow đang active trong `.github/workflows/`.
     Không tuyên bố đây là pipeline đã chạy trên cloud.

3. **Phân biệt ranh giới Artifact Identity (Image ID vs Manifest Digest):**
   - Đã loại bỏ hoàn toàn việc fallback sang digest giả lập hay lấy bừa `docker inspect .Id`.
   - Làm rõ sự khác nhau giữa Local Image Config ID (`.Id` trong Docker daemon) và
     OCI Image Manifest Digest (`sha256:...` đại diện cho toàn bộ manifest và layer
     descriptors, được Buildx xuất ra qua `--metadata-file` hoặc khi push registry).
   - Workflow specimen `delivery.yaml` bắt buộc trích xuất `containerimage.digest`,
     kiểm tra định dạng regex `^sha256:[0-9a-f]{64}$`, và fail ngay (exit 1) nếu thiếu
     digest thật thay vì bịa đặt bằng chứng.
   - Promotion gate và Kubernetes deployment bắt buộc dùng Manifest Digest thật.

4. **Loại bỏ Evidence Theater (Provenance Fail-Closed Thực Sự):**
   - `tests-passed=true` được suy ra hợp lệ từ đồ thị phụ thuộc (`needs: verify`).
   - `provenance-verified` được đặt là `false` vì stage này chưa có bước xác thực
     chữ ký số/attestation chuyên trách (như Cosign hay GitHub Attestations).
   - Tuyệt đối không hard-code `true`. Promotion gate từ chối ứng viên đúng theo
     nguyên tắc fail-closed: `promotion rejected: provenance not verified` và thoát với exit 1.
   - Loại bỏ hoàn toàn `|| echo ...` hay các cơ chế nuốt lỗi trong workflow specimen:
     khi gate từ chối, job dừng ngay lập tức và bước deploy (được chuyển sang dạng comment/tài liệu)
     chứng minh không có bất kỳ lệnh phát hành nào được thực thi khi thiếu provenance.

5. **Làm rõ việc sử dụng Wildcard `*` trong AWS IAM:**
   - Khẳng định chính xác: wildcard `*` trong `Resource = ["*"]` **chỉ được chấp nhận
     duy nhất** cho action `ecr:GetAuthorizationToken` vì đây là ràng buộc bắt buộc
     của AWS IAM (action này không hỗ trợ resource-level permissions).
   - Mọi permission khác có hỗ trợ resource scoping đều phải được khóa hẹp.

6. **Khóa chặt AWS Account ID động:**
   - Loại bỏ ký tự đại diện `*` trong account segment của các ARN ECR và App Runner.
   - Sử dụng `data.aws_caller_identity.current.account_id` để khóa chặt vào Account ID
     thực tế của caller, không hard-code account ID.

7. **Chuẩn hóa tên ECR Repository:**
   - Tách riêng biến `ecr_repository_name` (mặc định: `golang-master`) với validation
     bắt buộc viết thường (`^[a-z0-9][a-z0-9-_/]*$`), tránh lỗi không tương thích giữa
     tên GitHub repo viết hoa (`Golang`) và quy định của AWS ECR.

8. **Ranh giới Terraform Bridge:**
   - Terraform bridge là tài liệu thiết kế và mã nguồn kiểm tra cú pháp (reviewable code).
   - Không chứng minh role đã assume thành công, không chứng minh tài nguyên tồn tại
     hay deploy đã hoàn tất.
   - Máy hiện tại không có `terraform` hay `aws`. Blocker này được giữ explicit; không
     tự ý cài đặt và không tạo tài nguyên cloud.

9. **Bảy tầng bằng chứng trong Chương 18:**
   - Chương 18 và Bảng 21 phân định rõ 7 tầng: Source Revision → Verification →
     Local Image ID → Manifest Digest → Provenance → Promotion Gate → Deployment.

## 2. QA đã chạy thật trên môi trường

- **Go Toolchain (Go 1.27.1 windows/amd64):**
  - `labs/part16-real-signals`: `go test ./...` (PASS), `go test -race ./...` (PASS), `go vet ./...` (sạch).
  - `labs/part17-container-kubernetes/client-observer`: `go test ./...` (PASS), `go test -race ./...` (PASS), `go vet ./...` (sạch).
  - `labs/part17-reconciliation-contract`: `go test ./fixed` (PASS), `go test -race ./fixed` (PASS), `go vet ./fixed` (sạch); fixture cố ý đỏ `exercise` fail đúng nguyên nhân.
  - `labs/part18-promotion-evidence`: `go test ./fixed` (PASS), `go test -race ./fixed` (PASS), `go vet ./fixed` (sạch); fixture cố ý đỏ `exercise` fail đúng nguyên nhân.
  - `labs/part18-workflow-delivery`: `go test -v ./...` (PASS), `go test -race ./...` (PASS), `go vet ./...` (sạch).
  - CLI `promote-gate` chạy thật cả 4 ca:
    1. Đạt chuẩn đầy đủ test + provenance: exit 0 (`promotion approved`).
    2. Trượt test: exit 1 (`promotion rejected: tests not passed`).
    3. Thiếu provenance (fail-closed): exit 1 (`promotion rejected: provenance not verified`).
    4. Định danh `:latest`: exit 2 (`invalid candidate: digest must be a lowercase sha256 digest`).
  - `gofmt -l`: 100% sạch trên tất cả các lab.

- **Bảo toàn artifact cục bộ:**
  - Không sửa, không stage, không xóa:
    `.tmp-editorial-pages/`
    `labs/part10-measure-first/baseline-cpu.out`
    `labs/part10-measure-first/baseline.test.exe`

- **PDF Status:**
  - `scripts/build_pdf.py` build thành công bản **210 trang** `Golang_Master.pdf`.
  - Visual QA 100% qua `pypdfium2` rà soát toàn bộ các trang Chương 18 (188–201):
    không có bất kỳ dòng mã hay bảng biểu nào tràn lề.

## 3. Bước tiếp theo

Milestone B đã chính thức hoàn tất và đóng toàn bộ các vi chỉnh kỹ thuật.
Sẵn sàng mở **Milestone C (Capstone Project `projects/opsprobe/`)** trong lượt làm việc tiếp theo.
