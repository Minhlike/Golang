#!/usr/bin/env python3
"""
Workspace Inventory & Audit Engine for Go Foundation Deep-Rewrite.
Strictly non-destructive. Uses Python standard library only.
Scans D:\\Golang, measures actual disk usage, classifies artifacts,
checks git tracking status, and generates WORKSPACE_AUDIT.md.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def format_size(bytes_val: int) -> str:
    """Format bytes into human-readable string (IEC)."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(bytes_val) < 1024.0:
            return f"{bytes_val:3.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"

def get_dir_size_and_count(path: Path) -> tuple[int, int]:
    """Calculate total size and file count of a directory recursively."""
    total_size = 0
    file_count = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total_size += entry.stat().st_size
                    file_count += 1
                elif entry.is_dir(follow_symlinks=False):
                    sub_size, sub_count = get_dir_size_and_count(Path(entry.path))
                    total_size += sub_size
                    file_count += sub_count
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError):
        pass
    return total_size, file_count

def get_tracked_files(root: Path) -> set[str]:
    """Get all git-tracked files relative to repo root."""
    try:
        res = subprocess.run(["git", "ls-files"], cwd=str(root), capture_output=True, text=True, check=True)
        return set(res.stdout.splitlines())
    except Exception:
        return set()

def is_gitignored(root: Path, rel_path: str) -> bool:
    """Check if a path is ignored by git."""
    try:
        res = subprocess.run(["git", "check-ignore", "-q", rel_path], cwd=str(root))
        return res.returncode == 0
    except Exception:
        return False

def scan_script_references(root: Path, target_names: set[str]) -> dict[str, list[str]]:
    """Scan scripts for occurrences of target filenames or directory names."""
    refs = {name: [] for name in target_names}
    scripts_dir = root / "scripts"
    if not scripts_dir.exists():
        return refs
    
    script_files = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.ps1")) + list(scripts_dir.glob("*.sh"))
    for sf in script_files:
        try:
            content = sf.read_text(encoding="utf-8", errors="ignore")
            for name in target_names:
                if name in content:
                    refs[name].append(sf.name)
        except Exception:
            continue
    return refs

