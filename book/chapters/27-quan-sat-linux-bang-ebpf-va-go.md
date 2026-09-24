# Chương 27 — Quan sát Linux từ kernel bằng eBPF và Go

Cho đến thời điểm này của cuốn sách, chúng ta đã xây dựng các công cụ giám sát dựa trên ba trụ cột Observability truyền thống: Metrics (Prometheus), Logs và Tracing (OpenTelemetry). 

Tuy nhiên, tất cả các phương pháp đó đều chia sẻ một điểm yếu cốt tử: **Chúng hoàn toàn phụ thuộc vào việc ứng dụng ở tầng người dùng (Userspace) có hợp tác hay không**.

Hãy tưởng tượng một tình huống thực chiến trong vận hành:
- Một container Nginx bị khai thác lỗ hổng Remote Code Execution (RCE). Kẻ tấn công mở một shell ngầm `/bin/sh`, tải mã độc đào tiền ảo về thư mục `/tmp` và thực thi nó.
- Mã độc này không hề gọi OpenTelemetry SDK, không xuất metric Prometheus và đã xóa sạch lịch sử lệnh.
- Các công cụ APM truyền thống hoàn toàn "mù lòa" trước tiến trình lạ này.

Nếu muốn bắt quả tang kẻ tấn công, bạn không thể đứng ở tầng Userspace để quan sát. Bạn phải đứng ở tầng sâu nhất, nơi không một tiến trình nào có thể che giấu hành vi của mình: **Tầng nhân hệ điều hành (Linux Kernel)**.

Trước đây, can thiệp vào kernel đồng nghĩa với việc viết Linux Kernel Module (LKM) bằng ngôn ngữ C — một sai lầm nhỏ về con trỏ có thể làm sập toàn bộ máy chủ vật lý (Kernel Panic).

Công nghệ **eBPF (Extended Berkeley Packet Filter)** kết hợp với thư viện thuần Go **`cilium/ebpf`** đã thay đổi hoàn toàn cục diện đó. Chương này hướng dẫn bạn cách viết chương trình eBPF để móc vào các điểm then chốt của kernel, truyền dữ liệu tốc độ cao qua Ring Buffer và xây dựng một hệ thống quan sát tiến trình thời gian thực bằng Go mà không cần CGO.

---

## 1. Mental Model: Chuỗi luân chuyển sự kiện Kernel - Go Userspace

Mô hình tư duy cốt lõi của việc quan sát bằng eBPF và Go được thể hiện qua sơ đồ 6 bước:

~~~
[Sự kiện Kernel: Lệnh execve()]
              │
              ▼
[eBPF Tracepoint Hook] (Chạy ngầm trong kernel context)
              │
              ▼
[Kernel Verifier] (Kiểm tra an toàn tĩnh toàn diện)
              │
              ▼
[BPF Ring Buffer Map] (Vùng nhớ vòng chia sẻ kernel-user)
              │
              ▼
[cilium/ebpf Reader] (Go Userspace epoll thức dậy)
              │
              ▼
[Binary ABI Decoder] (Giải mã little-endian sang struct)
              │
              ▼
[Heuristic Anomaly Engine] (Cảnh báo vi phạm hành vi)
~~~

Trong mô hình này:
1. Mỗi khi có tiến trình cố gắng thực thi (`sys_enter_execve`), kernel kích hoạt điểm móc (tracepoint).
2. Chương trình eBPF thu thập thông tin định danh (PID, UID, GID, tên tiến trình gọi, đường dẫn file nhị phân).
3. Dữ liệu nhị phân được ghi vào bộ đệm vòng (Ring Buffer) dùng chung.
4. Ứng dụng Go ở userspace thức dậy thông qua cơ chế `epoll`, giải mã dữ liệu nhị phân và phân tích bất thường an ninh (heuristic).

---

## 2. Kernel Verifier: Ranh giới an toàn tối cao của hệ điều hành

Tại sao Linux Kernel lại cho phép mã do người dùng viết chạy trực tiếp bên trong không gian bộ nhớ của nhân?

