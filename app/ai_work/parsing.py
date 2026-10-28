"""Finite synthetic table layouts, explicit context inheritance, and omission audit."""
from collections import Counter
from decimal import Decimal
import hashlib
from pathlib import Path
import re
import unicodedata

PARSER_VERSION='controlled-pdf-v0.2'
ALIASES={'保护响应':'response','短路保护响应时间':'response','恢复电压':'recovery','保护后恢复电压':'recovery',
         '壳温起值/末值':'temperature','外观观察':'appearance','恢复方式':'method'}
KINDS=['response','recovery','temperature','appearance','method']
HEADERS={'记录','端口','字段','原始填写','报告填写判定'}
RID=re.compile(r'R\d{2,4}')
PORT=re.compile(r'[A-Z]\d{1,3}')
UNIT=re.compile(r'ms|s|V|mV')
PARSER_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def norm(text):return unicodedata.normalize('NFKC',text).strip()

def conditions(text):
    output={}
    for key,label in [('voltage','电压'),('role','角色'),('combination','组合'),('environment','环境')]:
        values=re.findall(label+r'\s*=\s*([^；;\n|]+)',norm(text))
        if values:
            canonical=[]
            for value in values:
                v=value.strip(' 。)')
                if key=='voltage':
                    m=re.fullmatch(r'(\d+(?:\.\d+)?)\s*V',v)
                    v=format(Decimal(m[1]).normalize(),'f') if m else None
                elif key=='role':v=v if v in {'输入','输出'} else None
                elif key=='combination':v=v if v in {'单口','多口'} else None
                elif key=='environment':
                    m=re.fullmatch(r'([+-]?\d+(?:\.\d+)?)\s*(?:摄氏度|°C)',v)
                    v=format(Decimal(m[1]).normalize(),'f') if m else None
                canonical.append(v)
            if len(set(canonical))>1:
                output.setdefault('_conflicts',[]).append(key)
            output[key]=canonical[0] if len(set(canonical))==1 else None
    return output

def fragment(page,quote):return dict(source_id=page['source_id'],page=page['page'],quote=quote)

