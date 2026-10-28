from copy import deepcopy
from io import BytesIO
import base64
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from app.ai_work.parsing import conditions,gate,same_conditions
from app.ai_work.review import parse_pdf,evaluate,basis_catalog,ReviewService,ConflictError,digest
from app.ai_work.export import export_xlsx,workbook_rows
from app.knowledge_assistant.core import ROOT,Corpus,Principal
from app.knowledge_assistant.server import LocalServer
from scripts.build_pdf_variants import build_pdf,cases

ENGINEER=Principal('variant-test','engineer',('DEMO-TASK-001',))

class VariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((ROOT/'data/pdf-variants-v0.1/cases.json').read_text())['cases']
        cls.basis=basis_catalog(Corpus(),ENGINEER)

    def report(self,n):
        c=self.manifest[n-1];p=ROOT/c['path'];self.assertEqual(digest(p.read_bytes()),c['sha256'])
        return parse_pdf(p.read_bytes(),p.name)

    def result(self,n):
        r=self.report(n);return r,evaluate(dict(report=r,corrections={}),self.basis)

    def test_pack_integrity_and_candidate_accounting(self):
        for n in range(1,24):
            with self.subTest(case=n):
                r=self.report(n);a=r['parse_audit']
                self.assertEqual(a['candidate_count'],a['captured_count']+a['unresolved_count'])
                for rows in r['fields'].values():
                    for row in rows:
                        for f in row['fragments']+row['condition_evidence']:
                            self.assertIn(f['quote'],r['pages'][f['page']-1]['text'])

    def test_reordered_columns_keep_port_field_and_value(self):
        r=self.report(3)
        self.assertEqual(r['fields']['C1:recovery'][0]['record_id'],'R04')
        self.assertEqual(r['fields']['C1:recovery'][0]['value'],'5.31 V')
        self.assertEqual(r['parse_audit']['captured_count'],8)

    def test_layout_aliases_wrap_and_fullwidth_are_supported(self):
        for n in [1,2,4,5,6]:
            with self.subTest(case=n):
                r,out=self.result(n)
                self.assertEqual(r['fields']['C1:response'][0]['value'],'0.68 s')
                self.assertEqual(r['parse_audit']['captured_count'],8)
                self.assertEqual(out['counts'],dict(no_issue=5,nonconformity=2,evidence_insufficient=3,conflict=2))

    def test_explicit_page_continuation_retains_both_sources(self):
        r,out=self.result(7);row=r['fields']['C1:response'][0]
        self.assertEqual(row['value'],'0.68 s')
        self.assertEqual({f['page'] for f in row['fragments']},{1,2})
        item=next(i for i in out['items'] if i['item_id']=='C1-01')
        self.assertTrue(any('接上页单位' in f['quote'] for f in item['report_evidence']))

    def test_unmarked_continuation_blocks_only_affected_unit(self):
        r,out=self.result(8);items={i['item_id']:i for i in out['items']}
        self.assertIsNone(items['C1-01']['calculation'])
        self.assertEqual(items['C1-01']['execution'],'not_checked')
        self.assertEqual(items['A1-01']['result'],'no_issue')
        self.assertTrue(any(i['code']=='orphan_unit' for i in r['parse_audit']['issues']))

    def test_scope_mismatch_or_unknown_never_produces_numeric_comparison(self):
        for n in [9,10,11,12,22,23]:
            with self.subTest(case=n):
                _,out=self.result(n);item=next(i for i in out['items'] if i['item_id']=='A1-01')
                self.assertEqual(item['execution'],'not_checked');self.assertIsNone(item['calculation'])
                self.assertNotIn(item['result'],{'no_issue','nonconformity'})

    def test_summary_different_voltage_or_environment_is_not_data_conflict(self):
        for n in [13,14]:
            with self.subTest(case=n):
                _,out=self.result(n);items={i['item_id']:i for i in out['items']}
                self.assertEqual(items['SUMMARY-C1']['result'],'evidence_insufficient')
                self.assertIn('测试条件',items['SUMMARY-C1']['explanation'])
                self.assertFalse(items['C1-01']['conditional'])
                self.assertEqual(items['C1-01']['result'],'nonconformity')

    def test_unmapped_extra_record_is_visible_and_blocks_affected_port(self):
        r,out=self.result(15)
        self.assertEqual(r['parse_audit']['candidate_count'],9)
        self.assertEqual(r['parse_audit']['unresolved_count'],1)
        self.assertTrue(any(i['kind']=='parsing' for i in out['items']))
        self.assertEqual(out['items'][0]['execution'],'not_checked')

    def test_truncated_extra_record_does_not_leave_existing_value_as_pass(self):
        r,out=self.result(16)
        self.assertTrue(r['parse_audit']['issues'])
        self.assertEqual(out['items'][0]['execution'],'not_checked')
        self.assertEqual(r['fields']['A1:response'][0]['record_id'],'R01')

    def test_missing_and_image_pages_do_not_disappear_from_coverage(self):
        for n,code in [(18,'page_count_mismatch'),(19,'unreadable_page')]:
            with self.subTest(case=n):
                r,out=self.result(n)
                self.assertTrue(any(i['code']==code for i in r['parse_audit']['issues']))
                self.assertFalse(any(i['result']=='no_issue' for i in out['items'][:10]))
                self.assertTrue(out['parsing_items'])

    def test_unknown_port_does_not_become_c1(self):
        r,out=self.result(20)
        self.assertEqual(len(r['fields']['C1:response']),1)
        issue=next(i for i in r['parse_audit']['issues'] if i['code']=='unsupported_port')
        self.assertIn('C10',issue['message'])

    def test_numeric_correction_cannot_override_test_conditions(self):
        r=self.report(9)
        out=evaluate(dict(report=r,corrections={'A1:response':dict(value='20 ms',reason='测试修正')}),self.basis)
        self.assertIsNone(out['items'][0]['calculation'])
        self.assertEqual(out['items'][0]['condition_status'],'conflict')

    def test_condition_equivalence_and_repeated_contradiction(self):
        a=conditions('电压=5.0 V；角色=输出；组合=单口；环境=25.0摄氏度')
        b=conditions('电压=5 V；角色=输出；组合=单口；环境=25°C')
        self.assertTrue(same_conditions(dict(conditions=a),dict(conditions=b)))
        eq=conditions('电压=5.0 V；电压=5 V；角色=输出；组合=单口')
        self.assertEqual(gate(dict(conditions=eq))[0],'matched')
        bad=conditions('电压=5 V；电压=9 V；角色=输出；组合=单口')
        self.assertEqual(gate(dict(conditions=bad))[0],'conflict')

    def test_additional_pdf_mixed_conditions_not_called_numeric_conflict(self):
        c=cases()[8];c['records'].insert(1,['R09','A1','保护响应','60 ms'])
        r=parse_pdf(build_pdf(c),'mixed-context.pdf')
        item=evaluate(dict(report=r,corrections={}),self.basis)['items'][0]
        self.assertEqual(item['result'],'evidence_insufficient')
        self.assertEqual(item['execution'],'not_checked')
        self.assertIn('多个测试条件',item['explanation'])

    def test_unsupported_template_still_rejected(self):
        with self.assertRaises(ValueError):self.report(24)

    def test_immutable_old_run_and_stale_parser_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            service=ReviewService(Path(tmp)/'db',Corpus())
            t=service.create(ENGINEER,{'sample':True});tid=t['task_id']
            service.confirm(ENGINEER,tid,dict(revision=1,acknowledged=True,corrections={}))
            old=service.run(ENGINEER,tid,dict(revision=2,idempotency_key='old-run-test-1'))
            t=service._task(ENGINEER,tid);t['snapshots'][-1]['report']['parser']='old-parser'
            service.db.execute('UPDATE aw_tasks SET payload=? WHERE id=?',(json.dumps(t),tid));service.db.commit()
            with self.assertRaises(ConflictError):service.run(ENGINEER,tid,dict(revision=2,idempotency_key='new-run-test-2'))
            self.assertEqual(service.result(ENGINEER,old['run_id'])['counts'],old['counts'])
            service.db.close()

    def test_export_preserves_conditions_and_coverage_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            service=ReviewService(Path(tmp)/'db',Corpus());c=self.manifest[8];blob=(ROOT/c['path']).read_bytes()
            t=service.create(ENGINEER,dict(filename='9v.pdf',pdf_base64=base64.b64encode(blob).decode()));tid=t['task_id']
            service.confirm(ENGINEER,tid,dict(revision=1,acknowledged=True,corrections={}))
            out=service.run(ENGINEER,tid,dict(revision=2,idempotency_key='export-condition-1'))
            self.assertTrue(export_xlsx(out).startswith(b'PK'))
            rows=workbook_rows(out);text=json.dumps(rows,ensure_ascii=False)
            self.assertIn('9',text);self.assertIn('不匹配',text);self.assertIn('解析覆盖',text)
            service.db.close()


