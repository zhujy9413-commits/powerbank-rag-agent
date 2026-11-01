"""Local knowledge maintenance: immutable source versions and atomic publication.

No provider call is needed for the keyword index. Task reports never pass through
this public-knowledge store. The local engineer profile is a demo maintainer,
not an enterprise identity or a professional sign-off.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import threading
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


def checksum(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def short_text(value, name, limit=300):
    if not isinstance(value, str) or not 0 < len(value.strip()) <= limit:
        raise ValueError(f"{name}需填写1至{limit}字。")
    return value.strip()


class KnowledgeMaintenance:
    def __init__(self, path, corpus):
        self.corpus = corpus
        self.lock = threading.RLock()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript('''CREATE TABLE IF NOT EXISTS knowledge_versions(id TEXT PRIMARY KEY, payload TEXT);
            CREATE TABLE IF NOT EXISTS knowledge_events(id INTEGER PRIMARY KEY, version_id TEXT, payload TEXT);''')
        if not self.db.execute('SELECT 1 FROM knowledge_versions LIMIT 1').fetchone():
            groups = defaultdict(list)
            for chunk in corpus.chunks:
                if chunk['scope'] == 'knowledge':
                    groups[chunk['document_id']].append(deepcopy(chunk))
            with self.db:
                for doc, chunks in groups.items():
                    c = chunks[0]
                    original = corpus.source(c['chunk_id'], type('SeedIdentity', (), {'role':c['allowed_roles'][0], 'task_ids':()})())['original_text']
                    entry = dict(id='SEED-'+doc, document_id=doc, version=c['version'], title=c['title'],
                                 source_origin=c.get('source_url') or '已有受控知识包', usage_rights='沿用原知识包登记范围',
                                 applicability='沿用原知识包适用范围', allowed_roles=c['allowed_roles'],
                                 material_type=c['material_type'], source_role='requirement', original_text=original,
                                 content_sha256=hashlib.sha256(original.encode()).hexdigest(), legacy=True,
                                 state='published' if c['publication_status']=='active' else 'retired', chunks=chunks,
                                 created_at=now(), review_note='原受控包基线，真实适用性仍待专业确认')
                    self._save(entry)
        self.refresh()

    def _auth(self, principal):
        if principal.role != 'engineer':
            raise PermissionError('当前身份没有知识维护权限。')

    def _all(self):
        return [json.loads(r[0]) for r in self.db.execute('SELECT payload FROM knowledge_versions ORDER BY rowid')]

    def _get(self, identity):
        row = self.db.execute('SELECT payload FROM knowledge_versions WHERE id=?', (identity,)).fetchone()
        if not row:
            raise ValueError('知识版本不存在。')
        return json.loads(row[0])

    def _save(self, entry):
        self.db.execute('INSERT OR REPLACE INTO knowledge_versions VALUES(?,?)', (entry['id'], json.dumps(entry, ensure_ascii=False)))

    def _event(self, entry, principal, action, note):
        self.db.execute('INSERT INTO knowledge_events(version_id,payload) VALUES(?,?)',
                        (entry['id'], json.dumps(dict(action=action, note=note, actor=principal.user_id, at=now()), ensure_ascii=False)))

    def refresh(self):
        """One runtime state swap; content IDs and original text remain immutable."""
        with self.corpus.lock,self.lock:
            entries = self._all()
            chunks = []
            for entry in entries:
                if entry['state'] not in {'published','retired'}:
                    continue
                for original in entry['chunks']:
                    c = deepcopy(original)
                    c.update(allowed_roles=entry['allowed_roles'], managed_original=entry['original_text'],
                             knowledge_version_id=entry['id'], source_origin=entry['source_origin'],
                             applicability=entry['applicability'], content_sha256=entry['content_sha256'])
                    c['publication_status'] = 'active' if entry['state']=='published' else 'archived'
                    chunks.append(c)
            self.corpus.apply_knowledge(chunks, 'LOCAL-'+checksum([(e['id'],e['state'],e['allowed_roles']) for e in entries if e['state'] in {'published','retired'}])[:16])

    def listing(self, principal):
        self._auth(principal)
        with self.lock:
            return [self.detail(principal,e['id']) for e in self._all()]

    def detail(self, principal, identity):
        self._auth(principal)
        with self.lock:
            entry = self._get(identity)
            events = [json.loads(r[0]) for r in self.db.execute('SELECT payload FROM knowledge_events WHERE version_id=? ORDER BY id',(identity,))]
            return {**entry, 'events':events}

    def submit(self, principal, data):
        self._auth(principal)
        required={'document_id','version','title','source_origin','usage_rights','applicability','allowed_roles','material_type','source_role','original_text'}
        if set(data)!=required:
            raise ValueError('请填写文档身份、版本、来源、使用范围、适用性、角色及原文；不接受文件路径或任务报告。')
        entry={k:short_text(data[k],k,60000 if k=='original_text' else 1000 if k in {'usage_rights','applicability'} else 300) for k in required-{'allowed_roles'}}
        entry['original_text']=data['original_text']
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}',entry['document_id']):
            raise ValueError('文档身份仅允许字母、数字、点、下划线和短横线。')
        roles=data['allowed_roles']
        if not isinstance(roles,list) or not roles or any(not isinstance(r,str) or r not in {'engineer','employee'} for r in roles):
            raise ValueError('访问角色无效。')
        if entry['material_type'] not in {'synthetic','product_policy','public_metadata'} or entry['source_role'] not in {'requirement','process','metadata'}:
            raise ValueError('当前维护入口仅接收受控模拟依据、流程或公开摘要；任务记录不能作为公共要求入库。')
        identity=checksum(entry)
        with self.corpus.lock,self.lock,self.db:
            prior=self.db.execute('SELECT id FROM knowledge_versions WHERE id=?',('K-'+identity[:24],)).fetchone()
            if prior:return self.detail(principal,prior[0])
            entry.update(id='K-'+identity[:24],allowed_roles=sorted(set(roles)),state='unverified',created_at=now(),
                         content_sha256=hashlib.sha256(entry['original_text'].encode()).hexdigest(),legacy=False,chunks=[])
            conflict=any(e['document_id']==entry['document_id'] and e['version']==entry['version'] and e['content_sha256']!=entry['content_sha256'] for e in self._all())
            if conflict:entry['conflict']='同一文档身份与版本已有不同原文，需另建版本并重新核验；不能覆盖。'
            self._save(entry);self._event(entry,principal,'submit','登记待核验资料')
            return self.detail(principal,entry['id'])

    def build_chunks(self, entry):
        text=entry['original_text']
        headings=list(re.finditer(r'(?m)^##\s+([^\n]+)',text))
        segments=[(m[1],text[m.start():headings[i+1].start() if i+1<len(headings) else len(text)]) for i,m in enumerate(headings)]
        if headings and text[:headings[0].start()].strip():
            segments.append(('文档说明',text[:headings[0].start()]))
        if not segments:segments=[('全文',text)]
        if len(segments)>100:raise ValueError('章节超过100个，请拆分资料。')
        return [dict(chunk_id=f"{entry['id']}-C{i}",document_id=entry['document_id'],title=entry['title'],version=entry['version'],
                     section=section,text=body,scope='knowledge',page=None,source_url=None,material_type=entry['material_type'],
                     source_role=entry['source_role'],allowed_roles=entry['allowed_roles'],publication_status='active')
                for i,(section,body) in enumerate(segments,1)]

    def transition(self, principal, identity, data):
        self._auth(principal)
        if set(data)-{'action','note','source_verified','version_verified','applicability_verified','allowed_roles'}:
            raise ValueError('维护操作字段无效。')
        action=data.get('action');note=short_text(data.get('note'),'操作理由',1000)
        with self.corpus.lock,self.lock,self.db:
            entry=self._get(identity)
            if action=='verify':
                if entry['state']!='unverified' or entry.get('conflict'):
                    raise ValueError(entry.get('conflict') or '只有待核验版本可以提交核验。')
                if any(data.get(k) is not True for k in ('source_verified','version_verified','applicability_verified')):
                    raise ValueError('来源、版本和专业适用性均须明确确认。')
                entry.update(state='pending_publish',review_note=note,reviewer=principal.user_id,reviewed_at=now())
            elif action=='publish':
                if entry['state']=='published':return self.detail(principal,identity)
                if entry['state']!='pending_publish':raise ValueError('资料须完成核验后才可发布。')
                try:
                    chunks=self.build_chunks(entry)
                    if not chunks or len({c['chunk_id'] for c in chunks})!=len(chunks) or any(c['text'] not in entry['original_text'] for c in chunks):
                        raise ValueError('索引或原文定位校验失败。')
                except Exception:
                    self._event(entry,principal,'publish_failed','索引构建失败，当前有效知识保持不变。')
                    self.db.commit()
                    raise ValueError('索引构建失败，未发布新版本，原有效快照保持。') from None
                # Publication and retirement happen in one database transaction.
                for old in self._all():
                    if old['document_id']==entry['document_id'] and old['state']=='published':
                        old.update(state='retired',retirement_reason='显式发布同文档的新版本',retired_at=now())
                        self._save(old);self._event(old,principal,'retire','发布新版本时保留旧来源供历史查询')
                entry.update(state='published',chunks=chunks,published_at=now(),publisher=principal.user_id)
            elif action=='retire':
                if entry['state']=='retired':return self.detail(principal,identity)
                if entry['state']!='published':raise ValueError('只有已发布资料可以停用。')
                entry.update(state='retired',retired_at=now(),retirement_reason=note)
            elif action=='access':
                roles=data.get('allowed_roles')
                if not isinstance(roles,list) or not roles or any(not isinstance(r,str) or r not in {'engineer','employee'} for r in roles):
                    raise ValueError('访问角色无效。')
                entry['allowed_roles']=sorted(set(roles))
            else:raise ValueError('不支持的维护操作。')
            self._save(entry);self._event(entry,principal,action,note)
        self.refresh()
        return self.detail(principal,identity)
