"""Display examples exercise actual retrieval; they never supply its answers."""
from copy import deepcopy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from app.knowledge_assistant.core import Assistant, Corpus, Principal
from app.knowledge_assistant.demo import CASES, demo_catalog
from app.knowledge_assistant.maintenance import KnowledgeMaintenance
from app.knowledge_assistant.providers import ProviderError
from app.knowledge_assistant.server import LocalServer

ENGINEER = Principal('demo-checker', 'engineer', ('DEMO-TASK-001',))
EMPLOYEE = Principal('demo-employee', 'employee')


class NoModel:
    def snapshot(self):
        return None


class DemoCatalogTests(unittest.TestCase):
    def test_eight_examples_retrieve_required_groups_from_real_sample_index(self):
        corpus = Corpus()
        catalog = demo_catalog(corpus, ENGINEER)
        self.assertEqual(len(catalog['cases']), 8)
        with tempfile.TemporaryDirectory() as directory:
            assistant = Assistant(corpus, NoModel(), Path(directory) / 'none.json')
            for example in catalog['cases']:
                with self.subTest(case=example['id']):
                    request = dict(example['request'])
                    question = request.pop('query')
                    result = assistant.ask(question, ENGINEER, **request)
                    found = set(result['trace']['retrieved_chunk_ids'])
                    for group in example['groups']:
                        self.assertTrue(found.intersection(group['chunk_ids']), group['label'])
                    self.assertEqual(result['trace']['generation'],
                        'skipped_insufficient_scope_or_evidence' if example['expected_status'] else 'not_requested')
                    if example['expected_status']:
                        self.assertEqual(result['status'], example['expected_status'])

    def test_demo_facts_do_not_disclose_restricted_numbers_to_employee(self):
        catalog = demo_catalog(Corpus(), EMPLOYEE)
        self.assertEqual([c['id'] for c in catalog['cases']], ['D08'])
        raw = json.dumps(catalog, ensure_ascii=False)
        for restricted in ['500 ms', '4.75', '0.68', 'DEMO-TASK-001', 'TR-P2-RESPONSE']:
            self.assertNotIn(restricted, raw)

    def test_knowledge_role_does_not_grant_task_example_access(self):
        principal = Principal('no-task', 'engineer')
        examples = demo_catalog(Corpus(), principal)['cases']
        self.assertEqual([c['id'] for c in examples], ['D01', 'D02', 'D03', 'D04', 'D08'])
        self.assertFalse(any(c['request']['task_id'] for c in examples))

    def test_changed_original_is_not_compared_against_stale_demo_facts(self):
        corpus = Corpus()
        corpus.by_id['SYN-SPEC-PB01-RevB-REC']['managed_original'] = '已经换版的模拟原文'
        self.assertFalse({'D01', 'D02', 'D07'} & {c['id'] for c in demo_catalog(corpus, ENGINEER)['cases']})

    def test_retirement_removes_affected_active_version_examples(self):
        corpus = Corpus()
        corpus.by_id['SYN-SPEC-PB01-RevB-REC']['publication_status'] = 'disabled'
        self.assertNotIn('D01', [c['id'] for c in demo_catalog(corpus, ENGINEER)['cases']])

    def test_managed_seed_versions_use_actual_query_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            corpus = Corpus()
            maintenance = KnowledgeMaintenance(Path(directory) / 'knowledge.db', corpus)
            try:
                first = demo_catalog(corpus, ENGINEER)['cases'][0]
                self.assertEqual(first['request']['version_ids'], ['SEED-SYN-SPEC-PB01-RevB'])
                result = Assistant(corpus, NoModel(), Path(directory) / 'none.json').ask(
                    first['request']['query'], ENGINEER,
                    **{k:v for k,v in first['request'].items() if k != 'query'})
                self.assertIn('SYN-SPEC-PB01-RevB-REC', result['trace']['retrieved_chunk_ids'])
            finally:
                maintenance.db.close()

    def test_display_expectation_is_not_in_generation_context(self):
        corpus = Corpus()
        labels = deepcopy(CASES)
        labels[2]['expectation'] = 'DISPLAY_ONLY_REFERENCE_SENTINEL'
        captured = []
        def generate(config, question, evidence, scope):
            captured.append(json.dumps([question, evidence, scope], ensure_ascii=False))
            raise ProviderError('模拟生成中断')
        class Configured:
            def snapshot(self):
                return {'provider': 'test', 'model': 'test'}
        with patch('app.knowledge_assistant.demo.CASES', labels), tempfile.TemporaryDirectory() as directory:
            example = next(c for c in demo_catalog(corpus, ENGINEER)['cases'] if c['id'] == 'D03')
            request = dict(example['request']); request['mode'] = 'answer'
            question = request.pop('query')
            Assistant(corpus, Configured(), Path(directory) / 'none.json', generator=generate).ask(question, ENGINEER, **request)
        self.assertEqual(len(captured), 1)
        self.assertNotIn('DISPLAY_ONLY_REFERENCE_SENTINEL', captured[0])


class DemoHttpTests(unittest.TestCase):
    def test_demo_catalog_requires_session_and_returns_no_private_case_for_employee(self):
        with tempfile.TemporaryDirectory() as directory:
            server = LocalServer(('127.0.0.1', 0), EMPLOYEE, Path(directory))
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            connection = http.client.HTTPConnection(*server.server_address, timeout=10)
            try:
                connection.request('GET', '/api/demo-cases')
                response = connection.getresponse(); response.read()
                self.assertEqual(response.status, 401)
                connection.request('GET', '/api/config')
                response = connection.getresponse(); cookie = response.getheader('Set-Cookie').split(';')[0]; response.read()
                connection.request('GET', '/api/demo-cases', headers={'Cookie': cookie})
                response = connection.getresponse(); catalog = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertEqual([c['id'] for c in catalog['cases']], ['D08'])
            finally:
                connection.close(); server.shutdown(); server.server_close(); thread.join()
                for store in [server.knowledge, server.store, server.review_service]:
                    store.db.close()