Câu trả lời nằm ở **Bộ kiểm định nhân (Kernel Verifier)**. Trước khi bất kỳ chương trình eBPF nào được nạp vào kernel thông qua lời gọi hệ thống `SYS_BPF`, Verifier sẽ phân tích tĩnh toàn bộ mã bytecode và thực thi các quy tắc kiểm tra nghiêm ngặt:

1. **Bảo đảm dừng hữu hạn (Termination Guarantee):** Verifier phân tích đồ thị luồng điều khiển (Control Flow Graph). Mọi nhánh rẽ thực thi phải được chứng minh có điểm kết thúc; mọi vòng lặp phải là vòng lặp hữu hạn có biên (bounded loops), loại bỏ hoàn toàn rủi ro treo CPU của kernel.
2. **Kiểm soát truy cập bộ nhớ an toàn (Memory Safety):** Mọi thao tác truy xuất bộ nhớ qua con trỏ đều phải kiểm tra ranh giới (bounds checking). Con trỏ trỏ tới vùng nhớ người dùng (Userspace) không bao giờ được dereference trực tiếp mà bắt buộc phải qua hàm trợ giúp an toàn như `bpf_probe_read_user_str()`.
3. **Hạn mức bộ nhớ Stack nghiêm ngặt (512-Byte Limit):** Chương trình eBPF chỉ được cấp phát tối đa **512 bytes** trên ngăn xếp (stack). Khai báo mảng lớn cục bộ sẽ bị Verifier từ chối ngay lập tức với lỗi tràn stack.
4. **Bảo toàn trạng thái thanh ghi và Frame Pointer:** Thanh ghi `R10` là con trỏ khung ngăn xếp chỉ đọc (read-only frame pointer). Verifier theo dõi chặt chẽ kiểu dữ liệu và phạm vi giá trị của từng thanh ghi (R0–R9) qua từng lệnh thực thi.

---

## 3. Kiến trúc CGO-Free và Trình sinh mã `bpf2go`

Khi lập trình eBPF với Go, nhiều người lầm tưởng rằng bắt buộc phải cài đặt trình biên dịch Clang/LLVM cồng kềnh trên máy chủ sản xuất hoặc phải kích hoạt CGO.

Thư viện **`github.com/cilium/ebpf`** giải quyết triệt để vấn đề này nhờ kiến trúc **CGO-Free**:

~~~
[exec_observer.c] ──(clang dev)──> [exec_observer.o]
                                         │
                                   (bpf2go sinh mã)
                                         │
                                         ▼
[Binary Go: main] <──(go build)── [exec_observer.go]
       │
 (Chạy độc lập trên production, CGO_ENABLED=0)
       │
       ▼
unix.Syscall(unix.SYS_BPF, ...) ──> Nạp vào Kernel
~~~

Chỉ thị sinh mã tiêu chuẩn sử dụng `bpf2go` (trong tệp Go `gen.go`):

~~~bash
go run github.com/cilium/ebpf/cmd/bpf2go \
    -target bpfel -cc clang \
    bpf bpf/exec_observer.c -- \
    -I/usr/include/bpf -O2 -g
~~~

1. **Giai đoạn phát triển:** Bạn viết mã C eBPF, sau đó chạy `go generate` với `bpf2go` và Clang trên máy phát triển để biên dịch mã nguồn C thành bytecode eBPF (định dạng ELF) cùng các tệp Go bindings tương ứng.
2. **Tự động nhúng Bytecode:** `bpf2go` tự động sinh ra tệp Go chứa mã bytecode ELF đã được nhúng thẳng vào binary thông qua tính năng `//go:embed`.
3. **Thực thi không CGO:** Khi binary Go khởi chạy trên máy chủ production, nó tự tay mở file descriptor và kích hoạt syscall cấp thấp của Linux: `unix.Syscall(unix.SYS_BPF, ...)` để nạp chương trình eBPF vào kernel mà **hoàn toàn không cần CGO** (`CGO_ENABLED=0`) và không cần cài thêm bất kỳ gói phần mềm nào trên OS host!
4. **Mô hình kiểm thử linh hoạt:** Trong môi trường CI hoặc máy phát triển không có Clang/kernel headers, mã Go có thể sử dụng các loader mô hình hóa hoặc giả lập nguồn đọc (`RecordReader`) để kiểm chứng toàn bộ pipeline xử lý mà không cần quyền root.

