"""Promoted v0.1 holdout failures are now regression data, never new holdout scores."""
from copy import deepcopy
import json
import unittest

from app.ai_work.parsing import extract_report,inspect_visuals
from app.ai_work.review import parse_pdf,evaluate,basis_catalog
from app.knowledge_assistant.core import ROOT,Corpus,Principal

class P0ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((ROOT/'data/review-holdout-v0.1/cases.json').read_text())['cases']
        cls.basis=basis_catalog(Corpus(),Principal('p0-regression','engineer',('DEMO-TASK-001',)))
    def old(self,n):
        case=self.manifest[n-1];p=ROOT/case['path'];r=parse_pdf(p.read_bytes(),p.name)
        return r,evaluate(dict(report=r,corrections={}),self.basis)
    def blocked(self,item):
        self.assertEqual(item['execution'],'not_checked');self.assertEqual(item['result'],'evidence_insufficient');self.assertIsNone(item['calculation'])
    def pages(self,text,visual=None):
        p=dict(text=text,page=1,source_id='unit-page')
        if visual:p['visual_audit']=visual
        return [p]
    def test_promoted_p0_failures_never_claim_no_issue(self):
        for n in [4,5,7,8,9]:
            with self.subTest(case=n):
                report,out=self.old(n);items={i['item_id']:i for i in out['items']}
                for check in self.manifest[n-1]['checks']:self.blocked(items[check['item_id']])
                self.assertEqual(report['parse_audit']['coverage_status'],'needs_review')
    def test_foreign_identity_keeps_explicit_candidate_and_quote(self):
        report,out=self.old(4);a=report['parse_audit']
        self.assertEqual((a['candidate_count'],a['captured_count'],a['unresolved_count']),(11,10,1))
        issue=next(i for i in a['issues'] if 'TC-401' in i['message'])
        self.assertIn('913 ms',issue['evidence'][0]['quote'])
    def test_long_identity_does_not_disappear(self):
        report,_=self.old(5);a=report['parse_audit']
        self.assertEqual((a['candidate_count'],a['unresolved_count']),(10,10))
    def test_unapproved_ids_in_delimited_and_vertical_layouts(self):
        for text in ['记录 | 端口 | 字段 | 原始填写\nTX-710 | A1 | 保护响应 | 877 ms',
                     '记录\n端口\n字段\n原始填写\nR876543\nC1\n恢复电压\n5.91 V']:
            with self.subTest(text=text):
                a=extract_report(self.pages(text))['parse_audit']
                self.assertEqual(a['candidate_count'],1);self.assertEqual(a['unresolved_count'],1);self.assertTrue(a['issues'])
    def test_record_shaped_line_without_identity_is_audited(self):
        r=extract_report(self.pages('A1 保护响应 987 ms'))
        self.assertEqual(r['parse_audit']['unresolved_count'],1)
        self.assertIn('A1:response',r['parse_audit']['issues'][0]['affected_keys'])
    def test_opaque_identity_formats_are_detected_by_record_structure(self):
        for text in ['测试-71 A1 保护响应 876 ms','记录 | 端口 | 字段 | 原始填写\n检查甲 | C1 | 恢复电压 | 5.91 V',
                     '记录\n端口\n字段\n原始填写\n检查乙\nA1\n保护响应\n871 ms']:
            with self.subTest(text=text):
                a=extract_report(self.pages(text))['parse_audit'];self.assertEqual(a['unresolved_count'],1)
    def test_empty_candidate_set_is_not_full_coverage(self):
        a=extract_report(self.pages('记录表A\n完全无法还原的表格'))['parse_audit']
        self.assertEqual(a['coverage_status'],'needs_review');self.assertIn('no_record_candidates',[i['code'] for i in a['issues']])
    def test_unitless_value_before_next_record_is_not_an_identity(self):
        text='记录\n端口\n字段\n原始填写\nR01\nA1\n保护响应\n80\nR02\nC1\n保护响应\n0.67 s'
        r=extract_report(self.pages(text))
        self.assertEqual(r['fields']['A1:response'][0]['value'],'80')
        self.assertEqual(r['parse_audit']['captured_count'],2);self.assertFalse(r['parse_audit']['issues'])
    def test_mixed_images_remain_unverified_on_text_pages(self):
        r,out=self.old(7)
        self.assertEqual(r['pages'][0]['visual_audit']['image_draws'],1)
        issue=next(i for i in r['parse_audit']['issues'] if i['code']=='unverified_image_content')
        self.assertEqual(issue['evidence'][0]['quote'],'')
        self.assertEqual(len(issue['affected_keys']),10)
        for item in out['items'][:10]:self.blocked(item)
    def test_visual_inspection_failure_is_conservative(self):
        class BrokenPage:
            def get_contents(self):raise ValueError('bad resource')
        visual=inspect_visuals(BrokenPage());self.assertEqual(visual['status'],'inspection_failed')
        a=extract_report(self.pages('R01 A1 保护响应 77 ms',visual))['parse_audit']
        self.assertIn('visual_inspection_failed',[i['code'] for i in a['issues']])
    def test_footnote_binds_only_exact_record_identity(self):
        text='R01 A1 保护响应 31 ms\nR010 C1 保护响应 41 ms\n注：R01实际测试条件为电压=12 V；角色=输入；组合=多口。'
        r=extract_report(self.pages(text));issue=next(i for i in r['parse_audit']['issues'] if i['code']=='unbound_local_condition')
        self.assertEqual(issue['affected_keys'],['A1:response'])
    def test_local_port_scope_does_not_override_global_silently(self):
        r=extract_report(self.pages('本报告测试条件：电压=5 V；角色=输出；组合=单口\nA1本表局部条件：电压=12 V；角色=输出；组合=单口\nR01 A1 保护响应 37 ms'))
        issue=next(i for i in r['parse_audit']['issues'] if i['code']=='unbound_local_condition')
        self.assertEqual(set(issue['affected_keys']),{'A1:'+k for k in ['response','recovery','temperature','appearance','method']})
    def test_unbound_prose_conditions_are_not_inherited_as_global(self):
        r=extract_report(self.pages('R01 A1 保护响应 39 ms\n备注：R01实测为12 V输出单口'))
        self.assertEqual(r['parse_audit']['issues'][0]['code'],'unbound_local_condition')
        self.assertEqual(r['parse_audit']['issues'][0]['affected_keys'],['A1:response'])
    def test_report_input_disclaimer_is_not_a_test_role(self):
        r=extract_report(self.pages('R01 A1 保护响应 39 ms\n本表是待审核输入。通过文字只是报告原文。'))
        self.assertFalse(r['parse_audit']['issues'])
    def test_global_and_bound_row_conditions_are_not_false_alarms(self):
        text='本报告测试条件：电压=5 V；角色=输出；组合=单口\nR01 A1 保护响应 123 ms\n条件：电压=9 V；角色=输出；组合=单口\nS01：A1保护响应 123 ms；条件：电压=9 V；角色=输出；组合=单口'
        r=extract_report(self.pages(text));self.assertFalse(r['parse_audit']['issues'])
        self.assertEqual(r['fields']['A1:response'][0]['conditions']['voltage'],'9')
    def test_numeric_corrections_do_not_erase_image_or_local_coverage_blocks(self):
        for n in [7,8,9]:
            with self.subTest(case=n):
                r,_=self.old(n);out=evaluate(dict(report=r,corrections={'A1:response':dict(value='1 ms',reason='unit test')}),self.basis)
                self.blocked(out['items'][0])

if __name__=='__main__':unittest.main()
