# FOUNDATION DEEP-REWRITE HANDOFF SPECIFICATION

> **Chiến dịch nâng cấp nền tảng:** Chuyển hóa toàn bộ khối chương nền tảng (Foundation Core & Foundation Bridge) thành tài liệu kỹ thuật chuyên sâu từ nguyên lý sơ cấp (First Principles), triệt tiêu văn phong AI-slop, tuân thủ kỷ luật Zero-Bullet cho chính văn và bảo đảm 100% luận điểm có bằng chứng thực nghiệm từ mã nguồn Go toolchain / runtime.

---

## 1. Executive Summary

Bộ giáo trình hiện tại đã hoàn thiện và đóng băng an toàn các chương ứng dụng thực chiến nâng cao từ Chương 22 đến Chương 28. Tuy nhiên, khối chương nền tảng (bao gồm Chương 00A, 00B và từ Chương 01 đến Chương 10, cùng Chương 14 và 19) đang dừng ở mức giải thích cú pháp và mô hình bề mặt, chưa phản ánh đúng bản chất thiết kế của Go runtime và compiler.

Mục tiêu của đợt đại tu (Foundation Deep-Rewrite) sắp tới:
1. **Biến khối nền tảng thành một trong những tài liệu Go sâu sắc, chính xác và có tính phản biện kỹ thuật cao nhất.**
2. **Không viết sách theo phong cách tutorial nhập môn bề mặt.** Độc giả mục tiêu là kỹ sư phần mềm, kỹ sư hạ tầng muốn hiểu chính xác điều gì xảy ra ở mức thanh ghi CPU, dòng bộ nhớ cache (cache line), stack frame của hệ điều hành, cấu trúc dữ liệu nội bộ của runtime và các pass tối ưu của trình biên dịch.
3. **Tuyệt đối không mở rộng sang Chương 29.** Phạm vi công việc kết thúc trọn vẹn tại Chương 28.
4. **Không chạm vào hay xáo trộn các chương đã hoàn tất và đóng băng từ Ch22 đến Ch28.**

---

## 2. Mental Model & First-Principles Mandate

Tất cả các chương thuộc khối Foundation phải được xây dựng từ nguyên lý sơ cấp của khoa học máy tính:

1. **Từ phần cứng lên phần mềm:**
   Mọi khái niệm ngôn ngữ phải được quy chiếu về:
   - Kiến trúc bộ nhớ: L1/L2/L3 cache, cache line (64 bytes), false sharing, non-temporal store, memory alignment và padding.
   - Vi kiến trúc CPU: Registers, ALU, branch predictor, out-of-order execution, instruction pipeline, memory barrier/fence.
   - Hệ điều hành: Kernel context switch, syscall overhead, virtual memory page (4KB / huge pages), TLB miss, signals, epoll/kqueue/IOCP.
2. **Giải thích động lực thiết kế (Design Rationale):**
   Không dừng lại ở việc nêu "Go hoạt động như thế nào", mà phải trả lời tường tận:
   - *Vì sao các tác giả ngôn ngữ (Ken Thompson, Rob Pike, Robert Griesemer) lại chọn hướng tiếp cận này?*
   - *Họ đã chấp nhận đánh đổi (trade-off) điều gì để đạt được sự đơn giản trong cú pháp hoặc thời gian biên dịch cực nhanh?*
3. **Chỉ ra điểm gãy (Failure Modes & Boundaries):**
   Một thiết kế tối ưu trong bối cảnh microservices phân tán chịu tải I/O có thể là thảm họa trong bối cảnh tính toán số học hiệu năng cao (HPC), xử lý âm thanh/video thời gian thực cứng (hard real-time), hoặc hệ thống nhúng siêu giới hạn RAM. Các chương phải làm rõ chính xác ngưỡng tải và ranh giới mà thiết kế của Go bộc lộ điểm yếu hoặc suy giảm hiệu năng nghiêm trọng.

---

## 3. Terminology & Disambiguation Rules

Để tránh mọi hiểu lầm kỹ thuật phổ biến trong cộng đồng và do các mô hình LLM tạo ra, bắt buộc phải phân biệt rạch ròi các nhóm khái niệm sau:

### 3.1. Năm Khái Niệm Assembly & Machine Code
Khi thảo luận về mã assembly hoặc chỉ thị máy, tác giả phải nêu đích danh tầng biểu diễn tương ứng:
1. **Compiler Assembly Listing (`go tool compile -S`):**
   Là bản biểu diễn trung gian dạng hợp ngữ giả do backend trình biên dịch (`cmd/compile/internal/ssagen`) phát ra. Bản danh sách này chứa các thanh ghi ảo, các chỉ thị giả lập của Go runtime (như `FUNCDATA`, `PCDATA`, `DUPOK`), và chưa qua bước giải quyết địa chỉ liên kết (linking).
2. **Go Assembler Syntax (`cmd/asm`):**
   Cú pháp hợp ngữ riêng biệt dựa trên quy chuẩn Plan 9 do Go định nghĩa, sử dụng các thanh ghi giả (`SB`, `FP`, `SP`, `PC`). Cú pháp này không đồng nhất hoàn toàn với cú pháp AT&T hay Intel x86 chuẩn.
3. **Object Code (`.a` / `.o`):**
   Mã đối tượng nhị phân trung gian được đóng gói theo định dạng riêng của Go toolchain, chứa mã máy chưa liên kết cùng bảng ký hiệu (symbol table) và dữ liệu debug DWARF.
4. **Final Binary Disassembly (`go tool objdump` hoặc `objdump -d`):**
   Kết quả dịch ngược từ tệp nhị phân thực thi cuối cùng đã qua `cmd/link`. Đây là các chỉ thị mã máy thực sự nằm trong phân vùng `.text` của tệp định dạng PE/ELF/Mach-O.
5. **Target Machine Instructions (x86-64 / ARM64):**
   Các opcode và ngữ nghĩa phần cứng thực tế của vi kiến trúc (ví dụ: `VMOVDQU`, `MFENCE`, `PAUSE` trên amd64; `LDAR`, `STLR`, `ISB` trên arm64).

### 3.2. Runtime Scheduler vs OS Thread Scheduler
- Phân biệt tuyệt đối giữa **Go Runtime M:N Cooperative/Preemptive Scheduler** (quản lý goroutine `G`, luồng hệ điều hành `M`, và ngữ cảnh thực thi logic `P` trong không gian người dùng) với **OS Kernel 1:1 Scheduler** (quản lý context switch, time-slice, mức độ ưu tiên của thread trong nhân hệ điều hành).
- Nhấn mạnh rằng scheduler của Go không can thiệp vào cách nhân hệ điều hành điều phối các thực thể `M` lên lõi CPU vật lý.

### 3.3. Virtual Memory vs Resident Set Size vs Go Runtime Arena
- **Virtual Memory (`VIRT`):** Không gian địa chỉ ảo mà tiến trình đăng ký với hệ điều hành (Go runtime có thể mmap trước hàng chục hoặc hàng trăm gigabyte địa chỉ ảo 64-bit mà không tốn RAM vật lý).
- **Resident Set Size (`RSS`):** Lượng trang nhớ vật lý thực tế được nạp vào RAM cho tiến trình.
- **Go Runtime Heap Arena:** Cấu trúc phân mảnh nội bộ của bộ cấp phát `mallocgc` (bao gồm `mspan`, `mcentral`, `mcache`, và các khối heap arena kích thước 64MB trên 64-bit architectures). Cần phân biệt bộ nhớ do runtime chiếm dụng (`sys`) với bộ nhớ thực tế chứa đối tượng người dùng (`inuse`).

### 3.4. Compile-time Escape Analysis vs Runtime Allocation
- **Escape Analysis:** Phân tích tĩnh tại thời điểm biên dịch (`cmd/compile/internal/escape`) nhằm xác định xem vòng đời (lifetime) của một biến có vượt ra ngoài phạm vi stack frame của hàm khởi tạo hay không.
- **Stack Allocation:** Cấp phát tức thời bằng cách điều chỉnh con trỏ ngăn xếp `SP`, không gây gánh nặng lên bộ thu gom rác.
- **Heap Allocation (`runtime.newobject` / `runtime.makeslice`):** Cấp phát động trong heap arena tại thời gian chạy khi phân tích escape chỉ ra biến bị rò rỉ (escape).