---

## 4. Kênh truyền dữ liệu tốc độ cao: BPF Ring Buffer

Để đưa dữ liệu từ Kernel lên Go Userspace, eBPF cung cấp cấu trúc dữ liệu **BPF Ring Buffer (`BPF_MAP_TYPE_RINGBUF`)**.

So với công nghệ cũ Perf Event Array (vốn cấp phát bộ đệm riêng cho từng CPU core, gây lãng phí RAM và làm đảo lộn thứ tự sự kiện), Ring Buffer sở hữu các ưu điểm vượt trội:
- **Bộ đệm vòng chia sẻ toàn cục:** Tất cả các CPU core cùng ghi vào một vùng nhớ vòng duy nhất, bảo đảm tính tuần tự theo thời gian của sự kiện.
- **Ánh xạ bộ nhớ (mmap):** Ứng dụng Go ánh xạ trực tiếp vùng nhớ của Ring Buffer vào không gian địa chỉ người dùng qua `mmap`, cho phép đọc sự kiện liên tục mà không cần gọi syscall riêng lẻ cho từng gói tin.
- **Cơ chế Reserve & Submit:** Thay vì cấp phát trên stack 512 bytes bị hạn chế, mã eBPF gọi `bpf_ringbuf_reserve` để giữ chỗ trực tiếp trong ring buffer, ghi dữ liệu vào vùng nhớ đó, rồi gọi `bpf_ringbuf_submit`. Nếu buffer đầy, hàm trả về NULL giúp kernel xử lý an toàn mà không bị crash.

---

## 5. Viết mã Kernel: Bắt sự kiện `sys_enter_execve`

Dưới đây là phần khai báo cấu trúc sự kiện và bản đồ Ring Buffer trong C eBPF (`labs/part27-ebpf-observer/bpf/exec_observer.c`):

~~~c
// +build ignore
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

char __license[] SEC("license") = "Dual MIT/GPL";

struct exec_event {
    __u32 pid;
    __u32 uid;
    __u32 gid;
    char  comm[16];
    char  filename[128];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024); // 256KB buffer
} events SEC(".maps");
~~~

Tiếp theo là hàm móc vào tracepoint `sys_enter_execve` để bắt thông tin mỗi khi có lời gọi thực thi nhị phân:

~~~c
SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct trace_event_raw_sys_enter *ctx) {
    struct exec_event *event;

    // Cấp phát trực tiếp trong ringbuffer
    event = bpf_ringbuf_reserve(
        &events, sizeof(struct exec_event), 0
    );
    if (!event) {
        return 0; // Buffer đầy hoặc bộ nhớ bận
    }

    __u64 pid_tgid = bpf_get_current_pid_tgid();
    event->pid = (__u32)(pid_tgid >> 32);

    __u64 uid_gid = bpf_get_current_uid_gid();
    event->uid = (__u32)(uid_gid);
    event->gid = (__u32)(uid_gid >> 32);

    // Đọc tên của tiến trình gọi (calling task)
    bpf_get_current_comm(
        &event->comm, sizeof(event->comm)
    );

    // Đọc đường dẫn file nhị phân đích từ tham số syscall
    const char *fn = (const char *)ctx->args[0];
    bpf_probe_read_user_str(
        &event->filename, sizeof(event->filename), fn
    );

    // Gửi sự kiện lên Userspace
    bpf_ringbuf_submit(event, 0);
    return 0;
}
~~~

