# PHỤ LỤC A — ATLAS LỖI GO
## Đọc lỗi từ triệu chứng đến nguyên nhân

Phụ lục này là tài liệu tra cứu kỹ thuật và phản xạ chẩn đoán nhanh, đóng vai trò điểm hội tụ cuối cùng cho các lỗi Go và lỗi vận hành xuất hiện xuyên suốt cuốn sách theo nguyên tắc Grayscale-first. Mỗi mục gồm: mã định danh chẩn đoán (bao gồm chuỗi lỗi thực tế `EXACT`, giá trị sentinel chuẩn `SENTINEL`, trạng thái nền tảng `STATUS`, hoặc nhóm hiện tượng chẩn đoán `FAMILY`); bản chất cơ chế trong 1 câu; điểm cảnh báo hiểu lầm (`!`) nếu có; hành động kiểm tra đầu tiên (`→`); cùng tham chiếu chương (`[ChX,Y]`).

### Bảng phân nhóm Taxonomy

| Nhóm | Tên nhóm | Phạm vi chẩn đoán | Mã lỗi |
| :--- | :--- | :--- | :--- |
| **A** | Compiler & Type System | Lỗi biên dịch, hệ thống kiểu, interface, scope và syntax | A01–A14 |
| **B** | Runtime & Panic | Crash process, nil pointer dereference, bounds, panic | B01–B11 |
| **C** | Error Values & I/O | Sentinel errors, stream truncated, encoding/decoding | C01–C08 |
| **D** | Context & Cancellation | Hủy tác vụ, timeout, deadline cascade, rò rỉ context | D01–D04 |
| **E** | Filesystem & Process | File I/O, quyền hạn Linux, binary PATH, signals OS | E01–E07 |
| **F** | Network / HTTP / TLS | DNS resolution, TCP handshake, reset socket, TLS/x509 | F01–F11 |
| **G** | Database | Connection pool, locking SQLite, transaction lifecycle | G01–G06 |
| **H** | Concurrency | Deadlock toàn cục, data race warning, goroutine leak | H01–H05 |
| **I** | Modules / Test / Toolchain | go.mod resolution, go vet static analysis, go test timeout | I01–I08 |
| **J** | Container / Kubernetes / CI-CD | OOMKilled, CrashLoopBackOff, probe failure, gate reject | J01–J10 |

### Bản đồ phản xạ 30 giây

| Triệu chứng nhận diện | Hướng tra | Triệu chứng nhận diện | Hướng tra |
| :--- | :--- | :--- | :--- |
| Không biên dịch được mã nguồn? | **Nhóm A** | Sự cố DNS / TCP / TLS / HTTP? | **Nhóm F** |
| Biên dịch được nhưng panic / crash? | **Nhóm B** | Database nghẽn / lỗi transaction? | **Nhóm G** |
| Hàm trả về `err != nil` / I/O stream? | **Nhóm C** | Data race / deadlock / leak goroutine? | **Nhóm H** |
| Tác vụ bị timeout / cancel? | **Nhóm D** | Lỗi go build / test / vet / module? | **Nhóm I** |
| Lỗi file / permission / process? | **Nhóm E** | Pod crash / OOM / probe fail / gate? | **Nhóm J** |

---

## A — Compiler & Type System

### A01 `undefined: x`
Không tìm thấy identifier trong scope hiện tại hoặc identifier chưa được export từ package ngoài.
→ Kiểm tra lỗi chính tả tên biến/hàm, scope khai báo, hoặc viết hoa chữ cái đầu nếu gọi từ package khác. [Ch1,3,5]

### A02 `no new variables on left side of :=`
Tất cả các biến ở vế trái toán tử `:=` đều đã được khai báo trước đó trong cùng một scope.
→ Đổi toán tử sang phép gán thường `=`, hoặc bổ sung ít nhất một biến mới vào vế trái. [Ch1,2]

### A03 `imported and not used: "pkg"`
Package được import vào file nguồn nhưng không có identifier nào trong file tham chiếu đến nó.
→ Xóa dòng import thừa, dùng blank identifier `_ "pkg"` nếu cần chạy hàm `init()`, hoặc chạy `goimports`. [Ch1,5]

### A04 `declared and not used: x`
Biến cục bộ được khai báo nhưng không có bất kỳ dòng code nào tiếp theo đọc hay sử dụng giá trị của nó.
→ Sử dụng biến vào logic, gán vào blank identifier `_ = x` nếu đang debug dở, hoặc loại bỏ khai báo thừa. [Ch1,2]

### A05 `cannot use x (variable of type T1) as T2 value in argument`
Sai khác kiểu dữ liệu trong phép gán hoặc truyền đối số; Go không hỗ trợ ép kiểu ngầm định (implicit coercion).
→ Thực hiện ép kiểu tường minh `T2(x)` nếu hai kiểu tương thích, hoặc sửa signature của hàm nhận. [Ch2,3,14]

### A06 `assignment mismatch`
* `1 variable but f returns 2 values`
* `2 variables but f returns 1 value`
Số lượng biến nhận ở vế trái không khớp chính xác với số lượng giá trị trả về của hàm ở vế phải.
→ Kiểm tra signature của hàm gọi và hứng đủ tất cả các giá trị trả về (dùng `_` để bỏ qua nếu cần). [Ch1,4]

### A07 `missing return`
Hàm có khai báo kiểu dữ liệu trả về nhưng tồn tại nhánh rẽ control-flow đi đến cuối block mà không có lệnh `return`.
→ Rà soát các nhánh `if/else`, `switch/case` để bảo đảm mọi luồng thực thi đều trả về giá trị hoặc panic. [Ch1,4]

