"""Append final evidence; never turn a structural gate into scientific/visual PASS."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
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
import urllib.request

from verify import ROOT, OUT, GO, digest, run
from continuation import excerpts, function
from checkpoint4 import chapter_pages

QA=ROOT/"tmp/pdfs/agent1-review/final"
PDF=ROOT/"tmp/pdfs/Golang_Master.candidate.pdf"
START="34aa4b41b048061422a3d77543a95b6ef228be63"
SDK=Path("D:/Golang/library_sources/repos/mcp-go-sdk")
SDK_SHA="3f3b699b2b67e1ed033a63d6651671dab53c2d32"


def blocks(path):
    text="\n".join(re.sub(r"^> ?","",x) for x in path.read_text(encoding="utf-8").splitlines())
    return [(lang.strip(),body) for _,lang,body in re.findall(r"^(~~~|```)([^\n]*)\n(.*?)^\1[ \t]*$",text,re.M|re.S)]


def final_tests():
    rs=[]
    for module in ["projects/opsprobe","labs/part21-reconciliation-controller","labs/part22-client-go-controller","labs/part23-controller-runtime-operator","labs/part24-aws-sdk-go-v2","labs/part25-github-automation","labs/part1-reading-go","labs/edition-contracts","labs/part29-change-evidence"]:
        for flags in [["test","-race","-count=3","-timeout=180s","-v","./..."],["vet","./..."]]:
            r=run([GO,*flags],ROOT/module);rs.append(r);print(module,flags[0],r["exit_code"],flush=True)
    if subprocess.check_output(["git","rev-parse","HEAD"],cwd=SDK,text=True).strip()!=SDK_SHA:
        raise RuntimeError("SDK source identity changed")
    with tempfile.TemporaryDirectory(dir=QA) as tmp:
        path=Path(tmp)/"module";shutil.copytree(ROOT/"labs/part28-mcp-ops-tools",path)
        file=path/"go.mod";file.write_text(file.read_text().replace("../../library_sources/repos/mcp-go-sdk",SDK.as_posix()),encoding="utf-8")
        for flags in [["test","-race","-count=3","-timeout=180s","-v","./..."],["vet","./..."]]:
            r=run([GO,*flags],path);r.update(classification="PASS" if r["exit_code"]==0 else "FAIL",dependency=SDK_SHA,modification="only local replace path; implementation and tests unchanged");rs.append(r);print("MCP",flags[0],r["exit_code"],flush=True)
        file=path/"server.go";file.write_bytes(subprocess.check_output(["git","show",START+":labs/part28-mcp-ops-tools/server.go"],cwd=ROOT))
        r=run([GO,"test","-run","^TestUnknownRoleCannotAuthorizeChange$","-count=1","-v","."],path)
        r.update(classification="EXPECTED_FAILURE",expected_exit_code=1,failure_signature_present="authorized mutation" in r["stdout_utf8"]);rs.append(r)
    return rs


def real_api():
    archive=Path("D:/Golang/.tools/reliability-envtest-1.37.0/envtest-v1.37.0-linux-amd64.tar.gz")
    url="https://github.com/kubernetes-sigs/controller-tools/releases/download/envtest-v1.37.0/envtest-v1.37.0-linux-amd64.tar.gz.sha512"
    raw=urllib.request.urlopen(url,timeout=45).read()
    expected=raw.decode("utf-8").split()[0];actual=hashlib.sha512(archive.read_bytes()).hexdigest()
    if expected!=actual:raise RuntimeError("independent official asset checksum mismatch")
    root=QA/"envtest";root.mkdir(exist_ok=True)
    linux=lambda p:"/mnt/"+p.resolve().drive[0].lower()+p.resolve().as_posix()[2:]
    rs=[]
    r=run(["wsl","-d","Ubuntu-24.04","--exec","tar","-xzf",linux(archive),"--no-same-owner","-C",linux(root)])
    r.update(official_checksum_url=url,official_checksum_sha256=hashlib.sha256(raw).hexdigest(),archive_sha512=actual,classification="PASS" if r["exit_code"]==0 else "FAIL");rs.append(r)
    if r["exit_code"]:return rs
    binary=QA/"api-contract.test"
    old=os.environ.get("CGO_ENABLED");os.environ.update(GOOS="linux",GOARCH="amd64",CGO_ENABLED="0")
    try:r=run([GO,"test","-mod=readonly","-tags","integration","-c","-o",str(binary),"./integration"],ROOT/"labs/part23-controller-runtime-operator")
    finally:
        os.environ.pop("GOOS",None);os.environ.pop("GOARCH",None);os.environ["CGO_ENABLED"]=old or "1"
    r.update(classification="COMPILE_ONLY",binary_sha256=digest(binary) if binary.exists() else None);rs.append(r)
    if r["exit_code"]:return rs
    assets=root/"controller-tools/envtest"
    prefix="cd "+linux(ROOT/"labs/part23-controller-runtime-operator/integration")+" && env -u TEST_ASSET_KUBE_APISERVER -u TEST_ASSET_ETCD -u TEST_ASSET_KUBECTL -u KUBECONFIG -u RELIABILITY_MUTANT USE_EXISTING_CLUSTER=false KUBEBUILDER_ASSETS="+linux(assets)+" "
    flags=linux(binary)+" '-test.run=^TestRealAPIContract$' -test.v -test.timeout=120s"
    for mutant in [False,True]:
        r=run(["wsl","-d","Ubuntu-24.04","--exec","sh","-lc",prefix+("RELIABILITY_MUTANT=root_status_write " if mutant else "")+flags])
        r.update(classification="EXPECTED_FAILURE" if mutant else "INTEGRATION_TESTED",expected_exit_code=1 if mutant else 0,failure_signature_present=("status writer contract" if mutant else "INTEGRATION_TESTED owned real API") in r["stdout_utf8"],asset_sha256={n:digest(assets/n) for n in ["kube-apiserver","etcd","kubectl"]})
        rs.append(r);print("real API mutant="+str(mutant),r["exit_code"],flush=True)
    return rs


def sources():
    # Re-fetch bytes at the MANUSCRIPT pins, not the evolving lock versions.
    catalog=json.loads((ROOT/"library_sources/catalog.json").read_text(encoding="utf-8"))
    ledger=(ROOT/"book/publication/library_atlas_evidence_ledger.md").read_text(encoding="utf-8")
    entries=re.findall(r"^\| (\d\d) \| `([^`]+)` \| `([0-9a-f]{40})` \|.*?\| (.*?) \|$",ledger,re.M)
    if len(entries)!=50:raise RuntimeError("not 50 source pins")
    jobs=[]
    for rank,module,sha,anchors in entries:
        config=next(x for x in catalog if x["rank"]==int(rank))
        paths=[p for p in re.findall(r"`([^`]+)`",anchors) if p.endswith((".go",".md"))]
        if not paths:raise RuntimeError("missing source path "+rank)
        remote=config["official_remote"].removesuffix(".git")
        repo=remote.removeprefix("https://github.com/")
        for path in paths:
            url=(f"{remote}/-/raw/{sha}/{path}" if remote.startswith("https://gitlab.com/") else f"https://raw.githubusercontent.com/{repo}/{sha}/{path}")
            jobs.append((rank,module,sha,path,url))
    def retrieve(job):
        rank,module,sha,path,url=job
        record={"rank":int(rank),"module":module,"commit":sha,"path":path,"url":url}
        try:
            data=urllib.request.urlopen(url,timeout=45).read();data.decode("utf-8")
            record.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),status="SOURCE_FILE_RETRIEVED_NOT_SEMANTIC_PASS")
            target=QA/"sources"/rank/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        except Exception as error:
            record.update(status="NOT_VERIFIED",error=str(error))
            # A Git object is content-addressed evidence, not an inherited QA
            # verdict. On network failure verify origin and both object hashes.
            config=next(x for x in catalog if x["rank"]==int(rank))
            local=Path("D:/Golang/library_sources/repos")/config["id"]
            if local.exists():
                try:
                    origin=subprocess.check_output(["git","remote","get-url","origin"],cwd=local,text=True).strip()
                    if origin.removesuffix(".git")!=config["official_remote"].removesuffix(".git"):raise RuntimeError("origin mismatch")
                    commit=subprocess.check_output(["git","cat-file","commit",sha],cwd=local)
                    computed=subprocess.run(["git","hash-object","-t","commit","--stdin"],input=commit,cwd=local,capture_output=True,check=True).stdout.decode().strip()
                    if computed!=sha:raise RuntimeError("commit hash mismatch")
                    data=subprocess.check_output(["git","show",sha+":"+path],cwd=local);data.decode("utf-8")
                    blob=subprocess.check_output(["git","rev-parse",sha+":"+path],cwd=local,text=True).strip()
                    actual=subprocess.run(["git","hash-object","--stdin"],input=data,cwd=local,capture_output=True,check=True).stdout.decode().strip()
                    if blob!=actual:raise RuntimeError("blob hash mismatch")
                    record.update(status="SOURCE_FILE_RETRIEVED_NOT_SEMANTIC_PASS",retrieval="local Git verified commit/blob objects; remote request failed",verified_origin=origin,blob_sha1=blob,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
                    target=QA/"sources"/rank/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                except Exception as fallback:record["git_fallback_error"]=str(fallback)
        print("source",rank,path,record["status"],flush=True)
        return record
    with ThreadPoolExecutor(max_workers=8) as pool:records=list(pool.map(retrieve,jobs))
    (QA/"sources.json").write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return records


def foundations():
    rs=[]
    with tempfile.TemporaryDirectory(dir=QA) as tmp:
        path=Path(tmp);file=path/"main.go"
        file.write_text(next(body for lang,body in blocks(ROOT/"book/chapters/00-mo-cua-vao-go.md") if lang=="go"),encoding="utf-8")
        r=run([GO,"run",str(file)],path);r["expected_stdout_present"]="he thong san sang" in r["stdout_utf8"];rs.append(r)
        file.write_text(next(body for lang,body in blocks(ROOT/"book/chapters/01-doc-va-viet-mot-chuong-trinh-go.md") if lang=="go"),encoding="utf-8")
        r=run([GO,"run",str(file)],path);r["expected_stdout_present"]="checkout failed" in r["stdout_utf8"];rs.append(r)
        binary=path/"classify.exe"
        rs.append(run([GO,"build","-gcflags=-l -S","-o",str(binary),str(ROOT/"labs/part1-reading-go/testdata/classify/main.go")],path))
        r=run([GO,"tool","objdump","-s","main\\.classify",str(binary)],path)
        r["instruction_contract_present"]=all(x in r["stdout_utf8"] for x in ["CMPQ AX", "$0x1f4", "JL ", "MOVL $0x6", "MOVL $0x7"]);rs.append(r)
    return rs


def pdf_fidelity():
    import pymupdf as fitz
    import build_pdf
    from PIL import Image
    from functools import cache
    oldpath=ROOT/"tmp/pdfs/agent1-review/checkpoint6.pdf"
    if digest(oldpath)!="ccf1b0ec58db14c1a216a2b824fe8314d30c5a49bd83719a597c060c28dc7e01":raise RuntimeError("old candidate changed")
    old,new=fitz.open(oldpath),fitz.open(PDF)
    compact=lambda s:re.sub(r"\s+","",unicodedata.normalize("NFC",s))
    @cache
    def body(doc,n):return compact("\n".join(doc[p].get_text(clip=fitz.Rect(0,0,doc[p].rect.width,doc[p].rect.height-45)) for p in chapter_pages(doc,n)))
    render=lambda s:html.unescape(re.sub(r"<[^>]+>","",build_pdf.inline(s,"JetBrainsMono")))
    mapping={int(p.name[:2]):p for p in (ROOT/"book/chapters").glob("[012][123456789]-*.md")}
    mapping.update({"Trước khi viết dòng Go đầu tiên":ROOT/"book/chapters/00-truoc-khi-viet-dong-go-dau-tien.md","Mở cửa vào Go":ROOT/"book/chapters/00-mo-cua-vao-go.md","BACK MATTER":ROOT/"book/appendices/devops-library-atlas.md","PHỤ LỤC A":ROOT/"book/appendices/error-atlas.md"})
    # Include Ch10/20 (the glob above deliberately avoids Ch00 ambiguity).
    for n in [10,20]:mapping[n]=next((ROOT/"book/chapters").glob(f"{n:02d}-*.md"))
    if len(mapping)!=33:raise RuntimeError("missing manuscript section")
    changed=set([17,18,20,21,22,23,24,25,26,27,28,"BACK MATTER","PHỤ LỤC A"])
    result={"sha256":digest(PDF),"pages":len(new),"unchanged_sections":{str(n):body(old,n)==body(new,n) for n in mapping if n not in changed},"code":[],"content":[],"toc":[],"bookmarks":[],"copy_fidelity":"Nonblank characters and expanded indentation only; not raw bytes/tabs/blank lines"}
    copied={};locations=[]
    for n,path in mapping.items():
        lines=[];linepages=[]
        for p in chapter_pages(new,n):
            for block in new[p].get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    spans=line["spans"]
                    if spans and all("JetBrainsMono" in s["font"] and abs(s["size"]-11.5)<.01 for s in spans):lines.append("".join(s["text"] for s in spans));linepages.append(p+1)
        cursor=0;copied[n]=[]
        for i,(lang,text) in enumerate(blocks(path),1):
            expected=[x.expandtabs(4).rstrip() for x in text.splitlines() if x.strip()]
            if not expected:continue
            start=next((j for j in range(cursor,len(lines)) if [x.strip() for x in lines[j:j+len(expected)]]==[x.strip() for x in expected]),None)
            if start is None:raise RuntimeError(f"PDF code mismatch {n} block{i}")
            actual=lines[start:start+len(expected)];cursor=start+len(expected)
            result["code"].append({"section":str(n),"block":i,"expanded_indentation_equal":actual==expected,"pages":sorted(set(linepages[start:cursor]))})
            if lang=="go":copied[n].append("\n".join(actual))
            if n in changed:locations.extend(linepages[start:cursor])
        in_code=False
        for number,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
            line=re.sub(r"^> ?","",line)
            if line.startswith(("~~~","```")):in_code=not in_code;continue
            if line.startswith("@references"):break
            if in_code or not line.strip() or line.startswith(("<!--","![")):continue
            cells=line.strip().strip("|").split("|") if line.startswith("|") else [line]
            for cell in cells:
                original=cell.strip()
                cell=re.sub(r"^(?:#{1,4}\s+|@(?:table|figure)\s+|[-*]\s+|\d+\.\s+)","",original)
                if n=="PHỤ LỤC A" and re.match(r"^## [A-J] — ",original):cell=cell.upper()
                if n=="PHỤ LỤC A" and original.startswith("→"):
                    cell=re.sub(r"\[(Ch\d+(?:,\s*\d+)*)\]\s*$",r"\1",cell)
                if cell and not re.fullmatch(r"[: -]+",cell):result["content"].append({"section":str(n),"line":number,"present":compact(render(cell)) in body(new,n)})
    result["bookmarks"]=[{"title":t,"page":p,"match":compact(t) in compact(new[p-1].get_text())} for _,t,p in new.get_toc()]
    lines=new[1].get_text().splitlines()
    for i,line in enumerate(lines[:-2]):
        if re.fullmatch(r"Chương \d+",line) and lines[i+2].isdigit():
            p=int(lines[i+2]);t=f"Chương {int(line.split()[-1])} — "+lines[i+1];result["toc"].append({"title":t,"page":p,"match":compact(t) in compact(new[p-1].get_text())})
    def pixels(data):
        im=Image.open(BytesIO(data)).convert("RGB");return hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
    inv=lambda d:Counter(pixels(d.extract_image(im[0])["image"]) for p in range(2,len(d)) for im in d[p].get_images(full=True))
    before,after=inv(old),inv(new)
    result["reviewed_raster_repairs"]=[]
    diagrams=["git-github-boundaries","webhook-hmac-verification","aws-credentials-resolution","ebpf-build-load","agent-mailbox-contract","vulnerability-call-reachability"]
    for name in diagrams:
        relative=f"assets/diagrams/{name}.png"
        original=subprocess.check_output(["git","show",START+":"+relative],cwd=ROOT)
        replacement=(ROOT/relative).read_bytes()
        a,b=pixels(original),pixels(replacement)
        if a==b:continue
        if before[a]!=after[b] or before[a]==0:raise RuntimeError(f"missing/repeated raster repair {name}")
        result["reviewed_raster_repairs"].append({"asset":relative,"before_sha256":hashlib.sha256(original).hexdigest(),"after_sha256":hashlib.sha256(replacement).hexdigest(),"occurrences":before[a]})
        del before[a];del after[b]
    result["body_raster_pixels_unchanged"]=before==after
    result["changed_section_pages"]=sorted({p+1 for n in changed for p in chapter_pages(new,n)})
    result["code_pages_in_changed_sections"]=sorted(set(locations))
    result["missing_content"]=[x for x in result["content"] if not x["present"]]
    result["automated_status"]="PASS" if all(result["unchanged_sections"].values()) and all(x["expanded_indentation_equal"] for x in result["code"]) and not result["missing_content"] and all(x["match"] for k in ["toc","bookmarks"] for x in result[k]) and len(result["toc"])==29 and result["body_raster_pixels_unchanged"] else "FAIL"
    (QA/"pdf_fidelity.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result,copied


def gates():
    rs=[]
    for name in ["validate_code_width","validate_error_atlas","validate_main_manuscript_no_bullets","validate_manuscript_diagrams","validate_diagram_encoding","validate_diagram_semantics","validate_visual_manifest"]:
        rs.append(run([sys.executable,"scripts/"+name+".py"]))
    rs.extend([run(["git","diff","--check",START]),run(["git","diff","--cached","--check"])])
    return rs


def main():
    parser=argparse.ArgumentParser();parser.add_argument("mode",choices=["tests","realapi","sources","foundations","gates","pdf","pdfaudit"]);parser.add_argument("--attempt",type=int,default=1);args=parser.parse_args()
    QA.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(ROOT/"scripts"))
    os.environ.update(GOTOOLCHAIN="local",GOWORK="off",CGO_ENABLED="1",PYTHONDONTWRITEBYTECODE="1")
    os.environ["PATH"]="D:/Golang/.tools/go1.27.1/bin;D:/DevTools/w64devkit/bin;"+os.environ["PATH"]
    file=OUT/"validation.json";d=json.loads(file.read_text(encoding="utf-8"));f=d.setdefault("finalization",{"starting_head":START})
    key=args.mode if args.attempt==1 else f"{args.mode}_{args.attempt}"
    if key in f:raise RuntimeError("do not overwrite earlier evidence")
    if args.mode=="pdf":
        result,copied=pdf_fidelity();f[key]=result;rs=excerpts(copied);f[key+"_excerpt_results"]=rs
    elif args.mode=="pdfaudit":
        result,_=pdf_fidelity()
        if f.get("pdf",{}).get("sha256")!=result["sha256"]:raise RuntimeError("do not reuse excerpt tests for a different PDF")
        f[key]=result;f[key]["printed_test_evidence_key"]="pdf_excerpt_results (same exact PDF SHA256; no tests claimed rerun)";rs=[]
    elif args.mode=="sources":f[key]=sources();rs=[]
    else:rs={"tests":final_tests,"realapi":real_api,"foundations":foundations,"gates":gates}[args.mode]();f[key]=rs
    bad=[r for r in rs if r["exit_code"]!=r.get("expected_exit_code",0) or not r.get("failure_signature_present",True) or not r.get("expected_stdout_present",True) or not r.get("instruction_contract_present",True)]
    status="FAIL" if bad or (args.mode in ["pdf","pdfaudit"] and f[key]["automated_status"]!="PASS") else "PASS"
    if args.mode=="sources":status="NOT_VERIFIED" if any(x["status"]=="NOT_VERIFIED" for x in f[key]) else "SOURCE_FILES_RETRIEVED_NOT_SEMANTIC_PASS"
    f[key+"_status"]=status
    f["recorded_at_utc"]=datetime.now(timezone.utc).isoformat()
    f["source_sha256"]={p.relative_to(ROOT).as_posix():digest(p) for p in [*ROOT.glob("book/chapters/*.md"),*ROOT.glob("book/appendices/*.md"),*ROOT.glob("labs/**/*.go"),*ROOT.glob("projects/opsprobe/**/*.go")]}
    file.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for r in bad:print(r["command"],r["stdout_utf8"],r["stderr_utf8"])
    print(key,status,flush=True);return int(status in ["FAIL","NOT_VERIFIED"])


if __name__=="__main__":raise SystemExit(main())