### Điểm kỹ thuật mấu chốt trong mã C:
- **Ý định thực thi (`sys_enter_execve`):** Tracepoint này được kích hoạt ngay tại cửa vào của syscall. Nó đại diện cho **ý định thực thi (execution attempt)**, không phải sự tạo tiến trình đã hoàn thành. Nếu tệp không tồn tại (`ENOENT`) hoặc không có quyền execute (`EACCES`), syscall sẽ thất bại, nhưng sự kiện tracepoint vẫn đã được ghi nhận.
- **Bản chất của `bpf_get_current_comm`:** Tại `sys_enter_execve`, hàm này trả về tên của **tiến trình đang gọi** (calling task, ví dụ `bash`, `containerd`, `python`), **không phải** tên binary mới đang được nạp. Tên binary đích nằm ở tham số thứ nhất `ctx->args[0]`.
- **Phân giải PID chính xác (`pid_tgid >> 32`):** Trong Linux kernel, `bpf_get_current_pid_tgid()` trả về 64-bit số nguyên (`tgid << 32 | pid`). Trong không gian người dùng, PID thông thường chính là TGID (32 bit cao).
- **Đọc an toàn qua `bpf_probe_read_user_str`:** Con trỏ `ctx->args[0]` trỏ vào bộ nhớ userspace. Kernel Verifier cấm dereference trực tiếp mà bắt buộc phải qua helper an toàn này để chống lỗi truy cập trang nhớ (page fault).

---

## 6. Xây dựng Trình giải mã nhị phân và Thu thập trong Go

Khi sự kiện từ kernel được đẩy vào Ring Buffer, ứng dụng Go nhận được một mảng byte nhị phân thô (`[]byte`). Nhiệm vụ của chúng ta là giải mã mảng byte này thành struct Go với hiệu năng tối đa.

### Mô hình dữ liệu và giải mã ABI (`event.go`)

~~~go
package ebpfobserver

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"time"
)

// EventPayloadSize đại diện cho kích thước struct C (156B).
const EventPayloadSize = 156

type ExecEvent struct {
	PID       uint32    `json:"pid"`
	UID       uint32    `json:"uid"`
	GID       uint32    `json:"gid"`
	Comm      string    `json:"comm"`
	Filename  string    `json:"filename"`
	Timestamp time.Time `json:"timestamp"`
}
~~~

Hàm giải mã bóc tách từng trường dữ liệu theo chuẩn little-endian:

~~~go
// DecodeExecEvent giải mã mảng byte thô từ Ring Buffer.
func DecodeExecEvent(data []byte) (*ExecEvent, error) {
	if len(data) < EventPayloadSize {
		return nil, fmt.Errorf(
			"truncated event: want %d bytes, got %d",
			EventPayloadSize, len(data),
		)
	}

	pid := binary.LittleEndian.Uint32(data[0:4])
	uid := binary.LittleEndian.Uint32(data[4:8])
	gid := binary.LittleEndian.Uint32(data[8:12])

	commBytes := data[12:28]
	fileBytes := data[28:156]

	return &ExecEvent{
		PID:       pid,
		UID:       uid,
		GID:       gid,
		Comm:      parseCString(commBytes),
		Filename:  parseCString(fileBytes),
		Timestamp: time.Now().UTC(),
	}, nil
}

// parseCString cắt bỏ các byte null kết thúc chuỗi của C.
func parseCString(b []byte) string {
	idx := bytes.IndexByte(b, 0)
	if idx >= 0 {
		return string(b[:idx])
	}
	return string(b)
}
~~~

---

## 7. Điều phối luồng sự kiện và Phát hiện Bất thường An ninh (`observer.go`)

Để kiểm thử được trên mọi nền tảng mà không phụ thuộc vào quyền root Linux khi chạy unit test, chúng ta trừu tượng hóa nguồn đọc bằng interface `RecordReader`:

~~~go
// RecordReader trừu tượng hóa nguồn đọc từ BPF Ring Buffer.
type RecordReader interface {
	Read() ([]byte, error)
	Close() error
}

type Observer struct {
	reader    RecordReader
	events    chan *ExecEvent
	errs      chan error
	done      chan struct{}
	closeOnce sync.Once
}