def extract_report(pages):
    fields={p+':'+k:[] for p in ['A1','C1'] for k in KINDS}
    candidates=[];issues=[];global_proofs=[];declarations=[];summary=[]
    def issue(code,message,page,quote,keys=None):
        issues.append(dict(code=code,message=message,affected_keys=keys or [],evidence=[fragment(page,quote)]))
    for page in pages:
        text=page['text']
        if not text.strip():
            issue('unreadable_page','此页无可提取文字，可能为图片页；尚未OCR或核验。',page,'',list(fields))
        for m in re.finditer(r'本报告测试条件[：:][^\n]+',text):
            declarations.append(conditions(m[0]));global_proofs.append(fragment(page,m[0]))
        m=re.search(r'本报告只列\s*5\s*V\s*输出角色的\s*记录。未包含充电输入、其他档位与组合。',text)
        if m:
            declarations.append(dict(voltage='5',role='输出',combination='单口'));global_proofs.append(fragment(page,m[0]))
    global_context={};conflicts=[]
    for key in ['voltage','role','combination','environment']:
        values={d[key] for d in declarations if key in d}
        if len(values)>1:conflicts.append(key)
        global_context[key]=next(iter(values)) if len(values)==1 else None
    conflicts=sorted(set(conflicts+[key for d in declarations for key in d.get('_conflicts',[])]))
    expected_pages={int(n) for p in pages for n in re.findall(r'共\s*(\d+)\s*页',p['text'])}
    if expected_pages and expected_pages!={len(pages)}:
        p=next(p for p in pages if re.search(r'共\s*\d+\s*页',p['text']))
        quote=next(line for line in p['text'].splitlines() if re.search(r'共\s*\d+\s*页',line))
        issue('page_count_mismatch','报告声明页数与物理PDF页数不一致，范围完整性待核对。',p,quote,list(fields))
    def add(page,raw,data,layout):
        rid=norm(data.get('记录',''));port=norm(data.get('端口',''));label=norm(data.get('字段',''));value=norm(data.get('原始填写',''))
        if rid=='无记录ID':return None
        candidate=dict(record_id=rid,port=port,field=label,page=page['page'],layout=layout,status='unmapped')
        candidates.append(candidate)
        kind=ALIASES.get(label)
        if port not in {'A1','C1'}:
            issue('unsupported_port','记录端口未配置：'+port,page,raw);return None
        keys=[port+':'+kind] if kind else [port+':'+k for k in KINDS]
        if not RID.fullmatch(rid) or not kind or not value:
            issue('unmapped_record','记录未完整映射：'+rid+' / '+port+' / '+label,page,raw,keys);return None
        value=value.split('条件:',1)[0].split('条件：',1)[0].strip(' ；;')
        local=conditions(raw) if re.search(r'条件[：:]',raw) else {}
        context=dict(global_context,**local)
        row=dict(record_id=rid,port=port,kind=kind,value=value,source_id=page['source_id'],page=page['page'],quote=raw,
                 fragments=[fragment(page,raw)],conditions=context,condition_evidence=list(global_proofs),global_condition_conflicts=conflicts)
        if local:row['condition_evidence'].append(fragment(page,raw))
        fields[port+':'+kind].append(row);candidate['status']='captured';return row
    previous_page_last=None
    for page in pages:
        text=page['text'];lines=[];offset=0
        for raw in text.splitlines(keepends=True):
            lines.append(dict(text=norm(raw),start=offset,end=offset+len(raw.rstrip('\r\n'))));offset+=len(raw)
        columns=['记录','端口','字段','原始填写'];i=0;last=None;last_end=-2
        while i<len(lines):
            entry=lines[i];s=entry['text']
            if not s:i+=1;continue
            if s.startswith('续表A(接上页单位)') and previous_page_last:
                j=i+1
                if j<len(lines) and UNIT.fullmatch(lines[j]['text']) and re.fullmatch(r'[+-]?\d+(?:\.\d+)?',previous_page_last['value']):
                    previous_page_last['value']+=' '+lines[j]['text']
                    previous_page_last['fragments'].append(fragment(page,text[entry['start']:lines[j]['end']]))
                    i=j+1;continue
            if UNIT.fullmatch(s):
                keys=[previous_page_last['port']+':'+previous_page_last['kind']] if previous_page_last else list(fields)
                issue('orphan_unit','单位未与记录安全关联；仅明确声明的跨页续行可连接。',page,text[entry['start']:entry['end']],keys)
                i+=1;continue
            if re.match(r'条件[：:]',s):
                if last and last_end==i-1:
                    raw=text[entry['start']:entry['end']];local=conditions(raw)
                    last['conditions'].update(local);last['condition_evidence'].append(fragment(page,raw))
                    if not local:last['conditions']['voltage']=None
                else:issue('unbound_condition','条件文字没有唯一相邻记录，未猜测对应关系。',page,text[entry['start']:entry['end']],list(fields))
                i+=1;continue
            pipe=[x.strip() for x in s.strip('|').split('|')]
            if len(pipe)>=4 and {'记录','端口','字段','原始填写'}<=set(pipe):
                columns=pipe;i+=1;continue
            if s in HEADERS:
                j=i
                while j<len(lines) and lines[j]['text'] in HEADERS:j+=1
                names=[x['text'] for x in lines[i:j]]
                if {'记录','端口','字段','原始填写'}<=set(names):columns=names;i=j;continue
            if len(pipe)>=4 and (RID.fullmatch(pipe[0]) or (columns[0]=='端口' and PORT.fullmatch(pipe[0]))):
                raw=text[entry['start']:entry['end']]
                last=add(page,raw,dict(zip(columns,pipe)), 'delimited');last_end=i;i+=1;continue
            inline=re.fullmatch(r'(R\d{2,4})\s+([A-Z]\d{1,3})\s+('+ '|'.join(sorted(map(re.escape,ALIASES),key=len,reverse=True))+r')(?:\s+(.*))?',s)
            if inline:
                rid,port,label,value=inline.groups();end=i;value=value or ''
                if i+1<len(lines) and re.fullmatch(r'[+-]?\d+(?:\.\d+)?',value) and UNIT.fullmatch(lines[i+1]['text']):
                    end=i+1;value+=' '+lines[end]['text']
                last=add(page,text[entry['start']:lines[end]['end']],dict(zip(['记录','端口','字段','原始填写'],[rid,port,label,value])),'inline');last_end=end;i=end+1;continue
            start=(columns[0]=='记录' and (RID.fullmatch(s) or s=='无记录ID')) or (columns[0]=='端口' and PORT.fullmatch(s))
            if start:
                cells=[];j=i
                for column in columns:
                    if j>=len(lines):break
                    v=lines[j]['text']
                    if j>i and (RID.fullmatch(v) and column!='记录' or v in HEADERS):break
                    cells.append(v);j+=1
                    if column=='原始填写' and re.fullmatch(r'[+-]?\d+(?:\.\d+)?',v) and j<len(lines) and UNIT.fullmatch(lines[j]['text']):
                        cells[-1]+=' '+lines[j]['text'];j+=1
                raw=text[entry['start']:lines[max(i,j-1)]['end']]
                last=add(page,raw,dict(zip(columns,cells)),'header_mapped');last_end=j-1;i=max(j,i+1);continue
            if re.match(r'^R\d{2,4}(?:\s|$)',s):
                parts=s.split();data=dict(记录=parts[0],端口=parts[1] if len(parts)>1 else '',字段=parts[2] if len(parts)>2 else '',原始填写=' '.join(parts[3:]))
                last=add(page,text[entry['start']:entry['end']],data,'unmapped_inline');last_end=i
            i+=1
        page_rows=[r for rows in fields.values() for r in rows if r['page']==page['page']]
        # The last parsed record in source order, independent of dictionary port order.
        previous_page_last=max(page_rows,key=lambda r:text.find(r['quote'])) if page_rows else None
        for m in re.finditer(r'(S\d{2})[：:]\s*(A1|C1)保护响应\s*(\d+(?:\.\d+)?)\s*(ms|s)(?![\d.a-zA-Z])([^\n]*)',text):
            local=conditions(m[0]) if re.search(r'条件[：:]',m[0]) else {}
            summary.append(dict(record_id=m[1],port=m[2],value=m[3]+' '+m[4],source_id=page['source_id'],page=page['page'],quote=m[0],
                conditions=dict(global_context,**local),condition_evidence=list(global_proofs)+([fragment(page,m[0])] if local else []),global_condition_conflicts=conflicts))
    ids=[r['record_id'] for rows in fields.values() for r in rows]
    audit=dict(candidate_count=len(candidates),captured_count=sum(c['status']=='captured' for c in candidates),
               unresolved_count=sum(c['status']!='captured' for c in candidates),candidates=candidates,issues=issues,
               coverage_status='needs_review' if issues else 'mapped',scanned_pages=[p['page'] for p in pages])
    return dict(fields=fields,summary=summary,duplicate_record_ids=sorted(k for k,n in Counter(ids).items() if n>1),
                global_conditions=global_context,condition_evidence=global_proofs,global_condition_conflicts=conflicts,parse_audit=audit)

def gate(row):
    context=row.get('conditions',{})
    if row.get('global_condition_conflicts') or context.get('_conflicts'):return 'conflict','测试条件声明互相矛盾，需核对适用条件。'
    expected=dict(voltage='5',role='输出',combination='单口')
    if any(context.get(k) is None for k in expected):return 'unknown','记录的电压、角色或端口组合条件未明确；未执行阈值比较。'
    if any(context[k]!=v for k,v in expected.items()):return 'conflict','报告实际条件与5 V、输出、单口的已配置范围不匹配；未执行阈值比较。'
    return 'matched','条件与本次受控范围相符。'

def same_conditions(a,b):
    if a.get('global_condition_conflicts') or b.get('global_condition_conflicts') or a.get('conditions',{}).get('_conflicts') or b.get('conditions',{}).get('_conflicts'):return False
    ca,cb=a.get('conditions',{}),b.get('conditions',{})
    required={'voltage','role','combination'}|{k for k in ['environment'] if ca.get(k) is not None or cb.get(k) is not None}
    return all(ca.get(k) is not None and ca.get(k)==cb.get(k) for k in required)
