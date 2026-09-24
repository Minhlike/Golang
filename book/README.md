# Bản đồ cuốn sách

Đây là một cuốn sách đi từ việc **đọc được một tệp Go** đến việc thiết kế, đo đạc và vận hành phần mềm. Mỗi chương là một chuyển dịch đáng kể trong cách nghĩ, không phải một từ khoá hay một API bị tách riêng.

## Phần I — Đọc và viết Go có chủ đích

1. **Một chương trình Go, đọc từ ngoài vào trong.** Tệp nguồn, package, import, tên, literal, khai báo, biểu thức, câu lệnh, block, kiểu, hàm, điều khiển luồng và cách compiler ghép chúng thành một chương trình.
2. **Giá trị di chuyển qua chương trình.** Biến, const, assignment, conversion, hàm, return, zero value, array, slice, string và điểm mà hai biến bắt đầu dùng chung dữ liệu.
3. **Mô hình dữ liệu và ownership.** Struct, map, pointer, method, interface, composition và cách chọn API nhỏ dễ đổi.

## Phần II — Làm cho code sửa được và tin được

4. **Biên lỗi.** Error, wrapping, cancellation, defer, panic/recover và quyết định lỗi nào phải đi qua ranh giới nào.
5. **Thiết kế package.** Module, import graph, internal, configuration, documentation và dependency mà một người đọc có thể lần theo.
6. **Thay đổi không sợ hãi.** Một đoạn code khó test được refactor dần sang unit test, fake, fuzz, race detector, benchmark và contract test.
7. **Dữ liệu đi vào và đi ra.** Stream, resource lifetime, filesystem, JSON/CSV, time, context và các lựa chọn khiến một chương trình I/O không tự treo.

## Phần III — Nhiều việc cùng lúc, nhưng không mất kiểm soát

8. **Một race bắt đầu từ đâu.** Các access chung không có thứ tự an toàn, bốn tầng bằng chứng, và cách đọc race report trước khi nói về API đồng thời.
9. **Dòng công việc có áp suất.** Channel, select, ownership, cancellation, backpressure, worker pool và leak.
10. **Khi chương trình chậm hoặc phình.** Benchmark, pprof, trace, allocation, escape, GC, G/M/P, syscall và cách đo trước khi tối ưu.

## Phần IV — Giao tiếp, dữ liệu và dịch vụ

11. **Một request thực sự đi đâu.** DNS, TCP, TLS, HTTP, connection reuse, retry, timeout và trace của client.
12. **Một service sống và tắt thế nào.** HTTP server, routing, middleware, validation, shutdown, log và security boundary.
13. **Dữ liệu có trạng thái.** Một thao tác nhiều bước chỉ có ý nghĩa khi state sau cùng kể được một câu chuyện nhất quán; bắt đầu bằng transaction, rồi đi tới pool, migration, cache, serialization và consistency.
14. **Khi kiểu trở thành dữ liệu.** Reflection, unsafe, memory layout và các giới hạn cần được chứng minh trước khi vượt qua.

## Phần V — Go trong vận hành

15. **Từ incident đến công cụ.** CLI, process, signal, os/exec, cấu hình và log; xây công cụ chẩn đoán cho một sự cố mô phỏng.
16. **Thấy được hệ thống.** Health check, metrics, tracing, SLI/SLO và điều tra sự cố bằng dữ liệu thay vì suy đoán; stage hai với Prometheus và OpenTelemetry.
17. **Đóng gói và điều phối.** OCI/Docker, Kubernetes API, controller, reconciliation và ranh giới vận hành; stage hai với containerization, cluster manifests và client-go.
18. **Đưa thay đổi ra production.** CI/CD, supply-chain security, IAM tối thiểu, cost guardrail, rollback và case study cuối sách; stage hai với delivery pipeline, promotion gate và AWS OIDC bridge.

## Phần VI — Abstraction giữ được thông tin

19. **Giữ type information khi abstraction lớn lên.** Generics, constraint, generic method của Go 1.27, interface runtime semantics, type assertion, type switch và typed-nil.

## Phần VII — Dự án tổng kết

20. **Dự án tổng kết: opsprobe từ mã nguồn đến vận hành.** Xây dựng hoàn chỉnh hệ thống `opsprobe` kết nối toàn bộ kiến thức: domain logic, worker pool bị chặn, transaction nguyên tử SQLite, telemetry Prometheus và OpenTelemetry, HTTP API có backpressure, container distroless non-root, và bài tập chẩn đoán sự cố rò rỉ socket TCP được chứng minh bằng thực nghiệm.

