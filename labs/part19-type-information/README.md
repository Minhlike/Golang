# Lab — giữ type information

Lab có ba phần độc lập. Mở test hoặc source được chỉ định trước, dự đoán điều
compiler/caller có thể biết, rồi mới viết code. Không dùng reflection để giải
phần generics hoặc typed-nil.

## 1. Tách duplication bằng generic contract

Mở `exercise/unique_test.go` trước `exercise/unique.go`. Viết `Unique[T
comparable]`: giữ phần tử đầu tiên theo thứ tự, không sửa input, và không ép
named type về builtin type. Chạy:

```powershell
go test -tags exercise ./exercise
```

## 2. Review API generic quá rộng

Đọc `review/overgeneralized.go`. Trước khi mở `review/answer.md`, tự ghi ngắn:
type parameter nào không giúp function có thêm operation hợp lệ, thông tin về
format/ownership nào đang bị giấu, và API nhỏ hơn nên nhận/trả gì. Đây là code
review, không có test xanh thay cho lập luận thiết kế.

## 3. Debug typed-nil

Mở `typednil/check_test.go`, dự đoán failure, rồi chạy:

```powershell
go test -tags typednilexercise ./typednil
```

Sửa `typednil/check.go` để nhánh thành công trả một `nil error` thật. Sau khi
qua test, so sánh với `typednil/fixed/` và chạy các reference check:

```powershell
go test ./fixed
go test -race ./fixed
go test ./typednil/fixed
go vet ./...
```

`fixed/collection.go` cũng có generic named type và generic method của Go
1.27. Nó là reference để đọc sau bài, không phải lời mời tạo `Map` method cho
mọi slice trong codebase.
