"""Input QA only: no imports of the production parser, review engine, or labels from old builders."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

from pypdf import PdfReader
from PIL import Image,ImageDraw,ImageFont,ImageChops

ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'data/p0-holdout-v0.1';RENDER=ROOT/'tmp/pdfs/p0-holdout-v0.1'
POPPLER='/Users/zhujiayi/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm'
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    out=PACK/'preflight.json'
    if out.exists():raise SystemExit('拒绝覆盖核验快照。')
    cases=json.loads((PACK/'cases.json').read_text())['cases'];assert len(cases)==20
    old_hashes={sha(p.read_bytes()) for p in (ROOT/'output/pdf').rglob('*.pdf') if 'p0-holdout-v0.1' not in p.parts}
    old_ids=set()
    for name in ['data/pdf-variants-v0.1/cases.json','data/review-holdout-v0.1/cases.json']:
        for c in json.loads((ROOT/name).read_text())['cases']:old_ids.update(r[0] for r in c.get('expected_text_records',c.get('records',[])) if r[0])
    verified=[];RENDER.mkdir(parents=True,exist_ok=True)
    for c in cases:
        p=ROOT/c['path'];b=p.read_bytes();assert sha(b)==c['sha256'] and sha(b) not in old_hashes
        r=PdfReader(p,strict=True);assert not r.is_encrypted and len(r.pages)==2
        texts=[p.extract_text() or '' for p in r.pages];text=''.join(''.join(texts).split())
        for rid,port,kind,value in c['expected_text_records']:
            assert not rid or rid in text,(c['case_id'],rid)
            assert ''.join(value.split()) in text,(c['case_id'],value)
            assert rid not in old_ids,(c['case_id'],rid)
        assert all(s in ''.join(texts) for s in ['模拟材料','PB-DEMO-01',c['case_id'],'RevB'])
        for row in c['expected_visual_records']:assert row[0] not in text
        # Resource enumeration is independent of production's actual drawing-operation inspection.
        resource_images=sum(len(p.images) for p in r.pages)
        if c['image_draws_expected']:assert resource_images>=1,c['case_id']
        if c['case_id']=='HN-17':assert resource_images>=1
        verified.append(dict(case_id=c['case_id'],sha256=c['sha256'],page_text=texts,resource_images=resource_images,new_pdf_hash=True,new_record_ids=True))
    def render(c):
        run=subprocess.run([POPPLER,'-r','85','-png',str(ROOT/c['path']),str(RENDER/c['case_id'])],check=True,capture_output=True,text=True)
        return dict(case_id=c['case_id'],stderr=run.stderr)
    with ThreadPoolExecutor(max_workers=4) as pool:logs=list(pool.map(render,cases))
    pages=sorted(RENDER.glob('HN-??-?.png'));assert len(pages)==40
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18);sheets=[]
    for start in range(0,40,8):
        sheet=Image.new('RGB',(1920,1260),'#dfe5ec');draw=ImageDraw.Draw(sheet)
        for index,p in enumerate(pages[start:start+8]):
            im=Image.open(p).convert('RGB');assert ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox()
            im.thumbnail((468,585));x=index%4*480+6;y=index//4*630+34;sheet.paste(im,(x,y));draw.text((x,y-26),p.stem,font=font,fill='black')
        p=RENDER/f'contact-{start//8+1}.png';sheet.save(p);sheets.append(str(p.relative_to(ROOT)))
    result=dict(validated_at=datetime.now(timezone.utc).isoformat(),production_engine_called=False,files=20,pages=40,
        expected_text_records=sum(len(c['expected_text_records']) for c in cases),visual_records=3,rendered_pages=40,render_logs=logs,contact_sheets=sheets,cases=verified)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['files','pages','expected_text_records','visual_records','production_engine_called']},ensure_ascii=False))

if __name__=='__main__':main()
