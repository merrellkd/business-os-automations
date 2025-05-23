import unittest

from semantic_search.utils.llm_utils import (
    init_providers,
    route_to_provider,
    format_context,
    handle_streaming,
    call_llm,
)


class TestLLMUtils(unittest.TestCase):
    def test_init_providers_returns_dict(self):
        providers = init_providers({})
        self.assertIsInstance(providers, dict)
        self.assertIn("ollama", providers)

    def test_route_to_provider(self):
        res = route_to_provider("high", user_preference="local")
        self.assertEqual(res["provider"], "openai")

    def test_format_context(self):
        chunks = ["a", "b"]
        self.assertEqual(format_context(chunks), "a\nb")

    def test_handle_streaming(self):
        stream = ["a", "b", "c"]
        self.assertEqual(handle_streaming(stream), "abc")

    def test_call_llm_returns_str(self):
        out = call_llm("hello", "llama2", provider="ollama")
        self.assertIsInstance(out, str)


if __name__ == "__main__":
    unittest.main()
