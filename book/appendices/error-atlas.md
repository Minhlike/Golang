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
| **J** | Container / Kubernetes / CI-CD | OOMKilled, CrashLoopBackOff, probe failure, gate reject | J01–J11 |

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
! Nil dereference có thể làm process crash; đừng dùng recover để che lỗi mà không xác định contract và recovery boundary.
→ Thêm kiểm tra `if ptr == nil` trước khi truy cập, hoặc rà soát constructor/hàm khởi tạo chưa gán con trỏ. [Ch2,3,12]

### B02 `panic: runtime error: index out of range [x] with length y`
Truy cập phần tử của slice hoặc mảng tại chỉ số âm hoặc lớn hơn hay bằng độ dài hiện tại `len`.
→ Kiểm tra `len(s)` trước khi truy cập trực tiếp qua index, hoặc ưu tiên duyệt bằng vòng lặp `for range`. [Ch2,7]

### B03 `panic: runtime error: slice bounds out of range [:x] with capacity y`
Biểu thức cắt slice `s[low:high]` có cận trên `high` vượt quá sức chứa `cap(s)` hoặc cận dưới lớn hơn cận trên.
→ Kiểm tra sức chứa `cap(s)` trước khi reslice, hoặc bảo đảm `low <= high <= cap`. [Ch2,7]

### B04 `panic: runtime error: makeslice: len out of range`
Hàm `make([]T, len, cap)` nhận tham số `len` hoặc `cap` là số âm, hoặc `len > cap`, hoặc vượt trần bộ nhớ hệ thống.
→ Kiểm tra kích thước buffer không âm và nằm trong ngân sách; buffer độ dài 0 có thể hợp lệ theo contract. [Ch2,7]

### B05 `panic: assignment to entry in nil map`
Thực hiện thao tác gán giá trị vào một key của map chưa được khởi tạo (`nil map`).
→ Khởi tạo map bằng hàm `make(map[K]V)` hoặc map literal `{}` trước khi ghi dữ liệu. [Ch2,3]

### B06 `panic: send on closed channel`
Thực hiện hành vi gửi dữ liệu vào một channel đã bị gọi lệnh `close()`.
! Bên đóng phải biết mọi sender đã ngừng gửi. `sync.Once` chỉ tránh đóng hai lần; nó không chặn việc gửi sau khi đóng.
→ Gom quyền đóng về goroutine điều phối, chờ các sender kết thúc rồi mới `close`. Producer duy nhất có thể tự đóng sau lần gửi cuối. [Ch8,9,12]

### B07 `panic: close of closed channel`
Gọi lệnh `close()` lần thứ hai trên cùng một channel đã được đóng trước đó.
→ Sử dụng `sync.Once` để bảo đảm đóng channel duy nhất một lần, hoặc kiểm soát lifecycle đóng tập trung. [Ch8,9]

### B08 `panic: interface conversion: interface {} is T1, not T2`
Ép kiểu dạng assertion `v := x.(T2)` thất bại trong runtime khi giá trị thực tế bên trong là `T1` hoặc `nil`.
→ Luôn luôn sử dụng cú pháp comma-ok an toàn: `v, ok := x.(T2)` và kiểm tra biến cờ `ok` trước khi sử dụng. [Ch3,14,19]

### B09 `fatal error: concurrent map read and map write`
Nhiều goroutine cùng truy cập đọc và ghi đồng thời vào một biến kiểu `map` chuẩn mà không có cơ chế khóa đồng bộ.
! Đây là lỗi fatal từ kiểm tra nội tại của runtime, không thể chặn bằng `recover`; khác với `-race`, theo dõi truy cập không đồng bộ trên những đường chạy được thực thi. Cả hai không bảo đảm phát hiện mọi race trong mọi lịch chạy.
→ Bảo vệ map bằng `sync.RWMutex`, dùng `sync.Map` khi phù hợp, hoặc tuần tự hóa qua channel; kiểm thử với `go test -race`. [Ch8,9,20]

