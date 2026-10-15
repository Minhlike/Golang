# Báo Cáo Thiết Kế Lại Sơ Đồ Chương 3 (Agent 2 — Design Only)

**Trạng thái phê duyệt:** `AWAITING_MANUAL_APPROVAL`  
**Nhánh Git:** `design/ch03-agent2-redesign`  
**Nguyên tắc cốt lõi:** Chỉ thiết kế lại 6 sơ đồ kỹ thuật của Chương 3; giữ nguyên 100% văn xuôi, code block, bảng biểu, renderer và file `Golang_Master.pdf`.

---

## 1. Mục tiêu & Chuẩn mực Thiết kế

Tuân thủ nghiêm ngặt tinh thần **Master Prompt** và tiêu chuẩn thiết kế đồ họa xuất bản của Chương 2:
1. **Phong cách mỹ thuật kỹ thuật chuyên nghiệp (Monochrome / Grayscale):**
   - Palette màu mực đen và xám đậm (`#000000`, `#1A1A1A`, `#262626`) đạt độ tương phản tối đa, bảo đảm đọc sắc nét khi in đen trắng hoặc hiển thị màn hình zoom 100%.
   - Khung khối viền mảnh kỹ thuật (`0.5pt - 1.0pt`), nền dải header xám nhạt (`#F6F7F9`, `#EEEEEE`), phân định rõ ràng các tầng scope và vai trò.
2. **Kích thước chuẩn xác theo bề rộng trang in:**
   - Chiều rộng `448.22 pt` (khớp chính xác 100% printable text width của sách).
   - Xuất bản raster ở độ phân giải siêu nét **300 DPI** (1868 px chiều ngang), chống răng cưa và vỡ nét.
3. **Phân biệt ngữ nghĩa Go Specification vs Runtime Implementation:**
   - Lời gọi hàm là phép truyền sao chép giá trị (pass-by-value).
   - Không áp đặt địa chỉ bộ nhớ số nguyên hoặc định kiến phân bổ stack/heap cố định.
   - Sơ đồ map thể hiện mô hình khái niệm (conceptual map data), không mô tả cấu trúc runtime hash table buckets.
   - Thỏa mãn interface hoàn toàn ngầm định theo method set tại compile-time, không có phân cấp thừa kế hay từ khóa `implements`.

---

## 2. Chi tiết 6 Sơ đồ Kỹ thuật được Tái thiết kế

