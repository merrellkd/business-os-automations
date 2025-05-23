import os
import unittest

from semantic_search.storage.faiss_manager import (
    init_index,
    add_vectors,
    search,
    save_index,
    load_index,
)


class TestFaissManager(unittest.TestCase):
    def setUp(self):
        self.index_path = 'tmp_index.pkl'
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        self.index = init_index(3)

    def tearDown(self):
        if os.path.exists(self.index_path):
            os.remove(self.index_path)

    def test_add_search_save_load(self):
        add_vectors(self.index, [[1, 0, 0], [0, 1, 0]], [1, 2])
        ids, scores = search(self.index, [1, 0, 0], k=1)
        self.assertEqual(ids[0], 1)

        save_index(self.index, self.index_path)
        loaded = load_index(self.index_path)
        ids_loaded, _ = search(loaded, [0, 1, 0], k=1)
        self.assertEqual(ids_loaded[0], 2)


if __name__ == '__main__':
    unittest.main()
