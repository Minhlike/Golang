# QUY CHUẨN THIẾT KẾ VÀ HỆ THỐNG IN ẤN (PRINT STYLE STANDARD)

Tài liệu này xác lập quy chuẩn kỹ thuật xuất bản (print contract) cho toàn bộ ấn bản `Golang_Master.pdf`, làm căn cứ nhất quán cho việc biên soạn các chương tiếp theo (Chương 22, 23...).

---

## 1. HÌNH HỌC TRANG VÀ LỀ TRANG ĐỐI XỨNG (FACING PAGES)

Ấn bản được thiết lập theo chuẩn sách in ~300 trang với hệ thống lề đối xứng (Mirrored Margins / Facing Pages):

- **Kích thước trang:** ISO A4 ($210\text{ mm} \times 297\text{ mm}$).
- **Lề trong (Gutter / Inside Margin):** $2.4\text{ cm}$ ($68.03\text{ pt}$). Đảm bảo khoảng cách an toàn khi đóng gáy sách (perfect binding / case binding), chữ không bị cuốn vào khe gáy.
- **Lề ngoài (Outside Margin):** $1.8\text{ cm}$ ($51.02\text{ pt}$).
- **Lề trên (Top Margin):** $2.0\text{ cm}$ ($56.69\text{ pt}$).
- **Lề dưới (Bottom Margin):** $2.0\text{ cm}$ ($56.69\text{ pt}$).
- **Độ rộng khối nội dung (Printable Width):** Đúng $16.8\text{ cm}$ ($476.22\text{ pt}$). Mọi thành phần (đoạn văn, bảng biểu, hộp mã lệnh, ghi chú) đều tuân thủ độ rộng chuẩn $16.8\text{ cm}$.

### Tọa độ trang lẻ (Recto - Trang phải):
- Khung nội dung bắt đầu từ $x = 2.4\text{ cm}$ (lề trong) đến $x = 19.2\text{ cm}$ (lề ngoài).
- Số trang đặt ở góc ngoài cùng bên phải: $x = 19.2\text{ cm}$, $y = 1.15\text{ cm}$.

### Tọa độ trang chẵn (Verso - Trang trái):
- Khung nội dung bắt đầu từ $x = 1.8\text{ cm}$ (lề ngoài) đến $x = 18.6\text{ cm}$ (lề trong).
- Số trang đặt ở góc ngoài cùng bên trái: $x = 1.8\text{ cm}$, $y = 1.15\text{ cm}$.

---

## 2. BỘ PHÔNG CHỮ XUẤT BẢN

Toàn bộ phông chữ được nhúng trực tiếp (embedded TrueType), không phụ thuộc vào hệ thống người đọc:

| Vai trò | Phông chữ | Cỡ chữ / Dòng (pt) | Màu sắc |
| :--- | :--- | :--- | :--- |
| **Tiêu đề sách (Title)** | Source Sans 3 Semibold | 36 / 42 | `#000000` (100% Black) |
| **Tiêu đề chương (H1)** | Source Sans 3 Semibold | 22 / 28 | `#000000` |
| **Tiêu đề mục (H2)** | Source Sans 3 Semibold | 16 / 21 | `#000000` |
| **Tiêu đề tiểu mục (H3)** | Source Sans 3 Semibold | 13.5 / 18 | `#000000` |
| **Thân bài (Body text)** | Source Serif 4 Regular | 13.5 / 20.5 | `#000000` |
| **Danh sách (Bullets)** | Source Serif 4 Regular | 13.5 / 20.5 | `#000000` |
| **Mã nguồn (Code block)** | JetBrains Mono Regular | 11.5 / 15.5 | `#000000` |
| **Bảng biểu (Table text)** | Source Serif 4 Regular | 10.5 / 14.2 | `#000000` |
| **Chú thích (Caption)** | Source Serif 4 Regular | 10.0 / 13.5 | `#2E2E2E` |
| **Tài liệu tham khảo (Ref)** | Source Sans 3 Regular | 9.5 / 12.8 | `#555555` |

---

## 3. NGUYÊN TẮC GRAYSCALE-FIRST (AN TOÀN CHO IN ẤN)

1. **Không dùng màu sắc để truyền tải ngữ nghĩa:** Toàn bộ nội dung sách phải đọc và phân biệt rõ ràng khi in bằng mực đen thuần túy hoặc khi photocopy đen trắng.
2. **Nền hộp mã và bảng biểu:** Sử dụng sắc độ xám nhạt đạt độ tương phản in ấn chuẩn:
   - Hộp mã lệnh: Nền `#F4F4F2`, viền bao `#666666` độ dày $0.65\text{ pt}$.
   - Dòng tiêu đề bảng biểu: Nền `#EAEAE6`, lưới kẻ bảng `#666666` độ dày $0.45\text{ pt}$.
   - Khối trích dẫn (Blockquote): Nền `#F6F6F4`, đường chỉ dẫn bên trái `#000000` độ dày $2.0\text{ pt}$.
3. **Đường nét (Line weights):**
   - Đường kẻ ngăn cách chính (Rule): $1.0\text{ pt}$ hoặc $0.55\text{ pt}$.
   - Đường chân trang (Footer hairline): $0.35\text{ pt}$, màu `#CCCCCC`.

---

## 4. QUY TẮC MẶT TRƯỚC VÀ MỤC LỤC (FRONT MATTER & TOC)

- **Trang bìa (Title Page):**
  - Tên sách: `GOLANG`
  - Phụ đề: `Giáo trình cập nhật liên tục về Kỹ nghệ phần mềm và DevOps/SRE`
  - Tác giả: `Đoàn Ngọc Hoàng Minh`
  - Minh họa: Cấu trúc hình học vector mô-đun chữ nhật (Modular Shelving Grid). Không dùng ảnh raster.
  - Tuyệt đối không có số trang hoặc chân trang trên trang bìa.
- **Mục lục (MỤC LỤC):**
  - Tiêu đề mục lục: `MỤC LỤC`. Không kèm đoạn văn giải thích trạng thái bản thảo.
  - Định dạng bảng 2 cột: Cột trái chứa tên chương, cột phải căn lề phải chứa số trang tương ứng.
  - Không sử dụng ký tự bullet `•` cho các chương trong mục lục.

---

## 5. THỨ TỰ BẤT BIẾN CỦA BẢN THẢO (STRUCTURAL INVARIANTS)

Bất kể sau này có thêm bao nhiêu chương mới, cấu trúc xuất bản luôn tuân thủ nghiêm ngặt:

$$\text{Front Matter (Bìa, Mục lục)} \longrightarrow \text{Chương 00, 01 \dots N} \longrightarrow \text{Back Matter (50 Thư viện)} \longrightarrow \text{Phụ lục A (Atlas Lỗi Go — LUÔN Ở CUỐI SÁCH)}$$
