"""Reproduce the scoped Ch11-13 checkpoint; never infer visual acceptance."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
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

from verify import ROOT, OUT, GO, digest, run

START = "62ce1f8dcd32ecd4a1408f1aabfd0ce25fb8844c"
OLD_SHA = "4345ad76f9ec7d99dd990366c6accf01bbeaca47b1cfc58e5d20429254478d91"
CHAPTERS = {11: "11-mot-request-thuc-su-di-dau.md", 12: "12-mot-service-song-va-tat-the-nao.md", 13: "13-mot-thay-doi-hoac-khong-co-gi.md"}
FIGURES = {11: "http-client-request-path", 12: "http-service-lifecycle", 13: "transaction-boundary"}
QA = ROOT / "tmp/pdfs/agent1-review/checkpoint4"
PDF = ROOT / "tmp/pdfs/Golang_Master.candidate.pdf"


def source(n):
    return (ROOT / "book/chapters" / CHAPTERS[n]).read_text(encoding="utf-8")


def blocks(n):
    # Include intended quoted fences too; do not hide them from fidelity checks.
    text = "\n".join(re.sub(r"^> ?", "", line) for line in source(n).splitlines())
    return [(lang.strip(), body) for _, lang, body in re.findall(r"^(~~~|```)([^\n]*)\n(.*?)^\1[ \t]*$", text, re.M | re.S)]


def history():
    d = json.loads((OUT / "validation.json").read_text(encoding="utf-8"))
    old = json.loads(subprocess.check_output(["git", "show", START + ":book/evidence/agent1-scientific-review/validation.json"], cwd=ROOT))
    if {k: v for k, v in d.items() if k != "checkpoint4"} != old:
        raise RuntimeError("prior evidence changed")
    return d


def save(d):
    (OUT / "validation.json").write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def manifest(reviewed=None):
    p = ROOT / "assets/visual-manifest.json"
    m = json.loads(p.read_text(encoding="utf-8"))
    reasons = {11: "R56/R57: direct HTTP/1 path, optional DNS and no guaranteed socket reuse.",
               12: "R59: shutdown context failure does not complete handlers or reclaim DB/logger; callback is not a join.",
               13: "R63: match action column; distinguish successful commit, pre-commit rollback and ambiguous commit error."}
    for x in m["assets"]:
        if x["asset_id"] not in FIGURES.values():
            continue
        n = next(n for n, name in FIGURES.items() if name == x["asset_id"])
        keys = ["review_status", "rendered_pdf_sha256", "rendered_page", "rendered_page_png_sha256", "visual_review_evidence", "source_sha256", "sha256", "minimum_printed_font_pt"]
        if "pre_checkpoint4_historical_review" not in x:
            x["pre_checkpoint4_historical_review"] = {k: x[k] for k in keys if k in x}
        for k in keys:
            x.pop(k, None)
        sh = hashlib.sha256((ROOT / x["source"]).read_text(encoding="utf-8").encode()).hexdigest()
        x.update(source_sha256=sh, source_file_sha256=digest(ROOT / x["source"]), sha256=digest(ROOT / x["local_asset_path"]),
                 semantic_sha256=sh, semantics_reviewed=True, semantic_repair_reason=reasons[n],
                 review_status="SOURCE_REVIEWED_RENDER_PENDING", style_source="assets/diagrams/publication-flow.iuml",
                 style_sha256=hashlib.sha256((ROOT / "assets/diagrams/publication-flow.iuml").read_text(encoding="utf-8").encode()).hexdigest(),
                 caption_vi=next(line[8:] for line in source(n).splitlines() if line.startswith("@figure ")),
                 modifications="Checkpoint4 scoped scientific repair; shared style unchanged; historical visual acceptance not transferred.")
        if reviewed:
            doc = reviewed["doc"]
            occurrences = [p+1 for p in chapter_pages(doc, n) if doc[p].get_images()]
            if len(occurrences) != 1 or occurrences[0] not in reviewed["pages"]:
                raise RuntimeError("figure page not actually opened")
            page = occurrences[0]
            x.update(review_status="SOURCE_AND_RENDER_REVIEWED", rendered_pdf_sha256=digest(PDF), rendered_page=page,
                     rendered_page_png_sha256=digest(QA / f"page-{page:03d}.png"),
                     visual_review_evidence="book/AGENT1_SCIENTIFIC_REVIEW.md#checkpoint-4")
    p.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def excerpts(copied=None):
    b = copied or {n: [text for lang, text in blocks(n) if lang == "go"] for n in CHAPTERS}
    records = []
    with tempfile.TemporaryDirectory(dir=QA) as tmp:
        for n, module in [(12, "part12-service-lifecycle"), (13, "part13-transaction-boundary")]:
            folder = Path(tmp) / module
            folder.mkdir()
            original = ROOT / "labs" / module
            for file in [*original.glob("go.*"), *original.joinpath("fixed").glob("*_test.go")]:
                shutil.copy2(file, folder / file.name)
            if n == 12:
                text = (original / "fixed/server.go").read_text(encoding="utf-8")
                text = text[:text.index("func (a app) createCheck")] + b[12][6] + "\n" + text[text.index("func validateTarget"):]
                text = text[:text.index("func ServeUntilStopped")] + b[12][0] + "\n" + b[12][1]
            else:
                text = (original / "fixed/disable.go").read_text(encoding="utf-8")
                text = text[:text.index("func Disable")] + b[13][1]
            (folder / "excerpt.go").write_text(text, encoding="utf-8")
            r = run([GO, "test", "-race", "-count=3", "-timeout=90s", "-v", "./..."], folder)
            r.update(classification="PASS", chapter=n, source_origin="PDF_LINES" if copied else "MARKDOWN_FENCES",
                     support="imports/types/helpers and unchanged lab tests; printed function implementations replace originals",
                     compiled_source_sha256=digest(folder / "excerpt.go"))
            if copied:
                r["pdf_sha256"] = digest(PDF)
            records.append(r)
    return records


def controls():
    results = []
    cases = [(11, "part11-request-path", "fetch.go", "defer resp.Body.Close()", "// MUTANT omitted close", "TestFetchClosesBodyOnSuccessStatusAndReadFailure", "response body was not closed"),
             (12, "part12-service-lifecycle", "server.go", 'if err := decoder.Decode(&extra); !errors.Is(err, io.EOF) {', 'if false {', "TestJSONBoundaryDocumentsDuplicateCaseAndSizePolicy", "oversized body reached Store")]
    for n, module, filename, before, after, test, signature in cases:
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            path = Path(tmp)
            original = ROOT / "labs" / module
            for file in [*original.glob("go.*"), *original.joinpath("fixed").glob("*.go")]:
                shutil.copy2(file, path / file.name)
            file = path / filename
            text = file.read_text(encoding="utf-8")
            if text.count(before) != 1:
                raise RuntimeError("mutant target must be unique")
            text = text.replace(before, after)
            if n == 12:
                text = text.replace("var extra struct{}", "var extra struct{}; _ = extra")
                # io remains needed only by the removed statement in this fixture.
                text = text.replace('\n\t"io"', '')
            file.write_text(text, encoding="utf-8")
            r = run([GO, "test", "-race", "-count=1", "-timeout=30s", "-run", "^"+test+"$", "-v", "./..."], path)
            r.update(classification="EXPECTED_FAILURE", expected_exit_code=1,
                     failure_signature_present=signature in r["stdout_utf8"]+r["stderr_utf8"], mutation=before+" -> "+after)
            results.append(r)
    return results


def chapter_pages(doc, n):
    title = f"Chương {n} —" if isinstance(n, int) else n
    toc = doc.get_toc()
    i = next(i for i, (_, t, _) in enumerate(toc) if t.startswith(title))
    return range(toc[i][2]-1, toc[i+1][2]-1 if i+1 < len(toc) else len(doc))


def pdf_check():
    import pymupdf as fitz
    from PIL import Image
    import build_pdf
    old_path = ROOT / "tmp/pdfs/agent1-review/checkpoint3.pdf"
    if digest(old_path) != OLD_SHA:
        raise RuntimeError("checkpoint3 PDF changed")
    old, new = fitz.open(old_path), fitz.open(PDF)
    compact = lambda s: re.sub(r"\s+", "", unicodedata.normalize("NFC", s))
    body = lambda d, n: compact(re.sub(r"(?m)^\d+\s*$", "", "\n".join(d[p].get_text() for p in chapter_pages(d, n))))
    render = lambda s: html.unescape(re.sub(r"<[^>]+>", "", build_pdf.inline(s, "JetBrainsMono")))
    result = {"sha256": digest(PDF), "pages": len(new), "baseline_sha256": OLD_SHA,
              "unchanged_sections": {str(n): body(old,n)==body(new,n) for n in [*[n for n in range(1,30) if n not in CHAPTERS], "Trước khi viết dòng Go đầu tiên", "Mở cửa vào Go", "BACK MATTER", "PHỤ LỤC A"]}}
    result["bookmarks"] = [{"title": t, "page": p, "match": compact(t) in compact(new[p-1].get_text())} for _,t,p in new.get_toc() if t.startswith("Chương ")]
    result["toc"] = []
    lines = new[1].get_text().splitlines()
    for i, line in enumerate(lines[:-2]):
        if re.fullmatch(r"Chương \d+",line) and lines[i+2].isdigit():
            p = int(lines[i+2]); t = f"Chương {int(line.split()[-1])} — " + lines[i+1]
            result["toc"].append({"title":t,"page":p,"match":compact(t) in compact(new[p-1].get_text())})
    copied, code, content = {}, [], []
    for n in CHAPTERS:
        pdf_lines=[]
        for p in chapter_pages(new,n):
            for block in new[p].get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    spans=line["spans"]
                    if spans and all("JetBrainsMono" in s["font"] and abs(s["size"]-11.5)<.01 for s in spans):
                        pdf_lines.append("".join(s["text"] for s in spans))
        cursor=0; copied[n]=[]
        for index,(lang,text) in enumerate(blocks(n),1):
            expected=[line.expandtabs(4).rstrip() for line in text.splitlines() if line.strip()]
            start=next((i for i in range(cursor,len(pdf_lines)) if [x.strip() for x in pdf_lines[i:i+len(expected)]]==[x.strip() for x in expected]),None)
            if start is None: raise RuntimeError(f"PDF code mismatch Ch{n} block{index}")
            actual=pdf_lines[start:start+len(expected)]
            code.append({"chapter":n,"block":index,"language":lang,"characters_equal":True,"expanded_indentation_equal":actual==expected})
            if lang=="go": copied[n].append("\n".join(actual))
            cursor=start+len(expected)
        in_code=False
        for i,line in enumerate(source(n).splitlines(),1):
            line=re.sub(r"^> ?", "",line)
            if line.startswith(("~~~","```")): in_code=not in_code; continue
            if line.startswith("@references"): break
            if in_code or not line.strip() or line.startswith(("<!--","![")): continue
            cells=line.strip().strip("|").split("|") if line.startswith("|") else [line]
            for cell in cells:
                cell=re.sub(r"^(?:#{1,4}\s+|@(?:table|figure)\s+)","",cell.strip())
                if cell and not re.fullmatch(r"[: -]+",cell): content.append({"chapter":n,"line":i,"present":compact(render(cell)) in body(new,n)})
    result.update(code=code,content=content,copy_fidelity="Nonblank characters and expanded indentation; not tabs/blank lines/raw-byte preservation")
    def pixels(data):
        with Image.open(BytesIO(data)) as image:
            rgb=image.convert("RGB"); return hashlib.sha256(str(rgb.size).encode()+rgb.tobytes()).hexdigest()
    inv=lambda d: Counter(pixels(d.extract_image(im[0])["image"]) for p in range(2,len(d)) for im in d[p].get_images(full=True))
    before,after=inv(old),inv(new);result["figures"]=[]
    for n,name in FIGURES.items():
        asset="assets/diagrams/"+name+".png"
        a=pixels(subprocess.check_output(["git","show",START+":"+asset],cwd=ROOT));b=pixels((ROOT/asset).read_bytes())
        result["figures"].append({"name":name,"old_count":before[a],"new_count":after[b]})
        before.subtract({a:1});after.subtract({b:1})
    result["unaffected_body_rasters_equal"]=+before==+after
    result["literal_h4"]=any("#### Gợi ý" in new[p].get_text() for p in range(2,len(new)))
    result["scope_pages"]=sorted({2,*[p+1 for n in CHAPTERS for p in chapter_pages(new,n)]})
    result["literal_code_fences_in_scope"]=any(re.search(r"(?m)^\s*(?:~~~|```)",new[p-1].get_text()) for p in result["scope_pages"])
    return result,copied


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["prepare","tests","pdf","review"])
    parser.add_argument("--pages",help="explicit individual pages already opened and observed")
    args=parser.parse_args()
    os.environ.update(GOTOOLCHAIN="local",GOWORK="off",CGO_ENABLED="1",PYTHONDONTWRITEBYTECODE="1")
    os.environ["PATH"]="D:/Golang/.tools/go1.27.1/bin;D:/DevTools/w64devkit/bin;"+os.environ["PATH"]
    sys.path.insert(0,str(ROOT/"scripts")); QA.mkdir(parents=True,exist_ok=True)
    if args.mode=="prepare": manifest(); return 0
    d=history();c=d.setdefault("checkpoint4",{"starting_head":START,"started_at_utc":datetime.now(timezone.utc).isoformat(),"scope":"CH11_CH12_CH13_ONLY"})
    c.setdefault("initial_pdf_fidelity_rejection", {
        "pdf_sha256":"c53c9711687be52b4e965470983f25fc42eefd84dfb24b84ac2ca4dfda3ae956",
        "page":224,"classification":"ACTUAL_DEFECT_NOT_PASS",
        "observed_error":"PDF code mismatch Ch12 block6",
        "cause":"Quoted Markdown fences printed literally and code rendered as callout prose, not JetBrainsMono code",
        "repair":"Unquote only the three-line Ch12 prediction fence; renderer and code characters unchanged",
        "evidence_kind":"Manual summary of observed failed fidelity run and extracted page text; not raw stdout"
    })
    if args.mode=="tests":
        if "results" in c: raise RuntimeError("tests already recorded; no silent overwrite")
        records=[run([GO,"version"]),run([GO,"env","-json","GOOS","GOARCH","GOVERSION"])]
        for module in ["part11-request-path","part12-service-lifecycle","part13-transaction-boundary","part10-resource-retention"]:
            for command in [[GO,"test","-race","-count=3","-timeout=120s","-v","./..."],[GO,"vet","./..."]]:
                r=run(command,ROOT/"labs"/module); records.append(r);print(module,command[1],r["exit_code"],flush=True)
        records.extend(excerpts());records.extend(controls())
        for name in ["validate_visual_manifest","validate_diagram_encoding","validate_diagram_semantics","validate_error_atlas","validate_main_manuscript_no_bullets","validate_manuscript_diagrams"]:
            records.append(run([sys.executable,"scripts/"+name+".py"]))
        c["results"]=records
    elif args.mode=="pdf":
        pdf,copied=pdf_check()
        if c.get("pdf") and c["pdf"]["sha256"]!=pdf["sha256"]:
            c.setdefault("superseded_pdf_evidence",[]).append({"pdf":c["pdf"],"pdf_excerpt_results":c.get("pdf_excerpt_results",[]),
                "status":"AUTOMATED_CHECKS_ONLY_NOT_FINAL_VISUAL_ACCEPTANCE"})
        c["pdf"]=pdf;c["pdf_excerpt_results"]=excerpts(copied)
        c["visual_status"]="NOT_REVIEWED_ON_THIS_SHA"
    else:
        import pymupdf as fitz
        if not args.pages: parser.error("review needs actual observed page numbers")
        pages=sorted(set(int(p) for p in args.pages.split(",")))
        doc=fitz.open(PDF)
        if c["pdf"]["sha256"]!=digest(PDF): raise RuntimeError("tested PDF changed")
        if any(not 1<=p<=len(doc) or not (QA/f"page-{p:03d}.png").is_file() for p in pages): raise RuntimeError("missing page render")
        manifest({"doc":doc,"pages":pages})
        c["manual_visual_review"]={"pdf_sha256":digest(PDF),"pages_actually_opened":pages,"count":len(pages),"not_opened":len(doc)-len(pages),
            "page_png_sha256":{str(p):digest(QA/f"page-{p:03d}.png") for p in pages},"resolution":"Poppler144dpi, individual pages original resolution",
            "status":"SCOPED_ACTUAL_REVIEW_NOT_WHOLE_BOOK_ACCEPTANCE"}
        c["visual_status"]="SCOPED_ACTUAL_REVIEW_ONLY"
        c["finalization_results"]=[run([sys.executable,"scripts/"+name+".py"]) for name in ["validate_visual_manifest","validate_diagram_semantics"]]
    c["diff_checks"]=[run(["git","diff","--check",START]),run(["git","diff","--cached","--check"])]
    import validate_code_width
    c["code_width_violations"]=validate_code_width.validate_all_code_blocks()
    patterns=["book/chapters/*.md","labs/part11-request-path/**/*.go","labs/part12-service-lifecycle/**/*.go","labs/part13-transaction-boundary/**/*.go","scripts/build_pdf.py", "book/evidence/agent1-scientific-review/checkpoint4.py","assets/visual-manifest.json"]
    c["source_hashes"]={p.relative_to(ROOT).as_posix():digest(p) for pattern in patterns for p in ROOT.glob(pattern)}
    for name in FIGURES.values():
        for ext in ["puml","png"]: c["source_hashes"][f"assets/diagrams/{name}.{ext}"]=digest(ROOT/f"assets/diagrams/{name}.{ext}")
    goroot=Path(GO).parent.parent
    c["pinned_toolchain_sources"]={n:digest(goroot/"src"/n) for n in ["net/http/server.go","net/http/transport.go","net/http/client.go","net/http/request.go","net/http/httptrace/trace.go","database/sql/sql.go","database/sql/ctxutil.go","encoding/json/decode.go","context/context.go","crypto/tls/common.go","crypto/x509/verify.go","os/signal/signal.go"]}
    results=[*c.get("results",[]),*c.get("pdf_excerpt_results",[]),*c.get("finalization_results",[]),*c["diff_checks"]]
    bad=[r for r in results if r["exit_code"]!=r.get("expected_exit_code",0) or not r.get("failure_signature_present",True)]
    pdf=c.get("pdf")
    pdf_bad=pdf and (not all(pdf["unchanged_sections"].values()) or not pdf["unaffected_body_rasters_equal"] or pdf["literal_h4"] or pdf["literal_code_fences_in_scope"]
        or len(pdf["toc"])!=29 or len(pdf["bookmarks"])!=29 or any(not x["match"] for k in ["toc","bookmarks"] for x in pdf[k])
        or any(not x["present"] for x in pdf["content"]) or any(not x["expanded_indentation_equal"] for x in pdf["code"])
        or any(x["old_count"]!=1 or x["new_count"]!=1 for x in pdf["figures"]))
    c["automated_status"]="FAIL" if bad or pdf_bad or c["code_width_violations"] else "PASS"
    c["recorded_at_utc"]=datetime.now(timezone.utc).isoformat()
    save(d)
    for r in bad: print(r["command"],r["stdout_utf8"],r["stderr_utf8"])
    print(json.dumps({"status":c["automated_status"],"failures":len(bad),"pdf_bad":pdf_bad,"width":c["code_width_violations"],"pages":pdf and pdf["pages"],"scope_pages":pdf and pdf["scope_pages"]}))
    return int(c["automated_status"]!="PASS")


if __name__=="__main__":
    raise SystemExit(main())
