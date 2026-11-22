"""Synthetic-data tests for the offline guard. No real exclusions are used."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "scripts"))
import private_guard as guard


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.policy = self.root / "local-only.json"
        self.policy.write_text(json.dumps({
            "ids": ["demo-company"], "tickers": ["7381"], "names": ["架空デモ株式会社"]
        }), encoding="utf-8")
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        self.write("_articles/demo.md", "# Safe sample\n")
        self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.DEVNULL).decode().strip()

    def write(self, path, text):
        dest = self.repo / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "test")
        return self.git("rev-parse", "HEAD")

    def check(self, sha=None, policy=None):
        try:
            guard.scan(self.repo, sha or self.git("rev-parse", "HEAD"),
                       guard.load_policy(policy or self.policy))
            return True
        except guard.Denied:
            return False

    def test_safe_data_passes(self):
        self.assertTrue(self.check())

    def test_missing_empty_and_bad_policy_fail(self):
        for data in (None, "", "{}", '{"ids": []}', "not json"):
            p = self.root / "bad.json"
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_text(data)
            with self.assertRaises(guard.Denied):
                guard.load_policy(p)

    def test_company_id_and_ticker(self):
        for text in ('{"company_id":"demo-company"}',
                     '{"ticker":"7381"}',
                     '{"company_id":"ｄｅｍｏ－ｃｏｍｐａｎｙ"}'):
            self.write("_data/sample.json", text)
            self.commit()
            self.assertFalse(self.check())

    def test_name_and_encoded_path(self):
        self.write("_articles/demo.md", "# 架空デモ株式会社\n")
        self.commit()
        self.assertFalse(self.check())
        self.write("_articles/demo.md", "# Safe\n")
        self.write("_articles/%25E6%259E%25B6%25E7%25A9%25BA%25E3%2583%2587%25E3%2583%25A2%25E6%25A0%25AA%25E5%25BC%258F%25E4%25BC%259A%25E7%25A4%25BE.md", "Safe")
        self.commit()
        self.assertFalse(self.check())

    def test_markdown_id_and_filename(self):
        self.write("_articles/demo.md", "---\\ncompany_id: demo-company\\n---\\n")
        self.commit()
        self.assertFalse(self.check())
        self.write("_articles/demo.md", "# Safe")
        self.write("_articles/7381.md", "# Safe")
        self.commit()
        self.assertFalse(self.check())

    def test_timestamp_not_ticker(self):
        self.write("_articles/demo.md", "2026-11-22T07:38:10.7381Z\n")
        self.commit()
        self.assertTrue(self.check())

    def test_ticker_with_context(self):
        self.write("_articles/demo.md", "証券コード 7381\n")
        self.commit()
        self.assertFalse(self.check())

    def test_old_commit_is_distinct(self):
        good_sha = self.git("rev-parse", "HEAD")
        self.write("_articles/demo.md", "# 架空デモ株式会社")
        bad_sha = self.commit()
        self.assertTrue(self.check(good_sha))
        self.assertFalse(self.check(bad_sha))

    def test_symlink_rejected(self):
        try:
            os.symlink("demo.md", self.repo / "_articles" / "linked.md")
        except (OSError, NotImplementedError):
            self.skipTest("symlink not supported")
        self.commit()
        self.assertFalse(self.check())

    def test_oversized_file_fails(self):
        self.write("_articles/demo.md", "x" * (guard.MAX_FILE_BYTES + 1))
        self.commit()
        self.assertFalse(self.check())

    def test_invalid_sha_rejected(self):
        self.assertFalse(self.check("main; echo unexpected"))


if __name__ == "__main__":
    unittest.main()
