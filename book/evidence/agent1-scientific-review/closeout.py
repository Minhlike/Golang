"""Freeze actual scoped observations and independently checked invariants."""
from datetime import datetime, timezone
import json
import subprocess
from pathlib import Path
from finalization import ROOT, OUT, QA, PDF, START, digest


def main():
    evidence=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
    final=evidence['finalization']
    sha=digest(PDF)
    if final['pdf_4']['sha256']!=sha or final['pdf_4_status']!='PASS':
        raise RuntimeError('final PDF evidence mismatch')
    if final['tests_2_status']!='PASS' or final['gates_4_status']!='PASS':
        raise RuntimeError('final regression/gates incomplete')
    visual=json.loads((QA/sha/'visual_manifest.json').read_text(encoding='utf-8'))
    if visual['pdf_sha256']!=sha:raise RuntimeError('visual PDF mismatch')
    if any(p['visual_check']=='NOT_REVIEWED' for p in visual['pages']):
        raise RuntimeError('scoped pages still unreviewed')
    for record in visual['pages']:
        if digest(QA/sha/f'page-{record["page"]}.png')!=record['render_sha256']:
            raise RuntimeError('observed render changed')
    targets={
        'D:/Golang/Golang_Master.pdf':'7dfedd9825d36ccfb57515311829bc163bb6eb746423487488419400c36d8b68',
        'D:/Golang/Golang_Master.prev.pdf':'685b0b7a51ed9d3ab5a9b531f040a4ed24132d94142972811d3b47e52daeaa8f',
        str(ROOT/'MASTER PROMPT.txt'):'45da2eb45b88d36fb5cfc95b63547b01274d618b8b8c6256efce4766f2c34785',
        str(ROOT/'scripts/build_pdf.py'):'f6f6a0c662a33a979b41fa4ee7656c9f110fdaa379eb7cf04832f69b01ede9f7',
        str(ROOT/'assets/diagrams/publication-flow.iuml'):'7814eeea002e42136464ce08cf5fe1de41b0d452be6938acb341dd8462681a9e',
        'D:/Golang/MASTER PROMPT.txt':'bd93e286595e9b45812b09d40124966137300d010fe19d063b860a564947d125',
    }
    protected={p:digest(Path(p)) for p in targets}
    if protected!=targets:raise RuntimeError('protected artifact changed')
    def git(*args,cwd=ROOT):
        return subprocess.check_output(['git',*args],cwd=cwd).decode('utf-8').strip()
    if git('status','--porcelain',cwd='D:/Golang'):
        raise RuntimeError('Agent2 worktree not clean; report actual state')
    if git('branch','--show-current')!='content/agent1-master-scientific-review':
        raise RuntimeError('wrong review branch')
    chapters=sorted(ROOT.glob('book/chapters/*.md'))
    if len(chapters)!=31:raise RuntimeError('unexpected chapter coverage')
    output={
        'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'starting_head':START,'parent_before_final_commit':git('rev-parse','HEAD'),
        'main':git('rev-parse','main'),'origin_main':git('rev-parse','origin/main'),
        'agent2_head':git('rev-parse','HEAD',cwd='D:/Golang'),
        'agent2_branch':git('branch','--show-current',cwd='D:/Golang'),
        'protected_sha256':protected,'candidate_sha256':sha,
        'chapter_files':{p.relative_to(ROOT).as_posix():digest(p) for p in chapters},
        'manual_reading_scope':'31 complete chapter manuscripts and two complete Atlas; reading is not execution of every claim',
        'final_pdf_evidence_key':'validation.json/finalization/pdf_4',
        'regression_evidence_key':'validation.json/finalization/tests_2',
        'scoped_visual_review':visual,
        'scoped_visual_pass':sum(p['visual_check']=='VISUAL_PASS' for p in visual['pages']),
        'scoped_visual_issues':[p for p in visual['pages'] if p['visual_check'].startswith('ISSUE:')],
        'whole_pdf_pages_not_opened':visual['pdf_pages']-len(visual['pages']),
        'issue_details':{'V04':{'severity':'P3','page':535,'description':'Curriculum Parts I-IX in summary table differ from PDF TOC Parts I-IV; structural/edition mismatch remains, outside design branch authority.'}},
        'scientific_review_status':'COMPLETE_WITH_VERIFICATION_LIMITS',
        'publication_status':'NOT_FULL_PUBLICATION_ACCEPTANCE',
        'no_new_chapters':True,'no_main_merge':True,'no_master_promotion':True,
    }
    target=OUT/'final_visual_review.json'
    if target.exists():raise RuntimeError('do not overwrite frozen closeout')
    target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('closed',len(visual['pages']),'actually opened pages; whole-publication acceptance NOT claimed')


if __name__=='__main__':main()