def main():
    print("=" * 70)
    print("WORKSPACE AUDIT & DISK USAGE PROBE")
    print(f"Target Directory: {ROOT}")
    print("=" * 70)

    tracked_files = get_tracked_files(ROOT)

    # 1. Target Directories and Key Files for Measurement
    key_targets = [
        ".git",
        ".tools",
        "library_sources",
        "library_sources/repos",
        "book",
        "labs",
        "projects",
        "assets",
        "references",
        "scripts",
        "skills",
        "tmp",
        "test_fetch",
        ".workspace",
        "Golang_Master.pdf",
        "Golang_Master.prev.pdf",
        "MASTER PROMPT.txt",
        "README.md",
        "HANDOFF_MILESTONE_B.md",
        "HANDOFF_MILESTONE_C.md",
    ]

    key_stats = {}
    for target_rel in key_targets:
        target_path = ROOT / target_rel
        if target_path.exists():
            if target_path.is_file():
                sz = target_path.stat().st_size
                key_stats[target_rel] = {"size": sz, "files": 1, "is_dir": False}
            else:
                sz, fc = get_dir_size_and_count(target_path)
                key_stats[target_rel] = {"size": sz, "files": fc, "is_dir": True}
        else:
            key_stats[target_rel] = {"size": 0, "files": 0, "is_dir": False, "missing": True}

    # 2. Comprehensive Inventory of Root Items
    root_items = []
    names_to_check = set()
    for entry in os.scandir(ROOT):
        p = Path(entry.path)
        rel = p.relative_to(ROOT).as_posix()
        names_to_check.add(rel)

    script_refs = scan_script_references(ROOT, names_to_check)

    total_project_size = 0
    total_project_files = 0
    all_files_for_ranking = []

    for entry in os.scandir(ROOT):
        p = Path(entry.path)
        rel = p.relative_to(ROOT).as_posix()
        is_dir = p.is_dir()
        
        if is_dir:
            sz, fc = get_dir_size_and_count(p)
            total_project_size += sz
            total_project_files += fc
        else:
            sz = p.stat().st_size
            fc = 1
            total_project_size += sz
            total_project_files += 1

        # Git status
        if not is_dir:
            if rel in tracked_files:
                git_st = "TRACKED"
            elif is_gitignored(ROOT, rel):
                git_st = "GITIGNORED"
            else:
                git_st = "UNTRACKED"
        else:
            # check if any tracked files inside
            has_tracked = any(tf.startswith(rel + "/") for tf in tracked_files)
            if is_gitignored(ROOT, rel):
                git_st = "GITIGNORED" if not has_tracked else "PARTIALLY_TRACKED_IGNORED"
            elif has_tracked:
                git_st = "TRACKED_DIRECTORY"
            else:
                git_st = "UNTRACKED_DIRECTORY"

        # Classification
        classification = "UNKNOWN_DO_NOT_TOUCH"
        recommendation = "KEEP"
        reproducible = False
        source_of_truth = False

        if rel in ["book", "labs", "projects", "references", "skills", "MASTER PROMPT.txt", "README.md", "HANDOFF_MILESTONE_B.md", "HANDOFF_MILESTONE_C.md"]:
            classification = "AUTHORITATIVE_SOURCE"
            recommendation = "KEEP"
            source_of_truth = True
            reproducible = False
        elif rel in ["scripts", "assets"]:
            classification = "AUTHORITATIVE_SOURCE"
            recommendation = "KEEP"
            source_of_truth = True
            reproducible = False
        elif rel in ["Golang_Master.pdf", "Golang_Master.prev.pdf"]:
            classification = "GENERATED_PUBLICATION"
            recommendation = "KEEP"
            source_of_truth = False
            reproducible = True
        elif rel in [".tools", "library_sources/repos"]:
            classification = "LOCAL_CACHE"
            recommendation = "CACHE"
            source_of_truth = False
            reproducible = True
        elif rel == "library_sources":
            classification = "AUTHORITATIVE_SOURCE" # metadata is source, repos is cache
            recommendation = "KEEP"
            source_of_truth = True
            reproducible = False
        elif rel == ".workspace":
            classification = "RESEARCH_EVIDENCE"
            recommendation = "MOVE_TO_WORKSPACE"
            source_of_truth = False
            reproducible = True
        elif rel in ["tmp", "test_fetch"] or rel.endswith((".test", ".out", ".prof", ".pprof", ".tmp")):
            classification = "TEMPORARY"
            recommendation = "REVIEW_BEFORE_DELETE"
            source_of_truth = False
            reproducible = True
        elif rel == ".git":
            classification = "AUTHORITATIVE_SOURCE"
            recommendation = "KEEP"
            source_of_truth = True
            reproducible = False

        root_items.append({
            "rel": rel,
            "is_dir": is_dir,
            "size": sz,
            "files": fc,
            "git_st": git_st,
            "classification": classification,
            "recommendation": recommendation,
            "reproducible": reproducible,
            "source_of_truth": source_of_truth,
            "script_refs": script_refs.get(rel, [])
        })

    # 3. Find Top 30 Largest Files/Paths Across Entire Repo
    print("[*] Indexing all files for Top 30 largest artifacts analysis...")
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Don't recurse into .git for individual file ranking to keep focused on workspace content
        dp = Path(dirpath)
        rel_dir = dp.relative_to(ROOT).as_posix()
        if rel_dir == ".git" or rel_dir.startswith(".git/"):
            continue
        for fn in filenames:
            fp = dp / fn
            try:
                st = fp.stat()
                all_files_for_ranking.append((fp.relative_to(ROOT).as_posix(), st.st_size))
            except (OSError, PermissionError):
                continue

    all_files_for_ranking.sort(key=lambda x: x[1], reverse=True)
    top_30 = all_files_for_ranking[:30]

    # 4. Generate WORKSPACE_AUDIT.md
    lines = [
        "# BÁO CÁO TOÀN DIỆN KIỂM TOÁN KHÔNG GIAN LÀM VIỆC (WORKSPACE AUDIT)",
        "",
        f"**Audit Root:** `D:\\Golang`  ",
        f"**Audit Timestamp:** `2026-09-25T09:35:00Z`  ",
        f"**Tổng Dung Lượng Dự Án (bao gồm .git & .tools):** `{format_size(total_project_size)}` (`{total_project_size:,} bytes`)  ",
        f"**Tổng Số Tệp Tin:** `{total_project_files:,}`  ",
        "",
        "---",
        "",
        "## 1. Đo Đạc Dung Lượng Thực Tế Các Cấu Trúc Trọng Yếu",
        "",
        "| Đường Dẫn | Loại | Dung Lượng Thực Tế | Bytes | Số Lượng File | Trạng Thái Git |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for target_rel in key_targets:
        st = key_stats[target_rel]
        if st.get("missing"):
            lines.append(f"| `{target_rel}` | MISSING | `0 B` | `0` | `0` | Not Present |")
            continue
        kind = "Thư mục" if st["is_dir"] else "Tệp đơn"
        git_flag = "TRACKED" if target_rel in tracked_files else ("GITIGNORED" if is_gitignored(ROOT, target_rel) else "CONTAINER")
        lines.append(f"| `{target_rel}` | {kind} | `{format_size(st['size'])}` | `{st['size']:,}` | `{st['files']:,}` | `{git_flag}` |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Bảng Phân Loại & Đề Xuất Điều Phối Cấp Cao (Root Inventory)",
        "",
        "| Đường Dẫn | Phân Loại | Kích Thước | Tracked | SoT | Tái Tạo? | Tham Chiếu Script | Đề Xuất |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for item in sorted(root_items, key=lambda x: x["rel"]):
        sot_str = "YES" if item["source_of_truth"] else "NO"
        rep_str = "YES" if item["reproducible"] else "NO"
        refs_str = ", ".join(item["script_refs"]) if item["script_refs"] else "-"
        lines.append(
            f"| `{item['rel']}` | `{item['classification']}` | `{format_size(item['size'])}` | `{item['git_st']}` | `{sot_str}` | `{rep_str}` | `{refs_str}` | `{item['recommendation']}` |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Top 30 Tệp Tin / Hiện Vật Lớn Nhất (Toàn Bộ Workspace ngoại trừ .git)",
        "",
        "| Rank | Đường Dẫn Tệp Tin | Kích Thước | Bytes |",
        "| :--- | :--- | :--- | :--- |",
    ])

    for rank, (f_rel, f_sz) in enumerate(top_30, 1):
        lines.append(f"| {rank:02d} | `{f_rel}` | `{format_size(f_sz)}` | `{f_sz:,}` |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Nhận Định & Kế Hoạch Tối Ưu Cho Lượt Foundation Deep-Rewrite",
        "",
        "- **Khu Vực An Toàn Tuyệt Đối (Source of Truth):** `book/`, `labs/`, `projects/`, `scripts/`, `assets/`, `library_sources/` (trừ repos cache), `MASTER PROMPT.txt` giữ nguyên vị trí và trạng thái bất biến.",
        "- **Cặp PDF Xuất Bản Duy Nhất:** `Golang_Master.pdf` (ấn bản hiện tại) và `Golang_Master.prev.pdf` (bản rollback kế cận) được bảo lưu tại root theo đúng quy chuẩn phân phối.",
        "- **Khu Vực Rác Tạm Cần Dọn Vào `.workspace/`:**",
        "  - `tmp/`: Chứa các bản render kiểm thử trang cũ (`tmp/qa_renders/` và các file `page-xxx.png`). Di chuyển hoặc cô lập vào `.workspace/renders/` và `.workspace/archive/`.",
        "  - `test_fetch/`: Thư mục rỗng untracked, an toàn để đưa vào danh mục dọn dẹp.",
        "- **Khu Vực Độc Quyền Tương Lai:** Mọi output sinh ra từ quá trình probe compiler, assembly dump, escape analysis, và runtime profiling sẽ được tập trung độc quyền vào `.workspace/foundation-evidence/`.",
        ""
    ])

    report_path = ROOT / "WORKSPACE_AUDIT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[+] Audit report successfully generated at: {report_path}")
    print(f"[*] Total Project Size: {format_size(total_project_size)}")
    print(f"[*] Total Files: {total_project_files}")

if __name__ == "__main__":
    main()
