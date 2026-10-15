# Báo Cáo Thiết Kế Lại Sơ Đồ Chương 3 (Agent 2 — Technical Corrections)

**Trạng thái phê duyệt:** `AWAITING_MANUAL_APPROVAL`  
**Nhánh Git:** `design/ch03-agent2-redesign`  
**Nguyên tắc cốt lõi:** Chỉ thiết kế lại 6 sơ đồ kỹ thuật của Chương 3; giữ nguyên 100% văn xuôi, code block, bảng biểu, renderer và file `Golang_Master.pdf`.

---

## 1. Mục tiêu & Chuẩn mực Thiết kế

Tuân thủ nghiêm ngặt tinh thần **Master Prompt** và các chỉ đạo kỹ thuật tại đợt hiệu chỉnh:
1. **Phong cách mỹ thuật kỹ thuật chuyên nghiệp (Monochrome / Grayscale):**
   - Palette màu mực đen và xám đậm (`#000000`, `#1A1A1A`, `#262626`) đạt độ tương phản tối đa, bảo đảm đọc sắc nét khi in đen trắng hoặc hiển thị màn hình zoom 100%.
   - Khung khối viền mảnh kỹ thuật (`0.5pt - 1.0pt`), nền dải header xám nhạt (`#F6F7F9`, `#EEEEEE`), phân định rõ ràng các tầng scope và vai trò.
2. **Kích thước chuẩn xác theo bề rộng trang in:**
   - Chiều rộng `448.22 pt` (khớp chính xác 100% printable text width của sách).
   - Xuất bản raster ở độ phân giải siêu nét **300 DPI** (1868 px chiều ngang), chống răng cưa và vỡ nét.
3. **Hiệu chỉnh kỹ thuật chuẩn xác theo Go Specification:**
   - **Hình 3.1:** Giữ nguyên mô hình Pass-by-Value; không thêm giả định về stack/heap hay thao tác copy vật lý.
   - **Hình 3.2:** Phân biệt rõ bản sao pointer value (tham số `balance`) với biến đích (`amount`) được dereference.
   - **Hình 3.3:** Làm rõ phép gán struct sao chép giá trị các field theo ngữ nghĩa Go, không bắt buộc copy vật lý từng lệnh; phân biệt rạch ròi sao chép struct với deep copy.
   - **Hình 3.4:** Thay toàn bộ khẳng định `copy descriptor` bằng `copy map value`; thể hiện chia sẻ map data ở tầng ngữ nghĩa, không giả định cấu trúc header hay bucket cố định.
   - **Hình 3.5:** Loại bỏ khẳng định tuyệt đối value receiver "chỉ đọc an toàn" hay "không thể thay đổi trạng thái gốc"; làm rõ `Summary` chỉ đọc field trong ví dụ hiện tại, value receiver không bảo đảm không có side effect. Đồng bộ receiver name `service Service` và `service *Service`.
   - **Hình 3.6:** Đồng bộ chính xác 100% tên tham số và receiver với mã nguồn Chương 3: `renderSummary(source SummarySource)`, `(service Service) Summary() string`, `(target StaticTarget) Summary() string`.
4. **Visual QA & Độ khả dụng:**
   - Tăng cỡ chữ nhãn phụ lên $\ge 7.0 - 7.2\,\text{pt}$, bảo đảm không có dòng chữ nào chạm biên hoặc chồng lấn đường nối/mũi tên tại kích thước in thực tế 448.22 pt.

---

## 2. Chi tiết 6 Sơ đồ Kỹ thuật Tái thiết kế

