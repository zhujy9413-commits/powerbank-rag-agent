"""P0 boundaries exercised with isolated synthetic material, never the user's DB."""
from copy import deepcopy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from app.knowledge_assistant.core import Corpus, Assistant, Principal
from app.knowledge_assistant.maintenance import KnowledgeMaintenance
from app.knowledge_assistant.server import Store, LocalServer
from app.ai_work.review import ReviewService, ConflictError
from app.ai_work import review
from app.ai_work.export import workbook_rows

ENGINEER=Principal('p0-engineer','engineer',('DEMO-TASK-001',))
EMPLOYEE=Principal('p0-employee','employee')
OTHER=Principal('p0-other','engineer')
class NoModel:
    def snapshot(self):return None


def document(version='1.0',text=None,document_id='P0-SYN-REFERENCE'):
    return dict(document_id=document_id,version=version,title='模拟研发响应说明',source_origin='为软件验证独立构造的模拟原文',
                usage_rights='仅用于本地模拟验证',applicability='PB-DEMO-01，5 V输出，单口短路保护记录',
                allowed_roles=['engineer','employee'],material_type='synthetic',source_role='requirement',
                original_text=text or '模拟资料\n\n## 响应条款\n保护响应时间不大于450 ms；这是独立构造的模拟要求。')


