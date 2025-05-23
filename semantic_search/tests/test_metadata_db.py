import os
import unittest
from datetime import datetime, timedelta

from semantic_search.storage.metadata_db import (
    init_db,
    add_file_metadata,
    add_chunk_metadata,
    query_by_date_range,
    get_chunk_by_id,
)


class TestMetadataDB(unittest.TestCase):
    def setUp(self):
        self.db_path = 'tmp_test.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = init_db(self.db_path)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_and_query(self):
        file_id = add_file_metadata(self.conn, 'file.txt', 100, datetime.now().timestamp())
        chunk_id = add_chunk_metadata(self.conn, file_id, 0, 'hello world')

        start = datetime.now() - timedelta(days=1)
        end = datetime.now() + timedelta(days=1)
        files = query_by_date_range(self.conn, start, end)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['id'], file_id)

        text = get_chunk_by_id(self.conn, chunk_id)
        self.assertEqual(text, 'hello world')


if __name__ == '__main__':
    unittest.main()
