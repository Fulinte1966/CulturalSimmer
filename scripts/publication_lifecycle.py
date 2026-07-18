"""Plan, preview, and finalize destructive publication lifecycle changes.

The script keeps planning side-effect free. A plan records both local file hashes
and remote Release assets; apply/finalize refuse to continue when that inventory
has changed. Public Git history is intentionally left intact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from build_book_changelogs import build_repository_changelogs
from build_site_updates_archive import build_site_updates_archive
from changelog_model import normalize_changelog
from compare_content_snapshots import compare_content_snapshots
from extract_content_snapshot import read_snapshot
from ingest_pdf import _dump_frontmatter, _load_markdown_parts
from render_release_changelog import render_release_changelog
from site_updates_data import atomic_write_json, load_generated_updates


ROOT = Path(__file__).resolve().parents[1]
OPERATIONS = {"withdraw-edition", "delist-book"}


def _run(command: list[str], *, input_text: str | None = None) -> str:
    result = subprocess.run(
        command,
        check=True,
        text=True,
        input=input_text,
        capture_output=True,
    )
    return result.stdout.strip()


def _gh(*args: str) -> str:
    return _run(["gh", *args])


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _load_book(root: Path, book_id: str) -> tuple[Path, dict[str, Any], str]:
    path = root / "src/content/books" / f"{book_id}.md"
    if not path.is_file():
        raise ValueError(f"Book does not exist: {book_id}")
    frontmatter, body = _load_markdown_parts(path)
    editions = frontmatter.get("editions")
    if not isinstance(editions, list) or not editions:
        raise ValueError(f"Book has no edition records: {book_id}")
    return path, frontmatter, body


def _ordered_editions(book: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [dict(item) for item in book["editions"]],
        key=lambda item: int(item["edition"]),
    )


def _release_tags(
    operation: str, book: dict[str, Any], edition: int | None
) -> list[str]:
    records = _ordered_editions(book)
    if operation == "withdraw-edition":
        matches = [item for item in records if int(item["edition"]) == edition]
        if not matches:
            raise ValueError(f"Edition does not exist: {book['id']}_v{edition}")
        if len(records) == 1:
            raise ValueError("The only edition cannot be withdrawn; delist the book")
        item = matches[0]
        return [str(item.get("releaseTag") or f"{book['id']}_v{edition}")]
    return [
        str(item.get("releaseTag") or f"{book['id']}_v{item['edition']}")
        for item in records
    ]


def _edition_paths(root: Path, tag: str) -> list[Path]:
    return [
        root / "src/data/manifests" / f"{tag}.json",
        root / "src/data/outlines" / f"{tag}.json",
        root / "src/data/reading" / f"{tag}.json",
        root / "src/data/changelogs" / f"{tag}.changelog.json",
        root / "public/covers" / f"{tag}.png",
        root / "public/covers" / f"{tag}_spine.png",
    ]


def _parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    source = path.read_text(encoding="utf-8")
    if not source.startswith("---\n"):
        raise ValueError(f"Markdown frontmatter is missing: {path}")
    _, raw, body = source.split("---", 2)
    value = yaml.safe_load(raw) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Markdown frontmatter must be an object: {path}")
    return value, body


def _associated_announcements(
    root: Path,
    operation: str,
    book: dict[str, Any],
    edition: int | None,
) -> tuple[list[Path], list[Path]]:
    explicit: list[Path] = []
    untyped_mentions: list[Path] = []
    book_id = str(book["id"])
    title = str(book.get("title") or "")
    tags = _release_tags(operation, book, edition)
    needles = [book_id, title, *tags]
    for path in sorted((root / "src/content/announcements").glob("*.md")):
        data, _ = _parse_frontmatter(path)
        if data.get("kind") == "important-erratum" and data.get("bookId") == book_id:
            if operation == "delist-book" or int(data.get("edition") or 0) == edition:
                explicit.append(path)
            continue
        text = path.read_text(encoding="utf-8")
        if any(needle and needle in text for needle in needles):
            untyped_mentions.append(path)
    return explicit, untyped_mentions


def _candidate_local_paths(
    root: Path,
    operation: str,
    book_path: Path,
    book: dict[str, Any],
    edition: int | None,
    explicit_announcements: list[Path],
) -> list[Path]:
    tags = _release_tags(operation, book, edition)
    paths: set[Path] = {
        book_path,
        root / "src/data/generated-updates.json",
        root / "src/data/site-update-pins.json",
        root / "docs/site-updates-archive.md",
        root / "src/data/changelogs" / f"{book['id']}.md",
        *explicit_announcements,
    }
    for tag in tags:
        paths.update(_edition_paths(root, tag))
    if operation == "withdraw-edition":
        records = _ordered_editions(book)
        successor = next(
            (item for item in records if int(item["edition"]) > int(edition or 0)),
            None,
        )
        if successor:
            successor_tag = str(
                successor.get("releaseTag")
                or f"{book['id']}_v{successor['edition']}"
            )
            paths.add(root / "src/data/changelogs" / f"{successor_tag}.changelog.json")
            paths.add(root / "src/data/manifests" / f"{successor_tag}.json")
    return sorted(paths)


def _target_update_ids(
    root: Path,
    operation: str,
    book: dict[str, Any],
    edition: int | None,
) -> list[str]:
    ordered = _ordered_editions(book)
    earliest = int(ordered[0]["edition"])
    ids: list[str] = []
    for update in load_generated_updates(root / "src/data/generated-updates.json"):
        if update["bookId"] != book["id"]:
            continue
        remove = operation == "delist-book" or (
            update["type"] == "book-added" and edition == earliest
        ) or (
            update["type"] == "book-updated"
            and int(update.get("edition") or 0) == edition
        )
        if not remove:
            continue
        update_edition = earliest if update["type"] == "book-added" else int(update["edition"])
        prefix = "new-book" if update["type"] == "book-added" else "book-version"
        ids.append(f"{prefix}-{book['id']}-v{update_edition}")
    return sorted(ids)


def _file_inventory(root: Path, paths: list[Path]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if path.is_file():
            data = path.read_bytes()
            entries.append(
                {"path": relative, "exists": True, "bytes": len(data), "sha256": _sha256_bytes(data)}
            )
        else:
            entries.append({"path": relative, "exists": False})
    return entries


def _remote_release_inventory(tags: list[str]) -> list[dict[str, Any]]:
    releases: list[dict[str, Any]] = []
    for tag in tags:
        payload = json.loads(_gh("api", f"repos/:owner/:repo/releases/tags/{tag}"))
        assets = [
            {
                "id": int(asset["id"]),
                "name": str(asset["name"]),
                "bytes": int(asset.get("size") or 0),
                "digest": asset.get("digest"),
            }
            for asset in payload.get("assets", [])
        ]
        releases.append(
            {
                "tag": tag,
                "releaseId": int(payload["id"]),
                "targetCommitish": payload.get("target_commitish"),
                "bodySha256": _sha256_bytes(
                    str(payload.get("body") or "").encode("utf-8")
                ),
                "assets": sorted(assets, key=lambda item: item["name"]),
            }
        )
    return releases


def _plan_hash(plan: dict[str, Any]) -> str:
    payload = {key: value for key, value in plan.items() if key != "inventorySha256"}
    return _sha256_bytes(_canonical_json(payload))


def create_plan(
    root: Path,
    *,
    operation: str,
    book_id: str,
    edition: int | None,
    reason: str | None,
    reason_digest: str | None = None,
    remote_inventory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if operation not in OPERATIONS:
        raise ValueError(f"Unknown operation: {operation}")
    if operation == "withdraw-edition" and (edition is None or edition < 1):
        raise ValueError("withdraw-edition requires a positive edition")
    if operation == "delist-book" and edition is not None:
        raise ValueError("delist-book does not accept an edition")
    if reason is not None:
        if not reason.strip():
            raise ValueError("A non-empty private reason is required")
        computed_reason_digest = _sha256_bytes(reason.strip().encode("utf-8"))
    elif reason_digest and re.fullmatch(r"[a-f0-9]{64}", reason_digest):
        computed_reason_digest = reason_digest
    else:
        raise ValueError("A private reason or its SHA-256 digest is required")

    book_path, book, _ = _load_book(root, book_id)
    explicit, mentions = _associated_announcements(
        root, operation, book, edition
    )
    if mentions:
        listed = ", ".join(path.relative_to(root).as_posix() for path in mentions)
        raise ValueError(
            "Untyped announcements reference the target; review them before removal: "
            + listed
        )
    tags = _release_tags(operation, book, edition)
    local_paths = _candidate_local_paths(
        root, operation, book_path, book, edition, explicit
    )
    plan: dict[str, Any] = {
        "schemaVersion": 1,
        "operation": operation,
        "bookId": book_id,
        "bookTitle": str(book.get("title") or ""),
        "edition": edition,
        # The reason belongs in the private operations ledger. The public plan
        # records only its digest so workflow inputs and logs do not disclose it.
        "reasonSha256": computed_reason_digest,
        "confirmation": (
            f"WITHDRAW {book_id}_v{edition}"
            if operation == "withdraw-edition"
            else f"DELIST {book_id}"
        ),
        "releaseTags": tags,
        "originalUpdateIds": _target_update_ids(
            root, operation, book, edition
        ),
        "explicitAnnouncements": [
            path.relative_to(root).as_posix() for path in explicit
        ],
        "files": _file_inventory(root, local_paths),
        "releases": remote_inventory if remote_inventory is not None else _remote_release_inventory(tags),
    }
    plan["inventorySha256"] = _plan_hash(plan)
    return plan


def _verify_plan(root: Path, plan: dict[str, Any], *, remote: bool) -> None:
    recorded_hash = str(plan.get("inventorySha256") or "")
    if recorded_hash != _plan_hash(plan):
        raise ValueError("Plan inventory digest is invalid")
    paths = [root / item["path"] for item in plan.get("files", [])]
    current_files = _file_inventory(root, paths)
    if current_files != plan.get("files"):
        raise ValueError("Local publication inventory has changed")
    if remote:
        current_releases = _remote_release_inventory(list(plan["releaseTags"]))
        if current_releases != plan.get("releases"):
            raise ValueError("Remote publication inventory has changed")


def _download_snapshot(tag: str, workspace: Path) -> dict[str, Any]:
    path = workspace / f"{tag}.content.json.gz"
    if not path.is_file():
        workspace.mkdir(parents=True, exist_ok=True)
        _gh(
            "release", "download", tag,
            "--pattern", path.name,
            "--dir", str(workspace),
        )
    return read_snapshot(path)


def _rebase_successor(
    root: Path,
    book: dict[str, Any],
    removed_edition: int,
    surviving: list[dict[str, Any]],
    workspace: Path,
) -> str | None:
    successor = next(
        (item for item in surviving if int(item["edition"]) > removed_edition),
        None,
    )
    if successor is None:
        return None
    predecessor = max(
        (item for item in surviving if int(item["edition"]) < int(successor["edition"])),
        key=lambda item: int(item["edition"]),
        default=None,
    )
    successor_tag = str(
        successor.get("releaseTag") or f"{book['id']}_v{successor['edition']}"
    )
    current_snapshot = _download_snapshot(successor_tag, workspace)
    if predecessor is None:
        changelog = {
            "schemaVersion": 1,
            "bookId": book["id"],
            "baseline": "earliest-surviving",
            "fromEdition": None,
            "toEdition": {
                "edition": int(successor["edition"]),
                "editionDate": str(successor["editionDate"]),
            },
            "changes": [],
        }
    else:
        predecessor_tag = str(
            predecessor.get("releaseTag")
            or f"{book['id']}_v{predecessor['edition']}"
        )
        previous_snapshot = _download_snapshot(predecessor_tag, workspace)
        changelog = compare_content_snapshots(previous_snapshot, current_snapshot)
    changelog = normalize_changelog(changelog)
    changelog_path = root / "src/data/changelogs" / f"{successor_tag}.changelog.json"
    changelog_path.write_text(
        json.dumps(changelog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest_path = root / "src/data/manifests" / f"{successor_tag}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["previousEdition"] = (
        int(predecessor["edition"]) if predecessor is not None else None
    )
    manifest["changelogSummary"] = changelog["summary"]
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return successor_tag


def _remove_generated_updates(
    root: Path,
    operation: str,
    book: dict[str, Any],
    edition: int | None,
) -> None:
    path = root / "src/data/generated-updates.json"
    updates = load_generated_updates(path)
    ordered = _ordered_editions(book)
    earliest = int(ordered[0]["edition"])
    kept = []
    removed_ids: set[str] = set()
    for update in updates:
        remove = update["bookId"] == book["id"] and (
            operation == "delist-book"
            or (
                update["type"] == "book-added" and edition == earliest
            )
            or (
                update["type"] == "book-updated"
                and int(update.get("edition") or 0) == edition
            )
        )
        if remove:
            removed_ids.add(str(update["id"]))
        else:
            kept.append(update)
    atomic_write_json(path, kept)

    pins_path = root / "src/data/site-update-pins.json"
    if pins_path.is_file():
        pins = json.loads(pins_path.read_text(encoding="utf-8"))
        if not isinstance(pins, list):
            raise ValueError("site-update-pins.json must contain an array")
        site_ids = {
            f"generated:{item_id}" for item_id in removed_ids
        } | removed_ids
        atomic_write_json(pins_path, [pin for pin in pins if pin not in site_ids])


def apply_plan(
    root: Path,
    plan: dict[str, Any],
    *,
    confirmation: str,
    workspace: Path,
) -> dict[str, Any]:
    _verify_plan(root, plan, remote=False)
    if confirmation != plan["confirmation"]:
        raise ValueError("Confirmation phrase does not match the plan")
    operation = str(plan["operation"])
    book_id = str(plan["bookId"])
    edition = plan.get("edition")
    book_path, book, body = _load_book(root, book_id)
    tags = list(plan["releaseTags"])

    successor_tag = None
    latest_surviving_tag = None
    if operation == "withdraw-edition":
        removed_edition = int(edition)
        surviving = [
            item
            for item in _ordered_editions(book)
            if int(item["edition"]) != removed_edition
        ]
        successor_tag = _rebase_successor(
            root, book, removed_edition, surviving, workspace
        )
        latest_record = max(surviving, key=lambda item: int(item["edition"]))
        latest_surviving_tag = str(
            latest_record.get("releaseTag")
            or f"{book_id}_v{latest_record['edition']}"
        )
        book["editions"] = surviving
        book_path.write_text(
            f"---\n{_dump_frontmatter(book)}---\n{body}", encoding="utf-8"
        )
        for tag in tags:
            for path in _edition_paths(root, tag):
                path.unlink(missing_ok=True)
    else:
        for item in _ordered_editions(book):
            tag = str(item.get("releaseTag") or f"{book_id}_v{item['edition']}")
            for path in _edition_paths(root, tag):
                path.unlink(missing_ok=True)
        book_path.unlink()
        (root / "src/data/changelogs" / f"{book_id}.md").unlink(missing_ok=True)

    for relative in plan.get("explicitAnnouncements", []):
        (root / relative).unlink(missing_ok=True)
    _remove_generated_updates(root, operation, book, edition)
    build_repository_changelogs(root)
    if operation == "delist-book":
        (root / "src/data/changelogs" / f"{book_id}.md").unlink(missing_ok=True)
    build_site_updates_archive(root)
    return {
        "successorReleaseTag": successor_tag,
        "latestSurvivingTag": latest_surviving_tag,
        "releaseTags": tags,
    }


def _superseded_block(latest_tag: str) -> str:
    repository = os.environ.get("GITHUB_REPOSITORY", "Fulinte1966/CulturalSimmer")
    latest_url = f"https://github.com/{repository}/releases/tag/{latest_tag}"
    return "\n".join(
        [
            "<!-- culturalsimmer-superseded:start -->",
            f"> 此版本已被 [{latest_tag}]({latest_url}) 取代。",
            "<!-- culturalsimmer-superseded:end -->",
        ]
    )


def mark_superseded_releases(book_id: str, latest_tag: str, older_tags: list[str]) -> None:
    marker = re.compile(
        r"\n?<!-- culturalsimmer-superseded:start -->[\s\S]*?"
        r"<!-- culturalsimmer-superseded:end -->\n?"
    )
    for tag in older_tags:
        release = json.loads(_gh("api", f"repos/:owner/:repo/releases/tags/{tag}"))
        body = marker.sub("\n", str(release.get("body") or "")).rstrip()
        notes = f"{_superseded_block(latest_tag)}\n\n{body}\n"
        _gh("release", "edit", tag, "--notes", notes)
    latest_release = json.loads(
        _gh("api", f"repos/:owner/:repo/releases/tags/{latest_tag}")
    )
    latest_body = marker.sub("\n", str(latest_release.get("body") or "")).strip()
    _gh("release", "edit", latest_tag, "--notes", f"{latest_body}\n", "--latest")
    print(f"Marked {len(older_tags)} {book_id} release(s) as superseded")


def mark_superseded_from_metadata(root: Path, metadata_path: Path) -> None:
    metadata = _load_json(metadata_path)
    _, book, _ = _load_book(root, str(metadata["id"]))
    latest_tag = str(metadata["canonicalTag"])
    older_tags = [
        str(item.get("releaseTag") or f"{book['id']}_v{item['edition']}")
        for item in _ordered_editions(book)
        if int(item["edition"]) < int(metadata["edition"])
    ]
    mark_superseded_releases(str(book["id"]), latest_tag, older_tags)


def finalize_remote(
    root: Path, plan: dict[str, Any], result: dict[str, Any]
) -> None:
    successor_tag = result.get("successorReleaseTag")
    if successor_tag:
        changelog_path = root / "src/data/changelogs" / f"{successor_tag}.changelog.json"
        manifest_path = root / "src/data/manifests" / f"{successor_tag}.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            notes = Path(temp_dir) / f"{successor_tag}.release-notes.md"
            release_manifest = Path(temp_dir) / f"{successor_tag}.manifest.json"
            changelog = normalize_changelog(
                json.loads(changelog_path.read_text(encoding="utf-8"))
            )
            notes.write_text(render_release_changelog(changelog), encoding="utf-8")
            shutil.copyfile(manifest_path, release_manifest)
            _gh("release", "edit", successor_tag, "--notes-file", str(notes))
            _gh(
                "release", "upload", successor_tag,
                str(changelog_path), str(release_manifest), "--clobber",
            )
    for tag in plan["releaseTags"]:
        _gh("release", "delete", str(tag), "--cleanup-tag", "--yes")
    if result.get("latestSurvivingTag"):
        _, book, _ = _load_book(root, str(plan["bookId"]))
        latest_tag = str(result["latestSurvivingTag"])
        older_tags = [
            str(item.get("releaseTag") or f"{book['id']}_v{item['edition']}")
            for item in _ordered_editions(book)
            if str(item.get("releaseTag") or f"{book['id']}_v{item['edition']}")
            != latest_tag
        ]
        mark_superseded_releases(str(book["id"]), latest_tag, older_tags)


def backup_plan(root: Path, plan: dict[str, Any], recipient: str) -> Path:
    if not recipient.strip():
        raise ValueError("An age recipient is required")
    _verify_plan(root, plan, remote=True)
    output_dir = root / "Outputs/removals"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    basename = f"{stamp}-{plan['operation']}-{plan['bookId']}"
    destination = output_dir / f"{basename}.tar.zst.age"
    with tempfile.TemporaryDirectory(prefix="culturalsimmer-removal-") as temp_dir:
        staging = Path(temp_dir) / basename
        staging.mkdir()
        (staging / "inventory.json").write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        files_root = staging / "repository"
        for item in plan["files"]:
            if not item.get("exists"):
                continue
            source = root / item["path"]
            target = files_root / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        releases_root = staging / "releases"
        for tag in plan["releaseTags"]:
            target = releases_root / str(tag)
            target.mkdir(parents=True, exist_ok=True)
            _gh("release", "download", str(tag), "--dir", str(target))

        tar = subprocess.Popen(
            ["tar", "-C", str(Path(temp_dir)), "-cf", "-", basename],
            stdout=subprocess.PIPE,
        )
        zstd = subprocess.Popen(
            ["zstd", "-q", "-T0", "-c"],
            stdin=tar.stdout,
            stdout=subprocess.PIPE,
        )
        assert tar.stdout is not None and zstd.stdout is not None
        tar.stdout.close()
        age = subprocess.run(
            ["age", "-r", recipient, "-o", str(destination)],
            stdin=zstd.stdout,
            check=False,
        )
        zstd.stdout.close()
        if tar.wait() != 0 or zstd.wait() != 0 or age.returncode != 0:
            destination.unlink(missing_ok=True)
            raise RuntimeError("Encrypted removal backup failed")
    return destination


def register_private_removal(plan: dict[str, Any], reason: str) -> None:
    reason = reason.strip()
    if _sha256_bytes(reason.encode("utf-8")) != plan.get("reasonSha256"):
        raise ValueError("Private reason does not match the plan digest")
    editions = []
    for tag in plan["releaseTags"]:
        match = re.search(r"_v([1-9]\d*)$", str(tag))
        if not match:
            raise ValueError(f"Unable to derive an edition from tag: {tag}")
        editions.append(int(match.group(1)))
    payload = {
        "ref": "main",
        "inputs": {
            "phase": "register",
            "operation": plan["operation"],
            "book_id": plan["bookId"],
            "title": plan["bookTitle"],
            "editions": json.dumps(editions),
            "tags": json.dumps(plan["releaseTags"]),
            "original_update_ids": json.dumps(plan["originalUpdateIds"]),
            "reason": reason,
            "reason_sha256": plan["reasonSha256"],
            "inventory_sha256": plan["inventorySha256"],
        },
    }
    _run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            "repos/Fulinte1966/CulturalSimmer-notifier/actions/workflows/record-publication-removal.yml/dispatches",
            "--input",
            "-",
        ],
        input_text=json.dumps(payload, ensure_ascii=False),
    )


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--operation", choices=sorted(OPERATIONS), required=True)
    plan_parser.add_argument("--book-id", required=True)
    plan_parser.add_argument("--edition", type=int)
    reason_group = plan_parser.add_mutually_exclusive_group(required=True)
    reason_group.add_argument("--reason")
    reason_group.add_argument("--reason-digest")
    plan_parser.add_argument("--output", required=True)
    plan_parser.add_argument("--remote-inventory")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--plan", required=True)
    verify_parser.add_argument("--remote", action="store_true")

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--plan", required=True)
    apply_parser.add_argument("--confirmation", required=True)
    apply_parser.add_argument("--workspace", required=True)
    apply_parser.add_argument("--output", required=True)

    finalize_parser = subparsers.add_parser("finalize-remote")
    finalize_parser.add_argument("--plan", required=True)
    finalize_parser.add_argument("--result", required=True)

    backup_parser = subparsers.add_parser("backup")
    backup_parser.add_argument("--plan", required=True)
    backup_parser.add_argument("--age-recipient", required=True)

    register_parser = subparsers.add_parser("register-private")
    register_parser.add_argument("--plan", required=True)
    register_parser.add_argument("--reason", required=True)

    supersede_parser = subparsers.add_parser("mark-superseded")
    supersede_parser.add_argument("--book-id", required=True)
    supersede_parser.add_argument("--latest-tag", required=True)
    supersede_parser.add_argument("--older-tag", action="append", default=[])

    supersede_metadata_parser = subparsers.add_parser("mark-superseded-from-metadata")
    supersede_metadata_parser.add_argument("--metadata", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            remote_inventory = (
                json.loads(Path(args.remote_inventory).read_text(encoding="utf-8"))
                if args.remote_inventory
                else None
            )
            plan = create_plan(
                ROOT,
                operation=args.operation,
                book_id=args.book_id,
                edition=args.edition,
                reason=args.reason,
                reason_digest=args.reason_digest,
                remote_inventory=remote_inventory,
            )
            Path(args.output).write_text(
                json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(plan["inventorySha256"])
        elif args.command == "verify":
            _verify_plan(ROOT, _load_json(Path(args.plan)), remote=args.remote)
            print("Publication inventory verified")
        elif args.command == "apply":
            result = apply_plan(
                ROOT,
                _load_json(Path(args.plan)),
                confirmation=args.confirmation,
                workspace=Path(args.workspace),
            )
            Path(args.output).write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        elif args.command == "finalize-remote":
            finalize_remote(
                ROOT,
                _load_json(Path(args.plan)),
                _load_json(Path(args.result)),
            )
        elif args.command == "backup":
            print(backup_plan(ROOT, _load_json(Path(args.plan)), args.age_recipient))
        elif args.command == "register-private":
            register_private_removal(_load_json(Path(args.plan)), args.reason)
            print("Private removal registration dispatched")
        elif args.command == "mark-superseded":
            mark_superseded_releases(
                args.book_id, args.latest_tag, list(args.older_tag)
            )
        else:
            mark_superseded_from_metadata(ROOT, Path(args.metadata))
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Publication lifecycle failed: {error}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
