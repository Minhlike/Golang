# BẢN ĐỒ PHÂN LOẠI CHƯƠNG VÀ ĐỊNH VỊ FOUNDATION DEEP-REWRITE

**Mục đích:** Phân loại vai trò chương trong manuscript hiện hành, không kích hoạt lại lượt rewrite lịch sử. Đối chiếu ngày 01-10-2026; nhãn vai trò không phải kết luận QA.
**Nguyên Tắc Phân Loại:**
- Một chương được định danh là **FOUNDATION_CORE** nếu nó trực tiếp kiến tạo hoặc thay đổi mô hình tư duy (mental model) nền tảng của lập trình viên về Go: kiểu dữ liệu, giá trị, bộ nhớ, con trỏ, ranh giới I/O, lỗi, đóng gói, kiểm thử, đồng quy, profiling, interface và generic.
- Một chương được định danh là **FOUNDATION_BRIDGE** nếu nó chuyển hóa các nguyên lý cốt lõi sang mô hình dịch vụ (service lifecycle, HTTP transport, database transactions, CLI diagnostics).
- Các chương thuộc **APPLICATION / SYSTEMS** giải quyết bài toán chuyên biệt thuộc hạ tầng, điều phối đám mây, bảo mật chuỗi cung ứng, eBPF hoặc AI agents. Nhãn này không loại chương khỏi kiểm tra correctness của nhiệm vụ hiện hành.

---

## 1. Danh Mục FOUNDATION_CORE (14 Chương)

| Mã Chương | Tên Tệp Chương | Tiêu Đề | Lý Do Xếp Hạng FOUNDATION_CORE (Mental Model Impact) |
| :--- | :--- | :--- | :--- |
| **00A** | `00-truoc-khi-viet-dong-go-dau-tien.md` | Trước khi viết dòng Go đầu tiên | Định hình triết lý ngôn ngữ, sự đánh đổi có chủ đích giữa tính đơn giản và tính năng, và tư duy thiết kế phần mềm bằng Go. |
| **00B** | `00-mo-cua-vao-go.md` | Mở cửa vào Go | Khởi tạo môi trường, giải mã vai trò của toolchain, cấu trúc module `go.mod`, quy ước biên dịch và ranh giới hệ điều hành. |
| **Ch01** | `01-doc-va-viet-mot-chuong-trinh-go.md` | Đọc và viết một chương trình Go | Cú pháp tường minh, luồng điều khiển, phạm vi biến (scope), và triết lý loại bỏ mã ngầm định (no magic). |
| **Ch02** | `02-gia-tri-slice-va-aliasing.md` | Giá trị, Slice và Aliasing | Phân biệt copy giá trị và chia sẻ backing array, độ dài/dung lượng và aliasing. Slice header 24 byte chỉ là ví dụ triển khai Go 1.27.1 trên amd64, không phải kích thước do spec bảo đảm. |
| **Ch03** | `03-mo-hinh-du-lieu-va-trach-nhiem-thay-doi.md` | Mô hình dữ liệu và trách nhiệm thay đổi | Cấu trúc dữ liệu Struct, căn chỉnh bộ nhớ (memory alignment, padding), Value vs Pointer receivers, và tính đóng gói hành vi. |
| **Ch04** | `04-bien-loi.md` | Biến lỗi | Triết lý error-as-value, phân biệt lỗi dự kiến và ngoại lệ chết người (`panic`), cây lỗi và unwrapping với `errors.Is`/`errors.As`. |
| **Ch05** | `05-thiet-ke-package.md` | Thiết kế package | Ranh giới che giấu thông tin (encapsulation), ngăn chặn circular dependency, thiết kế API công khai tối giản và có tính module hóa cao. |
| **Ch06** | `06-thay-doi-khong-so-hai.md` | Thay đổi không sợ hãi | Kỹ thuật kiểm thử table-driven test, subtests, ranh giới test isolation và decoupling qua interfaces. |
| **Ch07** | `07-du-lieu-di-vao-va-di-ra.md` | Dữ liệu đi vào và đi ra | Ranh giới trừu tượng I/O: hợp đồng `io.Reader`/`io.Writer`, streaming vs buffering, và quản lý rò rỉ tài nguyên với `Close()`. |
| **Ch08** | `08-mot-race-bat-dau-tu-dau.md` | Một race bắt đầu từ đâu | Đồng quy nền tảng: vòng đời Goroutine, bộ điều phối GMP, cơ chế phát hiện Data Race, đồng bộ hóa bằng `sync.Mutex` và atomic. |
| **Ch09** | `09-dong-cong-viec-co-ap-suat.md` | Dòng công việc có áp suất | Hợp đồng giao tiếp Channel (buffered/unbuffered), áp suất ngược (backpressure), rò rỉ goroutine và điều phối hủy bỏ bằng `context.Context`. |
| **Ch10** | `10-khi-chuong-trinh-cham-hoac-phinh.md` | Khi chương trình chậm hoặc phình | Đo lường hiệu năng từ first principles: Benchmark, CPU/Memory Profiling (pprof), và phân tích thoát biến (escape analysis). |
| **Ch14** | `14-khi-kieu-tro-thanh-du-lieu.md` | Khi kiểu trở thành dữ liệu | Ranh giới reflection: kiểm tra shape, quyền mutation và metadata lúc runtime; tách contract khỏi layout nội bộ khi khảo sát `unsafe` và cgo. |
| **Ch19** | `19-giu-type-information.md` | Giữ type information | Type parameter, type set và constraint giữ thông tin kiểu; chọn generic/interface/reflection theo boundary. Cách compiler sinh mã là chi tiết triển khai, không phải lý do mặc định để chọn API. |

