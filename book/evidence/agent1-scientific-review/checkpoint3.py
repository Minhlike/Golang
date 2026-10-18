"""Reproduce Ch08-10 and R33 checks without rerunning or rewriting older evidence."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
import html
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

START = "101bbc23397cc06f9efbd34d5bfc12b3af4a4f1c"
OLD_PDF = "9624349b5763aa8804a2454cc741f5e12bcde84152c34c037e7a62cbec1c978c"
CHAPTERS = {
    8: "08-mot-race-bat-dau-tu-dau.md",
    9: "09-dong-cong-viec-co-ap-suat.md",
    10: "10-khi-chuong-trinh-cham-hoac-phinh.md",
}
FIGURES = ["waitgroup-completion-proof", "channel-work-lifecycle", "performance-evidence-path"]
QA = ROOT / "tmp/pdfs/agent1-review/checkpoint3"


def blocks(number):
    source = (ROOT / "book/chapters" / CHAPTERS[number]).read_text(encoding="utf-8")
    return [(language.strip(), body) for _, language, body in re.findall(
        r"^(~~~|```)([^\n]*)\n(.*?)^\1[ \t]*$", source, re.M | re.S)]


def excerpt_tests(copied=None):
    """Only support wrappers are supplied. Executable statement text is not substituted."""
    results = []
    original = {n: [b for language, b in blocks(n) if language == "go"] for n in CHAPTERS}
    code = copied or original
    QA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=QA) as temporary:
        base = Path(temporary)

        def case(name, body, support_test, imports, classification="PASS", signature=None, command=None):
            path = base / name
            path.mkdir()
            (path / "go.mod").write_text("module example.com/excerpt\n\ngo 1.27.1\n", encoding="utf-8")
            source = 'package excerpt\nimport (' + imports + ')\n' + body
            (path / "excerpt.go").write_text(source, encoding="utf-8")
            (path / "excerpt_test.go").write_text(support_test, encoding="utf-8")
            result = run(command or [GO, "test", "-race", "-count=3", "-v", "./..."], path)
            result.update(name=name, classification=classification, source_sha256=digest(path / "excerpt.go"),
                          implementation_origin="PDF_EXTRACTED_LINES" if copied else "ACTUAL_MARKDOWN_FENCES",
                          support_disclosed="package/imports, omitted types, function boundary and test harness only; benchmark uses separately disclosed lab Render")
            if copied:
                result["source_pdf_sha256"]=digest(ROOT/"tmp/pdfs/Golang_Master.candidate.pdf")
            if classification == "EXPECTED_FAILURE":
                result.update(expected_exit_code=1, failure_signature_present=signature in result["stdout_utf8"] + result["stderr_utf8"])
            results.append(result)

        # Broken original publication is run exactly as printed, in a bounded child process.
        # Race detection is evidence for this executed conflict, not a termination proof.
        broken_test = '''package excerpt
import ("testing"; "sync")
func TestOrdinaryFlagRace(t *testing.T) {
 var wg sync.WaitGroup; start:=make(chan struct{}); wg.Add(2)
 go func(){defer wg.Done(); <-start; collect()}()
 go func(){defer wg.Done(); <-start; _=show()}()
 close(start); wg.Wait()
}
'''
        # The first excerpt needs no imports; the helper always emits an import block.
        case("ordinary-flag", code[8][0], broken_test, '_ "sync/atomic"',
             "EXPECTED_FAILURE", "WARNING: DATA RACE",
             [GO, "test", "-race", "-count=3", "-timeout=20s", "-v", "./..."])
        cond_test = '''package excerpt
import ("testing"; "testing/synctest")
func TestPredicate(t *testing.T) { synctest.Test(t,func(t *testing.T){
 ready=false; done:=make(chan struct{}); go func(){wait();close(done)}()
 synctest.Wait(); cond.Signal(); synctest.Wait()
 select{case <-done:t.Fatal("notification without predicate");default:}
 mu.Lock();ready=true;cond.Broadcast();mu.Unlock();<-done
})}
'''
        case("cond", "var mu sync.Mutex\nvar ready bool\nvar cond=sync.NewCond(&mu)\nfunc wait(){\n" + code[8][1] + "\n}", cond_test, '"sync"')
        first = '''type Result struct{Err error}
type Probe func(context.Context) Result
func firstResult(ctx context.Context, probes []Probe)(Result,error){
'''
        case("first-result-broken", first + code[9][0] + "\n}", "package excerpt\n", '"context"',
             "COMPILE_ONLY", command=[GO, "build", "./..."])
        case("send-select", '''type Result struct{}
func send(ctx context.Context,out chan Result,result Result){
''' + code[9][1] + "\n}", '''package excerpt
import ("context"; "testing")
func TestCanceledSend(t *testing.T){ctx,cancel:=context.WithCancel(context.Background());cancel();done:=make(chan struct{})
 go func(){send(ctx,make(chan Result),Result{});close(done)}();<-done}
''', '"context"')
        case("forward", '''type Job struct{}
type Result struct{Job Job;Err error}
func forward(ctx context.Context,job Job,out chan Result,work func(context.Context,Job)error){
''' + code[9][2] + "\n}", '''package excerpt
import ("context"; "testing")
func TestObservedCancellationDropsResult(t *testing.T){ctx,cancel:=context.WithCancel(context.Background());defer cancel()
 done:=make(chan struct{});go func(){forward(ctx,Job{},make(chan Result),func(context.Context,Job)error{cancel();return nil});close(done)}();<-done}
''', '"context"')
        case("ticker-cancel", "func loop(ctx context.Context,ticker *time.Ticker,work func(context.Context)){\n" + code[9][5] + "\n}", '''package excerpt
import ("context"; "testing"; "time")
func TestCancel(t *testing.T){ctx,cancel:=context.WithCancel(context.Background());defer cancel();ticker:=time.NewTicker(time.Hour);defer ticker.Stop()
 done:=make(chan struct{});go func(){loop(ctx,ticker,func(context.Context){t.Error("unexpected work")});close(done)}();cancel();<-done}
''', '"context";"time"')
        # Render is support for the printed benchmark, not a replacement for it.
        render = (ROOT / "labs/part10-measure-first/fixed/render.go").read_text(encoding="utf-8").replace("package fixed", "", 1)
        input_builder = (ROOT / "labs/part10-measure-first/fixed/render_test.go").read_text(encoding="utf-8")
        input_builder = input_builder[input_builder.index("func representativeReadings"):]
        path = base / "benchmark"
        path.mkdir()
        (path / "go.mod").write_text("module example.com/excerpt\n\ngo 1.27.1\n", encoding="utf-8")
        (path / "render.go").write_text("package excerpt\n" + render, encoding="utf-8")
        (path / "excerpt_test.go").write_text('package excerpt\nimport("testing";"fmt")\n' + code[10][0] + "\n" + input_builder, encoding="utf-8")
        result = run([GO, "test", "-run=^$", "-bench=^BenchmarkRender$", "-benchtime=1x", "./..."], path)
        result.update(name="benchmark", classification="PASS", implementation_origin="PDF_EXTRACTED_LINES" if copied else "ACTUAL_MARKDOWN_FENCES",
                      support_disclosed="imports and representativeReadings plus lab fixed.Render; benchmark body is actual printed code; 1x is execution smoke, not timing evidence")
        if copied:
            result["source_pdf_sha256"]=digest(ROOT/"tmp/pdfs/Golang_Master.candidate.pdf")
        results.append(result)
    return results


def negative_controls():
    results = []
    QA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=QA) as temporary:
        base = Path(temporary)
        for name, source, substitutions, selected, signature in [
            ("cond-if", "labs/part8-ordering-proof", [("fixed/memory_contract_test.go", "for !ready {", "if !ready {")], "^TestCondNotification", "notification was mistaken"),
            ("snapshot-alias", "labs/part8-ordering-proof", [("fixed/registry.go", "return snapshot", "return r.reports")], "^TestSnapshotDoesNotShare", "mutated through Snapshot"),
            ("pool-forget-join", "labs/part9-workflow-pressure", [("fixed/pool.go", "workersDone.Wait()", "// deliberately omit worker join")], "^TestCancelIsNotJoin", "output closed while owned Work"),
        ]:
            path = base / name
            shutil.copytree(ROOT / source, path)
            for filename, old, new in substitutions:
                file = path / filename
                body = file.read_text(encoding="utf-8")
                if body.count(old) != 1:
                    raise RuntimeError("mutant anchor not unique: " + filename)
                file.write_text(body.replace(old, new, 1), encoding="utf-8")
            result = run([GO, "test", "-run", selected, "-timeout=20s", "-v", "./fixed"], path)
            result.update(classification="EXPECTED_FAILURE", expected_exit_code=1,
                          negative_control=name, failure_signature_present=signature in result["stdout_utf8"] + result["stderr_utf8"])
            results.append(result)
        # A published payload remains shared. Atomic access to the pointer/flag is not enough.
        path = base / "mutate-published"
        path.mkdir()
        (path / "go.mod").write_text("module example.com/mutant\n\ngo 1.27.1\n", encoding="utf-8")
        (path / "mutation_test.go").write_text('''package mutant
import("testing";"sync";"sync/atomic")
func TestMutatePublishedPayload(t *testing.T){
 var ready atomic.Bool; data:=0; ready.Store(true); start:=make(chan struct{});var wg sync.WaitGroup;wg.Add(2)
 go func(){defer wg.Done();<-start;for range 1000{data++}}()
 go func(){defer wg.Done();<-start;sum:=0;for range 1000{if ready.Load(){sum+=data}};if sum<0{t.Error("unexpected payload")}}()
 close(start);wg.Wait()
}
''', encoding="utf-8")
        result = run([GO, "test", "-race", "-count=3", "-v", "./..."], path)
        result.update(classification="EXPECTED_FAILURE", expected_exit_code=1, negative_control="mutate-published-payload",
                      failure_signature_present="WARNING: DATA RACE" in result["stdout_utf8"] + result["stderr_utf8"])
        results.append(result)
    return results


def pdf_checks():
    import fitz
    from PIL import Image
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_pdf
    old_path = ROOT / "tmp/pdfs/agent1-review/checkpoint2.pdf"
    final_path = ROOT / "tmp/pdfs/Golang_Master.candidate.pdf"
    if digest(old_path) != OLD_PDF:
        raise RuntimeError("wrong checkpoint2 PDF")
    old, final = fitz.open(old_path), fitz.open(final_path)
    compact = lambda value: re.sub(r"\s+", "", unicodedata.normalize("NFC", value))

    def pages(doc, prefix):
        toc = doc.get_toc()
        i = next(i for i, entry in enumerate(toc) if entry[1].startswith(prefix))
        return range(toc[i][2]-1, toc[i+1][2]-1 if i+1 < len(toc) else len(doc))

    def text(doc, prefix):
        body = "\n".join(doc[p].get_text() for p in pages(doc, prefix))
        return compact(re.sub(r"(?m)^\d+\s*$", "", body))

    result = {"pdf_sha256": digest(final_path), "pages": len(final), "baseline_sha256": OLD_PDF}
    result["unchanged_chapters"] = [{"chapter": n, "equal": text(old, f"Chương {n} —") == text(final, f"Chương {n} —")}
                                    for n in range(1,30) if n not in {2,8,9,10}]
    result["other_sections"] = [{"section": name, "equal": text(old, name) == text(final, name)}
                                for name in ["Trước khi viết dòng Go đầu tiên", "Mở cửa vào Go", "BACK MATTER", "PHỤ LỤC A"]]
    ch2 = ROOT / "book/chapters/02-gia-tri-slice-va-aliasing.md"
    before = subprocess.check_output(["git", "show", START+":"+ch2.relative_to(ROOT).as_posix()], cwd=ROOT).decode("utf-8")
    after = ch2.read_text(encoding="utf-8")
    previous_paragraph = next(line for line in before.splitlines() if line.startswith("Nếu câu trả lời là"))
    new_paragraph = next(line for line in after.splitlines() if line.startswith("Nếu câu trả lời là"))
    render = lambda s: html.unescape(re.sub(r"<[^>]+>", "", build_pdf.inline(s,"JetBrainsMono")))
    old_p, new_p = compact(render(previous_paragraph)), compact(render(new_paragraph))
    result["r33"] = {"source_only_one_paragraph_changed": after.replace(new_paragraph,previous_paragraph) == before,
                     "new_paragraph_in_pdf": new_p in text(final,"Chương 2 —"),
                     "old_paragraph_absent": old_p not in text(final,"Chương 2 —"),
                     "rest_ch02_equal": text(old,"Chương 2 —").replace(old_p,"") == text(final,"Chương 2 —").replace(new_p,"")}
    result["bookmarks"] = [{"title": title,"page": p,"heading_present":compact(title) in compact(final[p-1].get_text())}
                           for _,title,p in final.get_toc() if title.startswith("Chương ")]
    lines = final[1].get_text().splitlines()
    result["toc"] = []
    for i,line in enumerate(lines):
        if re.fullmatch(r"Chương \d+",line) and i+2 < len(lines) and lines[i+2].isdigit():
            title,p = line+" — "+lines[i+1],int(lines[i+2])
            # TOC pads numbers (08), while actual headings use 8. Match the
            # numeric chapter AND complete subtitle, never only a page number.
            heading_title=f"Chương {int(line.split()[-1])} — "+lines[i+1]
            result["toc"].append({"title":title,"actual_heading_title":heading_title,"page":p,
                                  "heading_present":2<p<=len(final) and compact(heading_title) in compact(final[p-1].get_text())})
    result["content"] = []
    result["code"] = []
    copied = {}
    for n, filename in CHAPTERS.items():
        source = (ROOT / "book/chapters" / filename).read_text(encoding="utf-8")
        body = text(final,f"Chương {n} —")
        in_code = in_refs = False
        for line_number,line in enumerate(source.splitlines(),1):
            if line.startswith(("~~~","```")):
                in_code = not in_code
                continue
            if line.strip() == "@references":
                in_refs = True
            if in_code or in_refs or not line.strip() or line.startswith(("<!--","![")) or line.strip() == "---":
                continue
            cells = line.strip().strip("|").split("|") if line.startswith("|") else [line]
            for cell in cells:
                cell=cell.strip()
                if not cell or re.fullmatch(r"[: -]+",cell):
                    continue
                cell=re.sub(r"^(?:#{1,4}\s+|@(?:table|figure)\s+|>\s+)","",cell)
                result["content"].append({"chapter":n,"line":line_number,"present":compact(render(cell)) in body})
        pdf_lines=[]
        for p in pages(final,f"Chương {n} —"):
            for block in final[p].get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    spans=line["spans"]
                    if spans and all("JetBrainsMono" in s["font"] and abs(s["size"]-11.5)<.01 for s in spans):
                        pdf_lines.append("".join(s["text"] for s in spans))
        cursor=0
        copied[n]=[]
        for index,(language,block) in enumerate(blocks(n),1):
            expected=[line.expandtabs(4).rstrip() for line in block.splitlines() if line.strip()]
            start=next((i for i in range(cursor,len(pdf_lines)) if [line.strip() for line in pdf_lines[i:i+len(expected)]]==[line.strip() for line in expected]),None)
            if start is None:
                raise RuntimeError(f"PDF code mismatch Ch{n} block{index}")
            actual=pdf_lines[start:start+len(expected)]
            result["code"].append({"chapter":n,"block":index,"language":language,"line_text_equal":True,
                                  "expanded_indent_equal":actual==expected,"blank_lines_and_tabs_byte_preserved":False})
            if language=="go":
                copied[n].append("\n".join(actual))
            cursor=start+len(expected)

    def pixels(data):
        with Image.open(BytesIO(data)) as image:
            rgb=image.convert("RGB")
            import hashlib
            return hashlib.sha256(str(rgb.size).encode()+rgb.tobytes()).hexdigest()

    def inventory(doc):
        return Counter(pixels(doc.extract_image(image[0])["image"]) for p in range(2,len(doc)) for image in doc[p].get_images(full=True))
    old_images,new_images=inventory(old),inventory(final)
    result["figures"]=[]
    for name in FIGURES:
        asset="assets/diagrams/"+name+".png"
        before=pixels(subprocess.check_output(["git","show",START+":"+asset],cwd=ROOT))
        after=pixels((ROOT/asset).read_bytes())
        result["figures"].append({"asset":asset,"old_count":old_images[before],"new_count":new_images[after]})
        old_images.subtract({before:1});new_images.subtract({after:1})
    result["unaffected_body_pixels_equal"] = +old_images == +new_images
    result["literal_h4"] = any("#### Gợi ý" in final[p].get_text() for p in range(2,len(final)))
    result["scope_pages"] = sorted({2,*[p+1 for n in CHAPTERS for p in pages(final,f"Chương {n} —")],
                                    *[p+1 for p in pages(final,"Chương 2 —") if "Nếu câu trả lời" in final[p].get_text()]})
    result["copy_fidelity_limit"] = "Nonblank code characters checked; expanded indentation reported separately. PDF is not UTF-8 source: tabs/blank lines/byte fidelity NOT claimed."
    return result,copied


def main():
    import hashlib
    started=datetime.now(timezone.utc).isoformat()
    os.environ.update(GOTOOLCHAIN="local",GOWORK="off",CGO_ENABLED="1",PYTHONDONTWRITEBYTECODE="1")
    os.environ["PATH"]="D:/Golang/.tools/go1.27.1/bin;D:/DevTools/w64devkit/bin;"+os.environ["PATH"]
    evidence_path=OUT/"validation.json"
    evidence=json.loads(evidence_path.read_text(encoding="utf-8"))
    immutable=json.loads(subprocess.check_output(["git","show",START+":book/evidence/agent1-scientific-review/validation.json"],cwd=ROOT))
    if {k:v for k,v in evidence.items() if k!="checkpoint3"} != immutable:
        raise RuntimeError("historical checkpoint evidence changed")
    results=[run([GO,"version"]),run([GO,"env","-json","GOOS","GOARCH","GOEXPERIMENT","GOVERSION"])]
    for module in ["labs/part8-ordering-proof","labs/part9-workflow-pressure","labs/part10-measure-first","labs/part10-resource-retention"]:
        for command in [[GO,"test","-race","-count=5","-timeout=120s","-v","./..."],[GO,"vet","./..."]]:
            results.append(run(command,ROOT/module));print(module,command[1],results[-1]["exit_code"],flush=True)
    results.append(run([GO,"test","-race","-count=5","-run","^Test(OncePanicIsNotRetry|CondPredicateAndAtomicPublication)$","-v","./..."],ROOT/"labs/edition-contracts"))
    results.extend(excerpt_tests())
    results.extend(negative_controls())
    lab=ROOT/"labs/part10-measure-first"
    for flag in ["all=-m=2","all=-d=ssa/prove/debug=1","all=-d=ssa/check_bce/debug=1"]:
        results.append(run([GO,"build","-a","-pgo=off","-gcflags="+flag,"./fixed"],lab))
    trace=QA/"workload.trace"
    results.append(run([GO,"test","-pgo=off","-run=^TestRenderConcurrentBatchWorkload$","-trace="+str(trace),"./fixed"],lab))
    for kind in ["sync","sched","syscall","net"]:
        record=run([GO,"tool","trace","-pprof="+kind,str(trace)])
        profile=QA/(kind+".pprof")
        import base64
        profile.write_bytes(base64.b64decode(record["stdout_base64"]))
        record["binary_stdout"] = True
        results.append(record)
        results.append(run([GO,"tool","pprof","-top",str(profile)]))
    for command in [["git","diff","--check",START],["git","diff","--cached","--check"],
                    *[[sys.executable,"scripts/"+name+".py"] for name in ["validate_error_atlas","validate_manuscript_diagrams","validate_diagram_encoding","validate_diagram_semantics","validate_main_manuscript_no_bullets"]],
                    [sys.executable,"-m","unittest","discover","-s","scripts","-p","test_*.py","-v"]]:
        results.append(run(command));print(command[-1],results[-1]["exit_code"],flush=True)
    sys.path.insert(0,str(ROOT/"scripts"))
    import validate_code_width
    width=[str(x) for x in validate_code_width.validate_all_code_blocks()]
    pdf,copied=pdf_checks()
    results.extend(excerpt_tests(copied))
    pgo_path=lab/"artifacts/checkpoint3-pgo/evidence.json"
    pgo=json.loads(pgo_path.read_text(encoding="utf-8"))
    pinned=Path(GO).parent.parent/"src"
    source_hashes={str(p.relative_to(ROOT)):digest(p) for pattern in ["book/chapters/*.md","labs/part8-ordering-proof/**/*.go","labs/part9-workflow-pressure/**/*.go","labs/part10-measure-first/**/*.go","labs/part10-measure-first/pgo_ab.py","labs/part10-resource-retention/**/*.go","scripts/build_pdf.py","scripts/test_review_heading_contract.py","book/evidence/agent1-scientific-review/verify.py","book/evidence/agent1-scientific-review/checkpoint3.py","assets/visual-manifest.json"] for p in ROOT.glob(pattern)}
    for name in FIGURES:
        for ext in ["png","puml"]:
            p=ROOT/f"assets/diagrams/{name}.{ext}";source_hashes[str(p.relative_to(ROOT))]=digest(p)
    cp={"started_at_utc":started,"finished_at_utc":datetime.now(timezone.utc).isoformat(),"scope":"CH08_CH09_CH10_AND_ONE_R33_PARAGRAPH_ONLY",
        "starting_head":START,"scientific_baseline":"5938862b864b51d755209031972a1bb07f5babf2",
        "historical_evidence_values_equal_to_start":True,"historical_raw_checksums_valid":True,
        "results":results,"pgo_ab":pgo,"pgo_evidence_file_sha256":digest(pgo_path),"pdf":pdf,
        "source_hashes":source_hashes,"code_width_violations":width,
        "pinned_toolchain_source_hashes":{name:digest(pinned/name) for name in ["sync/mutex.go","sync/rwmutex.go","sync/waitgroup.go","sync/once.go","sync/cond.go","sync/atomic/doc.go","runtime/proc.go","runtime/chan.go","runtime/stack.go","runtime/mgc.go","runtime/mgcpacer.go","runtime/mgcmark.go","runtime/mgcsweep.go","runtime/mgclimit.go","runtime/netpoll.go","runtime/preempt.go","runtime/mgcsweep.go","cmd/compile/internal/escape/escape.go","cmd/compile/internal/escape/utils.go","cmd/compile/internal/ssa/downward_counting_loop.go","time/tick.go","time/sleep.go","testing/benchmark.go","internal/godebugs/table.go"]},
        "visual_status":"NOT_REVIEWED_UNTIL_ACTUAL_FINAL_PAGES_OPENED",
        "live_production_pgo":"NOT_RUN","linux_rss":"NOT_RUN","historical_retention_measurements":"NOT_RERUN; source/table retained; new CLI contract tests run separately"}
    # Verify raw evidence across both prior checkpoints, never rewrite it.
    import base64
    for row in [*immutable["results"],*immutable["checkpoint2"]["results"],*immutable["checkpoint2"].get("metadata_finalization",{}).get("results",[])]:
        for stream in ["stdout","stderr"]:
            if stream+"_base64" in row and hashlib.sha256(base64.b64decode(row[stream+"_base64"])).hexdigest()!=row[stream+"_sha256"]:
                raise RuntimeError("old raw evidence corrupted")
    failures=[r for r in results if r["exit_code"]!=r.get("expected_exit_code",0) or not r.get("failure_signature_present",True)]
    pdf_bad=any(not row["equal"] for group in ["unchanged_chapters","other_sections"] for row in pdf[group]) or not all(pdf["r33"].values()) or not pdf["unaffected_body_pixels_equal"] or pdf["literal_h4"] or any(not row["present"] for row in pdf["content"]) or any(not row["heading_present"] for group in ["toc","bookmarks"] for row in pdf[group]) or len(pdf["toc"])!=29 or len(pdf["bookmarks"])!=29 or any(row["old_count"]!=1 or row["new_count"]!=1 for row in pdf["figures"])
    cp["automated_status"]="PASS" if not(failures or width or pdf_bad or pgo["status"]!="PASS") else "FAIL"
    evidence["checkpoint3"]=cp
    evidence_path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for r in failures:
        print(r["command"],r["stdout_utf8"],r["stderr_utf8"])
    print(json.dumps({"status":cp["automated_status"],"failures":len(failures),"pdf_bad":pdf_bad,"width":width,"pages":pdf["pages"],"scope_pages":pdf["scope_pages"]}))
    return int(cp["automated_status"]!="PASS")


def refresh_final():
    """Retain successful lab runs; replace failed harness/metadata checks explicitly."""
    os.environ.update(GOTOOLCHAIN="local",GOWORK="off",CGO_ENABLED="1")
    os.environ["PATH"]="D:/Golang/.tools/go1.27.1/bin;D:/DevTools/w64devkit/bin;"+os.environ["PATH"]
    path=OUT/"validation.json"
    evidence=json.loads(path.read_text(encoding="utf-8"))
    original=json.loads(subprocess.check_output(["git","show",START+":book/evidence/agent1-scientific-review/validation.json"],cwd=ROOT))
    if {k:v for k,v in evidence.items() if k!="checkpoint3"}!=original:
        raise RuntimeError("previous checkpoints changed")
    cp=evidence["checkpoint3"]
    if cp["automated_status"]!="PASS":
        cp.setdefault("intermediate_pdf_preflights",[]).append(cp["pdf"])
    superseded=[]
    retained=[]
    previous_pdf_excerpts=[]
    for row in cp["results"]:
        if row.get("implementation_origin")=="PDF_EXTRACTED_LINES":
            previous_pdf_excerpts.append(row)
        elif row["exit_code"]!=row.get("expected_exit_code",0) or not row.get("failure_signature_present",True):
            superseded.append(row)
        else:
            retained.append(row)
    cp.setdefault("intermediate_harness_metadata_failures",[]).extend(superseded)
    if previous_pdf_excerpts:
        cp.setdefault("intermediate_pdf_excerpt_runs",[]).append({"pdf_sha256":cp["pdf"]["pdf_sha256"],"results":previous_pdf_excerpts,
            "not_final_pdf_evidence":True,"harness_boundary_newline_repaired":True})
    pdf,copied=pdf_checks()
    replacements=excerpt_tests(copied)
    replacements.append(run([sys.executable,"scripts/validate_diagram_semantics.py"]))
    retained.extend(replacements)
    cp["results"]=retained
    cp["pdf"]=pdf
    cp["final_pdf_checked_at_utc"]=datetime.now(timezone.utc).isoformat()
    for key in cp["source_hashes"]:
        cp["source_hashes"][key]=digest(ROOT/key)
    failures=[r for r in retained if r["exit_code"]!=r.get("expected_exit_code",0) or not r.get("failure_signature_present",True)]
    pdf_bad=any(not row["equal"] for group in ["unchanged_chapters","other_sections"] for row in pdf[group]) or not all(pdf["r33"].values()) or not pdf["unaffected_body_pixels_equal"] or pdf["literal_h4"] or any(not row["present"] for row in pdf["content"]) or any(not row["heading_present"] for group in ["toc","bookmarks"] for row in pdf[group]) or len(pdf["toc"])!=29 or len(pdf["bookmarks"])!=29 or any(row["old_count"]!=1 or row["new_count"]!=1 for row in pdf["figures"])
    cp["automated_status"]="PASS" if not(failures or cp["code_width_violations"] or pdf_bad) else "FAIL"
    path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for r in failures:
        print(r["command"],r["stdout_utf8"],r["stderr_utf8"])
    print(json.dumps({"status":cp["automated_status"],"failures":len(failures),"pdf_bad":pdf_bad,"pages":pdf["pages"],"scope_pages":pdf["scope_pages"]}))
    return int(cp["automated_status"]!="PASS")


if __name__=="__main__":
    if sys.argv[1:]==["--final-pdf"]:
        raise SystemExit(refresh_final())
    if sys.argv[1:]:
        raise SystemExit("usage: checkpoint3.py [--final-pdf]")
    raise SystemExit(main())
