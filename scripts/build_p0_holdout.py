"""Construct new post-fix synthetic inputs without importing production code or old builders."""
from copy import deepcopy
from io import BytesIO
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'data/p0-holdout-v0.1'
OUT=ROOT/'output/pdf/p0-holdout-v0.1'
LABEL=dict(response='保护响应',recovery='恢复电压',temperature='壳温起值/末值',appearance='外观观察',method='恢复方式')
ROWS=[['R2201','A1','response','209 ms'],['R2202','C1','response','0.311 s'],
      ['R2203','A1','recovery','4.83 V'],['R2204','C1','recovery','5.21 V'],
      ['R2205','A1','temperature','19.5摄氏度 / 30.5摄氏度'],['R2206','C1','temperature','20.0摄氏度 / 30.0摄氏度'],
      ['R2207','A1','appearance','无起火、无爆炸、无漏液'],['R2208','C1','appearance','无起火、无爆炸、无漏液'],
      ['R2209','A1','method','记录为取下测试负载后重新接入'],['R2210','C1','method','记录为重新接入负载端']]
ITEMS=[p+f'-{n:02d}' for p in ['A1','C1'] for n in range(1,6)]

def designs():
    titles=['正常新数值控制','不符合新数值控制','新外文编号补充记录','竖排长编号记录','中文编号分隔列',
            '换列后的外文编号','表格前的混排图片','嵌套Form中的图片','内联图片记录','装饰图也须人工核验',
            '跨页脚注指向前页记录','指定端口的本段工况','作用范围不明的局部声明','支持格式的行内9V',
            '文字化备注指向后页记录','局部条件引用不存在记录','未绘制图片资源不误报警','缺少编号的额外记录',
            '中文冒号与逗号的局部条件','无数字编号的恢复方式记录']
    out=[]
    for n,title in enumerate(titles,1):
        c=dict(case_id=f'HN-{n:02d}',title=title,records=deepcopy(ROWS),capture_required=True,
               visible_issue_required=False,expected_reject=False,expected_visual_records=[],checks=[],image_draws_expected=0,
               summary='S61：A1保护响应 209 ms',notes={},suffix={})
        def block(ids):return [dict(item_id=i,blocked=True,execution='not_checked') for i in ids]
        if n==1:c['checks']=[dict(item_id=i,result='no_issue') for i in ITEMS]
        if n==2:
            for i,v in {0:'571 ms',1:'0.693 s',2:'4.71 V',3:'5.32 V',4:'19.5摄氏度 / 33.0摄氏度',5:'20.0摄氏度 / 34.0摄氏度'}.items():c['records'][i][3]=v
            c['summary']='S61：A1保护响应 571 ms'
            c['checks']=[dict(item_id=i,result='nonconformity') for i in ['A1-01','C1-01','A1-02','C1-02','A1-03','C1-03']]
        if n==3:
            c['records'].append(['CHECK-8801','A1','response','859 ms']);c.update(capture_required=False,visible_issue_required=True)
            c['checks']=block(['A1-01'])+[dict(item_id='C1-01',result='no_issue')]
        if n==4:
            for i,r in enumerate(c['records'],88761):r[0]='R'+str(i)
            c.update(capture_required=False,visible_issue_required=True);c['checks']=block(ITEMS)
        if n==5:
            c['records'].append(['补测丙','C1','recovery','5.77 V']);c.update(capture_required=False,visible_issue_required=True)
            c['checks']=block(['C1-02'])+[dict(item_id='A1-02',result='no_issue')]
        if n==6:
            c['records'].append(['CHK-37','A1','response','889 ms']);c.update(capture_required=False,visible_issue_required=True)
            c['checks']=block(['A1-01'])+[dict(item_id='C1-01',result='no_issue')]
        if n in [7,8,9,10]:
            c.update(visible_issue_required=True,image_draws_expected=1);c['checks']=block(ITEMS)
            if n!=10:c['expected_visual_records']=[['IMG-990'+str(n),'C1','response',str(900+n)+' ms']]
        if n==11:
            c['notes'][2]='脚注：R2201实际测试条件为电压=12 V；角色=输入；组合=多口。'
            c['checks']=block(['A1-01'])+[dict(item_id='C1-01',result='no_issue')];c['visible_issue_required']=True
        if n==12:
            c['notes'][2]='C1本段工况：电压=9 V；角色=输出；组合=单口'
            c['checks']=block(ITEMS[5:])+[dict(item_id='A1-01',result='no_issue')];c['visible_issue_required']=True
        if n==13:
            c['notes'][1]='本段局部条件：电压=12 V；角色=输出；组合=单口'
            c['checks']=block(ITEMS);c['visible_issue_required']=True
        if n==14:
            c['suffix']['R2201']='；条件：电压=9 V；角色=输出；组合=单口'
            c['checks']=block(['A1-01'])+[dict(item_id='A1-02',result='no_issue')]
        if n==15:
            c['notes'][1]='备注：R2204实际为12 V输入角色'
            c['checks']=block(['C1-02'])+[dict(item_id='C1-01',result='no_issue')];c['visible_issue_required']=True
        if n==16:
            c['notes'][2]='注：R2201与R9999实际测试条件为电压=12 V；角色=输入；组合=多口'
            c['checks']=block(ITEMS);c['visible_issue_required']=True
        if n==17:c['checks']=[dict(item_id=i,result='no_issue') for i in ITEMS]
        if n==18:
            c['records'].append(['','C1','response','961 ms']);c.update(capture_required=False,visible_issue_required=True)
            c['checks']=block(['C1-01'])+[dict(item_id='A1-01',result='no_issue')]
        if n==19:
            c['notes'][2]='C1本表实际测试条件：电压：12 V，角色：输入，组合：多口'
            c['checks']=block(ITEMS[5:])+[dict(item_id='A1-01',result='no_issue')];c['visible_issue_required']=True
        if n==20:
            c['records'].append(['CheckAlpha','A1','method','记录为关闭负载后再连接']);c.update(capture_required=False,visible_issue_required=True)
            c['checks']=block(['A1-05'])+[dict(item_id='C1-05',result='no_issue')]
        out.append(c)
    return out