### A08 `invalid operation: operator not defined on struct`
Sử dụng toán tử so sánh (`==`, `!=`) trên struct chứa ít nhất một field không thể so sánh (như slice, map, func).
→ So sánh từng field có thể so sánh, hoặc tự viết hàm helper so sánh nghiệp vụ chuyên biệt. [Ch2,3]

### A09 `cannot assign to struct field in map`
Không thể gán trực tiếp field của struct nằm trong map (ví dụ `m["k"].Field = v`) vì map value không có địa chỉ cố định.
→ Lấy struct ra biến tạm, cập nhật field rồi gán ngược lại vào map, hoặc dùng map chứa pointer `map[K]*V`. [Ch2,3]

### A10 `cannot take the address of x`
Toán tử lấy địa chỉ `&` được áp dụng lên unaddressable value (giá trị trả về của hàm, hằng số, map index expression).
→ Gán giá trị đó vào một biến tạm cục bộ trước khi thực hiện lấy địa chỉ `&temp`. [Ch2,14]

### A11 `constant overflows int`
Giá trị hằng số vượt quá giới hạn biểu diễn bit của kiểu số nguyên đích trong kiến trúc hiện tại.
→ Chỉ định kiểu số nguyên có độ rộng bit lớn hơn (`int64`, `uint64`), hoặc sử dụng package `math/big`. [Ch1,2]

### A12 `syntax error: unexpected newline, expecting comma or }`
Thiếu dấu phẩy `,` ở phần tử cuối cùng của composite literal hoặc danh sách tham số nhiều dòng (multi-line).
→ Bổ sung dấu phẩy `,` vào cuối dòng ngay trước dấu đóng ngoặc nhọn `}` hoặc ngoặc đơn `)`. [Ch1,3]

### A13 `invalid type assertion: x.(T)`
Thực hiện cú pháp type assertion trên một biến không phải kiểu interface (`non-interface type`).
→ Chỉ áp dụng type assertion trên biến kiểu interface; kiểm tra lại kiểu dữ liệu thực tế của biến `x`. [Ch3,14,19]

### A14 `x does not implement I (missing method M)`
* `method M has pointer receiver`
Type cụ thể không thỏa mãn interface vì thiếu method hoặc sai khác receiver (pointer receiver vs value receiver).
→ Kiểm tra receiver của method `M`: nếu là pointer receiver `*T`, đối tượng truyền vào phải là địa chỉ `&val`. [Ch3,5,19]

---

## B — Runtime & Panic

### B01 `panic: runtime error: invalid memory address or nil pointer dereference`
Truy cập field hoặc gọi method trên một con trỏ hoặc interface có giá trị `nil`.
! Con trỏ nil là nguyên nhân hàng đầu gây crash process; tuyệt đối không dùng `recover()` bừa bãi để che giấu.
→ Thêm kiểm tra `if ptr == nil` trước khi truy cập, hoặc rà soát constructor/hàm khởi tạo chưa gán con trỏ. [Ch2,3,12]

### B02 `panic: runtime error: index out of range [x] with length y`
Truy cập phần tử của slice hoặc mảng tại chỉ số âm hoặc lớn hơn hay bằng độ dài hiện tại `len`.
→ Kiểm tra `len(s)` trước khi truy cập trực tiếp qua index, hoặc ưu tiên duyệt bằng vòng lặp `for range`. [Ch2,7]

### B03 `panic: runtime error: slice bounds out of range [:x] with capacity y`
Biểu thức cắt slice `s[low:high]` có cận trên `high` vượt quá sức chứa `cap(s)` hoặc cận dưới lớn hơn cận trên.
→ Kiểm tra sức chứa `cap(s)` trước khi reslice, hoặc bảo đảm `low <= high <= cap`. [Ch2,7]

### B04 `panic: runtime error: makeslice: len out of range`
Hàm `make([]T, len, cap)` nhận tham số `len` hoặc `cap` là số âm, hoặc `len > cap`, hoặc vượt trần bộ nhớ hệ thống.
→ Rà soát phép tính toán kích thước buffer cấp phát; bảo đảm biến kích thước luôn dương và nằm trong ngưỡng an toàn. [Ch2,7]

### B05 `panic: assignment to entry in nil map`
Thực hiện thao tác gán giá trị vào một key của map chưa được khởi tạo (`nil map`).
→ Khởi tạo map bằng hàm `make(map[K]V)` hoặc map literal `{}` trước khi ghi dữ liệu. [Ch2,3]

### B06 `panic: send on closed channel`
Thực hiện hành vi gửi dữ liệu vào một channel đã bị gọi lệnh `close()`.
! Đóng channel là quy ước thuộc về quyền sở hữu (channel ownership): chỉ bên sở hữu hoặc producer duy nhất mới được đóng channel sau khi gửi xong mọi dữ liệu; nếu có nhiều sender đồng thời, không sender đơn lẻ nào được tự ý close channel mà phải dùng `sync.Once` hoặc cơ chế điều phối riêng.
→ Tái cấu trúc ownership: gom quyền đóng channel về một goroutine điều phối hoặc dùng `sync.Once` để bảo đảm không có sender nào ghi sau khi đóng. [Ch8,9,12]

### B07 `panic: close of closed channel`
Gọi lệnh `close()` lần thứ hai trên cùng một channel đã được đóng trước đó.
→ Sử dụng `sync.Once` để bảo đảm đóng channel duy nhất một lần, hoặc kiểm soát lifecycle đóng tập trung. [Ch8,9]

