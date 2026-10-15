# BÁO CÁO THIẾT KẾ CHƯƠNG 2 — AGENT 2: NÂNG CẤP 4 SƠ ĐỒ & STRICT CONTENT LOCK

> **Trạng thái:** `AWAITING_MANUAL_APPROVAL`  
> **Repository:** `https://github.com/Minhlike/Golang.git`  
> **Branch thiết kế:** `design/ch02-agent2-redesign`  
> **BASE_HEAD (main):** `bb00a9ad33e3cd5115928dc3542d2ce66c8d08d8`  
> **Bản PDF Master (`Golang_Master.pdf`):** Giữ nguyên trạng 100%, không sửa đổi, không merge.  
> **Phạm vi khóa cứng (Strict Content Lock):** `book/chapters/02-gia-tri-slice-va-aliasing.md` giống 100% bản gốc trên `main` (`git diff` rỗng).

---

## 1. TỔNG QUAN YÊU CẦU & ĐIỀU CHỈNH PHẠM VI (STRICT CONTENT LOCK)

Theo yêu cầu nghiêm ngặt từ người dùng tại vòng rà soát mới nhất:
1. **Khóa cứng nội dung bài giảng (Strict Content Lock):**
   - Giữ nguyên 100% bài giảng, văn xuôi, tiêu đề, ví dụ, code block, terminal output, bảng biểu, caption, typography và bố cục chuẩn của PDF master cũ.
   - Tuyệt đối không viết lại, thêm, bớt, diễn giải hoặc can thiệp vào bất kỳ nội dung bài giảng nào (`git diff main book/chapters/02-gia-tri-slice-va-aliasing.md` = 0).
2. **Thu gọn phạm vi: Chỉ nâng cấp 4 sơ đồ (Diagram-Only Scope):**
   - Không áp dụng hệ thống thẻ đặc tả (Spec Card), bảng quy trình riêng hay Chapter Opener portal của prototype trước.
   - Loại bỏ hoàn toàn hình minh họa 3D Axonometric Section.
   - Tái sử dụng chính xác 4 đường dẫn asset hiện có trong `assets/diagrams/`:
     1. `assets/diagrams/array-copy.png`
     2. `assets/diagrams/slice-sharing.png`
     3. `assets/diagrams/slice-window.png`
     4. `assets/diagrams/append-storage.png`
3. **Đồng bộ chuẩn Renderer sách gốc:**
   - Cấu hình lại `scripts/build_ch02_preview.py` sử dụng đúng parser và engine dàn trang chuẩn của `scripts/build_pdf.py` (`MirroredDocTemplate`, font, style, code box, table grid).
4. **Hiến pháp bất biến về Code Block:**
   - **Tuyệt đối không đánh số dòng (NO LINE NUMBERS)** trong bất kỳ đoạn code nào.

---

## 2. CHI TIẾT KỸ THUẬT NÂNG CẤP TRÊN 4 SƠ ĐỒ

### 2.1 Sơ đồ 1 — `assets/diagrams/array-copy.png` (Hình 1)
- **Quy chuẩn kỹ thuật:**
  - Thể hiện chính xác ngữ nghĩa giá trị độc lập (Value Semantics) của phép gán mảng: biến `a: [3]int` và biến `b: [3]int`.
  - Phân tách rõ ràng trạng thái trước và sau mutation: phép gán `b := a` sao chép toàn bộ giá trị các phần tử; sau đó thao tác `b[0] = 99` chỉ làm thay đổi ô nhớ độc lập của `b[0]`, `a[0]` vẫn giữ nguyên giá trị `10`.
  - Loại bỏ hoàn toàn khẳng định Go specification bắt buộc sao chép vật lý 24 byte.
  - Footnote nêu rõ: *Kích thước 24B (3 x 8B) là chi tiết kiến trúc amd64; ngôn ngữ không ràng buộc vị trí vật lý cố định.*
- **Chất lượng thị giác:**
  - Bố cục đối xứng hai hộp biến `a` và `b`, mũi tên chuyển tiếp `b := a` ở trung tâm.
  - Chú thích chân hình 2 dòng cân đối, không tràn lề, độ phân giải 300 DPI sắc nét.