### Hình 3.1: Truyền Tham Số // Lời Gọi Hàm addBonus(balance) (Pass-by-Value)
- **Tập tin:** `assets/diagrams/pointer-value-call.png`
- **Kích thước:** `448.22 x 168.0 pt` (1868 x 700 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Tách bạch 2 vùng scope: Bên gọi (`main`) và Bên nhận (`func addBonus(x int)`).
  - Lời gọi `addBonus(balance)` copy giá trị nguyên thủy `100` từ `balance` vào tham số `x`.
  - Phép gán `x += 20` diễn ra hoàn toàn cục bộ trong frame hàm; biến `balance` bên caller được bảo toàn 100.
  - Footnote: Xác định rõ ngữ nghĩa biến và giá trị, không khẳng định phân bổ stack/heap vật lý trong RAM.

### Hình 3.2: Quan Hệ Pointer & Pointee // Giải Tham Chiếu (Dereference)
- **Tập tin:** `assets/diagrams/pointer-pointee.png`
- **Kích thước:** `448.22 x 175.0 pt` (1868 x 730 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Bên gọi có biến addressable `amount : int = 100`. Phép toán `&amount` tạo pointer value logic.
  - Lời gọi `addBonus(&amount)` sao chép pointer value vào tham số `balance : *int`.
  - Phép dereference `*balance += 20` giải tham chiếu và chọn chính biến `amount` làm đích gán, biến đổi giá trị thành `120`.
  - Footnote: Pointer value được truyền theo giá trị; phép dereference truy cập biến đích trực tiếp, không giả định địa chỉ số hay stack/heap.

### Hình 3.3: Ngữ Nghĩa Gán Struct // Sao Chép Theo Từng Trường (Field-by-Field Copy)
- **Tập tin:** `assets/diagrams/struct-copy.png`
- **Kích thước:** `448.22 x 180.0 pt` (1868 x 750 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Mô phỏng cấu trúc bảng trường dữ liệu rõ ràng cho `billing : Service` và `candidate : Service`.
  - Phép gán `candidate := billing` sao chép nông toàn bộ 4 trường (`Name`, `Port`, `Healthy`, `Retries`).
  - Phép gán `candidate.Healthy = false` chỉ biến đổi trường trên bản sao `candidate`; trường `Healthy` của `billing` vẫn giữ `true`.
  - Footnote: Gán struct sao chép độc lập từng trường. Nếu struct chứa pointer/slice/map thì field đó mang reference trỏ tới dữ liệu dùng chung (không deep copy).

### Hình 3.4: Ngữ Nghĩa Gán Map // Sao Chép Descriptor, Chia Sẻ Map Storage
- **Tập tin:** `assets/diagrams/map-sharing.png`
- **Kích thước:** `448.22 x 175.0 pt` (1868 x 730 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Hai biến map riêng biệt: `registry` và `alias`.
  - Phép gán `alias := registry` sao chép descriptor/header; cả hai descriptor cùng trỏ tới một vùng `SHARED MAP DATA`.
  - Phép tăng `alias["billing"]++` sửa trực tiếp ô lưu trữ của khóa `"billing"` từ 1 lên 2.
  - Đọc qua `registry["billing"]` lập tức quan sát thấy giá trị 2.
  - Footnote: Sơ đồ khái niệm, không mô tả chi tiết hash table bucket của runtime.

### Hình 3.5: Điều Phối Method Receiver // Value Receiver vs Pointer Receiver
- **Tập tin:** `assets/diagrams/method-receiver-trace.png`
- **Kích thước:** `448.22 x 188.0 pt` (1868 x 784 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Biến gốc `billing : Service` là biến addressable (lấy được địa chỉ `&billing`).
  - Nhánh 1 (Value Receiver `Summary`): Nhận bản sao struct value; chỉ đọc an toàn, không thể thay đổi `billing` gốc.
  - Nhánh 2 (Pointer Receiver `Record`): Go tự động chuyển cú pháp thành `(&billing).Record(false)` và truyền pointer value; sửa trực tiếp pointee `Healthy=false, Retries=1`.
  - Footnote: Sơ đồ trace ngữ nghĩa; Go tự lấy `&billing` trên biến addressable; không khẳng định vị trí stack/heap vật lý.

### Hình 3.6: Kiểu Cấu Trúc // Hợp Đồng Interface Nhỏ và Thỏa Mãn Ngầm Định
- **Tập tin:** `assets/diagrams/interface-contract.png`
- **Kích thước:** `448.22 x 196.0 pt` (1868 x 817 px @ 300 DPI)
- **Nội dung kỹ thuật:**
  - Phân tầng 3 lớp:
    - Consumer: `func renderSummary(s SummarySource) string` phụ thuộc duy nhất vào hợp đồng tối giản.
    - Contract: `type SummarySource interface { Summary() string }`.
    - Concrete Types: `type Service struct` và `type StaticTarget string` hoàn toàn độc lập, không có ancestor chung.
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

## 4. Kết Quả Kiểm Thử Tự Động

- `python scripts/test_publication_contracts.py`: **16/16 PASS**
- `python scripts/validate_code_width.py`: **0 overflow** (Mọi dòng code block nằm trong giới hạn printable width 448.22 pt)
- Bất biến văn bản: `book/chapters/03-mo-hinh-du-lieu-va-trach-nhiem-thay-doi.md` **0 dòng thay đổi** (nguyên vẹn 100%).
- Bất biến PDF Master: `Golang_Master.pdf` **không bị ghi đè, không staged**.
