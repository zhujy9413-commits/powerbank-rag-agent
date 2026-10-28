"""Input-only QA; production parser/engine is not invoked."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import unicodedata
from pypdf import PdfReader
from PIL import Image,ImageDraw,ImageFont,ImageChops

ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'data/p1-holdout-v0.1';RENDER=ROOT/'tmp/pdfs/p1-holdout-v0.1'
POPPLER='/Users/zhujiayi/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm'
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return ''.join(unicodedata.normalize('NFKC',s).split())

def main():
    out=PACK/'preflight.json'
    if out.exists():raise SystemExit('拒绝覆盖核验快照。')
    cases=json.loads((PACK/'cases.json').read_text())['cases'];assert len(cases)==20
    old_hashes={sha(p.read_bytes()) for p in (ROOT/'output/pdf').rglob('*.pdf') if 'p1-holdout-v0.1' not in p.parts}
    old_ids=set()
    for name in ['pdf-variants-v0.1','review-holdout-v0.1','p0-holdout-v0.1']:
        for c in json.loads((ROOT/'data'/name/'cases.json').read_text())['cases']:
            old_ids.update(r[0] for r in c.get('expected_text_records',c.get('expected_records',[])) if r[0])
    rows=[];RENDER.mkdir(parents=True,exist_ok=True)
    for c in cases:
        p=ROOT/c['path'];assert sha(p.read_bytes())==c['sha256'] and c['sha256'] not in old_hashes
        reader=PdfReader(p,strict=True);assert not reader.is_encrypted and len(reader.pages)==2
        texts=[p.extract_text() or '' for p in reader.pages];combined=norm(''.join(texts))
        for rid,port,kind,value in c['expected_text_records']:
            assert rid in combined and rid not in old_ids,(c['case_id'],rid)
            if c['case_id']=='HP-17' and rid=='R3302':
                assert norm('R3302 C1 保护响应 0.394') in norm(texts[0])
                assert '续表A(接上页单位)' in unicodedata.normalize('NFKC',texts[1]) and 's' in texts[1].splitlines()
            else:assert norm(value) in combined,(c['case_id'],value)
        for page,quote,kind,rid in c['expected_unit_owners']:
            assert norm(quote) in [norm(s) for s in texts[page-1].splitlines()],(c['case_id'],quote)
        assert all(s in ''.join(texts) for s in ['模拟材料','PB-DEMO-01',c['case_id'],'RevB'])
        assert all(len(p.images)==0 for p in reader.pages)
        fonts=[font.get_object() for p in reader.pages for font in p['/Resources']['/Font'].get_object().values()]
        assert any('/FontDescriptor' in f and '/FontFile2' in f['/FontDescriptor'].get_object() for f in fonts),'必须嵌入字体'
        rows.append(dict(case_id=c['case_id'],sha256=c['sha256'],new_pdf_hash=True,new_record_ids=True,page_text=texts,embedded_font=True))
    def render(c):
        run=subprocess.run([POPPLER,'-r','85','-png',str(ROOT/c['path']),str(RENDER/c['case_id'])],check=True,capture_output=True,text=True)
        return dict(case_id=c['case_id'],stderr=run.stderr)
    with ThreadPoolExecutor(max_workers=4) as pool:logs=list(pool.map(render,cases))
    pages=sorted(RENDER.glob('HP-??-?.png'));assert len(pages)==40
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18);sheets=[]
    for start in range(0,40,8):
        sheet=Image.new('RGB',(1920,1260),'#e3e8ef');draw=ImageDraw.Draw(sheet)
        for index,p in enumerate(pages[start:start+8]):
            im=Image.open(p).convert('RGB');assert ImageChops.difference(im,Image.new('RGB',im.size,'white')).getbbox()
            im.thumbnail((468,585));x=index%4*480+6;y=index//4*630+34;sheet.paste(im,(x,y));draw.text((x,y-26),p.stem,font=font,fill='black')
        p=RENDER/f'contact-{start//8+1}.png';sheet.save(p);sheets.append(str(p.relative_to(ROOT)))
    result=dict(validated_at=datetime.now(timezone.utc).isoformat(),production_engine_called=False,files=20,pages=40,expected_text_records=200,
        rendered_pages=40,render_logs=logs,contact_sheets=sheets,cases=rows)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['files','pages','expected_text_records','production_engine_called']},ensure_ascii=False))

if __name__=='__main__':main()
