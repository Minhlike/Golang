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
CHECKPOINT1 = "4a52a14eeeb07d0af31e9a47272ee833a1f2d6d8"
CHECKPOINT1_PDF_SHA256 = "de5c877c5bc88d2923f2103019bee26efe472935685c5d3483e91e784882e8e3"
CHECKPOINT2_CHAPTERS = {
    3: "03-mo-hinh-du-lieu-va-trach-nhiem-thay-doi.md",
    4: "04-bien-loi.md",
    5: "05-thiet-ke-package.md",
    6: "06-thay-doi-khong-so-hai.md",
    7: "07-du-lieu-di-vao-va-di-ra.md",
}
CHECKPOINT2_FIGURES = [
    "pointer-value-call", "pointer-pointee", "map-sharing", "method-receiver-trace",
    "interface-contract", "error-boundary-trace", "cancellation-cleanup-trace", "package-boundary-graph",
]
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


def pdf_checkpoint(checkpoint2: bool = False) -> dict:
    import fitz
    previous = ROOT / "tmp/pdfs/agent1-review/checkpoint1.pdf" if checkpoint2 else ROOT / "Golang_Master.pdf"
    if checkpoint2 and digest(previous) != CHECKPOINT1_PDF_SHA256:
        raise RuntimeError("checkpoint 1 PDF does not match the reviewed artifact")
    current = fitz.open(previous)
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

    changed = set(CHECKPOINT2_CHAPTERS) if checkpoint2 else {2, 16, 26, 27}
    unchanged = [{"chapter": n, "normalized_text_equal": chapter_text(current, n) == chapter_text(candidate, n)}
                 for n in range(1, 30) if n not in changed]
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
    all_images_equal = images_current == images_candidate
    full_image_counts = {"baseline": sum(images_current.values()), "candidate": sum(images_candidate.values())}
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
    checks = {
        "comparison_pdf": str(previous.relative_to(ROOT)),
        "comparison_pdf_sha256": digest(previous),
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
    if checkpoint2:
        import html
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_pdf
        code_checks = []
        content_checks = []
        for number, filename in CHECKPOINT2_CHAPTERS.items():
            source = (ROOT / "book/chapters" / filename).read_text(encoding="utf-8")
            blocks = re.findall(r"^(~~~|```)([^\n]*)\n(.*?)^\1[ \t]*$", source, re.M | re.S)
            pdf_lines = []
            for page in section_range(candidate, f"Chương {number} —"):
                for block in candidate[page].get_text("dict")["blocks"]:
                    for line in block.get("lines", []):
                        spans = line["spans"]
                        if spans and all("JetBrainsMono" in s["font"] and abs(s["size"]-11.5) < 0.01 for s in spans):
                            pdf_lines.append("".join(s["text"] for s in spans).strip())
            cursor = 0
            for index, (_, language, block) in enumerate(blocks):
                expected = [line.expandtabs(4).strip() for line in block.splitlines() if line.strip()]
                start = next((i for i in range(cursor, len(pdf_lines))
                              if pdf_lines[i:i+len(expected)] == expected), None)
                equal = start is not None
                if equal:
                    cursor = start + len(expected)
                code_checks.append({"chapter": number, "block": index+1, "language": language.strip(),
                                    "nonblank_lines": len(expected), "pdf_lines_equal_in_order": equal,
                                    "comparison": "exact nonblank line text; indentation expanded then stripped; internal spaces retained"})
            # Check every rendered prose/heading/caption line and every table
            # cell. References are intentionally omitted by the renderer.
            extracted = chapter_text(candidate, number)
            in_code = False
            in_references = False
            for line_number, line in enumerate(source.splitlines(), 1):
                if line.startswith(("~~~", "```")):
                    in_code = not in_code
                    continue
                if in_code or not line.strip():
                    continue
                if line.strip() == "@references":
                    in_references = True
                    continue
                if in_references:
                    continue
                if line.startswith("<!--") or line.strip() == "---" or line.startswith("!["):
                    continue
                cells = line.strip().strip("|").split("|") if line.startswith("|") else [line]
                for cell in cells:
                    cell = cell.strip()
                    if not cell or re.fullmatch(r"[: -]+", cell):
                        continue
                    cell = re.sub(r"^(?:#{1,4}\s+|@(?:table|figure)\s+|>\s+)", "", cell)
                    rendered = html.unescape(re.sub(r"<[^>]+>", "", build_pdf.inline(cell, "JetBrainsMono")))
                    content_checks.append({"chapter": number, "source_line": line_number,
                                           "kind": "table_cell" if line.startswith("|") else "prose_heading_caption",
                                           "normalized_text_present": compact(rendered) in extracted,
                                           "text": rendered})
        checks["changed_code_blocks"] = code_checks
        checks["changed_source_content"] = content_checks
        approved_repairs = []
        before_inventory = image_inventory(current)
        after_inventory = image_inventory(candidate)
        for name in CHECKPOINT2_FIGURES:
            filename = f"assets/diagrams/{name}.png"
            before = image_pixels(subprocess.check_output(["git", "show", CHECKPOINT1 + ":" + filename], cwd=ROOT))
            after = image_pixels((ROOT / filename).read_bytes())
            approved_repairs.append({"asset": filename, "before_rgb_sha256": before, "after_rgb_sha256": after,
                                     "baseline_occurrences": before_inventory[before], "candidate_occurrences": after_inventory[after],
                                     "approved_asset_pixels_present": before_inventory[before] == 1 and after_inventory[after] == 1})
            before_inventory.subtract({before: 1})
            after_inventory.subtract({after: 1})
        checks["unchanged_all_body_image_pixels"] = all_images_equal
        checks["approved_figure_repairs"] = approved_repairs
        checks["unaffected_body_image_pixels_equal"] = +before_inventory == +after_inventory
        checks["body_raster_image_occurrences"] = {
            **full_image_counts, "all_rgb_pixel_multiset_equal": all_images_equal,
            "cover_excluded": True, "new_figure_repair_in_checkpoint2": True,
        }
        checks["checkpoint1_scientific_fixes_preserved_by_chapter_parity"] = [2, 16, 26, 27]
    return checks


def checkpoint2_demonstrations() -> list[dict]:
    """New negative controls; retain the three checkpoint-1 controls above."""
    results = []
    temporary_root = ROOT / "tmp/agent1-excerpt-tests"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temporary_root) as folder:
        path = Path(folder)
        module = ROOT / "labs/part7-stream-boundaries"
        shutil.copytree(module, path, dirs_exist_ok=True)
        baseline = run(["git", "show", BASELINE + ":labs/part7-stream-boundaries/targets/bounded.go"])
        if baseline["exit_code"] != 0:
            raise RuntimeError("cannot retrieve baseline bounded reader")
        (path / "targets/bounded.go").write_text(baseline["stdout_utf8"], encoding="utf-8")
        result = run([GO, "test", "-run", "^TestReadBoundedRejectsUnrepresentableProbeBeforeReading$", "-v", "./targets"], path)
        result.update(classification="EXPECTED_FAILURE", expected_exit_code=1,
                      negative_control="baseline MaxInt64 branch must not bypass the bounded-read contract",
                      failure_signature_present="reads=1" in result["stdout_utf8"])
        results.append(result)
    with tempfile.TemporaryDirectory(dir=temporary_root) as folder:
        path = Path(folder)
        shutil.copytree(ROOT / "labs/part6-testable-command", path, dirs_exist_ok=True)
        config = path / "internal/config/config.go"
        source = config.read_text(encoding="utf-8")
        guard = 'if !found || raw == "" {'
        if source.count(guard) != 1:
            raise RuntimeError("constant-default mutant guard must match once")
        config.write_text(source.replace(guard, 'if !found || raw == "" || true {', 1), encoding="utf-8")
        result = run([GO, "test", "-run", "^FuzzLoadTargetsNeverReturnsInvalidTarget$", "-v", "./internal/config"], path)
        result.update(classification="PROPERTY_GAP_DEMONSTRATION",
                      negative_control="constant-default mutant passes the five validity-property seeds; this is NOT parser correctness")
        results.append(result)
        result = run([GO, "test", "-run", "^TestLoadTargetsUsesDefaultOrOverride$", "-v", "./internal/config"], path)
        result.update(classification="EXPECTED_FAILURE", expected_exit_code=1,
                      negative_control="same constant-default mutant fails the override mapping contract",
                      failure_signature_present="payments.internal" in result["stdout_utf8"] and "FAIL" in result["stdout_utf8"])
        results.append(result)
    return results


