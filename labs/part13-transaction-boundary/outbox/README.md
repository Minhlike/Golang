# Commit rồi chết: còn nhớ việc phải gửi không?

Đọc `TestOutboxContract`, dự đoán state sau mỗi checkpoint rồi mới mở
`store.go`. Không thay contract `Disable` cũ; outbox là bước thực nghiệm riêng.

## Contract và sự cố

Operation `credit-001`, delta 7, phải tăng số dư đúng một lần. Cùng key/delta
là retry; khác delta phải trả `ErrConflict` trước mutation. Operation record,
balance và event pending ở cùng transaction. Pending được đọc lại sau restart;
chỉ chuyển completed sau acknowledgment. Một dispatcher owner cho mỗi sender
file, không có multi-worker claim/lease/fencing hay retry nền.

`BrokenApply` commit nghiệp vụ trước rồi mới enqueue. Kill child tại
`after_commit` để thấy balance=7 nhưng pending=0. Bản sửa phải có pending=1.
Mọi subprocess dùng `os.Exit(77)` tại checkpoint, bỏ qua defers; test mở file
lại bằng connection mới, dispatch ở process mới và kiểm tra durable state.
Parent dùng CommandContext 20 giây và CombinedOutput để reap child, TempDir
sở hữu file; không gửi signal dựa vào timing ngẫu nhiên.

```powershell
# Từ labs/part13-transaction-boundary
go test -count=1 -v ./outbox
go test -race -count=1 ./outbox
go vet ./outbox
$env:RELIABILITY_MUTANT='split_commit'
go test -count=1 -run '^TestOutboxContract$' -v ./outbox
Remove-Item Env:RELIABILITY_MUTANT
```

Lệnh mutant phải exit 1 tại assertion `committed business requires pending
event`, không phải vì lỗi compile. Chạy cùng test không có mutant phải xanh.

## Không nhập nhằng “gửi một lần” và “hiệu ứng một lần”

Sender và receiver có database file riêng. Sender gọi receiver trực tiếp để
cô lập crash boundary, **không** chứng minh delivery qua network/broker thật.
Receiver ghi inbox key/payload và số dư trong một transaction riêng. Child
chết sau receiver commit nhưng trước completed; dispatcher mới gửi lại cùng
event. Inbox durable giúp giữ hiệu ứng một lần trong contract này. Test lỗi
acknowledgment ghi rõ hai attempts, một receiver effect. Cùng receiver key
nhưng payload khác cũng bị từ chối.

Outbox cho đường phát lại at-least-once khi owner tiếp tục dispatch, không
exactly-once delivery. Không có eventual-delivery guarantee nếu operator không
retry, lỗi vĩnh viễn không được xử lý hay identity bị xóa quá sớm. Lab chưa có
retention/TTL, poison-event policy, quota storage hay access-control API; data
và key phải có budget/policy riêng trước khi dùng ở service lâu dài.

## Bằng chứng và giả định storage

`UNIT_TESTED` cho validation/idempotency/concurrent connection. Process death
và database reopen là `REAL_LOCAL_VERIFIED` trên OS/toolchain ghi trong
[`validation.log`](../../../book/evidence/reliability-failure-paths/validation.log).
Receiver là SQLite thật nhưng thay cho external service; không gắn nhãn đã
kiểm chứng GitHub/provider. Checkpoint test chưa mô phỏng mất điện, torn write,
disk corruption hay filesystem mạng.

Driver giữ nguyên `modernc.org/sqlite v1.59.0`, mỗi connection có DELETE
journal, synchronous FULL, foreign keys và busy timeout 5000 ms. Unique key
và write đầu transaction serialize writers theo SQLite; không dùng in-memory
mutex thay database constraint. Các giả định lock/flush của OS/storage vẫn
thuộc [SQLite Atomic Commit](https://www.sqlite.org/atomiccommit.html).
DSN `_pragma` theo [driver v1.59.0](https://pkg.go.dev/modernc.org/sqlite@v1.59.0).
