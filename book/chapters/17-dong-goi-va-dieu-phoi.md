# Chương 17 — Đóng gói và điều phối

Một chương trình Go chạy được bằng `go run` thường tạo một ảo giác dễ chịu: source, compiler, shell, tệp cấu hình và tiến trình đang ở gần nhau, nên “chạy được” trông như một sự thật đơn giản. Nó không còn đơn giản khi program phải được build một lần, chạy trên máy khác, nhận cấu hình khác, bị dừng giữa chừng, rồi được thay thế khi node biến mất. Lúc ấy, câu hỏi không phải chỉ là “làm sao chạy Docker?” mà là: **ai sở hữu trạng thái mà ta muốn hệ thống duy trì?**

Mental model của chương là: **image đóng gói contract khởi động của một tiến trình; orchestrator duy trì trạng thái mong muốn bằng vòng điều hòa trạng thái (reconciliation), không lặp lại một câu lệnh start.** Image nói tiến trình mặc định nào, filesystem nào và default đối số nào có mặt. Một tải công việc khai báo nói bao nhiêu bản sao của artefact ấy cần tồn tại và policy nào áp dụng. bộ điều khiển (controller) quan sát trạng thái hiện tại, chọn một action nhỏ để đưa nó gần trạng thái mong muốn hơn, rồi lại quan sát. Không bước nào trong số này tự chứng minh application đã phục vụ đúng business yêu cầu.

## Một image chạy được chưa phải một triển khai

Giả sử team đã build một image và chạy thử một container. Binary in log, cổng mở, yêu cầu đầu tiên trả `200`. Khi đưa cùng image vào cluster, một instance bị restart vì tiến trình kết thúc, instance khác chưa nhận traffic vì chưa ready, còn triển khai vẫn đang thay Pod cũ bằng Pod mới. Nếu gọi tất cả là “Docker bị lỗi”, ta đánh mất ba boundary khác nhau:

@table Ba contract không nên trộn làm một

| Boundary | Câu hỏi chính | Bằng chứng phù hợp |
| --- | --- | --- |
| hiện vật gói phát hành | tiến trình nào, default args nào, tệp nào được mang theo? | Image cấu hình, digest, Dockerfile, SBOM nếu có. |
| Runtime | tiến trình có start, nhận signal, mở listener và thoát theo contract không? | Exit status, log, health/readiness, resource observation. |
| Control plane | trạng thái mong muốn có đang được đưa gần current state không? | Spec, status, event và action của bộ điều khiển (controller). |

Container không phải một máy ảo thu nhỏ, cũng không biến binary thành service đúng nghĩa. Nó là cách đóng gói filesystem và execution configuration cho một tiến trình. Còn `docker run` là một thao tác mệnh lệnh: nó yêu cầu runtime tạo một container ngay lúc này. Kubernetes làm việc ở lớp khác: object có `spec` diễn tả trạng thái mong muốn, `status` báo điều đã quan sát, và các bộ điều khiển (controller) liên tục cố đưa hai thứ gần nhau hơn. Vì thế, “đã apply YAML” không đồng nghĩa “đã có traffic phục vụ”, cũng như “Pod Running” không đồng nghĩa “mọi container đều ready”.

![Vòng reconciliation](../../assets/diagrams/reconciliation-loop.png)
@figure trạng thái mong muốn là input bền hơn một lệnh start. bộ điều khiển (controller) chạy nhiều vòng; trạng thái cluster có thể luôn thay đổi.

## Image là tiến trình contract, không phải bản sao của laptop

OCI image configuration có những execution default như platform, working directory, user, `Entrypoint` và `Cmd`. Với image chạy một binary Go, cách đọc hữu ích là: `ENTRYPOINT` chọn executable bền vững; `CMD` là default đối số mà runtime có thể override. Cả hai ở exec form giữ executable và từng đối số tách riêng, tránh một shell parent làm mờ quoting và đường đi của signal.

