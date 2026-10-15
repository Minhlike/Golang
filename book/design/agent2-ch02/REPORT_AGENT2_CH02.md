# BÁO CÁO THIẾT KẾ CHƯƠNG 2 — AGENT 2: HOÀN THIỆN 4 SƠ ĐỒ KỸ THUẬT & STRICT CONTENT LOCK

> **Trạng thái:** `AWAITING_MANUAL_APPROVAL`  
> **Repository:** `https://github.com/Minhlike/Golang.git`  
> **Branch thiết kế:** `design/ch02-agent2-redesign`  
> **Baseline Commit:** `054ce6a82a7eac8ab1638d38e2cf1ce49e3233ed`  
> **Bản PDF Master (`Golang_Master.pdf`):** Giữ nguyên trạng 100%, không sửa đổi, không merge.  
> **Phạm vi khóa cứng (Strict Content Lock):** `book/chapters/02-gia-tri-slice-va-aliasing.md` giống 100% bản gốc trên `main` (`git diff` rỗng).  
> **Quy chuẩn Preview:** Chỉ gồm 4 sơ đồ ở kích thước xuất bản thực tế, không chứa văn xuôi, bảng, code block, header hay footer.

---

## 1. TỔNG QUAN PHẠM VI & QUY CHUẨN THIẾT KẾ DUY NHẤT

Tuân thủ nghiêm ngặt chỉ thị từ người dùng tại vòng rà soát cuối cùng:
1. **Phạm vi duy nhất (Sole Scope):**
   - Chỉ hoàn thiện đúng 4 sơ đồ canonical của Chương 2 trong `assets/diagrams/`:
     1. `assets/diagrams/array-copy.png`
     2. `assets/diagrams/slice-sharing.png`
     3. `assets/diagrams/slice-window.png`
     4. `assets/diagrams/append-storage.png`
   - Tuyệt đối không can thiệp, không viết lại, không thêm bớt bất kỳ nội dung bài giảng nào (`git diff main book/chapters/02-gia-tri-slice-va-aliasing.md` = 0).
2. **Quy chuẩn Preview tối giản (Diagram-Only Preview):**
   - Không dựng lại 12 trang bài giảng Chương 2.
   - Tạo bản preview duy nhất (`book/design/agent2-ch02/ch02_preview.pdf` — 2 trang) trình bày trọn vẹn 4 sơ đồ ở kích thước thực tế tương đương trong sách (`448.22 pt`), có nhãn nhận diện và caption cho từng hình; không có bất kỳ văn bản bài giảng hay code nào.
3. **Vệ sinh Repository & Kiểm soát Merge (Hygiene & Merge Control):**
   - Dọn dẹp toàn bộ 12 ảnh specimen nhiều trang cũ (`ch02_page_01.png` .. `ch02_page_12.png`).
   - Thay thế bằng 2 trang specimen tập trung (`ch02_diagrams_p01.png`, `ch02_diagrams_p02.png`).
   - Sau khi người dùng phê duyệt, chỉ merge duy nhất các asset sơ đồ vào `main`.
4. **Hiến pháp code block:** Tuyệt đối không đánh số dòng (NO LINE NUMBERS).

---

## 2. CHI TIẾT NÂNG CẤP KỸ THUẬT & THỊ GIÁC TRÊN 4 SƠ ĐỒ

### 2.1 Hình 2.1 — Phép gán mảng: Sao chép toàn bộ giá trị (`array-copy.png`)
- **Đặc tả kỹ thuật:**
  - Minh họa chính xác ngữ nghĩa giá trị độc lập (Value Semantics) theo Go specification giữa biến `a: [3]int` và biến `b: [3]int`.
  - Phép gán `b := a` tạo một bản sao giá trị độc lập.
  - Phân tách rõ trước/sau mutation: thao tác `b[0] = 99` chỉ thay đổi ô nhớ riêng của `b[0]`, ô nhớ `a[0]` vẫn giữ nguyên giá trị `10`.
  - Không khẳng định Go specification bắt buộc sao chép vật lý 24 byte hay deep copy dữ liệu đích.
  - Footnote nêu rõ: *Kích thước 24B (3 × 8B) minh họa trên amd64; ngôn ngữ bảo đảm ngữ nghĩa giá trị độc lập, không áp đặt sao chép vật lý hay deep copy.*
- **Nâng cấp thị giác & Typography:**
  - Nâng font chú thích chân hình lên 7.3pt – 7.5pt; đổi màu mực sang tông đậm (`#333333` và `#1A1A1A`), loại bỏ màu xám mờ `#888888` để đạt độ tương phản xuất bản cao.
  - Căn lề phải rộng rãi cho chú thích `b[0] nhận giá trị mới 99 (vùng nhớ riêng của b)`, không chạm viền ngoài.