func NewObserver(
	reader RecordReader, bufferSize int,
) *Observer {
	if bufferSize <= 0 {
		bufferSize = 128
	}
	return &Observer{
		reader: reader,
		events: make(chan *ExecEvent, bufferSize),
		errs:   make(chan error, 16),
		done:   make(chan struct{}),
	}
}
~~~

Phương thức `Start` khởi động goroutine nền xử lý sự kiện:

~~~go
func (o *Observer) Start(
	ctx context.Context,
) (<-chan *ExecEvent, <-chan error) {
	go func() {
		defer close(o.events)
		defer close(o.errs)
		o.readLoop(ctx)
	}()
	return o.events, o.errs
}
~~~

Vòng lặp đọc dữ liệu từ Ring Buffer và đẩy vào channel với khả năng hủy qua context:

~~~go
func (o *Observer) readLoop(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-o.done:
			return
		default:
			data, err := o.reader.Read()
			if err != nil {
				if errors.Is(err, io.EOF) ||
					errors.Is(err, ErrObserverClosed) {
					return
				}
				o.sendErr(ctx, err)
				continue
			}

			event, decodeErr := DecodeExecEvent(data)
			if decodeErr != nil {
				o.sendErr(ctx, decodeErr)
				continue
			}
			o.sendEvent(ctx, event)
		}
	}
}
~~~

### Động cơ phát hiện bất thường an ninh (Heuristic Security Rules)
Khi nhận được sự kiện, chúng ta đối chiếu với các quy tắc an ninh phỏng đoán. Cần lưu ý: Đây là các **quy tắc phỏng đoán (Heuristics)** hỗ trợ giám sát, không phải lá chắn bảo mật tuyệt đối, bởi kẻ tấn công nâng cao có thể lẩn tránh bằng cách gọi `execveat`, nạp nhị phân từ RAM qua `memfd_create`, hoặc dùng symlink:

~~~go
type SecurityAlert struct {
	Event  *ExecEvent
	Rule   string
	Reason string
}

func checkBasicRules(e *ExecEvent) *SecurityAlert {
	fn := strings.ToLower(e.Filename)
	comm := strings.ToLower(e.Comm)

	// Luật 1: Thực thi từ thư mục tạm (/tmp, /dev/shm)
	if strings.HasPrefix(fn, "/tmp/") ||
		strings.HasPrefix(fn, "/dev/shm/") {
		return &SecurityAlert{
			Event:  e,
			Rule:   "SEC01_EXEC_FROM_TEMP_DIRECTORY",
			Reason: "process executed from writable temp path",
		}
	}

	// Luật 2: Daemon web tự ý mở shell tương tác (RCE)
	isShell := fn == "/bin/sh" || fn == "/bin/bash"
	isWeb := comm == "nginx" || comm == "node" ||
		comm == "python"
	if isShell && isWeb {
		return &SecurityAlert{
			Event:  e,
			Rule:   "SEC02_SHELL_FROM_WEBSERVER",
			Reason: "interactive shell spawned from web daemon",
		}
	}
	return nil
}
~~~

Tiếp theo là quy tắc phát hiện các tiện ích mạng chạy bằng quyền root:

~~~go
func DetectSecurityAnomalies(e *ExecEvent) *SecurityAlert {
	if e == nil {
		return nil
	}
	if alert := checkBasicRules(e); alert != nil {
		return alert
	}

	// Luật 3: Tiện ích dò quét mạng chạy với quyền root (UID 0)
	fn := strings.ToLower(e.Filename)
	isNet := strings.HasSuffix(fn, "/nc") ||
		strings.HasSuffix(fn, "/ncat")
	if isNet && e.UID == 0 {
		return &SecurityAlert{
			Event:  e,
			Rule:   "SEC03_ROOT_NETWORK_RECON",
			Reason: "network recon tool executed as root",
		}
	}
	return nil
}
~~~

---

## 8. Kiểm chứng Lab thực tế (`labs/part27-ebpf-observer`)

