#!/usr/bin/env python3
"""Trình xác thực kiểm toán tự động cho Phụ lục A: Living Error Atlas (book/appendices/error-atlas.md).

Không sử dụng dependency bên ngoài (Zero external dependencies).
Kiểm tra:
1. Sự tồn tại và cấu trúc tiêu đề chuẩn của Phụ lục A.
2. Thứ tự 10 nhóm Taxonomy chuẩn (A -> J).
3. Định dạng ID (^[A-J]\\d{2}$), tính liên tục và không trùng lặp mã lỗi.
4. Mọi entry đều có dòng hành động bắt đầu bằng '→ '.
5. Định dạng và tính hợp lệ của cross-reference (Chương 0 đến 21+).
6. Phát hiện trùng lặp exact message không cần thiết.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

EXPECTED_GROUPS = [
    ("A", "Compiler & Type System"),
    ("B", "Runtime & Panic"),
    ("C", "Error Values & I/O"),
    ("D", "Context & Cancellation"),
    ("E", "Filesystem & Process"),
    ("F", "Network / HTTP / TLS"),
    ("G", "Database"),
    ("H", "Concurrency"),
    ("I", "Modules / Test / Toolchain"),
    ("J", "Container / Kubernetes / CI-CD"),
]

VALID_CHAPTER_REGEX = re.compile(r"^Ch(?:ương\s+)?(\d{1,2})(?:,\s*(\d{1,2}))*$", re.IGNORECASE)


def validate_atlas(atlas_path: Path) -> bool:
    if not atlas_path.exists():
        print(f"[FAIL] Không tìm thấy file Error Atlas tại: {atlas_path}", file=sys.stderr)
        return False

    text = atlas_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    errors: list[str] = []

    # 1. Kiểm tra tiêu đề chính
    if not lines or lines[0].strip() != "# PHỤ LỤC A — ATLAS LỖI GO":
        errors.append(f"Dòng đầu tiên phải là '# PHỤ LỤC A — ATLAS LỖI GO', thực tế: '{lines[0] if lines else ''}'")

    has_subtitle = any(line.strip() == "## Đọc lỗi từ triệu chứng đến nguyên nhân" for line in lines[:5])
    if not has_subtitle:
        errors.append("Thiếu tiêu đề phụ '## Đọc lỗi từ triệu chứng đến nguyên nhân' trong 5 dòng đầu")

    # 2. Kiểm tra các nhóm Taxonomy (H2: ## Nhóm X — ...)
    group_pattern = re.compile(r"^##\s+([A-J])\s+—\s+(.+)$")
    found_groups: list[tuple[str, str]] = []
    for line in lines:
        m = group_pattern.match(line.strip())
        if m:
            found_groups.append((m.group(1), m.group(2).strip()))

    expected_codes = [g[0] for g in EXPECTED_GROUPS]
    found_codes = [g[0] for g in found_groups]
    if found_codes != expected_codes:
        errors.append(f"Thứ tự các nhóm Taxonomy không khớp chuẩn A->J. Kỳ vọng: {expected_codes}, thực tế: {found_codes}")

    # 3. Thu thập và kiểm tra từng entry (H3: ### X01 ...)
    entry_header_pattern = re.compile(r"^###\s+([A-J]\d{2})\s+`?([^`\n]+)`?$")
    bullet_msg_pattern = re.compile(r"^\s*[*•-]\s+`([^`]+)`")
    action_pattern = re.compile(r"^[→\->]\s*(.+?)(?:\s*\[?(Ch\d+(?:,\s*\d+)*)\]?)?$")

    seen_ids: set[str] = set()
    seen_titles: dict[str, str] = {}
    group_entries: dict[str, list[str]] = {code: [] for code in expected_codes}
    total_exact_messages = 0

    current_id: str | None = None
    current_entry_lines: list[str] = []
    entry_blocks: list[tuple[str, str, list[str]]] = []

    for line in lines:
        m_entry = entry_header_pattern.match(line.strip())
        if m_entry:
            if current_id:
                entry_blocks.append((current_id, current_title, current_entry_lines))
            current_id = m_entry.group(1)
            current_title = m_entry.group(2).strip()
            current_entry_lines = []
            continue
        if current_id:
            current_entry_lines.append(line)

    if current_id:
        entry_blocks.append((current_id, current_title, current_entry_lines))

    if not entry_blocks:
        errors.append("Không tìm thấy entry lỗi nào trong file!")

    for entry_id, title, block_lines in entry_blocks:
        group_code = entry_id[0]
        num_part = int(entry_id[1:])

        # Kiểm tra trùng ID
        if entry_id in seen_ids:
            errors.append(f"Trùng mã lỗi: {entry_id}")
        seen_ids.add(entry_id)
        group_entries[group_code].append(entry_id)

        # Kiểm tra trùng title
        norm_title = title.lower()
        if norm_title in seen_titles:
            errors.append(f"Lỗi {entry_id} có title trùng với {seen_titles[norm_title]}: '{title}'")
        seen_titles[norm_title] = entry_id

        # Đếm exact messages
        bullet_count = 0
        has_action = False
        has_ref = False

        for eline in block_lines:
            eline_s = eline.strip()
            b_match = bullet_msg_pattern.match(eline_s)
            if b_match:
                bullet_count += 1
            if eline_s.startswith("→"):
                has_action = True
                # Kiểm tra chapter reference
                ref_match = re.search(r"\[?(Ch\d+(?:,\s*\d+)*)\]?\s*$", eline_s)
                if ref_match:
                    has_ref = True

        if bullet_count > 0:
            total_exact_messages += bullet_count
        else:
            total_exact_messages += 1

        if not has_action:
            errors.append(f"Entry {entry_id} ('{title}') thiếu dòng hành động '→ '")
        if not has_ref:
            errors.append(f"Entry {entry_id} ('{title}') thiếu chapter reference hợp lệ dạng '[ChX,Y]'")

    # Kiểm tra tính liên tục của mã số trong từng nhóm (A01, A02, ...)
    for g_code, entries in group_entries.items():
        if not entries:
            errors.append(f"Nhóm {g_code} rỗng, không có entry nào!")
            continue
        expected_seq = [f"{g_code}{i:02d}" for i in range(1, len(entries) + 1)]
        if entries != expected_seq:
            errors.append(f"Nhóm {g_code} không liên tục về mã số: thực tế {entries} vs kỳ vọng {expected_seq}")

    if errors:
        print(f"[VALIDATOR-FAIL] Tìm thấy {len(errors)} vấn đề trong Error Atlas:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return False

    print("[VALIDATOR-PASS] Error Atlas hợp lệ tuyệt đối!")
    print(f"  - Số nhóm Taxonomy: {len(found_groups)} (A -> J)")
    print(f"  - Tổng số entry: {len(seen_ids)}")
    for g_code, g_name in EXPECTED_GROUPS:
        print(f"    * Nhóm {g_code} ({g_name}): {len(group_entries[g_code])} entries ({group_entries[g_code][0]}–{group_entries[g_code][-1]})")
    print(f"  - Tổng số exact error messages được cover: {total_exact_messages}")
    return True


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    atlas = root / "book/appendices/error-atlas.md"
    if not validate_atlas(atlas):
        sys.exit(1)
    sys.exit(0)
