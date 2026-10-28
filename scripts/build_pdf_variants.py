"""Create controlled, synthetic parser fixtures, independently of production parsing."""
from copy import deepcopy
from io import BytesIO
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/pdf-variants-v0.1"
PDFS=ROOT/"output/pdf/variants-v0.1"
RECORDS=[['R01','A1','保护响应','80 ms'],['R02','C1','保护响应','0.68 s'],
         ['R03','A1','恢复电压','5.08 V'],['R04','C1','恢复电压','5.31 V'],
         ['R05','A1','壳温起值/末值','25.0摄氏度 / 34.0摄氏度'],
         ['R06','C1','壳温起值/末值','25.0摄氏度 / 3?.0摄氏度'],
         ['R07','A1','外观观察','无起火、无爆炸、无漏液'],['R08','A1','恢复方式','记录为断开后重新连接']]
CONDITION='本报告测试条件：电压=5 V；角色=输出；组合=单口'


def cases():
    descriptions=[('compact','同一行记录'),('pipes','分隔列'),('reordered','列序变化'),('wrapped','数值单位换行'),
      ('aliases','受控字段别名'),('repeat-header','重复表头及全角字符'),('continued','明确跨页单位续行'),
      ('unmarked-continuation','跨页未声明续行'),('row-9v','记录为9 V'),('row-input','记录为输入角色'),
      ('row-multiport','记录为多口组合'),('global-9v','全局条件为9 V'),('summary-9v','摘要与明细电压不同'),
      ('summary-environment','摘要与明细环境不同'),('unknown-field','存在无法映射字段'),('truncated','额外记录截断'),
      ('duplicate-id','重复记录ID'),('missing-page','物理缺页'),('image-page','图片页未OCR'),('unknown-port','未配置端口'),
      ('missing-unit','数值缺少单位'),('missing-condition','未给报告测试条件'),('global-conflict','全局条件互相矛盾'),
      ('unsupported','非模拟模板')]
    output=[]
    for n,(slug,title) in enumerate(descriptions,1):
        c=dict(case_id=f'PV-{n:02d}',slug=slug,title=title,records=deepcopy(RECORDS),layout='table',global_condition=CONDITION,
               expected_records=deepcopy(RECORDS),item_expectations={},expected_blocked=[],expected_issue=False,expected_reject=False)
        if slug in {'compact','pipes','reordered','wrapped','repeat-header'}:c['layout']=slug
        if slug=='aliases':
            c['records'][0][2]='短路保护响应时间';c['records'][2][2]='保护后恢复电压'
        if slug in {'continued','unmarked-continuation'}:c['split']=True
        if slug.startswith('row-'):
            val={'row-9v':'电压=9 V；角色=输出；组合=单口','row-input':'电压=5 V；角色=输入；组合=单口','row-multiport':'电压=5 V；角色=输出；组合=多口'}[slug]
            c['row_condition']=val;c['expected_blocked']=['A1-01']
        if slug=='global-9v':c['global_condition']=CONDITION.replace('5 V','9 V');c['expected_blocked']=['A1-01','C1-01']
        if slug=='summary-9v':c['summary_condition']='电压=9 V；角色=输出；组合=单口';c['item_expectations']={'SUMMARY-C1':'evidence_insufficient'}
        if slug=='summary-environment':
            c['global_condition']+='；环境=25摄氏度';c['summary_condition']='电压=5 V；角色=输出；组合=单口；环境=40摄氏度'
            c['item_expectations']={'SUMMARY-C1':'evidence_insufficient'}
        if slug=='unknown-field':c['records'].insert(1,['R09','A1','保护动作延迟','90 ms']);c['expected_issue']=True;c['expected_blocked']=['A1-01']
        if slug=='truncated':c['truncated']=True;c['expected_issue']=True;c['expected_blocked']=['A1-01']
        if slug=='duplicate-id':c['records'][1][0]='R01';c['expected_records'][1][0]='R01';c['item_expectations']={'A1-01':'conflict','C1-01':'conflict'}
        if slug in {'missing-page','image-page','unmarked-continuation'}:c['expected_issue']=True;c['expected_blocked']=['A1-01','C1-01'] if slug!='unmarked-continuation' else ['C1-01']
        if slug=='unknown-port':c['records'].insert(1,['R09','C10','保护响应','80 ms']);c['expected_issue']=True
        if slug=='missing-unit':c['records'][0][3]='80';c['expected_records'][0][3]='80';c['item_expectations']={'A1-01':'evidence_insufficient'}
        if slug=='missing-condition':c['global_condition']='报告未提供测试条件';c['expected_blocked']=['A1-01','C1-01']
        if slug=='global-conflict':c['global_condition']+='\n本报告测试条件：电压=9 V；角色=输出；组合=单口';c['expected_blocked']=['A1-01','C1-01']
        if slug=='unsupported':c['expected_reject']=True
        if slug=='unmarked-continuation':c['expected_records'][1][3]='0.68'
        if slug=='missing-page':c['expected_records']=c['expected_records'][:4]
        output.append(c)
    return output


