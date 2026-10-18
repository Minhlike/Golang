"""Prepare scoped page renders; record only explicitly observed page numbers."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
import pymupdf as fitz
from PIL import Image
from finalization import ROOT, QA, PDF, START, blocks, digest
from checkpoint4 import chapter_pages

POPPLER=Path('C:/Users/Acer/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')

def prepare():
    sys.path.insert(0,str(ROOT/'scripts'))
    import build_pdf
    doc=fitz.open(PDF);sha=digest(PDF);out=QA/sha;out.mkdir(exist_ok=True)
    fidelity=json.loads((QA/'pdf_fidelity.json').read_text(encoding='utf-8'))
    if fidelity['sha256']!=sha:raise RuntimeError('fidelity PDF differs')
    normal=lambda s:re.sub(r'\s+','',unicodedata.normalize('NFC',s))
    render=lambda s:html.unescape(re.sub(r'<[^>]+>','',build_pdf.inline(s,'JetBrainsMono')))
    selected={2};reasons={2:['TOC']}
    for relative in subprocess.check_output(['git','diff','--name-only',START,'--','book/chapters','book/appendices'],cwd=ROOT,text=True).splitlines():
        path=ROOT/relative
        n=int(path.name[:2]) if path.parent.name=='chapters' else ('BACK MATTER' if path.name=='devops-library-atlas.md' else 'PHỤ LỤC A')
        old=subprocess.check_output(['git','show',START+':'+relative],cwd=ROOT).decode('utf-8')
        old= '\n'.join(re.sub(r'^> ?','',x) for x in old.splitlines())
        oldblocks=[body for _,_,body in re.findall(r'^(~~~|```)([^\n]*)\n(.*?)^\1[ \t]*$',old,re.M|re.S)]
        for i,(_,body) in enumerate(blocks(path),1):
            if body not in oldblocks:
                match=next(x for x in fidelity['code'] if x['section']==str(n) and x['block']==i)
                for p in match['pages']:selected.add(p);reasons.setdefault(p,[]).append(f'{n} changed fence {i}')
        added=[s[1:] for s in subprocess.check_output(['git','diff','--unified=0',START,'--',relative],cwd=ROOT).decode('utf-8').splitlines() if s.startswith('+') and not s.startswith('+++')]
        pages=list(chapter_pages(doc,n))
        for line in added:
            if len(line)<80 or line.startswith(('\t','    ','~~~','```','<!--')):continue
            line=re.sub(r'^(?:> ?|[-*] )','',line)
            expected=normal(render(line))[:90]
            for p in pages:
                if expected in normal(doc[p].get_text()):selected.add(p+1);reasons.setdefault(p+1,[]).append(f'{n} changed prose')
        if n==27:
            for p in pages:
                if 'bpf_map_lookup_elem(&counters, &key)' in doc[p].get_text():selected.add(p+1);reasons.setdefault(p+1,[]).append('27 quoted fence repair')
    # Changed native diagrams require actual final-PDF review, not old manifest labels.
    for item in json.loads((ROOT/'assets/visual-manifest.json').read_text(encoding='utf-8'))['assets']:
        relative=item['local_asset_path']
        original=subprocess.check_output(['git','show',START+':'+relative],cwd=ROOT)
        current=(ROOT/relative).read_bytes()
        if original==current:continue
        def pixelhash(data):
            from io import BytesIO
            with Image.open(BytesIO(data)) as im:
                rgb=im.convert('RGB');return hashlib.sha256(str(rgb.size).encode()+rgb.tobytes()).hexdigest()
        expected=pixelhash(current)
        with Image.open(ROOT/relative) as image:size=image.size
        checked={}
        for p in range(len(doc)):
            matches=[]
            for im in doc[p].get_images(full=True):
                if (im[2],im[3])!=size:continue
                if im[0] not in checked:checked[im[0]]=pixelhash(doc.extract_image(im[0])['image'])
                matches.append(checked[im[0]]==expected)
            if any(matches):
                for q in [p,p+1,p+2]:
                    if 1<=q<=len(doc):selected.add(q);reasons.setdefault(q,[]).append(f'changed figure {item["asset_id"]}, including boundary')
    # Review adjacent page boundaries of every changed fence.
    for p in list(selected):
        if any('fence' in r for r in reasons[p]):
            for q in [p-1,p+1]:
                if 1<=q<=len(doc):selected.add(q);reasons.setdefault(q,[]).append(f'boundary next to {p}')
    manifest={'pdf_sha256':sha,'pdf_pages':len(doc),'scope':'changed fences, changed prose and adjacent code page boundaries; NOT full-publication QA','pages':[{'page':p,'reasons':reasons[p],'visual_check':'NOT_REVIEWED'} for p in sorted(selected)]}
    target=out/'visual_manifest.json'
    if target.exists():raise RuntimeError('do not reset previous visual review')
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def one(p):
        subprocess.run([str(POPPLER),'-f',str(p),'-l',str(p),'-r','144','-singlefile','-png',str(PDF),str(out/f'page-{p}')],check=True,capture_output=True)
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(one,sorted(selected)))
    if digest(PDF)!=sha:raise RuntimeError('PDF changed during render; no visual observations accepted')
    print(sha,len(selected),sorted(selected),flush=True)

def observed(pages,issue=None):
    sha=digest(PDF);out=QA/sha;file=out/'visual_manifest.json';m=json.loads(file.read_text(encoding='utf-8'))
    if m['pdf_sha256']!=sha:raise RuntimeError('PDF changed')
    records={r['page']:r for r in m['pages']}
    for p in pages:
        record=records[p]
        if record['visual_check']!='NOT_REVIEWED':raise RuntimeError('already reviewed')
        image=out/f'page-{p}.png'
        with Image.open(image) as im:
            rgb=im.convert('RGB');r,g,b=rgb.split();gray=r.tobytes()==g.tobytes()==b.tobytes()
        record.update(visual_check='ISSUE:'+issue if issue else 'VISUAL_PASS',render_sha256=digest(image),grayscale_pixels_equal=gray,observation='Actual single page opened at original 144dpi resolution; checked code/text/figure legibility, boundaries, clipping and folio. Scoped, not whole-PDF acceptance.')
    file.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('observed',len([r for r in m['pages'] if r['visual_check']=='VISUAL_PASS']),'remaining',len([r for r in m['pages'] if r['visual_check']=='NOT_REVIEWED']))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','observed']);parser.add_argument('--pages');parser.add_argument('--issue');args=parser.parse_args()
    if args.mode=='prepare':prepare()
    else:
        if not args.pages:raise RuntimeError('explicit actually opened pages required')
        observed([int(p) for p in args.pages.split(',')],args.issue)
