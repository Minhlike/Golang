# Nguồn và giấy phép

Các chương tự viết, không chép lại nguyên văn tài liệu khác. Danh mục này ưu
tiên nguồn chính thức; URL được giữ thay vì commit bản sao tài liệu bên thứ ba.

| Nguồn | Vai trò | Giấy phép/lưu ý |
| --- | --- | --- |
| https://go.dev/ref/spec | Ngôn ngữ, package, variable, execution | Tài liệu chính thức Go |
| https://go.dev/doc/devel/release | Bản stable và release history | Tài liệu chính thức Go |
| https://go.dev/doc/go1.27 | Chi tiết thay đổi Go 1.27 | Tài liệu chính thức Go |
| https://go.dev/ref/mod | Module và dependency | Tài liệu chính thức Go |
| https://go.dev/cmd/go | Hành vi command `go` | Tài liệu chính thức Go |
| https://go.dev/doc/effective_go | Cách tổ chức và idiom | Tài liệu chính thức Go |
| https://go.dev/ref/mem | Memory model, happens-before và synchronization | Tài liệu chính thức Go |
| https://go.dev/doc/articles/race_detector | Cách dùng và giới hạn của race detector | Tài liệu chính thức Go |
| https://pkg.go.dev/sync | Cam kết đồng bộ của Mutex và WaitGroup | Tài liệu chính thức Go |
| https://pkg.go.dev/context | Hủy và deadline qua `context.Context` | Tài liệu chính thức Go |
| https://pkg.go.dev/errors | Chuỗi lỗi, `errors.Is` và `errors.As` | Tài liệu chính thức Go |
| https://pkg.go.dev/io | Contract của `Reader`, `Writer` và lifecycle I/O | Tài liệu chính thức Go |
| https://pkg.go.dev/encoding/json | Decoder/Encoder JSON theo stream | Tài liệu chính thức Go |
| https://pkg.go.dev/testing | Unit test, benchmark, `B.Loop` và allocation metric | Tài liệu chính thức Go |
| https://go.dev/doc/diagnostics | Profile, trace và giới hạn của dữ liệu chẩn đoán | Tài liệu chính thức Go |
| https://go.dev/cmd/trace | Execution trace của Go | Tài liệu chính thức Go |
| https://pkg.go.dev/net | Resolver và network boundary | Tài liệu chính thức Go |
| https://pkg.go.dev/crypto/tls | TLS config và xác minh hostname | Tài liệu chính thức Go |
| https://pkg.go.dev/net/http | HTTP client, transport, handler, server và shutdown | Tài liệu chính thức Go |
| https://pkg.go.dev/net/http/httptrace | Event trace cho outgoing HTTP request | Tài liệu chính thức Go |
| https://pkg.go.dev/net/http/httptest | Kiểm thử handler và HTTP test server | Tài liệu chính thức Go |
| https://pkg.go.dev/database/sql | `database/sql`: pool, context, transaction, `Rows` và contract driver | Tài liệu chính thức Go |
| https://www.sqlite.org/lang_transaction.html | Atomicity và lifecycle transaction của SQLite trong lab cục bộ | Tài liệu chính thức SQLite |
| https://pkg.go.dev/modernc.org/sqlite | Driver SQLite thuần Go dùng riêng cho lab transaction cục bộ | Xem license/version tại module; không phải production recommendation mặc định |
| https://go.dev/doc/security/best-practices | Thực hành bảo mật chung trong Go | Tài liệu chính thức Go |
| https://github.com/plantuml/plantuml/releases | PlantUML renderer | MIT/GPL dual license - xem release khi phân phối |

Khi cần đưa tài liệu tải về `references/`, chỉ thêm tài liệu được phép phân
phối và ghi rõ nguồn, phiên bản, license. Không đưa sách thương mại hay secret
vào repository.

## Đối chiếu content ngày 01-10-2026

| Nguồn chính thức / gốc | Claim được dùng và giới hạn |
| --- | --- |
| https://docs.aws.amazon.com/service-authorization/latest/reference/list_ecr.html | Resource scope theo từng action ECR; không suy thành luật wildcard toàn AWS. |
| https://kubernetes.io/docs/concepts/workloads/pods/probes/ | Failure threshold, readiness và liveness; policy probe không thay outcome người dùng. |
| https://kubernetes.io/docs/concepts/storage/persistent-volumes/ | RWO giới hạn node, không tự giới hạn một Pod. |
| https://www.sqlite.org/useovernet.html | Rủi ro filesystem locking khi dùng qua network; nhiều process không tự đồng nghĩa mất nhất quán. |
| https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api | Rate limit theo identity/endpoint; header thực tế và ngoại lệ. |
| https://docs.kernel.org/bpf/verifier.html | Kiểm tra chương trình trước khi nạp; không phải kiểm định từng record hay bảo đảm mọi overhead. |
| https://theupdateframework.github.io/specification/latest/ | Snapshot/timestamp roles, version và expiration; không kiểm kê mọi file hay chứng thực giờ server. |
| https://arxiv.org/html/2302.06590v1 | Peng et al.: 95 người phân nhóm, 70 completer; task JavaScript năm 2022, không thị trường việc làm. |
| https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf | 16 contributor, task-level randomization, 246 task và ước lượng thời gian có điều chỉnh; ingestion cache chỉ hỗ trợ đọc. |
| https://metr.org/blog/2026-02-24-uplift-update/ | Selection/time measurement làm kết quả mới khó diễn giải; xác nhận interval 2025, không quy thành luật Agent 2026. |
| https://go.dev/blog/survey2025 | 5.379 phản hồi sau làm sạch, thời gian/method/geography/use case; survey tự báo cáo, không RCT hay thống kê tuyển dụng. |
| https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm | Dự báo nhóm nghề tại Mỹ 2025–2035; không Go/SRE/Việt Nam. |
| https://dora.dev/research/2025/dora-report/ | Framing trên trang công bố, affiliation Google Cloud/industry; không đưa số survey từ báo cáo chưa đọc. |

Source ghim của Go 1.27.1 và thư viện được dùng khi diễn giải implementation, không dùng source map sinh sẵn làm bằng chứng API. Log compiler, benchmark và local gates nằm trong workspace QA; chúng có phạm vi tái lập riêng, không là chứng minh production.
