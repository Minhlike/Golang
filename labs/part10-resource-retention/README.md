# Một tiến trình Go đang giữ gì sau khi công việc đã xong?

Lab độc lập nối Ch02, Ch03, Ch09, Ch10 và Ch12. Chỉ dùng standard library, không HTTP profiler, không phụ thuộc opsprobe. `go.mod` dùng Go 1.27.1; bằng chứng số liệu trong `EVIDENCE.md` ghi đúng toolchain và môi trường đã chạy. Số liệu không phải output cố định mà mọi máy phải khớp.

## Đặt contract trước khi mở lời giải

Đọc `baseline/retention.go`, dự đoán cơ chế giữ tài nguyên của từng mode. `baseline` cố ý sai; không dùng nó như thư viện production. Đừng đọc `fixed` ngay. Hãy tạo implementation trong package `exercise` để đáp ứng các yêu cầu dưới đây, rồi chạy test có build tag. Package này hiện chỉ có contract test nên lần chạy đầu dự kiến lỗi compile vì chưa có implementation; đó không phải lệnh kiểm định bản sửa.

| Ranh giới | Điều phải chứng minh |
| --- | --- |
| `Prefix(buf, n)` | Với `0 <= n <= len(buf)`, trả byte slice riêng, length/capacity đúng n; sửa một bên không đổi bên kia |
| `NewCache(maxEntries, maxValueBytes)` | Budget dương; đơn chủ sở hữu, FIFO; cập nhật key không làm mới tuổi |
| `Put(key, value)`, `Len()` | Không vượt entry budget; key ≤128 byte; value length trong budget; copy key/value; từ chối input trước mutation/eviction |
| `Wait(ctx, in, started)` | Đóng started khi bắt đầu; receive hoặc cancellation mở đường thoát; done chỉ đóng khi công việc kết thúc |
| `RunTicker(ctx, period, rescue, work)` | Trả Worker có Started, Done, StopTicker; loop thoát vì ctx/rescue; StopTicker riêng không thay đường thoát |
| `DoTimeout(parent, budget, work)` | Scope một operation; child đã được cancel khi hàm return, cả thành công lẫn error |

`RunTicker` yêu cầu period dương như `time.NewTicker`. Callback phải tự tôn trọng context nếu muốn thời gian shutdown hữu hạn; hàm không có quyền giết callback. `rescue` là đường cứu hộ của thí nghiệm để bản lỗi cũng được join sau đo; không được dùng nó để bỏ qua cancellation contract. Cache không dành cho nhiều caller đồng thời, không phải LRU/TTL, và không phải giới hạn RSS. Bản copy byte/string giúp tránh backing storage lớn; metadata và allocator có chi phí ngoài tổng payload.

```powershell
go test -tags exercise ./exercise
```

Contract test là điểm khởi đầu, không phải toàn bộ bài. Tự thêm test FIFO `a,b,a,c`, update/rejection, input ownership, callback không hợp tác và cleanup ở error path trước khi mở `fixed/retention_test.go`. Các test bản sửa có sẵn không dùng ngưỡng heap/RSS hoặc so số goroutine toàn process; chúng dùng trạng thái, số entry và tín hiệu của công việc được sở hữu. Timeout năm giây chỉ là guard để test báo lỗi liveness, không là ngưỡng hiệu năng.

## Tái hiện trong process riêng

Từ thư mục lab, dùng PowerShell. Trên Unix, đổi `.exe` thành tên executable phù hợp và dấu nối dòng thành cú pháp shell tương ứng. Chạy `go version` để ghi môi trường, build một lần, giữ binary ấy cho cả before/after.

```powershell
go version
go build -o artifacts/investigate.exe ./cmd/investigate
./artifacts/investigate.exe -mode=slice `
  -cycles=4 -items=2 -bytes=4194304 -limit=2 `
  -out=artifacts/slice-baseline
./artifacts/investigate.exe -mode=slice -fixed `
  -cycles=4 -items=2 -bytes=4194304 -limit=2 `
  -out=artifacts/slice-fixed
go tool pprof -inuse_space -top `
  artifacts/slice-baseline/04.heap.pprof
go tool pprof -alloc_space -top `
  artifacts/slice-baseline/04.heap.pprof
go tool pprof -inuse_space -top -nodefraction=0 `
  '-focus=main.payload|fixed.Prefix' `
  artifacts/slice-fixed/04.heap.pprof
```

Đổi `-mode` và thư mục `-out` cho mỗi ca. Mode `churn` không giữ payload, là đối chứng cho việc cấp phát nhiều; `-fixed` không đổi logic mode này. Mode `goroutine` và `ticker` tạo worker chứ không dùng payload theo cờ `-bytes`. Mỗi worker được cancel trước khi đo; bản sửa chờ Done ngay, bản lỗi chờ đến rescue cuối thí nghiệm. Mode ticker dùng period một giờ để tách đường chờ loop khỏi chi phí callback. Các test riêng kích hoạt callback và kiểm tra cả bản hợp tác lẫn không hợp tác.

Mode context không dùng `-bytes`; tăng số operation để thấy đường giữ child rõ hơn:

```powershell
./artifacts/investigate.exe -mode=context `
  -cycles=4 -items=128 -out=artifacts/context-baseline