---

## 2. Danh Mục FOUNDATION_BRIDGE (4 Chương)

Các chương cầu nối chuyển tiếp tri thức từ nguyên lý nền tảng sang các thuộc tính dịch vụ hệ thống:

| Mã Chương | Tên Tệp Chương | Tiêu Đề | Vai Trò Cầu Nối |
| :--- | :--- | :--- | :--- |
| **Ch11** | `11-mot-request-thuc-su-di-dau.md` | Một request thực sự đi đâu | Cầu nối I/O sang mạng: Vòng đời HTTP request, connection pooling, transport roundtripper. |
| **Ch12** | `12-mot-service-song-va-tat-the-nao.md` | Một service sống và tắt thế nào | Cầu nối hệ điều hành: Tín hiệu POSIX/Windows, graceful shutdown, dọn dẹp tài nguyên đồng bộ. |
| **Ch13** | `13-mot-thay-doi-hoac-khong-co-gi.md` | Một thay đổi hoặc không có gì | Cầu nối lưu trữ: Ranh giới ACID trong cơ sở dữ liệu, quản lý kết nối và transaction rollback. |
| **Ch15** | `15-tu-incident-den-cong-cu.md` | Từ incident đến công cụ | Cầu nối vận hành: Chuyển đổi tư duy phân tích sự cố production thành công cụ dòng lệnh chuyên dụng. |

---

## 3. APPLICATION / SYSTEMS (13 chương, gồm Ch29)

Gồm Ch16–18 và Ch20–29; Ch19 đã thuộc FOUNDATION_CORE:
- **Ch16:** Quan sát hệ thống (Metrics, OpenTelemetry, Tracing)
- **Ch17:** Đóng gói container và điều phối Kubernetes
- **Ch18:** Đưa thay đổi ra production (CI/CD Pipelines)
- **Ch20:** Dự án tổng kết OpsProbe
- **Ch21:** Vòng lặp điều hòa Controller
- **Ch22:** Kubernetes client-go Controller
- **Ch23:** Kubernetes Operator với controller-runtime
- **Ch24:** Tự động hóa AWS SDK v2
- **Ch25:** Git & GitHub Automation hướng sự kiện
- **Ch26:** Bảo mật chuỗi cung ứng phần mềm (Cosign, SLSA, In-toto)
- **Ch27:** Giám sát nhân Linux bằng eBPF và Go
- **Ch28:** Model Context Protocol (MCP) và AIOps an toàn
- **Ch29:** Bằng chứng, quyền hành động và công việc kỹ sư trong kỷ nguyên Agent

---

## 4. Sử dụng phân loại

Phân loại giúp chọn điểm đặt kiến thức và tham chiếu chéo, không cấm sửa lỗi thật ở chương ứng dụng. Một nội dung đã đủ sâu nên để nguyên; kiến thức mượn trước cần được dạy đầy đủ ở chương sở hữu nó. Phạm vi thay đổi do nhiệm vụ hiện hành và gap matrix quyết định, không suy ra từ nhãn FOUNDATION hay APPLICATION.
