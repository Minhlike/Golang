"""Scoped Ch14-15 evidence. Manual page review is never inferred by a script."""
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
from checkpoint4 import chapter_pages

START = "6db2c4a886c1fe90a83ef64b242ec5ddbb5fe15b"
OLD_SHA = "924112a24a9a5ed8239fde1e3335fba4b198dbaf17fdccf26fdf8e59acc239f5"
CHAPTERS = {14: "14-khi-kieu-tro-thanh-du-lieu.md", 15: "15-tu-incident-den-cong-cu.md"}
FIGURE = "incident-command-lifecycle"
QA = ROOT / "tmp/pdfs/agent1-review/checkpoint5"
PDF = ROOT / "tmp/pdfs/Golang_Master.candidate.pdf"


def source(n):
    return (ROOT / "book/chapters" / CHAPTERS[n]).read_text(encoding="utf-8")


def blocks(n):
    text = "\n".join(re.sub(r"^> ?", "", line) for line in source(n).splitlines())
    return [(lang.strip(), text) for _, lang, text in re.findall(r"^(~~~|```)([^\n]*)\n(.*?)^\1[ \t]*$", text, re.M | re.S)]


def manifest(doc=None, pages=()):
    path = ROOT / "assets/visual-manifest.json"
    m = json.loads(path.read_text(encoding="utf-8"))
    x = next(x for x in m["assets"] if x["asset_id"] == FIGURE)
    keys = ["review_status", "rendered_pdf_sha256", "rendered_page", "rendered_page_png_sha256", "visual_review_evidence", "source_sha256", "sha256", "minimum_printed_font_pt"]
    x.setdefault("pre_checkpoint5_historical_review", {k: x[k] for k in keys if k in x})
    for k in keys:
        x.pop(k, None)
    h = hashlib.sha256((ROOT / x["source"]).read_text(encoding="utf-8").encode()).hexdigest()
    x.update(source_sha256=h, source_file_sha256=digest(ROOT/x["source"]), sha256=digest(ROOT/x["local_asset_path"]),
             semantic_sha256=h, semantics_reviewed=True, semantic_repair_reason="R77: lab Spec/Result fields, bytes.Buffer capture, context classification policy and direct-process-only cancellation; no safe-streaming/tree/socket promise.",
             review_status="SOURCE_REVIEWED_RENDER_PENDING", style_source="assets/diagrams/publication-flow.iuml",
             style_sha256=hashlib.sha256((ROOT/"assets/diagrams/publication-flow.iuml").read_text(encoding="utf-8").encode()).hexdigest(),
             caption_vi=next(line[8:] for line in source(15).splitlines() if line.startswith("@figure ")),
             modifications="Checkpoint5 scoped semantic repair, shared style unchanged. Historical visual acceptance is not transferred.")
    if doc is not None:
        occurrences = [p+1 for p in chapter_pages(doc, 15) if doc[p].get_images()]
        if len(occurrences) != 1 or occurrences[0] not in pages:
            raise RuntimeError("figure page not actually opened")
        p = occurrences[0]
        x.update(review_status="SOURCE_AND_RENDER_REVIEWED", rendered_pdf_sha256=digest(PDF), rendered_page=p,
                 rendered_page_png_sha256=digest(QA/f"page-{p:03d}.png"), visual_review_evidence="book/AGENT1_SCIENTIFIC_REVIEW.md#checkpoint-5")
    path.write_text(json.dumps(m, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def excerpts(copied=None):
    b = copied or {n: [text for lang, text in blocks(n) if lang == "go"] for n in CHAPTERS}
    rs = []
    for n, module in [(14, "part14-reflection-boundary"), (15, "part15-incident-command")]:
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            path = Path(tmp)
            original = ROOT/"labs"/module
            for f in [*original.glob("go.*"), *original.joinpath("fixed").glob("*_test.go")]:
                shutil.copy2(f, path/f.name)
            if n == 14:
                text = (original/"fixed/apply.go").read_text(encoding="utf-8")
                text = text[:text.index("func ApplyEnv")] + b[n][4]
            else:
                text = (original/"fixed/run.go").read_text(encoding="utf-8")
                text = text[:text.index("type Spec struct")] + b[n][1]+"\n"+b[n][2]+"\n"+b[n][3]
                (path/"logging_test.go").write_text('''package fixed
import("bytes";"context";"errors";"log/slog";"strings";"testing";"time")
func logOutcome(logger *slog.Logger, spec Spec, result Result, err error) {
'''+b[n][4]+'''
}
func TestPrintedLoggerDoesNotPanicOnInvalidSpec(t *testing.T) {
 var out bytes.Buffer
 logger:=slog.New(slog.NewJSONHandler(&out,nil))
 spec:=Spec{}
 result,err:=Run(context.Background(),spec)
 logOutcome(logger,spec,result,err)
 if out.Len()!=0 {t.Fatalf("invalid spec was logged as completed: %s",out.String())}
 spec=helperSpec("fail",10*time.Second)
 result,err=Run(context.Background(),spec)
 logOutcome(logger,spec,result,err)
 if !strings.Contains(out.String(),`"ok":false`) || strings.Contains(out.String(),"dependency refused") {t.Fatalf("logging contract: %s",out.String())}
}
''', encoding="utf-8")
            (path/"excerpt.go").write_text(text, encoding="utf-8")
            r = run([GO,"test","-race","-count=3","-timeout=180s","-v","./..."], path)
            r.update(chapter=n, classification="PASS" if r["exit_code"]==0 else "FAIL", source_origin="PDF_LINES" if copied else "MARKDOWN_FENCES",
                     support="imports/types/helpers and unchanged lab tests; printed ApplyEnv or Spec/Result/Run plus logging snippet replace lab implementations", compiled_source_sha256=digest(path/"excerpt.go"))
            if n==15: r["compiled_logging_test_sha256"]=digest(path/"logging_test.go")
            if copied: r["pdf_sha256"]=digest(PDF)
            rs.append(r)
    return rs


def control():
    with tempfile.TemporaryDirectory(dir=QA) as tmp:
        path=Path(tmp); original=ROOT/"labs/part14-reflection-boundary"
        for f in [*original.glob("go.*"), *original.joinpath("fixed").glob("*.go")]: shutil.copy2(f,path/f.name)
        f=path/"apply.go"; text=f.read_text(encoding="utf-8")
        before="if field.Type != stringType {"; after="if field.Type.Kind() != reflect.String {"
        if text.count(before)!=1: raise RuntimeError("mutant target not unique")
        text=text.replace(before,after).replace("stringType := reflect.TypeFor[string]()","// MUTANT accepts named string types")
        f.write_text(text,encoding="utf-8")
        r=run([GO,"test","-count=1","-run","^TestApplyEnvRejectsNamedStringType$","-v","./..."],path)
        r.update(classification="EXPECTED_FAILURE",expected_exit_code=1,mutant="exact_type_to_kind",failure_signature="want ErrSchema",
                 failure_signature_present="want ErrSchema" in r["stdout_utf8"])
        return r


def pdf_check():
    import pymupdf as fitz
    from PIL import Image
    import build_pdf
    old_path=ROOT/"tmp/pdfs/agent1-review/checkpoint4.pdf"
    if digest(old_path)!=OLD_SHA: raise RuntimeError("checkpoint4 PDF changed")
    old,new=fitz.open(old_path),fitz.open(PDF)
    compact=lambda s: re.sub(r"\s+","",unicodedata.normalize("NFC",s))
    # Exclude the footer by geometry, not every numeric line: a table cell
    # containing only "0" is real content, not a page number.
    body=lambda d,n: compact("\n".join(d[p].get_text(clip=fitz.Rect(0,0,d[p].rect.width,d[p].rect.height-45)) for p in chapter_pages(d,n)))
    render=lambda s: html.unescape(re.sub(r"<[^>]+>","",build_pdf.inline(s,"JetBrainsMono")))
    result={"sha256":digest(PDF),"pages":len(new),"baseline_sha256":OLD_SHA,
            "unchanged_sections":{str(n):body(old,n)==body(new,n) for n in [*[n for n in range(1,30) if n not in CHAPTERS],"Trước khi viết dòng Go đầu tiên","Mở cửa vào Go","BACK MATTER","PHỤ LỤC A"]}}
    result["bookmarks"]=[{"title":t,"page":p,"match":compact(t) in compact(new[p-1].get_text())} for _,t,p in new.get_toc() if t.startswith("Chương ")]
    result["toc"]=[];lines=new[1].get_text().splitlines()
    for i,line in enumerate(lines[:-2]):
        if re.fullmatch(r"Chương \d+",line) and lines[i+2].isdigit():
            p=int(lines[i+2]);t=f"Chương {int(line.split()[-1])} — "+lines[i+1]
            result["toc"].append({"title":t,"page":p,"match":compact(t) in compact(new[p-1].get_text())})
    copied,code,content={},[],[]
    for n in CHAPTERS:
        pdf_lines=[]
        for p in chapter_pages(new,n):
            for block in new[p].get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    spans=line["spans"]
                    if spans and all("JetBrainsMono" in s["font"] and abs(s["size"]-11.5)<.01 for s in spans): pdf_lines.append("".join(s["text"] for s in spans))
        cursor=0;copied[n]=[]
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
            line=re.sub(r"^> ?","",line)
            if line.startswith(("~~~","```")): in_code=not in_code;continue
            if line.startswith("@references"): break
            if in_code or not line.strip() or line.startswith(("<!--","![")): continue
            cells=line.strip().strip("|").split("|") if line.startswith("|") else [line]
            for cell in cells:
                cell=re.sub(r"^(?:#{1,4}\s+|@(?:table|figure)\s+)","",cell.strip())
                if cell and not re.fullmatch(r"[: -]+",cell): content.append({"chapter":n,"line":i,"present":compact(render(cell)) in body(new,n)})
    result.update(code=code,content=content,copy_fidelity="Nonblank characters and expanded indentation; not tabs/blank lines/raw-byte preservation")
    def pixels(data):
        with Image.open(BytesIO(data)) as im:
            rgb=im.convert("RGB");return hashlib.sha256(str(rgb.size).encode()+rgb.tobytes()).hexdigest()
    inv=lambda d:Counter(pixels(d.extract_image(im[0])["image"]) for p in range(2,len(d)) for im in d[p].get_images(full=True))
    before,after=inv(old),inv(new);asset="assets/diagrams/"+FIGURE+".png"
    a=pixels(subprocess.check_output(["git","show",START+":"+asset],cwd=ROOT));b=pixels((ROOT/asset).read_bytes())
    result["figure"]={"name":FIGURE,"old_count":before[a],"new_count":after[b]};before.subtract({a:1});after.subtract({b:1})
    result["unaffected_body_rasters_equal"]=+before==+after
    result["scope_pages"]=sorted({2,*[p+1 for n in CHAPTERS for p in chapter_pages(new,n)]})
    result["literal_h4"]=any("#### Gợi ý" in new[p].get_text() for p in range(2,len(new)))
    result["literal_code_fences_in_scope"]=any(re.search(r"(?m)^\s*(?:~~~|```)",new[p-1].get_text()) for p in result["scope_pages"])
    return result,copied


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("mode",choices=["prepare","tests","pdf","review"]);parser.add_argument("--pages")
    args=parser.parse_args();QA.mkdir(parents=True,exist_ok=True)
    os.environ.update(GOTOOLCHAIN="local",GOWORK="off",CGO_ENABLED="1",PYTHONDONTWRITEBYTECODE="1")
    os.environ["PATH"]="D:/Golang/.tools/go1.27.1/bin;D:/DevTools/w64devkit/bin;"+os.environ["PATH"]
    sys.path.insert(0,str(ROOT/"scripts"))
    if args.mode=="prepare": manifest();return 0
    path=OUT/"validation.json";d=json.loads(path.read_text(encoding="utf-8"))
    old=json.loads(subprocess.check_output(["git","show",START+":book/evidence/agent1-scientific-review/validation.json"],cwd=ROOT))
    if {k:v for k,v in d.items() if k!="checkpoint5"}!=old: raise RuntimeError("historical evidence changed")
    c=d.setdefault("checkpoint5",{"starting_head":START,"scope":"CH14_CH15_ONLY","started_at_utc":datetime.now(timezone.utc).isoformat()})
    if args.mode=="tests":
        if "results" in c: raise RuntimeError("tests already recorded; do not overwrite historical measurements")
        rs=[run([GO,"version"]),run([GO,"env","-json","GOOS","GOARCH","GOVERSION"])]
        for module,target in [("part14-reflection-boundary","./..."),("part15-incident-command","./..."),("edition-contracts","./interop"),("part10-resource-retention","./...")]:
            for command in [[GO,"test","-race","-count=3","-timeout=180s","-v",target],[GO,"vet",target]]:
                r=run(command,ROOT/"labs"/module);rs.append(r);print(module,command[1],r["exit_code"],flush=True)
        rs.extend(excerpts());rs.append(control())
        for name in ["validate_visual_manifest","validate_diagram_encoding","validate_diagram_semantics","validate_error_atlas","validate_main_manuscript_no_bullets","validate_manuscript_diagrams"]: rs.append(run([sys.executable,"scripts/"+name+".py"]))
        c["results"]=rs
    elif args.mode=="pdf":
        pdf,copied=pdf_check()
        if c.get("pdf") and (c["pdf"]["sha256"]!=pdf["sha256"] or any(not x["present"] for x in c["pdf"]["content"])):
            c.setdefault("superseded_pdf_evidence",[]).append({"pdf":c["pdf"],"pdf_excerpt_results":c.get("pdf_excerpt_results",[]),"status":"NOT_FINAL_VISUAL_ACCEPTANCE"})
        c["pdf"]=pdf;c["pdf_excerpt_results"]=excerpts(copied);c["visual_status"]="NOT_REVIEWED_ON_THIS_SHA"
    else:
        import pymupdf as fitz
        if not args.pages: parser.error("review requires explicit pages already opened and observed")
        pages=sorted(set(map(int,args.pages.split(","))));doc=fitz.open(PDF)
        if c["pdf"]["sha256"]!=digest(PDF): raise RuntimeError("tested PDF changed")
        if any(not 1<=p<=len(doc) or not (QA/f"page-{p:03d}.png").is_file() for p in pages): raise RuntimeError("missing page render")
        manifest(doc,pages)
        c["manual_visual_review"]={"pdf_sha256":digest(PDF),"pages_actually_opened":pages,"count":len(pages),"not_opened":len(doc)-len(pages),"page_png_sha256":{str(p):digest(QA/f"page-{p:03d}.png") for p in pages},"resolution":"Poppler144dpi, original resolution, individual pages","status":"SCOPED_ACTUAL_REVIEW_NOT_WHOLE_BOOK_ACCEPTANCE"}
        c["visual_status"]="SCOPED_ACTUAL_REVIEW_ONLY"
        c["finalization_results"]=[run([sys.executable,"scripts/"+name+".py"]) for name in ["validate_visual_manifest","validate_diagram_semantics"]]
    c["diff_checks"]=[run(["git","diff","--check",START]),run(["git","diff","--cached","--check"])]
    import validate_code_width
    c["code_width_violations"]=validate_code_width.validate_all_code_blocks()
    goroot=Path(GO).parent.parent
    names=["reflect/value.go","reflect/type.go","unsafe/unsafe.go","os/exec/exec.go","os/exec/lp_windows.go","os/exec/lp_unix.go","os/exec/exec_windows.go","os/exec/exec_posix.go","runtime/stack.go","runtime/mgc.go","runtime/mfinal.go","runtime/pinner.go","runtime/cgo/handle.go","cmd/cgo/doc.go"]
    c["pinned_toolchain_sources"]={n:digest(goroot/"src"/n) for n in names if (goroot/"src"/n).is_file()}
    fields=[line.strip() for line in (goroot/"src/reflect/value.go").read_text(encoding="utf-8").split("type Value struct {",1)[1].split("\n}",1)[0].splitlines() if line.strip() and not line.strip().startswith("//")]
    printed=[line.strip() for line in blocks(14)[1][1].splitlines()[1:-1]]
    c["pinned_value_declaration_match"]={"match":fields==printed,"fields":fields,"printed":printed,"not_public_API":True}
    patterns=["book/chapters/*.md","labs/part14-reflection-boundary/**/*.go","labs/part15-incident-command/**/*.go","labs/edition-contracts/interop/*.go","scripts/build_pdf.py","book/evidence/agent1-scientific-review/checkpoint5.py","assets/visual-manifest.json","assets/diagrams/publication-flow.iuml","assets/diagrams/incident-command-lifecycle.*"]
    c["source_hashes"]={p.relative_to(ROOT).as_posix():digest(p) for pattern in patterns for p in ROOT.glob(pattern)}
    rs=[*c.get("results",[]),*c.get("pdf_excerpt_results",[]),*c.get("finalization_results",[]),*c["diff_checks"]]
    bad=[r for r in rs if r["exit_code"]!=r.get("expected_exit_code",0) or not r.get("failure_signature_present",True)]
    pdf=c.get("pdf");pdf_bad=pdf and (not all(pdf["unchanged_sections"].values()) or not pdf["unaffected_body_rasters_equal"] or pdf["literal_h4"] or pdf["literal_code_fences_in_scope"] or len(pdf["toc"])!=29 or len(pdf["bookmarks"])!=29 or any(not x["match"] for k in ["toc","bookmarks"] for x in pdf[k]) or any(not x["present"] for x in pdf["content"]) or any(not x["expanded_indentation_equal"] for x in pdf["code"]) or any(pdf["figure"][k]!=1 for k in ["old_count","new_count"]))
    c["automated_status"]="FAIL" if bad or pdf_bad or c["code_width_violations"] or fields!=printed else "PASS"
    c["recorded_at_utc"]=datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for r in bad: print(r["command"],r["stdout_utf8"],r["stderr_utf8"])
    print(json.dumps({"status":c["automated_status"],"failures":len(bad),"pdf_bad":pdf_bad,"width":c["code_width_violations"],"pages":pdf and pdf["pages"],"scope_pages":pdf and pdf["scope_pages"]}))
    return int(c["automated_status"]!="PASS")


if __name__=="__main__": raise SystemExit(main())