~~~dockerfile
FROM golang:1.27.1 AS build
WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath \
  -o /out/probe-api ./cmd/probe-api

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/probe-api /probe-api
USER nonroot:nonroot
ENTRYPOINT ["/probe-api"]
CMD ["--cấu hình", "/etc/probe-api/cấu hình.json"]
~~~

Đây là một **mẫu cấu trúc**, không phải Dockerfile có thể copy nguyên xi cho lab hiện có: repository của sách không có `cmd/probe-api` hay `go.sum` ở root. Chi tiết ấy quan trọng hơn vẻ “môi trường vận hành-ready” của snippet. Một Dockerfile chỉ có ý nghĩa khi đường dẫn package, phụ thuộc, target platform và runtime assets đều khớp source thật. Đừng thêm `CGO_ENABLED=0`, distroless hay `nonroot` như một câu thần chú; hãy kiểm tra binary có cần C library, CA certificates, timezone data, shell hay write path nào không.

`RUN` chạy ở **build time** và tạo layer; `CMD` chỉ định default khi **container start**. Nhầm hai điều này có thể khiến test hoặc migration bị chạy lúc build, còn image khi start lại không có main tiến trình đúng. Tương tự, `COPY` source rồi build trong image không tự làm source reproducible: base image tag có thể trôi, module download cần phụ thuộc graph được kiểm soát, và final image phải được nhận diện bằng digest nếu identity chính xác quan trọng hơn một tag dễ đọc.

> **Dừng để dự đoán:** Nếu runtime override `CMD` thành `--config /run/config.json`, executable nào vẫn được chạy? Nếu `ENTRYPOINT` là shell form, tiến trình nào thực sự là PID 1 và signal termination sẽ đi qua đâu? Đừng trả lời bằng thói quen: mở image cấu hình hay Dockerfile rule của runtime đang dùng.

## Một tiến trình làm gì khi control plane muốn dừng nó?

Chương 12 đã tách vòng đời HTTP server khỏi `main`: signal dẫn tới context của application, server ngừng nhận connection mới, rồi `Shutdown` chờ yêu cầu đang hoạt động trong một grace period. Contract ấy vẫn thuộc về program. Container runtime và kubelet chỉ tạo thêm một upstream event: tới lúc termination, tiến trình nhận signal theo runtime policy; Kubernetes cũng có thể chờ một grace period trước khi buộc dừng. Không có lời hứa chung rằng mọi handler active tự bị cancel, mọi subprocess tự biến mất, hay mọi yêu cầu sẽ hoàn thành.

Vì vậy `ENTRYPOINT ["/probe-api"]` có ý nghĩa vận hành hơn `ENTRYPOINT /probe-api --config ...` khi intent là để binary trở thành tiến trình chính. Exec form không giải quyết tắt an toàn (graceful shutdown) thay chương trình, nhưng nó không chèn một command shell giữa runtime và binary. `SIGTERM` vẫn chỉ là một tín hiệu: application phải quyết định cách chuyển nó thành drain, thời hạn xử lý (deadline) và exit mã nguồn; hệ điều phối phải được cấu hình với thời gian đủ cho policy đó.

Đây cũng là lúc đọc lại readiness của Chương 16 cho đúng scope. Readiness trả lời “có nên gửi traffic mới vào instance này ngay bây giờ?”. Nó không phải một lời hứa image build đúng, không phải liveness, không phải lịch sử SLO, và không phải cái cớ để restart tiến trình vì phụ thuộc xa vừa chậm. Khi readiness false, traffic routing có thể dừng hướng yêu cầu mới tới instance; bộ điều khiển (controller) vẫn có thể giữ instance đó tồn tại để nó tự hồi phục hoặc để người vận hành điều tra.

## trạng thái mong muốn không phải một script dài

Một manifest minh họa dưới đây chỉ đặt ba ý rõ ràng: identity của artefact, số bản sao mong muốn và readiness contract. Nó không tuyên bố rằng đây là toàn bộ configuration của một môi trường vận hành service.