### B10 `fatal error: stack overflow`
Hàm gọi đệ quy vô tận hoặc chuỗi lồng hàm quá sâu khiến kích thước stack của goroutine tăng trưởng liên tục vượt quá giới hạn tối đa do Go runtime quy định (`maxstacksize`).
→ Bổ sung điều kiện dừng (base case) chuẩn xác cho hàm đệ quy, hoặc chuyển đổi giải thuật sang dạng lặp (iterative). [Ch10]

### B11 `fatal error: sync: unlock of unlocked mutex`
Go 1.27.1 phát lỗi fatal khi gọi `Unlock()` trên `sync.Mutex` hiện không được khóa, kể cả khi mutex đã được khóa rồi mở trước đó. `recover` không cứu được lỗi này; `sync.RWMutex` có diagnostic riêng.
→ Kiểm tra cấu trúc đặt `defer mu.Unlock()` ngay sau `mu.Lock()`, tránh gọi unlock thủ công rải rác nhiều nhánh return. [Ch8,12]

---

## C — Error Values & I/O

### C01 `io.EOF`
Tín hiệu hoàn tất stream đọc dữ liệu (đã đọc hết toàn bộ byte sẵn có, không còn byte nào phía sau).
! `io.EOF` thường đánh dấu hết stream; EOF xuất hiện sớm vẫn có thể vi phạm contract của format hoặc operation.
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

### C06 `unexpected end of JSON input`
Chuỗi JSON đưa vào `json.Unmarshal` bị rỗng hoặc bị ngắt cụt giữa chừng cú pháp.
! Phân biệt rõ: `json.Unmarshal` trả về lỗi cú pháp này khi buffer rỗng; trong khi `json.Decoder.Decode()` trên stream rỗng trả về `io.EOF`, và chỉ trả về unexpected end hoặc `io.ErrUnexpectedEOF` khi stream bị cắt cụt khi đang parse dở token.
→ Kiểm tra dữ liệu thực đọc được và lỗi decode; không dùng riêng `Content-Length` làm bằng chứng body đầy đủ. Giới hạn byte và xử lý stream rỗng theo contract API. [Ch7,11,20]

### C07 `sql: no rows in result set`
Truy vấn `QueryRowContext` không tìm thấy bất kỳ bản ghi nào khớp với điều kiện lọc trong cơ sở dữ liệu (`sql.ErrNoRows`).
→ Dùng `errors.Is(err, sql.ErrNoRows)` để phân biệt trường hợp không có dữ liệu với lỗi truy vấn database thực sự. [Ch13,20]

### C08 `sql: transaction has already been committed or rolled back`
Gọi lệnh `Commit()` hoặc `Rollback()` trên một transaction cơ sở dữ liệu (`*sql.Tx`) đã kết thúc trước đó (`sql.ErrTxDone`).
→ Rà soát pattern `defer tx.Rollback()`; nếu `Commit()` đã thành công thì rollback sau đó trả về lỗi này và an toàn để bỏ qua. [Ch13]

---

## D — Context & Cancellation

### D01 `context canceled`
Context bị hủy bởi `cancel()`, context cha bị hủy hoặc lifecycle của operation kết thúc.
! `http.Server.Shutdown` không tự hủy context của active request. Muốn signal dừng process hủy handler phải truyền application context có chủ đích; policy ấy có thể làm gián đoạn graceful drain.
→ Dừng vòng lặp xử lý của goroutine, dọn dẹp tài nguyên và trả về trạng thái canceled (áp dụng quy ước mã phi chuẩn HTTP 499 Client Closed Request phổ biến trong microservices / OutcomeCancel). [Ch4,11,12,20]

### D02 `context deadline exceeded`
Tác vụ không hoàn thành trong khoảng thời gian timeout hoặc trước mốc thời gian deadline đã ấn định (`context.DeadlineExceeded`).
! Client bị timeout không có nghĩa là downstream service đã ngừng xử lý; kết nối có thể vẫn đang chạy ngầm gây nghẽn.
→ Xác định nơi khởi tạo deadline (`WithTimeout`), đo lường độ trễ từng phân đoạn và điều chỉnh timeout hợp lý. [Ch4,11,12,20]

