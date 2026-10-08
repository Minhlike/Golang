# Bảng Bằng Chứng Đối Soát 50 Thư Viện (Library Atlas Evidence Ledger)

Bảng này phân định minh bạch giữa các thư viện đã được checkout mã nguồn và xác minh implementation tại commit ghim (`SEMANTIC_SOURCE_VERIFIED`) và các thư viện được xác thực danh mục định danh (`IDENTITY_VERIFIED_ONLY`).

| Rank | Thư viện | Commit ghim | Claim kỹ thuật kiểm tra | Điểm neo mã nguồn | Trạng thái (Verdict) |
|---|---|---|---|---|---|
| 01 | `k8s.io/client-go` | `2807644552` | Nếu controller lặp List toàn bộ Pod mỗi giây, nó tạo công việc tuần tự h... | `tools/cache/reflector.go, tools/cache/controller.go` | **SEMANTIC_SOURCE_VERIFIED** |
| 02 | `sigs.k8s.io/controller-runtime` | `67b72c2517` | `controller-runtime` tổ chức cache, controller và lifecycle dùng chung, ... | `pkg/controller/controller.go, pkg/internal/controller/controller.go` | **SEMANTIC_SOURCE_VERIFIED** |
| 03 | `github.com/aws/aws-sdk-go-v2` | `b189f382f4` | Một lời gọi S3 được SDK serialize, resolve endpoint, ký khi operation yê... | `aws/middleware/stack.go, aws/retry/retry.go` | **SEMANTIC_SOURCE_VERIFIED** |
| 04 | `github.com/prometheus/client_golang` | `d6087ee482` | Nhiều goroutine cập nhật cùng counter có thể tranh chấp lock và cache li... | `prometheus/registry.go, prometheus/counter.go` | **SEMANTIC_SOURCE_VERIFIED** |
| 05 | `go.opentelemetry.io/otel` | `58db4c898f` | Telemetry có overhead và cần budget. Export đồng bộ thêm thời gian chờ v... | `trace/tracer.go, sdk/trace/tracer.go` | **SEMANTIC_SOURCE_VERIFIED** |
| 06 | `go.opentelemetry.io/collector` | `0bf928af54` | Nếu SDK đo telemetry trong tiến trình, Collector là đường tiếp nhận, xử ... | `consumer/consumer.go, processor/processor.go` | IDENTITY_VERIFIED_ONLY |
| 07 | `github.com/moby/moby` | `89c5e8fd66` | Trong đường Linux container đang xét, runtime tổ chức process với namesp... | `client/container_create.go, client/hijack.go` | IDENTITY_VERIFIED_ONLY |
| 08 | `github.com/containerd/containerd/v2` | `a7fe631d96` | Nếu daemon quản lý container gặp sự cố, vòng đời của task đang chạy có b... | `client.go, core/runtime/v2/shim.go` | IDENTITY_VERIFIED_ONLY |
| 09 | `github.com/hashicorp/terraform-plugin-framework` | `c7ac25e863` | String Go có nhiều giá trị, trong đó chuỗi rỗng vẫn là giá trị hợp lệ; p... | `internal/provider/provider.go, internal/resource/resource.go` | IDENTITY_VERIFIED_ONLY |
| 10 | `helm.sh/helm/v3` | `144ca65f85` | Một thay đổi kiến trúc của Helm 3 là bỏ daemon Tiller của Helm 2. Quyền ... | `pkg/action/install.go, pkg/action/upgrade.go` | IDENTITY_VERIFIED_ONLY |
| 11 | `github.com/go-git/go-git/v5` | `3eeb238da6` | Một image `scratch` không tự mang shell, git hay C runtime; các biến thể... | `repository.go, worktree.go` | **SEMANTIC_SOURCE_VERIFIED** |
| 12 | `golang.org/x/crypto` | `3f62bf119e` | Một `ssh.Client` có thể multiplex shell, SFTP và port-forwarding trên cù... | `ssh/client.go, ssh/server.go` | IDENTITY_VERIFIED_ONLY |
| 13 | `github.com/open-policy-agent/opa` | `b2c26708e9` | Một gateway cần budget cho authorization theo SLO và concurrency của chí... | `rego/rego.go, topdown/query.go` | IDENTITY_VERIFIED_ONLY |
| 14 | `github.com/sigstore/cosign/v2` | `3e82f50a28` | Khi bạn kéo một container image `registry.internal/app:v1.2.0` về triển ... | `pkg/cosign/sign.go, pkg/cosign/verify.go` | IDENTITY_VERIFIED_ONLY |
| 15 | `google.golang.org/grpc` | `e84aa5ab15` | Xét scenario có một gRPC client duy trì connection lâu tới Service có nh... | `clientconn.go, server.go` | IDENTITY_VERIFIED_ONLY |
| 16 | `google.golang.org/protobuf` | `cdd4c5f740` | Protobuf dùng field number và wire type thay cho lặp tên field trên wire... | `proto/wire.go, reflect/protoreflect/value.go` | IDENTITY_VERIFIED_ONLY |
| 17 | `github.com/google/go-containerregistry` | `8a72a424fd` | Xét scenario chỉ cần đọc metadata hoặc tìm một file trong image lớn. `do... | `pkg/v1/remote/puller.go, pkg/v1/remote/pusher.go` | IDENTITY_VERIFIED_ONLY |
| 18 | `oras.land/oras-go/v2` | `105715ee12` | OCI Distribution quy định API trao đổi manifest và blob, trong đó digest... | `registry/remote/repository.go, content/oci/store.go` | IDENTITY_VERIFIED_ONLY |
| 19 | `github.com/containernetworking/cni` | `3f51e8803e` | Trong đường CNI thông thường của Pod không dùng hostNetwork, runtime chu... | `pkg/skel/skel.go, pkg/types/types.go` | IDENTITY_VERIFIED_ONLY |
| 20 | `github.com/cilium/ebpf` | `e55144e173` | Để quan sát syscall hay xử lý packet trong Linux, đã có nhiều cơ chế như... | `collection.go, map.go` | **SEMANTIC_SOURCE_VERIFIED** |
| 21 | `github.com/vishvananda/netlink` | `17daef607c` | Gọi ip bằng subprocess là một dependency vào executable, quoting/argumen... | `link_linux.go, route_linux.go` | IDENTITY_VERIFIED_ONLY |
| 22 | `github.com/crossplane/crossplane-runtime` | `84fc49a3e3` | Kubernetes vốn được thiết kế để điều phối container trên một cụm máy chủ... | `pkg/reconciler/managed/reconciler.go, pkg/resource/interfaces.go` | IDENTITY_VERIFIED_ONLY |
| 23 | `github.com/fluxcd/pkg/runtime` | `a1797f9a0f` | Khi một hệ thống GitOps tự động hóa triển khai phần mềm cho hàng trăm mi... | `runtime/controller/controller.go, runtime/conditions/setter.go` | IDENTITY_VERIFIED_ONLY |
| 24 | `github.com/google/go-github/v92` | `5149b4d745` | Khi viết một con bot tự động hóa GitHub Actions hoặc công cụ dọn dẹp các... | `github/github.go, github/actions_workflows.go` | **SEMANTIC_SOURCE_VERIFIED** |
| 25 | `github.com/spf13/cobra` | `88b30ab89d` | Một số CLI Go như `kubectl`, `helm`, `gh` và `hugo` dùng Cobra để tổ chứ... | `command.go, args.go` | IDENTITY_VERIFIED_ONLY |
| 26 | `github.com/spf13/viper` | `394040cacc` | 12-Factor App khuyến nghị tách cấu hình thay đổi theo deployment khỏi co... | `viper.go, flags.go` | IDENTITY_VERIFIED_ONLY |
| 27 | `github.com/fsnotify/fsnotify` | `76b01a6e8f` | Hot reload là một policy của ứng dụng, không phải tác dụng tự động của v... | `fsnotify.go, backend_windows.go` | IDENTITY_VERIFIED_ONLY |
| 28 | `go.uber.org/zap` | `5b81b37b81` | Nếu ứng dụng của bạn xử lý tải cao, việc ghi lại log trên mỗi request có... | `logger.go, zapcore/core.go` | IDENTITY_VERIFIED_ONLY |
| 29 | `go.uber.org/automaxprocs` | `1ea14c35ce` | `automaxprocs` quan trọng nhất trong bối cảnh lịch sử của các binary Go ... | `maxprocs/maxprocs.go` | IDENTITY_VERIFIED_ONLY |
| 30 | `github.com/hashicorp/go-retryablehttp` | `e1f5485fe8` | Xét scenario một client retry sau response 503 rồi dần gặp lỗi thiếu fil... | `client.go` | IDENTITY_VERIFIED_ONLY |
| 31 | `golang.org/x/sync` | `f75267d841` | Xét scenario nhiều request cùng thấy cache miss cho một key rồi cùng tru... | `errgroup/errgroup.go, semaphore/semaphore.go` | IDENTITY_VERIFIED_ONLY |
| 32 | `golang.org/x/time` | `fb013b3d30` | Một implementation token bucket minh họa có thể dùng goroutine với ticke... | `rate/rate.go` | IDENTITY_VERIFIED_ONLY |
| 33 | `github.com/hashicorp/go-plugin` | `155dcddc94` | Package `plugin` có giới hạn tương thích và platform được tài liệu hóa. ... | `client.go, server.go` | IDENTITY_VERIFIED_ONLY |
| 34 | `github.com/hashicorp/hcl/v2` | `00057cf06d` | Tại sao HashiCorp không dùng YAML hay JSON để viết cấu hình cho Terrafor... | `hclsyntax/parser.go, gohcl/decode.go` | IDENTITY_VERIFIED_ONLY |
| 35 | `github.com/hashicorp/terraform-plugin-go` | `09a1181b05` | Nếu `terraform-plugin-framework` (thư viện số 09) là giao diện cấp cao t... | `tfprotov6/server.go, tftypes/value.go` | IDENTITY_VERIFIED_ONLY |
| 36 | `github.com/prometheus/common` | `9a4aff03c1` | Một scrape workload nhiều target có thể tốn CPU ở parser. Chi phí phụ th... | `expfmt/text_parse.go, model/metric.go` | IDENTITY_VERIFIED_ONLY |
| 37 | `modernc.org/sqlite` | `c96a4e6cb2` | Driver dùng cgo cần C toolchain phù hợp khi build và có thêm allocator/l... | `driver.go` | IDENTITY_VERIFIED_ONLY |
| 38 | `go.opentelemetry.io/contrib` | `c4c6248ec2` | OpenTelemetry Go cốt lõi (mục 05) cung cấp API/SDK. Các module contrib c... | `instrumentation/net/http/otelhttp/handler.go, instrumentation/net/http/otelhttp/transport.go` | IDENTITY_VERIFIED_ONLY |
| 39 | `github.com/aquasecurity/trivy` | `e1fd17a0ea` | Trivy phát hiện package/version từ artifact rồi đối chiếu nguồn vulnerab... | `pkg/scanner/scan.go, pkg/fanal/artifact/artifact.go` | IDENTITY_VERIFIED_ONLY |
| 40 | `github.com/in-toto/in-toto-golang` | `36d782ffb2` | Trong một quy trình CI/CD hiện đại, mã nguồn trải qua nhiều bước: Lập tr... | `in_toto/in_toto.go, in_toto/model.go` | IDENTITY_VERIFIED_ONLY |
| 41 | `github.com/theupdateframework/go-tuf/v2` | `f5edbde31e` | Khi máy chủ tự động tải các bản cập nhật phần mềm hoặc chữ ký container ... | `metadata/client/client.go, metadata/trustedmetadata/trustedmetadata.go` | IDENTITY_VERIFIED_ONLY |
| 42 | `cloud.google.com/go` | `4e8373586a` | Với download lớn trên WAN, retry từ byte đầu có thể lặp nhiều công việc.... | `storage/bucket.go, storage/reader.go` | IDENTITY_VERIFIED_ONLY |
| 43 | `github.com/Azure/azure-sdk-for-go/sdk/azcore` | `d86ae78bd6` | Azure SDK for Go dùng policy pipeline để tổ chức các bước như authentica... | `sdk/azcore/arm/client.go, sdk/azcore/runtime/pipeline.go` | IDENTITY_VERIFIED_ONLY |
| 44 | `github.com/modelcontextprotocol/go-sdk` | `3f3b699b2b` | MCP định nghĩa cách client và server trao đổi tool/resource qua protocol... | `mcp/protocol.go, client/client.go` | **SEMANTIC_SOURCE_VERIFIED** |
| 45 | `github.com/google/adk-go` | `f9ce16ef9c` | ADK tổ chức model call, tool và session thành một vòng thực thi nhiều bư... | `agent.go` | IDENTITY_VERIFIED_ONLY |
| 46 | `github.com/microsoft/agent-framework-go` | `5fea526630` | Ở commit đã ghim, hãy đọc feature và giới hạn của Go implementation trướ... | `runtime.go` | IDENTITY_VERIFIED_ONLY |
| 47 | `github.com/cloudwego/eino` | `ba04fde864` | `eino` của CloudWeGo cung cấp các component và orchestration cho ứng dụn... | `compose/graph.go, schema/message.go` | IDENTITY_VERIFIED_ONLY |
| 48 | `trpc.group/trpc-go/trpc-agent-go` | `5a0030b628` | Một Agent phụ thuộc provider có thể gặp throttling, timeout hoặc lỗi tra... | `agent/agent.go, tools/tool.go` | IDENTITY_VERIFIED_ONLY |
| 49 | `github.com/kagent-dev/kagent` | `375fe73a0c` | Nếu bạn muốn trao quyền cho một AI Agent tự động điều tra nguyên nhân sự... | `pkg/agent/agent.go` | IDENTITY_VERIFIED_ONLY |
| 50 | `github.com/agentscope-ai/agentscope-go` | `8f82bd22c4` | Khi nhiều Agent cùng sửa state có pointer dùng chung, chương trình vẫn c... | `agents/agent.go, message/message.go` | IDENTITY_VERIFIED_ONLY |

## Thống kê tổng hợp
- **Tổng số thư viện trong Atlas**: 50
- **SEMANTIC_SOURCE_VERIFIED**: 9/50 (Đã checkout repo nội bộ tại `library_sources/repos/`, đối chiếu symbol và implementation trực tiếp)
- **IDENTITY_VERIFIED_ONLY**: 41/50 (Đã khóa định danh, commit, source tree sha256 và source map; chưa checkout toàn bộ cây mã nguồn local)
