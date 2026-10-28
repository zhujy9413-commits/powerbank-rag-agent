"""New P1 time-held-out inputs, authored only after application commit 48c4893.

No production imports and no old sample builders. Labels are author drafted.
"""
from copy import deepcopy
from io import BytesIO
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'data/p1-holdout-v0.1';OUT=ROOT/'output/pdf/p1-holdout-v0.1'
LABEL=dict(response='保护响应',recovery='恢复电压',temperature='壳温起值/末值',appearance='外观观察',method='恢复方式')
ROWS=[['R3301','A1','response','283 ms'],['R3302','C1','response','0.394 s'],
      ['R3303','A1','recovery','4.89 V'],['R3304','C1','recovery','5.17 V'],
      ['R3305','A1','temperature','18.4摄氏度 / 29.6摄氏度'],['R3306','C1','temperature','20.4摄氏度 / 30.6摄氏度'],
      ['R3307','A1','appearance','无起火、无爆炸、无漏液'],['R3308','C1','appearance','无起火、无爆炸、无漏液'],
      ['R3309','A1','method','记录为取下测试负载后重新接入'],['R3310','C1','method','记录为重新接入负载端']]
ITEMS=[p+f'-{n:02d}' for p in ['A1','C1'] for n in range(1,6)]

def designs():
    titles=['单行摘要新数值控制','秒摘要数值单位跨行','摘要标题数值单位三行','C1标题与数值单位分行','C1毫秒单位跨行',
            '全角摘要跨行','两端口分行摘要各自归属','同条件跨行摘要数值冲突','摘要后局部9V条件','摘要与明细环境不一致',
            '摘要单位跨页须核验','不完整摘要不能借走下一记录单位','表头打断摘要连续性','微秒摘要未配置',
            '无归属单位不误挂恢复方式','分隔表格记录跨行单位','明确声明的跨页记录单位','无声明的跨页记录单位',
            '两个待补单位记录不能猜测','摘要相邻条件自身矛盾']
    result=[]
    for n,title in enumerate(titles,1):
        c=dict(case_id=f'HP-{n:02d}',title=title,expected_text_records=deepcopy(ROWS),expected_visual_records=[],
               expected_reject=False,capture_required=True,visible_issue_required=False,checks=[],
               expected_summaries=[['S71','A1','283 ms']],expected_unit_owners=[],required_issue_codes=[],
               expected_summary_conditions={},expected_orphan_keys=[])
        def owner(page,unit,kind,rid):c['expected_unit_owners'].append([page,unit,kind,rid])
        def block(ids):return [dict(item_id=i,blocked=True,execution='not_checked') for i in ids]
        c['checks']=[dict(item_id=i,result='no_issue') for i in ITEMS]+[dict(item_id='SUMMARY-A1',result='no_issue')]
        if n in [2,3,6,7,8,9,10,20]:
            c['expected_summaries']=[['S71','A1','0.283 s']];owner(2,'s','summary','S71')
        if n in [4,5]:
            c['expected_summaries']=[['S72','C1','394 ms']]
            c['checks']=[dict(item_id=i,result='no_issue') for i in ITEMS]+[dict(item_id='SUMMARY-C1',result='no_issue')]
            if n==5:owner(2,'ms','summary','S72')
        if n==7:
            c['expected_summaries'].append(['S72','C1','394 ms']);owner(2,'ms','summary','S72')
            c['checks'].append(dict(item_id='SUMMARY-C1',result='no_issue'))
        if n==8:
            c['expected_summaries']=[['S71','A1','0.683 s']]
            c['checks']=[dict(item_id='A1-01',result='no_issue',conditional=True),dict(item_id='SUMMARY-A1',result='conflict'),dict(item_id='A1-05',result='no_issue')]
        if n in [9,10,20]:
            c['expected_summaries']=[['S71','A1','0.967 s']]
            c['checks']=[dict(item_id='A1-01',result='no_issue',conditional=False),dict(item_id='SUMMARY-A1',blocked=True,execution='not_checked'),dict(item_id='A1-05',result='no_issue')]
            c['expected_summary_conditions']={'S71':{'voltage':'9'} if n==9 else {'environment':'25'} if n==10 else {'voltage':None,'_conflicts':['voltage']}}
        if n in [11,12,13,14]:
            c.update(expected_summaries=[],visible_issue_required=True,required_issue_codes=['unresolved_summary'])
            c['checks']=block(ITEMS if n in [11,13] else ['A1-01'])+[dict(item_id='SUMMARY-MISSING',result='evidence_insufficient')]
            if n in [12,14]:c['checks'] += [dict(item_id='C1-01',result='no_issue'),dict(item_id='A1-05',result='no_issue')]
            if n in [11,13]:
                c['required_issue_codes'].append('orphan_unit');c['expected_orphan_keys']=[p+':'+k for p in ['A1','C1'] for k in LABEL]
                owner(2,'s' if n==11 else 'ms','unresolved',None)
            if n==12:owner(2,'s','record','R3302')
        if n==15:
            c.update(visible_issue_required=True,required_issue_codes=['orphan_unit']);c['checks']=block(ITEMS)
            c['expected_orphan_keys']=[p+':'+k for p in ['A1','C1'] for k in LABEL];owner(2,'s','unresolved',None)
        if n==16:owner(1,'ms','record','R3301')
        if n in [17,18]:
            owner(2,'s','record_continuation' if n==17 else 'unresolved','R3302' if n==17 else None)
            if n==18:
                c['expected_text_records'][1][3]='0.394';c.update(visible_issue_required=True,required_issue_codes=['orphan_unit'],expected_orphan_keys=['C1:response'])
                c['checks']=block(['C1-01'])+[dict(item_id='A1-01',result='no_issue'),dict(item_id='A1-05',result='no_issue'),dict(item_id='SUMMARY-A1',result='no_issue')]
        if n==19:
            c['expected_text_records'][0][3]='283';c['expected_text_records'][1][3]='0.394'
            c.update(visible_issue_required=True,required_issue_codes=['orphan_unit']);c['checks']=block(ITEMS)
            c['expected_orphan_keys']=[p+':'+k for p in ['A1','C1'] for k in LABEL];owner(2,'s','unresolved',None)
        result.append(c)
    return result