### D03 Client Disconnect During Body Read
Client ngắt kết nối khi handler đang đọc `req.Body`. Lỗi đọc tùy đường kết nối và trạng thái body; không bảo đảm luôn là `context.Canceled`. Incoming request context bị hủy khi kết nối đóng, request bị hủy trên HTTP/2 hoặc `ServeHTTP` kết thúc.
→ Kiểm tra `r.Context().Done()` hoặc `errors.Is(err, context.Canceled)` trong các tác vụ đọc stream để kịp thời giải phóng CPU và buffer. [Ch11,12,20]

### D04 Server Graceful Shutdown Timeout
Phương thức `server.Shutdown(ctx)` chạm mốc timeout của context truyền vào trước khi toàn bộ các kết nối HTTP đang hoạt động được đóng mềm mại, trả về `context.DeadlineExceeded`.
→ Điều tra request còn chạy và ngân sách drain. Context truyền cho `Shutdown` giới hạn thời gian chờ, không tự trở thành context của handler; kiểm tra policy hủy request riêng. [Ch12,20]

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
→ Kiểm tra working directory, mount và base image thực tế; image distroless thường không có shell/ls, nhưng biến thể debug khác. Dùng đường dẫn phù hợp hoặc công cụ chẩn đoán riêng. [Ch15,17]

### E06 `signal: terminated / signal: killed`
Process bị dừng đột ngột bởi tín hiệu hệ điều hành: SIGTERM khi dừng dịch vụ có phối hợp, hoặc SIGKILL khi bị cưỡng chế tiêu diệt (kill -9, hết hạn grace period, hoặc do Linux kernel OOM Killer).
! SIGKILL có thể đến từ nhiều nguyên nhân (admin kill, timeout của bộ điều phối, cgroup limit); không tự động suy diễn mọi SIGKILL đều là OOM.
→ Kiểm tra dmesg/journalctl hoặc Kubernetes termination reason để xác định process bị kill bởi OOM Killer hay do lệnh quản trị bên ngoài. [Ch10,12,17]

### E07 `failed to load bpf program: operation not permitted / permission denied (eBPF Verifier Error)`
* `failed to load bpf program: operation not permitted`
* `failed to load bpf program: permission denied: ... (verifier log)`
Load bị từ chối có thể do quyền, chính sách host hoặc bytecode không đạt kiểm tra verifier. Capability cần thiết tùy kernel và loại program; không suy ra nguyên nhân chỉ từ một chuỗi permission denied.
! Đọc error và verifier log nếu có. Verifier phân tích program trước khi cho chạy; không phải mọi lỗi permission đều có log verifier.
→ Kiểm tra feature, hook, policy và quyền tối thiểu trước khi cấp thêm quyền. Sửa bytecode theo log cụ thể; không có quy tắc rằng mọi pointer đều phải đi qua `bpf_probe_read_*`. [Ch27]

---

## F — Network / HTTP / TLS

### F01 `dial tcp: lookup host: no such host`
Hệ thống DNS resolver không thể phân giải tên miền mục tiêu thành địa chỉ IP hợp lệ (`net.DNSError`).
→ Kiểm tra cấu hình DNS cục bộ (`/etc/resolv.conf`), service discovery của cụm Kubernetes (CoreDNS), hoặc lỗi chính tả host. [Ch11,16,20]

### F02 `dial tcp: connect: connection refused`
Địa chỉ IP máy chủ hoạt động nhưng tại cổng đích không có bất kỳ process nào đang lắng nghe (nhận gói tin TCP RST).
→ Xác nhận service mục tiêu đã khởi chạy, bind đúng địa chỉ (`0.0.0.0` thay vì `127.0.0.1`), và port đích chính xác. [Ch4,11,16,20]

### F03 `i/o timeout / dial tcp: i/o timeout`
Dial không hoàn tất trong ngân sách kết nối, hoặc đọc/ghi vượt deadline tương ứng. `net.Dialer.Timeout` giới hạn dial, không đặt timeout chung cho mọi lần đọc/ghi sau đó.
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
! `InsecureSkipVerify` bỏ kiểm tra certificate chain và hostname mặc định; không dùng để chữa lỗi production. Custom verification cần contract riêng; TLS encryption không vì cờ này mà tự biến mất.
→ Thêm Root CA nội bộ vào trust store của hệ điều hành/container hoặc nạp CA tùy biến qua `tls.Config.RootCAs`. [Ch11,17,20]

