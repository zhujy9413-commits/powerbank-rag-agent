"""Consumed HO-17 and focused ownership regression; no fresh holdout inputs here."""
import json
import unittest
from app.ai_work.parsing import extract_report
from app.ai_work.review import parse_pdf,evaluate,basis_catalog
from app.knowledge_assistant.core import ROOT,Corpus,Principal

GLOBAL='本报告测试条件：电压=5 V；角色=输出；组合=单口\n'

class P1OwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.basis=basis_catalog(Corpus(),Principal('p1-regression','engineer',('DEMO-TASK-001',)))
    def parse(self,*texts):
        return extract_report([dict(text=GLOBAL+t if n==1 else t,page=n,source_id=f'p{n}') for n,t in enumerate(texts,1)])
    def issue(self,r,code):return [i for i in r['parse_audit']['issues'] if i['code']==code]
    def test_ho17_actual_fix_preserves_old_label_file(self):
        c=json.loads((ROOT/'data/review-holdout-v0.1/cases.json').read_text())['cases'][16]
        self.assertIn(dict(item_id='SUMMARY-MISSING',result='evidence_insufficient'),c['checks'])
        p=ROOT/c['path'];r=parse_pdf(p.read_bytes(),p.name);out=evaluate(dict(report=r,corrections={}),self.basis)
        by={i['item_id']:i for i in out['items']}
        self.assertEqual(r['summary'][0]['value'],'0.137 s');self.assertFalse(self.issue(r,'orphan_unit'))
        self.assertEqual(by['SUMMARY-A1']['result'],'no_issue');self.assertEqual(by['A1-05']['result'],'no_issue')
        self.assertNotIn('SUMMARY-MISSING',by)
    def test_same_page_summary_two_and_three_lines_share_unit_owner(self):
        for s in ['S12：A1保护响应 0.137\ns','S12：A1保护响应\n0.137\ns']:
            with self.subTest(s=s):
                r=self.parse('R01 A1 保护响应 137 ms\n'+s)
                self.assertEqual(r['summary'][0]['value'],'0.137 s');self.assertFalse(r['parse_audit']['issues'])
                own=r['parse_audit']['unit_ownership'];self.assertEqual((own[0]['owner_type'],own[0]['owner_id']),('summary','S12'))
                self.assertIn(r['summary'][0]['quote'],GLOBAL+'R01 A1 保护响应 137 ms\n'+s)
    def test_summary_label_then_numeric_and_unit_line(self):
        r=self.parse('R01 A1 保护响应 137 ms\nS12：A1保护响应\n137 ms')
        self.assertEqual(r['summary'][0]['value'],'137 ms');self.assertFalse(r['parse_audit']['issues'])
    def test_summary_next_line_conditions_bind_to_summary_not_method(self):
        r=self.parse('R01 A1 恢复方式 记录为重新接入负载端\nS12：A1保护响应 0.137\ns\n条件：电压=9 V；角色=输出；组合=单口')
        self.assertEqual(r['fields']['A1:method'][0]['conditions']['voltage'],'5')
        self.assertEqual(r['summary'][0]['conditions']['voltage'],'9');self.assertFalse(r['parse_audit']['issues'])
    def test_summary_condition_conflict_is_not_same_condition_numeric_conflict(self):
        r=self.parse('R01 A1 保护响应 137 ms\nS12：A1保护响应 0.777\ns\n条件：电压=9 V；角色=输出；组合=单口')
        r.update(pages=[dict(text=GLOBAL+'R01 A1 保护响应 137 ms\nS12：A1保护响应 0.777\ns\n条件：电压=9 V；角色=输出；组合=单口',page=1,source_id='p1',sha256='x',title='unit.pdf',document_id='unit',scope='task_only',material_type='synthetic')],report_basis='RevB')
        out=evaluate(dict(report=r,corrections={}),self.basis);by={i['item_id']:i for i in out['items']}
        self.assertFalse(by['A1-01']['conditional']);self.assertEqual(by['SUMMARY-A1']['result'],'evidence_insufficient')
    def test_incomplete_summary_never_steals_next_record_or_its_unit(self):
        r=self.parse('S12：A1保护响应 137\nR02 C1 保护响应 0.327\ns')
        self.assertFalse(r['summary']);self.assertEqual(r['fields']['C1:response'][0]['value'],'0.327 s')
        self.assertEqual(self.issue(r,'unresolved_summary')[0]['affected_keys'],['A1:response'])
    def test_blank_or_heading_breaks_summary_join(self):
        for gap in ['\n','记录表B\n']:
            r=self.parse('R01 A1 恢复方式 记录为重新接入负载端\nS12：A1保护响应 137\n'+gap+'ms')
            self.assertFalse(r['summary']);self.assertTrue(self.issue(r,'unresolved_summary'));self.assertTrue(self.issue(r,'orphan_unit'))
    def test_cross_page_summary_is_not_auto_merged(self):
        r=self.parse('R01 A1 恢复方式 记录为重新接入负载端\nS12：A1保护响应 137','ms')
        self.assertFalse(r['summary']);self.assertEqual(len(self.issue(r,'orphan_unit')[0]['affected_keys']),10)
    def test_unsupported_summary_unit_is_audited_without_false_numeric_conflict(self):
        r=self.parse('R01 A1 保护响应 137 ms\nS12：A1保护响应 137\nus')
        self.assertFalse(r['summary']);self.assertTrue(self.issue(r,'unresolved_summary'));self.assertFalse(self.issue(r,'orphan_unit'))
    def test_unknown_summary_port_does_not_disappear(self):
        r=self.parse('R01 A1 保护响应 137 ms\nS12：B2保护响应 137\nms')
        self.assertEqual(len(self.issue(r,'unresolved_summary')[0]['affected_keys']),10)
    def test_unrelated_orphan_unit_does_not_attach_to_previous_method(self):
        r=self.parse('R01 A1 恢复方式 记录为重新接入负载端','s')
        self.assertEqual(len(self.issue(r,'orphan_unit')[0]['affected_keys']),10)
        self.assertIsNone(r['parse_audit']['unit_ownership'][0]['owner_id'])
    def test_explicit_cross_page_record_unit_uses_unique_pending_tail(self):
        r=self.parse('R01 C1 保护响应 0.627','续表A（接上页单位）\ns')
        row=r['fields']['C1:response'][0];self.assertEqual(row['value'],'0.627 s');self.assertEqual(len(row['fragments']),2)
        self.assertFalse(r['parse_audit']['issues']);self.assertEqual(r['parse_audit']['unit_ownership'][0]['owner_type'],'record_continuation')
    def test_unmarked_pending_tail_is_diagnosed_without_join(self):
        r=self.parse('R01 C1 保护响应 0.627','s')
        self.assertEqual(r['fields']['C1:response'][0]['value'],'0.627')
        self.assertEqual(self.issue(r,'orphan_unit')[0]['affected_keys'],['C1:response'])
    def test_multiple_pending_records_never_guess_unit_owner(self):
        r=self.parse('R01 A1 保护响应 137\nR02 C1 保护响应 0.627','续表A（接上页单位）\ns')
        self.assertEqual(r['fields']['C1:response'][0]['value'],'0.627');self.assertEqual(len(self.issue(r,'orphan_unit')[0]['affected_keys']),10)
    def test_current_page_activity_prevents_old_tail_claim(self):
        r=self.parse('R01 C1 保护响应 0.627','R02 A1 恢复方式 记录为重新接入负载端\n续表A（接上页单位）\ns')
        self.assertEqual(r['fields']['C1:response'][0]['value'],'0.627');self.assertEqual(len(self.issue(r,'orphan_unit')[0]['affected_keys']),10)
    def test_fully_typed_tail_is_never_reused(self):
        r=self.parse('R01 C1 保护响应 627 ms','续表A（接上页单位）\ns')
        self.assertEqual(r['fields']['C1:response'][0]['value'],'627 ms');self.assertEqual(len(self.issue(r,'orphan_unit')[0]['affected_keys']),10)
    def test_inline_vertical_delimited_record_unit_has_correct_owner(self):
        for t in ['R01 A1 保护响应 137\nms','记录\n端口\n字段\n原始填写\nR01\nA1\n保护响应\n137\nms',
                  '记录 | 端口 | 字段 | 原始填写\nR01 | A1 | 保护响应 | 137\nms']:
            r=self.parse(t);self.assertEqual(r['fields']['A1:response'][0]['value'],'137 ms')
            self.assertEqual(r['parse_audit']['unit_ownership'][0]['owner_id'],'R01');self.assertFalse(r['parse_audit']['issues'])
    def test_method_numeric_does_not_claim_response_unit(self):
        r=self.parse('R01 A1 恢复方式 137\ns');self.assertEqual(r['fields']['A1:method'][0]['value'],'137')
        self.assertTrue(self.issue(r,'orphan_unit'))
    def test_two_summary_anchors_keep_distinct_unit_ownership(self):
        r=self.parse('R01 A1 保护响应 137 ms\nS12：A1保护响应 0.137\ns\nS13：C1保护响应\n627\nms')
        self.assertEqual([s['port'] for s in r['summary']],['A1','C1'])
        self.assertEqual([u['owner_id'] for u in r['parse_audit']['unit_ownership']],['S12','S13'])
    def test_summary_cannot_supply_unit_to_previous_detail(self):
        r=self.parse('R01 C1 保护响应 0.627','S12：A1保护响应 0.137\ns')
        self.assertEqual(r['fields']['C1:response'][0]['value'],'0.627');self.assertFalse(self.issue(r,'orphan_unit'))
    def test_unbound_conditions_after_incomplete_summary_do_not_mutate_previous_record(self):
        r=self.parse('R01 A1 恢复方式 记录为重新接入负载端\nS12：A1保护响应 137\n条件：电压=9 V')
        self.assertEqual(r['fields']['A1:method'][0]['conditions']['voltage'],'5');self.assertTrue(self.issue(r,'unbound_condition'))

if __name__=='__main__':unittest.main()
