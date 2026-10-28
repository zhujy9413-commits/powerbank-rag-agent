"""New synthetic evaluation material; no production parser or old fixture imports."""
from copy import deepcopy
from io import BytesIO
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'data/review-holdout-v0.1'
PDFS = ROOT / 'output/pdf/review-holdout-v0.1'
GLOBAL = '本报告测试条件：电压=5 V；角色=输出；组合=单口'
BASE = [
    ['R101','A1','response','137 ms'], ['R102','C1','response','0.243 s'],
    ['R103','A1','recovery','4.92 V'], ['R104','C1','recovery','5.17 V'],
    ['R105','A1','temperature','23.5摄氏度 / 32.0摄氏度'],
    ['R106','C1','temperature','24.5摄氏度 / 35.0摄氏度'],
    ['R107','A1','appearance','无起火、无爆炸、无漏液'],
    ['R108','C1','appearance','无起火、无爆炸、无漏液'],
    ['R109','A1','method','记录为移除负载后重新接入'],
    ['R110','C1','method','记录为重新连接输出负载'],
]
LABEL = dict(response='保护响应',recovery='恢复电压',temperature='壳温起值/末值',appearance='外观观察',method='恢复方式')
ITEMS = ['A1-01','A1-02','A1-03','A1-04','A1-05','C1-01','C1-02','C1-03','C1-04','C1-05']

