# BẢN ĐỒ PHÂN LOẠI CHƯƠNG VÀ ĐỊNH VỊ FOUNDATION DEEP-REWRITE

**Mục Đích:** Định vị ranh giới kỹ thuật và phân lập trọng tâm cho lượt Foundation Deep-Rewrite sắp tới.  
**Nguyên Tắc Phân Loại:**
- Một chương được định danh là **FOUNDATION_CORE** nếu nó trực tiếp kiến tạo hoặc thay đổi mô hình tư duy (mental model) nền tảng của lập trình viên về Go: kiểu dữ liệu, giá trị, bộ nhớ, con trỏ, ranh giới I/O, lỗi, đóng gói, kiểm thử, đồng quy, profiling, interface và generic.
- Một chương được định danh là **FOUNDATION_BRIDGE** nếu nó chuyển hóa các nguyên lý cốt lõi sang mô hình dịch vụ (service lifecycle, HTTP transport, database transactions, CLI diagnostics).
- Các chương thuộc **APPLICATION / SYSTEMS** giải quyết bài toán chuyên biệt thuộc domain hạ tầng, điều phối đám mây, bảo mật chuỗi cung ứng, eBPF hoặc AI agents, và không thuộc phạm vi mở rộng trong lượt rewrite này.

---

## 1. Danh Mục FOUNDATION_CORE (14 Chương)

| Mã Chương | Tên Tệp Chương | Tiêu Đề | Lý Do Xếp Hạng FOUNDATION_CORE (Mental Model Impact) |
| :--- | :--- | :--- | :--- |
| **00A** | `00-truoc-khi-viet-dong-go-dau-tien.md` | Trước khi viết dòng Go đầu tiên | Định hình triết lý ngôn ngữ, sự đánh đổi có chủ đích giữa tính đơn giản và tính năng, và tư duy thiết kế phần mềm bằng Go. |
| **00B** | `00-mo-cua-vao-go.md` | Mở cửa vào Go | Khởi tạo môi trường, giải mã vai trò của toolchain, cấu trúc module `go.mod`, quy ước biên dịch và ranh giới hệ điều hành. |
| **Ch01** | `01-doc-va-viet-mot-chuong-trinh-go.md` | Đọc và viết một chương trình Go | Cú pháp tường minh, luồng điều khiển, phạm vi biến (scope), và triết lý loại bỏ mã ngầm định (no magic). |
| **Ch02** | `02-gia-tri-slice-va-aliasing.md` | Giá trị, Slice và Aliasing | Phân biệt Value vs Pointer, giải mã cấu trúc 24-byte Slice header (`ptr`, `len`, `cap`), hiện tượng aliasing và phân bổ lại bộ nhớ ngầm. |
| **Ch03** | `03-mo-hinh-du-lieu-va-trach-nhiem-thay-doi.md` | Mô hình dữ liệu và trách nhiệm thay đổi | Cấu trúc dữ liệu Struct, căn chỉnh bộ nhớ (memory alignment, padding), Value vs Pointer receivers, và tính đóng gói hành vi. |
| **Ch04** | `04-bien-loi.md` | Biến lỗi | Triết lý error-as-value, phân biệt lỗi dự kiến và ngoại lệ chết người (`panic`), cây lỗi và unwrapping với `errors.Is`/`errors.As`. |
| **Ch05** | `05-thiet-ke-package.md` | Thiết kế package | Ranh giới che giấu thông tin (encapsulation), ngăn chặn circular dependency, thiết kế API công khai tối giản và có tính module hóa cao. |
| **Ch06** | `06-thay-doi-khong-so-hai.md` | Thay đổi không sợ hãi | Kỹ thuật kiểm thử table-driven test, subtests, ranh giới test isolation và decoupling qua interfaces. |
| **Ch07** | `07-du-lieu-di-vao-va-di-ra.md` | Dữ liệu đi vào và đi ra | Ranh giới trừu tượng I/O: hợp đồng `io.Reader`/`io.Writer`, streaming vs buffering, và quản lý rò rỉ tài nguyên với `Close()`. |
| **Ch08** | `08-mot-race-bat-dau-tu-dau.md` | Một race bắt đầu từ đâu | Đồng quy nền tảng: vòng đời Goroutine, bộ điều phối GMP, cơ chế phát hiện Data Race, đồng bộ hóa bằng `sync.Mutex` và atomic. |
| **Ch09** | `09-dong-cong-viec-co-ap-suat.md` | Dòng công việc có áp suất | Hợp đồng giao tiếp Channel (buffered/unbuffered), áp suất ngược (backpressure), rò rỉ goroutine và điều phối hủy bỏ bằng `context.Context`. |
| **Ch10** | `10-khi-chuong-trinh-cham-hoac-phinh.md` | Khi chương trình chậm hoặc phình | Đo lường hiệu năng từ first principles: Benchmark, CPU/Memory Profiling (pprof), và phân tích thoát biến (escape analysis). |
| **Ch14** | `14-khi-kieu-tro-thanh-du-lieu.md` | Khi kiểu trở thành dữ liệu | Khám phá cấu trúc Interface (`eface`, `iface`), bảng phương thức `itab`, chi phí dynamic dispatch và ranh giới reflection runtime. |
| **Ch19** | `19-giu-type-information.md` | Giữ type information | Hệ thống Generics trong Go: Type parameters, type sets, constraints, cơ chế monomorphization vs dictionary passing, và trade-off biên dịch. |

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

## 3. Danh Mục APPLICATION / SYSTEMS (13 Chương — Cố Định, Không Mở Rộng)

Bao gồm các chương từ **Ch16 đến Ch28** áp dụng Go vào các miền chuyên biệt:
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

---

## 4. Hướng Dẫn Điều Phối Cho Lượt Foundation Rewrite

1. **Tập Trung Toàn Lực Vào FOUNDATION_CORE:** Lượt rewrite sau chỉ tập trung đào sâu chất lượng và cơ sở lý luận khoa học cho 14 chương cốt lõi.
2. **Không Tự Động Phình To:** Các chương Application/Systems giữ nguyên factual content và trạng thái đã freeze, trừ khi có phát hiện factual blocker thực sự.
3. **Loại Bỏ Trùng Lặp Thông Qua Tham Chiếu Chéo:** Nếu phát hiện các đoạn lặp lại nguyên lý nền tảng trong các chương ứng dụng, đề xuất chuyển thành tham chiếu chéo ngược về các chương `FOUNDATION_CORE` tương ứng.