### B08 `panic: interface conversion: interface {} is T1, not T2`
Ép kiểu dạng assertion `v := x.(T2)` thất bại trong runtime khi giá trị thực tế bên trong là `T1` hoặc `nil`.
→ Luôn luôn sử dụng cú pháp comma-ok an toàn: `v, ok := x.(T2)` và kiểm tra biến cờ `ok` trước khi sử dụng. [Ch3,14,19]

### B09 `fatal error: concurrent map read and map write`
Nhiều goroutine cùng truy cập đọc và ghi đồng thời vào một biến kiểu `map` chuẩn mà không có cơ chế khóa đồng bộ.
! Phân biệt rõ: đây là crash cưỡng bức từ cơ chế kiểm tra nội tại của Go runtime (phát hiện cờ ghi đồng thời trong cấu trúc map nội bộ, không thể chặn bằng recover); khác với cảnh báo data race tổng quát từ ThreadSanitizer (`-race`) vốn quét trên mọi ô nhớ.
→ Bảo vệ map bằng `sync.RWMutex`, dùng `sync.Map` khi phù hợp, hoặc tuần tự hóa qua channel; kiểm thử với `go test -race`. [Ch8,9,20]

### B10 `fatal error: stack overflow`
Hàm gọi đệ quy vô tận hoặc chuỗi lồng hàm quá sâu khiến kích thước stack của goroutine tăng trưởng liên tục vượt quá giới hạn tối đa do Go runtime quy định (`maxstacksize`).
→ Bổ sung điều kiện dừng (base case) chuẩn xác cho hàm đệ quy, hoặc chuyển đổi giải thuật sang dạng lặp (iterative). [Ch10]

### B11 `panic: sync: unlock of unlocked mutex`
Gọi phương thức `Unlock()` trên một đối tượng `sync.Mutex` hoặc `sync.RWMutex` chưa từng được `Lock()`.
→ Kiểm tra cấu trúc đặt `defer mu.Unlock()` ngay sau `mu.Lock()`, tránh gọi unlock thủ công rải rác nhiều nhánh return. [Ch8,12]

---

## C — Error Values & I/O

### C01 `io.EOF`
Tín hiệu hoàn tất stream đọc dữ liệu (đã đọc hết toàn bộ byte sẵn có, không còn byte nào phía sau).
! `io.EOF` là một sentinel marker bình thường của I/O stream, hoàn toàn không phải sự cố hay lỗi hệ thống.
→ Xử lý `io.EOF` như một điều kiện kết thúc vòng lặp đọc dữ liệu hợp lệ thay vì return failure lên tầng trên. [Ch7,11,20]

### C02 `io.ErrUnexpectedEOF`
Stream dữ liệu bị ngắt đột ngột trước khi đọc đủ số byte dự kiến (ví dụ trong `io.ReadFull` hoặc fixed-size header).
→ Kiểm tra kết nối mạng có bị ngắt giữa chừng hoặc payload truyền tải có bị cắt cụt (truncated) hay không. [Ch7,11,20]

### C03 `io.ErrShortWrite`
Hàm `Write()` ghi được ít byte hơn buffer cung cấp nhưng không trả về lỗi cụ thể từ hệ thống bên dưới.
→ Rà soát bộ đệm đích hoặc cơ chế ghi phân đoạn; bảo đảm vòng lặp ghi tiếp tục cho đến khi cạn buffer. [Ch7]

### C04 `target document exceeds byte limit`
Dữ liệu stream đi vào vượt quá ngưỡng kích thước tối đa cho phép theo chính sách an toàn (giá trị sentinel `ErrDocumentTooLarge`).
→ Bảo vệ bộ nhớ khỏi cạn kiệt (OOM); từ chối xử lý tiếp và trả về lỗi payload vượt giới hạn cho caller. [Ch7,20]

### C05 `json: cannot unmarshal string into Go struct field of type int`
Kiểu dữ liệu trong JSON payload không tương thích với định nghĩa kiểu của struct field đích trong Go.
→ Đối chiếu schema JSON nguồn, điều chỉnh kiểu dữ liệu struct field hoặc triển khai `json.Unmarshaler` tùy biến. [Ch7,14,20]

### C06 `json: syntax error: unexpected end of JSON input`
Chuỗi JSON đưa vào `json.Unmarshal` bị rỗng hoặc bị ngắt cụt giữa chừng cú pháp.
! Phân biệt rõ: `json.Unmarshal` trả về lỗi cú pháp này khi buffer rỗng; trong khi `json.Decoder.Decode()` trên stream rỗng trả về `io.EOF`, và chỉ trả về unexpected end hoặc `io.ErrUnexpectedEOF` khi stream bị cắt cụt khi đang parse dở token.
→ Kiểm tra request body có rỗng không (`len == 0`), và xác thực header `Content-Length` từ client truyền lên trước khi decode. [Ch7,11,20]

### C07 `sql: no rows in result set`
Truy vấn `QueryRowContext` không tìm thấy bất kỳ bản ghi nào khớp với điều kiện lọc trong cơ sở dữ liệu (`sql.ErrNoRows`).
→ Dùng `errors.Is(err, sql.ErrNoRows)` để phân biệt trường hợp không có dữ liệu với lỗi truy vấn database thực sự. [Ch13,20]

### C08 `sql: transaction has already been committed or rolled back`
Gọi lệnh `Commit()` hoặc `Rollback()` trên một transaction cơ sở dữ liệu (`*sql.Tx`) đã kết thúc trước đó (`sql.ErrTxDone`).
→ Rà soát pattern `defer tx.Rollback()`; nếu `Commit()` đã thành công thì rollback sau đó trả về lỗi này và an toàn để bỏ qua. [Ch13]