### 3.5. Interface Representation: Fat Pointer Invariants
- **Non-empty Interface (`iface`):** Cấu trúc con trỏ kép gồm `tab *itab` (chứa kiểu dữ liệu cụ thể, con trỏ hàm thỏa mãn interface, hash mã định danh kiểu) và `data unsafe.Pointer`.
- **Empty Interface (`eface` / `any`):** Cấu trúc con trỏ kép gồm `_type *_type` (mô tả siêu dữ liệu kiểu) và `data unsafe.Pointer`.
- Tuyệt đối không gọi chung chung interface là một con trỏ đơn giản hoặc nhầm lẫn giữa chi phí đóng gói (boxing) và chi phí giải mã gọi hàm ảo (dynamic dispatch).

---

## 4. Anti-AI-Bias & Anti-AI-Slop Rules

Nhằm duy trì tính nghiêm túc của một chuyên khảo học thuật chuyên nghiệp, toàn bộ các chương phải tuân thủ nghiêm ngặt các rào chắn biên tập sau:

1. **Triệt tiêu AI-Slop:**
   Cấm tuyệt đối các mẫu câu mở đầu hoặc kết luận sáo rỗng thường gặp của LLM:
   - *"Trong kỷ nguyên số hóa / thế giới phát triển nhanh chóng hiện nay..."*
   - *"Hãy cùng chúng tôi lặn sâu (dive deep) vào thế giới của Go..."*
   - *"Như chúng ta đã biết..."*
   - *"Bài viết này sẽ cung cấp cho bạn cái nhìn toàn diện..."*
   - *"Tóm lại, Go là một ngôn ngữ tuyệt vời và mạnh mẽ..."*
2. **Cấm Thiên Kiến Một Chiều (Anti-One-Sided Bias):**
   - Không được ca ngợi Go một cách vô căn cứ hoặc tuyệt đối hóa các tính năng của ngôn ngữ.
   - Mọi tuyên bố về hiệu năng ("Go nhanh", "Goroutine siêu nhẹ") đều phải đi kèm số liệu định lượng, chi phí đánh đổi (trade-offs), và ngữ cảnh giới hạn.
3. **Kỷ Luật Zero-Bullet Cho Chính Văn (Zero-Bullet Rule):**
   - **Chính văn (main prose manuscript) của các chương sách tuyệt đối không sử dụng danh sách gạch đầu dòng (bullet points) để liệt kê thông tin.**
   - Mọi giải thích kiến trúc, quy trình, cơ chế, và phân tích đều phải được viết thành các đoạn văn xuôi (continuous analytical prose) hoàn chỉnh, có kết cấu mạch lạc, có luận điểm, dẫn chứng và lập luận chuyển tiếp tự nhiên.
   - Gạch đầu dòng chỉ được chấp nhận duy nhất trong các trường hợp ngoại lệ: tóm tắt đầu chương dạng metadata, mục lục, hoặc các danh mục ngắn mang tính chất cấu hình thuần túy.
4. **Chuẩn Mực Tiếng Việt Kỹ Thuật (~99% Vietnamese Target):**
   - Văn phong biên soạn phải là tiếng Việt chuẩn mực, mạch lạc, đanh thép và khúc chiết.
   - Không chêm xen tiếng Anh bừa bãi vào câu khi đã có thuật ngữ tiếng Việt chuẩn xác hoặc có thể diễn giải kỹ thuật rõ ràng (ví dụ: dùng "thu gom rác" thay cho "garbage collection", "ngăn xếp" thay cho "stack", "vùng nhớ động" thay cho "heap", "chuyển đổi ngữ cảnh" thay cho "context switch").
   - Giữ nguyên các định danh mã nguồn, tên thanh ghi, tên struct nội bộ hoặc thuật ngữ gốc mang tính kỹ thuật tuyệt đối không thể dịch (ví dụ: `itab`, `mcache`, `epoll`, `futex`, `CAS`, `runtime.g`).

