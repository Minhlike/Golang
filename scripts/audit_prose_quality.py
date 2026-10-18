#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/audit_prose_quality.py

Audits the entire manuscript (31 chapters + 2 appendices) for:
1. AI Slop: Stock phrases, empty fluency, hyperbolic adjectives, template openers.
2. Excessive Bold: Paragraphs with >= 3 bold tokens or bold label prefixes (**Label:**).
3. Dash Abuse: Em-dash (—), double hyphens (--), and list bullets in main prose.
4. English Overuse: Repeated bilingual parenthetical annotations and high non-Vietnamese word ratio in prose paragraphs.
"""

import sys
import re
from pathlib import Path
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding="utf-8")

# Patterns for AI Slop / Empty Fluency / Hyperbolic adjectives
AI_SLOP_PATTERNS = [
    # Stock openers & fillers
    (r"\b[Đđ]iều quan trọng cần (?:lưu ý|ghi nhớ|nhấn mạnh)\b", "STOCK_OPENER: Điều quan trọng cần lưu ý/ghi nhớ/nhấn mạnh"),
    (r"\b[Cc]ần (?:nhấn mạnh|lưu ý|ghi nhớ|thừa nhận) rằng\b", "STOCK_OPENER: Cần nhấn mạnh/lưu ý rằng"),
    (r"\b[Đđ]áng chú ý (?:là|rằng)\b", "STOCK_OPENER: Đáng chú ý là"),
    (r"\b[Cc]ó thể thấy (?:rằng)?\b", "STOCK_OPENER: Có thể thấy rằng"),
    (r"\b[Cc]ó thể khẳng định (?:rằng)?\b", "STOCK_OPENER: Có thể khẳng định rằng"),
    (r"\b[Kk]hông thể phủ nhận (?:rằng)?\b", "STOCK_OPENER: Không thể phủ nhận rằng"),
    (r"\b[Rr]õ ràng (?:là|rằng)\b", "STOCK_OPENER: Rõ ràng là"),
    
    # Conversational / AI cheerleader fluff
    (r"\b[Hh]ãy cùng (?:khám phá|tìm hiểu|đi sâu|bắt đầu|xem xét)\b", "AI_FLUFF: Hãy cùng khám phá/tìm hiểu"),
    (r"\b[Hh]ãy tưởng tượng\b", "AI_FLUFF: Hãy tưởng tượng"),
    (r"\b[Cc]húng ta hãy cùng\b", "AI_FLUFF: Chúng ta hãy cùng"),
    
    # Context cliché
    (r"\b[Tt]rong bối cảnh (?:hiện đại|công nghệ|số hóa|phát triển)?\b", "AI_CLICHE: Trong bối cảnh..."),
    (r"\b[Tt]rong thế giới (?:hiện đại|công nghệ|phần mềm|microservices|cloud)\b", "AI_CLICHE: Trong thế giới hiện đại/công nghệ"),
    (r"\b[Tt]rong kỷ nguyên (?:số|AI|thông tin|đám mây)\b", "AI_CLICHE: Trong kỷ nguyên..."),
    
    # Correlative template
    (r"\b[Kk]hông chỉ\b[^\.\n]+?\bmà còn\b", "AI_TEMPLATE: Không chỉ... mà còn..."),
    
    # Hyperbolic buzzwords & empty fluency
    (r"\bđóng vai trò (?:vô cùng |hết sức |cực kỳ )?(?:quan trọng|then chốt|cốt lõi)\b", "EMPTY_FLUENCY: đóng vai trò quan trọng/then chốt"),
    (r"\bvô cùng (?:mạnh mẽ|linh hoạt|quan trọng|hiệu quả|phức tạp)\b", "INFLATED_ADJECTIVE: vô cùng..."),
    (r"\bcực kỳ (?:mạnh mẽ|linh hoạt|quan trọng|hiệu quả|nhanh chóng)\b", "INFLATED_ADJECTIVE: cực kỳ..."),
    (r"\bsức mạnh (?:vượt trội|to lớn|kinh ngạc)\b", "INFLATED_ADJECTIVE: sức mạnh vượt trội"),
    (r"\btối ưu (?:hóa )?vượt trội\b", "INFLATED_ADJECTIVE: tối ưu vượt trội"),
    (r"\bgiải pháp (?:hoàn hảo|toàn diện|tối ưu nhất)\b", "INFLATED_ADJECTIVE: giải pháp hoàn hảo/toàn diện"),
    (r"\bchìa khóa vàng\b", "METAPHOR_SLOP: chìa khóa vàng"),
    (r"\bvũ khí bí mật\b", "METAPHOR_SLOP: vũ khí bí mật"),
    (r"\btrợ thủ đắc lực\b", "METAPHOR_SLOP: trợ thủ đắc lực"),
    (r"\bbước ngoặt\b", "INFLATED_ADJECTIVE: bước ngoặt"),
]

# Strict whitelist of technical terms, code keywords, technologies, protocols
WHITELIST = {
    "go", "golang", "package", "import", "func", "var", "const", "type", "struct",
    "interface", "chan", "select", "defer", "for", "range", "if", "else", "switch",
    "case", "default", "return", "make", "new", "len", "cap", "append", "copy",
    "panic", "recover", "nil", "true", "false", "iota", "main", "string", "int",
    "int64", "uint", "uint64", "float64", "bool", "byte", "rune", "error",
    "context", "sync", "io", "fmt", "net", "os", "testing", "time", "json",
    "sql", "pprof", "trace", "exec", "bufio", "bytes", "strings", "errors",
    "mutex", "rwmutex", "waitgroup", "atomic", "println", "print", "printf",
    "linux", "kubernetes", "k8s", "docker", "prometheus", "opentelemetry", "otel",
    "http", "https", "tcp", "udp", "tls", "dns", "grpc", "posix", "rest", "git",
    "aws", "s3", "iam", "cli", "ci", "cd", "api", "cpu", "ram", "eof", "sqlite",
    "opsprobe", "reconcile", "workqueue", "traceparent", "ebpf", "mcp", "aiops",
    "pod", "crd", "yaml", "json", "sdk", "grpc", "uri", "url", "id", "ip"
}

VIETNAMESE_DIACRITICS = re.compile(
    r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]",
    re.IGNORECASE
)

# Common non-diacritic Vietnamese words (thanh ngang)
VN_NON_DIACRITIC = {
    "ai", "an", "anh", "ba", "bac", "ban", "bang", "bao", "bat", "bay", "be",
    "ben", "bi", "bien", "biet", "binh", "bo", "bon", "bong", "buoc", "ca",
    "cac", "cach", "cai", "cam", "can", "canh", "cao", "cau", "cay", "che",
    "chen", "chi", "chia", "chiem", "chien", "chieu", "chin", "chinh", "cho",
    "choi", "chon", "chu", "chua", "chuc", "chun", "chung", "chuong", "chuyen",
    "co", "coc", "con", "cong", "coi", "cu", "cuc", "cung", "cuoi", "cuon",
    "da", "dac", "dai", "dan", "dang", "danh", "dao", "dau", "day", "de",
    "dem", "den", "dep", "di", "diem", "dien", "dieu", "dinh", "do", "doc",
    "doi", "don", "dong", "du", "duc", "dung", "duoc", "duoi", "duong", "duy",
    "em", "gai", "gan", "gap", "gay", "ghe", "ghi", "gia", "giai", "giao",
    "giay", "giu", "giua", "goi", "goc", "gom", "ha", "hai", "ham", "han",
    "hang", "hao", "hat", "hay", "he", "hen", "hien", "hieu", "hinh", "hoa",
    "hoan", "hoc", "hoi", "hom", "hon", "hop", "huong", "huy", "in", "it",
    "ke", "kem", "ket", "keu", "kha", "khach", "khai", "khang", "khanh", "khao",
    "khi", "khien", "kho", "khoa", "khoang", "khoi", "khong", "khu", "khung",
    "khuyen", "la", "lac", "lai", "lam", "lan", "lang", "lanh", "lao", "lat",
    "lay", "le", "len", "lenh", "leo", "li", "lich", "lien", "lieu", "linh",
    "lo", "loai", "loan", "loc", "loi", "lon", "long", "lop", "luat", "luc",
    "lui", "luon", "luong", "luu", "ma", "mac", "mai", "man", "mang", "manh",
    "mao", "mat", "mau", "may", "me", "men", "mi", "mien", "minh", "mo",
    "moc", "moi", "mon", "mong", "mot", "mua", "muc", "muon", "muoi", "nao",
    "nam", "nang", "nay", "nem", "nen", "neo", "net", "neu", "nga", "ngach",
    "ngay", "nghe", "nghen", "nghi", "nghia", "nghiep", "ngo", "ngoa", "ngoai",
    "ngon", "ngu", "nguon", "nguoi", "nguyen", "nhan", "nhanh", "nhau", "nhe",
    "nhi", "nhieu", "nhin", "nho", "nhom", "nhu", "nhung", "noi", "non", "nong",
    "nuoc", "o", "om", "on", "ong", "pa", "pha", "phai", "pham", "phan",
    "phap", "phat", "phay", "phi", "phia", "phien", "phim", "pho", "phoi",
    "phong", "phu", "phuc", "phung", "phuong", "qua", "quan", "quang", "quanh",
    "quay", "que", "quen", "quoc", "quy", "quyet", "ra", "rac", "rai", "ran",
    "rang", "ranh", "rao", "rat", "rau", "re", "rieng", "ro", "roi", "ron",
    "rong", "ru", "rua", "ruot", "rut", "sa", "sac", "sai", "sam", "san",
    "sang", "sanh", "sao", "sat", "sau", "say", "se", "si", "sinh", "so",
    "soi", "som", "son", "song", "su", "suc", "sung", "suot", "sua", "suy",
    "ta", "tac", "tai", "tam", "tan", "tang", "tao", "tap", "tat", "tay",
    "te", "ten", "tha", "thai", "tham", "than", "thang", "thanh", "thao",
    "that", "thay", "the", "them", "theo", "thi", "thich", "thiet", "thieu",
    "thinh", "tho", "thoi", "thon", "thong", "thu", "thua", "thuc", "thue",
    "thuan", "thuyen", "ti", "tich", "tien", "tiep", "tiet", "tieu", "tin",
    "tinh", "to", "toa", "toan", "toc", "toi", "ton", "tong", "tra", "trai",
    "tram", "tran", "trang", "tranh", "trao", "tre", "tren", "tri", "trich",
    "trien", "trieu", "trinh", "tro", "troi", "tron", "trong", "tru", "truc",
    "trum", "trung", "truoc", "truong", "truyen", "tu", "tuc", "tuan", "tung",
    "tuoi", "tuong", "tuy", "tuyen", "va", "vac", "vai", "van", "vang", "vao",
    "vat", "ve", "ven", "vi", "viac", "viec", "vien", "viet", "vinh", "vo",
    "voi", "von", "vong", "vu", "vua", "vuc", "vung", "vuon", "vuot", "xa",
    "xac", "xem", "xen", "xep", "xet", "xi", "xin", "xinh", "xoa", "xong",
    "xu", "xuan", "xuat", "xuyen", "y", "yeu",
    "cha", "gian", "truy", "xanh", "ngang", "ghim", "nguy", "xung", "ninh",
    "khoang", "nghieng", "nghiem", "nghien", "khuan", "duyen", "mu"
}

def clean_paragraph_for_nlp(p: str) -> str:
    """Removes code spans, images, markdown links, html tags for prose word analysis."""
    p = re.sub(r"`[^`]*`", "", p)
    p = re.sub(r"!\[.*?\]\(.*?\)", "", p)
    p = re.sub(r"\[.*?\]\(.*?\)", "", p)
    p = re.sub(r"<[^>]+>", "", p)
    return p

def audit_file(file_path: Path):
    lines = file_path.read_text(encoding="utf-8").splitlines()
    
    in_code_block = False
    in_table = False
    
    results = {
        "file": file_path.name,
        "ai_slop": [],
        "bold_overuse": [],
        "bold_prefix": [],
        "em_dash": [],
        "double_hyphen": [],
        "list_bullets": [],
        "repeated_bilingual": [],
        "high_english_paragraphs": [],
        "total_paragraphs": 0,
        "total_em_dashes": 0,
        "total_double_hyphens": 0,
    }
    
    bilingual_seen = Counter()
    
    # Track paragraphs
    curr_para = []
    curr_para_start_line = 0
    
    def process_paragraph(para_lines, start_ln):
        if not para_lines:
            return
        para_text = " ".join([l.strip() for l in para_lines])
        if not para_text or para_text.startswith("#"):
            return
            
        results["total_paragraphs"] += 1
        
        # 1. AI Slop scan
        for pattern, label in AI_SLOP_PATTERNS:
            for match in re.finditer(pattern, para_text):
                results["ai_slop"].append({
                    "line": start_ln,
                    "label": label,
                    "match": match.group(0),
                    "snippet": para_text[:120] + ("..." if len(para_text) > 120 else "")
                })
                
        # 2. Bold Overuse
        # Find all **...** spans
        bold_matches = re.findall(r"\*\*([^*]+)\*\*", para_text)
        if len(bold_matches) >= 3:
            results["bold_overuse"].append({
                "line": start_ln,
                "count": len(bold_matches),
                "samples": bold_matches[:5],
                "snippet": para_text[:140] + ("..." if len(para_text) > 140 else "")
            })
            
        # Bold Prefix (e.g. **Khái niệm:**, **Bước 1:**, **Lưu ý:**)
        if re.match(r"^\s*\*\*[A-ZÀ-Ỹa-zà-ỹ0-9\s:.-]+\*\*:\s*", para_text):
            m = re.match(r"^\s*(\*\*[A-ZÀ-Ỹa-zà-ỹ0-9\s:.-]+\*\*:)", para_text)
            results["bold_prefix"].append({
                "line": start_ln,
                "prefix": m.group(1),
                "snippet": para_text[:120] + ("..." if len(para_text) > 120 else "")
            })
            
        # 3. Dash abuse
        em_dashes = para_text.count("—")  # \u2014
        double_hyphens = para_text.count("--")
        results["total_em_dashes"] += em_dashes
        results["total_double_hyphens"] += double_hyphens
        
        if em_dashes >= 2:
            results["em_dash"].append({
                "line": start_ln,
                "count": em_dashes,
                "snippet": para_text[:140] + ("..." if len(para_text) > 140 else "")
            })
        if double_hyphens >= 2:
            results["double_hyphen"].append({
                "line": start_ln,
                "count": double_hyphens,
                "snippet": para_text[:140] + ("..." if len(para_text) > 140 else "")
            })
            
        # 4. English Overuse & Bilingual annotations
        # Find parenthetical bilingual annotations: e.g. "áp suất ngược (backpressure)"
        # Pattern: Vietnamese word(s) followed by (English words)
        paren_matches = re.finditer(r"([A-Za-zÀ-ỹ\s]{3,30})\s*\(([A-Za-z\s]{3,30})\)", para_text)
        for pm in paren_matches:
            vn_part = pm.group(1).strip()
            en_part = pm.group(2).strip().lower()
            if en_part not in WHITELIST and len(en_part.split()) <= 4:
                bilingual_seen[en_part] += 1
                if bilingual_seen[en_part] == 2:  # 2nd time onwards in same chapter!
                    results["repeated_bilingual"].append({
                        "line": start_ln,
                        "en_term": en_part,
                        "full_match": pm.group(0),
                        "snippet": para_text[:120] + ("..." if len(para_text) > 120 else "")
                    })
                    
        # Word analysis for prose
        clean_p = clean_paragraph_for_nlp(para_text)
        words = re.findall(r"\b[A-Za-zÀ-ỹĐđ0-9_-]+\b", clean_p)
        vn_cnt = 0
        en_words = []
        for w in words:
            if w.isdigit() or len(w) <= 1:
                continue
            wl = w.lower()
            if VIETNAMESE_DIACRITICS.search(w) or wl in VN_NON_DIACRITIC:
                vn_cnt += 1
            elif wl in WHITELIST:
                continue
            else:
                en_words.append(w)
                
        total_valid = vn_cnt + len(en_words)
        if total_valid >= 15:
            en_ratio = (len(en_words) / total_valid) * 100
            # Flag if > 15% English or >= 6 distinct English words in a single prose paragraph
            if (en_ratio >= 15.0 and len(en_words) >= 4) or len(en_words) >= 6:
                results["high_english_paragraphs"].append({
                    "line": start_ln,
                    "en_ratio": round(en_ratio, 1),
                    "en_count": len(en_words),
                    "en_samples": en_words[:6],
                    "snippet": clean_p[:140] + ("..." if len(clean_p) > 140 else "")
                })

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        
        # Check code fence
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if not in_code_block:
                process_paragraph(curr_para, curr_para_start_line)
                curr_para = []
                in_code_block = True
            else:
                in_code_block = False
            continue
            
        if in_code_block:
            continue
            
        # Check table
        if stripped.startswith("|"):
            process_paragraph(curr_para, curr_para_start_line)
            curr_para = []
            continue
            
        # Check list bullet in main prose (e.g. - item or * item)
        if re.match(r"^(\s*[-*]\s+)(?!\[[ x]\])", line):
            # Flag list bullets
            results["list_bullets"].append({
                "line": idx,
                "bullet": line[:60]
            })
            # Continue without adding to normal prose paragraph
            process_paragraph(curr_para, curr_para_start_line)
            curr_para = []
            continue

        # Check empty line
        if not stripped:
            process_paragraph(curr_para, curr_para_start_line)
            curr_para = []
            curr_para_start_line = 0
            continue
            
        # Accumulate paragraph
        if not curr_para:
            curr_para_start_line = idx
        curr_para.append(line)
        
    process_paragraph(curr_para, curr_para_start_line)
    return results

def main():
    target_files = sorted(Path("book/chapters").glob("*.md")) + sorted(Path("book/appendices").glob("*.md"))
    
    print("=" * 100)
    print("TOÀN DIỆN KIỂM TOÁN CHẤT LƯỢNG VĂN PHONG (PROSE QUALITY AUDIT)")
    print("4 Tiêu chí: 1. AI Slop | 2. Lạm dụng Bold (**) | 3. Dấu gạch ngang (—, --) | 4. Lạm dụng Tiếng Anh")
    print("=" * 100)
    
    total_slop = 0
    total_bold_overuse = 0
    total_bold_prefix = 0
    total_em_dashes = 0
    total_double_hyphens = 0
    total_repeated_bilingual = 0
    total_high_en_paras = 0
    total_bullets = 0
    
    summary_table = []
    
    for f in target_files:
        r = audit_file(f)
        
        slop_cnt = len(r["ai_slop"])
        bold_overuse_cnt = len(r["bold_overuse"])
        bold_prefix_cnt = len(r["bold_prefix"])
        em_cnt = r["total_em_dashes"]
        dh_cnt = r["total_double_hyphens"]
        bi_cnt = len(r["repeated_bilingual"])
        en_para_cnt = len(r["high_english_paragraphs"])
        bullet_cnt = len(r["list_bullets"])
        
        total_slop += slop_cnt
        total_bold_overuse += bold_overuse_cnt
        total_bold_prefix += bold_prefix_cnt
        total_em_dashes += em_cnt
        total_double_hyphens += dh_cnt
        total_repeated_bilingual += bi_cnt
        total_high_en_paras += en_para_cnt
        total_bullets += bullet_cnt
        
        summary_table.append((
            f.name,
            slop_cnt,
            bold_overuse_cnt,
            bold_prefix_cnt,
            em_cnt,
            dh_cnt,
            bi_cnt,
            en_para_cnt,
            bullet_cnt
        ))

    # Print summary
    print(f"{'Tên file':<44} | {'Slop':<5} | {'Bold>=3':<7} | {'BoldPref':<8} | {'EmDash':<6} | {'--':<4} | {'RepBiling':<9} | {'HighEN':<6} | {'Bullets':<7}")
    print("-" * 108)
    for row in summary_table:
        print(f"{row[0]:<44} | {row[1]:<5} | {row[2]:<7} | {row[3]:<8} | {row[4]:<6} | {row[5]:<4} | {row[6]:<9} | {row[7]:<6} | {row[8]:<7}")
    print("=" * 108)
    print(f"{'TỔNG CỘNG TOÀN BỘ SÁCH':<44} | {total_slop:<5} | {total_bold_overuse:<7} | {total_bold_prefix:<8} | {total_em_dashes:<6} | {total_double_hyphens:<4} | {total_repeated_bilingual:<9} | {total_high_en_paras:<6} | {total_bullets:<7}")
    print("=" * 108)

if __name__ == "__main__":
    main()
