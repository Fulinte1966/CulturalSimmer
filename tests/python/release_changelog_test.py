"""Tests for GitHub Release changelog Markdown rendering."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from render_release_changelog import escape_markdown_text, render_release_changelog
from sync_release_changelog import synchronize_changelog


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
            "pageLabels": ["ii", "iii"],
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
        self.assertTrue(markdown.startswith("### 2026 年 7 月第 2 版"))
        self.assertIn("较 `2026 年 6 月第 1 版` 共有 **3** 处不同", markdown)
        self.assertIn("`第 ii—iii 页` 认真 ***做*** 好出版工作。", markdown)
        self.assertIn("认真 ~~**删除**~~ 好出版工作。", markdown)
        self.assertIn("认真 **新增** 好出版工作。", markdown)
        self.assertNotIn("待复核", markdown)
        self.assertNotIn("<sub>?</sub>", markdown)

    def test_review_required_is_counted_and_marked_on_both_replace_sides(self) -> None:
        old_side = {
            "pages": [11],
            "pageLabels": ["1"],
            "prefix": "都是",
            "changedText": "十分",
            "suffix": "重要的。",
            "prefixTruncated": True,
            "suffixTruncated": False,
        }
        changelog = {
            "toEdition": {"edition": 2, "editionDate": "2026-08"},
            "fromEdition": {"edition": 1, "editionDate": "2026-07"},
            "summary": {"total": 1, "added": 0, "removed": 0, "changed": 1},
            "changes": [
                {
                    "type": "replace",
                    "needsReview": True,
                    "old": old_side,
                    "new": {**old_side, "changedText": "格外"},
                }
            ],
        }

        markdown = render_release_changelog(changelog)
        self.assertIn("> <sub>?</sub> 待复核 **1** 处", markdown)
        self.assertIn(
            "1. <sub>?</sub> <kbd>−</kbd> `第 1 页` … 都是 ***十分*** 重要的。<br>",
            markdown,
        )
        self.assertIn(
            "   <sub>?</sub> <kbd>+</kbd> `第 1 页` … 都是 ***格外*** 重要的。",
            markdown,
        )

    def test_changed_text_ending_in_punctuation_is_separated_from_context(self) -> None:
        changelog = {
            "toEdition": {"edition": 2, "editionDate": "2026-07"},
            "fromEdition": {"edition": 1, "editionDate": "2026-06"},
            "summary": {"total": 1, "added": 1, "removed": 0, "changed": 0},
            "changes": [
                {
                    "type": "insert",
                    "new": {
                        "pages": [43],
                        "pageLabels": ["33"],
                        "prefix": "",
                        "changedText": "新增测试一。",
                        "suffix": "作为资本主义经济细胞的商品",
                        "prefixTruncated": False,
                        "suffixTruncated": False,
                    },
                }
            ],
        }

        markdown = render_release_changelog(changelog)
        self.assertIn(
            "`第 33 页` **新增测试一。** 作为资本主义经济细胞的商品",
            markdown,
        )
        self.assertNotIn("**新增测试一。**作为", markdown)

    def test_source_markdown_characters_are_escaped(self) -> None:
        self.assertEqual(
            escape_markdown_text("* _ ~ ` < > \\"),
            "\\* \\_ \\~ \\` &lt; &gt; \\\\",
        )

    def test_physical_page_fallback_is_labeled_as_pdf_page(self) -> None:
        changelog = {
            "toEdition": {"edition": 2, "editionDate": "2026-07"},
            "fromEdition": {"edition": 1, "editionDate": "2026-06"},
            "summary": {"total": 1, "added": 1, "removed": 0, "changed": 0},
            "changes": [
                {
                    "type": "insert",
                    "new": {
                        "pages": [12, 13],
                        "pageLabels": [],
                        "prefix": "",
                        "changedText": "新增",
                        "suffix": "",
                    },
                }
            ],
        }

        markdown = render_release_changelog(changelog)
        self.assertIn("`PDF 第 12—13 页` **新增**", markdown)

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

    def test_manual_changes_recalculate_repository_and_release_statistics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            changelog_path = root / "src/data/changelogs/F0-9_v2.changelog.json"
            manifest_path = root / "src/data/manifests/F0-9_v2.json"
            notes_path = root / "release-notes.md"
            changelog_path.parent.mkdir(parents=True)
            manifest_path.parent.mkdir(parents=True)
            changelog_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "bookId": "F0-9",
                        "fromEdition": {"edition": 1, "editionDate": "2026-06"},
                        "toEdition": {"edition": 2, "editionDate": "2026-07"},
                        "summary": {
                            "total": 1,
                            "added": 1,
                            "removed": 0,
                            "changed": 0,
                        },
                        "changes": [
                            {
                                "index": 8,
                                "type": "insert",
                                "new": {
                                    "pages": [2],
                                    "pageLabels": ["i"],
                                    "prefix": "",
                                    "changedText": "人工新增",
                                    "suffix": "",
                                },
                            },
                            {
                                "index": 9,
                                "type": "delete",
                                "old": {
                                    "pages": [3],
                                    "pageLabels": ["1"],
                                    "prefix": "",
                                    "changedText": "人工删减",
                                    "suffix": "",
                                },
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "releaseTag": "F0-9_v2",
                        "changelogSummary": {
                            "total": 1,
                            "added": 1,
                            "removed": 0,
                            "changed": 0,
                        },
                    }
                ),
                encoding="utf-8",
            )

            synchronized = synchronize_changelog(
                "F0-9_v2", root=root, notes_output=notes_path
            )

            expected = {"total": 2, "added": 1, "removed": 1, "changed": 0}
            self.assertEqual(synchronized["summary"], expected)
            self.assertEqual(
                [change["index"] for change in synchronized["changes"]], [1, 2]
            )
            self.assertEqual(
                json.loads(changelog_path.read_text("utf-8"))["summary"], expected
            )
            self.assertEqual(
                json.loads(manifest_path.read_text("utf-8"))["changelogSummary"],
                expected,
            )
            self.assertIn("共有 **2** 处不同", notes_path.read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()
