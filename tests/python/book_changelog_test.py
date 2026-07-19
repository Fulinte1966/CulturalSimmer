"""Tests for aggregate per-book GitHub changelog generation."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from build_book_changelogs import build_repository_changelogs


class BookChangelogTests(unittest.TestCase):
    def test_builds_all_editions_newest_first_with_dynamic_statistics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            books_dir = root / "src/content/books"
            changelog_dir = root / "src/data/changelogs"
            books_dir.mkdir(parents=True)
            changelog_dir.mkdir(parents=True)
            (books_dir / "F-9.md").write_text(
                "---\n"
                "id: F-9\n"
                "title: 测试书\n"
                "editions:\n"
                "  - edition: 1\n"
                "    editionDate: 2026-06\n"
                "    releaseTag: F-9_v1\n"
                "  - edition: 2\n"
                "    editionDate: 2026-07\n"
                "    releaseTag: F-9_v2\n"
                "---\n",
                encoding="utf-8",
            )
            (changelog_dir / "F-9_v2.changelog.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "bookId": "F-9",
                        "fromEdition": {"edition": 1, "editionDate": "2026-06"},
                        "toEdition": {"edition": 2, "editionDate": "2026-07"},
                        "summary": {
                            "total": 99,
                            "added": 99,
                            "removed": 0,
                            "changed": 0,
                        },
                        "changes": [
                            {
                                "type": "insert",
                                "new": {
                                    "pages": [2],
                                    "pageLabels": ["1"],
                                    "prefix": "",
                                    "changedText": "新增内容",
                                    "suffix": "",
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            paths = build_repository_changelogs(root)
            markdown = paths[0].read_text(encoding="utf-8")

            self.assertLess(markdown.index("F-9_v2"), markdown.index("F-9_v1"))
            self.assertIn("共有 **1** 处不同", markdown)
            self.assertIn("初版发行", markdown)
            self.assertFalse(markdown.startswith("# 《测试书》版本更新日志"))
            self.assertNotIn("\n---\n\n---\n", markdown)
            self.assertEqual(markdown.count("\n---\n"), 2)
            build_repository_changelogs(root, check=True)

    def test_missing_noninitial_changelog_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            books_dir = root / "src/content/books"
            books_dir.mkdir(parents=True)
            (books_dir / "F-9.md").write_text(
                "---\nid: F-9\ntitle: 测试书\n"
                "editions:\n  - edition: 2\n    editionDate: 2026-07\n---\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Missing repository changelog"):
                build_repository_changelogs(root)


if __name__ == "__main__":
    unittest.main()
