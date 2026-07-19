"""Tests for the website publication safety boundary."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from publication_policy import assert_publishable, load_blocked_books


class PublicationPolicyTests(unittest.TestCase):
    def _write_policy(self, root: Path, body: str) -> None:
        path = root / "config/publication-policy.yml"
        path.parent.mkdir(parents=True)
        path.write_text(body, encoding="utf-8")

    def test_repository_policy_blocks_local_only_book(self) -> None:
        root = Path(__file__).resolve().parents[2]
        self.assertEqual(load_blocked_books(root), {"B-1": "仅供本地校对，不上架"})
        with self.assertRaisesRegex(SystemExit, "blocks B-1"):
            assert_publishable(root, "B-1")
        assert_publishable(root, "A9-1")
        assert_publishable(root, "F-1-1")

    def test_rejects_duplicate_policy_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_policy(
                root,
                "schemaVersion: 1\n"
                "blockedBooks:\n"
                "  - id: B-1\n"
                "    reason: local\n"
                "  - id: B-1\n"
                "    reason: duplicate\n",
            )
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load_blocked_books(root)


if __name__ == "__main__":
    unittest.main()
