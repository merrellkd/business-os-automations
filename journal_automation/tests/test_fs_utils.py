import os
from pathlib import Path
import shutil
import unittest

from journal_automation.utils.fs_utils import ensure_dir, move_folder, create_file

class TestFSUtils(unittest.TestCase):
    def setUp(self):
        self.tmp_root = Path('tmp_test_dir')
        shutil.rmtree(self.tmp_root, ignore_errors=True)
        ensure_dir(self.tmp_root)

    def tearDown(self):
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_ensure_dir(self):
        p = self.tmp_root / 'a' / 'b'
        ensure_dir(p)
        self.assertTrue(p.exists())

    def test_move_folder(self):
        src = self.tmp_root / 'src'
        dst = self.tmp_root / 'dst' / 'moved'
        ensure_dir(src)
        move_folder(src, dst)
        self.assertFalse(src.exists())
        self.assertTrue(dst.exists())

    def test_create_file(self):
        f = self.tmp_root / 'file.txt'
        create_file(f, 'hello')
        self.assertTrue(f.exists())
        with open(f) as fh:
            self.assertEqual(fh.read(), 'hello')

if __name__ == '__main__':
    unittest.main()