~~~yaml
apiVersion: apps/v1
kind: triển khai
metadata:
  name: probe-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: probe-api
  template:
    metadata:
      labels:
        app: probe-api
    spec:
      containers:
        - name: probe-api
          image: registry.example/probe-api@sha256:REPLACE_ME
          args: ["--cấu hình", "/etc/probe-api/cấu hình.json"]
          readinessProbe:
            httpGet:
              path: /readyz
              cổng: 8080
~~~

`replicas: 3` không có nghĩa “chạy lệnh start đúng ba lần rồi xong”. Nó là desired count. bộ điều khiển (controller) có thể tạo Pod khi thiếu, tạo replacement khi một Pod bị mất, hoặc từng bước thay replica khi template thay đổi. Pod là đơn vị tương đối ephemeral; một Pod đã được schedule không tự nhảy sang node khác. Higher-level bộ điều khiển (controller) mới là thứ tạo Pod khác để tải công việc tiếp tục tiến về trạng thái mong muốn.

`image` dùng digest trong ví dụ vì digest là identity bất biến của artefact cụ thể. Tag như `:latest` là một tên có thể trỏ đến image khác ở thời điểm khác; nó có thể hữu ích cho workflow phát triển, nhưng không nên được diễn giải như bằng chứng triển khai đang chạy đúng build nào. Placeholder `REPLACE_ME` cố ý làm manifest chưa apply được: một digest bịa ra sẽ tạo configuration trông hoàn chỉnh nhưng không có artefact để kéo.

Một pod spec cũng không phải nơi để nhét mọi cấu hình trong mã nguồn. Environment biến, Secret, ConfigMap, volume, service account, resource yêu cầu/limit và network policy đều có semantics, quyền truy cập và vòng đời riêng. Khi một field ảnh hưởng tới khả năng start hay readiness, nó là một phần của runtime contract phải test và quan sát; nó không phải “YAML glue” để bỏ qua mã nguồn review.

## Đọc điều hòa trạng thái (reconciliation) bằng một hàm nhỏ

Kubernetes bộ điều khiển (controller) thật quan sát API object, có cache, retry, error handling và nhiều resource khác nhau. Ta không mô phỏng cluster trong lab. Thay vào đó, minimal reproducer giữ lại phần tư duy cốt lõi: một lần quan sát trả về **action kế tiếp**, không hứa system đã hội tụ ngay sau action đó.

~~~go
type ActionKind string

const (
	ActionNone   ActionKind = "none"
	ActionCreate ActionKind = "create"
	ActionDelete ActionKind = "delete"
)

type Action struct {
	Kind  ActionKind
	Count int
}

func NextAction(desired, current int) (Action, error) {
	if desired < 0 || current < 0 {
		return Action{}, ErrNegativeReplicaCount
	}
	switch {
	case current < desired:
		return Action{
			Kind:  ActionCreate,
			Count: desired - current,
		}, nil
	case current > desired:
		return Action{
			Kind:  ActionDelete,
			Count: current - desired,
		}, nil
	default:
		return Action{Kind: ActionNone}, nil
	}
}
~~~

Hàm cố tình không `for` cho đến khi count bằng nhau. Nếu nó tự gọi “start” ba lần, nó sẽ che những event thật giữa các action: create có thể fail, instance có thể chưa ready, current state có thể thay đổi bởi một actor khác, hoặc bộ điều khiển (controller) có thể cần rate limit. `ActionNone` không chứng minh application healthy; nó chỉ nói snapshot count được đưa vào hàm đang bằng desired count. Sự khiêm tốn này là một property quan trọng của mã nguồn điều phối.

