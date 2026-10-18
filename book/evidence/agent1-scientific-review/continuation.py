"""Append reproducible continuous-review evidence without overwriting prior batches."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from verify import ROOT, OUT, GO, digest, run

QA = ROOT / "tmp/pdfs/agent1-review/continuation"
START = "34aa4b4"


def fences(n):
    source = next((ROOT / "book/chapters").glob(f"{n:02d}-*.md")).read_text(encoding="utf-8")
    source = "\n".join(re.sub(r"^> ?", "", x) for x in source.splitlines())
    return [body for _, lang, body in re.findall(r"^(~~~|```)([^\n]*)\n(.*?)^\1[ \t]*$", source, re.M | re.S) if lang.strip()=="go"]


def function(text, name):
    pattern = rf"(?ms)^func (?:\([^\n]*\) )?{re.escape(name)}(?:\[|\()(.*?)^}}(?:\n|$)"
    match = re.search(pattern,text)
    if not match: raise RuntimeError(f"missing function {name}")
    return match.group(0).rstrip()


def tests():
    rs=[]
    for module in ["projects/opsprobe", "labs/part21-reconciliation-controller", "labs/part22-client-go-controller", "labs/part23-controller-runtime-operator", "labs/part24-aws-sdk-go-v2", "labs/part25-github-automation", "labs/part10-resource-retention"]:
        for flags in [["test","-race","-count=3","-timeout=180s","-v","./..."],["vet","./..."]]:
            r=run([GO,*flags],ROOT/module);rs.append(r);print(module,flags[0],r["exit_code"],flush=True)
    return rs


def negative_controls():
    rs=[]
    cases=[("projects/opsprobe","internal/probe/probe.go","./internal/probe","TestDrainBoundaryContracts","panic:"),
           ("labs/part23-controller-runtime-operator","controllers/appservice_controller.go","./controllers","TestForeignDeploymentIsNotAdoptedOrMutated","name collision must be rejected"),
           ("labs/part25-github-automation","ratelimit.go",".","TestJitterRejectsNonFiniteAndOverflow|TestRateLimitNeverShortensKnownWaitOrWraps","accepted invalid jitter"),
           ("labs/part25-github-automation","gitops.go",".","TestCommitDoesNotAdvanceOnWriteOrCloseFailure","file failure was swallowed"),
           ("labs/part25-github-automation","webhook.go",".","TestEmptyWebhookSecretFailsClosed","empty shared secret authenticated")]
    for module,file,pkg,test,signature in cases:
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            path=Path(tmp)/"module";shutil.copytree(ROOT/module,path)
            (path/file).write_bytes(subprocess.check_output(["git","show",f"{START}:{module}/{file}"],cwd=ROOT))
            r=run([GO,"test","-count=1","-run",test,pkg],path)
            r.update(classification="EXPECTED_FAILURE",expected_exit_code=1,failure_signature_present=signature in (r["stdout_utf8"]+r["stderr_utf8"]),negative_control="new assertions against unchanged starting implementation",restored_file=f"{module}/{file}")
            rs.append(r);print("negative",module,file,r["exit_code"],flush=True)
    with tempfile.TemporaryDirectory(dir=QA) as tmp:
        path=Path(tmp)/"module";shutil.copytree(ROOT/"labs/part21-reconciliation-controller",path)
        file=path/"queue/workqueue.go";text=file.read_text(encoding="utf-8")
        text=text.replace(function(text,"retryDelay"),"""func retryDelay(base, max time.Duration, failures int) time.Duration {
 delay:=base*time.Duration(1<<(failures-1));if delay>max {return max};return delay
}""")
        file.write_text(text,encoding="utf-8")
        r=run([GO,"test","-count=1","-run","TestRetryDelaySaturatesBeforeOverflow","./queue"],path)
        r.update(classification="EXPECTED_FAILURE",expected_exit_code=1,failure_signature_present="want 10s" in r["stdout_utf8"],negative_control="old multiply-then-cap formula restored under helper signature")
        rs.append(r)
    return rs


def excerpts(copied=None):
    rs=[]
    for n,module,replacements in [(20,"projects/opsprobe",{"internal/probe/probe.go":["drainResponseBody"]}),
             (24,"labs/part24-aws-sdk-go-v2",{"credentials_provider.go":["Retrieve"],"storage.go":["ClassifyError"]}),
             (25,"labs/part25-github-automation",{"webhook.go":["VerifyHMACSHA256"],"ratelimit.go":["ParseRateLimit","CalculateBackoffWithJitter"],"gitops.go":["WriteFileAndCommit"]})]:
        bs="\n".join(copied[n] if copied else fences(n))
        with tempfile.TemporaryDirectory(dir=QA) as tmp:
            path=Path(tmp)/"module";shutil.copytree(ROOT/module,path)
            for filename,names in replacements.items():
                file=path/filename;text=file.read_text(encoding="utf-8")
                for name in names:text=text.replace(function(text,name),function(bs,name))
                if n==25 and filename=="ratelimit.go":text=text.replace("\"fmt\"","\"errors\"")
                file.write_text(text,encoding="utf-8")
            r=run([GO,"test","-race","-count=3","-timeout=180s","-v","./..."],path)
            r.update(chapter=n,classification="PASS" if r["exit_code"]==0 else "FAIL",source_origin="PDF_FUNCTIONS" if copied else "MARKDOWN_FUNCTIONS",functions=replacements)
            rs.append(r);print("printed",n,r["exit_code"],flush=True)
    # The Ch22 variant is deliberately not the callback-based lab. Compile it
    # separately and test its cache/current-state/delete guards with fake data.
    bs=copied[22] if copied else fences(22)
    selected=[next(b for b in bs if f"{name}" in b) for name in ["type Reconciler interface", "func (c *Controller) Run", "func (c *Controller) processNextItem(", "func (c *Controller) reconcileHandler("]]
    with tempfile.TemporaryDirectory(dir=QA) as tmp:
        path=Path(tmp)
        for file in (ROOT/"labs/part22-client-go-controller").glob("go.*"):shutil.copy2(file,path/file.name)
        (path/"excerpt.go").write_text('''package controller
import("context";"fmt";"sync";corev1 "k8s.io/api/core/v1";"k8s.io/apimachinery/pkg/util/runtime";"k8s.io/client-go/tools/cache";"k8s.io/client-go/util/workqueue")
'''+"\n".join(selected),encoding="utf-8")
        (path/"excerpt_test.go").write_text('''package controller
import("context";"testing";"time";corev1 "k8s.io/api/core/v1";metav1 "k8s.io/apimachinery/pkg/apis/meta/v1";"k8s.io/client-go/tools/cache";"k8s.io/client-go/util/workqueue")
type probeReconciler struct{calls int}
func(r *probeReconciler)Reconcile(context.Context,string)error{r.calls++;return nil}
func TestPrintedVariant(t *testing.T){
 q:=workqueue.NewTypedRateLimitingQueue[string](workqueue.DefaultTypedItemBasedRateLimiter[string]());defer q.ShutDown()
 idx:=cache.NewIndexer(cache.MetaNamespaceKeyFunc,cache.Indexers{});r:=&probeReconciler{};c:=&Controller{indexer:idx,queue:q,reconciler:r}
 if err:=c.reconcileHandler(context.Background(),"ns/missing");err!=nil||r.calls!=1{t.Fatal(err,r.calls)}
 p:=&corev1.Pod{ObjectMeta:metav1.ObjectMeta{Name:"p",Namespace:"ns"}};if err:=idx.Add(p);err!=nil{t.Fatal(err)}
 now:=metav1.NewTime(time.Now());p=p.DeepCopy();p.DeletionTimestamp=&now;if err:=idx.Update(p);err!=nil{t.Fatal(err)}
 if err:=c.reconcileHandler(context.Background(),"ns/p");err!=nil||r.calls!=1{t.Fatal("deletion guard",err,r.calls)}
 ctx,cancel:=context.WithCancel(context.Background());cancel();if err:=c.Run(ctx,1);err!=nil{t.Fatal(err)}
}
''',encoding="utf-8")
        r=run([GO,"test","-race","-count=3","-v","./..."],path);r.update(chapter=22,source_origin="MARKDOWN_VARIANT_NOT_LAB",classification="PASS" if r["exit_code"]==0 else "FAIL");rs.append(r)
    # The printed MCP handlers intentionally omit rate limiting. Test only
    # their stated identity/allowlist/authorization/HTTP contracts, not the
    # omitted limiter policy. The full lab has a separate all-tests run.
    bs=copied[28] if copied else fences(28)
    sdk=Path("D:/Golang/library_sources/repos/mcp-go-sdk")
    if subprocess.check_output(["git","rev-parse","HEAD"],cwd=sdk,text=True).strip()!="3f3b699b2b67e1ed033a63d6651671dab53c2d32":raise RuntimeError("SDK identity changed")
    with tempfile.TemporaryDirectory(dir=QA) as tmp:
        path=Path(tmp)/"module";shutil.copytree(ROOT/"labs/part28-mcp-ops-tools",path)
        file=path/"go.mod";file.write_text(file.read_text().replace("../../library_sources/repos/mcp-go-sdk",sdk.as_posix()),encoding="utf-8")
        file=path/"server.go";text=file.read_text(encoding="utf-8")
        for name in ["NewOpsServer","RecordAudit"]:
            text=text.replace(function(text,name),function("\n".join(bs),name))
        handlers=[b for b in bs if b.startswith("mcp.AddTool(")]
        if len(handlers)!=2:raise RuntimeError("MCP handlers missing")
        text=text.replace(function(text,"registerTools"),"func (s *OpsServer) registerTools() {\n"+"\n".join(handlers)+"\n}")
        file.write_text(text,encoding="utf-8")
        r=run([GO,"test","-race","-count=3","-v","-run","^(TestMCP|TestRestartFailsClosed|TestUnknownRole|TestApprovedTargetRedirect)","."],path)
        r.update(chapter=28,source_origin="PDF_FUNCTIONS" if copied else "MARKDOWN_FUNCTIONS",classification="PASS" if r["exit_code"]==0 else "FAIL",omitted_policy="rate limiting and authenticated caller key; NOT VERIFIED by printed excerpt tests")
        rs.append(r);print("printed",28,r["exit_code"],flush=True)
    return rs


def main():
    parser=argparse.ArgumentParser();parser.add_argument("mode",choices=["tests","negative","excerpts"]);args=parser.parse_args()
    QA.mkdir(parents=True,exist_ok=True)
    os.environ.update(GOTOOLCHAIN="local",GOWORK="off",CGO_ENABLED="1",PYTHONDONTWRITEBYTECODE="1")
    os.environ["PATH"]="D:/Golang/.tools/go1.27.1/bin;D:/DevTools/w64devkit/bin;"+os.environ["PATH"]
    path=OUT/"validation.json";d=json.loads(path.read_text(encoding="utf-8"));c=d.setdefault("continuation",{"starting_head":subprocess.check_output(["git","rev-parse",START],cwd=ROOT,text=True).strip()})
    if args.mode in c:raise RuntimeError("evidence already recorded; preserve earlier attempt")
    rs={"tests":tests,"negative":negative_controls,"excerpts":excerpts}[args.mode]()
    c[args.mode]=rs;c["source_sha256"]={p.relative_to(ROOT).as_posix():digest(p) for p in [*ROOT.glob("book/chapters/2[012345]*.md"),*ROOT.glob("labs/part2[12345]*/**/*.go"),*ROOT.glob("projects/opsprobe/**/*.go")]}
    c["recorded_at_utc"]=datetime.now(timezone.utc).isoformat()
    bad=[r for r in rs if r["exit_code"]!=r.get("expected_exit_code",0) or not r.get("failure_signature_present",True)]
    c[args.mode+"_status"]="FAIL" if bad else "PASS"
    path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for r in bad:print(r["command"],r["stdout_utf8"],r["stderr_utf8"])
    print(args.mode,c[args.mode+"_status"],flush=True);return int(bool(bad))


if __name__=="__main__":raise SystemExit(main())
