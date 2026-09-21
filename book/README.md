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
9. **Dòng công việc có áp suất.** Channel, select, ownership, timeout, cancellation, backpressure, worker pool và leak.
10. **Khi chương trình chậm hoặc phình.** Benchmark, pprof, trace, allocation, escape, GC, G/M/P, syscall và cách đo trước khi tối ưu.

## Phần IV — Giao tiếp, dữ liệu và dịch vụ

11. **Một request thực sự đi đâu.** DNS, TCP, TLS, HTTP, connection reuse, retry, timeout và trace của client.
12. **Một service sống và tắt thế nào.** HTTP server, routing, middleware, validation, shutdown, log và security boundary.
13. **Dữ liệu có trạng thái.** database/sql, pool, transaction, migration, cache, serialization và consistency mà lập trình viên phải thấy.
14. **Góc khuất của ngôn ngữ.** Reflection, unsafe, memory layout và các giới hạn cần được chứng minh trước khi vượt qua.

## Phần V — Go trong vận hành

15. **Từ incident đến công cụ.** CLI, process, signal, os/exec, cấu hình và log; xây công cụ chẩn đoán cho một sự cố mô phỏng.
16. **Thấy được hệ thống.** Health check, metrics, tracing, SLI/SLO và điều tra sự cố bằng dữ liệu thay vì suy đoán.
17. **Đóng gói và điều phối.** OCI/Docker, Kubernetes API, controller, reconciliation và ranh giới vận hành.
18. **Đưa thay đổi ra production.** CI/CD, supply-chain security, IAM tối thiểu, cost guardrail, rollback và case study cuối sách.

`opsprobe` là dự án xuyên suốt, nhưng không bị ép vào mọi trang. Nó chỉ xuất hiện khi một kiến thức cần được đặt vào áp lực của hệ thống thật: đầu tiên là một CLI đọc được endpoint; sau đó là kiểm tra có giới hạn đồng thời, dữ liệu quan sát được, và cuối cùng là một artefact có thể vận hành.

## Cách dùng bản hiện tại

Bản PDF đã hoàn thành **Phần I** và **Chương 6**. Chapter 7 mở bằng một chương trình tái hiện tối thiểu về ranh giới stream và vòng đời tài nguyên; Chương 8 bắt đầu bằng failure analysis về race. `opsprobe` chỉ nhận I/O mới khi có requirement vận hành thật.
