# Lab: model dữ liệu và ownership

Mở `main_test.go` trước. Test `TestRecordProbeUpdatesExistingMapEntry` là một
contract, không phải lời gợi ý từng dòng. Trong `recordProbe`, tạm bỏ câu gán
cuối `registry[name] = service`, chạy đúng test đó và đọc state mà assertion
báo. Đây là bug chạy được nhưng semantics sai: local `service` đã đổi, entry
trong map chưa đổi.

Khôi phục bằng cách lần lại đường mutation, không sửa test. Sau đó xóa thân của
`recordFailure` và tự viết lại từ `TestRecordFailureMutatesPointee`; chỉ khi
test xanh mới mở source cũ để đối chiếu. Kết thúc bằng `go test ./...` và
`go vet ./...`.