### F08 `x509: certificate has expired or is not yet valid`
Chứng chỉ số TLS của máy chủ đã quá hạn sử dụng, hoặc đồng hồ hệ thống trên máy chạy Go bị lệch thời gian (time drift).
→ Kiểm tra thời hạn chứng chỉ bằng `openssl x509`, gia hạn chứng chỉ hoặc đồng bộ lại đồng hồ hệ điều hành qua NTP. [Ch11,17]

### F09 `x509: certificate is valid for X, not Y`
Tên miền truy cập không khớp với danh sách Subject Alternative Names (SAN) được cấp trong chứng chỉ số TLS.
→ Cấp lại chứng chỉ với trường SAN bao quát đúng tên miền hoặc địa chỉ IP đang sử dụng để kết nối. [Ch11,17]

### F10 Unread Response Body (Lost Connection Reuse)
Với HTTP/1.x, đóng body trước EOF có thể làm mất khả năng tái sử dụng kết nối. HTTP/2 có lifecycle stream riêng; không suy ra cứ đóng body sớm là toàn bộ socket phải đóng.
! EOF của `io.LimitReader` có thể chỉ báo hết ngân sách, không phải hết body gốc. `ReuseEligible` là cờ của helper trong lab, không phải cam kết từ Transport.
→ Đóng body; nếu chọn drain, giới hạn byte và thời gian. EOF hỗ trợ một số đường HTTP/1.x reuse, không bảo đảm reuse ở mọi Transport/protocol. [Ch11,20]

### F11 `RequestTimeTooSkewed`
* `RequestTimeTooSkewed: The difference between the request time and the current time is too large.`
Diagnostic này có thể gặp từ Amazon S3 khi thời gian request lệch ngoài cửa sổ được service chấp nhận. Không áp một ngưỡng phút chung cho mọi service hoặc mọi kiểu ký AWS; đọc response và contract API thực tế.
! Thường gặp trong container hoặc máy ảo khi tiến trình đồng bộ thời gian NTP bị lỗi hoặc đóng băng sau khi suspend.
→ Đồng bộ lại đồng hồ hệ điều hành thông qua dịch vụ chrony hoặc NTP daemon (`chronyc makestep`). [Ch24]

---

## G — Database

### G01 `sql: database is closed`
Thực hiện thao tác trên `*sql.DB` đã đóng. Đây không phải `sql.ErrConnDone`: sentinel ấy dành cho `*sql.Conn` đã trả lại pool hoặc đóng.
→ Rà soát lifecycle của `*sql.DB`: chỉ khởi tạo duy nhất một lần lúc ứng dụng startup và chỉ đóng khi toàn bộ process tắt. [Ch13,20]

### G02 `driver: bad connection`
Driver báo connection không dùng được (`driver.ErrBadConn`); `database/sql` có thể retry theo contract. Đây khác với chờ pool đạt `SetMaxOpenConns`.
! Chờ pool có thể kết thúc khi connection được trả lại, context bị hủy/hết hạn hoặc DB đóng. Không có error string chuẩn mang tên "connection pool exhausted".
→ Kiểm tra health check kết nối, tăng `SetMaxOpenConns` nếu tải hợp lệ, hoặc đặt timeout cho context truy vấn để tránh goroutine bị treo vô hạn. [Ch13,20]

### G03 Unclosed sql.Rows (Connection Pool Starvation)
Không đóng `Rows` khi dừng duyệt sớm có thể giữ connection ngoài pool. Đọc tới EOF có thể tự đóng Rows theo contract, nhưng caller vẫn nên đóng tường minh và kiểm tra `rows.Err()`.
! `database/sql` không phát ra chuỗi lỗi báo quên close; triệu chứng thực tế là pool cạn kiệt âm thầm và các truy vấn kế tiếp bị treo đến khi context timeout.
→ Luôn đặt `defer rows.Close()` ngay sau dòng kiểm tra `if err != nil` của lệnh `db.QueryContext`. [Ch13,20]

