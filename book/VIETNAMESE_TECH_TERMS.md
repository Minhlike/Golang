# TỪ ĐIỂN THUẬT NGỮ KỸ THUẬT QUY CHUẨN (VIETNAMESE TECHNICAL GLOSSARY)

Tài liệu này xác lập bảng thuật ngữ chuẩn mực thống nhất xuyên suốt toàn bộ cuốn sách Go Living Textbook.

Nguyên tắc cốt lõi: **TARGET PROSE ≈ 99% TIẾNG VIỆT** — Văn xuôi, lời dẫn, chú thích sơ đồ, tiêu đề bảng biểu phải được viết bằng tiếng Việt trong sáng, chính xác, tự nhiên và giàu tính sư phạm; loại bỏ triệt để thói quen chêm từ tiếng Anh tùy tiện ("AI slop", "loanword clutter").

---

## 1. NGUYÊN TẮC ÁP DỤNG VÀ QUY TẮC LẦN ĐẦU XUẤT HIỆN

1. **Quy tắc lần đầu xuất hiện (First Encounter Rule):**
   Khi một khái niệm hoặc thuật ngữ kỹ thuật trừu tượng xuất hiện lần đầu tiên trong một chương, sử dụng mẫu định dạng:
   $$\text{Thuật ngữ tiếng Việt } (\text{English term})$$
   *Ví dụ:* `áp suất ngược (backpressure)`, `rò rỉ goroutine (goroutine leak)`, `điều hòa trạng thái (reconciliation)`.
   Từ các lần xuất hiện tiếp theo trong chương đó, **bắt buộc ưu tiên sử dụng hoàn toàn thuật ngữ tiếng Việt**.

2. **Nguyên tắc không dịch máy móc (Idiomatic Translation):**
   Dịch dựa trên bản chất cơ chế hoạt động kỹ thuật, không dịch từng chữ (word-by-word) ngô nghê.
   *Ví dụ:* `deadlock` dịch là `bế tắc đồng thời`, không dịch là "khóa chết"; `work-stealing` dịch là `cơ chế trộm việc`, không dịch là "đánh cắp công việc".

3. **Chính sách bảo tồn định danh (Strict Whitelist):**
   Giữ nguyên dạng tiếng Anh gốc đối với:
   - Các từ khóa (keywords) của ngôn ngữ Go: `package`, `import`, `func`, `var`, `const`, `type`, `struct`, `interface`, `chan`, `go`, `select`, `defer`, `for`, `range`, `if`, `else`, `switch`, `case`, `default`, `return`, `make`, `new`, `len`, `cap`, `append`, `copy`, `panic`, `recover`.
   - Các định danh mã nguồn (identifiers), tên hàm, tên kiểu, tên trường, tên package: `context.Context`, `sync.Mutex`, `io.Reader`, `http.Client`, `Reconcile()`, `WorkQueue`.
   - Tên giao thức, tiêu chuẩn quốc tế: `HTTP/1.1`, `HTTP/2`, `TCP/IP`, `TLS`, `DNS`, `gRPC`, `POSIX`, `REST`.
   - Tên công nghệ, công cụ, hệ điều hành: `Linux`, `Kubernetes`, `Docker`, `Prometheus`, `OpenTelemetry`, `Git`.
   - Các lệnh CLI và cờ (flags): `go test -race`, `go tool pprof`, `kubectl apply`.
   - Chuỗi thông điệp lỗi nguyên văn (exact error diagnostics) và giá trị sentinel: `io.EOF`, `sql.ErrNoRows`.

---

## 2. BẢNG THUẬT NGỮ KỸ THUẬT ĐỐI CHIẾU

### A. Cú pháp và Ngôn ngữ lập trình (Syntax & Language Fundamentals)

