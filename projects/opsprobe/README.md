# opsprobe

`opsprobe` sẽ là công cụ kiểm tra health của dependency cho một nhóm vận hành.
Nó không tạo request giả để “trông như microservice”; mỗi giai đoạn thêm một
năng lực có lý do vận hành.

| Giai đoạn | Năng lực | Kiến thức nối vào |
| --- | --- | --- |
| 1 | CLI kiểm tra một URL, exit code rõ | package, error, `net/http` |
| 2 | File config và nhiều target | I/O, JSON/YAML có chủ đích, testing |
| 3 | Concurrency bị chặn | context, worker pool, backpressure |
| 4 | Metrics, log, trace | observability và incident response |
| 5 | Container/Kubernetes/AWS | delivery, API, IAM, cost guardrail |

Chưa có code production ở đây. Đưa cả hệ thống vào từ chương đầu sẽ che mất
những quyết định mà người học cần tự làm. Khi bắt đầu implementation, mọi call
ra network sẽ có timeout/cancellation; lab cloud chỉ chạy sau khi có xác nhận
về chi phí và credential tối thiểu.