def build_pdf(case):
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader
    from PIL import Image,ImageDraw
    font=Path('/System/Library/Fonts/Supplemental/Songti.ttc')
    if not font.exists():raise RuntimeError('生成样本需要可嵌入的中文字体Songti.ttc，不能使用无字体的PDF替代。')
    pdfmetrics.registerFont(TTFont('VariantCJK',str(font),subfontIndex=0))
    out=BytesIO();c=canvas.Canvas(out,pagesize=(650,842),invariant=1)
    total=3 if case.get('split') or case['slug'] in {'missing-page','image-page'} else 2
    def line(text,y,x=36,size=10):c.setFont('VariantCJK',size);c.drawString(x,y,text)
    def page(n):
        line('模拟整机保护功能测试报告' if case['slug']!='unsupported' else '其他产品测试报告',805,size=17)
        line(case['case_id']+' / PB-DEMO-01 / '+case['title'],781)
        line(f'模拟材料，仅用于软件测试；未执行物理试验。第 {n} 页 / 共 {total} 页',25,size=9)
        return 748
    def table(rows,y):
        layout=case['layout'];columns=['记录','端口','字段','原始填写']
        order=[1,3,2,0] if layout=='reordered' else [0,1,2,3]
        xs=[36,105,185,355] if layout!='reordered' else [36,95,320,530]
        def cells(values,y):
            for j,index in enumerate(order):
                value=values[index]
                if layout=='repeat-header':value=value.translate(str.maketrans('RAC0123456789','ＲＡＣ０１２３４５６７８９'))
                if layout=='wrapped' and index==3 and value in {'80 ms','0.68 s','5.08 V','5.31 V'}:
                    val,unit=value.split();line(val,y,xs[j]);line(unit,y-12,xs[j])
                else:line(value,y,xs[j],size=9 if index==3 else 10)
        if layout not in {'compact','pipes'}:cells(columns,y);y-=30
        if layout=='pipes':line(' | '.join(columns),y);y-=25
        for n,row in enumerate(rows):
            if layout=='compact':line(' '.join(row),y,size=9)
            elif layout=='pipes':line(' | '.join(row),y,size=9)
            else:cells(row,y)
            y-=35 if layout=='wrapped' else 30
            if case.get('row_condition') and row[0]=='R01':line('条件：'+case['row_condition'],y,size=9);y-=25
            if layout=='repeat-header' and n==1:cells(columns,y);y-=30
        return y
    y=page(1)
    line('任务清单采用5 V输出角色；本页实际测试条件见下方。',y);y-=25
    for text in case['global_condition'].splitlines():line(text,y);y-=23
    line('报告填写的规格版本：SYN-SPEC-PB01-RevA。',y);y-=25
    summary='S01：C1保护响应80 ms'+('；条件：'+case['summary_condition'] if case.get('summary_condition') else '')
    line(summary,y,size=9);y-=30;line('记录表A',y);y-=25
    a=[r for r in case['records'] if r[2] not in {'壳温起值/末值','外观观察','恢复方式'}]
    b=[r for r in case['records'] if r not in a]
    if case.get('split'):
        table(a[:1],y);line('R02 C1 保护响应 0.68',y-100);c.showPage();y=page(2)
        if case['slug']=='continued':line('续表A（接上页单位）',y);y-=25
        line('s',y);y-=30;table(a[2:],y);c.showPage();y=page(3)
    else:
        end=table(a,y)
        if case.get('truncated'):line('R09 A1 保护响应',end-10)
        c.showPage();y=page(2)
    line('记录表B',y);table(b,y-30)
    if case['slug']=='image-page':
        c.showPage();page(3)
        # Image-only body in a page with no extractable header/footer text.
        # Recreate page below so the parser must explicitly surface OCR absence.
    elif case['slug']=='missing-page':c.showPage();y=page(3);line('缺页模拟：本页将在生成后删除。',y)
    c.save();blob=out.getvalue()
    if case['slug'] in {'missing-page','image-page'}:
        from pypdf import PdfReader,PdfWriter
        r=PdfReader(BytesIO(blob));w=PdfWriter()
        if case['slug']=='missing-page':
            # Drop the page containing temperature and observation records.
            for p in [r.pages[0],r.pages[2]]:w.add_page(p)
        else:
            for p in r.pages[:2]:w.add_page(p)
            image=Image.new('RGB',(550,550),'white');ImageDraw.Draw(image).text((25,50),'SCANNED SIMULATION\nR09 A1 protection response 60 ms\nOCR not performed',fill='black')
            buf=BytesIO();cc=canvas.Canvas(buf,pagesize=(650,842),invariant=1);cc.drawImage(ImageReader(image),45,150,width=550,height=550);cc.save()
            w.add_page(PdfReader(BytesIO(buf.getvalue())).pages[0])
        out=BytesIO();w.write(out);blob=out.getvalue()
    return blob


def main():
    BASE.mkdir(parents=True,exist_ok=True);PDFS.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for case in cases():
        path=PDFS/(case['case_id']+'-'+case['slug']+'.pdf')
        if path.exists():raise SystemExit('拒绝覆盖已存在的PDF样本：'+str(path))
        blob=build_pdf(case);path.write_bytes(blob)
        manifest.append(dict(case,path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(blob).hexdigest()))
    (BASE/'cases.json').write_text(json.dumps(dict(version='pdf-variants-v0.1',usage='synthetic_development_only',professional_review='pending',cases=manifest),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(pdf_files=len(manifest),manifest=str(BASE/'cases.json')),ensure_ascii=False))


if __name__=='__main__':main()
