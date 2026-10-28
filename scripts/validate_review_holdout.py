"""Before any engine evaluation: verify PDF/annotation assets and render every page."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess

from PIL import Image,ImageDraw,ImageFont,ImageChops
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'data/review-holdout-v0.1'
RENDER=ROOT/'tmp/pdfs/review-holdout-v0.1'
POPPLER='/Users/zhujiayi/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm'
def digest(b):return hashlib.sha256(b).hexdigest()

def main():
    destination=PACK/'preflight.json'
    if destination.exists():raise SystemExit('拒绝覆盖已核验快照。')
    manifest=json.loads((PACK/'cases.json').read_text());cases=manifest['cases']
    assert len(cases)==20 and len({c['case_id'] for c in cases})==20
    prior_hashes={digest(p.read_bytes()) for p in (ROOT/'output/pdf').rglob('*.pdf') if 'review-holdout-v0.1' not in p.parts}
    old_record_ids=set()
    for c in json.loads((ROOT/'data/pdf-variants-v0.1/cases.json').read_text())['cases']:
        old_record_ids.update(r[0] for r in c['records'])
    RENDER.mkdir(parents=True,exist_ok=True);verified=[]
    for c in cases:
        path=ROOT/c['path'];blob=path.read_bytes();assert digest(blob)==c['sha256'] and digest(blob) not in prior_hashes
        reader=PdfReader(BytesIO(blob),strict=True)
        if c['expected_reject']:assert reader.is_encrypted;assert reader.decrypt('synthetic-holdout-only')
        else:assert not reader.is_encrypted
        assert len(reader.pages)==c['page_count']==2
        texts=[p.extract_text() or '' for p in reader.pages]
        text='\n'.join(texts)
        assert all(s in text for s in ['模拟材料','PB-DEMO-01',c['case_id'],'SYN-SPEC-PB01-RevB'])
        assert all(r[0] in text for r in c['expected_text_records'])
        assert not old_record_ids & {r[0] for r in c['expected_text_records']}
        assert c['checks'] or c['expected_reject']
        images=sum(len(p.images) for p in reader.pages)
        if c['expected_visual_records']:assert images>=1 and all(r[0] not in text for r in c['expected_visual_records'])
        verified.append(dict(case_id=c['case_id'],path=c['path'],sha256=c['sha256'],pages=len(texts),page_text=texts,
            image_count=images,encrypted=c['expected_reject'],record_ids_present=True,prior_pdf_hash_disjoint=True,prior_record_ids_disjoint=True))
    def render(c):
        cmd=[POPPLER,'-r','85','-png']
        if c['expected_reject']:cmd+=['-upw','synthetic-holdout-only']
        cmd += [str(ROOT/c['path']),str(RENDER/c['case_id'])]
        run=subprocess.run(cmd,check=True,capture_output=True,text=True)
        return dict(case_id=c['case_id'],stderr=run.stderr)
    with ThreadPoolExecutor(max_workers=4) as pool:rendered=list(pool.map(render,cases))
    files=sorted(RENDER.glob('HO-??-?.png'));assert len(files)==40
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
    sheets=[]
    for start in range(0,len(files),8):
        contact=Image.new('RGB',(1920,1260),'#dfe5ec');d=ImageDraw.Draw(contact)
        for index,p in enumerate(files[start:start+8]):
            im=Image.open(p).convert('RGB');assert ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox()
            im.thumbnail((468,585));x=index%4*480+6;y=index//4*630+34
            contact.paste(im,(x,y));d.text((x,y-26),p.stem,font=font,fill='black')
        out=RENDER/f'contact-{start//8+1}.png';contact.save(out);sheets.append(str(out.relative_to(ROOT)))
    output=dict(validated_at=datetime.now(timezone.utc).isoformat(),production_engine_called=False,
        manifest_sha256=digest((PACK/'cases.json').read_bytes()),files=20,pages=40,
        text_records=sum(len(c['expected_text_records']) for c in cases if c.get('records_for_metric',True)),
        encrypted_records_excluded=10,visual_records=1,rendered_pages=len(files),rendered=rendered,contact_sheets=sheets,cases=verified)
    destination.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:output[k] for k in ['files','pages','text_records','visual_records','rendered_pages','production_engine_called']},ensure_ascii=False))

if __name__=='__main__':main()
