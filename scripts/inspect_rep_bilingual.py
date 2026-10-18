import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")
from audit_prose_quality import audit_file

for f in sorted(Path("book/chapters").glob("*.md")):
    res = audit_file(f)
    if res["repeated_bilingual"]:
        print(f"=== {f.name} ===")
        for item in res["repeated_bilingual"]:
            print(f"  Line {item['line']}: {item['full_match']}")
            print(f"    Snippet: {item['snippet']}")
