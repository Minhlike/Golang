# scripts/refine_prose_vietnamese.py
import re
from pathlib import Path

# Contextual mapping for Vietnamese prose refinement (only applied outside code/links)
PROSE_REPLACEMENTS = [
    # General engineering terms
    (r"\bdeclaration\b", "khai báo"),
    (r"\bdeclarations\b", "các khai báo"),
    (r"\bstatement\b", "câu lệnh"),
    (r"\bstatements\b", "các câu lệnh"),
    (r"\bexpression\b", "biểu thức"),
    (r"\bexpressions\b", "các biểu thức"),
    (r"\bcaller\b", "bên gọi"),
    (r"\bcallers\b", "các bên gọi"),
    (r"\bendpoint\b", "điểm cuối"),
    (r"\bendpoints\b", "các điểm cuối"),
    (r"\bdependency\b", "phụ thuộc"),
    (r"\bdependencies\b", "các gói phụ thuộc"),
    (r"\bconfig\b", "cấu hình"),
    (r"\bconfigs\b", "các cấu hình"),
    (r"\bfile config\b", "tệp cấu hình"),
    (r"\bcode\b", "mã nguồn"),
    (r"\bfile\b", "tệp"),
    (r"\bfiles\b", "các tệp"),
    (r"\bsource file\b", "tệp nguồn"),
    (r"\bsource files\b", "các tệp nguồn"),
    (r"\bchannel\b", "kênh truyền"),
    (r"\bchannels\b", "các kênh truyền"),
    (r"\bbuffer\b", "vùng đệm"),
    (r"\bbuffers\b", "các vùng đệm"),
    (r"\brequest\b", "yêu cầu"),
    (r"\brequests\b", "các yêu cầu"),
    (r"\bresponse\b", "phản hồi"),
    (r"\bresponses\b", "các phản hồi"),
    (r"\bport\b", "cổng"),
    (r"\bports\b", "các cổng"),
    (r"\bdeploy\b", "triển khai"),
    (r"\bdeployed\b", "được triển khai"),
    (r"\bdeployment\b", "triển khai"),
    (r"\btool\b", "công cụ"),
    (r"\btools\b", "các công cụ"),
    (r"\btooling\b", "bộ công cụ"),
    (r"\bprocess con\b", "tiến trình con"),
    (r"\bprocess\b", "tiến trình"),
    (r"\bprocesses\b", "các tiến trình"),
    (r"\bartifact\b", "hiện vật gói phát hành"),
    (r"\bartifacts\b", "các hiện vật gói phát hành"),
    (r"\bproduction\b", "môi trường vận hành"),
    (r"\bfunction\b", "hàm"),
    (r"\bfunctions\b", "các hàm"),
    (r"\bvariable\b", "biến"),
    (r"\bvariables\b", "các biến"),
    (r"\bvalue\b", "giá trị"),
    (r"\bvalues\b", "các giá trị"),
    (r"\bblock\b", "khối lệnh"),
    (r"\bblocks\b", "các khối lệnh"),
    (r"\bmain block\b", "khối lệnh main"),
    (r"\bif block\b", "khối lệnh if"),
    (r"\bfor block\b", "khối lệnh for"),
    (r"\bswitch block\b", "khối lệnh switch"),
    (r"\bparameter\b", "tham số"),
    (r"\bparameters\b", "các tham số"),
    (r"\bargument\b", "đối số"),
    (r"\barguments\b", "các đối số"),
    (r"\bpointer\b", "con trỏ"),
    (r"\bpointers\b", "các con trỏ"),
    (r"\baddressable\b", "có thể lấy địa chỉ"),
    (r"\bundefined\b", "chưa được định nghĩa"),
    (r"\bkeyword\b", "từ khóa"),
    (r"\bkeywords\b", "các từ khóa"),
    (r"\bidentifier\b", "tên định danh"),
    (r"\bidentifiers\b", "các tên định danh"),
    (r"\bsignature\b", "chữ ký hàm"),
    (r"\bsignatures\b", "các chữ ký hàm"),
    (r"\breceiver\b", "bộ tiếp nhận"),
    (r"\breceivers\b", "các bộ tiếp nhận"),
    (r"\bpointer receiver\b", "bộ tiếp nhận con trỏ"),
    (r"\bvalue receiver\b", "bộ tiếp nhận giá trị"),
    (r"\bunderlying array\b", "mảng nền"),
    (r"\bbacking array\b", "mảng nền"),
    (r"\bbacking storage\b", "vùng lưu trữ nền"),
    (r"\bdescriptor\b", "bộ mô tả (descriptor)"),
    (r"\breslice\b", "cắt lại lát cắt"),
    (r"\bmutation\b", "biến đổi dữ liệu"),
    (r"\baliasing\b", "chồng lấn ô nhớ (aliasing)"),
    (r"\bincident\b", "sự cố vận hành"),
    (r"\bincidents\b", "các sự cố vận hành"),
    (r"\blifecycle\b", "vòng đời"),
    (r"\bworkload\b", "tải công việc"),
    (r"\bmicroservice\b", "dịch vụ vi mô"),
    (r"\bmicroservices\b", "các dịch vụ vi mô"),
    (r"\boperation\b", "thao tác"),
    (r"\boperations\b", "các thao tác"),
    (r"\bdeadline\b", "thời hạn xử lý (deadline)"),
    (r"\btimeout\b", "hết thời hạn (timeout)"),
    (r"\bcancellation\b", "hủy thực thi"),
    (r"\bgraceful shutdown\b", "tắt an toàn (graceful shutdown)"),
    (r"\bworkqueue\b", "hàng đợi công việc (workqueue)"),
    (r"\brate-limiting\b", "giới hạn tốc độ"),
    (r"\bbackoff\b", "lùi bước (backoff)"),
    (r"\bexponential backoff\b", "lùi bước số mũ (exponential backoff)"),
    (r"\bcontroller\b", "bộ điều khiển (controller)"),
    (r"\bcontrollers\b", "các bộ điều khiển (controllers)"),
    (r"\breconciliation\b", "điều hòa trạng thái (reconciliation)"),
    (r"\bdesired state\b", "trạng thái mong muốn"),
    (r"\bactual state\b", "trạng thái thực tế"),
    (r"\bobservability\b", "năng lực quan sát (observability)"),
    (r"\btelemetry\b", "dữ liệu đo từ xa"),
]

