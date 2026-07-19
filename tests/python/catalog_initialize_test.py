from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from catalog_initialize import CONFIRMATION, apply_plan, create_plan


class CatalogInitializeTests(unittest.TestCase):
    def _fixture(self, root: Path) -> None:
        for directory in (
            "src/content/books",
            "src/content/announcements",
            "src/data/manifests",
            "src/data/outlines",
            "src/data/reading",
            "src/data/changelogs",
            "public/covers",
            "public/assets/announcements",
        ):
            (root / directory).mkdir(parents=True, exist_ok=True)
        (root / "src/content/books/A9-1.md").write_text("book\n", encoding="utf-8")
        (root / "src/data/manifests/A9-1_v1.json").write_text("{}\n", encoding="utf-8")
        (root / "src/data/generated-updates.json").write_text("[{}]\n", encoding="utf-8")
        (root / "src/content/announcements/2026-07-16-site-updates-radio.md").write_text(
            "announcement\n", encoding="utf-8"
        )
        (root / "public/assets/announcements/site-updates-radio-qr.svg").write_text(
            "<svg/>\n", encoding="utf-8"
        )
        (root / "src/data/site-update-pins.json").write_text(
            json.dumps(["manual:2026-07-16-site-updates-radio"]), encoding="utf-8"
        )

    def test_clears_generated_files_and_preserves_manual_announcement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)
            plan = create_plan(root)
            self.assertEqual(plan["releaseTags"], ["A9-1_v1"])
            apply_plan(root, plan, CONFIRMATION)
            self.assertFalse((root / "src/content/books/A9-1.md").exists())
            self.assertFalse((root / "src/data/manifests/A9-1_v1.json").exists())
            self.assertEqual(
                (root / "src/data/generated-updates.json").read_text("utf-8"), "[]\n"
            )
            self.assertTrue(
                (root / "src/content/announcements/2026-07-16-site-updates-radio.md").is_file()
            )

    def test_rejects_a_stale_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)
            plan = create_plan(root)
            (root / "src/content/books/A9-1.md").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "清单已经失效"):
                apply_plan(root, plan, CONFIRMATION)
