"""Scorer correctness only. These tests never invoke the engine on holdout PDFs."""
import unittest
from scripts.evaluate_review_holdout import score

class HoldoutHarnessTests(unittest.TestCase):
    def case(self,**extra):
        return dict(case_id='SCORER-ONLY',title='harness',expected_text_records=[['R900','A1','response','199 ms']],
                    expected_visual_records=[],expected_reject=False,checks=[dict(item_id='A1-01',blocked=True)],
                    visible_issue_required=False,capture_required=True,sha256='abc',**extra)
    def actual(self,**item):
        return dict(parsed=True,report=dict(fields={'x':[dict(record_id='R900',port='A1',kind='response',value='199 ms')]},pages=[]),
                    review=dict(items=[dict(item_id='A1-01',result='evidence_insufficient',calculation=None,**item)]))
    def test_missing_record_stays_in_denominator(self):
        a=self.actual();a['report']['fields']={};s=score(self.case(),a)
        self.assertEqual((s['text_expected'],s['text_matched']),(1,0));self.assertFalse(s['passed'])
    def test_positive_comparison_cannot_be_block(self):
        a=self.actual();a['review']['items'][0].update(result='no_issue',calculation='199 <= 500')
        self.assertFalse(score(self.case(),a)['passed'])
    def test_conservative_behavior_and_full_extraction_pass(self):
        self.assertTrue(score(self.case(),self.actual())['passed'])
    def test_exception_is_not_expected_encryption_rejection(self):
        c=self.case();c['expected_reject']=True
        self.assertFalse(score(c,dict(parsed=False,error_type='RuntimeError',error='加密'))['passed'])
        self.assertTrue(score(c,dict(parsed=False,error_type='ValueError',error='暂不支持加密PDF'))['passed'])
    def test_invalid_reference_fails_case(self):
        a=self.actual();a['report']['pages']=[dict(source_id='p',page=1,text='真实原文')]
        a['review']['items'][0]['report_evidence']=[dict(source_id='p',page=1,quote='不存在的引用',sha256='abc')]
        self.assertFalse(score(self.case(),a)['passed'])
    def test_extraction_optional_does_not_waive_warning(self):
        c=self.case();c.update(capture_required=False,visible_issue_required=True)
        a=self.actual();a['report']['fields']={}
        self.assertFalse(score(c,a)['passed'])

if __name__=='__main__':unittest.main()
