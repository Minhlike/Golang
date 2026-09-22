# Part 17 — Container, cluster và API thật

Đây là stage hai của `part17-reconciliation-contract`. Nó dùng đúng service từ
`../part16-real-signals`, sau khi mental model desired/current đã được kiểm tra
không phụ thuộc Docker hay Kubernetes.

## Prerequisite và an toàn

Lab là local-only: Docker, `kubectl` và kind phải có sẵn. kind dùng Docker làm
node; không thay bằng cluster cloud. `scripts/verify-prereqs.ps1` không cài gì
và fail rõ nếu thiếu tool.

```powershell
./scripts/verify-prereqs.ps1
```

Mọi lệnh bên dưới là đường thực thi tái lập **chưa được chạy trên checkout này
nếu prerequisite thiếu**. Không có AWS account, secret hay tài nguyên có phí.
Xóa cluster ở cuối lab để trả môi trường local về trạng thái trước đó.

## Bài 1: image là contract của process

Dockerfile nằm ở lab này, nhưng build context là module service thật để `COPY`
khớp với `go.mod` của nó.

```powershell
docker build `
  -f labs/part17-container-kubernetes/Dockerfile `
  -t probe-api:dev `
  labs/part16-real-signals
docker run --rm --name probe-api `
  --read-only --cap-drop ALL `
  -p 18080:18080 -e PORT=18080 probe-api:dev
```

Terminal khác:

```powershell
curl.exe -i http://localhost:18080/readyz
curl.exe -i http://localhost:18080/probe?mode=slow
docker inspect --format '{{.Config.User}}' probe-api
docker stop -t 5 probe-api
```

`docker stop` gửi termination signal rồi chỉ buộc dừng sau thời gian đã chọn;
nó kiểm tra service đã giữ lifecycle shutdown của Chương 12 hay chưa. `USER
65532:65532`, filesystem read-only và bỏ Linux capabilities là các giới hạn của
runtime image này, không phải chứng minh toàn bộ binary an toàn. Multi-stage
giữ Go toolchain ngoài final image; đánh đổi là không có shell/package manager
để debug bên trong container. Dùng tool debug tạm thời khi thật sự cần, không
thêm shell thường trực chỉ để tiện tay.

`probe-api:dev` là identity local có thể di chuyển. Nó **không** là identity
production: khi promotion, Chương 18 thay nó bằng digest đã được gate xét.

## Bài 2: desired state trong kind

```powershell
kind create cluster --name go-book
kind load docker-image probe-api:dev --name go-book
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl -n go-book rollout status deployment/probe-api
kubectl -n go-book get deploy,pod,service
kubectl -n go-book port-forward service/probe-api 18080:80
```

Ở terminal port-forward khác, gọi `/readyz` và `/probe`. Readiness nói Pod có
nên nhận traffic ở thời điểm quan sát; liveness chỉ là contract process còn
phục vụ được, nên không gọi dependency xa. Requests/limits ở manifest là ngân
sách scheduler/runtime của lab, không phải số capacity đã benchmark.

**Failure investigation, không đọc đáp án trước:** apply manifest lỗi, quan sát
desired/current bằng status, event và log, rồi khôi phục manifest tốt.

```powershell
kubectl apply -f k8s/failure-wrong-image.yaml
kubectl -n go-book rollout status deployment/probe-api --timeout=45s
kubectl -n go-book get pods
kubectl -n go-book get events --sort-by=.lastTimestamp
kubectl -n go-book describe pod -l app.kubernetes.io/name=probe-api
kubectl apply -f k8s/deployment.yaml
kubectl -n go-book rollout status deployment/probe-api
```

`rollout status` timeout là expected evidence của wrong image; nó không tự nói
network, registry hay image identity sai ở đâu. `describe` và event mới cho
bằng chứng control plane đã quan sát. Cleanup bắt buộc:

```powershell
kind delete cluster --name go-book
```

## Bài 3: client-go chỉ đọc API đã hiểu

Sau khi thao tác với `kubectl`, chạy client read-only:

```powershell
cd client-observer
go test ./...
go vet ./...
go run ./cmd/observe-deployment --namespace go-book --name probe-api
```

Chương trình `Get` một Deployment và mở watch trong tối đa 15 giây. Nó in
generation/spec desired và status observed/updated/available thay vì gọi object
"healthy". Watch có thể kết thúc hoặc không có event; client thật cần relist và
retry policy riêng, còn lab dừng có chủ đích để không biến thành operator.
Kubeconfig là credential boundary: chỉ dùng context local của learner; một
deployment client chạy trong cluster cần ServiceAccount/RBAC hẹp khác. Giữ
`client-go` cùng nhánh version tương thích cluster theo tài liệu Kubernetes.
