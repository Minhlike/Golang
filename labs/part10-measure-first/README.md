# Lab: đo trước khi tối ưu

Mở `exercise/render_test.go` trước. Test là contract: `Render` phải giữ đúng
format. Hãy tự chọn implementation trong `exercise/render.go`, rồi chạy:

```powershell
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
go test -run '^$' `
  -bench BenchmarkRenderRepresentativeInput `
  -benchmem -count=5 -tags exercise ./exercise
```

Benchmark đã có sẵn một workload 1.000 reading để phần dựng input không lẫn vào
phép đo. Trước khi chạy, ghi một giả thuyết có thể bị bác bỏ; sau năm lượt, so
output và allocation trước khi mở `fixed/`. Bản tham chiếu giữ nguyên output,
nhưng không phải lời mời gọi thay mọi phép nối chuỗi bằng `Builder`.

## Thu thập dấu vết thực thi (Execution Trace)

Để quan sát cách runtime điều phối các Goroutine (G) trên Thread hệ điều hành (M)
và Logical Processor (P), thu thập trace từ workload đồng thời:

```powershell
go test -run TestRenderConcurrentBatchWorkload -trace trace.out ./fixed
go tool trace trace.out
```

Để trích xuất các hồ sơ chờ đợi chuyên biệt dưới dạng pprof:

```powershell
# Hồ sơ chờ đợi đồng bộ (synchronization delay)
go tool trace -pprof=sync trace.out > sync.pprof
# Hồ sơ độ trễ điều phối (scheduler latency)
go tool trace -pprof=sched trace.out > sched.pprof
# Hồ sơ chờ đợi lời gọi hệ thống (syscall delay)
go tool trace -pprof=syscall trace.out > syscall.pprof
```
