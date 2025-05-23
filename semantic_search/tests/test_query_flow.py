import unittest
import shutil
from pathlib import Path

from semantic_search.flow import create_indexing_flow, create_query_flow


class TestQueryFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = Path('tmp_query_flow')
        shutil.rmtree(self.tmp, ignore_errors=True)
        self.tmp.mkdir()
        self.repo = self.tmp / 'repo'
        self.repo.mkdir()
        (self.repo / 'doc.md').write_text('hello world')

        self.shared = {
            'config': {
                'root_path': str(self.repo),
                'file_extensions': ['.md'],
                'index_path': str(self.tmp / 'index.pkl'),
                'metadata_path': str(self.tmp / 'meta.db'),
                'llm_provider': 'openai',
            },
            'indexing': {},
            'query': {},
        }

        # Build the index so query flow has something to search
        flow = create_indexing_flow()
        flow.run(self.shared)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_simple_query_flow(self):
        self.shared['query']['query'] = 'hello'
        flow = create_query_flow()
        flow.run(self.shared)
        self.assertIn('search_results', self.shared['query'])
        self.assertTrue(self.shared['query']['search_results'])
        self.assertIn('llm_response', self.shared['query'])

    def test_temporal_query_flow(self):
        self.shared['query']['query'] = 'what changed in last 7 days'
        flow = create_query_flow()
        flow.run(self.shared)
        self.assertTrue(self.shared['query']['temporal_files'])
        self.assertIn('llm_response', self.shared['query'])


if __name__ == '__main__':
    unittest.main()
