# Hướng Dẫn In Ấn — Sách Golang 2026

> [!WARNING]
> **TRẠNG THÁI CHẾ BẢN VẬT LÝ:** `PHYSICAL_PRINT_READINESS = BLOCKED_PENDING_PRINTER_SPEC`  
> - Độ dày gáy $28\,\text{mm}$ hiện chỉ là kích thước ước tính hình học danh định (nominal design estimate), **CHƯA ĐƯỢC NHÀ IN XÁC NHẬN** qua phép đo caliper thực tế trên lô giấy Ford $80\,\text{gsm}$ (độ ẩm, độ xốp/bulk factor, và dung sai keo dán gáy PUR).
> - Nghiêm cấm ký duyệt lệnh in ấn công nghiệp hoặc gia công bìa cứng/bìa mềm trước khi nhà in cung cấp phiếu đo caliper thực nghiệm.

---

## 1. Phân định giữa PDF Ứng viên (611 trang) và Tệp Chế bản In (612 trang)

1. **PDF Ứng viên Nội dung (Content Candidate PDF):**
   - Vị trí: `tmp/pdfs/Golang_Master.candidate.pdf`
   - Số trang: **ĐÚNG 611 TRANG** (Toàn bộ 29 chương, Atlas Thư viện và Phụ lục A).
   - SHA-256: `c799ddeb95b3695e4109ca7e041f21ed0098b22dbbb436d61b75ecee7207f09b`
   - Trạng thái: Ứng viên nghiệm thu độc lập (`AWAITING_MANUAL_APPROVAL`).

2. **Tệp Ruột Sách Chế bản In Hai Mặt (Duplex Prepress Book Block):**
   - Vị trí: [`02_RUOT_SACH_GOLANG_612TRANG_A4.pdf`](02_RUOT_SACH_GOLANG_612TRANG_A4.pdf)
   - Lưu ý quan trọng: Tệp tin `02_RUOT_SACH_GOLANG_612TRANG_A4.pdf` hiện lưu trong kho mã nguồn là tệp bản in của đợt release trước (SHA-256: `2d70b44e62ee4c743a06a590b6dd6ebc5a86955c9956888f78768d30889b041d`, khớp với `Golang_Master.pdf` gốc).
   - Quy trình chế bản in hai mặt: Khi Reviewer phê duyệt promote candidate 611 trang, khâu prepress sẽ bổ sung thêm đúng 01 trang trắng ở cuối (Trang 612) nhằm thỏa mãn quy cách in hai mặt (duplex) và đóng tay sách chẵn chia hết cho 4 ($612 = 153 \times 4$). Thao tác này **BẢO LƯU NGUYÊN VẸN 100% NỘI DUNG VÀ HÌNH HỌC CỦA 611 TRANG ĐẦU TIÊN**.

---

## 2. Thông số kỹ thuật tệp chế bản

1. **[`01_BIA_TRAI_GOLANG_A4_GAY28MM.pdf`](01_BIA_TRAI_GOLANG_A4_GAY28MM.pdf)**
   - Khổ in: $454.0 \times 303.0\,\text{mm}$ (Bìa 4 + Gáy $28\,\text{mm}$ + Bìa 1 + Bleed $3\,\text{mm}$)
   - Giấy bìa dự kiến: Couche $300\,\text{gsm}$, cán màng mờ, cấn 4 đường gáy.
   - Trạng thái: **BLOCKED** — Đang chờ phiếu đo caliper thực tế từ nhà in để điều chỉnh kích thước gáy chính xác trước khi xuất bản kẽm in bìa.

2. **[`02_RUOT_SACH_GOLANG_612TRANG_A4.pdf`](02_RUOT_SACH_GOLANG_612TRANG_A4.pdf)**
   - Khổ in: ISO A4 ($210.0 \times 297.0\,\text{mm}$)
   - Số trang dự kiến: 612 trang (611 trang nội dung ứng viên + 1 trang trắng đệm cuối).
   - Giấy ruột dự kiến: Woodfree / Ford $80\,\text{gsm}$, in 2 mặt đen trắng (1/1 Monochrome).
   - Đóng cuốn dự kiến: Khâu chỉ dán gáy keo nhiệt PUR áp lực cao.

*Chi tiết thông số kỹ thuật xem tại tệp [`THONG_SO_KY_THUAT_NHA_IN.txt`](THONG_SO_KY_THUAT_NHA_IN.txt).*
