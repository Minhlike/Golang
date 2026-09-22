# Part 16 — Signals thật, phạm vi nhỏ

Đây là **stage hai** sau `part16-observability-evidence`. Không thay recorder
conceptual; nó cho một HTTP service nhỏ phát ra ba loại evidence thật:

- JSON structured log ở stderr;
- Prometheus counter + histogram ở `/metrics`;
- OpenTelemetry trace ra stdout qua console exporter.

Metric chỉ có label `outcome` thuộc tập `success`, `failure`, `timeout`.
`mode`, raw URL, user ID, request ID và error text không được làm metric label.
Histogram dùng bucket cố ý: 5, 10, 25, 50, 100 và 250 ms. Đây là lựa chọn cho
lab local, không phải SLO mặc định của production. Counter sống trong process;
restart sẽ làm state local trở về zero.

## Chạy và quan sát

```powershell
go test ./...
go vet ./...
go test -race ./...
go run ./cmd/probe-api
```

Mở terminal khác:

```powershell
Invoke-WebRequest http://localhost:8080/probe?mode=ok
Invoke-WebRequest http://localhost:8080/probe?mode=slow
Invoke-WebRequest http://localhost:8080/probe?mode=fail
Invoke-WebRequest http://localhost:8080/probe?mode=timeout
Invoke-WebRequest http://localhost:8080/metrics
```

Hai lệnh `fail` và `timeout` trả HTTP lỗi theo chủ đích. Dùng `curl.exe -i` nếu
muốn thấy status code mà không để PowerShell coi response lỗi là exception.
Quan sát cùng một lần gọi ở ba nơi: JSON log ghi outcome/duration, Prometheus
aggregate số lần và histogram, trace stdout có `probe.request` chứa
`probe.dependency` làm child span.

## Nhiệm vụ tự điều tra

Không mở test trước. Chạy lần lượt `ok`, `slow`, `fail`, `timeout`, rồi trả lời:

1. Cặp nào đều làm duration cao nhưng chỉ một cặp có outcome lỗi?
2. Metric nào trả lời tần suất timeout, còn evidence nào giữ quan hệ request → dependency?
3. Vì sao thêm `mode` làm label có vẻ vô hại trong lab này nhưng raw URL là sai
   thiết kế khi input có thể vô hạn?
4. Restart process rồi scrape lại. Điều gì còn, điều gì mất?

Sau đó mở `probeapi/server_test.go`. Test không thay dashboard hay collector;
nó chỉ khóa contract local: log có field, metric không mang label mở, và trace
giữ quan hệ parent-child.

Console exporter phù hợp cho học tập và debugging local. Production thường gửi
trace qua collector/backend theo policy riêng; không đưa endpoint hay secret vào
log/trace attribute chỉ để dễ tìm.
