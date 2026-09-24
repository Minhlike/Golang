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

21. **Vòng lặp điều hòa và Controller Pattern.** Từ quan sát thụ động sang tự điều hòa chủ động; level-triggered vs edge-triggered; thiết kế rate-limited deduplicating workqueue bằng Go; kiểm soát giãn cách lũy thừa (exponential backoff) ngăn bão retry; tính lũy thừa (idempotency) và tắt nguồn mềm mại cho controller.

## Phụ lục (Luôn nằm ở cuối sách)

- **Phụ lục A — Atlas Lỗi Go: Đọc lỗi từ triệu chứng đến nguyên nhân.** Bản đồ phản xạ 10 nhóm (A–J) từ Compiler & Type System, Runtime & Panic, Error Values & I/O, Context & Cancellation, Filesystem & Process, Network / HTTP / TLS, Database, Concurrency, Modules & Toolchain, đến Container, Kubernetes & CI/CD. Bố cục 2 cột cô đọng, tối ưu in laser và tra cứu tức thì tại bàn làm việc. Quy ước cấu trúc: mọi chương mới (Chương 22 trở đi) đều được tự động xếp vào trước phần Phụ lục; Phụ lục A luôn là trang cuối cùng của sách.

## Cách dùng bản hiện tại

Bản PDF đã hoàn thành **Phần I** đến **Chương 21** và **Phụ lục A — Atlas Lỗi Go** (tổng cộng 238 trang). Chương 7 dùng chương trình tái hiện tối thiểu về ranh giới stream và vòng đời tài nguyên; Chương 8 đi từ race report đến chứng minh thứ tự với `Mutex` và `WaitGroup`; Chương 9 xây worker pool nhỏ từ contract về ownership, áp suất và cancellation. Chương 10 đặt benchmark, profile và trace vào một vòng điều tra có thể bác bỏ giả thuyết; Chương 11 lần theo một HTTP request theo các chặng có thể xảy ra và kiểm tra recorder trace an toàn khi hook chồng lên nhau; Chương 12 biến handler và shutdown thành một lifecycle có thể vận hành; Chương 13 khóa transaction boundary trên SQLite; Chương 14 dùng reflection để kiểm tra runtime shape mà không phá visibility hay lạm dụng `unsafe`; Chương 15 bắt đầu một incident command từ contract process, deadline, output và exit status; Chương 16 nối outcome thành structured logs, Prometheus metrics và OpenTelemetry traces trên một HTTP service thật; Chương 17 đóng gói service vào container distroless non-root, khai báo desired state trong Kubernetes và quan sát API bằng client-go; Chương 18 hiện thực hóa chuỗi delivery với GitHub Actions bảo mật, promotion gate bằng Go fail-closed và cầu nối AWS OIDC Terraform không lưu credential dài hạn; Chương 19 giữ type information qua generic contract, interface runtime semantics và typed-nil; Chương 20 hoàn tất toàn bộ dự án capstone `opsprobe` từ mã nguồn đến quy trình vận hành và ứng cứu sự cố; Chương 21 nâng tầm hệ thống lên năng lực tự điều hòa qua controller pattern, workqueue có kiểm soát tốc độ và tính lũy thừa; Phụ lục A khép lại cuốn sách với 78 mục chẩn đoán lỗi thực tế trải khắp 10 nhóm phân loại theo nguyên tắc Grayscale-first.
