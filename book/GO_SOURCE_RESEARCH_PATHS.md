# Đường dẫn nghiên cứu Go toolchain

Bản kê này là công cụ định vị implementation của Go 1.27.1, không phải evidence cho mọi claim cạnh đường dẫn. GOROOT local là `D:\Golang\.tools\go1.27.1`; các path trong bảng tương đối với `src/`. Target của các thí nghiệm Windows hiện hành là `windows/amd64`. Không sao chép cả GOROOT vào repository.

Đọc specification và API contract trước khi lần source. Chỉ mở một implementation khi cần giải thích một quan sát hoặc kiểm tra quyết định đã pin; người mới không cần thuộc struct runtime để hiểu value semantics. Mỗi kết luận từ source phải ghi symbol, version và phạm vi target nếu có.

## Compiler và artifact

| Path | Câu hỏi nó giúp điều tra | Ranh giới |
| --- | --- | --- |
| `cmd/compile/internal/syntax/` | Token, parser và cây cú pháp frontend được dựng thế nào? | Không coi cây này là bản giữ nguyên mọi token của source hay toàn bộ pipeline compile. |
| `cmd/compile/internal/types2/` | Tên, kiểu, assignability và generic inference được kiểm tra ở đâu? | Spec mới định nghĩa ngữ nghĩa; diagnostic cụ thể có thể đổi. |
| `cmd/compile/internal/noder/`, `ir/` | Source đã kiểm tra được đưa vào IR của compiler thế nào? | IR nội bộ không phải API của sách. |
| `cmd/compile/internal/types/` | Size, alignment và layout cho target được tính thế nào? | Kết quả theo target không thành layout phổ quát. |
| `cmd/compile/internal/escape/`, `inline/` | Data flow và inlining ảnh hưởng quyết định lưu trữ thế nào? | Không suy syntax pointer/interface thành heap allocation. |
| `cmd/compile/internal/deadlocals/` | Biến local không cần thiết được loại ở bước nào? | Dead-code elimination còn có các pass SSA; không quy mọi loại bỏ nhánh cho thư mục này. |
| `cmd/compile/internal/ssa/`, `ssa/_gen/` | SSA, prove, rewrite rules và lowering theo kiến trúc. | `_gen` là đường nguồn rules của version này, không phải `ssa/gen`. |
| `cmd/compile/internal/ssagen/`, `amd64/` | SSA thành danh sách instruction target thế nào? | Listing `-S` khác objdump của binary đã link. |
| `cmd/internal/obj/`, `cmd/asm/internal/asm/` | Symbol, relocation và instruction encoding được xử lý ở đâu? | Compiler không cần chạy CLI assembler riêng cho mọi tệp Go. |
| `cmd/link/internal/ld/`, `cmd/internal/goobj/` | Object, metadata và executable được liên kết thế nào? | So các đầu ra phải dùng cùng source, cờ và artifact; không quy đổi nhánh cho linker chỉ từ hai snapshot khác nhau. |

## Runtime và bộ nhớ

| Path | Nội dung cần tìm | Ranh giới |
| --- | --- | --- |
| `runtime/proc.go`, `runtime/runtime2.go` | G/M/P, hàng đợi chạy và các cấu trúc runtime. | P là tài nguyên điều phối, không phải core vật lý. |
| `runtime/malloc.go`, `mcache.go`, `mcentral.go`, `mheap.go` | Các đường allocation, size class và span. | Allocation observation cần compiler/benchmark; đọc source không cho một chi phí cố định. |
| `runtime/mpagealloc.go` | Bitmap và cấp các runtime heap page trong address space. | Không quản lý trực tiếp từng trang RAM vật lý của OS; virtual, resident và cgroup memory là các đại lượng khác nhau. |
| `runtime/mgc.go`, `mgcpacer.go` | Pha mark/sweep, STW, assist và pacing. | Không có latency hay tỷ lệ CPU bảo đảm cho service từ một constant của pacer. |
| `runtime/mgcmark.go`, `mgcmark_greenteagc.go`, `mgcsweep.go` | Đường mark và sweep của build tương ứng, gồm Green Tea. | Build selection và version quyết định implementation; “đồng thời” không có nghĩa không có pause. |
| `runtime/mgcscavenge.go` | Trả phần memory không cần giữ cho OS. | Heap metric giảm không tự chứng minh RSS giảm bằng lượng đó. |
| `runtime/stack.go` | Stack growth/copy, `stackMin` và phần theo OS. | `stackMin = 2048` byte không phải tổng allocation hay tổng chi phí của mọi goroutine. |
| `runtime/chan.go`, `select.go` | `hchan`, hàng đợi chờ và chọn case của implementation. | Ownership và happens-before dựa trên spec/Memory Model; không có ranking tốc độ primitive chung. |
| `internal/runtime/maps/`, `runtime/map.go` | Swiss-table map và cầu nối runtime của Go 1.27.1. | Không tái dùng mô hình `hmap/bmap` kiểu cũ như default của edition này; map semantics vẫn do spec quy định. |
| `runtime/slice.go`, `runtime/string.go` | Descriptor và các helper growth/conversion/concatenation. | Không suy physical copy hoặc allocation chỉ từ assignment/conversion syntax. |
| `runtime/iface.go`, `runtime/runtime2.go` | Conversion helpers và biểu diễn `iface/eface`. | Typed nil giải thích được bằng dynamic type/value; representation không phải contract của ngôn ngữ. |
| `runtime/panic.go`, `cmd/compile/internal/ssagen/` | Panic, recover, deferred calls và đường compiler tạo defer. | Không giả định mọi defer đều là một node linked list: có đường open-coded defer. |
| `runtime/trace.go`, `internal/trace/` | Ghi và đọc các sự kiện execution trace. | Không hứa độ chính xác microsecond chung hay trace chứa mọi chuyển động của source. |

## Hợp đồng tái lập

Khi ghi một thí nghiệm, lưu source identity, `go version`, target, cờ build, command và artifact thực sự được đọc. Path là điểm bắt đầu tìm symbol, không phải nhãn VERIFIED. Với API chung có backend theo OS, tách contract byte/error/deadline khỏi readiness của Linux và completion của Windows. Một phiên bản mới cần kiểm tra lại path và behavior liên quan thay vì kế thừa kết luận từ bảng này.
