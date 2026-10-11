"""Reproduce this scoped checkpoint, not a whole-book scientific acceptance."""
from __future__ import annotations

import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASELINE = "5938862b864b51d755209031972a1bb07f5babf2"
GO = os.environ.get("AGENT1_GO", "D:/Golang/.tools/go1.27.1/bin/go.exe")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: list[str], cwd: Path = ROOT) -> dict:
    result = subprocess.run(args, cwd=cwd, capture_output=True, check=False)
    return {
        "command": args, "cwd": str(cwd), "exit_code": result.returncode,
        "stdout_utf8": result.stdout.decode("utf-8", errors="replace"),
        "stderr_utf8": result.stderr.decode("utf-8", errors="replace"),
        "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
        "stdout_base64": base64.b64encode(result.stdout).decode("ascii"),
        "stderr_base64": base64.b64encode(result.stderr).decode("ascii"),
    }


def chapter26_excerpt_tests(from_pdf: bool = False) -> dict:
    """Compile the printed Go excerpts with ONLY their omitted support code.

    The gate and exercise implementations come from Markdown, not from policy.go.
    The existing lab tests thus exercise the implementation the reader sees.
    """
    chapter = ROOT / "book/chapters/26-chuoi-cung-ung-co-the-kiem-chung.md"
    blocks = re.findall(r"^~~~go\n(.*?)^~~~$", chapter.read_text(encoding="utf-8"), re.M | re.S)
    if from_pdf:
        import fitz
        doc = fitz.open(ROOT / "tmp/pdfs/Golang_Master.candidate.pdf")
        outline = doc.get_toc()
        begin = next(p-1 for _, title, p in outline if title.startswith("Chương 26 —"))
        end = next(p-1 for _, title, p in outline if title.startswith("Chương 27 —"))
        lines = []
        for page in range(begin, end):
            for block in doc[page].get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    spans = line["spans"]
                    if spans and all("JetBrainsMono" in s["font"] and abs(s["size"]-11.5) < 0.01 for s in spans):
                        lines.append("".join(s["text"] for s in spans).strip())
        copied = []
        cursor = 0
        for block in blocks:
            expected = [line.strip() for line in block.splitlines() if line.strip()]
            start = next(i for i in range(cursor, len(lines)) if lines[i] == expected[0])
            actual = lines[start:start+len(expected)]
            if actual != expected:
                raise RuntimeError("PDF code lines differ from Markdown: " + repr((expected, actual)))
            copied.append("\n".join(actual))
            cursor = start + len(expected)
        blocks = copied
    source = (ROOT / "labs/part26-supply-chain-gate/policy.go").read_text(encoding="utf-8")
    support = source[source.index("type DefaultProvenanceVerifier struct"):source.index("// PolicyEngine enforces")]
    support += source[source.index("// VerifyProvenance delegates"):source.index("// Evaluate evaluates")]
    support += source[source.index("// ComputeContentDigest calculates"):]
    header = '''package supplychain
import (
    "context"
    "crypto/ecdsa"
    "crypto/sha256"
    "encoding/hex"
    "errors"
    "fmt"
    "regexp"
    "strings"
    "time"
)
var digestRegex = regexp.MustCompile(`^sha256:[a-f0-9]{64}$`)
type DefaultSignatureVerifier struct { TrustedIssuers []string }
'''
    temporary_root = ROOT / "tmp/agent1-excerpt-tests"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temporary_root) as folder:
        path = Path(folder)
        (path / "excerpt.go").write_text(header + "\n".join(blocks) + "\n" + support, encoding="utf-8")
        module = ROOT / "labs/part26-supply-chain-gate"
        shutil.copy2(module / "go.mod", path / "go.mod")
        for test in module.glob("*_test.go"):
            shutil.copy2(test, path / test.name)
        result = run([GO, "test", "-race", "-count=3", "-v", "./..."], path)
        result["markdown_sha256"] = digest(chapter)
        result["excerpt_sha256"] = digest(path / "excerpt.go")
        result["support_scope"] = "digestRegex; verifier structs; DefaultProvenanceVerifier; delegate VerifyProvenance; ComputeContentDigest"
        result["go_blocks"] = len(blocks)
        result["implementation_origin"] = "ACTUAL_PDF_CODE_SPANS" if from_pdf else "MARKDOWN_GO_FENCES"
        return result


