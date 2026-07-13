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
            "---\n"
            "系统维护已经完成。\n",
            encoding="utf-8",
        )
        return root

    def test_builds_all_events_newest_first_without_build_time_noise(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            output = build_site_updates_archive(root)
            markdown = output.read_text(encoding="utf-8")

            self.assertTrue(markdown.startswith("# 本站更新归档\n"))
            self.assertLess(markdown.index("维护完成"), markdown.index("F0-9_v2"))
            self.assertLess(markdown.index("F0-9_v2"), markdown.index("F0-9_v1"))
            self.assertIn("### `2026-8-4` `维护` 维护完成", markdown)
            self.assertIn("系统维护已经完成。", markdown)
            self.assertIn("### `2026-8-3` `更新` F0-9_v2", markdown)
            self.assertIn("《测试书（上册）》已更新第 2 版。", markdown)
            self.assertIn("### `2026-7-2` `新书` F0-9_v1", markdown)
            self.assertIn("《测试书（上册）》已上架。", markdown)
            self.assertIn("<!-- update-id: book-version-F0-9-v2 -->", markdown)
            self.assertNotIn("\n---\n", markdown)
            self.assertNotIn("generatedAt", markdown)
            build_site_updates_archive(root, check=True)

    def test_check_rejects_a_stale_archive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            output = build_site_updates_archive(root)
            output.write_text("stale\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "out of date"):
                build_site_updates_archive(root, check=True)

    def test_announcement_without_body_uses_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            announcement = root / "src/content/announcements/2026-08-05-notice.md"
            announcement.write_text(
                "---\n"
                "title: 服务公告\n"
                "label: 公告\n"
                "publishedAt: 2026-08-05T09:00:00+08:00\n"
                "summary:\n"
                "  - 第一项说明。\n"
                "  - 第二项说明。\n"
                "---\n",
                encoding="utf-8",
            )

            markdown = build_site_updates_archive(root).read_text(encoding="utf-8")

            self.assertIn("### `2026-8-5` `公告` 服务公告", markdown)
            self.assertIn("第一项说明。\n\n第二项说明。", markdown)


if __name__ == "__main__":
    unittest.main()