---

## D — Context & Cancellation

### D01 `context canceled`
Context bị hủy chủ động thông qua việc gọi hàm `cancel()` từ caller hoặc do server nhận tín hiệu shutdown.
! Phân biệt rõ với timeout: cancellation xuất phát từ hành động chủ động hủy của client hoặc quy trình dừng service.
→ Dừng vòng lặp xử lý của goroutine, dọn dẹp tài nguyên và trả về trạng thái canceled (áp dụng quy ước mã phi chuẩn HTTP 499 Client Closed Request phổ biến trong microservices / OutcomeCancel). [Ch4,11,12,20]

### D02 `context deadline exceeded`
Tác vụ không hoàn thành trong khoảng thời gian timeout hoặc trước mốc thời gian deadline đã ấn định (`context.DeadlineExceeded`).
! Client bị timeout không có nghĩa là downstream service đã ngừng xử lý; kết nối có thể vẫn đang chạy ngầm gây nghẽn.
→ Xác định nơi khởi tạo deadline (`WithTimeout`), đo lường độ trễ từng phân đoạn và điều chỉnh timeout hợp lý. [Ch4,11,12,20]

### D03 Client Disconnect During Body Read
Client chủ động ngắt kết nối TCP hoặc request context bị hủy trong khi server đang trong tiến trình đọc stream `req.Body`. Trong Go, hàm `Read()` khi đó trả về lỗi ngữ nghĩa `context.Canceled` (hoặc `read: connection reset by peer` / `http.ErrBodyReadAfterClose`).
→ Kiểm tra `r.Context().Done()` hoặc `errors.Is(err, context.Canceled)` trong các tác vụ đọc stream để kịp thời giải phóng CPU và buffer. [Ch11,12,20]

### D04 Server Graceful Shutdown Timeout
Phương thức `server.Shutdown(ctx)` chạm mốc timeout của context truyền vào trước khi toàn bộ các kết nối HTTP đang hoạt động được đóng mềm mại, trả về `context.DeadlineExceeded`.
→ Tăng thời lượng shutdown grace period hoặc điều tra các goroutine/request xử lý tác vụ dài không chịu lắng nghe `ctx.Done()`. [Ch12,20]

---

## E — Filesystem & Process

### E01 `no such file or directory`
Đường dẫn tập tin hoặc thư mục mục tiêu không tồn tại trên filesystem của hệ điều hành (`os.ErrNotExist`).
→ Kiểm tra đường dẫn tuyệt đối/tương đối, working directory thực tế của process, hoặc mount path trong container. [Ch7,15,17]

### E02 `permission denied`
Process không có đủ quyền đọc, ghi, hoặc thực thi tập tin/thư mục mục tiêu (`os.ErrPermission`).
→ Kiểm tra file mode permission (`chmod`), UID/GID của container user (non-root), hoặc chính sách SELinux/AppArmor. [Ch15,17]

### E03 `file already exists`
Cố gắng tạo mới tập tin với cờ độc quyền (`os.O_EXCL`) hoặc tạo thư mục (`os.Mkdir`) khi đường dẫn đã tồn tại (`os.ErrExist`).
→ Sử dụng `os.IsExist(err)` để xử lý phân nhánh ghi đè hoặc bỏ qua nếu tập tin đã sẵn sàng. [Ch7,15]

### E04 `read-only file system`
Cố gắng ghi dữ liệu vào một filesystem được mount ở chế độ chỉ đọc (lỗi hệ thống `EROFS`, ví dụ trong distroless hoặc container bảo mật cao).
→ Chuyển đường dẫn ghi file tạm sang thư mục được mount volume riêng biệt (như `/tmp` kiểu `emptyDir`). [Ch17,18]

### E05 `executable file not found in $PATH`
Hàm `exec.LookPath` hoặc `exec.Command` không tìm thấy file thực thi tương ứng trong các thư mục của biến môi trường `$PATH` (`exec.ErrNotFound`).
→ Kiểm tra base image của container (distroless không có sẵn shell/ls), cung cấp đường dẫn tuyệt đối, hoặc cài đặt tool. [Ch15,17]

### E06 `signal: terminated / signal: killed`
Process bị dừng đột ngột bởi tín hiệu hệ điều hành: SIGTERM khi dừng dịch vụ có phối hợp, hoặc SIGKILL khi bị cưỡng chế tiêu diệt (kill -9, hết hạn grace period, hoặc do Linux kernel OOM Killer).
! SIGKILL có thể đến từ nhiều nguyên nhân (admin kill, timeout của bộ điều phối, cgroup limit); không tự động suy diễn mọi SIGKILL đều là OOM.
→ Kiểm tra dmesg/journalctl hoặc Kubernetes termination reason để xác định process bị kill bởi OOM Killer hay do lệnh quản trị bên ngoài. [Ch10,12,17]

### E07 `failed to load bpf program: operation not permitted / permission denied (eBPF Verifier Error)`
* `failed to load bpf program: operation not permitted`
* `failed to load bpf program: permission denied: ... (verifier log)`
Lỗi nạp chương trình eBPF vào Linux kernel thông qua syscall `SYS_BPF` khi tiến trình Go thiếu quyền quản trị (`CAP_BPF`/`CAP_SYS_ADMIN`), hoặc bytecode bị Kernel Verifier từ chối do vi phạm an toàn bộ nhớ (truy cập con trỏ ngoài biên, vòng lặp không xác định, hoặc stack vượt quá 512 bytes).
! Kernel Verifier từ chối ngay lập tức ở cấp hệ điều hành trước khi chương trình eBPF được thực thi; phía Go nhận lỗi chi tiết qua Verifier Log.
→ Chạy ứng dụng với quyền root hoặc cấp capability `setcap cap_bpf,cap_sys_admin+ep <binary>`, kiểm tra mã C eBPF bảo đảm mọi con trỏ đều qua hàm `bpf_probe_read_*` và kích thước stack < 512 bytes. [Ch27]