---

## 5. Mindmap & Semantic Diagram Standards

Mỗi chương phải có sơ đồ minh họa trực quan đáp ứng chuẩn mực phân loại rõ ràng:

1. **Tony Buzan Mindmap (Sơ đồ tư duy mở đầu chương):**
   - **Mục đích:** Cung cấp cái nhìn bao quát về mạng lưới khái niệm và mối liên hệ liên đới của toàn bộ chương trước khi bước vào chi tiết.
   - **Định dạng Mermaid:** Sử dụng cú pháp `mindmap` của Mermaid.
   - **Cấu trúc:** Đi từ gốc trung tâm (tên chương), rẽ nhánh cấp 1 (các trụ cột tư duy chính), và phân nhánh cấp 2 (các cơ chế then chốt).
2. **Semantic & Architectural Diagrams (Sơ đồ kỹ thuật chuyên sâu):**
   - **Mục đích:** Mô tả chính xác bố cục ô nhớ (memory layout), luồng trạng thái (state machine), đường đi dữ liệu (data flow) hoặc tương tác hệ thống.
   - **Định dạng Mermaid:** Sử dụng `classDiagram`, `stateDiagram-v2`, `flowchart TD` / `flowchart LR`, hoặc `sequenceDiagram`.
   - **Yêu cầu:** Gắn nhãn cụ thể các thành phần (kích thước byte, con trỏ, hướng mũi tên phản ánh chính xác luồng di chuyển hoặc trỏ địa chỉ).
3. **Không đánh đồng hai loại sơ đồ:** Sơ đồ tư duy không dùng để diễn tả luồng dữ liệu máy tính, và sơ đồ kiến trúc không dùng để thay thế bản đồ khái niệm chương.

---

## 6. Evidence-First Execution Pipeline

Mọi khẳng định trong chương phải trải qua quy trình xác minh 4 bước nghiêm ngặt:

```
[BƯỚC 1: Xác định luận điểm kỹ thuật (Claim)]
       │
       ▼
[BƯỚC 2: Chạy kiểm chứng / Trích xuất bằng chứng (Run Probes & Benchmarks)]
       │ (Sử dụng scripts/foundation_probe.ps1, go test -bench, pprof)
       ▼
[BƯỚC 3: Lưu trữ bằng chứng vào .workspace/foundation-evidence/]
       │ (Đối chiếu trực tiếp GOROOT source tại .tools/go1.27.1/src)
       ▼
[BƯỚC 4: Soạn thảo văn xuôi phân tích (Write Continuous Prose)]
```

- Không chấp nhận các khẳng định dạng truyền miệng ("goroutine khởi tạo tốn 2KB", "channel an toàn tuyệt đối", "con trỏ luôn thoát ra heap"). Phải kiểm chứng chính xác phiên bản Go mục tiêu (Go 1.27.1) định nghĩa struct và ngưỡng phân bổ ra sao trong thực tế.

---

## 7. Scope Boundary & Verification Checklist

Trước khi hoàn tất bất kỳ chương nào trong đợt rewrite nền tảng, tác giả phải đối chiếu danh sách kiểm tra sau:

- [ ] Chương có nằm trong danh mục `FOUNDATION_CORE` hoặc `FOUNDATION_BRIDGE` được định nghĩa tại `book/FOUNDATION_CHAPTERS.md` không?
- [ ] Chương 22 đến 28 có được giữ nguyên trạng và đóng băng không?
- [ ] Có xuất hiện bất kỳ nội dung nào thuộc về Chương 29 không? (Nghiêm cấm tuyệt đối).
- [ ] Chính văn chương có loại bỏ hoàn toàn bullet point spam không?
- [ ] Tỷ lệ tiếng Việt có đạt mục tiêu ~99% văn phong kỹ thuật chuẩn mực không?
- [ ] Đã phân biệt chính xác giữa compiler assembly listing và machine disassembly chưa?
- [ ] Bằng chứng kiểm chứng đã được ghi nhận đầy đủ trong thư mục `.workspace/foundation-evidence/` chưa?