Trong bộ điều khiển (controller) thật, trạng thái mong muốn không phải immutable mã nguồn constant và current state không phải biến local đáng tin vĩnh viễn. Spec có thể đổi lúc bộ điều khiển (controller) đang xử lý; cache có thể cũ; action trả lỗi hoặc thành công một phần. Vì vậy điều hòa trạng thái (reconciliation) phải idempotent: cùng desired/current observation thì `NextAction` đưa cùng action, và action đó có ý nghĩa an toàn khi vòng lặp chạy lại. Đây là documented control-loop pattern; chi tiết retry queue, status condition và ownership reference là implementation/API design của Kubernetes, không phải language semantics của Go.

@table Điều một vòng điều hòa trạng thái (reconciliation) được phép kết luận

| Observation | Action hợp lý của toy reconciler | Điều vẫn chưa biết |
| --- | --- | --- |
| Desired 3, current 1 | Tạo thêm 2 instance. | Hai instance đó có start hay ready không. |
| Desired 3, current 5 | Dừng/bỏ 2 instance. | Instance nào nên bị chọn, connection có cần drain không. |
| Desired 3, current 3 | Không đổi replica count. | Image revision, traffic, latency, SLO và resource health. |

## Lab: tự hoàn thành vòng lặp một bước

Mở `labs/part17-reconciliation-contract/exercise/reconcile_test.go` trước. Bài không cần Docker daemon, cluster, credential hay network. Test đưa desired/current count vào và đòi action bounded, idempotent về kết quả, không biến input âm thành một action “lạ”. Đây không phải Kubernetes giả lập; đó là cách tách mental model của điều hòa trạng thái (reconciliation) khỏi số lượng API mà người học chưa cần biết.

~~~powershell
cd labs/part17-điều hòa trạng thái (reconciliation)-contract
go test -tags exercise ./exercise
go test ./fixed
go vet ./fixed
go test -race ./fixed
~~~

Hãy viết `NextAction` từ contract, không mở `fixed/` trước. Câu hỏi trước khi mã nguồn là: action nào mang **chênh lệch** giữa desired và current, và case equal cần trả gì để bên gọi không phải đoán? Sau khi tests xanh, tự thay current bằng kết quả giả định của action rồi gọi lại. Điều gì xảy ra ở vòng thứ hai? Đó là trực giác idempotency tối thiểu của chapter.

**Đáp án — chỉ đọc sau khi đã tự làm.** Validate cả hai count trước, vì `desired - current` với số âm có thể biến một configuration lỗi thành action hợp lệ giả. Sau đó trả `create` hay `delete` với `Count` đúng bằng độ chênh; equal trả `ActionNone` với `Count` zero. Không mutate input, không loop, không sleep và không cố “chờ ready”: mỗi thứ đó thuộc boundary khác.

## Stage hai: đưa service thật vào container và cluster

Vòng lặp `NextAction` ở trên giúp ta hiểu bản chất của điều hòa trạng thái (reconciliation) mà chưa
cần tới cluster thật. Nhưng khi đưa một service Go vào vận hành, mã nguồn không còn
chạy trực tiếp trên máy lập trình. Nó phải được đóng gói vào một OCI image và
giao phó cho một hệ điều phối. `labs/part17-container-kubernetes` dùng chính
HTTP service `probe-api` từ `labs/part16-real-signals` để kiểm chứng trọn vẹn
chuỗi ranh giới này trên môi trường cục bộ.

~~~text
Dockerfile (multi-stage, non-root)
    |
    v
Image: probe-api:dev  --->  Container runtime (signal, cổng, read-only)
                                  |
                                  v
                            Cluster (kind)
                                  |
            +---------------------+---------------------+
            |                                           |
            v                                           v
      triển khai (desired)                       Service (traffic)
       - readiness: /readyz                       - cluster IP
       - liveness: /livez                         - cổng forwarding
            |
            v
   client-go observer (read-only Get/Watch)
~~~