Bộ kiểm thử tại `labs/part27-ebpf-observer/observer_test.go` vận hành độc lập (phân loại kiểm chứng: `UNIT_TESTED` / `MODEL_ONLY` đối với mô hình streaming channel, ABI decoding 156 bytes, heuristic anomaly detection và kiểm tra cấu trúc BPF Spec mà không đòi hỏi quyền root của Linux). Chạy bộ kiểm thử hoàn chỉnh với cờ kiểm tra tương tranh dữ liệu:

~~~bash
go test -v -race ./...
~~~

Kết quả xác thực 6 kịch bản thực chiến:

~~~
=== RUN   TestEncodeDecodeExecEvent
--- PASS: TestEncodeDecodeExecEvent (0.00s)
=== RUN   TestDecodeExecEventTruncated
--- PASS: TestDecodeExecEventTruncated (0.00s)
=== RUN   TestObserverStreaming
--- PASS: TestObserverStreaming (0.00s)
=== RUN   TestObserverContextCancellation
--- PASS: TestObserverContextCancellation (0.00s)
=== RUN   TestDetectSecurityAnomalies
--- PASS: TestDetectSecurityAnomalies (0.00s)
=== RUN   TestCiliumEbpfSpecLoading
--- PASS: TestCiliumEbpfSpecLoading (0.00s)
PASS
ok      part27-ebpf-observer   2.211s
~~~

### Phân tích kết quả kiểm thử:
1. **Serialization & Deserialization:** Đóng gói và giải mã chính xác 156 byte C ABI, bảo đảm các trường PID, UID, GID, Comm và Filename toàn vẹn.
2. **Xử lý gói tin lỗi (Truncated):** Xử lý an toàn khi payload bị cắt ngắn mà không gây hoảng loạn (panic).
3. **Luồng sự kiện liên tục (Streaming Pipeline):** Vận chuyển sự kiện bất đồng bộ qua Go channel, không xảy ra rò rỉ goroutine hay data race.
4. **Hủy bỏ tác vụ (Context Cancellation):** Dừng sạch sẽ vòng lặp đọc khi context bị hủy.
5. **Quy tắc An ninh Heuristic:** Nhận diện chính xác 3 kịch bản tấn công điển hình (mã độc trong `/tmp`, RCE từ Nginx, Netcat root) và bỏ qua tiến trình hợp lệ (`/usr/bin/go`).
6. **Khởi tạo eBPF Spec:** Khởi tạo thành công `CollectionSpec` của `cilium/ebpf` với Map loại `RingBuf` và Program loại `TracePoint`.

---

## 9. Các cạm bẫy người học thường gặp (Learner Pitfalls)

| Cạm bẫy thực tế | Hậu quả trên Production | Giải pháp phòng ngừa |
| :--- | :--- | :--- |
| **Khai báo mảng lớn trên eBPF stack** (ví dụ mảng 1024 bytes). | Kernel Verifier lập tức từ chối nạp chương trình với lỗi `stack overflow`. | Bộ nhớ stack của eBPF bị giới hạn cứng 512B; luôn dùng `bpf_ringbuf_reserve` để cấp phát. |
| **Lấy nhầm 32 bit thấp** của `bpf_get_current_pid_tgid()`. | Thu được Thread ID (TID) thay vì Process ID (PID), khiến log hiển thị PID sai lệch hoàn toàn. | Luôn dịch bit phải 32 bit: `(__u32)(pid_tgid >> 32)` để lấy đúng PID của tiến trình. |
| **Xử lý sự kiện userspace quá chậm** trong vòng lặp đọc. | Tràn bộ đệm Ring Buffer trong kernel, khiến các sự kiện quan trọng bị âm thầm đánh rơi (dropped). | Sử dụng buffered channel và mô hình Worker Pool ở tầng Go để tiêu thụ sự kiện với tốc độ cao. |
| **Chạy ứng dụng thiếu quyền** Linux Capabilities. | Syscall `SYS_BPF` trả về `EPERM: operation not permitted`. | Cấp quyền tối thiểu cho binary bằng lệnh: `sudo setcap cap_bpf,cap_sys_admin+ep <binary>`. |

---

## 10. Bài tập thực hành thiết kế Observer eBPF

