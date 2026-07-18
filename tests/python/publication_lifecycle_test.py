"""Tests for publication withdrawal and delisting transformations."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from publication_lifecycle import apply_plan, create_plan, register_private_removal
from candidate_lock import create_lock, verify_lock
from edition_policy import check_expected_edition
from extract_content_snapshot import NORMALIZATION_PROFILE, tokenize_text, write_snapshot


def write_book(root: Path, editions: list[int]) -> None:
    book = root / "src/content/books/A93-1.md"
    book.parent.mkdir(parents=True)
    records = "".join(
        "  - edition: {edition}\n"
        "    editionDate: 2026-07\n"
        "    releaseTag: A93-1_v{edition}\n"
        "    manifest: src/data/manifests/A93-1_v{edition}.json\n".format(
            edition=edition
        )
        for edition in editions
    )
    book.write_text(
        "---\nid: A93-1\ntitle: 测试书\ndescription: 测试。\ntags: []\n"
        f"editions:\n{records}---\n\n测试。\n",
        encoding="utf-8",
    )
    (root / "src/data/changelogs").mkdir(parents=True)
    (root / "src/data/generated-updates.json").write_text(
        json.dumps(
            [
                {
                    "id": "A93-1-listed",
                    "type": "book-added",
                    "publishedAt": "2026-07-01T00:00:00Z",
                    "bookId": "A93-1",
                },
                *[
                    {
                        "id": f"A93-1-v{edition}",
                        "type": "book-updated",
                        "publishedAt": f"2026-07-0{edition}T00:00:00Z",
                        "bookId": "A93-1",
                        "edition": edition,
                    }
                    for edition in editions
                    if edition > min(editions)
                ],
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "src/data/site-update-pins.json").write_text("[]\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs/site-updates-archive.md").write_text("fixture\n", encoding="utf-8")
    (root / "src/content/announcements").mkdir(parents=True)

    for edition in editions:
        tag = f"A93-1_v{edition}"
        changelog = {
            "schemaVersion": 1,
            "bookId": "A93-1",
            "fromEdition": (
                None
                if edition == min(editions)
                else {"edition": edition - 1, "editionDate": "2026-07"}
            ),
            "toEdition": {"edition": edition, "editionDate": "2026-07"},
            "changes": [],
        }
        (root / "src/data/changelogs" / f"{tag}.changelog.json").write_text(
            json.dumps(changelog), encoding="utf-8"
        )
        manifest = root / "src/data/manifests" / f"{tag}.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("{}\n", encoding="utf-8")


def write_content_snapshot(workspace: Path, edition: int, text: str) -> None:
    tokens = tokenize_text(text)
    write_snapshot(
        workspace / f"A93-1_v{edition}.content.json.gz",
        {
            "schemaVersion": 1,
            "normalizationProfile": NORMALIZATION_PROFILE,
            "bookId": "A93-1",
            "edition": edition,
            "editionDate": "2026-07",
            "pageCount": 1,
            "tokens": tokens,
            "pageRuns": [
                {
                    "start": 0,
                    "end": len(tokens),
                    "page": 1,
                    "label": "1",
                }
            ],
        },
    )


class PublicationLifecycleTests(unittest.TestCase):
    def test_candidate_lock_rejects_pdf_or_source_commit_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = root / "A93-1_v3.pdf"
            metadata = root / "candidate.json"
            lock = root / "candidate-lock.json"
            pdf.write_bytes(b"candidate-pdf")
            metadata.write_text(
                json.dumps(
                    {
                        "id": "A93-1",
                        "edition": 3,
                        "canonicalTag": "A93-1_v3",
                        "sourceReleaseTag": "ingest-A93-1-v3",
                        "sourceReleaseId": 42,
                        "sourceCommit": "source-commit",
                        "allowEditionSkip": False,
                        "sourcePdfPath": str(pdf),
                    }
                ),
                encoding="utf-8",
            )
            create_lock(metadata, lock)
            verify_lock(metadata, lock, "source-commit")
            with self.assertRaisesRegex(ValueError, "sourceCommit"):
                verify_lock(metadata, lock, "different-commit")
            changed_metadata = json.loads(metadata.read_text(encoding="utf-8"))
            changed_metadata["allowEditionSkip"] = True
            metadata.write_text(json.dumps(changed_metadata), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "allowEditionSkip"):
                verify_lock(metadata, lock, "source-commit")
            changed_metadata["allowEditionSkip"] = False
            metadata.write_text(json.dumps(changed_metadata), encoding="utf-8")
            pdf.write_bytes(b"changed-candidate-pdf")
            with self.assertRaisesRegex(ValueError, "pdfBytes|pdfSha256"):
                verify_lock(metadata, lock, "source-commit")

    def test_private_ledger_prevents_removed_edition_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ledger = root / "publication-removals.json"
            ledger.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "removals": [
                            {
                                "bookId": "A93-1",
                                "editions": [1, 2],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            reused = check_expected_edition(
                root, "A93-1", 2, ledger_path=ledger
            )
            self.assertFalse(reused.ok)
            self.assertEqual(reused.expected_edition, 3)
            next_edition = check_expected_edition(
                root, "A93-1", 3, ledger_path=ledger
            )
            self.assertTrue(next_edition.ok)

    def test_private_reason_is_sent_through_standard_input(self) -> None:
        reason = "Private rights review"
        plan = {
            "operation": "withdraw-edition",
            "bookId": "A93-1",
            "bookTitle": "测试书",
            "releaseTags": ["A93-1_v2"],
            "originalUpdateIds": ["book-version-A93-1-v2"],
            "reasonSha256": hashlib.sha256(reason.encode("utf-8")).hexdigest(),
            "inventorySha256": "a" * 64,
        }
        with patch("publication_lifecycle._run", return_value="") as run:
            register_private_removal(plan, reason)
        command = run.call_args.args[0]
        payload = json.loads(run.call_args.kwargs["input_text"])
        self.assertNotIn(reason, command)
        self.assertEqual(payload["inputs"]["reason"], reason)

    def test_withdraw_latest_restores_previous_without_reusing_number(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_book(root, [1, 2])
            plan = create_plan(
                root,
                operation="withdraw-edition",
                book_id="A93-1",
                edition=2,
                reason="Administrative correction",
                remote_inventory=[],
            )
            result = apply_plan(
                root,
                plan,
                confirmation="WITHDRAW A93-1_v2",
                workspace=root / "workspace",
            )
            self.assertIsNone(result["successorReleaseTag"])
            source = (root / "src/content/books/A93-1.md").read_text("utf-8")
            self.assertIn("edition: 1", source)
            self.assertNotIn("edition: 2", source)
            self.assertFalse((root / "src/data/manifests/A93-1_v2.json").exists())
            updates = json.loads(
                (root / "src/data/generated-updates.json").read_text("utf-8")
            )
            self.assertEqual([item["id"] for item in updates], ["A93-1-listed"])

    def test_withdraw_middle_rebases_successor_against_nearest_predecessor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            write_book(root, [1, 2, 3])
            write_content_snapshot(workspace, 1, "初版正文。")
            write_content_snapshot(workspace, 3, "第三版正文。")
            plan = create_plan(
                root,
                operation="withdraw-edition",
                book_id="A93-1",
                edition=2,
                reason="Administrative correction",
                remote_inventory=[],
            )

            result = apply_plan(
                root,
                plan,
                confirmation="WITHDRAW A93-1_v2",
                workspace=workspace,
            )

            self.assertEqual(result["successorReleaseTag"], "A93-1_v3")
            changelog = json.loads(
                (root / "src/data/changelogs/A93-1_v3.changelog.json").read_text(
                    encoding="utf-8"
                )
            )
            manifest = json.loads(
                (root / "src/data/manifests/A93-1_v3.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(changelog["fromEdition"]["edition"], 1)
            self.assertEqual(changelog["toEdition"]["edition"], 3)
            self.assertEqual(manifest["previousEdition"], 1)

    def test_withdraw_earliest_marks_successor_as_earliest_surviving(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            write_book(root, [1, 2, 3])
            write_content_snapshot(workspace, 2, "第二版正文。")
            plan = create_plan(
                root,
                operation="withdraw-edition",
                book_id="A93-1",
                edition=1,
                reason="Administrative correction",
                remote_inventory=[],
            )

            result = apply_plan(
                root,
                plan,
                confirmation="WITHDRAW A93-1_v1",
                workspace=workspace,
            )

            self.assertEqual(result["successorReleaseTag"], "A93-1_v2")
            changelog = json.loads(
                (root / "src/data/changelogs/A93-1_v2.changelog.json").read_text(
                    encoding="utf-8"
                )
            )
            manifest = json.loads(
                (root / "src/data/manifests/A93-1_v2.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(changelog["baseline"], "earliest-surviving")
            self.assertIsNone(changelog["fromEdition"])
            self.assertIsNone(manifest["previousEdition"])

    def test_only_edition_requires_delisting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_book(root, [1])
            with self.assertRaisesRegex(ValueError, "only edition"):
                create_plan(
                    root,
                    operation="withdraw-edition",
                    book_id="A93-1",
                    edition=1,
                    reason="Administrative correction",
                    remote_inventory=[],
                )

    def test_delist_removes_book_and_public_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_book(root, [1, 2])
            plan = create_plan(
                root,
                operation="delist-book",
                book_id="A93-1",
                edition=None,
                reason="Rights review",
                remote_inventory=[],
            )
            apply_plan(
                root,
                plan,
                confirmation="DELIST A93-1",
                workspace=root / "workspace",
            )
            self.assertFalse((root / "src/content/books/A93-1.md").exists())
            self.assertEqual(
                json.loads(
                    (root / "src/data/generated-updates.json").read_text("utf-8")
                ),
                [],
            )
            self.assertEqual(
                (root / "docs/site-updates-archive.md").read_text("utf-8"), ""
            )

    def test_confirmation_and_inventory_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_book(root, [1, 2])
            plan = create_plan(
                root,
                operation="withdraw-edition",
                book_id="A93-1",
                edition=2,
                reason="Administrative correction",
                remote_inventory=[],
            )
            with self.assertRaisesRegex(ValueError, "Confirmation"):
                apply_plan(
                    root,
                    plan,
                    confirmation="WITHDRAW WRONG",
                    workspace=root / "workspace",
                )
            (root / "src/data/generated-updates.json").write_text(
                "[]\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "inventory has changed"):
                apply_plan(
                    root,
                    plan,
                    confirmation="WITHDRAW A93-1_v2",
                    workspace=root / "workspace",
                )


if __name__ == "__main__":
    unittest.main()