Trước khi bắt đầu, lab kiểm tra các công cụ bắt buộc bằng script
`scripts/verify-prereqs.ps1`. Nó đòi hỏi `docker`, `kubectl` và `kind` có mặt
trên máy local. Nếu môi trường hiện tại chưa cài đặt những công cụ này, script
sẽ dừng lại với thông báo rõ ràng; khi đó, các lệnh dưới đây là đường dẫn thực
thi minh họa được chuẩn hóa để anh tái lập khi có đủ công cụ, tuyệt đối không
tự ý thay thế bằng một cluster cloud có phí.

~~~powershell
cd labs/part17-container-kubernetes
./scripts/verify-prereqs.ps1
~~~

### Image là contract của tiến trình

Dockerfile của lab áp dụng mô hình multi-stage build để tách biệt môi trường
biên dịch với môi trường thực thi. Stage đầu tiên dùng image Go chính thức để tải
module và biên dịch binary với `CGO_ENABLED=0` và cờ `-trimpath` nhằm loại bỏ
đường dẫn tệp hệ thống cục bộ khỏi binary. Stage cuối cùng chỉ sao chép duy nhất
tệp binary sang base image tối giản `distroless/static-debian12:nonroot`.

~~~dockerfile
FROM golang:1.27.1 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath \
  -o /out/probe-api ./cmd/probe-api

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/probe-api /probe-api
USER 65532:65532
ENTRYPOINT ["/probe-api"]
~~~

Contract khởi động ở đây rất chặt chẽ: `ENTRYPOINT` ở exec form đảm bảo binary
là PID 1 trong container. Cổng lắng nghe được cấu hình qua biến môi trường
`PORT`, khớp hoàn toàn với contract của HTTP server ở Chương 12 và 16. Khi chạy
container, ta áp dụng nguyên tắc đặc quyền tối thiểu: `--read-only` khóa toàn bộ
root filesystem, `--cap-drop ALL` tước bỏ mọi Linux capability thừa, và `USER
65532:65532` ngăn chặn việc chạy dưới quyền root.

~~~powershell
# Chạy từ thư mục gốc của repository (minh họa)
docker build `
  -f labs/part17-container-kubernetes/Dockerfile `
  -t probe-api:dev `
  labs/part16-real-signals

docker run --rm --name probe-api `
  --read-only --cap-drop ALL `
  -p 18080:18080 -e cổng=18080 probe-api:dev
~~~

Ở một terminal khác, ta kiểm tra các contract vận hành:

~~~powershell
curl.exe -i http://localhost:18080/readyz
curl.exe -i http://localhost:18080/probe?mode=slow
docker inspect --format '{{.cấu hình.User}}' probe-api
docker stop -t 5 probe-api
~~~

Lệnh `docker stop -t 5` gửi tín hiệu `SIGTERM` tới tiến trình và cho phép 5 giây để
server hoàn tất các yêu cầu đang xử lý trước khi runtime gửi `SIGKILL`. Đây chính
là phép thử cho contract tắt an toàn (graceful shutdown) mà ta đã xây dựng. Đánh đổi của
distroless và read-only filesystem là gì? Container sẽ không có shell (`/bin/sh`),
không có trình quản lý gói, và binary không thể tùy tiện ghi tệp tạm nếu không
được mount một thư mục riêng biệt. Sự bất tiện khi debug tại chỗ này đổi lại một
bề mặt tấn công cực kỳ hẹp.

Cần lưu ý: nhãn `probe-api:dev` chỉ là định danh cục bộ trên máy phát triển. Nó
không phải là một định danh bất biến dùng cho môi trường môi trường vận hành; Chương 18
sẽ giải quyết bài toán định danh bằng digest.

### trạng thái mong muốn và điều tra sự cố trong cluster

Khi chuyển từ container đơn lẻ sang Kubernetes, ta không còn ra lệnh chạy một
tiến trình mà khai báo trạng thái mong muốn thông qua các manifest: `namespace.yaml`,
`deployment.yaml` và `service.yaml`.

~~~powershell
kind create cluster --name go-book
kind load docker-image probe-api:dev --name go-book
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/triển khai.yaml
kubectl apply -f k8s/service.yaml
kubectl -n go-book rollout status triển khai/probe-api
kubectl -n go-book get triển khai,pod,service
kubectl -n go-book cổng-forward service/probe-api 18080:80
~~~

Trong `deployment.yaml`, hai probe phục vụ hai mục đích hoàn toàn khác biệt:

1. **Readiness Probe (`/readyz`):** Trả lời câu hỏi "Pod này có sẵn sàng nhận
   traffic từ Service ngay lúc này không?". Nếu readiness thất bại, điểm cuối
   bộ điều khiển (controller) sẽ tạm thời gỡ Pod khỏi danh sách IP nhận tải của Service, nhưng
   container **không** bị restart.
2. **Liveness Probe (`/livez`):** Trả lời câu hỏi "tiến trình này còn sống và hoạt
   động bình thường không, hay đã bị deadlock hoàn toàn?". Nếu liveness thất
   bại, kubelet sẽ tiêu diệt và restart container. Tuyệt đối không kiểm tra
   database hay phụ thuộc từ xa trong liveness probe; một sự cố mạng thoáng qua
   của phụ thuộc sẽ khiến toàn bộ cluster tự restart hàng loạt (cascading
   failure).

Phần tài nguyên cũng phân định rõ ràng giữa `requests` (con số scheduler dùng
để tìm node phù hợp cho Pod) và `limits` (ngưỡng tối đa kernel cho phép; vượt CPU
sẽ bị throttle, vượt memory sẽ bị OOM killer tiêu diệt).

Để hiểu cách điều tra sự cố bằng bằng chứng thay vì suy đoán, lab cung cấp
fixture `k8s/failure-wrong-image.yaml` với tên image không tồn tại:

~~~powershell
kubectl apply -f k8s/failure-wrong-image.yaml
kubectl -n go-book rollout status `
  triển khai/probe-api --hết thời hạn (timeout)=45s
