# Bản đồ cuốn sách

Cuốn sách đi từ ngôn ngữ, qua thiết kế phần mềm và hệ thống, đến các công cụ
DevOps/SRE. Thứ tự này có chủ ý: không thể debug timeout HTTP, goroutine leak
hay controller Kubernetes một cách đáng tin nếu chưa hiểu ownership dữ liệu,
error và cancellation.

## Phần I - Nền móng để tự viết Go

1. Go, toolchain và vòng lặp học có thể kiểm chứng.
2. Một chương trình Go: package, module, `go run`, `go build` và lỗi biên dịch.
3. Giá trị, kiểu, điều khiển luồng và tư duy zero value.
4. Hàm, `defer`, lỗi, `panic` và `recover`.
5. Array, slice, string, rune, UTF-8 và aliasing.
6. Map, struct, pointer, value semantics và API nhỏ.

## Phần II - Tổ chức code để sửa được

7. Method, interface, embedding và composition.
8. Error design: wrapping, `errors.Is`, `errors.As` và boundary lỗi.
9. Generics: constraint, `~`, `comparable`, và lúc không dùng.
10. Package design, modules, `internal/`, config và documentation.
11. Testing, table-driven tests, fakes, fuzzing, benchmark và race detector.
12. I/O, filesystem, JSON, CSV, time, streaming và `context`.

## Phần III - Đồng thời và runtime

13. Concurrency, parallelism, goroutine và scheduler - mô hình trước, API sau.
14. Channel, `select`, ownership, cancellation và backpressure.
15. Mutex, atomic, memory model, data race, deadlock và leak.
16. Pipeline, fan-in/fan-out, worker pool và bounded concurrency.
17. Stack, heap, escape analysis, GC, G/M/P, syscall và network poller.
18. Profiling, trace, benchmark methodology và tối ưu dựa trên số đo.

## Phần IV - Dịch vụ và dữ liệu

19. TCP, UDP, DNS, socket và những phần Linux cần để đọc network code.
20. HTTP client: timeout, reuse connection, TLS, retry và cancellation.
21. HTTP server: routing tối giản, middleware, shutdown và security boundary.
22. Database: `database/sql`, pool, transaction, migration và PostgreSQL.
23. Persistence, cache, serialization và consistency ở mức lập trình viên.
24. Reflection, `unsafe`, memory layout và các giới hạn không nên vượt qua.

## Phần V - Go cho DevOps/SRE

25. CLI và filesystem automation.
26. Process, signal, `os/exec`, pipe, log và kiểm soát concurrency.
27. API automation, health check, structured log và configuration.
28. Prometheus metrics, OpenTelemetry, tracing và điều tra sự cố.
29. Docker, OCI và đóng gói một service Go.
30. Kubernetes API, client-go, controller và reconciliation loop.
31. AWS SDK v2, IAM tối thiểu, cost guardrail và cleanup.
32. CI/CD, supply-chain security, reliability, profiling và case study.

`opsprobe` là dự án xuyên suốt. Nó bắt đầu bằng CLI kiểm tra endpoint, sau đó
nhận cấu hình, chạy kiểm tra đồng thời có giới hạn, xuất metrics và trace, rồi
được đóng gói cho container/Kubernetes/AWS. Dự án không phải CRUD đội lốt: nó
có lý do tồn tại là giúp một nhóm vận hành phát hiện dependency bị suy giảm
trước khi người dùng báo lỗi.

## Ý đồ sư phạm, không phải template chương

Sách không có một khuôn bắt buộc kiểu mở bài, định nghĩa, ví dụ, bài tập, đáp
án, tổng kết. Trước mỗi chương, tác giả phải xác định người học cần đổi trực
giác nào, ngộ nhận nào cần bị phá vỡ, và kỹ năng hay bằng chứng nào cho thấy
anh đã hiểu. Hình thức được chọn theo mục tiêu đó, không theo sự tiện lợi khi
viết.

Vì vậy, syntax có thể đi từ một ví dụ rồi rút quy luật; slice, pointer và memory
model có thể mở bằng tình huống bất ngờ rồi truy dấu dữ liệu; concurrency bắt
đầu từ race hoặc deadlock; network từ sequence diagram hay trace; performance
từ số đo; DevOps/SRE từ incident mô phỏng và công cụ được xây dần. Case study,
guided investigation, debugging session, code review, failure analysis và
mini-project đều là hình thức hợp lệ khi chúng dạy tốt hơn văn xuôi tuyến tính.

Một chương chỉ có exercise, recap, diagram, checklist hoặc đáp án khi chúng tạo
ra giá trị học tập cụ thể. Chương 5 sẽ mở bằng cuộc điều tra về slice aliasing,
không lặp lại trình tự của các chương trước.
