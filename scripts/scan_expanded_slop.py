import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

expanded_slop_patterns = [
    (r"\b[Đđ]iều quan trọng cần [^\.\n]+", "Điều quan trọng cần..."),
    (r"\b[Cc]ần (?:nhấn mạnh|lưu ý|ghi nhớ|thừa nhận) rằng[^\.\n]+", "Cần nhấn mạnh/lưu ý rằng..."),
    (r"\b[Đđ]áng chú ý (?:là|rằng)[^\.\n]+", "Đáng chú ý là..."),
    (r"\b[Cc]ó thể thấy (?:rằng)?[^\.\n]+", "Có thể thấy rằng..."),
    (r"\b[Cc]ó thể khẳng định[^\.\n]+", "Có thể khẳng định..."),
    (r"\b[Kk]hông thể phủ nhận[^\.\n]+", "Không thể phủ nhận..."),
    (r"\b[Rr]õ ràng (?:là|rằng)[^\.\n]+", "Rõ ràng là..."),
    (r"\b[Hh]ãy (?:cùng |tưởng tượng|hình dung)[^\.\n]+", "Hãy cùng/tưởng tượng/hình dung..."),
    (r"\b[Cc]húng ta hãy [^\.\n]+", "Chúng ta hãy..."),
    (r"\b[Tt]rong bối cảnh [^\.\n]+", "Trong bối cảnh..."),
    (r"\b[Tt]rong thế giới [^\.\n]+", "Trong thế giới..."),
    (r"\b[Tt]rong kỷ nguyên [^\.\n]+", "Trong kỷ nguyên..."),
    (r"\b[Đđ]ây chính là lúc[^\.\n]+", "Đây chính là lúc..."),
    (r"\b[Đđ]ó chính là lý do[^\.\n]+", "Đó chính là lý do..."),
    (r"\bđóng vai trò (?:vô cùng |hết sức |cực kỳ |then chốt|cốt lõi|quan trọng)?[^\.\n]+", "đóng vai trò..."),
    (r"\b(?:vô cùng|cực kỳ|hết sức|hoàn hảo|vượt trội)\b", "Từ hoa mỹ: vô cùng/cực kỳ/hoàn hảo/vượt trội"),
    (r"\b(?:chìa khóa vàng|vũ khí bí mật|trợ thủ đắc lực|bước ngoặt)\b", "Ẩn dụ sáo rỗng: chìa khóa vàng/vũ khí/trợ thủ"),
    (r"\b(?:mang lại|đem lại) sự linh hoạt[^\.\n]+", "mang lại sự linh hoạt..."),
    (r"\bnhắc nhở chúng ta[^\.\n]+", "nhắc nhở chúng ta..."),
    (r"^\s*(?:Bên cạnh đó|Đồng thời|Mặt khác|Hơn nữa),", "Liên từ dập khuôn đầu đoạn"),
]

files = sorted(list(Path("book/chapters").glob("*.md")) + list(Path("book/appendices").glob("*.md")))

findings = []
for f in files:
    text = f.read_text(encoding="utf-8")
    in_code = False
    for idx, line in enumerate(text.splitlines(), start=1):
        sline = line.strip()
        if sline.startswith("```") or sline.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code or sline.startswith("|") or sline.startswith("#"):
            continue
        for pat, desc in expanded_slop_patterns:
            m = re.search(pat, line)
            if m:
                findings.append((f.name, idx, desc, m.group(0), line.strip()))

print(f"TOTAL AI SLOP / STOCK PHRASES FOUND: {len(findings)}\n")
for f_name, idx, desc, match, line in findings:
    print(f"{f_name}:{idx} [{desc}]")
    print(f"  Match: {match[:70]}")
    print(f"  Line : {line[:100]}\n")
