import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")
from audit_prose_quality import audit_file

target_names = sys.argv[1:] if len(sys.argv) > 1 else ["21-vong-lap-dieu-hoa-controller.md"]
for name in target_names:
    p = Path(name)
    f = p if p.exists() else Path("book/chapters") / name
    res = audit_file(f)
    print(f"=== {name} ({len(res['high_english_paragraphs'])} flagged) ===")
    for item in res["high_english_paragraphs"]:
        print(f"Line {item['line']} (ratio {item['en_ratio']}%, count {item['en_count']}): {item['en_samples']}")
        print(f"  Snippet: {item['snippet']}\n")