./artifacts/investigate.exe -mode=context -fixed `
  -cycles=4 -items=128 -out=artifacts/context-fixed
go tool pprof -inuse_objects -top -nodefraction=0 `
  '-focus=context.WithDeadlineCause' `
  artifacts/context-baseline/04.heap.pprof
```

`cycle=0` là baseline trước workload; chu kỳ 1–4 chạy workload; chu kỳ 5 là sau harness bỏ view/cache, hủy parent và cứu/join worker lỗi. Trường `entries` chỉ đếm slice hoặc cache, không đếm context child. Mỗi chu kỳ ghi heap profile nhị phân và goroutine dump text có stack (`debug=2`). So các chu kỳ và đọc source; profile heap chỉ ra allocation site, không tự cho đường reference giữ object. Goroutine dump có thể chứa đường dẫn hay thông tin nhạy cảm trong ứng dụng thật; giữ các artifact cục bộ, không gửi hoặc mở listener công khai.

Giới hạn CLI: cycles 1–20, items 1–256, payload 16 byte–64 MiB, cache limit 1–256; tổng payload yêu cầu của slice/cache/churn tối đa 256 MiB, số worker tối đa 128. Context tối đa 5120 child theo tích cycles/items. Cache copy có chi phí cấp phát thêm, nên budget CLI không phải giới hạn tuyệt đối peak RAM. Chọn thư mục output mới cho từng lượt; chạy lại cùng đường dẫn sẽ thay các profile cùng tên. `artifacts/` được gitignore, không commit binary/profile sinh ra.

## Đọc phép đo, không đọc nhãn “leak”

Lab đặt `runtime.MemProfileRate=1` trước workload, làm profiling đắt hơn bình thường. Gọi GC hai lượt tại mỗi điểm đo để chuẩn hóa quan sát với độ trễ profile; không biến việc ép GC thành hướng sửa production. `runtime.KeepAlive` giữ view/cache/parent tới sau phép đo để compiler không cắt ngắn ý đồ fixture. Ghi dump/profile cũng tạo allocation, nên TotalAlloc có cả chi phí quan sát. Không cộng tất cả profile site rồi gọi đó là lượng dữ liệu nghiệp vụ.

`inuse_space` giúp hỏi object còn sống ở site nào; `alloc_space` hỏi đã cấp phát bao nhiêu từ đầu process. NumGoroutine là số đang tồn tại, chưa nói có vượt lifecycle owner không. HeapAlloc/HeapInuse/HeapSys/HeapReleased mô tả các phần heap khác nhau, không thay RSS. Một context có thể giữ timer/child mà không tạo goroutine mới. Deadline hoặc parent cancellation có thể giải phóng đường giữ ấy; bỏ cancel không luôn giữ mãi mãi.

Với Go 1.27.1, ticker không còn tham chiếu có thể được GC thu hồi theo thay đổi từ Go 1.23. Go 1.23–1.26 từng cho chọn behavior cũ theo module và `asynctimerchan`; Go 1.27 đã bỏ setting ấy, luôn dùng timer channel đồng bộ. Không suy ra behavior 1.27 từ ghi chú chuyển tiếp cũ. Không có test yêu cầu GC thu hồi một ticker ở thời điểm cố định. Test chỉ kiểm chứng Stop không đóng channel và không kết thúc worker thay cho đường return.

## Kiểm chứng bản sửa

```powershell
go test -count=1 ./...
go test -race -count=1 ./...
go vet ./...
go vet ./testdata/lostcancel
```

Ba lệnh đầu phải PASS; race cần C compiler được toolchain hỗ trợ. Lệnh cuối **phải báo lỗi** CancelFunc bị bỏ bằng `_`; `testdata` được Go loại khỏi `./...`. `baseline.ForgetCancel` minh họa giới hạn kiểm tra cục bộ: nhận CancelFunc nhưng không gọi, nên không được dùng vet sạch làm bằng chứng cleanup. Bản sửa gọi cancel ở scope operation và có test chứng minh child đã hủy khi callback kết thúc.

Sau khi test hợp đồng đúng, đo lại bằng cùng binary/workload, kiểm tra inuse và stack chờ. Đừng đặt assertion “RSS giảm x MiB” hoặc “heap bằng zero”. Test chứng minh trách nhiệm; số liệu giải thích hệ quả trên một môi trường cụ thể.

## Điểm neo chính thức

Specification: [slice expressions](https://go.dev/ref/spec#Slice_expressions), [map types](https://go.dev/ref/spec#Map_types). Documented behavior theo Go 1.27.1: [context](https://pkg.go.dev/context@go1.27.1), [Ticker.Stop](https://pkg.go.dev/time@go1.27.1#Ticker.Stop), [MemStats](https://pkg.go.dev/runtime@go1.27.1#MemStats), [MemProfile](https://pkg.go.dev/runtime@go1.27.1#MemProfile), [pprof.Profile](https://pkg.go.dev/runtime/pprof@go1.27.1#Profile). Lịch sử timer: [Go 1.23 Timer Channel Changes](https://go.dev/wiki/Go123Timer); trạng thái hiện tại: [Go 1.27 Runtime](https://go.dev/doc/go1.27#runtime). Implementation tham khảo đúng tag: [context/context.go](https://github.com/golang/go/blob/go1.27.1/src/context/context.go). Con số thực nghiệm chỉ thuộc lượt chạy ghi trong EVIDENCE, không thuộc language contract.
