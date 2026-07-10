"""Tests for normalized, page-addressable PDF content snapshots."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extract_content_snapshot import (
    UPDATE_PAGE_MARKER,
    _filter_structural_lines,
    extract_content_snapshot,
    normalize_extracted_text,
    tokenize_text,
)


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
                book_id="F0-9",
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
                    book_id="F0-9",
                    edition=1,
                    edition_date="2026-07",
                    exclude_cover=False,
                )


if __name__ == "__main__":
    unittest.main()
