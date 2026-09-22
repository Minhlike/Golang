# Handoff — tiếp tục Milestone B sau checkpoint an toàn

Đọc `MASTER PROMPT.txt`, `AGENTS.md`, toàn bộ Chương 16–18, `book/README.md`,
toàn bộ `labs/`, và PDF hiện tại trước khi mở thêm phạm vi. Đây là cuốn sách Go
tiếng Việt; giữ prose tự nhiên, mỗi chapter có mental model riêng, ưu tiên
contract/failure/evidence trước framework. Không retrofit Chương 1–15.

## Trạng thái đã hoàn tất và được kiểm chứng

- Milestone A đã hoàn tất, commit/push `0e3cd54`: Chương 19 và lab generics /
  interface runtime semantics.
- Trong checkpoint này, Chương 16 có thêm section **“Stage hai: ba signal đi
  qua một service thật”** và `labs/part16-real-signals`.
- Service thật chạy local bằng Go 1.27.1: JSON structured logs, Prometheus
  `/metrics` (counter + histogram với label `outcome` bounded), OpenTelemetry
  console trace có quan hệ `probe.request` → `probe.dependency`.
- Đã chạy thật `ok`, `slow`, `fail`, `timeout`; `fail` trả 503, `timeout` trả
  504. Đã kiểm tra trace parent-child, metric exposition, gofmt, `go test`,
  `go vet`, và `go test -race` của lab.
- Source đã tạo cho stage hai Chương 17:
  `labs/part17-container-kubernetes/`. Nó gồm Dockerfile multi-stage/non-root,
  manifest Deployment/Service/readiness/liveness/resources, wrong-image failure
  fixture, và `client-observer` dùng client-go v0.37.0 để Get + watch bounded
  một Deployment. Test/vet/race của module `client-observer` đã xanh.
- `Golang_Master.pdf` đã build được 197 trang. Visual QA section Ch16 cho thấy
  một ASCII line dài và blockquote bị vỡ thành nhiều hộp; source đã sửa nhưng
  **cần rebuild + render lại** trước khi coi checkpoint QA hoàn tất.

## Ranh giới không được nói quá

Máy tại thời điểm handoff không có `docker`, `kubectl`, `kind`, `k3d`,
`minikube`, `helm`, `terraform` hay `aws`. Vì vậy:

- Không được ghi local container/Kubernetes là “đã chạy” cho đến khi tool được
  phát hiện lại và command thật pass.
- Không tự cài Docker Desktop, driver VM, cluster cloud, hay tạo AWS resource.
  Lab đã có prerequisite check rõ ràng và local-only path.
- Không dùng AWS credential dài hạn; cloud/OIDC chỉ là optional, dry-run-first,
  least privilege. Không apply Terraform hay tạo resource có phí khi người dùng
  chưa phê duyệt cụ thể.

## Việc tiếp theo, theo đúng thứ tự

1. Hoàn tất Chương 17 bằng **một section stage hai** đặt sau conceptual lab.
   Dùng chính `part16-real-signals`; giải thích image/process contract, port
   config, signal + graceful shutdown, non-root/read-only filesystem trade-off,
   Deployment/Service, readiness khác liveness, resources, status/events,
   wrong-image investigation, rồi client-go là read-only Get/watch. Không biến
   chapter thành Docker/YAML reference. Các command không chạy thật phải mang
   nhãn prerequisite/illustrative đúng như README.
2. Nếu Docker/kind/kubectl hiện diện, chạy toàn bộ path local: build image, run
   với `PORT`, curl health/probe, inspect user, stop graceful; tạo kind, load
   image, apply, rollout, port-forward, wrong-image failure/recovery, chạy
   client-go; cleanup `kind delete cluster --name go-book`. Ghi environment và
   bằng chứng thật, không bịa output. Nếu tool vẫn thiếu, giữ blocker explicit.
3. Hoàn tất Chương 18 stage hai: workflow GitHub Actions nhỏ nhưng thật, từ
   source revision → test/vet → build → image/immutable digest → evidence →
   promotion gate. Không dùng `:latest` hay moving tag làm production identity;
   tối thiểu quyền; pin action bằng immutable commit SHA hoặc chính sách version
   đã giải thích. Chỉ workflow/job deploy mới có `id-token: write`.
4. Thêm optional AWS OIDC + Terraform bridge theo dạng reviewable, dry-run
   documentation/code: GitHub OIDC token khác cloud permission; trust policy
   restrict repository/ref/environment; policy action/resource hẹp; `plan`,
   state, outputs, cleanup. Không chạy cloud thật.
5. Cập nhật navigation/cross-reference của Ch16–18 và `book/README.md` chỉ khi
   Stage B đã coherent. Dùng nguồn chính thức, version-sensitive claims phải
   được kiểm chứng (Prometheus/OpenTelemetry, Docker, Kubernetes/client-go,
   GitHub Actions/OIDC, AWS/Terraform).
6. QA Milestone B: gofmt/test/vet/race mọi module mới, intentional failure
   fixture fail đúng lý do, build PDF, render các trang Ch16–18 ở 100%, audit
   code block không overflow, TOC/bookmarks/references. Chỉ khi B thực sự hoàn
   tất mới commit/push milestone B riêng. Capstone là Milestone C, không mở
   trước khi B có evidence xanh.

## Bảo toàn trạng thái

Không sửa/stage các artefact người dùng đang untracked:

- `.tmp-editorial-pages/`
- `labs/part10-measure-first/baseline-cpu.out`
- `labs/part10-measure-first/baseline.test.exe`

PDF typography phải giữ Source Serif 4 (body), Source Sans 3 (heading),
JetBrains Mono (code), 14 pt body, nền sáng, text đen và visual đọc được 100%.
Sau khi source book đổi, chạy `scripts/build_pdf.py`; render PDF bằng Poppler và
kiểm tra trực quan. Poppler có thể báo thiếu display font Symbol/ArialUnicode;
đó là warning đã biết, không phải bằng chứng QA fail nếu render bình thường.
