"""Tests for the generated repository site update archive."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from build_site_updates_archive import build_site_updates_archive


class SiteUpdatesArchiveTests(unittest.TestCase):
    def _root(self, directory: str) -> Path:
        root = Path(directory)
        (root / "src/content/books").mkdir(parents=True)
        (root / "src/content/announcements").mkdir(parents=True)
        (root / "src/data").mkdir(parents=True)
        (root / "src/content/books/F0-9.md").write_text(
            "---\n"
            "id: F0-9\n"
            "title: 测试书\n"
            "subtitle: （上册）\n"
            "editions:\n"
            "  - edition: 1\n"
            "    editionDate: 2026-07\n"
            "  - edition: 2\n"
            "    editionDate: 2026-08\n"
            "---\n",
            encoding="utf-8",
        )
        (root / "src/data/generated-updates.json").write_text(
            json.dumps(
                [
                    {
                        "id": "F0-9-listed",
                        "type": "book-added",
                        "publishedAt": "2026-07-01T16:00:00Z",
                        "bookId": "F0-9",
                    },
                    {
                        "id": "F0-9-v2",
                        "type": "book-updated",
                        "publishedAt": "2026-08-02T16:00:00Z",
                        "bookId": "F0-9",
                        "edition": 2,
                    },
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (root / "src/content/announcements/2026-08-04-maintenance.md").write_text(
            "---\n"
            "title: 维护完成\n"
            "label: 维护\n"
            "publishedAt: 2026-08-04T09:00:00+08:00\n"
            "kind: site-announcement\n"
            "summary:\n"
            "  - 恢复正常访问\n"
            "---\n",
            encoding="utf-8",
        )
        return root

    def test_builds_all_events_newest_first_without_build_time_noise(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            output = build_site_updates_archive(root)
            markdown = output.read_text(encoding="utf-8")

            self.assertTrue(markdown.startswith("# 本站更新归档\n"))
            self.assertLess(markdown.index("维护完成"), markdown.index("版本更新"))
            self.assertLess(markdown.index("版本更新"), markdown.index("新书上架"))
            self.assertIn("F0-9　《测试书（上册）》", markdown)
            self.assertIn("2026 年 8 月第 2 版", markdown)
            self.assertIn("<!-- update-id: book-version-F0-9-v2 -->", markdown)
            self.assertNotIn("generatedAt", markdown)
            build_site_updates_archive(root, check=True)

    def test_check_rejects_a_stale_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            output = build_site_updates_archive(root)
            output.write_text("stale\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "out of date"):
                build_site_updates_archive(root, check=True)


if __name__ == "__main__":
    unittest.main()
