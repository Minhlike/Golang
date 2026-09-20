# Golang Living Textbook

Nguồn của cuốn sách nằm trong `book/`; `Golang_Master.pdf` là bản đọc được
render từ nguồn đó. Edition đầu tiên được kiểm chứng với Go 1.27.1 vào
20-09-2026.

## Cấu trúc

- `book/chapters/`: Markdown là source of truth.
- `labs/`: bài thực hành có thể chạy độc lập.
- `projects/opsprobe/`: dự án DevOps/SRE xuyên suốt, lớn dần theo sách.
- `assets/diagrams/`: nguồn PlantUML, không lưu ảnh raster làm nguồn gốc.
- `references/`: danh mục nguồn và giới hạn giấy phép.
- `scripts/build_pdf.py`: renderer Markdown-to-PDF cục bộ, không phụ thuộc
  dịch vụ trả phí.

## Build cục bộ

Toolchain Go và PlantUML được đặt cục bộ trong `.tools/`, không sửa `PATH` hay
Registry Windows. Render PDF bằng Python bundled runtime:

```powershell
C:\Users\Acer\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build_pdf.py
```

Renderer luôn tạo candidate trong `tmp/pdfs/`, kiểm tra mở lại được, rồi mới
thay `Golang_Master.pdf`. Ở build đầu tiên, `Golang_Master.prev.pdf` là bản
đã kiểm tra cùng nội dung; ở các build sau nó là bản hợp lệ liền trước.

