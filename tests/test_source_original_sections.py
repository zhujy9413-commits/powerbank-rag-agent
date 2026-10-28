import unittest
from app.knowledge_assistant.core import Corpus,Principal,original_section
from app.ai_work.review import basis_catalog

class OriginalSectionTests(unittest.TestCase):
    def test_every_active_review_basis_has_exact_original_section(self):
        corpus=Corpus();actor=Principal('source-qa','engineer',('DEMO-TASK-001',))
        for cid,basis in basis_catalog(corpus,actor).items():
            with self.subTest(cid=cid):
                source=corpus.source(cid,actor)
                self.assertEqual(source['excerpt'],basis['text'])
                self.assertEqual(source['excerpt_kind'],'index_summary')
                self.assertIn(source['original_excerpt'],source['original_text'])
                self.assertIn(basis['section'].split()[0],source['original_excerpt'])
    def test_summary_and_original_remain_distinct(self):
        source=Corpus().source('SYN-NORM-RESPONSE',Principal('qa','engineer',()))
        self.assertIn('500 ms',source['original_excerpt']);self.assertNotEqual(source['excerpt'],source['original_excerpt'])
        self.assertTrue(source['original_excerpt'].startswith('## DEMO-01'))
        self.assertNotIn('## DEMO-02',source['original_excerpt'])
    def test_identity_boundaries_and_ambiguity_never_guess(self):
        text='## DEMO-010 Other\nwrong\n## DEMO-01 Desired\ncorrect\n'
        self.assertIn('correct',original_section(text,'DEMO-01'));self.assertNotIn('wrong',original_section(text,'DEMO-01'))
        self.assertIsNone(original_section(text,'DEMO-03'))
        self.assertIsNone(original_section('## A\nSPEC-REC x\n## B\nSPEC-REC y','SPEC-REC'))
        self.assertIsNone(original_section('## DEMO-01 A\nx\n## DEMO-01 B\ny','DEMO-01'))
    def test_clause_tag_inside_unique_body_retains_original_heading(self):
        result=original_section('## 身份\nRevB\n## 恢复电压要求\n模拟条款 SPEC-REC：4.75 V 至5.25 V\n','SPEC-REC')
        self.assertTrue(result.startswith('## 恢复电压要求'))
        self.assertEqual(result,original_section('## 身份\nRevB\n## 恢复电压要求\n模拟条款 SPEC-REC：4.75 V 至5.25 V\n','SPEC-REC 恢复电压'))

if __name__=='__main__':unittest.main()
