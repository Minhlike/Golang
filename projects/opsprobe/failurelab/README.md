# Người nhận rời đi giữa lúc dependency chậm

Đây là reproducer cạnh capstone, không thay `Pool`, HTTP API hay telemetry cũ.
Đọc các contract test trước khi mở `runner.go`. Runner dùng `ProbeSingle` thật,
HTTP loopback và chính `telemetry.New` của dự án (slog/Prometheus/OTel console).

## Dự đoán trước khi sửa

Giữ hai HTTP request tại barrier; cho hai job nữa vào queue capacity 2, rồi
nộp 100 job. Đáp án phải là 4 accepted, 100 rejected, peak running ≤2, peak
queue ≤2. Không spawn một goroutine cho mỗi submission. Release, consume và
join phải đưa running/queue về 0.

Consumer không đọc result nữa: một send không nghe cancellation sẽ giữ worker
dù request HTTP đã hoàn tất. Checkpoint trước send loại bỏ giả định “chắc
worker đã chạy tới đó”. `Done` chỉ đóng sau worker return; hủy context không
tự giết code. Mutant có rescue channel do test sở hữu, luôn được release và
join trong cleanup, kể cả khi assertion đỏ.

```powershell
# Từ projects/opsprobe
go test -count=1 -v ./failurelab
go test -race -count=1 ./failurelab
go vet ./failurelab
$env:RELIABILITY_MUTANT='uncancellable_send'
go test -count=1 -run '^TestConsumerStopsContract$' ./failurelab
Remove-Item Env:RELIABILITY_MUTANT
```

Mutant phải exit 1 với `contract: cancellation must release result handoff`.
Không biến lỗi compile hay test timeout toàn process thành bằng chứng ấy.

## Fault → bằng chứng → kết luận hẹp

| Fault/triệu chứng | Bằng chứng phân biệt | Bản sửa/contract |
| --- | --- | --- |
| Dependency chậm | Barrier handler xác nhận request tới nơi, release mới hoàn tất | Deadline tính từ admission, gồm queue; không cấp lại budget lúc dequeue |
| HTTP 503 | Status/outcome, log, histogram sample và span | Failure, không gọi healthy hay tự retry |
| Header 200, body bị cắt | `Content-Length=100` nhưng chỉ trả `short`; drain error | Phải là failure dù status 200 |
| Connection đóng | Server hijack rồi close trước header | Failure transport, không coi response rỗng là success |
| Queue đầy | Worker đang giữ tại dependency và len(queue)=capacity | `ErrFull`, hữu hạn worker+queue, không goroutine-per-job |
| Consumer bỏ output | Probe xong; worker ở send checkpoint | Cancel + join, send nghe context; drop bàn giao chưa hoàn tất |
| Caller hủy nhưng downstream còn sống | Runner Done trước khi handler riêng được release | Không đồng nhất client return với downstream kết thúc |

Barriers thay sleep trong assertions. Real deadline là fault được chờ; 5 giây
trong helper chỉ là guard liveness. Test expired queue inject timestamp đã
hết budget, không chờ một khoảng tùy ý để “hy vọng” job đủ cũ. Tất cả server,
client idle connections, worker và exporter đều có owner/cleanup.

`failurelab_running` đếm probe đang chạy; queue gauge đếm job chưa nhận, không
đếm result chưa giao. `Dropped` đếm accepted job bị bỏ trước execution khi
cancel; pending payload được drain trước Done. `Completed` tính probe xong,
không hứa consumer đã nhận result. Một registry/runner cho mỗi experiment;
không reuse registry để đăng ký trùng collector. Constructor failure không
được unregister collector của experiment khác.

## Phép chạy tải hữu hạn, không phải threshold hiệu năng

```powershell
$env:RUN_BOUNDED_LOAD='1'
go test -count=1 -run '^TestBoundedWorkloadObservation$' `
  -v ./failurelab
Remove-Item Env:RUN_BOUNDED_LOAD
```

64 attempts, worker 4, queue 16, budget từ admission 500 ms, timeout probe
100 ms, deadline tổng 10 giây. In completed/elapsed throughput, p50/p95 probe
duration theo nearest-rank của các result nhận được, outcome counts (chia
completed để tính error/timeout rate), accepted/rejected/dropped và peak bounds,
goroutine, HeapAlloc/TotalAlloc. Rejection rate dùng tổng 64 attempts. Đây là
sample hữu hạn của máy, không đặt assertion throughput hay latency phổ quát.

Histogram `failurelab_job_seconds` gồm queue delay, probe histogram và p50/p95
không gồm queue. Heap snapshot chưa chuẩn hóa sau GC, goroutine còn có HTTP
transport/exporter; chúng không tự chứng minh leak. Dùng lab retention Ch10
để tìm ownership sống thừa. Với CPU thấp/latency cao, trích `net`/`sched`/`sync`
profile của runtime trace để phân biệt I/O wait và runnable delay; test fault
không phải phép đo scheduler hay RSS. Không đo nguồn nào thì không kết luận
nguồn ấy.

Output thực nằm trong [verification](../../../book/evidence/reliability-failure-paths/validation.log).
`REAL_LOCAL_VERIFIED` cho HTTP loopback và log/metric/span output;
`UNIT_TESTED` cho bounds/cancellation. Fault là fixture có kiểm soát, không
incident production. `part16-real-signals` giữ bài học instrument nhỏ ban đầu;
không dựng thêm collector/backend và không retry mutating operation.
