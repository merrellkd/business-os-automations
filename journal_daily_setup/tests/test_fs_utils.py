import os
from pathlib import Path
import shutil
import unittest
import subprocess

from journal_daily_setup.utils.fs_utils import (
    ensure_dir,
    move_folder,
    create_file,
    github_pr_link,
)

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

    def test_github_pr_link(self):
        """Verify we can construct a PR link from a Git remote."""
        repo_root = self.tmp_root

        # Initialize a minimal git repository with an origin remote so that
        # ``git remote get-url origin`` succeeds.
        subprocess.run(['git', 'init'], cwd=repo_root, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(
            ['git', 'remote', 'add', 'origin', 'https://github.com/foo/bar.git'],
            cwd=repo_root,
            check=True,
            stdout=subprocess.DEVNULL,
        )

        link = github_pr_link(repo_root, 'feature')
        self.assertEqual(
            link,
            'https://github.com/foo/bar/pull/new/feature',
        )

if __name__ == '__main__':
    unittest.main()