class P0CompletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
        self.corpus=Corpus();self.knowledge=KnowledgeMaintenance(self.base/'knowledge.db',self.corpus)
        self.assistant=Assistant(self.corpus,NoModel(),self.base/'vectors.json')
        self.store=Store(self.base/'requests.db')
        self.work=ReviewService(self.base/'reviews.db',self.corpus)
    def tearDown(self):
        for service in (self.knowledge,self.store,self.work):service.db.close()
        self.tmp.cleanup()
    def verified(self,data=None):
        entry=self.knowledge.submit(ENGINEER,data or document())
        return self.knowledge.transition(ENGINEER,entry['id'],dict(action='verify',note='模拟资料的来源、版本和适用性核验记录',source_verified=True,version_verified=True,applicability_verified=True))
    def published(self,data=None):
        entry=self.verified(data)
        return self.knowledge.transition(ENGINEER,entry['id'],dict(action='publish',note='发布已核验的模拟版本'))
    def task(self,extra=None):
        task=self.work.create(ENGINEER,{'sample':True})
        data=dict(revision=1,acknowledged=True,corrections={});data.update(extra or {})
        task=self.work.confirm(ENGINEER,task['task_id'],data)
        return task,self.work.run(ENGINEER,task['task_id'],dict(revision=2,idempotency_key='p0-initial-run'))

    def test_unverified_and_pending_are_not_query_candidates(self):
        before=self.corpus.snapshot
        draft=self.knowledge.submit(ENGINEER,document())
        self.assertEqual(self.knowledge.submit(ENGINEER,document())['id'],draft['id'])
        with self.assertRaises(ValueError):self.knowledge.transition(ENGINEER,draft['id'],dict(action='publish',note='不能越过核验'))
        self.assertFalse(any(c['document_id']==draft['document_id'] for c in self.corpus.candidates(ENGINEER,True)))
        self.verified()
        self.assertEqual(self.corpus.snapshot,before)
        self.assertFalse(any(c['document_id']==draft['document_id'] for c in self.corpus.candidates(ENGINEER,True)))

    def test_original_whitespace_and_preamble_are_not_lost(self):
        raw='  模拟资料前言与全局条件。\n\n## 条款一\n模拟条款。\n\n## 条款二\n模拟脚注。\n'
        entry=self.published(document(text=raw))
        self.assertEqual(entry['original_text'],raw)
        self.assertTrue(any('前言与全局条件' in c['text'] for c in entry['chunks']))
        for c in entry['chunks']:self.assertIn(c['text'],raw)

    def test_report_identity_is_separate_from_adopted_basis(self):
        task,result=self.task()
        identity=task['snapshots'][-1]['report']['identity']
        self.assertEqual(identity['report_revision'],'R1')
        self.assertEqual(identity['report_number'],'SYN-TR-001-R1')
        self.assertEqual(identity['report_date'],'2024-06-30')
        self.assertEqual(result['snapshot']['report']['report_basis'],'RevA')
        self.assertEqual(result['snapshot']['basis']['SYN-SPEC-PB01-RevB-REC']['version'],'B')

    def test_report_model_conflict_is_rejected_before_rules(self):
        class Page(dict):
            def extract_text(self):return '模拟整机保护功能测试报告 模拟材料 记录表A 型号PB-OTHER-02；产品PB-DEMO-01'
        class Reader:
            is_encrypted=False
            pages=[Page()]
        with patch('pypdf.PdfReader',return_value=Reader()):
            with self.assertRaisesRegex(ValueError,'型号冲突'):review.parse_pdf(b'%PDF-fake-model-fixture','model-conflict.pdf')

    def test_unknown_model_cannot_reuse_demo_requirements(self):
        result=self.assistant.ask('PB-OTHER-02响应要求',ENGINEER,mode='answer')
        self.assertEqual(result['status'],'needs_scope');self.assertEqual(result['claims'],[])

    def test_verification_needs_all_explicit_confirmations(self):
        draft=self.knowledge.submit(ENGINEER,document())
        with self.assertRaises(ValueError):self.knowledge.transition(ENGINEER,draft['id'],dict(action='verify',note='不完整核验',source_verified=True,version_verified=True))
        self.assertEqual(self.knowledge.detail(ENGINEER,draft['id'])['state'],'unverified')

    def test_publish_is_idempotent_and_original_is_locatable(self):
        entry=self.published();before=self.corpus.snapshot
        again=self.knowledge.transition(ENGINEER,entry['id'],dict(action='publish',note='网络重试'))
        self.assertEqual(len(again['events']),len(entry['events']))
        self.assertEqual(self.corpus.snapshot,before)
        for chunk in entry['chunks']:
            source=self.corpus.source(chunk['chunk_id'],EMPLOYEE)
            self.assertIn(source['excerpt'],source['original_text'])
            self.assertEqual(source['excerpt_kind'],'verbatim')

    def test_new_version_keeps_old_source_and_default_uses_new(self):
        old=self.published();old_id=old['chunks'][0]['chunk_id']
        new=self.published(document('1.1','模拟资料\n\n## 响应条款\n保护响应时间不大于430 ms，独立构造。'))
        live=self.corpus.candidates(EMPLOYEE)
        self.assertIn(new['chunks'][0]['chunk_id'],[c['chunk_id'] for c in live])
        self.assertNotIn(old_id,[c['chunk_id'] for c in live])
        source=self.corpus.source(old_id,EMPLOYEE)
        self.assertIn('450 ms',source['original_text']);self.assertEqual(source['publication_status'],'archived')
        # Explicit selected historical documents have a stable document identity and retain both versions.
        historical=self.assistant.ask('响应',EMPLOYEE,document_ids=[old['document_id']])
        self.assertTrue(any(s['version']=='1.0' for s in historical['sources']))

    def test_explicit_same_document_version_selection_does_not_mix_revisions(self):
        old=self.published()
        new=self.published(document('1.1','模拟资料\n\n## 响应条款\n保护响应时间不大于430 ms，独立构造。'))
        historical=self.assistant.ask('响应',EMPLOYEE,version_ids=[old['id']])
        self.assertEqual({s['version'] for s in historical['sources']},{'1.0'})
        self.assertEqual(historical['scope']['version_ids'],[old['id']])
        comparison=self.assistant.ask('比较响应',EMPLOYEE,version_ids=[old['id'],new['id']])
        self.assertEqual({s['version'] for s in comparison['sources']},{'1.0','1.1'})

    def test_conflicting_same_version_cannot_overwrite(self):
        old=self.published();before=self.corpus.snapshot
        conflicting=self.knowledge.submit(ENGINEER,document(text='另一份不同的原文，声称同一版本。'))
        self.assertIn('conflict',conflicting)
        with self.assertRaises(ValueError):self.knowledge.transition(ENGINEER,conflicting['id'],dict(action='verify',note='不能覆盖',source_verified=True,version_verified=True,applicability_verified=True))
        self.assertEqual(self.corpus.snapshot,before)
        self.assertIn('450 ms',self.corpus.source(old['chunks'][0]['chunk_id'],EMPLOYEE)['text'])

    def test_index_failure_leaves_old_snapshot_and_allows_retry(self):
        old=self.published();next_entry=self.verified(document('1.1'));before=self.corpus.snapshot
        with patch.object(self.knowledge,'build_chunks',side_effect=RuntimeError('isolated index failure')):
            with self.assertRaises(ValueError):self.knowledge.transition(ENGINEER,next_entry['id'],dict(action='publish',note='失败验证'))
        self.assertEqual(self.corpus.snapshot,before)
        self.assertEqual(self.knowledge.detail(ENGINEER,old['id'])['state'],'published')
        self.assertEqual(self.knowledge.detail(ENGINEER,next_entry['id'])['state'],'pending_publish')
        self.knowledge.transition(ENGINEER,next_entry['id'],dict(action='publish',note='恢复后重试'))
        self.assertNotEqual(self.corpus.snapshot,before)

    def test_transaction_failure_does_not_retire_old_version(self):
        old=self.published();new=self.verified(document('1.1'));before=self.corpus.snapshot
        save=self.knowledge._save
        def fail(entry):
            if entry['id']==new['id']:raise RuntimeError('isolated commit preparation failure')
            return save(entry)
        with patch.object(self.knowledge,'_save',side_effect=fail):
            with self.assertRaises(RuntimeError):self.knowledge.transition(ENGINEER,new['id'],dict(action='publish',note='事务回滚'))
        self.assertEqual(self.corpus.snapshot,before)
        self.assertEqual(self.knowledge.detail(ENGINEER,old['id'])['state'],'published')

    def test_publication_survives_restart_and_does_not_import_task_reports(self):
        entry=self.published();fresh=Corpus();reopened=KnowledgeMaintenance(self.base/'knowledge.db',fresh)
        try:
            self.assertEqual(fresh.snapshot,self.corpus.snapshot)
            self.assertEqual(fresh.source(entry['chunks'][0]['chunk_id'],EMPLOYEE)['text'],entry['chunks'][0]['text'])
            self.assertFalse(any(c['scope']!='knowledge' for e in reopened.listing(ENGINEER) for c in e['chunks']))
        finally:reopened.db.close()

    def test_retirement_and_revocation_have_different_effects(self):
        entry=self.published();cid=entry['chunks'][0]['chunk_id']
        self.knowledge.transition(ENGINEER,entry['id'],dict(action='retire',note='停用模拟条款'))
        self.assertNotIn(cid,[c['chunk_id'] for c in self.corpus.candidates(EMPLOYEE)])
        self.assertIn(cid,[c['chunk_id'] for c in self.corpus.candidates(EMPLOYEE,True)])
        self.corpus.source(cid,EMPLOYEE)
        self.knowledge.transition(ENGINEER,entry['id'],dict(action='access',note='撤销员工访问',allowed_roles=['engineer']))
        with self.assertRaises(PermissionError):self.corpus.source(cid,EMPLOYEE)

    def test_saved_answer_rechecks_revoked_source(self):
        entry=self.published();result=self.assistant.ask('模拟研发响应说明',EMPLOYEE)
        self.assertIn(entry['chunks'][0]['chunk_id'],result['trace']['retrieved_chunk_ids'])
        self.store.add(EMPLOYEE,result)
        self.knowledge.transition(ENGINEER,entry['id'],dict(action='access',note='权限变更',allowed_roles=['engineer']))
        with self.assertRaises(PermissionError):self.store.get(EMPLOYEE,result['request_id'],self.corpus)

    def test_maintenance_permissions_and_report_role_are_not_bypassed(self):
        with self.assertRaises(PermissionError):self.knowledge.submit(EMPLOYEE,document())
        with self.assertRaises(PermissionError):self.knowledge.listing(EMPLOYEE)
        with self.assertRaises(ValueError):self.knowledge.submit(ENGINEER,dict(document(),source_role='report'))
        with self.assertRaises(ValueError):self.knowledge.submit(ENGINEER,dict(document(),path='/tmp/arbitrary-file'))

    def test_vector_snapshot_is_invalidated_when_knowledge_changes(self):
        self.assistant.vectors=dict(corpus_digest=self.corpus.digest,embedding_config=None,vectors={})
        self.assertTrue(self.assistant.vector_ready())
        self.published()
        self.assertFalse(self.assistant.vector_ready())

    def test_query_explicit_version_conflict_and_unauthorized_selection(self):
        result=self.assistant.ask('RevA恢复电压',ENGINEER,mode='answer',document_ids=['SYN-SPEC-PB01-RevB'])
        self.assertEqual(result['status'],'needs_scope');self.assertEqual(result['claims'],[])
        old=self.assistant.ask('RevA恢复电压',ENGINEER,document_ids=['SYN-SPEC-PB01-RevA'])
        self.assertTrue(any(s['version']=='A' for s in old['sources']))
        self.assertFalse(any(s['version']=='B' for s in old['sources']))
        with self.assertRaises(PermissionError):self.assistant.ask('恢复',EMPLOYEE,document_ids=['SYN-SPEC-PB01-RevB'])

    def test_unknown_explicit_revision_does_not_fall_back_to_current_requirements(self):
        result=self.assistant.ask('RevZ恢复电压要求',ENGINEER,mode='answer',include_archived=True)
        self.assertEqual(result['status'],'needs_scope');self.assertEqual(result['claims'],[])
        self.assertFalse(any(s['document_id']=='SYN-SPEC-PB01-RevB' for s in result['sources']))

    def test_retrieval_error_does_not_become_no_evidence(self):
        with patch.object(self.assistant,'search',side_effect=RuntimeError('isolated retrieval error')):
            result=self.assistant.ask('恢复电压',ENGINEER,mode='answer')
        self.assertEqual(result['status'],'retrieval_failed');self.assertEqual(result['claims'],[])
        self.assertEqual(result['trace']['error_stage'],'retrieval')

    def test_feedback_retry_is_idempotent_but_cannot_change_content(self):
        result=self.assistant.ask('标准',EMPLOYEE);self.store.add(EMPLOYEE,result)
        first=self.store.feedback(EMPLOYEE,result['request_id'],'useful','',self.corpus,'feedback-test-01')
        second=self.store.feedback(EMPLOYEE,result['request_id'],'useful','',self.corpus,'feedback-test-01')
        self.assertEqual(first,second)
        with self.assertRaises(ConflictError):self.store.feedback(EMPLOYEE,result['request_id'],'wrong_answer','不同反馈',self.corpus,'feedback-test-01')
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM feedback').fetchone()[0],1)
        with self.assertRaises(PermissionError):self.store.maintenance_feedback(EMPLOYEE,self.corpus)

    def test_checklist_exclusion_and_unknown_are_saved_and_exported(self):
        checklist={'C1:appearance':dict(state='not_applicable',reason='模拟场景明确排除此项，供范围流程验证'),
                   'A1:method':dict(state='needs_confirmation',reason='模拟适用性尚未确认')}
        task,result=self.task({'checklist':checklist})
        self.assertNotIn('C1-04',[i['item_id'] for i in result['items']])
        pending=next(i for i in result['items'] if i['item_id']=='A1-05')
        self.assertEqual(pending['execution'],'not_checked');self.assertIsNone(pending['system_result'])
        exported=json.dumps(workbook_rows(result),ensure_ascii=False)
        self.assertIn(checklist['C1:appearance']['reason'],exported);self.assertIn('无比较结论',exported)
        self.assertEqual(task['snapshots'][-1]['checklist'],checklist)

    def test_scope_reason_is_required(self):
        task=self.work.create(ENGINEER,{'sample':True})
        with self.assertRaises(ValueError):self.work.confirm(ENGINEER,task['task_id'],dict(revision=1,acknowledged=True,corrections={},checklist={'A1:response':dict(state='not_applicable',reason='')}))
        self.assertEqual(len(self.work.task(ENGINEER,task['task_id'])['snapshots']),1)

    def test_published_basis_selection_binds_source_and_old_run(self):
        custom=self.published(document(document_id='P0-SYN-RESPONSE'))
        task,first=self.task()
        updated=self.work.confirm(ENGINEER,task['task_id'],dict(revision=2,acknowledged=True,corrections={},basis_selection={'SYN-NORM-RESPONSE':custom['chunks'][0]['chunk_id']}))
        second=self.work.run(ENGINEER,task['task_id'],dict(revision=3,idempotency_key='p0-custom-basis'))
        item=next(i for i in second['items'] if i['item_id']=='A1-01')
        self.assertIn('450',item['requirement']);self.assertEqual(item['basis'][0]['document_id'],custom['document_id'])
        self.assertTrue(self.work.result(ENGINEER,first['run_id'])['historical'])
        self.assertEqual(self.work.result(ENGINEER,first['run_id'])['snapshot']['basis']['SYN-NORM-RESPONSE']['chunk_id'],'SYN-NORM-RESPONSE')
        self.assertEqual(updated['snapshots'][-1]['revision'],3)

    def test_task_basis_does_not_require_publication_or_enter_public_query(self):
        attachment=dict(title='本任务模拟响应依据',version='B',text='模拟保护响应时间不大于460 ms。',source_origin='独立构造的任务附件',applicability='PB-DEMO-01，仅本任务',reason='为软件验证明确采用',confirmed=True)
        task,result=self.task({'basis_attachments':{'SYN-NORM-RESPONSE':attachment}})
        source=next(i for i in result['items'] if i['item_id']=='A1-01')['basis'][0]
        self.assertEqual(source['scope'],'task_basis');self.assertIn('460',source['text'])
        self.assertNotIn(source['chunk_id'],self.corpus.by_id)
        self.assertEqual(self.work.source(ENGINEER,task['task_id'],source['chunk_id'])['original_text'],attachment['text'])
        with self.assertRaises(PermissionError):self.work.source(OTHER,task['task_id'],source['chunk_id'])
        self.assertFalse(any(c['scope']=='task_basis' for c in self.corpus.candidates(ENGINEER,True)))

    def test_report_cannot_be_selected_as_requirement(self):
        task=self.work.create(ENGINEER,{'sample':True})
        with self.assertRaises(ValueError):self.work.confirm(ENGINEER,task['task_id'],dict(revision=1,acknowledged=True,corrections={},basis_selection={'SYN-NORM-RESPONSE':'TR-P2-RESPONSE'}))

    def test_single_unit_failure_preserves_other_results_and_retry_history(self):
        task=self.work.create(ENGINEER,{'sample':True})
        self.work.confirm(ENGINEER,task['task_id'],dict(revision=1,acknowledged=True,corrections={}))
        rank=review.rank_bm25
        def fail_one(query,candidates):
            if query=='A1 外观观察':raise RuntimeError('isolated unit failure')
            return rank(query,candidates)
        with patch.object(review,'rank_bm25',side_effect=fail_one):
            failed=self.work.run(ENGINEER,task['task_id'],dict(revision=2,idempotency_key='p0-one-failed'))
        self.assertEqual(failed['execution_counts']['failed'],1)
        self.assertEqual(next(i for i in failed['items'] if i['item_id']=='A1-04')['execution'],'failed')
        good=self.work.run(ENGINEER,task['task_id'],dict(revision=2,idempotency_key='p0-after-repair'))
        self.assertEqual(next(i for i in good['items'] if i['item_id']=='A1-04')['execution'],'completed')
        for item in failed['items']:
            if item['item_id']!='A1-04':
                other=next(i for i in good['items'] if i['item_id']==item['item_id'])
                self.assertEqual((item['result'],item['explanation']),(other['result'],other['explanation']))
        self.assertEqual(self.work.result(ENGINEER,failed['run_id'])['execution_counts']['failed'],1)

    def test_interrupted_running_record_is_recovered_as_failure(self):
        task=self.work.create(ENGINEER,{'sample':True})
        self.work.confirm(ENGINEER,task['task_id'],dict(revision=1,acknowledged=True,corrections={}))
        request=dict(revision=2,idempotency_key='p0-interrupted-run')
        with patch.object(review,'evaluate',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.work.run(ENGINEER,task['task_id'],request)
        self.work.db.close();self.work=ReviewService(self.base/'reviews.db',self.corpus)
        restored=self.work.run(ENGINEER,task['task_id'],request)
        self.assertEqual(restored['state'],'failed');self.assertEqual(restored['error_stage'],'interrupted')
        self.assertEqual(restored['execution_counts']['failed'],10)
        fresh=self.work.run(ENGINEER,task['task_id'],dict(request,idempotency_key='p0-restored-new-run'))
        self.assertNotEqual(fresh['run_id'],restored['run_id'])
        self.assertEqual(self.work.result(ENGINEER,restored['run_id'])['state'],'failed')

    def test_correction_records_original_and_failed_comparison_is_not_success(self):
        _,result=self.task({'corrections':{'A1:response':dict(value='500',reason='模拟单位缺失输入，验证不强行比较')}})
        item=next(i for i in result['items'] if i['item_id']=='A1-01')
        self.assertEqual(item['execution'],'not_checked');self.assertIsNone(item['system_result'])
        self.assertIn('original_value',item['correction']);self.assertIn('quote',item['correction'])


class P0HttpFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.server=LocalServer(('127.0.0.1',0),ENGINEER,self.tmp.name)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        status,config,headers=self.call('GET','/api/config')
        self.assertEqual(status,200)
        self.headers={'Cookie':headers['Set-Cookie'].split(';')[0],'X-Local-Token':config['csrf_token'],'Content-Type':'application/json'}
    def tearDown(self):
        self.server.shutdown();self.server.server_close()
        for service in (self.server.store,self.server.review_service,self.server.knowledge):service.db.close()
        self.tmp.cleanup()
    def call(self,method,path,body=None):
        connection=http.client.HTTPConnection(*self.server.server_address,timeout=10)
        connection.request(method,path,json.dumps(body) if body is not None else None,getattr(self,'headers',{}))
        response=connection.getresponse();raw=response.read();headers=dict(response.getheaders())
        value=json.loads(raw) if 'json' in headers.get('Content-Type','') else raw
        connection.close();return response.status,value,headers
    def test_complete_work_review_restore_and_export_flow(self):
        status,task,_=self.call('POST','/api/ai-work/tasks',{'sample':True});self.assertEqual(status,200)
        path='/api/ai-work/tasks/'+task['task_id']
        checklist={'C1:method':dict(state='needs_confirmation',reason='模拟未决范围')}
        status,task,_=self.call('POST',path+'/confirm',dict(revision=1,acknowledged=True,corrections={},checklist=checklist));self.assertEqual(status,200)
        status,run,_=self.call('POST',path+'/run',dict(revision=2,idempotency_key='http-p0-flow'));self.assertEqual(status,200)
        for item in run['items']:
            status,updated,_=self.call('POST','/api/ai-work/runs/'+run['run_id']+'/review',dict(item_id=item['item_id'],version=0,disposition='unresolved',reason='软件流程验证代操作，非专业验收'))
            self.assertEqual(status,200)
        self.assertEqual(updated['state'],'review_complete')
        status,restored,_=self.call('GET',path);self.assertEqual(status,200);self.assertEqual(restored['runs'][0]['run_id'],run['run_id'])
        status,xlsx,_=self.call('GET','/api/ai-work/runs/'+run['run_id']+'/export');self.assertEqual(status,200);self.assertTrue(xlsx.startswith(b'PK'))
    def test_knowledge_publish_query_feedback_flow(self):
        status,entry,_=self.call('POST','/api/knowledge',document());self.assertEqual(status,200)
        for action in ('verify','publish'):
            data=dict(action=action,note='软件流程核验')
            if action=='verify':data.update(source_verified=True,version_verified=True,applicability_verified=True)
            status,_,_=self.call('POST','/api/knowledge/'+entry['id'],data);self.assertEqual(status,200)
        status,query,_=self.call('POST','/api/query',dict(query='模拟研发响应说明',document_ids=[entry['document_id']]));self.assertEqual(status,200);self.assertTrue(query['sources'])
        data=dict(request_id=query['request_id'],kind='wrong_citation',note='模拟反馈',operation_key='http-p0-feedback')
        a=self.call('POST','/api/feedback',data);b=self.call('POST','/api/feedback',data)
        self.assertEqual(a[1],b[1])
        status,feedback,_=self.call('GET','/api/maintenance-feedback');self.assertEqual(status,200);self.assertEqual(len(feedback),1)
        status,_,_=self.call('POST','/api/maintenance-feedback/'+str(feedback[0]['id']),dict(state='handled',note='已核对模拟原文，未自动发布'));self.assertEqual(status,200)
        status,js,_=self.call('GET','/maintenance.js');self.assertEqual(status,200);self.assertIn(b'loadMaintenance',js)
