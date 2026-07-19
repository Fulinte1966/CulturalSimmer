"""Side-effect-free tests for the PDF ingestion orchestrator."""

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import ingest_pdf
from site_updates_data import append_generated_update
from edition_policy import check_expected_edition, find_previous_edition_record
from extract_content_snapshot import NORMALIZATION_PROFILE, write_snapshot


class IngestPdfTests(unittest.TestCase):
    def test_loads_classification_mapping(self) -> None:
        labels = ingest_pdf._load_classifications()
        self.assertEqual(labels["F"], "经济")
        self.assertEqual(labels["A1"], "马克思、恩格斯著作")
        self.assertEqual(labels["A9"], "张春桥、姚文元著作")
        self.assertEqual(labels["I"], "文学")
        self.assertNotIn("F0", labels)
        self.assertNotIn("A93", labels)

    def test_publish_normalizes_release_asset_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_pdf = root / "uploaded-name.pdf"
            source_pdf.write_bytes(b"fixture")
            metadata_path = root / "metadata.json"
            snapshot_path = root / "F-9_v2.content.json.gz"
            changelog_path = root / "F-9_v2.changelog.json"
            notes_path = root / "F-9_v2.release-notes.md"
            snapshot_path.write_bytes(b"snapshot")
            changelog_path.write_text("{}\n", encoding="utf-8")
            notes_path.write_text("notes\n", encoding="utf-8")
            metadata_path.write_text(
                json.dumps(
                    {
                        "id": "F-9",
                        "title": "标题",
                        "edition": 2,
                        "previousEdition": 1,
                        "canonicalTag": "F-9_v2",
                        "canonicalFilename": "F-9_v2.pdf",
                        "sourcePdfPath": str(source_pdf),
                        "contentSnapshotPath": str(snapshot_path),
                        "changelogPath": str(changelog_path),
                        "releaseNotesPath": str(notes_path),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            calls: list[tuple[str, ...]] = []

            manifest_path = root / "src/data/manifests/F-9_v2.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps({"githubAssetDigest": None}), encoding="utf-8"
            )
            book_path = root / "src/content/books/F-9.md"
            book_path.parent.mkdir(parents=True)
            book_path.write_text(
                "---\n"
                "id: F-9\n"
                "title: 标题\n"
                "editions:\n"
                "  - edition: 1\n"
                "    editionDate: 2026-06\n"
                "  - edition: 2\n"
                "    editionDate: 2026-07\n"
                "---\n",
                encoding="utf-8",
            )

            def fake_gh(*args):
                calls.append(args)
                if args[:2] == ("api", "repos/:owner/:repo/releases/tags/F-9_v2"):
                    return json.dumps(
                        {
                            "assets": [
                                {
                                    "name": "F-9_v2.pdf",
                                    "digest": "sha256:fixture",
                                }
                            ],
                            "published_at": "2026-07-11T12:00:00Z",
                        }
                    )
                return ""

            with patch.object(ingest_pdf, "ROOT", root), patch.object(
                ingest_pdf, "_gh", side_effect=fake_gh
            ):
                ingest_pdf.cmd_publish(
                    ["--metadata", str(metadata_path), "--workspace", str(root)]
                )

            normalized = root / "F-9_v2.pdf"
            self.assertEqual(normalized.read_bytes(), b"fixture")
            self.assertIn(normalized.resolve().as_posix(), calls[0])
            self.assertIn(snapshot_path.resolve().as_posix(), calls[0])
            self.assertIn(changelog_path.resolve().as_posix(), calls[0])
            self.assertIn("--notes-file", calls[0])
            self.assertEqual(calls[-1][:3], ("release", "upload", "F-9_v2"))
            manifest = json.loads(manifest_path.read_text("utf-8"))
            self.assertEqual(manifest["githubAssetDigest"], "sha256:fixture")
            generated = json.loads(
                (root / "src/data/generated-updates.json").read_text("utf-8")
            )
            self.assertEqual(
                generated,
                [
                    {
                        "id": "F-9-v2",
                        "type": "book-updated",
                        "publishedAt": "2026-07-11T12:00:00Z",
                        "bookId": "F-9",
                        "edition": 2,
                    }
                ],
            )
            archive = (root / "docs/site-updates-archive.md").read_text("utf-8")
            self.assertIn("`更新` F-9_v2", archive)
            self.assertIn("《标题》已更新第 2 版。", archive)
            self.assertIn("<!-- update-id: book-version-F-9-v2 -->", archive)

    def test_generated_site_update_append_is_atomic_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "generated-updates.json"
            update = {
                "id": "F-9-listed",
                "type": "book-added",
                "publishedAt": "2026-07-11T12:00:00Z",
                "bookId": "F-9",
            }
            self.assertTrue(append_generated_update(path, update))
            self.assertFalse(append_generated_update(path, update))
            self.assertEqual(len(json.loads(path.read_text("utf-8"))), 1)
            with self.assertRaisesRegex(ValueError, "Conflicting"):
                append_generated_update(
                    path, {**update, "publishedAt": "2026-07-12T12:00:00Z"}
                )

    def test_failed_push_rolls_back_only_canonical_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_path = Path(temp_dir) / "metadata.json"
            metadata_path.write_text(
                json.dumps({"canonicalTag": "F-9_v2"}), encoding="utf-8"
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

            self.assertEqual(calls[0][:3], ("release", "delete", "F-9_v2"))
            self.assertTrue("--cleanup-tag" in calls[0])
            self.assertFalse(any("ingest-fixture" in call for call in calls))

    def test_generate_uses_safe_yaml_and_records_source_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            metadata_path = root / "metadata.json"
            changelog_path = root / "workspace/F-9_v2.changelog.json"
            changelog_path.parent.mkdir(parents=True)
            changelog_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "bookId": "F-9",
                        "fromEdition": None,
                        "toEdition": {"edition": 2, "editionDate": "2026-06"},
                        "summary": {
                            "total": 99,
                            "added": 99,
                            "removed": 0,
                            "changed": 0,
                        },
                        "changes": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            metadata = {
                "id": "F-9",
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
                "zlibraryUrl": "https://z-library.sk/book/fixture",
                "sourceReleaseId": 10,
                "sourceAssetId": 20,
                "sourceSha256": "abc",
                "sourcePdfPath": str(root / "fixture.pdf"),
                "canonicalTag": "F-9_v2",
                "canonicalFilename": "F-9_v2.pdf",
                "changelogPath": str(changelog_path),
            }
            (root / "fixture.pdf").write_bytes(b"fixture")
            book_path = root / "src/content/books/F-9.md"
            book_path.parent.mkdir(parents=True)
            book_path.write_text(
                "---\n"
                "id: F-9\n"
                'title: "标题: [测试] # 一"\n'
                "description: 简介。\n"
                "notifyUpdates: false\n"
                "editions:\n"
                "  - edition: 1\n"
                "    editionDate: 2026-05\n"
                "---\n\n简介。\n",
                encoding="utf-8",
            )
            metadata_path.write_text(
                json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
            )
            reading_path = root / "src/data/reading/F-9_v2.json"

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

            markdown = (root / "src/content/books/F-9.md").read_text("utf-8")
            frontmatter = yaml.safe_load(markdown.split("---", 2)[1])
            self.assertEqual(frontmatter["title"], metadata["title"])
            self.assertEqual(frontmatter["zlibraryUrl"], metadata["zlibraryUrl"])
            self.assertFalse(frontmatter["notifyUpdates"])
            self.assertEqual(frontmatter["editions"][-1]["edition"], 2)
            self.assertIn("  - edition: 2", markdown)
            self.assertNotIn("edition", frontmatter)
            self.assertNotIn("date", frontmatter)
            manifest = json.loads(
                (root / "src/data/manifests/F-9_v2.json").read_text("utf-8")
            )
            self.assertEqual(manifest["editionDate"], "2026-06")
            self.assertEqual(manifest["schemaVersion"], 4)
            self.assertEqual(manifest["pageCount"], 12)
            self.assertEqual(manifest["wordCount"], 102)
            self.assertEqual(manifest["sourceAssetId"], 20)
            self.assertEqual(
                manifest["metadata"]["zlibraryUrl"], metadata["zlibraryUrl"]
            )
            self.assertEqual(
                manifest["changelogPath"],
                "src/data/changelogs/F-9_v2.changelog.json",
            )
            repository_changelog = json.loads(
                (root / manifest["changelogPath"]).read_text("utf-8")
            )
            self.assertEqual(
                repository_changelog["summary"],
                {"total": 0, "added": 0, "removed": 0, "changed": 0},
            )
            self.assertTrue(manifest["generatedAt"])

    def test_expected_edition_from_existing_editions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            books_dir = root / "src/content/books"
            books_dir.mkdir(parents=True)
            (books_dir / "F-9.md").write_text(
                "---\nid: F-9\neditions:\n  - edition: 1\n    editionDate: \"2026-06\"\n---\n",
                encoding="utf-8",
            )

            check = check_expected_edition(root, "F-9", 2)
            self.assertTrue(check.ok)
            self.assertEqual(check.expected_edition, 2)

    def test_previous_edition_uses_highest_lower_record_not_minus_one(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            books_dir = root / "src/content/books"
            books_dir.mkdir(parents=True)
            (books_dir / "F-9.md").write_text(
                "---\nid: F-9\neditions:\n"
                "  - edition: 1\n    editionDate: '2026-01'\n    releaseTag: F-9_v1\n"
                "  - edition: 3\n    editionDate: '2026-03'\n    releaseTag: F-9_v3\n"
                "---\n",
                encoding="utf-8",
            )

            previous = find_previous_edition_record(root, "F-9", 5)
            self.assertIsNotNone(previous)
            self.assertEqual(previous["edition"], 3)

    def test_changelog_reuses_compatible_previous_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            books_dir = root / "src/content/books"
            books_dir.mkdir(parents=True)
            (books_dir / "F-9.md").write_text(
                "---\nid: F-9\neditions:\n"
                "  - edition: 1\n    editionDate: '2026-06'\n    releaseTag: F-9_v1\n"
                "---\n",
                encoding="utf-8",
            )
            current_pdf = workspace / "current.pdf"
            current_pdf.write_bytes(b"fixture")
            metadata_path = root / "metadata.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "id": "F-9",
                        "edition": 2,
                        "editionDate": "2026-07",
                        "canonicalTag": "F-9_v2",
                        "sourcePdfPath": str(current_pdf),
                    }
                ),
                encoding="utf-8",
            )

            def make_snapshot(text: str, edition: int, date: str) -> dict:
                tokens = list(text)
                return {
                    "schemaVersion": 1,
                    "normalizationProfile": NORMALIZATION_PROFILE,
                    "bookId": "F-9",
                    "edition": edition,
                    "editionDate": date,
                    "pageCount": 1,
                    "tokens": tokens,
                    "pageRuns": [
                        {
                            "start": 0,
                            "end": len(tokens),
                            "page": 1,
                            "label": "i",
                        }
                    ],
                }

            previous_snapshot_path = workspace / "F-9_v1.content.json.gz"
            write_snapshot(
                previous_snapshot_path,
                make_snapshot("甲乙", 1, "2026-06"),
            )

            with patch.object(ingest_pdf, "ROOT", root), patch.object(
                ingest_pdf,
                "extract_content_snapshot",
                return_value=make_snapshot("甲丙", 2, "2026-07"),
            ), patch.object(
                ingest_pdf,
                "_download_release_asset",
                return_value=previous_snapshot_path,
            ):
                ingest_pdf.cmd_changelog(
                    [
                        "--metadata",
                        str(metadata_path),
                        "--workspace",
                        str(workspace),
                    ]
                )

            metadata = json.loads(metadata_path.read_text("utf-8"))
            self.assertEqual(metadata["previousEdition"], 1)
            self.assertEqual(metadata["changelogSummary"]["changed"], 1)
            self.assertTrue(Path(metadata["contentSnapshotPath"]).exists())
            self.assertTrue(Path(metadata["releaseNotesPath"]).exists())

    def test_repeated_edition_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            books_dir = root / "src/content/books"
            books_dir.mkdir(parents=True)
            (books_dir / "F-9.md").write_text(
                "---\nid: F-9\neditions:\n  - edition: 1\n    editionDate: \"2026-06\"\n---\n",
                encoding="utf-8",
            )

            check = check_expected_edition(root, "F-9", 1)
            self.assertFalse(check.ok)
            self.assertIn("已存在", check.message)


if __name__ == "__main__":
    unittest.main()
