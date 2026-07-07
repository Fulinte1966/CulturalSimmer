"""Side-effect-free tests for the PDF ingestion orchestrator."""

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import ingest_pdf
from edition_policy import check_expected_edition


class IngestPdfTests(unittest.TestCase):
    def test_loads_classification_mapping(self) -> None:
        labels = ingest_pdf._load_classifications()
        self.assertEqual(labels["F"], "经济")
        self.assertEqual(labels["F0"], "马克思主义政治经济学")

    def test_publish_normalizes_release_asset_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_pdf = root / "uploaded-name.pdf"
            source_pdf.write_bytes(b"fixture")
            metadata_path = root / "metadata.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "title": "标题",
                        "edition": 2,
                        "canonicalTag": "F0-9_v2",
                        "canonicalFilename": "F0-9_v2.pdf",
                        "sourcePdfPath": str(source_pdf),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            calls: list[tuple[str, ...]] = []

            with patch.object(
                ingest_pdf, "_gh", side_effect=lambda *args: calls.append(args) or ""
            ):
                ingest_pdf.cmd_publish(
                    ["--metadata", str(metadata_path), "--workspace", str(root)]
                )

            normalized = root / "F0-9_v2.pdf"
            self.assertEqual(normalized.read_bytes(), b"fixture")
            self.assertIn(normalized.resolve().as_posix(), calls[0])

    def test_failed_push_rolls_back_only_canonical_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_path = Path(temp_dir) / "metadata.json"
            metadata_path.write_text(
                json.dumps({"canonicalTag": "F0-9_v2"}), encoding="utf-8"
            )
            calls: list[tuple[str, ...]] = []

            with patch.object(
                ingest_pdf, "_gh", side_effect=lambda *args: calls.append(args) or ""
            ):
                ingest_pdf.cmd_cleanup(
                    [
                        "--metadata",
                        str(metadata_path),
                        "--release-tag",
                        "ingest-fixture",
                        "--push-success",
                        "false",
                    ]
                )

            self.assertEqual(calls[0][:3], ("release", "delete", "F0-9_v2"))
            self.assertTrue("--cleanup-tag" in calls[0])
            self.assertFalse(any("ingest-fixture" in call for call in calls))

    def test_generate_uses_safe_yaml_and_records_source_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            metadata_path = root / "metadata.json"
            metadata = {
                "id": "F0-9",
                "title": "标题: [测试] # 一",
                "subtitle": "副题",
                "author": "作者",
                "edition": 2,
                "editionDate": "2026-06",
                "editionDateSource": "xmp:CreateDate",
                "pdfCreateDate": "2026-06-18T21:32:10+08:00",
                "date": "2026-06-21",
                "tags": ["甲", "乙"],
                "description": "简介。",
                "language": "zh-CN",
                "sourceReleaseId": 10,
                "sourceAssetId": 20,
                "sourceSha256": "abc",
                "sourcePdfPath": str(root / "fixture.pdf"),
                "canonicalTag": "F0-9_v2",
                "canonicalFilename": "F0-9_v2.pdf",
            }
            (root / "fixture.pdf").write_bytes(b"fixture")
            metadata_path.write_text(
                json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
            )
            reading_path = root / "src/data/reading/F0-9_v2.json"

            def fake_extract_book_assets(*args, **kwargs):
                reading_path.parent.mkdir(parents=True, exist_ok=True)
                reading_path.write_text(
                    json.dumps(
                        {
                            "pageCount": 12,
                            "cjkCharacterCount": 100,
                            "latinTokenCount": 2,
                        }
                    ),
                    encoding="utf-8",
                )
                return {"reading": reading_path}

            fake_assets = types.SimpleNamespace(
                extract_book_assets=fake_extract_book_assets
            )

            with patch.object(ingest_pdf, "ROOT", root), patch.dict(
                sys.modules, {"book_assets": fake_assets}
            ):
                ingest_pdf.cmd_generate(
                    ["--metadata", str(metadata_path), "--workspace", str(root)]
                )

            markdown = (root / "src/content/books/F0-9.md").read_text("utf-8")
            frontmatter = yaml.safe_load(markdown.split("---", 2)[1])
            self.assertEqual(frontmatter["title"], metadata["title"])
            self.assertEqual(frontmatter["editions"][0]["edition"], 2)
            self.assertNotIn("edition", frontmatter)
            self.assertNotIn("date", frontmatter)
            manifest = json.loads(
                (root / "src/data/manifests/F0-9_v2.json").read_text("utf-8")
            )
            self.assertEqual(manifest["editionDate"], "2026-06")
            self.assertEqual(manifest["pageCount"], 12)
            self.assertEqual(manifest["wordCount"], 102)
            self.assertEqual(manifest["sourceAssetId"], 20)
            self.assertTrue(manifest["generatedAt"])

    def test_expected_edition_from_existing_editions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            books_dir = root / "src/content/books"
            books_dir.mkdir(parents=True)
            (books_dir / "F0-9.md").write_text(
                "---\nid: F0-9\neditions:\n  - edition: 1\n    editionDate: \"2026-06\"\n---\n",
                encoding="utf-8",
            )

            check = check_expected_edition(root, "F0-9", 2)
            self.assertTrue(check.ok)
            self.assertEqual(check.expected_edition, 2)

    def test_repeated_edition_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            books_dir = root / "src/content/books"
            books_dir.mkdir(parents=True)
            (books_dir / "F0-9.md").write_text(
                "---\nid: F0-9\neditions:\n  - edition: 1\n    editionDate: \"2026-06\"\n---\n",
                encoding="utf-8",
            )

            check = check_expected_edition(root, "F0-9", 1)
            self.assertFalse(check.ok)
            self.assertIn("已存在", check.message)


if __name__ == "__main__":
    unittest.main()
