# Hồ sơ lịch sử — Foundation Deep-Rewrite

Tài liệu này từng là chỉ thị cho một lượt sửa nền tảng trước edition Ch29. Nó không còn là kế hoạch đang chờ thực thi, không đóng băng Ch22–28 và không cấm Ch29 đã có trong manuscript. Nội dung cũ có thể xem trong lịch sử Git; không dùng các giả thuyết phần cứng hay mục tiêu chất lượng của nó làm bằng chứng cho sách hiện hành.

## Nguyên tắc còn áp dụng

Độ sâu phải giúp người học dự đoán, bác bỏ hoặc debug một hành vi. Đi từ token, syntax, value, type và scope khi người mới cần; không bắt mọi bài học mở đầu bằng CPU hay runtime. Language semantics và API contract là nền trước khi xem implementation ghim phiên bản. Chi tiết hardware chỉ thêm khi giải thích được phép đo hoặc failure đang xét.

`book/FOUNDATION_CHAPTERS.md` phân loại vai trò chương. `book/BASIC_GO_COVERAGE.md` giữ inventory retrofit lịch sử. `book/README.md` là bản đồ hiện tại. `book/GO_CRITICAL_ANALYSIS_PLAN.md` chứa câu hỏi nghiên cứu, không kết luận performance đã được đo. QA chỉ có hiệu lực cho source/artifact và phạm vi nêu trong `book/FINAL_PUBLICATION_QA.md`.

## Những suy luận không được kế thừa

Cache line 64 byte, page 4 KiB, stack ban đầu, allocator arena hay chi phí syscall/cgo không phải hằng số chung của ngôn ngữ Go. Muốn dùng số phải xác định architecture, OS, toolchain, configuration và cách đo hoặc source. Không quy pointer thành heap, interface thành allocation, goroutine thành một OS thread hoặc race-test xanh thành chương trình race-free.

Một giả thuyết về GC latency, scheduler, channel/mutex hay FFI cần workload và phép kiểm chứng trước khi thành prose. Không có yêu cầu một mô-típ bài học hay một số diagram cố định cho mọi chương. Không có nhãn “100% bằng chứng thực nghiệm” thay cho việc xác định contract nào thật sự đã được test.

Hồ sơ này chỉ giữ ranh giới đọc tài liệu lịch sử; không kích hoạt một rewrite mới.