def build(case,n):
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    from PIL import Image,ImageDraw,ImageFont
    font='/System/Library/Fonts/Supplemental/Songti.ttc'
    pdfmetrics.registerFont(TTFont('P0HoldoutFont',font,subfontIndex=0))
    buf=BytesIO();c=canvas.Canvas(buf,pagesize=(740,900),invariant=1)
    def line(s,y,size=11):c.setFont('P0HoldoutFont',size);c.drawString(35,y,s)
    def image(page,y):
        im=Image.new('RGB',(1280,100),'white');d=ImageDraw.Draw(im)
        text='模拟标识图 - 待人工确认' if n==10 else ' '.join([case['expected_visual_records'][0][0],'C1','保护响应',case['expected_visual_records'][0][3]])
        d.text((8,22),text,font=ImageFont.truetype(font,30),fill='#164b76')
        if n==8:
            c.beginForm('NestedImage',0,0,650,70);c.drawImage(ImageReader(im),0,0,width=640,height=50);c.endForm()
            c.beginForm('OuterForm',0,0,650,70);c.doForm('NestedImage');c.endForm()
            c.saveState();c.translate(35,y);c.doForm('OuterForm');c.restoreState()
        elif n==9:c.drawInlineImage(im,35,y,width=640,height=50)
        else:c.drawImage(ImageReader(im),35,y,width=640,height=50)
    for page,port in [(1,'A1'),(2,'C1')]:
        if page==2:c.showPage()
        line('模拟整机保护功能测试报告',855,18)
        line('模拟材料 / PB-DEMO-01 / '+case['case_id']+' / '+case['title'],824,11)
        line('报告填写的规格版本：SYN-SPEC-PB01-RevB',797)
        if page==1:line('本报告测试条件：电压=5 V；角色=输出；组合=单口',770,10)
        line('记录表'+('A' if page==1 else 'B'),741,13);y=709
        if n==7 and page==1:image(page,y-48);y-=75
        if page in case['notes'] and n in [12,13,19]:line(case['notes'][page],y,10);y-=30
        if n in [5,6]:
            columns=['端口','原始填写','字段','记录'] if n==6 else ['记录','端口','字段','原始填写']
            line(' | '.join(columns),y,10);y-=27
        for rid,p,kind,value in [r for r in case['records'] if r[1]==port]:
            if n==4:
                for v in [rid,p,LABEL[kind],value]:line(v,y,10);y-=18
                y-=10
            elif n in [5,6]:
                cells=dict(记录=rid,端口=p,字段=LABEL[kind],原始填写=value)
                line(' | '.join(cells[k] for k in columns),y,10);y-=33
            else:line(' '.join([rid,p,LABEL[kind],value]).strip()+case['suffix'].get(rid,''),y,10);y-=33
        if n in [8,9,10] and page==2:image(page,y-55);y-=80
        if page in case['notes'] and n not in [12,13,19]:line(case['notes'][page],y-8,10);y-=35
        if page==2:line(case['summary'],y-15,10)
        line('软件评测构造样本，未执行物理测试。',61,9);line(f'第{page}页 / 共2页',29,9)
    c.save();blob=buf.getvalue()
    if n==17:
        from pypdf import PdfReader,PdfWriter
        from pypdf.generic import DictionaryObject,DecodedStreamObject,NameObject,NumberObject
        writer=PdfWriter();writer.append_pages_from_reader(PdfReader(BytesIO(blob)))
        resources=writer.pages[0]['/Resources'];objects=resources.get('/XObject',DictionaryObject());objects=objects.get_object()
        stream=DecodedStreamObject();stream.set_data(bytes([220,60,60]))
        stream.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Image'),NameObject('/Width'):NumberObject(1),NameObject('/Height'):NumberObject(1),NameObject('/ColorSpace'):NameObject('/DeviceRGB'),NameObject('/BitsPerComponent'):NumberObject(8)})
        objects[NameObject('/UnusedStamp')]=writer._add_object(stream);resources[NameObject('/XObject')]=objects
        b=BytesIO();writer.write(b);blob=b.getvalue()
    return blob

def main():
    if (PACK/'cases.json').exists() or OUT.exists():raise SystemExit('拒绝覆盖新样本。')
    PACK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True)
    cases=[]
    for n,c in enumerate(designs(),1):
        blob=build(c,n);p=OUT/(c['case_id']+'.pdf');p.write_bytes(blob)
        label={k:v for k,v in c.items() if k not in ['records','notes','suffix','summary']}
        label.update(expected_text_records=c['records'],path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(blob).hexdigest(),page_count=2)
        cases.append(label)
    (PACK/'cases.json').write_text(json.dumps(dict(version='p0-holdout-v0.1',label_author='same_author_implementation_aware',external_independence=False,cases=cases),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(files=len(cases),pages=40,text_records=sum(len(c['expected_text_records']) for c in cases),visual_records=sum(len(c['expected_visual_records']) for c in cases)),ensure_ascii=False))

if __name__=='__main__':main()