---

## F — Network / HTTP / TLS

### F01 `dial tcp: lookup host: no such host`
Hệ thống DNS resolver không thể phân giải tên miền mục tiêu thành địa chỉ IP hợp lệ (`net.DNSError`).
→ Kiểm tra cấu hình DNS cục bộ (`/etc/resolv.conf`), service discovery của cụm Kubernetes (CoreDNS), hoặc lỗi chính tả host. [Ch11,16,20]

### F02 `dial tcp: connect: connection refused`
Địa chỉ IP máy chủ hoạt động nhưng tại cổng đích không có bất kỳ process nào đang lắng nghe (nhận gói tin TCP RST).
→ Xác nhận service mục tiêu đã khởi chạy, bind đúng địa chỉ (`0.0.0.0` thay vì `127.0.0.1`), và port đích chính xác. [Ch4,11,16,20]

### F03 `i/o timeout / dial tcp: i/o timeout`
Quá trình bắt tay TCP hoặc thao tác đọc/ghi socket không nhận được phản hồi trước khi `net.Dialer.Timeout` kết thúc.
→ Kiểm tra tường lửa/security group có đang chặn gói tin SYN không, routing mạng, hoặc server mục tiêu bị treo cứng. [Ch11,16,20]

### F04 `read: connection reset by peer`
Phía đối tác (peer) của kết nối TCP đã gửi gói tin RST để ngắt kết nối cưỡng bức ngay lập tức.
! Thường xảy ra khi process phía bên kia bị crash đột ngột, khởi động lại, hoặc tràn socket buffer.
→ Kiểm tra log của server phía đối tác xem có sự cố panic, OOM, hay timeout của load balancer trung gian không. [Ch11,12,20]

### F05 `write: broken pipe`
Client cố gắng ghi dữ liệu vào socket TCP trong khi phía nhận đã đóng chiều đọc và gửi tín hiệu FIN/RST trước đó.
→ Bắt lỗi ghi socket, ngừng gửi dữ liệu lên kết nối đã chết và dọn dẹp các tài nguyên liên đới của handler. [Ch11,12,20]

### F06 `http: server closed idle connection`
Connection pool HTTP/1.1 cố gắng tái sử dụng kết nối nhưng server phía đối diện đã đóng socket do hết hạn idle timeout.
→ Bật cơ chế retry an toàn cho các request có tính idempotent, hoặc cấu hình `IdleConnTimeout` của client nhỏ hơn server. [Ch11,20]

### F07 `x509: certificate signed by unknown authority`
Bắt tay TLS thất bại vì chứng chỉ số của máy chủ không được ký bởi Certificate Authority (CA) có trong trust store của client.
! Tuyệt đối không bật `InsecureSkipVerify: true` trong môi trường production vì sẽ vô hiệu hóa hoàn toàn bảo mật TLS.
→ Thêm Root CA nội bộ vào trust store của hệ điều hành/container hoặc nạp CA tùy biến qua `tls.Config.RootCAs`. [Ch11,17,20]

### F08 `x509: certificate has expired or is not yet valid`
Chứng chỉ số TLS của máy chủ đã quá hạn sử dụng, hoặc đồng hồ hệ thống trên máy chạy Go bị lệch thời gian (time drift).
→ Kiểm tra thời hạn chứng chỉ bằng `openssl x509`, gia hạn chứng chỉ hoặc đồng bộ lại đồng hồ hệ điều hành qua NTP. [Ch11,17]

### F09 `x509: certificate is valid for X, not Y`
Tên miền truy cập không khớp với danh sách Subject Alternative Names (SAN) được cấp trong chứng chỉ số TLS.
→ Cấp lại chứng chỉ với trường SAN bao quát đúng tên miền hoặc địa chỉ IP đang sử dụng để kết nối. [Ch11,17]

### F10 Unread Response Body (Lost Connection Reuse)
Client đóng response body (`resp.Body.Close()`) khi dữ liệu stream chưa được đọc đến `io.EOF`, khiến `net/http.Transport` không thể tái sử dụng socket TCP trong pool cho các request tiếp theo.
! Bounded drain (`io.LimitReader`) chỉ giúp kết nối đủ điều kiện tái sử dụng (`ReusedEligible = true`) khi toàn bộ dữ liệu thực sự chạm `io.EOF` trong ngưỡng giới hạn (như 16 KiB); nếu payload vượt quá giới hạn, socket buộc phải bị đóng để bảo vệ bộ nhớ.
→ Luôn đọc cạn có giới hạn bằng `io.LimitReader` và chỉ coi kết nối là reuse-eligible khi số byte còn lại chạm `io.EOF` trước khi `Close()`. [Ch11,20]

### F11 `RequestTimeTooSkewed`
* `RequestTimeTooSkewed: The difference between the request time and the current time is too large.`
Lỗi xác thực chữ ký đám mây (`AWS SigV4 HTTP 403 Forbidden`) khi đồng hồ hệ thống của máy client bị lệch quá 15 phút so với đồng hồ chuẩn của AWS Server, khiến timestamp trong chữ ký SigV4 bị từ chối để chống tấn công phát lại (replay attack).
! Thường gặp trong container hoặc máy ảo khi tiến trình đồng bộ thời gian NTP bị lỗi hoặc đóng băng sau khi suspend.
→ Đồng bộ lại đồng hồ hệ điều hành thông qua dịch vụ chrony hoặc NTP daemon (`chronyc makestep`). [Ch24]

