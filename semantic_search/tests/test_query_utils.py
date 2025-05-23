import unittest

from semantic_search.utils.query_utils import (
    chunk_text,
    classify_query,
    extract_temporal_markers,
    build_metadata_filters,
)


class TestQueryUtils(unittest.TestCase):
    def test_chunk_text_markdown(self):
        text = "# Title\n\nParagraph one.\n\nParagraph two."
        chunks = chunk_text(text, '.md')
        # Expect three chunks: one for the title and two for paragraphs.
        self.assertEqual(len(chunks), 3)

    def test_classify_and_extract(self):
        query = 'summarize last 7 days'
        self.assertEqual(classify_query(query), 'temporal')
        temporal = extract_temporal_markers(query)
        self.assertIsNotNone(temporal['start'])
        filters = build_metadata_filters(query)
        self.assertIn('start_date', filters)
        self.assertIn('end_date', filters)


if __name__ == '__main__':
    unittest.main()
