import os
import shutil
import subprocess
import unittest
from pathlib import Path

from semantic_search.utils.fs_utils import (
    apply_gitignore,
    scan_directory,
    get_file_metadata,
    read_file_content,
)


class TestFSUtils(unittest.TestCase):
    def setUp(self):
        self.tmp = Path('tmp_fs_test')
        shutil.rmtree(self.tmp, ignore_errors=True)
        self.tmp.mkdir()
        (self.tmp / 'file.md').write_text('# hello')
        (self.tmp / 'file.txt').write_text('text')
        (self.tmp / 'ignore.log').write_text('ignored')
        # create git repo with .gitignore
        subprocess.run(['git', 'init'], cwd=self.tmp, stdout=subprocess.DEVNULL)
        (self.tmp / '.gitignore').write_text('*.log\n')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scan_directory_and_gitignore(self):
        files = scan_directory(str(self.tmp), ['.md', '.txt', '.log'])
        names = {f.name for f in files}
        self.assertIn('file.md', names)
        self.assertIn('file.txt', names)
        self.assertNotIn('ignore.log', names)

    def test_get_file_metadata_and_read(self):
        md_file = self.tmp / 'file.md'
        meta = get_file_metadata(str(md_file))
        self.assertEqual(meta['path'], str(md_file))
        self.assertIn('size', meta)
        content = read_file_content(str(md_file))
        self.assertTrue(content.startswith('# hello'))


if __name__ == '__main__':
    unittest.main()