---

## G — Database

### G01 `sql: database is closed`
Thực hiện thao tác truy vấn hoặc thực thi lệnh trên đối tượng `*sql.DB` sau khi phương thức `db.Close()` đã được gọi (`sql.ErrConnDone`).
→ Rà soát lifecycle của `*sql.DB`: chỉ khởi tạo duy nhất một lần lúc ứng dụng startup và chỉ đóng khi toàn bộ process tắt. [Ch13,20]

### G02 `driver: bad connection`
Kết nối vật lý tới database bị ngắt đột ngột phía máy chủ hoặc mạng (`driver.ErrBadConn`). Đồng thời, khi connection pool bị cạn kiệt (`SetMaxOpenConns`), các truy vấn mới sẽ bị xếp hàng chờ đến khi `context deadline exceeded` thay vì trả về một error string riêng từ `database/sql`.
! `database/sql` không có error string chuẩn mang tên "connection pool exhausted"; khi hết connection, hệ thống xếp hàng đợi cho đến khi context timeout.
→ Kiểm tra health check kết nối, tăng `SetMaxOpenConns` nếu tải hợp lệ, hoặc đặt timeout cho context truy vấn để tránh goroutine bị treo vô hạn. [Ch13,20]

### G03 Unclosed sql.Rows (Connection Pool Starvation)
Hiện tượng quên gọi `rows.Close()` sau khi duyệt qua kết quả truy vấn `db.QueryContext`, khiến kết nối database bên dưới bị giam giữ vĩnh viễn ngoài pool và làm cạn kiệt kết nối của ứng dụng.
! `database/sql` không phát ra chuỗi lỗi báo quên close; triệu chứng thực tế là pool cạn kiệt âm thầm và các truy vấn kế tiếp bị treo đến khi context timeout.
→ Luôn đặt `defer rows.Close()` ngay sau dòng kiểm tra `if err != nil` của lệnh `db.QueryContext`. [Ch13,20]

### G04 `sqlite: database is locked / busy`
SQLite gặp xung đột ghi đồng thời từ nhiều transaction hoặc goroutine trên cùng một tập tin cơ sở dữ liệu (`busy / locked`).
→ Kích hoạt chế độ WAL (`_journal_mode=WAL`), thiết lập busy timeout (`_busy_timeout=5000`), hoặc tuần tự hóa luồng ghi. [Ch13,20]

### G05 `UNIQUE constraint failed`
Cố gắng chèn hoặc cập nhật bản ghi có giá trị trùng lặp trên cột được đánh chỉ mục duy nhất (PRIMARY KEY hoặc UNIQUE).
→ Bắt lỗi conflict, áp dụng chính sách `ON CONFLICT DO UPDATE` (upsert) hoặc kiểm tra sự tồn tại trước khi ghi. [Ch13,20]

### G06 `FOREIGN KEY constraint failed`
Thao tác insert hoặc delete vi phạm tính toàn vẹn quan hệ khóa ngoại giữa bảng cha và bảng con.
→ Kiểm tra thứ tự thao tác dữ liệu: luôn chèn bản ghi bảng cha trước bảng con, và xóa bản ghi bảng con trước bảng cha. [Ch13,20]

---

## H — Concurrency

### H01 `fatal error: all goroutines are asleep - deadlock!`
Tất cả các goroutine trong chương trình đều đang bị block (chờ channel, mutex) mà không còn bất kỳ goroutine nào chạy để mở khóa.
! Go runtime chỉ phát hiện deadlock khi TOÀN BỘ goroutine đều ngủ; nếu còn 1 goroutine chạy nền (như ticker), deadlock cục bộ bị bỏ qua!
→ Thiết kế đồ thị phụ thuộc của lock/channel; luôn tuân thủ thứ tự acquisition lock nhất quán và tránh chờ đợi vòng tròn. [Ch8,9,12]

### H02 `WARNING: DATA RACE`
Go race detector (`go test -race` / `go run -race`) phát hiện ít nhất hai goroutine cùng truy cập một ô nhớ và có ít nhất một thao tác ghi.
! Tuyệt đối không phớt lờ cảnh báo data race; race condition dẫn đến dữ liệu bị hỏng âm thầm và crash ngẫu nhiên không thể dự đoán.
→ Bảo vệ vùng nhớ dùng chung bằng `sync.Mutex`, chuyển sang toán tử `sync/atomic`, hoặc tái cấu trúc truyền dữ liệu qua channel. [Ch8,9,20]

### H03 Goroutine Leak
Goroutine được sinh ra nhưng không bao giờ kết thúc vì bị block vô hạn trên channel không có buffer, mutex không được nhả, hoặc I/O thiếu context cancellation.
! Go runtime không tự động garbage collect goroutine bị block; một goroutine bị leak sẽ giữ toàn bộ stack frame và bộ nhớ tham chiếu liên quan.
→ Luôn truyền `context.Context` có timeout/cancellation vào goroutine; bảo đảm mọi nhánh rẽ đều có điều kiện thoát hoặc dùng buffered channel thích hợp. [Ch8,9,12,20]