def refine_prose(text: str) -> str:
    # Tokenize text into chunks: code fences, inline codes, markdown links/images, prose
    tokens = []
    pos = 0
    pattern = re.compile(r"(```[\s\S]*?```|`[^`\n]+`|!\[.*?\]\(.*?\)|\$begin:math:display\$.*?\$end:math:display\$)", re.DOTALL)
    
    for m in pattern.finditer(text):
        start, end = m.span()
        if start > pos:
            tokens.append((False, text[pos:start]))
        tokens.append((True, m.group(0)))
        pos = end
    if pos < len(text):
        tokens.append((False, text[pos:]))

    # Only replace in non-code chunks
    out_chunks = []
    for is_code, chunk in tokens:
        if is_code:
            out_chunks.append(chunk)
        else:
            refined = chunk
            for pat, repl in PROSE_REPLACEMENTS:
                refined = re.sub(pat, repl, refined, flags=re.IGNORECASE)
            out_chunks.append(refined)
            
    return "".join(out_chunks)

def process_chapters():
    chapters = sorted(Path("book/chapters").glob("*.md"))
    modified_count = 0
    for ch in chapters:
        original = ch.read_text(encoding="utf-8")
        refined = refine_prose(original)
        if refined != original:
            ch.write_text(refined, encoding="utf-8")
            modified_count += 1
            print(f"Refined prose: {ch.name}")
    print(f"Total chapters refined: {modified_count}/{len(chapters)}")

if __name__ == "__main__":
    process_chapters()
