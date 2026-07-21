"""Prepare and execute a protected pre-launch test catalog reset.

The default ``plan`` command is side-effect free. A real reset requires an
encrypted local backup, an Access-protected preview, an Environment approval,
and an exact confirmation phrase. This operation is intentionally separate
from withdrawal/delisting: test edition numbers may be reused after a reset,
while editions removed from a production catalog remain permanently reserved.
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

from build_site_updates_archive import build_site_updates_archive
from site_updates_data import atomic_write_json, load_generated_updates


ROOT = Path(__file__).resolve().parents[1]
OPERATION = "reset-prelaunch-test-catalog"
CONFIRMATION = "RESET PRELAUNCH TEST CATALOG"
GENERATED_DIRECTORIES = (
    "src/content/books",
    "src/data/manifests",
    "src/data/outlines",
    "src/data/reading",
    "src/data/changelogs",
    "public/covers",
    "public/fonts/subset",
)
GENERATED_FILES = (
    "src/data/generated-updates.json",
    "src/data/site-update-pins.json",
    "docs/site-updates-archive.md",
)
CANONICAL_TAG = re.compile(r"^[A-Z](?:[A-Z0-9.-]*[A-Z0-9])?_v[1-9]\d*$")


def _run(command: list[str], *, check: bool = True) -> str:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{detail}")
    return result.stdout.strip()


def _gh(*args: str, check: bool = True) -> str:
    return _run(["gh", *args], check=check)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _load_frontmatter(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    if not source.startswith("---\n"):
        raise ValueError(f"Markdown frontmatter is missing: {path}")
    parts = source.split("---", 2)
    if len(parts) != 3:
        raise ValueError(f"Markdown frontmatter is invalid: {path}")
    value = yaml.safe_load(parts[1]) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Markdown frontmatter must be an object: {path}")
    return value


def _book_inventory(root: Path) -> tuple[list[str], list[str]]:
    book_ids: list[str] = []
    tags: list[str] = []
    for path in sorted((root / "src/content/books").glob("*.md")):
        data = _load_frontmatter(path)
        book_id = str(data.get("id") or "").strip()
        editions = data.get("editions")
        if not book_id or not isinstance(editions, list):
            raise ValueError(f"Book metadata is incomplete: {path}")
        book_ids.append(book_id)
        for edition in editions:
            if not isinstance(edition, dict):
                raise ValueError(f"Edition metadata is invalid: {path}")
            number = int(edition["edition"])
            tags.append(str(edition.get("releaseTag") or f"{book_id}_v{number}"))
    return sorted(book_ids), sorted(set(tags))


def _important_errata(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted((root / "src/content/announcements").glob("*.md")):
        if _load_frontmatter(path).get("kind") == "important-erratum":
            paths.append(path)
    return paths


def _target_paths(root: Path) -> list[Path]:
    paths: set[Path] = {root / relative for relative in GENERATED_FILES}
    for relative in GENERATED_DIRECTORIES:
        directory = root / relative
        if not directory.exists():
            continue
        paths.update(
            path
            for path in directory.rglob("*")
            if path.is_file() and path.name != ".gitkeep"
        )
    paths.update(_important_errata(root))
    return sorted(paths)


def _file_inventory(root: Path, paths: list[Path]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if not path.is_file():
            entries.append({"path": relative, "exists": False})
            continue
        value = path.read_bytes()
        entries.append(
            {
                "path": relative,
                "exists": True,
                "bytes": len(value),
                "sha256": _sha256_bytes(value),
            }
        )
    return entries


def _flatten_pages(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("GitHub API response must be an array")
    if value and isinstance(value[0], list):
        return [item for page in value for item in page]
    return value


def _repository() -> str:
    configured = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if configured:
        return configured
    return _gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner")


def _immutable_releases_enabled(repository: str) -> bool:
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repository}/immutable-releases",
            "-H",
            "X-GitHub-Api-Version: 2026-03-10",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        payload = json.loads(result.stdout)
        return bool(payload.get("enabled", True))
    if "HTTP 404" in result.stderr or "Not Found" in result.stderr:
        return False
    raise RuntimeError(result.stderr.strip() or "Unable to inspect immutable releases")


def _publication_release(release: dict[str, Any], canonical_tags: set[str]) -> bool:
    tag = str(release.get("tag_name") or release.get("tag") or "")
    if tag in canonical_tags or tag.startswith("ingest-"):
        return True
    asset_names = {str(item.get("name") or "") for item in release.get("assets", [])}
    return (
        f"{tag}.manifest.json" in asset_names
        and f"{tag}.content.json.gz" in asset_names
        and bool(CANONICAL_TAG.fullmatch(tag))
    )


def _normalize_remote_state(
    value: dict[str, Any], canonical_tags: set[str], book_ids: set[str]
) -> dict[str, Any]:
    releases: list[dict[str, Any]] = []
    for release in value.get("releases", []):
        if not _publication_release(release, canonical_tags):
            continue
        assets = [
            {
                "id": int(asset["id"]),
                "name": str(asset["name"]),
                "bytes": int(asset.get("size") or asset.get("bytes") or 0),
                "digest": asset.get("digest"),
            }
            for asset in release.get("assets", [])
        ]
        releases.append(
            {
                "tag": str(release.get("tag_name") or release.get("tag")),
                "releaseId": int(release.get("id") or release.get("releaseId")),
                "draft": bool(release.get("draft", False)),
                "prerelease": bool(release.get("prerelease", False)),
                "targetCommitish": release.get("target_commitish")
                or release.get("targetCommitish"),
                "bodySha256": release.get("bodySha256")
                or _sha256_bytes(str(release.get("body") or "").encode("utf-8")),
                "assets": sorted(assets, key=lambda item: item["name"]),
            }
        )
    release_tags = {item["tag"] for item in releases}
    tags: list[dict[str, str]] = []
    for item in value.get("tags", []):
        tag = str(item.get("tag") or item.get("ref") or "").removeprefix("refs/tags/")
        belongs_to_known_book = any(
            re.fullmatch(re.escape(book_id) + r"_v[1-9]\d*", tag)
            for book_id in book_ids
        )
        if (
            tag in release_tags
            or tag in canonical_tags
            or belongs_to_known_book
            or tag.startswith("ingest-")
        ):
            tags.append(
                {
                    "tag": tag,
                    "sha": str(
                        item.get("sha") or item.get("object", {}).get("sha") or ""
                    ),
                }
            )
    return {
        "immutableReleases": bool(value.get("immutableReleases", False)),
        "releases": sorted(releases, key=lambda item: item["tag"]),
        "tags": sorted(tags, key=lambda item: item["tag"]),
    }


def _remote_state(canonical_tags: set[str], book_ids: set[str]) -> dict[str, Any]:
    repository = _repository()
    releases = _flatten_pages(
        json.loads(
            _gh(
                "api",
                "--paginate",
                "--slurp",
                f"repos/{repository}/releases?per_page=100",
            )
        )
    )
    refs = _flatten_pages(
        json.loads(
            _gh(
                "api",
                "--paginate",
                "--slurp",
                f"repos/{repository}/git/matching-refs/tags/?per_page=100",
            )
        )
    )
    tags = [
        {"ref": item.get("ref"), "sha": item.get("object", {}).get("sha")}
        for item in refs
    ]
    return _normalize_remote_state(
        {
            "immutableReleases": _immutable_releases_enabled(repository),
            "releases": releases,
            "tags": tags,
        },
        canonical_tags,
        book_ids,
    )


def _plan_hash(plan: dict[str, Any]) -> str:
    payload = {key: value for key, value in plan.items() if key != "inventorySha256"}
    return _sha256_bytes(_canonical_json(payload))


def create_plan(
    root: Path,
    *,
    reason: str | None,
    reason_digest: str | None = None,
    remote_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if reason is not None:
        if not reason.strip():
            raise ValueError("A non-empty private reason is required")
        digest = _sha256_bytes(reason.strip().encode("utf-8"))
    elif reason_digest and re.fullmatch(r"[a-f0-9]{64}", reason_digest):
        digest = reason_digest
    else:
        raise ValueError("A private reason or its SHA-256 digest is required")

    book_ids, canonical_tags = _book_inventory(root)
    normalized_remote = (
        _normalize_remote_state(remote_state, set(canonical_tags), set(book_ids))
        if remote_state is not None
        else _remote_state(set(canonical_tags), set(book_ids))
    )
    if normalized_remote["immutableReleases"]:
        raise ValueError(
            "Immutable Releases is enabled; a pre-launch reset cannot reuse deleted tags"
        )
    update_ids = [
        str(item["id"])
        for item in load_generated_updates(root / "src/data/generated-updates.json")
    ]
    plan: dict[str, Any] = {
        "schemaVersion": 1,
        "operation": OPERATION,
        "versionReusePolicy": "prelaunch-test-only",
        "reasonSha256": digest,
        "confirmation": CONFIRMATION,
        "bookIds": book_ids,
        "originalUpdateIds": sorted(update_ids),
        "files": _file_inventory(root, _target_paths(root)),
        "remote": normalized_remote,
    }
    plan["inventorySha256"] = _plan_hash(plan)
    return plan


def verify_plan(root: Path, plan: dict[str, Any], *, remote: bool) -> None:
    if plan.get("operation") != OPERATION:
        raise ValueError("This is not a pre-launch catalog reset plan")
    if plan.get("versionReusePolicy") != "prelaunch-test-only":
        raise ValueError("The plan does not authorize pre-launch test tag reuse")
    if plan.get("inventorySha256") != _plan_hash(plan):
        raise ValueError("Plan inventory digest is invalid")
    paths = [root / item["path"] for item in plan.get("files", [])]
    if _file_inventory(root, paths) != plan.get("files"):
        raise ValueError("Local catalog inventory has changed")
    if remote:
        # Rebuild the remote side with the same publication ownership boundary.
        canonical = {
            item["tag"]
            for item in plan["remote"]["releases"]
            if CANONICAL_TAG.fullmatch(item["tag"])
        }
        current = _remote_state(canonical, set(plan.get("bookIds", [])))
        if current != plan.get("remote"):
            raise ValueError("Remote catalog inventory has changed")


def _remaining_manual_ids(root: Path) -> set[str]:
    result: set[str] = set()
    for path in sorted((root / "src/content/announcements").glob("*.md")):
        if _load_frontmatter(path).get("kind", "site-announcement") == "site-announcement":
            result.add(f"manual:{path.stem}")
    return result


def apply_plan(root: Path, plan: dict[str, Any], *, confirmation: str) -> dict[str, Any]:
    verify_plan(root, plan, remote=False)
    if confirmation != CONFIRMATION or confirmation != plan.get("confirmation"):
        raise ValueError("Confirmation phrase does not match the reset plan")

    pins_path = root / "src/data/site-update-pins.json"
    pins = json.loads(pins_path.read_text(encoding="utf-8")) if pins_path.is_file() else []
    if not isinstance(pins, list) or not all(isinstance(item, str) for item in pins):
        raise ValueError("site-update-pins.json must contain a string array")

    removed = 0
    for item in plan["files"]:
        path = root / item["path"]
        if path.is_file():
            path.unlink()
            removed += 1

    atomic_write_json(root / "src/data/generated-updates.json", [])
    valid_manual_ids = _remaining_manual_ids(root)
    atomic_write_json(
        pins_path,
        [item for item in pins if item in valid_manual_ids],
    )
    build_site_updates_archive(root)
    return {
        "schemaVersion": 1,
        "operation": OPERATION,
        "inventorySha256": plan["inventorySha256"],
        "removedFiles": removed,
        "preservedManualAnnouncements": len(valid_manual_ids),
        "preservedPins": len([item for item in pins if item in valid_manual_ids]),
        "releaseTags": [item["tag"] for item in plan["remote"]["releases"]],
        "gitTags": [item["tag"] for item in plan["remote"]["tags"]],
        "notifierUpdateIds": plan.get("originalUpdateIds", []),
    }


def _verify_downloaded_assets(directory: Path, release: dict[str, Any]) -> None:
    for asset in release["assets"]:
        path = directory / asset["name"]
        if not path.is_file() or path.stat().st_size != int(asset["bytes"]):
            raise ValueError(
                "Release asset backup is incomplete: "
                f"{release['tag']}/{asset['name']}"
            )
        digest = str(asset.get("digest") or "")
        if digest.startswith("sha256:") and _sha256_file(path) != digest.removeprefix("sha256:"):
            raise ValueError(
                "Release asset backup digest mismatch: "
                f"{release['tag']}/{asset['name']}"
            )


def backup_plan(root: Path, plan: dict[str, Any], recipient: str) -> tuple[Path, Path]:
    if not recipient.strip():
        raise ValueError("An age recipient is required")
    verify_plan(root, plan, remote=True)
    output_dir = root / "Outputs/catalog-resets"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    basename = f"{stamp}-catalog-reset-{plan['inventorySha256'][:12]}"
    destination = output_dir / f"{basename}.tar.zst.age"
    receipt = output_dir / f"{basename}.receipt.json"

    with tempfile.TemporaryDirectory(prefix="culturalsimmer-reset-") as temp_dir:
        staging = Path(temp_dir) / basename
        staging.mkdir()
        (staging / "inventory.json").write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        _run(
            [
                "git",
                "-C",
                str(root),
                "bundle",
                "create",
                str(staging / "repository.bundle"),
                "--all",
            ]
        )
        files_root = staging / "repository-files"
        for item in plan["files"]:
            if not item.get("exists"):
                continue
            source = root / item["path"]
            target = files_root / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        repository = _repository()
        for release in plan["remote"]["releases"]:
            target = staging / "releases" / release["tag"]
            target.mkdir(parents=True, exist_ok=True)
            (target / "release.json").write_text(
                _gh("api", f"repos/{repository}/releases/{release['releaseId']}") + "\n",
                encoding="utf-8",
            )
            _gh("release", "download", release["tag"], "--dir", str(target))
            _verify_downloaded_assets(target, release)

        tar = subprocess.Popen(
            ["tar", "-C", temp_dir, "-cf", "-", basename], stdout=subprocess.PIPE
        )
        zstd = subprocess.Popen(
            ["zstd", "-q", "-T0", "-c"], stdin=tar.stdout, stdout=subprocess.PIPE
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
            raise RuntimeError("Encrypted catalog reset backup failed")

    receipt_value = {
        "schemaVersion": 1,
        "inventorySha256": plan["inventorySha256"],
        "backup": destination.name,
        "backupBytes": destination.stat().st_size,
        "backupSha256": _sha256_file(destination),
    }
    receipt.write_text(
        json.dumps(receipt_value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination, receipt


def _delete_tag(repository: str, tag: str) -> None:
    result = subprocess.run(
        ["gh", "api", "--method", "DELETE", f"repos/{repository}/git/refs/tags/{tag}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if (
        result.returncode != 0
        and "HTTP 404" not in result.stderr
        and "Reference does not exist" not in result.stderr
    ):
        raise RuntimeError(result.stderr.strip() or f"Unable to delete tag: {tag}")


def finalize_remote(plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("inventorySha256") != _plan_hash(plan):
        raise ValueError("Plan inventory digest is invalid")
    if plan["remote"].get("immutableReleases"):
        raise ValueError("Immutable Releases prevents this pre-launch reset")
    repository = _repository()
    deleted_releases: list[str] = []
    for release in plan["remote"]["releases"]:
        tag = release["tag"]
        if _gh("release", "view", tag, "--json", "tagName", "--jq", ".tagName", check=False):
            _gh("release", "delete", tag, "--cleanup-tag", "--yes")
        deleted_releases.append(tag)
    deleted_tags: list[str] = []
    for item in plan["remote"]["tags"]:
        _delete_tag(repository, item["tag"])
        deleted_tags.append(item["tag"])
    return {"deletedReleases": deleted_releases, "deletedTags": deleted_tags}


def build_workflow_inputs(
    plan: dict[str, Any], receipt: dict[str, Any], *, mode: str
) -> dict[str, str]:
    if mode not in {"preview", "promote"}:
        raise ValueError("Workflow mode must be preview or promote")
    if plan.get("inventorySha256") != _plan_hash(plan):
        raise ValueError("Plan inventory digest is invalid")
    if receipt.get("inventorySha256") != plan["inventorySha256"]:
        raise ValueError("Backup receipt does not belong to this inventory")
    backup_digest = str(receipt.get("backupSha256") or "")
    if not re.fullmatch(r"[a-f0-9]{64}", backup_digest):
        raise ValueError("Backup receipt has no valid SHA-256 digest")
    return {
        "mode": mode,
        "reason_sha256": str(plan["reasonSha256"]),
        "inventory_sha256": str(plan["inventorySha256"]),
        "backup_sha256": backup_digest,
        "confirmation": CONFIRMATION,
    }


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    plan_parser = commands.add_parser("plan")
    reasons = plan_parser.add_mutually_exclusive_group(required=True)
    reasons.add_argument("--reason")
    reasons.add_argument("--reason-digest")
    plan_parser.add_argument("--remote-state")
    plan_parser.add_argument("--output", required=True)

    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--plan", required=True)
    verify_parser.add_argument("--remote", action="store_true")

    apply_parser = commands.add_parser("apply")
    apply_parser.add_argument("--plan", required=True)
    apply_parser.add_argument("--confirmation", required=True)
    apply_parser.add_argument("--output", required=True)

    backup_parser = commands.add_parser("backup")
    backup_parser.add_argument("--plan", required=True)
    backup_parser.add_argument("--age-recipient", required=True)

    finalize_parser = commands.add_parser("finalize-remote")
    finalize_parser.add_argument("--plan", required=True)
    finalize_parser.add_argument("--output", required=True)

    inputs_parser = commands.add_parser("workflow-inputs")
    inputs_parser.add_argument("--plan", required=True)
    inputs_parser.add_argument("--receipt", required=True)
    inputs_parser.add_argument("--mode", choices=("preview", "promote"), required=True)
    inputs_parser.add_argument("--output", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            remote_state = _load_json(Path(args.remote_state)) if args.remote_state else None
            plan = create_plan(
                ROOT,
                reason=args.reason,
                reason_digest=args.reason_digest,
                remote_state=remote_state,
            )
            Path(args.output).write_text(
                json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(plan["inventorySha256"])
        elif args.command == "verify":
            verify_plan(ROOT, _load_json(Path(args.plan)), remote=args.remote)
            print("Catalog reset inventory verified")
        elif args.command == "apply":
            result = apply_plan(
                ROOT, _load_json(Path(args.plan)), confirmation=args.confirmation
            )
            Path(args.output).write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print("Pre-launch test catalog reset applied")
        elif args.command == "backup":
            archive, receipt = backup_plan(
                ROOT, _load_json(Path(args.plan)), args.age_recipient
            )
            print(archive)
            print(receipt)
        elif args.command == "finalize-remote":
            result = finalize_remote(_load_json(Path(args.plan)))
            Path(args.output).write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print("Remote publication resources removed")
        else:
            inputs = build_workflow_inputs(
                _load_json(Path(args.plan)),
                _load_json(Path(args.receipt)),
                mode=args.mode,
            )
            Path(args.output).write_text(
                json.dumps(inputs, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print("GitHub workflow inputs generated")
    except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
