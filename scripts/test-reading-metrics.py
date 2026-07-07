"""Unit tests for generated PDF reading metrics."""

import json
import tempfile
import unittest
from pathlib import Path

from book_assets import (
    count_text_units,
    extract_book_assets,
    normalize_pdf_text,
)


class ReadingMetricTests(unittest.TestCase):
    def test_counts_cjk_characters(self) -> None:
        self.assertEqual(count_text_units("啊" * 1000), (1000, 0))

    def test_counts_latin_words(self) -> None:
        self.assertEqual(
            count_text_units("one two HTML5 iPhone 2025"),
            (0, 5),
        )

    def test_counts_unspaced_mixed_text(self) -> None:
        text = "iPhone于2025年发布HTML5标准和A股数据"
        self.assertEqual(count_text_units(text), (10, 4))

    def test_recovers_legacy_gbk_pdf_text(self) -> None:
        self.assertEqual(
            normalize_pdf_text("ÕþÖÎ¾­¼ÃÑ§ »ù´¡ÖªÊ¶"),
            "政治经济学 基础知识",
        )

    def test_preserves_normal_mixed_text(self) -> None:
        text = "iPhone于2025年发布HTML5标准"
        self.assertEqual(normalize_pdf_text(text), text)

    def test_extracts_assets_from_temporary_pdf(self) -> None:
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF is not installed")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            pdf_path = root / "sample.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text(
                (72, 72),
                " ".join(["reading"] * 120),
            )
            document.set_toc([[1, "Opening", 1]])
            document.save(pdf_path)
            document.close()

            outputs = extract_book_assets(
                pdf_path,
                "A8-99",
                1,
                root,
            )
            self.assertTrue(outputs["cover"].exists())
            self.assertTrue(outputs["spine"].exists())
            self.assertTrue(outputs["outline"].exists())
            self.assertTrue(outputs["reading"].exists())

            reading = json.loads(outputs["reading"].read_text(encoding="utf-8"))
            self.assertEqual(reading["fileSizeBytes"], pdf_path.stat().st_size)

            cover = fitz.Pixmap(outputs["cover"])
            spine = fitz.Pixmap(outputs["spine"])
            self.assertEqual(spine.width, 1)
            self.assertEqual(spine.height, cover.height)


if __name__ == "__main__":
    unittest.main()