### 2.2 Sơ đồ 2 — `assets/diagrams/slice-sharing.png` (Hình 2)
- **Quy chuẩn kỹ thuật:**
  - Minh họa hai slice value độc lập (`Descriptor a` và `Descriptor b`) cùng tham chiếu tới một mảng nền chung (`Backing Array`).
  - Phân định rõ giữa đặc tả Go specification (ngữ nghĩa slice là cửa sổ nhìn vào mảng nền) và mô hình triển khai runtime `gc` 64-bit (cấu trúc 3 word: con trỏ `Data`, `Len`, `Cap`).
  - Loại bỏ khẳng định bắt buộc sao chép bitwise 24 byte.
  - Thao tác `b[0] = 99` ghi thẳng vào mảng nền, khiến `a[0]` cũng quan sát thấy giá trị `99`.
- **Chất lượng thị giác:**
  - Cột trái: 2 descriptor xếp dọc theo kiến trúc từ máy (Vertical Struct Word Layout).
  - Cột phải: Mảng nền dùng chung (Backing Array).
  - Đường vector trực giao (orthogonal routing) uốn góc vuông dứt khoát, chấm tròn tại gốc `Data`, mũi tên trỏ chuẩn xác vào ô `index [0]`.
  - Không chồng chéo chữ, dãn cách tiêu đề và badge `Backing Array` rộng rãi.

### 2.3 Sơ đồ 3 — `assets/diagrams/slice-window.png` (Hình 3)
- **Quy chuẩn kỹ thuật:**
  - **Sửa lỗi định danh quan trọng:** Sửa nhãn biến `base` thành `base : []int` (thay cho lỗi `[5]int` trước đây), đúng với đoạn mã nguồn thực tế `base := []int{10, 20, 30, 40, 50}`.
  - Thể hiện chính xác lát cắt `x := base[1:3]`:
    - Con trỏ `x.Data` bắt đầu tại `base[1]`.
    - Thước đo độ dài `len(x) = 2`: bao phủ cửa sổ quan sát trực tiếp `[20, 30]`.
    - Thước đo sức chứa `cap(x) = 4`: kéo dài từ điểm bắt đầu (`base[1]`) tới hết giới hạn mảng nền gốc (`[20, 30, 40, 50]`).
  - Footnote trích dẫn quy chuẩn Go spec về công thức `high - low` và biên capacity.
- **Chất lượng thị giác:**
  - Tiêu đề mảng nền đặt cao tại `y = 126`, mũi tên con trỏ `x bắt đầu tại base[1]` hạ thấp xuống đỉnh ô nhớ, triệt tiêu hoàn toàn sự chồng lấn chữ.
  - Các ô nhớ hiển thị rõ ràng chỉ số `base[i]` và giá trị bên trong.

### 2.4 Sơ đồ 4 — `assets/diagrams/append-storage.png` (Hình 4)
- **Quy chuẩn kỹ thuật:**
  - Thiết kế cấu trúc cây quyết định (Decision Tree Flowchart) kiểm tra điều kiện sức chứa: `append(s, ...): Kiểm tra len + số_mới <= cap?`.
  - **Nhánh 1: Đủ sức chứa (`len + 1 <= cap`)**:
    - Ngôn ngữ tái sử dụng mảng nền hiện tại, ghi đè phần tử mới vào vị trí index `len`, trả về descriptor có len tăng thêm.
    - Hệ quả: `old` và `s` tiếp tục chia sẻ mảng nền (aliasing).
  - **Nhánh 2: Vượt sức chứa (`len + 1 > cap`)**:
    - Ngôn ngữ cấp phát mảng nền mới đủ lớn và sao chép phần tử cũ sang; runtime `gc` tính toán phân bổ khối nhớ qua `growslice`.
    - Hệ quả: Phân tách mảng nền (`grown` trỏ mảng mới, không làm thay đổi `old`).
  - **Lưu ý kỹ thuật phân biệt Shallow vs Deep copy:** Footnote nêu rõ: *Nhánh 2 tách biệt mảng nền độc lập cho phần tử kiểu giá trị. Với phần tử là con trỏ hoặc struct lồng ghép, đây là shallow copy của mảng nền, không phải deep copy dữ liệu đích.*
- **Chất lượng thị giác:**
  - Đường dẫn cây nhánh (Tree tee routing): Một đường rơi thẳng từ đáy hộp quyết định, rẽ nhánh ngang sang hai phía và hạ vuông góc xuống hai hộp nhánh.
  - Nhãn `[Có] Đủ sức chứa` và `[Không] Vượt sức chứa` đặt độc lập ở khoảng trống phía trên đường ngang, cách xa đường phân nhánh trung tâm hơn 16 pt, không cắt ngang bất kỳ đường nét nào.