### H04 `panic: sync: negative WaitGroup counter`
Phương thức `wg.Add()` nhận giá trị âm làm counter nhỏ hơn 0, hoặc phương thức `wg.Done()` bị gọi nhiều lần hơn số lần `Add()`.
→ Kiểm tra số lần gọi `Done()`; luôn gọi `Add()` TRƯỚC KHI khởi chạy goroutine worker, tuyệt đối không gọi `Add()` bên trong worker. [Ch8,9]

### H05 `panic: sync: WaitGroup misuse: Add called concurrently with Wait`
Phương thức `wg.Add()` được gọi đồng thời trong khi một goroutine khác đang thực thi phương thức `wg.Wait()`.
→ Toàn bộ các thao tác `wg.Add()` khởi tạo phải hoàn tất trước khi lệnh `wg.Wait()` bắt đầu được gọi. [Ch8,9]

---

## I — Modules / Test / Toolchain

### I01 `go: cannot find main module`
Lệnh `go build` hoặc `go test` được thực thi tại một thư mục không chứa file `go.mod` và không thuộc không gian làm việc `go.work`.
→ Di chuyển terminal vào đúng thư mục con chứa module cần thao tác (`working-directory`), hoặc khởi tạo module bằng `go mod init`. [Ch1,5,18]

### I02 `go: module X: git fetch: authentication required`
Go module resolver không thể tải mã nguồn của module private do thiếu thông tin xác thực Git qua SSH hoặc Personal Access Token.
→ Cấu hình biến môi trường `GOPRIVATE=github.com/myorg/*` và thiết lập Git credential helper hoặc SSH key tương ứng. [Ch5,18]

### I03 `go vet: composite literal uses unkeyed fields`
Khai báo struct literal không chỉ định tên field tường minh (ví dụ viết `Point{1, 2}` thay vì `Point{X: 1, Y: 2}`).
→ Bổ sung tên field vào struct literal để tránh lỗi vỡ mã nguồn khi struct được thêm trường mới trong tương lai. [Ch3,6]

### I04 `go vet: unreachable code`
Đoạn mã nằm ở vị trí không bao giờ có thể được thực thi tới (ngay sau lệnh `return`, `panic`, hoặc vòng lặp vô tận không có break).
→ Loại bỏ đoạn mã chết (dead code) không cần thiết hoặc điều chỉnh lại cấu trúc điều hướng control-flow. [Ch1,4]

### I05 `go test: no Go files in directory`
Thư mục chỉ định trong lệnh test không chứa bất kỳ tập tin mã nguồn Go (`*.go`) hợp lệ nào thuộc package cần kiểm thử.
→ Kiểm tra lại đường dẫn package hoặc bổ sung tập tin kiểm thử `*_test.go` tương ứng vào thư mục. [Ch6,18]

### I06 `go test: build constraints exclude all Go files`
Tất cả các file mã nguồn Go trong thư mục đều bị loại trừ bởi build tags chỉ định ở đầu file (ví dụ `//go:build integration`).
→ Truyền cờ build tags tương ứng khi thực thi lệnh kiểm thử, ví dụ: `go test -tags=integration ./...`. [Ch6,18]

### I07 `go test: timed out after Xm`
Toàn bộ suite kiểm thử hoặc một test cụ thể chạy vượt quá giới hạn thời gian cho phép (mặc định 10 phút hoặc cờ `-timeout`).
→ Điều tra các test bị treo do deadlock, rò rỉ goroutine hoặc sleep quá lâu; chạy `go test -v -timeout=30s` để cô lập test lỗi. [Ch6,8,20]

### I08 `API rate limit exceeded`
* `API rate limit exceeded for user ID <id>`
Lỗi từ chối (`GitHub API HTTP 403 Forbidden`) khi số lượng request gửi tới máy chủ GitHub vượt quá định mức cho phép (5.000 requests/giờ cho authenticated token hoặc 60 requests/giờ cho IP nặc danh), hoặc vi phạm chính sách chống lạm dụng Secondary Rate Limit (`Retry-After`).
! Thường gặp khi các bot tự động hóa hoặc CI/CD pipeline gửi yêu cầu liên tục trong vòng lặp mà không kiểm tra hạn mức còn lại.
→ Bóc tách header `X-RateLimit-Reset` hoặc `Retry-After` để tạm dừng tiến trình (sleep with jitter) cho đến khi quota được khôi phục trước khi gửi yêu cầu tiếp theo. [Ch25]

---

## J — Container / Kubernetes / CI-CD

### J01 CrashLoopBackOff
Trạng thái chờ (`Waiting Reason`) của Kubernetes Pod khi container liên tục khởi động, gặp lỗi panic hoặc exit code > 0 rồi tắt, khiến kubelet áp dụng giãn cách khởi động lại.
! Đây là trạng thái điều phối của Pod (Waiting Reason) trong Kubernetes, không phải chuỗi lỗi do Go runtime sinh ra.
→ Kiểm tra log của container trước khi crash bằng lệnh `kubectl logs <pod> --previous`, rà soát biến môi trường và config bị thiếu. [Ch17,18,21]

### J02 OOMKilled (Exit Code 137)
Trạng thái kết thúc (`Terminated Reason`) của container trong Kubernetes khi tổng bộ nhớ RAM của process vượt hạn mức `resources.limits.memory` và bị Linux cgroup OOM Killer gửi SIGKILL.
! OOMKilled là trạng thái báo cáo bởi kubelet/container runtime; bên trong process Go chỉ nhận tín hiệu SIGKILL cưỡng bức mà không kịp chạy defer.
→ Kiểm tra rò rỉ bộ nhớ qua heap profile (`pprof`), điều chỉnh thuật toán caching hoặc nâng hạn mức `limits.memory` cho pod. [Ch10,17,21]