def regression_demonstrations() -> list[dict]:
    """Run negative controls in disposable copies, never mutate the checkout."""
    results = []
    temporary_root = ROOT / "tmp/agent1-excerpt-tests"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temporary_root) as folder:
        path = Path(folder)
        original = run(["git", "show", BASELINE + ":labs/part2-values/main.go"])
        if original["exit_code"] != 0:
            return [original]
        (path / "main.go").write_text(original["stdout_utf8"], encoding="utf-8")
        for name in ["go.mod", "main_test.go"]:
            shutil.copy2(ROOT / "labs/part2-values" / name, path / name)
        result = run([GO, "test", "-run", "^TestRedactedCopyEmptyInput$", "-v"], path)
        result["classification"] = "EXPECTED_FAILURE"
        result["negative_control"] = "baseline redactedCopy with new empty-input contract test"
        result["expected_exit_code"] = 1
        result["failure_signature_present"] = "index out of range" in result["stdout_utf8"]
        results.append(result)
    with tempfile.TemporaryDirectory(dir=temporary_root) as folder:
        path = Path(folder)
        module = ROOT / "labs/part26-supply-chain-gate"
        for source in [*module.glob("*.go"), module / "go.mod"]:
            shutil.copy2(source, path / source.name)
        source = (path / "contract_examples.go").read_text(encoding="utf-8")
        guard = "\tif err == nil {\n\t\terr = timeoutCtx.Err()\n\t}\n"
        if source.count(guard) != 1:
            raise RuntimeError("negative-control guard must match exactly once")
        (path / "contract_examples.go").write_text(source.replace(guard, "", 1), encoding="utf-8")
        result = run([GO, "test", "-run", "^TestRemoteVerificationRejectsNilAfterCancellation$", "-v"], path)
        result["classification"] = "EXPECTED_FAILURE"
        result["negative_control"] = "remove post-callback cancellation check"
        result["expected_exit_code"] = 1
        result["failure_signature_present"] = "cancellation was turned into allow" in result["stdout_utf8"]
        results.append(result)
    # Change only the imported function in a child process. No checkout or
    # candidate is modified; this recreates the nested-keep orphan regression.
    mutant = f'''import inspect, sys, unittest
sys.path.insert(0, {str(ROOT / "scripts")!r})
import build_pdf, test_review_heading_contract
source = inspect.getsource(build_pdf.keep_headings_with_content)
guard = "                in {{'H1', 'H2', 'H3', 'body-intro'}}"
assert source.count(guard) == 1
exec(source.replace(guard, "                in {{'H1', 'H2', 'H3'}}", 1), build_pdf.__dict__)
unittest.main(module=test_review_heading_contract,
    argv=['negative-control', 'AnswerHeadingContract.test_heading_moves_with_intro_and_code_not_a_nested_keep', '-v'])
'''
    result = run([sys.executable, "-c", mutant])
    result["classification"] = "EXPECTED_FAILURE"
    result["negative_control"] = "remove heading-intro flattening in isolated Python process"
    result["expected_exit_code"] = 1
    result["failure_signature_present"] = "unexpectedly found" in result["stderr_utf8"]
    results.append(result)
    return results