### 2.2 Hình 2.2 — Slice Descriptor và Chia sẻ mảng nền (`slice-sharing.png`)
- **Đặc tả kỹ thuật:**
  - Minh họa hai slice value riêng biệt (`Descriptor a` và `Descriptor b`) cùng tham chiếu tới một mảng nền chung (`Backing Array`).
  - Phân định rành mạch giữa ngữ nghĩa Go specification (lát cắt là cửa sổ tham chiếu mảng nền) và mô hình triển khai của `gc` 64-bit (cấu trúc 3 word: con trỏ `Data`, `Len`, `Cap`).
  - Không áp đặt cấu trúc bộ nhớ vật lý cố định; loại bỏ khẳng định bitwise copy 24 byte bắt buộc.
  - Thao tác `b[0] = 99` ghi thẳng vào mảng nền dùng chung qua con trỏ `Data`, khiến `a[0]` quan sát thấy giá trị `99` (aliasing).
- **Nâng cấp thị giác & Typography:**
  - Tăng cỡ chữ nhãn trường descriptor (`Data`, `Len`, `Cap`) lên 7.2pt – 8.0pt.
  - Đường vector trực giao (orthogonal routing) uốn góc 90° sắc nét, xuất phát từ chấm tròn gốc `Data` và trỏ mũi tên dứt khoát vào ô `[0]` của mảng nền.
  - Chú thích biến dị đặt lùi an toàn trong lề, tăng tương phản đọc rõ ở mức zoom 100%.

### 2.3 Hình 2.3 — Hình học cửa sổ lát cắt (`slice-window.png`)
- **Đặc tả kỹ thuật:**
  - **Sửa nhãn định danh chính xác:** Phân biệt rõ rệt biến lát cắt `base : []int` với mảng nền 5 phần tử bên dưới (nhãn: `Biến lát cắt gốc: base : []int (Biểu thức gán: x := base[1:3])` và `Mảng nền bên dưới gồm 5 phần tử int:`).
  - Biểu diễn chính xác cửa sổ lát cắt `x := base[1:3]`:
    - Con trỏ `x.Data` trỏ chính xác vào phần tử `base[1]`.
    - Thước đo độ dài `len(x) = 2`: bao phủ cửa sổ quan sát trực tiếp `[20, 30]`.
    - Thước đo sức chứa `cap(x) = 4`: tính từ điểm bắt đầu (`base[1]`) tới hết mảng nền (`[20, 30, 40, 50]`).
  - Footnote Go spec: `base[1:3]` xác định `len = 3 - 1 = 2`, `cap(x) = 4`.
- **Nâng cấp thị giác & Typography:**
  - Tăng chiều cao sơ đồ lên 195 pt để tạo khoảng thở 14 pt giữa thước đo `cap(x)` và dòng footnote, triệt tiêu hoàn toàn sự áp sát/chồng lấn chữ.
  - Nét thước đo và gạch chặn phân đoạn vuông vức, rõ ràng.

### 2.4 Hình 2.4 — Đặc tả phân nhánh append (`append-storage.png`)
- **Đặc tả kỹ thuật:**
  - **Thống nhất tuyệt đối điều kiện trên toàn sơ đồ:** Biểu thức `len(s) + số_phần_tử_thêm <= cap(s)` và `len(s) + số_phần_tử_thêm > cap(s)` được sử dụng đồng bộ tại hộp quyết định trung tâm, trên cả 2 nhánh phân luồng và tiêu đề các hộp nhánh.
  - **Nhánh 1: Đủ sức chứa (`len(s) + số_phần_tử_thêm <= cap(s)`)**:
    - Ngôn ngữ: Tái sử dụng mảng nền hiện tại (không cấp phát mới).
    - Thao tác: Ghi đè phần tử mới vào vị trí index `len(s)`.
    - Kết quả: Trả về descriptor mới có `len` tăng thêm; hệ quả chia sẻ mảng nền (aliasing).
  - **Nhánh 2: Vượt sức chứa (`len(s) + số_phần_tử_thêm > cap(s)`)**:
    - Ngôn ngữ: Cấp phát mảng mới và sao chép phần tử cũ sang.
    - Runtime: `gc/growslice` tính toán dung lượng và phân bổ bộ nhớ mới.
    - Kết quả: Trả về descriptor mới trỏ tới mảng nền mới; hệ quả phân tách mảng nền (không đổi mảng cũ).
  - **Cảnh báo phân biệt Shallow vs Deep copy:** Footnote nêu rõ: *Nhánh 2 tách biệt mảng nền độc lập cho phần tử kiểu giá trị cơ bản. Nếu phần tử chứa con trỏ hoặc struct lồng tham chiếu, đây là shallow copy mảng nền, không phải deep copy dữ liệu đích.*
