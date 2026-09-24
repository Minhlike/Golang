#!/usr/bin/env python3
"""Trình xác thực kiểm toán tự động cho Phụ lục A: Living Error Atlas (book/appendices/error-atlas.md).

Không sử dụng dependency bên ngoài (Zero external dependencies).
Kiểm tra:
1. Sự tồn tại và cấu trúc tiêu đề chuẩn của Phụ lục A.
2. Thứ tự 10 nhóm Taxonomy chuẩn (A -> J).
3. Định dạng ID (^[A-J]\\d{2}$), tính liên tục và không trùng lặp mã lỗi.
4. Mọi entry đều có dòng hành động bắt đầu bằng '→ '.
5. Định dạng và tính hợp lệ của cross-reference (xác thực các chương ChX thực sự tồn tại trong book/chapters/).
6. Phát hiện trùng lặp diagnostic patterns / strings không cần thiết.
7. Phân loại và đếm riêng: EXACT / SENTINEL / STATUS / FAMILY.
8. Báo cáo tổng số diagnostic patterns được cover.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
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

# Phân loại bản chất kỹ thuật của từng entry:
# - EXACT: chuỗi lỗi thực sự được compiler / runtime / library / tool phát ra
# - SENTINEL: error value chuẩn như io.EOF, sql.ErrNoRows, os.ErrNotExist, v.v.
# - STATUS: Kubernetes / runtime / CI status hoặc reason
# - FAMILY: tên hiện tượng / diagnostic family
ENTRY_TYPES: dict[str, str] = {
    # Nhóm A: Compiler & Type System (14 EXACT)
    "A01": "EXACT", "A02": "EXACT", "A03": "EXACT", "A04": "EXACT", "A05": "EXACT",
    "A06": "EXACT", "A07": "EXACT", "A08": "EXACT", "A09": "EXACT", "A10": "EXACT",
    "A11": "EXACT", "A12": "EXACT", "A13": "EXACT", "A14": "EXACT",

    # Nhóm B: Runtime & Panic (11 EXACT)
    "B01": "EXACT", "B02": "EXACT", "B03": "EXACT", "B04": "EXACT", "B05": "EXACT",
    "B06": "EXACT", "B07": "EXACT", "B08": "EXACT", "B09": "EXACT", "B10": "EXACT",
    "B11": "EXACT",

    # Nhóm C: Error Values & I/O (2 EXACT, 6 SENTINEL)
    "C01": "SENTINEL", "C02": "SENTINEL", "C03": "SENTINEL", "C04": "SENTINEL",
    "C05": "EXACT", "C06": "EXACT", "C07": "SENTINEL", "C08": "SENTINEL",

    # Nhóm D: Context & Cancellation (2 SENTINEL, 2 FAMILY)
    "D01": "SENTINEL", "D02": "SENTINEL", "D03": "FAMILY", "D04": "FAMILY",

    # Nhóm E: Filesystem & Process (3 SENTINEL, 3 EXACT)
    "E01": "SENTINEL", "E02": "SENTINEL", "E03": "SENTINEL",
    "E04": "EXACT", "E05": "EXACT", "E06": "EXACT",

    # Nhóm F: Network / HTTP / TLS (9 EXACT, 1 FAMILY)
    "F01": "EXACT", "F02": "EXACT", "F03": "EXACT", "F04": "EXACT", "F05": "EXACT",
    "F06": "EXACT", "F07": "EXACT", "F08": "EXACT", "F09": "EXACT", "F10": "FAMILY",

    # Nhóm G: Database (4 EXACT, 1 SENTINEL, 1 FAMILY)
    "G01": "SENTINEL", "G02": "EXACT", "G03": "FAMILY",
    "G04": "EXACT", "G05": "EXACT", "G06": "EXACT",

    # Nhóm H: Concurrency (4 EXACT, 1 FAMILY)
    "H01": "EXACT", "H02": "EXACT", "H03": "FAMILY", "H04": "EXACT", "H05": "EXACT",

    # Nhóm I: Modules & Toolchain (7 EXACT)
    "I01": "EXACT", "I02": "EXACT", "I03": "EXACT", "I04": "EXACT", "I05": "EXACT",
    "I06": "EXACT", "I07": "EXACT",

    # Nhóm J: Container / Kubernetes / CI-CD (7 STATUS)
    "J01": "STATUS", "J02": "STATUS", "J03": "STATUS", "J04": "STATUS",
    "J05": "STATUS", "J06": "STATUS", "J07": "STATUS",
}


def discover_existing_chapters(chapters_dir: Path) -> set[int]:
    """Tìm tất cả các số chương hiện có trong book/chapters/."""
    chapters = set()
    if not chapters_dir.exists():
        return chapters
    for f in chapters_dir.glob("*.md"):
        prefix = f.stem.split("-")[0]
        if prefix.isdigit():
            chapters.add(int(prefix))
    return chapters


def validate_atlas(atlas_path: Path, chapters_dir: Path | None = None) -> bool:
    if not atlas_path.exists():
        print(f"[FAIL] Không tìm thấy file Error Atlas tại: {atlas_path}", file=sys.stderr)
        return False

    if chapters_dir is None:
        chapters_dir = atlas_path.resolve().parents[1] / "chapters"

    existing_chapters = discover_existing_chapters(chapters_dir)

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
    entry_header_pattern = re.compile(r"^###\s+([A-J]\d{2})\s+(.+)$")
    bullet_msg_pattern = re.compile(r"^\s*[*•-]\s+(`[^`]+`|.+)$")

    seen_ids: set[str] = set()
    seen_titles: dict[str, str] = {}
    group_entries: dict[str, list[str]] = {code: [] for code in expected_codes}
    all_diagnostic_patterns: list[tuple[str, str]] = []  # (entry_id, pattern_str)

    current_id: str | None = None
    current_title: str = ""
    current_entry_lines: list[str] = []
    entry_blocks: list[tuple[str, str, list[str]]] = []

    for line in lines:
        m_entry = entry_header_pattern.match(line.strip())
        if m_entry:
            if current_id:
                entry_blocks.append((current_id, current_title, current_entry_lines))
            current_id = m_entry.group(1)
            current_title = m_entry.group(2).strip().strip("`")
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

        # Kiểm tra trùng ID
        if entry_id in seen_ids:
            errors.append(f"Trùng mã lỗi: {entry_id}")
        seen_ids.add(entry_id)
        group_entries[group_code].append(entry_id)

        # Kiểm tra phân loại tồn tại
        if entry_id not in ENTRY_TYPES:
            errors.append(f"Entry {entry_id} chưa được định nghĩa trong từ điển ENTRY_TYPES!")

        # Kiểm tra trùng title
        norm_title = title.lower().strip()
        if norm_title in seen_titles:
            errors.append(f"Lỗi {entry_id} có title trùng với {seen_titles[norm_title]}: '{title}'")
        seen_titles[norm_title] = entry_id

        # Thu thập diagnostic patterns
        bullets: list[str] = []
        has_action = False
        has_ref = False

        for eline in block_lines:
            eline_s = eline.strip()
            b_match = bullet_msg_pattern.match(eline_s)
            if b_match:
                b_text = b_match.group(1).strip().strip("`")
                bullets.append(b_text)
            if eline_s.startswith("→"):
                has_action = True
                # Kiểm tra chapter reference
                ref_match = re.search(r"\[?(Ch\d+(?:,\s*\d+)*)\]?\s*$", eline_s)
                if ref_match:
                    has_ref = True
                    # Validate các số chương thực sự tồn tại trong repo
                    raw_nums = ref_match.group(1).replace("Ch", "").split(",")
                    for n_str in raw_nums:
                        n = int(n_str.strip())
                        if n not in existing_chapters:
                            errors.append(
                                f"Entry {entry_id} tham chiếu đến Chương {n} không tồn tại trong book/chapters/!"
                            )

        if bullets:
            for b in bullets:
                all_diagnostic_patterns.append((entry_id, b))
        else:
            all_diagnostic_patterns.append((entry_id, title))

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

    # Kiểm tra trùng lặp diagnostic patterns giữa các entry khác nhau
    pattern_counter = Counter(p[1].lower().strip() for p in all_diagnostic_patterns)
    for pat, count in pattern_counter.items():
        if count > 1:
            matching_ids = [p[0] for p in all_diagnostic_patterns if p[1].lower().strip() == pat]
            # Cho phép nếu là các bullet trong cùng một entry, nhưng không cho phép trùng giữa các entry khác nhau
            if len(set(matching_ids)) > 1:
                errors.append(f"Phát hiện trùng lặp diagnostic pattern '{pat}' giữa các entries: {matching_ids}")

    if errors:
        print(f"[VALIDATOR-FAIL] Tìm thấy {len(errors)} vấn đề trong Error Atlas:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return False

    # Thống kê phân loại
    type_counts = Counter(ENTRY_TYPES[eid] for eid in seen_ids if eid in ENTRY_TYPES)

    print("[VALIDATOR-PASS] Error Atlas: structural validation passed!")
    print(f"  - Số nhóm Taxonomy: {len(found_groups)} (A -> J)")
    print(f"  - Tổng số entry: {len(seen_ids)}")
    print(f"    * EXACT (compiler/runtime/library diagnostics): {type_counts['EXACT']}")
    print(f"    * SENTINEL (standard & defined error values): {type_counts['SENTINEL']}")
    print(f"    * STATUS (Kubernetes/runtime/CI status & reasons): {type_counts['STATUS']}")
    print(f"    * FAMILY (diagnostic phenomena families): {type_counts['FAMILY']}")
    for g_code, g_name in EXPECTED_GROUPS:
        entries = group_entries[g_code]
        print(f"    * Nhóm {g_code} ({g_name}): {len(entries)} entries ({entries[0]}–{entries[-1]})")
    print(f"  - Tổng số diagnostic patterns được cover: {len(all_diagnostic_patterns)}")
    return True


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    atlas = root / "book/appendices/error-atlas.md"
    chapters = root / "book/chapters"
    if not validate_atlas(atlas, chapters):
        sys.exit(1)
    sys.exit(0)
