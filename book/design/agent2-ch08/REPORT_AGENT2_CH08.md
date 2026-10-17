# BÁO CÁO VI CHỈNH KỸ THUẬT CUỐI CÙNG SƠ ĐỒ CHƯƠNG 08 (AGENT 2)
**Ngày thực hiện:** 17/10/2026  
**Nhánh công việc:** `design/ch08-agent2-redesign` (baseline: `b5c84ed`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và reviewer kiểm tra độc lập trước khi phê duyệt tích hợp)

---

## 1. Mục tiêu vi chỉnh kỹ thuật cuối cùng (Last Micro-Fix)
1. **Strict Content Lock:** Giữ nguyên tuyệt đối 100% nội dung Markdown `book/chapters/08-mot-race-bat-dau-tu-dau.md`, toàn bộ code block, bảng biểu, caption, typography và file sách gốc `Golang_Master.pdf`.
2. **Chuẩn hóa chú thích về `time.Sleep`:**
   - Sửa dòng chú thích tại chân trang: không ngụ ý chỉ WaitGroup/channel mới tạo đồng bộ; nêu chính xác các cơ chế theo Go Memory Model:
     `• Không dùng time.Sleep thay cho cơ chế đồng bộ: Sleep không tạo happens-before; đồng bộ phải dùng cơ chế phù hợp theo Go Memory Model (channel, mutex, atomic,...).`
   - Nhấn mạnh bản chất: `time.Sleep` không thiết lập quan hệ happens-before tất định; sự đồng bộ phải dựa trên các primitive chính thức của Go Memory Model.
3. **Nâng cấp triệt để các nhãn 5.8 pt còn lại:**
   - Nhãn dòng 395 (`r.mu.Lock() → copy → r.mu.Unlock(); assert len == workers`): Nâng từ 5.8 pt lên **6.1 pt** (độ rộng 145.5 pt trong khung 184 pt, lề an toàn ~38.5 pt, tuyệt đối không tràn viền).
   - Nhãn dòng 411 (`go worker(i)`): Nâng từ 5.8 pt lên **6.2 pt**, mở rộng khung huy hiệu từ 48 pt lên **52 pt** (cách đều hai viền cột 6.11 pt, căn giữa hoàn hảo).
   - Kiểm tra toàn bộ script: **100% font chữ $\ge 6.0\text{ pt}$**, không còn bất kỳ nhãn nào dưới 6.0 pt.
4. **Bảo toàn toàn bộ thành phần đã đạt:**
   - Cú pháp gán slice: `3. r.reports = append(r.reports, report)` đúng `fixed/registry.go`.
   - Tiến trình 4 bước chuẩn xác của `registry.Add(report)`: `Lock()` $\rightarrow$ `defer Unlock()` $\rightarrow$ `append` $\rightarrow$ `return`.
   - Phân biệt rõ vai trò: Mutex bảo vệ an toàn vùng nhớ (chống data race) vs WaitGroup thiết lập mốc hoàn tất (kiểm tra bất biến logic nghiệp vụ).
   - Phân biệt rõ: Mỗi `Done()` giảm bộ đếm công việc vs Lượt `Done()` cuối cùng đưa counter về 0 mở khóa `Wait()` trả về.
   - Bố cục 2 cột, 4 tầng song song không cắt nét; 100% thuần Grayscale ($R = G = B$).
5. **Repository Hygiene:**
   - Chỉ cập nhật PNG asset, preview PDF 1 trang, ảnh specimen, generator script và báo cáo này.
   - Không tạo thêm file thừa hay thư mục mới.

---

## 2. Kết quả kiểm định tự động (Verification Suite)
- `python scripts/test_publication_contracts.py`: **16/16 PASS (100%)**
- `python scripts/validate_code_width.py`: **PASS (0 dòng tràn lề)**
- `git diff main -- book/chapters/08-mot-race-bat-dau-tu-dau.md`: **0 DIFF (Tài liệu bài giảng hoàn toàn nguyên vẹn)**
- `git diff main -- book/chapters/`: **0 DIFF (Toàn bộ Markdown sách được bảo toàn)**
- `Golang_Master.pdf`: **KHÔNG THAY ĐỔI** (Bảo toàn 614 trang nguyên bản)
- `Grayscale Audit`: **0 non-grayscale pixels / 2.610.261 pixels (100% pure monochrome)**
- `Font Size Audit`: **Min font size = 6.0 pt (0 nhãn < 6.0 pt)**

---

## 3. Danh mục tệp cập nhật trên branch `design/ch08-agent2-redesign`
1. `assets/diagrams/waitgroup-completion-proof.png` (PNG vector xuất bản 320 DPI, 2117 × 1233 px, thuần grayscale R=G=B, min font 6.0 pt)
2. `book/design/agent2-ch08/ch08_preview.pdf` (PDF preview độc lập 1 trang tại kích thước 1:1)
3. `book/design/agent2-ch08/specimens/ch08_diagrams_p01.png` (Specimen trực quan của trang preview)
4. `scripts/ch08_vector_diagrams.py` (Script ReportLab cập nhật nhãn font 6.0+ pt và chú thích Go Memory Model)
5. `book/design/agent2-ch08/REPORT_AGENT2_CH08.md` (Báo cáo vi chỉnh này)