kubectl -n go-book get pods
kubectl -n go-book get events --sort-by=.lastTimestamp
kubectl -n go-book describe pod `
  -l app.kubernetes.io/name=probe-api
kubectl apply -f k8s/triển khai.yaml
kubectl -n go-book rollout status triển khai/probe-api
~~~

Lệnh `rollout status` sẽ hết thời hạn (timeout) sau 45 giây. Người mới thường vội kết luận
"Kubernetes bị treo". Nhưng khi kiểm tra `get events` và `describe pod`, control
plane cho ta bằng chứng cụ thể: `ErrImagePull` và `ImagePullBackOff`. Sau khi xác
định đúng nguyên nhân, ta khôi phục bằng cách apply lại `deployment.yaml` gốc.
Khi hoàn tất, ta dọn dẹp cluster cục bộ bằng lệnh:
`kind delete cluster --name go-book`.

### Quan sát API bằng client-go

Thay vì phụ thuộc hoàn toàn vào lệnh CLI `kubectl`, các kỹ sư Go thường cần viết
các công cụ chẩn đoán hoặc tự động hóa bằng chính ngôn ngữ Go. Thư mục
`labs/part17-container-kubernetes/client-observer` minh họa một chương trình
chẩn đoán chỉ đọc (read-only) dùng thư viện `k8s.io/client-go`.

Chương trình nạp cấu hình cluster từ kubeconfig cục bộ, gọi API `Get` để lấy
snapshot của triển khai `probe-api`, và mở một kênh `Watch` có giới hạn 15 giây
để lắng nghe các thay đổi:

~~~powershell
cd labs/part17-container-kubernetes/client-observer
go test ./...
go vet ./...
go test -race ./...
go run ./cmd/observe-triển khai `
  --namespace go-book --name probe-api
~~~

Kết quả in ra tách biệt rõ giữa trạng thái mong muốn và current observation:

~~~text
get: generation=1 observed=1 desired=1 updated=1 available=1
~~~

