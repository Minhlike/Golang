"""Reproduce Ch17-19 checks; visual acceptance requires explicit observed pages."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from functools import cache
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
from checkpoint4 import chapter_pages

START = "61d506fb46279cf2d3bd6bf20715cb46329dbb59"
OLD_SHA = "c860f5ca012f0132da65a2b2d05404db1f814f45e25379309cce6851ed89c73c"
CHAPTERS = {17: "17-dong-goi-va-dieu-phoi.md", 18: "18-dua-thay-doi-ra-production.md", 19: "19-giu-type-information.md"}
FIGURES = ["container-cluster-observation", "reconciliation-loop"]
QA = ROOT / "tmp/pdfs/agent1-review/checkpoint6"
PDF = ROOT / "tmp/pdfs/Golang_Master.candidate.pdf"


def source(n):
    return (ROOT / "book/chapters" / CHAPTERS[n]).read_text(encoding="utf-8")


def blocks(n):
    text = "\n".join(re.sub(r"^> ?", "", line) for line in source(n).splitlines())
    return [(lang.strip(), body) for _, lang, body in re.findall(r"^(~~~|```)([^\n]*)\n(.*?)^\1[ \t]*$", text, re.M | re.S)]


def excerpts(copied=None):
    bs = copied or {n: [body for lang, body in blocks(n) if lang == "go"] for n in CHAPTERS}
    results = []
    for n, module, filename in [(17, "part17-reconciliation-contract", "reconcile.go"), (18, "part18-promotion-evidence", "admission.go")]:
        original = ROOT / "labs" / module
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            path = Path(tmp)
            for f in [*original.glob("go.*"), *original.joinpath("fixed").glob("*_test.go")]:
                shutil.copy2(f, path / f.name)
            support = (original / "fixed" / filename).read_text(encoding="utf-8").split("type ", 1)[0]
            if n == 18:
                support += "func validDigest" + (original / "fixed" / filename).read_text(encoding="utf-8").split("func validDigest", 1)[1]
            (path / "excerpt.go").write_text(support + bs[n][0], encoding="utf-8")
            r = run([GO, "test", "-race", "-count=3", "-v", "./..."], path)
            r.update(chapter=n, classification="PASS" if r["exit_code"] == 0 else "FAIL", support="unchanged lab imports and tests; implementation is printed fence", source_origin="PDF_LINES" if copied else "MARKDOWN_FENCES", compiled_source_sha256=digest(path / "excerpt.go"))
            results.append(r)
    # The Ch19 fences mix declarations and statements. Wrap statements explicitly;
    # the intentional assignment error is compiled separately, never called PASS.
    b = bs[19]
    with tempfile.TemporaryDirectory(dir=QA) as tmp:
        path = Path(tmp)
        shutil.copy2(ROOT / "labs/part19-type-information/go.mod", path / "go.mod")
        text = 'package fixed\nimport("context";"fmt";"math";"testing")\n' + b[0] + "\n"
        for index, split in [(1, "names :="), (2, "slowest :="), (4, "ports :="), (5, "labels :=")]:
            part = b[index]
            # Unique has both names/ports statements: retain as an executable test.
            if index == 1 and split not in part:
                split = "ports :="
            declarations, statements = part.split(split, 1)
            text += declarations + f"\nfunc TestPrinted{index}(t *testing.T) {{\n" + split + statements + "\n"
            name = {1: "names" if split == "names :=" else "ports", 2: "slowest", 4: "ports", 5: "labels"}[index]
            # Consume every illustrative short variable without changing its value.
            vars_ = re.findall(r"(?m)^([A-Za-z]\w*) :=", split + statements)
            text += "\n".join("_ = " + x for x in vars_) + "\n}\n"
        text += b[6] + "\n" + b[7] + "\n" + b[8].split("var problem", 1)[0] + "\n" + b[9]
        text += '''
func NewSet[T comparable](values ...T) Set[T] { s:=make(Set[T]); for _,v:=range values {s[v]=struct{}{}}; return s }
func TestPrintedMaxNaNOrder(t *testing.T) { n:=math.NaN(); if Max(n,1)!=1 || !math.IsNaN(Max(1,n)) {t.Fatal("NaN order")}}
func TestPrintedTypedNil(t *testing.T) { var p *ProbeError; var e error=p; if e==nil || checkTarget(true)==nil {t.Fatal("intentional typed nil bug was not reproduced")}}
'''
        for f in (ROOT / "labs/part19-type-information/fixed").glob("*_test.go"):
            shutil.copy2(f, path / f.name)
        (path / "excerpt_test.go").write_text(text, encoding="utf-8")
        r = run([GO, "test", "-race", "-count=3", "-v", "./..."], path)
        r.update(chapter=19, classification="PASS" if r["exit_code"] == 0 else "FAIL", source_origin="PDF_LINES" if copied else "MARKDOWN_FENCES", support="package/imports, statement wrappers, NewSet helper; declarations and algorithm bodies from fences", compiled_source_sha256=digest(path / "excerpt_test.go"))
        results.append(r)
        (path / "assignment_test.go").write_text("package fixed\n" + b[3].replace("slowest :=", "var slowest =") + "\n", encoding="utf-8")
        r = run([GO, "test", "./..."], path)
        r.update(classification="EXPECTED_FAILURE", expected_exit_code=1, failure_signature="as int64 value in variable declaration", failure_signature_present="as int64 value in variable declaration" in r["stderr_utf8"], source_origin="PDF_LINES" if copied else "MARKDOWN_FENCES")
        results.append(r)
    return results


def negative_control():
    with tempfile.TemporaryDirectory(dir=QA) as tmp:
        path = Path(tmp)
        module = ROOT / "labs/part19-type-information"
        for f in [*module.glob("go.*"), *module.joinpath("fixed").glob("*.go")]:
            shutil.copy2(f, path / f.name)
        target = path / "collection.go"
        text = target.read_text(encoding="utf-8")
        needle = "result := make([]T, 0, len(values))"
        if text.count(needle) != 1:
            raise RuntimeError("mutant target not unique")
        target.write_text(text.replace(needle, "result := values[:0] // MUTANT aliases input"), encoding="utf-8")
        r = run([GO, "test", "-run", "^TestUniqueAllocatesOuterSliceButDoesNotClonePointees$", "-v", "./..."], path)
        r.update(classification="EXPECTED_FAILURE", expected_exit_code=1, mutant="alias_output_slice", failure_signature_present="result outer slice aliases input" in r["stdout_utf8"])
        return r


def config_contracts():
    import yaml
    workflow = yaml.safe_load((ROOT / "labs/part18-workflow-delivery/workflows/delivery.yaml").read_text(encoding="utf-8"))
    steps = yaml.safe_load(blocks(18)[4][1])
    expected = workflow["jobs"]["verify"]["steps"]
    assert [s["uses"] for s in steps if "uses" in s] == [s["uses"] for s in expected if "uses" in s]
    gate = next(s for s in workflow["jobs"]["promote-production"]["steps"] if s.get("name", "").startswith("Evaluate Promotion"))
    assert gate["working-directory"] == "labs/part18-workflow-delivery"
    assert "go run ./cmd/promote-gate" in gate["run"]
    variables = (ROOT / "labs/part18-workflow-delivery/terraform/variables.tf").read_text(encoding="utf-8")
    ecr = re.search(r'"(\^\[a-z0-9\].*?\$)"', variables).group(1)
    role = re.search(r'"(\^\[A-Za-z0-9.*?\$)"', variables).group(1)
    valid_ecr = lambda s: 2 <= len(s) <= 256 and re.fullmatch(ecr, s) is not None
    for name in ["golang-master", "team/api", "a__b", "a.b", "a--b"]: assert valid_ecr(name), name
    for name in ["a", "team//api", "api-", "API", "_api", "a"*257]: assert not valid_ecr(name), name
    for name in ["deploy-production", "Deploy_1+=,.@-"]: assert re.fullmatch(role, name), name
    for name in ["team/api", "", "a"*65]: assert not re.fullmatch(role, name), name
    assert re.search(r"name\s*=\s*var\.deployer_role_name", (ROOT / "labs/part18-workflow-delivery/terraform/main.tf").read_text(encoding="utf-8"))
    print("YAML extracted steps match specimen; static ECR/IAM boundary cases PASS. NOT terraform validate or cloud integration.")


def manifest(doc=None, pages=()):
    path = ROOT / "assets/visual-manifest.json"
    m = json.loads(path.read_text(encoding="utf-8"))
    keys = ["review_status", "rendered_pdf_sha256", "rendered_page", "rendered_page_png_sha256", "visual_review_evidence", "source_sha256", "sha256", "minimum_printed_font_pt"]
    for name in FIGURES:
        x = next(x for x in m["assets"] if x["asset_id"] == name)
        x.setdefault("pre_checkpoint6_historical_review", {k: x[k] for k in keys if k in x})
        for k in keys:
            x.pop(k, None)
        h = hashlib.sha256((ROOT / x["source"]).read_text(encoding="utf-8").encode()).hexdigest()
        x.update(source_sha256=h, source_file_sha256=digest(ROOT / x["source"]), sha256=digest(ROOT / x["local_asset_path"]), semantic_sha256=h, semantics_reviewed=True, review_status="SOURCE_REVIEWED_RENDER_PENDING", semantic_repair_reason="R91: probe termination/readiness scope, actual Deployment observer; retries do not guarantee convergence", modifications="Scoped semantic repair; shared style unchanged; prior visual status not transferred")
        if doc is not None:
            png = (ROOT / x["local_asset_path"]).read_bytes()
            from PIL import Image
            def pixel(data):
                im = Image.open(BytesIO(data)).convert("RGB")
                return im.size, hashlib.sha256(im.tobytes()).hexdigest()
            matches = [p+1 for p in chapter_pages(doc, 17) for im in doc[p].get_images() if pixel(doc.extract_image(im[0])["image"]) == pixel(png)]
            if len(matches) != 1 or matches[0] not in pages:
                raise RuntimeError("figure not actually observed")
            p = matches[0]
            x.update(review_status="SOURCE_AND_RENDER_REVIEWED", rendered_pdf_sha256=digest(PDF), rendered_page=p, rendered_page_png_sha256=digest(QA / f"page-{p:03d}.png"), visual_review_evidence="book/AGENT1_SCIENTIFIC_REVIEW.md#checkpoint-6")
    path.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pdf_check():
    import pymupdf as fitz
    from PIL import Image
    import build_pdf
    old_path = ROOT / "tmp/pdfs/agent1-review/checkpoint5.pdf"
    if digest(old_path) != OLD_SHA:
        raise RuntimeError("baseline candidate changed")
    old, new = fitz.open(old_path), fitz.open(PDF)
    compact = lambda s: re.sub(r"\s+", "", unicodedata.normalize("NFC", s))
    @cache
    def body(doc, n):
        return compact("\n".join(doc[p].get_text(clip=fitz.Rect(0, 0, doc[p].rect.width, doc[p].rect.height-45)) for p in chapter_pages(doc, n)))
    render = lambda s: html.unescape(re.sub(r"<[^>]+>", "", build_pdf.inline(s, "JetBrainsMono")))
    result = {"sha256": digest(PDF), "pages": len(new), "unchanged_sections": {str(n): body(old,n)==body(new,n) for n in [*[n for n in range(1,30) if n not in CHAPTERS], "Trước khi viết dòng Go đầu tiên", "Mở cửa vào Go", "BACK MATTER", "PHỤ LỤC A"]}}
    result["bookmarks"] = [{"title":t,"page":p,"match":compact(t) in compact(new[p-1].get_text())} for _,t,p in new.get_toc() if t.startswith("Chương ")]
    result["toc"] = []; lines=new[1].get_text().splitlines()
    for i,line in enumerate(lines[:-2]):
        if re.fullmatch(r"Chương \d+",line) and lines[i+2].isdigit():
            p=int(lines[i+2]); t=f"Chương {int(line.split()[-1])} — "+lines[i+1]
            result["toc"].append({"title":t,"page":p,"match":compact(t) in compact(new[p-1].get_text())})
    copied, code, content = {}, [], []
    for n in CHAPTERS:
        pdf_lines = []
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
            actual=pdf_lines[start:start+len(expected)];cursor=start+len(expected)
            code.append({"chapter":n,"block":index,"language":lang,"expanded_indentation_equal":actual==expected})
            if lang=="go":copied[n].append("\n".join(actual))
        in_code=False
        for i,line in enumerate(source(n).splitlines(),1):
            line=re.sub(r"^> ?","",line)
            if line.startswith(("~~~","```")):in_code=not in_code;continue
            if line.startswith("@references"):break
            if in_code or not line.strip() or line.startswith(("<!--","![")):continue
            cells=line.strip().strip("|").split("|") if line.startswith("|") else [line]
            for cell in cells:
                cell=re.sub(r"^(?:#{1,4}\s+|@(?:table|figure)\s+)","",cell.strip())
                if cell and not re.fullmatch(r"[: -]+",cell):content.append({"chapter":n,"line":i,"present":compact(render(cell)) in body(new,n)})
    def pixels(data):
        im=Image.open(BytesIO(data)).convert("RGB")
        return hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
    inv=lambda d:Counter(pixels(d.extract_image(im[0])["image"]) for p in range(2,len(d)) for im in d[p].get_images(full=True))
    before,after=inv(old),inv(new); result["figures"]=[]
    for name in FIGURES:
        asset="assets/diagrams/"+name+".png"
        a=pixels(subprocess.check_output(["git","show",START+":"+asset],cwd=ROOT));b=pixels((ROOT/asset).read_bytes())
        result["figures"].append({"name":name,"old_count":before[a],"new_count":after[b]});before.subtract({a:1});after.subtract({b:1})
    result.update(unaffected_body_rasters_equal=+before==+after, code=code, content=content, scope_pages=sorted({2,*[p+1 for n in CHAPTERS for p in chapter_pages(new,n)]}), literal_code_fences=any(re.search(r"(?m)^\s*(?:~~~|```)",new[p].get_text()) for n in CHAPTERS for p in chapter_pages(new,n)))
    return result,copied


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("mode",choices=["prepare","tests","fixtures","config","pdf","review"]);parser.add_argument("--pages")
    args=parser.parse_args();QA.mkdir(parents=True,exist_ok=True)
    os.environ.update(GOTOOLCHAIN="local",GOWORK="off",CGO_ENABLED="1",PYTHONDONTWRITEBYTECODE="1")
    os.environ["PATH"]="D:/Golang/.tools/go1.27.1/bin;D:/DevTools/w64devkit/bin;"+os.environ["PATH"]
    sys.path.insert(0,str(ROOT/"scripts"))
    if args.mode=="prepare":manifest();return 0
    path=OUT/"validation.json";d=json.loads(path.read_text(encoding="utf-8"))
    old=json.loads(subprocess.check_output(["git","show",START+":book/evidence/agent1-scientific-review/validation.json"],cwd=ROOT))
    if {k:v for k,v in d.items() if k!="checkpoint6"}!=old:raise RuntimeError("historical evidence changed")
    c=d.setdefault("checkpoint6",{"starting_head":START,"scope":"CH17_CH18_CH19_ONLY"})
    if args.mode=="tests":
        if "results" in c:raise RuntimeError("do not overwrite prior test evidence")
        rs=[run([GO,"version"])]
        for module in ["part17-reconciliation-contract","part17-container-kubernetes/client-observer","part18-promotion-evidence","part18-workflow-delivery","part19-type-information","part16-real-signals"]:
            for command in [[GO,"test","-race","-count=3","-timeout=180s","-v","./..."],[GO,"vet","./..."]]:
                r=run(command,ROOT/"labs"/module);rs.append(r);print(module,command[1],r["exit_code"],flush=True)
        rs.extend(excerpts());rs.append(negative_control())
        r=run([GO,"test","-tags","typednilexercise","./typednil"],ROOT/"labs/part19-type-information")
        r.update(classification="EXPECTED_FAILURE",expected_exit_code=1,failure_signature_present="want nil" in r["stdout_utf8"]);rs.append(r)
        for name in ["validate_visual_manifest","validate_diagram_encoding","validate_diagram_semantics","validate_error_atlas","validate_main_manuscript_no_bullets","validate_manuscript_diagrams"]:rs.append(run([sys.executable,"scripts/"+name+".py"]))
        c["results"]=rs
        c["real_tools"]={name:{"classification":"NOT_RUN","executable_found":shutil.which(name)} for name in ["docker","kubectl","kind","terraform","aws"]}
    elif args.mode=="fixtures":
        c.setdefault("superseded_harness_results",[]).append({"results":c["results"][13:17],"reason":"Omitted validDigest support and misclassified intentional typed-nil demonstration; no product failure hidden"})
        c["results"][13:17]=excerpts()
    elif args.mode=="config":
        if c.get("configuration_results"):
            c.setdefault("superseded_configuration_results",[]).append(c["configuration_results"])
        c["configuration_results"]=[run([sys.executable,"-c","import sys;sys.path.insert(0,'book/evidence/agent1-scientific-review');from checkpoint6 import config_contracts;config_contracts()"])]
        r=run([GO,"run","./labs/part18-workflow-delivery/cmd/promote-gate"],ROOT)
        r.update(classification="EXPECTED_FAILURE",expected_exit_code=1,failure_signature_present="go.mod file not found" in r["stderr_utf8"]);c["configuration_results"].append(r)
    elif args.mode=="pdf":
        if c.get("pdf") and c["pdf"]["sha256"] != digest(PDF):
            observed = sorted(set(map(int, args.pages.split(",")))) if args.pages else []
            c.setdefault("superseded_pdf_evidence",[]).append({"pdf":c["pdf"],"excerpt_results":c.get("pdf_excerpt_results",[]),"pages_actually_opened":observed,"page_png_sha256":{str(p):digest(QA/f"page-{p:03d}.png") for p in observed},"status":"INVALIDATED_FOR_FINAL_SHA"})
        c["pdf"],copied=pdf_check();c["pdf_excerpt_results"]=excerpts(copied);c["visual_status"]="NOT_REVIEWED_ON_THIS_SHA"
    else:
        import pymupdf as fitz
        if not args.pages:parser.error("review requires actual observed pages")
        pages=sorted(set(map(int,args.pages.split(","))));doc=fitz.open(PDF)
        if c["pdf"]["sha256"]!=digest(PDF):raise RuntimeError("PDF changed")
        if any(not (QA/f"page-{p:03d}.png").is_file() for p in pages):raise RuntimeError("missing page render")
        manifest(doc,pages)
        c["manual_visual_review"]={"pdf_sha256":digest(PDF),"pages_actually_opened":pages,"count":len(pages),"not_opened":len(doc)-len(pages),"page_png_sha256":{str(p):digest(QA/f"page-{p:03d}.png") for p in pages},"resolution":"Poppler144dpi/original individual pages","status":"SCOPED_ACTUAL_REVIEW_NOT_WHOLE_BOOK_ACCEPTANCE"}
        c["visual_status"]="SCOPED_ACTUAL_REVIEW_ONLY"
    c["diff_checks"]=[run(["git","diff","--check",START]),run(["git","diff","--cached","--check"])]
    import validate_code_width
    c["code_width_violations"]=validate_code_width.validate_all_code_blocks()
    c["source_hashes"]={p.relative_to(ROOT).as_posix():digest(p) for pattern in ["book/chapters/1[789]*.md","labs/part17*/**/*.go","labs/part18*/**/*","labs/part19*/**/*.go","book/evidence/agent1-scientific-review/checkpoint6.py"] for p in ROOT.glob(pattern) if p.is_file()}
    rs=[*c.get("results",[]),*c.get("configuration_results",[]),*c.get("pdf_excerpt_results",[]),*c["diff_checks"]]
    bad=[r for r in rs if r["exit_code"]!=r.get("expected_exit_code",0) or not r.get("failure_signature_present",True)]
    pdf=c.get("pdf");pdf_bad=pdf and (not all(pdf["unchanged_sections"].values()) or not pdf["unaffected_body_rasters_equal"] or pdf["literal_code_fences"] or len(pdf["toc"])!=29 or len(pdf["bookmarks"])!=29 or any(not x["match"] for k in ["toc","bookmarks"] for x in pdf[k]) or any(not x["present"] for x in pdf["content"]) or any(not x["expanded_indentation_equal"] for x in pdf["code"]) or any(x["old_count"]!=1 or x["new_count"]!=1 for x in pdf["figures"]))
    c["automated_status"]="FAIL" if bad or pdf_bad or c["code_width_violations"] else "PASS"
    c["recorded_at_utc"]=datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for r in bad:print(r["command"],r["stdout_utf8"],r["stderr_utf8"])
    print(json.dumps({"status":c["automated_status"],"failures":len(bad),"pdf_bad":pdf_bad,"width":c["code_width_violations"],"pages":pdf and pdf["pages"],"scope_pages":pdf and pdf["scope_pages"]}))
    return int(c["automated_status"]!="PASS")


if __name__=="__main__":raise SystemExit(main())
