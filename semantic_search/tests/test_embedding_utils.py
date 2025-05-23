import unittest

from semantic_search.utils.embedding_utils import (
    generate_embeddings,
    fallback_to_cloud,
    init_ollama_embeddings,
    validate_model_availability,
)


class TestEmbeddingUtils(unittest.TestCase):
    def test_generate_embeddings_shape(self):
        texts = ["hello world", "another piece of text"]
        vectors = generate_embeddings(texts, use_fallback=True)
        self.assertEqual(len(vectors), 2)
        self.assertEqual(len(vectors[0]), 768)

    def test_validate_model_availability_returns_bool(self):
        # We cannot know if ollama is installed in the test environment so we
        # simply assert that the function returns a boolean value.
        result = validate_model_availability("nomic-embed-text")
        self.assertIsInstance(result, bool)

    def test_fallback_to_cloud(self):
        texts = ["one"]
        vecs = fallback_to_cloud(texts)
        self.assertEqual(len(vecs), 1)
        self.assertEqual(len(vecs[0]), 768)


if __name__ == "__main__":
    unittest.main()
