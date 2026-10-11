"""Finalize explicitly reviewed figures/pages; never generate a visual PASS."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from verify import ROOT, OUT, GO, digest, run
from checkpoint3 import START, CHAPTERS, FIGURES, QA

REASONS = {
    "waitgroup-completion-proof": "R38: separate counting completion from mutex-protected data visibility; remove memory-barrier label and per-Done unblocking implication.",
    "channel-work-lifecycle": "R44/R45: ownership is a lab policy, not a Go compiler rule; coordinator joins dispatcher and workers before output close.",
    "performance-evidence-path": "R52: heap profile gives allocation site, not retention path or unwanted allocation verdict; profiling narrows a hypothesis and is not mandatory for every optimization.",
}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only",action="store_true")
    parser.add_argument("--pages",help="comma-separated pages ACTUALLY opened and observed by reviewer")
    args=parser.parse_args()
    path=ROOT/"assets/visual-manifest.json"
    manifest=json.loads(path.read_text(encoding="utf-8"))
    if args.source_only:
        for item in manifest["assets"]:
            name=item["asset_id"]
            if name not in FIGURES:
                continue
            historical_keys=["review_status","rendered_pdf_sha256","rendered_page","rendered_page_png_sha256","visual_review_evidence","source_sha256","sha256","minimum_printed_font_pt"]
            if "checkpoint2_historical_review" not in item:
                item["checkpoint2_historical_review"]={k:item[k] for k in historical_keys if k in item}
            for key in historical_keys:
                item.pop(key,None)
            source_hash=hashlib.sha256((ROOT/item["source"]).read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            item.update(source_sha256=source_hash,sha256=digest(ROOT/item["local_asset_path"]),
                        semantic_sha256=source_hash,semantics_reviewed=True,
                        semantic_repair_reason=REASONS[name],review_status="SOURCE_REVIEWED_RENDER_PENDING",
                        modifications="Checkpoint3 scientific source correction; historical review retained separately, not transferred to new candidate.")
            item["style_source"]="assets/diagrams/publication-flow.iuml"
            item["style_sha256"]=hashlib.sha256((ROOT/item["style_source"]).read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return 0
    if not args.pages:
        parser.error("--pages requires actual human/model observation, not automatic scope selection")
    import fitz
    pdf_path=ROOT/"tmp/pdfs/Golang_Master.candidate.pdf"
    document=fitz.open(pdf_path)
    sha=digest(pdf_path)
    reviewed=sorted(set(int(p) for p in args.pages.split(",")))
    for p in reviewed:
        if not 1<=p<=len(document) or not(QA/f"page-{p:03d}.png").exists():
            raise RuntimeError("missing actual page render")
    reviewed_set=set(reviewed)
    for item in manifest["assets"]:
        if item["asset_id"] not in FIGURES:
            continue
        chapter=int(item["chapter_section"].replace("\\","/").split("/")[-1][:2])
        toc=document.get_toc()
        i=next(i for i,(_,title,_) in enumerate(toc) if title.startswith(f"Chương {chapter} —"))
        candidates=range(toc[i][2]-1,toc[i+1][2]-1)
        pages=[p+1 for p in candidates if document[p].get_images()]
        if len(pages)!=1 or pages[0] not in reviewed_set:
            raise RuntimeError("figure page not independently reviewed")
        p=pages[0]
        item.update(review_status="SOURCE_AND_RENDER_REVIEWED",rendered_pdf_sha256=sha,rendered_page=p,
                    source_file_sha256=digest(ROOT/item["source"]),
                    rendered_page_png_sha256=digest(QA/f"page-{p:03d}.png"),
                    visual_review_evidence="book/AGENT1_SCIENTIFIC_REVIEW.md#checkpoint-3")
        chapter_source=(ROOT/"book/chapters"/CHAPTERS[chapter]).read_text(encoding="utf-8")
        item["caption_vi"]=next(line.removeprefix("@figure ") for line in chapter_source.splitlines() if line.startswith("@figure "))
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    evidence_path=OUT/"validation.json"
    evidence=json.loads(evidence_path.read_text(encoding="utf-8"))
    original=json.loads(subprocess.check_output(["git","show",START+":book/evidence/agent1-scientific-review/validation.json"],cwd=ROOT))
    if {k:v for k,v in evidence.items() if k!="checkpoint3"}!=original:
        raise RuntimeError("previous checkpoints changed")
    cp=evidence["checkpoint3"]
    if cp["pdf"]["pdf_sha256"]!=sha:
        raise RuntimeError("visual review does not match tested PDF")
    compiler_text="\n".join(r["stderr_utf8"] for r in cp["results"]
        if "build" in r["command"] and "-a" in r["command"]).replace("\\","/")
    observations=[
        "fixed/render.go:13:6: cannot inline Render: function too complex: cost 231 exceeds budget 80",
        "fixed/render.go:13:13: readings does not escape",
        "fixed/render.go:16:18: inlining call to strings.(*Builder).WriteString",
        "fixed/render.go:18:36: inlining call to strconv.FormatInt",
        "fixed/render.go:16:18: append(strings.b.buf, strings.s...) escapes to heap in Render:",
        "fixed/render.go:15:20: Induction variable: limits [0,?), increment 1",
        "fixed/render.go:15:20: Inverted loop iteration",
        "fixed/render.go:21:19: Disproved Less64",
        "strings/strings.go:987:27: Proved IsInBounds",
        "strings/strings.go:988:38: Proved IsSliceInBounds"]
    cp["printed_compiler_observations"]={s:s in compiler_text for s in observations}
    if not all(cp["printed_compiler_observations"].values()):
        raise RuntimeError("printed compiler observation does not match actual pinned build")
    cp["pinned_toolchain_source_hashes"]["internal/buildcfg/exp.go"]=digest(Path(GO).parent.parent/"src/internal/buildcfg/exp.go")
    cp["manual_visual_review"]={"pdf_sha256":sha,"pages_actually_opened":reviewed,"count":len(reviewed),
        "not_opened":len(document)-len(reviewed),"resolution":"Poppler 144dpi individual pages, original resolution displayed",
        "page_png_sha256":{str(p):digest(QA/f"page-{p:03d}.png") for p in reviewed},
        "no_contact_sheet_substitution":True,"status":"SCOPED_MANUAL_REVIEW_ONLY_NOT_PUBLICATION_ACCEPTANCE"}
    # This is an explicit observation record, not an automatically accepted
    # previous layout. Those pages were opened before the final rebuild.
    intermediate=QA/"intermediate-d6bf.pdf"
    intermediate_sha="d6bf2b2df8ad097233777bc94d971e22ecdcf643f06ba005e85c55564e877dda"
    if not intermediate.exists() or digest(intermediate)!=intermediate_sha:
        raise RuntimeError("intermediate observation artifact missing or changed")
    cp["intermediate_manual_visual_review"]={
        "pdf_sha256":intermediate_sha,
        "pages_actually_opened":[2,51,52,53,*range(157,206)],
        "count":53,"not_final_pdf_acceptance":True,
        "issue":{"page":172,"finding":"R44","observed":"connector crosses result label",
                 "repair":"removed redundant edge label in PlantUML; data-flow arrow retained"}}
    cp["manual_visual_review"]["nonblocking_layout_observations"]=[
        {"page":160,"severity":"P3","observation":"long table terms wrap mid-word; text remains readable and unclipped"},
        {"page":188,"severity":"P3","observation":"Benchmark label wraps in table; text remains readable and unclipped"}]
    cp["visual_status"]="SCOPED_ACTUAL_PAGES_REVIEWED; REMAINDER_NOT_REVIEWED"
    finalization=[]
    for script in ["validate_visual_manifest","validate_diagram_semantics"]:
        finalization.append(run([sys.executable,"scripts/"+script+".py"]))
    finalization.extend([run(["git","diff","--check",START]),run(["git","diff","--cached","--check"])])
    cp["metadata_finalization"]={"recorded_at_utc":datetime.now(timezone.utc).isoformat(),"results":finalization}
    for key in cp["source_hashes"]:
        cp["source_hashes"][key]=digest(ROOT/key)
    cp["source_hashes"]["book/evidence/agent1-scientific-review/finalize_checkpoint3.py"]=digest(Path(__file__))
    for name in ["labs/part10-measure-first/.gitignore","labs/part10-measure-first/README.md"]:
        cp["source_hashes"][name]=digest(ROOT/name)
    evidence_path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for record in finalization:
        print(record["command"],record["exit_code"],record["stdout_utf8"][-100:])
    return int(any(r["exit_code"] for r in finalization))


if __name__=="__main__":
    raise SystemExit(main())