### G04 `sqlite: database is locked / busy`
SQLite gặp xung đột ghi đồng thời từ nhiều transaction hoặc goroutine trên cùng một tập tin cơ sở dữ liệu (`busy / locked`).
→ Cân nhắc WAL, busy timeout hoặc tuần tự hóa ghi theo workload. Cú pháp DSN/pragma tùy driver; các tên `_journal_mode` và `_busy_timeout` không phải contract chung của `database/sql`. [Ch13,20]

### G05 `UNIQUE constraint failed`
Cố gắng chèn hoặc cập nhật bản ghi có giá trị trùng lặp trên cột được đánh chỉ mục duy nhất (PRIMARY KEY hoặc UNIQUE).
→ Bắt lỗi conflict, áp dụng chính sách `ON CONFLICT DO UPDATE` (upsert) hoặc kiểm tra sự tồn tại trước khi ghi. [Ch13,20]

### G06 `FOREIGN KEY constraint failed`
Thao tác insert hoặc delete vi phạm tính toàn vẹn quan hệ khóa ngoại giữa bảng cha và bảng con.
→ Kiểm tra foreign key, transaction, deferred constraint và cascade của database thật; không áp một thứ tự insert/delete duy nhất cho mọi schema. [Ch13,20]

---

## H — Concurrency

### H01 `fatal error: all goroutines are asleep - deadlock!`
Runtime phát hiện không còn công việc có thể tiến triển theo các điều kiện kiểm tra nội tại của version đang chạy.
! Goroutine chờ I/O hoặc timer không tự đồng nghĩa deadlock. Runtime không phát hiện mọi vòng chờ cục bộ; goroutine khác còn hoạt động có thể che một nhóm đang kẹt.
→ Thiết kế đồ thị phụ thuộc của lock/channel; luôn tuân thủ thứ tự acquisition lock nhất quán và tránh chờ đợi vòng tròn. [Ch8,9,12]

### H02 `WARNING: DATA RACE`
Go race detector (`go test -race` / `go run -race`) phát hiện các truy cập xung đột tới cùng vùng nhớ, có ít nhất một lần ghi và thiếu quan hệ đồng bộ cần thiết trên đường chạy được quan sát.
! Không bỏ qua data race. Kết quả có thể không nhất quán hoặc gây crash; một lần chạy không crash không chứng minh chương trình đúng.
→ Bảo vệ vùng nhớ dùng chung bằng `sync.Mutex`, chuyển sang toán tử `sync/atomic`, hoặc tái cấu trúc truyền dữ liệu qua channel. [Ch8,9,20]

### H03 Goroutine Leak
Goroutine không kết thúc vì không còn đường thoát khỏi chờ channel, lock hoặc I/O. Context chỉ hữu ích nếu operation thực sự quan sát cancellation.
! Go runtime không tự động garbage collect goroutine bị block; một goroutine bị leak sẽ giữ toàn bộ stack frame và bộ nhớ tham chiếu liên quan.
→ Xác định owner và đường thoát; truyền context/deadline tới API có hỗ trợ. Buffer chỉ đổi thời điểm block, không tự sửa leak. [Ch8,9,12,20]

### H04 `panic: sync: negative WaitGroup counter`
Phương thức `wg.Add()` nhận giá trị âm làm counter nhỏ hơn 0, hoặc phương thức `wg.Done()` bị gọi nhiều lần hơn số lần `Add()`.
→ Kiểm tra số lần `Done()` và tăng counter trước khi khởi chạy worker trong mẫu đang học. `Add` dương khi counter bằng 0 phải xảy ra trước `Wait`; không để worker mới tự tăng sau khi caller đã có thể `Wait`. [Ch8,9]

