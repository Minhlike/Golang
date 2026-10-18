import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")
from audit_prose_quality import audit_file

files = sorted(Path("book/chapters").glob("*.md"))
for f in files:
    res = audit_file(f)
    if res["high_english_paragraphs"]:
        print(f"=== {f.name} ({len(res['high_english_paragraphs'])} paragraphs flagged) ===")
        for item in res["high_english_paragraphs"][:3]:
            print(f"  Line {item['line']} (EN ratio: {item['en_ratio']}%, count: {item['en_count']}):")
            print(f"    Words: {item['en_samples']}")
            print(f"    Snippet: {item['snippet']}")
        print()