### Thử thách 1: Bộ đếm tần suất thực thi tiến trình (Exec Rate Limiter)
**Yêu cầu:** Một tiến trình bị lỗi hoặc tấn công có thể liên tục gọi thực thi nhị phân làm cạn kiệt tài nguyên hệ điều hành. Hãy viết một hàm Go nhận vào luồng sự kiện `<-chan *ExecEvent`, theo dõi số lượng lệnh thực thi sinh ra bởi mỗi tiến trình gọi (`Comm`) trong cửa sổ trượt 1 giây, và phát cảnh báo nếu một tiến trình gọi sinh ra quá 50 lần thực thi mỗi giây.

### Thử thách 2: Bóc tách tham số dòng lệnh từ Syscall (Argv Extraction)
**Yêu cầu:** Trong C eBPF, tham số thứ hai của `execve` (`ctx->args[1]`) là một mảng con trỏ trỏ tới danh sách đối số dòng lệnh (`argv`). Hãy thiết kế cấu trúc dữ liệu Go mở rộng `ExecEventExtended` có trường `Args []string` và viết hàm tách mảng các chuỗi con cách nhau bởi ký tự khoảng trắng hoặc byte null an toàn.

---

## 11. Hướng dẫn giải và Phân tích kiến trúc bài tập

### Lời giải Thử thách 1: Bộ phát hiện tần suất thực thi

~~~go
type ForkBombDetector struct {
	mu       sync.Mutex
	counts   map[string]int
	lastTick time.Time
}

func NewForkBombDetector() *ForkBombDetector {
	return &ForkBombDetector{
		counts:   make(map[string]int),
		lastTick: time.Now(),
	}
}

func (d *ForkBombDetector) Check(
	e *ExecEvent, threshold int,
) bool {
	d.mu.Lock()
	defer d.mu.Unlock()

	now := time.Now()
	if now.Sub(d.lastTick) >= time.Second {
		// Reset bộ đếm mỗi giây
		d.counts = make(map[string]int)
		d.lastTick = now
	}

	d.counts[e.Comm]++
	return d.counts[e.Comm] > threshold
}
~~~

### Lời giải Thử thách 2: Bóc tách đối số dòng lệnh

~~~go
type ExecEventExtended struct {
	ExecEvent
	Args []string `json:"args"`
}

func ParseRawArgs(raw []byte) []string {
	var args []string
	tokens := bytes.Split(raw, []byte{0})
	for _, tok := range tokens {
		s := strings.TrimSpace(string(tok))
		if len(s) > 0 {
			args = append(args, s)
		}
	}
	return args
}
~~~

Kỹ thuật bóc tách danh sách đối số cho phép người vận hành không chỉ biết file nào được thực thi, mà còn nắm rõ các cờ tham số nguy hiểm (ví dụ `curl http://... | bash`).

---

Với sức mạnh của **eBPF kết hợp cùng Go**, bạn đã sở hữu khả năng quan sát và bảo vệ hệ thống từ tầng sâu nhất của hệ điều hành Linux — nơi mà không một tiến trình độc hại nào có thể lẩn tránh.

Nhưng trong bức tranh vận hành hiện đại của năm 2026, các kỹ sư SRE không chỉ làm việc với các hệ thống tự động hóa truyền thống, mà đang ngày càng hợp tác với các **Tác tử Trí tuệ Nhân tạo (AI Agents)**. Khi chúng ta trao quyền cho AI Agent truy cập vào hệ thống hạ tầng để tự động xử lý sự cố (AIOps), câu hỏi sống còn đặt ra là: **Làm thế nào để trao công cụ cho Agent mà không trao toàn quyền?** Trong **Chương 28** — chương cuối cùng của lộ trình nâng cao — chúng ta sẽ tìm hiểu cách xây dựng máy chủ công cụ an toàn bằng Go theo giao thức **Model Context Protocol (MCP)**, thiết lập ranh giới phân quyền nghiêm ngặt, phòng chống tấn công Prompt Injection và lưu vết kiểm toán (Audit Trail) cho mọi thao tác của Agent.
