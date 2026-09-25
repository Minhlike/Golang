#!/usr/bin/env python3
"""
validate_main_manuscript_no_bullets.py

Validates the Zero-Bullet Rule for the main manuscript (book/chapters/*.md).
Rules:
- Unordered Markdown list items (-, *, +) in narrative prose: FAIL.
- Ordered Markdown list items (1., 2., ...) in narrative prose: FAIL.
Exceptions allowed:
- Fenced code blocks (``` ... ```)
- PlantUML source (@startuml ... @enduml)
- Markdown tables (| ... |)
- Metadata comments (<!-- ... -->)
- Back matter / Error Atlas / Reference sections (e.g. lines after @references)
"""

import sys
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CHAPTERS_DIR = Path("book/chapters")

def validate_chapter(file_path: Path) -> list[tuple[int, str, str]]:
    violations = []
    lines = file_path.read_text(encoding="utf-8").splitlines()
    
    in_code_fence = False
    in_plantuml = False
    in_references = False
    
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        
        # Check code fence
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
            
        # Check plantuml
        if stripped.startswith("@startuml"):
            in_plantuml = True
            continue
        if stripped.startswith("@enduml"):
            in_plantuml = False
            continue
        if in_plantuml:
            continue
            
        # Check references block
        if stripped == "@references":
            in_references = True
            continue
        if stripped.startswith("#"):
            in_references = False
            
        if in_references:
            continue
            
        # Ignore comments & tables & horizontal rules
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        if stripped == "---":
            continue
            
        # Check unordered bullets: -, *, + followed by space
        if re.match(r"^[-*+]\s+", stripped):
            violations.append((idx, "UNORDERED_BULLET", line))
            continue
            
        # Check ordered list: 1., 2., etc. followed by space
        if re.match(r"^\d+\.\s+", stripped):
            violations.append((idx, "ORDERED_LIST", line))
            continue

    return violations

def main():
    if not CHAPTERS_DIR.exists():
        print(f"Directory {CHAPTERS_DIR} not found.")
        sys.exit(1)
        
    all_violations = {}
    total_violations = 0
    
    for md_file in sorted(CHAPTERS_DIR.glob("*.md")):
        violations = validate_chapter(md_file)
        if violations:
            all_violations[md_file.name] = violations
            total_violations += len(violations)
            
    print("=" * 80)
    print("ZERO-BULLET VALIDATOR REPORT (book/chapters/*.md)")
    print("=" * 80)
    
    if total_violations == 0:
        print("[ZERO-BULLET-PASS] All chapter narrative prose is completely free of bullets.")
        sys.exit(0)
    else:
        print(f"[ZERO-BULLET-FAIL] Found {total_violations} bullet violations across {len(all_violations)} files:")
        for fn, v_list in all_violations.items():
            print(f"\n--- {fn} ({len(v_list)} violations) ---")
            for line_no, kind, text in v_list[:10]:
                print(f"  Line {line_no:4d} [{kind}]: {text}")
            if len(v_list) > 10:
                print(f"  ... and {len(v_list) - 10} more violations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