def build(case,n):
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont('P1HoldoutFont','/System/Library/Fonts/Supplemental/Songti.ttc',subfontIndex=0))
    buf=BytesIO();c=canvas.Canvas(buf,pagesize=(740,900),invariant=1)
    summaries={1:['S71：A1保护响应 283 ms'],2:['S71：A1保护响应 0.283','s'],3:['S71：A1保护响应','0.283','s'],
        4:['S72：C1保护响应','394 ms'],5:['S72：C1保护响应 394','ms'],6:['Ｓ７１：Ａ１保护响应 ０.２８３','ｓ'],
        7:['S71：A1保护响应 0.283','s','S72：C1保护响应','394','ms'],8:['S71：A1保护响应 0.683','s'],
        9:['S71：A1保护响应 0.967','s','条件：电压=9 V；角色=输出；组合=单口'],
        10:['S71：A1保护响应 0.967','s；条件：环境=25摄氏度'],11:[],12:[],
        13:['S71：A1保护响应 283','记录表B（摘要续行待核验）','ms'],14:['S71：A1保护响应 283','us'],
        20:['S71：A1保护响应 0.967','s','条件：电压=5 V；电压=9 V；角色=输出；组合=单口']}
    # Expected ownership is a normalized exact unit-only line, not a fabricated quote.
    if n==10:case['expected_unit_owners']=[]
    def line(s,y,size=11):c.setFont('P1HoldoutFont',size);c.drawString(35,y,s)
    def row(r,y,split=False,delimited=False):
        rid,p,k,v=r;prefix=' | '.join([rid,p,LABEL[k],v]) if delimited else ' '.join([rid,p,LABEL[k],v])
        if split:
            first,unit=v.rsplit(' ',1);prefix=' | '.join([rid,p,LABEL[k],first]) if delimited else ' '.join([rid,p,LABEL[k],first])
            line(prefix,y,10);line(unit,y-22,10);return y-48
        line(prefix,y,10);return y-31
    for page,port in [(1,'A1'),(2,'C1')]:
        if page==2:c.showPage()
        line('模拟整机保护功能测试报告',855,18);line('模拟材料 / PB-DEMO-01 / '+case['case_id']+' / '+case['title'],824,11)
        line('报告填写的规格版本：SYN-SPEC-PB01-RevB',797)
        if page==1:line('本报告测试条件：电压=5 V；角色=输出；组合=单口'+('；环境=23摄氏度' if n==10 else ''),770,10)
        line('记录表'+('A' if page==1 else 'B'),741,13);y=710
        if page==2 and n in [11,17,18,19]:
            if n in [17,19]:line('续表A（接上页单位）',y,10);y-=22
            line('s',y,10);y-=32
        if n==16:line('记录 | 端口 | 字段 | 原始填写',y,10);y-=30
        chosen=[r for r in ROWS if r[1]==port]
        if n in [17,18]:
            chosen=[r for r in chosen if r[0]!='R3302']
            if page==1:chosen=chosen+[ROWS[1]]
        if n==19:
            chosen=[r for r in chosen if r[0] not in ['R3301','R3302']]
            if page==1:chosen=chosen+[ROWS[0],ROWS[1]]
        if n==12 and page==2:line('S71：A1保护响应 283',y,10);y-=22
        for r in chosen:
            r=list(r)
            if (n in [17,18] and r[0]=='R3302') or (n==19 and r[0] in ['R3301','R3302']):r[3]=r[3].rsplit(' ',1)[0]
            y=row(r,y,split=(n==16 and r[0]=='R3301') or (n==12 and r[0]=='R3302'),delimited=n==16)
        if n==11 and page==1:line('S71：A1保护响应 0.283',y,10)
        if page==2:
            if n==15:line('s',y,10);y-=28
            for s in summaries.get(n,['S71：A1保护响应 283 ms']):line(s,y,10);y-=22
        line('软件评测构造样本，未执行物理测试。',61,9);line(f'第{page}页 / 共2页',29,9)
    c.save();return buf.getvalue()

def main():
    if (PACK/'cases.json').exists() or OUT.exists():raise SystemExit('拒绝覆盖样本。')
    PACK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True);cases=[]
    for n,c in enumerate(designs(),1):
        blob=build(c,n);p=OUT/(c['case_id']+'.pdf');p.write_bytes(blob)
        c.update(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(blob).hexdigest(),page_count=2);cases.append(c)
    (PACK/'cases.json').write_text(json.dumps(dict(version='p1-holdout-v0.1',label_author='same_author_implementation_aware',external_independence=False,cases=cases),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(files=len(cases),pages=40,text_records=sum(len(c['expected_text_records']) for c in cases)),ensure_ascii=False))

if __name__=='__main__':main()
