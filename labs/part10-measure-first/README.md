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

`>` cho profile nhị phân yêu cầu PowerShell 7.4 trở lên (native byte-preserving
redirection), hoặc shell có chuyển hướng nhị phân tương đương. Với Windows
PowerShell cũ, dùng subprocess ghi byte trực tiếp, không qua Out-File/text encoding.

## A/B có và không có PGO

Từ thư mục lab, chạy `python pgo_ab.py --go <đường-dẫn-go-đã-pin>`.
Output mặc định là `artifacts/pgo-ab`; nếu đã tồn tại, chọn một thư mục mới bằng
`--out`. Script không ghi đè evidence cũ. Chỉ dùng Python standard library và Go,
không tải dependency hay chạy workload production.

Hai phía dùng cùng `fixed.Render`, không so `baseline` nối chuỗi với `fixed`.
Profile huấn luyện được thu khi `-pgo=off`, chỉ đại diện cho 1000 Reading của
benchmark này. Script build hai test binary riêng, ghi lệnh compiler `-x`, kiểm
tra output cả hai, loại hai lượt warmup khỏi thống kê, rồi chạy sáu cặp A/B theo
thứ tự luân phiên. Mỗi mẫu 400ms, GOMAXPROCS=2, không bật profiler khi đo A/B.
Evidence giữ từng mẫu, môi trường, source/profile/binary SHA và raw stdout/stderr
dưới dạng base64 cùng checksum; text UTF-8 chỉ là bản giải mã để đọc.

Min/max/median mô tả lượt chạy, không là khoảng tin cậy hay chứng minh cải thiện
production. Máy không được cô lập khỏi tải nền; profile hẹp không đủ đại diện
cho toàn service. Nếu source thay đổi, phải thu lại profile và build cả hai phía.
