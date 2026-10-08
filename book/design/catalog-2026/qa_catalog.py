"""Independent measurements for the isolated catalog; no automatic VISUAL_PASS."""
from __future__ import annotations

import json

import numpy as np
import pymupdf as fitz
from pypdf import PdfReader

from build_catalog import HERE, ROOT, W, H, WIDTH, INNER, OUTER, TOP, BOTTOM, sha, dump, protected_snapshot, parse


def copy_probe(doc,reader):
    fixture=(HERE/"copy_fixture.txt").read_bytes()
    text=fixture.decode("utf-8")
    baseline_conversion=text.expandtabs(4)
    page=next(i for i,p in enumerate(doc) if "Code-copy laboratory" in p.get_text() and "QA fixture" in p.get_text())
    results={"fixture_sha256":sha(fixture),"literal_tabs":text.count("\t"),
             "expandtabs4_preserves_bytes":baseline_conversion.encode("utf-8")==fixture,
             "expanded_sha256":sha(baseline_conversion.encode("utf-8")),
             "reader_clipboard_tests":{"reader_1":"UNKNOWN: not performed", "reader_2":"UNKNOWN: not performed"},
             "extractors_are_not_pdf_readers":True,"catalog_page":page+1,"extractors":{}}
    for name,extracted in (("PyMuPDF",doc[page].get_text()),("pypdf",reader.pages[page].extract_text())):
        (HERE/("copy_extracted_"+name.lower()+".txt")).write_text(extracted,encoding="utf-8")
        results["extractors"][name]={"contains_exact_fixture":text in extracted,"tabs":extracted.count("\t"),
                                    "unicode_present":"Tiếng Việt: ă â ê ô ơ ư đ" in extracted,
                                    "actual_text_supported_for_exact_fixture":text in extracted}
    dump("copy_code_results.json",results)
    return results