### J03 ImagePullBackOff / ErrImagePull
Trạng thái chờ (`Waiting Reason`) của Pod khi Kubernetes không thể tải container image từ registry (sai image tag, thiếu secret xác thực, hoặc nghẽn mạng).
! Đây là trạng thái lỗi kéo image của Kubernetes control plane, xảy ra trước khi container Go khởi chạy.
→ Kiểm tra tên image và tag, cấu hình `imagePullSecrets` cho service account, hoặc kiểm tra kết nối mạng egress của cụm. [Ch17,18]

### J04 CreateContainerConfigError
Trạng thái lỗi cấu hình (`Waiting Reason`) khi Kubernetes không tìm thấy ConfigMap hoặc Secret được tham chiếu trong cấu hình Pod.
! Lỗi ở cấp scheduler/kubelet khi chuẩn bị môi trường chạy container, xảy ra trước khi binary Go được thực thi.
→ Chạy `kubectl describe pod <pod>` để xác định chính xác tên ConfigMap/Secret đang bị thiếu và tạo bổ sung vào namespace. [Ch17,21]

### J05 Readiness probe failed
* `HTTP probe failed with statuscode: 503`
Sự kiện chẩn đoán (`Kubelet Event`) phát ra khi endpoint kiểm tra mức độ sẵn sàng (`/readyz`) trả về mã lỗi hoặc timeout, khiến pod bị rút khỏi danh sách nhận traffic của Service.
! Đây là sự kiện chẩn đoán (Kubelet Event); container Go vẫn đang chạy bình thường nhưng chưa sẵn sàng phục vụ lưu lượng.
→ Kiểm tra tình trạng kết nối đến các dependency hạ tầng (database, cache) và rà soát logic kiểm tra sẵn sàng của handler. [Ch12,17,20,21]

### J06 Liveness probe failed
Sự kiện chẩn đoán (`Kubelet Event`) phát ra khi endpoint kiểm tra sự sống (`/livez`) không phản hồi hoặc trả về mã lỗi, khiến Kubernetes ra lệnh tiêu diệt và khởi động lại container.
! Tuyệt đối không để liveness probe phụ thuộc vào database bên ngoài; nếu database chết, toàn bộ cụm pod sẽ restart dây chuyền!
→ Liveness probe chỉ được kiểm tra nội tại process (deadlock, event loop); không kiểm tra dependency bên ngoài. [Ch12,17,21]

### J07 Admission Gate Rejected
* `unsigned artifact or digest mismatch`
Trạng thái từ chối (`Admission / Policy Status`) từ Kubernetes Validating Admission Webhook hoặc Promotion Gate của CI/CD khi artifact container image không có chữ ký cosign hợp lệ hoặc digest SHA-256 không khớp với bản ghi phát hành.
! Đây là rào chắn chính sách ở tầng CI/CD delivery hoặc Kubernetes admission webhook, không phải lỗi từ runtime của ứng dụng.
→ Bảo đảm image được build và ký số thông qua pipeline CI chính thức có attestation/provenance hợp lệ trước khi promote. [Ch18]

### J08 `Operation cannot be fulfilled: the object has been modified`
* `Operation cannot be fulfilled on <resource>: the object has been modified; please apply your changes to the latest version and try again`
Lỗi từ chối (`API Server HTTP 409 Conflict`) khi một client cố gắng cập nhật đối tượng nhưng `metadata.resourceVersion` gửi lên đã lỗi thời so với bản ghi hiện hành trong etcd.
! Đây là cơ chế kiểm soát đồng thời lạc quan (Optimistic Concurrency Control) của Kubernetes nhằm ngăn chặn ghi đè mất dữ liệu giữa các client cạnh tranh.
→ Sử dụng `k8s.io/client-go/util/retry.RetryOnConflict` để đọc lại snapshot mới nhất từ API Server và áp dụng thay đổi trước khi thử lại. [Ch22]

### J09 `no kind is registered for the type in scheme`
* `no kind is registered for the type <Type> in scheme <Scheme>`
Lỗi cấu hình runtime (`Kubernetes Scheme Error`) khi một Go struct được truyền vào Controller Client hoặc Reconciler nhưng kiểu dữ liệu này chưa được đăng ký vào bảng `runtime.Scheme` thông qua hàm `AddToScheme`.
! Xảy ra phổ biến khi khởi tạo Operator với Custom Resource Definition (CRD) nhưng quên nạp `v1alpha1.AddToScheme(mgr.GetScheme())`.
→ Đăng ký SchemeBuilder của CRD vào Manager Scheme trước khi khởi động Controller. [Ch23]

### J10 Denied by Supply Chain Policy: reachable vulnerability or untrusted builder
* `reachable <SEVERITY> vulnerability <ID> in <package> (symbol: <symbol>)`
* `untrusted builder identity: <builder>`
Trạng thái chặn (`Supply Chain Verification Gate Status`) khi artifact mang theo CVE có ký hiệu thực sự được gọi trong đồ thị cuộc gọi thực thi (Call-Graph Reachability) hoặc được build từ quy trình không được cấp phép.
! Khác với các công cụ quét phụ thuộc tĩnh báo cáo hàng loạt CVE trong thư viện không dùng tới, cảnh báo này cho biết mã độc/lỗi logic nằm trên luồng thực thi trực tiếp của binary.
→ Cập nhật phiên bản dependency đã vá lỗi, loại bỏ việc gọi ký hiệu chứa lỗ hổng, hoặc kiểm tra lại builder ID trong CI workflow. [Ch26]


