# eBPF observer: phạm vi kiểm chứng

Test Go kiểm tra decoder little-endian, channel/cancellation với reader giả lập,
heuristic và `CollectionSpec` mô hình hóa. Test không biên dịch C, load ELF hoặc
attach vào kernel. `Observer.Start` chỉ gọi một lần; adapter thật phải làm `Close`
đánh thức `Read` đang block và quy đổi lỗi đóng reader phù hợp.

## Build object trên Linux

Cần kernel có BTF, `bpftool`, Clang hỗ trợ target BPF và header libbpf ở include
path của compiler. Từ thư mục module:

```sh
bpftool btf dump file /sys/kernel/btf/vmlinux \
    format c > bpf/vmlinux.h
go generate ./...
```

`vmlinux.h` khai báo kiểu `trace_event_raw_sys_enter`; không thay nó bằng riêng
`linux/bpf.h`. Header và bindings/object sinh ra được gitignore. Target `bpfel`
khớp decoder little-endian của lab. Compile-time assertion kiểm tra kích thước
record 156 byte; nó không chứng minh verifier chấp nhận bytecode.

Lab không có binary loader/attach hoàn chỉnh. Sau khi build object, cần nối loader
và adapter `ringbuf.Reader`, rồi kiểm tra trên kernel mục tiêu: quyền, hook,
verifier log, event mất/cắt ngắn, namespace PID và overhead. Hook quan sát exec
attempt, không xác nhận exec thành công. Timestamp hiện tại là giờ userspace decode.

## Lần kiểm tra local ngày 2026-10-01

Go test/vet/race chạy trên Windows với Go 1.27.1. WSL Ubuntu-24.04 có BTF trên
kernel 5.15.167.4-microsoft-standard-WSL2 nhưng không có Clang/bpftool. Vì vậy C
build và load/attach vẫn `SKIPPED_WITH_REASON`; không dùng test fake để thay thế.
