import sys
import re
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, "scripts")
from audit_prose_language import WHITELIST, VIETNAMESE_DIACRITICS, VN_NON_DIACRITIC

all_en = Counter()
en_by_file = defaultdict = Counter()

files = sorted(Path("book/chapters").glob("*.md"))

for f in files:
    text = f.read_text(encoding="utf-8")
    # remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # remove inline code
    text = re.sub(r"`[^`]*`", "", text)
    # remove links and images
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    
    words = re.findall(r"\b[A-Za-zÀ-ỹĐđ0-9_-]+\b", text)
    for w in words:
        if w.isdigit() or len(w) <= 1:
            continue
        wl = w.lower()
        if VIETNAMESE_DIACRITICS.search(w) or wl in VN_NON_DIACRITIC or wl in WHITELIST:
            continue
        all_en[wl] += 1

print("Top 150 unquoted English/foreign words in prose across chapters:")
for w, c in all_en.most_common(150):
    print(f"{w:20}: {c:4}")