def designs():
    names = [
        ('boundaries','新数值与边界组合'), ('outside','边界外数值组合'),
        ('canonical','全角条件与别名混排'), ('foreign-id','补充记录使用TC编号'),
        ('long-id','记录ID为五位数字'), ('broken-label','字段名在单元格内换行'),
        ('mixed-raster','同页文字与图片补充记录混排'), ('footnote','实际条件写在脚注'),
        ('section-scope','表标题指定局部条件'), ('repeated-dimension','单行重复且矛盾的电压声明'),
        ('unknown-role','行内角色明确为未记录'), ('two-contexts','同字段存在5V与12V两条记录'),
        ('unknown-environment','摘要环境明确为未记录'), ('load-context','明细与摘要负载条件不同'),
        ('specimen-context','同字段来自不同样机'), ('condition-before','跨页且条件位于记录之前'),
        ('summary-wrap','摘要数值与单位跨行'), ('header-unit','单位仅写在列标题'),
        ('local-only','仅一条记录有完整条件'), ('encrypted','加密报告应拒绝'),
    ]
    cases=[]
    for n,(slug,title) in enumerate(names,1):
        c=dict(case_id=f'HO-{n:02d}',slug=slug,title=title,records=deepcopy(BASE),global_line=GLOBAL,
               capture_required=True,expected_reject=False,checks=[],visible_issue_required=False,
               summary='S41：A1保护响应 137 ms',row_suffix={},row_after={})
        if slug=='boundaries':
            for i,v in {0:'500 ms',1:'0.500 s',2:'4.75 V',3:'5.25 V',4:'21.0摄氏度 / 33.0摄氏度',5:'22.0摄氏度 / 34.0摄氏度'}.items():c['records'][i][3]=v
            c['summary']='S41：A1保护响应 0.500 s'
            c['checks']=[dict(item_id=i,result='no_issue') for i in ITEMS]
        if slug=='outside':
            for i,v in {0:'501 ms',1:'0.501 s',2:'4.74 V',3:'5.26 V',4:'21.0摄氏度 / 33.1摄氏度',5:'22.0摄氏度 / 34.1摄氏度'}.items():c['records'][i][3]=v
            c['summary']='S41：A1保护响应 501 ms'
            c['checks']=[dict(item_id=i,result='nonconformity') for i in ['A1-01','A1-02','A1-03','C1-01','C1-02','C1-03']]
        if slug=='canonical':
            c['global_line']='本报告测试条件：电压=５．０ V；角色=输出；组合=单口；环境=２３．５摄氏度'
            c['summary']='S41：A1保护响应 0.137 s；条件：电压=5 V；角色=输出；组合=单口；环境=23.50摄氏度'
            c['checks']=[dict(item_id='SUMMARY-A1',result='no_issue')]
        if slug=='foreign-id':
            c['records'].append(['TC-401','A1','response','913 ms'])
            c.update(capture_required=False,visible_issue_required=True)
            c['checks']=[dict(item_id='A1-01',blocked=True,execution='not_checked')]
        if slug=='long-id':
            for i,r in enumerate(c['records'],50001):r[0]='R'+str(i)
            c.update(capture_required=False,visible_issue_required=True)
            c['checks']=[dict(item_id=i,blocked=True,execution='not_checked') for i in ITEMS]
        if slug=='broken-label':
            c.update(capture_required=False,visible_issue_required=True)
            c['checks']=[dict(item_id='A1-02',blocked=True,execution='not_checked')]
        if slug=='mixed-raster':
            c['visual_records']=[['R711','A1','response','927 ms']]
            c['visible_issue_required']=True
            c['checks']=[dict(item_id='A1-01',blocked=True,execution='not_checked')]
        if slug=='footnote':
            c['footnote']='注：R101实际测试条件为电压=12 V；角色=输入；组合=多口。'
            c['checks']=[dict(item_id='A1-01',blocked=True,execution='not_checked')]
        if slug=='section-scope':
            c['checks']=[dict(item_id=i,blocked=True,execution='not_checked') for i in ITEMS[:5]]
        if slug=='repeated-dimension':
            c['row_suffix']['R101']='；条件：电压=5 V；电压=12 V；角色=输出；组合=单口'
            c['checks']=[dict(item_id='A1-01',blocked=True,execution='not_checked')]
        if slug=='unknown-role':
            c['row_after']['R102']='条件：电压=5 V；角色=未记录；组合=单口'
            c['checks']=[dict(item_id='C1-01',blocked=True,execution='not_checked')]
        if slug=='two-contexts':
            c['records'].append(['R611','A1','response','0.779 s'])
            c['row_suffix']['R611']='；条件：电压=12 V；角色=输出；组合=单口'
            c['checks']=[dict(item_id='A1-01',blocked=True,execution='not_checked')]
        if slug=='unknown-environment':
            c['global_line']+='；环境=23.5摄氏度'
            c['summary']='S41：A1保护响应 0.837 s；条件：环境=未记录'
            c['checks']=[dict(item_id='SUMMARY-A1',result='evidence_insufficient',execution='not_checked'),dict(item_id='A1-01',conditional=False)]
        if slug=='load-context':
            c['row_suffix']['R101']='；条件：负载=2.0 A'
            c['summary']='S41：A1保护响应 0.837 s；条件：负载=0.5 A'
            c['checks']=[dict(item_id='SUMMARY-A1',result='evidence_insufficient',execution='not_checked'),dict(item_id='A1-01',conditional=False)]
        if slug=='specimen-context':
            c['row_suffix']['R101']='；条件：样机=SN-A'
            c['records'].append(['R612','A1','response','0.819 s'])
            c['row_suffix']['R612']='；条件：样机=SN-B'
            c['checks']=[dict(item_id='A1-01',result='evidence_insufficient',execution='not_checked',blocked=True)]
        if slug=='condition-before':
            c['visible_issue_required']=True
            c['checks']=[dict(item_id='C1-01',blocked=True,execution='not_checked')]
        if slug=='summary-wrap':
            c['summary']='S41：A1保护响应 0.137\ns'
            c['checks']=[dict(item_id='SUMMARY-MISSING',result='evidence_insufficient')]
        if slug=='header-unit':
            c['records'][0][3]='137';c['records'][1][3]='243'
            c['checks']=[dict(item_id=i,blocked=True) for i in ['A1-01','C1-01']]
        if slug=='local-only':
            c['global_line']='测试条件在相应记录旁列出，其他记录未填写。'
            c['row_after']['R101']='条件：电压=5 V；角色=输出；组合=单口'
            c['checks']=[dict(item_id='A1-01',result='no_issue')]+[dict(item_id=i,blocked=True,execution='not_checked') for i in ITEMS if i!='A1-01']
        if slug=='encrypted':c.update(expected_reject=True,capture_required=False,records_for_metric=False)
        cases.append(c)
    return cases

