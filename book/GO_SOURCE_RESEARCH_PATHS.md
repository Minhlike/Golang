# DANH MỤC ĐƯỜNG DẪN MÃ NGUỒN GO TOOLCHAIN PHỤC VỤ FOUNDATION REWRITE

**Toolchain Bản Địa:** Go 1.27.1 (`windows/amd64`)  
**GOROOT Định Vị:** `D:\Golang\.tools\go1.27.1\src`  
**Nguyên Tắc Bất Biến:** Tuyệt đối không sao chép (duplicate) mã nguồn từ GOROOT vào kho lưu trữ sách. Bản kê này đóng vai trò chỉ dẫn định vị (Source Navigator) để Agent ở lượt Foundation Deep-Rewrite tra cứu trực tiếp từ first principles.

---

## 1. Trình Biên Dịch (Compiler Frontend & Type Checking)

Toàn bộ mã nguồn nằm tại `D:\Golang\.tools\go1.27.1\src\cmd\compile\internal/`:

| Phân Vùng Kiến Trúc | Đường Dẫn Thực Tế | Chức Năng Cốt Lõi Cần Nghiên Cứu |
| :--- | :--- | :--- |
| **Lexer & Parser** | `cmd/compile/internal/syntax/` | Phân tích từ vựng và cú pháp Go, xây dựng cây cú pháp nguồn (Concrete Syntax Tree). |
| **Type Checking** | `cmd/compile/internal/types2/` | Kiểm tra hệ thống kiểu tĩnh, suy diễn kiểu (type inference), kiểm tra giao diện và generic instantiation. |
| **AST to IR Bridge** | `cmd/compile/internal/noder/` | Chuyển đổi cú pháp CST sang cấu trúc biểu diễn trung gian thống nhất (AST to IR). |
| **Intermediate Repr**| `cmd/compile/internal/ir/` | Cấu trúc dữ liệu Node, Type, Symbol của toàn bộ chương trình trong quá trình biên dịch. |
| **Type Layout** | `cmd/compile/internal/types/` | Cấu trúc kích thước kiểu, căn chỉnh bộ nhớ (memory alignment, padding) của struct, array, slice. |

---

## 2. Tối Ưu Hóa & Sinh Mã (Compiler Optimization & SSA Backend)

| Phân Vùng Kiến Trúc | Đường Dẫn Thực Tế | Chức Năng Cốt Lõi Cần Nghiên Cứu |
| :--- | :--- | :--- |
| **Escape Analysis** | `cmd/compile/internal/escape/` | Thuật toán phân tích thoát (escape analysis) quyết định phân bổ biến trên Stack hay Heap. |
| **Inlining Engine** | `cmd/compile/internal/inline/` | Thuật toán thẩm định chi phí hàm (inlining budget/heuristics) để gộp thân hàm trực tiếp. |
| **Dead Code & Locals**| `cmd/compile/internal/deadlocals/` | Loại bỏ các biến cục bộ và nhánh lệnh không bao giờ được thực thi. |
| **SSA Construction** | `cmd/compile/internal/ssa/` | Biểu diễn Static Single Assignment: tối ưu hóa biểu thức con chung, lan truyền hằng số, loop invariant. |
| **SSA Rules Generator**| `cmd/compile/internal/ssa/gen/` | Quy tắc biến đổi SSA và hạ cấp lệnh (lowering rules) theo từng kiến trúc CPU. |
| **Arch SSA Gen** | `cmd/compile/internal/ssagen/` | Chuyển đổi đồ thị SSA thành danh sách lệnh hợp ngữ máy trừu tượng của Go. |
| **AMD64 Codegen** | `cmd/compile/internal/amd64/` | Sinh mã máy chuyên biệt cho tập chỉ lệnh x86-64 (thanh ghi, quy ước gọi ABI nội bộ). |

---

## 3. Trình Hợp Ngữ & Liên Kết (Assembler & Linker)

| Phân Vùng Kiến Trúc | Đường Dẫn Thực Tế | Chức Năng Cốt Lõi Cần Nghiên Cứu |
| :--- | :--- | :--- |
| **Go Assembler** | `cmd/asm/internal/asm/` | Trình biên dịch mã hợp ngữ Go (Go Assembly syntax) sang tệp mã đối tượng (Object Code). |
| **Instruction Architecture** | `cmd/internal/obj/` | Định nghĩa kiến trúc chỉ lệnh máy trừu tượng (Prog, Addr, Reg). |
| **Go Linker** | `cmd/link/internal/ld/` | Trình liên kết các package đối tượng, gắn metadata DWARF, định vị bảng hàm và sinh executable nhị phân cuối. |
| **Object File Format** | `cmd/internal/goobj/` | Cấu trúc nhị phân nội bộ của tệp `.a` và object stream trước khi link. |