def audit():
    snapshot=json.loads((HERE/"protected_snapshot.json").read_text(encoding="utf-8"))
    assert protected_snapshot()==snapshot,"Protected files have changed"
    inventory=json.loads((HERE/"object_inventory.json").read_text(encoding="utf-8"))
    live=[]
    for path in sorted((ROOT/"book/chapters").glob("*.md"))+sorted((ROOT/"book/appendices").glob("*.md")):
        for n in parse(path):
            live.append((path.relative_to(ROOT).as_posix(),n["line"],n["type"],sha(n["raw"].encode("utf-8"))))
    recorded=[(n["source"],n["line"],n["type"],n["sha256"]) for n in inventory["nodes"]]
    assert live==recorded,"Lossless AST drift"
    keys=set(live)
    for specimen in json.loads((HERE/"specimen_provenance.json").read_text(encoding="utf-8")):
        assert ("book/"+specimen["source"],specimen["line"],specimen["type"],specimen["sha256"]) in keys
    pdf=HERE/"catalog.pdf"
    doc=fitz.open(pdf); reader=PdfReader(pdf)
    navigation=json.loads((HERE/"catalog_navigation.json").read_text(encoding="utf-8"))
    outline=doc.get_toc()
    assert [(v["title"],v["page"]) for v in navigation]==[(v[1],v[2]) for v in outline]
    for entry in navigation:
        assert " ".join(entry["title"].split()) in " ".join(doc[entry["page"]-1].get_text().split()),entry
    render=HERE/"renders"; render.mkdir(exist_ok=True)
    measurements=[]
    for i,page in enumerate(doc,1):
        assert abs(page.rect.width-W)<.01 and abs(page.rect.height-H)<.01
        assert page.rotation==0 and page.mediabox==page.cropbox
        left=INNER if i%2 else OUTER
        offenders=[]; fontnames=set(); folio=[]; text=page.get_text("dict")
        spans=[]
        for block in text["blocks"]:
            if block["type"]!=0:continue
            for line in block["lines"]:
                for s in line["spans"]:
                    spans.append(s); fontnames.add(s["font"])
                    x0,y0,x1,y1=s["bbox"]
                    is_chrome=(s["text"]=="GOLANG / DESIGN PROTOTYPE 2026") or (s["text"]==str(i) and y0>H-45)
                    if s["text"]==str(i) and y0>H-45:folio.append(s["bbox"])
                    if not is_chrome and (x0<left-1 or x1>left+WIDTH+1 or y0<TOP-1 or y1>H-BOTTOM+1):
                        offenders.append({"text":s["text"],"bbox":s["bbox"]})
                    assert "\ufffd" not in s["text"],"Replacement glyph"
        assert folio,"Folio missing"
        if i%2:assert abs(folio[0][2]-(left+WIDTH))<1
        else:assert abs(folio[0][0]-left)<1
        pix=page.get_pixmap(matrix=fitz.Matrix(150/72,150/72),colorspace=fitz.csRGB)
        image=render/f"catalog-{i:03d}.png"; pix.save(image)
        rgb=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3).astype(np.int16)
        maxdiff=int(np.max(np.max(rgb,axis=2)-np.min(rgb,axis=2)))
        assert maxdiff<=1,f"Non-grayscale page {i}"
        body=[s for s in spans if s["text"] not in (str(i),"GOLANG / DESIGN PROTOTYPE 2026")]
        assert body,"Blank page"
        bitmaps=[]
        for img in page.get_image_info():
            box=fitz.Rect(img["bbox"])
            if box.width and box.height:
                bitmaps.append({"width_px":img["width"],"height_px":img["height"],"effective_dpi_x":round(img["width"]*72/box.width,1),"effective_dpi_y":round(img["height"]*72/box.height,1)})
        measurements.append({"page":i,"frame_left_pt":round(left,3),"folio_bbox":folio[0],"fonts":sorted(fontnames),
                             "frame_offenders":offenders,"grayscale_max_channel_difference":maxdiff,"raster_images":bitmaps,
                             "render_sha256":sha(image.read_bytes()),"visual_check":"NOT_REVIEWED"})
    embedded=[]
    for i,page in enumerate(reader.pages,1):
        for font in page["/Resources"].get_object()["/Font"].get_object().values():
            f=font.get_object()
            if "/FontDescriptor" in f:
                descriptor=f["/FontDescriptor"].get_object()
                assert any(k in descriptor for k in ("/FontFile","/FontFile2","/FontFile3"))
                embedded.append(str(f.get("/BaseFont")))
            elif f.get("/BaseFont")!="/Helvetica":
                raise AssertionError(f"Unexpected unembedded font {f}")
    # ReportLab adds an unused Helvetica resource. Check actual rendered spans;
    # only embedded Source/JetBrains fonts must be used for text.
    assert all(not any("Helvetica" in n for n in p["fonts"]) for p in measurements)
    links=doc[0].get_links()
    assert len(links)==12 and all(v["kind"]==fitz.LINK_GOTO and 0<=v["page"]<len(doc) for v in links)
    expected_keys=["cover-A","cover-B","cover-C","cover-D","system","chapter","figure","question","answer","library","atlas","copy"]
    destinations={v["key"]:v["page"]-1 for v in navigation}
    assert [v["page"] for v in links]==[destinations[key] for key in expected_keys]
    result={"scope":"catalog only; not full-book publication QA","pdf_sha256":sha(pdf.read_bytes()),"page_count":len(doc),
            "protected_files_unchanged":len(snapshot),"lossless_ast_blocks_checked":len(live),
            "specimen_raw_hashes":"PASS","A4_crop_rotation":"PASS","mirrored_frame":"PASS" if not any(p["frame_offenders"] for p in measurements) else "FAIL",
            "grayscale_pixel_scan":"PASS: RGB channel delta <= 1 on every 150 dpi page",
            "folio_position":"PASS","fonts_used_embedded":"PASS","unused_base14_resource":"Helvetica; not used in rendered text",
            "TOC_links":"PASS: 12 internal destinations", "bookmarks":"PASS: titles and destinations match rendered headings",
            "pages":measurements,"copy_probe":copy_probe(doc,reader)}
    ledger=HERE/"visual_review.json"
    if ledger.exists():
        review=json.loads(ledger.read_text(encoding="utf-8"))
        if review["pdf_sha256"]==result["pdf_sha256"]:
            assert [r["page"] for r in review["pages"]]==list(range(1,len(doc)+1))
            for measured,observed in zip(measurements,review["pages"]):
                measured["visual_check"]=observed["status"]
                measured["observation"]=observed["observation"]
            result["visual_review"]="23 individually opened final pages; manual ledger matches SHA"
        else:
            result["visual_review"]="INVALIDATED: ledger belongs to a different PDF; all pages NOT_REVIEWED"
    dump("qa_results.json",result)
    print(json.dumps({k:v for k,v in result.items() if k not in ("pages","copy_probe")},ensure_ascii=False,indent=2))


if __name__=="__main__":audit()