def pdf_checkpoint() -> dict:
    import fitz
    current = fitz.open(ROOT / "Golang_Master.pdf")
    candidate = fitz.open(ROOT / "tmp/pdfs/Golang_Master.candidate.pdf")
    compact = lambda text: re.sub(r"\s+", "", unicodedata.normalize("NFC", text))
    toc = candidate.get_toc()
    bookmark_checks = []
    for _, title, page in toc:
        if title.startswith("Chương "):
            bookmark_checks.append({"title": title, "page": page,
                                    "heading_present": page > 2 and compact(title) in compact(candidate[page-1].get_text())})
    toc_lines = candidate[1].get_text().splitlines()
    toc_checks = []
    for i, line in enumerate(toc_lines):
        match = re.fullmatch(r"Chương (\d+)", line)
        if match and i + 2 < len(toc_lines) and toc_lines[i+2].isdigit():
            number = int(match.group(1))
            page = int(toc_lines[i+2])
            title = f"Chương {number} — {toc_lines[i+1]}"
            toc_checks.append({"number": number, "page": page,
                               "heading_present": page > 2 and compact(title) in compact(candidate[page-1].get_text())})
    def section_range(doc, prefix):
        outline = doc.get_toc()
        start = next(i for i, entry in enumerate(outline) if entry[1].startswith(prefix))
        begin = outline[start][2] - 1
        end = outline[start+1][2] - 1 if start+1 < len(outline) else len(doc)
        return range(begin, end)

    def section_text(doc, prefix):
        pages = section_range(doc, prefix)
        text = "\n".join(doc[p].get_text() for p in pages)
        # Layout-only normalization, NOT a code-byte integrity assertion.
        text = re.sub(r"(?m)^\d+\s*$", "", text)
        text = re.sub(r"(?m)^####\s+", "", text)
        return compact(text)

    def chapter_text(doc, number):
        return section_text(doc, f"Chương {number} —")

    unchanged = [{"chapter": n, "normalized_text_equal": chapter_text(current, n) == chapter_text(candidate, n)}
                 for n in range(1, 30) if n not in {2, 16, 26, 27}]
    other_sections = [{"section": prefix,
                       "normalized_text_equal": section_text(current, prefix) == section_text(candidate, prefix)}
                      for prefix in ["Trước khi viết dòng Go đầu tiên", "Mở cửa vào Go", "BACK MATTER", "PHỤ LỤC A"]]

    def image_inventory(doc):
        inventory = Counter()
        # Cover artwork is deliberately excluded: this build does not recreate
        # the separately promoted full-bleed cover. This is a reported limit.
        for page in range(2, len(doc)):
            for image in doc[page].get_images(full=True):
                inventory[image_pixels(doc.extract_image(image[0])["image"])] += 1
        return inventory

    def image_pixels(data):
        from PIL import Image
        with Image.open(BytesIO(data)) as image:
            rgb = image.convert("RGB")
            return hashlib.sha256(str(rgb.size).encode("ascii") + rgb.tobytes()).hexdigest()

    images_current = image_inventory(current)
    images_candidate = image_inventory(candidate)
    figure = "assets/diagrams/supply-chain-policy-evidence.png"
    before_pixels = image_pixels(subprocess.check_output(["git", "show", BASELINE + ":" + figure], cwd=ROOT))
    after_pixels = image_pixels((ROOT / figure).read_bytes())
    repair_matches = (images_current[before_pixels] == 1 and images_candidate[after_pixels] == 1)
    images_current.subtract({before_pixels: 1})
    images_candidate.subtract({after_pixels: 1})
    unchanged_images_equal = +images_current == +images_candidate
    code_checks = []
    for number, file in [(2, "02-gia-tri-slice-va-aliasing.md"),
                         (16, "16-thay-duoc-he-thong.md"),
                         (26, "26-chuoi-cung-ung-co-the-kiem-chung.md"),
                         (27, "27-quan-sat-linux-bang-ebpf-va-go.md")]:
        text = (ROOT / "book/chapters" / file).read_text(encoding="utf-8")
        blocks = re.findall(r"^~~~go\n(.*?)^~~~$", text, re.M | re.S)
        extracted = chapter_text(candidate, number)
        for index, block in enumerate(blocks):
            code_checks.append({"chapter": number, "go_block": index+1,
                                "tokens_present_in_order": compact(block) in extracted,
                                "raw_string_contains_literal_tab": any("\t" in literal for literal in re.findall(r"`([^`]*)`", block))})
    body = "\n".join(p.get_text() for p in candidate)
    return {
        "candidate_sha256": digest(ROOT / "tmp/pdfs/Golang_Master.candidate.pdf"),
        "pages": len(candidate), "bookmarks": bookmark_checks, "toc": toc_checks,
        "unchanged_chapter_text": unchanged, "changed_go_blocks": code_checks,
        "unchanged_front_chapters_and_atlases": other_sections,
        "body_raster_image_occurrences": {"baseline": sum(images_current.values())+1,
                                          "candidate": sum(images_candidate.values())+1,
                                          "unaffected_rgb_pixel_multiset_equal": unchanged_images_equal,
                                          "approved_figure_rgb_pixels_match": repair_matches,
                                          "repaired_asset": figure,
                                          "before_pixel_sha256": before_pixels,
                                          "after_pixel_sha256": after_pixels},
        "literal_h4_markers_remaining": "#### Gợi ý" in body,
        "corrected_idempotency_present": "lũy đẳng" in body,
        "removed_mistranslation_absent": "lũy thừa bất biến" not in body,
        "latest_verifier_explanation_present": "PTR_TO_MAP_VALUE_OR_NULL" in body,
        "note": "Automated scoped content checks; visual review and unreviewed material remain in report. No publication acceptance.",
    }


