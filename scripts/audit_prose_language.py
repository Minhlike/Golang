# scripts/audit_prose_language.py
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Strict whitelist of exact technical names, acronyms, protocols, and Go symbols
WHITELIST = {
    # Go keywords & primitives
    "go", "golang", "package", "import", "func", "var", "const", "type", "struct",
    "interface", "chan", "select", "defer", "for", "range", "if", "else", "switch",
    "case", "default", "return", "make", "new", "len", "cap", "append", "copy",
    "panic", "recover", "nil", "true", "false", "iota", "main", "string", "int",
    "int64", "uint", "uint64", "float64", "bool", "byte", "rune", "error",
    # Standard packages & APIs
    "context", "sync", "io", "fmt", "net", "os", "testing", "time", "json",
    "sql", "pprof", "trace", "exec", "bufio", "bytes", "strings", "errors",
    "mutex", "rwmutex", "waitgroup", "atomic", "println", "print", "printf",
    # Technologies & Protocols
    "linux", "kubernetes", "k8s", "docker", "prometheus", "opentelemetry", "otel",
    "http", "https", "tcp", "udp", "tls", "dns", "grpc", "posix", "rest", "git",
    "aws", "s3", "iam", "cli", "ci", "cd", "api", "cpu", "ram", "eof", "sqlite",
    # Architecture Identifiers
    "opsprobe", "reconcile", "workqueue", "traceparent"
}

VIETNAMESE_DIACRITICS = re.compile(
    r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]",
    re.IGNORECASE
)

# Comprehensive list of standard tone-level (thanh ngang) Vietnamese words
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
    "xu", "xuan", "xuat", "xuyen", "y", "yeu"
}

def audit_chapter(path: Path):
    text = path.read_text(encoding="utf-8")
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Remove inline code
    text = re.sub(r"`[^`]*`", "", text)
    # Remove images and markdown links
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    words = re.findall(r"\b[A-Za-zÀ-ỹĐđ0-9_-]+\b", text)
    vn_count = 0
    en_flagged = []

    for w in words:
        if w.isdigit() or len(w) <= 1:
            continue
        wl = w.lower()
        if VIETNAMESE_DIACRITICS.search(w) or wl in VN_NON_DIACRITIC:
            vn_count += 1
        elif wl in WHITELIST:
            continue
        else:
            en_flagged.append(w)

    total = vn_count + len(en_flagged)
    ratio = (vn_count / total * 100) if total > 0 else 100.0
    return vn_count, en_flagged, ratio

def main():
    chapters = sorted(Path("book/chapters").glob("*.md"))
    total_vn = 0
    total_en = 0

    print("=" * 80)
    print("AUDIT PROSE LANGUAGE RATIO (VIETNAMESE-FIRST)")
    print("=" * 80)

    for ch in chapters:
        vn, flagged, ratio = audit_chapter(ch)
        total_vn += vn
        total_en += len(flagged)
        sample = flagged[:5]
        print(f"{ch.name:45} | VN: {vn:5} | Flags: {len(flagged):3} | VN Ratio: {ratio:5.1f}% | {sample}")

    overall = (total_vn / (total_vn + total_en) * 100) if (total_vn + total_en) > 0 else 100.0
    print("=" * 80)
    print(f"TOTAL WORDS: {total_vn + total_en:,} | VN: {total_vn:,} | EN Flags: {total_en:,} | OVERALL: {overall:.2f}%")
    print("=" * 80)

if __name__ == "__main__":
    main()
