# BÁO CÁO VI CHỈNH KỸ THUẬT SƠ ĐỒ CHƯƠNG 08 (AGENT 2)
**Ngày thực hiện:** 17/10/2026  
**Nhánh công việc:** `design/ch08-agent2-redesign` (baseline: `4150c33`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và reviewer kiểm tra độc lập trước khi phê duyệt tích hợp)

---

## 1. Mục tiêu vi chỉnh kỹ thuật theo yêu cầu phê duyệt
1. **Strict Content Lock:** Giữ nguyên tuyệt đối 100% nội dung Markdown `book/chapters/08-mot-race-bat-dau-tu-dau.md`, toàn bộ code block, bảng biểu, caption, typography và file sách gốc `Golang_Master.pdf`.
2. **Chuẩn hóa cú pháp gán slice:**
   - Sửa `append(r.reports, report)` thành biểu thức đầy đủ và chính xác theo Go spec:
     `3. r.reports = append(r.reports, report)`
   - Đúng từng ký tự với mã nguồn `fixed/registry.go`.
3. **Mô hình hóa chi tiết 4 bước trong `registry.Add(report)`:**
   - Bước 1: `1. r.mu.Lock()` $\rightarrow$ Chiếm khóa bảo vệ slice.
   - Bước 2: `2. defer r.mu.Unlock()` $\rightarrow$ Đăng ký nhả khóa khi return.
   - Bước 3: `3. r.reports = append(r.reports, report)` $\rightarrow$ Cập nhật slice dưới sự bảo vệ của lock.
   - Bước 4: `4. Add() return` $\rightarrow$ Defer kích hoạt `r.mu.Unlock()`.
4. **Loại bỏ khẳng định về giải phóng stack (Implementation Detail):**
   - Không đánh đồng việc kết thúc hàm worker với giải phóng stack ngay lập tức của runtime.
   - Chuẩn hóa theo API contract của `sync.WaitGroup`:
     * `wg.Done() thực thi (tại return)`: Mỗi `Done()` giảm bộ đếm của WaitGroup.
     * `Worker hoàn tất phần việc`: Kết thúc phạm vi công việc do WaitGroup theo dõi.
5. **Chuẩn hóa nhãn WaitGroup và mốc hoàn tất:**
   - Phân biệt rõ: Mỗi lần `Done()` chỉ giảm bộ đếm công việc còn chờ; **lượt `Done()` cuối cùng** đưa counter về 0 mới mở khóa cho `Wait()` trả về.
   - Nhãn cạnh đứt ngang chuẩn hóa: `Lượt Done() cuối mở khóa Wait()` (happens-before synchronization barrier).
6. **Tách biệt rạch ròi giữa Mutex và WaitGroup:**
   - **`sync.Mutex`:** Bảo vệ truy cập đồng thời vào slice `reports` (loại trừ data race).
   - **`sync.WaitGroup`:** Thiết lập mốc hoàn tất (bảo đảm mọi worker đã xong việc trước khi đọc snapshot).
   - Tách kiểm tra `len(reports) == workers` thành kiểm tra bất biến nghiệp vụ, không đồng nhất nó với bằng chứng vắng mặt data race.
7. **Chuẩn hóa khuyến nghị về `time.Sleep`:**
   - Thay khẳng định tuyệt đối bằng:
     `• Không dùng time.Sleep thay cho cơ chế đồng bộ: Sleep chỉ đoán thời gian, không công bố quan hệ thứ tự; đồng bộ phải dựa trên WaitGroup/channel.`
   - Thừa nhận đầy đủ các cơ chế đồng bộ chính thức khác trong Go (channel, sync primitives).
8. **Nâng cao khả năng đọc (Visual QA):**
   - Toàn bộ nhãn nhỏ được nâng từ 5.8 pt lên 6.0 – 6.8 pt.
   - 100% thuần Grayscale ($R = G = B$).
   - Giữ nguyên bố cục 2 cột, 4 tầng song song không cắt nét.

---

## 2. Kết quả kiểm định tự động (Verification Suite)
- `python scripts/test_publication_contracts.py`: **16/16 PASS (100%)**
- `python scripts/validate_code_width.py`: **PASS (0 dòng tràn lề)**
- `git diff main -- book/chapters/08-mot-race-bat-dau-tu-dau.md`: **0 DIFF (Tài liệu bài giảng hoàn toàn nguyên vẹn)**
- `git diff main -- book/chapters/`: **0 DIFF (Toàn bộ Markdown sách được bảo toàn)**
- `Golang_Master.pdf`: **KHÔNG THAY ĐỔI** (Bảo toàn 614 trang nguyên bản)
- `Grayscale Audit`: **0 non-grayscale pixels / 2,610,261 pixels (100% pure monochrome)**

---

## 3. Danh mục tệp cập nhật trên branch `design/ch08-agent2-redesign`
1. `assets/diagrams/waitgroup-completion-proof.png` (PNG vector xuất bản 320 DPI, 2117 × 1233 px, thuần grayscale R=G=B)
2. `book/design/agent2-ch08/ch08_preview.pdf` (PDF preview độc lập 1 trang tại kích thước 1:1)
3. `book/design/agent2-ch08/specimens/ch08_diagrams_p01.png` (Specimen trực quan của trang preview)
4. `scripts/ch08_vector_diagrams.py` (Script ReportLab sinh vector diagram chuẩn xuất bản)
5. `scripts/build_ch08_preview.py` (Script ReportLab + PyMuPDF sinh preview PDF và ảnh specimen)
6. `book/design/agent2-ch08/REPORT_AGENT2_CH08.md` (Báo cáo vi chỉnh này)
