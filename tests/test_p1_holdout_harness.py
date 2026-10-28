"""Scoring-only adversarial self-checks; never imports or evaluates fresh PDFs."""
from copy import deepcopy
import unittest
from scripts.evaluate_p1_holdout import score_p1

class P1HarnessTests(unittest.TestCase):
    def fixture(self):
        case=dict(case_id='SCORE-ONLY',title='scorer',expected_text_records=[],expected_visual_records=[],checks=[],expected_reject=False,
            capture_required=True,visible_issue_required=False,sha256='abc',expected_summaries=[['S90','A1','0.251 s']],
            expected_unit_owners=[[1,'s','summary','S90']],expected_summary_conditions={'S90':{'voltage':'5'}},required_issue_codes=[],expected_orphan_keys=[])
        f=dict(source_id='p',page=1,quote='s')
        actual=dict(parsed=True,report=dict(fields={},pages=[dict(source_id='p',page=1,text='S90：A1保护响应 0.251\ns',sha256='abc')],
            summary=[dict(record_id='S90',port='A1',value='0.251 s',conditions={'voltage':'5'},fragments=[f],condition_evidence=[])],
            parse_audit=dict(issues=[],unit_ownership=[dict(owner_type='summary',owner_id='S90',evidence=f)])),review=dict(items=[]))
        return case,actual
    def test_full_control_passes(self):
        c,a=self.fixture();self.assertTrue(score_p1(c,a)['passed'])
    def test_wrong_summary_value_fails(self):
        c,a=self.fixture();a['report']['summary'][0]['value']='0.951 s';self.assertFalse(score_p1(c,a)['passed'])
    def test_missing_or_misbound_unit_fails(self):
        for change in ['missing','misbound','duplicate']:
            c,a=self.fixture();owners=a['report']['parse_audit']['unit_ownership']
            if change=='missing':owners.clear()
            elif change=='misbound':owners[0]['owner_id']='R900'
            else:owners.append(deepcopy(owners[0]))
            self.assertFalse(score_p1(c,a)['passed'])
    def test_missing_condition_is_not_equal_to_explicit_unknown(self):
        c,a=self.fixture();c['expected_summary_conditions']['S90']['voltage']=None;a['report']['summary'][0]['conditions']={}
        self.assertFalse(score_p1(c,a)['passed'])
    def test_invented_fragment_or_page_fails(self):
        c,a=self.fixture();a['report']['summary'][0]['fragments']=[dict(source_id='p',page=2,quote='s')]
        self.assertFalse(score_p1(c,a)['passed'])
    def test_wrong_orphan_scope_fails(self):
        c,a=self.fixture();a['report']['parse_audit']['issues']=[dict(code='orphan_unit',affected_keys=['A1:method'])]
        c['expected_orphan_keys']=['A1:response'];self.assertFalse(score_p1(c,a)['passed'])

if __name__=='__main__':unittest.main()