| Thuật ngữ tiếng Anh (English) | Thuật ngữ tiếng Việt quy chuẩn (Standard Vietnamese) | Ghi chú & Ngữ cảnh sử dụng |
| :--- | :--- | :--- |
| **variable** | **biến** / **biến số** | Ô nhớ được đặt tên lưu trữ giá trị |
| **constant** | **hằng** / **hằng số** | Giá trị bất biến được xác định tại thời điểm compile |
| **literal** | **giá trị nguyên văn** | Giá trị biểu diễn trực tiếp trong mã (`123`, `"text"`, `true`) |
| **identifier** | **định danh** / **tên định danh** | Tên gọi do lập trình viên đặt cho biến, hàm, kiểu |
| **keyword** | **từ khóa** | Từ dành riêng của ngôn ngữ Go (`func`, `var`...) |
| **declaration** | **khai báo** | Giới thiệu một định danh mới vào chương trình |
| **definition** | **định nghĩa** | Mô tả chi tiết cấu trúc hoặc thân thực thi |
| **assignment** | **phép gán** | Gán giá trị mới cho một biến đã tồn tại (`=`) |
| **short variable declaration** | **khai báo biến ngắn** | Cú pháp khai báo kết hợp gán và suy luận kiểu (`:=`) |
| **expression** | **biểu thức** | Cấu trúc tính toán sinh ra một giá trị cụ thể |
| **statement** | **câu lệnh** | Đơn vị hành động làm thay đổi trạng thái chương trình |
| **block** | **khối lệnh** | Đoạn mã nằm trong cặp dấu ngoặc nhọn `{}` |
| **scope** | **phạm vi** / **phạm vi sống** | Vùng không gian trong mã mà một định danh có hiệu lực |
| **shadowing** | **che khuất biến** | Biến ở scope con che khuất biến trùng tên ở scope cha |
| **type inference** | **suy luận kiểu** | Compiler tự xác định kiểu dữ liệu dựa trên giá trị khởi tạo |
| **type conversion** | **chuyển đổi kiểu** | Cú pháp tường minh `T(v)` đổi giá trị sang kiểu `T` |
| **type assertion** | **khẳng định kiểu** | Biểu thức `x.(T)` trích xuất kiểu cụ thể từ interface |
| **type switch** | **rẽ nhánh theo kiểu** | Cấu trúc `switch x.(type)` phân luồng theo kiểu động |
| **zero value** | **giá trị mặc định** / **giá trị zero** | Giá trị khởi tạo tự động khi biến được khai báo không gán |
| **parameter** | **tham số** / **tham số hình thức** | Biến được định nghĩa trong chữ ký hàm |
| **argument** | **đối số** / **đối số thực tế** | Giá trị cụ thể được truyền vào hàm khi gọi |
| **signature** | **chữ ký hàm** | Tập hợp tên tham số, kiểu tham số và kiểu trả về |
| **multiple return values** | **nhiều giá trị trả về** | Khả năng hàm Go trả về cùng lúc nhiều giá trị |
| **variadic function** | **hàm đa tham số** | Hàm chấp nhận số lượng đối số thay đổi (`...T`) |
| **recursion** | **đệ quy** | Kỹ thuật hàm tự gọi lại chính nó |
| **base case** | **điều kiện dừng** | Trường hợp chặn đệ quy tránh tràn stack |

---

### B. Kiểu dữ liệu và Mô hình bộ nhớ (Data Types & Memory Model)

