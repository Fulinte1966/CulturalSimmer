"""Tests for normalized, page-addressable PDF content snapshots."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extract_content_snapshot import (
    UPDATE_PAGE_MARKER,
    _complex_block_indexes,
    _filter_structural_lines,
    extract_content_snapshot,
    normalize_extracted_text,
    tokenize_text,
)
from compare_content_snapshots import compare_content_snapshots
from render_release_changelog import render_release_changelog


CHANGE_TYPES = (
    "replace",
    "delete",
    "insert",
    "replace",
    "delete",
    "insert",
    "replace",
    "delete",
    "insert",
    "replace",
    "insert",
)


def _write_chapter_fixture(pdf_path: Path, *, revised: bool) -> None:
    import fitz

    document = fitz.open()
    cover = document.new_page(width=420, height=595)
    cover.insert_text((72, 120), "COVER")

    for chapter, change_type in enumerate(CHANGE_TYPES, start=1):
        page = document.new_page(width=420, height=595)
        page.insert_text((72, 25), "Repeated header")
        old_tokens = [
            f"chapter{chapter:02d}",
            f"before{chapter:02d}",
            f"context{chapter:02d}",
            f"stable{chapter:02d}",
            f"target{chapter:02d}",
            f"after{chapter:02d}",
            f"detail{chapter:02d}",
            f"ending{chapter:02d}",
        ]
        new_tokens = list(old_tokens)
        if change_type == "replace":
            new_tokens[4] = f"revised{chapter:02d}"
        elif change_type == "delete":
            del new_tokens[4]
        else:
            new_tokens.insert(5, f"added{chapter:02d}")
        tokens = new_tokens if revised else old_tokens
        page.insert_text((72, 120), " ".join(tokens[:4]))
        page.insert_text((72, 145), " ".join(tokens[4:]) + ".")
        page.insert_text((200, 575), str(chapter))

    colophon = document.new_page(width=420, height=595)
    font_path = (
        Path(__file__).resolve().parents[2]
        / "tools/font-sources/LXGWNeoZhiSongScreen.ttf"
    )
    colophon.insert_text(
        (72, 120),
        "排版\n排印\n内部书号 F-9",
        fontname="FixtureSong",
        fontfile=str(font_path),
    )
    colophon.insert_text(
        (72, 170),
        "2026年7月第" + ("2" if revised else "1") + "版",
        fontname="FixtureSong",
        fontfile=str(font_path),
    )
    document.set_page_labels(
        [
            {"startpage": 0, "prefix": "", "style": "r", "firstpagenum": 1},
            {"startpage": 1, "prefix": "", "style": "D", "firstpagenum": 1},
        ]
    )
    document.save(pdf_path)
    document.close()


class ContentSnapshotTests(unittest.TestCase):
    def test_tokenization_ignores_layout_whitespace_and_uses_nfc(self) -> None:
        first = tokenize_text("认真  做好\nGitHub 2026。cafe\u0301")
        second = tokenize_text("认真做好 GitHub   2026。café")
        self.assertEqual(first, second)
        self.assertEqual(first[-1], "é")

    def test_soft_hyphen_and_line_end_hyphen_are_removed(self) -> None:
        self.assertEqual(
            normalize_extracted_text("pub\u00adlish\npub-\nlish"),
            "publish\npublish",
        )

    def test_pdf_extraction_nulls_and_duplicate_semicolons_are_removed(self) -> None:
        self.assertEqual(normalize_extracted_text("公式\x00；；正文"), "公式；正文")

    def test_toc_page_numbers_are_removed_but_titles_remain(self) -> None:
        text = "第一章　绪论 …… 1\n第二章　生产 … 23\n附录 .... 108"
        self.assertEqual(
            _filter_structural_lines(text, toc=True, colophon=False),
            "第一章　绪论\n第二章　生产\n附录",
        )

    def test_colophon_release_fields_are_removed_conservatively(self) -> None:
        text = "电子书制作：CulturalSimmer\n2026年7月第2版\n正文说明"
        self.assertEqual(
            _filter_structural_lines(text, toc=False, colophon=True),
            "电子书制作：CulturalSimmer\n正文说明",
        )

    def test_repeated_margins_page_numbers_and_update_page_are_excluded(self) -> None:
        import fitz

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "fixture.pdf"
            document = fitz.open()
            width, height = 420, 595
            for page_index in range(5):
                page = document.new_page(width=width, height=height)
                if page_index == 0:
                    page.insert_text((72, 120), "COVER")
                    continue
                page.insert_text((72, 25), "Repeated header")
                page.insert_text((72, 120), f"Body section {page_index}")
                page.insert_text((72, height - 35), "Repeated footer")
                page.insert_text((200, height - 20), str(100 + page_index))
            update_page = document.new_page(width=width, height=height)
            update_page.insert_text((72, 120), UPDATE_PAGE_MARKER)
            update_page.insert_text((72, 150), "This text must not appear")
            document.save(pdf_path)
            document.close()

            snapshot = extract_content_snapshot(
                pdf_path,
                book_id="F-9",
                edition=1,
                edition_date="2026-07",
            )

            joined = "".join(snapshot["tokens"])
            self.assertNotIn("COVER", joined)
            self.assertNotIn("Repeatedheader", joined)
            self.assertNotIn("Repeatedfooter", joined)
            self.assertNotIn("Thistextmustnotappear", joined)
            self.assertNotIn("101", joined)
            self.assertIn("Bodysection1", joined)
            self.assertEqual(snapshot["exclusions"]["markerPages"], [6])
            self.assertIsNone(snapshot["pageRuns"][0]["label"])

    def test_pdf_without_comparable_text_fails_instead_of_reporting_no_changes(self) -> None:
        import fitz

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "empty.pdf"
            document = fitz.open()
            document.new_page(width=420, height=595)
            document.save(pdf_path)
            document.close()

            with self.assertRaisesRegex(ValueError, "no comparable text"):
                extract_content_snapshot(
                    pdf_path,
                    book_id="F-9",
                    edition=1,
                    edition_date="2026-07",
                    exclude_cover=False,
                )

    def test_complex_graphics_and_rotated_pages_are_skipped(self) -> None:
        import fitz

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "complex.pdf"
            document = fitz.open()
            page = document.new_page(width=420, height=595)
            page.insert_text((72, 40), "Ordinary body before diagram")
            page.draw_rect(fitz.Rect(60, 80, 360, 220))
            page.insert_text((100, 140), "Diagram labels must be skipped")
            page.insert_text((72, 280), "Ordinary body after diagram")

            rotated = document.new_page(width=420, height=595)
            rotated.insert_text((72, 120), "Rotated table must be skipped")
            rotated.set_rotation(90)
            document.save(pdf_path)
            document.close()

            snapshot = extract_content_snapshot(
                pdf_path,
                book_id="F-9",
                edition=1,
                edition_date="2026-07",
                exclude_cover=False,
            )

            joined = "".join(snapshot["tokens"])
            self.assertIn("Ordinarybodybeforediagram", joined)
            self.assertIn("Ordinarybodyafterdiagram", joined)
            self.assertNotIn("Diagramlabelsmustbeskipped", joined)
            self.assertNotIn("Rotatedtablemustbeskipped", joined)
            self.assertGreaterEqual(
                snapshot["exclusions"]["removedBlocks"]["complexRegions"], 2
            )

    def test_math_dominant_text_block_is_classified_as_complex(self) -> None:
        class FakePage:
            rotation = 0
            rect = type("Rect", (), {"width": 420.0, "height": 595.0})()

            @staticmethod
            def cluster_drawings():
                return []

        blocks = [
            {
                "bbox": (100.0, 100.0, 300.0, 130.0),
                "lines": [
                    {
                        "spans": [
                            {
                                "text": "G-W-G'",
                                "font": "TeXGyreTermesMath-Regular",
                            }
                        ]
                    }
                ],
            },
            {
                "bbox": (60.0, 200.0, 360.0, 230.0),
                "lines": [
                    {"spans": [{"text": "ordinary body", "font": "Song"}]}
                ],
            },
        ]

        self.assertEqual(_complex_block_indexes(FakePage(), blocks), {0})

    def test_full_pdf_comparison_reports_one_change_per_chapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            old_pdf = Path(temp_dir) / "old.pdf"
            new_pdf = Path(temp_dir) / "new.pdf"
            _write_chapter_fixture(old_pdf, revised=False)
            _write_chapter_fixture(new_pdf, revised=True)

            old_snapshot = extract_content_snapshot(
                old_pdf,
                book_id="F-9",
                edition=1,
                edition_date="2026-06",
            )
            new_snapshot = extract_content_snapshot(
                new_pdf,
                book_id="F-9",
                edition=2,
                edition_date="2026-07",
            )
            self.assertEqual(old_snapshot["pageRuns"][0]["page"], 2)
            self.assertEqual(old_snapshot["pageRuns"][0]["label"], "1")
            self.assertNotIn("内部书号", "".join(old_snapshot["tokens"]))
            changelog = compare_content_snapshots(old_snapshot, new_snapshot)

            self.assertEqual(
                changelog["summary"],
                {"total": 11, "added": 4, "removed": 3, "changed": 4},
            )
            self.assertEqual(
                [change["type"] for change in changelog["changes"]],
                list(CHANGE_TYPES),
            )
            self.assertEqual(
                [
                    (change.get("new") or change.get("old"))["pages"]
                    for change in changelog["changes"]
                ],
                [[page] for page in range(2, 13)],
            )
            self.assertEqual(
                [
                    (change.get("new") or change.get("old"))["pageLabels"]
                    for change in changelog["changes"]
                ],
                [[str(label)] for label in range(1, 12)],
            )
            markdown = render_release_changelog(changelog)
            self.assertIn("共有 **11** 处不同", markdown)
            self.assertIn("<kbd>+ 新增</kbd> **4** 处", markdown)
            self.assertIn("<kbd>− 删减</kbd> **3** 处", markdown)
            self.assertIn("<kbd>± 修改</kbd> **4** 处", markdown)


if __name__ == "__main__":
    unittest.main()