class VariantHttpTests(unittest.TestCase):
    def test_upload_diagnostics_and_condition_block_are_returned_by_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            server=LocalServer(('127.0.0.1',0),ENGINEER,tmp)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def call(method,path,body=None,headers=None):
                conn=http.client.HTTPConnection(*server.server_address)
                conn.request(method,path,json.dumps(body) if body is not None else None,headers or {})
                response=conn.getresponse();raw=response.read();h=dict(response.getheaders());code=response.status;conn.close()
                return code,json.loads(raw),h
            try:
                _,cfg,h=call('GET','/api/config');headers={'Cookie':h['Set-Cookie'].split(';')[0],'X-Local-Token':cfg['csrf_token'],'Content-Type':'application/json'}
                case=json.loads((ROOT/'data/pdf-variants-v0.1/cases.json').read_text())['cases'][8]
                code,t,_=call('POST','/api/ai-work/tasks',dict(filename='row-9v.pdf',pdf_base64=base64.b64encode((ROOT/case['path']).read_bytes()).decode()),headers)
                self.assertEqual(code,200);self.assertEqual(t['snapshots'][0]['report']['parse_audit']['captured_count'],8)
                base='/api/ai-work/tasks/'+t['task_id']
                self.assertEqual(call('POST',base+'/confirm',dict(revision=1,acknowledged=True,corrections={}),headers)[0],200)
                code,out,_=call('POST',base+'/run',dict(revision=2,idempotency_key='http-variant-1'),headers)
                self.assertEqual(code,200);self.assertEqual(out['items'][0]['execution'],'not_checked');self.assertIsNone(out['items'][0]['calculation'])
            finally:
                server.shutdown();server.server_close();server.store.db.close();server.review_service.db.close()

if __name__=='__main__':unittest.main()