## Phần VIII — Hệ thống Tự trị và Điều hòa

21. **Vòng lặp điều hòa và Controller Pattern.** Từ quan sát thụ động sang tự điều hòa chủ động; level-triggered vs edge-triggered; thiết kế rate-limited deduplicating workqueue bằng Go; kiểm soát giãn cách lũy thừa (exponential backoff) ngăn bão retry; tính lũy đẳng (idempotency) và tắt nguồn mềm mại cho controller.

## Phần IX — Điều phối Nâng cao, Hạ tầng Cloud & Tự động hóa Thông minh (Roadmap đang triển khai)

22. **Từ watch đến một controller Kubernetes thật.** API server là authoritative state; List/Watch; resourceVersion; Reflector và Informer; event handler và cache sync; typed rate-limited workqueue của client-go; optimistic concurrency; retry và conflict resolution.
23. **Từ controller đến operator: API riêng và vòng đời tài nguyên.** Custom Resource Definition (CRD); spec vs status; controller-runtime Scheme và Manager; Reconcile request; owner references và garbage collection; finalizer idempotency.
24. **Tự động hóa AWS bằng Go mà không biến credential thành bí mật dài hạn.** AWS SDK for Go v2; credential provider chain; temporary tokens và IAM roles; Smithy middleware stack; SigV4 signing; typed service errors; retry budget và pagination.
25. **Git và GitHub dưới góc nhìn của một hệ thống tự động hóa.** Local Git state (go-git) vs GitHub hosted state (go-github); Webhook HMAC signature verification; delivery ID deduplication; primary và secondary rate-limiting; exponential backoff.
26. **Chuỗi cung ứng phần mềm có thể kiểm chứng.** Go module dependency graph và go.sum; govulncheck symbol reachability; immutable OCI digests; keyless signing với Cosign; provenance và attestation; fail-closed admission policy gate.
27. **Quan sát Linux từ kernel bằng eBPF và Go.** eBPF verifier và ranh giới kernel/userspace; bpf2go code generation; BPF maps và ring buffers; nạp và quản lý vòng đời eBPF bằng cilium/ebpf; quan sát process exec tracepoints.
28. **MCP và AIOps bằng Go: trao công cụ cho Agent mà không trao toàn quyền.** Model Context Protocol (MCP) Go SDK; stdio transport; schema-validated tool definitions; least privilege và ranh giới authorization; phòng chống SSRF; audit trail cho các hành động vận hành.

## Back Matter & Phụ lục (Luôn nằm ở cuối sách)

- **Back Matter — Atlas Mã Nguồn 50 Thư Viện Go DevOps & Cloud.** Mổ xẻ trực tiếp kiến trúc mã nguồn của 50 thư viện Go tiêu biểu trong hệ sinh thái Cloud Native/DevOps tại các commit đã khóa hash bất biến (Zero-Guess Protocol). Luôn nằm ngay sau chương kỹ thuật cuối cùng và trước Error Atlas.
- **Phụ lục A — Atlas Lỗi Go: Đọc lỗi từ triệu chứng đến nguyên nhân.** Bản đồ phản xạ 10 nhóm (A–J) từ Compiler & Type System, Runtime & Panic, Error Values & I/O, Context & Cancellation, Filesystem & Process, Network / HTTP / TLS, Database, Concurrency, Modules & Toolchain, đến Container, Kubernetes & CI/CD. Bố cục 2 cột cô đọng, tối ưu in laser và tra cứu tức thì. Quy ước bất biến: Phụ lục A luôn là tài liệu CUỐI CÙNG của cuốn sách bất kể có thêm bao nhiêu chương mới.

## Cách dùng bản hiện tại

Bản PDF hiện tại bao gồm đầy đủ Front Matter, Mục lục động, toàn bộ các chương kỹ thuật từ Chương 00 đến Chương 27, Back Matter 50 Thư viện Go DevOps & Cloud, và Phụ lục A — Atlas Lỗi Go (được biên dịch print-ready tự động qua `scripts/build_pdf.py` với fatal code-width preflight). Chương tiếp theo (Chương 28) thuộc lộ trình khóa đã định (`FORWARD ROADMAP LOCK`) đang được viết và kiểm thử tuần tự theo tiêu chuẩn nghiêm ngặt của Living Textbook.
