"""Tests for adjacent-edition content comparison and page mapping."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from compare_content_snapshots import DiffLimitError, compare_content_snapshots
from extract_content_snapshot import NORMALIZATION_PROFILE, tokenize_text


def snapshot(text: str, edition: int, page: int = 1) -> dict:
    tokens = tokenize_text(text)
    return {
        "schemaVersion": 1,
        "normalizationProfile": NORMALIZATION_PROFILE,
        "bookId": "F0-9",
        "edition": edition,
        "editionDate": f"2026-0{edition}",
        "pageCount": page,
        "tokens": tokens,
        "pageRuns": [
            {"start": 0, "end": len(tokens), "page": page, "label": str(page)}
        ],
    }


class ContentDiffTests(unittest.TestCase):
    def test_repagination_without_content_change_has_no_diff(self) -> None:
        old = snapshot("认真作好出版工作。", 1, page=1)
        new = snapshot("认真作好出版工作。", 2, page=2)
        changelog = compare_content_snapshots(old, new)
        self.assertEqual(changelog["summary"]["total"], 0)

    def test_one_character_replacement_maps_old_and_new_pages(self) -> None:
        old = snapshot("认真做好出版工作。", 1, page=1)
        new = snapshot("认真作好出版工作。", 2, page=2)
        change = compare_content_snapshots(old, new)["changes"][0]
        self.assertEqual(change["type"], "replace")
        self.assertEqual(change["old"]["changedText"], "做")
        self.assertEqual(change["new"]["changedText"], "作")
        self.assertEqual(change["old"]["pages"], [1])
        self.assertEqual(change["new"]["pages"], [2])
        self.assertEqual(change["old"]["pageLabels"], ["1"])
        self.assertEqual(change["new"]["pageLabels"], ["2"])

    def test_insertion_deletion_punctuation_and_number_changes(self) -> None:
        insertion = compare_content_snapshots(
            snapshot("认真作好出版工作。", 1),
            snapshot("我们要认真作好出版工作。", 2),
        )
        self.assertEqual(insertion["summary"]["added"], 1)
        self.assertEqual(insertion["changes"][0]["new"]["changedText"], "我们要")

        deletion = compare_content_snapshots(
            snapshot("我们要认真作好出版工作。", 1),
            snapshot("认真作好出版工作。", 2),
        )
        self.assertEqual(deletion["summary"]["removed"], 1)

        punctuation = compare_content_snapshots(
            snapshot("版本2025。", 1), snapshot("版本2026！", 2)
        )
        self.assertGreater(punctuation["summary"]["total"], 0)

    def test_cross_page_range_is_preserved(self) -> None:
        old = snapshot("甲乙丙丁", 1)
        new = snapshot("甲新增乙丙丁", 2)
        new["pageRuns"] = [
            {"start": 0, "end": 2, "page": 12, "label": "ii"},
            {
                "start": 2,
                "end": len(new["tokens"]),
                "page": 13,
                "label": "iii",
            },
        ]
        change = compare_content_snapshots(old, new)["changes"][0]
        self.assertEqual(change["new"]["pages"], [12, 13])
        self.assertEqual(change["new"]["pageLabels"], ["ii", "iii"])

    def test_size_limit_fails_clearly(self) -> None:
        old = snapshot("甲乙丙", 1)
        new = snapshot("甲乙丁", 2)
        with self.assertRaises(DiffLimitError):
            compare_content_snapshots(old, new, max_tokens=2)

    def test_large_sequence_with_one_change_completes_within_limit(self) -> None:
        old_tokens = [f"token{index}" for index in range(25_000)]
        new_tokens = list(old_tokens)
        new_tokens[12_500] = "replacement"
        old = snapshot("甲", 1)
        new = snapshot("乙", 2)
        old["tokens"] = old_tokens
        new["tokens"] = new_tokens
        old["pageRuns"] = [
            {"start": 0, "end": len(old_tokens), "page": 1, "label": "i"}
        ]
        new["pageRuns"] = [
            {"start": 0, "end": len(new_tokens), "page": 2, "label": "1"}
        ]

        changelog = compare_content_snapshots(old, new, timeout_seconds=5)
        self.assertEqual(changelog["summary"]["changed"], 1)

    def test_identical_text_relocated_to_adjacent_page_is_not_a_content_change(self) -> None:
        old = snapshot("正文甲需要换页的相同内容。脚注正文乙", 1, page=10)
        new = snapshot("正文甲脚注。需要换页的相同内容正文乙", 2, page=10)
        old["pageRuns"] = [
            {"start": 0, "end": len(old["tokens"]), "page": 10, "label": "1"}
        ]
        new["pageRuns"] = [
            {"start": 0, "end": 5, "page": 10, "label": "1"},
            {
                "start": 5,
                "end": len(new["tokens"]),
                "page": 11,
                "label": "2",
            },
        ]

        changelog = compare_content_snapshots(old, new)
        self.assertEqual(changelog["summary"]["total"], 0)

    def test_long_change_is_truncated_to_release_display_limit(self) -> None:
        old = snapshot("甲。", 1)
        new = snapshot(f"甲{'新' * 300}。", 2)
        side = compare_content_snapshots(old, new)["changes"][0]["new"]
        self.assertTrue(side["changedTextTruncated"])
        self.assertEqual(len(side["changedText"]), 160)
        self.assertEqual(side["changedTokenCount"], 300)


if __name__ == "__main__":
    unittest.main()