Chương trình này cố ý giữ phạm vi hẹp: nó không tạo, sửa hay xóa bất kỳ tài
nguyên nào. Nó minh họa sự khác biệt giữa `Generation` (số phiên bản spec mà
người dùng muốn) và `ObservedGeneration` (phiên bản spec mà bộ điều khiển (controller) đã xử lý).
Nếu hai con số này lệch nhau, hệ thống đang trong quá trình chuyển trạng thái.

@table Các lớp kiểm soát từ binary đến cluster

| Tầng kiểm soát | Nhiệm vụ chính | Bằng chứng kiểm chứng | Giới hạn không được suy diễn |
| --- | --- | --- | --- |
| Binary | Xử lý yêu cầu, signal, HTTP các cổng. | Unit/race test, JSON log. | Chưa biết môi trường filesystem hay cgroup. |
| Container | Đóng gói filesystem, user, PID 1. | `docker inspect`, exit mã nguồn. | Chạy được 1 container không đảm bảo tính sẵn sàng. |
| tải công việc | Điều phối replica, rolling update, probe. | Rollout status, Pod events. | Pod Available không chứng minh logic app không lỗi. |
| Client-go | Đọc và theo dõi trạng thái qua API. | Generation, ObservedGeneration. | Snapshot tại một thời điểm không thay thế bộ điều khiển (controller). |

**Dừng để dự đoán.** Nếu một Pod có liveness probe thành công nhưng readiness
probe thất bại, Service có chuyển tiếp yêu cầu vào Pod đó không? Kubelet có
restart Pod không? Hãy đối chiếu câu trả lời với bảng trên trước khi xem tiếp.

## Khi nào phải dùng Docker, Kubernetes và client-go thật

Khi requirement cần build/push image, chạy integration test trong container, triển khai tải công việc, đọc status cluster hoặc viết bộ điều khiển (controller), lúc đó công cụ thật là bắt buộc. Docker CLI/BuildKit và Kubernetes API đều có version, quyền và cluster policy của chúng; client-go không phải một gói tiện ích để import chỉ vì cần parse YAML. Trước khi chạm API, hãy viết rõ resource nào là source of truth, identity nào được ownership, retry có thể lặp action nào, status nào bên gọi được tin, và credential nào agent được phép dùng.

Điểm dừng của chương là một cách nhìn không còn “triển khai = chạy command”. Artefact identity, tiến trình vòng đời và trạng thái mong muốn là ba contract liên tiếp. Chương 16 cho ta signal để biết instance hiện ra sao; chương này cho ta bộ điều khiển (controller) để hiểu vì sao instance có thể bị tạo, thay hoặc rút khỏi traffic. Từ đây, phần tiếp theo có thể đi sâu hơn vào delivery pipeline, configuration, policy hay một control loop có domain thật mà không biến Dockerfile hay Kubernetes YAML thành ma thuật nền.

@references
1. Open Container Initiative. Image configuration: platform, `Entrypoint`, `Cmd`, `WorkingDir`, `User` và default execution các tham số. github.com/opencontainers/image-spec/blob/main/cấu hình.md
2. Docker Authors. Dockerfile reference: `RUN`, `CMD`, `ENTRYPOINT`, exec form và shell form. docs.docker.com/reference/dockerfile/
3. Kubernetes Authors. các bộ điều khiển (controllers): trạng thái mong muốn, current state và control loops. kubernetes.io/docs/concepts/architecture/bộ điều khiển (controller)/
4. Kubernetes Authors. Pod vòng đời: Pod spec/status, restart policy, readiness và container vòng đời. kubernetes.io/docs/concepts/workloads/pods/pod-vòng đời/
5. Kubernetes Authors. Package `client-go`: programmatic interface cho Kubernetes API. pkg.go.dev/k8s.io/client-go
6. GoogleContainerTools. Distroless: language focused docker images, non-root user và minimal runtime footprint. github.com/GoogleContainerTools/distroless