def create_pdf(case):
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    from PIL import Image,ImageDraw,ImageFont
    font='/System/Library/Fonts/Supplemental/Songti.ttc'
    pdfmetrics.registerFont(TTFont('HoldoutSong',font,subfontIndex=0))
    buf=BytesIO();c=canvas.Canvas(buf,pagesize=(720,900),invariant=1)
    def line(s,y,size=11,x=36):
        c.setFont('HoldoutSong',size);c.drawString(x,y,s)
    def header(page):
        line('模拟整机保护功能测试报告',858,18)
        line('模拟材料 / PB-DEMO-01 / '+case['case_id']+' / 新样本留出评测',831)
        line('报告填写的规格版本：SYN-SPEC-PB01-RevB',808)
        line(f'第{page}页 / 共2页',26,9)
    header(1);line(case['global_line'],780,10)
    line('记录表A',752,13)
    y=721
    if case['slug']=='section-scope':
        line('本表局部条件：电压=12 V；角色=输出；组合=单口',y,10);y-=27
    # Page 1: A1 records; page 2: C1 records. The design never reuses the old builder.
    for page,port in [(1,'A1'),(2,'C1')]:
        if page==2:
            c.showPage();header(2);line('记录表B',780,13);y=748
            if case['slug']=='condition-before':line('条件：电压=12 V；角色=输出；组合=单口',y,10);y-=24
        for r in (r for r in case['records'] if r[1]==port):
            rid,p,kind,value=r;label=LABEL[kind]
            if case['slug']=='canonical':label={'response':'短路保护响应时间','recovery':'保护后恢复电压'}.get(kind,label)
            if case['slug']=='broken-label' and rid=='R103':
                for v in [rid,p,'保护后','恢复电压',value]:line(v,y);y-=19
            elif case['slug']=='header-unit' and kind=='response':
                line('记录 | 端口 | 字段 | 原始填写 | 报告填写判定',y,10);y-=23
                line('本段保护响应数值单位：ms',y,10);y-=23
                line(' | '.join([rid,p,label,value,'待复核']),y);y-=28
            else:
                line(' '.join([rid,p,label,value])+case['row_suffix'].get(rid,''),y,10);y-=33
            if rid in case['row_after']:line(case['row_after'][rid],y,10);y-=27
        if page==1:
            if case.get('footnote'):line(case['footnote'],y-8,10);y-=36
            if case.get('visual_records'):
                image=Image.new('RGB',(1250,90),'white');d=ImageDraw.Draw(image)
                d.text((12,22),'R711 A1 保护响应 927 ms',font=ImageFont.truetype(font,29),fill='#111111')
                c.drawImage(ImageReader(image),36,y-53,width=625,height=45);y-=70
            line('评测材料，不用于真实产品合规或实验操作。',y-30,9)
        else:
            for s in case['summary'].splitlines():line(s,y-15,10);y-=23
    c.save();blob=buf.getvalue()
    if case['expected_reject']:
        from pypdf import PdfReader,PdfWriter
        writer=PdfWriter();writer.append_pages_from_reader(PdfReader(BytesIO(blob)))
        writer.encrypt('synthetic-holdout-only')
        out=BytesIO();writer.write(out);blob=out.getvalue()
    return blob

def main():
    if (PACK/'cases.json').exists() or PDFS.exists():raise SystemExit('拒绝覆盖留出样本；必须使用新版本。')
    PACK.mkdir(parents=True,exist_ok=True);PDFS.mkdir(parents=True)
    out=[]
    for case in designs():
        blob=create_pdf(case);path=PDFS/(case['case_id']+'-'+case['slug']+'.pdf');path.write_bytes(blob)
        # Label values come from the predeclared design, never extracted parser output.
        entry={k:v for k,v in case.items() if k not in ['row_suffix','row_after','global_line','summary']}
        entry.update(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(blob).hexdigest(),page_count=2,
                     expected_text_records=case['records'],expected_visual_records=case.get('visual_records',[]))
        entry.pop('records');entry.pop('visual_records',None);out.append(entry)
    (PACK/'cases.json').write_text(json.dumps(dict(version='review-holdout-v0.1',label_author='same project author; implementation-aware',
        external_independence=False,professional_review='pending',cases=out),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(files=len(out),pages=sum(c['page_count'] for c in out)),ensure_ascii=False))

if __name__=='__main__':main()