### H05 `panic: sync: WaitGroup misuse: Add called concurrently with Wait`
Diagnostic này không có nghĩa mọi `Add` đồng thời với `Wait` đều sai. Theo contract, `Add` dương khi counter đang bằng 0 phải xảy ra trước `Wait`; khi counter đã dương, quy tắc khác áp dụng.
→ Trong mẫu worker đang học, đăng ký task trước khi khởi chạy; nếu tái sử dụng WaitGroup, chỉ thêm lứa mới sau khi mọi `Wait` của lứa cũ đã trả về. [Ch8,9]

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
GitHub REST API có thể trả HTTP 403 hoặc 429 khi vượt primary hay secondary rate limit. Theo tài liệu ngày 29-09-2026, mức cơ bản là 5.000 request/giờ cho user được xác thực và 60 cho IP không xác thực; loại token, App, endpoint và Enterprise có ngoại lệ. Dùng header thực tế, không gán mức ấy cho mọi token.
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
! Kubelet trên node phối hợp với container runtime để kéo image; trạng thái được báo về API. Lỗi này xảy ra trước khi container Go khởi chạy.
→ Kiểm tra tên image và tag, cấu hình `imagePullSecrets` cho service account, hoặc kiểm tra kết nối mạng egress của cụm. [Ch17,18]

### J04 CreateContainerConfigError
Trạng thái lỗi cấu hình (`Waiting Reason`) khi Kubernetes không tìm thấy ConfigMap hoặc Secret được tham chiếu trong cấu hình Pod.
! Kubelet gặp lỗi khi chuẩn bị cấu hình container; không phải diagnostic của Go hay riêng thao tác chọn node của scheduler.
→ Chạy `kubectl describe pod <pod>` để xác định chính xác tên ConfigMap/Secret đang bị thiếu và tạo bổ sung vào namespace. [Ch17,21]

### J05 Readiness probe failed
* `HTTP probe failed with statuscode: 503`
Sự kiện chẩn đoán (`Kubelet Event`) phát ra khi endpoint kiểm tra mức độ sẵn sàng (`/readyz`) trả về mã lỗi hoặc timeout, khiến pod bị rút khỏi danh sách nhận traffic của Service.
! Đây là sự kiện chẩn đoán (Kubelet Event); container Go vẫn đang chạy bình thường nhưng chưa sẵn sàng phục vụ lưu lượng.
→ Kiểm tra tình trạng kết nối đến các dependency hạ tầng (database, cache) và rà soát logic kiểm tra sẵn sàng của handler. [Ch12,17,20,21]

### J06 Liveness probe failed
Sự kiện chẩn đoán (`Kubelet Event`) phát ra khi endpoint kiểm tra sự sống (`/livez`) không phản hồi hoặc trả về mã lỗi, khiến Kubernetes ra lệnh tiêu diệt và khởi động lại container.
! Tránh dùng lỗi database xa làm liveness failure nếu restart không chữa được nó; policy sai có thể gây cascading restart.
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
Trạng thái chặn theo policy khi công cụ phân tích tìm đường gọi có thể tới ký hiệu liên quan lỗ hổng, hoặc identity của builder không được chấp nhận.
! Reachability tĩnh không chứng minh đường ấy đã chạy, khai thác thành công hay có mã độc. Phân biệt kết quả phân tích với trace thực nghiệm.
→ Cập nhật phiên bản dependency đã vá lỗi, loại bỏ việc gọi ký hiệu chứa lỗ hổng, hoặc kiểm tra lại builder ID trong CI workflow. [Ch26]

### J11 MCP Tool Execution Denied: unauthorized mutation or SSRF boundary violation
* `mcp: tool authorization denied for role <role> on tool <tool>`
* `mcp: ssrf blocked: target ip <ip> belongs to private/metadata range`
Trạng thái từ chối (`MCP Security Boundary Status`) khi Agent AI cố gắng kích hoạt công cụ làm thay đổi trạng thái hạ tầng (Mutating Tool) mà không có quyền hạn, hoặc truyền tham số URL vi phạm ranh giới phòng vệ SSRF (hướng tới AWS Metadata Service `169.254.169.254` hoặc Loopback `127.0.0.1`).
! Schema kiểm tra cấu trúc và constraint đã khai báo, không thay authorization, kiểm soát destination hay phòng prompt injection. Handler, gateway hoặc lớp mạng phải thực thi policy phù hợp; không phải yêu cầu bắt buộc dùng Go.
→ Kiểm tra role của Agent trong phiên MCP, cấu hình whitelist URL cho công cụ mạng, hoặc cấp token ủy quyền (Change Request ID) trước khi gọi các tool gây đột biến. [Ch28]


