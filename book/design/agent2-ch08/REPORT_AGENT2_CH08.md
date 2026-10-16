# BÁO CÁO THIẾT KẾ SƠ ĐỒ KỸ THUẬT CHƯƠNG 08 (AGENT 2)
**Ngày thực hiện:** 17/10/2026  
**Nhánh công việc:** `design/ch08-agent2-redesign` (baseline: `12e0723`)  
**Trạng thái:** `AWAITING_MANUAL_APPROVAL` (Chờ người dùng và reviewer kiểm tra độc lập trước khi phê duyệt tích hợp)

---

## 1. Bối cảnh kiểm toán chuyển giao từ Chương 06 & 07 sang Chương 08
- **Chương 06 (`06-thay-doi-khong-so-hai.md`)**: Kiểm toán toàn bộ văn bản và bản in Master PDF (trang 119–143) $\rightarrow$ **0 sơ đồ** (Không có hình ảnh).
- **Chương 07 (`07-du-lieu-di-vao-va-di-ra.md`)**: Kiểm toán toàn bộ văn bản và bản in Master PDF (trang 144–157) $\rightarrow$ **0 sơ đồ** (Không có hình ảnh).
- **Chương 08 (`08-mot-race-bat-dau-tu-dau.md`)**: Chương kế tiếp trong lộ trình có chứa hình ảnh kỹ thuật:
  * **Hình 20 (Trang 163, xref 365):** `assets/diagrams/waitgroup-completion-proof.png`
  * Bounding box trên Master PDF: `Width = 476.22 pt, Height = 277.31 pt` (Tỉ lệ khung hình AR = 1.71731, trọn vẹn bề ngang trang in A4).

---

## 2. Mục tiêu thiết kế vector xuất bản Chương 08
1. **Strict Content Lock:** Giữ nguyên tuyệt đối 100% nội dung Markdown `book/chapters/08-mot-race-bat-dau-tu-dau.md`, toàn bộ code block, bảng biểu, caption, typography và file sách gốc `Golang_Master.pdf`.
2. **Khớp 100% với mã nguồn lab thực tế (`labs/part8-ordering-proof/`):**
   - Phản ánh chính xác tiến trình kiểm thử `TestRegistryKeepsCompletedReports`:
     * Điều phối viên thiết lập `wg.Add(workers)` trước khi spawn bất kỳ worker nào.
     * Mỗi worker goroutine gọi `defer wg.Done()` ngay khi vào hàm.
     * Thao tác thêm kết quả `registry.Add(report)` thực hiện: `mu.Lock()` $\rightarrow$ `append` $\rightarrow$ `mu.Unlock()`.
     * Khi hàm worker return, `defer` kích hoạt `wg.Done()`, giảm counter của WaitGroup.
     * Bên điều phối treo thực thi tại `wg.Wait()` cho đến khi counter trở về 0.
     * `wg.Wait()` giải phóng, bên điều phối gọi `registry.Snapshot()` với cơ chế `copy` an toàn, kiểm chứng `len(reports) == workers`.
3. **Mô hình hóa quan hệ Happens-Before theo chuẩn Go Memory Model:**
   - **Thứ tự lập trình (Program Order):** Các mũi tên liền dọc trong từng goroutine bảo toàn trật tự thực thi dòng lệnh.
   - **Mốc hoàn tất WaitGroup (Completion Barrier):** Cạnh đứt ngang duy nhất từ `wg.Done()` sang `wg.Wait() giải phóng & trả về` với nhãn chú thích: `Done() mở khóa lượt Wait() này` (khớp chính xác từng từ trong caption và PUML gốc).
   - **Tính bắc cầu của Happens-Before (Transitivity):**
     $$\text{registry.Add(report)} \xrightarrow{\text{code}} \text{wg.Done()} \xrightarrow{\text{sync.WaitGroup}} \text{wg.Wait() trả về} \xrightarrow{\text{code}} \text{registry.Snapshot()}$$
     $\implies$ Mọi thay đổi bộ nhớ trong `Add()` đều hiển thị một cách tất định đối với `Snapshot()`.