| Thuật ngữ tiếng Anh (English) | Thuật ngữ tiếng Việt quy chuẩn (Standard Vietnamese) | Ghi chú & Ngữ cảnh sử dụng |
| :--- | :--- | :--- |
| **array** | **mảng cố định** / **mảng** | Dãy phần tử liên tiếp có độ dài cố định là một phần của kiểu |
| **slice** | **lát cắt** / **slice** | Cấu trúc tham chiếu linh hoạt gồm pointer, len, cap |
| **backing array** | **mảng nền** / **mảng đỡ phía sau** | Mảng bộ nhớ thực tế nơi slice lưu trữ dữ liệu |
| **capacity** | **dung lượng** | Số phần tử tối đa mảng nền có thể chứa từ phần tử đầu slice |
| **length** | **độ dài** | Số phần tử hiện có trong lát cắt hoặc mảng |
| **map** | **bảng ánh xạ** / **map** | Cấu trúc dữ liệu liên kết khóa - giá trị (hash table) |
| **struct** | **cấu trúc** / **kiểu cấu trúc** | Tập hợp các trường dữ liệu có tên gom nhóm lại |
| **field** | **trường** / **trường dữ liệu** | Thành phần dữ liệu bên trong một struct |
| **pointer** | **con trỏ** | Biến lưu trữ địa chỉ ô nhớ của một giá trị khác |
| **address-of operator** | **toán tử lấy địa chỉ (`&`)** | Lấy ra địa chỉ bộ nhớ của một biến |
| **dereference operator** | **toán tử giải tham chiếu (`*`)** | Truy cập hoặc gán giá trị tại ô nhớ con trỏ đang trỏ tới |
| **value semantics** | **ngữ nghĩa giá trị** | Sao chép toàn bộ dữ liệu khi truyền tham số hoặc gán |
| **pointer semantics** | **ngữ nghĩa con trỏ** | Chia sẻ địa chỉ bộ nhớ, các bên cùng thao tác trên 1 ô nhớ |
| **method** | **phương thức** | Hàm được gắn liền với một kiểu dữ liệu thông qua receiver |
| **receiver** | **bộ tiếp nhận** / **đối tượng nhận** | Biến đại diện cho instance mà method được triệu gọi |
| **interface** | **giao diện** / **interface** | Tập hợp các chữ ký phương thức mô tả hành vi |
| **implicit satisfaction** | **thỏa mãn ngầm định** | Type tự động thỏa mãn interface mà không cần từ khóa `implements` |
| **composition** | **cấu thành** / **hợp thành** | Xây dựng type phức tạp từ các type đơn giản |
| **embedding** | **nhúng kiểu** | Đặt struct hoặc interface vô danh vào struct khác |
| **memory aliasing** | **chồng lấn địa chỉ ô nhớ** | Hiện tượng hai biến/con trỏ cùng trỏ vào một vùng nhớ |
| **escape analysis** | **phân tích thoát** | Cơ chế compiler xác định biến nằm trên Stack hay Heap |
| **stack allocation** | **cấp phát trên stack** | Cấp phát vùng nhớ nhanh, tự thu hồi khi hàm kết thúc |
| **heap allocation** | **cấp phát trên heap** | Cấp phát trên vùng nhớ chung, do Garbage Collector thu hồi |

---

### C. Lập trình Đồng thời & Runtime (Concurrency & Runtime Engine)

| Thuật ngữ tiếng Anh (English) | Thuật ngữ tiếng Việt quy chuẩn (Standard Vietnamese) | Ghi chú & Ngữ cảnh sử dụng |
| :--- | :--- | :--- |
| **concurrency** | **tính đồng thời** / **lập trình đồng thời** | Cấu trúc chương trình thành các luồng công việc độc lập |
| **parallelism** | **tính song song** | Thực thi vật lý đồng thời trên nhiều lõi CPU |
| **goroutine** | **goroutine** / **tiến trình nhẹ Go** | Luồng thực thi nhẹ do Go runtime quản lý (không phải OS thread) |
| **channel** | **kênh truyền** / **channel** | Ống dẫn dữ liệu đồng bộ hoặc có đệm giữa các goroutine |
| **unbuffered channel** | **kênh không đệm** | Kênh yêu cầu bên gửi và bên nhận phải gặp nhau cùng lúc |
| **buffered channel** | **kênh có đệm** | Kênh có hàng đợi lưu trữ tạm thời các phần tử |
| **deadlock** | **bế tắc đồng thời** / **deadlock** | Trạng thái các goroutine cùng chờ nhau vô tận mà không giải phóng |
| **data race** | **xung đột dữ liệu** / **race condition** | Hai goroutine cùng truy cập một ô nhớ mà có ít nhất một bên ghi |
| **race detector** | **bộ phát hiện xung đột (`-race`)** | Công cụ runtime phân tích và cảnh báo xung đột dữ liệu |
| **starvation** | **đói tài nguyên** | Tiến trình bị các luồng khác chiếm dụng tài nguyên quá lâu |
| **goroutine leak** | **rò rỉ goroutine** | Goroutine bị treo vô hạn, không bao giờ kết thúc giải phóng |
| **backpressure** | **áp suất ngược** | Cơ chế điều tiết tốc độ sản sinh việc để không làm sập hạ tầng |
| **cancellation** | **hủy thực thi** | Tín hiệu dừng công việc qua `context.Context` |
| **graceful shutdown** | **tắt dịch vụ an toàn** | Đóng tiếp nhận mới, hoàn tất việc đang xử lý trước khi thoát |
| **worker pool** | **nhóm tiến trình xử lý** | Tập hợp cố định các goroutine cùng lấy việc từ một hàng đợi |
| **pipeline** | **đường ống xử lý dữ liệu** | Chuỗi các công đoạn nối tiếp nhau qua channel |
| **bounded concurrency** | **giới hạn đồng thời** | Khống chế số lượng công việc chạy đồng thời tối đa |
| **mutex (mutual exclusion)** | **khóa loại trừ tương hỗ** | Công cụ đồng bộ bảo vệ vùng tài nguyên tranh chấp (`sync.Mutex`) |
| **atomic operation** | **thao tác nguyên tử** | Lệnh can thiệp phần cứng thực hiện trọn vẹn không bị ngắt quãng |