def checkpoint2_main() -> int:
    started_at = datetime.now(timezone.utc).isoformat()
    os.environ["GOTOOLCHAIN"] = "local"
    os.environ["CGO_ENABLED"] = "1"
    os.environ["GOWORK"] = "off"
    # Carry forward the committed historical evidence byte-for-byte as JSON
    # values; do not relabel its timestamps/measurements as a fresh test run.
    historical = run(["git", "show", CHECKPOINT1 + ":book/evidence/agent1-scientific-review/validation.json"])
    if historical["exit_code"] != 0:
        raise RuntimeError("cannot retrieve immutable checkpoint 1 evidence")
    evidence = json.loads(historical["stdout_utf8"])
    for result in evidence["results"]:
        for stream in ["stdout", "stderr"]:
            raw = base64.b64decode(result[stream + "_base64"], validate=True)
            if hashlib.sha256(raw).hexdigest() != result[stream + "_sha256"]:
                raise RuntimeError("historical raw output checksum mismatch")
    results = [run([GO, "version"])]
    for module in ["labs/part3-data-models", "labs/part4-error-boundaries",
                   "labs/part5-package-design", "labs/part5-package-refactor",
                   "labs/part6-testable-command", "labs/part6-race-detector",
                   "labs/part7-stream-boundaries", "labs/edition-contracts"]:
        for args in [[GO, "test", "-race", "-count=3", "-v", "./..."], [GO, "vet", "./..."]]:
            result = run(args, ROOT / module)
            results.append(result)
            print(module, args[1], result["exit_code"], flush=True)
    results.append(run([GO, "test", "-run", "^$", "-fuzz", "^FuzzLoadTargetsNeverReturnsInvalidTarget$",
                        "-fuzztime=2s", "-parallel=2", "./internal/config"], ROOT / "labs/part6-testable-command"))
    for args, module, signature in [
        ([GO, "test", "-tags", "exercise", "./..."], "labs/part5-package-refactor", "no required module provides package"),
        ([GO, "test", "-race", "-tags", "raceexercise", "./broken"], "labs/part6-race-detector", "WARNING: DATA RACE"),
    ]:
        result = run(args, ROOT / module)
        result.update(classification="EXPECTED_FAILURE", expected_exit_code=1,
                      negative_control="intentional unfinished/broken teaching fixture, not a passing implementation",
                      failure_signature_present=signature in result["stdout_utf8"] + result["stderr_utf8"])
        results.append(result)
    results.extend(regression_demonstrations())
    results.extend(checkpoint2_demonstrations())
    for args in [
        ["git", "diff", "--check", BASELINE], ["git", "diff", "--cached", "--check"],
        [sys.executable, "scripts/validate_error_atlas.py"],
        [sys.executable, "scripts/validate_manuscript_diagrams.py"],
        [sys.executable, "scripts/validate_diagram_encoding.py"],
        [sys.executable, "scripts/validate_diagram_semantics.py"],
        [sys.executable, "scripts/validate_main_manuscript_no_bullets.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py", "-v"],
    ]:
        result = run(args)
        results.append(result)
        print(args[-1], result["exit_code"], flush=True)
    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_code_width
    violations = validate_code_width.validate_all_code_blocks()
    pdf_checks = pdf_checkpoint(checkpoint2=True)
    source_hashes = {}
    for pattern in ["book/chapters/*.md", "labs/part3-data-models/**/*.go", "labs/part4-error-boundaries/**/*.go",
                    "labs/part5-package-design/**/*.go", "labs/part5-package-refactor/**/*.go",
                    "labs/part6-testable-command/**/*.go", "labs/part6-race-detector/**/*.go",
                    "labs/part7-stream-boundaries/**/*.go", "labs/edition-contracts/**/*.go",
                    "labs/part*/go.mod", "scripts/build_pdf.py", "scripts/test_review_heading_contract.py",
                    "book/evidence/agent1-scientific-review/verify.py", "assets/visual-manifest.json"]:
        for path in ROOT.glob(pattern):
            source_hashes[str(path.relative_to(ROOT))] = digest(path)
    for name in CHECKPOINT2_FIGURES:
        for extension in ["puml", "png"]:
            path = ROOT / f"assets/diagrams/{name}.{extension}"
            source_hashes[str(path.relative_to(ROOT))] = digest(path)
    evidence["checkpoint2"] = {
        "started_at_utc": started_at, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "CHECKPOINT_CH03_CH04_CH05_CH06_CH07_NOT_WHOLE_BOOK_ACCEPTANCE",
        "starting_head": CHECKPOINT1, "scientific_baseline_head": BASELINE,
        "tested_head_before_checkpoint_commit": run(["git", "rev-parse", "HEAD"])["stdout_utf8"].strip(),
        "historical_checkpoint1_evidence_values_preserved": True,
        "source_hashes": source_hashes, "results": results,
        "pinned_toolchain_source_hashes": {
            name: digest(Path(GO).parent.parent / "src" / name)
            for name in ["cmd/go/internal/load/pkg.go", "os/root.go", "os/file_posix.go",
                         "bufio/bufio.go", "io/io.go", "errors/wrap.go", "testing/testing.go"]
        },
        "code_width_violations": [str(v) for v in violations], "pdf_checkpoint": pdf_checks,
        "visual_status": "MANUAL_REVIEW_IN_REVIEWER_REPORT_NOT_AUTOMATIC_PASS",
        "live_paths": "CHECKPOINT1_NOT_RUN_LIMITATIONS_RETAINED",
    }
    (OUT / "validation.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failures = [r for r in results if r["exit_code"] != r.get("expected_exit_code", 0)
                or r.get("failure_signature_present", True) is not True]
    pdf_failures = (
        len(pdf_checks["bookmarks"]) != 29 or len(pdf_checks["toc"]) != 29
        or any(not v["heading_present"] for group in ["bookmarks", "toc"] for v in pdf_checks[group])
        or any(not v["normalized_text_equal"] for group in ["unchanged_chapter_text", "unchanged_front_chapters_and_atlases"] for v in pdf_checks[group])
        or not pdf_checks["unaffected_body_image_pixels_equal"]
        or any(not v["approved_asset_pixels_present"] for v in pdf_checks["approved_figure_repairs"])
        or any(not v["pdf_lines_equal_in_order"] for v in pdf_checks["changed_code_blocks"])
        or any(not v["normalized_text_present"] for v in pdf_checks["changed_source_content"])
        or pdf_checks["literal_h4_markers_remaining"]
    )
    print("failures", len(failures), "code_width_violations", len(violations), "pdf_scope_failures", pdf_failures)
    for failure in failures:
        print(failure["stdout_utf8"], failure["stderr_utf8"])
    for group, field in [("changed_code_blocks", "pdf_lines_equal_in_order"), ("changed_source_content", "normalized_text_present")]:
        for failure in pdf_checks[group]:
            if not failure[field]:
                print("PDF mismatch", failure)
    return int(bool(failures or violations or pdf_failures))


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
    if sys.argv[1:] == ["--checkpoint2"]:
        raise SystemExit(checkpoint2_main())
    if sys.argv[1:]:
        raise SystemExit("usage: verify.py [--checkpoint2]")
    raise SystemExit(main())