---

## 3. DANH SÁCH FILE VÀ ARTIFACT TRÌNH DUYỆT

1. **4 Sơ đồ kỹ thuật vector (300 DPI PNG):**
   - `assets/diagrams/array-copy.png` (1868x575 px)
   - `assets/diagrams/slice-sharing.png` (1868x759 px)
   - `assets/diagrams/slice-window.png` (1868x667 px)
   - `assets/diagrams/append-storage.png` (1868x817 px)
2. **Kịch bản sinh sơ đồ & Engine Preview:**
   - `scripts/ch02_vector_diagrams.py`: Vẽ vector ReportLab chính xác và xuất PNG 300 DPI.
   - `scripts/build_ch02_preview.py`: Engine dựng độc lập theo đúng kiến trúc `build_pdf.py`.
3. **Tài liệu kiểm định trực quan (Preview PDF & 12 Trang Specimens):**
   - PDF Preview độc lập: `book/design/agent2-ch02/ch02_preview.pdf` (12 trang)
   - 12 ảnh chụp trang specimen (150 DPI):
     - [Trang 1: Mở đầu Chương 2 chuẩn mực](specimens/ch02_page_01.png)
     - [Trang 2: Hình 1 — Array Copy Semantics](specimens/ch02_page_02.png)
     - [Trang 3: Hình 2 — Slice Sharing & Aliasing](specimens/ch02_page_03.png)
     - [Trang 4: Bảng 1 — Copy value vs chia sẻ storage](specimens/ch02_page_04.png)
     - [Trang 5: Hình 3 — Slice Window Geometry](specimens/ch02_page_05.png)
     - [Trang 6: Cơ chế Full Slice Expression](specimens/ch02_page_06.png)
     - [Trang 7: Hình 4 — Append Capacity Branching](specimens/ch02_page_07.png)
     - [Trang 8: Aliasing Bug thực tế & Bài tập](specimens/ch02_page_08.png)
     - [Trang 9: Memory Retention & KeepAlive](specimens/ch02_page_09.png)
     - [Trang 10: String: Bytes trước, Text sau](specimens/ch02_page_10.png)
     - [Trang 11: Pointer là câu hỏi khác](specimens/ch02_page_11.png)
     - [Trang 12: Ranh giới API & Tài liệu tham khảo](specimens/ch02_page_12.png)

---

## 4. KẾT QUẢ KIỂM TOÁN CHẤT LƯỢNG (QA AUDIT)

| Tiêu chuẩn QA | Kết quả | Chi tiết kiểm chứng |
| :--- | :---: | :--- |
| **Strict Content Lock** | **PASS** | `git diff main book/chapters/02-gia-tri-slice-va-aliasing.md` rỗng (0 dòng thay đổi). |
| **Code Block: 0 Line Numbers** | **PASS** | Toàn bộ 12 trang không có số dòng code nào. |
| **Code Width Preflight** | **PASS** | `validate_code_width.py`: 0 dòng tràn lề (Usable width: 448.22 pt). |
| **Publication Contracts** | **PASS** | `test_publication_contracts.py`: 16/16 tests passed (100%). |
| **Visual QA — Không đè nét** | **PASS** | Đã kiểm tra trực quan toàn bộ 4 sơ đồ tại zoom 100% và qua 12 file specimens. |
| **Kỹ thuật — Quy chuẩn Go Spec** | **PASS** | Sửa `base: []int`, phân định rõ Go spec vs gc 64-bit runtime, phân biệt shallow vs deep copy. |

---

## 5. HARD APPROVAL GATE

```text
================================================================================
                    HARD APPROVAL GATE: AWAITING_MANUAL_APPROVAL
================================================================================
  [X] TUYỆT ĐỐI KHÔNG MERGE VÀO MAIN.
  [X] TUYỆT ĐỐI KHÔNG SỬA ĐỔI HOẶC GHI ĐÈ GOLANG_MASTER.PDF.
  [X] Mọi thay đổi chỉ nằm trên branch: design/ch02-agent2-redesign.
  [X] Nội dung bài giảng Chương 2 giữ nguyên vẹn 100% so với main.
  [X] Sẵn sàng cho người dùng và ChatGPT Reviewer tiến hành đối chiếu độc lập.
================================================================================
```