---

### D. Hệ thống, DevOps, Mạng & SRE (Systems & Production Engineering)

| Thuật ngữ tiếng Anh (English) | Thuật ngữ tiếng Việt quy chuẩn (Standard Vietnamese) | Ghi chú & Ngữ cảnh sử dụng |
| :--- | :--- | :--- |
| **reconciliation** | **điều hòa trạng thái** | Vòng lặp liên tục đưa thực tế về trạng thái mong muốn |
| **desired state** | **trạng thái mong muốn** | Cấu hình do người dùng khai báo (Spec) |
| **actual state** | **trạng thái thực tế** | Hiện trạng đo đạc được từ hạ tầng thực tế (Status) |
| **rate-limiting** | **giới hạn tốc độ** | Khống chế số lượng yêu cầu trong một đơn vị thời gian |
| **workqueue** | **hàng đợi công việc** | Hàng đợi chứa các khóa đối tượng cần reconcile |
| **exponential backoff** | **lùi bước số mũ** | Thuật toán tăng thời gian chờ sau mỗi lần thử lại thất bại |
| **retry** | **thử lại** | Thực hiện lại tác vụ khi gặp sự cố tạm thời (transient error) |
| **idempotency** | **tính lũy thỏa** / **tính bảo toàn kết quả** | Thực hiện lặp lại nhiều lần cho cùng một kết quả như một lần |
| **health check** | **kiểm tra sức khỏe** | Cơ chế kiểm tra liveness và readiness của dịch vụ |
| **circuit breaker** | **cầu dao ngắt mạch** | Cơ chế tự động ngắt kết nối đến dịch vụ hỏng để bảo vệ hệ thống |
| **observability** | **năng lực quan sát** | Khả năng suy luận trạng thái nội tại qua dữ liệu phát ra |
| **metrics** | **chỉ số đo lường** | Dữ liệu số học thống kê (Counter, Gauge, Histogram) |
| **logs** | **nhật ký vận hành** | Chuỗi sự kiện có mốc thời gian ghi nhận diễn biến hệ thống |
| **traces** | **dấu vết thực thi** | Luồng đi của một yêu cầu xuyên qua các dịch vụ phân tán |
| **call path** | **đường đi lời gọi** | Chuỗi các hàm hoặc dịch vụ được gọi tuần tự |
| **dependency** | **phụ thuộc** / **gói phụ thuộc** | Module hoặc dịch vụ mà thành phần khác dựa vào để chạy |
| **lifecycle** | **vòng đời** | Toàn bộ các giai đoạn từ khởi tạo, hoạt động đến hủy bỏ |
| **throughput** | **thông lượng** | Lượng công việc hoàn thành trong một đơn vị thời gian |
| **latency** | **độ trễ** | Thời gian cần thiết để phản hồi một yêu cầu |
| **overhead** | **chi phí phụ trội** | Tài nguyên CPU/RAM tiêu hao thêm để duy trì cơ chế |
