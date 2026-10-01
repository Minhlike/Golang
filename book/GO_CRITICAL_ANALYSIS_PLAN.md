# Câu hỏi phản biện và hợp đồng bằng chứng

Đây là hồ sơ câu hỏi nghiên cứu, không phải nguồn bảo chứng cho manuscript. Bảng cũ là kế hoạch của giai đoạn foundation rewrite; các ngưỡng latency, throughput, cgo overhead và so sánh ngôn ngữ chưa có phép đo được gỡ khỏi hồ sơ này. Chương hiện hành đã dạy nhiều boundary bên dưới; “cần đo” không có nghĩa chương đó chưa được viết.

## Trạng thái được phép dùng

`QUESTION` là câu hỏi chưa có kết luận; `HYPOTHESIS_TO_TEST` là giả thuyết có cách bác bỏ; `MEASUREMENT_REQUIRED` yêu cầu workload và phép đo trước khi kết luận về chi phí. `OFFICIAL_CLAIM_WITH_SOURCE` giữ đúng phạm vi lời công bố chính thức, không biến nó thành phép đo của sách. `VERIFIED_AT_PINNED_VERSION` chỉ dùng cho claim cụ thể đã đối chiếu source hoặc thí nghiệm ở version/target ghi rõ. Không dùng một nhãn VERIFIED chung để suy tất cả nhận định trong hàng đều đúng.

| Chủ đề và vị trí hiện hành | Câu hỏi cần trả lời | Bằng chứng và phép thử cần có | Trạng thái của câu hỏi chi phí |
| --- | --- | --- | --- |
| GC, Ch10/Ch17 | Với workload này, pause, mark assist, live heap và CPU GC ảnh hưởng latency ra sao? | GC Guide cho mô hình; `runtime/mgc.go`, `mgcpacer.go` và đường Green Tea của Go 1.27.1 cho implementation; profile/trace và phân phối latency của workload đã pin cho chi phí. Không có ngưỡng STW phổ quát. | MEASUREMENT_REQUIRED |
| Goroutine và stack, Ch09/Ch20 | Bao nhiêu bộ nhớ bị giữ khi tăng số goroutine và độ sâu lời gọi? | `runtime/stack.go` phân biệt `stackMin`, phần theo OS và allocation làm tròn; `proc.go` cho đường khởi tạo. Đo stack, object bị giữ và tài nguyên downstream, không lấy một constant làm tổng chi phí goroutine. | MEASUREMENT_REQUIRED |
| Preemption, Ch09/Ch20 | Đường CPU-bound hay native call nào làm một công việc khác chờ lâu? | `runtime/preempt.go`, backend theo OS/arch và trace của source/cờ build cụ thể. Release note về một khả năng không chứng minh mọi vòng lặp đều có bounded response time. | QUESTION |
| Channel, mutex và atomic, Ch08/Ch09 | Cơ chế nào giữ đúng invariant với proof và ownership dễ kiểm tra nhất? Nếu có pressure, chi phí của contract tương đương ra sao? | Memory Model và API `sync`, `sync/atomic` trước; source `runtime/chan.go` chỉ cho implementation. So benchmark khi hai phương án cùng giữ semantics; không đặt ngưỡng ops/s hay bảng thắng-thua chung. | QUESTION |
| Interface, Ch03/Ch14/Ch19 | Concrete value có escape không; call có còn gián tiếp trong artifact này không? | Compiler diagnostic, assembly và allocation benchmark của đúng source/target; `runtime/runtime2.go` và `iface.go` cho representation/conversion. Không suy boxing thành heap allocation, hoặc indirect call thành vô hiệu hóa branch predictor. | MEASUREMENT_REQUIRED |
| Zero value, Ch01/Ch03 | Miền nghiệp vụ có cần phân biệt absent với zero không? | Spec về initialization cho ngữ nghĩa Go thông thường; contract/parser test cho dữ liệu ngoài. Có thể dùng bool hiện diện, wrapper hay pointer tùy domain; pointer không tự buộc heap allocation. | QUESTION |
| Error boundary, Ch04/Ch06 | Failure nào cần identity, context và cleanup policy nào bảo toàn bằng chứng? | API `errors`, `fmt`, `context`; test failure state và code review. Pprof không đo độ dễ đọc hay tỷ lệ nhánh source để kết luận error handling tốt/xấu. | QUESTION |
| Compiler và PGO, Ch01/Ch10 | Artifact có tối ưu nào, và tối ưu ấy có ích với workload cần phục vụ không? | Source `cmd/compile/internal/ssa`, diagnostic/objdump cùng artifact, PGO docs và profile đại diện. Nếu so toolchain/ngôn ngữ, phải giữ workload, output contract, environment và metric tương đương; chưa có phần trăm chênh lệch chung. | MEASUREMENT_REQUIRED |
| cgo, Ch14 | Payload, lifetime, allocator và deployment nào khiến boundary C có ích hoặc đắt? | `cmd/cgo` pointer contract và `runtime/cgocall.go` đã pin; đo crossing cộng công việc thật, xác minh toolchain/native dependencies. Không có số ns/call hay tần suất đổi ngôn ngữ phổ quát; FFI của ngôn ngữ khác cũng cần đánh giá riêng. | MEASUREMENT_REQUIRED |
| Allocator và RSS, Ch10/Ch17/Ch20 | Heap metrics, address space, RSS và cgroup charge đang khác nhau vì điều gì? | `malloc.go`, `mheap.go`, `mpagealloc.go`, `mgcscavenge.go`, runtime metrics và OS/cgroup observation. Đo sau workload và thời điểm GC/scavenge cụ thể; không hứa heap giảm thì RSS giảm tương ứng hay tránh OOM. | MEASUREMENT_REQUIRED |

## Điều kiện đưa một kết luận vào sách

Một phép đo cần source identity, version, OS/arch, workload, cấu hình liên quan, command, metric, kết quả và limitation. Một đối chiếu source cần symbol/path và version, không chỉ tên thư mục. Một claim API cần tài liệu contract; source của một implementation không nâng nó thành luật ngôn ngữ. Kết quả kiểm thử chỉ được dùng cho assertion và đường chạy đã thực thi.

Trước khi viết thêm, đối chiếu mục hiện hành trong manuscript và lab tương ứng. Nếu boundary đã được dạy đủ, giữ nguyên; nếu chỉ thiếu liên kết giữa các ý, thêm cross-reference thay vì tạo một survey mới. Hồ sơ này không yêu cầu một wave hay chương tiếp theo và không cấp quyền đưa giả thuyết chưa đo vào prose như fact.