---

## 4. Hệ Thống Thực Thi (Go Runtime Core & Memory)

Toàn bộ mã nguồn nằm tại `D:\Golang\.tools\go1.27.1\src\runtime/`:

| Phân Vùng Kiến Trúc | Tệp Nguồn / Thư Mục | Chức Năng Cốt Lõi Cần Nghiên Cứu |
| :--- | :--- | :--- |
| **Goroutine Scheduler** | `runtime/proc.go` | Mô hình GMP: cấu trúc Goroutine (`g`), Thread hệ điều hành (`m`), Bộ vi xử lý logic (`p`), work-stealing, sysmon. |
| **Memory Allocator** | `runtime/malloc.go` | Bộ cấp phát bộ nhớ TCMalloc-derived: `mcache` (per-P), `mcentral` (per-size-class), `mheap` (trang bộ nhớ/spans). |
| **Page Allocator** | `runtime/mpagealloc.go` | Cấp phát và quản lý bitmap các trang bộ nhớ vật lý trong heap. |
| **Garbage Collector** | `runtime/mgc.go` | Chu trình gom rác phân tán: Concurrent Tricolor Mark-Sweep, thế hệ STW tối thiểu, write barrier. |
| **GC Pacer** | `runtime/mgcpacer.go` | Thuật toán điều tốc GC động dựa trên GOGC và tỷ lệ gia tăng bộ nhớ heap mục tiêu. |
| **GC Mark & Sweep** | `runtime/mgcmark.go`, `runtime/mgcsweep.go` | Giai đoạn đánh dấu đối tượng sống (grey/black work queues) và dọn dẹp span rác. |
| **Stack Management** | `runtime/stack.go` | Cấp phát và mở rộng ngăn xếp liên tục (contiguous stack copy/growth) khởi đầu từ 2KB. |
| **Channels** | `runtime/chan.go` | Cấu trúc nội bộ của channel: `hchan`, bộ đệm vòng `buf`, hàng đợi khóa `waitq`, phân mảnh `sudog`. |
| **Select Multiplexer** | `runtime/select.go` | Thuật toán xáo trộn ngẫu nhiên và khóa các kênh trong cấu trúc lệnh `select`. |
| **Hash Maps** | `runtime/map.go`, `runtime/map_fast64.go` | Cấu trúc bảng băm: `hmap`, mảng các bucket `bmap`, phân mảnh tophash, di dời dữ liệu lũy tiến (evacuation). |
| **Slices & Strings** | `runtime/slice.go`, `runtime/string.go` | Cấu trúc header của Slice/String, cơ chế `growslice` tính toán cấp số nhân và làm tròn lớp kích thước. |
| **Interfaces** | `runtime/iface.go`, `runtime/runtime2.go` | Cấu trúc giao diện rỗng `eface` (`_type`, `data`) và giao diện có phương thức `iface` (`itab`, `data`). |
| **Panics & Defers** | `runtime/panic.go` | Chuỗi danh sách liên kết `_defer`, cơ chế thu hồi lỗi `recover`, mở cuộn ngăn xếp khi panic. |
| **Execution Tracer** | `runtime/trace.go` | Bộ ghi dấu sự kiện runtime chuẩn xác micro-giây phục vụ công cụ `go tool trace`. |

---

## 5. Quy Chuẩn Sử Dụng Cho Lượt Foundation Rewrite

1. **Luôn Bắt Đầu Từ First Principles:** Khi giải thích cách vận hành của Channel, Map, Slice, Interface, hoặc Goroutine, Agent phải đối chiếu trực tiếp với các cấu trúc dữ liệu tương ứng trong `runtime/` nêu trên.
2. **Không Đoán Định Ngầm:** Mọi phát biểu về chi phí bộ nhớ, thuật toán phân bổ hoặc hành vi runtime phải có bằng chứng từ mã nguồn thực tế của phiên bản `go1.27.1`.
3. **Phân Biệt Rạch Ròi Cấp Độ Trừu Tượng:** Không nhầm lẫn giữa cú pháp ngôn ngữ (syntax), mô hình trung gian của trình biên dịch (AST/IR/SSA), và cấu trúc vận hành thực tế ở thời điểm chạy (runtime data structures).