4. **Phân biệt rạch ròi bản chất giữa `sync.WaitGroup` và `sync.Mutex`:**
   - `WaitGroup` cung cấp tín hiệu hoàn tất công việc, **KHÔNG** tự bảo vệ bộ nhớ.
   - `Mutex` bắt buộc để ngăn chặn data race giữa các worker khi ghi đồng thời vào slice `reports`.
   - Cảnh báo rõ nguyên tắc cấm dùng `time.Sleep` thay cho cơ chế đồng bộ chính thức.
5. **Kiến trúc bố cục 4 tầng song song (4-Row Parallel Lifecycle Layout):**
   - Loại bỏ hoàn toàn các đường mũi tên chéo cắt nhau (loại bỏ mũi tên `Unlock -> Lock` thừa từng gây rối mắt ở bản nháp cũ).
   - Tầng 1: Khởi động & Đăng ký (`defer wg.Done()` $\leftrightarrow$ `wg.Add(workers)`).
   - Tầng 2: Thực thi & Treo chờ (`registry.Add(report)` $\leftrightarrow$ `wg.Wait() [TREO CHỜ]`).
   - Tầng 3: Mốc hoàn tất (`wg.Done() thực thi` $\xrightarrow{\text{cạnh đứt ngang}}$ `wg.Wait() giải phóng & trả về`).
   - Tầng 4: Kết thúc & Đọc bất biến (`Worker kết thúc` $\leftrightarrow$ `reports := registry.Snapshot()`).
6. **Chuẩn hóa bảng màu Grayscale thuần túy (`R = G = B`):**
   - 100% điểm ảnh có $R = G = B$ (0 pixel có màu hoặc sắc pha lệch).
   - Độ tương phản sắc nét, tối ưu cho in ấn chất lượng cao.
7. **Visual QA & Publication Match:**
   - Kích thước xuất bản thực tế: **476.22 × 277.31 pt** (AR = 1.71731, khớp chính xác 1:1 với xref 365 Trang 163).
   - Xuất bản ảnh 320 DPI (2117 × 1233 px), chữ rõ ràng từ 5.8 pt đến 7.8 pt, không có hiện tượng cắt chữ, đè nét hay tràn viền.

---

## 3. Kết quả kiểm định tự động (Verification Suite)
- `python scripts/test_publication_contracts.py`: **16/16 PASS (100%)**
- `python scripts/validate_code_width.py`: **PASS (0 dòng tràn lề)**
- `git diff main -- book/chapters/08-mot-race-bat-dau-tu-dau.md`: **0 DIFF (Tài liệu bài giảng hoàn toàn nguyên vẹn)**
- `git diff main -- book/chapters/`: **0 DIFF (Toàn bộ Markdown sách được bảo toàn)**
- `Golang_Master.pdf`: **KHÔNG THAY ĐỔI** (Bảo toàn 614 trang nguyên bản)
- `Grayscale Audit`: **0 non-grayscale pixels / 2,610,261 pixels (100% pure monochrome)**

---

## 4. Danh mục tệp cập nhật trên branch `design/ch08-agent2-redesign`
1. `assets/diagrams/waitgroup-completion-proof.png` (PNG vector xuất bản 320 DPI, 2117 × 1233 px, thuần grayscale R=G=B)
2. `book/design/agent2-ch08/ch08_preview.pdf` (PDF preview độc lập 1 trang tại kích thước 1:1)
3. `book/design/agent2-ch08/specimens/ch08_diagrams_p01.png` (Specimen trực quan của trang preview)
4. `scripts/ch08_vector_diagrams.py` (Script ReportLab sinh vector diagram chuẩn xuất bản)
5. `scripts/build_ch08_preview.py` (Script ReportLab + PyMuPDF sinh preview PDF và ảnh specimen)
6. `book/design/agent2-ch08/REPORT_AGENT2_CH08.md` (Báo cáo thiết kế này)