- **Nâng cấp thị giác & Typography (Zero Collision Routing):**
  - **Khắc phục triệt để lỗi chồng chữ giữa 2 nhánh:** Căn giữa nhãn điều kiện `[Có] len(s) + số_phần_tử_thêm <= cap(s)` và `[Không] len(s) + số_phần_tử_thêm > cap(s)` trực tiếp phía trên từng hộp nhánh tương ứng, tạo khoảng cách an toàn rộng tới 68 pt ở giữa, hoàn toàn không cắt hoặc đè lên trục phân nhánh thẳng đứng.

---

## 3. DANH SÁCH FILE VÀ ARTIFACT BÀN GIAO

1. **4 File sơ đồ kỹ thuật hoàn thiện (300 DPI PNG):**
   - `assets/diagrams/array-copy.png` (1868 × 617 px)
   - `assets/diagrams/slice-sharing.png` (1868 × 817 px)
   - `assets/diagrams/slice-window.png` (1868 × 813 px)
   - `assets/diagrams/append-storage.png` (1868 × 917 px)
2. **Kịch bản sinh sơ đồ & Renderer Preview:**
   - `scripts/ch02_vector_diagrams.py`: Bộ vẽ vector ReportLab chuẩn xác và xuất ảnh 300 DPI.
   - `scripts/build_ch02_preview.py`: Renderer preview độc lập, chỉ xuất 4 sơ đồ ở kích thước thực tế.
3. **Artifact Preview độc lập (Chỉ gồm 4 sơ đồ):**
   - PDF Preview 2 trang: `book/design/agent2-ch02/ch02_preview.pdf`
   - 2 Ảnh specimen trang (200 DPI):
     - [Trang 1: Hình 2.1 (Array Copy) & Hình 2.2 (Slice Sharing)](specimens/ch02_diagrams_p01.png)
     - [Trang 2: Hình 2.3 (Slice Window) & Hình 2.4 (Append Branching)](specimens/ch02_diagrams_p02.png)
4. **Vệ sinh repository:**
   - Đã xóa sạch 12 file specimen `ch02_page_01.png` .. `ch02_page_12.png` của đợt preview cũ.

---

## 4. KẾT QUẢ KIỂM TRA CHẤT LƯỢNG (QA AUDIT)

| Hạng mục kiểm tra | Kết quả | Chi tiết kiểm chứng |
| :--- | :---: | :--- |
| **Strict Content Lock** | **PASS** | `git diff main book/chapters/02-gia-tri-slice-va-aliasing.md` rỗng (0 dòng thay đổi). |
| **Code Block: 0 Line Numbers** | **PASS** | Tuyệt đối không thêm số dòng vào bất kỳ code block nào. |
| **Code Width Preflight** | **PASS** | `python scripts/validate_code_width.py`: 0 dòng tràn lề (usable width 448.22 pt). |
| **Publication Contracts** | **PASS** | `python scripts/test_publication_contracts.py`: 16/16 tests passed. |
| **Visual QA Zoom 100%** | **PASS** | Đã kiểm tra trực quan cả 4 ảnh sơ đồ và 2 trang preview: không chồng chữ, không cắt nhãn, tương phản cao. |
| **Unified Append Condition** | **PASS** | Toàn bộ sơ đồ dùng đồng nhất `len(s) + số_phần_tử_thêm <= cap(s)`. |
| **Distinction: base vs backing array** | **PASS** | Hình 2.3 phân biệt rõ `base : []int` và mảng nền 5 phần tử. |
| **Memory Disclaimer** | **PASS** | Phân định rõ Go spec vs mô hình `gc` 64-bit; disclaimer shallow vs deep copy đầy đủ. |

---

## 5. HARD APPROVAL GATE

```text
================================================================================
                    HARD APPROVAL GATE: AWAITING_MANUAL_APPROVAL
================================================================================
  [X] TUYỆT ĐỐI KHÔNG MERGE VÀO MAIN.
  [X] TUYỆT ĐỐI KHÔNG SỬA ĐỔI HOẶC GHI ĐÈ GOLANG_MASTER.PDF.
  [X] Tất cả thay đổi chỉ nằm trên branch: design/ch02-agent2-redesign.
  [X] Nội dung bài giảng Chương 2 giữ nguyên vẹn 100% so với main.
  [X] Bản preview độc lập chỉ gồm đúng 4 sơ đồ ở kích thước xuất bản thực tế.
  [X] Sẵn sàng để người dùng và ChatGPT Reviewer tiến hành đối chiếu phê duyệt.
================================================================================
```
