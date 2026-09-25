# CẨM NANG CẤU TRÚC WORKSPACE (WORKSPACE GUIDE)

> **Dự án:** Chuyên khảo Kỹ thuật Go Chuyên sâu (Advanced Go Engineering Manuscript & Labs)  
> **Repository:** `D:\Golang` (`https://github.com/Minhlike/Golang`)  
> **Toolchain cục bộ:** Go 1.27.1 (`windows/amd64`) đặt tại `.tools/go1.27.1`

---

## 1. Cấu Trúc Thư Mục Dự Án

| Thư mục / Tệp tin | Vai trò kỹ thuật | Trạng thái cam kết (Git) |
|---|---|---|
| `book/` | Bản thảo giáo trình (Markdown). Bao gồm các chương từ `ch00a` đến `ch28`. | Tracked |
| `labs/` | Mã nguồn thực hành độc lập cho từng chương (`part01` đến `part28`). | Tracked |
| `projects/` | Các dự án phần mềm mẫu tích hợp quy mô lớn (microservices, operators). | Tracked |
| `library_sources/` | Bộ lưu trữ và catalog thư viện bên thứ ba (50 thư viện thực chiến). Mã nguồn tải về được cache tại `library_sources/repos/`. | `lock.json` tracked, `repos/` ignored |
| `assets/` | Hình ảnh kiến trúc, tài nguyên đồ họa phục vụ xuất bản sách. | Tracked |
| `scripts/` | Bộ công cụ tự động hóa: kiểm tra code width, build PDF, probe compiler/assembly, audit. | Tracked |
| `.workspace/` | Không gian làm việc cục bộ: lưu bằng chứng compiler/runtime, log scratch, bản dựng tạm, tài liệu lưu trữ. | Ignored hoàn toàn |
| `.tools/` | Bản phân phối Go compiler cục bộ (`go1.27.1`). Toàn bộ mã nguồn thư viện chuẩn và runtime nằm tại `.tools/go1.27.1/src/`. | Ignored |
| `tmp/` | Thư mục bộ đệm tạm thời của hệ thống và các công cụ dòng lệnh. | Ignored |
| `Golang_Master.pdf` | Tệp xuất bản PDF chính thức hoàn chỉnh của toàn bộ cuốn sách. | Tracked tại root |
| `Golang_Master.prev.pdf` | Bản sao lưu đối chiếu của bản dựng PDF xuất bản gần nhất. | Tracked tại root |

---

## 2. Kế Hoạch & Bằng Chứng Phục Vụ Foundation Deep-Rewrite

Mọi tài liệu chỉ đạo và kho lưu trữ phục vụ cho chiến dịch đại tu khối nền tảng được định vị tại các điểm sau:

1. **Kế hoạch phạm vi chương:** `book/FOUNDATION_CHAPTERS.md` (Phân loại `FOUNDATION_CORE`, `FOUNDATION_BRIDGE` và `APPLICATION/SYSTEMS`).
2. **Cẩm nang chiến dịch biên soạn:** `book/FOUNDATION_DEEP_REWRITE_HANDOFF.md` (Quy định First-Principles, Zero-Bullet Rule, chuẩn ngôn ngữ ~99% tiếng Việt, phân định 5 cấp độ assembly).
3. **Bảng phân tích phản biện kỹ thuật:** `book/GO_CRITICAL_ANALYSIS_PLAN.md` (10 chủ đề phản biện cốt lõi: GC latency, stack thrashing, scheduling preemption, cgo, fragmentation, v.v.).
4. **Bản đồ mã nguồn GOROOT:** `book/GO_SOURCE_RESEARCH_PATHS.md` (Địa chỉ chính xác trong `.tools/go1.27.1/src/` cho compiler passes và runtime subsystems).
5. **Kho lưu trữ bằng chứng thực nghiệm cục bộ:** `.workspace/foundation-evidence/` (Nơi chứa output của compiler `-S`, objdump disassembly, escape analysis logs, và SSA prove diagnostics).

---

## 3. Hướng Dẫn Vận Hành Các Script Cơ Bản

### 3.1. Kiểm Tra Độ Rộng Khối Mã Nguồn (Code Width Validator)
Kiểm tra toàn bộ các khối mã nguồn (````go ... ````) trong `book/` để bảo đảm không vượt quá giới hạn 82 ký tự/dòng, tránh tràn khung khi dàn trang sách in / PDF:
```powershell
uv run --with reportlab,pypdf python scripts/validate_code_width.py
```
*Điều kiện thành công:* Báo cáo trả về `CODE_LINES_OVERFLOWING = 0`.

### 3.2. Biên Dịch Xuất Bản Toàn Tập Sách (Build Master PDF)
Tổng hợp toàn bộ các tệp Markdown trong `book/`, nhúng hình ảnh từ `assets/` và biên dịch thành tệp PDF hoàn chỉnh:
```powershell
python scripts/build_master.py
```
*Đầu ra:* Cập nhật tệp `Golang_Master.pdf` tại thư mục gốc.

### 3.3. Trích Xuất Bằng Chứng Trình Biên Dịch & Runtime (Foundation Probe)
Sử dụng công cụ `scripts/foundation_probe.ps1` để tự động hóa trích xuất bằng chứng kỹ thuật với tiêu đề siêu dữ liệu (metadata header) chuẩn mực:

- **Kiểm tra thông tin toolchain:**
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts\foundation_probe.ps1 -Mode BuildInfo
  ```
- **Xuất compiler assembly listing (`-S`):**
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts\foundation_probe.ps1 -Mode SourceToAsm -SourceFile labs\part2-values\main.go
  ```
- **Xuất machine binary disassembly (`go tool objdump`):**
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts\foundation_probe.ps1 -Mode Objdump -SourceFile labs\part2-values\main.go -Symbol main.main
  ```
- **Chạy phân tích rò rỉ bộ nhớ (Escape Analysis `-m -m`):**
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts\foundation_probe.ps1 -Mode Escape -SourceFile labs\part2-values\main.go -Verbosity 2
  ```
- **Xuất phân tích tối ưu hóa SSA và Bounds Check Elimination:**
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts\foundation_probe.ps1 -Mode Optimizations -SourceFile labs\part2-values\main.go
  ```
*Toàn bộ kết quả xuất ra được lưu tự động tại `.workspace/foundation-evidence/` mà không gây xáo trộn thư mục git.*

### 3.4. Quét Toàn Diện Workspace (Workspace Audit)
Cập nhật báo cáo dung lượng đĩa và phân loại tệp tin:
```powershell
python scripts/audit_workspace.py
```
*Đầu ra:* Cập nhật tệp `WORKSPACE_AUDIT.md`.