def main() -> int:
    started_at = datetime.now(timezone.utc).isoformat()
    os.environ["GOTOOLCHAIN"] = "local"
    os.environ["CGO_ENABLED"] = "1"
    results = [run([GO, "version"]), run(
        [GO, "test", "-run", "^TestSliceDescriptorImplementationMeasurement$", "-v"],
        ROOT / "labs/part2-values",
    )]
    for module in [
        "labs/part2-values", "labs/part16-observability-evidence",
        "labs/part16-real-signals", "labs/part26-supply-chain-gate",
        "labs/part27-ebpf-observer", "labs/part10-resource-retention",
        "projects/opsprobe",
    ]:
        for args in [[GO, "test", "-race", "-count=3", "./..."], [GO, "vet", "./..."]]:
            result = run(args, ROOT / module)
            results.append(result)
            print(module, args[1], result["exit_code"], flush=True)
    excerpt = chapter26_excerpt_tests()
    results.append(excerpt)
    print("chapter26 printed excerpt", excerpt["exit_code"], flush=True)
    pdf_excerpt = chapter26_excerpt_tests(from_pdf=True)
    results.append(pdf_excerpt)
    print("chapter26 copied PDF code", pdf_excerpt["exit_code"], flush=True)
    results.extend(regression_demonstrations())
    for args in [
        ["git", "diff", "--check", BASELINE],
        ["git", "diff", "--cached", "--check"],
        [sys.executable, "scripts/validate_error_atlas.py"],
        [sys.executable, "scripts/validate_manuscript_diagrams.py"],
        [sys.executable, "scripts/validate_main_manuscript_no_bullets.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py", "-v"],
    ]:
        result = run(args)
        results.append(result)
        print(args[-1], result["exit_code"], flush=True)
    # This validator's CLI may exit 0 on violations: inspect its actual result.
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_code_width
    violations = validate_code_width.validate_all_code_blocks()
    artifacts = []
    import fitz
    for label, name in [
        ("A", "book/publication/Golang_Master_baseline_f2211520.pdf"),
        ("B", "book/print_ready/02_RUOT_SACH_GOLANG_525TRANG_A4.pdf"),
        ("C", "Golang_Master.pdf"),
        ("candidate", "tmp/pdfs/Golang_Master.candidate.pdf"),
    ]:
        path = ROOT / name
        if path.exists():
            with fitz.open(path) as doc:
                artifacts.append({"label": label, "file": name, "sha256": digest(path),
                                  "pages": len(doc), "bookmarks": doc.get_toc()})
    pdf_checks = pdf_checkpoint()
    evidence = {
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "CHECKPOINT_CH02_CH16_CH26_CH27_NOT_WHOLE_BOOK_ACCEPTANCE",
        "baseline_head": BASELINE,
        "tested_head_before_checkpoint_commit": run(["git", "rev-parse", "HEAD"])["stdout_utf8"].strip(),
        "tested_worktree_diff": run(["git", "diff", "--stat", BASELINE])["stdout_utf8"],
        "source_hashes": {str(p.relative_to(ROOT)): digest(p) for pattern in [
            "book/chapters/*.md", "labs/part2-values/*.go", "labs/part26-supply-chain-gate/*.go",
            "labs/part27-ebpf-observer/*.go", "labs/part16-observability-evidence/fixed/*.go",
            "labs/part16-real-signals/probeapi/*.go",
            "book/VIETNAMESE_TECH_TERMS.md", "scripts/build_pdf.py",
            "scripts/test_review_heading_contract.py",
            "book/evidence/agent1-scientific-review/verify.py",
            "assets/diagrams/supply-chain-policy-evidence.*", "assets/visual-manifest.json",
        ] for p in ROOT.glob(pattern)},
        "results": results, "code_width_violations": [str(v) for v in violations],
        "artifacts": artifacts,
        "visual_status": "MANUAL_REVIEW_IN_REVIEWER_REPORT_NOT_AUTOMATIC_PASS",
        "live_sigstore_slsa_govulncheck": "NOT_RUN",
        "live_linux_bpf_compile_load_attach": "NOT_RUN",
        "pdf_checkpoint": pdf_checks,
    }
    (OUT / "validation.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failures = [r for r in results if r["exit_code"] != r.get("expected_exit_code", 0)
                or r.get("failure_signature_present", True) is not True]
    pdf_failures = (
        len(pdf_checks["bookmarks"]) != 29 or len(pdf_checks["toc"]) != 29
        or any(not v["heading_present"] for group in ["bookmarks", "toc"] for v in pdf_checks[group])
        or any(not v["normalized_text_equal"] for v in pdf_checks["unchanged_chapter_text"])
        or any(not v["normalized_text_equal"] for v in pdf_checks["unchanged_front_chapters_and_atlases"])
        or not pdf_checks["body_raster_image_occurrences"]["unaffected_rgb_pixel_multiset_equal"]
        or not pdf_checks["body_raster_image_occurrences"]["approved_figure_rgb_pixels_match"]
        or any(not v["tokens_present_in_order"] or v["raw_string_contains_literal_tab"] for v in pdf_checks["changed_go_blocks"])
        or pdf_checks["literal_h4_markers_remaining"]
        or not pdf_checks["latest_verifier_explanation_present"]
        or not pdf_checks["removed_mistranslation_absent"]
    )
    print("failures", len(failures), "code_width_violations", len(violations))
    for failure in failures:
        print(failure["stdout_utf8"], failure["stderr_utf8"])
    print("pdf_scope_failures", bool(pdf_failures))
    return int(bool(failures or violations or pdf_failures))


if __name__ == "__main__":
    raise SystemExit(main())
