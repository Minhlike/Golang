# Coverage sau Ch28 — bản đồ hiện hành và câu hỏi lịch sử

Đối chiếu manuscript ngày 01-10-2026: Ch29 đã có, dạy phân biệt dữ liệu nghiên cứu, survey, dự báo và suy luận của tác giả; nối proposal, evidence, authority và postcondition bằng lab local. Không có tranche Ch29–32 đang chờ tự động viết. Bản đồ chương hiện tại nằm ở `book/README.md`; Error Atlas vẫn sau Library Atlas và là nội dung cuối sách.

## Coverage đã có trong source

Ch21–23 dạy reconciliation, keyed queue, stale cache, optimistic concurrency, ownership và finalizer. Ch24–26 dạy cloud API, credential, retry, delivery, artifact identity và các ranh giới kiểm chứng supply chain. Ch27–28 dạy điểm quan sát kernel và policy cho tool Agent. Ch29 tổng hợp quyền hành động và chi phí kiểm chứng; không dự báo riêng việc làm Go/SRE tại Việt Nam.

Các chương này không chứng minh live deployment hay mọi thư viện production. Inventory library khóa 50 identity và cung cấp đường đọc có mục tiêu, không phải full-tree review của 50 implementation. Claim có version phải đối chiếu source/contract thực; QA lịch sử không tự áp cho bản build mới.

## Câu hỏi để cân nhắc nếu người dùng yêu cầu mở rộng

| Hướng | Câu hỏi trước authoring | Không được mặc định |
| --- | --- | --- |
| Consensus | Workload nào cần linearizability, membership và recovery? Test partition có oracle gì? | Một toy Raft hay vài lịch fault injection không chứng minh mọi lịch chạy. |
| XDP/TC | Hook, driver, kernel, packet size và throughput đo ra sao? | Không có hàng triệu packet/giây chung cho mọi host hoặc hook. |
| Wasm/plugin | Host import, memory, deadline, identity và quyền I/O bị giới hạn thế nào? | Không có sandbox an toàn tuyệt đối; tránh cgo còn tùy runtime/target. |
| Chaos/recovery | Fault nào được phép, blast radius, owner dừng thử và postcondition là gì? | Inject được một lỗi không chứng minh resilience hay SLO ở mọi failure. |

Đây là câu hỏi nghiên cứu, không cam kết chương mới và không phải các năng lực đã hoàn tất. Chỉ mở rộng khi gap matrix của nhiệm vụ được phép chứng minh learning value vượt duplication và maintenance cost.
