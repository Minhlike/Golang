#!/usr/bin/env python3
"""
Zero-Guess Protocol Validator for Go DevOps Library Source Lab.
Validates:
1. catalog.json: exactly 50 libraries, ranks 1..50, unique IDs, valid enums, valid URLs.
2. lock.json: schema, valid commits, release statuses, fingerprints.
3. status.json: sync status enums.
4. provenance/: all 50 resolution records exist.
5. source_maps/: all 50 architectural source maps exist.
6. repos/: for any checked-out repository, verify commit match, detached HEAD, clean worktree, and source tree SHA-256 fingerprint.

Zero external dependencies - standard library only.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB_SOURCES_DIR = ROOT / "library_sources"
CATALOG_PATH = LIB_SOURCES_DIR / "catalog.json"
LOCK_PATH = LIB_SOURCES_DIR / "lock.json"
STATUS_PATH = LIB_SOURCES_DIR / "status.json"
PROVENANCE_DIR = LIB_SOURCES_DIR / "provenance"
SOURCE_MAPS_DIR = LIB_SOURCES_DIR / "source_maps"
REPORT_PATH = LIB_SOURCES_DIR / "UPDATE_REPORT.md"
REPOS_DIR = LIB_SOURCES_DIR / "repos"

VALID_TIERS = {"TIER_S", "TIER_A", "TIER_B", "FRONTIER"}
VALID_STRATEGIES = {
    "GO_MODULE_STABLE",
    "GIT_STABLE_TAG",
    "MODULE_PREFIX_TAG",
    "MULTI_MODULE",
    "PRE_RELEASE_ALLOWED",
    "HEAD_TRACKING",
    "GO_MODULE_LATEST_MAJOR",
}
VALID_RELEASE_STATUSES = {
    "OFFICIAL_STABLE",
    "PRE_RELEASE_FRONTIER",
    "UNSTABLE_HEAD",
    "PINNED",
    "BLOCKED",
}
VALID_SYNC_STATUSES = {
    "UP_TO_DATE",
    "UPDATED",
    "FIRST_INSTALL",
    "CHECK_ONLY_UPDATE_AVAILABLE",
    "DIRTY_BLOCKED",
    "REMOTE_IDENTITY_MISMATCH",
    "TAG_MOVED_SECURITY_REVIEW_REQUIRED",
    "NO_VALID_RELEASE",
    "NETWORK_ERROR",
    "REMOTE_ERROR",
    "VERSION_RESOLUTION_ERROR",
    "AMBIGUOUS_VERSION",
    "CHECKOUT_ERROR",
    "VERIFY_ERROR",
    "HASH_MISMATCH",
    "PRE_RELEASE_UPDATED",
    "UNSTABLE_HEAD_UPDATED",
}

IMPLEMENTATION_CLAIMED_LIBRARIES = {
    "k8s-client-go",
    "controller-runtime",
    "aws-sdk-go-v2",
    "go-git",
    "go-github",
    "cilium-ebpf",
    "mcp-go-sdk",
}

HEX_40_REGEX = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
HEX_64_REGEX = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)


def compute_tree_fingerprint(repo_path: Path) -> str:
    """Compute deterministic SHA-256 over all git-tracked files: sorted path + null + sha256(content)."""
    from concurrent.futures import ThreadPoolExecutor
    cmd = ["git", "-C", str(repo_path), "ls-files"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    tracked_files = sorted(res.stdout.splitlines())
    
    def _hash_file(rel):
        full_path = repo_path / rel
        if not full_path.is_file():
            return rel, None
        try:
            with open(full_path, "rb") as f:
                return rel, hashlib.sha256(f.read()).digest()
        except OSError:
            return rel, None

    with ThreadPoolExecutor(max_workers=16) as ex:
        file_hashes = dict(ex.map(_hash_file, tracked_files))

    h = hashlib.sha256()
    for rel_path in tracked_files:
        file_sha = file_hashes.get(rel_path)
        if file_sha is not None:
            h.update(rel_path.encode("utf-8") + b"\x00" + file_sha)
    return h.hexdigest()


def validate_catalog() -> tuple[list[str], dict[str, dict]]:
    errors = []
    if not CATALOG_PATH.exists():
        return [f"Missing catalog.json at {CATALOG_PATH}"], {}
    
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"Failed to parse catalog.json: {e}"], {}
    
    if not isinstance(data, list):
        return ["catalog.json root must be a JSON array of 50 items"], {}
    
    if len(data) != 50:
        errors.append(f"catalog.json must contain exactly 50 entries, found {len(data)}")
        
    seen_ids = set()
    seen_ranks = set()
    catalog_map = {}
    
    for i, entry in enumerate(data):
        lib_id = entry.get("id")
        rank = entry.get("rank")
        name = entry.get("name")
        tier = entry.get("tier")
        strat = entry.get("version_strategy")
        remote = entry.get("official_remote")
        
        if not lib_id or not isinstance(lib_id, str):
            errors.append(f"Entry {i} missing valid 'id'")
            continue
        if lib_id in seen_ids:
            errors.append(f"Duplicate library id: {lib_id}")
        seen_ids.add(lib_id)
        catalog_map[lib_id] = entry
        
        if rank is None or not isinstance(rank, int):
            errors.append(f"Library '{lib_id}' rank must be integer, got {rank}")
        else:
            if rank in seen_ranks:
                errors.append(f"Duplicate rank {rank} for library '{lib_id}'")
            seen_ranks.add(rank)
            
        if tier not in VALID_TIERS:
            errors.append(f"Library '{lib_id}' has invalid tier '{tier}'. Must be in {VALID_TIERS}")
            
        if strat not in VALID_STRATEGIES:
            errors.append(f"Library '{lib_id}' has invalid strategy '{strat}'. Must be in {VALID_STRATEGIES}")
            
        if not remote or not remote.startswith("https://") or not remote.endswith(".git"):
            errors.append(f"Library '{lib_id}' official_remote must be https://...git URL, got '{remote}'")
            
        important_paths = entry.get("important_paths")
        if not isinstance(important_paths, list) or len(important_paths) == 0:
            errors.append(f"Library '{lib_id}' important_paths must be non-empty list")
            
    expected_ranks = set(range(1, 51))
    missing_ranks = expected_ranks - seen_ranks
    if missing_ranks:
        errors.append(f"Missing ranks in catalog: {sorted(missing_ranks)}")
        
    return errors, catalog_map


def validate_lock(catalog_map: dict) -> tuple[list[str], dict[str, dict]]:
    errors = []
    if not LOCK_PATH.exists():
        return [f"Missing lock.json at {LOCK_PATH}"], {}
        
    try:
        with open(LOCK_PATH, "r", encoding="utf-8") as f:
            lock_doc = json.load(f)
    except Exception as e:
        return [f"Failed to parse lock.json: {e}"], {}
        
    libs = lock_doc.get("libraries", {})
    if not isinstance(libs, dict):
        return ["lock.json 'libraries' field must be a dictionary"], {}
        
    if len(libs) != 50:
        errors.append(f"lock.json must contain 50 libraries, found {len(libs)}")
        
    for lib_id, cat_entry in catalog_map.items():
        if lib_id not in libs:
            errors.append(f"Library '{lib_id}' missing from lock.json")
            continue
            
        l_entry = libs[lib_id]
        status = l_entry.get("release_status")
        if status not in VALID_RELEASE_STATUSES:
            errors.append(f"Library '{lib_id}' invalid release_status '{status}' in lock.json")
            
        commit = l_entry.get("resolved_commit")
        if status != "BLOCKED":
            if not commit or not HEX_40_REGEX.match(commit):
                errors.append(f"Library '{lib_id}' has invalid 40-char commit SHA '{commit}' in lock.json")
                
            fingerprint = l_entry.get("source_tree_sha256")
            if fingerprint:
                if not HEX_64_REGEX.match(fingerprint):
                    errors.append(f"Library '{lib_id}' invalid 64-char source_tree_sha256 '{fingerprint}'")
                elif fingerprint == "0" * 64 and lib_id in IMPLEMENTATION_CLAIMED_LIBRARIES:
                    errors.append(f"Library '{lib_id}' is claimed for implementation but has all-zero fingerprint in lock.json")
            elif lib_id in IMPLEMENTATION_CLAIMED_LIBRARIES:
                errors.append(f"Library '{lib_id}' is claimed for implementation but lacks source_tree_sha256 in lock.json")
                
    return errors, libs


def validate_status(catalog_map: dict) -> list[str]:
    errors = []
    if not STATUS_PATH.exists():
        return [f"Missing status.json at {STATUS_PATH}"]
        
    try:
        with open(STATUS_PATH, "r", encoding="utf-8") as f:
            status_doc = json.load(f)
    except Exception as e:
        return [f"Failed to parse status.json: {e}"]
        
    libs = status_doc.get("libraries", {})
    if not isinstance(libs, dict):
        return ["status.json 'libraries' field must be a dictionary"]
        
    for lib_id in catalog_map:
        if lib_id not in libs:
            errors.append(f"Library '{lib_id}' missing from status.json")
            continue
        st = libs[lib_id].get("sync_status")
        if st not in VALID_SYNC_STATUSES:
            errors.append(f"Library '{lib_id}' has invalid sync_status '{st}' in status.json")
            
    return errors


def validate_provenance_and_sourcemaps(catalog_map: dict) -> list[str]:
    errors = []
    for lib_id in catalog_map:
        # Provenance check
        prov_file = PROVENANCE_DIR / f"{lib_id}.json"
        if not prov_file.exists():
            errors.append(f"Missing provenance file: {prov_file.name}")
        else:
            try:
                with open(prov_file, "r", encoding="utf-8") as f:
                    pdata = json.load(f)
                if pdata.get("id") != lib_id:
                    errors.append(f"Provenance file {prov_file.name} id mismatch: {pdata.get('id')}")
            except Exception as e:
                errors.append(f"Failed to read provenance {prov_file.name}: {e}")

        # Source map check
        sm_file = SOURCE_MAPS_DIR / f"{lib_id}.json"
        if not sm_file.exists():
            errors.append(f"Missing source map file: {sm_file.name}")
        else:
            try:
                with open(sm_file, "r", encoding="utf-8") as f:
                    smdata = json.load(f)
                if smdata.get("id") != lib_id:
                    errors.append(f"Source map {sm_file.name} id mismatch: {smdata.get('id')}")
                req_fields = ["entrypoints", "public_api", "core_types", "call_paths", "concurrency_model", "boundaries"]
                for rf in req_fields:
                    if rf not in smdata:
                        errors.append(f"Source map {sm_file.name} missing field '{rf}'")
            except Exception as e:
                errors.append(f"Failed to read source map {sm_file.name}: {e}")

    return errors


def validate_local_repos(catalog_map: dict, lock_libs: dict) -> list[str]:
    errors = []
    if not REPOS_DIR.exists():
        errors.append(f"Missing repos directory at {REPOS_DIR}")
        return errors

    # Enforce mandatory checkout presence for all implementation-claimed libraries
    for lib_id in sorted(IMPLEMENTATION_CLAIMED_LIBRARIES):
        repo_dir = REPOS_DIR / lib_id
        if not repo_dir.exists() or not (repo_dir / ".git").exists():
            errors.append(f"SOURCE_UNVERIFIED_BLOCKER: Required implementation library '{lib_id}' missing from {REPOS_DIR}")
        
    for lib_id, l_entry in lock_libs.items():
        repo_dir = REPOS_DIR / lib_id
        if not repo_dir.exists() or not (repo_dir / ".git").exists():
            continue
            
        expected_commit = l_entry.get("resolved_commit")
        if not expected_commit:
            continue
            
        cat_entry = catalog_map.get(lib_id, {})
        expected_remote = cat_entry.get("official_remote")
        if expected_remote:
            res = subprocess.run(["git", "-C", str(repo_dir), "remote", "get-url", "origin"], capture_output=True, text=True)
            if res.returncode == 0:
                actual_remote = res.stdout.strip()
                if actual_remote.lower() != expected_remote.lower() and not actual_remote.lower().endswith(expected_remote.lower()):
                    errors.append(f"Repo '{lib_id}' origin remote mismatch: expected {expected_remote}, got {actual_remote}")

        # Check detached HEAD state
        res = subprocess.run(["git", "-C", str(repo_dir), "symbolic-ref", "-q", "HEAD"], capture_output=True, text=True)
        if res.returncode == 0:
            errors.append(f"Repo '{lib_id}' is on branch '{res.stdout.strip()}', expected detached HEAD")

        # Check current HEAD commit
        res = subprocess.run(["git", "-C", str(repo_dir), "rev-parse", "HEAD"], capture_output=True, text=True)
        if res.returncode != 0:
            errors.append(f"Repo '{lib_id}' git rev-parse HEAD failed: {res.stderr.strip()}")
            continue
        actual_commit = res.stdout.strip()
        if actual_commit.lower() != expected_commit.lower():
            errors.append(f"Repo '{lib_id}' HEAD commit mismatch: expected {expected_commit}, got {actual_commit}")
            
        # Check clean worktree
        res = subprocess.run(["git", "-C", str(repo_dir), "status", "--porcelain"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            errors.append(f"Repo '{lib_id}' worktree is dirty! Zero-Guess Protocol requires pristine clean checkout.")
            
        # Check source tree fingerprint if recorded in lock
        expected_sha = l_entry.get("source_tree_sha256")
        if not expected_sha or expected_sha == "0" * 64:
            if lib_id in IMPLEMENTATION_CLAIMED_LIBRARIES:
                errors.append(f"Repo '{lib_id}' has all-zero or missing fingerprint in lock.json")
        else:
            computed_sha = compute_tree_fingerprint(repo_dir)
            if computed_sha.lower() != expected_sha.lower():
                errors.append(f"Repo '{lib_id}' source_tree_sha256 mismatch: expected {expected_sha}, computed {computed_sha}")
                
    return errors


def validate_report_consistency(catalog_map: dict, lock_libs: dict) -> list[str]:
    errors = []
    if not REPORT_PATH.exists():
        return [f"Missing UPDATE_REPORT.md at {REPORT_PATH}"]

    try:
        content = REPORT_PATH.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Failed to read UPDATE_REPORT.md: {e}"]

    row_pattern = re.compile(
        r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)…`\s*\|\s*`([^`]+)…`\s*\|\s*`([^`]+)`\s*\|",
        re.MULTILINE
    )
    matches = row_pattern.findall(content)
    if len(matches) != len(catalog_map):
        errors.append(f"UPDATE_REPORT.md table must contain {len(catalog_map)} rows, found {len(matches)}")

    report_libs = set()
    for rank_str, lid, tier, mod, strat, ver, commit_prefix, sha_prefix, sync in matches:
        report_libs.add(lid)
        if lid not in lock_libs:
            errors.append(f"UPDATE_REPORT.md contains unknown library '{lid}'")
            continue
        l_entry = lock_libs[lid]
        exp_commit = (l_entry.get("resolved_commit") or "")[:10]
        exp_sha = (l_entry.get("source_tree_sha256") or "0" * 64)[:10]
        exp_ver = l_entry.get("resolved_version", "")

        if ver != exp_ver:
            errors.append(f"UPDATE_REPORT.md version mismatch for '{lid}': report has '{ver}', lock.json has '{exp_ver}'")
        if commit_prefix.lower() != exp_commit.lower():
            errors.append(f"UPDATE_REPORT.md commit mismatch for '{lid}': report has '{commit_prefix}', lock.json has '{exp_commit}'")
        if sha_prefix.lower() != exp_sha.lower():
            errors.append(f"UPDATE_REPORT.md source_tree_sha256 mismatch for '{lid}': report has '{sha_prefix}', lock.json has '{exp_sha}'")

    missing = set(catalog_map.keys()) - report_libs
    if missing:
        errors.append(f"UPDATE_REPORT.md missing libraries: {sorted(missing)}")

    return errors


def main():
    print("=" * 70)
    print("ZERO-GUESS PROTOCOL VALIDATOR — GO DEVOPS LIBRARY SOURCE LAB")
    print("=" * 70)
    
    all_errors = []
    
    # 1. Catalog
    cat_errors, catalog_map = validate_catalog()
    all_errors.extend(cat_errors)
    if not cat_errors:
        print(f"[*] catalog.json: PASS (50 valid libraries, Ranks 1..50)")
    else:
        print(f"[!] catalog.json: FAIL ({len(cat_errors)} errors)")
        for err in cat_errors:
            print(f"    - {err}")
            
    # 2. Lock
    lock_errors, lock_libs = validate_lock(catalog_map)
    all_errors.extend(lock_errors)
    if not lock_errors:
        print(f"[*] lock.json: PASS (50 libraries locked with valid commits)")
    else:
        print(f"[!] lock.json: FAIL ({len(lock_errors)} errors)")
        for err in lock_errors:
            print(f"    - {err}")
            
    # 3. Status
    status_errors = validate_status(catalog_map)
    all_errors.extend(status_errors)
    if not status_errors:
        print(f"[*] status.json: PASS (50 libraries with valid status enums)")
    else:
        print(f"[!] status.json: FAIL ({len(status_errors)} errors)")
        for err in status_errors:
            print(f"    - {err}")
            
    # 4. Provenance & Source Maps
    ps_errors = validate_provenance_and_sourcemaps(catalog_map)
    all_errors.extend(ps_errors)
    if not ps_errors:
        print(f"[*] provenance/ & source_maps/: PASS (50 records each)")
    else:
        print(f"[!] provenance/ & source_maps/: FAIL ({len(ps_errors)} errors)")
        for err in ps_errors[:10]:
            print(f"    - {err}")
        if len(ps_errors) > 10:
            print(f"    ... and {len(ps_errors) - 10} more")
            
    # 5. Local Repos (if checked out)
    repo_errors = validate_local_repos(catalog_map, lock_libs)
    all_errors.extend(repo_errors)
    if not repo_errors:
        print(f"[*] repos/ checkouts: PASS (commits, clean status, fingerprints)")
    else:
        print(f"[!] repos/ checkouts: FAIL ({len(repo_errors)} errors)")
        for err in repo_errors:
            print(f"    - {err}")

    # 6. UPDATE_REPORT.md consistency with lock.json
    report_errors = validate_report_consistency(catalog_map, lock_libs)
    all_errors.extend(report_errors)
    if not report_errors:
        print(f"[*] UPDATE_REPORT.md consistency: PASS (exact match with lock.json)")
    else:
        print(f"[!] UPDATE_REPORT.md consistency: FAIL ({len(report_errors)} errors)")
        for err in report_errors:
            print(f"    - {err}")

    # Summary Metrics
    catalog_locked = len(catalog_map)
    impl_verified = sum(1 for e in lock_libs.values() if e.get("source_tree_sha256") and e.get("source_tree_sha256") != "0" * 64)
    fingerprint_pending = catalog_locked - impl_verified

    print("-" * 70)
    print(f"CATALOG_LOCKED = {catalog_locked}")
    print(f"IMPLEMENTATION_SOURCE_VERIFIED = {impl_verified}")
    print(f"FINGERPRINT_PENDING = {fingerprint_pending}")
            
    print("=" * 70)
    if all_errors:
        print(f"OVERALL RESULT: FAILED ({len(all_errors)} total errors)")
        sys.exit(1)
    else:
        print("OVERALL RESULT: PASSED (100% compliance with Zero-Guess Protocol)")
        sys.exit(0)


if __name__ == "__main__":
    main()
