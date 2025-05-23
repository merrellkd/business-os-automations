import unittest

from semantic_search.flow import create_query_flow


class TestQueryFlow(unittest.TestCase):
    def test_flow_runs_with_minimal_shared(self):
        shared = {
            'query': {'query': 'test question'},
            'config': {'llm_provider': 'ollama', 'output_format': 'chat'},
        }
        flow = create_query_flow()
        result = flow.run(shared)
        self.assertIn('llm_response', shared['query'])
        self.assertEqual(result, shared['query']['llm_response'])


if __name__ == '__main__':
    unittest.main()
