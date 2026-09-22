# Lab: evidence có denominator

Mở `exercise/recorder_test.go` trước. Lab này không dựng exporter hay dashboard;
nó khóa semantic của một metric bounded trước.

```powershell
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
go test ./fixed
go vet ./fixed
go test -race ./fixed
```

Contract: chỉ có `success`, `failure`, `timeout`; outcome lạ trả error và không
mutate state; `Completed` luôn bằng tổng ba bucket; no data không có success
ratio; `Snapshot` trả bản copy ổn định khi nhiều goroutine cùng `Observe`.
Không thêm target, URL, trace ID hay raw error làm label của recorder này.
