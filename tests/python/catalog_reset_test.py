"""Tests for the protected pre-launch catalog reset transaction."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from catalog_reset import (
    CONFIRMATION,
    _immutable_releases_enabled,
    apply_plan,
    build_workflow_inputs,
    create_plan,
    verify_plan,
)


def write_fixture(root: Path) -> dict:
    for relative in (
        "src/content/books",
        "src/content/announcements",
        "src/data/manifests",
        "src/data/outlines",
        "src/data/reading",
        "src/data/changelogs",
        "public/covers",
        "public/fonts/subset",
    ):
        directory = root / relative
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").write_text("", encoding="utf-8")
    (root / "docs").mkdir()

    (root / "src/content/books/A93-1.md").write_text(
        "---\nid: A93-1\ntitle: 测试书\ntags: []\neditions:\n"
        "  - edition: 1\n    editionDate: 2026-07\n    releaseTag: A93-1_v1\n"
        "---\n\n测试正文。\n",
        encoding="utf-8",
    )
    (root / "src/content/announcements/manual.md").write_text(
        "---\ntitle: 手工公告\nlabel: 公告\npublishedAt: 2026-07-01T08:00:00+08:00\n"
        "kind: site-announcement\nsummary:\n  - 保留。\n---\n\n保留公告。\n",
        encoding="utf-8",
    )
    (root / "src/content/announcements/erratum.md").write_text(
        "---\ntitle: 勘误\nlabel: 勘误\npublishedAt: 2026-07-02T08:00:00+08:00\n"
        "kind: important-erratum\nbookId: A93-1\nedition: 1\nsummary:\n  - 删除。\n---\n",
        encoding="utf-8",
    )
    for relative in (
        "src/data/manifests/A93-1_v1.json",
        "src/data/outlines/A93-1_v1.json",
        "src/data/reading/A93-1_v1.json",
        "src/data/changelogs/A93-1_v1.changelog.json",
    ):
        (root / relative).write_text("{}\n", encoding="utf-8")
    (root / "src/data/changelogs/A93-1.md").write_text("generated\n", encoding="utf-8")
    (root / "public/covers/A93-1_v1.png").write_bytes(b"cover")
    (root / "public/fonts/subset/generated.woff2").write_bytes(b"font")
    (root / "src/data/generated-updates.json").write_text(
        json.dumps(
            [
                {
                    "id": "A93-1-listed",
                    "type": "book-added",
                    "publishedAt": "2026-07-01T00:00:00Z",
                    "bookId": "A93-1",
                }
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "src/data/site-update-pins.json").write_text(
        '["manual:manual", "automatic:A93-1-listed", "manual:erratum"]\n',
        encoding="utf-8",
    )
    (root / "docs/site-updates-archive.md").write_text("old archive\n", encoding="utf-8")

    return {
        "immutableReleases": False,
        "releases": [
            {
                "id": 1,
                "tag_name": "A93-1_v1",
                "draft": False,
                "prerelease": False,
                "target_commitish": "main",
                "body": "release",
                "assets": [
                    {
                        "id": 11,
                        "name": "A93-1_v1.pdf",
                        "size": 3,
                        "digest": "sha256:" + hashlib.sha256(b"pdf").hexdigest(),
                    }
                ],
            },
            {
                "id": 2,
                "tag_name": "code-v1",
                "draft": False,
                "prerelease": False,
                "target_commitish": "main",
                "body": "unrelated",
                "assets": [],
            },
            {
                "id": 3,
                "tag_name": "A9-1_v1",
                "draft": False,
                "prerelease": False,
                "target_commitish": "main",
                "body": "orphan test release",
                "assets": [
                    {"id": 31, "name": "A9-1_v1.manifest.json", "size": 2},
                    {"id": 32, "name": "A9-1_v1.content.json.gz", "size": 2},
                ],
            },
            {
                "id": 4,
                "tag_name": "ingest-fixture",
                "draft": True,
                "prerelease": False,
                "target_commitish": "main",
                "body": "draft test release",
                "assets": [],
            },
        ],
        "tags": [
            {"ref": "refs/tags/A93-1_v1", "object": {"sha": "book-sha"}},
            {"ref": "refs/tags/A9-1_v1", "object": {"sha": "orphan-sha"}},
            {"ref": "refs/tags/ingest-fixture", "object": {"sha": "draft-sha"}},
            {"ref": "refs/tags/code-v1", "object": {"sha": "code-sha"}},
        ],
    }


class CatalogResetTests(unittest.TestCase):
    @patch("catalog_reset.subprocess.run")
    def test_immutable_release_check_uses_explicit_release_fields_on_403(
        self, run
    ) -> None:
        run.return_value.returncode = 1
        run.return_value.stdout = ""
        run.return_value.stderr = "gh: Resource not accessible by integration (HTTP 403)"

        self.assertFalse(
            _immutable_releases_enabled("owner/repo", [{"immutable": False}])
        )
        self.assertTrue(
            _immutable_releases_enabled("owner/repo", [{"immutable": True}])
        )

    @patch("catalog_reset.subprocess.run")
    def test_immutable_release_check_rejects_unverifiable_403(self, run) -> None:
        run.return_value.returncode = 1
        run.return_value.stdout = ""
        run.return_value.stderr = "gh: Resource not accessible by integration (HTTP 403)"

        with self.assertRaisesRegex(RuntimeError, "CATALOG_RESET_ADMIN_TOKEN"):
            _immutable_releases_enabled("owner/repo", [])

    def test_plan_filters_unrelated_releases_and_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            remote = write_fixture(root)
            plan = create_plan(root, reason="Pre-launch cleanup", remote_state=remote)

            self.assertEqual(plan["bookIds"], ["A93-1"])
            self.assertEqual(plan["originalUpdateIds"], ["A93-1-listed"])
            self.assertEqual(
                [item["tag"] for item in plan["remote"]["releases"]],
                ["A9-1_v1", "A93-1_v1", "ingest-fixture"],
            )
            self.assertEqual(
                [item["tag"] for item in plan["remote"]["tags"]],
                ["A9-1_v1", "A93-1_v1", "ingest-fixture"],
            )
            verify_plan(root, plan, remote=False)

    def test_plan_rejects_immutable_releases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            remote = write_fixture(root)
            remote["immutableReleases"] = True
            with self.assertRaisesRegex(ValueError, "Immutable Releases"):
                create_plan(root, reason="Pre-launch cleanup", remote_state=remote)

    def test_apply_clears_generated_catalog_and_preserves_manual_announcement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = create_plan(
                root,
                reason="Pre-launch cleanup",
                remote_state=write_fixture(root),
            )
            result = apply_plan(root, plan, confirmation=CONFIRMATION)

            self.assertFalse((root / "src/content/books/A93-1.md").exists())
            self.assertFalse((root / "src/content/announcements/erratum.md").exists())
            self.assertTrue((root / "src/content/announcements/manual.md").exists())
            self.assertTrue((root / "src/content/books/.gitkeep").exists())
            self.assertEqual(
                json.loads((root / "src/data/generated-updates.json").read_text("utf-8")),
                [],
            )
            self.assertEqual(
                json.loads((root / "src/data/site-update-pins.json").read_text("utf-8")),
                ["manual:manual"],
            )
            archive = (root / "docs/site-updates-archive.md").read_text("utf-8")
            self.assertIn("手工公告", archive)
            self.assertNotIn("测试书", archive)
            self.assertEqual(result["notifierUpdateIds"], ["A93-1-listed"])

    def test_apply_requires_exact_confirmation_and_unchanged_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = create_plan(
                root,
                reason="Pre-launch cleanup",
                remote_state=write_fixture(root),
            )
            with self.assertRaisesRegex(ValueError, "Confirmation"):
                apply_plan(root, plan, confirmation="RESET")
            (root / "src/data/generated-updates.json").write_text("[]\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inventory has changed"):
                verify_plan(root, plan, remote=False)

    def test_workflow_inputs_bind_the_backup_to_the_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = create_plan(
                root,
                reason="Pre-launch cleanup",
                remote_state=write_fixture(root),
            )
            receipt = {
                "inventorySha256": plan["inventorySha256"],
                "backupSha256": "a" * 64,
            }
            inputs = build_workflow_inputs(plan, receipt, mode="preview")
            self.assertEqual(inputs["confirmation"], CONFIRMATION)
            self.assertEqual(inputs["backup_sha256"], "a" * 64)
            receipt["inventorySha256"] = "b" * 64
            with self.assertRaisesRegex(ValueError, "does not belong"):
                build_workflow_inputs(plan, receipt, mode="promote")


if __name__ == "__main__":
    unittest.main()