### Hình 3.1: Truyền Tham Số // Lời Gọi Hàm addBonus(balance) (Pass-by-Value)
- **Tập tin:** `assets/diagrams/pointer-value-call.png`
- **Kích thước:** `448.22 x 168.0 pt` (1868 x 700 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Tách bạch 2 vùng scope: Bên gọi (`main`) và Bên nhận (`func addBonus(x int)`).
  - Lời gọi `addBonus(balance)` copy giá trị nguyên thủy `100` từ `balance` vào tham số `x`.
  - Phép gán `x += 20` diễn ra hoàn toàn cục bộ trong frame hàm; biến `balance` bên caller được bảo toàn 100.
  - Footnote: Xác định rõ ngữ nghĩa biến và giá trị theo Go specification; không khẳng định thao tác copy vật lý hay phân bổ stack/heap.

### Hình 3.2: Quan Hệ Pointer & Pointee // Giải Tham Chiếu (Dereference)
- **Tập tin:** `assets/diagrams/pointer-pointee.png`
- **Kích thước:** `448.22 x 175.0 pt` (1868 x 730 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Bên gọi có biến addressable `amount : int = 100`. Phép toán `&amount` tạo pointer value logic.
  - Lời gọi `addBonus(&amount)` sao chép pointer value vào tham số `balance : *int`.
  - Phép dereference `*balance += 20` giải tham chiếu và chọn chính biến `amount` làm đích gán, biến đổi giá trị thành `120`.
  - Footnote: Phân biệt rõ bản sao pointer value (tham số `balance`) với biến đích (`amount`); phép dereference truy cập trực tiếp biến đích, không giả định địa chỉ số hay phân bổ stack/heap.

### Hình 3.3: Ngữ Nghĩa Gán Struct // Sao Chép Giá Trị Các Field (Value Semantics)
- **Tập tin:** `assets/diagrams/struct-copy.png`
- **Kích thước:** `448.22 x 180.0 pt` (1868 x 750 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Mô phỏng cấu trúc bảng trường dữ liệu rõ ràng cho `billing : Service` và `candidate : Service`.
  - Phép gán `candidate := billing` sao chép giá trị các field theo ngữ nghĩa Go (không bắt buộc copy vật lý từng lệnh).
  - Phép gán `candidate.Healthy = false` chỉ biến đổi trường trên bản sao `candidate`; trường `Healthy` của `billing` vẫn giữ `true`.
  - **Micro-Fix Bố cục & Nhãn:**
    - Thẻ chú thích `candidate.Healthy = false` (rộng 110 pt, cao 36 pt) đặt căn giữa tại khoảng trống 128.22 pt, chừa khoảng cách an toàn ~9.1 pt với cả 2 khối struct.
    - Nhãn tóm tắt đáy khung struct tinh chỉnh thành `[BẢO TOÀN] billing.Healthy = true` và `[MUTATED] candidate.Healthy = false` (`BookSansBold 7.0 pt`), chừa biên >26 pt bên trong khung, tuyệt đối không chạm viền hay tràn lề.
  - Footnote: Sao chép struct không đồng nghĩa deep copy; nếu có field chứa pointer/slice/map, chúng vẫn chia sẻ dữ liệu tham chiếu.

### Hình 3.4: Ngữ Nghĩa Gán Map // Sao Chép Map Value, Chia Sẻ Map Data
- **Tập tin:** `assets/diagrams/map-sharing.png`
- **Kích thước:** `448.22 x 175.0 pt` (1868 x 730 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Hai biến map riêng biệt: `registry` và `alias`.
  - Phép gán `alias := registry` sao chép map value; cả hai map value cùng tham chiếu tới vùng `SHARED MAP DATA`.
  - Phép tăng `alias["billing"]++` sửa trực tiếp ô lưu trữ của khóa `"billing"` từ 1 lên 2.
  - Đọc qua `registry["billing"]` lập tức quan sát thấy giá trị 2.
  - Footnote: Sơ đồ biểu diễn chia sẻ ở tầng ngữ nghĩa ngôn ngữ, không giả định cấu trúc header hay bucket hash table của runtime.

### Hình 3.5: Điều Phối Method Receiver // Value Receiver vs Pointer Receiver
- **Tập tin:** `assets/diagrams/method-receiver-trace.png`
- **Kích thước:** `448.22 x 188.0 pt` (1868 x 784 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Biến gốc `billing : Service` là biến addressable (lấy được địa chỉ `&billing`).
  - Nhánh 1 (Value Receiver `Summary`): `func (service Service) Summary() string` nhận bản sao struct value; trong ví dụ này chỉ đọc `service.Name`, không mutate trực tiếp `billing` gốc.
  - Nhánh 2 (Pointer Receiver `Record`): Đồng bộ chữ ký chuẩn xác 100% với bài giảng: `func (service *Service) Record(healthy bool)`. Go tự động chuyển cú pháp thành `(&billing).Record(false)` và truyền pointer value; sửa trực tiếp pointee `Healthy=false, Retries=1`.
  - **Micro-Fix Bố cục & Nhãn:**
    - Tái cân đối bề rộng hai bên: khối `billing` trái rộng 122 pt, khối receiver phải mở rộng lên 206 pt; chữ ký `func (service *Service) Record(healthy bool)` in bằng `BookMono 6.5 pt` chừa lề an toàn tới 18.6 pt trước viền phải.
    - Khoảng hở trung tâm 92.22 pt chứa mũi tên `Record(false)` chạy thẳng ngang tại `arrow_y = 57.0`; nhãn `billing.Record(false)` đặt phía trên mũi tên 8 pt (chừa biên 5.16 pt so với cả hai khối hộp), nhãn phụ `(Truyền &billing)` đặt phía dưới mũi tên 9 pt; triệt để loại bỏ mọi hiện tượng chồng chữ hoặc cắt nét.
  - Footnote: `Summary` chỉ đọc field trong ví dụ này; value receiver không bảo đảm không có side effect (nếu struct chứa reference hoặc thực hiện I/O). Go tự lấy `(&billing)` khi gọi pointer receiver trên biến addressable.

### Hình 3.6: Kiểu Cấu Trúc // Hợp Đồng Interface Nhỏ và Thỏa Mãn Ngầm Định
- **Tập tin:** `assets/diagrams/interface-contract.png`
- **Kích thước:** `448.22 x 196.0 pt` (1868 x 817 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Phân tầng 3 lớp:
    - Consumer: `func renderSummary(source SummarySource) string` phụ thuộc duy nhất vào hợp đồng tối giản.
    - Contract: `type SummarySource interface { Summary() string }`.
    - Concrete Types: `func (service Service) Summary() string` và `func (target StaticTarget) Summary() string` hoàn toàn độc lập, không có ancestor chung.
  - Các mũi tên thỏa mãn ngầm định (implicit satisfaction) kết nối thẳng từ concrete types lên interface contract tại compile-time, không cần từ khóa `implements`.
  - Footnote: Kiểu cấu trúc của Go thỏa mãn ngầm định qua method set tại compile-time; hai concrete type hoàn toàn độc lập.

---

## 3. Bản Duyệt (Specimen Preview)

- **Tập tin PDF Preview:** [`book/design/agent2-ch03/ch03_preview.pdf`](file:///d:/Golang/book/design/agent2-ch03/ch03_preview.pdf)
- **Tập tin Specimen hình ảnh (3 trang):**
  1. [`book/design/agent2-ch03/specimens/ch03_diagrams_p01.png`](file:///d:/Golang/book/design/agent2-ch03/specimens/ch03_diagrams_p01.png) (Hình 3.1 & 3.2)
  2. [`book/design/agent2-ch03/specimens/ch03_diagrams_p02.png`](file:///d:/Golang/book/design/agent2-ch03/specimens/ch03_diagrams_p02.png) (Hình 3.3 & 3.4)
  3. [`book/design/agent2-ch03/specimens/ch03_diagrams_p03.png`](file:///d:/Golang/book/design/agent2-ch03/specimens/ch03_diagrams_p03.png) (Hình 3.5 & 3.6)

---

## 4. Kết Quả Kiểm Thử Tự Động & Repository Hygiene

- `python scripts/test_publication_contracts.py`: **16/16 PASS**
- `python scripts/validate_code_width.py`: **0 overflow** (Mọi dòng code block nằm trong giới hạn printable width 448.22 pt)
- Bất biến văn bản: `git diff main -- book/chapters/03-mo-hinh-du-lieu-va-trach-nhiem-thay-doi.md` **0 dòng thay đổi** (nguyên vẹn 100%).
- Bất biến PDF Master: `Golang_Master.pdf` **không bị ghi đè, không staged**.
