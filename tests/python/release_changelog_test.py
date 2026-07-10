"""Tests for GitHub Release changelog Markdown rendering."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from render_release_changelog import escape_markdown_text, render_release_changelog


class ReleaseChangelogTests(unittest.TestCase):
    def test_first_edition_uses_fixed_template(self) -> None:
        changelog = {
            "toEdition": {"edition": 1, "editionDate": "2026-06"},
            "fromEdition": None,
            "summary": {"total": 0, "added": 0, "removed": 0, "changed": 0},
            "changes": [],
        }
        self.assertEqual(
            render_release_changelog(changelog),
            "### 2026 年 6 月第 1 版\n\n---\n\n初次发布。\n",
        )

    def test_replace_insert_delete_and_page_ranges_follow_template(self) -> None:
        side = {
            "pages": [12, 13],
            "prefix": "认真",
            "changedText": "做",
            "suffix": "好出版工作。",
            "prefixTruncated": False,
            "suffixTruncated": False,
        }
        changelog = {
            "toEdition": {"edition": 2, "editionDate": "2026-07"},
            "fromEdition": {"edition": 1, "editionDate": "2026-06"},
            "summary": {"total": 3, "added": 1, "removed": 1, "changed": 1},
            "changes": [
                {"type": "replace", "old": side, "new": {**side, "changedText": "作"}},
                {"type": "delete", "old": {**side, "changedText": "删除"}},
                {"type": "insert", "new": {**side, "changedText": "新增"}},
            ],
        }
        markdown = render_release_changelog(changelog)
        self.assertIn("较 `2026 年 6 月第 1 版` 共有 **3** 处不同", markdown)
        self.assertIn("`第 12—13 页` 认真***做***好出版工作。", markdown)
        self.assertIn("~~**删除**~~", markdown)
        self.assertIn("**新增**", markdown)

    def test_source_markdown_characters_are_escaped(self) -> None:
        self.assertEqual(
            escape_markdown_text("* _ ~ ` < > \\"),
            "\\* \\_ \\~ \\` &lt; &gt; \\\\",
        )

    def test_max_changes_limits_body_not_summary(self) -> None:
        side = {
            "pages": [1],
            "prefix": "",
            "changedText": "新增",
            "suffix": "",
        }
        changelog = {
            "toEdition": {"edition": 2, "editionDate": "2026-07"},
            "fromEdition": {"edition": 1, "editionDate": "2026-06"},
            "summary": {"total": 2, "added": 2, "removed": 0, "changed": 0},
            "changes": [
                {"type": "insert", "new": side},
                {"type": "insert", "new": side},
            ],
        }
        markdown = render_release_changelog(changelog, max_changes=1)
        self.assertIn("共有 **2** 处不同", markdown)
        self.assertIn("仅列出前 **1** 处差异", markdown)
        self.assertNotIn("\n2. ", markdown)


if __name__ == "__main__":
    unittest.main()
