#!/usr/bin/env python3
"""
Audit List Density Tool for Golang Master Manuscript.
Audits chapters for Prose-First technical writing guidelines:
- Counts prose paragraphs vs bullet blocks vs numbered lists
- Flags longest list blocks
- Flags list items with unusually long prose (> 150 chars)
- Identifies candidate sections needing editorial review
Zero external dependencies.
"""

import os
import re
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = ROOT / "book" / "chapters"


def audit_chapter(file_path: Path) -> dict:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    
    total_paragraphs = 0
    bullet_blocks = 0
    numbered_blocks = 0
    longest_bullet_block = 0
    long_bullet_items = []
    sections_with_list_abuse = []
    
    in_code = False
    in_table = False
    in_bullet_list = False
    in_numbered_list = False
    current_list_len = 0
    current_section = "Intro"
    section_lists = {}
    
    for idx, line in enumerate(lines, 1):
        s_line = line.strip()
        
        # Fenced code
        if s_line.startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if in_code:
            continue
            
        # Tables
        if s_line.startswith("|"):
            in_table = True
            continue
        if in_table and not s_line.startswith("|"):
            in_table = False
            
        # Headings
        if s_line.startswith("#"):
            if in_bullet_list:
                bullet_blocks += 1
                if current_list_len > longest_bullet_block:
                    longest_bullet_block = current_list_len
                in_bullet_list = False
                current_list_len = 0
            if in_numbered_list:
                numbered_blocks += 1
                in_numbered_list = False
                current_list_len = 0
            current_section = s_line.lstrip("#").strip()
            continue
            
        # Ignore comments, dividers, directives
        if s_line.startswith(("<!--", "@", "---", "===")) or not s_line:
            if in_bullet_list:
                bullet_blocks += 1
                if current_list_len > longest_bullet_block:
                    longest_bullet_block = current_list_len
                in_bullet_list = False
                current_list_len = 0
            if in_numbered_list:
                numbered_blocks += 1
                in_numbered_list = False
                current_list_len = 0
            continue
            
        # Bullet list item
        if re.match(r"^[-*]\s+", s_line):
            if not in_bullet_list:
                in_bullet_list = True
                current_list_len = 1
                section_lists[current_section] = section_lists.get(current_section, 0) + 1
            else:
                current_list_len += 1
            item_text = re.sub(r"^[-*]\s+", "", s_line)
            if len(item_text) > 150 or item_text.count(".") >= 2:
                long_bullet_items.append((idx, current_section, item_text[:60] + "..."))
            continue
            
        # Numbered list item
        if re.match(r"^\d+\.\s+", s_line):
            if not in_numbered_list:
                in_numbered_list = True
                current_list_len = 1
                section_lists[current_section] = section_lists.get(current_section, 0) + 1
            else:
                current_list_len += 1
            continue
            
        # If we reached here and were in a list, close it
        if in_bullet_list:
            bullet_blocks += 1
            if current_list_len > longest_bullet_block:
                longest_bullet_block = current_list_len
            in_bullet_list = False
            current_list_len = 0
        if in_numbered_list:
            numbered_blocks += 1
            in_numbered_list = False
            current_list_len = 0
            
        # Normal prose paragraph
        if not in_table:
            total_paragraphs += 1

    # End of file flush
    if in_bullet_list:
        bullet_blocks += 1
        if current_list_len > longest_bullet_block:
            longest_bullet_block = current_list_len
    if in_numbered_list:
        numbered_blocks += 1

    candidates = [sec for sec, cnt in section_lists.items() if cnt >= 2]

    return {
        "file": file_path.name,
        "paragraphs": total_paragraphs,
        "bullet_blocks": bullet_blocks,
        "numbered_blocks": numbered_blocks,
        "longest_bullet": longest_bullet_block,
        "long_items_count": len(long_bullet_items),
        "long_items": long_bullet_items[:3],
        "candidates": candidates,
    }


def main():
    print("=" * 85)
    print("AUDIT LIST DENSITY & PROSE-FIRST WRITING METRICS")
    print("=" * 85)
    print(f"{'Chapter':<40} | {'Prose':<5} | {'Bullets':<7} | {'NumList':<7} | {'MaxBlt':<6} | {'LongItems':<9}")
    print("-" * 85)
    
    files = sorted(CHAPTERS_DIR.glob("*.md"))
    ch22_28_reports = []
    
    for f in files:
        rep = audit_chapter(f)
        ch_num_match = re.match(r"^(\d+)-", f.name)
        is_target = ch_num_match and 22 <= int(ch_num_match.group(1)) <= 28
        if is_target:
            ch22_28_reports.append(rep)
            
        name_display = f.name if len(f.name) <= 40 else f.name[:37] + "..."
        print(f"{name_display:<40} | {rep['paragraphs']:<5} | {rep['bullet_blocks']:<7} | {rep['numbered_blocks']:<7} | {rep['longest_bullet']:<6} | {rep['long_items_count']:<9}")

    print("=" * 85)
    print("\n[FOCUS AUDIT: CHAPTERS 22 -> 28]")
    print("-" * 85)
    for rep in ch22_28_reports:
        print(f"\n[*] {rep['file']}:")
        print(f"    - Prose paragraphs: {rep['paragraphs']}, Bullet blocks: {rep['bullet_blocks']}, Numbered blocks: {rep['numbered_blocks']}")
        print(f"    - Longest bullet block: {rep['longest_bullet']} items")
        print(f"    - Long bullet items (>150 chars or multi-sentence): {rep['long_items_count']}")
        if rep['candidates']:
            print(f"    - Sections with >=2 list blocks: {', '.join(rep['candidates'][:4])}")
        if rep['long_items']:
            for line_no, sec, sample in rep['long_items']:
                print(f"      [L{line_no}] ({sec[:30]}): {sample}")

    print("\n" + "=" * 85)


if __name__ == "__main__":
    main()
